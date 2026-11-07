"""GHOST FORMS IN GAME: the bodies the six new forms fly around as (same hag ghost, same 54 x 50 cell and anchor as
ghost_forms.py, so GhostPack.FormPrefab clones the player's ghost prefab and only swaps clips).

    python3 ghost_forms_v11.py [--out dir] [--only Name,Name]

  FormBanshee  Spawn 10, Idle 6, Run 6, Wail 6 (WAIL on 3: the ring leaves her mouth)   hair streaming, a wailing mouth
  FormSexton   Spawn 10, Idle 6, Run 6                                                  a gravedigger's spade on her shoulder, a lantern
  FormKindler  Spawn 10, Idle 6, Run 6, Ignite 6 (IGNITE on 3)                           a long lit taper, sparks
  FormMason    Spawn 10, Idle 6, Run 6, Rouse 6 (STRIKE on 3)                            a mallet and chisel, stone dust
  FormHexer    Spawn 10, Idle 6, Run 6, Throw 6 (RELEASE on 3, hand at the Poltergeist's) a poppet in one hand, a hex pin in the other
  FormMiser    Spawn 10, Idle 6, Run 6                                                  hunched over a strongbox, coins orbiting

Flesh = the vanilla ghost key colours (recoloured by each player's ramp); every prop colour is nudged until no player
ramp touches it (ghost_v11kit.make_safe), so props look the same for P1-P4.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ghost_forms as GF  # noqa: E402
import ghost_v11kit as KT  # noqa: E402
from ghosts_v2_kit import mute_rgb  # noqa: E402
from ghost_forms import Pose, hag, arm, _T, finish, spawn_frames, cv, ell, tube, line, P, ik, IDLE_DURS, RUN_DURS, SPAWN_DURS  # noqa: E402
from anim import pack, preview  # noqa: E402

OUT = [KT.OUT]
_KEYS = {}


def K(h, a=255):
    """A ramp-safe prop colour registered in the ghost palette; returns its key."""
    key = "#" + h + ("%02x" % a)
    if key not in GF.GPAL:
        GF.GPAL[key] = KT.make_safe(mute_rgb([KT.hx(h)], 0.6)[0]) + (a,)   # Crawl's muted palette, then ramp-safe
    return key


def R_(*hs):
    return [K(h) for h in hs]


MIST = R_("2a5a66", "4aa0b0", "8ae0ee", "d8fcff")
WOOD = R_("3a2214", "5e3a20", "865630", "ad7a46")
IRON = R_("26262e", "44464f", "6a6c74", "a2a4ac")
FLM = R_("a8301a", "e8701e", "ffc040", "fff0a0")
WAXC = R_("b4a07a", "dccaa0", "f2e6c4")
STONEC = R_("4c4e58", "6a6c76", "8e909a", "b4b6bc")
BURL = R_("4a3420", "76563a", "a07c52", "c8a474")
HEXC = R_("3a1850", "7a3aa8", "c47ae8", "f0d0ff")
GOLDC = R_("6a4a10", "a87818", "e0b02a", "ffe070", "fff8c8")
STEELC = R_("5a6070", "a0a8b8", "e8eef8")
PINR = K("d83a3a"); PINB = K("3a7ad8"); STITCHC = K("2a1a12"); BLACKC = K("0e0c10")
SOULG = R_("2c6a3a", "5ab86a", "a8f0a0")


def bob6(i):
    return [0, -1, -1, 0, 1, 1][i % 6]


def sway6(i):
    return [0, 0.6, 1, 0.6, 0, -0.6][i % 6]


# ================================================================== BANSHEE
def banshee_pose(i, gape=0):
    return Pose(bob=bob6(i), sway=sway6(i), hair=[0, 1, 2, 1, 0, -1][i % 6] + 1.0, face="wail",
                back=(9.0, -17.0 + bob6(i) * 0.3), front=(8.0, -13.5 + bob6(i) * 0.3), claw=(True, True), lean=0.4)


def wail_rings(c, x, y, ph, n=2, big=False):
    for k in range(n):
        r = 2.0 + ((ph + k * 3) % 6) * (1.2 if not big else 1.8)
        for j in range(-3, 4):
            a = j * 0.28
            col = MIST[3] if r < 5 else MIST[2] if r < 8 else MIST[1]
            c.put(*P(x + r * math.cos(a), y + r * 1.2 * math.sin(a)), col)


def banshee_draw(c, p, frac=1.0, ph=0, rings=1, big=False):
    hands = hag(c, p, wild=True)
    # hands cupped round her mouth on idle: front hand near the jaw, a long wail streaming out
    if frac >= 1 and rings:
        hx_, hy_ = _T(p, 9.5, -15.0)
        wail_rings(c, hx_, hy_, ph, n=rings, big=big)
    # long strands of hair streaming off her back (more than the plain hag)
    for k in range(3):
        x0, y0 = _T(p, -1.5, -17.5 + k * 1.2)
        L = 6 + k * 2 + p.hair
        line(c, x0, y0, x0 - L, y0 + 2 + k + math.sin(ph + k) * 1.2, 'b' if k else 'a')
        c.put(*P(x0 - L - 1, y0 + 3 + k), '2')


def banshee_idle(i):
    p = banshee_pose(i)
    c = cv(); banshee_draw(c, p, ph=i)
    return finish(c)


def banshee_run(i):
    p = Pose(bob=[0, -1, -2, -1, 0, 1][i] - 1, lean=2.8, sway=1.0 + 0.3 * (i % 3), tail=1.2, hair=2.4, face="wail",
             back=(-4.0, -21.0), front=(10.0, -18.0), claw=(True, True))
    c = cv(); banshee_draw(c, p, ph=i, rings=0)
    return finish(c)


BANSHEE_WAIL = 3


def banshee_wail(i):
    keys = [dict(lean=-1.0, bob=0, front=(6.0, -26.0), back=(-4.0, -26.0), hair=0.0, rings=0),
            dict(lean=-2.0, bob=-1, front=(4.0, -28.0), back=(-6.0, -27.0), hair=-1.0, rings=0),
            dict(lean=0.5, bob=-2, front=(10.0, -26.0), back=(-8.0, -24.0), hair=2.0, rings=1),
            dict(lean=2.0, bob=-2, front=(12.0, -22.0), back=(-10.0, -22.0), hair=3.5, rings=3),
            dict(lean=1.5, bob=-1, front=(11.0, -20.0), back=(-9.0, -21.0), hair=3.0, rings=2),
            dict(lean=0.6, bob=0, front=(6.0, -24.0), back=(-3.0, -24.0), hair=1.0, rings=1)]
    k = keys[i]
    p = Pose(bob=k["bob"], lean=k["lean"], hair=k["hair"], face="wail", eyes="glow" if i < 3 else "angry",
             front=k["front"], back=k["back"], claw=(True, True), sway=-0.5 + i * 0.2)
    c = cv(); banshee_draw(c, p, ph=i, rings=k["rings"], big=i >= 3)
    if i == BANSHEE_WAIL:   # the first ring bursting out all round her
        for j in range(16):
            a = 2 * math.pi * j / 16
            c.put(*P(2 + 14 * math.cos(a), -14 + 7 * math.sin(a)), MIST[3] if j % 2 else MIST[2])
    return finish(c)


# ================================================================== SEXTON
def spade(c, sx, sy, ang, frac=1.0):
    """A gravedigger's spade: a wooden haft from (sx, sy) along ang, an iron blade at the far end."""
    if frac <= 0: return
    a = math.radians(ang)
    L = 14
    ex, ey = sx + L * math.cos(a), sy + L * math.sin(a)
    for k, (x, y) in enumerate(GF.line_px(*P(sx, sy), *P(ex, ey))):
        c.put(x, y, WOOD[3] if k % 3 else WOOD[2])
    # T-grip at the near end
    nx, ny = -math.sin(a), math.cos(a)
    c.put(*P(sx - math.cos(a) + nx, sy - math.sin(a) + ny), WOOD[1]); c.put(*P(sx - math.cos(a) - nx, sy - math.sin(a) - ny), WOOD[1])
    if frac < 1: return
    # blade: a spade-shaped plate
    for t in range(5):
        w = [1.6, 2.0, 2.0, 1.6, 0.8][t]
        bx, by = ex + t * math.cos(a), ey + t * math.sin(a)
        for s in range(-int(w * 2), int(w * 2) + 1):
            q = s / 2.0
            c.put(*P(bx + nx * q, by + ny * q), IRON[3] if q < 0 else IRON[2])
    c.put(*P(ex + 4.6 * math.cos(a), ey + 4.6 * math.sin(a)), IRON[1])


