"""THE GILDED SECRET: a hidden gold monster line offered only in the gold idol's 4th starter slot.

    python3 goldsecret_rigs.py [outdir] [--only Name,Name]       (default outdir art/out_goldsecret)

Tree (a true binary tree, nothing shared):
  Coffer Mimic (T1) -> Vault Warden (T2) {Hoard Wyrm, Vault Colossus}
                    -> Gilt Regent  (T2) {Gilded Sovereign, Grand Treasurer}

Look: a gilded treasure chest that bites, and what it grows into. Gold leaf and iron bands over dark wood, crimson
velvet and ermine for the regal branch, an emerald keyhole that glows like an eye (the line's signature: every
monster keeps it), ivory fangs on every lid and jaw. Palette is the line's own (Armenian-letter keys below), lit from
the top-left, 1 px dark-umber outline, glow pixels laid last.

Same method as belmora_tree.py: every frame is a fresh re-posed drawing from shaded primitives (belmora_rigs: ell,
tube, poly, line), monsters face right, feet at (cellW//2, cellH-2). FX: origin = (cellW//2, h) printed per sheet.
"""
import math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import belmora_rigs as B          # noqa: E402  (primitives, sheet writer)
import belmora_tree as BT         # noqa: E402  (gl, rot, lay_down)
from rig import Canvas, line_px   # noqa: E402
from anim import Spr, PALETTE     # noqa: E402
from ghosts_v2_kit import selout_anims  # noqa: E402

ell, tube, line, poly, P = B.ell, B.tube, B.line, B.poly, B.P
gl, rot = BT.gl, BT.rot
DEFAULT_OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "art", "out_goldsecret")

PALETTE.update({
    'ա': (0x24, 0x16, 0x10),   # outline: dark umber
    # gold leaf, dark -> light
    'բ': (0x5e, 0x3a, 0x12), 'գ': (0x9c, 0x68, 0x1c), 'դ': (0xd8, 0xa2, 0x30), 'ե': (0xf6, 0xd2, 0x5a), 'զ': (0xff, 0xf2, 0xb0),
    # crimson velvet
    'է': (0x52, 0x12, 0x20), 'ը': (0x8e, 0x22, 0x32), 'թ': (0xc6, 0x3c, 0x48),
    # ermine / ivory
    'ժ': (0x90, 0x88, 0x7c), 'ի': (0xd4, 0xcc, 0xba), 'լ': (0xf6, 0xf2, 0xe4),
    # iron / black lacquer
    'խ': (0x30, 0x2c, 0x32), 'ծ': (0x50, 0x4a, 0x52), 'կ': (0x7a, 0x72, 0x76),
    # chest wood
    'հ': (0x4e, 0x2c, 0x18), 'ձ': (0x7c, 0x48, 0x26), 'ղ': (0xa6, 0x68, 0x38),
    # emerald (the keyhole eye)
    'ճ': (0x12, 0x5c, 0x3c), 'մ': (0x34, 0xb8, 0x70), 'յ': (0xa8, 0xff, 0xcc),
    # mouth and tongue
    'ն': (0x32, 0x0a, 0x16), 'շ': (0xb8, 0x46, 0x66), 'ո': (0xf0, 0x92, 0xaa),
    # sapphire
    'չ': (0x1e, 0x32, 0x84), 'պ': (0x4a, 0x80, 0xea), 'ջ': (0xbc, 0xdc, 0xff),
    # sparkle
    'ռ': (0xff, 0xff, 0xf2),
    # molten gold (hot end)
    'ս': (0xa8, 0x3c, 0x10), 'վ': (0xff, 0x8c, 0x22),
    # ink
    'տ': (0x1e, 0x14, 0x28), 'ր': (0x44, 0x2e, 0x60),
    # parchment
    'ց': (0xb4, 0x98, 0x6c), 'ւ': (0xec, 0xdc, 0xb4),
    # ruby
    'փ': (0x7c, 0x08, 0x1a), 'ք': (0xec, 0x30, 0x4c),
})
OUT = 'ա'
# Crawl's palette: the line's gold is old and grimy; the emerald keyhole eye is its one bright accent
from ghosts_v2_kit import mute_palette  # noqa: E402
mute_palette(PALETTE, "բգդեզէըթժիլխծկհձղնշոչպջռսվտրցւփք", sat=0.62)
GOLD = "բգդե"
GOLD_L = "գդեզ"
CRIM = "էըթ"
ERM = "ժիլ"
IRON = "խծկ"
WOOD = "հձղ"
EMER = "ճմյ"
SAPH = "չպջ"
PARCH = "ցւլ"
MOLT = "սվեզ"
INK = "տր"
FANG = "իլ"


# ------------------------------------------------------------------ frame canvas with the line's outline colour
class Fr(B.Fr):
    def done(self, outline=True, clip=True):
        base = dict(self.u.px)
        base.update(self.b.px)
        spr = Spr(base)
        if outline: spr = B.outl(spr, OUT)
        px = dict(self.n.px)
        px.update(spr.px)
        px.update(self.g.px)
        if clip: px = {k: v for k, v in px.items() if k[1] <= 0}
        return Spr(px)


def outl(spr):
    return B.outl(spr, OUT)


def paste(c, spr, dx=0, dy=0, over=True):
    for (x, y), v in spr.px.items(): c.put(x + dx, y + dy, v, over)


def rect(c, x0, y0, x1, y1, ramp, bias=0.0, over=True):
    """Filled box lit from the top-left (inclusive integer bounds)."""
    w, h = max(1, x1 - x0), max(1, y1 - y0)
    for y in range(int(y0), int(y1) + 1):
        for x in range(int(x0), int(x1) + 1):
            u, v = (x - x0) / w, (y - y0) / h
            l = 0.55 - 0.9 * (u * 0.45 + v * 0.75) + bias
            c.put(x, y, B.pick(ramp, l), over)


def lay_down(spr, deg=-80):
    return BT.lay_down(spr, deg)


def sparkle(c, x, y, size=1, ch='ռ', arm='ե'):
    """A four-point star glint."""
    x, y = P(x, y)
    c.put(x, y, ch)
    for k in range(1, size + 1):
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            c.put(x + dx, y + dy, arm if k == size else ch)


def keyhole(c, x, y, glow=1, big=False):
    """The line's signature: an emerald keyhole eye on a gold plate."""
    x, y = P(x, y)
    if big:
        for dy in (-2, -1, 0, 1, 2):
            for dx in (-2, -1, 0, 1, 2):
                if abs(dx) + abs(dy) <= 3: c.put(x + dx, y + dy, 'ե' if dx + dy < 0 else 'դ' if dx + dy < 2 else 'գ')
        c.put(x, y - 1, 'ճ' if not glow else 'մ'); c.put(x, y, 'ճ' if not glow else 'յ' if glow > 1 else 'մ'); c.put(x, y + 1, 'ճ')
        return
    c.put(x - 1, y, 'դ'); c.put(x + 1, y, 'գ'); c.put(x, y - 1, 'ե'); c.put(x, y + 1, 'գ')
    c.put(x, y, 'յ' if glow > 1 else 'մ' if glow else 'ճ')


def fangs(c, x0, x1, y, dirn=-1, step=2, ln=1, ramp=FANG, off=0):
    """A row of ivory fangs pointing up (dirn -1) or down (+1) along y from x0 to x1."""
    x = int(round(x0)) + off
    while x <= int(round(x1)):
        for k in range(ln + 1):
            c.put(x, int(round(y)) + dirn * k, ramp[min(len(ramp) - 1, k)] if dirn < 0 else ramp[max(0, len(ramp) - 1 - k)])
        x += step


def claw_leg(c, hx, hy, fx, fy, ramp=GOLD, out=1.0, knee_up=2.5):
    """A short jointed claw leg: hip -> knee (out and up) -> clawed foot."""
    kx, ky = (hx + fx) / 2 + out * (1 if fx >= hx else -1), min(hy, fy) - knee_up + (hy + fy) / 2 - min(hy, fy)
    tube(c, [(hx, hy), (kx, ky), (fx, fy)], [0.9, 0.7, 0.5], ramp, bias=0.1)
    c.put(*P(fx + (1 if fx >= hx else -1), fy), ramp[0])


BUILT = {}
NOTES = {}


def sheet(name, anims, outdir, scale=6):
    B.sheet(name, selout_anims(anims), outdir, scale=scale)
    BUILT[name] = B.BUILT[name]


def fx_sheet(name, anims, outdir, scale=6):
    B.fx_sheet(name, selout_anims(anims), outdir, scale=scale)
    BUILT[name] = B.BUILT[name]


def tail(idle0, death, death_d, knock):
    return B.std_tail(idle0, death, death_d, knock)


# ------------------------------------------------------------------ death: collapse, coins spilling, the gold dulling
def _tarnish_ramp():
    """Each gold-leaf char -> (half dulled, fully dulled): the leaf browns and greys as the line's magic goes out."""
    mud = (0x5a, 0x4c, 0x3c)
    out = {}
    for i, ch in enumerate("բգդեզ"):
        c = PALETTE[ch]
        steps = []
        for k in (0.35, 0.7):
            cc = tuple(int(c[j] + (mud[j] - c[j]) * k) for j in range(3))
            key = chr(0x2C00 + i * 2 + len(steps))
            PALETTE[key] = cc
            steps.append(key)
        out[ch] = steps
    return out


TARNISH = _tarnish_ramp()
DIM_GEM = {'յ': 'ճ', 'մ': 'ճ', 'ջ': 'չ', 'պ': 'չ', 'ք': 'փ', 'ռ': 'ե'}


def tarnish(spr, k):
    """k = 0 (bright) .. 2 (dull): the gold leaf darkens toward umber, gems and glints go out."""
    if k <= 0: return spr
    m = {ch: v[k - 1] for ch, v in TARNISH.items()}
    m.update(DIM_GEM)
    return Spr({p: m.get(v, v) for p, v in spr.px.items()})


def coin_at(c, x, y, flat=False, k=0):
    """A gold coin: face-on in the air (3 x 2), flat on the floor (3 x 1); k = 1 tarnished."""
    x, y = P(x, y)
    hi, mid, lo = ('ե', 'դ', 'գ') if not k else (TARNISH['ե'][0], TARNISH['դ'][0], TARNISH['գ'][0])
    if flat:
        c.put(x - 1, y, mid); c.put(x, y, hi); c.put(x + 1, y, lo)
        return
    c.put(x, y - 1, hi); c.put(x - 1, y, mid); c.put(x, y, mid); c.put(x + 1, y, lo); c.put(x + 1, y - 1, mid)


def with_coins(spr, air=(), floor=(), k=0, pile=None):
    """spr plus coins in the air, coins lying on the floor and an optional heap (x, width) in front."""
    c = Canvas()
    for p_, v in spr.px.items(): c.put(*p_, v)
    if pile:
        x0, w = pile
        for i in range(int(w)):
            h = int(round(2.2 * (1 - abs(i - w / 2.0) / (w / 2.0 + 0.5))))
            for j in range(h + 1):
                c.put(int(x0 + i), -j, ('դ' if (i + j) % 2 else 'ե') if not k else TARNISH['դ'][0 if (i + j) % 2 else 1])
            c.put(int(x0 + i), -h - 1, 'գ' if not k else TARNISH['գ'][1], over=False)
    for (x, y) in air: coin_at(c, x, y, k=k)
    for (x, y) in floor: coin_at(c, x, y, flat=True, k=k)
    return Spr(c.px)


def topple(spr, deg, piv):
    """Fall forward about a pivot on the floor (the front foot), then sit back on the floor line."""
    return B.grounded(rot(spr, deg, piv))


def gold_death(recoil, buckle, slump, down, fx, air, deg=(35.0, 78.0)):
    """Death 4: recoil (0), buckle with coins bursting out (1), topple forward over the front foot as the gold dulls (2),
    face down in a spill of tarnished coins (3). recoil/buckle/slump/down are freshly posed frames; fx = the front foot;
    deg = how far frames 2 and 3 tip forward."""
    return [recoil,
            with_coins(buckle, air=air),
            with_coins(tarnish(topple(slump, deg[0], (fx, 0.0)), 1),
                       air=[(x + 5, y + 6) for (x, y) in air[:2]], floor=[(fx + 6, 0), (fx - 2, 0)]),
            with_coins(tarnish(topple(down, deg[1], (fx, 0.0)), 2), floor=[(fx + 10, 0), (fx - 6, 0), (fx + 15, 0)],
                       pile=(fx + 3, 6), k=1)]


# ================================================================== COFFER MIMIC (T1)
def chest_lid(L=13, H=3.4, band=True, teeth=True, shut=False):
    """The lid in hinge space: hinge at (0, 0), lid running right along +x, arched up (y negative)."""
    c = Canvas()
    for x in range(0, L + 1):
        u = x / float(L)
        top = -H * math.sqrt(max(0.0, 1 - (2 * u - 1) ** 2 * 0.55))
        for y in range(int(math.floor(top)), 1):
            v = (y - top) / max(0.5, -top)
            l = 0.7 - u * 0.5 - v * 0.9
            c.put(x, y, B.pick(WOOD, l))
        c.put(x, int(math.floor(top)), 'դ' if u < 0.6 else 'գ')            # gilded rim along the arch
    if band:
        for bx in (2, L - 3):
            for y in range(-int(H) - 1, 1):
                if (bx, y) in c.px: c.put(bx, y, 'ե' if y < -1 else 'դ')
    for x in range(0, L + 1): c.put(x, 0, 'գ' if x % 4 else 'դ')        # gold lip
    if teeth and not shut:
        for x in range(3, L, 2): c.put(x, 1, 'լ'); c.put(x, 2, 'ի') if x % 4 == 1 else None
    return c.spr()


