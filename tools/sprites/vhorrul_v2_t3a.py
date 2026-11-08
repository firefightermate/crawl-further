"""Vhorrul tier 3, first half: Tallow Colossus, Pyre Warden, Tallow Renderer, Wick Hag, Candle Wyrm, Fuse Scorpion.
Built through vhorrul_v2_rigs.py. T3 idle limit 42 x 40."""
import math
from vhorrul_v2_rigs import (Rig, Xf, ik, lerp, flame, candle, smoke_curl, drip, floor_pool, ember_dots, glow_ring,
                             sheet, tail_anims, line_px, scaled)
from vhorrul_v2_t1 import bez, dust
from vhorrul_v2_t2 import biped, boots, walk_feet, swipe_arc, worm_path


def legs2(r, hip, feet, mat, rad=(2.0, 1.6), ln=(4.0, 4.0), z=0.0):
    for k, (fx, fy) in enumerate(feet):
        near = k == 1
        hp = (hip[0] + (1.2 if near else -1.2), hip[1])
        kx, ky = ik(hp[0], hp[1], fx, fy - 1.0, ln[0], ln[1], bend=1)
        r.tube([hp, (kx, ky), (fx, fy - 1.0)], [rad[0], rad[1], rad[1]], mat, z + (0.6 if near else -1.0), bias=0.0 if near else -0.3)


# ================================================================== TALLOW COLOSSUS
def colossus(layers=0, lean=0.0, crouch=0.0, feet=((-4.0, 0.0), (4.0, 0.0)), fist=(10.0, -12.0), fist2=(-8.0, -11.0),
             ph=0, extra=None, prone=0.0, tilt=0.0, dead=False):
    """A hunched giant of poured and re-poured tallow: broad and top-heavy, an old wick burning out of its skull, candles
    half sunk in its shoulders, fists like dripping lumps. layers (0-3): soaked-up wax, each one bigger with sagging
    sheets; prone (0-1): toppled flat on its face."""
    r = Rig()
    k = 1.0 + 0.1 * layers
    T = Xf(tilt, (0.0, 0.0))
    if prone > 0.5:
        # face down along the floor, pushing itself up
        lift = (prone - 1.0) * -6.0
        r.ell(0.0, -4.5 - lift * 0.3, 13.0 * k, 4.6 * k, "tallow", 0.0)
        r.ell(-2.0, -7.0 - lift * 0.3, 9.0 * k, 2.6 * k, "tallow", 0.2, clip=lambda x, y: y < -6.0 - lift * 0.3)
        r.ell(13.0 * k, -3.6 - lift * 0.5, 3.6, 3.2, "tallow", 0.5)
        flame(r, 15.5 * k, -6.0 - lift * 0.5, 3.0, ph, "fire", 1.0, lean=2.0)
        for x in (-8, -3, 4):
            candle(r, x * k, -8.2 * k - lift * 0.3, 2.4, 2.0, z=0.6, ph=ph + x, flh=2.6)
        for s in (-1, 1):
            r.ell(12.0 * k + s * 2, -1.4, 3.0 * k, 2.0, "tallow", 1.0 if s > 0 else -1.0)
        if extra: extra(r)
        return r.resolve()
    hip = (lean * 0.3, -8.5 * k + crouch)
    legs2(r, hip, feet, "tallow", (2.4 * k, 2.0 * k), (4.5 * k, 4.5 * k))
    for (fx, fy) in feet:
        drip(r, fx + 1.2, fy - 2.6, 1.6, "bees", 0.7)
    cx, cy = hip[0] + lean, hip[1] - 9.0 * k
    # the body: a top-heavy mound with a hunch, skins of newer tallow poured over it
    r.ell(cx - 1.0, cy, 10.0 * k, 10.0 * k, "tallow", 0.0, ang=tilt)
    r.ell(cx - 2.0, cy - 3.0 * k, 8.0 * k, 6.0 * k, "grease", 0.2, clip=lambda x, y: y < cy - 2.0 * k + 0.25 * (x - cx))
    # wax strata: the poured layers show as yellowed bands round the body, one more per soaked-up layer
    for i in range(2 + layers):
        y0 = cy + (1.5 + 2.4 * i) * k
        w = 9.0 * k * math.sqrt(max(0.05, 1.0 - ((y0 - cy) / (10.0 * k)) ** 2))
        r.polyline([(cx - 1.0 - w + 0.6, y0 - 0.6), (cx - 1.0, y0 + 0.4), (cx - 1.0 + w - 0.6, y0 - 0.2)], "bees", 0.31, tone=2)
        r.polyline([(cx - 1.0 - w + 1.2, y0 - 1.4), (cx - 1.0, y0 - 0.6), (cx - 1.0 + w - 1.6, y0 - 1.2)], "tallow", 0.31, tone=4)
    for i in range(layers):   # the soaked-up layers sag off it in sheets
        for dx in (-7, -2, 4):
            drip(r, cx + dx * k - i, cy + 4 * k + i * 1.5, 2.0 + i, "bees", 0.32 + 0.01 * i)
    for (dx, dy) in ((-5, -6), (-2, -8), (2, -4)):   # the melt sheen
        r.dot(cx + dx * k, cy + dy * k, "white", 3, 0.4)
    for dx, ln in ((-6, 3.0), (-1, 4.0), (5, 2.0)):
        drip(r, cx + dx * k, cy - 1.0 * k, ln, "tallow", 0.25)
    # head sunk between the shoulders: no neck, two ember pits, the old wick burning out of its skull
    hx, hy = cx + 5.0 * k, cy - 7.5 * k
    r.ell(hx, hy, 3.4, 3.0, "tallow", 0.8)
    r.dot(hx + 1.0, hy - 0.4, "soot", 0, 0.9); r.dot(hx + 2.4, hy - 0.2, "soot", 0, 0.9)
    r.dot(hx + 1.0, hy - 0.6, "ember", 3, 0.91); r.dot(hx + 2.4, hy - 0.4, "ember", 2, 0.91)
    r.line(hx + 0.6, hy + 1.6, hx + 2.8, hy + 1.4, "soot", 0.9, tone=1)
    r.line(hx - 0.4, hy - 3.0, hx - 0.6, hy - 4.4, "wick", 0.95, tone=2)
    flame(r, hx - 0.6, hy - 4.6, 4.0 + 0.4 * layers, ph, "fire", 1.0)
    # candles half sunk in the shoulders
    for j, (dx, dy, h) in enumerate(((-6.5, -6.0, 3.0), (-3.0, -8.5, 2.2), (1.0, -9.0, 3.4))):
        candle(r, cx + dx * k, cy + dy * k, h, 2.0, z=0.6, ph=ph + j, flh=2.6)
    # arms: thick tubes ending in dripping lumps of fists
    shn, shf = (cx + 6.0 * k, cy - 3.0 * k), (cx - 7.0 * k, cy - 3.0 * k)
    for near, s, (tx, ty) in ((False, shf, fist2), (True, shn, fist)):
        ex, ey = ik(s[0], s[1], tx, ty, 6.0 * k, 5.0 * k, bend=1 if near else -1)
        z = 2.0 if near else -1.2
        r.tube([s, (ex, ey), (tx, ty)], [2.4 * k, 2.0 * k, 2.0 * k], "tallow", z, bias=0.0 if near else -0.3)
        r.ell(tx, ty, 3.0 * k, 2.8 * k, "tallow", z + 0.05, bias=0.0 if near else -0.3)
        drip(r, tx - 1.0, ty + 2.6 * k, 2.0, "bees", z + 0.06)
        r.dot(tx - 1.2, ty - 1.4 * k, "white", 3, z + 0.07)
    if extra: extra(r)
    return r.resolve()


