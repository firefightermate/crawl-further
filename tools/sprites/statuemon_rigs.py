"""SECRET STATUES: five secret tier-3 monsters offered ONLY by rare secret statues between fights (a statue variant
with a gold-seamed plinth that glints), and every effect sheet they use. Drawn at final size (no ArtScale entry),
Crawl's vanilla style (1 px dark outline, top-left light, readable on a dark floor).

    python3 tools/sprites/statuemon_rigs.py [outdir] [--only Name,Name]

Their shared identity (distinct from every god and from the silver/gold lines): LIVING STATUES. Each is carved from its
own stone (weathered granite, temple bronze, chess marble, peach marble, blue-veined angel marble) and each carries a
thin GOLD SEAM (kintsugi: a crack mended with gold), the same seam that marks their secret plinths.

  StmGrotesque   a crouching granite gargoyle with folded stone wings and ember eyes. It IS a statue: Set in Stone
                 turns it to stone (can't be hurt) and every hit it takes is thrown back as a shard when it breaks out;
                 the first killing blow only crumbles it to rubble, and it reforms.
  StmSixfold     a six-armed bronze temple idol on a jade lotus. Every basic swing is a random one of four weapons
                 (sword, mace, spear, flail); its special is a random rite of four readable shot patterns, its sigil
                 shown over its head beforehand.
  StmGambit      a living marble chess knight. Knight's Tour: three L-shaped leaps (landings marked first); a landing
                 on the hero puts him in check, and its next stamp on him lands harder.
  StmCaryatid    a marble temple maiden who carries a column capital on her head. She raises marble columns from the
                 floor that stand as solid stone, and shelters beside them.
  StmLachrymosa  LEGENDARY. A mourning angel of blue-veined marble with a cracked gilded halo (our own design). Seen
                 by the hero she is stone (slow, hard to hurt); unseen she is swift. Lights Out: she pinches out her
                 halo and the room goes dark for 2.5 s, and nobody can watch her.
"""
import math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import belmora_rigs as B          # noqa: E402  (primitives + sheet writer)
import silver_rigs as SV          # noqa: E402  (ring, sparks, star4, crescent, rot helpers; its palette is not used)
from rig import Canvas, line_px   # noqa: E402
from anim import Spr, SprRGB, PALETTE   # noqa: E402
from ghosts_v2_kit import selout_anims  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "art", "out_statuemon")

ell, tube, P, pick, ik = B.ell, B.tube, B.P, B.pick, B.ik
ring, sparks, star4, rot, rot_pt = SV.ring, SV.sparks, SV.star4, SV.rot, SV.rot_pt

# ------------------------------------------------------------------ palette (this pack only; Cyrillic letters)
PALETTE.update({
    'Ж': (0x19, 0x17, 0x1d),   # outline
    # granite (Grotesque)
    'а': (0x2a, 0x2c, 0x2b), 'б': (0x42, 0x46, 0x43), 'в': (0x5c, 0x61, 0x5b), 'г': (0x7a, 0x7f, 0x76),
    'д': (0x99, 0x9d, 0x92), 'е': (0xbd, 0xc0, 0xb2),
    'м': (0x4c, 0x60, 0x36), 'н': (0x6c, 0x82, 0x46),                       # moss
    'о': (0xb8, 0x44, 0x12), 'п': (0xff, 0x86, 0x26), 'р': (0xff, 0xd6, 0x76),   # ember
    # bronze / verdigris / jade (Sixfold)
    'с': (0x3a, 0x28, 0x1a), 'т': (0x68, 0x44, 0x24), 'у': (0x96, 0x64, 0x2e), 'ф': (0xc4, 0x8c, 0x42), 'х': (0xec, 0xc2, 0x68),
    'ц': (0x26, 0x54, 0x4a), 'ч': (0x42, 0x86, 0x72), 'ш': (0x74, 0xbc, 0xa0),
    'щ': (0x3c, 0xdc, 0xac), 'ъ': (0xb4, 0xff, 0xe2),
    'ю': (0x9a, 0x44, 0x62), 'я': (0xd8, 0x84, 0x9c),                       # lotus
    # gold seam (every statue)
    'ы': (0x86, 0x5e, 0x18), 'ь': (0xd6, 0xa6, 0x2e), 'э': (0xff, 0xe6, 0x86), 'й': (0xff, 0xff, 0xe8),
    # chess marble + onyx (Gambit)
    'А': (0x58, 0x56, 0x60), 'Б': (0x88, 0x86, 0x90), 'В': (0xb2, 0xb0, 0xb8), 'Г': (0xd6, 0xd4, 0xd8), 'Д': (0xf2, 0xf0, 0xee),
    'Е': (0x14, 0x12, 0x18), 'Ё': (0x2a, 0x28, 0x32), 'З': (0x46, 0x44, 0x52),
    'И': (0xb4, 0x16, 0x2c), 'Й': (0xff, 0x58, 0x66), 'К': (0x96, 0x8a, 0xa6),
    # peach marble + terracotta (Caryatid)
    'Л': (0x5a, 0x48, 0x40), 'М': (0x8a, 0x74, 0x64), 'Н': (0xb6, 0x9e, 0x86), 'О': (0xda, 0xc6, 0xaa), 'П': (0xf6, 0xea, 0xd4),
    'Р': (0x66, 0x2a, 0x1a), 'С': (0x9e, 0x48, 0x28), 'Т': (0xcc, 0x74, 0x42),
    # angel marble + tears (Lachrymosa)
    'Ф': (0x30, 0x34, 0x44), 'Х': (0x52, 0x58, 0x6c), 'Ц': (0x7a, 0x82, 0x96), 'Ч': (0xa4, 0xac, 0xbe), 'Ш': (0xcc, 0xd4, 0xe0),
    'Щ': (0x52, 0xa2, 0xe6), 'Ъ': (0x9c, 0xd8, 0xff), 'Ы': (0xe6, 0xf6, 0xff), 'Ь': (0x0e, 0x10, 0x18),
    'Э': (0x6a, 0x52, 0x86), 'Ю': (0x3a, 0x2c, 0x50),                       # dusk (her shadowed folds)
})
OUT = 'Ж'
GRAN = "абвгде"
GRAND = "абвг"
MOSS = "мн"
EMBER = "опр"
BRONZE = "стуфх"
VERD = "цчш"
JADE = "щъ"
GOLD = "ыьэй"
MARB = "АБВГД"
ONYX = "ЕЁЗ"
PEACH = "ЛМНОП"
TERRA = "РСТ"
ANGEL = "ФХЦЧШ"
TEARS = "ЩЪЫ"
# Crawl's palette: weathered, grimy stone and bronze; the gold seam (and the gargoyle's ember eyes) stay the accent
from ghosts_v2_kit import mute_palette  # noqa: E402
mute_palette(PALETTE, GRAN + MOSS + BRONZE + VERD + JADE + MARB + ONYX + PEACH + TERRA + ANGEL + TEARS, sat=0.6)
mute_palette(PALETTE, GOLD, sat=0.75)


# ------------------------------------------------------------------ frame with an outline
class Fr:
    """Layers: n = far (no outline), u = under (outlined, behind), b = body (outlined), g = glow (over the outline)."""

    def __init__(self, outline=OUT):
        self.n, self.u, self.b, self.g = Canvas(), Canvas(), Canvas(), Canvas()
        self.o = outline

    def done(self, clip=True):
        base = dict(self.u.px); base.update(self.b.px)
        out = dict(base)
        for (x, y) in base:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                k = (x + dx, y + dy)
                if k not in base: out[k] = self.o
        px = dict(self.n.px); px.update(out); px.update(self.g.px)
        if clip: px = {k: v for k, v in px.items() if k[1] <= 0}
        return Spr(px)


def gl(c, x0, y0, x1, y1, ramp, over=True):
    pts = line_px(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1)))
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        c.put(x, y, ramp[min(len(ramp) - 1, int(i / max(1, n) * len(ramp)))], over)
    return pts


def ln(c, x0, y0, x1, y1, ch, over=True):
    pts = line_px(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1)))
    for (x, y) in pts: c.put(x, y, ch, over)
    return pts


def poly(c, pts, ramp, over=True, bias=0.0):
    """Filled polygon shaded by a top-left light across its bbox."""
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    w, h = max(1.0, x1 - x0), max(1.0, y1 - y0)
    for y in range(int(math.floor(y0)), int(math.ceil(y1)) + 1):
        for x in range(int(math.floor(x0)), int(math.ceil(x1)) + 1):
            inside = False
            j = len(pts) - 1
            for i in range(len(pts)):
                xi, yi = pts[i]; xj, yj = pts[j]
                if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi): inside = not inside
                j = i
            if not inside: continue
            l = -(((x - x0) / w - 0.5) + ((y - y0) / h - 0.5)) * 1.2 + bias
            c.put(x, y, pick(ramp, l), over)


def seam(c, pts, k=0, glint=None):
    """The gold seam (kintsugi) along a polyline: dark gold with lighter flecks; `glint` lights one point of it."""
    i = 0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for (x, y) in line_px(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))):
            c.put(x, y, "ь" if (i + k) % 3 else "э")
            i += 1
    if glint is not None and pts:
        gx, gy = pts[min(len(pts) - 1, glint)]
        star4(c, gx, gy, size=1, ch="э", core="й")


def S_(c):
    return c.spr()


def inked(lay, part, ink, skip=()):
    """Lay `part` (a Canvas) over `lay` and draw `ink` on the layer's pixels bordering it, so overlapping limbs
    stay readable against the body behind them (vanilla draws inner contours the same way)."""
    for (x, y), v in part.px.items():
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            k = (x + dx, y + dy)
            if k not in part.px and k in lay.px and lay.px[k] not in skip: lay.px[k] = ink
    for (x, y), v in part.px.items(): lay.put(x, y, v)


BUILT = {}
NOTES = {}


def sheet(name, anims, outdir, scale=5):
    B.sheet(name, selout_anims(anims), outdir, scale=scale)
    BUILT[name] = B.BUILT[name]


def fx_sheet(name, anims, outdir, scale=6):
    B.fx_sheet(name, selout_anims(anims), outdir, scale=scale)
    BUILT[name] = B.BUILT[name]


def tail(idle0, death, death_d, knock, portrait=None):
    return [("Death", death, death_d), ("Dead", [death[-1]], [0.3]), ("Statue", [idle0.stone()], [0.2]),
            ("Knockback", [knock], [0.2]), ("Portrait", [portrait or idle0], [0.2])]


def rubble(c, cx, cy, w, ramp, seed, n=None, glow=None):
    """A heap of broken stone chunks centred at (cx, cy) on the floor."""
    rnd = random.Random(seed)
    n = n or int(w * 0.9)
    for i in range(n):
        x = cx + rnd.uniform(-w / 2, w / 2)
        hgt = (1 - abs(x - cx) / (w / 2 + 0.01)) * w * 0.28
        y = cy - rnd.uniform(0, hgt)
        r = rnd.uniform(1.0, 2.3)
        ell(c, x, y, r * 1.2, r, ramp, bias=rnd.uniform(-0.2, 0.2), jit=0.3, seed=seed + i)
    if glow:
        for i in range(3):
            c.put(*P(cx + rnd.uniform(-w / 4, w / 4), cy - rnd.uniform(1, w * 0.18)), glow[i % len(glow)])