def mimic(dx=0.0, dy=0.0, lid=8.0, ph=0.0, stride=0.0, tongue=0.0, glint=0, eye=1, crouch=0.0, pitch=0.0,
          legs_in=0.0, shut=False, dark=False, gold_glow=1, spill=0, clamp=0, bite=None, reach=0.0):
    """The Coffer Mimic: a gilded, iron-banded chest on four claw legs. lid = opening angle (deg); tongue 0..1 lolls
    out of the front; eye = keyhole glow (0 dark .. 2 bright); legs_in tucks the legs under (play dead).
    pitch tips the whole chest about its front foot (+ = nose down, - = rearing up); reach stretches the legs (a lunge);
    clamp shows the fangs locked across the shut seam; bite = (x, y) of the snap flash, from the front of the lid lip."""
    f = Fr()
    bx0, bx1 = -6 + dx, 6 + dx
    by1 = -3.0 + dy + crouch * 0.5 + legs_in * 2.6 - reach
    by0 = by1 - 6
    # ---- legs: far pair dim behind (no outline), near pair in front; a scuttling diagonal gait
    legs = [(-3.5, -5.5, 0.0, f.n), (3.5, 5.5, math.pi, f.n), (-4.5, -7.0, math.pi, f.u), (4.5, 7.0, 0.0, f.u)]
    for k, (hx, fx, off, lay) in enumerate(legs):
        lift = max(0.0, math.sin(ph + off)) * 1.6 * stride
        foot = (dx + fx * (1 - legs_in * 0.45) + stride * 1.6 * math.cos(ph + off), -lift + (0 if not legs_in else -0.0))
        hip = (dx + hx, by1 - 0.5)
        if legs_in > 0.5: continue                                    # folded away inside: a plain chest on the floor
        ramp = "բգ" if lay is f.n else GOLD
        claw_leg(lay, hip[0], hip[1], foot[0], foot[1], ramp, out=1.0, knee_up=1.6 + crouch * 0.4)
    # ---- the box
    rect(f.b, bx0, by0, bx1, by1, WOOD, bias=0.15)
    for x in range(int(bx0), int(bx1) + 1):                       # gold rims top / bottom
        f.b.put(x, int(by0), 'ե' if x < bx0 + 6 else 'դ'); f.b.put(x, int(by1), 'գ')
    for bx in (bx0 + 2, bx1 - 2):                                  # iron bands with gold rivets
        for y in range(int(by0) + 1, int(by1)):
            f.b.put(int(bx), y, 'ծ' if y > by0 + 2 else 'կ')
        f.b.put(int(bx), int(by0) + 2, 'ե'); f.b.put(int(bx), int(by1) - 1, 'դ')
    for x, y in ((bx0, by0), (bx1, by0), (bx0, by1), (bx1, by1)):   # corner caps
        f.b.put(int(x), int(y), 'ե' if (x, y) == (bx0, by0) else 'դ')
    keyhole(f.b, dx + 0.0, by0 + 3.0, glow=eye)
    # ---- mouth: open lid shows the dark maw lined with fangs and a gleam of treasure
    hinge = (bx0 - 0.0, by0)
    a = -lid
    if lid > 4 and not shut:
        depth = min(4.0, lid / 9.0)
        for x in range(int(bx0) + 1, int(bx1)):
            for y in range(int(round(by0 - depth)), int(by0) + 1):
                if y < by0: f.b.put(x, y, 'ն')
        if gold_glow:
            for k in range(4):
                gx = int(bx0) + 3 + k * 2
                f.b.put(gx, int(by0) - 1, 'ե' if (k + gold_glow) % 2 else 'դ')
            f.g.put(int(bx0) + 5, int(by0) - 1, 'զ')
        fangs(f.b, bx0 + 2, bx1 - 1, by0 - 1, dirn=-1, step=2, ln=1 if lid > 18 else 0, off=0)
    if clamp:
        # jaws locked: fangs from both lips cross the seam on the front half, the front tooth juts out past the lip
        for x in range(int(bx0) + 5, int(bx1) + 1, 2):
            f.g.put(x, int(by0) - 1, 'լ'); f.g.put(x + 1, int(by0) + 1, 'լ'); f.g.put(x + 1, int(by0) + 2, 'ի')
        f.g.put(int(bx1) + 1, int(by0), 'լ'); f.g.put(int(bx1) + 1, int(by0) + 1, 'ի')
    # ---- the lid, rotated about the hinge
    ls = chest_lid(L=int(bx1 - bx0), teeth=lid > 6 and not shut, shut=shut)
    ls = rot(ls, a, (0.0, 0.0))
    for (x, y), v in ls.px.items():
        f.b.put(int(x + hinge[0]), int(y + hinge[1]), v)
    # ---- tongue: a crimson tongue lolling out over the front lip
    if tongue > 0 and lid > 6 and not shut:
        n = int(2 + tongue * 5)
        for i in range(n):
            t = i / max(1, n - 1)
            x = bx1 - 3 + i * 0.9
            y = by0 - 1 + math.sin(t * 2.6) * 1.8 * tongue + t * 3.5 * tongue
            f.b.put(*P(x, y), 'շ'); f.b.put(*P(x, y + 1), 'ո' if i < n - 1 else 'շ')
    if glint: sparkle(f.g, bx0 + 1 + glint * 2, by0 - 0.5, 1)
    if spill:
        for k in range(spill):
            f.g.put(*P(bx1 + 1 + k * 1.5, by0 - 2 + (k % 2)), 'ե' if k % 2 else 'զ')
    if bite is not None:
        # the snap: a white flash with short bite lines, drawn on the body so it moves with the jaws
        sx, sy = bx1 + bite[0], by0 + bite[1]
        sparkle(f.g, sx, sy, 2)
        for ddx, ddy in ((2, -2), (2, 2), (3, 0)):
            f.g.put(*P(sx + ddx * 1.2, sy + ddy * 1.2), 'ե')
    out = f.done(clip=not pitch)
    if pitch:
        out = rot(out, pitch, (bx1 + 1.0, 0.0))
        out = Spr({k: v for k, v in out.px.items() if k[1] <= 0})
    if dark:
        return Spr({k: ('ճ' if v in ('յ', 'մ') else v) for k, v in out.px.items()})
    return out


SNAP_T = [0.1, 0.12, 0.06, 0.1, 0.1, 0.1, 0.12]


def build_mimic(outdir):
    M = mimic
    idle = [M(lid=4), M(lid=7, tongue=0.3, dy=-0.4), M(lid=9, tongue=0.5, eye=2, glint=2, dy=-0.4), M(lid=6, tongue=0.2)]
    run = [M(ph=i * math.pi / 3, stride=1.0, lid=5 + 3 * abs(math.sin(i * math.pi / 3)), dy=-0.6 * abs(math.sin(i * math.pi / 3)),
             tongue=0.2 if i % 2 else 0.0) for i in range(6)]
    # SNAP: rear back and gape, lunge nose-first with the jaws wide, slam them shut on the hero (HIT f3: fangs locked
    # across the seam and the snap flash at the front lip, all on the body), chew a stolen coin, settle back.
    snap = [M(lid=14, crouch=1.0, eye=2, pitch=-6), M(lid=50, crouch=1.4, eye=2, tongue=0.8, dx=-0.5, pitch=-12),
            M(lid=72, dx=2.0, eye=2, tongue=1.0, pitch=10, reach=1.0, stride=0.6),
            M(lid=3, dx=3.0, eye=2, pitch=8, reach=0.6, clamp=1, bite=(2.0, 0.0)),
            M(lid=7, dx=2.5, eye=2, pitch=4, spill=2), M(lid=4, dx=1.5, glint=2), M(lid=4, dx=0.5)]
    # up / down variants (same frames and timing): the bite goes where it aims
    snap_up = [M(lid=14, crouch=1.2, eye=2), M(lid=50, crouch=1.6, eye=2, tongue=0.8, pitch=-6),
               M(lid=88, dy=-2.0, eye=2, tongue=1.0, pitch=-8, reach=1.6, stride=0.4),
               M(lid=3, dy=-3.0, dx=0.5, eye=2, pitch=-10, reach=1.4, clamp=1, bite=(-2.0, -3.5)),
               M(lid=7, dy=-1.5, eye=2, pitch=-4, spill=2), M(lid=4, glint=2), M(lid=4)]
    snap_dn = [M(lid=14, crouch=1.0, eye=2, pitch=-4), M(lid=50, crouch=1.2, eye=2, tongue=0.8, pitch=-10),
               M(lid=60, dx=1.5, eye=2, tongue=1.0, pitch=22, stride=0.6),
               M(lid=3, dx=2.0, eye=2, pitch=26, clamp=1, bite=(2.5, 3.0)),
               M(lid=7, dx=1.5, eye=2, pitch=12, spill=2), M(lid=4, dx=1.0, glint=2), M(lid=4, dx=0.5)]
    # FEIGN (special): the lid shuts, the legs fold away and it lies there as a plain treasure chest; Lurk loops while
    # it waits; Spring is the ambush lunge (the bite box goes live on f1, the jaws lock on f2 with the snap flash).
    feign = [M(lid=2, legs_in=0.3, eye=1), M(lid=0, legs_in=0.7, eye=0, shut=True), M(lid=0, legs_in=1.0, eye=0, shut=True, glint=1)]
    lurk = [M(lid=0, legs_in=1.0, eye=0, shut=True, glint=2), M(lid=0, legs_in=1.0, eye=0, shut=True),
            M(lid=0, legs_in=1.0, eye=0, shut=True, glint=3), M(lid=0, legs_in=1.0, eye=0, shut=True)]
    spring = [M(lid=65, legs_in=0.3, eye=2, tongue=1.0, dy=-1.0, spill=3, pitch=-10),
              M(lid=85, dx=2.5, dy=-1.5, eye=2, tongue=1.0, pitch=12, reach=1.2, stride=0.8),
              M(lid=3, dx=4.0, eye=2, pitch=10, reach=0.6, clamp=1, bite=(2.0, 0.0)),
              M(lid=9, dx=3.0, eye=2, pitch=4, tongue=0.5, spill=2), M(lid=4, dx=1.0)]
    death = gold_death(M(lid=40, eye=2, tongue=1.0, dy=-1.0), M(lid=75, eye=1, tongue=1.0, crouch=2.0, legs_in=0.4, spill=3),
                       M(lid=95, eye=0, tongue=1.0, dark=True, legs_in=0.7, crouch=2.0),
                       M(lid=110, eye=0, tongue=1.0, dark=True, legs_in=1.0, crouch=2.5), 6.0,
                       [(-3.0, -16.0), (3.0, -18.0), (8.0, -14.0)], deg=(18.0, 0.0))
    knock = M(lid=25, dx=-1.0, dy=-1.0, eye=2, tongue=0.6)
    anims = [("Idle", idle, [0.22, 0.18, 0.22, 0.18]), ("Run", run, [0.07] * 6),
             ("Snap", snap, SNAP_T), ("SnapUp", snap_up, SNAP_T), ("SnapDown", snap_dn, SNAP_T),
             ("Feign", feign, [0.1, 0.12, 0.14]), ("Lurk", lurk, [0.3, 0.3, 0.3, 0.3]),
             ("Spring", spring, [0.04, 0.05, 0.08, 0.12, 0.12])]
    anims += tail(idle[0], death, [0.08, 0.12, 0.16, 0.4], knock)
    sheet("GoldMimic", anims, outdir)


# ================================================================== VAULT WARDEN (T2, Coffer Mimic line)
def big_key(c, x, y, ang, L=12.0, bow=2.6, glint=False, ramp=GOLD):
    """A great gold key gripped at (x, y): the ring bow sits behind the grip, the shaft runs along ang for L px
    and ends in a toothed bit. Returns the bit's tip."""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    bx, by = x - ux * (bow + 0.8), y - uy * (bow + 0.8)
    ell(c, bx, by, bow, bow, ramp, bias=0.25)
    ell(c, bx, by, bow * 0.45, bow * 0.45, "ա", over=True)            # the ring's hole
    tip = (x + ux * L, y + uy * L)
    tube(c, [(x, y), tip], [0.9, 0.8], ramp, bias=0.2)
    for k in (1.0, 2.6, 3.8):                                          # bit teeth hang off one side of the shaft
        tx, ty = x + ux * (L - k), y + uy * (L - k)
        for j in range(1, 3 if k != 2.6 else 4):
            c.put(*P(tx + nx * j, ty + ny * j), 'դ' if j == 1 else 'գ')
    if glint: c.put(*P(x + ux * L * 0.5 - nx * 0.6, y + uy * L * 0.5 - ny * 0.6), 'զ')
    return tip


def chain_links(c, p0, p1, phase=0, sag=0.0):
    """An iron chain from p0 to p1 (alternating link pixels), sagging by sag px in the middle."""
    n = max(2, int(math.hypot(p1[0] - p0[0], p1[1] - p0[1])))
    for i in range(n + 1):
        t = i / float(n)
        x = p0[0] + (p1[0] - p0[0]) * t
        y = p0[1] + (p1[1] - p0[1]) * t + sag * 4 * t * (1 - t)
        c.put(*P(x, y), 'կ' if (i + phase) % 2 else 'ծ')


def warden(dx=0.0, dy=0.0, ph=0.0, stride=0.0, lean=0.0, jaw=12.0, eye=1, near=(8.0, -10.0), far=(-7.0, -10.0),
           key_ang=68.0, key=True, chain_to=None, crouch=0.0, glint=False, dark=False, spark=0):
    """The Vault Warden: the chest grown into a squat brute. Torso = an iron-banded strongbox, head = its fanged lid
    with the keyhole eye, iron arms with gold gauntlets, a great gold key in the near fist."""
    f = Fr()
    hip_y = -5.5 + crouch + dy
    sk = math.tan(math.radians(lean))
    T = lambda x, y: (dx + x + sk * (hip_y - y), y)
    # legs: thick iron with gold knee caps
    feet = ((-3.5 + stride * 2.8 * math.cos(ph), max(0.0, math.sin(ph)) * 1.8 * stride),
            (3.5 - stride * 2.8 * math.cos(ph), max(0.0, -math.sin(ph)) * 1.8 * stride))
    for k, (fx, fy) in enumerate(feet):
        hp = (dx + (-2.8 if k == 0 else 2.8), hip_y)
        ft = (dx + fx, -fy)
        (kx, ky), _ = B.ik(hp[0], hp[1], ft[0], ft[1], 3.1, 3.1, bend=-1)
        lay = f.u if k == 0 else f.b
        tube(lay, [hp, (kx, ky), ft], [2.0, 1.7, 1.5], "խծ" if k == 0 else IRON, bias=0.1)
        lay.put(*P(kx + 0.5, ky), 'դ'); lay.put(*P(kx - 0.5, ky), 'գ')
        gl(lay, ft[0] - 2, ft[1], ft[0] + 2.5, ft[1], "խծ")                        # iron boot
    # far arm (behind)
    sh_f = T(-5.5, hip_y - 7.5)
    (ex, ey), _ = B.ik(sh_f[0], sh_f[1], dx + far[0], far[1] + crouch, 4.5, 4.0, bend=1)
    tube(f.u, [sh_f, (ex, ey), (dx + far[0], far[1] + crouch)], [1.8, 1.5, 1.3], "խծ", bias=0.1)
    ell(f.u, dx + far[0], far[1] + crouch, 2.0, 1.8, "բգ", bias=0.2)
    # torso: the strongbox (slightly trapezoid, wider at the shoulders)
    x0, x1 = -6.5, 6.5
    ty0, ty1 = hip_y - 9, hip_y
    for y in range(int(ty0), int(ty1) + 1):
        w = 0.6 * (ty1 - y) / 9.0
        a0, a1 = T(x0 - w, y)[0], T(x1 + w, y)[0]
        for x in range(int(round(a0)), int(round(a1)) + 1):
            u, v = (x - a0) / (a1 - a0), (y - ty0) / 9.0
            f.b.put(x, y, B.pick(WOOD, 0.6 - u * 0.5 - v * 0.8 + 0.1))
    for y in range(int(ty0), int(ty1) + 1):                         # iron bands + gold rivets
        for bxx in (-3.5, 3.0):
            f.b.put(*P(*T(bxx, y)), 'ծ' if y > ty0 + 2 else 'կ')
        if (y - int(ty0)) % 3 == 1:
            f.b.put(*P(*T(-3.5, y)), 'դ'); f.b.put(*P(*T(3.0, y)), 'դ')
    for x in range(int(x0) - 1, int(x1) + 2):
        f.b.put(*P(*T(x, ty0)), 'ե' if x < 0 else 'դ'); f.b.put(*P(*T(x, ty1)), 'գ')
        f.b.put(*P(*T(x, ty0 + 4)), 'գ' if x % 3 else 'դ')                             # the old lid line, a gold belt
    keyhole(f.b, *T(0.0, ty0 + 6.5), glow=0 if dark else 1)                            # the old keyhole: now a lock on its belly
    # head: the lid, hinged at the back of the shoulders, opening as a jaw over a dark wedge of maw
    hinge = T(x0 - 0.5, ty0)
    ja = math.radians(jaw)
    if jaw > 3:
        for x in range(int(T(x0, ty0)[0]) + 1, int(T(x1, ty0)[0]) + 1):
            depth = (x - hinge[0]) * math.tan(ja) * 0.9
            for y in range(int(round(ty0 - depth)), int(ty0)):
                f.b.put(x, y, 'ն')
            if depth > 1.5 and x % 2 == 0: f.b.put(x, int(round(ty0 - 1)), 'լ')          # lower fangs
        if jaw > 14: f.b.put(int(T(x1, ty0)[0]) - 3, int(ty0) - 1, 'շ')                  # tongue tip
    lid = chest_lid(L=int(x1 - x0) + 2, H=4.4, teeth=jaw > 4)
    lid = rot(lid, -jaw, (0.0, 0.0))
    for (x, y), v in lid.px.items(): f.b.put(int(round(x + hinge[0])), int(round(y + hinge[1])), v)
    # the keyhole eye on the lid's front face
    ex_, ey_ = 9.5 * math.cos(-ja) + 2.4 * math.sin(-ja), 9.5 * math.sin(-ja) - 2.4 * math.cos(-ja)
    ec = (hinge[0] + ex_, hinge[1] + ey_)
    keyhole(f.b, ec[0], ec[1], glow=0 if dark else max(1, eye), big=True)
    if eye >= 2 and not dark: f.g.put(*P(ec[0], ec[1]), 'յ')
    # near arm (in front) with the key
    sh_n = T(5.5, hip_y - 7.5)
    hand = (dx + near[0], near[1] + crouch)
    (ex, ey), _ = B.ik(sh_n[0], sh_n[1], hand[0], hand[1], 4.5, 4.0, bend=-1)
    tube(f.b, [sh_n, (ex, ey), hand], [2.0, 1.7, 1.5], IRON, bias=0.15)
    f.b.put(*P(ex, ey), 'դ')
    ell(f.b, sh_n[0], sh_n[1] - 0.5, 2.4, 1.8, GOLD, bias=0.3)                             # gold pauldron
    tip = None
    if key:
        tip = big_key(f.b, hand[0], hand[1], key_ang, L=12.0, glint=glint)
    ell(f.b, hand[0], hand[1], 2.1, 1.9, GOLD, bias=0.25)                              # gold gauntlet over the grip
    # the chain: wound on the forearm, its free end trailing to the thrown key
    for k in range(3):
        t = 0.3 + k * 0.2
        f.b.put(*P(ex + (hand[0] - ex) * t, ey + (hand[1] - ey) * t + 1), 'կ' if k % 2 else 'ծ')
    if chain_to is not None:
        chain_links(f.g, (hand[0] + 1, hand[1]), chain_to, sag=1.5 if not key else 0.0)
    if spark:
        for k in range(spark):
            a = math.radians(-150 + k * 50)
            f.g.put(*P(hand[0] + 4 * math.cos(a), hand[1] + 4 * math.sin(a)), 'զ' if k % 2 else 'ե')
    out = f.done()
    if dark: out = Spr({k: ('ճ' if v in ('յ', 'մ') else v) for k, v in out.px.items()})
    return out, tip