def body_shadow(r, length, k=1.0, tone=1):
    """The body-shaped shadow on the floor ahead (Topple's tell): its length is where it will land."""
    p = r.part(False, -6.0)
    for x in range(4, int(4 + length)):
        t = (x - 4) / float(length)
        hw = 2.5 + 2.0 * math.sin(math.pi * min(1.0, t * 1.2))
        for y in range(int(-hw * 0.5), int(hw * 0.5) + 1):
            r.put(x, -1.5 + y, -6.0, "soot", 0.5, p, tone)


@scaled(1.1)
def colossus_sheet(outdir):
    Co = colossus
    anims = []
    for L in range(4):
        idle = [Co(layers=L, crouch=[0, 0.4, 0.7, 0.4][i], fist=(10.0 + L, -10.0 + [0, 0.4, 0.7, 0.4][i] - L), ph=i) for i in range(4)]
        run = []
        for i in range(6):
            f = walk_feet(i, 6, 3.4, 1.6, 8.0)
            run.append(Co(layers=L, feet=f, lean=1.0, crouch=0.8 * abs(math.sin(i / 6.0 * math.tau)),
                          fist=(10.5 + L + f[0][0] * 0.6, -10.0 - L), fist2=(-8.0 - L + f[1][0] * 0.6, -10.0 - L), ph=i))
        suffix = "" if L == 0 else str(L)
        anims += [("Idle" + suffix, idle, [0.2, 0.17, 0.2, 0.17]), ("Run" + suffix, run, [0.1] * 6)]
        if L == 0: idle0 = idle
    fists = [Co(fist=(6.0, -16.0), fist2=(-8.0, -12.0), lean=-1.0, ph=0),
             Co(fist=(3.0, -19.0), fist2=(-6.0, -12.0), lean=-1.8, ph=1),
             Co(fist=(17.0, -9.0), fist2=(-5.0, -14.0), lean=2.0, feet=((-4.0, 0), (6.0, 0)), ph=2,
                extra=lambda r: swipe_arc(r, 6.0, -14.0, 13.0, -60, 20, "tallow", 4.8, 2, 4)),
             Co(fist=(8.0, -12.0), fist2=(9.0, -18.0), lean=0.5, ph=3),
             Co(fist=(6.0, -12.0), fist2=(17.0, -8.0), lean=2.2, feet=((-4.0, 0), (6.0, 0)), ph=4,
                extra=lambda r: swipe_arc(r, 5.0, -12.0, 13.0, -40, 30, "tallow", 4.8, 2, 4)),
             Co(fist=(9.0, -11.0), fist2=(-4.0, -12.0), lean=0.8, ph=5), Co(ph=0)]
    # Topple: rears back 0.8 s over its shadow, falls flat (impact f1 of Fall), lies, pushes up
    rear = [Co(lean=-2.0, fist=(4.0, -24.0), fist2=(-6.0, -24.0), tilt=-6, ph=i, extra=(lambda k: lambda r: body_shadow(r, 22 + 2 * k))(i))
            for i in range(4)]
    fall = [Co(lean=4.0, fist=(18.0, -14.0), fist2=(14.0, -16.0), tilt=24, ph=0, extra=lambda r: body_shadow(r, 28, tone=0)),
            Co(prone=1.0, ph=1, extra=lambda r: (dust(r, 22, 0, 0, 1.6), dust(r, 6, 0, 0, 1.6))),
            Co(prone=1.0, ph=2, extra=lambda r: dust(r, 22, 0, 1, 1.6))]
    prone = [Co(prone=1.0, ph=i) for i in range(2)]
    getup = [Co(prone=0.7, ph=0), Co(prone=0.4, ph=1), Co(crouch=3.0, lean=2.0, fist=(10.0, -4.0), fist2=(4.0, -4.0), ph=2),
             Co(crouch=1.0, lean=1.0, ph=3)]
    knock = Co(lean=-2.0, tilt=-8, fist=(6.0, -8.0), fist2=(-11.0, -14.0), ph=2)
    d0 = Co(lean=-2.5, tilt=-10, fist=(4.0, -20.0), fist2=(-10.0, -20.0), ph=1)
    d1 = Co(prone=1.0, ph=3)
    d2 = colossus_corpse()
    anims += [("Fists", fists, [0.1, 0.1, 0.05, 0.12, 0.05, 0.12, 0.12]),
              ("Rear", rear, [0.2] * 4), ("Fall", fall, [0.06, 0.08, 0.1]), ("Prone", prone, [0.25, 0.25]),
              ("GetUp", getup, [0.12, 0.12, 0.12, 0.12])]
    anims += tail_anims(idle0[0], [d0, d1, d2, d2], [0.1, 0.14, 0.2, 0.4], knock)
    return sheet("TallowColossus", anims, outdir, scale=5)


def colossus_corpse():
    r = Rig()
    r.ell(0.0, -3.4, 14.0, 3.6, "tallow", 0.0)
    r.ell(-2.0, -5.0, 10.0, 2.0, "tallow", 0.2, clip=lambda x, y: y < -4.6)
    r.ell(14.0, -2.6, 3.2, 2.6, "tallow", 0.4)
    smoke_curl(r, 13.0, -6.0, 1, 2.0)
    for x in (-8, -2, 4):
        candle(r, x, -6.4, 1.6, 2.0, z=0.6, out=True, ph=x)
    floor_pool(r, 0.0, -0.4, 16.0, 1.2, "tallow", -2.0)
    return r.resolve()


