"""SILVER UNIQUES: the three tier-3 silver monsters reached ONLY through the silver ghost's tier-3 orb upgrade,
and every effect sheet they use. Drawn at final size (no design scale), Crawl's vanilla style (1 px dark outline,
top-left light, readable on a dark floor).

    python3 tools/sprites/silver_rigs.py [outdir] [--only Name,Name]

Their shared "silver spirit" identity (distinct from every god): neutral moonlit silver plate / hide with hard white
specular glints, a night-navy outline, cream moonlight and a pale mint spectral glow, ghostly dithered wisps where the
body fades, and a crescent-moon motif on each of them.

  SilMoonwarden   common A  a hollow silver knight with a moon-disc face, a crescent halo and a crescent glaive.
                            Its moon waxes over its head (New -> Full, 2 s a step); Moonfall drops the moon on the
                            hero, bigger the fuller it is; at Full its sweeps also throw a crescent wave.
  SilCometStag    common B  a spectral silver stag with crescent-moon antlers and a comet-tail mane. Comet: it
                            becomes a streak of starlight that rebounds off walls (3 bounces). Running straight for
                            1 s charges its antlers (next gore bursts).
  SilAstrarch     legendary a floating star-reader: silver mask with one star eye, astrolabe halo, a cape that is
                            a window into the night sky. Starshots leave stars on the floor; Constellation joins
                            them and starfall rains on everything inside the shape.
"""
import math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import belmora_rigs as B          # noqa: E402  (primitives + sheet writer; its palette chars are not used here)
from rig import Canvas, line_px   # noqa: E402
from anim import Spr, PALETTE     # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "art/out_silver")
DUMP = os.environ.get("CRAWL_DUMP", os.path.join(os.path.dirname(os.path.dirname(HERE)), "build", "dump"))

ell, tube, poly, P, pick = B.ell, B.tube, B.poly, B.P, B.pick

# ------------------------------------------------------------------ palette (this pack only; Greek letters)
PALETTE.update({
    'α': (0x17, 0x17, 0x22),   # night outline
    'β': (0x2e, 0x30, 0x3e),   # gunmetal shadow
    'γ': (0x4e, 0x53, 0x62),   # dark silver
    'δ': (0x78, 0x7d, 0x8c),   # silver mid
    'ε': (0xa2, 0xa6, 0xb2),   # silver
    'ζ': (0xcc, 0xcf, 0xd6),   # light silver
    'η': (0xee, 0xef, 0xf3),   # polish
    'θ': (0xff, 0xff, 0xff),   # specular
    'μ': (0xe6, 0xdf, 0xc4),   # moon cream
    'ν': (0xfb, 0xf6, 0xe0),   # moon bright
    'ξ': (0xa8, 0xa2, 0x8a),   # moon shadow (maria)
    'ο': (0x6e, 0x6a, 0x5a),   # moon dark side
    'π': (0x6c, 0xd6, 0xbe),   # spectral mint
    'ρ': (0xbc, 0xfa, 0xea),   # spectral bright
    'ς': (0x3e, 0x86, 0x7a),   # spectral deep
    'σ': (0x14, 0x16, 0x30),   # night sky deep
    'τ': (0x22, 0x26, 0x4e),   # night sky
    'υ': (0x36, 0x3c, 0x74),   # night sky light
    'φ': (0x58, 0x60, 0xa4),   # dusk rim
    'χ': (0xff, 0xf8, 0xd8),   # star
    'ψ': (0x0c, 0x0c, 0x14),   # void (visor slits)
    'ω': (0x62, 0x68, 0x80),   # cloth grey-blue
    'Ω': (0x8a, 0x90, 0xa8),   # cloth light
})
OUT = 'α'
SIL = "βγδεζη"          # plate ramp dark -> light
SILD = "αβγδε"          # far-side plate (dimmer)
MOON = "οξμν"
CLOTH = "βγωΩ"
NIGHT = "στυφ"
GLOW = "ςπρ"
HIDE = "γδεζη"         # stag hide
HIDED = "βγδε"


# ------------------------------------------------------------------ frame with the silver outline
class Fr:
    """Layers: n = far (no outline), u = under (outlined, behind), b = body (outlined), g = glow (over the outline)."""

    def __init__(self):
        self.n, self.u, self.b, self.g = Canvas(), Canvas(), Canvas(), Canvas()

    def done(self, clip=True):
        base = dict(self.u.px); base.update(self.b.px)
        out = dict(base)
        for (x, y) in base:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                k = (x + dx, y + dy)
                if k not in base: out[k] = OUT
        px = dict(self.n.px); px.update(out); px.update(self.g.px)
        if clip: px = {k: v for k, v in px.items() if k[1] <= 0}
        return Spr(px)


def gl(c, x0, y0, x1, y1, ramp, over=True):
    """1 px line coloured along its length (ramp[0] at the start)."""
    pts = line_px(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1)))
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        c.put(x, y, ramp[min(len(ramp) - 1, int(i / max(1, n) * len(ramp)))], over)
    return pts


def ln(c, x0, y0, x1, y1, ch, over=True):
    pts = line_px(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1)))
    for (x, y) in pts: c.put(x, y, ch, over)
    return pts


def rot_pt(x, y, deg, px=0.0, py=0.0):
    a = math.radians(deg)
    dx, dy = x - px, y - py
    return px + dx * math.cos(a) - dy * math.sin(a), py + dx * math.sin(a) + dy * math.cos(a)


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


def crescent(c, cx, cy, r, ang, bite, ramp, over=True, glint=None, rim=None):
    """A crescent moon: disc of radius r minus a disc of the same radius shifted `bite` px toward `ang` (deg, 0 = right).
    Lit from the top-left; `rim` paints the outer edge."""
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    ox, oy = cx + ca * bite, cy + sa * bite
    R = int(r) + 2
    for y in range(int(cy - R), int(cy + R) + 1):
        for x in range(int(cx - R), int(cx + R) + 1):
            d0 = math.hypot(x - cx, y - cy)
            if d0 > r: continue
            if math.hypot(x - ox, y - oy) <= r * 0.98: continue
            l = -((x - cx) + (y - cy)) / (r * 1.414) * 0.8 + 0.15
            ch = pick(ramp, l)
            if rim and d0 > r - 1.0: ch = rim
            c.put(x, y, ch, over)
    if glint: c.put(*P(cx - r * 0.55, cy - r * 0.55), glint)


def disc(c, cx, cy, r, ramp, over=True, bias=0.0):
    ell(c, cx, cy, r, r, ramp, bias=bias, over=over)


def moon_face(c, cx, cy, r, phase=4, dark="ο", ramp=MOON, maria=True):
    """A moon disc showing `phase` (0 new .. 4 full): the unlit part painted `dark`."""
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            dx, dy = x - cx, y - cy
            if dx * dx + dy * dy > r * r: continue
            # terminator: lit from the right (waxing), lit width grows with phase
            k = phase / 4.0
            u = dx / max(0.5, math.sqrt(max(0.01, r * r - dy * dy)))      # -1 .. 1 across the row
            lit = u > 1 - 2 * k
            if lit:
                l = -(dx + dy) / (r * 1.414) * 0.6 + 0.25
                ch = pick(ramp[1:], l)
                if maria and ((x * 3 + y * 5) % 11 == 0) and abs(dx) < r - 1 and abs(dy) < r - 1: ch = ramp[1]
            else:
                if dark is None: continue
                ch = dark
            c.put(x, y, ch)


def star4(c, x, y, size=1, ch="χ", core="θ", arm=None):
    """A 4-point twinkle: centre + arms of `size` px."""
    x, y = int(round(x)), int(round(y))
    arm = arm or ch
    c.put(x, y, core)
    for k in range(1, size + 1):
        cc = arm if k == size else ch
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)): c.put(x + dx, y + dy, cc)


def dither_wisp(c, x0, y0, x1, y1, w0, w1, ramp, seed=0, density=0.55):
    """A tapering ghostly wisp from (x0,y0) to (x1,y1): checker-dithered, thinning toward the end."""
    rnd = random.Random(seed)
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(n + 1):
        t = i / max(1, n)
        cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        w = w0 + (w1 - w0) * t
        for k in range(-int(w), int(w) + 1):
            # perpendicular offset
            dx, dy = (y1 - y0), -(x1 - x0)
            L = math.hypot(dx, dy) or 1
            px_, py_ = int(round(cx + dx / L * k)), int(round(cy + dy / L * k))
            if (px_ + py_) % 2 == 0 and rnd.random() < density * (1.15 - t):
                c.put(px_, py_, ramp[min(len(ramp) - 1, int((1 - t) * len(ramp)))], over=False)


def sheen(spr, band_x, width=2, slope=1.0, chars=("δ", "ε", "ζ"), up=None):
    """A specular glint band sweeping across polished silver: pixels of the plate ramp inside the diagonal band are
    lifted one or two steps (x + slope*y within [band_x, band_x + width])."""
    up = up or {"β": "γ", "γ": "δ", "δ": "ε", "ε": "ζ", "ζ": "η", "η": "θ", "Ω": "ζ", "ω": "Ω"}
    out = dict(spr.px)
    for (x, y), v in spr.px.items():
        s = x + slope * y
        if band_x <= s < band_x + width and v in up:
            out[(x, y)] = up[v]
            if band_x + width * 0.3 <= s < band_x + width * 0.7 and up.get(up[v]): out[(x, y)] = up[up[v]]
    return Spr(out)


def tint_stone(spr):
    return spr.stone()


def corpse_wisps(c, cx, cy, n, h, seed=0, ramp=GLOW):
    rnd = random.Random(seed)
    for i in range(n):
        x = cx + rnd.uniform(-8, 8)
        top = cy - rnd.uniform(h * 0.5, h)
        for y in range(int(cy), int(top), -1):
            if (y + i) % 2 == 0:
                c.put(int(round(x + math.sin(y * 0.6 + i) * 1.2)), y, ramp[0 if y > (cy + top) / 2 else 1], over=False)


BUILT = {}
NOTES = {}


def sheet(name, anims, outdir, scale=5):
    B.sheet(name, anims, outdir, scale=scale)
    BUILT[name] = B.BUILT[name]


def fx_sheet(name, anims, outdir, scale=6):
    B.fx_sheet(name, anims, outdir, scale=scale)
    BUILT[name] = B.BUILT[name]


def tail(idle0, death, death_d, knock, portrait=None):
    return [("Death", death, death_d), ("Dead", [death[-1]], [0.3]), ("Statue", [idle0.stone()], [0.2]),
            ("Knockback", [knock], [0.2]), ("Portrait", [portrait or idle0], [0.2])]