def build_warden(outdir):
    W = lambda **k: warden(**k)[0]
    idle = [W(), W(dy=0.3, jaw=14, near=(8.0, -9.7), key_ang=67), W(dy=0.5, jaw=17, eye=2, glint=True, near=(8.0, -9.5), key_ang=66),
            W(dy=0.2, jaw=13, key_ang=67)]
    run = [W(ph=i * math.pi / 3, stride=1.0, lean=5, dy=-0.5 * abs(math.sin(i * math.pi / 3)), jaw=11 + 4 * abs(math.sin(i * math.pi / 3)),
             near=(8.0 + math.sin(i * math.pi / 3), -10.5), key_ang=40 + 8 * math.sin(i * math.pi / 3),
             far=(-7.0 - math.sin(i * math.pi / 3), -10.0)) for i in range(6)]
    # SWING: heave the key up and back, then bring it round and down (HIT f3: the bit lands at ~(20, -4)), follow through
    sw = [W(near=(6.0, -16.0), key_ang=-140, crouch=0.5, jaw=10), W(near=(3.0, -19.0), key_ang=-170, crouch=1.0, lean=-5, jaw=14, eye=2),
          W(near=(9.0, -16.0), key_ang=-60, lean=4, jaw=18, eye=2, dx=1.0), W(near=(11.0, -9.0), key_ang=15, lean=8, jaw=20, eye=2, dx=2.0, glint=True, spark=3),
          W(near=(10.0, -7.0), key_ang=35, lean=8, jaw=12, dx=2.0), W(near=(9.5, -10.0), key_ang=-30, lean=3, dx=1.0), W()]
    # SHACKLE: wind the key back on its chain, hurl it (RELEASE f3 from the fist at ~(11, -14)), the chain pays out,
    # then a hard yank (f6) and the key is caught back
    sh = [W(near=(4.0, -14.0), key_ang=-160, crouch=0.5, jaw=8), W(near=(1.0, -16.0), key_ang=-190, lean=-6, crouch=1.0, jaw=12, eye=2),
          W(near=(11.0, -14.0), key_ang=-10, lean=6, jaw=18, eye=2, dx=1.0),
          W(near=(11.5, -13.0), key=False, chain_to=(22.0, -12.0), lean=6, jaw=16, eye=2, dx=1.0),
          W(near=(11.0, -13.0), key=False, chain_to=(26.0, -11.0), lean=4, jaw=12, eye=2, dx=1.0),
          W(near=(10.0, -13.0), key=False, chain_to=(24.0, -11.0), lean=2, jaw=10, eye=2),
          W(near=(5.0, -13.0), key=False, chain_to=(14.0, -12.0), lean=-8, jaw=16, eye=2, crouch=1.0, dx=-1.0, spark=2),
          W(near=(9.0, -12.0), key_ang=-100, jaw=8)]
    death = gold_death(W(lean=-10, jaw=22, eye=2, near=(11, -16), key_ang=-60),
                       W(lean=8, crouch=3.5, jaw=30, near=(9, -4), far=(-6, -5), key_ang=150),
                       W(lean=16, crouch=4.5, jaw=36, eye=0, dark=True, key=False, near=(9, -3), far=(-7, -3)),
                       W(lean=20, crouch=5.0, jaw=40, eye=0, dark=True, key=False, near=(10, -2), far=(-8, -2)), 6.0,
                       [(-4.0, -20.0), (2.0, -23.0), (7.0, -19.0)])
    knock = W(lean=-12, dx=-1.0, jaw=18, eye=2, near=(7.0, -15.0), key_ang=-140)
    anims = [("Idle", idle, [0.24, 0.2, 0.24, 0.2]), ("Run", run, [0.08] * 6),
             ("Swing", sw, [0.12, 0.16, 0.05, 0.07, 0.12, 0.12, 0.12]),
             ("Shackle", sh, [0.12, 0.16, 0.06, 0.08, 0.1, 0.1, 0.1, 0.14])]
    anims += tail(idle[0], death, [0.08, 0.12, 0.16, 0.4], knock)
    sheet("GoldWarden", anims, outdir)
    NOTES["GoldWarden"] = {"swing_tip": warden(near=(11.0, -9.0), key_ang=15, lean=8, jaw=20, dx=2.0)[1],
                           "throw_hand": (11.0 + 1.0, -14.0)}


# ================================================================== GILT REGENT (T2, Coffer Mimic line)
def ermine(c, x, y, k):
    """Ermine fur pixel: white with the odd black tail spot."""
    c.put(*P(x, y), 'ա' if k % 5 == 2 else 'լ' if k % 3 else 'ի')


def crown(c, g, x, y, w=5, h=3, points=3, tilt=0.0, gems="քմ", glint=False):
    """A gold crown: band of width 2w+1 at (x, y) (band's bottom row), points rising h px, gems on the band."""
    for i in range(-w, w + 1):
        yy = y + int(round(i * tilt))
        c.put(int(round(x + i)), yy, 'գ'); c.put(int(round(x + i)), yy - 1, 'ե' if i < 0 else 'դ')
    for k in range(points):
        px_ = x - w + (2 * w) * k / max(1, points - 1)
        yy = y - 1 + int(round((px_ - x) * tilt))
        for j in range(1, h + 1):
            c.put(*P(px_, yy - j), 'ե' if j < h else 'զ')
        c.put(*P(px_, yy - h - 1), gems[k % len(gems)])
    for k, gx in enumerate((x - w * 0.5, x + w * 0.5)):
        g.put(*P(gx, y - 1 + (gx - x) * tilt), gems[k % len(gems)])
    if glint: g.put(*P(x - w + 1, y - 2), 'ռ')


def scepter(c, g, x, y, ang, L=10.0, orb=1, gem='մ', head="emerald"):
    """A gold scepter gripped at (x, y), pointing along ang, an orb gem at its head. Returns the orb centre."""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    tail_ = (x - ux * 2.5, y - uy * 2.5)
    head_ = (x + ux * L, y + uy * L)
    tube(c, [tail_, head_], [0.6, 0.7], GOLD, bias=0.25)
    ell(c, head_[0] - ux * 0.6, head_[1] - uy * 0.6, 1.6, 1.6, GOLD, bias=0.2)       # the cradle
    ramp = EMER if head == "emerald" else SAPH
    ell(c, head_[0] + ux * 0.8, head_[1] + uy * 0.8, 1.6, 1.6, ramp, bias=0.3)
    if orb >= 2: g.put(*P(head_[0] + ux * 0.4, head_[1] + uy * 0.4 - 0.6), 'յ' if head == "emerald" else 'ջ')
    if orb >= 3:
        for k in range(4):
            aa = math.radians(45 + k * 90)
            g.put(*P(head_[0] + ux * 0.8 + 3 * math.cos(aa), head_[1] + uy * 0.8 + 3 * math.sin(aa)), 'յ' if head == "emerald" else 'ջ')
    return (head_[0] + ux * 0.8, head_[1] + uy * 0.8)


def regent(dx=0.0, dy=0.0, lean=0.0, hem=0.0, hand=(6.0, -13.0), sc_ang=-80.0, orb=1, scroll=0.0, eye=1, glint=False,
           collar=1.0, dark=False, far=(-5.0, -12.0), crouch=0.0, crown_tilt=0.0):
    """The Gilt Regent: the mimic's secret occupant, a small crowned figure in crimson velvet and ermine. Its gold
    mask has a single keyhole eye; the chest lid has become a fanged gold ruff round its neck."""
    f = Fr()
    sk = math.tan(math.radians(lean))
    neck_y = -13.0 + dy + crouch
    hand = (hand[0], hand[1] + 3.5); far = (far[0], far[1] + 3.5)      # authored on a taller draft: same poses, 3.5 px lower
    T = lambda x, y: (dx + x + sk * (0 - y) * 0.5 if y < 0 else dx + x, y)
    # robe: a crimson bell from the shoulders to the floor, ermine hem and front panel
    for y in range(int(neck_y), 1):
        t = (y - neck_y) / (0 - neck_y)
        hw = 2.6 + t * 3.8 + (math.sin(hem + y * 0.7) * 0.5 if t > 0.6 else 0.0)
        cx = T(0.0, y)[0] + (math.sin(hem) * 0.8 * t * t)
        for x in range(int(round(cx - hw)), int(round(cx + hw)) + 1):
            u = (x - (cx - hw)) / (2 * hw)
            l = 0.55 - u * 0.95 - t * 0.2
            f.b.put(x, y, B.pick(CRIM, l))
        if t > 0.86:
            for k, x in enumerate(range(int(round(cx - hw)), int(round(cx + hw)) + 1)): ermine(f.b, x, y, k + y)
        fx_ = int(round(cx + 1.2 + t * 0.8))
        if t > 0.15: ermine(f.b, fx_, y, y * 2); f.b.put(fx_ + 1, y, 'ժ' if t > 0.5 else 'ի')
    # far arm: sleeve tucked, hand at far
    sh = T(-2.5, neck_y + 2.0)
    tube(f.u, [sh, (dx + far[0], far[1] + crouch)], [1.6, 1.3], "էը", bias=0.1)
    f.u.put(*P(dx + far[0], far[1] + crouch + 1), 'դ')
    if scroll > 0:
        # an unrolled decree hangs from the far hand
        hx, hy = dx + far[0], far[1] + crouch + 1
        L = int(2 + scroll * 7)
        for j in range(L):
            for i in range(-1, 2):
                f.u.put(*P(hx + i - 0.5, hy + 1 + j), 'ւ' if i < 1 else 'ց')
        for j in range(1, L, 2): f.u.put(*P(hx - 0.5, hy + 1 + j), 'բ')
        f.u.put(*P(hx - 0.5, hy + L + 1), 'թ'); f.u.put(*P(hx + 0.5, hy + L + 1), 'ը')            # red wax seal
    # the ruff: the old chest lid, a gold arch round the neck with fangs along its top edge
    nx, ny = T(0.5, neck_y)
    for i in range(-5, 6):
        yy = ny - 1 + int(round(abs(i) * 0.25))
        f.b.put(int(round(nx + i)), yy, 'ե' if i < 0 else 'դ'); f.b.put(int(round(nx + i)), yy + 1, 'գ')
        if i % 2 == 0 and abs(i) < 5: f.b.put(int(round(nx + i)), yy - 1, 'լ' if collar > 0.5 else 'ի')
    # head: gold mask with the keyhole eye, a velvet hood behind it
    hx, hy = nx + 0.6, ny - 4.0
    ell(f.b, hx - 1.4, hy - 0.2, 3.0, 3.2, CRIM, bias=-0.1)                                # hood
    ell(f.b, hx + 0.4, hy, 2.4, 2.9, GOLD_L, bias=0.15)                                   # mask
    f.b.put(*P(hx + 1.2, hy + 2.0), 'բ'); f.b.put(*P(hx + 2.2, hy + 1.6), 'բ')             # mouth slit
    keyhole(f.b, hx + 1.2, hy - 0.4, glow=0 if dark else eye)
    if eye >= 2 and not dark: f.g.put(*P(hx + 1.2, hy - 0.4), 'յ')
    crown(f.b, f.g, hx + 0.2, int(round(hy - 2.8)), w=3, h=2, points=3, tilt=crown_tilt, gems="քմք", glint=glint)
    # near arm with the scepter
    sh = T(2.5, neck_y + 2.0)
    hd = (dx + hand[0], hand[1] + crouch)
    (ex, ey), _ = B.ik(sh[0], sh[1], hd[0], hd[1], 3.4, 3.4, bend=-1)
    tube(f.b, [sh, (ex, ey), hd], [1.6, 1.4, 1.2], CRIM, bias=0.2)
    f.b.put(*P(hd[0] - 0.8, hd[1]), 'լ')                                                   # ermine cuff
    orbc = scepter(f.b, f.g, hd[0], hd[1], sc_ang, L=8.0, orb=orb)
    f.b.put(*P(hd[0], hd[1]), 'դ')
    out = f.done()
    if dark: out = Spr({k: ('ճ' if v in ('յ', 'մ') else v) for k, v in out.px.items()})
    return out, orbc


