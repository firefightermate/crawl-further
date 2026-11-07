"""GHOST FORMS IN GAME + menu marks: the bodies a Gleaner, Binder or Poltergeist player flies around as, and the
small menu sprites (violet god-list pip, MOD badge gem).

    python3 ghost_forms.py [outdir] [--only Name,Name]

How the vanilla ghost shows the player's colour (checked in the game data, see TIMING.md):
  the four ghost prefabs CharacterP1BlueGhost .. P4YellowGhost share ONE set of frames (AtlasEnemies ghost_p1_blue_*)
  and differ only in their MeshRenderer material: P1 = AtlasEnemies (SpriteTinted, frames drawn as they are),
  P2/P3/P4 = MaterialPalettedRed/Green/Yellow (PowerHoof/SpritePaletted, _ColorRamp PaletteRed_91 / PaletteGreen_90 /
  PaletteYellow_121). The ramps remap exactly the ghost's own colours: 4 shroud greys -> the player's colour, 4 pale
  head/hand yellows -> a tinted yellow, the pink eye stays pink. Every other colour is drawn unchanged.
So the form bodies are drawn with exactly those key colours for the ghost's flesh (shroud, hair, head, hands, eyes)
at the vanilla alpha (158), and their props (sack, chains, cutlery, hex fire) with colours whose ramp slot is pink in
all three ramps (asserted below), so they look the same for every player. GhostPack.cs draws each form with a copy of
the player's own ghost material, exactly like the vanilla ghost.

Sheets (54 x 50 cells: the vanilla ghost's own cell, same anchor, so the prefab's sprite offset is kept):
  FormGleaner      Spawn 10, Idle 6, Run 6
  FormBinder       Spawn 10, Idle 6, Run 6
  FormPoltergeist  Spawn 10, Idle 6, Run 6, Throw 6
Menu: ModVioletPip (3 x 4, the god-list pip size), ModBadgeGem (5 x 5, the MOD gem Core's ModGem shows over mod art).
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from rig import Canvas, line_px  # noqa: E402
from anim import Spr, pack, preview  # noqa: E402
from shaded_prims import ell, tube, line, P, ik  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "art", "out_ghosts")
CORE_OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "art", "core")
DUMP = os.environ.get("CRAWL_DUMP", os.path.join(os.path.dirname(os.path.dirname(HERE)), "build", "dump"))

CELL = (54, 50)
ORIGIN = (28, 42)      # the ghost's transform point inside the vanilla 54 x 50 ghost cell (anchor BotCenter, offset (-1, -7.5))
GA = 158               # vanilla ghost alpha


def hx(h, a=255):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


# ghost flesh: the vanilla ghost's own key colours (slot -> player colour in each player ramp)
FLESH = {
    'a': (150, 154, 138, GA), 'b': (148, 166, 148, GA), 'c': (143, 166, 151, GA), 'd': (145, 174, 164, GA),   # shroud
    'h': (205, 210, 132, GA), 'i': (212, 221, 143, GA), 'j': (219, 225, 145, GA), 'k': (230, 233, 151, GA),   # head/hands
    'e': (242, 178, 147, GA),                                                                                  # eyes
    # faint wisps: the same shroud slots at a lower alpha (the ramp keys on rgb only)
    '1': (150, 154, 138, 96), '2': (148, 166, 148, 120), '3': (150, 154, 138, 60),
}
# props + details: colours whose _ColorRamp slot is pink in every player ramp (drawn as is for every player)
PROPS = {
    'M': hx('161c1c', 210), 'O': hx('3a4038', 200),                                           # mouth, eye socket
    'K': hx('2a1e18'), 's': hx('4e3a2a'), 'S': hx('6b5238'), 't': hx('8a6c48'), 'T': hx('a88a5e'), 'r': hx('c8b07a'),  # sack
    'g': hx('33846a'), 'G': hx('72cc9e'), 'z': hx('a8e8c4'), 'Z': hx('e8fdf0'),               # ectoplasm = ghost_rigs GOO7[2,4,5,6]
    'q': hx('1e4a44'), 'Q': hx('2c625a'), 'w': hx('4c9c8c'), 'W': hx('70ccb8'), 'X': hx('c8fff0'),   # binder chain
    'm': hx('3a3e48'), 'n': hx('6e7484'), 'N': hx('a6aebe'), 'u': hx('d8e0ee'), 'U': hx('f4f6fa'),   # steel
    'p': hx('8a93a8'), 'R': hx('5a6aa0'),                                                     # plate shade, rim
    'v': hx('2a4426'), 'V': hx('5aa44a'), 'x': hx('7fd36a'), 'y': hx('d8ffa0'),               # hex fire
}
GPAL = dict(FLESH); GPAL.update(PROPS)
SHROUD = "abcd"
SKIN = "hijk"


def _slot(c):
    r, g, b = c[:3]
    return min(15, r * 16 // 255) + 16 * min(15, g * 16 // 255), min(63, b * 64 // 255)


def check_ramps():
    """Flesh colours must be remapped by every player ramp and props must be left alone (pink) by all of them."""
    from PIL import Image
    paths = [os.path.join(DUMP, "tex", n + ".png") for n in ("PaletteRed_91", "PaletteGreen_90", "PaletteYellow_121")]
    if not all(os.path.exists(p) for p in paths):
        print("ramp check skipped (no vanilla dump)"); return
    for p in paths:
        im = Image.open(p).convert("RGB"); px = im.load()
        mapped = {(x, 63 - y) for x in range(256) for y in range(64) if px[x, y] != (255, 0, 255)}
        for ch, c in FLESH.items():
            assert _slot(c) in mapped, "flesh %s %s not remapped by %s" % (ch, c, p)
        for ch, c in PROPS.items():
            assert _slot(c) not in mapped, "prop %s %s would be recoloured by %s" % (ch, c, p)


class SprA(Spr):
    """Sprite whose chars map through GPAL to RGBA (the ghost flesh is translucent)."""

    def to_rgba(self):
        return {k: GPAL[c] for k, c in self.px.items() if c in GPAL}


def cv():
    return Canvas()


# ================================================================== the hag ghost, in-game scale (~22 x 22)
class Pose:
    def __init__(self, **kw):
        self.bob = 0.0            # whole-body vertical offset (negative = up)
        self.lean = 0.0           # head/shoulders forward (+x) relative to the tail
        self.sway = 0.0           # tail sway (-1..1)
        self.hair = 0.0           # hair stream offset
        self.stretch = 1.0        # vertical stretch about the hem (spawn)
        self.front = (9.0, -21.0)  # near (front) hand target, body coords
        self.back = (4.0, -23.0)   # far hand target
        self.claw = (True, True)  # fingers spread on (front, back)
        self.face = "wail"        # wail | hum | grit | calm
        self.eyes = "glow"        # glow | angry | shut
        self.tail = 1.0           # tail length factor
        self.wisp = 0.0           # 0..1: how much of the body has formed (spawn)
        self.squash = 1.0         # horizontal scale
        self.__dict__.update(kw)


def _T(p, x, y):
    """Body coords -> sprite coords: stretch about the hem, lean the upper body forward, bob."""
    k = max(0.0, min(1.0, -y / 22.0))
    return x * p.squash + p.lean * k, y * p.stretch + p.bob


def shroud(c, p):
    sw = p.sway
    tl = p.tail
    pts = [(2.6, -13.5), (2.2, -10.5), (0.6, -7.2), (-2.6, -4.6), (-6.5 * tl, -3.2 + sw * 0.6),
           (-9.8 * tl, -3.6 + sw * 1.2), (-12.0 * tl, -5.2 + sw * 1.6), (-12.6 * tl, -7.0 + sw * 1.4)]
    rad = [2.7, 3.9, 4.2, 3.4, 2.2, 1.3, 0.8, 0.45]
    pts = [_T(p, x, y) for x, y in pts]
    rad = [r * (0.5 + 0.5 * p.squash) for r in rad]
    tube(c, pts, rad, SHROUD, bias=0.05)
    # ragged hem: a few torn tatters hanging under the belly, a darker fold down the middle
    for (x, l) in ((-1.5, 2), (1.0, 1), (3.0, 2)):
        X, Y = P(*_T(p, x + 0.4 * sw, -3.2))
        for k in range(l):
            if (X, Y + k) not in c.px: c.put(X, Y + k, '1' if k == l - 1 else 'a')
    for (x, y) in ((1.5, -10), (0.8, -8), (-0.5, -6), (-2.0, -5)):
        X, Y = P(*_T(p, x, y))
        if (X, Y) in c.px: c.put(X, Y, 'a')
    # tail tip fades out
    tip = P(*_T(p, -13.2 * tl, -8.2 + sw * 1.2))
    c.put(tip[0], tip[1], '1')
    c.put(tip[0] + 1, tip[1] - 1, '3')


def hair(c, p, wild=False):
    hx_, hy_ = _T(p, 2.6, -16.5)
    ell(c, hx_ - 1.0, hy_ - 0.4, 3.4, 3.4, "abc", bias=-0.1)
    clumps = ((-160, 6.5, 1.6), (-185, 7.5, 1.5), (-205, 5.5, 1.3)) + (((-130, 5.0, 1.2),) if wild else ())
    for i, (a0, L, r0) in enumerate(clumps):
        a1 = a0 + 25 + p.hair * 10 + (12 if wild else 0)
        x0, y0 = hx_ - 1.5, hy_ - 1.0 + i * 1.0
        x1 = x0 + L * 0.5 * math.cos(math.radians(a0)); y1 = y0 + L * 0.5 * math.sin(math.radians(a0))
        x2 = x1 + L * 0.5 * math.cos(math.radians(a1)); y2 = y1 + L * 0.5 * math.sin(math.radians(a1))
        tube(c, [(x0, y0), (x1, y1), (x2, y2)], [r0, r0 * 0.7, 0.45], "abc" if i == 0 else "ab")
        c.put(*P(x2 + math.cos(math.radians(a1)), y2 + math.sin(math.radians(a1))), '1')
    if wild:   # strands standing on end (poltergeist fury)
        for dx, h in ((-2.0, 3), (0.5, 4), (2.5, 2)):
            line(c, hx_ + dx, hy_ - 3, hx_ + dx - 0.8 + 0.5 * p.hair, hy_ - 3 - h, 'b')
            c.put(*P(hx_ + dx - 0.8 + 0.5 * p.hair, hy_ - 3 - h), '2')


HEADS = {
    # 6 x 6 hag heads facing right (3/4 view): j/k lit skin, h shade, O sunken socket, e glowing eye, M open mouth
    "wail": [".jkkj.",
             "jkkkjh",
             "OejOeh",
             "hijjih",
             ".hMMh.",
             "..MO.."],
    "hum":  [".jkkj.",
             "jkkkjh",
             "OejOeh",
             "hijjih",
             ".hiMh.",
             "..hh.."],
    "grit": ["O.kk.O",
             "jOkjOh",
             "OejOeh",
             "hijjih",
             ".MjMM.",
             "..hh.."],
    "calm": [".jkkj.",
             "jkkkjh",
             "OOjOOh",
             "hijjih",
             ".hiOh.",
             "..hh.."],
}


def head(c, p):
    hx_, hy_ = _T(p, 3.2, -16.0)
    key = "grit" if p.eyes == "angry" else p.face
    g = HEADS[key]
    X0, Y0 = int(round(hx_)) - 3, int(round(hy_)) - 3
    for j, row in enumerate(g):
        for i, ch in enumerate(row):
            if ch == '.': continue
            if p.eyes == "shut" and ch == 'e': ch = 'O'
            c.put(X0 + i, Y0 + j, ch)
    # a lit crown so the skull reads above the hair
    c.put(X0 + 2, Y0 - 1, 'j'); c.put(X0 + 3, Y0 - 1, 'h')


def arm(c, p, shoulder, target, claw=True, front=True, l1=4.6, l2=4.6, bend=-1):
    sx, sy = _T(p, *shoulder)
    tx, ty = target
    (ex, ey), (hx_, hy_) = ik(sx, sy, tx, ty, l1, l2, bend=bend)
    ramp = "hij" if front else "hh"
    tube(c, [(sx, sy), (ex, ey), (hx_, hy_)], [0.8, 0.65, 0.6], ramp)
    if claw:
        a = math.atan2(hy_ - ey, hx_ - ex)
        for da in (-0.6, 0.0, 0.6):
            fx, fy = hx_ + 2.2 * math.cos(a + da), hy_ + 2.2 * math.sin(a + da)
            line(c, hx_, hy_, fx, fy, 'i' if front else 'h')
            c.put(*P(fx, fy), 'k' if front else 'i')
    return (hx_, hy_)


def hag(c, p, wild=False, behind=None, between=None, front_fn=None, back_arm=True, front_arm=True):
    """Draw order: far arm, behind-props, hair, shroud, head, between-props, near arm, front props."""
    hands = {}
    if back_arm:
        hands["back"] = arm(c, p, (5.2, -12.5), _T(p, *p.back) if p.back else None, claw=p.claw[1], front=False,
                            bend=-1) if p.back else None
    if behind: behind(c, p)
    hair(c, p, wild)
    shroud(c, p)
    head(c, p)
    if between: between(c, p)
    if front_arm and p.front:
        hands["front"] = arm(c, p, (1.2, -12.0), _T(p, *p.front), claw=p.claw[0], front=True, bend=-1)
    if front_fn: front_fn(c, p, hands)
    return hands


def finish(c):
    return SprA(c.px)


# ================================================================== spawn: rising out of a pool of ectoplasm
def spawn_pool(c, w, h, bub=0, y=-4.5):
    """The puddle the ghost rises from (vanilla spawn frames 0-2 sit ~4-6 px above the ghost's origin)."""
    for x in range(-int(w), int(w) + 1):
        t = abs(x) / max(1.0, w)
        top = int(round(y - h * (1 - t * t)))
        for yy in range(top, int(y) + 1):
            ch = 'd' if yy == top and x < 0 else 'c' if yy == top else 'a' if yy == int(y) else 'b'
            c.put(x, yy, ch)
        if abs(x) == int(w): c.put(x, int(y), '1')
    for k in range(bub):
        bx = [-3, 2, 4, -1][k % 4]
        c.put(bx, int(round(y - h)) - 1 - (k % 2), '2')


def column(c, top, w, lean=0.0, y=-4.5):
    """A rising column of ectoplasm (spawn frames 3-4)."""
    pts = [(0.0, y), (lean * 0.4, (y + top) / 2), (lean, top)]
    tube(c, pts, [w, w * 0.8, w * 0.65], SHROUD, bias=0.1)


def spawn_frames(form, final_pose, final_fn):
    """10 frames, 0.1 s each, the vanilla ghost spawn's timing (its events: sound at 0.2 s, input on at 0.7 s)."""
    out = []
    # 0-2 the pool gathers and bubbles
    for i, (w, h, b) in enumerate(((7, 0.6, 0), (6, 1.6, 2), (5, 3.0, 3))):
        c = cv(); spawn_pool(c, w, h, b); out.append(finish(c))
    # 3 a column surges up, a pale head inside it
    c = cv(); spawn_pool(c, 4, 1.0)
    column(c, -15.0, 3.0, lean=0.5)
    ell(c, 0.6, -15.5, 2.0, 2.4, SKIN, bias=0.1); c.put(0, -16, 'e'); c.put(2, -16, 'e')
    out.append(finish(c))
    # 4 the hag tears free, stretched tall, arms flung up
    p = Pose(stretch=1.35, lean=-1.0, bob=-1.0, tail=0.45, front=(5.0, -30.0), back=(0.0, -30.5), face="wail", sway=0.0,
             squash=0.85)
    c = cv(); spawn_pool(c, 3, 0.5)
    hag(c, p); out.append(finish(c))
    # 5 still rising, the tail starting to curl
    p = Pose(stretch=1.18, lean=0.0, bob=-4.0, tail=0.7, front=(8.0, -29.0), back=(2.0, -30.0), face="wail", sway=-1.0,
             squash=0.92)
    c = cv(); hag(c, p); out.append(finish(c))
    # 6-8: the form's own tools materialise (form_fn draws them with a 'form' fraction)
    for k, (bob, st, fr) in enumerate(((-6.0, 1.08, 0.35), (-6.5, 1.0, 0.7), (-4.5, 0.97, 1.0))):
        p = final_pose(k + 2)
        p.bob += bob + 1.5 * k * 0.0
        p.stretch = st
        c = cv(); final_fn(c, p, fr); out.append(finish(c))
    # 9 settle onto the idle bob
    p = final_pose(0); p.bob -= 1.0
    c = cv(); final_fn(c, p, 1.0); out.append(finish(c))
    return out


# ================================================================== GLEANER: a sack of ectoplasm at her side, beckoning
def sack(c, x, y, sw, fill=1.0, frac=1.0, open_=1.0):
    """A bulging burlap sack hanging from its neck at (x, y); fill swells it, frac fades it in (spawn)."""
    if frac <= 0: return
    if frac < 0.5:   # a ghostly outline of the sack first
        for k in range(10):
            a = k / 10.0 * 2 * math.pi
            c.put(*P(x + sw * 0.5 + 3.4 * math.cos(a), y + 4.6 + 3.2 * math.sin(a)), 'g' if k % 2 else 'G')
        return
    cx, cy = x + sw * 0.6, y + 4.4
    rx, ry = 3.3 + 0.5 * fill, 3.2 + 0.3 * fill
    ell(c, cx, cy, rx, ry, "sStT", bias=0.05)
    # outline the bottom + far side so it reads off the floor
    for k in range(18):
        a = k / 18.0 * 2 * math.pi
        X, Y = P(cx + (rx + 0.6) * math.cos(a), cy + (ry + 0.6) * math.sin(a))
        if (X, Y) not in c.px and (math.sin(a) > -0.2 or math.cos(a) > 0.4): c.put(X, Y, 'K')
    # neck gathered by a rope, mouth open with a green glow
    ell(c, x, y + 0.6, 1.8, 1.1, "sS")
    line(c, x - 1.6, y + 1.4, x + 1.6, y + 1.4, 'r')
    if open_ > 0:
        c.put(*P(x - 1, y), 'g'); c.put(*P(x, y), 'G'); c.put(*P(x + 1, y), 'g')
        c.put(*P(x, y - 1), 'z')
    # patches and a seam
    c.put(*P(cx - 1.5, cy + 1.0), 's'); c.put(*P(cx + 1.4, cy - 0.6), 'K')
    c.put(*P(cx - 0.4, cy + 2.4), 'S')


def motes(c, tx, ty, ph, n=3, r0=8.0):
    """Ectoplasm motes spiralling into the point (tx, ty); ph in [0, 1) loops."""
    for i in range(n):
        u = ((i + ph) / n) % 1.0
        a = 2.4 * (1 - u) * 2 * math.pi + 0.8 + i
        r = r0 * (1 - u)
        x, y = tx + r * math.cos(a), ty + r * 0.55 * math.sin(a) - 3.0 * (1 - u)
        if u < 0.85:
            c.put(*P(x, y), 'Z' if u > 0.4 else 'z')
            tx_, ty_ = x - 1.2 * math.sin(a) * (1 - u), y + 0.8 * math.cos(a) * (1 - u)
            if P(tx_, ty_) != P(x, y): c.put(*P(tx_, ty_), 'G')


def gleaner_pose(i):
    bob = [0, -1, -1, 0, 1, 1][i % 6]
    sw = [0, 0.6, 1, 0.6, 0, -0.6][i % 6]
    beck = [0, 1, 2, 1, 0, -1][i % 6]
    return Pose(bob=bob, sway=sw, hair=[0, 1, 1, 0, -1, -1][i % 6], face="hum",
                back=(8.5 + beck * 0.4, -21.5 + beck * 0.7), front=(7.5, -9.0 + bob * 0.3),
                claw=(False, True), lean=0.4)


def gleaner_draw(c, p, frac=1.0, ph=0.0, swing=0.0, fill=1.0):
    hands = hag(c, p, front_arm=False)
    # the near arm hangs down to the sack's neck
    hand = arm(c, p, (1.2, -12.0), _T(p, *p.front), claw=False, front=True, bend=1)
    nx, ny = hand
    sack(c, nx + 0.5, ny + 0.5, swing, fill=fill, frac=frac)
    # fingers curled round the rope
    c.put(*P(nx + 1, ny), 'k'); c.put(*P(nx, ny + 1), 'i')
    if frac >= 1.0 and ph is not None:
        motes(c, nx + 0.5, ny, ph)


def gleaner_idle(i):
    p = gleaner_pose(i)
    c = cv(); gleaner_draw(c, p, ph=i / 6.0, swing=[0, 0.4, 0.8, 0.4, 0, -0.4][i], fill=[1.0, 1.1, 1.2, 1.1, 1.0, 0.95][i])
    return finish(c)


def gleaner_run(i):
    bob = [0, -1, -2, -1, 0, 1][i]
    p = Pose(bob=bob - 1, lean=2.6, sway=[1.0, 1.4, 1.6, 1.4, 1.0, 0.8][i], tail=1.15, hair=1.6, face="hum",
             back=(12.0, -17.5 + [0, -1, -2, -1, 0, 1][i] * 0.6), claw=(False, True),
             front=(5.0, -8.5), squash=1.0)
    c = cv(); gleaner_draw(c, p, ph=None, swing=-1.8 - 0.4 * [0, 1, 2, 1, 0, -1][i], fill=1.0)
    # motes streaming behind
    for k in range(3):
        x = -6 - k * 3 - (i % 3); y = -18 + k * 2 + (i % 2) + bob
        c.put(x, y, 'z' if k else 'Z')
    return finish(c)


# ================================================================== BINDER: chained hands, a glowing shackle
def chain_px(c, pts, phase, lit=True, shade=False):
    k = 0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for (x, y) in line_px(*P(x0, y0), *P(x1, y1)):
            if k > 0 and (x, y) == last: continue
            ch = ('W' if k % 2 == 0 else 'Q') if not shade else ('w' if k % 2 == 0 else 'q')
            if lit and (k + phase) % 7 == 0: ch = 'X'
            c.put(x, y, ch)
            last = (x, y); k += 1
    return k


def shackle(c, x, y, ph, frac=1.0):
    """The bound blob: a small ring of chain round a glowing gel bead."""
    if frac <= 0: return
    ell(c, x, y, 2.0, 1.7, "gGzZ" if frac >= 1 else "gG", bias=0.2)
    c.put(*P(x + 0.5, y - 0.5), 'Z' if ph % 2 else 'z')
    for k in range(10):
        a = (k / 10.0 + ph / 24.0) * 2 * math.pi
        c.put(*P(x + 2.8 * math.cos(a), y + 2.2 * math.sin(a)), 'X' if k == ph % 10 else ('W' if k % 2 else 'Q'))


def binder_pose(i):
    bob = [0, -1, -1, 0, 1, 1][i % 6]
    return Pose(bob=bob, sway=[0, 0.6, 1, 0.6, 0, -0.6][i % 6], hair=[0, 1, 1, 0, -1, -1][i % 6], face="calm",
                eyes="glow", front=(6.5, -9.5), back=(8.5, -10.5), claw=(False, False), lean=0.6)


def binder_draw(c, p, frac=1.0, ph=0, dangle=0.0, trail=0.0):
    def between(c_, p_):
        # a chain wound round her: across the chest and round the tail
        a0 = _T(p_, -2.8, -11.0); a1 = _T(p_, 1.0, -8.6); a2 = _T(p_, 5.6, -10.6)
        n = chain_px(c_, [a0, a1, a2], ph * 2, lit=frac >= 1)
        t0 = _T(p_, -9.2, -5.6 + p_.sway); t1 = _T(p_, -5.0, -3.0 + p_.sway * 0.5); t2 = _T(p_, -1.6, -4.4)
        chain_px(c_, [t0, t1, t2], ph * 2 + 3, lit=frac >= 1, shade=True)
    hands = hag(c, p, between=between if frac > 0.3 else None)
    # hands joined: a loop of chain hangs from them to the shackled bead
    hx_, hy_ = hands.get("front") or _T(p, 6.5, -9.5)
    c.put(*P(hx_ + 0.5, hy_ - 0.5), 'k'); c.put(*P(hx_ + 1.5, hy_), 'j')
    if frac > 0.3:
        bx, by = hx_ + 1.8 + dangle - trail, hy_ + 6.2 - abs(dangle) * 0.3
        mid = (hx_ + 1.4 + dangle * 0.5 - trail * 0.5, hy_ + 3.0)
        chain_px(c, [(hx_ + 1, hy_ + 1), mid, (bx, by - 2.2)], ph, lit=frac >= 1)
        shackle(c, bx, by, ph, frac)


def binder_idle(i):
    p = binder_pose(i)
    c = cv(); binder_draw(c, p, ph=i, dangle=[0, 0.6, 1.0, 0.6, 0, -0.6][i])
    return finish(c)


def binder_run(i):
    bob = [0, -1, -2, -1, 0, 1][i]
    p = Pose(bob=bob - 1, lean=2.4, sway=[1.0, 1.4, 1.6, 1.4, 1.0, 0.8][i], tail=1.15, hair=1.6, face="calm",
             front=(9.0, -11.0), back=(10.5, -12.0), claw=(False, False))
    c = cv(); binder_draw(c, p, ph=i, dangle=-1.5, trail=2.0 + (i % 2))
    return finish(c)


# ================================================================== POLTERGEIST: flung crockery, a hex-fire throw
KNIFE = ["U", "U", "u", "u", "N", "m", "s", "s"]   # tip -> blade -> bolster -> wooden handle
FORK = ["u", "u", "N", "N", "m", "s", "s"]


def utensil(c, x, y, ang, kind="knife", frac=1.0):
    if frac <= 0: return
    pal = KNIFE if kind == "knife" else FORK
    a = math.radians(ang)
    pts = [(x + k * math.cos(a), y + k * math.sin(a)) for k in range(len(pal))]
    for k, (px_, py_) in enumerate(pts):
        ch = pal[k] if frac >= 1 else ('n' if k % 2 else 'N')
        c.put(*P(px_, py_), ch)
    if kind == "fork" and frac >= 1:   # tines
        nx, ny = -math.sin(a), math.cos(a)
        c.put(*P(x + nx, y + ny), 'N'); c.put(*P(x - nx, y - ny), 'N')


def plate(c, x, y, ang=0.0, frac=1.0):
    if frac <= 0: return
    if frac < 1:
        ell(c, x, y, 2.8, 1.2, "pN", ang=ang); return
    ell(c, x, y, 3.6, 1.8, "pNuU", ang=ang, bias=0.25)
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    for k in range(24):   # blue rim round the edge
        a = k / 24.0 * 2 * math.pi
        u, v = 3.9 * math.cos(a), 2.1 * math.sin(a)
        X, Y = P(x + u * ca - v * sa, y + u * sa + v * ca)
        if (X, Y) not in c.px or math.sin(a) > 0.3: c.put(X, Y, 'R')
    ell(c, x + 0.3, y + 0.2, 1.6, 0.7, "pN", ang=ang)   # the well of the plate


HEXBALL = {1: [".x.", "xyx", ".V."],
           2: [".xV.", "xyyV", "xyyV", ".Vv."],
           3: ["..x..", ".xyxV", "xyyyV", ".xyVv", "..Vv."]}


def hex_flame(c, x, y, ph, size=1.0):
    """A ball of green hex fire held in the hand, flame tongues licking up (size 1-3)."""
    g = HEXBALL[max(1, min(3, int(round(size))))]
    h = len(g)
    X0, Y0 = int(round(x)) - h // 2, int(round(y)) - h // 2
    for j, row in enumerate(g):
        for i, ch in enumerate(row):
            if ch != '.': c.put(X0 + i, Y0 + j, ch)
    for k in range(1, h):   # tongues
        fx = X0 + h // 2 + (1 if (k + ph) % 2 else -1) * (k // 2)
        c.put(fx, Y0 - k, 'x' if k == 1 else 'V' if k == 2 else 'v')


def polter_pose(i):
    bob = [0, -1, -1, 0, 1, 1][i % 6]
    return Pose(bob=bob, sway=[0, 0.6, 1, 0.6, 0, -0.6][i % 6], hair=[0, 1, 2, 1, 0, -1][i % 6], face="grit",
                eyes="angry", back=(-1.5 + [0, 0.5, 1, 0.5, 0, -0.5][i % 6], -23.5 + bob * 0.3),
                front=(10.5, -17.0 + [0, -1, -1, 0, 1, 1][i % 6] * 0.5), claw=(True, False), lean=0.8)


def polter_items(c, p, ph, frac=1.0, spin=0, spread=1.0, cx=-0.5, cy=-15.0):
    """Cutlery circling her: a knife and a fork on a tilted orbit (one lap per 6 frames)."""
    for k, kind in enumerate(("knife", "fork")):
        a = (ph / 6.0 + k * 0.5) * 2 * math.pi
        x = cx + 11.0 * spread * math.cos(a)
        y = cy + 4.0 * spread * math.sin(a) + p.bob
        utensil(c, x, y, ang=(ph * 60 + k * 150 + spin) % 360, kind=kind, frac=frac)


def polter_draw(c, p, frac=1.0, ph=0, items=True, plate_at=None, flame=None, behind_items=True):
    def behind(c_, p_):
        # items on the far half of the orbit go behind her
        if items and behind_items:
            sub = cv(); polter_items(sub, p_, ph, frac)
            for (x, y), v in sub.px.items():
                if y < p_.bob - 15: c_.put(x, y, v)
    hands = hag(c, p, wild=True, behind=behind)
    bh = hands.get("back")
    if plate_at is None and bh is not None:
        plate(c, bh[0] - 0.5, bh[1] - 1.8, ang=-20, frac=frac)
    elif plate_at:
        plate(c, plate_at[0], plate_at[1], ang=plate_at[2], frac=frac)
    if items:
        sub = cv(); polter_items(sub, p, ph, frac)
        for (x, y), v in sub.px.items():
            if y >= p.bob - 15: c.put(x, y, v)
    if flame and hands.get("front"):
        fx, fy = hands["front"]
        hex_flame(c, fx + flame[0], fy + flame[1], ph, flame[2])


def polter_idle(i):
    p = polter_pose(i)
    c = cv(); polter_draw(c, p, ph=i)
    return finish(c)


def polter_run(i):
    bob = [0, -1, -2, -1, 0, 1][i]
    p = Pose(bob=bob - 1, lean=2.8, sway=[1.0, 1.4, 1.6, 1.4, 1.0, 0.8][i], tail=1.15, hair=2.0, face="grit",
             eyes="angry", back=(0.0, -24.0), front=(13.0, -15.0), claw=(True, False))
    c = cv(); polter_draw(c, p, ph=i, items=False)
    # the cutlery trails behind her in her wake
    utensil(c, -10 - (i % 2), -17 + bob, 180 + 20 * (i % 3), "knife")
    utensil(c, -14 + (i % 2), -11 + bob, 160 - 25 * (i % 3), "fork")
    return finish(c)


# Throw: the hex bolt leaves the front hand on frame 3 (see TIMING.md for the spawn point)
THROW_DURS = [0.08, 0.08, 0.05, 0.06, 0.08, 0.1]
THROW_RELEASE = 3


def throw_hand():
    """Sprite coords of the throwing hand on the release frame (= where the hex bolt should appear)."""
    p = Pose(lean=3.0, front=(13.0, -8.5))
    sx, sy = _T(p, 1.2, -12.0)
    return ik(sx, sy, *_T(p, *p.front), 4.6, 4.6, bend=-1)[1]


def polter_throw(i):
    keys = [
        # wind-up: lean back, the hand pulled up over the shoulder, hex fire kindling in it
        dict(lean=-1.0, bob=0, front=(-1.0, -24.0), back=(9.0, -14.0), fl=(0.0, -1.0, 2), sway=-0.6),
        dict(lean=-2.2, bob=-1, front=(-5.0, -22.5), back=(10.0, -15.0), fl=(-0.5, -1.0, 3), sway=-1.0),
        # whip: the arm sweeps over the top, the body pitches forward
        dict(lean=1.4, bob=-1, front=(7.0, -26.0), back=(-4.0, -15.0), fl=(0.5, -0.5, 3), sway=0.4),
        # release: arm flung out level, the bolt leaves the hand
        dict(lean=3.0, bob=0, front=(13.0, -8.5), back=(-6.0, -17.0), fl=None, sway=1.2),
        # follow-through: hand drops past the hip
        dict(lean=2.4, bob=1, front=(10.0, -4.5), back=(-5.0, -19.0), fl=None, sway=1.0),
        # recover
        dict(lean=1.2, bob=0, front=(10.0, -15.0), back=(-2.0, -22.0), fl=None, sway=0.4),
    ]
    k = keys[i]
    p = Pose(bob=k["bob"], lean=k["lean"], sway=k["sway"], hair=1.5 if i < 3 else -1.0, face="grit" if i != 3 else "wail",
             eyes="angry", front=k["front"], back=k["back"], claw=(i >= 3, i < 2))
    c = cv()
    polter_draw(c, p, ph=i, items=True, plate_at=False, flame=k["fl"])
    if i == 2:   # green smear trailing the throwing hand over the top
        for t in range(7):
            a = math.radians(-200 + t * 20)
            r = 9.0
            c.put(*P(2.5 + p.lean + r * math.cos(a), -16.5 + r * 0.9 * math.sin(a)), 'x' if t > 3 else 'V' if t > 1 else 'v')
    if i == THROW_RELEASE:   # burst of hex fire where the bolt leaves the hand
        hx_, hy_ = _T(p, *p.front)
        for (dx, dy, ch) in ((1, 0, 'y'), (2, 0, 'y'), (3, 0, 'x'), (1, -1, 'x'), (2, -1, 'x'), (1, 1, 'x'), (2, 1, 'V'),
                             (4, -1, 'V'), (4, 1, 'V'), (3, -2, 'v'), (3, 2, 'v'), (5, 0, 'V'), (0, -2, 'v'), (0, 2, 'v')):
            c.put(*P(hx_ + dx, hy_ + dy), ch)
    if i == 4:   # embers drifting off the spent hand
        hx_, hy_ = _T(p, *p.front)
        c.put(*P(hx_ + 3, hy_ - 3), 'x'); c.put(*P(hx_ + 5, hy_ - 5), 'v'); c.put(*P(hx_ + 1, hy_ - 4), 'V')
    return finish(c)


# ================================================================== sheets
BUILT = {}
FORMS = {
    "FormGleaner": dict(idle=gleaner_idle, run=gleaner_run, pose=gleaner_pose,
                        draw=lambda c, p, fr: gleaner_draw(c, p, frac=fr, ph=0.0 if fr >= 1 else None)),
    "FormBinder": dict(idle=binder_idle, run=binder_run, pose=binder_pose,
                       draw=lambda c, p, fr: binder_draw(c, p, frac=fr, ph=0)),
    "FormPoltergeist": dict(idle=polter_idle, run=polter_run, pose=polter_pose,
                            draw=lambda c, p, fr: polter_draw(c, p, frac=fr, ph=0), throw=polter_throw),
}
IDLE_DURS = [0.2] * 6          # vanilla ghost idle: 0.2 s per frame
RUN_DURS = [0.1] * 6           # vanilla ghost run: 0.1 s per frame
SPAWN_DURS = [0.1] * 10        # vanilla ghost spawn: 10 x 0.1 s (events keep their times)


def build_form(name, outdir):
    f = FORMS[name]
    idle = [f["idle"](i) for i in range(6)]
    run = [f["run"](i) for i in range(6)]
    spawn = spawn_frames(name, f["pose"], f["draw"])
    anims = [("Spawn", spawn, SPAWN_DURS), ("Idle", idle, IDLE_DURS), ("Run", run, RUN_DURS)]
    if "throw" in f:
        anims.append(("Throw", [f["throw"](i) for i in range(6)], THROW_DURS))
    img, man = pack(name, anims, CELL[0], CELL[1], ORIGIN, outdir, cols=8)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=6)
    BUILT[name] = {"cell": CELL, "feet": ORIGIN, "anims": [(a, len(fr), list(d)) for a, fr, d in anims], "img": img, "man": man}
    print("built %-18s cell %dx%d  %s" % (name, CELL[0], CELL[1], ", ".join("%s:%d" % (a, len(fr)) for a, fr, d in anims)))