def lantern(c, x, y, ph, frac=1.0):
    if frac <= 0: return
    line(c, x, y, x, y + 2, IRON[2])
    for yy in range(3, 7):
        for xx in (-1, 0, 1):
            edge = abs(xx) == 1 or yy in (3, 6)
            c.put(*P(x + xx, y + yy), IRON[1] if edge else (SOULG[2] if (ph + yy) % 3 else SOULG[1]))
    c.put(*P(x, y + 4), SOULG[2])


def sexton_pose(i):
    return Pose(bob=bob6(i), sway=sway6(i), hair=[0, 1, 1, 0, -1, -1][i % 6], face="calm", eyes="glow",
                back=(-3.0, -18.5 + bob6(i) * 0.3), front=(8.0, -9.0 + bob6(i) * 0.3), claw=(False, False), lean=0.3)


def sexton_draw(c, p, frac=1.0, ph=0, run=False):
    def behind(c_, p_):
        # the spade rests on her far shoulder, the blade sticking up behind her head
        bx, by = _T(p_, 4.0, -12.0)
        spade(c_, bx, by, -128 if not run else -150, frac)
    hands = hag(c, p, behind=behind)
    fh = hands.get("front")
    if fh: lantern(c, fh[0] + 0.5, fh[1], ph, frac)