# ================================================================== PYRE WARDEN
def warden(hip=(0.0, -11.5), feet=((-2.5, 0.0), (2.5, 0.0)), lean=0.0, hand=(7.0, -16.0), hand2=(-2.0, -15.0),
           censer=None, chain_from=None, shield=0.0, ph=0, extra=None, sigil=2):
    """A temple door-warden: scorched white surcoat over mail, a tall brazier-shield with the saint's sigil burning on
    it (far arm), a censer swinging on a chain from the near hand. censer: where the censer hangs (default: below the
    hand). shield: 0 at its side .. 1 thrust forward."""
    r = Rig()
    shn, shf, (nx, ny) = biped(r, hip, feet, lean, 10.0, (hand, hand2), (5.8, 5.8), (4.8, 4.6), "steel", "steel",
                               legr=(2.0, 1.6), armr=(1.7, 1.4))
    boots(r, feet, "steel", w=3.0)
    hx, hy = hip
    T = Xf(lean * 6.0, (hx, hy))
    r.poly([T(hx - 5.4, hy + 0.6), T(hx + 5.4, hy + 0.6), T(hx + 6.0, hy - 10.0), T(hx - 6.0, hy - 10.2)], "steel", 0.0, curve=0.6)
    # the surcoat: white, scorched at the hem, a gold sigil on the chest
    r.poly([T(hx - 4.6, hy - 9.8), T(hx + 4.8, hy - 9.6), T(hx + 5.6, hy + 5.6), T(hx + 0.6, hy + 4.0), T(hx - 4.4, hy + 5.8)],
           "cloth", 0.3, curve=0.5)
    for x in (-2.4, -0.6, 1.4, 3.0):
        r.dot(*T(hx + x, hy + 3.6), "soot", 1, 0.32)
    r.dot(*T(hx + 1.0, hy - 5.4), "gold", 4, 0.35); r.line(*T(hx + 1.0, hy - 6.6), *T(hx + 1.0, hy - 3.8), "gold", 0.34, tone=3)
    r.line(*T(hx - 0.2, hy - 5.4), *T(hx + 2.2, hy - 5.4), "gold", 0.34, tone=3)
    # great pauldrons and a gorget
    for (px_, z_) in ((shf[0] - 1.0, -0.6), (shn[0] + 1.2, 2.4)):
        r.ell(px_, shn[1] - 0.6, 3.4, 2.6, "steel", z_)
        r.line(px_ - 2.6, shn[1] + 1.0, px_ + 2.4, shn[1] + 1.2, "bronze", z_ + 0.01, tone=3)
    r.ell(nx + 0.4, ny + 0.6, 3.0, 1.4, "bronze", 0.9)
    # helm: a tall visored warden's helm with a crest of smoke
    gx, gy = nx + 0.6, ny
    r.poly([(gx - 2.8, gy), (gx + 3.0, gy), (gx + 3.0, gy - 6.0), (gx, gy - 7.4), (gx - 2.8, gy - 6.0)], "steel", 1.0, curve=0.7)
    r.line(gx, gy - 7.4, gx, gy - 1.0, "bronze", 1.01, tone=3)
    r.line(gx + 0.2, gy - 3.4, gx + 2.6, gy - 3.4, "soot", 1.02, tone=0)
    r.dot(gx + 1.8, gy - 3.4, "sigil", 3, 1.03)
    # the brazier-shield on the far arm: tall, with a bowl of fire on top and the sigil burning on its face
    sx, sy = lerp(hand2[0] - 5.2, hand2[0] + 6.0, shield), hand2[1] + 6.0
    r.poly([(sx - 4.0, sy + 8.4), (sx + 4.0, sy + 8.4), (sx + 4.4, sy - 9.0), (sx - 4.4, sy - 9.0)], "bronze", 2.6, curve=0.6)
    r.line(sx - 3.8, sy + 8.0, sx - 4.0, sy - 8.6, "gold", 2.61, tone=3)
    r.line(sx + 4.0, sy + 8.0, sx + 4.2, sy - 8.6, "bronze", 2.61, tone=1)
    for yy in (sy - 4.0, sy + 4.0):
        r.dot(sx - 2.8, yy, "gold", 4, 2.615); r.dot(sx + 3.0, yy, "gold", 2, 2.615)
    r.poly([(sx - 4.8, sy - 9.0), (sx + 4.8, sy - 9.0), (sx + 3.6, sy - 12.0), (sx - 3.6, sy - 12.0)], "steel", 2.62)
    flame(r, sx - 1.5, sy - 12.0, 4.0, ph, "fire", 2.7, wide=1.4)
    flame(r, sx + 1.5, sy - 12.0, 4.6, ph + 2, "fire", 2.71, wide=1.4)
    if sigil:
        zz = 2.65
        for (dx, dy) in ((0, -5), (0, -4), (0, -3), (0, -2), (-1, -4), (1, -4), (0, -1), (-2, -4), (2, -4), (0, -6)):
            r.dot(sx + dx, sy + dy, "sigil", 3 if sigil == 2 else 2, zz)
    # the censer on its chain
    if censer is None:
        censer = (hand[0] + 0.5, hand[1] + 6.0)
    r.line(hand[0], hand[1], censer[0], censer[1] - 1.5, "steel", 3.0, tone=3)
    r.ell(censer[0], censer[1], 1.8, 1.6, "bronze", 3.1)
    r.dot(censer[0] + 0.6, censer[1] + 0.2, "ember", 3, 3.2)
    smoke_curl(r, censer[0], censer[1] - 2.0, ph, 3.2, 0.6)
    if extra: extra(r)
    return r.resolve()