# ======================================================================================= MOONWARDEN (common A)
def glaive(f, hx, hy, ang, L=24, back=6, smear=0, glint=False, moon=0.0, layer=None):
    """The crescent glaive held at hand (hx, hy): shaft from `back` px behind the hand to L px ahead along `ang`
    (deg; -90 = straight up), a crescent moon blade on the head, its edge facing forward-out."""
    lay = layer or f.b
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    bx, by = hx - ca * back, hy - sa * back
    tx, ty = hx + ca * L, hy + sa * L
    # shaft: dark core with a lit top edge
    pts = ln(lay, bx, by, tx, ty, "γ")
    for i, (x, y) in enumerate(pts):
        if i % 5 == 2: lay.put(x, y, "ε")
    lay.put(*P(bx, by), "δ")
    # blade: a crescent centred a little past the tip, opening back toward the wielder's side
    nx, ny = -sa, ca                                   # normal (blade side = +n, i.e. "below/forward" of the shaft)
    bcx, bcy = tx + nx * 2.4 + ca * 0.5, ty + ny * 2.4 + sa * 0.5
    crescent(lay, bcx, bcy, 5.2, math.degrees(math.atan2(-ny, -nx)), 2.6, "γδεζη")
    if glint: lay.put(*P(bcx + nx * 3.2 - ca * 1.0, bcy + ny * 3.2 - sa * 1.0), "θ")
    # a ferrule ring under the blade
    lay.put(*P(tx - ca * 1.5, ty - sa * 1.5), "ζ")
    if moon > 0:
        r = 1.6 + moon * 1.6
        disc(f.g, tx + nx * 2.0, ty + ny * 2.0 - 1, r, "μνν")
        star4(f.g, tx + nx * 2.0, ty + ny * 2.0 - 1, size=1 + int(moon * 1.5), ch="ν", core="θ")
    if smear:
        # a solid pale arc of motion trailing the blade (smear = how many 12-degree steps it spans)
        for step in range(smear * 12, 0, -1):
            a2 = math.radians(ang - step * 1.0 * (1 if smear > 0 else -1))
            for rr, ch in ((L + 4.0, "ζ"), (L + 3.0, "η"), (L + 2.0, "ε")):
                fade = step / (smear * 12.0)
                if fade > 0.7 and rr != L + 3.0: continue
                f.g.put(*P(hx + math.cos(a2) * rr, hy + math.sin(a2) * rr), ch if fade < 0.45 else "δ", over=False)
    return (tx, ty), (bcx + nx * 3.0, bcy + ny * 3.0)


def warden_leg(f, hip, foot, near=True):
    lay = f.b if near else f.u
    ramp = SIL if near else SILD
    (kx, ky), _ = B.ik(hip[0], hip[1], foot[0], foot[1], 6.4, 6.4, bend=-1)
    tube(lay, [hip, (kx, ky), foot], [1.9, 1.5, 1.4], ramp, bias=-0.2)
    # knee cop
    disc(lay, kx + 0.3, ky, 1.4, ramp, bias=0.2)
    # sabaton: a pointed plate foot
    fx, fy = foot
    for dx in range(-1, 4): lay.put(*P(fx + dx, fy), ramp[1] if dx < 2 else ramp[2])
    lay.put(*P(fx + 1, fy - 1), ramp[3]); lay.put(*P(fx + 3, fy - 1), ramp[2])


def warden_cape(f, sx, sy, sway=0.0, stream=0.0, seed=0, lift=0.0):
    """Moonlit mantle hanging from the shoulders down the back, tattering into spectral wisps."""
    rnd = random.Random(seed)
    top = (sx - 1.0, sy)
    pts = []
    n = 9
    for i in range(n + 1):
        t = i / n
        # trailing edge: hangs down and back; streams out horizontally when running (stream 0..1)
        bx = top[0] - 4.0 - t * (6.0 + stream * 8.0) + math.sin(t * 3.0 + sway) * (1.0 + stream)
        by = top[1] + t * (17.0 - stream * 7.0 - lift * 4) + math.sin(t * 2.2 + sway * 0.7) * 0.6
        pts.append((bx, by))
    # fill between the body line (x = sx) and the trailing edge
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        for yy in range(int(min(y0, y1)), int(max(y0, y1)) + 1):
            t = (yy - y0) / (y1 - y0) if y1 != y0 else 0
            ex = x0 + (x1 - x0) * t
            for xx in range(int(round(ex)), int(round(sx)) + 1):
                d = (sx - xx) / max(1.0, sx - ex)
                ch = "τ" if d > 0.6 else ("υ" if d > 0.25 else ("φ" if (xx + yy) % 4 == 0 else "υ"))
                if xx == int(round(ex)) or xx == int(round(ex)) + 1: ch = "ε" if (yy % 3) else "ζ"
                f.u.put(xx, yy, ch, over=False)
    # tattered spectral hem
    lx, ly = pts[-1]
    for k in range(4):
        hx = lx + k * 1.6 + rnd.uniform(-0.4, 0.4)
        dither_wisp(f.n, hx, ly, hx - 2 - stream * 4, ly + 4 - stream * 2.5, 0.8, 0.2, "ςπρ", seed=seed + k, density=0.8)
    return pts


def moonwarden(dx=0.0, dy=0.0, lean=0.0, legs=((-3.0, 0.0), (3.0, 0.0)), hand=(6.0, -15.0), gang=-84.0, gl_back=9,
               gl_len=16, smear=0, cape_sway=0.0, stream=0.0, halo=1.0, eye=1, moon=0.0, crouch=0.0, glint=-99,
               head_tilt=0.0, back_hand=None, seed=0, crack=False, halo_off=(0.0, 0.0)):
    """The Moonwarden, facing right. hand = front hand position (relative to feet), gang = glaive angle."""
    f = Fr()
    cy0 = dy + crouch
    hipx, hipy = dx - 0.5 + lean * 0.3, -12.5 + cy0
    # legs (far leg first, under layer)
    (fx0, fy0), (fx1, fy1) = legs
    warden_leg(f, (hipx - 1.2, hipy), (dx + fx0, fy0), near=False)
    # torso
    chx, chy = hipx + lean * 0.6 + 0.6, hipy - 7.0
    shx, shy = chx + 0.5 + lean * 0.3, chy - 4.0
    warden_cape(f, shx - 1.0, shy - 0.5, sway=cape_sway, stream=stream, seed=seed)
    # tassets (plate skirt)
    for k, (ox, w) in enumerate(((-3.0, 2.2), (0.0, 2.6), (3.0, 2.2))):
        ell(f.b, hipx + ox * 0.9, hipy - 1.0, w, 2.8, SIL, bias=-0.15 - k * 0.08)
    warden_leg(f, (hipx + 1.2, hipy), (dx + fx1, fy1), near=True)
    # breastplate
    ell(f.b, chx, chy, 5.0, 6.2, SIL, bias=-0.12)
    ell(f.b, chx - 0.4, hipy - 2.2, 3.6, 1.6, SIL, bias=-0.1)        # waist fauld
    # engraved crescent on the breastplate (dark inlay, mint core when the moon is high)
    crescent(f.b, chx + 0.6, chy - 0.6, 2.4, 0, 1.2, "ββγ")
    if moon >= 0.75: f.g.put(*P(chx - 0.8, chy - 0.8), "ρ")
    # far pauldron
    ell(f.u, shx - 3.6, shy + 0.6, 2.6, 2.2, SILD, bias=0.1)
    # back arm (holding the shaft lower down, or swinging free)
    if back_hand is None:
        bh = (hand[0] - 5.0 + dx * 0, hand[1] + 4.0)
    else:
        bh = back_hand
    tube(f.u, [(shx - 3.2, shy + 1.5), ((shx - 3.2 + bh[0] + dx) / 2 - 0.5, (shy + bh[1] + cy0) / 2 + 1.5), (bh[0] + dx, bh[1] + cy0)],
         [1.3, 1.1, 1.1], SILD)
    # head: helm with a moon-disc face
    hx, hy = shx + 1.6 + head_tilt * 0.5, shy - 4.6
    # crescent halo behind the head (the warden's crest)
    if halo > 0:
        # the lunar crest: a horns-up crescent standing behind the helm
        crescent(f.u, hx - 1.2 + halo_off[0], hy - 2.6 + halo_off[1], 5.4 * halo, -90, 2.8 * halo, "ξμνν")
        f.g.put(*P(hx - 5.6 * halo + halo_off[0], hy - 5.4 + halo_off[1]), "ν")
    ell(f.b, hx - 0.6, hy, 3.9, 4.3, "βγγδε", bias=0.0)
    moon_face(f.b, hx + 1.0, hy + 0.4, 3.0, phase=4)
    # visor slit: a dark crescent eye, glowing mint inside
    f.b.put(*P(hx + 1.6, hy - 0.2), "ψ"); f.b.put(*P(hx + 2.4, hy + 0.3), "ψ"); f.b.put(*P(hx + 0.8, hy + 0.4), "ψ")
    if eye: f.g.put(*P(hx + 1.6, hy - 0.2), "ρ" if eye == 1 else "π")
    if crack:
        ln(f.b, hx + 0.2, hy - 2.2, hx + 1.8, hy + 1.4, "β")
    # helm crest ridge
    gl(f.b, hx - 3.4, hy - 2.6, hx + 0.6, hy - 4.2, "γεη")
    # near pauldron (layered over the chest)
    ell(f.b, shx + 1.0, shy + 0.8, 2.8, 2.4, SIL, bias=0.2)
    f.b.put(*P(shx + 0.0, shy - 0.2), "η")
    # front arm: shoulder -> elbow -> hand
    (ex, ey), _ = B.ik(shx + 1.0, shy + 1.6, hand[0] + dx, hand[1] + cy0, 5.2, 5.2, bend=1)
    tube(f.b, [(shx + 1.0, shy + 1.6), (ex, ey), (hand[0] + dx, hand[1] + cy0)], [1.5, 1.3, 1.4], SIL, bias=0.1)
    disc(f.b, hand[0] + dx, hand[1] + cy0, 1.3, SIL, bias=0.2)     # gauntlet
    tip, edge = glaive(f, hand[0] + dx, hand[1] + cy0, gang, L=gl_len, back=gl_back, smear=smear,
                       glint=glint > -50, moon=moon if moon >= 1.0 else 0.0)
    spr = f.done()
    if glint > -50:
        spr = sheen(spr, glint, width=3, slope=0.6)
    return spr, {"tip": tip, "edge": edge, "head": (hx, hy), "chest": (chx, chy)}