def build_regent(outdir):
    R_ = lambda **k: regent(**k)[0]
    idle = [R_(), R_(hem=0.8, dy=-0.3, orb=2), R_(hem=1.6, dy=-0.5, orb=2, glint=True, eye=2), R_(hem=2.4, dy=-0.2)]
    run = [R_(hem=i * 1.05, lean=7, dy=-0.6 * abs(math.sin(i * math.pi / 3)), hand=(6.5, -12.5), sc_ang=-60) for i in range(6)]
    # BOLT: lift the scepter, level it at the hero (RELEASE f3 from the orb at ~(15, -15)), recoil
    bolt = [R_(hand=(5.0, -14.0), sc_ang=-110, orb=2), R_(hand=(4.0, -16.0), sc_ang=-140, orb=3, lean=-4, eye=2),
            R_(hand=(7.0, -15.0), sc_ang=-20, orb=3, lean=5, eye=2), R_(hand=(8.0, -15.0), sc_ang=-5, orb=3, lean=7, eye=2, glint=True),
            R_(hand=(6.5, -14.0), sc_ang=-40, orb=1, lean=2), R_()]
    # DECREE: unroll the decree in the far hand, raise the scepter, bring it down like a seal (RELEASE f4: the seal
    # falls on the hero), hold, roll it up
    dec = [R_(scroll=0.2, far=(-5, -13)), R_(scroll=0.6, far=(-6, -14), hand=(5, -16), sc_ang=-95, orb=2, eye=2),
           R_(scroll=1.0, far=(-6, -14), hand=(4, -19), sc_ang=-100, orb=3, eye=2, lean=-3, crown_tilt=-0.1),
           R_(scroll=1.0, far=(-6, -14), hand=(5, -20), sc_ang=-90, orb=3, eye=2, lean=-4, glint=True),
           R_(scroll=1.0, far=(-6, -14), hand=(8, -12), sc_ang=30, orb=3, eye=2, lean=6, crouch=0.5),
           R_(scroll=1.0, far=(-6, -14), hand=(8, -11), sc_ang=40, orb=2, eye=2, lean=6, crouch=0.5),
           R_(scroll=0.5, far=(-5, -13), hand=(6, -13), sc_ang=-50, orb=1), R_(scroll=0.1)]
    death = gold_death(R_(lean=-10, eye=2, hand=(4, -18), sc_ang=-140, crown_tilt=-0.2),
                       R_(lean=10, crouch=4, hand=(7, -5), sc_ang=40, crown_tilt=0.3, orb=0),
                       R_(lean=18, crouch=5, eye=0, dark=True, hand=(8, -4), sc_ang=70, crown_tilt=0.5, orb=0),
                       R_(lean=22, crouch=6, eye=0, dark=True, hand=(8, -3), sc_ang=80, crown_tilt=0.6, orb=0), 4.0,
                       [(-3.0, -20.0), (2.0, -23.0), (6.0, -18.0)])
    knock = R_(lean=-14, dx=-1.0, eye=2, hand=(5, -16), sc_ang=-130, crown_tilt=-0.15)
    anims = [("Idle", idle, [0.24, 0.2, 0.24, 0.2]), ("Run", run, [0.08] * 6),
             ("Bolt", bolt, [0.12, 0.14, 0.06, 0.08, 0.12, 0.12]),
             ("Decree", dec, [0.1, 0.12, 0.14, 0.12, 0.06, 0.18, 0.12, 0.12])]
    anims += tail(idle[0], death, [0.08, 0.12, 0.16, 0.4], knock)
    sheet("GoldRegent", anims, outdir)
    NOTES["GoldRegent"] = {"bolt_orb": regent(hand=(7.0, -15.0), sc_ang=-20, lean=5)[1]}


# ================================================================== HOARD WYRM (T3, Vault Warden line)
def build_wyrm(outdir):
    """Drawn by goldsecret_v2.py with the material renderer."""
    import goldsecret_v2 as V2
    import ghosts_v2_kit as KIT
    V2.wyrm_sheet(outdir)
    BUILT["GoldWyrm"] = KIT.BUILT["GoldWyrm"]