# ================================================================== menu marks
PIP = ["LLV",
       "LVV",
       "VVD",
       "VDD"]
PIP_COL = {"L": (0xe8, 0xd8, 0xff, 255), "V": (0x9a, 0x6c, 0xe8, 255), "D": (0x5e, 0x36, 0xa8, 255)}


def build_menu(outdir):
    from PIL import Image
    import json
    # ModVioletPip: the god list's 3 x 4 pip (vanilla MenuItemDeityDefault is a plain white 3 x 4 block that the menu
    # tints), drawn as a faceted violet gem: lit top-left, shaded bottom-right
    img = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
    for y, row in enumerate(PIP):
        for x, ch in enumerate(row):
            img.putpixel((x, y), PIP_COL[ch])
    img.save(os.path.join(outdir, "ModVioletPip.png"))
    json.dump({"cellW": 3, "cellH": 4, "cols": 1, "anims": [{"name": "Idle", "frames": [0], "durations": [1.0]}]},
              open(os.path.join(outdir, "ModVioletPip.json"), "w"))
    _menu_preview(img.crop((0, 0, 3, 4)), os.path.join(outdir, "ModVioletPip_preview.png"))
    # ModBadgeGem: the 5 x 5 gem defined in tools/badge.py (validate.py checks the sheet against it)
    sys.path.insert(0, os.path.join(HERE, ".."))
    import badge
    img = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    for y, row in enumerate(badge.GEM):
        for x, ch in enumerate(row):
            if ch in badge.COL: img.putpixel((x, y), badge.COL[ch])
    img.save(os.path.join(outdir, "ModBadgeGem.png"))
    json.dump({"cellW": 5, "cellH": 5, "cols": 1, "anims": [{"name": "Idle", "frames": [0], "durations": [1.0]}]},
              open(os.path.join(outdir, "ModBadgeGem.json"), "w"))
    _menu_preview(img.crop((0, 0, 5, 5)), os.path.join(outdir, "ModBadgeGem_preview.png"))
    print("built ModVioletPip 3x4, ModBadgeGem 5x5")