def warden_corpse(stage):
    """Death: the plates sag, the knight kneels, the armour falls empty as the spirit leaves."""
    f = Fr()
    # a pile of plates: tassets, breastplate on its side, helm with the dimmed moon face, the glaive across
    ell(f.b, -1.5, -2.2, 6.5, 2.4, SIL, bias=0.0)
    ell(f.b, 3.5, -3.0, 3.2, 3.0, SIL, bias=0.15)
    moon_face(f.b, 4.4, -3.2, 2.0, phase=1)
    ell(f.b, -6.0, -1.6, 2.6, 1.6, SILD)
    ln(f.b, -11, -1, 11, -2, "γ")
    crescent(f.b, 12.5, -3.0, 4.2, 200, 2.2, "γδεζ")
    for k in range(3): f.b.put(-9 + k * 7, -1, "ε")
    if stage < 1:
        corpse_wisps(f.g, -1, -4, 5, 10, seed=3)
    return f.done()


def build_moonwarden(outdir):
    S = lambda **k: moonwarden(**k)[0]
    idle = []
    for i in range(4):
        b = [0.0, -0.4, -0.7, -0.3][i]
        idle.append(S(dy=b, cape_sway=i * 1.55, hand=(6.2, -15.0 + b), gang=-84 + [0, 1, 2, 1][i], glint=[-40, -28, -16, -4][i],
                      halo_off=(0, [0, -0.5, -0.8, -0.4][i]), seed=i))
    run = []
    for i in range(6):
        ph = i / 6 * 2 * math.pi
        a, c = math.cos(ph), math.sin(ph)
        legs = ((-0.5 - a * 4.5, -max(0.0, c) * 2.4), (1.0 + a * 4.5, -max(0.0, -c) * 2.4))
        bob = -abs(c) * 0.9
        run.append(S(dx=0.5, dy=bob, lean=2.0, legs=legs, hand=(7.4, -15.5 + bob), gang=-58 + a * 3, stream=0.65 + 0.1 * c,
                     cape_sway=ph * 2, glint=[-30, -22, -14, -6, 2, 10][i], seed=10 + i))
    # Sweep: wind the glaive back over the shoulder, then a low-to-high crescent sweep in front (hit on frame 3)
    sw = []
    keys = [  # hand, glaive angle, lean, legs, smear, back hand
        dict(hand=(3.0, -20.0), gang=-140, lean=-1.2, legs=((-4.0, 0.0), (3.0, 0.0)), back_hand=(0.0, -18.0)),
        dict(hand=(1.0, -22.0), gang=-170, lean=-2.2, legs=((-4.5, 0.0), (3.5, 0.0)), back_hand=(-1.5, -19.0)),
        dict(hand=(8.0, -15.0), gang=-20, lean=2.5, legs=((-5.0, 0.0), (5.0, 0.0)), smear=3, back_hand=(3.0, -14.0)),
        dict(hand=(10.0, -14.0), gang=10, lean=3.2, legs=((-5.5, 0.0), (6.0, 0.0)), smear=4, back_hand=(5.0, -13.0)),
        dict(hand=(9.0, -17.0), gang=-10, lean=2.6, legs=((-5.0, 0.0), (5.5, 0.0)), smear=1, back_hand=(4.0, -15.0)),
        dict(hand=(7.0, -16.5), gang=-55, lean=1.0, legs=((-4.0, 0.0), (4.0, 0.0)), back_hand=(2.0, -13.0)),
        dict(hand=(6.2, -16.0), gang=-80, lean=0.0, legs=((-3.0, 0.0), (3.0, 0.0))),
    ]
    for i, k in enumerate(keys):
        sw.append(S(cape_sway=i * 0.9, stream=[0, 0, .4, .5, .3, .1, 0][i], seed=20 + i, **k))
    sw_d = [0.12, 0.14, 0.05, 0.07, 0.09, 0.12, 0.12]
    # Moonfall: raise the glaive to the sky, the moon gathers on its head, then point it at the hero (release frame 5)
    mf = []
    keys = [
        dict(hand=(5.0, -18.0), gang=-95, moon=0.0),
        dict(hand=(4.0, -22.0), gang=-100, moon=0.3, lean=-0.8),
        dict(hand=(3.5, -25.0), gang=-98, moon=1.0, lean=-1.2),
        dict(hand=(3.5, -25.5), gang=-96, moon=1.4, lean=-1.2),
        dict(hand=(4.0, -25.0), gang=-92, moon=1.9, lean=-1.0),
        dict(hand=(9.0, -19.0), gang=-35, moon=0.0, lean=2.0, smear=2),
        dict(hand=(9.5, -18.0), gang=-28, moon=0.0, lean=2.2),
        dict(hand=(7.0, -16.5), gang=-60, moon=0.0, lean=0.8),
    ]
    for i, k in enumerate(keys):
        mf.append(S(cape_sway=i * 1.1, seed=30 + i, eye=2 if 2 <= i <= 4 else 1,
                    back_hand=(k["hand"][0] - 4.0, k["hand"][1] + 6.0), halo=1.0 + (0.1 if 3 <= i <= 4 else 0), **k))
    mf_d = [0.12, 0.12, 0.12, 0.1, 0.1, 0.06, 0.14, 0.14]
    # Death: stagger, kneel, the spirit leaves (empty plates fall), corpse
    d0 = S(lean=-2.0, hand=(4.0, -14.0), gang=-60, eye=2, crack=True, seed=40)
    d1 = S(lean=1.0, crouch=4.0, legs=((-4.0, 0.0), (3.0, -1.0)), hand=(7.0, -9.0), gang=-30, eye=0, crack=True, halo=0.6, seed=41)
    d2 = B.merge(warden_corpse(0), Spr({}))
    d3 = warden_corpse(1)
    knock = S(lean=-2.6, hand=(3.0, -17.0), gang=-115, legs=((-4.0, 0.0), (2.0, 0.0)), eye=2, seed=45)
    portrait = moonwarden(glint=-20, seed=0)[0]
    sheet("SilMoonwarden", [("Idle", idle, [0.2, 0.18, 0.2, 0.18]), ("Run", run, [0.09] * 6),
                            ("Sweep", sw, sw_d), ("Moonfall", mf, mf_d)] +
          tail(idle[0], [d0, d1, d2, d3], [0.14, 0.16, 0.18, 0.3], knock, portrait), outdir)
    # spawn points (facing right, relative to the feet): glaive edge on the hit frame / moon on the release frame
    _, k3 = moonwarden(**keys and dict(hand=(10.0, -14.0), gang=10, lean=3.2, legs=((-5.5, 0.0), (6.0, 0.0))))
    NOTES["SilMoonwarden"] = "sweep edge at %s, tip %s" % (tuple(round(v, 1) for v in k3["edge"]), tuple(round(v, 1) for v in k3["tip"]))


# ======================================================================================= COMET STAG (common B)
def stag_leg(f, hip, foot, near, front, lift=0.0):
    lay = f.b if near else f.n
    ramp = HIDE if near else "αβγδ"
    # deer legs: the front knee bends back, the hock (hind) bends forward; thin cannon down to a dark hoof
    bend = 1 if front else -1
    (kx, ky), _ = B.ik(hip[0], hip[1], foot[0], foot[1] - 1, 5.0, 5.4, bend=bend)
    tube(lay, [hip, (kx, ky)], [1.5, 0.9], ramp, bias=-0.1)
    tube(lay, [(kx, ky), (foot[0], foot[1] - 1)], [0.8, 0.7], ramp, bias=-0.1)
    lay.put(*P(foot[0], foot[1]), "β" if near else "α"); lay.put(*P(foot[0] + 1, foot[1]), "β" if near else "α")
    if near: lay.put(*P(kx, ky), ramp[3])


def comet_streak(c, x0, y0, length, ang, w=2.2, seed=0, bright=1.0):
    """A comet tail: white core, mint then silver, breaking into dithered motes toward its end."""
    rnd = random.Random(seed)
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    n = int(length)
    for i in range(n):
        t = i / max(1, n)
        cx, cy = x0 + ca * i, y0 + sa * i
        ww = w * (1 - t * 0.75)
        for k in range(-int(math.ceil(ww)), int(math.ceil(ww)) + 1):
            px_, py_ = cx - sa * k, cy + ca * k
            edge = abs(k) / max(0.5, ww)
            if edge > 1.0: continue
            if t > 0.55 and ((int(px_) + int(py_) + i) % 2 or rnd.random() < t - 0.4): continue
            ch = "θ" if (edge < 0.35 and t < 0.35 * bright) else ("ρ" if edge < 0.6 and t < 0.6 else ("π" if t < 0.75 else "ε"))
            c.put(*P(px_, py_), ch, over=False)


def stag_antlers(f, hx, hy, tilt=0.0, glow=0.0, far=True):
    """A lyre-shaped rack of slim silver beams with star-budded tines, cradling a small crescent moon between them."""
    R = lambda x, y: rot_pt(hx + x, hy + y, tilt, hx, hy)
    def beam(lay, pts, tines, ramp):
        pp = [R(*q) for q in pts]
        for (x0, y0), (x1, y1) in zip(pp, pp[1:]): gl(lay, x0, y0, x1, y1, ramp)
        ends = [pp[-1]]
        for i, (tx, ty) in tines:
            q = R(tx, ty)
            gl(lay, pp[i][0], pp[i][1], q[0], q[1], ramp[1:])
            ends.append(q)
        return ends
    ends = []
    if far:
        ends += beam(f.u, [(1, 0), (3, -4), (5, -8), (5, -12)], [(1, (6, -6))], "δεζ")
    mx, my = R(0.5, -9.0)
    crescent(f.u, mx, my, 2.7, -90 + tilt, 1.6, "ξμνν")
    ends += beam(f.b, [(-1, 0), (-3, -4), (-4, -9), (-2, -13)], [(1, (0, -7)), (2, (-1, -11))], "εζηη")
    for k, (tx, ty) in enumerate(ends):
        if glow >= 0.5:
            star4(f.g, tx, ty, size=1, ch="ρ", core="θ")
        else:
            f.g.put(*P(tx, ty), "θ" if k % 2 == 0 else "ρ")
    if glow >= 0.5: star4(f.g, mx, my - 1, size=2, ch="ν", core="θ")