# ======================================================================================= GROTESQUE (it IS a statue)
def bat_wing(lay, root, tips, ramp, mem="бв", bone="гд", seed=0):
    """A stone bat wing: bony fingers from the root to each tip, membrane filled between neighbouring fingers and
    sagging toward the root (scalloped trailing edge, lit 1 px rim); bones drawn over it."""
    rx, ry = root
    memb = set()
    for i in range(len(tips) - 1):
        (ax, ay), (bx, by) = tips[i], tips[i + 1]
        for t in range(0, 41):
            u = t / 40.0
            ex, ey = ax + (bx - ax) * u, ay + (by - ay) * u
            sag = math.sin(u * math.pi) * 0.3
            ex, ey = ex + (rx - ex) * sag, ey + (ry - ey) * sag
            for q in line_px(int(round(rx)), int(round(ry)), int(round(ex)), int(round(ey))): memb.add(q)
    bones = set()
    for (tx, ty) in tips:
        for q in line_px(int(round(rx)), int(round(ry)), int(round(tx)), int(round(ty))): bones.add(q)
    for (x, y) in memb:
        rim = any((x + ddx, y + ddy) not in memb and (x + ddx, y + ddy) not in bones for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        lay.put(x, y, mem[1] if rim else mem[0], over=False)
    for (tx, ty) in tips:
        pts = line_px(int(round(rx)), int(round(ry)), int(round(tx)), int(round(ty)))
        for k, (x, y) in enumerate(pts):
            lay.put(x, y, bone[1] if k > len(pts) * 0.35 else bone[0])
        lay.put(*P(tx, ty), bone[1])


def grotesque(dx=0.0, dy=0.0, lean=0.0, crouch=0.0, wing=0.0, arm=(8.0, 0.0), arm_b=(5.0, 0.0), legs=((-4.0, 0.0), (-7.0, 0.0)),
              head=(0.0, 0.0), jaw=0.0, tail=0.0, eyes=1, stone=False, cracks=0, claws=False, seed=0, glint=None):
    """The Grotesque, facing right, crouched on its knuckles. wing: 0 folded high, 1 half open, 2 spread."""
    f = Fr()
    R = "бвгдее" if stone else GRAN
    RD = "бвгд" if stone else GRAND
    cy0 = dy + crouch
    hip = (dx - 4.5 + lean * 0.2, -7.5 + cy0)
    ch = (dx + 1.5 + lean, -12.5 + cy0)            # chest
    sh = (ch[0] + 2.0, ch[1] - 1.0)                # shoulder
    hd = (ch[0] + 6.0 + head[0], ch[1] - 5.0 + head[1])
    # ---- wings (behind everything): root on the upper back
    wr = (ch[0] - 3.5, ch[1] - 3.5)
    if wing <= 0.5:
        tips = [(wr[0] - 9.0, wr[1] - 3.0), (wr[0] - 7.0, wr[1] - 11.0), (wr[0] - 2.5, wr[1] - 14.0)]
    elif wing <= 1.5:
        tips = [(wr[0] - 12.0, wr[1] - 3.0), (wr[0] - 10.0, wr[1] - 11.0), (wr[0] - 4.0, wr[1] - 15.0)]
    else:
        tips = [(wr[0] - 15.0, wr[1] + 1.0), (wr[0] - 14.0, wr[1] - 9.0), (wr[0] - 7.0, wr[1] - 16.0)]
    far_tips = [(x + 3.0, y - 1.0) for (x, y) in tips]
    bat_wing(f.u, (wr[0] + 2.0, wr[1]), far_tips, RD, mem="аб", bone="бв")
    bat_wing(f.u, wr, tips, R, mem="бв", bone="ге")
    # ---- tail: from the rump, curling, with a spade tip
    t0 = (hip[0] - 3.5, hip[1] + 1.5)
    sw = math.sin(tail) * 1.5
    tpts = [t0, (t0[0] - 4.0, t0[1] + 3.0 + sw * 0.3), (t0[0] - 8.0, t0[1] + 2.0 + sw), (t0[0] - 9.5, t0[1] - 2.0 + sw)]
    tube(f.u, tpts, [1.4, 1.1, 0.9, 0.7], RD)
    tx, ty = tpts[-1]
    for (x, y) in ((0, 0), (-1, -1), (1, -1), (0, -1), (0, -2)): f.u.put(*P(tx + x, ty + y), R[2] if y < -1 else R[1])
    # ---- far hind leg + far arm
    fl = legs[1]
    (kx, ky), _ = ik(hip[0] - 1.0, hip[1], dx + fl[0], fl[1] - 1.0, 4.4, 4.6, bend=-1)
    tube(f.u, [(hip[0] - 1.0, hip[1]), (kx, ky), (dx + fl[0], fl[1] - 1.0)], [2.2, 1.4, 1.1], RD)
    f.u.put(*P(dx + fl[0] + 1, fl[1]), RD[1]); f.u.put(*P(dx + fl[0] + 2, fl[1]), RD[0])
    (ex, ey), _ = ik(sh[0] - 1.5, sh[1] + 1.0, dx + arm_b[0], arm_b[1] - 1.0, 5.2, 5.6, bend=1)
    tube(f.u, [(sh[0] - 1.5, sh[1] + 1.0), (ex, ey), (dx + arm_b[0], arm_b[1] - 1.0)], [1.6, 1.2, 1.0], RD)
    for k in range(3): f.u.put(*P(dx + arm_b[0] + k * 0.8, arm_b[1]), RD[0])
    # ---- torso: a hunched barrel leaning forward
    ell(f.b, hip[0] + 0.5, hip[1] - 0.5, 4.6, 4.2, R, bias=-0.05)             # haunch
    ell(f.b, ch[0] - 1.5, ch[1] + 0.5, 6.4, 5.0, R, ang=-22 - lean * 3, bias=0.05)
    # ribs / belly plates
    for k in range(3):
        f.b.put(*P(ch[0] - 1.0 + k * 1.6, ch[1] + 3.6 - k * 0.3), R[1])
    # spine ridge knobs
    for k in range(4):
        f.b.put(*P(ch[0] - 5.0 + k * 2.2, ch[1] - 4.2 - k * 0.5), R[4])
    # ---- near hind leg: big crouched thigh, clawed foot
    nl = legs[0]
    (kx, ky), _ = ik(hip[0] + 1.0, hip[1] + 0.5, dx + nl[0], nl[1] - 1.0, 4.6, 4.6, bend=-1)
    ell(f.b, (hip[0] + kx) / 2 + 0.5, (hip[1] + ky) / 2, 3.2, 2.4, R, ang=-30, bias=0.1)
    tube(f.b, [(kx, ky), (dx + nl[0], nl[1] - 1.0)], [1.5, 1.2], R)
    for k in range(4): f.b.put(*P(dx + nl[0] - 1 + k, nl[1]), R[1] if k < 3 else R[0])
    f.b.put(*P(dx + nl[0] + 3, nl[1] - 1), R[3])
    # ---- head: heavy brow, snout, fangs, swept horns, pointed ear
    hx, hy = hd
    ell(f.b, hx - 0.5, hy, 3.8, 3.4, R, bias=0.05)
    ell(f.b, hx + 3.0, hy + 1.2, 2.6, 1.8, R, bias=0.15)                       # snout
    # jaw (opens downward)
    jy = hy + 3.0 + jaw * 2.2
    ell(f.b, hx + 2.0, jy, 2.6, 1.2, R, bias=-0.2)
    if jaw > 0.2 and not stone:
        for x in range(int(hx), int(hx + 4)):
            f.b.put(x, int(round(hy + 2.4 + jaw)), "о")
    f.b.put(*P(hx + 4.4, hy + 2.6), R[5]); f.b.put(*P(hx + 2.8, hy + 2.6 + jaw * 0.5), R[5])   # fangs
    # brow ridge + horns
    gl(f.b, hx - 2.5, hy - 2.6, hx + 2.6, hy - 1.4, R[3:])
    horn = [(hx - 1.0, hy - 2.8), (hx - 3.0, hy - 5.6), (hx - 6.0, hy - 6.8), (hx - 8.0, hy - 6.2)]
    tube(f.b, horn, [1.3, 1.0, 0.7, 0.4], R, bias=0.2)
    f.u.put(*P(hx + 0.5, hy - 4.6), R[2]); f.u.put(*P(hx + 0.0, hy - 5.6), R[3])  # far horn stub
    ell(f.b, hx - 3.5, hy - 0.5, 1.4, 2.2, R, ang=35, bias=0.1)                # ear
    # eyes: ember
    if stone:
        f.b.put(*P(hx + 1.2, hy - 0.6), "а")
    elif eyes:
        f.g.put(*P(hx + 1.2, hy - 0.6), "р"); f.g.put(*P(hx + 2.0, hy - 0.6), "п")
    else:
        f.b.put(*P(hx + 1.2, hy - 0.6), "о")
    # ---- near arm: long, knuckles down, talons
    (ex, ey), _ = ik(sh[0], sh[1] + 0.5, dx + arm[0], arm[1] - 1.2, 5.6, 6.0, bend=1)
    tube(f.b, [(sh[0], sh[1] + 0.5), (ex, ey), (dx + arm[0], arm[1] - 1.2)], [2.0, 1.5, 1.3], R, bias=0.05)
    ell(f.b, sh[0] + 0.2, sh[1] + 0.2, 2.4, 2.0, R, bias=0.2)                # shoulder knob
    ax_, ay_ = dx + arm[0], arm[1]
    if claws:
        for k in range(3):
            gl(f.b, ax_, ay_ - 1.2, ax_ + 2.8 + k * 0.4, ay_ - 2.6 + k * 1.7, R[3:])
            f.b.put(*P(ax_ + 2.8 + k * 0.4, ay_ - 2.6 + k * 1.7), R[5])
    else:
        for k in range(3): f.b.put(*P(ax_ - 0.5 + k, ay_), R[1])
        f.b.put(*P(ax_ + 2.4, ay_ - 0.5), R[4])
    spr = f.done()
    px = dict(spr.px)
    # moss on upward-facing granite (stable pattern in body space) and the gold seam across the chest
    if not stone:
        ox, oy = int(round(dx)), int(round(cy0))
        for (x, y), v in list(px.items()):
            if v in R[2:5] and (x, y - 1) in px and px[(x, y - 1)] == OUT and ((x - ox) * 7 + (y - oy) * 3) % 5 == 0:
                px[(x, y)] = "н" if v != R[2] else "м"
    c2 = Canvas(); c2.px = px
    seam(c2, [(ch[0] - 5.0, ch[1] - 1.5), (ch[0] - 2.5, ch[1] + 0.5), (ch[0] - 0.5, ch[1] - 0.5), (ch[0] + 1.5, ch[1] + 2.0)],
         k=seed, glint=glint)
    # cracks (Set in Stone stores the hero's hits as cracks)
    rnd = random.Random(77)
    for i in range(cracks):
        x0, y0 = ch[0] - 5 + rnd.uniform(0, 9), ch[1] - 4 + rnd.uniform(0, 7)
        pts = [(x0, y0)]
        for k in range(3):
            pts.append((pts[-1][0] + rnd.uniform(-2, 2), pts[-1][1] + rnd.uniform(0.5, 2)))
        for (a, b) in zip(pts, pts[1:]):
            for q in line_px(*P(*a), *P(*b)):
                if q in px: c2.px[q] = "а"
    return Spr(c2.px), {"head": hd, "chest": ch, "hand": (dx + arm[0], arm[1])}


def grot_corpse(stage):
    """Death: it cracks and falls apart into a heap of granite (no reform this time); the ember eyes go out."""
    c = Canvas()
    rubble(c, 0, 0, 22 - stage * 2, GRAN, 9 + stage, glow=("о", "а") if stage == 0 else None)
    # a broken wing finger and a horn lying on the heap
    gl(c, -9, -1, -3, -5 + stage, "вгд")
    gl(c, 4, -3, 8, -5, "гд")
    f = Fr(); f.b = c
    s = f.done()
    c2 = Canvas(); c2.px = dict(s.px)
    seam(c2, [(-4, -2), (-1, -3), (2, -2)])
    return Spr(c2.px)


def build_grotesque(outdir):
    S = lambda **k: grotesque(**k)[0]
    idle = []
    for i in range(4):
        b = [0.0, 0.3, 0.6, 0.3][i]
        idle.append(S(dy=b, wing=0.0, tail=i * 1.6, head=(0, b * 0.5), seed=i, eyes=0 if i == 3 else 1,
                      arm=(8.0, 0.0), jaw=0.0))
    run = []
    for i in range(6):
        ph = i / 6 * 2 * math.pi
        a, c = math.cos(ph), math.sin(ph)
        # a loping knuckle-gallop: arms and legs alternate, the body rocks
        run.append(S(dx=0.0, dy=-max(0.0, c) * 1.6, lean=1.0 + a * 0.6, wing=0.6 if c > 0 else 0.2,
                     arm=(9.0 + a * 3.5, -max(0.0, -c) * 2.0), arm_b=(6.0 - a * 3.0, -max(0.0, c) * 1.6),
                     legs=((-4.0 - a * 3.0, -max(0.0, c) * 1.6), (-7.0 + a * 3.0, -max(0.0, -c) * 1.5)),
                     tail=ph * 2, seed=10 + i, jaw=0.3))
    # Rake: rear back with the near arm up, lunge and rake the talons down (hit on frame 3)
    rk = []
    keys = [
        dict(lean=-1.0, crouch=1.0, arm=(7.0, -3.0), wing=0.6),
        dict(lean=-2.5, crouch=-1.0, arm=(4.0, -16.0), wing=1.0, jaw=0.6, claws=True),
        dict(lean=-3.0, crouch=-2.0, arm=(3.0, -18.0), wing=1.4, jaw=1.0, claws=True),
        dict(lean=3.5, crouch=1.0, arm=(14.0, -6.0), wing=1.6, jaw=1.0, claws=True),
        dict(lean=3.0, crouch=1.5, arm=(13.0, -1.0), wing=1.0, jaw=0.6, claws=True),
        dict(lean=1.5, crouch=0.5, arm=(10.0, 0.0), wing=0.6, jaw=0.2),
        dict(lean=0.0, crouch=0.0, arm=(8.0, 0.0), wing=0.0),
    ]
    for i, k in enumerate(keys):
        rk.append(S(seed=20 + i, tail=i * 1.2, **k))
    rk_d = [0.1, 0.12, 0.1, 0.05, 0.08, 0.1, 0.1]
    # Set in Stone: wings wrap, it hunches and greys (StoneOn 4), holds as stone (StoneHold 2), bursts out (StoneBurst 4)
    son = [S(wing=0.3, crouch=1.0, seed=30),
           S(wing=0.0, crouch=2.0, head=(-1, 1), seed=31, eyes=0),
           S(wing=0.0, crouch=2.5, head=(-1, 1.5), seed=32, stone=True, cracks=0),
           S(wing=0.0, crouch=2.5, head=(-1, 1.5), seed=33, stone=True, cracks=1)]
    shold = [S(wing=0.0, crouch=2.5, head=(-1, 1.5), seed=33, stone=True, cracks=1),
             S(wing=0.0, crouch=2.5, head=(-1, 1.5), seed=33, stone=True, cracks=2)]
    sbur = [S(wing=0.0, crouch=1.5, head=(-1, 1.0), stone=True, cracks=5, seed=34),
            S(wing=2.0, crouch=-1.5, jaw=1.0, seed=35, claws=True, arm=(9.0, -5.0)),
            S(wing=1.6, crouch=-0.5, jaw=0.8, seed=36, arm=(9.0, -2.0)),
            S(wing=0.4, seed=37)]
    # stone shell chips flying off the burst frame
    c = Canvas(); c.px = dict(sbur[1].px)
    for k in range(8):
        a = k / 8 * 2 * math.pi
        c.put(*P(math.cos(a) * 15, -12 + math.sin(a) * 11), "д" if k % 2 else "г")
    sbur[1] = Spr(c.px)
    # Crumble (involuntary, its passive): it falls apart (5), lies as rubble with an ember heart (2), reforms (6)
    cr = []
    for i in range(5):
        if i < 2:
            cr.append(S(crouch=2.0 + i * 2, wing=0.0, cracks=3 + i * 2, eyes=0, head=(0, 1 + i), seed=40 + i))
        else:
            cc = Canvas(); rubble(cc, 0, 0, 16 + i * 2, GRAN, 41 + i, glow="оп")
            f = Fr(); f.b = cc; cr.append(f.done())
    rb = []
    for i in range(2):
        cc = Canvas(); rubble(cc, 0, 0, 20, GRAN, 44)
        f = Fr(); f.b = cc; s = f.done()
        c2 = Canvas(); c2.px = dict(s.px)
        # the ember heart pulses in the heap
        c2.put(0, -3, "п" if i == 0 else "р"); c2.put(1, -3, "о"); c2.put(0, -4, "о" if i == 0 else "п")
        seam(c2, [(-6, -1), (-2, -4), (3, -2)], k=i)
        rb.append(Spr(c2.px))
    rf = []
    for i in range(6):
        if i < 2:
            cc = Canvas(); rubble(cc, 0, 0, 20 - i * 3, GRAN, 45 + i, glow="пр")
            f = Fr(); f.b = cc; s = f.done()
            c2 = Canvas(); c2.px = dict(s.px)
            for k in range(5 + i * 3):
                a = k * 2.4
                c2.put(*P(math.cos(a) * (10 - i * 3), -2 - abs(math.sin(a)) * (6 + i * 4)), "г" if k % 2 else "д")
            rf.append(Spr(c2.px))
        else:
            rf.append(S(crouch=[3.0, 1.5, 0.5, 0.0][i - 2], wing=[0.0, 1.0, 1.6, 0.4][i - 2], cracks=[3, 1, 0, 0][i - 2],
                        jaw=[0, 0.8, 1.0, 0][i - 2], seed=50 + i))
    d0 = S(lean=-2.0, crouch=1.0, wing=1.0, jaw=1.0, cracks=2, seed=60)
    d1 = S(crouch=3.5, wing=0.2, cracks=6, eyes=0, head=(0, 2), seed=61)
    d2 = grot_corpse(0)
    d3 = grot_corpse(1)
    knock = S(lean=-3.0, crouch=-1.0, wing=1.4, jaw=0.8, arm=(6.0, -4.0), seed=65)
    portrait = grotesque(wing=0.5, jaw=0.4, seed=0)[0]
    sheet("StmGrotesque", [("Idle", idle, [0.22, 0.2, 0.22, 0.12]), ("Run", run, [0.08] * 6),
                           ("Rake", rk, rk_d), ("StoneOn", son, [0.08, 0.1, 0.1, 0.12]), ("StoneHold", shold, [0.2, 0.2]),
                           ("StoneBurst", sbur, [0.08, 0.06, 0.1, 0.12]),
                           ("Crumble", cr, [0.08, 0.1, 0.12, 0.12, 0.14]), ("Rubble", rb, [0.25, 0.25]),
                           ("Reform", rf, [0.12, 0.12, 0.1, 0.08, 0.1, 0.12])] +
          tail(idle[0], [d0, d1, d2, d3], [0.12, 0.16, 0.18, 0.3], knock, portrait), outdir)
    _, k3 = grotesque(**dict(lean=3.5, crouch=1.0, arm=(14.0, -6.0), wing=1.6, jaw=1.0, claws=True))
    NOTES["StmGrotesque"] = "rake hand on the hit frame %s, chest %s" % (tuple(round(v, 1) for v in k3["hand"]),
                                                                         tuple(round(v, 1) for v in k3["chest"]))


# ======================================================================================= SIXFOLD IDOL (random attacks)
def patina(spr, ox, oy, k=0):
    """Verdigris pooling over bronze in soft patches (low-frequency, stable in body space), heaviest on the darker,
    lower tones; the lit bronze stays clean."""
    out = dict(spr.px)
    for (x, y), v in spr.px.items():
        u, w = x - ox, y - oy
        n = math.sin(u * 0.55 + 1.3) + math.sin(w * 0.7 + u * 0.25) + 0.35 * math.sin(u * 1.7 - w * 1.1)
        if v == "с" and n > 0.2: out[(x, y)] = "ц"
        elif v == "т" and n > 0.5: out[(x, y)] = "ц"
        elif v == "у" and n > 1.1: out[(x, y)] = "ч"
    return Spr(out)


def idol_arm(lay, sh, hand, ramp, r=(1.3, 1.0, 1.1), bend=1, bracelet=True):
    (ex, ey), _ = ik(sh[0], sh[1], hand[0], hand[1], 4.4, 4.4, bend=bend)
    tube(lay, [sh, (ex, ey), hand], list(r), ramp, bias=0.1)
    if bracelet:
        mx, my = (ex + hand[0]) / 2, (ey + hand[1]) / 2
        lay.put(*P(mx, my), "ь")
    ell(lay, hand[0], hand[1], 1.2, 1.1, ramp, bias=0.2)
    return (ex, ey)


def idol_sword(lay, g, hand, ang, L=11, smear=0):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    # hilt + guard
    lay.put(*P(hand[0] - ca * 1.5, hand[1] - sa * 1.5), "ы")
    nx, ny = -sa, ca
    for k in (-2, -1, 1, 2): lay.put(*P(hand[0] + ca * 1.0 + nx * k, hand[1] + sa * 1.0 + ny * k), "ь")
    # a wavy kris blade, bronze with a gold edge
    for i in range(2, L + 1):
        w = math.sin(i * 0.9) * 0.6
        x, y = hand[0] + ca * i + nx * w, hand[1] + sa * i + ny * w
        lay.put(*P(x, y), "х" if i % 3 else "ф")
        lay.put(*P(x - nx, y - ny), "у")
    g.put(*P(hand[0] + ca * L, hand[1] + sa * L), "э")
    if smear:
        for step in range(1, smear * 10):
            a2 = math.radians(ang - step * 3)
            for rr, ch in ((L + 1.0, "э"), (L, "х"), (L - 1.0, "ф")):
                g.put(*P(hand[0] + math.cos(a2) * rr, hand[1] + math.sin(a2) * rr), ch if step < smear * 5 else "ь", over=False)


def idol_spear(lay, g, hand, ang, fwd=10, back=8):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    gl(lay, hand[0] - ca * back, hand[1] - sa * back, hand[0] + ca * fwd, hand[1] + sa * fwd, "тууф")
    tx, ty = hand[0] + ca * fwd, hand[1] + sa * fwd
    nx, ny = -sa, ca
    # leaf blade in jade-gold
    for i in range(1, 5):
        w = [1.2, 1.4, 1.0, 0.4][i - 1]
        for k in (-1, 0, 1):
            lay.put(*P(tx + ca * i + nx * w * k, ty + sa * i + ny * w * k), "ш" if k == 0 else "ч")
    g.put(*P(tx + ca * 5, ty + sa * 5), "ъ")
    lay.put(*P(tx, ty), "ь")


def idol_mace(lay, g, hand, ang, L=7, glow=False):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    gl(lay, hand[0] - ca * 1.5, hand[1] - sa * 1.5, hand[0] + ca * L, hand[1] + sa * L, "ту")
    hx, hy = hand[0] + ca * (L + 1.5), hand[1] + sa * (L + 1.5)
    ell(lay, hx, hy, 2.4, 2.4, BRONZE, bias=0.1)
    for k in range(6):
        a = k / 6 * 2 * math.pi
        lay.put(*P(hx + math.cos(a) * 3.0, hy + math.sin(a) * 3.0), "ф" if k < 3 else "у")
    lay.put(*P(hx - 0.6, hy - 0.8), "ь")
    if glow: g.put(*P(hx - 1, hy - 1), "э")
    return hx, hy


def idol_flail(lay, g, hand, ball, links=4):
    """A short handle and a chain to a spiked jade-bronze ball at `ball`."""
    hx, hy = hand
    gl(lay, hx, hy, hx + 1.5, hy - 2.0, "ту")
    sx, sy = hx + 1.5, hy - 2.0
    bx, by = ball
    for i in range(1, links + 1):
        t = i / (links + 1)
        lay.put(*P(sx + (bx - sx) * t, sy + (by - sy) * t + math.sin(t * math.pi) * 1.0), "ф" if i % 2 else "у")
    ell(lay, bx, by, 2.0, 2.0, "цчшъ", bias=0.1)
    for k in range(4):
        a = k / 4 * 2 * math.pi + 0.4
        lay.put(*P(bx + math.cos(a) * 2.8, by + math.sin(a) * 2.8), "ф")


def sixfold(dx=0.0, dy=0.0, bob=0.0, lean=0.0, sword=None, spear=None, mace=None, flail=None, hands=None,
            eye=1, crown_glint=None, seed=0, smear=0, glow_hands=False, cast=0.0, lotus_open=0.0, sigil=None):
    """The Sixfold Idol hovering on its lotus, facing right. Each weapon arg = (hand x, hand y, angle) relative to the
    shoulder line; None = rest pose. flail = (hand x, hand y, ball x, ball y)."""
    f = Fr()
    hover = -3.0 + bob + dy
    # ---- lotus (petals fan from a jade cup)
    lc = (dx, hover - 1.0)
    for k, a in enumerate((-160, -130, -100, -80, -50, -20)):
        r = 6.5 + lotus_open
        ax, ay = lc[0] + math.cos(math.radians(a)) * r * 1.3, lc[1] + math.sin(math.radians(a)) * r * 0.45
        ell(f.u if k in (0, 5) else f.b, (lc[0] + ax) / 2, (lc[1] + ay) / 2 + 0.5, 3.0, 1.4, "юяя" if k % 2 else "юя",
            ang=a * 0.25, bias=0.2)
    ell(f.b, lc[0], lc[1] + 0.8, 4.5, 1.3, "цчш", bias=0.1)
    # ---- crossed legs
    ell(f.b, dx, hover - 3.6, 7.0, 2.3, "стууф", bias=-0.2)
    ell(f.b, dx + 4.5, hover - 3.2, 1.8, 1.2, BRONZE, bias=0.2)           # near foot sole
    # ---- torso
    tx, ty = dx + lean * 0.5, hover - 10.0
    sx, sy = tx, ty - 3.5                     # shoulder line
    # far arms (under): spear (top), flail (mid), far casting hand (low)
    sp = spear or (-5.5, -5.0, -95)
    h = (sx - 2.5 + sp[0], sy + sp[1])
    idol_spear(f.u, f.g, h, sp[2], fwd=9 if sp[2] < -60 else 11, back=9)
    idol_arm(f.u, (sx - 2.5, sy - 0.5), h, "стуф", bend=-1)
    fl = flail or (-7.0, 2.0, -8.5, 6.5)
    h = (sx - 2.5 + fl[0], sy + fl[1])
    idol_arm(f.u, (sx - 2.5, sy + 2.0), h, "стуф", bend=-1)
    idol_flail(f.u, f.g, h, (sx + fl[2], sy + fl[3]))
    hb = hands[1] if hands else (2.0, 7.0)
    idol_arm(f.u, (sx - 2.0, sy + 4.0), (sx + hb[0], sy + hb[1]), "стуф", bend=-1, bracelet=False)
    # body
    ell(f.b, tx, ty, 6.0, 6.8, "стууфх", bias=-0.1)
    ell(f.b, tx + 0.4, ty + 4.2, 4.2, 1.6, "стууф", bias=-0.2)           # belly
    # gold collar + belt
    for k in range(-4, 5):
        f.b.put(*P(tx + k, ty - 4.2 + abs(k) * 0.35), "ь" if k % 2 else "э")
    for k in range(-4, 5): f.b.put(*P(tx + k, ty + 2.6), "ы" if k % 3 else "ь")
    # ---- head + tiered crown
    hx, hy = tx + 1.2, ty - 9.5
    ell(f.b, hx, hy, 3.4, 3.6, "стуфх", bias=0.05)
    ell(f.b, hx + 2.6, hy + 0.6, 1.0, 1.4, BRONZE, bias=0.2)              # nose / profile
    f.b.put(*P(hx + 1.6, hy + 0.4), "с")                                 # closed eye line
    f.b.put(*P(hx + 2.2, hy + 0.4), "с")
    f.b.put(*P(hx + 1.8, hy + 2.4), "у")                                 # serene lips
    f.b.put(*P(hx - 2.5, hy + 0.5), "ь"); f.b.put(*P(hx - 2.5, hy + 1.5), "э")   # earring
    for t, (w, hh) in enumerate(((3.4, 1.3), (2.6, 1.2), (1.8, 1.1), (1.0, 1.0))):
        cy_ = hy - 3.2 - t * 2.2
        ell(f.b, hx - 0.2, cy_, w, hh, "ыьэ", bias=0.0)
        for k in range(-int(w), int(w) + 1): f.b.put(*P(hx - 0.2 + k, cy_ + hh), "с")   # dark groove under each tier
    f.b.put(*P(hx - 0.2, hy - 12.6), "э")
    # third eye (jade): opens wide during the cast
    if eye:
        f.g.put(*P(hx + 1.0, hy - 2.0), "ъ" if eye == 2 or cast > 0.5 else "щ")
        if cast > 0.5: star4(f.g, hx + 1.0, hy - 2.0, size=1, ch="щ", core="ъ")
    if crown_glint is not None:
        star4(f.g, hx - 0.2 + crown_glint[0], hy - 6 + crown_glint[1], size=1, ch="э", core="й")
    # ---- near arms (over): sword (top), mace (mid), near casting hand (low); each inked against what is behind it
    NB = "стуф"
    hn = hands[0] if hands else (4.5, 6.0)
    orb = (sx + (hn[0] + hb[0]) / 2 + 1.5, sy + (hn[1] + hb[1]) / 2 - 1.0)
    part = Canvas()
    idol_arm(part, (sx + 2.5, sy + 4.0), (sx + hn[0], sy + hn[1]), NB, bracelet=False)
    inked(f.b, part, "с")
    if glow_hands or cast > 0:
        ell(f.g, orb[0], orb[1], 1.6 + cast, 1.6 + cast, "щщъ", bias=0.3)
        f.g.put(*P(orb[0] - 0.5, orb[1] - 0.5), "ъ")
    else:
        ell(f.b, orb[0], orb[1], 1.4, 1.4, "цчш", bias=0.3)
    ma = mace or (6.5, 2.5, -35)
    h = (sx + 2.5 + ma[0], sy + ma[1])
    part = Canvas()
    idol_arm(part, (sx + 2.5, sy + 1.5), h, NB)
    idol_mace(part, f.g, h, ma[2])
    inked(f.b, part, "с")
    sw = sword or (4.5, -6.5, -75)
    h = (sx + 2.5 + sw[0], sy + sw[1])
    part = Canvas()
    idol_arm(part, (sx + 2.0, sy - 1.0), h, NB)
    idol_sword(part, f.g, h, sw[2], smear=smear)
    inked(f.b, part, "с")
    spr = f.done()
    spr = patina(spr, int(round(dx)), int(round(hover)), seed)
    c = Canvas(); c.px = dict(spr.px)
    # the gold seam: a mended crack down the face of the torso
    seam(c, [(tx - 1.5, ty - 3.0), (tx + 0.5, ty - 0.5), (tx - 0.5, ty + 1.5), (tx + 1.0, ty + 3.5)], k=seed)
    if sigil:
        sigil_mark(c, hx, hy - 17, sigil, 0)
    return Spr(c.px), {"head": (hx, hy), "torso": (tx, ty), "shoulder": (sx, sy), "orb": orb}


def sigil_mark(c, x, y, kind, frame):
    """The four rites' sigils (also the indicator sheet FxStmSigil): Ring, Fan, Spiral, Cross. Jade on gold."""
    x, y = int(round(x)), int(round(y))
    if kind == "Ring":
        ring(c, x, y, 4.0, 1.0, "ыьэ", thick=1)
        for k in range(8):
            a = k / 8 * 2 * math.pi + frame * 0.2
            c.put(*P(x + math.cos(a) * 6, y + math.sin(a) * 6), "ъ" if (k + frame) % 2 else "щ")
    elif kind == "Fan":
        for k in range(5):
            a = math.radians(-60 + k * 30)
            gl(c, x - 3, y + 2, x - 3 + math.cos(a - math.pi / 2 + math.pi / 2) * 0 + math.sin(a) * 7 - 0, y + 2 - math.cos(a) * 7, "ыьэ")
            c.put(*P(x - 3 + math.sin(a) * 8, y + 2 - math.cos(a) * 8), "ъ" if (k + frame) % 2 else "щ")
    elif kind == "Spiral":
        for i in range(26):
            t = i / 25
            a = t * 3.6 * math.pi + frame * 0.6
            r = 0.8 + t * 5.4
            c.put(*P(x + math.cos(a) * r, y + math.sin(a) * r), "э" if i % 4 == 0 else ("ь" if t < 0.7 else "щ"))
        c.put(x, y, "ъ")
    elif kind == "Cross":
        for k in range(-5, 6):
            c.put(x + k, y, "ь" if abs(k) < 4 else "щ"); c.put(x, y + k, "ь" if abs(k) < 4 else "щ")
        for k in (-4, 4):
            for j in (-4, 4):
                c.put(x + k // 2 * (1 if j > 0 else -1) // 1, y + j // 2, "э" if frame % 2 else "ы")
        star4(c, x, y, size=1, ch="э", core="ъ")


def sixfold_corpse(stage):
    c = Canvas()
    rubble(c, -2, 0, 18 - stage * 2, BRONZE, 70 + stage)
    # the crown rolls off, a jade lotus petal or two
    ell(c, 7, -2, 2.4, 1.6, "ыьэ", bias=0.2); c.put(7, -4, "э")
    ell(c, -8, -1, 2.2, 1.0, "юя", bias=0.2)
    gl(c, -12, -1, -4, -3, "тууф")
    f = Fr(); f.b = c
    s = patina(f.done(), 0, 0, stage)
    c2 = Canvas(); c2.px = dict(s.px)
    seam(c2, [(-5, -2), (-2, -4), (1, -2)])
    if stage == 0:
        for k in range(3): c2.put(-3 + k * 3, -6 - k, "щ")
    return Spr(c2.px)


def build_sixfold(outdir):
    S = lambda **k: sixfold(**k)[0]
    idle = []
    for i in range(4):
        b = [0.0, -0.5, -1.0, -0.5][i]
        idle.append(S(bob=b, seed=i, crown_glint=(1, -1) if i == 1 else None,
                      flail=(-7.0, 2.0, -8.5 + [0, 0.5, 1, 0.5][i], 6.5),
                      sword=(4.5, -6.5 + b * 0.3, -75 + i), spear=(-5.5, -5.0, -95 + [0, 1, 2, 1][i])))
    run = []
    for i in range(6):
        ph = i / 6 * 2 * math.pi
        b = -1.0 - math.sin(ph) * 0.8
        run.append(S(dx=0.5, bob=b, lean=1.5, seed=10 + i, flail=(-7.0, 2.0, -11.0 + math.cos(ph), 4.0 + math.sin(ph)),
                     sword=(5.0, -6.0, -60), spear=(-5.0, -6.5, -80), lotus_open=0.5 * math.sin(ph)))
    # CUT (sword, top near arm): raise back, slash down-forward in a wide arc (hit 3)
    cut = []
    keys = [dict(sword=(2.0, -9.0, -110)), dict(sword=(0.0, -11.0, -150), lean=-1.0),
            dict(sword=(1.0, -12.0, -165), lean=-1.5),
            dict(sword=(8.0, -3.0, -10), lean=2.0, smear=4), dict(sword=(8.5, 0.5, 25), lean=2.0, smear=2),
            dict(sword=(6.5, -3.0, -30), lean=1.0), dict(sword=(4.5, -6.5, -75))]
    for i, k in enumerate(keys): cut.append(S(seed=20 + i, **k))
    cut_d = [0.1, 0.1, 0.1, 0.05, 0.08, 0.1, 0.1]
    # SLAM (mace, mid near arm): heave overhead, smash down on the floor in front (hit 3)
    slam = []
    keys = [dict(mace=(4.0, -3.0, -80)), dict(mace=(2.0, -8.0, -120), lean=-1.0), dict(mace=(0.0, -10.0, -150), lean=-1.5, bob=-1),
            dict(mace=(10.0, 4.0, 40), lean=2.5, bob=1.0), dict(mace=(10.0, 5.0, 50), lean=2.5, bob=1.0),
            dict(mace=(8.0, 3.0, 0), lean=1.0), dict(mace=(6.5, 2.5, -35))]
    for i, k in enumerate(keys): slam.append(S(seed=30 + i, **k))
    slam_d = [0.1, 0.12, 0.12, 0.05, 0.1, 0.1, 0.1]
    # THRUST (spear, top far arm): draw back, then drive it straight forward across the body (hit 3), long reach
    th = []
    keys = [dict(spear=(-4.0, -3.0, -40)), dict(spear=(-7.0, -1.0, -5), lean=-1.0), dict(spear=(-9.0, -1.0, 0), lean=-2.0),
            dict(spear=(9.0, -1.0, 0), lean=2.5), dict(spear=(10.0, -1.0, 0), lean=2.5),
            dict(spear=(2.0, -4.0, -40), lean=1.0), dict(spear=(-5.5, -7.0, -95))]
    for i, k in enumerate(keys): th.append(S(seed=40 + i, **k))
    th_d = [0.1, 0.1, 0.1, 0.04, 0.1, 0.1, 0.1]
    # WHIRL (flail, mid far arm): whirl the ball once all round the idol (hit 2..6), 8 frames
    wh = []
    for i in range(8):
        if i in (0, 7):
            wh.append(S(seed=50 + i, flail=(-7.0, 1.0, -8.5, 6.5) if i == 7 else (-5.0, -2.0, -7.0, -4.0)))
            continue
        a = math.radians(-90 + (i - 1) * 60)
        hand = (-1.0, -2.0)
        ball = (math.cos(a) * 12.0, -2.0 + math.sin(a) * 6.0)
        wh.append(S(seed=50 + i, flail=(hand[0] - 2.5, hand[1], ball[0], ball[1]), bob=-0.5))
    wh_d = [0.1, 0.06, 0.06, 0.06, 0.06, 0.06, 0.06, 0.12]
    # CAST (special, the rite): all arms rise, the third eye opens, the hands push the orb out at release frame 5
    cs = []
    for i in range(9):
        up = [0.0, 0.4, 0.8, 1.0, 1.0, 1.0, 0.6, 0.3, 0.0][i]
        cs.append(S(seed=60 + i, cast=[0, 0.3, 0.6, 0.9, 1.0, 1.4, 0.6, 0.2, 0][i], bob=-up,
                    sword=(4.5, -6.5 - up * 3, -75 - up * 20), spear=(-5.5, -7.0 - up * 3, -95 + up * 10),
                    mace=(6.5, 2.5 - up * 6, -35 - up * 45), flail=(-7.0, 2.0 - up * 5, -9.5, 2.0 - up * 2),
                    hands=((7.0 + up * 3, 5.0), (5.0 + up * 3, 6.0)) if i >= 4 else None,
                    eye=2 if 2 <= i <= 6 else 1, lotus_open=up))
    cs_d = [0.1, 0.1, 0.1, 0.1, 0.1, 0.06, 0.1, 0.1, 0.1]
    d0 = S(lean=-2.0, bob=0.5, seed=80, eye=0)
    d1 = S(lean=1.0, bob=2.0, dy=1.0, seed=81, eye=0, sword=(6, 0, 30), spear=(-8, -2, -150), mace=(8, 4, 60))
    d2 = sixfold_corpse(0)
    d3 = sixfold_corpse(1)
    knock = S(lean=-2.5, seed=85, sword=(1.0, -9.0, -130), spear=(-8.0, -4.0, -130))
    portrait = sixfold(seed=0, crown_glint=(1, -1))[0]
    sheet("StmSixfold", [("Idle", idle, [0.2, 0.2, 0.2, 0.2]), ("Run", run, [0.09] * 6),
                         ("Cut", cut, cut_d), ("Slam", slam, slam_d), ("Thrust", th, th_d), ("Whirl", wh, wh_d),
                         ("Cast", cs, cs_d)] +
          tail(idle[0], [d0, d1, d2, d3], [0.12, 0.16, 0.18, 0.3], knock, portrait), outdir)
    _, k = sixfold(spear=(9.0, -1.0, 0), lean=2.5)
    _, c = sixfold(seed=65, cast=1.4, hands=((10.0, 5.0), (8.0, 6.0)))
    NOTES["StmSixfold"] = "shoulder %s, cast orb %s" % (tuple(round(v, 1) for v in k["shoulder"]), tuple(round(v, 1) for v in c["orb"]))


# ======================================================================================= GAMBIT (the marble chess knight)
def knight_head(f, piv, tilt, gape=0.0, eye=1, mane_sway=0.0, blink=False):
    """The horse-head bust on the collar at piv, tilted by `tilt` degrees (+ = nose down/forward). Marble with an onyx
    mane, lavender veins and a ruby eye. Returns world points of interest."""
    R = lambda x, y: rot_pt(piv[0] + x, piv[1] + y, tilt, piv[0], piv[1])
    # neck + head silhouette (local, facing right; y up negative)
    sil = [(-4.5, 0.0), (-5.0, -6.0), (-4.0, -12.0), (-1.5, -17.0), (1.0, -19.5), (3.0, -19.0), (6.0, -16.0),
           (9.5, -12.5), (11.0, -10.5), (10.5, -8.5), (8.0, -8.0), (5.0, -9.0), (3.0, -8.5), (2.5, -5.0), (4.0, 0.0)]
    poly(f.b, [R(*q) for q in sil], MARB, bias=0.25)
    # jaw line / lower lip (opens when it bites the floor)
    jaw = [(5.0, -9.0), (8.0, -8.0 + gape * 2.0), (10.0, -8.5 + gape * 1.5)]
    for a, b in zip(jaw, jaw[1:]): gl(f.b, *R(*a), *R(*b), "БА")
    if gape > 0.3:
        for q in ((7.0, -8.6), (8.0, -8.4)): f.b.put(*P(*R(*q)), "Ё")
    # nostril, cheek plane, brow
    f.b.put(*P(*R(10.0, -10.5)), "Ё")
    for q in ((3.0, -12.5), (4.0, -11.5), (5.0, -11.0)): f.b.put(*P(*R(*q)), "Б")
    gl(f.b, *R(1.0, -16.5), *R(5.0, -14.5), "ВГ")
    # ears
    for ex, base in ((0.0, 0), (1.8, 1)):
        e = [R(ex - 0.5, -19.0), R(ex + 0.5, -22.5 - base * 0.5), R(ex + 1.5, -19.0)]
        poly(f.b if base else f.u, e, MARB if base else "АБВ", bias=0.2)
    # onyx mane: a solid crest down the back of the neck, notched into carved locks
    mp = [(-0.5, -19.5), (-3.0, -16.0), (-5.0, -11.5), (-6.0, -6.0), (-5.8, -1.5)]
    tube(f.b, [R(*q) for q in mp], [1.3, 1.7, 1.8, 1.7, 1.4], "ЕЁЗЗ", bias=0.1)
    for i in range(1, 5):
        a, b = mp[i - 1], mp[i]
        q = R((a[0] + b[0]) / 2 - 1.6, (a[1] + b[1]) / 2 + math.sin(mane_sway + i) * 0.3)
        f.b.put(*P(*q), "Е")
        f.b.put(*P(*R(a[0] - 0.4, a[1])), "З")
    # eye
    ep = R(4.6, -14.0)
    if blink: f.b.put(*P(*ep), "Ё")
    elif eye:
        f.g.put(*P(*ep), "Й"); f.g.put(*P(ep[0] - 1, ep[1]), "И")
    else: f.b.put(*P(*ep), "И")
    # lavender veins through the marble
    for a, b in (((-3.0, -4.0), (-1.0, -9.0)), ((-1.0, -9.0), (0.5, -12.0)), ((6.0, -12.0), (8.5, -10.0))):
        for q in line_px(*P(*R(*a)), *P(*R(*b))):
            if q in f.b.px and f.b.px[q] in "ВГД": f.b.px[q] = "К"
    return {"nose": R(10.5, -9.5), "eye": ep, "seam": [R(-4.5, -5.0), R(-2.0, -7.5), R(0.0, -6.5), R(2.5, -8.5)]}


def knight_base(f, cx, cy, squash=0.0):
    """The turned chess base: foot disc, an onyx-and-marble checkered band, a collar ring."""
    w = 6.8 * (1 + squash * 0.18)
    h = 1.0 - squash * 0.3
    ell(f.b, cx, cy - 1.5, w, 1.8 * h + 0.2, MARB, bias=0.0)                                  # foot disc
    # checkered band
    for x in range(int(round(cx - w + 1)), int(round(cx + w))):
        for y in range(int(round(cy - 4.5 + squash)), int(round(cy - 2.5 + squash * 0.5)) + 1):
            sq = ((x - int(round(cx))) // 2 + (y // 2)) % 2
            lit = x < cx - w * 0.3
            f.b.put(x, y, ("Ё" if lit else "Е") if sq else ("Д" if lit else "В"))
    ell(f.b, cx, cy - 5.6 + squash, w * 0.78, 1.3, MARB, bias=0.2)                           # collar
    ell(f.b, cx, cy - 6.8 + squash, w * 0.6, 1.0, "БВГ", bias=0.1)


def gambit(dx=0.0, dy=0.0, lift=0.0, tilt=0.0, squash=0.0, gape=0.0, eye=1, mane=0.0, blink=False, seed=0, glint=None,
           crown=False):
    """The Gambit standing (or hopping `lift` px up), facing right."""
    f = Fr()
    cy = dy - lift
    knight_base(f, dx, cy, squash)
    piv = (dx - 0.5, cy - 6.5 + squash * 1.2)
    pts = knight_head(f, piv, tilt, gape=gape, eye=eye, mane_sway=mane, blink=blink)
    spr = f.done()
    c = Canvas(); c.px = dict(spr.px)
    seam(c, pts["seam"], k=seed, glint=glint)
    return Spr(c.px), pts


def gambit_corpse(stage):
    """Death: it topples and breaks at the neck: the head lies by the base."""
    f = Fr()
    knight_base(f, -3.0, 0.0, squash=0.6 if stage else 0.2)
    head = Fr()
    knight_head(head, (3.0, -1.0), 85, eye=0)
    for k, v in head.b.px.items(): f.b.put(k[0], k[1], v)
    for k, v in head.u.px.items(): f.u.put(k[0], k[1], v)
    s = f.done()
    c = Canvas(); c.px = dict(s.px)
    seam(c, [(-2, -3), (0, -5), (2, -3)])
    if stage == 0:
        for k in range(5): c.put(-1 + k * 2, -8 - (k % 2) * 2, "Г" if k % 2 else "В")
    return Spr(c.px)


def build_gambit(outdir):
    S = lambda **k: gambit(**k)[0]
    idle = []
    for i in range(4):
        idle.append(S(tilt=[0, -2, -3, -1][i], mane=i * 1.5, seed=i, blink=(i == 3), glint=3 if i == 1 else None))
    run = []
    # a hop: crouch, spring, up, over, down, land
    for i, (lift, sq, t) in enumerate(((0, 0.8, 6), (2, -0.3, -4), (5, -0.4, -8), (5, -0.2, -2), (2, 0.0, 6), (0, 0.9, 8))):
        run.append(S(lift=lift, squash=sq, tilt=t, mane=i * 1.2, seed=10 + i))
    # SLAM: rear back, then hammer the head down in front (hit 3)
    sl = []
    for i, (t, sq, lift, g) in enumerate(((-10, 0.2, 0, 0), (-24, -0.2, 1, 0.3), (-30, -0.3, 2, 0.6), (38, 0.8, 0, 1.0),
                                           (34, 0.9, 0, 0.6), (15, 0.4, 0, 0.2), (0, 0.0, 0, 0))):
        sl.append(S(tilt=t, squash=sq, lift=lift, gape=g, seed=20 + i))
    # crack lines under the slammed nose
    c = Canvas(); c.px = dict(sl[3].px)
    for k in range(4): c.put(10 + k * 2, -(k % 2), "Б" if k % 2 else "А")
    sl[3] = Spr(c.px)
    sl_d = [0.1, 0.12, 0.12, 0.05, 0.1, 0.1, 0.1]
    # KNIGHT'S TOUR: TourCrouch (3: the landing square is marked), TourAir (3: a tucked spin), TourLand (3)
    tc = [S(squash=0.4, tilt=4, seed=30), S(squash=0.9, tilt=8, seed=31, eye=1), S(squash=1.1, tilt=10, seed=32, glint=2)]
    ta = [S(lift=6, squash=-0.4, tilt=-14, seed=33), S(lift=9, squash=-0.3, tilt=-6, seed=34), S(lift=6, squash=-0.2, tilt=10, seed=35)]
    tl = [S(squash=1.2, tilt=14, seed=36, gape=0.4), S(squash=0.6, tilt=6, seed=37), S(squash=0.1, tilt=0, seed=38)]
    d0 = S(tilt=-20, squash=0.3, seed=40, gape=0.6)
    d1 = S(tilt=40, squash=0.6, seed=41, eye=0)
    d2 = gambit_corpse(0)
    d3 = gambit_corpse(1)
    knock = S(tilt=-22, lift=1, seed=45, gape=0.4)
    portrait = gambit(seed=0, glint=3)[0]
    sheet("StmGambit", [("Idle", idle, [0.24, 0.2, 0.24, 0.14]), ("Run", run, [0.07, 0.07, 0.08, 0.08, 0.07, 0.08]),
                        ("Slam", sl, sl_d), ("TourCrouch", tc, [0.14, 0.14, 0.12]), ("TourAir", ta, [0.1, 0.1, 0.1]),
                        ("TourLand", tl, [0.06, 0.1, 0.12])] +
          tail(idle[0], [d0, d1, d2, d3], [0.12, 0.14, 0.18, 0.3], knock, portrait), outdir)
    _, k = gambit(tilt=38, squash=0.8, gape=1.0)
    NOTES["StmGambit"] = "nose on the slam frame %s" % (tuple(round(v, 1) for v in k["nose"]),)


# ======================================================================================= CARYATID (columns)
def capital(lay, cx, cy, ang=0.0, glint=False):
    """An Ionic capital (the column top she carries): an abacus slab over an echinus with two spiral volutes."""
    R = lambda x, y: rot_pt(cx + x, cy + y, ang, cx, cy)
    slab = [R(-7.0, -2.5), R(7.0, -2.5), R(7.0, -0.8), R(-7.0, -0.8)]
    poly(lay, slab, PEACH, bias=0.3)
    ech = [R(-5.0, -0.8), R(5.0, -0.8), R(3.5, 1.8), R(-3.5, 1.8)]
    poly(lay, ech, "ЛМНО", bias=0.1)
    for sx in (-1, 1):
        vx, vy = R(sx * 5.6, 0.6)
        ell(lay, vx, vy, 1.9, 1.9, PEACH, bias=0.2)
        lay.put(*P(vx, vy), "Л")
        lay.put(*P(vx + sx * 0.8, vy - 0.8), "М")
    # egg-and-dart band in terracotta
    for k in range(-3, 4):
        lay.put(*P(*R(k * 1.3, 0.4)), "С" if k % 2 else "Т")
    if glint:
        star4(lay, *R(-5.5, -2.5), size=1, ch="П", core="й")


def caryatid(dx=0.0, dy=0.0, sway=0.0, lean=0.0, cap=None, cap_ang=0.0, hands=None, step=0.0, eyes=0, seed=0,
             glint=None, cap_glint=False, hair=0.0, free_arm=None, cracks=0, carry=True):
    """The Caryatid, facing right. cap = (x, y) of the capital's centre (default on her head); hands = near, far."""
    f = Fr()
    hip = (dx + sway * 0.4, -13.0 + dy)
    ch = (hip[0] + 0.6 + lean * 0.6, hip[1] - 7.0)
    hd = (ch[0] + 0.8 + lean * 0.4, ch[1] - 7.0)
    cap = cap or (hd[0] - 0.5, hd[1] - 6.5)
    nh, fh = hands or ((cap[0] + 6.0, cap[1] + 2.0), (cap[0] - 4.5, cap[1] + 2.5))
    # ---- far arm (under)
    fsh = (ch[0] - 2.4, ch[1] - 2.6)
    (ex, ey), _ = ik(fsh[0], fsh[1], fh[0], fh[1], 5.0, 5.0, bend=-1)
    tube(f.u, [fsh, (ex, ey), fh], [1.4, 1.1, 1.0], "ЛМНО", bias=0.05)
    # ---- drapery: a long chiton widening to the floor, its hem lifted by the stepping foot
    top = hip[1] - 1.0
    for y in range(int(top), 1):
        t = (y - top) / max(1.0, -top)
        half = 2.6 + t * 4.2
        cx = hip[0] + (1 - t) * 0.3 + t * (step * 0.8) + math.sin(y * 0.4 + sway) * 0.3
        for x in range(int(math.floor(cx - half)), int(math.ceil(cx + half)) + 1):
            u = (x - cx) / half
            fold = math.sin((x - cx) * 1.6 + y * 0.08 + sway * 0.5)
            l = -u * 0.55 + fold * 0.35 - 0.05
            ch_ = pick(PEACH, l)
            if fold < -0.75: ch_ = "М"
            if y == 0 or y == -1: ch_ = "С" if (x + seed) % 3 else "Т"              # terracotta hem border
            f.b.put(x, y, ch_)
    # stepping foot (sandal) peeks out under the hem
    if abs(step) > 0.2:
        fx = hip[0] + step * 4.0
        f.b.put(*P(fx + 3, 0), "Н"); f.b.put(*P(fx + 4, 0), "О"); f.b.put(*P(fx + 4, -1), "Р")
    # ---- bodice + sash
    ell(f.b, ch[0], ch[1] + 1.0, 4.0, 5.0, PEACH, bias=0.1)
    ell(f.b, ch[0] + 1.6, ch[1] - 0.2, 1.8, 1.8, PEACH, bias=0.3)            # bust
    for k in range(-4, 5): f.b.put(*P(hip[0] + k, hip[1] - 1.0 + abs(k) * 0.15), "С" if k % 2 else "Т")
    f.b.put(*P(hip[0] - 1, hip[1]), "Р"); f.b.put(*P(hip[0] - 1, hip[1] + 1), "С"); f.b.put(*P(hip[0] - 2, hip[1] + 2), "Р")   # sash tail
    # diagonal drape over the chest
    for q in line_px(*P(ch[0] - 2.5, ch[1] - 2.5), *P(ch[0] + 2.0, ch[1] + 3.0)):
        if q in f.b.px: f.b.px[q] = "М"
    # ---- head: braided crown of hair, profile face, closed gold-lidded eyes
    hx, hy = hd
    ell(f.b, hx - 2.4, hy - 0.6, 2.0, 2.6, "ЛМН", bias=0.0)                   # hair mass (back of the head)
    ell(f.b, hx - 3.6, hy + 1.6, 1.3, 1.5, "ЛМН", bias=0.1)                    # bun
    ell(f.b, hx + 0.4, hy + 0.2, 2.6, 3.2, "МНОПП", bias=0.35)                # face
    for k in range(4): f.b.put(*P(hx - 2.6 + k * 1.2, hy - 2.9 + (k % 2) * 0.4), "Н")   # braid band
    f.b.put(*P(hx + 2.7, hy + 0.5), "О")                                      # nose
    f.b.put(*P(hx + 1.4, hy - 0.2), "ь" if not eyes else "э")                 # closed eye: a gold line
    f.b.put(*P(hx + 2.0, hy - 0.2), "ы" if not eyes else "й")
    f.b.put(*P(hx + 1.8, hy + 1.8), "С")                                      # lips
    # neck
    ell(f.b, hx - 0.6, hy + 3.6, 1.2, 1.4, PEACH, bias=0.1)
    # ---- the capital she carries (behind the near arm, over her head)
    if carry:
        capital(f.b, cap[0], cap[1], cap_ang, glint=cap_glint)
    # ---- near arm (over)
    nsh = (ch[0] + 2.0, ch[1] - 2.8)
    part = Canvas()
    target = free_arm if free_arm is not None else nh
    if free_arm is None and target[1] < nsh[1] - 4:
        # carrying: the elbow juts forward, clear of her face
        ex, ey = max(hd[0] + 6.5, target[0] + 1.0), hd[1] + 2.0
    else:
        (ex, ey), _ = ik(nsh[0], nsh[1], target[0], target[1], 5.0, 5.0, bend=1)
    tube(part, [nsh, (ex, ey), target], [1.5, 1.2, 1.1], "ЛМНО", bias=0.0)
    part.put(*P((ex + target[0]) / 2, (ey + target[1]) / 2), "ь")              # gold armlet
    inked(f.b, part, "Л")
    spr = f.done()
    c = Canvas(); c.px = dict(spr.px)
    seam(c, [(ch[0] - 2.5, ch[1] + 4.5), (ch[0] - 0.5, ch[1] + 6.5), (ch[0] + 0.5, ch[1] + 9.0), (ch[0] + 2.5, ch[1] + 10.5)],
         k=seed, glint=glint)
    rnd = random.Random(91)
    for i in range(cracks):
        x0, y0 = ch[0] - 3 + rnd.uniform(0, 6), ch[1] - 2 + rnd.uniform(0, 14)
        pts = [(x0, y0)]
        for k in range(3): pts.append((pts[-1][0] + rnd.uniform(-1.6, 1.6), pts[-1][1] + rnd.uniform(0.6, 2)))
        for a, b in zip(pts, pts[1:]):
            for q in line_px(*P(*a), *P(*b)):
                if q in c.px and c.px[q] != OUT: c.px[q] = "Л"
    return Spr(c.px), {"head": hd, "cap": cap, "chest": ch}


def caryatid_corpse(stage):
    c = Canvas()
    rubble(c, -2, 0, 20 - stage * 2, PEACH, 120 + stage)
    f = Fr(); f.b = c
    capital(f.b, 7.0, -3.0, 20)
    s = f.done()
    c2 = Canvas(); c2.px = dict(s.px)
    seam(c2, [(-7, -2), (-3, -4), (0, -2)])
    for k in range(4): c2.put(-10 + k * 3, 0, "С" if k % 2 else "Т")
    if stage == 0:
        for k in range(4): c2.put(-4 + k * 3, -7 - k % 2 * 2, "О" if k % 2 else "Н")
    return Spr(c2.px)


def build_caryatid(outdir):
    S = lambda **k: caryatid(**k)[0]
    idle = []
    for i in range(4):
        sw = [0.0, 0.8, 1.2, 0.6][i]
        idle.append(S(sway=sw, dy=[0, 0, -0.4, 0][i], seed=i, cap_glint=(i == 2)))
    run = []
    for i in range(6):
        ph = i / 6 * 2 * math.pi
        run.append(S(sway=math.sin(ph) * 1.2, step=math.cos(ph), dy=-abs(math.sin(ph)) * 0.6, lean=1.0, seed=10 + i))
    # SMASH: heave the capital high, bring it down in front (hit 4); recover
    sm = []
    keys = [dict(), dict(cap=(1.0, -40.0), dy=-0.5), dict(cap=(0.0, -43.0), dy=-1.0, lean=-1.0),
            dict(cap=(7.0, -34.0), lean=1.0, cap_ang=15),
            dict(cap=(14.0, -4.0), lean=3.5, cap_ang=8, dy=1.0), dict(cap=(14.0, -3.5), lean=3.5, cap_ang=4, dy=1.0),
            dict(cap=(9.0, -22.0), lean=1.5, cap_ang=10), dict()]
    for i, k in enumerate(keys):
        if "cap" in k:
            cx, cy = k["cap"]
            k["hands"] = ((cx + 5.0, cy + 2.0), (cx - 4.0, cy + 2.5)) if cy < -20 else ((cx - 2.0, cy - 3.0), (cx - 5.0, cy - 3.0))
        sm.append(S(seed=20 + i, **k))
    sm_d = [0.1, 0.12, 0.14, 0.06, 0.05, 0.1, 0.12, 0.1]
    # RAISE: balance the capital on one hand, sweep the other arm up from the floor (release 4) - the column rises
    rs = []
    for i in range(8):
        up = [0.0, -0.3, -0.6, 0.2, 1.0, 1.0, 0.6, 0.0][i]
        hd_cap = (-1.0, -36.0)
        rs.append(S(seed=30 + i, step=0.6 if 2 <= i <= 4 else 0.0, eyes=1 if 3 <= i <= 5 else 0,
                    hands=((hd_cap[0] + 5.0, hd_cap[1] + 2.0), (hd_cap[0] - 4.5, hd_cap[1] + 2.5)),
                    free_arm=(8.0 + up * 2.0, -8.0 - up * 20.0) if i > 0 else None, cap=hd_cap, lean=up * 0.8))
    rs_d = [0.1, 0.1, 0.12, 0.08, 0.06, 0.12, 0.12, 0.1]
    d0 = S(lean=-1.5, cracks=3, seed=40, cap=(-3.0, -35.0), cap_ang=-20)
    d1 = S(lean=1.0, dy=2.0, cracks=6, seed=41, carry=False, hands=((6.0, -14.0), (-5.0, -16.0)))
    d2 = caryatid_corpse(0)
    d3 = caryatid_corpse(1)
    knock = S(lean=-2.0, seed=45, cap=(-3.0, -36.0), cap_ang=-25)
    portrait = caryatid(seed=0, cap_glint=True)[0]
    sheet("StmCaryatid", [("Idle", idle, [0.24, 0.2, 0.24, 0.2]), ("Run", run, [0.1] * 6),
                          ("Smash", sm, sm_d), ("Raise", rs, rs_d)] +
          tail(idle[0], [d0, d1, d2, d3], [0.12, 0.16, 0.18, 0.3], knock, portrait), outdir)


# ======================================================================================= LACHRYMOSA (legendary)
def angel_wing(lay, root, wrist, tip_ang, n, L, ramp, far=False, seed=0, droop=0.0):
    """A feathered stone wing: an arm bone from the root to the wrist, then `n` long feathers fanning from the arm
    and wrist (tapered, overlapping, each with a lit leading edge), starting at angle tip_ang (deg) and turning down."""
    rx, ry = root; wx, wy = wrist
    rnd = random.Random(seed)
    # feathers first (back to front: the longest primaries at the wrist first)
    for i in reversed(range(n)):
        t = i / max(1, n - 1)
        bx, by = wx + (rx - wx) * t * 0.85, wy + (ry - wy) * t * 0.85
        a = math.radians(tip_ang + t * (60 + droop))
        ln_ = L * (1 - t * 0.45) + rnd.uniform(-0.8, 0.8)
        ex, ey = bx + math.cos(a) * ln_, by + math.sin(a) * ln_
        tube(lay, [(bx, by), ((bx + ex) / 2, (by + ey) / 2), (ex, ey)], [1.5, 1.3, 0.5], ramp, bias=0.15 - (0.25 if far else 0))
        # a dark trailing edge (the gap to the next feather) and a lit quill
        px_, py_ = -math.sin(a), math.cos(a)
        side = 1.0 if px_ * (rx - wx) + py_ * (ry - wy) > 0 else -1.0
        for k, q in enumerate(line_px(*P(bx + px_ * side * 1.4, by + py_ * side * 1.4), *P(ex + px_ * side * 0.6, ey + py_ * side * 0.6))):
            if k > 0: lay.put(q[0], q[1], ramp[0])
        for k, q in enumerate(line_px(*P(bx, by), *P(ex, ey))):
            if 1 < k < ln_ * 0.7: lay.put(q[0], q[1], ramp[-1] if not far else ramp[-2])
    # coverts along the arm
    for i in range(5):
        t = i / 4
        cx, cy = wx + (rx - wx) * t, wy + (ry - wy) * t
        ell(lay, cx + 0.3, cy + 1.0, 1.5, 1.1, ramp, bias=0.3 - (0.2 if far else 0))
    tube(lay, [root, wrist], [1.6, 1.1], ramp, bias=0.3 - (0.2 if far else 0))


def lachrymosa(dx=0.0, dy=0.0, lift=0.0, lean=0.0, wings=0.0, weep=1.0, hands=None, face=0, halo=1.0, halo_glint=None, halo_lit=1.0,
               tear=-1, robe=0.0, seed=0, glint=None, cracks=0, crumble=0.0, eyes_glow=1):
    """Lachrymosa, facing right. wings 0 folded high .. 1 half .. 2 spread wide; weep 1 = hand over her eyes;
    face 1 = her face bared (hollow glowing eyes); tear = frame of the falling tear (-1 none)."""
    f = Fr()
    base_y = dy - lift
    hip = (dx + lean * 0.3, base_y - 15.0)
    ch = (hip[0] + 0.8 + lean * 0.8, hip[1] - 8.0)
    hd = (ch[0] + 1.6 + lean * 0.5, ch[1] - 7.0)
    hx, hy = hd
    # ---- halo (behind everything): a gilded ring, cracked through with a mended seam
    if halo > 0:
        hc = (hx - 1.5, hy - 1.5)
        for k in range(28):
            a = k / 28 * 2 * math.pi
            if 0.3 < a < 0.62: continue                         # the crack gap
            x, y = hc[0] + math.cos(a) * 6.2 * halo, hc[1] + math.sin(a) * 6.2 * halo
            l = -(math.cos(a) + math.sin(a)) / 1.414
            ramp = "ыьэ" if halo_lit > 0.7 else ("Хыь" if halo_lit > 0.3 else "ФХы")     # the halo's light snuffed out
            f.n.put(*P(x, y), pick(ramp, l))
            if k % 3 == 0: f.n.put(*P(hc[0] + math.cos(a) * 5.2 * halo, hc[1] + math.sin(a) * 5.2 * halo), "ы" if halo_lit > 0.3 else "Ф")
        if halo_glint is not None:
            a = halo_glint
            star4(f.g, hc[0] + math.cos(a) * 6.2, hc[1] + math.sin(a) * 6.2, size=1, ch="э", core="й")
    # ---- wings: far wing then (later) near wing
    sh = (ch[0] - 1.5, ch[1] - 3.0)
    if wings < 0.5:
        wr_f, ta, L = (sh[0] - 6.0, sh[1] - 9.5), 95, 18
    elif wings < 1.5:
        wr_f, ta, L = (sh[0] - 11.0, sh[1] - 9.0), 70, 18
    else:
        wr_f, ta, L = (sh[0] - 15.0, sh[1] - 4.0), 40, 15
    angel_wing(f.u, (sh[0] + 1.0, sh[1] - 1.0), (wr_f[0] + 4.0, wr_f[1] + 1.0), ta - 8, 6, L - 2, "ФХЦЧ", far=True, seed=seed + 7)
    # ---- robe: falls from the chest to a wide hem; lifted (hovering) she trails wisps instead of feet
    top = ch[1] + 2.0
    bottom = base_y
    for y in range(int(top), int(bottom) + 1):
        t = (y - top) / max(1.0, bottom - top)
        half = 3.4 + t * 5.0
        cx = hip[0] + t * (robe * 2.0 - lean * 0.6) + math.sin(y * 0.35 + robe * 2) * 0.4
        for x in range(int(math.floor(cx - half)), int(math.ceil(cx + half)) + 1):
            u = (x - cx) / half
            fold = math.sin((x - cx) * 1.3 + y * 0.12 + robe * 1.5)
            l = -u * 0.6 + fold * 0.35
            c_ = pick(ANGEL, l)
            if fold < -0.8: c_ = "Ф"
            if crumble > 0 and ((x * 7 + y * 13) % 11) / 11.0 < crumble * (0.4 + t * 0.8): continue
            f.b.put(x, y, c_)
    # ---- chest, far arm
    ell(f.b, ch[0], ch[1] + 1.5, 3.8, 4.6, ANGEL, bias=0.1)
    nh, fh = hands or ((hx + 2.5, hy + 0.5), (ch[0] - 3.0, ch[1] + 7.0))
    fsh = (ch[0] - 2.2, ch[1] - 1.8)
    (ex, ey), _ = ik(fsh[0], fsh[1], fh[0], fh[1], 5.0, 5.0, bend=-1)
    tube(f.u, [fsh, (ex, ey), fh], [1.3, 1.0, 1.0], "ФХЦЧ", bias=0.0)
    # ---- head: veiled hair, profile; the hand over her eyes when she weeps, hollow glowing eyes when she doesn't
    ell(f.b, hx - 1.8, hy - 0.2, 2.6, 3.2, "ФХЦЧ", bias=-0.05)               # hair falling back
    tube(f.b, [(hx - 2.5, hy + 1.0), (hx - 3.5, hy + 5.0), (hx - 3.0, hy + 8.0)], [1.6, 1.4, 0.8], "ФХЦ")
    ell(f.b, hx + 0.4, hy + 0.2, 2.6, 3.2, "ЦЧШШ", bias=0.3)                  # face
    f.b.put(*P(hx + 2.9, hy + 0.6), "Ч")                                      # nose
    f.b.put(*P(hx + 1.8, hy + 2.2), "Х")                                      # mouth
    if face:
        f.g.put(*P(hx + 1.4, hy - 0.4), "Ы" if eyes_glow else "Ь"); f.g.put(*P(hx + 2.0, hy - 0.4), "Ъ" if eyes_glow else "Ь")
        f.b.put(*P(hx + 1.4, hy + 0.4), "Ь"); f.b.put(*P(hx + 2.0, hy + 0.4), "Ь")
    else:
        f.b.put(*P(hx + 1.6, hy - 0.4), "Х")
    # tears: two glowing streaks down the cheek and a drop that falls (tear = its frame)
    f.g.put(*P(hx + 1.8, hy + 1.0), "Ъ"); f.g.put(*P(hx + 1.6, hy + 2.6), "Щ")
    if tear >= 0:
        ty = hy + 4.0 + tear * 3.5
        if ty < base_y - 1:
            f.g.put(*P(hx + 2.0, ty), "Ы"); f.g.put(*P(hx + 2.0, ty - 1), "Ъ")
        else:
            f.g.put(*P(hx + 1.0, base_y - 1), "Ъ"); f.g.put(*P(hx + 3.0, base_y - 1), "Ъ")
    # ---- near wing (over the back), then the near arm
    if wings < 0.5:
        wr, ta2, L2 = (sh[0] - 4.0, sh[1] - 10.5), 100, 18
    elif wings < 1.5:
        wr, ta2, L2 = (sh[0] - 9.0, sh[1] - 12.0), 75, 20
    else:
        wr, ta2, L2 = (sh[0] - 14.0, sh[1] - 8.0), 45, 17
    part = Canvas()
    angel_wing(part, sh, wr, ta2, 7, L2, ANGEL, seed=seed, droop=8 if wings < 0.5 else 0)
    inked(f.b, part, "Ф")
    nsh = (ch[0] + 1.8, ch[1] - 2.0)
    part = Canvas()
    (ex, ey), _ = ik(nsh[0], nsh[1], nh[0], nh[1], 5.2, 5.0, bend=1)
    tube(part, [nsh, (ex, ey), nh], [1.5, 1.2, 1.2], "ХЦЧШ", bias=0.1)
    ell(part, nh[0], nh[1], 1.6, 1.4, "ХЦЧШ", bias=0.2)                       # the hand (over her eyes when weeping)
    if weep and not face:
        part.put(*P(nh[0] + 1.6, nh[1] - 0.5), "Ч"); part.put(*P(nh[0] + 1.6, nh[1] + 0.5), "Ч")   # fingers
    inked(f.b, part, "Ф")
    spr = f.done()
    c = Canvas(); c.px = dict(spr.px)
    # gold seam: mended crack from the collarbone down the robe
    seam(c, [(ch[0] + 2.0, ch[1] - 1.0), (ch[0] + 0.5, ch[1] + 1.5), (ch[0] + 1.5, ch[1] + 4.0), (ch[0] + 0.5, ch[1] + 6.0)],
         k=seed, glint=glint)
    rnd = random.Random(131)
    for i in range(cracks):
        x0, y0 = ch[0] - 3 + rnd.uniform(0, 6), ch[1] - 3 + rnd.uniform(0, 18)
        pts = [(x0, y0)]
        for k in range(4): pts.append((pts[-1][0] + rnd.uniform(-1.8, 1.8), pts[-1][1] + rnd.uniform(0.5, 2.2)))
        for a, b in zip(pts, pts[1:]):
            for q in line_px(*P(*a), *P(*b)):
                if q in c.px and c.px[q] != OUT: c.px[q] = "Ъ" if i % 3 == 0 else "Ф"
    return Spr(c.px), {"head": hd, "chest": ch, "hand": nh}


def lach_corpse(stage):
    c = Canvas()
    rubble(c, -1, 0, 24 - stage * 2, ANGEL, 140 + stage)
    f = Fr(); f.b = c
    # a broken wing lies across the heap, the halo fallen flat in two pieces
    angel_wing(f.b, (-12.0, -2.0), (-3.0, -4.0), -10, 5, 9, ANGEL, seed=3)
    s = f.done()
    c2 = Canvas(); c2.px = dict(s.px)
    for k in range(18):
        a = k / 18 * 2 * math.pi
        if 0.3 < a < 0.7 or 3.4 < a < 3.8: continue
        c2.put(*P(8 + math.cos(a) * 5, -1.6 + math.sin(a) * 1.4), pick("ыьэ", -math.cos(a)))
    seam(c2, [(-5, -3), (-2, -5), (2, -3)])
    if stage == 0:
        for k in range(4): c2.put(-3 + k * 2, -8 - k * 2, "Ъ" if k % 2 else "Щ")
    else:
        c2.put(0, -2, "Щ")
    return Spr(c2.px)


def build_lachrymosa(outdir):
    S = lambda **k: lachrymosa(**k)[0]
    # Idle 6 (showpiece): she weeps, a tear falls, her halo turns a glint round, the wings breathe
    idle = []
    for i in range(6):
        idle.append(S(dy=[0, -0.3, -0.6, -0.8, -0.6, -0.3][i], tear=i if i < 5 else -1, halo_glint=i * 1.05, seed=i,
                      robe=i * 0.5, glint=2 if i == 3 else None))
    run = []
    for i in range(6):
        ph = i / 6 * 2 * math.pi
        run.append(S(lift=1.5 + math.sin(ph) * 1.0, lean=2.0, wings=1.0, robe=ph, seed=10 + i, weep=0, face=1,
                     hands=None if False else ((lambda h: (h[0] + 2.5, h[1] + 0.5))(lachrymosa(lean=2.0)[1]["head"]),
                                               (-4.0, -12.0 + math.sin(ph))), halo_glint=ph))
    # LAMENT: she bares her face, flares her wings and rakes with both hands (hit 4)
    la = []
    keys = [dict(face=1, weep=0, wings=0.6), dict(face=1, weep=0, wings=1.0, lean=-1.0, hands=((6.0, -36.0), (-3.0, -33.0))),
            dict(face=1, weep=0, wings=1.6, lean=-1.5, hands=((5.0, -38.0), (-2.0, -36.0))),
            dict(face=1, weep=0, wings=2.0, lean=-1.5, hands=((4.0, -39.0), (-1.0, -37.0))),
            dict(face=1, weep=0, wings=2.0, lean=3.0, hands=((14.0, -18.0), (11.0, -14.0))),
            dict(face=1, weep=0, wings=1.6, lean=3.0, hands=((13.0, -12.0), (10.0, -9.0))),
            dict(face=1, weep=0, wings=1.0, lean=1.5, hands=((9.0, -16.0), (5.0, -14.0))), dict(wings=0.4)]
    for i, k in enumerate(keys): la.append(S(seed=20 + i, halo_glint=i * 0.7, **k))
    # claw streaks on the hit frame
    c = Canvas(); c.px = dict(la[4].px)
    for k in range(3):
        gl(c, 12 + k, -26 + k * 3, 20 + k, -12 + k * 3, "ШЧЦ")
    la[4] = Spr(c.px)
    la_d = [0.1, 0.1, 0.1, 0.1, 0.05, 0.08, 0.1, 0.12]
    # SNUFF (special, 7): she reaches up and pinches out the light of her own halo (release 4: the lights go out)
    sn = []
    hd0 = lachrymosa()[1]["head"]
    keys = [dict(), dict(face=1, weep=0, hands=((hd0[0] + 1.0, hd0[1] - 5.0), None), wings=0.3),
            dict(face=1, weep=0, hands=((hd0[0] - 1.0, hd0[1] - 8.0), None), wings=0.6, halo_lit=1.0),
            dict(face=1, weep=0, hands=((hd0[0] - 1.5, hd0[1] - 7.5), None), wings=1.0, halo_lit=0.5),
            dict(face=1, weep=0, hands=((hd0[0] - 1.5, hd0[1] - 7.0), None), wings=1.6, halo_lit=0.1),
            dict(face=1, weep=0, hands=((hd0[0] + 2.0, hd0[1] - 2.0), None), wings=1.0, halo_lit=0.1),
            dict(wings=0.4, halo_lit=0.4)]
    for i, k in enumerate(keys):
        if k.get("hands") and k["hands"][1] is None:
            k["hands"] = (k["hands"][0], (lachrymosa()[1]["chest"][0] - 3.0, lachrymosa()[1]["chest"][1] + 7.0))
        sn.append(S(seed=30 + i, halo_glint=None, **k))
    # the last of the halo light pinched between her fingers on the release frame
    c = Canvas(); c.px = dict(sn[4].px)
    star4(c, hd0[0] - 1.5, hd0[1] - 8.5, size=1, ch="э", core="й")
    sn[4] = Spr(c.px)
    sn_d = [0.1, 0.1, 0.12, 0.1, 0.06, 0.12, 0.12]
    # DEATH 6: her halo falls, she cracks with light, the wings break, she crumbles
    d = [S(face=1, weep=0, cracks=3, wings=1.0, lean=-1.0, seed=60),
         S(face=1, weep=0, cracks=6, wings=0.6, halo=0.0, seed=61, dy=1.0),
         S(face=1, weep=0, cracks=9, wings=0.0, halo=0.0, crumble=0.4, seed=62, dy=2.0, eyes_glow=0),
         S(face=1, weep=0, cracks=10, wings=0.0, halo=0.0, crumble=0.8, seed=63, dy=3.0, eyes_glow=0),
         lach_corpse(0), lach_corpse(1)]
    knock = S(face=1, weep=0, wings=1.4, lean=-2.5, seed=65, hands=((5.0, -34.0), (-4.0, -30.0)))
    portrait = lachrymosa(seed=0, halo_glint=4.0, glint=2)[0]
    sheet("StmLachrymosa", [("Idle", idle, [0.22, 0.18, 0.18, 0.2, 0.18, 0.22]), ("Run", run, [0.1] * 6),
                            ("Lament", la, la_d), ("Snuff", sn, sn_d)] +
          tail(idle[0], d, [0.1, 0.12, 0.12, 0.14, 0.16, 0.3], knock, portrait), outdir)


# ======================================================================================= FX
def chips(c, cx, cy, n, r0, r1, seed, ramp, ratio=0.8):
    rnd = random.Random(seed)
    for i in range(n):
        a = rnd.uniform(0, 2 * math.pi); r = rnd.uniform(r0, r1)
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * ratio
        c.put(*P(x, y), ramp[i % len(ramp)])
        if i % 3 == 0: c.put(*P(x + 1, y), ramp[(i + 1) % len(ramp)])


def fx_splat(outdir):
    def splat(seed):
        fr = []
        for i in range(4):
            c = Canvas(); rnd = random.Random(seed)
            for k in range(8):
                a = rnd.uniform(-2.8, -0.3); sp = rnd.uniform(2, 5)
                x, y = math.cos(a) * sp * (i + 1) * 0.8, math.sin(a) * sp * (i + 1) * 0.6 + i * i * 0.6
                c.put(*P(x, y), "е" if i == 0 else ("д" if i < 2 else ("г" if i < 3 else "в")))
                if i < 2 and k % 2: c.put(*P(x + 1, y), "г")
            if i == 0: star4(c, 0, -1, size=1, ch="э", core="й")
            fr.append(S_(c))
        return fr
    fx_sheet("FxStmSplat", [("Play", splat(4), [0.05, 0.06, 0.07, 0.08]), ("Play2", splat(11), [0.05, 0.06, 0.07, 0.08])], outdir)


def fx_impact(outdir):
    wall, hit = [], []
    for i in range(5):
        c = Canvas(); r = 1 + i * 1.6
        if i < 4:
            for k in range(8):
                a = k / 8 * 2 * math.pi + 0.3
                L = r + (1.5 if k % 2 == 0 else 0)
                gl(c, math.cos(a) * r * 0.4, math.sin(a) * r * 0.4, math.cos(a) * L, math.sin(a) * L, "едг" if i < 2 else "гвб")
        if i <= 1: star4(c, 0, 0, size=2 - i, ch="э", core="й")
        chips(c, 0, 0, 4 + i, r, r + 2, 3 + i, "дгвь")
        hit.append(S_(c))
        c = Canvas()
        for k in range(6):
            a = math.radians(-80 + k * 32)
            if i < 4: gl(c, 0, 0, math.cos(a) * (r + k % 2), math.sin(a) * (r + k % 2), "едг" if i < 2 else "гвб")
        chips(c, 2, 0, 3 + i, r * 0.6, r + 1.5, 9 + i, "дгв")
        wall.append(S_(c))
    fx_sheet("FxStmImpact", [("Wall", wall, [0.04, 0.05, 0.05, 0.06, 0.07]), ("Hit", hit, [0.04, 0.05, 0.05, 0.06, 0.07])], outdir)


def fx_death(outdir):
    """Any secret statue's death: a gout of stone dust, chips, and the gold seam's light escaping upward."""
    fr = []
    for i in range(7):
        c = Canvas()
        r = 3 + i * 2.2
        for k in range(int(20 + i * 4)):
            a = k * 2.39 + i * 0.3
            rr = r * (0.4 + (k % 5) / 5)
            x, y = math.cos(a) * rr * 1.2, -4 - abs(math.sin(a)) * rr * 0.9 - i
            if (k + i) % 2 == 0 or i < 3: c.put(*P(x, y), "е" if i < 2 else ("д" if i < 4 else ("г" if i < 6 else "в")))
        ring(c, 0, 0, 3 + i * 2.0, 0.42, "вгде" if i < 4 else "бв", gap=(lambda a: int(a * 5) % 2 == 0) if i > 3 else None)
        if i < 5:
            for k in range(3): c.put(-2 + k * 2, -8 - i * 4 - k * 2, "э" if k == 1 else "ь")
        if i == 1: star4(c, 0, -10, size=2, ch="э", core="й")
        fr.append(S_(c))
    fx_sheet("FxStmDeath", [("Play", fr, [0.05, 0.06, 0.07, 0.08, 0.08, 0.1, 0.12])], outdir)


def fx_awaken(outdir):
    """A secret statue taken: its gold seam blazes, the stone skin bursts in a ring of chips and dust (9 frames)."""
    fr = []
    for i in range(9):
        c = Canvas()
        if i < 4:
            # the seam light climbing the figure
            for k in range(6 + i * 3):
                y = -2 - k * 1.3
                c.put(*P(math.sin(k * 1.3) * 1.5, y), "й" if k % 3 == 0 else ("э" if i > 1 else "ь"))
        if i >= 2:
            t = i - 2
            ring(c, 0, 0, 4 + t * 3.2, 0.42, "вгдеэ"[max(0, 4 - t):] or "в", thick=2 if t < 3 else 1)
            chips(c, 0, -12, 6 + t * 3, 4 + t * 2, 8 + t * 3, 200 + i, "дгвь")
        if 3 <= i <= 5:
            star4(c, 0, -14 - (i - 3) * 2, size=4 - (i - 3), ch="э", core="й")
        fr.append(S_(c))
    fx_sheet("FxStmAwaken", [("Play", fr, [0.06, 0.06, 0.06, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1])], outdir)


# ---- Grotesque
def fx_rake(outdir):
    fr = []
    for i in range(4):
        c = Canvas()
        for k in range(3):
            off = (k - 1) * 3
            a0 = 130 - i * 28
            for a in range(a0, a0 - 80, -5):
                r = 9 + k
                ch = "е" if a > a0 - 25 else ("д" if a > a0 - 50 else "г")
                if i == 3 and (a // 5) % 2: continue
                c.put(*P(math.cos(math.radians(a)) * r + off * 0.4, -math.sin(math.radians(a)) * r * 0.85 + off), ch, over=False)
        if i < 2: c.put(6, -6 + i, "р"); c.put(7, -6 + i, "п")
        fr.append(S_(c))
    fx_sheet("FxStmRake", [("Slash", fr, [0.04, 0.05, 0.06, 0.07])], outdir)


def fx_dust(outdir):
    """Set in Stone: the grit it sheds as it petrifies, a ring that grinds the hero's feet (slows)."""
    fr = []
    for i in range(6):
        c = Canvas()
        r = 6 + i * 3.4
        ring(c, 0, 0, r, 0.42, "вгд" if i < 4 else "бв", thick=2 if i < 3 else 1, gap=(lambda a: int(a * 4) % 3 == 0) if i > 2 else None)
        chips(c, 0, -1, 10 + i * 2, r * 0.5, r, 210 + i, "гдвб", ratio=0.42)
        for k in range(4):
            a = k / 4 * 2 * math.pi + i
            c.put(*P(math.cos(a) * r * 0.7, math.sin(a) * r * 0.3 - 2 - i), "д")
        fr.append(S_(c))
    fx_sheet("FxStmDust", [("Play", fr, [0.05, 0.06, 0.07, 0.08, 0.09, 0.1])], outdir)


def fx_shard(outdir):
    fr = []
    for i in range(4):
        c = Canvas()
        pts = [(4, 0), (0, -1.6), (-4, -0.4 + (i % 2) * 0.4), (-1, 1.4)]
        poly(c, pts, "вгде", bias=0.2)
        c.put(4, 0, "е"); c.put(-1, 1, "б")
        if i % 2: c.put(0, 0, "э")
        for k in range(1, 4): c.put(-4 - k * 2, (k + i) % 2, "г" if k < 2 else "в")
        f = Fr(); f.b = c
        fr.append(f.done(clip=False))
    fx_sheet("FxStmShard", [("Fly", fr, [0.05] * 4)], outdir)


def fx_shell(outdir):
    """The stone shell bursting off the Grotesque (6 frames), centred on its body (origin = its feet)."""
    fr = []
    for i in range(6):
        c = Canvas()
        for k in range(10):
            a = k / 10 * 2 * math.pi + 0.2
            r = 4 + i * 3.0
            x, y = math.cos(a) * r, -10 + math.sin(a) * r * 0.85 + i * i * 0.25
            if i < 5:
                ell(c, x, y, 1.4 - i * 0.15, 1.1, "вгде", bias=0.2)
        if i < 2: star4(c, 0, -10, size=3 - i, ch="е", core="й")
        chips(c, 0, -10, 8, 2 + i * 2, 6 + i * 3, 230 + i, "дгвь")
        f = Fr(); f.b = c
        fr.append(f.done(clip=False))
    fx_sheet("FxStmShell", [("Play", fr, [0.04, 0.05, 0.06, 0.07, 0.08, 0.1])], outdir)


def fx_chip(outdir):
    fr = []
    for i in range(4):
        c = Canvas()
        chips(c, 0, 0, 5 + i, 1 + i, 3 + i * 1.5, 240 + i, "едгв")
        if i == 0: star4(c, 0, 0, size=1, ch="д", core="е")
        fr.append(S_(c))
    fx_sheet("FxStmChip", [("Play", fr, [0.04, 0.05, 0.06, 0.07])], outdir)


def fx_crack(outdir):
    """Indicator over the petrified Grotesque: one stone pip per stored hit (1..6), cracked and glowing ember."""
    anims = []
    for n in range(1, 7):
        fr = []
        for i in range(2):
            c = Canvas()
            for k in range(n):
                x = -(n - 1) * 2.5 + k * 5
                f = Fr(); ell(f.b, x, -2, 1.8, 1.8, "вгде", bias=0.2)
                f.b.put(*P(x - 0.5, -2), "о" if i == 0 else "п")
                f.b.put(*P(x + 0.5, -3), "а")
                for q, v in f.done(clip=False).px.items(): c.put(q[0], q[1], v)
            fr.append(S_(c))
        anims.append((str(n), fr, [0.2, 0.2]))
    fx_sheet("FxStmCrack", anims, outdir)


def fx_keystone(outdir):
    """Indicator under the Grotesque while it can still reform: an ember keystone rune glowing in a faint ring."""
    fr = []
    for i in range(4):
        c = Canvas()
        ring(c, 0, 0, 10, 0.4, "аоп" if i % 2 else "ао", gap=lambda a, i=i: (int(a * 6 + i) % 3) == 0)
        for k in range(3):
            a = (k / 3 + i / 12) * 2 * math.pi
            x, y = math.cos(a) * 10, math.sin(a) * 4
            c.put(*P(x, y), "р" if (k + i) % 2 else "п")
        fr.append(S_(c))
    fx_sheet("FxStmKeystone", [("Loop", fr, [0.18] * 4)], outdir)


# ---- Sixfold
def fx_idol_cut(outdir):
    fr = []
    for i in range(5):
        c = Canvas()
        a0, a1 = [(-130, -80), (-120, -20), (-100, 30), (-60, 55), (-10, 60)][i]
        for a in range(a0, a1 + 1, 2):
            t = (a - a0) / max(1, a1 - a0)
            for rr, ch in ((15.0, "ф"), (14.0, "х"), (13.0, "э" if t > 0.6 else "х"), (12.0, "ь")):
                if i >= 3 and rr < 13: continue
                if i == 4 and (a // 2) % 2: continue
                c.put(*P(math.cos(math.radians(a)) * rr - 4, math.sin(math.radians(a)) * rr * 0.8), ch, over=False)
        if i in (2, 3): sparks(c, 6, 2, 5, 2, 6, 300 + i, chars="йэщ")
        fr.append(S_(c))
    fx_sheet("FxStmIdolCut", [("Sweep", fr, [0.04, 0.04, 0.05, 0.06, 0.07])], outdir)


def fx_idol_slam(outdir):
    fr = []
    for i in range(6):
        c = Canvas()
        r = 3 + i * 2.6
        ring(c, 0, 0, r, 0.42, "уфх" if i < 3 else "ту", thick=2 if i < 2 else 1, gap=(lambda a: int(a * 5) % 2 == 0) if i > 3 else None)
        for k in range(6):
            a = k / 6 * 2 * math.pi + 0.4
            L = r * 0.9
            if i < 5: gl(c, math.cos(a) * 1.5, math.sin(a) * 0.6, math.cos(a) * L, math.sin(a) * L * 0.42, "сту")
        if i < 2: star4(c, 0, -2, size=2 - i, ch="э", core="й")
        chips(c, 0, -3, 6 + i, 2, 4 + i * 2, 310 + i, "фуцш", ratio=0.6)
        fr.append(S_(c))
    fx_sheet("FxStmIdolSlam", [("Play", fr, [0.04, 0.05, 0.06, 0.07, 0.08, 0.09])], outdir)


def fx_idol_thrust(outdir):
    fr = []
    for i in range(4):
        c = Canvas()
        L = [18, 30, 30, 24][i]
        for x in range(0, L):
            w = 1 if x < L - 5 else 0
            ch = "х" if x > L * 0.6 else ("ф" if x > L * 0.3 else "у")
            if i == 3 and x % 2: continue
            c.put(x, 0, ch, over=False)
            if w and i < 3: c.put(x, -1, "у" if x % 3 else "ш"); c.put(x, 1, "т")
        if i in (1, 2): star4(c, L, 0, size=1, ch="ъ", core="й")
        fr.append(S_(c))
    fx_sheet("FxStmIdolThrust", [("Play", fr, [0.04, 0.05, 0.06, 0.07])], outdir)


def fx_idol_whirl(outdir):
    fr = []
    for i in range(6):
        c = Canvas()
        a0 = i * 60
        for a in range(a0, a0 + 300, 3):
            t = (a - a0) / 300
            r = 18
            ch = "э" if t > 0.8 else ("х" if t > 0.55 else ("ф" if t > 0.3 else "у"))
            if t < 0.3 and (a // 3) % 2: continue
            c.put(*P(math.cos(math.radians(a)) * r, -6 + math.sin(math.radians(a)) * r * 0.45), ch, over=False)
        bx, by = math.cos(math.radians(a0 + 300)) * 18, -6 + math.sin(math.radians(a0 + 300)) * 8
        ell(c, bx, by, 2.0, 2.0, "чшъ", bias=0.2)
        fr.append(S_(c))
    fx_sheet("FxStmIdolWhirl", [("Spin", fr, [0.06] * 6)], outdir)


def fx_idol_orb(outdir):
    fr = []
    for i in range(4):
        c = Canvas()
        ell(c, 0, 0, 2.2, 2.2, "чщъ", bias=0.3)
        c.put(-1, -1, "й")
        for k in range(4):
            a = k / 4 * 2 * math.pi + i * 0.4
            c.put(*P(math.cos(a) * 3.4, math.sin(a) * 3.4), "ь" if (k + i) % 2 else "э")
        for k in range(1, 4): c.put(-3 - k, (k + i) % 2 - 0, "щ" if k < 2 else "ч")
        fr.append(S_(c))
    fx_sheet("FxStmIdolOrb", [("Fly", fr, [0.05] * 4)], outdir)


def fx_idol_pillar(outdir):
    """Cross rite: a jade spike bursts from the floor after a gold warning glyph (9 frames; damage on 5..6)."""
    fr = []
    for i in range(9):
        c = Canvas()
        if i < 5:
            ring(c, 0, 0, 5.0, 0.45, "ыь" if i % 2 else "ьэ", gap=lambda a: int(a * 4) % 2 == 0)
            c.put(0, 0, "э" if i % 2 else "ь")
            for k in (-2, 2): c.put(k, 0, "ь")
        else:
            t = i - 5
            h = [10, 14, 12, 6][t]
            for y in range(0, h):
                w = max(0, int((1 - y / h) * 3))
                for x in range(-w, w + 1):
                    c.put(x, -y, "щ" if x < 0 else ("ч" if x > 0 else "ъ"))
            ring(c, 0, 0, 4 + t * 2, 0.45, "чш", gap=lambda a: int(a * 5) % 2 == 0)
            chips(c, 0, -2, 4 + t, 2, 5 + t, 320 + i, "шщь", ratio=0.6)
        f = Fr(); f.b = c
        fr.append(f.done(clip=False) if i >= 5 else S_(c))
    fx_sheet("FxStmIdolPillar", [("Play", fr, [0.12, 0.1, 0.1, 0.08, 0.08, 0.04, 0.06, 0.08, 0.1])], outdir)


def fx_sigil(outdir):
    anims = []
    for k in ("Ring", "Fan", "Spiral", "Cross"):
        fr = []
        for i in range(2):
            c = Canvas(); sigil_mark(c, 0, -7, k, i)
            fr.append(S_(c))
        anims.append((k, fr, [0.18, 0.18]))
    fx_sheet("FxStmSigil", anims, outdir)


# ---- Gambit
def fx_stamp(outdir):
    fr = []
    for i in range(5):
        c = Canvas()
        for k in range(5):
            a = math.radians(-170 + k * 40)
            L = 3 + i * 2.5
            if i < 4: gl(c, 0, 0, math.cos(a) * L, math.sin(a) * L * 0.5, "ДГВБ"[i:] or "Б")
        ring(c, 0, 0, 2 + i * 2.4, 0.4, "БВГ" if i < 3 else "АБ", gap=(lambda a: int(a * 4) % 2 == 0) if i > 2 else None)
        chips(c, 0, -2, 4 + i, 2, 3 + i * 2, 330 + i, "ГВЁ", ratio=0.6)
        fr.append(S_(c))
    fx_sheet("FxStmStamp", [("Play", fr, [0.04, 0.05, 0.06, 0.07, 0.08])], outdir)


def board_square(c, x, y, s, k, solid=False):
    """A chessboard square outline (s px) centred at (x, y) on the floor (squashed to 0.5 height)."""
    hs = s / 2.0
    for t in range(int(s) + 1):
        for (px_, py_) in ((x - hs + t, y - hs * 0.5), (x - hs + t, y + hs * 0.5), (x - hs, y - hs * 0.5 + t * 0.5), (x + hs, y - hs * 0.5 + t * 0.5)):
            c.put(*P(px_, py_), ("Е" if (t // 2 + k) % 2 else "Д"))
    if solid:
        for yy in range(int(y - hs * 0.5) + 1, int(y + hs * 0.5)):
            for xx in range(int(x - hs) + 1, int(x + hs)):
                if ((xx // 3) + (yy // 2)) % 2 == 0: c.put(xx, yy, "Ё")


def fx_knight_mark(outdir):
    """Where the Gambit's next leap lands: a chess square drawn on the floor, closing in and flashing (6 frames)."""
    fr = []
    for i in range(6):
        c = Canvas()
        s = [26, 22, 19, 18, 18, 18][i]
        board_square(c, 0, 0, s, i, solid=i >= 3)
        if i >= 3: star4(c, 0, -1, size=1, ch="Й", core="Д")
        fr.append(S_(c))
    fx_sheet("FxStmKnightMark", [("Play", fr, [0.07, 0.07, 0.07, 0.07, 0.06, 0.06])], outdir)


def fx_landing(outdir):
    fr = []
    for i in range(6):
        c = Canvas()
        r = 4 + i * 3
        ring(c, 0, 0, r, 0.45, "ВГД" if i < 3 else "БВ", thick=2 if i < 2 else 1)
        board_square(c, 0, 0, 10 + i * 4, i)
        chips(c, 0, -2, 8 + i, r * 0.5, r + 2, 340 + i, "ДГЁ", ratio=0.5)
        fr.append(S_(c))
    fx_sheet("FxStmLanding", [("Play", fr, [0.04, 0.05, 0.06, 0.07, 0.08, 0.09])], outdir)


def fx_check(outdir):
    """Over a hero in check: a tiny marble knight with a pulsing ruby eye and a red ring."""
    fr = []
    for i in range(4):
        c = Canvas()
        f = Fr()
        knight_head(f, (0.0, 0.0), 0, eye=1)
        sm = f.done(clip=False)
        # shrink to half size
        small = {}
        for (x, y), v in sm.px.items(): small[(int(math.floor(x / 2.0)), int(math.floor(y / 2.0)) - 1)] = v
        for q, v in small.items(): c.put(q[0], q[1], v)
        ring(c, 0, -5, 7, 0.9 if i % 2 else 1.0, "ИЙ", gap=lambda a, i=i: int(a * 4 + i) % 2 == 0)
        fr.append(S_(c))
    fx_sheet("FxStmCheck", [("Loop", fr, [0.15] * 4)], outdir)


def fx_checkmate(outdir):
    """Checkmate: the Gambit's slam on a hero in check - a marble king's crown cracks apart over him in a ruby flash."""
    fr = []
    for i in range(6):
        c = Canvas()
        r = 3 + i * 2.6
        ring(c, 0, -10, r, 1.0, "ИЙ" if i < 3 else "И", gap=(lambda a: int(a * 5) % 2 == 0) if i > 2 else None)
        if i < 4:
            sp = i * 1.5
            # the crown: a band with three points, split down the middle (halves drift apart)
            for side in (-1, 1):
                ox = side * sp
                for x in range(0, 4):
                    c.put(*P(ox + side * x, -9), "Г" if x % 2 else "Д")
                    c.put(*P(ox + side * x, -10), "В")
                for x in (1, 3):
                    c.put(*P(ox + side * x, -11), "Д"); c.put(*P(ox + side * x, -12), "Г")
                c.put(*P(ox + side * 2, -11), "И")
        chips(c, 0, -10, 5 + i * 2, 2 + i, 4 + i * 2, 360 + i, "ДГЙ")
        if i < 2: star4(c, 0, -10, size=2 - i, ch="Й", core="Д")
        fr.append(S_(c))
    fx_sheet("FxStmCheckmate", [("Play", fr, [0.04, 0.05, 0.06, 0.07, 0.08, 0.1])], outdir)


def fx_leap_dust(outdir):
    fr = []
    for i in range(4):
        c = Canvas()
        for s_ in (-1, 1):
            for k in range(4):
                c.put(*P(s_ * (3 + i * 2 + k), -k * 0.6 - i * 0.5), "Г" if k < 2 else "В")
        chips(c, 0, -1, 4, 2 + i, 4 + i * 2, 350 + i, "ВБ", ratio=0.5)
        fr.append(S_(c))
    fx_sheet("FxStmLeapDust", [("Play", fr, [0.05, 0.06, 0.07, 0.08])], outdir)


# ---- Caryatid
def fx_capital(outdir):
    fr = []
    for i in range(6):
        c = Canvas()
        r = 4 + i * 2.5
        ring(c, 0, 0, r, 0.42, "НОП" if i < 3 else "МН", thick=2 if i < 2 else 1, gap=(lambda a: int(a * 5) % 2 == 0) if i > 3 else None)
        for k in range(5):
            a = math.radians(-180 + k * 45)
            if i < 4: gl(c, 0, 0, math.cos(a) * r, math.sin(a) * r * 0.42, "ЛМ")
        chips(c, 0, -3, 6 + i * 2, 2, 4 + i * 2.2, 360 + i, "ОНТС", ratio=0.7)
        fr.append(S_(c))
    fx_sheet("FxStmCapital", [("Play", fr, [0.04, 0.05, 0.06, 0.07, 0.08, 0.09])], outdir)


def column_spr(h, crack=0, glint=None, seed=0):
    """A fluted marble column h px tall standing on a base, with a terracotta band and a gold seam."""
    f = Fr()
    ell(f.b, 0, -1.2, 5.0, 1.6, PEACH, bias=0.1)                                # base
    for y in range(-2, -int(h) - 1, -1):
        for x in range(-3, 4):
            flute = (x + 3) % 2
            l = -x / 3.0 * 0.7 + (0.15 if flute else -0.15)
            f.b.put(x, y, pick(PEACH, l))
    if h > 8:
        for x in range(-3, 4): f.b.put(x, -6, "С" if x % 2 else "Т")
        ell(f.b, 0, -h - 0.5, 4.6, 1.4, PEACH, bias=0.3)                        # top
    s = f.done(clip=False)
    c = Canvas(); c.px = dict(s.px)
    if h > 8:
        seam(c, [(-1, -h + 2), (1, -h * 0.6), (-1, -h * 0.35), (1, -3)], k=seed, glint=glint)
    rnd = random.Random(370)
    for i in range(crack):
        x0, y0 = rnd.uniform(-3, 3), -rnd.uniform(3, h - 2)
        for q in line_px(*P(x0, y0), *P(x0 + rnd.uniform(-2, 2), y0 + rnd.uniform(1, 4))):
            if q in c.px and c.px[q] != OUT: c.px[q] = "Л"
    return Spr(c.px)


def fx_column(outdir):
    """Raise Column: Warn (a crack ring under the hero, 4), Rise (bursts up, hit on 0..1, 5), Stand (4, loop),
    Crumble (6). Origin = the column's foot."""
    warn, rise, stand, crumble = [], [], [], []
    for i in range(4):
        c = Canvas()
        ring(c, 0, 0, 7 - i * 0.6, 0.42, "НО" if i % 2 else "МН", gap=lambda a: int(a * 5) % 3 == 0)
        for k in range(4):
            a = k / 4 * 2 * math.pi + i * 0.3
            gl(c, 0, 0, math.cos(a) * (2 + i), math.sin(a) * (1 + i * 0.4), "ЛМ")
        warn.append(S_(c))
    for i, h in enumerate((8, 20, 26, 24, 24)):
        s = column_spr(h, seed=i)
        c = Canvas(); c.px = dict(s.px)
        if i < 3: chips(c, 0, -2, 8, 4, 8 + i * 2, 380 + i, "ОНМ", ratio=0.5)
        rise.append(Spr(c.px))
    for i in range(4):
        stand.append(column_spr(24, seed=i, glint=i * 2 if i in (1, 2) else None))
    for i in range(6):
        if i < 2:
            crumble.append(column_spr(24 - i * 2, crack=4 + i * 4, seed=i))
        else:
            c = Canvas(); rubble(c, 0, 0, 16 - (i - 2) * 2, PEACH, 390 + i)
            f = Fr(); f.b = c
            s = f.done(clip=False)
            c2 = Canvas(); c2.px = dict(s.px)
            if i < 4: chips(c2, 0, -8, 6, 2, 8, 395 + i, "НО", ratio=0.8)
            crumble.append(Spr(c2.px))
    fx_sheet("FxStmColumn", [("Burst", warn + rise, [0.18, 0.16, 0.14, 0.12, 0.04, 0.04, 0.05, 0.06, 0.1]),
                             ("Warn", warn, [0.18, 0.16, 0.14, 0.12]), ("Rise", rise, [0.04, 0.04, 0.05, 0.06, 0.1]),
                             ("Stand", stand, [0.6, 0.08, 0.08, 0.6]), ("Crumble", crumble, [0.06, 0.08, 0.08, 0.1, 0.12, 0.14])], outdir)


def fx_shelter(outdir):
    fr = []
    for i in range(4):
        c = Canvas()
        ring(c, 0, 0, 9, 0.4, "МНО", gap=lambda a, i=i: (int(a * 6 + i) % 3) == 0)
        for k in range(2):
            x = -9 + k * 18
            for y in range(0, 4 + (i % 2)): c.put(x, -y, "О" if y % 2 else "Н")
        fr.append(S_(c))
    fx_sheet("FxStmShelter", [("Loop", fr, [0.18] * 4)], outdir)


# ---- Lachrymosa
def fx_lament(outdir):
    fr = []
    for i in range(5):
        c = Canvas()
        for k in range(4):
            a0 = 140 - i * 26
            for a in range(a0, a0 - 70, -4):
                r = 10 + k * 1.5
                ch = "Ы" if a > a0 - 20 else ("Ш" if a > a0 - 45 else "Ч")
                if i >= 3 and (a // 4) % 2: continue
                c.put(*P(math.cos(math.radians(a)) * r - 2, -math.sin(math.radians(a)) * r * 0.85 + k * 1.5 - 6), ch, over=False)
        if i < 3: sparks(c, 6, -6, 4, 1, 4, 400 + i, chars="ЫЪЩ")
        fr.append(S_(c))
    fx_sheet("FxStmLament", [("Slash", fr, [0.04, 0.05, 0.05, 0.06, 0.07])], outdir)


def fx_snuff(outdir):
    """Lights Out: the halo's light pinched out - a curl of grey smoke and dying gold embers rising (origin = her feet,
    drawn at halo height) - 8 frames."""
    fr = []
    for i in range(8):
        c = Canvas()
        y0 = -36
        if i < 2: star4(c, 0, y0, size=2 - i, ch="э", core="й")
        for k in range(10):
            t = k / 9.0
            y = y0 - 2 - t * (6 + i * 2.2)
            x = math.sin(t * 5.0 + i * 0.7) * (1.0 + t * 2.5)
            if t * 9 > i * 1.6 + 2: continue
            if (k + i) % 4 == 3: continue
            c.put(*P(x, y), "Ч" if t < 0.3 else ("Ц" if t < 0.65 else "Х"))
            if t > 0.3 and k % 2: c.put(*P(x + 1, y), "Х")
        for k in range(3):
            if i < 6:
                c.put(*P(-3 + k * 3 + math.sin(i + k), y0 + 1 - i * 1.5 - k), "ь" if (i + k) % 2 else "ы")
        fr.append(S_(c))
    fx_sheet("FxStmSnuff", [("Play", fr, [0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.11, 0.12])], outdir)


def fx_seen(outdir):
    """Over Lachrymosa while the hero looks at her: an open stone eye (she is stone while seen)."""
    fr = []
    for i in range(4):
        c = Canvas()
        for x in range(-4, 5):
            yy = round(math.sqrt(max(0, 16 - x * x)) * 0.45)
            c.put(x, -3 - yy, "Ш"); c.put(x, -3 + yy, "Ч")
        ell(c, 0, -3, 1.6, 1.4, "ХЦ", bias=0.2)
        c.put(0, -3, "Ь"); c.put(-1, -4, "Ы" if i % 2 else "Ш")
        c.put(-5, -3, "Ц"); c.put(5, -3, "Ц")
        f = Fr(); f.b = c
        fr.append(f.done(clip=False))
    fx_sheet("FxStmSeen", [("Loop", fr, [0.2, 0.15, 0.2, 0.15])], outdir)


def fx_unseen(outdir):
    """Under Lachrymosa while she is unseen: slow tear-light wisps rising round her hem (she is swift)."""
    fr = []
    for i in range(4):
        c = Canvas()
        ring(c, 0, 0, 11, 0.36, "ЩЪ", gap=lambda a, i=i: (int(a * 7 + i * 2) % 4) == 0)
        for k in range(5):
            x = -10 + k * 5 + (i % 2)
            y = -((i * 4 + k * 6) % 16) - 1
            c.put(x, y, "Ъ" if (k + i) % 3 else "Ы")
            if (k + i) % 2 == 0: c.put(x, y + 1, "Щ")
        fr.append(S_(c))
    fx_sheet("FxStmUnseen", [("Loop", fr, [0.14] * 4)], outdir)


def fx_arrival(outdir):
    """The legendary's arrival: a crack of gold light splits the air, feathers and marble dust fall (10 frames)."""
    fr = []
    for i in range(10):
        c = Canvas()
        if i < 5:
            w = [1, 2, 4, 3, 1][i]
            for y in range(-44, 1):
                xo = int(round(math.sin(y * 0.35) * 2))
                for x in range(-w, w + 1):
                    if abs(x) < w * 0.5 or (x + y) % 2 == 0:
                        c.put(x + xo, y, "й" if abs(x) <= 0 and i in (1, 2, 3) else ("э" if abs(x) < w * 0.7 else "ь"))
        if i >= 2:
            t = i - 2
            ring(c, 0, 0, 5 + t * 3.0, 0.42, "ХЦЧШ"[max(0, 3 - t):] or "Х", thick=2 if t < 3 else 1)
            for k in range(4):
                fx_, fy_ = -12 + k * 8 + math.sin(i + k) * 2, -30 + t * 4 + (k % 2) * 5
                gl(c, fx_, fy_, fx_ + 2, fy_ + 1, "ЦЧШ")
        sparks(c, 0, -16, 4 + i, 3 + i, 8 + i * 2, 410 + i, chars="ЫЪэ", cross=i < 5)
        fr.append(S_(c))
    fx_sheet("FxStmArrival", [("Play", fr, [0.05, 0.05, 0.06, 0.06, 0.07, 0.08, 0.08, 0.09, 0.1, 0.1])], outdir)



# ======================================================================================= the secret plinths
# Each secret statue is its monster carved in Crawl's own statue stone (statue_rigs.build: the same carving as every
# vanilla and mod statue) standing on a plinth MENDED WITH GOLD: a kintsugi seam runs across the plinth's face and a
# glint travels along it every ~2 s; a tiny glyph is cut into the plinth's front (claws, six pips, an L, a column, a
# tear). The legendary's plinth is gilded along its lips and a light sits over her head. Cells 44 x 44, plinth bottom
# on the last row, centred (the vanilla statue placement rules, see statue_rigs.py).
STATUE_CELL = 44
GLYPHS = {
    "StmGrotesque": [(-1, 0), (0, 1), (1, 0), (-1, -1), (1, -1)],         # three claw scratches (drawn as strokes)
    "StmSixfold": [(-2, 0), (0, 0), (2, 0), (-2, 2), (0, 2), (2, 2)],
    "StmGambit": [(-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1)],
    "StmCaryatid": [(-1, -1), (0, -1), (1, -1), (0, 0), (0, 1), (-1, 2), (0, 2), (1, 2)],
    "StmLachrymosa": [(0, -1), (-1, 0), (1, 0), (0, 1), (0, 0)],
}
STATUE_ORDER = ["StmGrotesque", "StmSixfold", "StmGambit", "StmCaryatid", "StmLachrymosa"]


def build_statues(outdir):
    import statue_rigs as ST
    from PIL import Image
    ST.CELL_W = ST.CELL_H = STATUE_CELL
    ST.FEET_ROW = STATUE_CELL - 6
    rgb = lambda ch: PALETTE[ch] + (255,)
    frames, anims, log = [], [], []
    for art in STATUE_ORDER:
        jp = os.path.join(outdir, art + ".json")
        src = ST.source_frame(jp)
        legend = art == "StmLachrymosa"
        ST.MAX_FIG_W, ST.MAX_FIG_H = (32, 32) if legend else (28, 28)
        img, info = ST.build(art, src[0], src[1], random.Random("statue:" + art))
        W = H = STATUE_CELL
        px = img.load()
        # plinth extents (bottom 8 rows)
        rows = {}
        for y in range(H - 8, H):
            xs = [x for x in range(W) if px[x, y][3] > 0]
            if xs: rows[y] = (min(xs), max(xs))
        x0 = min(v[0] for v in rows.values()); x1 = max(v[1] for v in rows.values())
        # the seam: from the top face's back-left corner, across the front lip, down the front to the base
        cx = (x0 + x1) // 2
        seam_pts = [(x0 + 3, H - 7), (x0 + 6, H - 5), (cx - 1, H - 4), (cx + 2, H - 3), (cx + 1, H - 2), (x1 - 3, H - 1)]
        path = []
        for a, b in zip(seam_pts, seam_pts[1:]):
            for q in line_px(a[0], a[1], b[0], b[1]):
                if q not in path and px[q][3] > 0: path.append(q)
        # the glyph cut into the front face (row H-3 .. H-1 area, right of the seam)
        gx, gy = x1 - 5, H - 3
        base = img.copy()
        bp = base.load()
        for (dx, dy) in GLYPHS[art]:
            q = (gx + dx, gy + dy - 1)
            if 0 <= q[0] < W and 0 <= q[1] < H and bp[q][3] > 0: bp[q] = rgb("а")
        for i, q in enumerate(path): bp[q] = rgb("ь" if i % 3 else "ы")
        if legend:
            for y in (H - 8, H - 3):
                if y in rows:
                    for x in range(rows[y][0], rows[y][1] + 1):
                        if bp[x, y][3] > 0: bp[x, y] = rgb("ь" if (x + y) % 2 else "э")
        fr = []
        n = 7
        for f in range(n):
            im = base.copy(); p2 = im.load()
            if 1 <= f <= 5:
                k = int((f - 1) / 4.0 * (len(path) - 1))
                for j in range(max(0, k - 1), min(len(path), k + 2)):
                    p2[path[j]] = rgb("э" if j != k else "й")
                x, y = path[k]
                for dx, dy in ((0, -1), (0, -2), (1, -1), (-1, -1)):
                    if f in (2, 3, 4) and 0 <= x + dx < W and 0 <= y + dy < H and p2[x + dx, y + dy][3] == 0:
                        p2[x + dx, y + dy] = rgb("э")
            if legend:
                # a soft light over her carved head, brightest as the seam glints
                bb = base.getbbox()
                hx, hy = (bb[0] + bb[2]) // 2, bb[1] - 2
                ch = "ь" if f in (0, 6) else ("э" if f in (1, 5) else "й")
                for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1)) if f in (2, 3, 4) else ((0, 0),):
                    if 0 <= hy + dy < H: p2[hx + dx, hy + dy] = rgb(ch if (dx, dy) == (0, 0) else "э")
            fr.append(im)
        anims.append({"name": "Statue_" + art, "frames": list(range(len(frames), len(frames) + n)),
                      "durations": [1.6, 0.07, 0.07, 0.07, 0.07, 0.08, 0.3]})
        frames += fr
        bb = base.getbbox()
        log.append("%-14s %s, visible %dx%d" % (art, info, bb[2] - bb[0], bb[3] - bb[1]))
    cols = 8
    rows_n = (len(frames) + cols - 1) // cols
    pw = 1
    while pw < cols * STATUE_CELL: pw *= 2
    ph = 1
    while ph < rows_n * STATUE_CELL: ph *= 2
    sheet_img = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet_img.paste(f, ((i % cols) * STATUE_CELL, (i // cols) * STATUE_CELL))
    import json as _json
    sheet_img.save(os.path.join(outdir, "StmStatues.png"))
    _json.dump({"cellW": STATUE_CELL, "cellH": STATUE_CELL, "cols": cols, "anims": anims}, open(os.path.join(outdir, "StmStatues.json"), "w"))
    # preview: each statue's frames, 5x, on a floor strip, with a vanilla statue for comparison
    sc = 5
    pv = Image.new("RGBA", ((STATUE_CELL + 2) * 8 * sc, (STATUE_CELL + 6) * len(anims) * sc), (28, 26, 32, 255))
    for r, a in enumerate(anims):
        for j, fi in enumerate(a["frames"]):
            pv.alpha_composite(frames[fi].resize((STATUE_CELL * sc, STATUE_CELL * sc), Image.NEAREST),
                               (j * (STATUE_CELL + 2) * sc, r * (STATUE_CELL + 6) * sc))
    pv.convert("RGB").save(os.path.join(outdir, "StmStatues_preview.png"))
    BUILT["StmStatues"] = {"cell": (STATUE_CELL, STATUE_CELL), "feet": (STATUE_CELL // 2, STATUE_CELL), "anims": [(a["name"], 7, a["durations"]) for a in anims]}
    print("\n".join(log))


MONSTERS = [("StmGrotesque", build_grotesque), ("StmSixfold", build_sixfold), ("StmGambit", build_gambit),
            ("StmCaryatid", build_caryatid), ("StmLachrymosa", build_lachrymosa)]
FX_ORDER = [("FxStmSplat", fx_splat), ("FxStmImpact", fx_impact), ("FxStmDeath", fx_death), ("FxStmAwaken", fx_awaken),
            ("FxStmRake", fx_rake), ("FxStmDust", fx_dust), ("FxStmShard", fx_shard), ("FxStmShell", fx_shell),
            ("FxStmChip", fx_chip), ("FxStmCrack", fx_crack), ("FxStmKeystone", fx_keystone),
            ("FxStmIdolCut", fx_idol_cut), ("FxStmIdolSlam", fx_idol_slam), ("FxStmIdolThrust", fx_idol_thrust),
            ("FxStmIdolWhirl", fx_idol_whirl), ("FxStmIdolOrb", fx_idol_orb), ("FxStmIdolPillar", fx_idol_pillar),
            ("FxStmSigil", fx_sigil), ("FxStmStamp", fx_stamp), ("FxStmKnightMark", fx_knight_mark),
            ("FxStmLanding", fx_landing), ("FxStmCheck", fx_check), ("FxStmCheckmate", fx_checkmate), ("FxStmLeapDust", fx_leap_dust),
            ("FxStmCapital", fx_capital), ("FxStmColumn", fx_column), ("FxStmShelter", fx_shelter),
            ("FxStmLament", fx_lament), ("FxStmSnuff", fx_snuff), ("FxStmSeen", fx_seen), ("FxStmUnseen", fx_unseen),
            ("FxStmArrival", fx_arrival)]
FX = FX_ORDER

SYNC = """
## Move anims: sync frames (facing right; spawn points relative to the feet, y up NEGATIVE; C# offsets use y up positive)

### StmGrotesque
| Clip | Frames | Moment | Spawn point |
|---|---|---|---|
| `Rake` (7): 0.10, 0.12, 0.10, 0.05, 0.08, 0.10, 0.10 | 3 | HIT: ModStmRakeHit (22 x 16) + FxStmRake | box (14, -8), slash (12, -9); talons (14, -6) |
| Stone = `StoneOn` 4 + `StoneHold` x5 + `StoneBurst` 4 | 3 | StmStoneOn: stone, ModStmDust (slow ring) at the feet | feet |
| | 15 | StmStoneBurst: 4 + 2 per stored hit ModStmShard (max 12) + FxStmShell | shards from (0, -10) |
| Crumble (status anim) = `Crumble` 5 + `Rubble` x4 + `Reform` 6 | 4 / last | collide off / StmReformed (3.5 health), collide on | - |

### StmSixfold (four basics, random each swing; `StmIdolReroll` on frame 0 of each)
| Clip | Frames | Moment | Spawn point |
|---|---|---|---|
| `Cut` (7): 0.10, 0.10, 0.10, 0.05, 0.08, 0.10, 0.10 | 3 | ModStmCutHit 26 x 18 + FxStmIdolCut | box (12, -11), arc (10, -14) |
| `Slam` (7): 0.10, 0.12, 0.12, 0.05, 0.10, 0.10, 0.10 | 3 | ModStmSlamHit 22 x 12 + FxStmIdolSlam | box (16, -4), ring (17, -1) |
| `Thrust` (7): 0.10, 0.10, 0.10, 0.04, 0.10, 0.10, 0.10 | 3 | ModStmThrustHit 36 x 10 + FxStmIdolThrust | box (22, -13), streak from (6, -17) |
| `Whirl` (8): 0.10, 0.06 x6, 0.12 | 2 | ModStmWhirlHit 44 x 24 (live 0.36 s) + FxStmIdolWhirl | box (0, -9) |
| `Cast` (9): 0.10 x5, 0.06, 0.10 x3 | 0 / 5 | StmIdolRite (sigil) / StmIdolFire: the rite | orbs from (10, -12) |

### StmGambit
| Clip | Frames | Moment | Spawn point |
|---|---|---|---|
| `Slam` (7): 0.10, 0.12, 0.12, 0.05, 0.10, 0.10, 0.10 | 3 | ModStmStampHit 20 x 16 + FxStmStamp; StmGambitSlam (checkmate) | box (14, -8), nose (14, -7) |
| Tour = (`TourCrouch` 3 + `TourAir` 3 + `TourLand` 3) x3 | 9k / 9k+3 / 9k+6 | StmTourMark (FxStmKnightMark) / StmTourJump (can't be hit, 0.3 s flight) / StmTourLand (ModStmLanding 30 x 14) | the L square |

### StmCaryatid
| Clip | Frames | Moment | Spawn point |
|---|---|---|---|
| `Smash` (8): 0.10, 0.12, 0.14, 0.06, 0.05, 0.10, 0.12, 0.10 | 4 | ModStmSmashHit 24 x 14 + FxStmCapital | box (15, -5), dust (15, -1) |
| `Raise` (8): 0.10, 0.10, 0.12, 0.08, 0.06, 0.12, 0.12, 0.10 | 4 | StmRaiseColumn: ModStmColumnBurst at the hero (FxStmColumn Burst: warn 0.6 s, hit frames 4-5), the column 0.75 s later | hero (max 140 px) |

### StmLachrymosa
| Clip | Frames | Moment | Spawn point |
|---|---|---|---|
| `Lament` (8): 0.10 x4, 0.05, 0.08, 0.10, 0.12 | 4 | ModStmLamentHit 26 x 22 + FxStmLament | box (13, -13), slash (12, -14) |
| `Snuff` (7): 0.10, 0.10, 0.12, 0.10, 0.06, 0.12, 0.12 | 4 | StmLightsOut: Lights Out (2.5 s, the dark overlay is drawn in code: LightsOut in StatuePack.cs) + FxStmSnuff at her halo + the dark cue | feet (art at halo height) |

### StmStatues (the secret plinths)
One 7-frame loop per secret ("Statue_<sheet>"): 1.6 s still, the gold seam's glint runs along it (frames 1-5), 0.3 s.
44 x 44 cells, plinth bottom on the last row, centred (PropMonsterStatue BotCenter anchor).
"""


def write_timing(outdir):
    rows = ["# Secret statues: sprite timing", "",
            "Generated by `tools/sprites/statuemon_rigs.py`. Frame indices are 0-based. Monsters face right; feet = (cellW//2, cellH-2).",
            "Drawn at final size (no ArtScale entry).", "", "## Monster sheets", "",
            "| Sheet | Cell (w x h) | Feet | Anims (frames) |", "|---|---|---|---|"]
    for n, _ in MONSTERS:
        if n not in BUILT: continue
        b = BUILT[n]
        rows.append("| %s | %d x %d | (%d, %d) | %s |" % (n, b["cell"][0], b["cell"][1], b["feet"][0], b["feet"][1],
                                                         ", ".join("%s %d" % (a, k) for a, k, _ in b["anims"])))
    rows.append(SYNC)
    rows += ["", "## FX sheets (origin = the pixel Strike.ArtAt / Strike.Ground put on the effect's transform)", "",
             "| Sheet | Cell | Origin | Anims |", "|---|---|---|---|"]
    for n, _ in FX_ORDER + [("StmStatues", None)]:
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
    if only is None or "StmStatues" in only: build_statues(outdir)
    for k, v in NOTES.items(): print("  %s: %s" % (k, v))
    for n, _ in FX_ORDER:
        if n in BUILT: print("  %-18s cell %s origin %s" % (n, BUILT[n]["cell"], BUILT[n]["feet"]))
    if only is None: write_timing(outdir)


if __name__ == "__main__":
    main()