def sexton_idle(i):
    c = cv(); sexton_draw(c, sexton_pose(i), ph=i); return finish(c)


def sexton_run(i):
    p = Pose(bob=[0, -1, -2, -1, 0, 1][i] - 1, lean=2.4, sway=1.0 + 0.2 * (i % 3), tail=1.15, hair=1.6, face="calm",
             back=(1.0, -19.0), front=(11.0, -10.0 + (i % 2)), claw=(False, False))
    c = cv(); sexton_draw(c, p, ph=i, run=True); return finish(c)


# ================================================================== KINDLER
def taper(c, hx_, hy_, ang, ph, frac=1.0, size=1):
    """A long wax taper held at (hx_, hy_), pointing ang, burning at its tip."""
    if frac <= 0: return (hx_, hy_)
    a = math.radians(ang)
    L = 8
    tx, ty = hx_ + L * math.cos(a), hy_ + L * math.sin(a)
    for k, (x, y) in enumerate(GF.line_px(*P(hx_ - 2 * math.cos(a), hy_ - 2 * math.sin(a)), *P(tx, ty))):
        c.put(x, y, WAXC[2] if k % 2 else WAXC[1])
    if frac < 1: return (tx, ty)
    flick = [0, 1, 0, -1][ph % 4]
    c.put(*P(tx, ty - 1), FLM[3]); c.put(*P(tx + flick * 0.5, ty - 2), FLM[2]); c.put(*P(tx + flick, ty - 3), FLM[1])
    c.put(*P(tx - 1, ty - 1), FLM[1]); c.put(*P(tx + 1, ty - 1), FLM[2])
    if size >= 2:
        for (dx, dy, col) in ((0, -4, FLM[1]), (-1, -2, FLM[2]), (1, -3, FLM[2]), (flick, -5, FLM[0]), (2, -2, FLM[1])):
            c.put(*P(tx + dx, ty + dy), col)
    # sparks
    for k in range(2 if size < 2 else 4):
        sx, sy = tx + [-2, 3, 1, -3][(ph + k) % 4], ty - 4 - ((ph + k * 2) % 4)
        c.put(*P(sx, sy), FLM[2] if k % 2 else FLM[3])
    return (tx, ty)


def kindler_pose(i):
    return Pose(bob=bob6(i), sway=sway6(i), hair=[0, 1, 1, 0, -1, -1][i % 6], face="hum", eyes="glow",
                back=(1.0, -20.5 + bob6(i) * 0.3), front=(9.5, -15.5 + bob6(i) * 0.3), claw=(False, True), lean=0.6)


def kindler_draw(c, p, frac=1.0, ph=0, ang=-60, size=1):
    hands = hag(c, p)
    fh = hands.get("front")
    if fh: taper(c, fh[0], fh[1], ang, ph, frac, size)