def comet_stag(dx=0.0, dy=0.0, tilt=0.0, legs=None, head=0.0, neck=0.0, mane=0.0, tail=0.0, blink=False, glow=0.0,
               gore=0.0, seed=0, flank=True, hurt=False):
    """The Comet Stag facing right. legs = 4 foot positions (far-front, far-hind, near-front, near-hind)."""
    f = Fr()
    if legs is None: legs = ((6.0, 0.0), (-6.5, 0.0), (8.0, 0.0), (-4.5, 0.0))
    bx, by = dx - 0.5, -14.0 + dy
    hips = {"ff": (bx + 6.0, by + 2.0), "fh": (bx - 6.5, by + 1.5), "nf": (bx + 7.0, by + 2.4), "nh": (bx - 5.5, by + 2.0)}
    # far legs (no outline, dim)
    stag_leg(f, hips["ff"], (dx + legs[0][0], legs[0][1]), False, True)
    stag_leg(f, hips["fh"], (dx + legs[1][0], legs[1][1]), False, False)
    # comet tail
    comet_streak(f.n, bx - 9.5, by - 2.0, 9 + tail * 6, 190 + tail * 8, w=1.8, seed=seed)
    # barrel, chest and haunch
    ell(f.b, bx, by, 9.2, 4.4, HIDE, bias=-0.25)
    ell(f.b, bx - 6.5, by - 0.4, 4.2, 4.6, HIDE, bias=-0.2)
    ell(f.b, bx + 6.5, by + 0.2, 4.0, 4.8, HIDE, bias=-0.1)
    # belly shade
    for x in range(int(bx - 8), int(bx + 8)): f.b.put(x, int(by + 4), "γ")
    # flank constellation: a few star specks joined faintly
    if flank:
        pts = [(bx - 5, by - 1), (bx - 2, by - 2.5), (bx + 1, by - 0.5), (bx + 3.5, by - 2)]
        for i, (sx, sy) in enumerate(pts):
            f.b.put(*P(sx, sy), "θ" if i % 2 == 0 else "η")
    # neck up to the head
    nx0, ny0 = bx + 7.5, by - 2.5
    hx, hy = rot_pt(bx + 14.0, by - 9.0, head * 40 + neck * 10, nx0, ny0)
    tube(f.b, [(nx0, ny0), ((nx0 + hx) / 2 - 0.5, (ny0 + hy) / 2 + 0.5), (hx - 1.0, hy + 0.5)], [3.0, 2.0, 1.8], HIDE, bias=-0.05)
    # mane: a comet streaming back off the neck
    comet_streak(f.u, hx - 2.0, hy - 0.5, 9 + mane * 5, 168 + mane * 6 + head * 20, w=1.6, seed=seed + 7, bright=0.3)
    # head: skull and muzzle angled down-forward
    hang = 25 + head * 45
    mx, my = hx + math.cos(math.radians(hang)) * 6.0, hy + math.sin(math.radians(hang)) * 6.0
    ell(f.b, hx, hy, 3.2, 2.7, HIDE, bias=0.1)
    tube(f.b, [(hx + 0.5, hy + 0.3), (mx, my)], [2.2, 1.3], HIDE, bias=0.05)
    f.b.put(*P(mx + 0.4, my + 0.2), "β")                                   # nose
    # ear
    ex, ey = hx - 1.6, hy - 2.4
    tube(f.b, [(ex, ey), (ex - 2.8, ey - 1.6 - neck)], [1.0, 0.4], HIDE)
    # eye (mint) and the brow star
    f.g.put(*P(hx + 1.0, hy - 0.3), "π" if not blink else "β")
    if not blink and not hurt: f.g.put(*P(hx + 1.0, hy - 0.3), "ρ")
    star4(f.g, hx - 0.2, hy - 2.2, size=1, ch="ν", core="θ")
    stag_antlers(f, hx - 0.8, hy - 2.0, tilt=head * 35 + gore * 25, glow=glow)
    # near legs
    stag_leg(f, hips["nh"], (dx + legs[3][0], legs[3][1]), True, False)
    stag_leg(f, hips["nf"], (dx + legs[2][0], legs[2][1]), True, True)
    spr = f.done(clip=tilt == 0.0)
    if tilt:
        spr = rot(spr, tilt, (dx - 5.0, 0.0))
        spr = Spr({k: v for k, v in spr.px.items() if k[1] <= 0})
    return spr, {"head": (hx, hy), "muzzle": (mx, my)}


def comet_form(dx=0.0, phase=0, stretch=1.0, seed=0):
    """The stag as a streak of starlight: a blazing head with the crescent antlers inside, a long tail behind."""
    f = Fr()
    cx, cy = dx + 4.0, -12.0
    comet_streak(f.n, cx - 2, cy, 22 * stretch, 180 + [0, 3, -3][phase % 3], w=4.2, seed=seed + phase)
    comet_streak(f.n, cx - 3, cy - 3, 12 * stretch, 188, w=1.5, seed=seed + 11)
    comet_streak(f.n, cx - 3, cy + 3, 12 * stretch, 172, w=1.5, seed=seed + 13)
    ell(f.b, cx, cy, 5.6, 4.2, "επρρ", bias=0.4)
    ell(f.g, cx + 0.8, cy - 0.5, 2.6, 2.0, "ρθθ", bias=0.5)
    # the antler crescents ride on the blaze
    crescent(f.b, cx - 1.5, cy - 6.0, 4.0, 25, 2.2, "δεζη")
    crescent(f.u, cx - 3.5, cy - 5.0, 3.4, 25, 2.0, "γδε")
    for k in range(3):
        a = phase * 40 + k * 120
        star4(f.g, cx + math.cos(math.radians(a)) * 7.0, cy + math.sin(math.radians(a)) * 4.5, size=1, ch="ρ", core="θ")
    return f.done()


def stag_corpse(stage):
    f = Fr()
    # lying on its side: barrel, legs folded, head down, the mane guttered out
    ell(f.b, 0.0, -3.4, 9.5, 3.4, HIDE, bias=-0.1)
    ell(f.b, -6.5, -3.4, 4.0, 3.2, HIDE)
    for (x0, x1) in ((-8, -12), (-5, -9), (5, 10), (7, 12)):
        ln(f.b, x0, -1, x1, -1, "δ"); f.b.put(x1, -1, "β")
    ell(f.b, 11.0, -2.6, 2.6, 2.0, HIDE, bias=0.1)
    tube(f.b, [(12.0, -2.4), (16.0, -1.4)], [1.6, 1.0], HIDE)
    crescent(f.u, 9.0, -6.5, 3.6, 300, 2.0, "γδε")
    for i, (sx, sy) in enumerate(((-4, -4), (-1, -5), (2, -4))): f.b.put(sx, sy, "η")
    if stage == 0:
        corpse_wisps(f.g, 0, -5, 6, 9, seed=5)
        comet_streak(f.n, -10, -4, 6, 180, w=1.2, seed=3, bright=0.3)
    return f.done()


def build_comet_stag(outdir):
    S = lambda **k: comet_stag(**k)[0]
    idle = []
    for i in range(4):
        b = [0.0, -0.3, -0.5, -0.2][i]
        idle.append(S(dy=b, head=[0.0, 0.03, 0.05, 0.02][i], mane=[0, .3, .6, .3][i], tail=[0, .4, .2, .5][i], blink=i == 2,
                      neck=[0, .3, .5, .2][i], seed=i))
    run = []
    for i in range(6):
        ph = i / 6 * 2 * math.pi
        # rotary gallop: hind pair, then front pair
        def lg(off, base, reach):
            a = ph + off
            return (base + math.cos(a) * reach, -max(0.0, math.sin(a)) * 3.2)
        legs = (lg(0.6, 6.5, 5.0), lg(2.6, -6.0, 5.0), lg(1.0, 7.5, 5.5), lg(3.0, -5.0, 5.5))
        bob = -abs(math.sin(ph)) * 1.4
        run.append(S(dx=0.5, dy=bob, head=-0.05 + 0.05 * math.sin(ph), mane=1.0, tail=1.0, seed=10 + i,
                     legs=legs, neck=0.2))
    # Gore: drop the head, antlers forward, lunge and toss (hit on frame 3)
    gk = [dict(head=0.2, dy=0.5), dict(head=0.55, dy=1.0, dx=-1.0), dict(head=0.85, dy=1.4, dx=2.0, gore=0.3),
          dict(head=0.7, dy=0.8, dx=4.0, gore=0.6, glow=0.6), dict(head=0.1, dy=-1.0, dx=3.5, gore=-0.6),
          dict(head=0.0, dy=-0.5, dx=2.0), dict(head=0.05, dy=0.0, dx=0.5)]
    gore = []
    for i, k in enumerate(gk):
        legs = ((6.0 + max(0, k.get("dx", 0) - 1), 0.0), (-7.0, 0.0), (8.5 + max(0, k.get("dx", 0) - 1), 0.0), (-5.0, 0.0))
        gore.append(S(legs=legs, mane=0.6, tail=0.5, seed=20 + i, **k))
    gore_d = [0.12, 0.12, 0.06, 0.08, 0.1, 0.12, 0.12]
    # Comet: rear up, ignite (rise 3), the streak (loop 3), land and skid (end 2)
    rise = [S(tilt=-12, head=-0.2, mane=0.8, tail=0.6, glow=0.3, seed=30,
              legs=((9.0, -4.0), (-6.0, 0.0), (11.0, -5.0), (-4.5, 0.0))),
            S(tilt=-22, head=-0.3, mane=1.2, tail=1.0, glow=0.8, seed=31,
              legs=((10.0, -6.0), (-6.0, 0.0), (12.0, -7.0), (-4.5, 0.0))),
            B.merge(S(dy=1.5, head=0.3, mane=1.5, tail=1.5, glow=1.0, seed=32), comet_form(phase=0, stretch=0.5, seed=32))]
    loop = [comet_form(phase=i, seed=40 + i) for i in range(3)]
    end = [S(dx=-2.0, dy=0.5, head=0.3, mane=1.6, tail=1.4, glow=0.6, seed=45, legs=((4.0, 0.0), (-9.0, 0.0), (6.0, 0.0), (-7.0, 0.0))),
           S(dx=-0.5, head=0.1, mane=0.8, tail=0.6, seed=46)]
    d0 = S(head=-0.4, neck=0.6, tail=0.2, hurt=True, seed=50, dy=0.5)
    d1 = S(tilt=10, head=0.6, hurt=True, blink=True, seed=51, legs=((3.0, 0.0), (-8.0, 0.0), (5.0, 0.0), (-6.0, 0.0)), dy=2.0)
    d2 = stag_corpse(0)
    d3 = stag_corpse(1)
    knock = S(head=-0.35, neck=0.5, tilt=-8, hurt=True, seed=55, legs=((5.0, 0.0), (-7.5, 0.0), (6.5, 0.0), (-5.5, 0.0)))
    sheet("SilCometStag", [("Idle", idle, [0.2, 0.18, 0.2, 0.18]), ("Run", run, [0.075] * 6),
                           ("Gore", gore, gore_d), ("CometRise", rise, [0.12, 0.12, 0.08]), ("CometLoop", loop, [0.06] * 3),
                           ("CometEnd", end, [0.12, 0.14])] +
          tail(idle[0], [d0, d1, d2, d3], [0.14, 0.16, 0.18, 0.3], knock), outdir)
    _, g3 = comet_stag(**gk[3])
    NOTES["SilCometStag"] = "gore head at %s" % (tuple(round(v, 1) for v in g3["head"]),)