def _menu_preview(im, path, scale=12):
    from PIL import Image
    bg = Image.new("RGBA", (im.width + 2, im.height + 2), (28, 26, 32, 255))
    bg.alpha_composite(im, (1, 1))
    bg.resize((bg.width * scale, bg.height * scale), Image.NEAREST).convert("RGB").save(path)


# ================================================================== per-player preview (simulates the ramp shader)
def ramps():
    from PIL import Image
    out = [None]
    for n in ("PaletteRed_91", "PaletteGreen_90", "PaletteYellow_121"):
        pth = os.path.join(DUMP, "tex", n + ".png")
        if not os.path.exists(pth): return None
        im = Image.open(pth).convert("RGB"); px = im.load()
        out.append({(x, 63 - y): px[x, y] for x in range(256) for y in range(64) if px[x, y] != (255, 0, 255)})
    return out


def as_player(img, ramp):
    """img recoloured through one player's ghost ramp (None = P1, the material without a ramp)."""
    if ramp is None: return img.copy()
    out = img.copy(); px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            c = px[x, y]
            if c[3] == 0: continue
            m = ramp.get(_slot(c))
            if m: px[x, y] = m + (c[3],)
    return out


MARK = "## Ghost forms in game (tools/sprites/ghost_forms.py)"


def write_timing(outdir):
    """Append (or replace) this script's section of TIMING.md (ghost_rigs.py writes the rest)."""
    path = os.path.join(outdir, "TIMING.md")
    old = open(path).read() if os.path.exists(path) else ""
    if MARK in old: old = old[:old.index(MARK)].rstrip() + "\n"
    hx_, hy_ = throw_hand()
    L = ["", MARK, "",
         "In-game bodies of the Gleaner, Binder and Poltergeist (the Wisp keeps the vanilla ghost). 54 x 50 cells = the",
         "vanilla ghost's own cell (AtlasEnemies ghost_p1_blue_*), drawn at the same place in it, so the cloned ghost prefab",
         "keeps its sprite anchor (BotCenter, offset (-1, -7.5)), HitZone and attack node. Origin (the ghost's transform) =",
         "cell pixel (%d, %d); sprite coords below are relative to it (x right, y up NEGATIVE)." % ORIGIN, "",
         "Player colours work exactly like the vanilla ghost: shroud/hair = the 4 vanilla shroud colours, head/hands = the 4",
         "vanilla skin yellows, eyes = the vanilla eye pink, all at alpha 158; GhostPack gives each form clip an atlas whose",
         "material is a copy of that player's ghost material (P1 SpriteTinted, P2-P4 SpritePaletted + their ramp), so P2-P4",
         "remap those colours to orange / green / tan like the vanilla ghost. Props (sack, chains, cutlery, hex fire) use",
         "colours every ramp leaves alone (ghost_forms.check_ramps asserts both).", "",
         "| Sheet | Anims (frames, total s) |", "|---|---|"]
    for n in FORMS:
        if n not in BUILT: continue
        L.append("| %s | %s |" % (n, ", ".join("%s %d, %.2f s" % (a, k, sum(d)) for a, k, d in BUILT[n]["anims"])))
    L += ["",
          "- Spawn 10 x 0.1 s = the vanilla P1BlueGhostSpawn timing, so its events keep their times (input multiply 0 / 0.4 /",
          "  0.5 / 0.8 s, sound 0.2 s, input on 0.7 s): pool 0-2, column 3, the hag tears free 4-5, her tools form 6-8, settle 9.",
          "- Idle 6 x 0.2 s loop (bob 0,-1,-1,0,1,1). Run 6 x 0.1 s loop (leaning, tail streaming). Dead = Idle (vanilla).",
          "- FormPoltergeist Throw 6 frames, %s s: wind-up 0-1 (hex fire kindled overhead), whip 2, RELEASE on frame %d"
          % ("/".join("%.2f" % d for d in THROW_DURS), THROW_RELEASE),
          "  (t = %.2f s): the hand is at (%.1f, %.1f) -> the hex bolt spawns there (node (0, 10) + offset (%.0f, %.0f) in code)."
          % (sum(THROW_DURS[:THROW_RELEASE]), hx_, hy_, round(hx_), round(-hy_ - 10)),
          "  Follow-through 4, recover 5; AnimRun at the end.", "",
          "## Menu marks", "",
          "| Sheet | Cell | Anims | Notes |", "|---|---|---|---|",
          "| ModVioletPip | 3 x 4 | Idle 1 | God list / origin / ghost-form pip for mod entries (vanilla MenuItemDeityDefault is a white 3 x 4 block the menu tints). |",
          "| ModBadgeGem | 5 x 5 | Idle 1 | The MOD gem Core's ModGem draws over mod art in the menus (pixels from tools/badge.py). |",
          ""]
    open(path, "w").write(old + "\n".join(L))
    print("appended ghost forms to", path)


def main():
    args = sys.argv[1:]
    only = None
    if "--only" in args:
        i = args.index("--only"); only = set(args[i + 1].split(",")); del args[i:i + 2]
    outdir = args[0] if args else DEFAULT_OUT
    os.makedirs(outdir, exist_ok=True)
    check_ramps()
    for n in FORMS:
        if only is None or n in only: build_form(n, outdir)
    if only is None or only & {"ModVioletPip", "ModBadgeGem"}:
        build_menu(CORE_OUT if outdir == DEFAULT_OUT else outdir)   # the pip and gem are Core's (art/core)
    if only is None:
        write_timing(outdir)


if __name__ == "__main__":
    main()