def kindler_idle(i):
    c = cv(); kindler_draw(c, kindler_pose(i), ph=i, ang=-62 + [0, 3, 6, 3, 0, -3][i]); return finish(c)


def kindler_run(i):
    p = Pose(bob=[0, -1, -2, -1, 0, 1][i] - 1, lean=2.6, sway=1.0 + 0.3 * (i % 3), tail=1.15, hair=1.6, face="hum",
             back=(9.0, -18.0), front=(12.0, -13.0), claw=(False, True))
    c = cv(); kindler_draw(c, p, ph=i, ang=-20); return finish(c)


KINDLER_IGNITE = 3


def kindler_ignite(i):
    keys = [dict(lean=-0.5, front=(6.0, -22.0), ang=-90, size=1), dict(lean=-1.5, front=(3.0, -22.0), ang=-115, size=2),
            dict(lean=0.5, front=(10.0, -22.0), ang=-40, size=2), dict(lean=2.6, front=(12.0, -14.0), ang=-10, size=2),
            dict(lean=2.0, front=(13.0, -12.0), ang=10, size=1), dict(lean=0.8, front=(10.0, -15.0), ang=-50, size=1)]
    k = keys[i]
    p = Pose(bob=[0, -1, -1, 0, 0, 0][i], lean=k["lean"], face="grit" if i in (2, 3) else "hum", eyes="angry" if i in (2, 3) else "glow",
             front=k["front"], back=(-2.0, -21.0), claw=(False, True), hair=1.0)
    c = cv(); kindler_draw(c, p, ph=i, ang=k["ang"], size=k["size"])
    if i == KINDLER_IGNITE:   # a tongue of fire flung forward
        fx, fy = _T(p, *k["front"])
        for t in range(5):
            if fx + 6 + t <= 25: c.put(*P(fx + 6 + t, fy - 3 + (t % 2)), FLM[3 - min(3, t // 2)])
    return finish(c)


# ================================================================== MASON
def mallet(c, x, y, ang, frac=1.0):
    if frac <= 0: return
    a = math.radians(ang)
    ex, ey = x + 6 * math.cos(a), y + 6 * math.sin(a)
    for k, (px_, py_) in enumerate(GF.line_px(*P(x, y), *P(ex, ey))):
        c.put(px_, py_, WOOD[2] if k % 2 else WOOD[3])
    if frac < 1: return
    nx, ny = -math.sin(a), math.cos(a)
    for s in range(-2, 3):
        for t in range(0, 3):
            c.put(*P(ex + nx * s + math.cos(a) * t, ey + ny * s + math.sin(a) * t), WOOD[1] if s > 0 else WOOD[2] if t else WOOD[3])


def chisel(c, x, y, ang, frac=1.0):
    if frac <= 0: return
    a = math.radians(ang)
    for k in range(6):
        c.put(*P(x + k * math.cos(a), y + k * math.sin(a)), IRON[3] if k > 3 else IRON[2] if k > 1 else WOOD[2])


def dust(c, x, y, ph, n=3):
    for k in range(n):
        dx, dy = [(-3, -2), (2, -3), (4, 0), (-1, 2)][(ph + k) % 4]
        c.put(*P(x + dx, y + dy), STONEC[3] if k % 2 else STONEC[2])


def mason_pose(i):
    return Pose(bob=bob6(i), sway=sway6(i), hair=[0, 1, 1, 0, -1, -1][i % 6], face="calm", eyes="glow",
                back=(6.5, -19.5 + bob6(i) * 0.4), front=(9.0, -12.0), claw=(False, False), lean=0.5)


def mason_draw(c, p, frac=1.0, ph=0, mal=-60, chi=20, d=0):
    hands = hag(c, p)
    bh, fh = hands.get("back"), hands.get("front")
    if bh: mallet(c, bh[0], bh[1], mal, frac)
    if fh: chisel(c, fh[0], fh[1], chi, frac)
    if d and fh: dust(c, fh[0] + 5, fh[1] + 1, ph, d)


def mason_idle(i):
    c = cv(); mason_draw(c, mason_pose(i), ph=i, mal=-60 + [0, -8, -15, -8, 0, 6][i], d=1 if i in (4, 5) else 0)
    return finish(c)


def mason_run(i):
    p = Pose(bob=[0, -1, -2, -1, 0, 1][i] - 1, lean=2.4, sway=1.0 + 0.2 * (i % 3), tail=1.15, hair=1.6, face="calm",
             back=(7.0, -21.0), front=(12.0, -13.0), claw=(False, False))
    c = cv(); mason_draw(c, p, ph=i, mal=-100, chi=10); return finish(c)


MASON_STRIKE = 3


def mason_rouse(i):
    mal = [-80, -130, -160, 30, 10, -40][i]
    p = Pose(bob=[0, -1, -2, 0, 1, 0][i], lean=[0, -1, -1.5, 2, 1.5, 0.5][i], face="grit" if i in (2, 3) else "calm",
             eyes="angry" if i == 3 else "glow", back=[(6, -22), (3, -25), (1, -26), (10, -16), (10, -15), (7, -19)][i],
             front=(10.0, -12.0), claw=(False, False), hair=1.0)
    c = cv(); mason_draw(c, p, ph=i, mal=mal, chi=20, d=4 if i in (3, 4) else 0)
    if i == MASON_STRIKE:   # sparks off the chisel
        fx, fy = _T(p, 10.0, -12.0)
        for (dx, dy) in ((2, -3), (4, -2), (5, -4), (3, -5)):
            c.put(*P(fx + dx, fy + dy), FLM[2])
    return finish(c)


# ================================================================== HEXER
def poppet_small(c, x, y, ph, frac=1.0):
    """A tiny voodoo poppet held up (~5 x 7) with a pin through it."""
    if frac <= 0: return
    ell(c, x, y - 2, 2.2, 2.0, BURL, bias=0.2)
    ell(c, x, y + 1.6, 1.5, 1.7, BURL, bias=0.1)
    c.put(*P(x, y - 2), BLACKC); c.put(*P(x + 1, y - 2), K("f4f2ea")); c.put(*P(x, y - 0.6), STITCHC); c.put(*P(x + 1, y - 0.6), STITCHC)
    c.put(*P(x - 2, y + 2), BURL[1]); c.put(*P(x + 2, y + 2), BURL[2])
    if frac >= 1:
        line(c, x - 3, y - 4, x + 1, y - 1, STEELC[1]); c.put(*P(x - 3, y - 4), PINR)
        c.put(*P(x - 1 + (ph % 2), y - 5), HEXC[2])


def hex_pin_held(c, x, y, ang, ph, glow=False):
    a = math.radians(ang)
    for k in range(6):
        c.put(*P(x + k * math.cos(a), y + k * math.sin(a)), STEELC[2] if k > 2 else STEELC[1])
    c.put(*P(x - math.cos(a), y - math.sin(a)), PINB)
    if glow:
        tx, ty = x + 6 * math.cos(a), y + 6 * math.sin(a)
        c.put(*P(tx, ty), HEXC[3]); c.put(*P(tx + 1, ty), HEXC[2]); c.put(*P(tx, ty - 1), HEXC[2])


def hexer_pose(i):
    return Pose(bob=bob6(i), sway=sway6(i), hair=[0, 1, 2, 1, 0, -1][i % 6], face="grit", eyes="glow",
                back=(12.0, -21.0 + bob6(i) * 0.3), front=(8.5, -11.0 + bob6(i) * 0.3), claw=(False, False), lean=0.6)


def hexer_draw(c, p, frac=1.0, ph=0, pin_ang=-30, pin=True, glow=False, flame=None):
    hands = hag(c, p)
    bh, fh = hands.get("back"), hands.get("front")
    if bh: poppet_small(c, bh[0], bh[1] - 3, ph, frac)
    if fh and pin and frac >= 1: hex_pin_held(c, fh[0], fh[1], pin_ang, ph, glow)


def hexer_idle(i):
    c = cv(); hexer_draw(c, hexer_pose(i), ph=i, pin_ang=-55 + [0, -6, -12, -6, 0, 6][i], glow=i in (2, 3)); return finish(c)


def hexer_run(i):
    p = Pose(bob=[0, -1, -2, -1, 0, 1][i] - 1, lean=2.6, sway=1.0 + 0.3 * (i % 3), tail=1.15, hair=1.8, face="grit",
             back=(13.0, -20.0), front=(10.0, -11.0), claw=(False, False))
    c = cv(); hexer_draw(c, p, ph=i, pin_ang=0); return finish(c)


HEXER_RELEASE = GF.THROW_RELEASE


def hexer_throw(i):
    """Same arm path as the Poltergeist's Throw, so the pin leaves the hand at the same point (code offset (12, -1))."""
    keys = [dict(lean=-1.0, bob=0, front=(-1.0, -24.0), ang=-100, glow=True),
            dict(lean=-2.2, bob=-1, front=(-5.0, -22.5), ang=-150, glow=True),
            dict(lean=1.4, bob=-1, front=(7.0, -26.0), ang=-60, glow=True),
            dict(lean=3.0, bob=0, front=(13.0, -8.5), ang=0, glow=False),
            dict(lean=2.4, bob=1, front=(10.0, -4.5), ang=40, glow=False),
            dict(lean=1.2, bob=0, front=(10.0, -15.0), ang=-30, glow=False)]
    k = keys[i]
    p = Pose(bob=k["bob"], lean=k["lean"], hair=1.5 if i < 3 else -1.0, face="grit", eyes="angry",
             front=k["front"], back=(-4.0, -17.0), claw=(False, False))
    c = cv(); hexer_draw(c, p, ph=i, pin_ang=k["ang"], pin=i != HEXER_RELEASE and i != 4, glow=k["glow"])
    if i == HEXER_RELEASE:
        hx_, hy_ = _T(p, *p.front)
        for (dx, dy, col) in ((1, 0, HEXC[3]), (2, 0, HEXC[3]), (3, 0, HEXC[2]), (2, -1, HEXC[2]), (2, 1, HEXC[2]), (4, -1, HEXC[1]),
                              (4, 1, HEXC[1])):
            c.put(*P(hx_ + dx, hy_ + dy), col)
    return finish(c)


# ================================================================== MISER
def strongbox(c, x, y, frac=1.0, lid=0.0):
    if frac <= 0: return
    for yy in range(0, 5):
        for xx in range(-4, 5):
            edge = xx in (-4, 4) or yy == 4
            c.put(*P(x + xx, y + yy), WOOD[1] if edge else WOOD[3] if yy == 0 else WOOD[2])
    for xx in (-2, 2):
        for yy in range(0, 5): c.put(*P(x + xx, y + yy), IRON[2])
    if frac < 1: return
    c.put(*P(x, y + 2), GOLDC[3]); c.put(*P(x, y + 3), GOLDC[1])
    ly = y - 1 - int(round(lid * 2))
    for xx in range(-4, 5): c.put(*P(x + xx, ly), WOOD[3] if xx < 2 else WOOD[2])
    if lid > 0:
        for xx in range(-3, 4, 2): c.put(*P(x + xx, y - 1), GOLDC[3] if xx % 4 else GOLDC[4])


def coin_px(c, x, y, ph):
    w = [1, 1, 0, 1][ph % 4]
    for dx in range(-w, w + 1): c.put(*P(x + dx, y), GOLDC[3] if dx <= 0 else GOLDC[2])
    c.put(*P(x, y - 1) if w else P(x, y + 1), GOLDC[4] if w else GOLDC[1])


def miser_pose(i):
    return Pose(bob=bob6(i) * 0.5, sway=sway6(i), hair=[0, 1, 1, 0, -1, -1][i % 6] * 0.5, face="hum", eyes="glow",
                back=(7.5, -10.5), front=(8.5, -9.5), claw=(True, True), lean=1.8)


def miser_draw(c, p, frac=1.0, ph=0, coins=3, lid=0.0):
    def behind(c_, p_):
        for k in range(coins):
            a = (ph / 6.0 + k / float(max(1, coins))) * 2 * math.pi
            if math.sin(a) < 0: coin_px(c_, -1 + 11 * math.cos(a), -14 + 3.5 * math.sin(a) + p_.bob, ph + k)
    hands = hag(c, p, behind=behind if frac >= 1 else None)
    bx, by = _T(p, 8.0, -9.0)
    strongbox(c, bx + 1, by + 1, frac, lid)
    fh = hands.get("front")
    if fh: c.put(*P(fh[0], fh[1]), 'k')
    if frac >= 1:
        for k in range(coins):
            a = (ph / 6.0 + k / float(max(1, coins))) * 2 * math.pi
            if math.sin(a) >= 0: coin_px(c, -1 + 11 * math.cos(a), -14 + 3.5 * math.sin(a) + p.bob, ph + k)


def miser_idle(i):
    c = cv(); miser_draw(c, miser_pose(i), ph=i, lid=0.5 if i in (2, 3) else 0.0); return finish(c)


def miser_run(i):
    p = Pose(bob=[0, -1, -2, -1, 0, 1][i] - 1, lean=3.0, sway=1.0 + 0.3 * (i % 3), tail=1.15, hair=1.4, face="hum",
             back=(9.0, -10.0), front=(10.0, -9.0), claw=(True, True))
    c = cv(); miser_draw(c, p, ph=i, coins=2); return finish(c)


# ================================================================== sheets
FORMS = {
    "FormBanshee": dict(idle=banshee_idle, run=banshee_run, pose=banshee_pose,
                        draw=lambda c, p, fr: banshee_draw(c, p, frac=fr, rings=1 if fr >= 1 else 0),
                        extra=("Wail", banshee_wail, [0.08, 0.1, 0.08, 0.08, 0.12, 0.12])),
    "FormSexton": dict(idle=sexton_idle, run=sexton_run, pose=sexton_pose, draw=lambda c, p, fr: sexton_draw(c, p, frac=fr)),
    "FormKindler": dict(idle=kindler_idle, run=kindler_run, pose=kindler_pose, draw=lambda c, p, fr: kindler_draw(c, p, frac=fr),
                        extra=("Ignite", kindler_ignite, [0.08, 0.08, 0.06, 0.08, 0.1, 0.1])),
    "FormMason": dict(idle=mason_idle, run=mason_run, pose=mason_pose, draw=lambda c, p, fr: mason_draw(c, p, frac=fr),
                      extra=("Rouse", mason_rouse, [0.08, 0.1, 0.08, 0.06, 0.1, 0.12])),
    "FormHexer": dict(idle=hexer_idle, run=hexer_run, pose=hexer_pose, draw=lambda c, p, fr: hexer_draw(c, p, frac=fr),
                      extra=("Throw", hexer_throw, GF.THROW_DURS)),
    "FormMiser": dict(idle=miser_idle, run=miser_run, pose=miser_pose, draw=lambda c, p, fr: miser_draw(c, p, frac=fr, coins=3 if fr >= 1 else 0)),
}
BUILT = {}


def build_form(name):
    f = FORMS[name]
    idle = [f["idle"](i) for i in range(6)]
    run = [f["run"](i) for i in range(6)]
    spawn = spawn_frames(name, f["pose"], f["draw"])
    anims = [("Spawn", spawn, SPAWN_DURS), ("Idle", idle, IDLE_DURS), ("Run", run, RUN_DURS)]
    if "extra" in f:
        an, fn, du = f["extra"]
        anims.append((an, [fn(i) for i in range(6)], du))
    img, man = pack(name, anims, GF.CELL[0], GF.CELL[1], GF.ORIGIN, OUT[0], cols=8)
    preview(img, man, os.path.join(OUT[0], name + "_preview.png"), scale=6)
    BUILT[name] = {"anims": [(a, len(fr), list(d)) for a, fr, d in anims], "img": img, "man": man}
    print("built %-14s cell %dx%d  %s" % (name, GF.CELL[0], GF.CELL[1], ", ".join("%s:%d" % (a, len(fr)) for a, fr, d in anims)))


def check_safe():
    for k, v in GF.GPAL.items():
        if k.startswith("#"):
            assert KT.ramp_safe(v), "prop colour %s would be recoloured" % k


def main():
    args = sys.argv[1:]
    only = None
    if "--only" in args:
        i = args.index("--only"); only = set(args[i + 1].split(",")); del args[i:i + 2]
    if "--out" in args:
        i = args.index("--out"); OUT[0] = args[i + 1]; del args[i:i + 2]; os.makedirs(OUT[0], exist_ok=True)
    for n in FORMS:
        if only is None or n in only: build_form(n)
    check_safe()


if __name__ == "__main__":
    main()