# ======================================================================================= ASTRARCH (legendary)
STARFIELD = [(random.Random(7 + i).uniform(-1, 1), random.Random(99 + i).uniform(0, 1), i) for i in range(80)]


def night_cape(f, top_l, top_r, bot_l, bot_r, frame=0, bright=0.0, links=False, hem=0.0, seed=0):
    """The cape: a window into the night sky (deep navy gradient, twinkling stars), trimmed in silver, hem rippling."""
    pts = [top_l, top_r, bot_r]
    # rippled hem from bot_r back to bot_l
    n = 8
    for i in range(1, n):
        t = i / n
        x = bot_r[0] + (bot_l[0] - bot_r[0]) * t
        y = bot_r[1] + (bot_l[1] - bot_r[1]) * t + math.sin(t * 9.0 + hem) * 1.3
        pts.append((x, y))
    pts.append(bot_l)
    xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
    inside = {}
    def shade(x, y):
        inside[(x, y)] = 1
        t = (y - min(ys)) / max(1, max(ys) - min(ys))
        return NIGHT[min(3, int(t * 2.2 + 0.4))] if (x + y) % 7 else NIGHT[1]
    poly(f.u, pts, "τ", shade=shade)
    # silver trim along the cape's outer edges
    for (x, y) in list(inside):
        edge = any((x + dx, y + dy) not in inside for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge: f.u.put(x, y, "ε" if (x + y) % 3 else "ζ")
    # stars inside the cape (fixed per cape-local position, twinkle by frame)
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    stars = []
    for (u, v, i) in STARFIELD:
        x = int(round((x0 + x1) / 2 + u * (x1 - x0) / 2 * (0.4 + 0.6 * v)))
        y = int(round(y0 + 2 + v * (y1 - y0 - 4)))
        if (x, y) not in inside or not all((x + dx, y + dy) in inside for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))): continue
        tw = (i * 3 + frame) % 5
        ch = "χ" if tw == 0 or bright > 0.5 else ("φ" if tw in (1, 3) else "υ")
        if i % 6 == 0 and (tw == 0 or bright > 0.5):
            star4(f.u, x, y, size=1, ch="φ" if bright < 0.5 else "ρ", core="χ")
        else:
            f.u.put(x, y, ch)
        stars.append((x, y))
    if links and len(stars) >= 3:
        # the cape's own constellation lights up: dotted lines between neighbouring stars
        stars.sort()
        for (ax, ay), (bx, by) in zip(stars[::2], stars[2::2]):
            if math.hypot(bx - ax, by - ay) > 9: continue
            for k, (x, y) in enumerate(line_px(ax, ay, bx, by)):
                if k % 2 == 0 and (x, y) in inside and f.u.px.get((x, y)) in NIGHT: f.u.put(x, y, "π")
    return inside


def astrolabe(f, cx, cy, r, turn=0.0, flare=0.0):
    """The astrolabe halo: a thin silver ring with tick marks, a crescent at its crown."""
    for k in range(64):
        a = k / 64 * 2 * math.pi
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * 0.92
        behind = math.sin(a) > 0.25 and abs(math.cos(a)) < 0.6     # the lower arc passes behind the head
        lay = f.n if behind else f.u
        lay.put(*P(x, y), "δ" if math.cos(a) + math.sin(a) > 0 else "ζ", over=False)
    for k in range(8):
        a = turn + k / 8 * 2 * math.pi
        x, y = cx + math.cos(a) * (r + 1.0), cy + math.sin(a) * (r + 1.0) * 0.92
        f.u.put(*P(x, y), "η" if k % 2 == 0 else "ε", over=False)
    crescent(f.u, cx, cy - r - 1.2, 2.6 + flare, -90, 1.6, "ξμνν")
    if flare > 0:
        for k in range(12):
            a = turn * 2 + k / 12 * 2 * math.pi
            rr = r + 2.5 + flare * 1.5
            f.g.put(*P(cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.92), "ρ" if k % 3 else "θ", over=False)


def astrarch(dx=0.0, dy=0.0, lean=0.0, frame=0, hem=0.0, turn=0.0, hand=(7.0, -20.0), palm=(-7.0, -20.0), palm_star=1.0,
             staff_ang=-82.0, flare=0.0, cape_bright=0.0, links=False, stream=0.0, eye=1, crack=0, seed=0, fade=0.0):
    """The Argent Astrarch, hovering, facing right. hand = sceptre hand, palm = the star hand (relative to feet)."""
    f = Fr()
    oy = dy
    # spectral tail fading to the floor and motes under it
    dither_wisp(f.n, dx - 1.0 - stream * 3, -6 + oy, dx - 2.0 - stream * 6, -1, 3.2, 0.6, "ςπρ", seed=seed, density=0.9)
    for k in range(3):
        mx, my = dx - 4 + k * 4 + math.sin(frame * 1.3 + k) * 1.2, -2 - ((frame + k * 2) % 4)
        f.g.put(*P(mx, my), "ρ" if k != 1 else "χ")
    # cape behind the body: shoulders to a wide rippling hem, streaming back when gliding
    sh = (dx + 0.5 + lean * 0.6, -25.5 + oy)
    night_cape(f, (sh[0] - 4.5, sh[1] - 1.0), (sh[0] + 4.0, sh[1] - 0.5),
               (dx - 19.0 - stream * 5, -4.5 + oy + stream * -4), (dx + 14.0 - stream * 6, -5.5 + oy),
               frame=frame, bright=cape_bright, links=links, hem=hem, seed=seed)
    # the robe's silver front panel
    poly(f.b, [(sh[0] - 1.0, sh[1] + 2), (sh[0] + 3.0, sh[1] + 2), (dx + 4.0 - stream * 2, -7.5 + oy), (dx - 0.5 - stream * 2, -7.0 + oy)],
         "δ", shade=lambda x, y: SIL[2 + (1 if (x - y) % 6 == 0 else 0) + (1 if x < sh[0] + 1 else 0)])
    gl(f.b, sh[0] + 1.0, sh[1] + 3, dx + 2.0 - stream * 2, -8 + oy, "ηζε")        # centre seam
    ell(f.b, sh[0] + 0.5, sh[1] + 2.5, 3.6, 2.6, SIL, bias=0.1)                   # mantle collar
    # head: hood rim and the mask
    hx, hy = sh[0] + 1.2 + lean * 0.4, sh[1] - 4.5
    astrolabe(f, hx - 0.5, hy - 0.5, 6.4, turn=turn, flare=flare)
    ell(f.b, hx - 1.2, hy - 0.2, 3.8, 4.2, "βγδ", bias=-0.1)                       # hood
    ell(f.b, hx + 0.6, hy + 0.2, 2.6, 3.4, "εζηη", bias=0.2)                      # mask
    if crack:
        gl(f.b, hx + 0.2, hy - 3.2, hx + 1.4, hy + 0.2, "β")
        if crack > 1: gl(f.b, hx + 1.4, hy + 0.2, hx + 0.4, hy + 3.0, "β")
    # the single star eye
    if eye:
        star4(f.g, hx + 1.4, hy - 0.4, size=1 if eye == 1 else 2, ch="ρ" if eye == 1 else "π", core="χ")
    else:
        f.b.put(*P(hx + 1.4, hy - 0.4), "β")
    # back arm: the open palm with a hovering star
    tube(f.u, [(sh[0] - 2.0, sh[1] + 2.0), ((sh[0] - 2 + palm[0] + dx) / 2 - 1, (sh[1] + palm[1] + oy) / 2 + 2), (palm[0] + dx, palm[1] + oy)],
         [1.4, 1.1, 1.0], "βγδε", bias=0.1)
    if palm_star > 0:
        star4(f.g, palm[0] + dx, palm[1] + oy - 2.5, size=int(round(palm_star)), ch="ρ" if palm_star < 2 else "χ", core="θ",
              arm="π" if palm_star >= 2 else None)
    # sceptre arm and the sceptre (a staff topped by an armillary sphere with a star in it)
    (ex, ey), _ = B.ik(sh[0] + 2.5, sh[1] + 2.0, hand[0] + dx, hand[1] + oy, 5.5, 5.5, bend=1)
    ca, sa = math.cos(math.radians(staff_ang)), math.sin(math.radians(staff_ang))
    bx_, by_ = hand[0] + dx - ca * 12, hand[1] + oy - sa * 12
    tx, ty = hand[0] + dx + ca * 10, hand[1] + oy + sa * 10
    gl(f.b, bx_, by_, tx, ty, "γδεζ")
    ell(f.g, tx + ca * 2.2, ty + sa * 2.2, 2.4, 2.4, "δζ", over=False)
    for k in range(10):
        a = k / 10 * 2 * math.pi + turn
        f.b.put(*P(tx + ca * 2.2 + math.cos(a) * 2.4, ty + sa * 2.2 + math.sin(a) * 1.0), "ζ")
    star4(f.g, tx + ca * 2.2, ty + sa * 2.2, size=1 + (1 if flare > 0 else 0), ch="ν", core="θ")
    tube(f.b, [(sh[0] + 2.5, sh[1] + 2.0), (ex, ey), (hand[0] + dx, hand[1] + oy)], [1.5, 1.2, 1.1], SIL, bias=0.1)
    disc(f.b, hand[0] + dx, hand[1] + oy, 1.2, SIL, bias=0.2)
    spr = f.done()
    if fade > 0:
        rnd = random.Random(seed)
        spr = Spr({k: (v if rnd.random() > fade else ("ρ" if rnd.random() < 0.3 else None)) for k, v in spr.px.items()})
        spr = Spr({k: v for k, v in spr.px.items() if v})
    return spr, {"head": (hx, hy), "palm": (palm[0] + dx, palm[1] + oy - 2.5), "orb": (tx + ca * 2.2, ty + sa * 2.2)}


def astrarch_corpse(stage):
    f = Fr()
    # the cape fallen flat (still full of dim stars), the mask face-up on it, the sceptre across
    inside = {}
    poly(f.u, [(-13, -1), (10, -1), (8, -4), (-10, -5)], "τ", shade=lambda x, y: inside.setdefault((x, y), "τ" if (x + y) % 5 else "υ"))
    for (u, v, i) in STARFIELD[:14]:
        x, y = int(-11 + (u + 1) * 10), int(-2 - v * 2)
        if (x, y) in inside and (i + stage) % 3 == 0: f.g.put(x, y, "φ" if stage else "χ")
    ell(f.b, 1.0, -4.0, 2.6, 2.2, "εζηη", bias=0.2)
    gl(f.b, 0.5, -6.0, 1.6, -2.2, "β")
    f.b.put(2, -4, "β" if stage else "φ")
    gl(f.b, -12, -6, 12, -2, "γδε")
    if stage == 0:
        for k in range(6): star4(f.g, -9 + k * 4, -9 - (k % 3) * 3, size=1, ch="π", core="χ")
    return f.done()


