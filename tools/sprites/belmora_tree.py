"""BEL'MORA v0.10 tree: the ten new monsters and their effect sheets (drawn at final size, no design scale).

    python3 belmora_tree.py [outdir] [--only Name,Name]      (also run by belmora_rigs.py main)

Tree (every evolution has exactly one parent):
  Bell Urchin   -> Bell Diver {Drowned Bell, Drowned Captain}      Spinewalker {Crown of Thorns, Brood Urchin}
  Lurefish      -> Salt Siren {Tide Matriarch, Jelly Siren}         Brine Lamprey {Storm Eel, Slime Hag}
  Barnacle Crab -> Bell Hermit {Abyss Kraken, Belltower Hermit}     Anemone Boxer {Anemone Colossus, Reef Champion}

New monsters (sheet: look):
  BelSpinewalker   T2  the Bell Urchin's violet test raised on four long pale spine-stilts, a chime of brass bells under it
  BelBoxer         T2  the Barnacle Crab grown bigger and spikier, front-on under its barnacle dome, an anemone on each claw
  BelCrownThorns   T3  an indigo crown-of-thorns starfish walking upright on two arms, red-tipped spines, brass chimes
  BelBrood         T3  a bloated violet brood urchin on six short stilts, its back crusted with glowing pink eggs
  BelColossus      T3  a huge front-on crab whose barnacle dome has become a garden of stinging anemones
  BelChampion      T3  a crab standing upright like a prize fighter: barnacle helmet, coral gauntlets wrapped in anemones
  BelBelltower     T3  a hermit crab carrying a broken stone bell tower (two bells) instead of a single bell
  BelStormEel      T3  a long blue-black eel with the lamprey's gill pores turned electric yellow, sparking spots
  BelSlimeHag      T3  a pale pink hagfish tied in a knot, eyeless, whiskered, dripping green slime
  BelJellySiren    T3  the Salt Siren rising out of a pale jellyfish bell, trailing amber stinging tentacles
"""
import math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import belmora_rigs as B          # noqa: E402  (palette, primitives, sheet writer)
from rig import Canvas, line_px   # noqa: E402
from anim import Spr, PALETTE     # noqa: E402

ell, tube, line, poly, P, pick, Fr = B.ell, B.tube, B.line, B.poly, B.P, B.pick, B.Fr
DEFAULT_OUT = B.DEFAULT_OUT

PALETTE.update({
    # anemones (magenta -> pink, lime tips)
    'Ж': (0x7a, 0x2c, 0x5c), 'З': (0xc4, 0x4c, 0x8a), 'И': (0xf0, 0x8c, 0xbc), 'Й': (0xc8, 0xf0, 0x7a),
    # crown-of-thorns indigo
    'Л': (0x2c, 0x26, 0x5c), 'П': (0x46, 0x3e, 0x90), 'Ф': (0x6a, 0x62, 0xbc), 'Ц': (0x9c, 0x98, 0xe4),
    # storm eel blue-black
    'Ч': (0x1e, 0x26, 0x38), 'Ш': (0x34, 0x42, 0x5e), 'Щ': (0x52, 0x66, 0x8a), 'Ы': (0x7e, 0x94, 0xb8),
    # hagfish flesh
    'Э': (0x5c, 0x30, 0x3a), 'Ю': (0x94, 0x5a, 0x62), 'Я': (0xbe, 0x86, 0x82), 'б': (0xe4, 0xb6, 0xaa),
    # slime
    'в': (0xa8, 0xcc, 0x5c), 'г': (0xe0, 0xf4, 0x9c), 'д': (0x5e, 0x80, 0x34),
    # jelly bell
    'ж': (0x5c, 0x80, 0x9a), 'з': (0x96, 0xc2, 0xd4), 'и': (0xd6, 0xf0, 0xf6),
    # dark amber (lion's mane tentacles)
    'п': (0x7c, 0x3c, 0x1c),
    # tower stone (warm grey)
    'к': (0x4a, 0x46, 0x44), 'м': (0x78, 0x72, 0x6a), 'н': (0xa6, 0x9e, 0x90), 'р': (0xcc, 0xc4, 0xb0),
})
URCH = "jnNN"
URCH_L = "nNNЦ"
SPINE = "xfH"
EGG = "ЖЗИИ"
ANEM = "ЖЗИ"
CRAB = "pPPaa"
STAR = "ЛПФЦ"
EEL = "ЧШЩЫ"
HAG = "ЭЮЯб"
SLIME = "двг"
JELLY = "жжзи"
AMBER = "пoOY"
CORAL = "aoOY"
TSTONE = "кмнр"
FLESH = "zxMC"


# ------------------------------------------------------------------ helpers
def gl(c, x0, y0, x1, y1, ramp, over=True):
    """1 px line coloured along its length (ramp[0] at the start)."""
    pts = line_px(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1)))
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        t = i / max(1, n - 1)
        c.put(x, y, ramp[min(len(ramp) - 1, int(t * len(ramp)))], over)
    return pts


def rot(spr, deg, piv=(0.0, 0.0)):
    """Rotate a pixel sprite about piv (nearest neighbour, inverse mapped so no holes)."""
    if not spr.px: return spr
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    xs = [p[0] for p in spr.px]; ys = [p[1] for p in spr.px]
    R = int(max(abs(min(xs) - piv[0]), abs(max(xs) - piv[0]), abs(min(ys) - piv[1]), abs(max(ys) - piv[1]))) * 2 + 3
    out = {}
    for y in range(int(piv[1] - R), int(piv[1] + R) + 1):
        for x in range(int(piv[0] - R), int(piv[0] + R) + 1):
            dx, dy = x - piv[0], y - piv[1]
            sx, sy = dx * ca + dy * sa + piv[0], -dx * sa + dy * ca + piv[1]
            k = (int(round(sx)), int(round(sy)))
            if k in spr.px: out[(x, y)] = spr.px[k]
    return Spr(out)


def lay_down(spr, deg=-80, squash=1.0):
    """A corpse: the pose tipped over (backwards for negative deg) and set on the floor."""
    s = rot(spr, deg)
    if squash != 1.0:
        b = s.bbox()
        s = Spr({(x, int(round(y * squash))): v for (x, y), v in s.px.items()})
    return B.grounded(s)


def clip0(spr):
    return Spr({k: v for k, v in spr.px.items() if k[1] <= 0})


def anemone(c, x, y, r=2.4, flare=0.0, seed=0, n=9, sway=0.0):
    """A stinging anemone: frilly magenta-pink ball, tendrils with lime tips radiating (longer when it flares)."""
    for k in range(n):
        a = math.radians(k * 360.0 / n + seed * 23 + sway * (1 if k % 2 else -1))
        L = r + 1.2 + flare * 2.2 + (k % 2) * 0.7
        x1, y1 = x + math.cos(a) * L, y + math.sin(a) * L * 0.9
        gl(c, x + math.cos(a) * r * 0.5, y + math.sin(a) * r * 0.5, x1, y1, "ЗИ")
        c.put(*P(x1, y1), "Й")
    ell(c, x, y, r, r * 0.9, ANEM, bias=0.35)
    c.put(*P(x - r * 0.35, y - r * 0.4), "И")
    c.put(*P(x + 0.3, y + 0.2), "Ж")


def spines_ring(c, cx, cy, rx, ry, a0, a1, n, L, ramp_lit="xfH", ramp_dark="zxf", tip=True, seed=0, sway=0.0, r0=0.6):
    """Urchin spines radiating from an ellipse between angles a0..a1 (deg, 0 = right, 90 = down)."""
    for k in range(n):
        a = a0 + (a1 - a0) * (k + 0.5) / n + sway * (1 if k % 2 else -1)
        long_ = k % 2 == 0
        ln = L * (1.0 if long_ else 0.55)
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        lit = (ca + sa) < -0.25
        pts = gl(c, cx + ca * rx * r0, cy + sa * ry * r0, cx + ca * (rx + ln), cy + sa * (ry + ln), ramp_lit if lit else ramp_dark)
        if tip and long_ and pts: c.put(*pts[-1], "Q" if lit else "E")


def tubercle_shader(band_off=0.0):
    def tex(nu, nv, d, l, ch, x, y):
        if d < 0.9:
            k = math.sqrt(max(0.0, 1 - nv * nv))
            if k > 0.2:
                m = (nu / k) * 1.25 + band_off
                if abs(m - round(m)) < 0.13 and (y % 2 == 0):
                    return "d" if l > 0.15 else "D"
        if l > 0.75 and d < 0.6: return "Q" if (x + y) % 3 == 0 else "N"
        return ch
    return tex


def stone_tail(idle0, death, death_d, knock):
    return B.std_tail(idle0, death, death_d, knock)


BUILT = {}
NOTES = {}


def sheet(name, anims, outdir, scale=5):
    B.sheet(name, anims, outdir, scale=scale)
    BUILT[name] = B.BUILT[name]


def fx_sheet(name, anims, outdir, scale=6):
    B.fx_sheet(name, anims, outdir, scale=scale)
    BUILT[name] = B.BUILT[name]


# ================================================================== SPINEWALKER (T2, Bell Urchin line)
def spinewalker(dx=0.0, dy=0.0, h=14.0, ph=0.0, stride=0.0, tilt=0.0, puff=1.0, eye="open", stab=None, squat=0.0,
                chime=0.0, egg=0.0, curl=0.0, spark=0, extra=None):
    """The Bell Urchin's test (rx 6) raised on four spine stilts; a chime of three brass bells hangs under it."""
    f = Fr()
    cx, cy = dx, -h + dy + squat
    # legs: far pair dim (no outline), near pair outlined. Diagonal gait.
    specs = [(-3.4, -8.5, math.pi, f.n, "zx"), (3.4, 8.0, 0.0, f.n, "zx"),
             (-4.6, -11.0, 0.0, f.u, SPINE), (4.6, 11.0, math.pi, f.u, SPINE)]
    feet = []
    for k, (hx, fx, off, layer, ramp) in enumerate(specs):
        hip = (cx + hx, cy + 1.6)
        lift = max(0.0, math.sin(ph + off)) * 2.2 * stride
        foot = (dx + fx + stride * 2.6 * math.cos(ph + off), -lift)
        if k == 3 and stab is not None: foot = (dx + stab[0], stab[1])
        if curl:
            foot = (foot[0] + (hip[0] + (hx * 1.4) - foot[0]) * curl, foot[1] + (hip[1] - 5 - foot[1]) * curl)
        sd = 1 if foot[0] > hip[0] else -1
        # spider-like: the knee juts up and out above the body's side, the shin drops long to the floor
        kx, ky = hip[0] + sd * (3.2 + abs(hx) * 0.25) + (foot[0] - (dx + fx)) * 0.4, hip[1] - 4.5 + (lift * 0.6) * -1
        if k == 3 and stab is not None:
            kx, ky = (hip[0] + foot[0]) / 2 + 1.0, min(hip[1] - 4.0, (hip[1] + foot[1]) / 2 - 3.0)
        if curl: kx, ky = kx + (hip[0] - kx) * curl * 0.3, ky + 3 * curl
        ax, ay = foot
        if k == 3 and (stab is not None or curl > 0.4): layer = f.b
        if k >= 2:
            tube(layer, [hip, (kx, ky), (ax, ay)], [0.9, 0.7, 0.35], ramp, bias=0.2)
            layer.put(*P(kx, ky - 1), "N"); layer.put(*P(kx, ky), "n")
        else:
            gl(layer, hip[0], hip[1], kx, ky, "zx"); gl(layer, kx, ky, ax, ay, "xz")
        feet.append((ax, ay))
    # spines: upper half and sides, behind the test
    spines_ring(f.u, cx, cy, 6.2, 5.0, 175 + tilt, 365 + tilt, 14, 3.4 * puff, sway=puff * 2 - 2)
    # the test
    ell(f.b, cx, cy, 6.4, 5.0, URCH, ang=tilt, bias=0.2, shader=tubercle_shader(ph * 0.1))
    for k in range(4):      # short front spines over the rim
        a = 200 + k * 40 + tilt
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        line(f.b, cx + ca * 4.6, cy + sa * 3.6, cx + ca * 7.0, cy + sa * 5.6, "f")
    # egg sac swelling under the back (Sow)
    if egg > 0:
        ell(f.b, cx - 2.5, cy + 4.2 + egg * 1.2, 1.4 + egg * 1.0, 1.2 + egg * 0.9, EGG, bias=0.3)
        f.g.put(*P(cx - 2.5, cy + 4.2 + egg * 1.2), "q")
    # the chime: three brass bells on threads under the belly (the Bell Urchin's little bell, multiplied)
    for k, (bx, ln) in enumerate(((-2.4, 2.0), (0.6, 3.0), (3.4, 2.0))):
        sw = chime * (1 if k % 2 else -1) * 1.2
        top = (cx + bx, cy + 4.6)
        bot = (cx + bx + sw, cy + 4.6 + ln)
        line(f.b, top[0], top[1], bot[0], bot[1], "J")
        B.bell_tiny(f.b, bot[0], bot[1] + 3.2, glint=(k == 1 and chime > 0.5))
    # eyes on the front of the test
    ex, ey = cx + 3.6 + math.cos(math.radians(tilt)) * 0.3, cy + 0.6 + tilt * 0.05
    if eye == "open":
        for a in (0, 2): f.g.put(*P(ex + a, ey), "c"); f.g.put(*P(ex + a, ey + 1), "D")
    elif eye == "wide":
        for a in (0, 2): f.g.put(*P(ex + a, ey), "c"); f.g.put(*P(ex + a, ey - 1), "Q")
    elif eye == "squint":
        for a in (0, 2): f.g.put(*P(ex + a, ey), "E")
    else:
        for a in (0, 2): f.g.put(*P(ex + a, ey), "z")
    if spark and stab is not None:
        sx, sy = dx + stab[0], stab[1]
        for k, (a, b) in enumerate(((2, -1), (1, -3), (-1, -2), (3, 0), (-2, 0))[:spark]):
            f.g.put(*P(sx + a, sy + b), "Q" if k % 2 == 0 else "E")
    if extra: extra(f, cx, cy)
    return f.done(), feet


def build_spinewalker(outdir):
    S = lambda **k: spinewalker(**k)[0]
    idle = [S(h=14.0, chime=0.0), S(h=14.4, chime=0.6, puff=1.04), S(h=14.6, chime=1.0, puff=1.06, eye="squint"),
            S(h=14.2, chime=0.4, puff=1.02)]
    run = [S(ph=i * math.pi / 3, stride=1.0, h=14.0 + 0.6 * abs(math.sin(i * math.pi / 3)), tilt=-3, chime=math.sin(i) * 0.8)
           for i in range(6)]
    # STAB: the near front stilt rears up high and spears down ahead. HIT f3 at the stilt tip (16, 1).
    stab = [S(stab=(10.0, -12.0), tilt=-4, chime=0.4), S(stab=(7.0, -17.0), tilt=-10, eye="wide", dx=-0.8, chime=0.9),
            S(stab=(15.0, -6.0), tilt=6, dx=1.2, eye="wide", chime=-0.6),
            S(stab=(16.0, -1.0), tilt=9, dx=2.0, h=13.4, eye="squint", spark=5, chime=-1.0),
            S(stab=(16.0, -1.0), tilt=8, dx=2.0, h=13.4, eye="squint", spark=2, chime=-0.6),
            S(stab=(12.5, -6.0), tilt=3, dx=1.0, chime=0.2), S(chime=0.3)]
    # SOW: it squats, the egg sac swells under its back and drops (RELEASE f4: the eggs land around it), rises
    sow = [S(squat=1.0, egg=0.2, chime=0.3), S(squat=2.5, egg=0.6, puff=1.1, chime=0.6, eye="squint"),
           S(squat=4.0, egg=1.0, puff=1.2, chime=0.9, eye="squint"), S(squat=4.6, egg=1.3, puff=1.25, chime=1.0, eye="wide"),
           S(squat=3.0, egg=0.0, puff=0.9, chime=-0.8, eye="open"), S(squat=1.5, chime=-0.5), S(squat=0.6, chime=0.2),
           S(chime=0.0)]
    death = [S(tilt=-12, eye="wide", chime=1.0, puff=1.2, dx=-0.5), S(tilt=-22, squat=4.0, eye="dead", curl=0.3, chime=-1.0),
             S(tilt=-30, squat=8.0, eye="dead", curl=0.7, puff=0.8, chime=0.5),
             lay_down(S(tilt=0, squat=9.0, eye="dead", curl=1.0, puff=0.7), deg=-15)]
    knock = S(tilt=-14, dx=-1.0, eye="squint", chime=1.0, puff=1.15)
    anims = [("Idle", idle, [0.22, 0.18, 0.22, 0.18]), ("Run", run, [0.08] * 6),
             ("Stab", stab, [0.14, 0.14, 0.06, 0.07, 0.14, 0.12, 0.14]),
             ("Sow", sow, [0.12, 0.14, 0.16, 0.18, 0.08, 0.14, 0.14, 0.14])]
    anims += stone_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    sheet("BelSpinewalker", anims, outdir)