@scaled(1.26)
def warden_sheet(outdir):
    Wd = warden
    idle = [Wd(hip=(0, -11.5 + [0, 0.3, 0.5, 0.3][i]), censer=(7.5 + [0, 0.6, 1.0, 0.6][i], -10.0), ph=i) for i in range(4)]
    run = []
    for i in range(6):
        f = walk_feet(i, 6, 3.0, 1.4, 5.0)
        run.append(Wd(feet=f, lean=0.5, censer=(5.5 - f[1][0] * 0.4, -8.5), hand2=(-1.5, -15.0 - abs(math.sin(i)) * 0.4), ph=i))
    smash = [Wd(hand=(5.0, -18.0), censer=(1.0, -22.0), lean=-0.4, ph=0), Wd(hand=(2.0, -21.0), censer=(-6.0, -24.0), lean=-0.8, ph=1),
             Wd(hand=(3.0, -22.0), censer=(4.0, -30.0), lean=-0.4, ph=2),
             Wd(hand=(9.0, -16.0), censer=(17.0, -12.0), lean=0.8, feet=((-2.5, 0), (4.5, 0)), ph=3,
                extra=lambda r: swipe_arc(r, 6.0, -18.0, 12.0, -100, 30, "ember", 4.8, 1, 3)),
             Wd(hand=(10.0, -12.0), censer=(19.0, -1.5), lean=1.2, feet=((-2.5, 0), (4.5, 0)), ph=4,
                extra=lambda r: ember_dots(r, [(16, -3, 4), (22, -3, 3), (19, -5, 3), (14, -1, 2), (24, -1, 2)])),
             Wd(hand=(8.0, -13.0), censer=(15.0, -3.0), lean=0.8, ph=5), Wd(ph=0)]
    stoke = [Wd(hand=(4.0, -15.0), censer=(-4.0, -12.0), lean=-0.5, ph=0), Wd(hand=(1.0, -15.0), censer=(-10.0, -14.0), lean=-0.9, ph=1),
             Wd(hand=(0.0, -16.0), censer=(-11.0, -18.0), lean=-1.0, ph=2),
             Wd(hand=(9.0, -14.0), censer=(14.0, -18.0), lean=0.6, ph=3, extra=lambda r: swipe_arc(r, 4.0, -14.0, 11.0, 160, 330, "ember", 4.8, 1, 3)),
             Wd(hand=(10.0, -12.0), censer=(20.0, -10.0), lean=1.0, ph=4, sigil=2,
                extra=lambda r: (ember_dots(r, [(20, -12, 4), (22, -10, 3), (18, -9, 3)]), glow_ring(r, 0, -1, 9, "sigil", -3, 3, 2.5))),
             Wd(hand=(9.0, -13.0), censer=(15.0, -6.0), lean=0.6, ph=5, extra=lambda r: glow_ring(r, 0, -1, 13, "sigil", -3, 2, 3.5)),
             Wd(hand=(7.0, -14.0), censer=(9.0, -8.0), ph=0), Wd(ph=1)]
    knock = Wd(hip=(-1.0, -11.0), lean=-1.0, hand=(5.0, -12.0), censer=(1.0, -6.0), ph=2)
    d0 = Wd(hip=(-1.0, -10.5), lean=-1.2, hand=(4.0, -17.0), censer=(-2.0, -14.0), ph=1)
    d1 = Wd(hip=(0.0, -7.0), feet=((-3.0, 0), (1.0, 0)), lean=1.2, hand=(8.0, -2.0), censer=(12.0, -1.5), hand2=(-3.0, -4.0), ph=3, sigil=1)
    anims = [("Idle", idle, [0.18, 0.15, 0.18, 0.15]), ("Run", run, [0.1] * 6),
             ("Smash", smash, [0.12, 0.12, 0.1, 0.05, 0.08, 0.12, 0.12]),
             ("Stoke", stoke, [0.12, 0.12, 0.12, 0.05, 0.1, 0.12, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, warden_corpse(0), warden_corpse(1)], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("VhPyreWarden", anims, outdir, scale=5)


def warden_corpse(stage):
    r = Rig()
    r.poly([(-9, -1), (6, -1), (6.5, -5), (-8.5, -5.5)], "cloth", 0.0, curve=0.4)
    r.poly([(6, -1), (10.5, -1), (11, -5.5), (6.5, -5.5)], "iron", 0.5)
    r.poly([(-12, -0.5), (-3, -0.5), (-3, -4), (-12, -4)], "bronze", 0.6)
    r.dot(-7.5, -2.2, "sigil" if stage == 0 else "gold", 2, 0.7)
    r.ell(13, -1.6, 1.8, 1.5, "bronze", 0.6)
    smoke_curl(r, 13, -3.0, 2, 1.0)
    return r.resolve()


# ================================================================== TALLOW RENDERER
def renderer(hip=(0.0, -8.5), feet=((-3.0, 0.0), (3.0, 0.0)), lean=0.0, hand=(8.0, -11.0), hand2=(-3.0, -12.0),
             ladle=0.0, pot=0.0, ph=0, extra=None, steam=True, slosh=0):
    """A hulking ghoul butcher hunched under a boiling cauldron strapped to its back, a long iron ladle, an apron gone
    see-through with fat. ladle: the ladle's angle (deg from the hand, 0 = ahead); pot: 0 on the back .. 1 tipped over
    the shoulder."""
    r = Rig()
    shn, shf, (nx, ny) = biped(r, hip, feet, lean + 1.4, 7.0, (hand, hand2), (4.2, 4.2), (4.4, 4.2), "ghoul", "ghoul",
                               legr=(1.8, 1.4), armr=(1.6, 1.3))
    boots(r, feet, "lthr", w=2.6)
    hx, hy = hip
    T = Xf(14.0 + lean * 6.0, (hx, hy))
    r.ell(*T(hx, hy - 4.0), 6.8, 7.0, "ghoul", 0.0)
    # the apron, glossy and see-through with fat
    r.poly([T(hx + 1.0, hy - 7.0), T(hx + 5.0, hy - 5.0), T(hx + 5.0, hy + 3.0), T(hx + 1.0, hy + 3.4)], "grease", 0.3, curve=0.3)
    r.dot(*T(hx + 3.0, hy - 1.0), "ghoul", 2, 0.31)
    # head jutting from the hunch: a bald ghoul head, a jaw of yellow teeth, ember eyes
    gx, gy = nx + 3.6, ny + 2.2
    r.ell(gx, gy - 1.2, 2.4, 2.2, "ghoul", 1.2)
    r.dot(gx + 1.2, gy - 1.8, "ember", 3, 1.3)
    r.line(gx + 0.4, gy + 0.6, gx + 2.4, gy + 0.2, "bone", 1.3, tone=3)
    # the cauldron on its back (or tipping over the shoulder)
    cxp = lerp(hx - 5.0, hx + 2.0, pot); cyp = lerp(hy - 8.5, hy - 16.0, pot)
    TC = Xf(lerp(0.0, 110.0, pot), (cxp, cyp))
    r.poly([TC(cxp - 5.0, cyp - 3.0), TC(cxp + 5.0, cyp - 3.0), TC(cxp + 4.2, cyp + 3.4), TC(cxp - 4.2, cyp + 3.4)], "iron", -1.0 if pot < 0.5 else 3.5, curve=0.8)
    r.line(*TC(cxp - 5.4, cyp - 3.0), *TC(cxp + 5.4, cyp - 3.0), "rust", -0.95 if pot < 0.5 else 3.55, tone=3)
    rim = TC(cxp, cyp - 3.6)
    if pot < 0.5:
        r.line(cxp - 4.0, cyp - 3.6, cxp + 4.0, cyp - 3.6, "bees", -0.9, tone=4)
        for i in range(2 + slosh):
            r.dot(cxp - 2 + i * 2, cyp - 4.2 - (i + ph) % 2, "bees", 3, -0.88)
    else:
        lip = TC(cxp + 5.4, cyp - 3.0)
        for i in range(5):
            r.ell(lip[0] + i * 1.6, lip[1] + i * 1.2, 1.4, 1.2, "bees", 3.6)
    if steam:
        for i in range(3):
            smoke_curl(r, cxp - 3 + i * 3, cyp - 5 - (i % 2), ph + i, -0.5, 0.6)
    r.line(*T(hx - 2.0, hy - 9.0), *T(hx + 1.0, hy - 1.0), "lthr", 0.5, tone=2)   # the strap
    # the long iron ladle
    a = math.radians(ladle)
    end = (hand[0] + 12.0 * math.cos(a), hand[1] + 12.0 * math.sin(a))
    r.line(hand[0] - 2.0 * math.cos(a), hand[1] - 2.0 * math.sin(a), *end, "iron", 2.9, tone=3)
    r.ell(end[0] + 1.0 * math.cos(a), end[1] + 1.0 * math.sin(a), 1.8, 1.4, "iron", 2.95)
    r.dot(end[0] + 1.0 * math.cos(a), end[1] + 1.0 * math.sin(a) - 0.6, "bees", 4, 3.0)
    if extra: extra(r)
    return r.resolve()


def boil_wave_under(r, k):
    """The wave of boiling tallow it rides: a crest under its feet, foam and steam."""
    p = r.part(False, -0.5)
    K = r.k
    for x in range(-12, 14):
        h = 3.0 + 2.0 * math.sin((x + k * 3) * 0.5) * 0.4 + (3.0 if -4 < x < 6 else 0.0) * (1 - abs(x - 1) / 6.0)
        for y in range(int(h * K) + 1):
            t = 4 if y == int(h * K) else 3 if y > h * K - 2 else 2
            for xx in range(int(x * K), int((x + 1) * K)):
                r.put(xx, -y, -0.5, "bees", 0.5, p, t)
    for i in range(4):
        smoke_curl(r, -10 + i * 3, -6 - (i % 2), k + i, -1.0, 0.5)


@scaled(1.45)
def renderer_sheet(outdir):
    Rd = renderer
    idle = [Rd(hip=(0, -8.5 + [0, 0.3, 0.5, 0.3][i]), ladle=60.0 + [0, 3, 6, 3][i], ph=i) for i in range(4)]
    run = []
    for i in range(6):
        f = walk_feet(i, 6, 3.2, 1.4, 6.0)
        run.append(Rd(feet=f, lean=0.6, ladle=70.0 + f[1][0] * 4, hand2=(-3.0 + f[0][0] * 0.5, -12.0), ph=i, slosh=i % 2))
    ladle = [Rd(hand=(2.0, -14.0), ladle=-120.0, lean=-0.6, ph=0), Rd(hand=(-1.0, -16.0), ladle=-160.0, lean=-1.0, ph=1),
             Rd(hand=(4.0, -17.0), ladle=-60.0, lean=-0.2, ph=2),
             Rd(hand=(10.0, -10.0), ladle=10.0, lean=1.2, feet=((-3, 0), (5, 0)), ph=3, extra=lambda r: _tallow_fan(r)),
             Rd(hand=(9.0, -9.0), ladle=30.0, lean=0.8, ph=4), Rd(ph=5)]
    tip = [Rd(hand=(4.0, -16.0), hand2=(-1.0, -17.0), pot=0.2, ladle=90.0, ph=0),
           Rd(hand=(4.0, -18.0), hand2=(0.0, -19.0), pot=0.5, ladle=90.0, ph=1),
           Rd(hand=(5.0, -18.0), hand2=(1.0, -19.0), pot=0.85, ladle=90.0, ph=2),
           Rd(hand=(6.0, -16.0), hand2=(2.0, -17.0), pot=1.0, ladle=60.0, lean=0.6, ph=3, extra=lambda r: boil_wave_under(r, 0))]
    ride = [Rd(hip=(0.0, -13.5), feet=((-3.0, -5.0), (3.0, -5.5)), hand=(8.0, -17.0), hand2=(-5.0, -20.0), ladle=-40.0 + 6 * i,
               lean=0.8, ph=i, extra=(lambda k: lambda r: boil_wave_under(r, k))(i)) for i in range(4)]
    swing = [Rd(hand=(2.0, -18.0), ladle=-130.0, lean=-0.4, ph=0), Rd(hand=(1.0, -19.0), ladle=-170.0, lean=-0.8, ph=1),
             Rd(hand=(11.0, -10.0), ladle=20.0, lean=1.4, feet=((-3, 0), (5, 0)), ph=2,
                extra=lambda r: swipe_arc(r, 6.0, -14.0, 15.0, -110, 40, "bees", 4.8, 2, 4)),
             Rd(hand=(10.0, -8.0), ladle=50.0, lean=1.0, ph=3), Rd(ph=4)]
    knock = Rd(hip=(-1.0, -8.0), lean=-1.6, hand=(5.0, -14.0), ladle=-30.0, ph=2)
    d0 = Rd(hip=(-1.0, -8.0), lean=-1.8, hand=(4.0, -16.0), ladle=-60.0, ph=1)
    d1 = Rd(hip=(0.0, -5.0), feet=((-3.0, 0), (1.0, 0)), lean=2.0, hand=(9.0, -2.0), hand2=(-2.0, -3.0), pot=0.6, ladle=0.0, ph=3)
    anims = [("Idle", idle, [0.18, 0.15, 0.18, 0.15]), ("Run", run, [0.1] * 6),
             ("Ladle", ladle, [0.1, 0.1, 0.08, 0.06, 0.1, 0.12]),
             ("Tip", tip, [0.1, 0.1, 0.1, 0.1]), ("Ride", ride, [0.08] * 4),
             ("Swing", swing, [0.08, 0.08, 0.05, 0.1, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, renderer_corpse(), renderer_corpse()], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("VhRenderer", anims, outdir, scale=5)


def _tallow_fan(r):
    for k, a in enumerate((-20.0, -5.0, 10.0, 25.0)):
        for i in range(3):
            d = 15.0 + i * 4
            x, y = 6.0 + d * math.cos(math.radians(a)), -10.0 + d * math.sin(math.radians(a)) * 0.6
            r.dot(x, y, "bees", 4 - i, 4.0)


def renderer_corpse():
    r = Rig()
    r.ell(0.0, -3.0, 9.0, 3.0, "ghoul", 0.0)
    r.ell(9.5, -2.4, 2.4, 2.0, "ghoul", 0.3)
    r.poly([(-14, -1), (-6, -1), (-6.5, -7), (-13.5, -7)], "iron", 0.5, curve=0.6)
    r.line(-4, -1, 12, -1, "iron", 0.6, tone=3)
    floor_pool(r, -10.0, -0.4, 8.0, 1.0, "bees", -2.0)
    smoke_curl(r, -10, -8, 1, 1.0)
    return r.resolve()


# ================================================================== WICK HAG
def hag(hip=(0.0, -8.5), feet=((-2.0, 0.0), (2.4, 0.0)), lean=0.0, hand=(6.0, -12.0), hand2=(-2.5, -11.0), ph=0, extra=None,
        crown=1.0, poppet=None):
    """A hunched candle-seller crone: matted hair with seven candles burning hex-violet in it, a tray of wax poppets on
    a strap round her neck. Small and hunched under a crown of flames. poppet: a poppet held at that point."""
    r = Rig()
    shn, shf, (nx, ny) = biped(r, hip, feet, lean + 2.0, 8.0, (hand, hand2), (4.4, 4.4), (4.0, 3.8), "violet", "flesh",
                               legr=(1.2, 1.0), armr=(0.9, 0.7))
    hx, hy = hip
    T = Xf(20.0 + lean * 8.0, (hx, hy))
    # skirts and shawl: a ragged bell, the shawl's fringe over it
    r.poly([T(hx - 6.0, hy + 8.4), T(hx + 6.4, hy + 8.4), T(hx + 4.0, hy - 8.0), T(hx - 3.6, hy - 8.4)], "violet", 0.0, curve=0.7)
    r.poly([T(hx - 3.6, hy - 8.6), T(hx + 4.0, hy - 8.2), T(hx + 4.6, hy - 3.0), T(hx - 4.0, hy - 2.6)], "soot", 0.1, curve=0.6)
    for x in (-3, -1, 1, 3):
        r.dot(*T(hx + x, hy - 2.4), "soot", 2, 0.12)
        r.dot(*T(hx + x + 0.5, hy + 8.4), "violet", 1, 0.02)
    # the tray of poppets on her belly, on a strap round her neck
    tx, ty = T(hx + 4.6, hy - 1.0)
    r.line(*T(hx + 0.6, hy - 8.0), tx - 3.0, ty, "lthr", 1.35, tone=2)
    r.poly([(tx - 3.4, ty), (tx + 4.4, ty), (tx + 4.0, ty + 1.6), (tx - 3.0, ty + 1.6)], "dwood", 1.4)
    for i in range(3):
        px_ = tx - 2.0 + i * 2.6
        r.dot(px_, ty - 3, "tallow", 4, 1.45); r.dot(px_, ty - 2, "votive", 2, 1.45); r.dot(px_, ty - 1, "tallow", 3, 1.45)
    # head jutting forward: hooked nose, one hex eye, matted hair under the candle crown
    gx, gy = nx + 3.0, ny + 2.4
    r.ell(gx - 1.4, gy - 2.6, 4.2, 3.2, "soot", 1.0)    # hair
    for k in range(4):
        r.dot(gx - 4.6 + k * 0.6, gy - 0.6 + k, "soot", 2, 1.01)   # matted strands down the back
    r.ell(gx + 0.8, gy - 0.8, 2.6, 2.8, "tallow", 1.2)          # a face of melting candle wax
    r.poly([(gx + 2.6, gy - 1.8), (gx + 4.8, gy + 0.4), (gx + 2.8, gy + 0.6)], "tallow", 1.25)
    for dx, ln in ((-0.6, 2.6), (1.2, 3.4), (2.6, 2.0)):
        drip(r, gx + dx, gy + 1.4, ln, "tallow", 1.27)
    r.dot(gx + 1.6, gy - 1.6, "ember", 4, 1.3)
    r.dot(gx + 0.0, gy - 1.6, "soot", 0, 1.3)
    r.line(gx + 0.4, gy + 1.0, gx + 2.2, gy + 1.2, "soot", 1.3, tone=0)
    for i in range(int(round(7 * crown))):
        a = math.radians(-165 + i * 25)
        cx_, cy_ = gx - 1.2 + 4.4 * math.cos(a), gy - 3.0 + 2.6 * math.sin(a)
        candle(r, cx_, cy_, 2.2 + (i % 3) * 0.8, 1.4, z=1.1 + (0.2 if 1 < i < 5 else -0.3), ph=ph + i, fl="fire", flh=2.8, drip=1)
    if crown >= 1.0:   # the tall wick burning up out of the middle of her hair
        candle(r, gx - 1.0, gy - 5.0, 6.5, 1.8, z=1.2, ph=ph + 3, flh=5.0, drip=2)
    if poppet:
        doll(r, poppet[0], poppet[1], 3.0, lit=True, ph=ph)
    if extra: extra(r)
    return r.resolve()


def doll(r, x, y, z, lit=True, ph=0, flinch=0.0, melt=0.0):
    """A wax poppet of the hero (in his red), 4 x 6, its wick lit."""
    s = 1.0 - melt
    r.ell(x, y - 1.6 * s, 1.4 + melt, 1.6 * s + 0.3, "tallow", z)
    r.ell(x + flinch, y - 3.8 * s, 1.2, 1.1 * s + 0.2, "tallow", z + 0.01)
    r.dot(x + flinch, y - 2.0 * s, "votive", 2, z + 0.02)     # his red tunic
    r.dot(x - 1, y - 1.4 * s, "votive", 1, z + 0.02)
    if lit and melt < 0.8:
        r.dot(x + flinch, y - 5.2 * s, "wick", 1, z + 0.03)
        flame(r, x + flinch, y - 5.6 * s, 2.0, ph, "fire", z + 0.04)


@scaled(1.16)
def hag_sheet(outdir):
    Hg = hag
    idle = [Hg(hip=(0, -8.5 + [0, 0.2, 0.4, 0.2][i]), hand=(6.0, -12.0 + [0, 0.2, 0.4, 0.2][i]), ph=i) for i in range(4)]
    run = [Hg(feet=walk_feet(i, 6, 2.2, 1.0, 3.0), lean=0.4, hand=(6.0, -11.5 + math.sin(i) * 0.4), ph=i) for i in range(6)]
    hex_ = [Hg(hand=(3.0, -15.0), lean=-0.3, ph=0), Hg(hand=(1.0, -17.0), lean=-0.6, ph=1),
            Hg(hand=(4.0, -18.0), lean=-0.2, ph=2, extra=lambda r: flame(r, 4.0, -19.0, 2.4, 2, "fire", 4.0)),
            Hg(hand=(10.0, -13.0), lean=0.6, ph=3, extra=lambda r: flame(r, 14.0, -13.0, 3.0, 3, "fire", 4.0, lean=2.0)),
            Hg(hand=(9.0, -12.0), lean=0.4, ph=4), Hg(ph=5)]
    pop = [Hg(hand=(5.0, -11.0), ph=0), Hg(hand=(6.0, -8.0), lean=0.4, ph=1, poppet=(5.5, -7.0)),
           Hg(hand=(6.0, -4.0), lean=0.8, hip=(0.0, -7.5), ph=2, poppet=(6.5, -3.5)),
           Hg(hand=(7.0, -2.0), lean=1.0, hip=(0.0, -7.0), ph=3, poppet=(8.0, -0.2)),
           Hg(hand=(7.0, -3.0), lean=0.8, hip=(0.0, -7.3), ph=4, extra=lambda r: doll(r, 9.0, 0.0, 3.0, ph=4)),
           Hg(hand=(6.0, -10.0), lean=0.2, ph=5, extra=lambda r: doll(r, 9.0, 0.0, 3.0, ph=5)), Hg(ph=0)]
    knock = Hg(lean=-1.0, hand=(4.0, -15.0), hand2=(-5.0, -13.0), ph=2)
    d0 = Hg(lean=-1.2, hand=(3.0, -16.0), hand2=(-5.0, -14.0), ph=1)
    d1 = Hg(hip=(0.0, -4.5), lean=1.6, hand=(6.0, -1.0), hand2=(-2.0, -1.0), ph=3, crown=0.6)
    anims = [("Idle", idle, [0.18, 0.15, 0.18, 0.15]), ("Run", run, [0.09] * 6),
             ("Hex", hex_, [0.1, 0.1, 0.1, 0.06, 0.1, 0.12]),
             ("Poppet", pop, [0.1, 0.1, 0.1, 0.1, 0.12, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, hag_corpse(0), hag_corpse(1)], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("VhWickHag", anims, outdir, scale=6)


def hag_corpse(stage):
    r = Rig()
    r.poly([(-7, -1), (5, -1), (4, -4.5), (-6, -4)], "violet", 0.0)
    r.ell(6.6, -2.2, 2.0, 1.8, "soot", 0.4)
    for i in range(5):
        candle(r, 4 + i * 1.2, -3.5 - (i % 2), 1.2, 1.0, z=0.6, out=True, ph=i)
    for i in range(3): r.dot(-4 + i * 3, -0.6, "tallow", 3, 0.7)
    return r.resolve()


# ================================================================== CANDLE WYRM
def wyrm(sway=0.0, rear=1.0, strike=0.0, jaw=0.0, ph=0, extra=None, low=0.0, swim=False, dead=False):
    """The worm reared up for good: an upright tallow serpent in a tall S, a mane of five candles burning blue at the
    base, a long jaw. rear: 0 lying .. 1 upright; strike: 0 .. 1 the head driven down ahead; low: racing along the floor."""
    r = Rig()
    if swim:
        for k in range(5):
            x = -6 + k * 3.2 + math.sin(ph + k) * 0.6
            r.dot(x - 1, -1.0, "tallow", 3, -1.0); r.dot(x + 1, -1.0, "tallow", 2, -1.0)
            flame(r, x, -1.4, 3.6, ph + k, "fire", 2.0); flame(r, x, -1.4, 1.6, ph + k, "blue", 2.1, core=False)
        return r.resolve(floor=False)
    # body path: a coiled base on the floor rising in an S to the head
    h = lerp(10.0, 26.0, rear * (1.0 - low))
    base = [(-8.0, -2.5), (-4.0, -2.8), (0.0, -3.0)]
    p0 = (0.0, -3.0)
    hx = lerp(4.0, 14.0, strike) + sway
    hy = lerp(-h, -8.0, strike)
    mid = bez(p0, (13.0 + sway, -3.0 - h * 0.3), (-10.0 + sway * 0.5, -h * 0.75), (hx, hy), 22)
    pts = base + mid[1:]
    n = len(pts)
    radii = [lerp(4.8, 2.8, i / float(n - 1)) for i in range(n)]
    r.tube(pts, radii, "tallow", 0.0, zs=[0.05 * i for i in range(n)])
    # segment rings round the wax body, a lit ridge along its back
    for i in range(1, n - 1, 2):
        (x0, y0), (x1, y1) = pts[i - 1], pts[i + 1]
        dx, dy = x1 - x0, y1 - y0
        L = max(0.1, math.hypot(dx, dy)); nx_, ny_ = -dy / L, dx / L
        rr = radii[i] * 0.9
        r.line(pts[i][0] - nx_ * rr, pts[i][1] - ny_ * rr, pts[i][0] + nx_ * rr, pts[i][1] + ny_ * rr, "bees", 0.05 * i + 0.03, tone=2)
        r.dot(pts[i][0] - nx_ * rr * 0.6 - 0.5, pts[i][1] - ny_ * rr * 0.6 - 0.5, "tallow", 4, 0.05 * i + 0.04)
    # belly line and wax drips down the S
    for i in range(3, n - 2, 4):
        drip(r, pts[i][0] + 1.5, pts[i][1] + 1.0, 1.6, "tallow", 0.05 * i + 0.02)
    # head: a long jaw, ember eye
    a = math.atan2(pts[-1][1] - pts[-2][1], pts[-1][0] - pts[-2][0])
    hd = (hx + 2.0, hy + (1.0 if strike > 0.5 else 0.0))
    r.ell(hd[0], hd[1], 3.0, 2.2, "tallow", 1.5)
    r.tube([(hd[0] + 1.0, hd[1] - 0.4), (hd[0] + 5.6, hd[1] + 0.2)], [1.4, 0.8], "tallow", 1.55)
    r.tube([(hd[0] + 0.6, hd[1] + 1.2), (hd[0] + 4.6 + jaw, hd[1] + 1.8 + jaw * 2.4)], [1.0, 0.6], "bees", 1.45)
    if jaw > 0.3:
        r.dot(hd[0] + 3.0, hd[1] + 1.0 + jaw, "blue", 3, 1.5)
    r.dot(hd[0] + 0.8, hd[1] - 1.0, "ember" if not dead else "soot", 3, 1.6)
    # the mane: five candles down the back of the neck, flames blue at the base
    for k in range(5):
        i = n - 3 - k * 4
        if i < 0: break
        x, y = pts[i]
        candle(r, x - 2.0, y - radii[i] * 0.7, 3.0, 1.8, z=1.0 + 0.05 * i, ph=ph + k, flh=3.4, drip=1, out=dead, lean=-0.4)
        if not dead:
            flame(r, x - 2.4, y - radii[i] * 0.7 - 3.6, 1.4, ph + k, "blue", 1.1 + 0.05 * i, core=False)
    if extra: extra(r)
    return r.resolve()


@scaled(1.14)
def wyrm_sheet(outdir):
    Wy = wyrm
    idle = [Wy(sway=[0, 0.6, 1.0, 0.6][i], ph=i) for i in range(4)]
    run = [Wy(sway=1.5 * math.sin(i / 6.0 * math.tau), rear=0.85, ph=i) for i in range(6)]
    strike = [Wy(rear=1.05, sway=-2.0, ph=0), Wy(rear=1.1, sway=-3.0, jaw=0.6, ph=1), Wy(rear=1.1, sway=-3.0, jaw=1.0, ph=2),
              Wy(strike=1.0, jaw=0.4, ph=3, extra=lambda r: (dust(r, 20, 0, 0, 1.4), ember_dots(r, [(19, -4, 3), (22, -6, 2)], mat="blue"))),
              Wy(strike=0.7, jaw=0.2, ph=4), Wy(rear=0.9, ph=5)]
    coil = [Wy(low=1.0, sway=2.0 * math.sin(i * 1.6), ph=i, extra=(lambda k: lambda r: _lit_trail(r, k))(i)) for i in range(4)]
    swim = [Wy(swim=True, ph=i) for i in range(4)]
    swimrun = [Wy(swim=True, ph=i * 2) for i in range(6)]
    knock = Wy(sway=-4.0, rear=0.8, jaw=0.8, ph=2)
    d0 = Wy(sway=-5.0, rear=0.7, jaw=1.0, ph=1)
    d1 = Wy(rear=0.0, low=1.0, sway=3.0, jaw=0.5, ph=3, dead=True)
    d2 = Wy(rear=0.0, low=1.0, sway=2.0, ph=4, dead=True, extra=lambda r: floor_pool(r, 0, -0.5, 12.0, 1.0, "tallow", -2.0))
    anims = [("Idle", idle, [0.18, 0.15, 0.18, 0.15]), ("Run", run, [0.09] * 6),
             ("Strike", strike, [0.12, 0.1, 0.1, 0.05, 0.1, 0.12]), ("Coil", coil, [0.06] * 4),
             ("Swim", swim, [0.12] * 4), ("SwimRun", swimrun, [0.07] * 6)]
    anims += tail_anims(idle[0], [d0, d1, d2, d2], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("VhCandleWyrm", anims, outdir, scale=5)


def _lit_trail(r, k):
    for i in range(4):
        x = -10 - i * 3
        flame(r, x, -0.6, 2.0 + (i + k) % 2, k + i, "fire", -2.0)


# ================================================================== FUSE SCORPION
def scorpion(claw=0.0, claw2=0.0, tail=0.0, sting=0.0, legs=0.0, lean=0.0, ph=0, extra=None, dead=False, crouch=0.0):
    """Ash-grey plates over old beeswax, pincers of candle iron, a long braided wick for a tail, always lit. Low and wide
    with the tail arched high. claw/claw2: 0 shut .. 1 open; tail: sway; sting: 0 arched .. 1 driven into the floor ahead."""
    r = Rig()
    by = -4.0 + crouch
    # eight legs, four a side
    for k in range(4):
        for near in (False, True):
            hx = -4.0 + k * 2.6
            ph_ = legs + k * 1.3 + (0.0 if near else math.pi)
            fx = hx + (1.6 if near else -1.0) + 1.2 * math.sin(ph_)
            z = 1.2 if near else -1.2
            r.tube([(hx, by + 0.6), (hx + (1.4 if near else -0.6), by - 1.6), (fx, -max(0.0, 0.8 * math.cos(ph_)))], [0.7, 0.6, 0.45],
                   "rust", z, bias=0.0 if near else -0.3)
    # body: segmented plates over beeswax
    for i in range(5):
        x = -6.0 + i * 3.0 + lean
        r.ell(x, by - 1.6, 3.6, 3.6, "bees", 0.1 * i)
        r.ell(x - 0.4, by - 3.2, 3.4, 2.4, "rust", 0.1 * i + 0.05, clip=lambda xx, yy, yb=by: yy < yb - 0.8)
        r.dot(x - 1.2, by - 3.4, "rust", 4, 0.1 * i + 0.06)
        drip(r, x + 1.4, by - 0.2, 1.2, "bees", 0.1 * i + 0.07)
    hx = 7.0 + lean
    r.ell(hx, by - 0.4, 2.8, 2.4, "rust", 0.6)
    r.dot(hx + 1.0, by - 1.6, "ember", 3, 0.7); r.dot(hx + 2.0, by - 1.2, "ember", 2, 0.7)
    # pincers of candle iron (the far one behind)
    for near, op in ((False, claw2), (True, claw)):
        z = 1.6 if near else -1.0
        sx, sy = hx + 1.0, by + (0.2 if near else -1.0)
        ex, ey = sx + 3.0 + op * 1.0, sy - 0.6 + (0.4 if near else -0.4)
        cx, cy = ex + 3.0 + op * 2.0, ey - 0.2
        r.tube([(sx, sy), (ex, ey), (cx, cy)], [1.1, 1.1, 1.6], "iron", z, bias=0.0 if near else -0.3)
        r.tube([(cx, cy), (cx + 3.0, cy - 1.0 - op * 1.6)], [0.9, 0.4], "iron", z + 0.01)
        r.tube([(cx, cy + 0.6), (cx + 2.6, cy + 0.8 + op * 1.6)], [0.7, 0.3], "iron", z + 0.01)
        r.dot(cx - 0.4, cy - 1.0, "tallow", 4, z + 0.02)
    # the tail: a braided wick arching high over the back, its tip always lit
    tb = (-7.0 + lean, by - 1.0)
    if sting <= 0.0:
        tip = (-1.0 + tail, by - 16.0)
        pts = bez(tb, (-13.0, by - 4.0), (-11.0 + tail * 0.5, by - 18.0), tip, 16)
    else:
        tip = (lerp(-1.0, 16.0, sting), lerp(by - 17.0, -1.0, sting))
        pts = bez(tb, (-13.0, by - 4.0), (lerp(-11.0, 2.0, sting), by - 20.0), tip, 16)
    for i, (x, y) in enumerate(pts):
        rad = lerp(1.9, 1.1, i / float(len(pts) - 1))
        r.ell(x, y, rad, rad, "bees" if i % 2 else "rust", -0.4 + 0.01 * i)
        r.dot(x - 0.4, y - rad * 0.6, "wick", 2, -0.39 + 0.01 * i)
    # the last stretch of the tail is braided fuse, burning down toward the tip
    pf = pts[-5:]
    for i, (x, y) in enumerate(pf):
        r.dot(x, y, "wick", 3, 0.5)
        if not dead and i >= 2: r.dot(x + (0.6 if (i + ph) % 2 else -0.6), y - 0.6, "ember", 3 if i == 4 else 2, 0.6)
    if dead:
        smoke_curl(r, tip[0], tip[1] - 1, ph, 2.0)
    else:
        flame(r, tip[0], tip[1] - 0.6, 3.6, ph, "fire", 2.0)
        flame(r, tip[0], tip[1] - 0.8, 1.8, ph, "spark", 2.1, core=False)
        ember_dots(r, [(tip[0] + 2 - ph % 3, tip[1] - 4 - ph % 2, 4), (tip[0] - 2 + ph % 2, tip[1] - 3, 3)], z=2.2, mat="spark")
    if extra: extra(r)
    return r.resolve()


@scaled(1.35)
def scorpion_sheet(outdir):
    Sc = scorpion
    idle = [Sc(tail=[0, 0.6, 1.0, 0.6][i], claw=[0, 0.2, 0.4, 0.2][i], ph=i, legs=0.2 * i) for i in range(4)]
    run = [Sc(tail=1.0 * math.sin(i), legs=i * math.tau / 6, ph=i, lean=0.3 * math.sin(i)) for i in range(6)]
    snap = [Sc(claw=0.6, claw2=0.6, lean=-0.6, ph=0), Sc(claw=1.0, claw2=1.0, lean=-1.2, crouch=0.5, ph=1),
            Sc(claw=1.0, claw2=1.0, lean=1.0, ph=2),
            Sc(claw=0.0, claw2=0.0, lean=2.0, ph=3, extra=lambda r: ember_dots(r, [(20, -5, 4), (21, -3, 3), (19, -7, 2)], mat="spark")),
            Sc(claw=0.3, claw2=0.2, lean=1.0, ph=4), Sc(ph=5)]
    sting = [Sc(tail=-2.0, crouch=0.5, ph=0), Sc(tail=-3.0, crouch=1.0, ph=1), Sc(sting=0.4, ph=2),
             Sc(sting=1.0, lean=0.6, ph=3, extra=lambda r: (dust(r, 16, 0, 0), ember_dots(r, [(16, -2, 4), (17, -3, 3), (15, -3, 3)], mat="spark"))),
             Sc(sting=0.8, ph=4), Sc(sting=0.3, ph=5), Sc(ph=0)]
    knock = Sc(lean=-1.6, tail=-3.0, claw=0.8, claw2=0.8, ph=2)
    d0 = Sc(lean=-2.0, tail=-4.0, claw=1.0, claw2=1.0, ph=1, crouch=1.0)
    # every death frame is its own pose: the recoil, the legs giving, the tail sagging, the wick smoking out
    d1 = Sc(crouch=1.6, claw=0.7, claw2=0.6, lean=-1.0, tail=-5.0, ph=2, dead=True)
    d2 = Sc(crouch=2.2, claw=0.5, claw2=0.3, lean=-0.4, tail=-5.6, ph=4, dead=True)
    d3 = Sc(crouch=2.4, claw=0.4, ph=3, dead=True, tail=-6.0)
    anims = [("Idle", idle, [0.18, 0.15, 0.18, 0.15]), ("Run", run, [0.08] * 6),
             ("Snap", snap, [0.1, 0.1, 0.06, 0.05, 0.1, 0.12]),
             ("Sting", sting, [0.1, 0.12, 0.06, 0.06, 0.1, 0.1, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, d3], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("VhFuseScorpion", anims, outdir, scale=5)


JOBS = [("TallowColossus", colossus_sheet), ("VhPyreWarden", warden_sheet), ("VhRenderer", renderer_sheet),
        ("VhWickHag", hag_sheet), ("VhCandleWyrm", wyrm_sheet), ("VhFuseScorpion", scorpion_sheet)]
SYNC = {
    "TallowColossus": {"Fists": [("fist 1: swing box at (8, -10)", 2), ("fist 2", 4)],
                       "Rear": [("reared: the body-shaped shadow on the floor ahead (the warning)", 0)],
                       "Fall": [("IMPACT: the body lands 6..34 px ahead (+10 per layer)", 1)],
                       "GetUp": [("back on its feet", 3)]},
    "VhPyreWarden": {"Smash": [("CENSER lands at (19, -1): ember ring", 4)], "Stoke": [("the censer strikes the fire: rings start", 4)]},
    "VhRenderer": {"Ladle": [("fan of tallow from the ladle at (18, -10)", 3)], "Tip": [("the wave pours out ahead (40 px wide)", 3)],
                   "Swing": [("LADLE swing at the end of the ride: box at (14, -10)", 2)]},
    "VhWickHag": {"Hex": [("flame flicked from the fingers at (14, -13)", 3)], "Poppet": [("poppet set down at (9, 0)", 4)]},
    "VhCandleWyrm": {"Strike": [("STRIKE: the head lands 30 px ahead; box 16 x 14 at (16, -6)", 3)]},
    "VhFuseScorpion": {"Snap": [("SNAP: claws at (20, -5); box 16 x 14 at (16, -5)", 3)],
                       "Sting": [("the tail stings the floor at (16, 0): the spark starts", 3)]},
}
NOTES = {"TallowColossus": "Idle1-3 / Run1-3: one to three soaked-up wax layers (10 % bigger each, sagging sheets).",
         "VhCandleWyrm": "Coil: racing along the floor laying lit wax. Swim / SwimRun: under the wax, only the mane flames show.",
         "VhRenderer": "Ride loops on the wave crest (feet 5 px up on the wave)."}