def build_astrarch(outdir):
    S = lambda **k: astrarch(**k)[0]
    idle = []
    for i in range(6):
        ph = i / 6 * 2 * math.pi
        b = -1.0 - math.sin(ph) * 1.0
        idle.append(S(dy=b, frame=i, hem=ph, turn=ph / 4, palm=(-7.0, -19.5 + math.sin(ph) * 0.6),
                      hand=(7.0, -20.0 + math.sin(ph + 1) * 0.4), palm_star=1 + (i % 3 == 0), seed=i))
    run = []
    for i in range(6):
        ph = i / 6 * 2 * math.pi
        run.append(S(dx=0.5, dy=-1.0 - math.sin(ph) * 0.6, lean=2.0, frame=i, hem=ph * 1.5, turn=ph / 4, stream=0.7,
                     palm=(-8.0, -18.0), hand=(8.0, -19.0), staff_ang=-60, seed=10 + i))
    # Starshot: pull the palm star back over the shoulder, thrust the open palm at the hero (release frame 3)
    sk = [dict(palm=(-7.0, -20.0), palm_star=1), dict(palm=(-9.0, -24.0), palm_star=2, lean=-0.8),
          dict(palm=(-6.0, -26.0), palm_star=2, lean=-1.0, eye=2), dict(palm=(9.0, -21.0), palm_star=2, lean=2.0, eye=2),
          dict(palm=(11.0, -20.0), palm_star=0, lean=2.4), dict(palm=(6.0, -20.0), palm_star=0, lean=1.2),
          dict(palm=(-6.0, -20.0), palm_star=1, lean=0.2)]
    shot = [S(frame=i, hem=i * 0.8, turn=i * 0.2, seed=20 + i, dy=-1.0, **k) for i, k in enumerate(sk)]
    shot_d = [0.1, 0.1, 0.1, 0.05, 0.09, 0.12, 0.12]
    # Constellation: both arms to the sky, the halo flares, the cape's stars join into a figure, then down (release 5)
    ck = [dict(palm=(-7.0, -22.0), hand=(7.0, -22.0)), dict(palm=(-9.0, -27.0), hand=(8.0, -26.0), staff_ang=-88, flare=0.4),
          dict(palm=(-9.0, -30.0), hand=(8.5, -29.0), staff_ang=-92, flare=0.8, cape_bright=0.6, eye=2),
          dict(palm=(-9.5, -31.0), hand=(8.5, -30.0), staff_ang=-92, flare=1.2, cape_bright=1.0, links=True, eye=2),
          dict(palm=(-9.5, -31.0), hand=(8.5, -30.0), staff_ang=-92, flare=1.6, cape_bright=1.0, links=True, eye=2),
          dict(palm=(-10.0, -22.0), hand=(10.0, -21.0), staff_ang=-50, flare=1.0, cape_bright=1.0, links=True, eye=2, lean=1.5),
          dict(palm=(-9.0, -20.0), hand=(9.0, -20.0), staff_ang=-60, flare=0.5, cape_bright=0.5, links=True, lean=1.0),
          dict(palm=(-8.0, -20.0), hand=(7.5, -20.0), staff_ang=-75, flare=0.2, cape_bright=0.2),
          dict(palm=(-7.0, -20.0), hand=(7.0, -20.0))]
    con = [S(frame=i, hem=i * 0.9, turn=i * 0.35, seed=30 + i, dy=-1.0 - (1.0 if 2 <= i <= 5 else 0), palm_star=2 if 2 <= i <= 5 else 1, **k)
           for i, k in enumerate(ck)]
    con_d = [0.1, 0.1, 0.1, 0.12, 0.12, 0.06, 0.12, 0.12, 0.12]
    # Death: the mask cracks, she sinks, comes apart into stars, the empty cape falls
    death = [S(dy=-1.0, crack=1, eye=2, frame=0, seed=40, palm_star=0, lean=-1.5),
             S(dy=0.0, crack=2, eye=1, frame=1, seed=41, palm_star=0, lean=-2.5, palm=(-6.0, -16.0), hand=(6.0, -16.0), staff_ang=-50),
             S(dy=1.0, crack=2, eye=0, frame=2, seed=42, palm_star=0, lean=-3.0, palm=(-6.0, -14.0), hand=(6.0, -14.0), staff_ang=-35,
               fade=0.25, cape_bright=1.0),
             S(dy=2.0, crack=2, eye=0, frame=3, seed=43, palm_star=0, lean=-3.0, palm=(-6.0, -13.0), hand=(6.0, -13.0), staff_ang=-25,
               fade=0.6, cape_bright=1.0),
             astrarch_corpse(0), astrarch_corpse(1)]
    death_d = [0.12, 0.12, 0.12, 0.14, 0.2, 0.3]
    knock = S(dy=-0.5, lean=-3.0, crack=0, eye=2, frame=2, seed=55, palm=(-9.0, -24.0), hand=(5.0, -18.0), staff_ang=-110, palm_star=0)
    portrait = S(dy=-1.0, frame=0, seed=0, palm_star=2, flare=0.3)
    sheet("SilAstrarch", [("Idle", idle, [0.16] * 6), ("Run", run, [0.09] * 6),
                          ("Starshot", shot, shot_d), ("Constellation", con, con_d)] +
          tail(idle[0], death, death_d, knock, portrait), outdir)
    _, a3 = astrarch(**dict(sk[3], dy=-1.0))
    NOTES["SilAstrarch"] = "starshot palm star at %s" % (tuple(round(v, 1) for v in a3["palm"]),)


MONSTERS = [("SilMoonwarden", build_moonwarden), ("SilCometStag", build_comet_stag), ("SilAstrarch", build_astrarch)]

# ======================================================================================= FX
def ring(c, cx, cy, r, ratio, ramp, step=1.0, gap=None, over=True, thick=1):
    """An ellipse ring (floor rings use ratio ~0.45). ramp[0] on the lower-right, ramp[-1] on the upper-left."""
    n = max(12, int(r * 7))
    for k in range(n):
        a = k / n * 2 * math.pi
        if gap and gap(a): continue
        for t in range(thick):
            rr = r - t
            x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr * ratio
            l = -(math.cos(a) + math.sin(a)) / 1.414
            c.put(*P(x, y), pick(ramp, l), over)


def sparks(c, cx, cy, n, r0, r1, seed, chars="θρπ", ratio=1.0, cross=False):
    rnd = random.Random(seed)
    for i in range(n):
        a = rnd.uniform(0, 2 * math.pi); r = rnd.uniform(r0, r1)
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * ratio
        if cross and i % 3 == 0: star4(c, x, y, size=1, ch=chars[1 % len(chars)], core=chars[0])
        else: c.put(*P(x, y), chars[i % len(chars)])


def S_(c):
    return c.spr()


def fx_impact(outdir):
    wall, hit = [], []
    for i in range(5):
        c = Canvas(); r = 1 + i * 1.6
        if i < 4:
            for k in range(8):
                a = k / 8 * 2 * math.pi + 0.3
                L = r + (1.5 if k % 2 == 0 else 0)
                gl(c, math.cos(a) * (r * 0.4), math.sin(a) * (r * 0.4), math.cos(a) * L, math.sin(a) * L, "θηε" if i < 2 else "ζεδ")
        if i <= 1: star4(c, 0, 0, size=2 - i, ch="ρ", core="θ")
        sparks(c, 0, 0, 4 + i, r, r + 2, 3 + i, chars="ηπδ")
        hit.append(S_(c))
        c = Canvas()
        # a wall puff: a half burst opening away from the wall (left)
        for k in range(6):
            a = math.radians(-80 + k * 32)
            L = r + (1 if k % 2 else 0)
            if i < 4: gl(c, 0, 0, math.cos(a) * L, math.sin(a) * L, "θζδ" if i < 2 else "εδγ")
        sparks(c, 2, 0, 3 + i, r * 0.6, r + 1.5, 9 + i, chars="ζπγ")
        wall.append(S_(c))
    fx_sheet("FxSilImpact", [("Wall", wall, [0.04, 0.05, 0.05, 0.06, 0.07]), ("Hit", hit, [0.04, 0.05, 0.05, 0.06, 0.07])], outdir)


def fx_splat(outdir):
    def splat(seed):
        fr = []
        for i in range(4):
            c = Canvas(); rnd = random.Random(seed)
            for k in range(7):
                a = rnd.uniform(-2.6, -0.5); sp = rnd.uniform(2, 5)
                x, y = math.cos(a) * sp * (i + 1) * 0.8, math.sin(a) * sp * (i + 1) * 0.6 + i * i * 0.5
                ch = "θ" if i == 0 else ("ζ" if i < 2 else ("δ" if i < 3 else "γ"))
                c.put(*P(x, y), ch)
                if i < 2 and k % 2: c.put(*P(x + 1, y), "ε")
            if i == 0: star4(c, 0, -1, size=1, ch="η", core="θ")
            fr.append(S_(c))
        return fr
    fx_sheet("FxSilSplat", [("Play", splat(4), [0.05, 0.06, 0.07, 0.08]), ("Play2", splat(11), [0.05, 0.06, 0.07, 0.08])], outdir)


def fx_death(outdir):
    fr = []
    for i in range(7):
        c = Canvas()
        h = 6 + i * 4
        w = max(1.0, 5.0 - i * 0.6)
        if i < 6:
            for y in range(0, -int(h), -1):
                t = -y / h
                ww = w * (1 - t * 0.7)
                for x in range(-int(ww), int(ww) + 1):
                    if (x + y + i) % 2 == 0 or abs(x) < ww * 0.4:
                        c.put(x, y, "θ" if abs(x) < 1 and t < 0.5 and i < 3 else ("ρ" if abs(x) < ww * 0.5 else "π"))
        ring(c, 0, 0, 3 + i * 1.8, 0.4, "δεζη" if i < 4 else "γδ", gap=(lambda a: (int(a * 5) % 2 == 0)) if i > 3 else None)
        sparks(c, 0, -h * 0.6, 3 + i, 2, 4 + i * 1.5, 20 + i, chars="χρπ")
        fr.append(S_(c))
    fx_sheet("FxSilDeath", [("Play", fr, [0.05, 0.06, 0.07, 0.08, 0.08, 0.1, 0.12])], outdir)