# ================================================================== ANEMONE BOXER (T2, Barnacle Crab line)
def boxer(dx=0.0, dy=0.0, hop=0.0, tilt=0.0, legs=0.0, near=(0.0, 0.0), far=(0.0, 0.0), eyes=1.0, eye="open", sink=0.0,
          splay=0.0, tuck=0.0, flare=0.0, sting=None, dark=False):
    """Front-on crab (the Barnacle Crab, bigger and spikier) with an anemone held in each claw like a boxing glove.
    near / far = hand offsets (x, y) from their rest points (near = right hand, far = left hand)."""
    f = Fr()
    cx, cy = dx, -7.0 + dy - hop + sink
    lift = tilt * 0.08
    for side in (-1, 1):
        for k in range(3):
            phs = legs + k * 2.1 + (0 if side > 0 else math.pi)
            root = (cx + side * (3.4 + k * 1.0), cy + 1.4 + side * lift)
            reach = (7.0 + k * 1.6) * (1 - 0.5 * tuck) + splay * 1.6
            knee = (cx + side * (reach * 0.62 + 1.0), cy - 2.4 - k * 0.5 + 2.4 * tuck - splay * 0.6 + side * lift - max(0.0, math.sin(phs)) * 0.7)
            foot = (cx + side * (reach + 1.8) + 0.6 * math.cos(phs), -max(0.0, math.sin(phs)) * 1.3 * (1 if hop == 0 else 0) - hop * 0.6 + sink * 0.2)
            gl(f.u, root[0], root[1], knee[0], knee[1], "pP" if side > 0 else "jp")
            gl(f.u, knee[0], knee[1], foot[0], foot[1], "Pa" if side > 0 else "pP")
            f.u.put(*P(*knee), "a" if side > 0 else "P")
    # carapace, spiked rim
    ell(f.b, cx, cy, 8.2, 3.4, CRAB, ang=tilt, bias=0.35)
    for x in range(int(cx - 6), int(cx + 7), 2):
        f.b.put(x, int(round(cy + 1.9 + (x - cx) * lift / 6)), "a")
    for k, x in enumerate((-7.5, -5.0, 5.0, 7.5)):
        f.b.put(*P(cx + x, cy - 2.6 - (k % 2) * 0.4), "a"); f.b.put(*P(cx + x + (0.6 if x > 0 else -0.6), cy - 3.4), "P")
    for x in range(int(cx - 2), int(cx + 3)): f.b.put(x, int(round(cy + 2.2)), "Z")
    def crust(nu, nv, d, l, ch, x, y):
        if (x * 5 + y * 3) % 7 == 0 and d < 0.8: return "z"
        return ch
    ell(f.b, cx - 0.2, cy - 3.0, 5.8, 6.2, "xfHH", ang=tilt, bias=0.2, vmax=0.0, shader=crust)
    B.barnacles(f.b, [(cx - 3.0, cy - 5.6), (cx + 0.4, cy - 7.6), (cx + 2.8, cy - 5.0)], seed=12, big=True)
    for x in range(int(cx - 5), int(cx + 6)):
        if x % 3 != 1: f.b.put(x, int(round(cy - 3.0)), "z")
    # a tuft of anemone on the dome (the boxer's colours already growing on it)
    anemone(f.b, cx - 1.6, cy - 8.2, r=1.1, flare=flare * 0.5, seed=3, n=6)
    if eyes > 0.05:
        for k, ex_ in enumerate((cx - 2.2, cx + 2.2)):
            top = cy - 0.2 - 1.8 * eyes * (1 - 0.7 * tuck)
            line(f.b, ex_, cy + 0.2, ex_, top, "P")
            ex2 = ex_ + (1 if k else -1)
            for (qx, qy) in ((ex_, top - 1), (ex2, top - 1), (ex_, top - 2), (ex2, top - 2)):
                f.b.put(*P(qx, qy), "z" if dark else "a")
            if not dark:
                f.g.put(*P(ex2 if eye != "wide" else ex_, top - 1), "Z" if eye != "wide" else "c")
                if eye == "wide": f.g.put(*P(ex2, top - 2), "Q")
    hands = []
    for side, off, lay in ((-1, far, f.b), (1, near, f.b)):
        ax, ay = cx + side * 5.6, cy - 0.6 + side * lift
        hx_ = cx + side * (6.8 - 4.0 * tuck) + off[0]
        hy_ = cy - 4.6 + 3.8 * tuck + off[1]
        mid = ((ax + hx_) / 2 + side * 1.0, (ay + hy_) / 2 + 0.8)
        tube(lay, [(ax, ay), mid, (hx_, hy_ + 1.4)], [1.3, 1.2, 1.1], "jpP", bias=0.05)
        ell(lay, hx_, hy_ + 0.4, 2.0, 1.8, CRAB, bias=0.4)
        anemone(lay, hx_ + side * 0.4, hy_ - 1.4, r=2.0, flare=flare, seed=7 + side, n=8)
        hands.append((hx_ + side * 0.4, hy_ - 1.4))
    if sting is not None:
        sx, sy = hands[1] if sting == "near" else hands[0]
        for k, (a, b) in enumerate(((3, -2), (4, 0), (3, 2), (5, -1), (5, 1), (6, 0))):
            f.g.put(*P(sx + a, sy + b), "Й" if k % 2 else "И")
    return f.done(), hands


def build_boxer(outdir):
    X = lambda **k: boxer(**k)[0]
    idle = [X(near=(0, 0), far=(0, 0), legs=0.0), X(near=(0.4, -0.6), far=(-0.4, 0.3), dy=-0.3, legs=0.5, flare=0.3),
            X(near=(0.2, -0.2), far=(-0.2, -0.6), legs=0.9, eyes=0.85, flare=0.5), X(near=(-0.2, 0.3), far=(0.3, -0.2), dy=0.2, legs=0.4)]
    run = [X(dy=-0.5 if i % 2 else 0, legs=i * 1.05, near=(0.6 * (i % 2), 0.5 * (i % 2)), far=(-0.6 * ((i + 1) % 2), 0.5 * ((i + 1) % 2)),
             tilt=[0, 2, 0, -2, 0, 2][i]) for i in range(6)]
    # JAB: one-two. Near (right) glove HITS on f2 at ~(17, -11); the far glove crosses over and HITS on f4 at ~(14, -10)
    jab = [X(near=(-2.0, 1.5), far=(1.0, -1.0), tilt=-3), X(near=(-3.5, 2.0), far=(1.5, -1.5), dx=-0.6, tilt=-5, eye="wide"),
           X(near=(8.5, 0.0), far=(1.0, -0.5), dx=1.2, tilt=4, sting="near", flare=0.6),
           X(near=(1.0, 1.0), far=(4.0, -0.5), dx=0.6, tilt=1),
           X(near=(-1.0, 2.0), far=(20.0, 0.5), dx=1.6, tilt=5, sting="far", flare=0.6),
           X(near=(0.0, 0.5), far=(6.0, 0.0), dx=0.6), X()]
    # FLURRY: crouch, hop in, then three quick stinging jabs (HITS f2, f4, f6), recover
    fl = [X(sink=1.5, near=(-2, 2), far=(1, 1), eye="wide", flare=0.4), X(hop=2.0, dx=1.0, near=(-1, -1), far=(1, -1), legs=1.0, flare=0.8),
          X(dx=2.0, near=(9.0, -1.0), far=(1.0, 0.0), sting="near", flare=1.0, tilt=4),
          X(dx=2.0, near=(2.0, 1.0), far=(14.0, 1.5), flare=1.0, tilt=3),
          X(dx=2.5, near=(9.5, 1.5), far=(2.0, 0.0), sting="near", flare=1.2, tilt=5),
          X(dx=2.5, near=(3.0, 0.0), far=(18.0, -1.0), flare=1.2, tilt=4),
          X(dx=2.5, near=(9.0, -2.0), far=(4.0, 0.0), sting="near", flare=1.2, tilt=6),
          X(dx=1.5, near=(2.0, 0.5), far=(1.0, 0.5), flare=0.6), X(flare=0.2)]
    death = [X(tilt=-6, eye="wide", near=(-1, -2), far=(1, -2)), X(tilt=-10, sink=1.0, tuck=0.3, eyes=0.6, splay=0.4, near=(1, 2), far=(-1, 2)),
             X(tilt=-12, sink=2.2, tuck=0.4, dark=True, eyes=0.3, splay=0.8, near=(2, 3), far=(-2, 3)),
             X(tilt=-12, sink=3.0, tuck=0.5, dark=True, eyes=0.0, splay=1.0, near=(2.5, 3.5), far=(-2.5, 3.5))]
    knock = X(dx=-1, tilt=-8, eye="wide", near=(-1.5, -2), far=(1.0, -1.5))
    anims = [("Idle", idle, [0.22, 0.16, 0.22, 0.16]), ("Run", run, [0.07] * 6),
             ("Jab", jab, [0.12, 0.1, 0.07, 0.1, 0.07, 0.14, 0.14]),
             ("Flurry", fl, [0.12, 0.1, 0.06, 0.07, 0.06, 0.07, 0.06, 0.12, 0.14])]
    anims += stone_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    sheet("BelBoxer", anims, outdir)
    NOTES["BelBoxer"] = {"near_jab": boxer(near=(8.5, 0.0), dx=1.2, tilt=4)[1][1], "far_jab": boxer(far=(20.0, 0.5), dx=1.6, tilt=5)[1][0]}