# ================================================================== VAULT COLOSSUS (T3, Vault Warden line)
def ingot(c, x, y, w=5, h=2, ramp=GOLD_L):
    """A gold bar seen from the side: a trapezoid with a lit top face."""
    for j in range(h + 1):
        inset = 1 if j == 0 else 0
        for i in range(-w // 2 + inset, w // 2 + 1 - inset):
            c.put(int(round(x + i)), int(round(y - h + j)), ramp[3] if j == 0 else ramp[2] if i < 0 else ramp[1])
    c.put(int(round(x - w // 2 + 1)), int(round(y - h)), 'զ')


def vault_door(c, g, cx, cy, r, spin=0.0, open_=0.0, glow=0):
    """The round vault door: gold rim with bolts, iron face, a three-spoke wheel; open_ 0..1 swings it aside on a
    hinge at its left edge, showing the hoard glowing inside."""
    if open_ > 0.05:
        ell(c, cx, cy, r, r, "ն", bias=0.0)                                         # the dark interior
        rnd = random.Random(7)
        for y in range(int(cy), int(cy + r)):                                        # the hoard heaped in the bottom half
            for x in range(int(cx - r), int(cx + r) + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 > (r - 0.6) ** 2: continue
                top = cy + 1.5 - 2.0 * math.cos((x - cx) / r * 1.4)
                if y < top: continue
                k = rnd.random()
                c.put(x, y, 'զ' if k < 0.08 else 'ե' if k < 0.35 else 'դ' if k < 0.75 else 'գ')
        for gx, gy, gem in ((-2, 2, 'ք'), (2, 3, 'մ'), (0, 1, 'պ')): c.put(*P(cx + gx, cy + gy), gem)
        if glow:
            for k in range(5):
                g.put(*P(cx - 3 + k * 1.5, cy + r * 0.3 - (k % 2) * 2), 'զ' if (k + glow) % 2 else 'ե')
        # the door itself, seen edge-on as it swings round its left hinge
        w = max(1.0, r * (1 - open_))
        dx_ = cx - r - w * 0.2
        ell(c, dx_, cy, w * 0.5 + 0.8, r, GOLD, bias=0.2)
        ell(c, dx_ + 0.3, cy, max(0.6, w * 0.5 - 0.4), r - 1.2, IRON, bias=0.1)
        return
    ell(c, cx, cy, r, r, GOLD, bias=0.25)                                            # gold rim
    ell(c, cx, cy, r - 1.6, r - 1.6, IRON, bias=0.15)                                # iron face
    for k in range(8):                                                               # locking bolts
        a = math.radians(k * 45 + 22)
        c.put(*P(cx + math.cos(a) * (r - 0.8), cy + math.sin(a) * (r - 0.8)), 'զ' if k in (5, 6) else 'բ')
    for k in range(3):                                                               # the wheel
        a = math.radians(spin + k * 120)
        gl(c, cx, cy, cx + math.cos(a) * (r - 2.8), cy + math.sin(a) * (r - 2.8), "դե")
        c.put(*P(cx + math.cos(a) * (r - 2.4), cy + math.sin(a) * (r - 2.4)), 'ե')
    keyhole(c, cx, cy, glow=1)


def colossus_v(dx=0.0, dy=0.0, ph=0.0, stride=0.0, lean=0.0, near=(13.0, -14.0), far=(-13.0, -14.0), spin=0.0, door=0.0,
               glow=0, jaw=8.0, eye=1, crouch=0.0, dark=False, glint=False, quake=0):
    """The Vault Colossus: a walking bank vault. Iron body trimmed in gold, the round vault door on its chest, the
    Warden's lid-jaw shrunk to a head on top, shoulders stacked with gold bars, ingot fists."""
    f = Fr()
    hip_y = -7.0 + crouch + dy
    sk = math.tan(math.radians(lean))
    T = lambda x, y: (dx + x + sk * (hip_y - y), y)
    # legs: iron pillars with gold bands
    for k, fx in enumerate((-5.5, 5.5)):
        off = 0 if k == 0 else math.pi
        lift = max(0.0, math.sin(ph + off)) * 2.0 * stride
        fxx = dx + fx + stride * 2.4 * math.cos(ph + off)
        lay = f.u if k == 0 else f.b
        rect(lay, fxx - 2.5, hip_y, fxx + 2.5, -lift, "խծ" if k == 0 else IRON, bias=0.1)
        for x in range(int(fxx - 3), int(fxx + 4)): lay.put(x, int(-lift), 'խ')
        lay.put(int(fxx - 1), int(hip_y + 2), 'դ'); lay.put(int(fxx), int(hip_y + 2), 'դ')
    # far arm (behind)
    sh_f = T(-9.5, hip_y - 19)
    hf = (dx + far[0], far[1] + crouch)
    (ex, ey), _ = B.ik(sh_f[0], sh_f[1], hf[0], hf[1], 6.5, 6.0, bend=1)
    tube(f.u, [sh_f, (ex, ey), hf], [3.0, 2.6, 2.4], "խծ", bias=0.1)
    rect(f.u, hf[0] - 3, hf[1] - 2.5, hf[0] + 3, hf[1] + 2.5, "բգդ", bias=0.1)
    # body: the vault
    x0, x1, y0, y1 = -10.5, 10.5, hip_y - 22, hip_y
    for y in range(int(y0), int(y1) + 1):
        a0, a1 = T(x0, y)[0], T(x1, y)[0]
        for x in range(int(round(a0)), int(round(a1)) + 1):
            u, v = (x - a0) / (a1 - a0), (y - y0) / (y1 - y0)
            f.b.put(x, y, B.pick(IRON, 0.55 - u * 0.6 - v * 0.5))
    for y in range(int(y0), int(y1) + 1):
        f.b.put(*P(*T(x0, y)), 'գ'); f.b.put(*P(*T(x1, y)), 'բ')
    for x in range(int(x0), int(x1) + 1):
        f.b.put(*P(*T(x, y0)), 'ե' if x < 0 else 'դ'); f.b.put(*P(*T(x, y1)), 'գ'); f.b.put(*P(*T(x, y1 - 2)), 'բ' if x % 3 else 'դ')
    for (cx_, cy_) in ((x0 + 1.5, y0 + 1.5), (x1 - 1.5, y0 + 1.5), (x0 + 1.5, y1 - 3.5), (x1 - 1.5, y1 - 3.5)):
        f.b.put(*P(*T(cx_, cy_)), 'դ')                                               # corner rivets
    dc = T(0.5, y0 + 11)
    vault_door(f.b, f.g, dc[0], dc[1], 7.5, spin=spin, open_=door, glow=glow)
    # head: the lid-jaw, small on top
    hinge = T(-5.0, y0)
    if jaw > 3:
        for x in range(int(hinge[0]) + 1, int(hinge[0]) + 10):
            d = (x - hinge[0]) * math.tan(math.radians(jaw)) * 0.9
            for y in range(int(round(y0 - d)), int(y0)): f.b.put(x, y, 'ն')
            if d > 1.4 and x % 2 == 0: f.b.put(x, int(y0) - 1, 'լ')
    lid = rot(chest_lid(L=10, H=4.0, teeth=jaw > 4), -jaw, (0.0, 0.0))
    for (x, y), v in lid.px.items(): f.b.put(int(round(x + hinge[0])), int(round(y + hinge[1])), v)
    ja = math.radians(-jaw)
    ec = (hinge[0] + 6.5 * math.cos(ja) + 2.2 * math.sin(ja), hinge[1] + 6.5 * math.sin(ja) - 2.2 * math.cos(ja))
    keyhole(f.b, ec[0], ec[1], glow=0 if dark else max(1, eye), big=True)
    if eye >= 2 and not dark: f.g.put(*P(*ec), 'յ')
    # shoulders: stacked gold bars
    for sx in (-8.5, 8.0):
        sp = T(sx, y0 + 1)
        ingot(f.b, sp[0], sp[1], w=6, h=2); ingot(f.b, sp[0] + 0.5, sp[1] - 2, w=5, h=1)
    # near arm (in front) with its ingot fist
    sh_n = T(9.5, hip_y - 18)
    hn = (dx + near[0], near[1] + crouch)
    (ex, ey), _ = B.ik(sh_n[0], sh_n[1], hn[0], hn[1], 6.5, 6.0, bend=-1)
    tube(f.b, [sh_n, (ex, ey), hn], [3.2, 2.8, 2.6], IRON, bias=0.15)
    f.b.put(*P(ex, ey), 'դ'); f.b.put(*P(ex + 1, ey), 'գ')
    rect(f.b, hn[0] - 3.5, hn[1] - 3, hn[0] + 3.5, hn[1] + 3, GOLD, bias=0.2)
    for x in range(int(hn[0] - 3), int(hn[0] + 4)): f.b.put(x, int(hn[1] - 3), 'ե')
    f.b.put(*P(hn[0] - 2, hn[1] - 2), 'զ')
    if glint: sparkle(f.g, hn[0] - 2, hn[1] - 3, 1)
    if quake:
        for k in range(quake):
            for side in (-1, 1):
                f.g.put(*P(hn[0] + side * (5 + k * 2), -k * 0.5), 'ե' if k % 2 else 'դ')
    out = f.done()
    if dark: out = Spr({k: ('ճ' if v in ('յ', 'մ') else v) for k, v in out.px.items()})
    return out, hn


def build_colossus(outdir):
    V = lambda **k: colossus_v(**k)[0]
    idle = [V(), V(dy=0.3, spin=15, jaw=10), V(dy=0.5, spin=30, jaw=12, eye=2, glint=True), V(dy=0.2, spin=45, jaw=9)]
    run = [V(ph=i * math.pi / 3, stride=1.0, lean=4, dy=-0.6 * abs(math.sin(i * math.pi / 3)), spin=i * 20,
             near=(13.0 + 1.5 * math.sin(i * math.pi / 3), -14.0), far=(-13.0 - 1.5 * math.sin(i * math.pi / 3), -14.0)) for i in range(6)]
    # SLAM: both fists up over the head, then down on the floor in front (HIT f4: fist at ~(17, -3) + quake ring)
    sl = [V(near=(11, -24), far=(-9, -24), crouch=0.5, jaw=12), V(near=(8, -34), far=(-5, -33), crouch=-0.5, lean=-6, jaw=18, eye=2),
          V(near=(9, -35), far=(-4, -34), lean=-8, jaw=20, eye=2, glint=True), V(near=(16, -12), far=(6, -12), lean=8, jaw=14, eye=2, crouch=1.5),
          V(near=(17, -3), far=(9, -3), lean=12, jaw=10, eye=2, crouch=3.0, quake=3), V(near=(16, -5), far=(8, -5), lean=8, crouch=2.0), V()]
    # PAYOUT: the wheel spins (f0-2), the door swings open (f3), RELEASE f4 (the banked gold bursts out), glow, shut
    po = [V(spin=60, jaw=12), V(spin=150, jaw=14, eye=2), V(spin=260, jaw=16, eye=2, glint=True), V(door=0.5, jaw=20, eye=2, crouch=0.5),
          V(door=1.0, glow=1, jaw=26, eye=2, crouch=1.0, near=(15, -18), far=(-15, -18)),
          V(door=1.0, glow=2, jaw=24, eye=2, crouch=1.0, near=(15, -18), far=(-15, -18)),
          V(door=1.0, glow=1, jaw=18, eye=2, crouch=0.5), V(door=0.5, jaw=12), V(spin=0, jaw=8)]
    death = gold_death(V(lean=-8, jaw=26, eye=2, door=0.5, glow=1),
                       V(lean=8, crouch=4, jaw=32, door=1.0, glow=1, near=(14, -4), far=(-8, -4)),
                       V(lean=14, crouch=6, jaw=38, eye=0, dark=True, door=1.0, near=(15, -3), far=(-6, -3)),
                       V(lean=18, crouch=7, jaw=40, eye=0, dark=True, door=1.0, near=(15, -2), far=(-6, -2)), 10.0,
                       [(-6.0, -30.0), (2.0, -34.0), (9.0, -28.0)], deg=(30.0, 66.0))
    knock = V(lean=-10, dx=-1.0, jaw=20, eye=2, near=(11, -20), far=(-11, -20))
    anims = [("Idle", idle, [0.26, 0.22, 0.26, 0.22]), ("Run", run, [0.09] * 6),
             ("Slam", sl, [0.12, 0.14, 0.16, 0.05, 0.1, 0.14, 0.14]),
             ("Payout", po, [0.1, 0.1, 0.12, 0.08, 0.1, 0.16, 0.16, 0.1, 0.12])]
    anims += tail(idle[0], death, [0.08, 0.12, 0.16, 0.4], knock)
    sheet("GoldVault", anims, outdir, scale=5)
    NOTES["GoldVault"] = {"slam_fist": colossus_v(near=(17, -3), far=(9, -3), lean=12, crouch=3.0)[1]}


# ================================================================== GILDED SOVEREIGN (T3, Gilt Regent line)
def sovereign(dx=0.0, dy=0.0, ph=0.0, stride=0.0, lean=0.0, hand=(9.0, -17.0), sc_ang=-75.0, orb_hand=(-7.0, -18.0),
              orb_up=0.0, cape=0.0, orb=1, eye=1, glint=False, crouch=0.0, dark=False, crown_tilt=0.0, smear=0):
    """The Gilded Sovereign: the Regent crowned for good. Gold plate armour over crimson, a great ermine mantle and a
    flowing cape, the keyhole mask, a five-pointed crown set with sapphires, sapphire scepter and a gold orb."""
    f = Fr()
    hip_y = -12.5 + crouch + dy
    hand = (hand[0], hand[1] + 1.5); orb_hand = (orb_hand[0], orb_hand[1] + 1.5)
    sk = math.tan(math.radians(lean))
    T = lambda x, y: (dx + x + sk * (hip_y - y), y)
    # cape behind: crimson, flaring back, ermine-trimmed hem
    top = T(-1.0, hip_y - 13)
    hem_y = -1.0
    for y in range(int(top[1]), int(hem_y) + 1):
        t = (y - top[1]) / (hem_y - top[1])
        x0 = top[0] - 3 - t * (6 + cape * 3) - math.sin(t * 3 + cape * 2) * 1.2 * t
        x1 = top[0] + 3 + t * 2
        for x in range(int(round(x0)), int(round(x1)) + 1):
            f.u.put(x, y, B.pick(CRIM, 0.3 - (x1 - x) / max(1.0, x1 - x0) * 0.2 - t * 0.5))
        if t > 0.9:
            for k, x in enumerate(range(int(round(x0)), int(round(x1)) + 1)): ermine(f.u, x, y, k + y)
    # legs: gold greaves, crimson under
    feet = ((-3.0 + stride * 3.0 * math.cos(ph), max(0.0, math.sin(ph)) * 2.0 * stride),
            (3.0 - stride * 3.0 * math.cos(ph), max(0.0, -math.sin(ph)) * 2.0 * stride))
    for k, (fx, fy) in enumerate(feet):
        hp = (dx + (-2.0 if k == 0 else 2.0), hip_y)
        ft = (dx + fx, -fy)
        (kx, ky), _ = B.ik(hp[0], hp[1], ft[0], ft[1], 6.4, 6.4, bend=-1)
        lay = f.u if k == 0 else f.b
        tube(lay, [hp, (kx, ky)], [1.8, 1.5], "էը" if k == 0 else CRIM, bias=0.1)
        tube(lay, [(kx, ky), ft], [1.6, 1.3], "բգ" if k == 0 else GOLD, bias=0.2)
        lay.put(*P(kx, ky), 'ե'); gl(lay, ft[0] - 1.5, ft[1], ft[0] + 2.5, ft[1], "բգ")
    # far arm holding the orb
    sh_f = T(-4.0, hip_y - 11)
    of = (dx + orb_hand[0], orb_hand[1] + crouch)
    (ex, ey), _ = B.ik(sh_f[0], sh_f[1], of[0], of[1], 5.0, 5.0, bend=1)
    tube(f.u, [sh_f, (ex, ey), of], [1.8, 1.5, 1.3], "էը", bias=0.1)
    ell(f.u, of[0], of[1] - 2.2, 2.4, 2.4, GOLD_L, bias=0.25)                             # the gold orb
    B.line(f.u, of[0], of[1] - 4.6, of[0], of[1] - 6.4, 'ե'); B.line(f.u, of[0] - 1, of[1] - 5.6, of[0] + 1, of[1] - 5.6, 'ե')
    f.u.put(*P(of[0], of[1] - 2.2), 'պ')
    if orb_up > 0.5:
        for k in range(6):
            a = math.radians(k * 60 + orb_up * 30)
            f.g.put(*P(of[0] + math.cos(a) * 4.0, of[1] - 2.2 + math.sin(a) * 4.0), 'ջ' if k % 2 else 'ե')
    # torso: gold cuirass, crimson tabard
    tc = T(0.0, hip_y - 6.0)
    ell(f.b, tc[0], tc[1], 5.0, 7.0, GOLD, ang=lean, bias=0.2, shader=lambda nu, nv, d, l, ch, x, y: 'բ' if abs(nu) < 0.12 and nv > -0.6 else ch)
    for y in range(int(hip_y - 2), int(hip_y + 4)):
        for x in range(int(T(-2.5, y)[0]), int(T(2.5, y)[0]) + 1): f.b.put(x, y, 'ը' if x < tc[0] else 'է')
    f.b.put(*P(tc[0], tc[1] - 2), 'պ'); f.b.put(*P(tc[0] + 1, tc[1] - 2), 'չ')               # sapphire on the breast
    # ermine mantle over the shoulders
    mc = T(0.0, hip_y - 12.0)
    for i in range(-6, 7):
        for j in range(0, 3 - abs(i) // 4):
            ermine(f.b, mc[0] + i, mc[1] + j + abs(i) * 0.2, i * 3 + j)
    # head: hood, mask with keyhole eye, five-point crown
    hx, hy = mc[0] + 0.8, mc[1] - 3.6
    ell(f.b, hx - 1.4, hy, 3.2, 3.4, CRIM, bias=-0.1)
    ell(f.b, hx + 0.4, hy + 0.2, 2.6, 3.1, GOLD_L, bias=0.15)
    f.b.put(*P(hx + 1.4, hy + 2.2), 'բ'); f.b.put(*P(hx + 2.3, hy + 1.8), 'բ')
    keyhole(f.b, hx + 1.2, hy - 0.2, glow=0 if dark else eye)
    if eye >= 2 and not dark: f.g.put(*P(hx + 1.2, hy - 0.2), 'յ')
    crown(f.b, f.g, hx + 0.2, int(round(hy - 3.0)), w=4, h=3, points=5, tilt=crown_tilt, gems="պմպքպ", glint=glint)
    # near arm with the sapphire scepter
    sh_n = T(4.0, hip_y - 11)
    hd = (dx + hand[0], hand[1] + crouch)
    (ex, ey), _ = B.ik(sh_n[0], sh_n[1], hd[0], hd[1], 5.0, 5.0, bend=-1)
    ell(f.b, sh_n[0], sh_n[1], 2.4, 2.0, GOLD, bias=0.3)                                  # pauldron
    tube(f.b, [sh_n, (ex, ey), hd], [1.8, 1.5, 1.4], CRIM, bias=0.2)
    f.b.put(*P(ex, ey), 'դ')
    head_ = scepter(f.b, f.g, hd[0], hd[1], sc_ang, L=12.0, orb=orb, head="sapphire")
    f.b.put(*P(*hd), 'դ')
    if smear:
        for k in range(smear):
            a = math.radians(sc_ang - 25 - k * 12)
            for rr in (11, 13):
                f.g.put(*P(hd[0] + math.cos(a) * rr, hd[1] + math.sin(a) * rr), 'ջ' if k % 2 else 'լ', over=False)
    out = f.done()
    if dark: out = Spr({k: ('ճ' if v in ('յ', 'մ') else v) for k, v in out.px.items()})
    return out, head_


def build_sovereign(outdir):
    S_ = lambda **k: sovereign(**k)[0]
    idle = [S_(), S_(dy=-0.3, cape=0.3, orb=2), S_(dy=-0.5, cape=0.6, orb=2, eye=2, glint=True), S_(dy=-0.2, cape=0.9)]
    run = [S_(ph=i * math.pi / 3, stride=1.0, lean=6, dy=-0.6 * abs(math.sin(i * math.pi / 3)), cape=0.8 + 0.4 * math.sin(i * math.pi / 3),
              hand=(9.5, -16.0), sc_ang=-55) for i in range(6)]
    # SMITE: lift the scepter high (f1-2), bring it down in front (HIT f3: the sapphire head at ~(20, -7)), recover
    sm = [S_(hand=(7, -21), sc_ang=-120, crouch=0.5, orb=2), S_(hand=(4, -25), sc_ang=-150, lean=-6, orb=3, eye=2, cape=0.5),
          S_(hand=(10, -20), sc_ang=-40, lean=4, orb=3, eye=2, smear=3), S_(hand=(12, -12), sc_ang=15, lean=10, orb=3, eye=2, crouch=1.5, glint=True, smear=4),
          S_(hand=(12, -11), sc_ang=20, lean=8, orb=2, crouch=1.5), S_(hand=(10, -15), sc_ang=-30, lean=3), S_()]
    # KNEEL: the orb is raised high (f2-3), then the scepter points at the hero (RELEASE f4: a crown ring closes on him)
    kn = [S_(orb_hand=(-6, -22), orb_up=0.2), S_(orb_hand=(-5, -28), orb_up=0.6, eye=2, cape=0.4),
          S_(orb_hand=(-4, -31), orb_up=1.0, eye=2, cape=0.6, glint=True, orb=2), S_(orb_hand=(-4, -31), orb_up=1.4, eye=2, cape=0.8, orb=3),
          S_(orb_hand=(-5, -26), orb_up=1.6, hand=(12, -19), sc_ang=-15, eye=2, lean=6, orb=3, cape=0.9),
          S_(orb_hand=(-5, -25), orb_up=1.2, hand=(12, -19), sc_ang=-12, eye=2, lean=6, orb=3, cape=0.7),
          S_(orb_hand=(-6, -21), hand=(10, -17), sc_ang=-50, cape=0.4), S_()]
    death = gold_death(S_(lean=-10, eye=2, hand=(6, -24), sc_ang=-140, crown_tilt=-0.2, cape=0.8),
                       S_(lean=10, crouch=5, hand=(11, -6), sc_ang=40, crown_tilt=0.3, cape=0.4, orb_hand=(-6, -8)),
                       S_(lean=18, crouch=7, eye=0, dark=True, hand=(12, -4), sc_ang=70, crown_tilt=0.5, orb=0, orb_hand=(-6, -6)),
                       S_(lean=22, crouch=8, eye=0, dark=True, hand=(12, -3), sc_ang=80, crown_tilt=0.6, orb=0, orb_hand=(-6, -5)), 5.0,
                       [(-4.0, -28.0), (2.0, -32.0), (8.0, -26.0)])
    knock = S_(lean=-14, dx=-1.0, eye=2, hand=(6, -22), sc_ang=-130, crown_tilt=-0.15, cape=0.9)
    anims = [("Idle", idle, [0.24, 0.2, 0.24, 0.2]), ("Run", run, [0.08] * 6),
             ("Smite", sm, [0.12, 0.16, 0.05, 0.07, 0.12, 0.12, 0.12]),
             ("Kneel", kn, [0.1, 0.12, 0.14, 0.12, 0.08, 0.16, 0.12, 0.12])]
    anims += tail(idle[0], death, [0.08, 0.12, 0.16, 0.4], knock)
    sheet("GoldSovereign", anims, outdir, scale=5)
    NOTES["GoldSovereign"] = {"smite_head": sovereign(hand=(12, -12), sc_ang=15, lean=10, crouch=1.5)[1]}


# ================================================================== GRAND TREASURER (T3, Gilt Regent line)
def ledger(c, g, x, y, open_=1.0, glow=0, write=0):
    """The great ledger held open at (x, y) (spine bottom): crimson boards, gold corners, ruled parchment pages."""
    w = 3 + int(open_ * 3)
    rect(c, x - w - 1, y - 7, x + w + 1, y, CRIM, bias=0.1)                            # boards
    for (cx_, cy_) in ((x - w - 1, y - 7), (x + w + 1, y - 7), (x - w - 1, y), (x + w + 1, y)): c.put(int(cx_), int(cy_), 'ե')
    if open_ > 0.2:
        rect(c, x - w, y - 6, x - 1, y - 1, PARCH, bias=0.4)
        rect(c, x + 1, y - 6, x + w, y - 1, PARCH, bias=0.2)
        c.put(int(x), int(y - 6), 'ժ')
        for j in range(y - 5, y - 1, 2):                                               # ledger lines in gold ink
            for i in range(1, w): c.put(int(x - w + i), int(j), 'գ' if (i + j) % 3 else 'բ'); c.put(int(x + i), int(j), 'գ' if (i + j + 1) % 3 else 'բ')
        if glow:
            for k in range(3): g.put(int(x - 2 + k * 2), int(y - 7 - (k + glow) % 2), 'զ' if k % 2 else 'ե')
        if write: g.put(int(x + 1 + write % w), int(y - 5 + (write % 2) * 2), 'ե')


def treasurer(dx=0.0, dy=0.0, ph=0.0, lean=0.0, hem=0.0, hand=(8.0, -20.0), q_ang=-60.0, book=(-6.0, -17.0), book_open=1.0,
              glow=0, write=0, eye=1, glint=False, crouch=0.0, dark=False, hover=0.0, flick=0):
    """The Grand Treasurer: the Regent grown gaunt and tall over its accounts. A hooded crimson robe with an ermine
    stole, the gold keyhole mask, a gold balance hanging from its sash, the great ledger in one hand and a gold quill
    in the other."""
    f = Fr()
    sk = math.tan(math.radians(lean))
    neck_y = -27.0 + dy + crouch - hover
    T = lambda x, y: (dx + x + sk * (-y) * 0.6, y)
    # robe: long and narrow, a dark crimson column with deep folds
    for y in range(int(neck_y), 1):
        t = (y - neck_y) / (0 - neck_y)
        hw = 3.2 + t * 3.0 + (math.sin(hem + y * 0.6) * 0.6 if t > 0.7 else 0.0)
        cx = T(0.0, y)[0] + math.sin(hem) * 0.7 * t * t
        for x in range(int(round(cx - hw)), int(round(cx + hw)) + 1):
            u = (x - (cx - hw)) / (2 * hw)
            fold = 0.25 if (x - int(cx) + 20) % 3 == 0 and t > 0.4 else 0.0
            f.b.put(x, y, B.pick("էըըթ", 0.6 - u * 0.95 - t * 0.15 - fold))
        if t > 0.92:
            for x in range(int(round(cx - hw)), int(round(cx + hw)) + 1): f.b.put(x, y, 'է' if (x + y) % 2 else 'ը')
    # sash and the hanging balance
    sy = int(round(neck_y + 10))
    for x in range(int(T(-3.5, sy)[0]), int(T(3.8, sy)[0]) + 1): f.b.put(x, sy, 'դ' if x % 2 else 'ե')
    bpx, bpy = T(2.0, sy + 1)
    B.line(f.b, bpx, bpy, bpx, bpy + 3, 'գ')
    B.line(f.b, bpx - 2.5, bpy + 3, bpx + 2.5, bpy + 3, 'դ')
    for sx_ in (-2.5, 2.5):
        f.b.put(*P(bpx + sx_, bpy + 4), 'գ'); f.b.put(*P(bpx + sx_ - 0.5, bpy + 5), 'դ'); f.b.put(*P(bpx + sx_ + 0.5, bpy + 5), 'դ')
    # ermine stole: two long strips down the front
    for y in range(int(neck_y), int(neck_y + 16)):
        for xo in (1.0, 3.0):
            ermine(f.b, T(xo, y)[0], y, y * 2 + int(xo))
    # the ledger in the far hand (behind the body edge), arm in a crimson sleeve
    sh_f = T(-3.0, neck_y + 2.5)
    bh = (dx + book[0], book[1] + crouch - hover)
    (ex, ey), _ = B.ik(sh_f[0], sh_f[1], bh[0], bh[1], 5.5, 5.5, bend=1)
    tube(f.u, [sh_f, (ex, ey), bh], [1.8, 1.6, 1.4], "էը", bias=0.1)
    ledger(f.u, f.g, int(round(bh[0])), int(round(bh[1] + 1)), open_=book_open, glow=glow, write=write)
    # hood and mask
    hx, hy = T(1.0, neck_y - 4.0)
    ell(f.b, hx - 1.0, hy - 0.5, 3.6, 4.2, "էըթ", bias=-0.2)
    ell(f.b, hx + 0.8, hy + 0.4, 2.3, 2.9, GOLD_L, bias=0.1)
    f.b.put(*P(hx + 1.6, hy + 2.4), 'բ')
    keyhole(f.b, hx + 1.4, hy, glow=0 if dark else eye)
    if eye >= 2 and not dark: f.g.put(*P(hx + 1.4, hy), 'յ')
    for k in range(3): f.b.put(*P(hx - 2.5 + k, hy - 4.2 + k * 0.2), 'գ')                 # a thin gold circlet over the hood
    f.b.put(*P(hx - 1.0, hy - 4.6), 'մ')
    # near arm: the gold quill
    sh_n = T(2.8, neck_y + 2.5)
    hd = (dx + hand[0], hand[1] + crouch - hover)
    (ex, ey), _ = B.ik(sh_n[0], sh_n[1], hd[0], hd[1], 5.5, 5.5, bend=-1)
    tube(f.b, [sh_n, (ex, ey), hd], [1.8, 1.5, 1.3], "ըթ", bias=0.2)
    f.b.put(*P(hd[0] - 1, hd[1]), 'լ')
    a = math.radians(q_ang)
    qt = (hd[0] + math.cos(a) * 7, hd[1] + math.sin(a) * 7)
    tube(f.b, [(hd[0] - math.cos(a) * 1.5, hd[1] - math.sin(a) * 1.5), qt], [0.5, 1.4], GOLD_L, bias=0.3)     # the feather vane
    B.line(f.b, hd[0], hd[1], hd[0] + math.cos(a) * 6.5, hd[1] + math.sin(a) * 6.5, 'գ')                   # its shaft
    nib = (hd[0] - math.cos(a) * 2.2, hd[1] - math.sin(a) * 2.2)
    f.b.put(*P(*nib), 'տ')
    if flick:
        for k in range(flick):
            aa = a + math.radians(160 + k * 18)
            f.g.put(*P(hd[0] + math.cos(aa) * (5 + k), hd[1] + math.sin(aa) * (5 + k)), 'ե' if k % 2 else 'դ', over=False)
    if glint: sparkle(f.g, hx - 2.5, hy - 4.5, 1)
    out = f.done()
    if dark: out = Spr({k: ('ճ' if v in ('յ', 'մ') else v) for k, v in out.px.items()})
    return out, hd


def build_treasurer(outdir):
    Q = lambda **k: treasurer(**k)[0]
    idle = [Q(), Q(hem=0.8, dy=-0.3, write=1), Q(hem=1.6, dy=-0.5, eye=2, glint=True, glow=1, write=2), Q(hem=2.4, dy=-0.2, write=3)]
    run = [Q(hem=i * 1.05, lean=6, dy=-0.6 * abs(math.sin(i * math.pi / 3)), hand=(8.5, -19.0), book_open=0.3) for i in range(6)]
    # QUILLS: draw the quill back, flick it (RELEASE f3: three gold quills from ~(12, -24)), follow through
    qu = [Q(hand=(6, -22), q_ang=-110), Q(hand=(3, -25), q_ang=-150, lean=-5, eye=2), Q(hand=(9, -23), q_ang=-40, lean=4, eye=2, flick=2),
          Q(hand=(12, -21), q_ang=10, lean=8, eye=2, flick=4, glint=True), Q(hand=(11, -18), q_ang=40, lean=6), Q(hand=(9, -19), q_ang=-30), Q()]
    # AUDIT: the ledger is raised and opened (f1-2), the quill writes the hero's name in gold (f3-5), the book is
    # slammed shut (RELEASE f6: the debt mark lands on the hero)
    au = [Q(book=(-5, -20), book_open=0.6), Q(book=(-3, -23), book_open=1.0, glow=1, eye=2),
          Q(book=(-2, -24), glow=2, eye=2, hand=(2, -24), q_ang=100, write=1), Q(book=(-2, -24), glow=1, eye=2, hand=(3, -23), q_ang=95, write=2),
          Q(book=(-2, -24), glow=2, eye=2, hand=(2, -24), q_ang=100, write=3, glint=True),
          Q(book=(0, -22), book_open=0.2, eye=2, hand=(6, -21), q_ang=-60, lean=5, glow=2), Q(book=(1, -21), book_open=0.0, eye=2, lean=6, crouch=0.5),
          Q(book_open=0.5)]
    death = gold_death(Q(lean=-10, eye=2, book=(-8, -24), hand=(6, -26), q_ang=-140),
                       Q(lean=10, crouch=5, book=(-8, -6), hand=(9, -6), q_ang=40, book_open=0.4),
                       Q(lean=18, crouch=7, eye=0, dark=True, book=(-6, -4), hand=(10, -4), q_ang=70, book_open=0.0),
                       Q(lean=22, crouch=8, eye=0, dark=True, book=(-5, -3), hand=(10, -3), q_ang=80, book_open=0.0), 5.0,
                       [(-4.0, -28.0), (2.0, -32.0), (8.0, -26.0)])
    knock = Q(lean=-14, dx=-1.0, eye=2, hand=(6, -24), q_ang=-130, book=(-8, -20))
    anims = [("Idle", idle, [0.24, 0.2, 0.24, 0.2]), ("Run", run, [0.08] * 6),
             ("Quills", qu, [0.12, 0.14, 0.06, 0.07, 0.12, 0.12, 0.12]),
             ("Audit", au, [0.1, 0.12, 0.14, 0.12, 0.14, 0.06, 0.16, 0.12])]
    anims += tail(idle[0], death, [0.08, 0.12, 0.16, 0.4], knock)
    sheet("GoldTreasurer", anims, outdir, scale=5)
    NOTES["GoldTreasurer"] = {"quill_hand": treasurer(hand=(12, -21), q_ang=10, lean=8)[1]}


# ================================================================== FX (origin = effect centre on the ground)
def cv():
    return Canvas()


def ring(c, r, ry_k=0.4, ramp="գդեզ", gap=0, phase=0, width=1, dy=0.0):
    """A floor ring of radius r (flattened by ry_k), coloured round its circumference (lit at the top-left)."""
    n = max(12, int(r * 7))
    for k in range(n):
        if gap and (k + phase) % gap == 0: continue
        a = 2 * math.pi * k / n
        for wv in range(width):
            rr = r - wv
            x, y = math.cos(a) * rr, math.sin(a) * rr * ry_k + dy
            l = -(math.cos(a) + math.sin(a)) * 0.5
            c.put(*P(x, y), B.pick(ramp, l + (0.3 if wv == 0 else -0.2)))


def motes(c, n, r, cy=0.0, seed=0, ramp="դեզ", ry_k=1.0):
    rnd = random.Random(seed)
    for k in range(n):
        a = rnd.uniform(0, 2 * math.pi); d = rnd.uniform(0.3, 1.0) * r
        c.put(*P(math.cos(a) * d, cy + math.sin(a) * d * ry_k), rnd.choice(ramp))


def fx_splat():
    """FxGiltSplat: gold dust and a fleck of lacquer burst off a hit (two variants, 4 frames each)."""
    out = []
    for v in range(2):
        fr = []
        for i in range(4):
            c = cv()
            rnd = random.Random(30 + v)
            for k in range(8 + v * 2):
                a = rnd.uniform(-math.pi, 0.3) if v == 0 else rnd.uniform(-math.pi * 1.1, 0.1)
                d = (1.5 + i * 2.2) * rnd.uniform(0.6, 1.1)
                x, y = math.cos(a) * d, -5 + math.sin(a) * d + i * i * 0.35
                if i < 3 or k % 2: c.put(*P(x, y), ('զ' if i == 0 else 'ե') if k % 3 == 0 else 'դ' if i < 2 else 'գ')
            if i == 0: sparkle(c, 0, -5, 1)
            fr.append(c.spr())
        out.append(fr)
    return out


def fx_hoard():
    """FxGiltHoard Cash: coins the Coffer Mimic steals or drops - a shower of gold motes rising (6 frames)."""
    cash = []
    for i in range(6):
        c = cv()
        rnd = random.Random(4)
        for k in range(14):
            x = rnd.uniform(-7, 7); y0 = rnd.uniform(-4, 0)
            y = y0 - i * 3 - rnd.uniform(0, 2)
            if i < 5 or k % 3 == 0: c.put(*P(x, y), 'զ' if (k + i) % 4 == 0 else 'ե' if k % 2 else 'դ')
        if i < 2: ring(c, 4 + i * 3, 0.4, "դեզ")
        cash.append(c.spr())
    return cash


def fx_key_arc():
    """FxGiltKeyArc: the Warden's key swing - a gold smear sweeping down through the front (Swing, 3 frames)."""
    out = []
    for i in range(3):
        c = cv()
        a0, a1 = [(-150, -60), (-90, 20), (-20, 40)][i]
        for rr in (10, 11, 12):
            for k in range(14):
                a = math.radians(a0 + (a1 - a0) * k / 13.0)
                t = k / 13.0
                if i == 2 and t < 0.5: continue
                c.put(*P(math.cos(a) * rr, -8 + math.sin(a) * rr), ('զ' if t > 0.75 else 'ե' if t > 0.4 else 'դ') if rr == 11 else 'գ' if t > 0.3 else 'բ')
        if i == 1: sparkle(c, math.cos(math.radians(15)) * 12, -8 + math.sin(math.radians(15)) * 12, 1)
        out.append(c.spr())
    return out


def fx_key():
    """FxGiltKey: the thrown key spinning on the end of its chain (Fly, 4 frames, faces right, centred on (0, 0))."""
    out = []
    for i in range(4):
        c = cv()
        ang = i * 90 - 20
        big_key(c, 0, 0, ang, L=6.0, bow=1.8, glint=i % 2 == 0)
        for k in range(1, 6):                                              # the chain trailing behind
            c.put(-3 - k, (k + i) % 2 * (1 if k % 2 else 0), 'կ' if k % 2 else 'ծ')
        out.append(Spr(B.outl(c.spr(), OUT).px))
    return out


def fx_chain():
    """FxGiltChain: one 4 px stretch of the shackle chain (Link, 2 frames: the links glint in turn), drawn along +x."""
    out = []
    for i in range(2):
        c = cv()
        for x in range(-2, 3):
            if (x + i) % 2:
                c.put(x, 0, 'կ'); c.put(x, -1, 'ծ')
            else:
                c.put(x, -1, 'կ'); c.put(x, 0, 'ծ'); c.put(x, -2, 'ծ') if x == 0 else None
        if i: c.put(0, -1, 'ե')
        out.append(c.spr())
    return out


def fx_shackle():
    """FxGiltShackle: a gold manacle locked round the hero's ankles with a short chain stub (Loop 4, feet overlay:
    drawn on the line 2 px above the cell bottom)."""
    out = []
    for i in range(4):
        c = cv()
        ring(c, 5.0, 0.42, "բգդե", dy=-3.0)
        ring(c, 5.0, 0.42, "բգդե", dy=-2.0)
        for k in range(3): c.put(5 + k, -2 + (k + i) % 2, 'կ' if k % 2 else 'ծ')
        c.put(-2, -5, 'ճ'); c.put(-1, -5, 'մ' if i % 2 else 'յ')                 # the keyhole lock
        if i == 1: c.put(-4, -4, 'ռ')
        out.append(c.spr())
    return out


def fx_clank():
    """FxGiltClank: a hit glancing off the Warden's armoured front - a gold shield flash and sparks (Play, 4)."""
    out = []
    for i in range(4):
        c = cv()
        if i < 2:
            for y in range(-11, -1):
                for x in range(-2, 3):
                    if abs(x) + abs(y + 6) * 0.45 < 3.2 - i: c.put(x, y, 'զ' if i == 0 else 'ե')
        for k in range(6):
            a = math.radians(-160 + k * 28)
            d = 3 + i * 3
            if i > 0: c.put(*P(-math.cos(a) * d * 0.4 - i, -6 + math.sin(a) * d), 'ե' if k % 2 else 'դ')
        out.append(c.spr())
    return out


def fx_bolt():
    """FxGiltBolt: the Regent's scepter bolt - an emerald spark in a gold ring, trailing glitter (Fly, 4)."""
    out = []
    for i in range(4):
        c = cv()
        ell(c, 0, 0, 2.2, 2.0, "դեզ", bias=0.3)
        ell(c, 0, 0, 1.2, 1.1, EMER, bias=0.4)
        c.put(0, 0, 'յ')
        for k in range(4):
            c.put(-3 - k * 2 - (i % 2), ((k + i) % 3) - 1, 'ե' if k < 2 else 'գ')
        s = Spr(B.outl(c.spr(), OUT).px)
        s.px[(1, -1)] = 'ռ'
        out.append(s)
    return out


def fx_bolt_pop():
    """FxGiltBoltPop: the bolt bursting - emerald and gold flecks (Play, 4)."""
    out = []
    for i in range(4):
        c = cv()
        if i == 0: ell(c, 0, -4, 3, 3, "մյռ", bias=0.4)
        for k in range(8):
            a = math.radians(k * 45 + i * 10)
            d = 2 + i * 2.2
            if i < 3 or k % 2: c.put(*P(math.cos(a) * d, -4 + math.sin(a) * d), 'յ' if k % 2 else 'ե' if i < 2 else 'գ')
        out.append(c.spr())
    return out


def fx_seal():
    """FxGiltSeal: the Decree's seal. f0-f4 a gold target ring with the crown sigil grows on the floor while a huge
    crimson wax seal drops from above; f5 IMPACT (damage f5-f6); f6-f8 the wax splashes out and fades."""
    out = []
    for i in range(9):
        c = cv()
        if i <= 5:
            r = 4 + min(i, 4) * 1.6
            ring(c, r, 0.4, "բգդե", gap=5 if i < 4 else 0, phase=i)
            for k in range(3):                                         # crown sigil in the middle
                c.put(-2 + k * 2, -1, 'դ'); c.put(-2 + k * 2, -2, 'ե')
            c.put(-1, 0, 'գ'); c.put(0, 0, 'գ'); c.put(1, 0, 'գ')
        if i <= 4:
            h = 40 - i * 9
            ell(c, 0, -h, 4.0, 2.4, "էըթ", bias=0.3)
            for k in range(-2, 3): c.put(k, -h, 'ե' if k % 2 else 'դ')
            c.put(0, int(-h - 1), 'զ')
        if i == 5:
            ell(c, 0, -2, 6.5, 3.0, "էըթ", bias=0.3)
            for k in range(-3, 4): c.put(k, -3, 'ե' if k % 2 else 'դ')
            ring(c, 11, 0.4, "դեզ")
        if i >= 6:
            for k in range(10):
                a = 2 * math.pi * k / 10
                d = 6 + (i - 5) * 3
                c.put(*P(math.cos(a) * d, math.sin(a) * d * 0.4 - 1), 'թ' if i < 8 else 'ը')
            if i < 8: ell(c, 0, -1, 5.0 - (i - 6) * 1.5, 2.2, "էը", bias=0.2)
        out.append(c.spr())
    return out


def fx_tax():
    """FxGiltTax: TAXED, shown over the hero's head - a little gold-crowned wax seal on a ribbon that swings (Loop 4)."""
    out = []
    for i in range(4):
        c = cv()
        sw = [-1, 0, 1, 0][i]
        B.line(c, -3, -9, 0 + sw, -5, 'թ'); B.line(c, 3, -9, 0 + sw, -5, 'ը')     # ribbon
        ell(c, sw, -3, 2.6, 2.4, "էըթ", bias=0.3)
        c.put(sw - 1, -4, 'ե'); c.put(sw, -5, 'ե'); c.put(sw + 1, -4, 'ե'); c.put(sw, -3, 'դ')   # crown stamp
        s = Spr(B.outl(c.spr(), OUT).px)
        if i == 1: s.px[(sw - 2, -5)] = 'ռ'
        out.append(s)
    return out


def fx_tithe():
    """FxGiltTithe: the tax paid - a ribbon of gold motes spiralling up into the Regent (Play, 6, body overlay)."""
    out = []
    for i in range(6):
        c = cv()
        for k in range(10):
            t = (k / 10.0 + i / 6.0) % 1.0
            a = t * 4 * math.pi
            c.put(*P(math.cos(a) * (6 - t * 4), -2 - t * 18), 'զ' if k % 3 == 0 else 'ե' if t < 0.7 else 'դ')
        out.append(c.spr())
    return out


def fx_ripple():
    """FxGiltRipple: Royal Distance - a gold ring with a crown crest bursting out from the Regent's feet (Play, 5)."""
    out = []
    for i in range(5):
        c = cv()
        r = 4 + i * 4.5
        ring(c, r, 0.42, "գդեզ" if i < 3 else "բգդ", gap=0 if i < 3 else 3, phase=i, width=2 if i < 3 else 1)
        if i < 3:
            for k in range(5):
                a = math.radians(-150 + k * 30)
                c.put(*P(math.cos(a) * r, math.sin(a) * r * 0.42 - 2), 'ե')
        out.append(c.spr())
    return out


def fx_molten():
    """FxGiltMolten: a glob of molten gold arcing along the floor (Fly, 4: it wobbles and drips; centred)."""
    out = []
    for i in range(4):
        c = cv()
        ell(c, 0, 0, 2.6 + (i % 2) * 0.4, 2.2 - (i % 2) * 0.3, MOLT, bias=0.4)
        c.put(-1, -1, 'զ')
        for k in range(3): c.put(-3 - k, (k + i) % 2, 'վ' if k == 0 else 'ս')
        out.append(Spr(B.outl(c.spr(), OUT).px))
    return out


def molten_pool(spread, phase, fade=0.0, hot=1.0):
    c = cv()
    rnd = random.Random(11)
    for y in range(-3, 4):
        for x in range(-12, 13):
            d = (x / (11.0 * spread)) ** 2 + (y / (3.4 * spread)) ** 2 + math.sin(x * 0.9 + phase) * 0.06
            if d > 1.0: continue
            if fade and rnd.random() < fade: continue
            if d > 0.75: ch = 'բ' if hot < 0.5 else 'ս'
            elif (x + y * 3 + phase * 2) % 7 == 0: ch = 'զ'
            elif d < 0.3: ch = 'ե' if hot > 0.5 else 'դ'
            else: ch = 'վ' if hot > 0.7 and (x + y) % 3 == 0 else 'դ'
            c.put(x, y - 1, ch)
    return c.spr()


def fx_pool():
    """FxGiltPool: molten gold on the floor - splashes out, bubbles (damage + slow while live), crusts over and
    hardens dark, then fades (Life, 9)."""
    return [molten_pool(0.5, 0), molten_pool(0.9, 1), molten_pool(1.0, 2), molten_pool(1.0, 3), molten_pool(1.0, 4),
            molten_pool(1.0, 5, hot=0.8), molten_pool(1.0, 6, hot=0.6), molten_pool(0.95, 7, fade=0.3, hot=0.3), molten_pool(0.9, 8, fade=0.65, hot=0.2)]


def fx_gilded():
    """FxGiltGilded: GILDED - gold leaf flaking over the hero (body overlay, Loop 4): flakes cling to the outline of a
    16 px figure and drift down, glinting."""
    out = []
    for i in range(4):
        c = cv()
        rnd = random.Random(21)
        for k in range(16):
            x = rnd.uniform(-5, 5); y = rnd.uniform(-17, -3)
            y += (i * 1.2 + k) % 4 * 0.6
            c.put(*P(x, y), 'զ' if (k + i) % 5 == 0 else 'ե' if k % 2 else 'դ')
            if k % 3 == 0: c.put(*P(x + 1, y), 'գ')
        c.put(*P(-4 + i * 2, -14 + i), 'ռ')
        out.append(c.spr())
    return out


def fx_shatter():
    """FxGiltShatter: the gilding shattering off the hero under the Wyrm's bite - gold shards burst out (Play, 5)."""
    out = []
    for i in range(5):
        c = cv()
        if i == 0:
            for y in range(-16, -1):
                for x in range(-4, 5):
                    if (x * x) / 16.0 + ((y + 9) ** 2) / 56.0 < 1 and (x + y) % 2 == 0: c.put(x, y, 'ե')
            sparkle(c, 0, -9, 2)
        for k in range(10):
            a = math.radians(k * 36 + 10)
            d = 3 + i * 3
            x, y = math.cos(a) * d, -9 + math.sin(a) * d * 0.8 + i * i * 0.4
            if i < 4 or k % 2:
                c.put(*P(x, y), 'զ' if k % 3 == 0 else 'ե'); c.put(*P(x + 1, y), 'գ')
        out.append(c.spr())
    return out


def fx_quake():
    """FxGiltQuake: the Colossus' slam - a ring of cracked floor and kicked-up gold dust (Ring, 5)."""
    out = []
    for i in range(5):
        c = cv()
        r = 5 + i * 3.5
        ring(c, r, 0.4, "բգդե" if i < 3 else "բգ", gap=4 if i >= 3 else 0, phase=i)
        rnd = random.Random(i)
        for k in range(8):
            a = rnd.uniform(0, 2 * math.pi)
            c.put(*P(math.cos(a) * r * 0.8, math.sin(a) * r * 0.35 - 1 - (2 - abs(i - 2))), 'ե' if k % 2 else 'կ')
        out.append(c.spr())
    return out


def fx_payout():
    """FxGiltPayout: the vault pays out - a huge gold shockwave with bars and gems flung round it (Play, 6)."""
    out = []
    for i in range(6):
        c = cv()
        r = 6 + i * 5
        ring(c, r, 0.42, "գդեզ" if i < 4 else "բգդ", width=3 if i < 3 else 2, gap=0 if i < 4 else 3, phase=i)
        if i < 3:
            ring(c, r * 0.6, 0.42, "դեզ", gap=3, phase=i)
        rnd = random.Random(40)
        for k in range(10):
            a = rnd.uniform(0, 2 * math.pi)
            d = r * rnd.uniform(0.5, 1.0)
            y = math.sin(a) * d * 0.42 - (3 + i * 1.5) * math.sin(min(1.0, i / 4.0) * math.pi)
            if i < 5 or k % 2:
                if k % 3 == 0: ingot(c, math.cos(a) * d, y, w=3, h=1)
                else: c.put(*P(math.cos(a) * d, y), 'ք' if k % 5 == 1 else 'մ' if k % 5 == 2 else 'ե')
        if i == 0: sparkle(c, 0, -6, 3)
        out.append(c.spr())
    return out


def fx_ingot():
    """FxGiltIngot: a gold bar tumbling through the air (Fly, 4, centred)."""
    out = []
    for i in range(4):
        c = cv()
        sh = Canvas()
        ingot(sh, 0, 1, w=6, h=2)
        s = rot(sh.spr(), i * 45, (0.0, 0.0))
        paste(c, s)
        s2 = Spr(B.outl(c.spr(), OUT).px)
        if i % 2 == 0: s2.px[(-1, -2)] = 'ռ'
        out.append(s2)
    return out


def fx_bank():
    """FxGiltBank: the gold banked in the vault, over its head - One / Two / Three stacked bars (Loop 4 each)."""
    anims = {}
    for n in (1, 2, 3):
        fr = []
        for i in range(4):
            c = cv()
            for k in range(n):
                ingot(c, (k - (n - 1) / 2.0) * 2.0 + (k % 2), -1 - k * 2.0, w=5, h=1)
            s = Spr(B.outl(c.spr(), OUT).px)
            s.px[(int(-2 + i), -2 - (n - 1) * 2)] = 'ռ' if i % 2 == 0 else 'զ'
            fr.append(s)
        anims[n] = fr
    return anims


def fx_kneel():
    """FxGiltKneel: KNEEL! A ring of gold crown points round the hero that closes in. f0-f6 warning (it shrinks from
    r 22 to 9, points rising), f7 SLAM (damage f7-f8: r 16 with a daze), f8-f10 the crown dissolves."""
    out = []
    for i in range(11):
        c = cv()
        if i <= 6:
            r = 22 - i * 2.2
            ring(c, r, 0.42, "բգդե", gap=0)
            n = 10
            for k in range(n):
                a = 2 * math.pi * k / n + i * 0.12
                x, y = math.cos(a) * r, math.sin(a) * r * 0.42
                h = 1 + i // 2
                for j in range(1, h + 1): c.put(*P(x, y - j), 'ե' if j < h else 'զ')
                if k % 3 == 0: c.put(*P(x, y - h - 1), 'պ')
        elif i <= 8:
            r = 9 + (i - 7) * 5
            ring(c, r, 0.42, "դեզ", width=3)
            ring(c, r * 0.5, 0.42, "եզ", width=1)
            for k in range(12):
                a = 2 * math.pi * k / 12
                c.put(*P(math.cos(a) * r, math.sin(a) * r * 0.42 - 3), 'ջ' if k % 2 else 'զ')
            if i == 7: sparkle(c, 0, -8, 3, ch='ռ', arm='ջ')
        else:
            r = 18 + (i - 9) * 3
            ring(c, r, 0.42, "գդ", gap=2, phase=i)
            motes(c, 8, r * 0.7, cy=-2, seed=i, ramp="գդջ", ry_k=0.42)
        out.append(c.spr())
    return out


def fx_jewel():
    """FxGiltJewel: one of the Sovereign's crown jewels - Orbit (a faceted sapphire that turns and glints, Loop 6)
    and Break (it cracks and bursts into blue shards, 5)."""
    orbit = []
    for i in range(6):
        c = cv()
        w = [2.0, 1.6, 1.0, 0.6, 1.0, 1.6][i]
        for y in range(-3, 4):
            for x in range(-3, 4):
                if abs(x) / max(0.5, w) + abs(y) / 3.0 <= 1.0:
                    c.put(x, y, 'ջ' if x < 0 and y < 0 else 'պ' if y <= 0 else 'չ')
        s = Spr(B.outl(c.spr(), OUT).px)
        if i in (0, 3): s.px[(0, -2)] = 'ռ'
        orbit.append(s)
    brk = []
    for i in range(5):
        c = cv()
        if i == 0:
            for y in range(-3, 4):
                for x in range(-2, 3):
                    if abs(x) / 2.0 + abs(y) / 3.0 <= 1.0: c.put(x, y, 'ջ' if (x + y) % 2 else 'ռ')
        for k in range(8):
            a = math.radians(k * 45 + 20)
            d = 2 + i * 2.2
            if i < 4 or k % 2: c.put(*P(math.cos(a) * d, math.sin(a) * d + i * 0.5), 'ջ' if k % 2 else 'պ')
        brk.append(c.spr())
    return orbit, brk


def fx_shard():
    """FxGiltShard: a sapphire shard flung back at the hero (Fly, 2, faces right, centred)."""
    out = []
    for i in range(2):
        c = cv()
        poly(c, [(-3, 0), (0, -1.5), (4, 0), (0, 1.5)], 'պ')
        c.put(0, -1, 'ջ'); c.put(1, 0, 'ջ')
        for k in range(3): c.put(-5 - k - i, (k + i) % 2 - 0, 'ջ' if k == 0 else 'պ')
        out.append(Spr(B.outl(c.spr(), OUT).px))
    return out


def fx_smite():
    """FxGiltSmite: the Sovereign's scepter striking the floor - a blue-white flash, a small crown of gold sparks and
    a ring (Play, 5)."""
    out = []
    for i in range(5):
        c = cv()
        if i < 2:
            for j in range(10 - i * 4):
                c.put(0, -j, 'ռ' if j < 4 else 'ջ'); c.put(1, -j, 'ջ') if j % 2 else None
        ring(c, 3 + i * 3, 0.4, "պջզ" if i < 3 else "չպ", gap=0 if i < 3 else 2, phase=i)
        for k in range(5):
            a = math.radians(-160 + k * 35)
            d = 2 + i * 2
            if i > 0: c.put(*P(math.cos(a) * d, -2 + math.sin(a) * d), 'ե' if k % 2 else 'ջ')
        out.append(c.spr())
    return out


def fx_quill():
    """FxGiltQuill: a thrown gold quill, nib first (Fly, 2, faces right, centred)."""
    out = []
    for i in range(2):
        c = cv()
        tube(c, [(-5, 0), (2, 0)], [1.4, 0.6], GOLD_L, bias=0.3)
        B.line(c, -6, 0, 3, 0, 'գ')
        c.put(4, 0, 'տ'); c.put(3, 0, 'բ')
        for k in range(2): c.put(-8 - k - i, (k + i) % 2, 'ե')
        out.append(Spr(B.outl(c.spr(), OUT).px))
    return out


def ink_blot(spread, phase, fade=0.0):
    c = cv()
    rnd = random.Random(17)
    for y in range(-3, 4):
        for x in range(-10, 11):
            d = (x / (9.0 * spread)) ** 2 + (y / (3.0 * spread)) ** 2 + math.sin(x * 1.3 + y + phase) * 0.08
            if d > 1.0 or (fade and rnd.random() < fade): continue
            ch = 'տ' if d > 0.6 else 'ր' if d > 0.3 else 'բ'
            if (x * 3 + y + phase) % 9 == 0: ch = 'դ'
            c.put(x, y - 1, ch)
    for k in range(4):                                                   # gold-ink splashes round the rim
        a = k * 1.6 + 0.4
        c.put(*P(math.cos(a) * 11 * spread, math.sin(a) * 4 * spread - 1), 'գ' if not fade else 'տ')
    return c.spr()


def fx_ink():
    """FxGiltInk: a blot of the Treasurer's ink-and-gold under the hero - splashes, lingers (slows while live), dries
    and fades (Life, 8)."""
    return [ink_blot(0.4, 0), ink_blot(0.85, 1), ink_blot(1.0, 2), ink_blot(1.0, 3), ink_blot(1.0, 4), ink_blot(1.0, 5),
            ink_blot(0.95, 6, 0.35), ink_blot(0.9, 7, 0.7)]


def fx_debt():
    """FxGiltDebt: IN DEBT, over the hero's head - an open ledger page with a gold tally that keeps ticking up (Loop 6)."""
    out = []
    for i in range(6):
        c = cv()
        rect(c, -5, -9, -1, -1, PARCH, bias=0.4); rect(c, 1, -9, 5, -1, PARCH, bias=0.2)
        c.put(0, -9, 'ը'); c.put(0, -1, 'ը')
        for k in range(min(i + 1, 5)):                                   # tally strokes
            if k < 4: B.line(c, 1.5 + k, -7, 1.5 + k, -4, 'դ')
            else: B.line(c, 1, -4, 5, -7, 'թ')
        for j in (-7, -5, -3): B.line(c, -4, j, -2, j, 'գ')
        s = Spr(B.outl(c.spr(), OUT).px)
        if i == 5: s.px[(3, -10)] = 'ռ'
        out.append(s)
    return out


def fx_interest():
    """FxGiltInterest: the debt collected - a gold seal stamps down on the hero and bursts into a ring of gold (Play, 6)."""
    out = []
    for i in range(6):
        c = cv()
        if i < 2:
            h = 14 - i * 8
            ell(c, 0, -6 - h, 4, 2.4, "գդե", bias=0.3)
            B.line(c, -2, -6 - h, 2, -6 - h, 'ը')
        else:
            r = 3 + (i - 2) * 4
            ring(c, r, 0.45, "դեզ" if i < 4 else "գդ", width=2 if i < 4 else 1, dy=-1)
            for k in range(8):
                a = math.radians(k * 45 + i * 7)
                c.put(*P(math.cos(a) * r * 0.8, -6 + math.sin(a) * r * 0.6 - (i - 2)), 'ե' if k % 2 else 'թ')
            if i == 2: sparkle(c, 0, -7, 2)
        out.append(c.spr())
    return out


def fx_stamp():
    """FxGiltStamp: PAID - a crimson stamp flashing on the Treasurer when a hit is written off at the cap (Play, 5)."""
    out = []
    for i in range(5):
        c = cv()
        s_ = [0.6, 1.2, 1.0, 1.0, 0.9][i]
        w, h = int(5 * s_), int(3 * s_)
        for y in range(-h, h + 1):
            for x in range(-w, w + 1):
                if abs(x) == w or abs(y) == h: c.put(x, y - 14, 'թ' if i < 3 else 'ը')
        if s_ >= 1.0:
            for k, x in enumerate(range(-w + 2, w - 1)):
                c.put(x, -14, 'թ' if k % 2 == 0 or i < 4 else 'ը'); c.put(x, -15, 'ը' if k % 3 else 'թ')
        if i == 1:
            for k in range(6):
                a = math.radians(k * 60)
                c.put(*P(math.cos(a) * 8, -14 + math.sin(a) * 5), 'ե')
        if i == 4: c = Canvas() if False else c
        out.append(c.spr())
    return out


def fx_mark():
    """FxGiltMark: the audit landing on the hero - a ledger page flutters down onto him and flashes (Play, 6)."""
    out = []
    for i in range(6):
        c = cv()
        y = -26 + i * 4
        sw = [2, -2, 2, -1, 0, 0][i]
        if i < 5:
            for yy in range(-2, 2):
                for xx in range(-3, 4):
                    c.put(xx + sw + (yy if i % 2 else -yy) // 2, y + yy, 'ւ' if xx < 1 else 'ց')
            B.line(c, -2 + sw, y - 1, 2 + sw, y - 1, 'գ')
        if i >= 4:
            ring(c, 4 + (i - 4) * 4, 0.45, "դեզ", dy=-1)
            sparkle(c, 0, -8 - (i - 4) * 2, 1)
        out.append(c.spr())
    return out


FX_ORDER = []


def build_fx(outdir, only=None):
    def want(n): return only is None or n in only
    def F(name, anims, scale=6):
        FX_ORDER.append(name)
        if want(name): fx_sheet(name, anims, outdir, scale=scale)
    a, b = fx_splat()
    F("FxGiltSplat", [("Play", a, [0.04, 0.05, 0.06, 0.08]), ("Play2", b, [0.04, 0.05, 0.06, 0.08])])
    F("FxGiltHoard", [("Cash", fx_hoard(), [0.05, 0.06, 0.07, 0.08, 0.09, 0.1])])
    F("FxGiltKeyArc", [("Swing", fx_key_arc(), [0.05, 0.05, 0.06])])
    F("FxGiltKey", [("Fly", fx_key(), [0.05] * 4)], scale=8)
    F("FxGiltChain", [("Link", fx_chain(), [0.12, 0.12])], scale=8)
    F("FxGiltShackle", [("Loop", fx_shackle(), [0.12] * 4)])
    F("FxGiltClank", [("Play", fx_clank(), [0.04, 0.05, 0.06, 0.08])])
    F("FxGiltBolt", [("Fly", fx_bolt(), [0.05] * 4)], scale=8)
    F("FxGiltBoltPop", [("Play", fx_bolt_pop(), [0.04, 0.05, 0.06, 0.08])])
    F("FxGiltSeal", [("Fall", fx_seal(), [0.1, 0.1, 0.1, 0.1, 0.08, 0.06, 0.08, 0.1, 0.12])], scale=5)
    F("FxGiltTax", [("Loop", fx_tax(), [0.15] * 4)], scale=8)
    F("FxGiltTithe", [("Play", fx_tithe(), [0.06] * 6)])
    F("FxGiltRipple", [("Play", fx_ripple(), [0.04, 0.05, 0.06, 0.07, 0.08])], scale=5)
    F("FxGiltMolten", [("Fly", fx_molten(), [0.06] * 4)], scale=8)
    F("FxGiltPool", [("Life", fx_pool(), [0.06, 0.08, 0.4, 0.4, 0.4, 0.4, 0.4, 0.3, 0.2])])
    F("FxGiltGilded", [("Loop", fx_gilded(), [0.12] * 4)])
    F("FxGiltShatter", [("Play", fx_shatter(), [0.04, 0.05, 0.06, 0.07, 0.08])])
    F("FxGiltQuake", [("Ring", fx_quake(), [0.05, 0.05, 0.06, 0.07, 0.08])], scale=5)
    F("FxGiltPayout", [("Play", fx_payout(), [0.05, 0.06, 0.07, 0.08, 0.09, 0.1])], scale=4)
    F("FxGiltIngot", [("Fly", fx_ingot(), [0.05] * 4)], scale=8)
    bank = fx_bank()
    F("FxGiltBank", [("One", bank[1], [0.15] * 4), ("Two", bank[2], [0.15] * 4), ("Three", bank[3], [0.15] * 4)], scale=8)
    F("FxGiltKneel", [("Play", fx_kneel(), [0.13, 0.13, 0.13, 0.13, 0.13, 0.13, 0.12, 0.06, 0.08, 0.1, 0.12])], scale=4)
    orbit, brk = fx_jewel()
    F("FxGiltJewel", [("Orbit", orbit, [0.08] * 6), ("Break", brk, [0.04, 0.05, 0.06, 0.07, 0.08])], scale=8)
    F("FxGiltShard", [("Fly", fx_shard(), [0.06, 0.06])], scale=8)
    F("FxGiltSmite", [("Play", fx_smite(), [0.04, 0.05, 0.06, 0.07, 0.08])])
    F("FxGiltQuill", [("Fly", fx_quill(), [0.06, 0.06])], scale=8)
    F("FxGiltInk", [("Life", fx_ink(), [0.06, 0.08, 0.5, 0.5, 0.5, 0.5, 0.35, 0.25])])
    F("FxGiltDebt", [("Loop", fx_debt(), [0.18] * 6)], scale=8)
    F("FxGiltInterest", [("Play", fx_interest(), [0.05, 0.05, 0.06, 0.07, 0.08, 0.1])])
    F("FxGiltStamp", [("Play", fx_stamp(), [0.04, 0.06, 0.12, 0.12, 0.1])])
    F("FxGiltMark", [("Play", fx_mark(), [0.05, 0.05, 0.05, 0.05, 0.06, 0.08])])


MONSTERS = [("GoldMimic", build_mimic), ("GoldWarden", build_warden), ("GoldRegent", build_regent), ("GoldWyrm", build_wyrm),
            ("GoldVault", build_colossus), ("GoldSovereign", build_sovereign), ("GoldTreasurer", build_treasurer)]


# sync frames (TIMING.md): sheet -> [(anim, frame, moment, spawn point from the feet, x fwd / y up NEGATIVE)]
EVENTS = {
    "GoldMimic": [("Snap", 3, "HIT: the jaws lock with the snap flash at the lip (ModGoldMimicSnap); SnapUp / SnapDown the same",
                   "jaws (9, -8): box (9, 6) 12 x 10"),
                  ("Feign", 1, "PLAY DEAD on: a quarter damage, each hit drops 1-4 gold, watches for the hero (26 px)", "-"),
                  ("Spring", 0, "clip frame 11: GoldFeignOff (the brain jumps here when the hero comes near), turn to him, lunge", "-"),
                  ("Spring", 1, "HIT: the ambush bite (ModGoldMimicSpring); the jaws lock on f2", "box (10, 7) 18 x 14")],
    "GoldWarden": [("Swing", 3, "HIT: the key comes down (ModGoldKeySwing, FxGiltKeyArc)", "bit (24, -6): box centre (16, -7) 22 x 16"),
                   ("Shackle", 3, "RELEASE: the key flies on its chain (ModGoldKey)", "fist (12, -14)")],
    "GoldRegent": [("Bolt", 3, "RELEASE: emerald bolt (ModGoldBolt)", "orb (15, -14.5)"),
                   ("Decree", 4, "RELEASE: the seal (ModGoldSeal) starts falling on the hero; lands 0.48 s later", "hero (ClosestEnemy)")],
    "GoldWyrm": [("Maul", 3, "HIT: jaws shut (ModGoldWyrmMaul)", "jaws (31, -8): box (24, 7) 18 x 14"),
                 ("Breath", 4, "RELEASE: three molten globs (-18, 0, 18 deg) on the floor line, art 12 px up", "(25, -1)")],
    "GoldVault": [("Slam", 4, "HIT: ingot fists + FxGiltQuake ring", "fists (17, 0): box (15, 4) 20 x 14, quake (17, 0)"),
                  ("Payout", 4, "RELEASE: GoldPayout (ring at the feet, one ingot per banked bar from (0, -14))", "(0, 0)")],
    "GoldSovereign": [("Smite", 3, "HIT: the sapphire head strikes (ModGoldSmite + FxGiltSmite)", "head (24, -6): box (21, 6) 16 x 14"),
                      ("Kneel", 4, "RELEASE: the crown ring closes on the hero (slams 0.84 s later)", "hero (ClosestEnemy)")],
    "GoldTreasurer": [("Quills", 3, "RELEASE: three quills (-12, 0, 12 deg)", "hand (12, -21)"),
                      ("Audit", 5, "RELEASE: the ledger page (ModGoldMark) falls on the hero, lands 0.2 s later", "hero (ClosestEnemy)")],
}


def write_timing(outdir):
    L = ["# The Gilded Secret: sprite timing", "",
         "Generated by `tools/sprites/goldsecret_rigs.py`. Monsters face right; feet = (cellW//2, cellH-2). FX origin = the",
         "effect's centre on the floor, given as the cell pixel passed to Strike.ArtAt / Strike.Ground. Spawn points are in",
         "pixels from the feet (x forward, y up NEGATIVE); the kits in src/CrawlFurther/Secrets/GoldSecretPack.cs use offsetY = -y.", "",
         "| Sheet | Cell (w x h) | Feet | Anims (frames) |", "|---|---|---|---|"]
    for n, _ in MONSTERS:
        if n not in BUILT: continue
        b = BUILT[n]; cw, ch = b["cell"]
        L.append("| %s | %d x %d | (%d, %d) | %s |" % (n, cw, ch, cw // 2, ch - 2, ", ".join("%s %d" % (a, k) for a, k, d in b["anims"])))
    L += ["", "## Sync frames", ""]
    for n, _ in MONSTERS:
        if n not in BUILT: continue
        anims = {a: (k, d) for a, k, d in BUILT[n]["anims"]}
        for an in sorted({e[0] for e in EVENTS[n]}, key=lambda a: [e[0] for e in EVENTS[n]].index(a)):
            k, d = anims[an]
            L += ["### %s / `%s`: %d frames, %.2f s" % (n, an, k, sum(d)), "Durations: " + ", ".join("%.2f" % x for x in d), "",
                  "| Frame | t (s) | Moment | Spawn point |", "|---|---|---|---|"]
            for (a2, fi, ev, sp) in EVENTS[n]:
                if a2 == an: L.append("| %d | %.2f | %s | %s |" % (fi, sum(d[:fi]), ev, sp))
            L.append("")
    L += ["Mimic special clip: Feign 3 + Lurk 4 x 2 + Spring 5 = 16 frames (Lurk waits up to 2.4 s).", "",
          "## Effect sheets", "", "| Sheet | Cell | Origin | Anims |", "|---|---|---|---|"]
    for n in FX_ORDER:
        if n not in BUILT: continue
        b = BUILT[n]; cw, ch = b["cell"]
        L.append("| %s | %d x %d | (%d, %d) | %s |" % (n, cw, ch, b["feet"][0], b["feet"][1],
                 ", ".join("%s %d, %.2f s" % (a, k, sum(d)) for a, k, d in b["anims"])))
    open(os.path.join(outdir, "TIMING.md"), "w").write("\n".join(L) + "\n")


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    only = None
    if "--only" in a:
        i = a.index("--only"); only = set(a[i + 1].split(",")); del a[i:i + 2]
    outdir = a[0] if a else DEFAULT_OUT
    os.makedirs(outdir, exist_ok=True)
    for n, fn in MONSTERS:
        if only is None or n in only: fn(outdir)
    build_fx(outdir, only)
    if only is None: write_timing(outdir)
    print("origins (cell x, y) for Strike.ArtAt / Ground:")
    for n in FX_ORDER:
        if n in BUILT: print("  %-16s cell %2dx%-2d origin (%d, %d)" % (n, BUILT[n]["cell"][0], BUILT[n]["cell"][1], BUILT[n]["feet"][0], BUILT[n]["feet"][1]))
    for k, v in NOTES.items(): print("  %s: %s" % (k, v))


if __name__ == "__main__":
    main()