# ---- Moonwarden
def fx_glaive(outdir):
    """The glaive's crescent sweep: a thick moonlit arc in front of the warden (origin = its spawn point)."""
    fr = []
    for i in range(5):
        c = Canvas()
        a0, a1 = [(-120, -70), (-110, -10), (-95, 40), (-60, 60), (-10, 65)][i]
        for a in range(a0, a1 + 1, 2):
            t = (a - a0) / max(1, a1 - a0)
            for rr, ch in ((15.0, "ε"), (14.0, "η"), (13.0, "θ" if t > 0.6 else "ζ"), (12.0, "ζ"), (11.0, "δ")):
                if i >= 3 and rr < 13: continue
                if i == 4 and (a // 2) % 2: continue
                c.put(*P(math.cos(math.radians(a)) * rr - 4, math.sin(math.radians(a)) * rr * 0.8), ch, over=False)
        if i in (2, 3): sparks(c, 6, 2, 5, 2, 6, 30 + i, chars="θρν")
        fr.append(S_(c))
    fx_sheet("FxSilGlaive", [("Sweep", fr, [0.04, 0.04, 0.05, 0.06, 0.07])], outdir)


def fx_crescent_wave(outdir):
    fr = []
    for i in range(4):
        c = Canvas()
        crescent(c, 0, 0, 5.5, 180, 2.8 + (i % 2) * 0.4, "ξμνν")
        for k in range(3):
            c.put(-5 - k * 2 - i % 2, -2 + k * 2, "π" if k % 2 else "ρ")
        c.put(2, -4, "θ")
        fr.append(S_(c))
    fx_sheet("FxSilCrescent", [("Fly", fr, [0.06] * 4)], outdir)


def fx_moonfall(outdir):
    """Moonfall at the hero: a shadow ring warns (3), the moon falls (2), it lands in a ring of moonlight (4).
    Three sizes by the warden's moon: Small (crescent), Mid (half), Full."""
    anims = []
    for name, phase, R, H in (("Small", 1.6, 4.6, 26), ("Mid", 2.7, 5.8, 28), ("Full", 4, 7.0, 30)):
        fr = []
        for i in range(9):
            c = Canvas()
            ringr = R * 1.8
            if i < 5:
                ring(c, 0, 0, ringr * (0.6 + 0.2 * min(i, 2)), 0.42, "δεζ" if i % 2 == 0 else "γδε", gap=lambda a: int(a * 4) % 3 == 0)
                ring(c, 0, 0, ringr * 0.35, 0.42, "ξμ")
                if i < 3: c.put(0, 0, "μ")
            if 1 <= i <= 4:
                y = -H + (i - 1) * H / 3.2
                cc = Canvas()
                moon_face(cc, 0, y, R, phase=phase, dark=None if phase < 4 else "β")
                sp = Fr(); sp.b = cc
                for k, v in sp.done(clip=False).px.items(): c.put(k[0], k[1], v)
                for k in range(3): c.put(-1 + k, int(y - R - 2 - k * 2), "ζ" if k != 1 else "η")
            if i >= 5:
                t = i - 5
                ring(c, 0, 0, ringr * (0.8 + t * 0.35), 0.45, "δζην"[::-1][t:] or "δ", thick=2 if t < 2 else 1)
                if t < 2:
                    moon_face(c, 0, -2 + t, R * (0.8 - t * 0.3), phase=phase, dark=None)
                sparks(c, 0, -3, 5 + t * 2, ringr * 0.4, ringr * (0.9 + t * 0.3), 50 + i, chars="νθρ", ratio=0.6, cross=t < 2)
            fr.append(S_(c))
        anims.append((name, fr, [0.16, 0.14, 0.1, 0.08, 0.06, 0.05, 0.06, 0.07, 0.09]))
    fx_sheet("FxSilMoonfall", anims, outdir)


def fx_phase(outdir):
    """The moon over the Moonwarden's head: one anim per phase (New, Crescent, Half, Gibbous, Full), 2 frames each."""
    anims = []
    for ph, name in enumerate(("New", "Crescent", "Half", "Gibbous", "Full")):
        fr = []
        for i in range(2):
            c = Canvas()
            cc = Canvas()
            moon_face(cc, 0, -4, 3.2, phase=ph, dark="τ")
            f = Fr(); f.b = cc
            for k, v in f.done(clip=False).px.items(): c.put(k[0], k[1], v)
            if ph == 4:
                c.put(-5, -8 if i == 0 else -1, "θ"); c.put(5, -1 if i == 0 else -8, "ρ")
            elif i == 1:
                c.put(4, -7, "ρ")
            fr.append(S_(c))
        anims.append((name, fr, [0.3, 0.3]))
    fx_sheet("FxSilPhase", anims, outdir)


# ---- Comet Stag
def fx_antler(outdir):
    fr = []
    for i in range(4):
        c = Canvas()
        # two antler-tine streaks raking up and forward
        for k, off in enumerate((-3, 2)):
            a0 = 150 - i * 30
            for a in range(a0, a0 - 70, -4):
                r = 9 + k * 2
                ch = "θ" if a > a0 - 20 else ("ζ" if a > a0 - 45 else "δ")
                if i == 3 and (a // 4) % 2: continue
                c.put(*P(math.cos(math.radians(a)) * r + off, -math.sin(math.radians(a)) * r * 0.8 - 2), ch, over=False)
        if i < 2: star4(c, 7, -9 + i * 2, size=1, ch="ρ", core="θ")
        fr.append(S_(c))
    fx_sheet("FxSilAntler", [("Slash", fr, [0.04, 0.05, 0.06, 0.07])], outdir)


def fx_comet_trail(outdir):
    fr = []
    for i in range(5):
        c = Canvas()
        L = 14 - i * 2
        if L > 2:
            comet_streak(c, 4, 0, L, 180, w=3.0 - i * 0.5, seed=60 + i, bright=1.0 - i * 0.25)
        sparks(c, 0, 0, 2 + i, 2, 5 + i, 70 + i, chars="ρπε")
        fr.append(S_(c))
    fx_sheet("FxSilCometTrail", [("Play", fr, [0.05, 0.05, 0.06, 0.07, 0.08])], outdir)


def fx_bounce(outdir):
    fr = []
    for i in range(5):
        c = Canvas()
        r = 2 + i * 2.2
        for k in range(8):
            a = k / 8 * 2 * math.pi
            L = r + (2 if k % 2 == 0 else 0)
            if i < 4: gl(c, math.cos(a) * r * 0.3, -12 + math.sin(a) * r * 0.3, math.cos(a) * L, -12 + math.sin(a) * L, "θρπ")
        if i < 3: star4(c, 0, -12, size=3 - i, ch="ρ", core="θ")
        sparks(c, 0, -12, 4 + i * 2, r, r + 3, 80 + i, chars="χρπ", cross=True)
        fr.append(S_(c))
    fx_sheet("FxSilBounce", [("Play", fr, [0.04, 0.05, 0.05, 0.06, 0.08])], outdir)


def fx_charge_burst(outdir):
    fr = []
    for i in range(6):
        c = Canvas()
        r = 3 + i * 2.6
        ring(c, 0, -8, r, 0.8, "πρθ" if i < 3 else "ςπ", gap=(lambda a: int(a * 6) % 2 == 0) if i > 3 else None, thick=2 if i < 2 else 1)
        if i < 3:
            crescent(c, -2, -8, 4.0 - i * 0.6, 0, 2.0, "μνν")
            crescent(c, 2, -8, 4.0 - i * 0.6, 180, 2.0, "μνν")
        sparks(c, 0, -8, 6 + i, r * 0.6, r + 2, 90 + i, chars="θρχ", cross=i < 3)
        fr.append(S_(c))
    fx_sheet("FxSilChargeBurst", [("Play", fr, [0.04, 0.05, 0.05, 0.06, 0.07, 0.08])], outdir)


def fx_antler_glow(outdir):
    """Indicator over the stag's head while its antlers are charged: two little crescent horns and a pulsing star."""
    fr = []
    for i in range(4):
        c = Canvas()
        crescent(c, -3, -4, 3.0, -60, 1.6, "πρρ")
        crescent(c, 3, -4, 3.0, -120, 1.6, "πρρ")
        star4(c, 0, -5, size=1 + (i % 2), ch="χ" if i % 2 else "ρ", core="θ")
        if i in (1, 2): c.put(-6 + i * 4, -9, "θ")
        fr.append(S_(c))
    fx_sheet("FxSilAntlerGlow", [("Loop", fr, [0.12] * 4)], outdir)


# ---- Astrarch
def fx_starshot(outdir):
    fr = []
    for i in range(4):
        c = Canvas()
        star4(c, 0, 0, size=2, ch="χ" if i % 2 else "ρ", core="θ", arm="π")
        if i % 2: c.put(1, -1, "χ"); c.put(-1, 1, "χ")
        else: c.put(1, 1, "ν"); c.put(-1, -1, "ν")
        for k in range(1, 5): c.put(-2 - k, (k % 2) * (1 if i % 2 else -1), "π" if k < 3 else "ς")
        fr.append(S_(c))
    fx_sheet("FxSilStarshot", [("Fly", fr, [0.05] * 4)], outdir)


def fx_star(outdir):
    """A star set into the floor: Land (4), Idle twinkle (4), Burst (5) when the constellation uses it."""
    def base(c, k=0):
        ring(c, 0, 0, 3.0, 0.45, "ςπρ", gap=lambda a: int(a * 3 + k) % 2 == 0)
    land, idle, burst = [], [], []
    for i in range(4):
        c = Canvas()
        y = -9 + i * 3
        if i < 3:
            star4(c, 0, y, size=2, ch="ρ", core="θ", arm="π")
            for kk in range(1, 4 - i): c.put(0, y - kk * 2, "π")
        else:
            base(c); star4(c, 0, -2, size=2, ch="χ", core="θ", arm="ρ"); sparks(c, 0, -1, 5, 2, 5, 100, chars="θρ", ratio=0.5)
        land.append(S_(c))
    for i in range(4):
        c = Canvas(); base(c, i)
        star4(c, 0, -2 - (1 if i == 2 else 0), size=1 + (i % 2), ch="χ" if i % 2 else "ρ", core="θ", arm="π" if i % 2 else None)
        c.put(-3 + i * 2, -5 - (i % 2), "χ" if i % 2 else "π")
        idle.append(S_(c))
    for i in range(5):
        c = Canvas(); r = 2 + i * 2
        ring(c, 0, 0, r, 0.45, "πρθ"[:3 - min(2, i // 2)], thick=1)
        if i < 2: star4(c, 0, -3, size=3, ch="χ", core="θ", arm="ρ")
        for k in range(4): c.put(0, -4 - i * 3 - k * 2, "ρ" if k < 2 else "π")
        sparks(c, 0, -3, 4 + i, r, r + 3, 110 + i, chars="χρ", ratio=0.6)
        burst.append(S_(c))
    fx_sheet("FxSilStar", [("Land", land, [0.05, 0.05, 0.05, 0.1]), ("Idle", idle, [0.16] * 4), ("Burst", burst, [0.05, 0.05, 0.06, 0.07, 0.08])], outdir)


def fx_link(outdir):
    """One dot of a constellation line: it appears, glows, holds and fades (the brain lays a dotted line of them)."""
    fr = []
    for i in range(6):
        c = Canvas()
        ch = ["ς", "π", "ρ", "θ", "ρ", "π"][i]
        c.put(0, 0, ch)
        if i in (2, 3, 4): c.put(1, 0, "π"); c.put(-1, 0, "π")
        if i == 3: c.put(0, -1, "ρ"); c.put(0, 1, "ρ")
        fr.append(S_(c))
    fx_sheet("FxSilLink", [("Play", fr, [0.06, 0.06, 0.1, 0.25, 0.25, 0.1])], outdir)


def fx_starfall(outdir):
    fr = []
    for i in range(7):
        c = Canvas()
        if i < 4:
            y = -34 + i * 9
            star4(c, 0, y, size=1, ch="χ", core="θ")
            for k in range(1, 7): c.put(-k // 3, y - k * 2, "ρ" if k < 3 else "π")
        else:
            t = i - 4
            ring(c, 0, 0, 2 + t * 2.5, 0.45, "πρθ"[t:] or "π")
            if t < 2: star4(c, 0, -2, size=2 - t, ch="χ", core="θ")
            sparks(c, 0, -2, 4 + t * 2, 2, 4 + t * 2, 120 + i, chars="χρπ", ratio=0.6)
        fr.append(S_(c))
    fx_sheet("FxSilStarfall", [("Fall", fr, [0.05, 0.04, 0.04, 0.04, 0.05, 0.06, 0.08])], outdir)


def fx_star_hit(outdir):
    fr = []
    for i in range(6):
        c = Canvas(); r = 4 + i * 2.5
        ring(c, 0, 0, r, 0.45, "ςπρθ"[max(0, 3 - i):] or "ς", thick=2 if i < 3 else 1)
        for k in range(5):
            a = k / 5 * 2 * math.pi + i * 0.3
            star4(c, math.cos(a) * r * 0.8, math.sin(a) * r * 0.36 - 3 - i, size=1 if i < 4 else 0, ch="χ", core="θ")
        if i < 3:
            for y in range(-24, 0, 2): c.put(0, y + i * 3, "ρ" if y > -12 else "π")
        fr.append(S_(c))
    fx_sheet("FxSilStarHit", [("Play", fr, [0.04, 0.05, 0.06, 0.07, 0.08, 0.09])], outdir)


def fx_veil(outdir):
    """Astral Veil (3+ stars out): a ring of slow starlight round the Astrarch's hem and motes rising (body overlay)."""
    fr = []
    for i in range(4):
        c = Canvas()
        ring(c, 0, 0, 13, 0.32, "ςπρ", gap=lambda a, i=i: (int(a * 8 + i * 2) % 4) == 0)
        for k in range(6):
            x = -12 + k * 5 + (i % 2)
            y = -((i * 5 + k * 7) % 22) - 2
            c.put(x, y, "ρ" if (k + i) % 3 else "χ")
            if (k + i) % 2 == 0: c.put(x, y + 1, "π")
        fr.append(S_(c))
    fx_sheet("FxSilVeil", [("Loop", fr, [0.14] * 4)], outdir)


def fx_arrival(outdir):
    """The legendary's arrival: a column of starlight drops, a moonlit ring blooms, stars scatter (9 frames)."""
    fr = []
    for i in range(9):
        c = Canvas()
        if i < 5:
            w = [1, 3, 5, 4, 2][i]
            for y in range(-46, 1):
                for x in range(-w, w + 1):
                    if abs(x) < w * 0.5 or (x + y) % 2 == 0:
                        c.put(x, y, "θ" if abs(x) <= 1 and i in (1, 2, 3) else ("ρ" if abs(x) < w * 0.7 else "π"))
        if i >= 2:
            t = i - 2
            ring(c, 0, 0, 5 + t * 3.5, 0.42, "φδζημ"[max(0, 4 - t):] or "φ", thick=2 if t < 3 else 1)
            if t < 4: ring(c, 0, 0, 3 + t * 2.0, 0.42, "πρθ", gap=lambda a: int(a * 6) % 2 == 0)
        sparks(c, 0, -14, 4 + i * 2, 3 + i, 8 + i * 3, 130 + i, chars="χθρπ", cross=True)
        if 2 <= i <= 4: crescent(c, 0, -30 + i * 2, 5, -90, 2.4, "ξμνν")
        fr.append(S_(c))
    fx_sheet("FxSilArrival", [("Play", fr, [0.05, 0.05, 0.06, 0.06, 0.07, 0.08, 0.08, 0.09, 0.1])], outdir)


FX_ORDER = [("FxSilImpact", fx_impact), ("FxSilSplat", fx_splat), ("FxSilDeath", fx_death), ("FxSilGlaive", fx_glaive),
            ("FxSilCrescent", fx_crescent_wave), ("FxSilMoonfall", fx_moonfall), ("FxSilPhase", fx_phase),
            ("FxSilAntler", fx_antler), ("FxSilCometTrail", fx_comet_trail), ("FxSilBounce", fx_bounce),
            ("FxSilChargeBurst", fx_charge_burst), ("FxSilAntlerGlow", fx_antler_glow), ("FxSilStarshot", fx_starshot),
            ("FxSilStar", fx_star), ("FxSilLink", fx_link), ("FxSilStarfall", fx_starfall), ("FxSilStarHit", fx_star_hit),
            ("FxSilVeil", fx_veil), ("FxSilArrival", fx_arrival)]

FX = FX_ORDER


SYNC = """
## Move anims: sync frames (facing right; spawn points relative to the feet, y up NEGATIVE)

### SilMoonwarden / `Sweep` (7): 0.12, 0.14, 0.05, 0.07, 0.09, 0.12, 0.12
| Frame | Moment | Spawn point |
|---|---|---|
| 0-1 | wind the glaive back over the shoulder (aim free) | - |
| 2 | HIT: ModSilGlaiveHit (24 x 20 box) + the FxSilGlaive arc; at Full moon SilSweepWave throws ModSilCrescentWave | box (16, -11), arc (14, -14) = centred on the hand (10, -14), wave (12, -12) |
| 3 | follow-through, glaive tip (26, -11) | - |

### SilMoonwarden / `Moonfall` (8): 0.12, 0.12, 0.12, 0.10, 0.10, 0.06, 0.14, 0.14
| Frame | Moment | Spawn point |
|---|---|---|
| 2-4 | the moon gathers on the glaive head | - |
| 5 | RELEASE: SilMoonfall drops FxSilMoonfall Small / Mid / Full on the hero (max 150 px) | at hero |

FxSilMoonfall (all three sizes, 9 frames, the C# durations): 0.16, 0.14, 0.10, 0.08, 0.06 (warning ring 0.54 s, the moon falls on
frames 1-4), damage on 5..7 (impact ring). Small 24 x 10 / 0.8, Mid 32 x 13 / 1.2, Full 40 x 16 / 1.6 + daze.

### SilCometStag / `Gore` (7): 0.12, 0.12, 0.06, 0.08, 0.10, 0.12, 0.12
| Frame | Moment | Spawn point |
|---|---|---|
| 3 | HIT: ModSilGoreHit (18 x 18) + FxSilAntler slash; a charged gore also bursts FxSilChargeBurst on the hero | box (19, -12), slash (12, -14) |

### SilCometStag / Comet = `CometRise` (3) + `CometLoop` x6 (18) + `CometEnd` (2)
| Frame | Moment | Spawn point |
|---|---|---|
| 2 | can't be hit from here | - |
| 3 | SilCometStart: flight at 230 px/s, 3 wall bounces (FxSilBounce at each), FxSilCometTrail every 0.05 s; ModSilCometHit attached (0.9 per 0.4 s) | body (4, -12), trail centred (0, -12) |
| 21 | SilCometEnd: lands, hittable again | - |

### SilAstrarch / `Starshot` (7): 0.10, 0.10, 0.10, 0.05, 0.09, 0.12, 0.12
| Frame | Moment | Spawn point |
|---|---|---|
| 3 | RELEASE: ModSilStarshot on the floor line under the palm (art 14 px up); where it stops it sets ModSilStar | (9, -1), palm star (9, -24) |

### SilAstrarch / `Constellation` (9): 0.10, 0.10, 0.10, 0.12, 0.12, 0.06, 0.12, 0.12, 0.12
| Frame | Moment | Spawn point |
|---|---|---|
| 2-4 | arms raised, halo flares, the cape's stars join up | - |
| 5 | RELEASE: SilConstellation: dotted FxSilLink outline of her stars (0.04 s an edge), 0.8 s later FxSilStarfall over the shape; 0.18 s on the hero inside takes ModSilStarHit | at the stars / the hero |

## FX sheets (origin = the pixel Strike.ArtAt / Strike.Ground put on the effect's transform)
"""


def write_timing(outdir):
    rows = ["# Silver uniques: sprite timing", "",
            "Generated by `tools/sprites/silver_rigs.py`. Frame indices are 0-based. Monsters face right; feet = (cellW//2, cellH-2).",
            "Drawn at final size (no ArtScale entry).", "", "## Monster sheets", "",
            "| Sheet | Cell (w x h) | Feet | Anims (frames) |", "|---|---|---|---|"]
    for n, _ in MONSTERS:
        if n not in BUILT: continue
        b = BUILT[n]
        rows.append("| %s | %d x %d | (%d, %d) | %s |" % (n, b["cell"][0], b["cell"][1], b["feet"][0], b["feet"][1],
                                                         ", ".join("%s %d" % (a, k) for a, k, _ in b["anims"])))
    rows.append(SYNC)
    rows += ["| Sheet | Cell | Origin | Anims |", "|---|---|---|---|"]
    for n, _ in FX_ORDER:
        if n not in BUILT: continue
        b = BUILT[n]
        rows.append("| %s | %d x %d | (%d, %d) | %s |" % (n, b["cell"][0], b["cell"][1], b["feet"][0], b["feet"][1],
                                                         ", ".join("%s %d" % (a, k) for a, k, _ in b["anims"])))
    open(os.path.join(outdir, "TIMING.md"), "w").write("\n".join(rows) + "\n")


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    only = None
    if "--only" in a:
        i = a.index("--only"); only = set(a[i + 1].split(",")); del a[i:i + 2]
    outdir = a[0] if a else DEFAULT_OUT
    os.makedirs(outdir, exist_ok=True)
    for n, fn in MONSTERS + FX:
        if only is None or n in only: fn(outdir)
    for k, v in NOTES.items(): print("  %s: %s" % (k, v))
    for n, _ in FX_ORDER:
        if n in BUILT: print("  %-18s cell %s origin %s" % (n, BUILT[n]["cell"], BUILT[n]["feet"]))
    if only is None: write_timing(outdir)


if __name__ == "__main__":
    main()