# ================================================================== CROWN OF THORNS (T3, Spinewalker line)
def star_arm(f, c, cx, cy, ang, L, bend=0.0, bristle=1.0, r0=3.4, seed=0):
    """A tapered starfish arm from the disc, bent a little, spined along both edges; returns its tip."""
    a = math.radians(ang)
    mid = (cx + math.cos(a + bend) * L * 0.55, cy + math.sin(a + bend) * L * 0.55)
    tip = (cx + math.cos(a + bend * 1.6) * L, cy + math.sin(a + bend * 1.6) * L)
    sp, _ = B.catmull([(cx, cy), mid, tip], [1, 1, 1], step=0.7)
    n = len(sp)
    rad = [r0 + (0.7 - r0) * (i / max(1, n - 1)) for i in range(n)]
    tube(c, sp, rad, STAR, bias=0.0)
    # spines along both edges, red tips
    for i in range(2, n - 1, 2):
        (x0, y0), (x1, y1) = sp[i - 1], sp[min(n - 1, i + 1)]
        tl = math.hypot(x1 - x0, y1 - y0) or 1
        nx_, ny_ = -(y1 - y0) / tl, (x1 - x0) / tl
        for sd in (-1, 1):
            if (i // 2 + (sd > 0) + seed) % 2: continue
            r = rad[i]
            bx, by = sp[i][0] + nx_ * sd * r, sp[i][1] + ny_ * sd * r
            ln = (1.6 + 0.5 * ((i + seed) % 3 == 0)) * bristle
            ex, ey = bx + nx_ * sd * ln, by + ny_ * sd * ln
            gl(f.g, bx + nx_ * sd * 0.6, by + ny_ * sd * 0.6, ex, ey, "ЦR" if (i + seed) % 3 else "Фr", over=False)
    # a row of pale pore dots down the arm's middle
    for i in range(3, n - 2, 3):
        c.put(*P(*sp[i]), "Ц")
    return tip


def crown(dx=0.0, dy=0.0, legs=(112.0, 68.0), arms=(205.0, 268.0, 330.0), lens=(15.5, 15.5, 13.5, 14.5, 13.5),
          bend=(0.0, 0.0, 0.0, 0.0, 0.0), bristle=1.0, eye="open", chime=0.0, glow=0, spin=0.0, streak=None):
    """Crown-of-thorns starfish standing on its two lower arms; three arms raised; chime bells on two arm tips."""
    f = Fr()
    cy = -lens[1] * math.sin(math.radians(legs[1])) - 1.0 + dy
    cx = dx
    tips = []
    order = [(legs[0] + spin, lens[0], bend[0], f.u), (legs[1] + spin, lens[1], bend[1], f.b),
             (arms[0] + spin, lens[2], bend[2], f.u), (arms[1] + spin, lens[3], bend[3], f.b), (arms[2] + spin, lens[4], bend[4], f.b)]
    for k, (a, L, bd, lay) in enumerate(order):
        tips.append(star_arm(f, lay, cx, cy, a, L, bend=bd, bristle=bristle, seed=k))
    # central disc: lighter, pore ring and five glowing eye-pores round the mouth
    ell(f.b, cx, cy, 5.2, 5.0, "ПФЦЦ", bias=0.1)
    for k in range(5):
        a = math.radians(k * 72 - 90 + spin)
        ex, ey = cx + math.cos(a) * 2.4, cy + math.sin(a) * 2.3
        if eye == "dead": f.g.put(*P(ex, ey), "Л")
        elif eye == "squint": f.g.put(*P(ex, ey), "E")
        else:
            f.g.put(*P(ex, ey), "c" if (glow or eye == "wide") else "E")
    f.g.put(*P(cx, cy), "Z"); f.g.put(*P(cx + 1, cy), "Л")
    # chime bells (Spinewalker): hang from the two side-arm tips
    for k, t in enumerate((tips[2], tips[4])):
        sw = chime * (1 if k else -1)
        line(f.b, t[0], t[1] + 0.5, t[0] + sw, t[1] + 2.5, "J")
        B.bell_tiny(f.b, t[0] + sw, t[1] + 5.6, glint=(k == 1 and abs(chime) > 0.5))
    if streak:
        for (x0, y0, x1, y1) in streak: gl(f.g, x0, y0, x1, y1, "ФЦR", over=False)
    return f.done(), tips, (cx, cy)


def build_crown(outdir):
    C = lambda **k: crown(**k)[0]
    idle = [C(chime=0.0), C(arms=(203, 266, 332), chime=0.5, bristle=1.05, dy=-0.3), C(arms=(201, 265, 334), chime=0.9, bristle=1.1, dy=-0.5),
            C(arms=(204, 267, 331), chime=0.4, bristle=1.03, dy=-0.2)]
    run = []
    for i in range(6):
        t = i * math.pi / 3
        run.append(C(legs=(112 + 14 * math.sin(t), 68 + 14 * math.sin(t)), spin=4 * math.sin(t), dy=-0.8 * abs(math.cos(t)),
                     arms=(205 - 6 * math.sin(t), 268, 330 + 6 * math.sin(t)), chime=math.sin(t) * 1.0))
    # LASH: the right arm rears up, then sweeps forward and down through the hero (HIT f3), recovers
    lash = [C(arms=(210, 262, 300), lens=(15.5, 15.5, 13.5, 14.5, 14.5), chime=0.5),
            C(arms=(214, 258, 282), lens=(15.5, 15.5, 13.5, 14.5, 15.0), spin=-6, eye="wide", chime=1.0),
            C(arms=(206, 266, 350), lens=(15.5, 15.5, 13.5, 14.5, 16.0), spin=4, chime=-0.6,
              streak=[(8, -24, 15, -16), (10, -22, 16, -12)]),
            C(arms=(204, 268, 18), lens=(15.5, 15.5, 13.5, 14.5, 16.5), spin=8, chime=-1.0, eye="squint"),
            C(arms=(204, 268, 22), lens=(15.5, 15.5, 13.5, 14.5, 16.5), spin=8, chime=-0.6, eye="squint"),
            C(arms=(205, 268, 355), spin=3, chime=0.2), C(chime=0.0)]
    # SHED: bristles (spines grow), shudders, then flings its thorns (RELEASE f3), regrows
    shed = [C(bristle=1.3, chime=0.3), C(bristle=1.7, arms=(200, 268, 335), spin=-3, eye="wide", chime=0.8),
            C(bristle=2.0, arms=(198, 268, 338), spin=3, eye="wide", chime=-0.8, glow=1),
            C(bristle=0.4, arms=(208, 270, 345), spin=6, chime=-1.0,
              streak=[(14, -18, 22, -15), (13, -14, 22, -12), (12, -10, 21, -8)]),
            C(bristle=0.4, chime=-0.5), C(bristle=0.6, chime=0.3), C(bristle=0.8, chime=0.1), C(chime=0.0)]
    death = [C(spin=-10, eye="wide", chime=1.0, bristle=1.3), C(spin=-25, dy=2.0, eye="dead", chime=-1.0, bristle=0.9),
             lay_down(C(spin=-30, eye="dead", bristle=0.8, legs=(130, 50)), deg=-55),
             lay_down(C(spin=0, eye="dead", bristle=0.6, legs=(150, 30), arms=(215, 270, 325)), deg=-90, squash=0.55)]
    knock = C(spin=-12, dx=-1.0, eye="squint", chime=1.0, bristle=1.2)
    anims = [("Idle", idle, [0.24, 0.2, 0.24, 0.2]), ("Run", run, [0.09] * 6),
             ("Lash", lash, [0.16, 0.14, 0.06, 0.07, 0.14, 0.14, 0.14]),
             ("Shed", shed, [0.14, 0.14, 0.18, 0.07, 0.12, 0.12, 0.12, 0.12])]
    anims += stone_tail(idle[0], death, [0.1, 0.12, 0.16, 0.4], knock)
    sheet("BelCrownThorns", anims, outdir)
    NOTES["BelCrownThorns"] = {"lash_tip": crown(arms=(204, 268, 18), lens=(15.5, 15.5, 13.5, 14.5, 16.5), spin=8)[1][4],
                               "shed_tip": crown(bristle=0.4, arms=(208, 270, 345), spin=6)[1][4]}


# ================================================================== BROOD URCHIN (T3, Spinewalker line)
def brood(dx=0.0, dy=0.0, squash=0.0, ph=0.0, stride=0.0, mouth=0, eye="open", eggs=1.0, bristle=1.0, tilt=0.0, launch=None,
          legs_curl=0.0, spray=0, nlay=6):
    """A bloated brood urchin (rx 11) on six short stilts; pink eggs cluster on its back; a wide maw with three eyes."""
    f = Fr()
    rx, ry = 11.0 * (1 + squash * 0.08), 7.6 * (1 - squash * 0.14)
    cx, cy = dx, -(ry + 4.6) + dy + squash * 1.5
    # six short stilts
    for k in range(6):
        hx = -8.0 + k * 3.2
        off = 0.0 if k % 2 else math.pi
        lift = max(0.0, math.sin(ph + off)) * 1.8 * stride
        hip = (cx + hx * 0.85, cy + ry * 0.7)
        foot = (dx + hx * 1.15 + stride * 1.5 * math.cos(ph + off), -lift)
        if legs_curl: foot = (foot[0] + (hip[0] - foot[0]) * legs_curl * 0.6, foot[1] - 3 * legs_curl)
        lay = f.n if k in (1, 3) else f.u
        if lay is f.n: gl(lay, hip[0], hip[1], foot[0], foot[1], "zx")
        else: tube(lay, [hip, ((hip[0] + foot[0]) / 2 + (1 if hx > 0 else -1) * 0.8, (hip[1] + foot[1]) / 2), foot], [0.8, 0.6, 0.4], SPINE, bias=0.2)
    spines_ring(f.u, cx, cy, rx, ry, 180 + tilt, 360 + tilt, 18, 4.6 * bristle, sway=0)
    ell(f.b, cx, cy, rx, ry, URCH, ang=tilt, bias=0.2, shader=tubercle_shader(0.3))
    # egg clutch on the back
    epos = [(-6.0, -4.5, 2.1), (-2.5, -6.2, 2.4), (1.4, -6.0, 2.2), (4.8, -4.2, 1.9), (-4.2, -1.8, 1.8), (-0.4, -3.2, 2.0)]
    for k, (ex, ey, er) in enumerate(epos[:nlay]):
        s = er * (0.7 + 0.3 * eggs)
        ell(f.b, cx + ex, cy + ey * (1 - squash * 0.1), s, s * 0.9, EGG, bias=0.35)
        f.g.put(*P(cx + ex + 0.3, cy + ey + 0.3), "q" if eggs < 1.15 else "N")
        f.b.put(*P(cx + ex - s * 0.4, cy + ey - s * 0.45), "X")
    # maw + eyes on the front-right
    mx, my = cx + rx * 0.62, cy + ry * 0.25
    for k in range(-2, 3):
        f.b.put(*P(mx + k * 0.6, my + abs(k) * 0.4), "Z")
    if mouth:
        ell(f.b, mx + 0.6, my + 1.0, 1.4 + mouth * 0.5, 0.6 + mouth * 0.7, "ZZp")
        for k in (-1, 1): f.b.put(*P(mx + 0.6 + k, my + 0.4), "H")
    for k, (ex, ey) in enumerate(((mx - 2.6, my - 3.0), (mx - 0.4, my - 3.6), (mx + 1.6, my - 2.6))):
        if eye == "dead": f.g.put(*P(ex, ey), "z")
        elif eye == "squint": f.g.put(*P(ex, ey), "E")
        else:
            f.g.put(*P(ex, ey), "c"); f.g.put(*P(ex, ey + 1), "D")
            if eye == "wide": f.g.put(*P(ex, ey - 1), "Q")
    if launch is not None:   # an egg flung up out of the clutch
        lx, ly = launch
        ell(f.g, cx + lx, cy + ly, 2.0, 1.9, EGG, bias=0.35)
        f.g.put(*P(cx + lx, cy + ly + 2.6), "И"); f.g.put(*P(cx + lx, cy + ly + 4.0), "З")
    for k in range(spray):
        f.g.put(*P(mx + 3 + k * 1.6, my - 0.5 + (k % 2)), "f" if k % 2 else "H")
    return f.done(), (mx, my)


def build_brood(outdir):
    Bm = lambda **k: brood(**k)[0]
    idle = [Bm(), Bm(squash=0.15, eggs=1.05), Bm(squash=0.25, eggs=1.1, eye="squint"), Bm(squash=0.1, eggs=1.03)]
    run = [Bm(ph=i * math.pi / 3, stride=1.0, squash=0.15 * abs(math.sin(i * math.pi / 3)), tilt=-2) for i in range(6)]
    # SPRAY: rears back, maw gapes, spits a fan of three spines (RELEASE f3 at the maw), settles
    spray = [Bm(squash=0.3, tilt=-4, mouth=1, eye="wide"), Bm(squash=0.5, tilt=-8, mouth=2, eye="wide", bristle=1.15),
             Bm(squash=-0.2, tilt=4, mouth=3, bristle=1.2), Bm(squash=-0.3, tilt=6, mouth=3, spray=4, eye="squint"),
             Bm(squash=0.0, tilt=3, mouth=2, spray=2), Bm(tilt=1, mouth=1), Bm()]
    # MORTAR: hunches, the clutch swells, an egg is hurled high (RELEASE f4), the clutch shrinks, it rises
    mortar = [Bm(squash=0.3, eggs=1.15), Bm(squash=0.7, eggs=1.3, eye="squint"), Bm(squash=1.0, eggs=1.45, eye="squint", bristle=1.1),
              Bm(squash=-0.4, eggs=1.2, eye="wide", launch=(-1.0, -12.0), nlay=5),
              Bm(squash=-0.3, eggs=1.0, eye="wide", launch=(-1.0, -20.0), nlay=4),
              Bm(squash=0.2, eggs=0.9, nlay=4), Bm(squash=0.1, eggs=0.95, nlay=5), Bm()]
    death = [Bm(squash=0.4, tilt=-8, eye="wide", mouth=2), Bm(squash=0.9, tilt=-14, eye="dead", mouth=1, legs_curl=0.4, bristle=0.8),
             Bm(squash=1.4, tilt=-16, eye="dead", legs_curl=0.8, bristle=0.6, eggs=0.7, dy=1.5),
             B.grounded(Bm(squash=2.2, tilt=-10, eye="dead", legs_curl=1.0, bristle=0.4, eggs=0.6, nlay=3, dy=3.0))]
    knock = Bm(squash=0.3, tilt=-10, dx=-1.0, eye="squint", bristle=1.1)
    anims = [("Idle", idle, [0.24, 0.2, 0.24, 0.2]), ("Run", run, [0.1] * 6),
             ("Spray", spray, [0.14, 0.14, 0.12, 0.06, 0.12, 0.14, 0.14]),
             ("Mortar", mortar, [0.14, 0.16, 0.18, 0.07, 0.1, 0.14, 0.14, 0.14])]
    anims += stone_tail(idle[0], death, [0.1, 0.12, 0.16, 0.4], knock)
    sheet("BelBrood", anims, outdir)
    NOTES["BelBrood"] = {"maw": brood(squash=-0.3, tilt=6, mouth=3)[1]}


# ================================================================== ANEMONE COLOSSUS (T3, Anemone Boxer line)
GARDEN = [(-7.5, -5.0, 1.9, 1), (-3.6, -9.0, 2.3, 2), (1.0, -10.2, 2.4, 3), (5.4, -7.6, 2.1, 4), (-0.8, -5.2, 1.7, 5),
          (8.4, -3.6, 1.6, 6), (-9.6, -2.4, 1.5, 7)]


def colossus(dx=0.0, dy=0.0, legs=0.0, tilt=0.0, near=(0.0, 0.0), far=(0.0, 0.0), open_=(0.4, 0.4), flare=0.0, eye="open",
             sink=0.0, splay=0.0, sway=0.0, pulse=0, dark=False):
    """A huge front-on crab: the barnacle dome is a garden of anemones; two massive pincers with anemone cuffs."""
    f = Fr()
    cx, cy = dx, -9.5 + dy + sink
    lift = tilt * 0.06
    for side in (-1, 1):
        for k in range(4):
            phs = legs + k * 1.7 + (0 if side > 0 else math.pi)
            root = (cx + side * (5.0 + k * 1.6), cy + 2.0 + side * lift)
            reach = 10.5 + k * 1.9 + splay * 2.0
            knee = (cx + side * (reach * 0.7 + 2.5), cy - 3.4 - k * 0.7 - splay * 0.8 + side * lift - max(0.0, math.sin(phs)) * 0.8)
            foot = (cx + side * (reach + 2.6) + 0.6 * math.cos(phs), -max(0.0, math.sin(phs)) * 1.2 + sink * 0.25)
            if side * (foot[0] - cx) > 20.5: foot = (cx + side * 20.5, foot[1])
            tube(f.u, [root, knee, foot], [0.9, 0.7, 0.4], "jpP" if side < 0 else "pPa", bias=0.1)
            f.u.put(*P(*knee), "a")
    ell(f.b, cx, cy, 14.0, 4.4, CRAB, ang=tilt, bias=0.35)
    for x in range(int(cx - 11), int(cx + 12), 2):
        f.b.put(x, int(round(cy + 2.8 + (x - cx) * lift / 6)), "a")
    for x in range(int(cx - 3), int(cx + 4)): f.b.put(x, int(round(cy + 3.0)), "Z")
    for k in range(3): f.b.put(*P(cx - 1 + k, cy + 3.8), "j")
    def crust(nu, nv, d, l, ch, x, y):
        if (x * 5 + y * 3) % 7 == 0 and d < 0.8: return "z"
        return ch
    ell(f.b, cx - 0.2, cy - 3.4, 11.0, 8.0, "xfHH", ang=tilt, bias=0.15, vmax=0.0, shader=crust)
    for x in range(int(cx - 10), int(cx + 11)):
        if x % 3 != 1: f.b.put(x, int(round(cy - 3.4)), "z")
    B.barnacles(f.b, [(cx - 6.0, cy - 7.2), (cx + 3.8, cy - 10.0), (cx + 8.0, cy - 6.0)], seed=21, big=True)
    for (ax, ay, ar, sd) in GARDEN:
        anemone(f.b, cx + ax, cy - 3.4 + ay * 0.92, r=ar, flare=flare, seed=sd, n=8, sway=sway * 10)
    # stalk eyes peering out under the garden's lip
    for k, ex_ in enumerate((cx - 2.6, cx + 2.6)):
        top = cy - 1.8
        line(f.b, ex_, cy + 0.6, ex_, top, "P")
        for (qx, qy) in ((ex_, top - 1), (ex_ + (1 if k else -1), top - 1)):
            f.b.put(*P(qx, qy), "z" if dark else "a")
        if not dark: f.g.put(*P(ex_ + (1 if k else -1), top - 1), "c" if eye in ("wide", "glare") else "Z")
    hands = []
    for side, off, op in ((-1, far, open_[1]), (1, near, open_[0])):
        ax, ay = cx + side * 11.5, cy - 0.8 + side * lift
        hx_ = cx + side * 16.0 + off[0]
        hy_ = cy - 7.0 + off[1]
        mid = ((ax + hx_) / 2 + side * 1.4, (ay + hy_) / 2 + 1.0)
        tube(f.b, [(ax, ay), mid, (hx_, hy_ + 2.2)], [2.0, 1.8, 1.7], "jpP", bias=0.05)
        anemone(f.b, (ax + hx_) / 2 + side * 1.0, (ay + hy_) / 2 + 0.4, r=1.2, flare=flare * 0.6, seed=11 + side, n=6)
        ell(f.b, hx_, hy_, 3.2, 2.8, CRAB, bias=0.45)
        for fs, ln, ramp in ((side, 4.0, "Paa"), (-side, 3.4, "pPa")):
            a = math.radians(-90 + fs * (6 + 26 * op))
            bx_, by_ = hx_ + fs * 1.4, hy_ - 2.0
            ex2, ey2 = bx_ + ln * math.cos(a), by_ + ln * math.sin(a)
            tube(f.b, [(bx_, by_), (ex2, ey2)], [1.0, 0.45], ramp, bias=0.2)
            f.b.put(*P(ex2 - fs * 0.9, ey2 + 0.3), "H")
        f.b.put(*P(hx_ - 1.0 * side, hy_ - 0.8), "a")
        hands.append((hx_, hy_))
    if pulse:
        rr = 15 + pulse * 3
        for k in range(28):
            a = 2 * math.pi * k / 28
            x, y = cx + rr * math.cos(a), -1 + rr * 0.32 * math.sin(a)
            if y <= 0 and k % 2 == 0: f.g.put(*P(x, y), "И" if k % 4 else "Й", over=False)
    return f.done(), hands


def build_colossus(outdir):
    Co = lambda **k: colossus(**k)[0]
    idle = [Co(sway=0.0), Co(sway=0.5, dy=-0.3, flare=0.2, legs=0.4), Co(sway=1.0, dy=-0.4, flare=0.35, legs=0.7),
            Co(sway=0.5, dy=-0.1, flare=0.15, legs=0.3)]
    run = [Co(legs=i * 1.05, dy=-0.5 if i % 2 else 0, sway=math.sin(i), tilt=[0, 1.5, 0, -1.5, 0, 1.5][i],
              near=(0, 0.6 * (i % 2)), far=(0, 0.6 * ((i + 1) % 2))) for i in range(6)]
    # HAMMER: both pincers rise high, then slam the floor ahead (HIT f3; the near pincer lands at ~(21, -3))
    ham = [Co(near=(-1, -5), far=(1, -5), open_=(0.8, 0.8), eye="glare"), Co(near=(-2, -8.5), far=(2, -8.5), open_=(1, 1), dy=-1, eye="glare"),
           Co(near=(3, 0), far=(-1, 0), open_=(0.2, 0.2), tilt=3),
           Co(near=(5, 4.5), far=(1, 3.5), open_=(0.0, 0.0), tilt=4, sink=1.0, eye="glare"),
           Co(near=(5, 4.5), far=(1, 3.5), open_=(0.0, 0.0), tilt=3, sink=1.0),
           Co(near=(2, 1), far=(0, 1), open_=(0.3, 0.3), sink=0.4), Co()]
    # BLOOM: the anemones swell and flare, then pulse a stinging ring (aura starts on f3), settle back
    bloom = [Co(flare=0.5, sway=0.5), Co(flare=1.0, sway=1.0, eye="glare"), Co(flare=1.6, sway=-0.5, eye="glare", dy=-1),
             Co(flare=2.0, sway=0.6, pulse=1, eye="glare", dy=-1), Co(flare=1.8, sway=-0.8, pulse=2, dy=-0.5),
             Co(flare=1.6, sway=0.8, pulse=1), Co(flare=1.0, sway=0.2), Co(flare=0.4)]
    death = [Co(tilt=-4, eye="wide", near=(-1, -4), far=(1, -4), flare=1.0), Co(tilt=-8, sink=1.0, splay=0.4, near=(1, 3), far=(-1, 3), flare=0.4, dark=True),
             Co(tilt=-9, sink=2.4, splay=0.8, near=(2, 5), far=(-2, 5), flare=-0.4, dark=True),
             Co(tilt=-9, sink=3.4, splay=1.0, near=(3, 5.5), far=(-3, 5.5), flare=-0.6, dark=True)]
    knock = Co(dx=-1, tilt=-6, eye="wide", near=(-1.5, -3), far=(1.0, -2.5), flare=0.8)
    anims = [("Idle", idle, [0.26, 0.2, 0.26, 0.2]), ("Run", run, [0.1] * 6),
             ("Hammer", ham, [0.16, 0.16, 0.06, 0.08, 0.16, 0.14, 0.16]),
             ("Bloom", bloom, [0.12, 0.14, 0.14, 0.12, 0.12, 0.12, 0.14, 0.14])]
    anims += stone_tail(idle[0], death, [0.1, 0.12, 0.16, 0.4], knock)
    sheet("BelColossus", anims, outdir)
    NOTES["BelColossus"] = {"slam": colossus(near=(5, 4.5), far=(1, 3.5), open_=(0, 0), tilt=4, sink=1.0)[1]}


# ================================================================== REEF CHAMPION (T3, Anemone Boxer line)
def gauntlet(c, x, y, ang, size=1.0, flare=0.0, glint=False, open_=0.5):
    """A coral-red crab gauntlet: a fat palm and two pincer prongs (dark gap between) pointing along ang, with the
    Boxer's anemone wrapped round the wrist."""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    ell(c, x, y, 3.0 * size, 2.5 * size, "pPaИ", ang=ang, bias=0.3)
    hx, hy = x + ux * 2.2 * size, y + uy * 2.2 * size
    tips = []
    for k, (sd, ln, ramp) in enumerate(((-1, 3.8, "PaИ"), (1, 3.2, "pPa"))):
        aa = a + sd * math.radians(10 + 22 * open_)
        bx, by = hx + nx * sd * 1.0 * size, hy + ny * sd * 1.0 * size
        mx, my = bx + math.cos(aa) * ln * 0.6 * size, by + math.sin(aa) * ln * 0.6 * size
        tx, ty = mx + math.cos(aa - sd * 0.7) * ln * 0.5 * size, my + math.sin(aa - sd * 0.7) * ln * 0.5 * size
        tube(c, [(bx, by), (mx, my), (tx, ty)], [1.2 * size, 0.9 * size, 0.4], ramp, bias=0.25)
        c.put(*P(tx, ty), "W")
        tips.append((tx, ty))
    if open_ > 0.25:
        poly(c, [(hx + ux * 0.6, hy + uy * 0.6), tips[0], tips[1]], "Z", over=False)
    if glint: c.put(*P(x - ux - nx * 1.0, y - uy - ny * 1.0), "X")
    c.put(*P(x - nx * 0.8, y - ny * 0.8), "И")
    anemone(c, x - ux * 3.0 * size, y - uy * 3.0 * size, r=1.3, flare=flare, seed=int(ang) % 7, n=7)
    return (x + ux * 5.5 * size, y + uy * 5.5 * size)


def champion(dx=0.0, dy=0.0, lean=0.0, ph=0.0, stride=0.0, near=(9.0, -18.0), far=(5.0, -20.0), crouch=0.0, eye="open",
             flare=0.0, glint=False, feet=None, dark=False, shimmer=0, gang=(-60.0, -45.0), gopen=(0.5, 0.5)):
    """A crab standing upright like a prize fighter: two jointed red legs, carapace torso, barnacle helmet, stalk
    eyes, coral gauntlets wrapped in the Boxer's anemones. near / far = gauntlet centres (from the feet)."""
    f = Fr()
    hip_y = -10.5 + crouch + dy
    lt = math.tan(math.radians(lean))
    T = lambda x, y: (dx + x + lt * (hip_y - y) * -1 * 0 + lt * (-(y - hip_y)), y)
    # legs (back leg under, near leg over), knees forward like a boxer's stance
    ft = feet or ((-4.0 + stride * 3 * math.cos(ph), max(0.0, math.sin(ph)) * 1.6 * stride),
                  (3.5 - stride * 3 * math.cos(ph), max(0.0, -math.sin(ph)) * 1.6 * stride))
    for k, (fx, fy) in enumerate(ft):
        hp = (dx + (-2.2 if k == 0 else 2.2), hip_y)
        foot = (dx + fx, -fy)
        (kx, ky), (ax, ay) = B.ik(hp[0], hp[1], foot[0], foot[1], 6.0, 6.2, bend=-1)
        lay = f.u if k == 0 else f.b
        tube(lay, [hp, (kx, ky), (ax, ay)], [1.6, 1.3, 1.0], "jpP" if k == 0 else "pPa", bias=0.1)
        lay.put(*P(kx, ky), "a")
        gl(lay, ax - 1.5, ay, ax + 2.0, ay, "pa")          # pointed foot tip
    # little walking legs folded at the waist (far side, dim)
    for k in range(2):
        gl(f.n, dx - 3 + k * 2, hip_y - 2, dx - 6 + k * 1.5, hip_y + 2.5, "jp")
    # abdomen plates + torso carapace
    ell(f.b, *T(0.6, hip_y - 2.0), 3.6, 2.6, "pPaa", bias=0.3)
    for k in range(3): f.b.put(*P(*T(-1.5 + k * 1.5, hip_y - 1.4)), "p")
    tc = T(0.0, hip_y - 8.0)
    ell(f.b, tc[0], tc[1], 5.6, 7.0, "pPaa", ang=lean, bias=0.3)
    for k in range(4):       # the carapace's pale segment ridges and a spined rim
        y_ = tc[1] - 3.5 + k * 2.4
        for x_ in range(-2, 3): f.b.put(*P(tc[0] + 0.8 + x_ + lt * (tc[1] - y_), y_), "a" if (x_ + k) % 2 else "o")
    for k in range(3): f.b.put(*P(tc[0] - 5.4, tc[1] - 3 + k * 3), "a"); f.b.put(*P(tc[0] - 6.2, tc[1] - 3.5 + k * 3), "P")
    # kelp belt
    for k in range(-4, 5): f.b.put(*P(*T(k * 1.0, hip_y - 3.2 + abs(k) * 0.15)), "Lvl"[k % 3])
    B.kelp(f.b, int(round(tc[0] - 3)), int(round(hip_y - 3)), 4, 0.5, seed=3)
    # barnacle helmet (the dome) + face
    hc = T(-0.6, hip_y - 16.6)
    def crust(nu, nv, d, l, ch, x, y):
        if (x * 5 + y * 3) % 7 == 0 and d < 0.8: return "z"
        return ch
    ell(f.b, hc[0], hc[1], 5.2, 4.6, "xfHH", ang=lean, bias=0.2, vmax=0.25, shader=crust)
    B.barnacles(f.b, [(hc[0] - 2.4, hc[1] - 2.2), (hc[0] + 1.0, hc[1] - 3.4)], seed=33, big=True)
    for k in range(-4, 5):
        if k % 3 != 1: f.b.put(*P(hc[0] + k, hc[1] + 1.0), "z")
    for k, ex_ in enumerate((hc[0] + 2.0, hc[0] + 4.0)):
        line(f.b, ex_, hc[1] + 2.4, ex_ + 0.4, hc[1] + 0.4, "P")
        f.b.put(*P(ex_ + 0.4, hc[1] - 0.4), "z" if dark else "a"); f.b.put(*P(ex_ + 1.4, hc[1] - 0.4), "z" if dark else "a")
        if not dark: f.g.put(*P(ex_ + 1.4, hc[1] - 0.4), "c" if eye == "wide" else "Z" if eye != "squint" else "E")
    f.b.put(*P(hc[0] + 3.4, hc[1] + 3.4), "Z"); f.b.put(*P(hc[0] + 4.2, hc[1] + 3.2), "a")      # mandibles
    # arms: far (under), near (over)
    tips = []
    for k, (gx, gy) in enumerate((far, near)):
        sh = T(-3.0 if k == 0 else 3.4, hip_y - 11.5)
        g = (dx + gx, gy + crouch * 0.5)
        (ex, ey), _ = B.ik(sh[0], sh[1], g[0], g[1], 5.0, 5.0, bend=-1)
        lay = f.u if k == 0 else f.b
        tube(lay, [sh, (ex, ey), g], [1.4, 1.2, 1.1], "jpP" if k == 0 else "pPa", bias=0.1)
        tips.append(gauntlet(lay, g[0], g[1], gang[k], size=1.25 if k else 1.0, flare=flare, glint=glint and k == 1, open_=gopen[k]))
    if shimmer:
        for k in range(shimmer):
            a = math.radians(-60 + k * 40)
            f.g.put(*P(dx + near[0] + 5 * math.cos(a), near[1] + 5 * math.sin(a)), "Y" if k % 2 else "y", over=False)
    return f.done(), tips


def build_champion(outdir):
    Ch = lambda **k: champion(**k)[0]
    idle = [Ch(), Ch(dy=0.3, near=(9.2, -17.6), far=(5.2, -19.6), flare=0.2), Ch(dy=0.5, near=(9.4, -17.2), far=(5.4, -19.3), flare=0.3, glint=True),
            Ch(dy=0.2, near=(9.1, -17.8), far=(5.1, -19.8), flare=0.1)]
    run = [Ch(ph=i * math.pi / 3, stride=1.0, lean=6, dy=-0.6 * abs(math.sin(i * math.pi / 3)),
              near=(9.5 + math.sin(i * math.pi / 3), -17.5), far=(5.5 - math.sin(i * math.pi / 3), -19.5)) for i in range(6)]
    # UPPERCUT: dip, coil low, drive up (HIT f3: the near gauntlet at ~(14, -25)), follow through, recover
    up = [Ch(crouch=1.5, near=(8.0, -12.0), far=(5.0, -20.0), lean=4, gang=(-50, -10)), Ch(crouch=3.0, near=(6.0, -8.0), far=(6.0, -21.0), lean=8, eye="wide", gang=(-50, 10), gopen=(0.4, 0.1)),
          Ch(crouch=0.5, near=(12.0, -18.0), far=(4.5, -19.0), lean=-2, flare=0.5, dx=1.0, gang=(-50, -60), gopen=(0.4, 0.1)),
          Ch(crouch=-1.0, near=(11.5, -29.0), far=(4.0, -18.0), lean=-8, flare=0.9, dx=1.5, glint=True, eye="squint", shimmer=4,
             gang=(-40, -80), gopen=(0.3, 0.9)),
          Ch(crouch=-1.0, near=(11.0, -29.5), far=(4.0, -18.0), lean=-8, flare=0.7, dx=1.5, gang=(-40, -80), gopen=(0.3, 0.7)),
          Ch(crouch=0.5, near=(10.5, -20.0), far=(5.0, -19.0), lean=-2, dx=0.8), Ch()]
    # GUARD: gauntlets cross in front of the face (guard on f1 .. off f7); the coral glints while it waits
    gd = [Ch(near=(8.0, -21.0), far=(6.5, -22.0), crouch=0.5), Ch(near=(6.5, -24.0), far=(6.0, -21.5), crouch=1.2, eye="squint", gang=(-100, -80), gopen=(0.2, 0.2)),
          Ch(near=(6.5, -24.0), far=(6.0, -21.5), crouch=1.4, eye="squint", glint=True, shimmer=2, gang=(-100, -80), gopen=(0.1, 0.1)),
          Ch(near=(6.6, -23.8), far=(6.0, -21.4), crouch=1.2, eye="squint", shimmer=3, gang=(-100, -80), gopen=(0.1, 0.1)),
          Ch(near=(6.5, -24.0), far=(6.0, -21.5), crouch=1.4, eye="squint", glint=True, shimmer=2, gang=(-100, -80), gopen=(0.1, 0.1)),
          Ch(near=(6.6, -23.8), far=(6.0, -21.4), crouch=1.2, eye="squint", shimmer=3, gang=(-100, -80), gopen=(0.1, 0.1)),
          Ch(near=(6.5, -24.0), far=(6.0, -21.5), crouch=1.4, eye="squint", glint=True, shimmer=2, gang=(-100, -80), gopen=(0.1, 0.1)),
          Ch(near=(8.5, -19.0), far=(5.5, -20.0), crouch=0.4)]
    death = [Ch(lean=-10, eye="wide", near=(5, -24), far=(2, -24), dx=-0.5), Ch(lean=-20, crouch=3.0, eye="squint", near=(8, -10), far=(-2, -12), dark=True),
             lay_down(Ch(lean=0, eye="squint", near=(9, -9), far=(-4, -10), dark=True), deg=-50),
             lay_down(Ch(lean=0, eye="squint", near=(10, -6), far=(-6, -8), dark=True, feet=((-5, 0), (4, 0))), deg=-90)]
    knock = Ch(lean=-14, dx=-1.0, eye="squint", near=(7.0, -22.0), far=(3.5, -24.0), crouch=0.5)
    anims = [("Idle", idle, [0.24, 0.2, 0.24, 0.2]), ("Run", run, [0.08] * 6),
             ("Uppercut", up, [0.14, 0.14, 0.06, 0.07, 0.14, 0.14, 0.14]),
             ("Guard", gd, [0.1, 0.12, 0.2, 0.2, 0.2, 0.2, 0.2, 0.14])]
    anims += stone_tail(idle[0], death, [0.08, 0.12, 0.16, 0.4], knock)
    sheet("BelChampion", anims, outdir)
    NOTES["BelChampion"] = {"upper": champion(crouch=-1.0, near=(11.5, -29.0), far=(4.0, -18.0), lean=-8, dx=1.5, gang=(-40, -80))[1][1],
                            "guard": champion(near=(6.5, -24.0), far=(6.0, -21.5), crouch=1.4)[1][1]}


# ================================================================== BELLTOWER HERMIT (T3, Bell Hermit line)
def belltower(dx=0.0, dy=0.0, lean=0.0, legs=0.0, claw=(-30, -5, 30), ring=0, sway=0.0, eye="open", eyes=1.0, lift=0.0,
              reach=0.0, bob=0.0, dark=False, snap=0):
    """A hermit crab under a broken stone bell tower: two bronze bells hang in the tower; the maroon crab (legs, stalk
    eyes, crusher claw) spills out under its front."""
    f = Fr()
    base = (dx - 3.0, -6.5 + dy - lift)
    a = math.radians(-90 - 12 + lean)      # the tower's axis leans back
    ux, uy = math.cos(a), math.sin(a)      # up the tower
    nx, ny = -uy, ux                       # across (toward the front at lean 0... x+)
    W, H = 6.4, 26.0
    def Tp(s, t): return (base[0] + ux * t + nx * s, base[1] + uy * t + ny * s)
    hb = (dx + 4.0 + reach, -4.2 + dy - lift + bob)
    # far crab legs (dim) + under-body
    for k in range(3):
        ph = legs + k * 2.4 + math.pi
        root = (hb[0] - 4 + k * 2.2, hb[1] + 0.4)
        foot = (root[0] - 2 + k * 1.4 + 1.2 * math.sin(ph), -max(0.0, math.cos(ph)) * 1.0 - lift)
        gl(f.n, root[0], root[1], (root[0] + foot[0]) / 2 - 1, root[1] - 1.5, "jp"); gl(f.n, (root[0] + foot[0]) / 2 - 1, root[1] - 1.5, foot[0], foot[1], "pj")
    ell(f.u, hb[0] - 1.5, hb[1] - 0.6, 5.6, 3.0, CRAB, bias=0.2)
    # the tower: a stone block with brick courses, an arched bell opening, a broken top
    def stone(x, y):
        # local coords
        rx_, ry_ = x - base[0], y - base[1]
        t = rx_ * ux + ry_ * uy
        s = rx_ * nx + ry_ * ny
        l = -s / W * 0.8 + 0.25
        ch = pick(TSTONE, l)
        if int(t) % 5 == 0: ch = "к"
        elif int(s + (3 if (int(t) // 5) % 2 else 0)) % 6 == 0: ch = "к"
        return ch
    top = [Tp(-W, H - 1), Tp(-W * 0.4, H + 1.5), Tp(0, H - 0.5), Tp(W * 0.5, H + 2.0), Tp(W, H - 2)]
    poly(f.b, [Tp(-W, 0), Tp(W, 0)] + top[::-1], "м", shade=stone)
    # arched opening
    def hole(x, y): return "Z"
    op = [Tp(-W + 2.2, 7), Tp(W - 2.2, 7), Tp(W - 2.2, 17), Tp(0, 20.5), Tp(-W + 2.2, 17)]
    poly(f.b, op, "Z")
    gl(f.b, *Tp(-W + 2.0, 6.5), *Tp(W - 2.0, 6.5), "н")
    # beam + bell inside the opening
    bc = Tp(0, 13.5)
    line(f.b, *Tp(-W + 2.2, 18), *Tp(W - 2.2, 18), "J")
    B.church_bell(f.b, f.g, bc[0] + sway * 1.6, bc[1], 90 + lean + sway * 22, size=4.2, crack=False, ring=ring, seed=81, round_=False)
    # second, smaller bell hung from a broken beam on the top
    tb = Tp(1.5, H + 2.5)
    line(f.b, *Tp(-2.5, H + 0.5), tb[0] + 2.5, tb[1] - 0.5, "J")
    B.church_bell(f.b, f.g, tb[0] - sway * 1.2, tb[1] + 2.6, 90 + lean - sway * 18, size=2.6, crack=False, ring=0, seed=82, round_=True)
    B.barnacles(f.b, [Tp(-W + 1.0, 3.0), Tp(W - 1.5, 9.0), Tp(-W + 1.5, 21.0)], seed=83, big=True)
    B.kelp(f.b, int(round(Tp(W - 0.5, 4)[0])), int(round(Tp(W - 0.5, 4)[1])), 5, 0.7, seed=4)
    B.kelp(f.b, int(round(Tp(-W + 0.5, 12)[0])), int(round(Tp(-W + 0.5, 12)[1])), 6, 0.7, seed=1)
    if ring:
        for k in range(3):
            for sd in (-1, 1):
                p = Tp(sd * (W + 1.5 + ring), 10 + k * 5)
                f.g.put(*P(*p), "Q" if k == 1 else "E", over=False)
    # front: stalk eyes, near legs and the crusher claw
    if eyes > 0.1:
        for k, ox in enumerate((0.6, 2.6)):
            b0 = (hb[0] + ox, hb[1] - 2.2)
            line(f.b, *b0, b0[0] + 0.4 + k * 0.5, b0[1] - 4.0 * eyes, "jp")
            ex, ey = P(b0[0] + 0.4 + k * 0.5, b0[1] - 4.0 * eyes - 0.8)
            if eye == "dead" or dark: f.g.put(ex, ey, "x")
            elif eye == "squint": f.g.put(ex, ey, "E")
            else:
                f.g.put(ex, ey, "c"); f.g.put(ex, ey - 1, "Q")
                if eye == "wide": f.g.put(ex + 1, ey, "c")
    for k in range(3):
        ph = legs + k * 2.1
        root = (hb[0] - 4.0 + k * 2.4, hb[1] + 1.2)
        up = 1.6 + 1.0 * max(0.0, math.sin(ph))
        knee = (root[0] + 1.6 + k * 0.4, root[1] - up + 0.4)
        foot = (root[0] + 2.8 + k * 0.8 + 1.1 * math.sin(ph), -max(0.0, 1.3 * math.cos(ph)) - lift)
        gl(f.b, *root, *knee, "pP"); gl(f.b, *knee, *foot, "Pa")
        f.b.put(*P(*knee), "a")
    tip = B.crab_claw(f.b, hb[0] + 2.0, hb[1] + 0.2, claw[0], claw[1], claw[2], big=1.1, ramp="jpPa")
    if snap:
        for k, (aa, bb) in enumerate(((2, -2), (3, 0), (2, 2), (4, -3), (4, 2), (5, 0))[:snap]):
            f.g.put(*P(tip[0] + aa, tip[1] + bb), "Q" if k % 2 == 0 else "E")
    return f.done(), tip


def build_belltower(outdir):
    Bt = lambda **k: belltower(**k)[0]
    idle = [Bt(claw=(-28, -6, 26)), Bt(claw=(-26, -3, 32), legs=0.3, dy=0.3, sway=0.3, bob=0.2),
            Bt(claw=(-24, -1, 34), legs=0.5, dy=0.4, sway=0.5, eye="squint", bob=0.3), Bt(claw=(-30, -8, 22), legs=0.2, dy=0.1, sway=0.2)]
    run = []
    for i in range(6):
        t = i * math.pi / 3
        run.append(Bt(legs=t * 1.5, dy=-0.6 * abs(math.sin(t)), lean=3 * math.sin(t), lift=0.4 * abs(math.sin(t)), sway=0.6 * math.sin(t),
                      claw=(-34 + 6 * math.sin(t), -10 + 5 * math.sin(t), 22 + 8 * math.cos(t))))
    # CRUSH: raise the claw wide, lunge, SNAP at full reach (HIT f3, tip ~(24, -3)), grind, recover
    crush = [Bt(claw=(-80, -50, 40), lean=-4, dx=-0.5, eye="wide", legs=0.4, sway=-0.4),
             Bt(claw=(-110, -90, 58), lean=-8, dx=-1.2, eye="wide", legs=0.8, sway=-0.8),
             Bt(claw=(-25, -2, 60), lean=4, dx=1.5, legs=1.6, reach=1.0, sway=0.6),
             Bt(claw=(-4, 8, -6), lean=6, dx=2.5, legs=2.0, reach=1.5, eye="squint", snap=6, sway=1.0, ring=1),
             Bt(claw=(-6, 6, -4), lean=5, dx=2.2, legs=2.0, reach=1.2, eye="squint", snap=3, sway=0.6),
             Bt(claw=(-20, -2, 14), lean=2, dx=1.0, legs=1.4, sway=0.2), Bt(claw=(-28, -6, 24), legs=0.6)]
    # MARCH: rears back, slams the claw on the floor and both bells swing out (RELEASE f4: the peals march out)
    march = [Bt(claw=(-90, -70, 30), lean=-6, eye="wide", sway=-0.5), Bt(claw=(-120, -100, 40), lean=-11, dy=-0.5, eye="wide", sway=-1.0),
             Bt(claw=(-60, -30, 10), lean=-4, sway=-0.4), Bt(claw=(10, 60, 0), lean=6, dx=1.0, sway=1.0, ring=1, eye="squint"),
             Bt(claw=(12, 62, 0), lean=7, dx=1.2, sway=1.2, ring=2, eye="squint"), Bt(claw=(8, 55, 0), lean=5, dx=1.0, sway=-0.8, ring=2),
             Bt(claw=(-10, 20, 10), lean=3, sway=0.6, ring=1), Bt(claw=(-20, -2, 18), sway=-0.3), Bt(claw=(-28, -6, 24))]
    death = [Bt(claw=(-100, -70, 40), lean=-8, eye="wide", sway=-1.0), Bt(claw=(-140, 170, 30), lean=-16, dy=0.5, eye="dead", eyes=0.6, sway=1.2),
             lay_down(Bt(claw=(170, 120, 20), eye="dead", eyes=0.5, sway=0.4, dark=True), deg=-40),
             lay_down(Bt(claw=(170, 120, 20), eye="dead", eyes=0.3, dark=True), deg=-85)]
    knock = Bt(claw=(-110, -60, 35), lean=-10, dx=-0.6, eye="squint", legs=0.8, lift=0.6, sway=-1.0)
    anims = [("Idle", idle, [0.26, 0.2, 0.26, 0.2]), ("Run", run, [0.09] * 6),
             ("Crush", crush, [0.14, 0.14, 0.07, 0.06, 0.12, 0.12, 0.14]),
             ("March", march, [0.14, 0.16, 0.08, 0.06, 0.12, 0.14, 0.14, 0.12, 0.14])]
    anims += stone_tail(idle[0], death, [0.1, 0.12, 0.16, 0.4], knock)
    sheet("BelBelltower", anims, outdir)
    NOTES["BelBelltower"] = {"tip": belltower(claw=(-4, 8, -6), lean=6, dx=2.5, legs=2.0, reach=1.5)[1],
                             "slam": belltower(claw=(10, 60, 0), lean=6, dx=1.0)[1]}


# ================================================================== STORM EEL (T3, Brine Lamprey line)
def eel_spine(dx=0.0, dy=0.0, phase=0.0, amp=1.0, neck=1.0, head=(0.0, 0.0), lunge=0.0, length=1.0, coil=0.0):
    length *= 1.12
    pts = []
    n = 7
    for k in range(n):
        x = dx - 19.0 * length + k * 3.4 * length * (1 - coil * 0.35) + lunge * k / n * 0.7
        y = -2.4 - amp * math.sin(k * 1.05 + phase) * (0.5 + 0.5 * k / n) - coil * 3.0 * math.sin(k * 0.9 + 1)
        pts.append((x, y))
    nb = pts[-1]
    hy = -4.5 - 9.5 * neck + dy + head[1]
    pts.append((nb[0] + 1.6 + lunge * 0.5, nb[1] - 3.6 * neck))
    pts.append((nb[0] + 2.4 + lunge * 0.8 + head[0] * 0.4, hy + 0.5))
    pts.append((nb[0] + 6.0 + lunge + head[0], hy))
    return pts


def eel(spine=None, mouth=0, eye="open", glow=1, crackle=0, hdir=None, seed=0, dark=False, **kw):
    """A long blue-black eel: a continuous dorsal fin, sparking yellow electric spots along its flank, the lamprey's
    seven gill pores (now glowing yellow), a hooked jaw with needle teeth."""
    f = Fr()
    pts = spine if spine is not None else eel_spine(**kw)
    rad = [0.6, 1.2, 1.8, 2.2, 2.6, 2.8, 2.9, 2.9, 2.6, 3.0][-len(pts):]
    sp, sr = B.catmull(pts, rad, step=0.8)
    n = len(sp)
    # dorsal fin along the top, from a quarter back to just behind the head; tail fin
    for i in range(int(n * 0.08), int(n * 0.8)):
        (x0, y0), (x1, y1) = sp[max(0, i - 1)], sp[min(n - 1, i + 1)]
        tl = math.hypot(x1 - x0, y1 - y0) or 1
        nx_, ny_ = (y1 - y0) / tl, -(x1 - x0) / tl
        if ny_ > 0: nx_, ny_ = -nx_, -ny_
        hgt = 1.4 + 0.5 * math.sin(i * 0.6)
        f.u.put(*P(sp[i][0] + nx_ * (sr[i] + 0.6), sp[i][1] + ny_ * (sr[i] + 0.6)), "Ш")
        f.u.put(*P(sp[i][0] + nx_ * (sr[i] + hgt), sp[i][1] + ny_ * (sr[i] + hgt)), "Щ" if i % 3 else "Ы")
    tx, ty = sp[0]
    for a in (-170, 180, 165):
        gl(f.u, tx, ty, tx + 3.2 * math.cos(math.radians(a)), ty + 2.6 * math.sin(math.radians(a)), "ШЩ")
    tube(f.b, sp, sr, EEL, bias=-0.12)
    # pale belly, electric organ spots along the flank
    for i in range(1, n - 1):
        (x0, y0), (x1, y1) = sp[i - 1], sp[i + 1]
        tl = math.hypot(x1 - x0, y1 - y0) or 1
        nx_, ny_ = -(y1 - y0) / tl, (x1 - x0) / tl
        if ny_ < 0: nx_, ny_ = -nx_, -ny_
        r = sr[i]
        if r > 1.0: f.b.put(*P(sp[i][0] + nx_ * r * 0.65, sp[i][1] + ny_ * r * 0.65), "Ы" if i % 3 else "u")
        if i % 2 == 0 and r > 1.3 and i < n - 8 and i % 4 != 1:
            f.b.put(*P(sp[i][0] - nx_ * r * 0.15, sp[i][1] - ny_ * r * 0.15), "Щ")
        if i % 4 == 1 and r > 1.3 and i < n - 8:
            f.g.put(*P(sp[i][0] - nx_ * r * 0.1, sp[i][1] - ny_ * r * 0.1), "Y" if glow else "o")
    # head
    hx, hy = pts[-1]
    if hdir is None:
        px_, py_ = sp[max(0, n - 4)]
        hdir = math.degrees(math.atan2(hy - py_, hx - px_))
    a = math.radians(hdir)
    ux, uy = math.cos(a), math.sin(a)
    nx_, ny_ = -uy, ux
    ell(f.b, hx + ux * 0.5, hy + uy * 0.5, 4.6, 3.0, EEL, ang=hdir, bias=0.15)
    # jaw: lower jaw hinges open
    ja = a + math.radians(18 + 14 * mouth)
    jx0, jy0 = hx - ux * 0.5 + nx_ * 1.4, hy - uy * 0.5 + ny_ * 1.4
    tube(f.b, [(jx0, jy0), (jx0 + math.cos(ja) * 4.6, jy0 + math.sin(ja) * 4.6)], [1.1, 0.6], "ШЩЫ", bias=0.2)
    if mouth:
        poly(f.b, [(hx + ux * 3.8 + nx_ * 0.4, hy + uy * 3.8 + ny_ * 0.4), (jx0, jy0), (jx0 + math.cos(ja) * 4.2, jy0 + math.sin(ja) * 4.2)], "Z", over=True)
        for k in range(3):
            f.b.put(*P(hx + ux * (1.5 + k * 1.1) + nx_ * 0.9, hy + uy * (1.5 + k * 1.1) + ny_ * 0.9), "X")
            f.b.put(*P(jx0 + math.cos(ja) * (1.2 + k * 1.1) - nx_ * 0.4, jy0 + math.sin(ja) * (1.2 + k * 1.1) - ny_ * 0.4), "u")
    # gill pores (the Lamprey's seven), now electric
    gp = []
    for i in range(n - 6, 0, -1):
        q = P(*sp[i])
        if math.hypot(q[0] - hx, q[1] - hy) < 3.5: continue
        if gp and abs(q[0] - gp[-1][0]) + abs(q[1] - gp[-1][1]) < 2: continue
        gp.append(q)
        if len(gp) == 7: break
    for k, (x, y) in enumerate(gp):
        f.g.put(x, y, ("y" if k % 2 == 0 else "Y") if glow >= 2 else ("Y" if k % 2 == 0 else "o") if glow else "Ш")
    ex, ey = P(hx + ux * 1.2 - nx_ * 1.0, hy + uy * 1.2 - ny_ * 1.0)
    if eye == "dead": f.g.put(ex, ey, "Щ")
    elif eye == "squint": f.g.put(ex, ey, "o")
    else:
        f.g.put(ex, ey, "y"); f.g.put(ex - 1, ey, "Y")
        if eye == "wide": f.g.put(ex, ey - 1, "y")
    if crackle:
        rnd = random.Random(seed * 13 + crackle)
        for k in range(crackle * 3):
            i = rnd.randrange(2, n - 2)
            x, y = sp[i]
            r = sr[i] + 1.5
            ang = rnd.uniform(0, 2 * math.pi)
            px_, py_ = x + math.cos(ang) * r, y + math.sin(ang) * r
            for j in range(3):
                qx, qy = px_ + math.cos(ang) * (j + 1) * 1.3 + rnd.choice((-1, 0, 1)), py_ + math.sin(ang) * (j + 1) * 1.3
                if qy <= 0: f.g.put(*P(qx, qy), "y" if j == 0 else ("c" if j == 1 else "Y"), over=False)
    if dark: pass
    return f.done(), (hx + ux * 4.0, hy + uy * 4.0)


def build_eel(outdir):
    E = lambda **k: eel(**k)[0]
    idle = [E(phase=i * 0.5, amp=1.2, neck=1.0, head=(0, [0, -0.4, -0.6, -0.2][i]), glow=1 + (i == 2), crackle=1 if i == 2 else 0, seed=i)
            for i in range(4)]
    run = [E(phase=i * math.pi / 3 * 2, amp=1.8, neck=0.8, lunge=0.6, head=(0, -0.4 * abs(math.sin(i))), seed=i) for i in range(6)]
    # SHOCK: rear back, gape, lunge (HIT f3: jaws at ~(18, -8)), crackle, recover
    shock = [E(phase=0.6, amp=1.5, neck=1.2, head=(-3.0, -1.5), lunge=-1.0, mouth=1, eye="wide", glow=2, hdir=-20),
             E(phase=0.9, amp=1.9, neck=1.35, head=(-4.5, -2.0), lunge=-1.5, mouth=2, eye="wide", glow=2, crackle=1, hdir=-30),
             E(phase=1.4, amp=0.7, neck=0.7, head=(3.5, 1.0), lunge=4.0, mouth=3, eye="wide", glow=2, crackle=1, hdir=8, length=1.04),
             E(phase=1.6, amp=0.5, neck=0.65, head=(4.5, 1.5), lunge=5.0, mouth=1, eye="squint", glow=2, crackle=3, hdir=12, length=1.06, seed=3),
             E(phase=1.8, amp=0.6, neck=0.7, head=(4.0, 1.5), lunge=4.6, mouth=1, eye="squint", glow=1, crackle=2, hdir=10, seed=4),
             E(phase=2.0, amp=1.0, neck=0.9, head=(1.5, 0.5), lunge=2.0, mouth=1, glow=1),
             E(phase=2.2, amp=1.1, neck=1.0)]
    # DISCHARGE: coils tight, charge builds (crackle grows), FLASH (RELEASE f4), sparks fade
    dis = [E(phase=0.4, amp=1.4, neck=1.2, coil=0.3, glow=2, crackle=1, seed=1, head=(-1, -1)),
           E(phase=0.8, amp=1.6, neck=1.3, coil=0.6, glow=2, crackle=2, seed=2, head=(-2, -2), eye="wide"),
           E(phase=1.2, amp=1.8, neck=1.4, coil=0.8, glow=2, crackle=3, seed=3, head=(-2, -2.5), eye="wide", mouth=1),
           E(phase=1.6, amp=1.8, neck=1.4, coil=0.9, glow=2, crackle=4, seed=4, head=(-2, -3), eye="wide", mouth=2),
           E(phase=2.0, amp=1.2, neck=1.5, coil=0.4, glow=2, crackle=6, seed=5, head=(0, -3.5), eye="wide", mouth=3),
           E(phase=2.4, amp=1.2, neck=1.3, coil=0.3, glow=2, crackle=3, seed=6, head=(0, -2), mouth=2),
           E(phase=2.8, amp=1.2, neck=1.1, glow=1, crackle=1, seed=7, mouth=1), E(phase=3.2, amp=1.2, neck=1.0)]
    death = [E(phase=1.0, amp=2.2, neck=1.5, head=(-3, -2), mouth=3, eye="wide", glow=2, crackle=3, hdir=-70, seed=9),
             E(phase=1.6, amp=1.6, neck=0.6, head=(2, 2), mouth=2, eye="squint", glow=1, crackle=1, hdir=40),
             E(phase=2.2, amp=1.0, neck=0.1, head=(3, 1), mouth=1, eye="dead", glow=0, hdir=20),
             E(spine=[(-19, -1.5), (-14, -2.0), (-9, -1.4), (-4, -2.2), (1, -1.6), (5, -1.8), (8, -2.0), (11, -2.2), (14, -2.0)],
               mouth=1, eye="dead", glow=0, hdir=10)]
    knock = E(phase=0.8, amp=1.8, neck=1.3, head=(-3.5, -1.0), lunge=-1.5, mouth=1, eye="squint", glow=2, crackle=1, hdir=-40)
    anims = [("Idle", idle, [0.22, 0.18, 0.22, 0.18]), ("Run", run, [0.08] * 6),
             ("Shock", shock, [0.14, 0.12, 0.06, 0.07, 0.14, 0.12, 0.14]),
             ("Discharge", dis, [0.12, 0.14, 0.14, 0.12, 0.08, 0.12, 0.12, 0.14])]
    anims += stone_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    sheet("BelStormEel", anims, outdir)
    NOTES["BelStormEel"] = {"jaw": eel(phase=1.6, amp=0.5, neck=0.65, head=(4.5, 1.5), lunge=5.0, mouth=1, hdir=12, length=1.06)[1]}


# ================================================================== SLIME HAG (T3, Brine Lamprey line)
def hag_path(dx=0.0, dy=0.0, knot=1.0, phase=0.0, head=(0.0, 0.0), lunge=0.0, rise=1.0, tail=0.0):
    """Tail -> loop (the knot) -> neck -> head. knot 1 = a full loop at the middle, 0 = loosened to an S."""
    k = knot
    w = math.sin(phase) * 0.8
    pts = [(dx - 17 + tail, -2.0 + w * 0.5), (dx - 12, -2.4 - w * 0.4), (dx - 6.5, -2.6 + w * 0.3),
           (dx - 2.0 + lunge * 0.2, -4.0 - 4.0 * k), (dx - 4.5 + lunge * 0.2, -9.0 - 3.0 * k), (dx - 8.0 * k - 1.0 + lunge * 0.2, -6.0 - 1.0 * k),
           (dx - 4.0 * k + lunge * 0.3, -2.8), (dx + 2.0 + lunge * 0.6, -2.6 + w * 0.3),
           (dx + 6.0 + lunge * 0.9 + head[0] * 0.5, -5.0 - 3.0 * rise + head[1] * 0.5 + dy),
           (dx + 9.5 + lunge + head[0], -8.0 - 3.0 * rise + head[1] + dy)]
    return pts


def hag(path=None, mouth=0, drip=0, glow=1, barb=0.0, hdir=None, dark=False, spew=0, **kw):
    """A hagfish in a knot: pale pink flesh, dark knotted crossing, eyeless blunt head with barbels, slime everywhere."""
    pts = path if path is not None else hag_path(**kw)
    rad = [0.7, 1.5, 2.2, 2.5, 2.5, 2.5, 2.6, 2.7, 2.7, 2.9]
    sp, sr = B.catmull(pts, rad, step=0.7)
    n = len(sp)
    half = int(n * 0.55)
    # first half (tail + loop) and second half (crossing over it toward the head), each outlined on its own
    def body(lo, hi):
        f = Fr()
        tube(f.b, sp[lo:hi], sr[lo:hi], HAG, bias=-0.2)
        for i in range(max(lo, 1), min(hi, n - 1)):
            (x0, y0), (x1, y1) = sp[i - 1], sp[i + 1]
            tl = math.hypot(x1 - x0, y1 - y0) or 1
            nx_, ny_ = -(y1 - y0) / tl, (x1 - x0) / tl
            if ny_ < 0: nx_, ny_ = -nx_, -ny_
            r = sr[i]
            if r > 1.2 and i % 3 == 0: f.b.put(*P(sp[i][0] + nx_ * r * 0.6, sp[i][1] + ny_ * r * 0.6), "Я")
            if r > 1.2 and i % 5 == 3: f.b.put(*P(sp[i][0] - nx_ * r * 0.5, sp[i][1] - ny_ * r * 0.5), "Э")
        return f
    f1 = body(0, half + 1)
    f2 = body(half - 1, n)
    # tail fin
    tx, ty = sp[0]
    for a in (-160, 180, 160): gl(f1.b, tx, ty, tx - 2.6, ty + 2.0 * math.sin(math.radians(a)), "ЮЯ")
    # head on f2
    hx, hy = pts[-1]
    if hdir is None:
        px_, py_ = sp[max(0, n - 4)]
        hdir = math.degrees(math.atan2(hy - py_, hx - px_))
    a = math.radians(hdir)
    ux, uy = math.cos(a), math.sin(a)
    nx_, ny_ = -uy, ux
    ell(f2.b, hx + ux * 0.6, hy + uy * 0.6, 3.6, 2.8, HAG, ang=hdir, bias=0.0)
    mx, my = hx + ux * 3.6, hy + uy * 3.6
    # mouth: a round rasping slit, teeth plates
    if mouth:
        ell(f2.b, mx - ux * 0.4, my - uy * 0.4 + 0.4, 1.0 + 0.4 * mouth, 0.8 + 0.5 * mouth, "ZZЭ")
        for k in (-1, 1): f2.b.put(*P(mx - ux * 0.3 + nx_ * k * (0.8 + 0.3 * mouth), my - uy * 0.3 + ny_ * k * (0.8 + 0.3 * mouth)), "X")
    else:
        f2.b.put(*P(mx - ux * 0.3, my - uy * 0.3), "Э")
    # barbels: two pairs of whiskers at the snout
    for k, (o, ln) in enumerate(((-1.6, 2.6), (-0.4, 2.2), (0.8, 2.4), (1.8, 2.0))):
        bx, by = hx + ux * 2.8 + nx_ * o, hy + uy * 2.8 + ny_ * o
        ba = a + math.radians((o * 22) + barb * (12 if k % 2 else -12))
        gl(f2.g, bx, by, bx + math.cos(ba) * ln, by + math.sin(ba) * ln, "Яб")
    # eyeless: two pale eye spots under the skin
    f2.b.put(*P(hx + ux * 0.6 - nx_ * 1.4, hy + uy * 0.6 - ny_ * 1.4), "б")
    # gill pores (the Lamprey's), glowing slime-green
    gp = []
    for i in range(n - 6, half, -1):
        q = P(*sp[i])
        if math.hypot(q[0] - hx, q[1] - hy) < 3.5: continue
        if gp and abs(q[0] - gp[-1][0]) + abs(q[1] - gp[-1][1]) < 2: continue
        gp.append(q)
        if len(gp) == 5: break
    s1 = f1.done(); s2 = f2.done()
    px = dict(s1.px); px.update(s2.px)
    g = {}
    for k, (x, y) in enumerate(gp): g[(x, y)] = ("г" if k % 2 == 0 else "в") if glow else "Э"
    # slime: drips under the body, a sheen pool on the floor, flecks
    rnd = random.Random(drip * 7 + 1)
    for i in range(2, n - 3, 4):
        x, y = sp[i]
        r = sr[i]
        if y + r + 1 <= -1 and rnd.random() < 0.7:
            L = 1 + (i + drip) % 3
            for j in range(L):
                k = P(x, y + r + 1 + j)
                if k[1] <= 0 and k not in px: g[k] = "в" if j < L - 1 else "г"
    for x in range(int(sp[0][0]) + 2, int(sp[-1][0]) + 2):
        if (x + drip) % 3 != 0: g.setdefault((x, 0), "д" if (x // 2) % 2 else "в")
    for k in range(spew):
        g[P(mx + 2 + k * 1.5, my + (k % 2) - k * 0.2)] = "г" if k % 2 else "в"
    px.update(g)
    return clip0(Spr(px)), (mx, my)


def build_hag(outdir):
    Hh = lambda **k: hag(**k)[0]
    idle = [Hh(phase=0.0, barb=0.0, drip=0), Hh(phase=0.6, barb=0.5, drip=1, rise=1.05), Hh(phase=1.2, barb=1.0, drip=2, rise=1.1),
            Hh(phase=1.8, barb=0.5, drip=3, rise=1.05)]
    run = [Hh(phase=i * math.pi / 3, knot=0.85 + 0.1 * math.sin(i * math.pi / 3), lunge=0.8 * math.sin(i * math.pi / 3),
              tail=math.cos(i * math.pi / 3), barb=math.sin(i), drip=i) for i in range(6)]
    # RASP: rear, open, lunge low (HIT f3: mouth at ~(18, -6)), rasp, let go, settle
    rasp = [Hh(rise=1.4, head=(-2, -1), mouth=1, barb=1.0), Hh(rise=1.6, head=(-3.5, -1.5), mouth=2, barb=1.5, knot=1.1),
            Hh(rise=0.5, head=(4.0, 2.5), lunge=3.0, mouth=3, knot=0.7), Hh(rise=0.3, head=(5.0, 3.0), lunge=4.0, mouth=2, knot=0.6, spew=2),
            Hh(rise=0.35, head=(4.5, 3.0), lunge=3.6, mouth=1, knot=0.65, drip=2), Hh(rise=0.8, head=(1.5, 1.0), lunge=1.5, mouth=1), Hh()]
    # SPEW: knot cinches tight, the head rears, slime gushes (RELEASE f4 at the mouth), knot loosens
    spew = [Hh(knot=1.15, rise=1.2, barb=0.5), Hh(knot=1.35, rise=1.4, head=(-1.5, -1), barb=1.0, mouth=1),
            Hh(knot=1.5, rise=1.6, head=(-2.5, -1.5), barb=1.5, mouth=2, drip=1), Hh(knot=1.55, rise=1.7, head=(-2.5, -2.0), mouth=3, drip=2),
            Hh(knot=1.2, rise=1.3, head=(1.0, -0.5), mouth=3, spew=5, drip=3), Hh(knot=1.1, rise=1.2, head=(0.5, 0), mouth=2, spew=3, drip=4),
            Hh(knot=1.0, rise=1.1, mouth=1, drip=5), Hh()]
    death = [Hh(rise=1.8, head=(-3, -2), mouth=3, knot=1.3), Hh(rise=0.6, head=(2, 2), mouth=2, knot=0.6, glow=0),
             Hh(rise=0.0, head=(3, 3), mouth=1, knot=0.3, glow=0, drip=3),
             Hh(path=[(-17, -1.5), (-12, -1.8), (-7, -1.4), (-3, -2.0), (0, -1.6), (3, -1.8), (6, -1.6), (9, -1.8), (12, -2.0), (15, -2.0)],
                mouth=1, glow=0, hdir=5, drip=5)]
    knock = Hh(rise=1.5, head=(-3.5, -1.0), lunge=-1.5, mouth=1, knot=1.2, barb=1.5)
    anims = [("Idle", idle, [0.22, 0.18, 0.22, 0.18]), ("Run", run, [0.09] * 6),
             ("Rasp", rasp, [0.14, 0.12, 0.06, 0.07, 0.14, 0.12, 0.14]),
             ("Spew", spew, [0.12, 0.14, 0.14, 0.12, 0.08, 0.12, 0.12, 0.14])]
    anims += stone_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    sheet("BelSlimeHag", anims, outdir)
    NOTES["BelSlimeHag"] = {"rasp": hag(rise=0.3, head=(5.0, 3.0), lunge=4.0, mouth=2, knot=0.6)[1],
                            "spew": hag(knot=1.2, rise=1.3, head=(1.0, -0.5), mouth=3)[1]}


# ================================================================== JELLY SIREN (T3, Salt Siren line)
SKIN = "zxMC"


def jelly(dx=0.0, bob=0.0, pulse=0.0, tph=0.0, lash=0.0, arms=((-4.0, -24.0), (5.0, -23.0)), head=(0.0, 0.0), mouth=0,
          eye="open", hair=0.0, glow=1, lings=(), tdrop=0.0, dark=False):
    """The Salt Siren rising out of a pale jellyfish bell; amber lion's-mane tentacles trail to the floor."""
    f = Fr()
    cx, cy = dx, -17.0 + bob
    rx, ry = 8.6 * (1 + pulse * 0.12), 6.4 * (1 - pulse * 0.14)
    # tentacles (behind): eight amber strands from under the margin
    tips = []
    for k in range(8):
        x0 = cx - 6.5 + k * 1.85
        y0 = cy + 0.8
        L = 15.0 + (k % 3) * 1.2 - tdrop * 4
        pts = []
        for j in range(7):
            t = j / 6.0
            sw = math.sin(tph + k * 0.9 + t * 3.0) * 1.4 * t
            lx = lash * t * t * (8 + k * 1.2)
            px_, py_ = x0 + sw + lx - t * 1.5 * (1 - lash), min(-0.5, y0 + t * L - lash * t * t * 7)
            pts.append((px_, py_))
        lay = f.n if k % 2 else f.u
        for (a, b), (c_, d) in zip(pts, pts[1:]):
            gl(lay, a, b, c_, d, "пo" if k % 2 else "oO")
        lay.put(*P(*pts[-1]), "Y")
        tips.append(pts[-1])
    # oral arms: cream ruffles under the bell
    for k in range(3):
        x0 = cx - 2.4 + k * 2.4
        for j in range(5):
            f.u.put(*P(x0 + math.sin(tph + j + k) * 0.8, cy + 1.5 + j), "и" if j % 2 else "W")
    # the bell: translucent dome with a frilled margin and a four-lobed glow inside
    def bellsh(nu, nv, d, l, ch, x, y):
        if d > 0.82: return "з" if l > -0.1 else "ж"
        if (x + y) % 5 == 0 and d < 0.5: return "X"
        return ch
    ell(f.b, cx, cy, rx, ry, JELLY, bias=0.25, vmax=0.25, shader=bellsh)
    for k in range(4):      # four faint gonad crescents inside the bell
        a = math.radians(k * 90 + 20)
        x_, y_ = cx + math.cos(a) * 3.0, cy - 2.2 + math.sin(a) * 1.5
        f.b.put(*P(x_, y_), "И" if glow else "ж"); f.b.put(*P(x_ + 1, y_), "З" if glow else "ж")
    for k in range(-int(rx) + 1, int(rx)):
        f.b.put(*P(cx + k, cy + ry * 0.25 + 1 + (k % 2)), "з" if k % 2 else "и")
    # the siren rising from the bell's crown: torso, head, kelp hair, the Lurefish lure (Salt Siren lineage)
    waist = (cx + 0.2, cy - ry * 0.75)
    sh = (cx + 0.6, waist[1] - 6.0)
    hd = (cx + 1.4 + head[0], sh[1] - 3.6 + head[1])
    tube(f.b, [waist, ((waist[0] + sh[0]) / 2, (waist[1] + sh[1]) / 2), sh], [2.4, 2.0, 2.0], SKIN, bias=0.25)
    for k in range(3): f.b.put(*P(waist[0] - 1 + k, waist[1] - 0.5), "з")
    # far arm (under)
    shb = (sh[0] - 1.6, sh[1] + 0.8)
    hb = (cx + arms[0][0], arms[0][1] + bob)
    (ebx, eby), _ = B.ik(shb[0], shb[1], hb[0], hb[1], 3.6, 3.6, bend=-1)
    tube(f.u, [shb, (ebx, eby), hb], [0.8, 0.7, 0.6], SKIN)
    # head
    ell(f.b, hd[0], hd[1], 2.4, 2.6, SKIN, bias=0.4)
    for k in range(9):
        hx_ = hd[0] - 2.4 - (k % 3) * 0.6 - hair * 0.4
        hy_ = hd[1] - 1.6 + k * 0.9
        f.b.put(*P(hx_, hy_), "Lvl"[k % 3]); f.b.put(*P(hx_ - 1 - hair * 0.3 * (k / 8.0), hy_ + 0.5), "L" if k % 2 else "v")
    for k in range(5): f.b.put(*P(hd[0] - 1.6 + k * 0.8, hd[1] - 2.6 - (k % 2) * 0.4), "Lvl"[k % 3])
    ex, ey = P(hd[0] + 1.1, hd[1] - 0.2)
    if eye == "dead": f.g.put(ex, ey, "x")
    elif eye == "shut": f.g.put(ex, ey, "z")
    else:
        f.g.put(ex, ey, "c")
        if eye == "wide": f.g.put(ex, ey - 1, "Q")
    if mouth:
        for j in range(mouth): f.b.put(ex, ey + 2 + j, "Z")
    stalk = [(hd[0] + 0.8, hd[1] - 2.4), (hd[0] + 2.4 + hair * 0.3, hd[1] - 3.8), (hd[0] + 4.4 + hair * 0.5, hd[1] - 3.6)]
    for (x0, y0), (x1, y1) in zip(stalk, stalk[1:]): line(f.b, x0, y0, x1, y1, "x")
    lx_, ly_ = P(*stalk[-1])
    f.g.put(lx_, ly_ + 1, "c" if glow else "E"); f.g.put(lx_ + 1, ly_ + 1, "Q"); f.g.put(lx_, ly_ + 2, "B" if glow else "d")
    # near arm (over)
    shf = (sh[0] + 1.2, sh[1] + 0.8)
    hf = (cx + arms[1][0], arms[1][1] + bob)
    (efx, efy), _ = B.ik(shf[0], shf[1], hf[0], hf[1], 3.8, 3.8, bend=1)
    tube(f.b, [shf, (efx, efy), hf], [0.8, 0.7, 0.6], SKIN)
    f.b.put(*P(*hf), "C")
    # little jellies being released
    for (lx, ly) in lings:
        ell(f.g, cx + lx, cy + ly, 2.3, 1.8, "жзи", bias=0.4, vmax=0.3)
        f.g.put(*P(cx + lx - 1, cy + ly + 1.5), "O"); f.g.put(*P(cx + lx + 1, cy + ly + 1.5), "o")
    spr = f.done()
    return spr, tips


def build_jelly(outdir):
    J = lambda **k: jelly(**k)[0]
    idle = [J(bob=0.0, pulse=0.0, tph=0.0), J(bob=-0.5, pulse=0.4, tph=0.8, hair=0.5), J(bob=-1.0, pulse=0.7, tph=1.6, hair=1.0),
            J(bob=-0.5, pulse=0.3, tph=2.4, hair=0.5)]
    run = [J(bob=-0.6 * abs(math.sin(i * math.pi / 3)), pulse=0.4 + 0.3 * math.sin(i * math.pi / 3), tph=i * 1.0, hair=1.0 + 0.5 * math.sin(i),
             lash=-0.15, dx=0.0) for i in range(6)]
    # LASH: draws the tentacles back, then whips them forward (HIT f3, tips ~(16, -4)), they trail back
    lash = [J(lash=-0.35, pulse=0.3, arms=((-6, -26), (2, -27)), eye="wide"), J(lash=-0.55, pulse=0.6, arms=((-6, -27), (-1, -29)), eye="wide", bob=-1),
            J(lash=0.6, pulse=-0.2, arms=((-3, -23), (9, -22)), tph=1.0), J(lash=1.0, pulse=-0.3, arms=((-2, -22), (10, -20)), tph=1.4, mouth=1),
            J(lash=0.9, pulse=-0.2, arms=((-2, -22), (9, -21)), tph=1.8), J(lash=0.4, pulse=0.1, tph=2.2), J(tph=2.6)]
    # BROOD: the bell swells and contracts hard, three little jellies drop from under it (RELEASE f4), drift out
    brood_ = [J(pulse=0.5, arms=((-5, -26), (6, -26))), J(pulse=1.0, arms=((-6, -28), (6, -28)), eye="wide", mouth=1, bob=-1),
              J(pulse=1.3, arms=((-6, -29), (7, -29)), eye="wide", mouth=2, bob=-1.5), J(pulse=-0.4, tdrop=0.3, bob=1.0, mouth=2, lings=((0, 6),)),
              J(pulse=-0.5, tdrop=0.2, bob=1.0, lings=((-5, 8), (2, 9), (7, 7))), J(pulse=0.0, lings=((-8, 10), (3, 11), (10, 8))),
              J(pulse=0.3), J()]
    death = [J(pulse=1.0, eye="wide", mouth=2, arms=((-6, -28), (7, -28))), J(pulse=-0.5, bob=4, eye="shut", glow=0, tdrop=0.4),
             J(pulse=-0.8, bob=9, eye="dead", glow=0, tdrop=0.8, arms=((-6, -10), (6, -9))),
             lay_down(J(pulse=-0.9, bob=0, eye="dead", glow=0, tdrop=1.0), deg=-80, squash=0.7)]
    knock = J(pulse=0.6, bob=-1.0, dx=-1.0, eye="shut", lash=-0.6, mouth=1)
    anims = [("Idle", idle, [0.2, 0.18, 0.2, 0.18]), ("Run", run, [0.09] * 6),
             ("Lash", lash, [0.14, 0.14, 0.06, 0.07, 0.14, 0.14, 0.14]),
             ("Brood", brood_, [0.12, 0.14, 0.16, 0.08, 0.12, 0.14, 0.14, 0.14])]
    anims += stone_tail(idle[0], death, [0.1, 0.12, 0.16, 0.4], knock)
    sheet("BelJellySiren", anims, outdir)
    NOTES["BelJellySiren"] = {"lash_tips": jelly(lash=1.0, pulse=-0.3, arms=((-2, -22), (10, -20)), tph=1.4)[1]}


# ================================================================== FX
def cv():
    return Canvas()


def fx_spine_egg():
    """FxBelSpineEgg: the Spinewalker's spined egg. Lay 3 (drops and settles), Idle 4 (pulses, arming), Burst 6
    (cracks, a ring of spines shoots out along the floor to r ~16; damage f1-f3)."""
    def egg(dy=0.0, sq=1.0, glow=0, crack=0, spines=1.0):
        f = Fr()
        cy = -3.0 + dy
        for k in range(10):
            a = 180 + k * 20
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            gl(f.u, ca * 1.8, cy + sa * 1.6, ca * (3.6 + (k % 2) * 1.0) * spines, cy + sa * (3.2 + (k % 2)) * spines, "nNH")
        ell(f.b, 0, cy, 3.0 * sq, 2.6 / sq, EGG, bias=0.35)
        f.b.put(-1, int(round(cy - 1)), "X")
        f.g.put(0, int(round(cy + 0.4)), "q" if not glow else "N")
        if glow: f.g.put(1, int(round(cy)), "И" if glow == 1 else "X")
        if crack:
            for (a, b) in ((-1, -1), (0, 0), (1, -1), (2, 0))[:crack + 1]: f.g.put(a, int(round(cy)) + b, "Z")
        return f.done(clip=False)
    lay = [egg(dy=-5, sq=0.85), egg(dy=0.5, sq=1.25), egg(dy=0, sq=1.0)]
    idle = [egg(glow=0), egg(glow=1, sq=1.04), egg(glow=2, sq=1.08), egg(glow=1, sq=1.04)]
    burst = []
    for i, r in enumerate((3, 7, 11, 14, 16, 17)):
        c = cv()
        ry = r * 0.36 + 0.8
        for k in range(12):
            a = 2 * math.pi * k / 12 + 0.13
            x0, y0 = (r - 3) * math.cos(a), (r - 3) * 0.36 * math.sin(a)
            x1, y1 = r * math.cos(a), ry * math.sin(a)
            if i < 5: gl(c, x0, y0 - 1, x1, y1 - 1, "fHQ" if i < 3 else "xf")
            else:
                if k % 2: c.put(*P(x1, y1 - 1), "x")
        if i < 3:
            ell(c, 0, -2, 3.2 - i, 2.0 - i * 0.5, EGG, bias=0.4)
            for k in range(4 + i * 2):
                a = k * 2.4
                c.put(*P(math.cos(a) * (2 + i), -2 + math.sin(a) * (1 + i)), "И" if k % 2 else "N")
        burst.append(c.spr())
    return lay, idle, burst


def fx_sting():
    """FxBelSting: an anemone's sting landing - pink tendrils lash out, lime venom flecks scatter (4 frames)."""
    out = []
    for i in range(4):
        c = cv()
        n = 7
        for k in range(n):
            a = math.radians(-70 + k * 22)
            L = [3, 6, 7, 5][i] + (k % 2)
            gl(c, 0, -5, math.cos(a) * L, -5 + math.sin(a) * L * 0.9, "ЗИ" if i < 3 else "ЖЗ")
            if i >= 1: c.put(*P(math.cos(a) * (L + 1), -5 + math.sin(a) * (L + 1) * 0.9), "Й" if k % 2 == i % 2 else "г")
        if i == 0: ell(c, 0, -5, 2.0, 2.0, "ИXX", bias=0.5)
        if i >= 2:
            for k in range(5): c.put(*P(3 + k * 1.3, -5 + ((k * 3 + i) % 5) - 2), "Й" if k % 2 else "в")
        out.append(c.spr())
    return out


def fx_thorn():
    """FxBelThorn: a red-tipped indigo thorn (Fly 2, faces right) with a faint trail."""
    out = []
    for i in range(2):
        c = cv()
        tube(c, [(-4, -4), (3, -4)], [1.1, 0.4], STAR, bias=0.3)
        c.put(4, -4, "R"); c.put(3, -4, "r")
        for k in range(3): c.put(-6 - k * 1 - i, -4 + (k + i) % 2 * (1 if k % 2 else -1), "Ф" if k == 0 else "П")
        out.append(Spr(B.outl(c.spr()).px))
    return out


def fx_thorn_patch():
    """FxBelThornPatch: thorns jammed in the floor - grows (2), bristles (alternating 4), falls apart (2). 8 frames."""
    def patch(h=1.0, ph=0, fade=0.0):
        c = cv()
        rnd = random.Random(5)
        for k in range(9):
            x = rnd.uniform(-9, 9); y = rnd.uniform(-1.5, 1.5)
            if fade and rnd.random() < fade: continue
            ln = (2.5 + rnd.uniform(0, 2.5)) * h
            lean = rnd.uniform(-1.2, 1.2) + (0.4 if (k + ph) % 2 else -0.4) * (h > 0.6)
            gl(c, x, y, x + lean, y - ln, "ПФЦ")
            c.put(*P(x + lean, y - ln - 1), "R")
        for k in range(10):
            x = -9 + k * 2; y = (k % 3) - 1
            if not fade or k % 2: c.put(*P(x, y), "Л" if k % 2 else "к")
        return c.spr()
    return [patch(0.3), patch(0.7), patch(1.0, 0), patch(1.0, 1), patch(1.0, 0), patch(1.0, 1), patch(0.8, 0, 0.4), patch(0.5, 1, 0.75)]


def fx_brood_spine():
    """FxBelBroodSpine: a violet spine with a pink egg-sac blob at its base (Fly 2, faces right)."""
    out = []
    for i in range(2):
        c = cv()
        gl(c, -3, -4, 4, -4, "nNHH")
        c.put(5, -4, "Q")
        ell(c, -3.5, -4, 1.6, 1.3, EGG, bias=0.4)
        for k in range(3): c.put(-6 - k - i, -4 + ((k + i) % 2), "З" if k == 0 else "Ж")
        out.append(Spr(B.outl(c.spr()).px))
    return out


def fx_mortar():
    """FxBelMortar: the brood egg falls on a marked spot. f0-f4: a pink target ring grows on the floor and the egg
    drops in from high above; f5 IMPACT (spines burst, r ~14); f6-f8 pink splatter fades. Ground origin."""
    out = []
    for i in range(9):
        c = cv()
        if i <= 5:
            r = 6 + i * 1.6
            ry = r * 0.36 + 0.6
            for k in range(int(r * 4)):
                a = 2 * math.pi * k / int(r * 4)
                if (k + i) % 3 == 0: continue
                c.put(*P(r * math.cos(a), ry * math.sin(a)), "З" if i < 4 else "И")
            c.put(0, 0, "Ж")
        if i <= 4:
            h = [40, 30, 20, 11, 4][i]
            ell(c, 0, -h - 2, 2.4, 2.0 + (0.6 if i >= 3 else 0), EGG, bias=0.35)
            for k in range(1, 4): c.put(0, -h + 1 - k * 2 - 2, "З" if k == 1 else "Ж")
            for k in range(6):   # a few spines on the egg
                a = math.radians(180 + k * 36)
                gl(c, math.cos(a) * 2, -h - 2 + math.sin(a) * 1.8, math.cos(a) * 3.6, -h - 2 + math.sin(a) * 3.2, "nH")
            sw = 1.0 + (4 - i) * 0.3
            ell(c, 0, 0, 2.2 / sw + 1, 0.8, "Ж", bias=0)
        if i == 5 or i == 6:
            r = 14 if i == 5 else 16
            for k in range(14):
                a = 2 * math.pi * k / 14
                gl(c, 3 * math.cos(a), -1 + 1.2 * math.sin(a), r * math.cos(a), -1 + r * 0.36 * math.sin(a), "ИfH" if i == 5 else "Зx")
            if i == 5: ell(c, 0, -2, 4.0, 3.0, "ИXX", bias=0.5)
            for k in range(8):
                a = k * 0.8
                c.put(*P(math.cos(a) * 5, -4 - abs(math.sin(a)) * (6 if i == 5 else 9)), "И" if k % 2 else "Й")
        if i >= 6:
            rnd = random.Random(3)
            for k in range(14 - (i - 6) * 4):
                x = rnd.uniform(-12, 12); y = rnd.uniform(-2.5, 2.0)
                c.put(*P(x, y), "З" if k % 3 else "И")
                if i < 8: c.put(*P(x + 1, y), "Ж")
        out.append(c.spr())
    return out


def fx_sting_aura():
    """FxBelStingAura: one pulse of the Colossus' sting ring (r 30 on the floor), tendrils flicking up. 5 frames."""
    out = []
    for i, r in enumerate((14, 22, 28, 31, 32)):
        c = cv()
        ry = r * 0.36 + 0.8
        n = int(r * 3)
        for k in range(n):
            a = 2 * math.pi * k / n
            if i >= 3 and (k // 2) % 3 == 0: continue
            x, y = r * math.cos(a), ry * math.sin(a)
            c.put(*P(x, y), "И" if i < 2 else "З" if i < 4 else "Ж")
            c.put(*P(x * 0.9, y * 0.85), "З" if i < 3 else "Ж", over=False)
        for k in range(10):
            a = 2 * math.pi * (k + 0.5) / 10
            x, y = r * math.cos(a), ry * math.sin(a)
            hgt = [3, 5, 6, 4, 2][i]
            gl(c, x, y, x + math.cos(a) * 1.2, y - hgt, "ЗИЙ")
        out.append(c.spr())
    return out


def fx_counter():
    """FxBelCounter: the Champion's counterpunch - a parry flash, then an orange coral burst and lime sting flecks."""
    out = []
    for i in range(5):
        c = cv()
        cy = -14
        if i == 0:
            for k in range(8):
                a = math.radians(k * 45)
                gl(c, math.cos(a) * 1.5, cy + math.sin(a) * 1.5, math.cos(a) * 5, cy + math.sin(a) * 5, "yYO")
            ell(c, 0, cy, 1.6, 1.6, "yy", bias=0.5)
        else:
            r = [0, 4, 8, 11, 13][i]
            for k in range(10):
                a = math.radians(-60 + k * 13)
                x0, y0 = math.cos(a) * (r - 3), cy + math.sin(a) * (r - 3)
                x1, y1 = math.cos(a) * r, cy + math.sin(a) * r
                gl(c, x0, y0, x1, y1, "OY" if i < 3 else "ao")
            for k in range(4):
                c.put(*P(3 + k * 2.5 + i, cy - 3 + (k * 5 + i) % 7), "Й" if k % 2 else "И")
            if i < 3: ell(c, 3, cy, 3.0 - i * 0.6, 3.0 - i * 0.6, "OYy", bias=0.5)
        out.append(c.spr())
    return out


def fx_march_ring():
    """FxBelMarchRing: one step of the Belltower's marching peal - a bronze ring slams out of the floor (r 4..11)."""
    out = []
    for i, r in enumerate((4, 8, 11, 12, 12)):
        c = cv()
        ry = r * 0.4 + 0.8
        n = int(r * 6)
        for k in range(n):
            a = 2 * math.pi * k / n
            if i >= 3 and (k // 2) % 3 == 0: continue
            x, y = r * math.cos(a), ry * math.sin(a)
            c.put(*P(x, y), "w" if i < 2 else "e" if i < 4 else "A")
            c.put(*P(x * 0.86, y * 0.8), "e" if i < 2 else "A", over=False)
        h = [6, 9, 7, 3, 0][i]
        for sd in (-1, 1):
            for k in range(3):
                c.put(*P(sd * (r * 0.45 + 1 + k * 0.6), -ry - 1 - h * 0.4 - k * 1.2), "X" if i < 2 else "w", over=False)
        if i <= 1:
            ell(c, 0, -2, 2.0 + i, 1.4, "ewX", bias=0.4)
            gl(c, 0, -2, 0, -h - 2, "ewX")
        out.append(c.spr())
    return out


def fx_shock_ring():
    """FxBelShockRing: the Storm Eel's discharge around itself: a crackling yellow ring (r 10..26) of forked bolts."""
    out = []
    for i, r in enumerate((10, 17, 23, 26, 26)):
        c = cv()
        rnd = random.Random(i * 7 + 2)
        ry = r * 0.4 + 1
        n = 16
        prev = None
        for k in range(n + 1):
            a = 2 * math.pi * k / n
            x, y = r * math.cos(a) + rnd.uniform(-1.5, 1.5), ry * math.sin(a) - 3 + rnd.uniform(-1.5, 1.5)
            if prev and not (i >= 3 and k % 3 == 0):
                gl(c, prev[0], prev[1], x, y, "y" if i < 2 else "Yo" if i < 4 else "o")
            prev = (x, y)
        if i < 3:
            for k in range(6):
                a = rnd.uniform(0, 2 * math.pi)
                x0, y0 = 2 * math.cos(a), -3 + 1.5 * math.sin(a)
                x1, y1 = r * 0.7 * math.cos(a), -3 + ry * 0.7 * math.sin(a) - rnd.uniform(0, 4)
                mx, my = (x0 + x1) / 2 + rnd.uniform(-2, 2), (y0 + y1) / 2 + rnd.uniform(-2, 2)
                gl(c, x0, y0, mx, my, "cy"); gl(c, mx, my, x1, y1, "yY")
            ell(c, 0, -3, 2.5 - i * 0.6, 2.0 - i * 0.5, "yc", bias=0.5)
        out.append(c.spr())
    return out


def fx_spark_pool():
    """FxBelSparkPool: an electrified brine pool - sparks crawl over it and arcs snap up (8 frames, 2.4 s live)."""
    out = []
    for i in range(8):
        c = cv()
        rnd = random.Random(i * 5 + 1)
        live = 1 <= i <= 6
        rx, ry = 12, 3.4
        for k in range(18 if live else 8):
            a = rnd.uniform(0, 2 * math.pi); rr = rnd.uniform(0.2, 1.0)
            x, y = rx * rr * math.cos(a), -1 + ry * rr * math.sin(a)
            c.put(*P(x, y), "y" if k % 3 == 0 else "Y" if live else "o")
            if live and k % 2 == 0: c.put(*P(x + rnd.choice((-1, 1)), y + rnd.choice((-1, 0))), "c")
        if live:
            for k in range(2):
                x = rnd.uniform(-9, 9)
                h = rnd.uniform(5, 9)
                px_, py_ = x, -1
                for j in range(4):
                    nx_, ny_ = x + rnd.uniform(-1.5, 1.5), -1 - h * (j + 1) / 4
                    gl(c, px_, py_, nx_, ny_, "Yy" if j < 3 else "c")
                    px_, py_ = nx_, ny_
        for k in range(-rx, rx + 1, 3):
            c.put(*P(k, -1 + (ry if k % 2 else -ry) * math.sqrt(max(0, 1 - (k / rx) ** 2))), "o" if live else "п", over=False)
        out.append(c.spr())
    return out


def fx_slime_glob():
    """FxBelSlimeGlob: a wobbling glob of hagfish slime (Fly 4, faces right), strings trailing."""
    out = []
    for i in range(4):
        c = cv()
        sq = [1.0, 1.15, 1.0, 0.88][i]
        ell(c, 0, -4, 2.6 * sq, 2.2 / sq, "двгг", bias=0.4)
        c.put(-1, -5, "X")
        for k in range(4): c.put(-3 - k, -4 + ((k + i) % 3) - 1, "в" if k < 2 else "д")
        out.append(Spr(B.outl(c.spr(), "д").px))
    return out


def fx_slime_pool():
    """FxBelSlimePool: a sticky slime puddle that roots (Life 9: spreads 2, gleams 5, dries 2)."""
    def pool(spread=1.0, ph=0, fade=0.0):
        c = cv()
        lobes = [(0, 0, 10.0, 2.8), (-6, 0.3, 5.0, 2.2), (5.5, -0.2, 5.5, 2.4), (-1.5, -0.6, 6.5, 3.0)]
        inside = {}
        for (lx, ly, rx, ry) in lobes:
            rx, ry = rx * spread, max(1.0, ry * (0.5 + 0.5 * spread))
            for y in range(int(-ry) - 1, int(ry) + 2):
                for x in range(int(lx * spread - rx) - 1, int(lx * spread + rx) + 2):
                    d = ((x - lx * spread) / rx) ** 2 + ((y - ly) / ry) ** 2
                    if d <= 1.0: inside[(x, y)] = min(inside.get((x, y), 9), d)
        for (x, y), d in inside.items():
            if fade and ((x * 7 + y * 13) % 10) / 10.0 < fade: continue
            edge = any((x + a, y + b) not in inside for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            ch = ("г" if y < 0 else "в") if edge else ("в" if (x + y * 2 + ph) % 6 == 0 else "д")
            if not edge and (x * 3 + y * 5 + ph) % 13 == 0: ch = "г"
            c.put(x, y - 3, ch)
        if fade < 0.5:
            for k in range(3):
                x = -6 + k * 6 + ph
                c.put(*P(x, -4), "X"); gl(c, x, -5, x, -6 - (k + ph) % 2, "г")
        return c.spr()
    return [pool(0.4, 0), pool(0.8, 1), pool(1.0, 0), pool(1.0, 1), pool(1.0, 2), pool(1.0, 1), pool(1.0, 0), pool(0.9, 1, 0.45), pool(0.8, 0, 0.8)]


def fx_jellyling():
    """FxBelJellyling: a little drifting jellyfish (Fly 4: the bell pulses, tentacles stream behind)."""
    out = []
    for i in range(4):
        f = Fr()
        p = [0.0, 0.3, 0.0, -0.25][i]
        for k in range(4):
            x0 = -2.2 + k * 1.5
            for j in range(5):
                f.n.put(*P(x0 + math.sin(i + k + j) * 0.6 - j * 0.3, -5.5 + j), "O" if j < 2 else "o" if j < 4 else "п")
        ell(f.b, 0, -7, 3.4 * (1 + p * 0.2), 2.8 * (1 - p * 0.2), "жзии", bias=0.35, vmax=0.3)
        f.g.put(-1, -8, "X"); f.g.put(0, -7, "И" if i % 2 else "З")
        out.append(f.done(clip=False))
    return out


def fx_jelly_pop():
    """FxBelJellyPop: a jellyling bursting on the hero - a pale membrane flash, amber stinging threads (4 frames)."""
    out = []
    for i in range(4):
        c = cv()
        r = [2, 5, 7, 8][i]
        for k in range(10):
            a = 2 * math.pi * k / 10
            gl(c, math.cos(a) * (r - 2), -6 + math.sin(a) * (r - 2) * 0.8, math.cos(a) * r, -6 + math.sin(a) * r * 0.8,
               "иX" if i < 2 else "зж")
            if i >= 1: c.put(*P(math.cos(a + 0.3) * (r - 1), -6 + math.sin(a + 0.3) * (r - 1)), "O" if k % 2 else "o")
        if i == 0: ell(c, 0, -6, 2.6, 2.2, "иXX", bias=0.5)
        out.append(c.spr())
    return out


FX_NOTES = {
    "FxBelSpineEgg": "Spinewalker egg mine. `Lay` (3) then `Idle` (4, loop) = ModBelSpineEgg (inert, arms after 0.6 s); `Burst` (6) = "
                     "ModBelEggBurst (ground ring r 16, damage f1-f3), spawned when the hero comes within 18 px or after 7 s.",
    "FxBelSting": "Anemone Boxer sting landing (Play 4): ModBoxerStingFx, attached at the glove on each jab hit.",
    "FxBelThorn": "Crown of Thorns thorn (Fly 2, faces right): ModThornShot (Shed fan, rolls along the floor; art 4 px up) and ModThornBack (Thorns passive).",
    "FxBelThornPatch": "Crown of Thorns thorn patch (Life 8, 2.9 s): ModThornPatch ground hazard 20 x 8, damage f1-f6 every 0.5 s + bleed.",
    "FxBelBroodSpine": "Brood Urchin spray spine (Fly 2, faces right): ModBroodSpine.",
    "FxBelMortar": "Brood Urchin mortar (Fall 9): ModBroodMortar spawned at the hero; f0-f4 target ring + falling egg (0.5 s warning), "
                   "f5 IMPACT damage f5-f6 (ring r 14), f6-f8 splatter.",
    "FxBelStingAura": "Anemone Colossus sting pulse (Play 5): ModColossusPulse at its feet, ring r 30, damage f1-f3 + poison.",
    "FxBelCounter": "Reef Champion counterpunch (Play 5): ModChampionCounter (parry flash f0, coral burst f1-f4), damage f1-f2.",
    "FxBelMarchRing": "Belltower Hermit marching peal step (Play 5): ModBelltowerRing, ground ring r 12, damage f0-f2.",
    "FxBelShockRing": "Storm Eel discharge around itself (Play 5): ModEelShockRing, ring r 26, damage f1-f3 + daze.",
    "FxBelSparkPool": "Storm Eel electrified brine pool (Life 8, 2.4 s): ModEelSparkPool on each brine pool, 24 x 8, damage f1-f6 every 0.4 s.",
    "FxBelSlimeGlob": "Slime Hag slime glob (Fly 4): ModHagGlob, lobbed along the floor (art 4 px up), lands as ModHagSlime.",
    "FxBelSlimePool": "Slime Hag slime puddle (Life 9, 3.1 s): ModHagSlime root zone (StatusStuckToFloor -> the mod's 0.8 s root).",
    "FxBelJellyling": "Jelly Siren jellyling (Fly 4): ModJellyling, drifts 50 px/s and steers at the hero for 4 s.",
    "FxBelJellyPop": "Jelly Siren jellyling popping on contact (Play 4): ModJellyPop.",
}
FX_ORDER = list(FX_NOTES)


def build_fx(outdir, only=None):
    def want(n): return only is None or n in only
    if want("FxBelSpineEgg"):
        lay, idle, burst = fx_spine_egg()
        fx_sheet("FxBelSpineEgg", [("Lay", lay, [0.08, 0.08, 0.1]), ("Idle", idle, [0.16] * 4),
                                   ("Burst", burst, [0.04, 0.05, 0.05, 0.06, 0.07, 0.08])], outdir)
    if want("FxBelSting"): fx_sheet("FxBelSting", [("Play", fx_sting(), [0.04, 0.05, 0.06, 0.08])], outdir)
    if want("FxBelThorn"): fx_sheet("FxBelThorn", [("Fly", fx_thorn(), [0.06, 0.06])], outdir, scale=8)
    if want("FxBelThornPatch"):
        fx_sheet("FxBelThornPatch", [("Life", fx_thorn_patch(), [0.08, 0.1, 0.5, 0.5, 0.5, 0.5, 0.35, 0.35])], outdir)
    if want("FxBelBroodSpine"): fx_sheet("FxBelBroodSpine", [("Fly", fx_brood_spine(), [0.06, 0.06])], outdir, scale=8)
    if want("FxBelMortar"):
        fx_sheet("FxBelMortar", [("Fall", fx_mortar(), [0.12, 0.1, 0.1, 0.1, 0.08, 0.06, 0.08, 0.1, 0.12])], outdir, scale=5)
    if want("FxBelStingAura"): fx_sheet("FxBelStingAura", [("Play", fx_sting_aura(), [0.06, 0.07, 0.08, 0.09, 0.1])], outdir, scale=4)
    if want("FxBelCounter"): fx_sheet("FxBelCounter", [("Play", fx_counter(), [0.06, 0.05, 0.06, 0.07, 0.08])], outdir)
    if want("FxBelMarchRing"): fx_sheet("FxBelMarchRing", [("Play", fx_march_ring(), [0.05, 0.06, 0.07, 0.08, 0.09])], outdir)
    if want("FxBelShockRing"): fx_sheet("FxBelShockRing", [("Play", fx_shock_ring(), [0.05, 0.06, 0.07, 0.08, 0.09])], outdir, scale=4)
    if want("FxBelSparkPool"): fx_sheet("FxBelSparkPool", [("Life", fx_spark_pool(), [0.1, 0.4, 0.4, 0.4, 0.4, 0.4, 0.3, 0.1])], outdir)
    if want("FxBelSlimeGlob"): fx_sheet("FxBelSlimeGlob", [("Fly", fx_slime_glob(), [0.07] * 4)], outdir, scale=8)
    if want("FxBelSlimePool"):
        fx_sheet("FxBelSlimePool", [("Life", fx_slime_pool(), [0.08, 0.1, 0.5, 0.5, 0.5, 0.5, 0.5, 0.25, 0.2])], outdir)
    if want("FxBelJellyling"): fx_sheet("FxBelJellyling", [("Fly", fx_jellyling(), [0.1] * 4)], outdir, scale=8)
    if want("FxBelJellyPop"): fx_sheet("FxBelJellyPop", [("Play", fx_jelly_pop(), [0.04, 0.05, 0.06, 0.08])], outdir)


MONSTERS = [("BelSpinewalker", build_spinewalker), ("BelBoxer", build_boxer), ("BelCrownThorns", build_crown),
            ("BelBrood", build_brood), ("BelColossus", build_colossus), ("BelChampion", build_champion),
            ("BelBelltower", build_belltower), ("BelStormEel", build_eel), ("BelSlimeHag", build_hag),
            ("BelJellySiren", build_jelly)]

# sync frames (TIMING.md): sheet -> [(anim, frame, moment, spawn point from the feet, x fwd / y up NEGATIVE)]
EVENTS = {
    "BelSpinewalker": [("Stab", 3, "HIT: the stilt spears the floor", "(16, -1); hitbox (13, 4) 12 x 10"),
                       ("Sow", 4, "RELEASE: the egg sac drops - 3 ModBelSpineEgg around it", "(15, 0), (-12, 5), (2, -10) Position")],
    "BelBoxer": [("Jab", 2, "HIT 1: near glove", "(17, -13): box (14, 11) 14 x 12, FxBelSting at (17, -8)"),
                 ("Jab", 4, "HIT 2: far glove crosses over (poisons)", "(14, -12.5)"),
                 ("Flurry", 2, "HIT: near jab", "(15, -11)"), ("Flurry", 4, "HIT: near jab", "(15, -10)"),
                 ("Flurry", 6, "HIT: near jab (poisons)", "(15, -12)")],
    "BelCrownThorns": [("Lash", 3, "HIT: the right arm sweeps down through the hero", "tip (14, -8): box (13, 9) 20 x 16"),
                       ("Shed", 3, "RELEASE: three thorns fan out (-18, 0, 18 deg), rolling on the floor", "(12, -1) floor, art 4 px up")],
    "BelBrood": [("Spray", 3, "RELEASE: three spines from the maw (-16, 0, 16 deg)", "maw (11, -9)"),
                 ("Mortar", 3, "RELEASE: the egg is hurled up; three FxBelMortar land on the hero and two spots beside", "hero (0, 0), (-18, 6), (18, -6)")],
    "BelColossus": [("Hammer", 3, "HIT: both pincers slam the floor", "pincers land x 17-24: box (15, 6) 24 x 14"),
                    ("Bloom", 3, "AURA: 6 sting pulses, one every 0.5 s (ModColossusPulse at the feet)", "(0, 0)")],
    "BelChampion": [("Uppercut", 3, "HIT: the near gauntlet drives up", "gauntlet (13, -29), tip (14, -36): box (14, 15) 14 x 24"),
                    ("Guard", 1, "GUARD on (takes no damage; the first hero hit is countered)", "-"),
                    ("Guard", 7, "GUARD off", "-")],
    "BelBelltower": [("Crush", 3, "HIT: crusher claw snaps", "tip (24, -2): box (17, 4) 20 x 12"),
                     ("March", 3, "RELEASE: 5 peals march from (14, 0) toward the hero, 14 px apart, 0.12 s apart", "(14, 0)")],
    "BelStormEel": [("Shock", 3, "HIT: shocking bite", "jaws (24, -8): box (17, 8) 16 x 12"),
                    ("Discharge", 4, "RELEASE: shock ring around it + every brine pool within 130 px sparks for 2.4 s", "(0, 0)")],
    "BelSlimeHag": [("Rasp", 3, "HIT: rasping bite", "mouth (22, -7): box (16, 7) 16 x 12"),
                    ("Spew", 4, "RELEASE: three slime globs (-20, 0, 20 deg) land as root puddles", "mouth (12, -16) -> floor (12, 0)")],
    "BelJellySiren": [("Lash", 3, "HIT: tentacles whip forward", "tips (12..20, -2..-8): box (14, 5) 20 x 12"),
                      ("Brood", 4, "RELEASE: three jellylings drop from under the bell and steer at the hero", "(2, -8)")],
}


def timing_lines():
    L = ["", "## v0.10 tree: ten new monsters (belmora_tree.py, drawn at final size; no ArtScale entries)", "",
         "| Sheet | Cell (w x h) | Feet | Anims (frames) |", "|---|---|---|---|"]
    for n, _ in MONSTERS:
        if n not in BUILT: continue
        b = BUILT[n]; cw, ch = b["cell"]
        L.append("| %s | %d x %d | (%d, %d) | %s |" % (n, cw, ch, cw // 2, ch - 2, ", ".join("%s %d" % (a, k) for a, k, d in b["anims"])))
    L += ["", "### Sync frames", ""]
    for n, _ in MONSTERS:
        if n not in BUILT: continue
        anims = {a: (k, d) for a, k, d in BUILT[n]["anims"]}
        for an in sorted({e[0] for e in EVENTS[n]}, key=lambda a: [e[0] for e in EVENTS[n]].index(a)):
            k, d = anims[an]
            L += ["#### %s / `%s`: %d frames, %.2f s" % (n, an, k, sum(d)), "Durations: " + ", ".join("%.2f" % x for x in d), "",
                  "| Frame | t (s) | Moment | Spawn point |", "|---|---|---|---|"]
            for (a2, fi, ev, sp) in EVENTS[n]:
                if a2 != an: continue
                L.append("| %d | %.2f | %s | %s |" % (fi, sum(d[:fi]), ev, sp))
            L.append("")
    L += ["### v0.10 effect sheets", "", "| Sheet | Cell | Origin | Anims | Notes |", "|---|---|---|---|---|"]
    for n in FX_ORDER:
        if n not in BUILT: continue
        b = BUILT[n]; cw, ch = b["cell"]
        L.append("| %s | %d x %d | (%d, %d) | %s | %s |" % (n, cw, ch, b["feet"][0], b["feet"][1],
                 ", ".join("%s %d, %.2f s" % (a, k, sum(d)) for a, k, d in b["anims"]), FX_NOTES[n]))
    L += ["", "### v0.10 lineage fixes (one parent each)",
          "- BelDiver (Bell Urchin): the red crab-claw back hand is now a canvas glove studded with violet urchin spines.",
          "- BelSiren (Lurefish): the urchin spines in her hair are now the Lurefish's teal fin crest.",
          "- BelDrownedBell (Bell Diver): the Hermit's crusher claw front hand is now a brass-cuffed diving gauntlet.",
          "- BelCaptain (Bell Diver): the Siren's lure on the hat brim is now a short iron chain.",
          "- BelKraken (Bell Hermit): the Lamprey's sucker is now a black hooked beak.", ""]
    return L


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    only = None
    if "--only" in a:
        i = a.index("--only"); only = set(a[i + 1].split(",")); del a[i:i + 2]
    outdir = a[0] if a else DEFAULT_OUT
    os.makedirs(outdir, exist_ok=True)
    for n, fn in MONSTERS:
        if only is None or n in only: fn(outdir)
    if only is None or only & set(FX_ORDER):
        build_fx(outdir, None if only is None else only & set(FX_ORDER))
    for k, v in NOTES.items(): print("  %s: %s" % (k, v))


if __name__ == "__main__":
    main()
