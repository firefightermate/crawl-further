"""Vhorrul tier 3, second half: Grub Mother, Pyre Tick, Ashen Seraph, Lantern Wraith, Grand Chandelier, Votive
Reliquary. Built through vhorrul_v2_rigs.py. T3 idle limit 42 x 40 (the Chandelier's chain runs off the top)."""
import math
from vhorrul_v2_rigs import (Rig, Xf, ik, lerp, flame, candle, smoke_curl, drip, floor_pool, ember_dots, glow_ring,
                             sheet, tail_anims, line_px, scaled)
from vhorrul_v2_t1 import bez, dust, _ash_cloud
from vhorrul_v2_t2 import biped, walk_feet, swipe_arc


# ================================================================== GRUB MOTHER
def mother(wave=0.0, rear=0.0, mouth=0.0, ph=0, extra=None, sag=0.0, dead=False, squirm=0):
    """An immense pale grub-sow, a long low mound: her back see-through where the clutch squirms, a crown of guttered
    candles, stubby trotters along her belly. rear: the front lifts (the slam / the spit)."""
    r = Rig()
    n = 7
    segs = []
    for i in range(n):
        t = i / float(n - 1)
        x = lerp(-15.0, 11.0, t)
        rad = 3.4 + 4.0 * math.sin(math.pi * min(1.0, 0.1 + t * 0.95))
        y = -rad * 0.8 + sag - rear * max(0.0, t - 0.5) ** 2 * 18.0 + 0.4 * math.sin(i + wave)
        segs.append((x - rear * max(0.0, t - 0.6) * 4.0, y, rad))
    for k in range(5):   # trotters
        x = -10 + k * 5
        r.tube([(x, -2.0), (x + 0.6, -0.4)], [1.2, 1.0], "pink", 0.8 if k % 2 else -0.8)
    for i, (x, y, rad) in enumerate(segs):
        r.ell(x, y, rad * 1.05, rad, "pink", 0.1 * i)
        if 1 <= i <= 4:   # the see-through back with the clutch inside
            r.ell(x - 0.6, y - rad * 0.35, rad * 0.7, rad * 0.45, "grease", 0.1 * i + 0.03)
            for j in range(2):
                gx = x - 1.5 + j * 2.4 + math.sin(squirm + i + j) * 0.8
                r.dot(gx, y - rad * 0.4, "bees", 3, 0.1 * i + 0.05); r.dot(gx + 1, y - rad * 0.4, "bees", 2, 0.1 * i + 0.05)
    hx, hy, hr = segs[-1]
    r.ell(hx + 2.4, hy + 0.4, 3.6, 3.2, "pink", 1.0)
    r.ell(hx + 5.0, hy + 1.0, 0.9 + mouth, 1.0 + mouth * 1.6, "soot", 1.1)
    r.dot(hx + 5.2, hy + 1.0, "votive", 1 + int(mouth > 0.5), 1.15)
    r.dot(hx + 2.8, hy - 1.4, "ember" if not dead else "soot", 3, 1.2)
    # crown of guttered candles on her back
    for k, i in enumerate((2, 3, 4)):
        x, y, rad = segs[i]
        for j in range(2):
            candle(r, x - 1.2 + j * 2.6, y - rad + 0.8, 2.0 + (j + k) % 2, 1.6, z=0.8 + 0.1 * i, ph=ph + k + j, flh=2.4, out=dead, drip=1)
    if extra: extra(r)
    return r.resolve()


def mother_sheet(outdir):
    Mo = mother
    idle = [Mo(wave=i * 0.6, ph=i, squirm=i) for i in range(4)]
    run = [Mo(wave=i * 1.1, ph=i, squirm=i, sag=0.4 * math.sin(i)) for i in range(6)]
    slam = [Mo(rear=0.3, ph=0), Mo(rear=0.7, mouth=0.4, ph=1), Mo(rear=1.0, mouth=0.6, ph=2),
            Mo(rear=-0.3, mouth=0.2, ph=3, extra=lambda r: (dust(r, 18, 0, 0, 1.6), floor_pool(r, 17, -0.6, 4.0, 1.0, "tallow", -2.0))),
            Mo(rear=-0.1, ph=4), Mo(ph=5)]
    spit = [Mo(rear=0.2, ph=0, squirm=0), Mo(rear=0.5, mouth=0.4, ph=1, squirm=2), Mo(rear=0.8, mouth=0.8, ph=2, squirm=4),
            Mo(rear=0.9, mouth=1.0, ph=3, squirm=6), Mo(rear=0.4, mouth=1.0, ph=4, extra=lambda r: _grubs_fly(r, 0)),
            Mo(rear=0.2, mouth=0.5, ph=5, extra=lambda r: _grubs_fly(r, 1)), Mo(ph=0)]
    knock = Mo(rear=0.6, mouth=0.8, ph=2, wave=2.0)
    d0 = Mo(rear=0.8, mouth=1.0, ph=1)
    d1 = Mo(sag=2.0, mouth=0.6, ph=3, dead=True)
    d2 = Mo(sag=3.0, dead=True, extra=lambda r: floor_pool(r, 0, -0.5, 18.0, 1.2, "tallow", -2.0))
    anims = [("Idle", idle, [0.18, 0.15, 0.18, 0.15]), ("Run", run, [0.1] * 6),
             ("Slam", slam, [0.12, 0.1, 0.1, 0.05, 0.1, 0.12]),
             ("Spit", spit, [0.1, 0.1, 0.1, 0.1, 0.06, 0.1, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, d2], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("VhBroodMother", anims, outdir, scale=5)


def _grubs_fly(r, k):
    for i, (x, y) in enumerate(((20, -16), (24, -12), (18, -11))):
        x += k * 4; y += k * 3
        r.ell(x, y, 1.4, 0.9, "tallow", 4.0)
        r.dot(x + 1, y, "ember", 2, 4.1)


# ================================================================== PYRE TICK
def tick(rear=0.0, legs=0.0, swell=1.0, jaw=0.0, ph=0, extra=None, dead=False, lean=0.0):
    """A tick bloated on pyre fire: a round shell cracked across, the fire showing through, barbed mouthparts, eight
    thin legs. rear: the front lifts (spraying)."""
    r = Rig()
    cx, cy = lean, -9.0 - rear * 2.0
    R = 7.5 * swell
    for k in range(4):
        for near in (False, True):
            a = legs + k * 0.9 + (0.0 if near else 1.6)
            hx = cx - 4.0 + k * 2.6
            knee = (hx + (k - 1.5) * 3.0, cy - 6.0 + abs(k - 1.5))
            foot = (hx + (k - 1.5) * 5.0 + 1.2 * math.sin(a), -max(0.0, 1.0 * math.cos(a)))
            z = 1.4 if near else -1.4
            r.tube([(hx, cy + 1.0), knee, foot], [0.6, 0.6, 0.4], "tick", z, bias=0.0 if near else -0.35)
    r.ell(cx, cy, R, R * 0.85, "tick", 0.0, ang=-rear * 10)
    # the cracks: magma showing through the shell
    for pts in (((-4, -4), (-1, -2), (1, -5), (4, -3)), ((-5, 1), (-2, 2), (0, 0), (3, 3)), ((2, -1), (5, 0))):
        for a_, b_ in zip(pts, pts[1:]):
            for (x, y) in line_px(int(cx + a_[0] * swell), int(cy + a_[1] * swell), int(cx + b_[0] * swell), int(cy + b_[1] * swell)):
                pc = r.part(True, 0.2)
                r.put(x, y, 0.2, "magma" if not dead else "soot", 0.5, pc, 3 if (x + y + ph) % 3 else 4)
                r.put(x, y + 1, 0.2, "magma" if not dead else "soot", 0.5, pc, 2)
    hx, hy = cx + R * 0.9, cy + 1.6 + rear * 1.0
    r.ell(hx, hy, 2.4, 2.0, "tick", 0.5)
    for s in (-1, 1):
        r.tube([(hx + 1.4, hy + s * 0.6), (hx + 3.6 + jaw, hy + s * (0.8 + jaw * 1.4)), (hx + 4.2, hy + s * 0.2)], [0.6, 0.5, 0.3],
               "bone", 0.6 if s > 0 else 0.4)
    r.dot(hx + 0.4, hy - 1.0, "eye", 3, 0.7)
    if extra: extra(r)
    return r.resolve()


@scaled(1.4)
def tick_sheet(outdir):
    Tk = tick
    idle = [Tk(swell=1.0 + [0, 0.02, 0.04, 0.02][i], ph=i, legs=0.2 * i) for i in range(4)]
    run = [Tk(legs=i * math.tau / 6, ph=i, lean=0.3 * math.sin(i)) for i in range(6)]
    bite = [Tk(lean=-1.0, jaw=0.5, ph=0), Tk(lean=-1.6, jaw=1.0, ph=1), Tk(lean=1.0, jaw=1.0, ph=2),
            Tk(lean=3.0, jaw=0.0, ph=3, extra=lambda r: ember_dots(r, [(16, -8, 3), (17, -6, 2)], mat="magma")), Tk(lean=1.5, ph=4), Tk(ph=5)]
    spray = [Tk(rear=0.4, swell=1.04, ph=0), Tk(rear=0.8, swell=1.08, jaw=0.6, ph=1), Tk(rear=1.0, swell=1.1, jaw=1.0, ph=2),
             Tk(rear=1.0, swell=1.1, jaw=1.0, ph=3), Tk(rear=0.6, swell=1.0, jaw=1.0, ph=4, extra=lambda r: _blood_fan(r, 0)),
             Tk(rear=0.3, ph=5, extra=lambda r: _blood_fan(r, 1)), Tk(ph=0)]
    knock = Tk(lean=-2.0, rear=0.5, jaw=1.0, ph=2)
    d0 = Tk(lean=-2.0, rear=0.8, jaw=1.0, swell=1.05, ph=1)
    d1 = Tk(swell=0.9, ph=3, dead=True, legs=1.0)
    anims = [("Idle", idle, [0.18, 0.15, 0.18, 0.15]), ("Run", run, [0.07] * 6),
             ("Bite", bite, [0.1, 0.1, 0.06, 0.05, 0.1, 0.12]),
             ("Spray", spray, [0.1, 0.1, 0.1, 0.1, 0.06, 0.1, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, tick_corpse(), tick_corpse()], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("VhPyreTick", anims, outdir, scale=5)


def _blood_fan(r, k):
    for i, a in enumerate((-30, -15, 0, 15, 30)):
        d = 12 + k * 5
        x, y = 10 + d * math.cos(math.radians(a)), -12 + d * math.sin(math.radians(a)) * 0.6 + k * 2
        r.dot(x, y, "magma", 4, 4.0); r.dot(x - 1, y, "magma", 3, 4.0)


def tick_corpse():
    r = Rig()
    r.ell(0, -3.6, 8.0, 3.4, "tick", 0.0)
    for x in (-5, -2, 2, 5):
        r.tube([(x, -6), (x + 1, -9), (x + 2, -8)], [0.5, 0.4, 0.3], "tick", 0.5)
    r.line(-4, -4, 4, -3, "soot", 0.2, tone=0)
    smoke_curl(r, 0, -7, 2, 1.0)
    return r.resolve()


# ================================================================== ASHEN SERAPH
def seraph(hip=(0.0, -12.0), feet=((-2.0, 0.0), (2.5, 0.0)), lean=0.0, hand=(6.0, -16.0), hand2=(-4.0, -15.0), lance=-80.0,
           wings=0.0, white=False, ph=0, extra=None, alt=0.0):
    """A six-winged seraph of ash with a moth's face and a long cinder lance; its wings shed flakes. Tall with a wide
    crown of wings. wings: 0 folded up behind .. 1 beating wide; white: the wings flare white (Ash to Ash)."""
    r = Rig()
    hip = (hip[0], hip[1] - alt)
    shn, shf, (nx, ny) = biped(r, hip, feet, lean, 8.0, (hand, hand2), (5.8, 5.8), (4.4, 4.2), "ash", "ash",
                               legr=(1.2, 0.9), armr=(1.0, 0.8))
    hx, hy = hip
    # six wings: three pairs fanned behind the body
    for pair, (ang, ln) in enumerate(((-135, 17.0), (-168, 15.0), (155, 11.0))):
        for s, z in ((-1, -2.0 - pair * 0.1), (1, -1.6 - pair * 0.1)):
            a = math.radians(ang + wings * (20 if pair < 2 else -10)) if s < 0 else math.radians(-180 - ang - wings * (20 if pair < 2 else -10))
            root = (nx, ny + 3.0 + pair * 1.6)
            tip = (root[0] + ln * (1.0 + 0.2 * wings) * math.cos(a), root[1] + ln * math.sin(a) * (0.8 - 0.3 * pair))
            px_, py_ = -math.sin(a), math.cos(a)
            mx, my = (root[0] + tip[0]) / 2, (root[1] + tip[1]) / 2
            wd = 5.2 - 0.8 * pair
            pts_ = [root, (root[0] - px_ * wd * 0.7, root[1] - py_ * wd * 0.7), (mx - px_ * wd, my - py_ * wd), tip,
                    (mx + px_ * wd * 0.5, my + py_ * wd * 0.5), (root[0] + px_ * 1.2, root[1] + py_ * 1.2)]
            r.poly(pts_, "ashw", z,
                   bias=-0.15 if s < 0 else 0.0, normal=(-0.3, -0.4, 1.0))
            r.line(root[0], root[1], tip[0], tip[1], "white" if white else "ash", z + 0.01, tone=4 if white else 2)
            r.line(mx - px_ * wd * 0.5, my - py_ * wd * 0.5, tip[0], tip[1], "white" if white else "ashw", z + 0.012, tone=3 if white else 4)
            if not white and (pair + ph) % 2 == 0:   # flakes shed off the tips
                r.dot(tip[0] + s * 1.0, tip[1] + 2.0 + ph % 3, "ash", 3, z)
    T = Xf(lean * 6.0, (hx, hy))
    # a long robe of ash, girdled
    r.poly([T(hx - 5.8, hy + 7.6), T(hx + 6.2, hy + 7.6), T(hx + 4.0, hy - 8.0), T(hx - 3.8, hy - 8.2)], "ashw", 0.0, curve=0.7)
    for x in (-2.6, 0.4, 3.0):   # folds of the ash robe, a smoulder at the hem
        r.line(*T(hx + x * 0.6, hy - 6.0), *T(hx + x, hy + 7.0), "ashw", 0.02, tone=1)
    r.line(*T(hx - 4.4, hy + 7.2), *T(hx + 4.8, hy + 7.2), "ember", 0.03, tone=2)
    r.line(*T(hx - 2.6, hy - 2.0), *T(hx + 2.8, hy - 2.0), "ember", 0.05, tone=2)
    for x in (-2.0, 0.5, 2.6):
        r.dot(*T(hx + x, hy + 7.0), "ash", 1, 0.05)
    # moth face: pale, two big soot eyes, feathered antennae swept back
    gx, gy = nx + 0.6, ny - 0.6
    r.ell(gx, gy, 2.2, 2.4, "ashw", 1.2)
    r.dot(gx + 0.4, gy - 0.4, "soot", 0, 1.3); r.dot(gx + 1.6, gy - 0.4, "soot", 0, 1.3)
    r.dot(gx + 1.6, gy - 0.6, "ember", 3, 1.31)
    for s in (-1, 1):
        pts = bez((gx + s * 0.6, gy - 2.0), (gx + s * 1.4, gy - 5.0), (gx + s * 3.0, gy - 6.6), (gx + s * 4.6 - 1, gy - 6.0), 6)
        r.polyline(pts, "ash", 1.25, tone=3)
    # the cinder lance: a long haft with an ember blade
    a = math.radians(lance)
    tip = (hand[0] + 16.0 * math.cos(a), hand[1] + 16.0 * math.sin(a))
    butt = (hand[0] - 5.0 * math.cos(a), hand[1] - 5.0 * math.sin(a))
    r.line(*butt, *tip, "soot", 2.9, tone=3)
    b0 = (tip[0] - 3.0 * math.cos(a), tip[1] - 3.0 * math.sin(a))
    r.line(*b0, *tip, "ember", 2.95, tone=3)
    r.dot(*tip, "fire", 4, 3.0)
    if extra: extra(r)
    return r.resolve()


@scaled(1.19)
def seraph_sheet(outdir):
    Se = seraph
    idle = [Se(hip=(0, -12.0 + [0, 0.4, 0.6, 0.4][i]), wings=[0, 0.1, 0.2, 0.1][i], ph=i, hand=(6.0, -16.0 + [0, 0.4, 0.6, 0.4][i]))
            for i in range(4)]
    run = [Se(feet=walk_feet(i, 6, 2.6, 1.2, 4.0), lean=0.6, wings=0.3 + 0.2 * math.sin(i), lance=-60.0, hand=(7.0, -15.0), ph=i)
           for i in range(6)]
    lance = [Se(hand=(2.0, -15.0), lance=-10.0, lean=-0.6, ph=0), Se(hand=(-1.0, -14.0), lance=-5.0, lean=-1.2, wings=0.4, ph=1),
             Se(hand=(4.0, -14.0), lance=0.0, lean=0.4, wings=0.8, ph=2),
             Se(hand=(12.0, -14.0), lance=0.0, lean=1.6, wings=1.0, feet=((-2.0, 0), (6.0, 0)), ph=3,
                extra=lambda r: ember_dots(r, [(30, -15, 4), (31, -13, 3), (29, -17, 2)])),
             Se(hand=(9.0, -14.0), lance=-5.0, lean=1.0, wings=0.6, ph=4), Se(ph=5)]
    beat = [Se(wings=0.0, ph=0), Se(wings=-0.3, ph=1, alt=1.0), Se(wings=1.0, white=True, ph=2, alt=2.0),
            Se(wings=1.2, white=True, ph=3, alt=2.0, extra=lambda r: _smoke_cols(r, 0)),
            Se(wings=0.2, white=True, ph=4, alt=1.0, extra=lambda r: _smoke_cols(r, 1)),
            Se(wings=1.0, ph=5, extra=lambda r: _smoke_cols(r, 2)), Se(ph=0)]
    knock = Se(lean=-1.0, wings=0.8, hand=(4.0, -18.0), lance=-120.0, ph=2)
    d0 = Se(lean=-1.2, wings=1.0, hand=(3.0, -19.0), lance=-140.0, ph=1)
    d1 = Se(hip=(0.0, -6.0), feet=((-3.0, 0), (1.0, 0)), lean=1.6, wings=-0.5, hand=(7.0, -3.0), lance=0.0, ph=3)
    anims = [("Idle", idle, [0.18, 0.15, 0.18, 0.15]), ("Run", run, [0.09] * 6),
             ("Lance", lance, [0.1, 0.1, 0.08, 0.05, 0.1, 0.12]),
             ("Beat", beat, [0.1, 0.1, 0.06, 0.1, 0.1, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, seraph_corpse(), seraph_corpse()], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("VhAshSeraph", anims, outdir, scale=5)


def _smoke_cols(r, k):
    for x in (-14, 14):
        for j in range(4 + k):
            r.dot(x + math.sin(j + k) * 0.8, -j * 2.0 - 1, "smoke", 0.5 if False else (3 if j < 2 else 2), 5.0)


def seraph_corpse():
    r = Rig()
    r.poly([(-14, -1), (-6, -6), (0, -2), (6, -6), (14, -1), (0, 0)], "ashw", -0.5, bias=-0.2)
    r.poly([(-4, -1), (6, -1), (5, -4), (-3, -4)], "ashw", 0.0)
    r.ell(8.0, -2.4, 2.0, 2.0, "ashw", 0.4)
    r.line(-10, -2, 16, -1, "soot", 0.6, tone=3)
    smoke_curl(r, 0, -5, 1, 1.0)
    return r.resolve()


# ================================================================== LANTERN WRAITH
def wraith(bob=0.0, lean=0.0, lamp=(9.0, -18.0), hand2=(-4.0, -14.0), full=False, ph=0, extra=None, fade=0.0, swing=0.0):
    """A robed wraith with no legs, a soul-fire lantern held out on a crook, a teal flame for a face. Tall and thin with
    the lantern swung out. full: the lantern holds a stolen soul flame (warm gold) beside its own teal one."""
    r = Rig()
    cy = -4.0 + bob
    # the robe: a long tapering shroud that frays into wisps above the floor
    top = (lean, cy - 18.0)
    r.poly([(top[0] - 3.4, top[1] + 2.0), (top[0] + 3.8, top[1] + 2.0), (9.0 + lean * 0.4, cy), (2.0, cy + 2.4), (-1.0, cy + 1.4),
            (-9.0 + lean * 0.4, cy + 2.6)], "robe", 0.0, curve=0.7)
    r.poly([(top[0] - 3.6, top[1] + 2.4), (top[0] + 4.0, top[1] + 2.4), (top[0] + 5.0, top[1] + 7.0), (top[0] - 5.0, top[1] + 7.4)],
           "robe", 0.05, bias=0.1, curve=0.6)   # the shoulder cape
    for x in (-3.0, 0.0, 3.0):
        r.line(top[0] + x * 0.5, top[1] + 8.0, x * 1.4, cy, "robe", 0.06, tone=1)
    for i in range(3):   # soul light leaking from the hem
        r.dot(-3.0 + i * 3.0 + lean * 0.4, cy + 2.0 + (i + ph) % 2, "soul", 2, 0.07)
    for i, x in enumerate((-4.0, -1.0, 2.0, 4.5)):
        r.line(x + lean * 0.4, cy + 1.5, x - 1 + lean * 0.4, cy + 3.5 + (i + ph) % 2, "robe", 0.01, tone=1 if i % 2 else 2)
    # hood and the teal face flame
    r.ell(top[0] + 0.4, top[1] - 0.4, 3.0, 3.2, "robe", 1.0)
    r.ell(top[0] + 1.2, top[1] + 0.2, 1.8, 2.2, "soot", 1.05)
    flame(r, top[0] + 1.2, top[1] + 1.8, 3.6, ph, "soul", 1.1)
    # arms: the crook arm (near) and a bony far hand
    sh = (top[0] + 1.6, top[1] + 4.0)
    for near, tgt in ((True, (lamp[0] - 3.0, lamp[1] + 3.0)), (False, hand2)):
        s = sh if near else (top[0] - 1.6, top[1] + 4.0)
        ex, ey = ik(s[0], s[1], tgt[0], tgt[1], 4.4, 4.0, bend=1)
        z = 2.0 if near else -0.8
        r.tube([s, (ex, ey), tgt], [1.2, 0.9, 0.8], "robe", z, bias=0.0 if near else -0.3)
        r.dot(tgt[0] + 0.6, tgt[1], "bone", 3, z + 0.01)
    # the crook: a long staff with a hook at the top, the lantern hanging off it
    hand = (lamp[0] - 3.0, lamp[1] + 3.0)
    r.line(hand[0] - 1.0, hand[1] + 8.0, hand[0] + 0.5, hand[1] - 4.0, "dwood", 2.5, tone=3)
    r.polyline([(hand[0] + 0.5, hand[1] - 4.0), (hand[0] + 2.0, hand[1] - 5.6), (lamp[0] + swing, lamp[1] - 4.0)], "dwood", 2.5, tone=3)
    lx, ly = lamp[0] + swing, lamp[1]
    r.line(lx, ly - 4.0, lx, ly - 2.6, "iron", 2.6, tone=2)
    r.poly([(lx - 2.4, ly - 2.6), (lx + 2.4, ly - 2.6), (lx + 2.2, ly + 2.6), (lx - 2.2, ly + 2.6)], "glass", 2.7, flat=None)
    r.line(lx - 2.0, ly - 2.6, lx + 2.0, ly - 2.6, "iron", 2.75, tone=3)
    r.line(lx - 1.8, ly + 2.4, lx + 1.8, ly + 2.4, "iron", 2.75, tone=1)
    flame(r, lx, ly + 1.8, 3.4, ph, "soul", 2.8)
    if full:
        flame(r, lx + 0.8, ly + 1.8, 2.2, ph + 2, "fire", 2.85, wide=0.8)
    if extra: extra(r)
    s = r.resolve()
    if fade:
        s.px = {k: v for k, v in s.px.items() if (k[0] * 3 + k[1] * 5) % 7 >= int(fade * 7)}
    return s


@scaled(1.45)
def wraith_sheet(outdir):
    Wr = wraith
    sets = {}
    for full in (False, True):
        idle = [Wr(bob=[0, -0.6, -1.0, -0.6][i], lamp=(9.0, -18.0 + [0, -0.6, -1.0, -0.6][i]), swing=[0, 0.4, 0.6, 0.4][i], full=full, ph=i)
                for i in range(4)]
        run = [Wr(bob=-0.8 - 0.4 * math.sin(i), lean=1.0, lamp=(10.0, -17.0), swing=-0.8 + 0.4 * math.sin(i), full=full, ph=i) for i in range(6)]
        sets[full] = (idle, run)
    idle, run = sets[False]
    swing = [Wr(lamp=(5.0, -22.0), lean=-0.6, swing=-1.0, ph=0), Wr(lamp=(2.0, -24.0), lean=-1.0, swing=-1.6, ph=1),
             Wr(lamp=(8.0, -24.0), lean=0.0, ph=2), Wr(lamp=(13.0, -19.0), lean=1.2, swing=1.4, ph=3,
                                                       extra=lambda r: (flame(r, 18.0, -17.0, 3.0, 3, "soul", 4.0), ember_dots(r, [(16, -18, 3)], mat="soul"))),
             Wr(lamp=(12.0, -18.0), lean=0.8, swing=1.0, ph=4), Wr(ph=5)]
    take = [Wr(lamp=(6.0, -20.0), lean=-0.4, ph=0), Wr(lamp=(4.0, -22.0), lean=-0.8, swing=-1.0, ph=1),
            Wr(lamp=(12.0, -16.0), lean=1.0, swing=1.6, ph=2), Wr(lamp=(14.0, -15.0), lean=1.4, swing=2.0, ph=3, extra=lambda r: _soul_cone(r, 0)),
            Wr(lamp=(13.0, -16.0), lean=1.2, swing=1.0, ph=4, full=True, extra=lambda r: _soul_cone(r, 1)),
            Wr(lamp=(10.0, -17.0), lean=0.6, ph=5, full=True), Wr(ph=0, full=True)]
    knock = Wr(lean=-1.4, lamp=(6.0, -20.0), swing=-2.0, ph=2)
    d0 = Wr(lean=-1.6, lamp=(5.0, -21.0), swing=-2.0, ph=1, fade=0.15)
    d1 = Wr(bob=3.0, lean=0.4, lamp=(10.0, -8.0), ph=3, fade=0.45)
    anims = [("Idle", idle, [0.18, 0.15, 0.18, 0.15]), ("Run", run, [0.09] * 6),
             ("IdleFull", sets[True][0], [0.18, 0.15, 0.18, 0.15]), ("RunFull", sets[True][1], [0.09] * 6),
             ("Swing", swing, [0.1, 0.1, 0.08, 0.06, 0.1, 0.12]),
             ("Take", take, [0.1, 0.12, 0.08, 0.06, 0.1, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, wraith_corpse(), wraith_corpse()], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("LanternWraith", anims, outdir, scale=5)


def _soul_cone(r, k):
    for d in range(4, 22, 2):
        w = d * 0.45
        for j in range(-int(w), int(w) + 1, 2):
            if (d + j + k) % 4 == 0:
                r.dot(14 + d, -15 + j * 0.6, "soul", 3 if d < 12 else 2, 4.0)


def wraith_corpse():
    r = Rig()
    r.poly([(-8, -1), (6, -1), (5, -3), (-7, -3.5)], "robe", 0.0)
    r.poly([(7, -1), (10, -1), (10, -4), (7, -4)], "glass", 0.4)
    r.dot(8.5, -2.5, "soul", 1, 0.5)
    smoke_curl(r, 8.5, -5, 1, 1.0, 0.6)
    return r.resolve()


# ================================================================== GRAND CHANDELIER
def chandelier(high=0.0, spin=0.0, ph=0, flare=0.0, tilt=0.0, extra=None, drop=0.0, out=False, chain=True):
    """An iron ring chandelier of a dozen candles, hanging from a chain that runs off the top of the cell, a
    wax-drowned saint's face in the hub. high: 0 low on its chain .. 1 high (shorter chain, smaller shadow); spin: the
    ring's turn (deg); flare: every candle leaps."""
    r = Rig()
    cy = lerp(-15.0, -24.0, high) + drop
    if chain:
        pc = r.part(True, -3.0)
        for y in range(-38, int(cy - 5)):   # the chain runs off the top of the cell
            r.put(0 + (y % 2) * 0.0, y, -3.0, "iron", 0.5, pc, 3 if y % 3 == 0 else 2 if y % 3 == 1 else 1)
        for s in (-1, 1):   # the three hanging chains
            r.line(0, cy - 6, s * 9.0, cy, "iron", -2.9, tone=2)
        r.line(0, cy - 6, 0, cy - 2, "iron", -2.9, tone=2)
    # shadow on the floor: smaller when it hangs high
    sw = lerp(11.0, 7.0, high) if drop < 10 else 13.0
    r.ell(0.0, -0.6, sw, 1.2, "soot", -6.0, flat=1)
    # the ring: an ellipse seen from a little above, candles round it
    R, Ry = 12.0, 3.4
    T = Xf(tilt, (0.0, cy))
    back, front = [], []
    for k in range(10):
        a = math.radians(spin + k * 36.0)
        x, y = R * math.cos(a), cy + Ry * math.sin(a)
        (front if math.sin(a) > 0 else back).append((T(x, y), k))
    def ring_half(sign, z):
        p = r.part(False, z)
        for i in range(60):
            a = i / 60.0 * math.tau
            if (math.sin(a) > 0) != (sign > 0): continue
            x, y = T(R * math.cos(a), cy + Ry * math.sin(a))
            r.put(x, y, z, "bronze", 0.5, p, 3 if math.sin(a) > 0 and math.cos(a) < 0.3 else 2 if sign > 0 else 1)
            r.put(x, y + 1, z, "bronze", 0.5, p, 1)
    ring_half(-1, -1.0)
    for (x, y), k in back:
        candle(r, x, y - 0.5, 2.6, 1.6, z=-0.8, ph=ph + k, flh=2.6 + 2.0 * flare, drip=1, out=out)
    # the hub: the saint's face drowned in wax
    hx, hy = T(0.0, cy + 1.0)
    r.ell(hx, hy, 3.4, 3.6, "tallow", 0.5)
    r.dot(hx - 1, hy - 0.6, "soot", 0, 0.6); r.dot(hx + 1, hy - 0.6, "soot", 0, 0.6)
    r.dot(hx + 1, hy - 0.8, "ember" if not out else "soot", 2, 0.61)
    r.line(hx - 0.6, hy + 1.4, hx + 0.6, hy + 1.4, "soot", 0.61, tone=1)
    for dx in (-2, 0, 2):
        drip(r, hx + dx, hy + 3.0, 2.0 + abs(dx) * 0.5, "tallow", 0.62)
    ring_half(1, 1.0)
    for (x, y), k in front:
        candle(r, x, y - 0.5, 2.6, 1.6, z=1.2, ph=ph + k, flh=2.6 + 2.0 * flare, drip=1, out=out)
    if extra: extra(r)
    return r.resolve()


def chandelier_sheet(outdir):
    Ch = chandelier
    idle = [Ch(spin=i * 9.0, ph=i, tilt=[0, 2, 0, -2][i]) for i in range(4)]
    run = [Ch(spin=i * 12.0, ph=i, tilt=5 + 2 * math.sin(i)) for i in range(6)]
    ihigh = [Ch(high=1.0, spin=i * 9.0, ph=i, tilt=[0, 2, 0, -2][i]) for i in range(4)]
    rhigh = [Ch(high=1.0, spin=i * 12.0, ph=i, tilt=5 + 2 * math.sin(i)) for i in range(6)]
    wheel = [Ch(spin=0, ph=0, tilt=-4), Ch(spin=10, ph=1, tilt=-6, flare=0.4)]
    for i in range(5):
        wheel.append(Ch(spin=40 + i * 36, ph=i + 2, flare=1.0, extra=(lambda k: lambda r: _wheel_fire(r, k))(i)))
    wheel.append(Ch(spin=230, ph=0, tilt=2))
    drip_ = [Ch(spin=i * 6, ph=i, extra=(lambda k: lambda r: _drips(r, k))(i)) for i in range(6)]
    flare = [Ch(flare=0.6, ph=0, extra=lambda r: _drips(r, 5)), Ch(flare=1.4, ph=1, extra=lambda r: glow_ring(r, 0, -1.5, 15, "fire", -3, 4, 4.0)),
             Ch(flare=1.0, ph=2, extra=lambda r: glow_ring(r, 0, -1.5, 15, "fire", -3, 3, 4.0)), Ch(flare=0.3, ph=3)]
    knock = Ch(tilt=-14, ph=2, spin=20)
    d0 = Ch(tilt=-20, ph=1, spin=30, flare=0.6)
    d1 = Ch(tilt=-8, ph=3, drop=10.0, chain=False, out=True)
    d2 = Ch(tilt=0, ph=4, drop=13.5, chain=False, out=True, extra=lambda r: floor_pool(r, 0, -0.5, 14.0, 1.2, "tallow", -6.5))
    anims = [("Idle", idle, [0.18] * 4), ("Run", run, [0.1] * 6), ("IdleHigh", ihigh, [0.18] * 4), ("RunHigh", rhigh, [0.1] * 6),
             ("Wheel", wheel, [0.1, 0.1, 0.06, 0.06, 0.06, 0.06, 0.06, 0.12]),
             ("Drip", drip_, [0.25] * 6), ("Flare", flare, [0.1, 0.08, 0.12, 0.15])]
    anims += tail_anims(idle[0], [d0, d1, d2, d2], [0.1, 0.1, 0.14, 0.4], knock)
    return sheet("VhChandelier", anims, outdir, scale=5)


def _wheel_fire(r, k):
    swipe_arc(r, 0.0, -15.0, 17.0, k * 72, k * 72 + 120, "fire", 4.8, 2, 3)


def _drips(r, k):
    p = r.part(True, 3.0)
    for j in range(8):
        a = j / 8.0 * math.tau
        x, y = 14 * math.cos(a), -1.0 + 4.0 * math.sin(a)
        fall = ((k + j) % 3) * 4
        r.put(x, -14 + fall, 3.0, "tallow", 0.5, p, 4)
        r.put(x, y, -5.0, "tallow", 0.5, p, 3 if k > j % 6 else 2)


# ================================================================== VOTIVE RELIQUARY
def reliquary(lean=0.0, feet=None, bob=0.0, door=0.0, weep=0, ph=0, extra=None, tilt=0.0, out=False, sheen=False):
    """A walking shrine of dark wood on root legs: shelves of red votive candles, a weeping skull in a glass case at
    its heart, a pitched roof. weep: tears of holy oil (0-3)."""
    r = Rig()
    if feet is None:
        feet = ((-5.0, 0.0), (-1.5, 0.0), (2.0, 0.0), (5.5, 0.0))
    by = -7.0 + bob
    for k, (fx, fy) in enumerate(feet):
        hx = -4.5 + k * 3.0
        z = 0.8 if k % 2 else -0.8
        r.tube([(hx, by), (lerp(hx, fx, 0.5) + (k - 1.5) * 0.8, by + 3.0), (fx, fy - 0.4)], [1.2, 0.9, 0.6], "dwood", z,
               bias=0.0 if k % 2 else -0.3)
        r.dot(fx + 1, fy - 0.2, "dwood", 2, z)
    T = Xf(tilt, (0.0, by))
    w, h = 9.0, 18.0
    r.poly([T(-w + lean, by), T(w + lean, by), T(w + lean, by - h), T(-w + lean, by - h)], "dwood", 0.0, curve=0.5)
    r.poly([T(-w - 1.4 + lean, by - h), T(w + 1.4 + lean, by - h), T(lean, by - h - 6.0)], "dwood", 0.1, normal=(-0.3, -0.7, 0.6))
    r.line(*T(-w - 1.4 + lean, by - h), *T(lean, by - h - 6.0), "gold", 0.15, tone=3)
    r.dot(*T(lean, by - h - 6.6), "gold", 4, 0.16)
    # open triptych doors on either side, votives burning inside them
    for sd in (-1, 1):
        x0 = sd * (w + 0.4) + lean
        r.poly([T(x0, by - 1.0), T(x0 + sd * 4.4, by - 2.0), T(x0 + sd * 4.4, by - h + 2.0), T(x0, by - h + 1.0)], "dwood",
               0.15 if sd > 0 else -0.5, bias=0.0 if sd > 0 else -0.25, curve=0.3)
        r.line(*T(x0 + sd * 4.4, by - 2.0), *T(x0 + sd * 4.4, by - h + 2.0), "gold", 0.16 if sd > 0 else -0.49, tone=3 if sd < 0 else 2)
        for yy in (by - 5.0, by - 11.0):
            vx, vy = T(x0 + sd * 2.2, yy)
            r.poly([(vx - 0.8, vy), (vx + 0.8, vy), (vx + 0.8, vy - 1.6), (vx - 0.8, vy - 1.6)], "votive", 0.17 if sd > 0 else -0.48)
            if not out: flame(r, vx, vy - 1.4, 1.8, ph + int(yy), "fire", 0.18 if sd > 0 else -0.47, wide=0.6)
    # shelves of votives: two rows each side of the case
    for row, yy in enumerate((by - 4.0, by - 14.0)):
        r.line(*T(-w + lean, yy + 0.6), *T(w + lean, yy + 0.6), "dwood", 0.2, tone=3)
        for k, xx in enumerate((-7.2, -4.8, 4.8, 7.2)):
            x, y = T(xx + lean, yy)
            r.poly([(x - 0.9, y), (x + 0.9, y), (x + 0.9, y - 1.8), (x - 0.9, y - 1.8)], "votive", 0.3)
            if not out:
                flame(r, x, y - 1.6, 2.0, ph + k + row, "fire", 0.4, wide=0.7)
    # the glass case with the weeping skull
    cx, cy = T(lean, by - 9.5)
    r.poly([(cx - 2.8, cy + 3.6), (cx + 2.8, cy + 3.6), (cx + 2.8, cy - 4.0), (cx - 2.8, cy - 4.0)], "glass", 0.5, bias=-0.2)
    r.ell(cx, cy - 0.6, 2.0, 2.2, "bone", 0.6)
    r.dot(cx - 0.8, cy - 0.8, "soot", 0, 0.7); r.dot(cx + 0.8, cy - 0.8, "soot", 0, 0.7)
    r.line(cx - 0.8, cy + 1.2, cx + 0.8, cy + 1.2, "soot", 0.7, tone=1)
    for i in range(weep):
        r.dot(cx - 0.8, cy + 0.2 + i * 1.4, "gold", 4 if i % 2 == 0 else 3, 0.75)
        r.dot(cx + 0.8, cy + 0.6 + i * 1.4, "gold", 3, 0.75)
    r.line(cx - 3.0, cy - 4.2, cx + 3.0, cy - 4.2, "gold", 0.8, tone=3)
    r.line(cx - 3.0, cy + 3.8, cx + 3.0, cy + 3.8, "gold", 0.8, tone=2)
    if sheen:
        glow_ring(r, cx, cy - 16.0, 3.0, "sigil", 2.0, 3, 1.0)
    if extra: extra(r)
    return r.resolve()


@scaled(1.12)
def reliquary_sheet(outdir):
    Rq = reliquary
    idle = [Rq(bob=[0, -0.3, -0.5, -0.3][i], ph=i) for i in range(4)]
    run = []
    for i in range(6):
        a = i / 6.0 * math.tau
        feet = tuple((x + 1.4 * math.cos(a + k * 1.6), -max(0.0, math.sin(a + k * 1.6))) for k, x in enumerate((-5.0, -1.5, 2.0, 5.5)))
        run.append(Rq(feet=feet, lean=0.4, tilt=2 * math.sin(a), bob=-0.5 * abs(math.sin(a)), ph=i))
    fan = [Rq(tilt=-3, ph=0), Rq(tilt=-6, lean=-0.6, ph=1), Rq(tilt=4, lean=0.6, ph=2, extra=lambda r: _votive_burst(r, 0)),
           Rq(tilt=6, lean=0.8, ph=3, extra=lambda r: _votive_burst(r, 1)), Rq(tilt=2, ph=4), Rq(ph=5)]
    anoint = [Rq(ph=0, weep=1), Rq(ph=1, weep=2, bob=0.5), Rq(ph=2, weep=3, bob=1.0, sheen=True),
              Rq(ph=3, weep=3, bob=1.0, sheen=True, extra=lambda r: glow_ring(r, 0, -1.0, 12, "sigil", -3, 3, 3.0)),
              Rq(ph=4, weep=2, bob=0.5, sheen=True, extra=lambda r: glow_ring(r, 0, -1.0, 16, "sigil", -3, 2, 4.0)),
              Rq(ph=5, weep=1), Rq(ph=0)]
    knock = Rq(tilt=-10, lean=-1.0, ph=2)
    d0 = Rq(tilt=-14, lean=-1.2, ph=1, weep=3)
    d1 = Rq(tilt=-40, bob=3.0, ph=3, out=True)
    anims = [("Idle", idle, [0.18, 0.15, 0.18, 0.15]), ("Run", run, [0.1] * 6),
             ("Fan", fan, [0.1, 0.1, 0.08, 0.06, 0.1, 0.12]),
             ("Anoint", anoint, [0.1, 0.12, 0.12, 0.08, 0.12, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, reliquary_corpse(), reliquary_corpse()], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("VhReliquary", anims, outdir, scale=5)


def _votive_burst(r, k):
    for i, a in enumerate((-15, 0, 15)):
        d = 9 + k * 5
        flame(r, 6 + d * math.cos(math.radians(a)), -12 + d * math.sin(math.radians(a)), 2.4, i + k, "fire", 4.0, lean=1.5)


def reliquary_corpse():
    r = Rig()
    r.poly([(-10, -1), (8, -1), (8, -7), (-10, -7)], "dwood", 0.0)
    r.poly([(8, -1), (13, -4), (8, -7)], "dwood", 0.1)
    r.ell(0, -4, 2.0, 2.0, "bone", 0.5)
    for x in (-7, -4, 4):
        r.dot(x, -1.6, "votive", 2, 0.6)
    smoke_curl(r, -4, -8, 1, 1.0)
    return r.resolve()


JOBS = [("VhBroodMother", mother_sheet), ("VhPyreTick", tick_sheet), ("VhAshSeraph", seraph_sheet),
        ("LanternWraith", wraith_sheet), ("VhChandelier", chandelier_sheet), ("VhReliquary", reliquary_sheet)]
SYNC = {
    "VhBroodMother": {"Slam": [("HEAD SLAM: box 22 x 16 at (16, -4); wax pool at (18, 0)", 3)],
                      "Spit": [("3 grublings leave the mouth (16, -10), land by the hero", 4)]},
    "VhPyreTick": {"Bite": [("BITE: box 15 x 14 at (14, -9)", 3)], "Spray": [("5 drops of burning blood leave the jaws (14, -10)", 4)]},
    "VhAshSeraph": {"Lance": [("THRUST: lance tip at (30, -15); box 34 x 10 at (17, -14)", 3)],
                    "Beat": [("the wings flare white: every fire within 50 px goes out", 2)]},
    "LanternWraith": {"Swing": [("soul orb leaves the lantern at (16, -18)", 3)], "Take": [("the cone: 50 px from the lantern (14, -15)", 3)]},
    "VhChandelier": {"Wheel": [("flame wheel live", 2), ("wax globs flung", 5)], "Drip": [("drips fall round the ring (r 30)", 0)],
                     "Flare": [("every candle flares: the ring lights", 1)]},
    "VhReliquary": {"Fan": [("votive flames leave the case at (6, -16)", 2)], "Anoint": [("the skull weeps: kin within 50 px anointed", 3)]},
}
NOTES = {"LanternWraith": "IdleFull / RunFull: the lantern holds the hero's stolen soul flame (a warm flame beside the teal one).",
         "VhChandelier": "Idle / Run hang low; IdleHigh / RunHigh hang 9 px higher (shorter chain, smaller shadow). The chain runs "
                         "off the top of the cell."}

# These sheets are drawn bigger than their rig units (the scaled() factor): the points in their sync rows above are in
# rig units, so multiply them by the factor for pixels (the kits' offsets in VhorrulPack.cs already are).
for _n, _k in (("TallowColossus", 1.1), ("VhPyreTick", 1.4), ("MothMatron", 1.08), ("Chandler", 1.12), ("VhPyreWarden", 1.26), ("VhRenderer", 1.45), ("VhWickHag", 1.16), ("VhCandleWyrm", 1.14),
               ("VhFuseScorpion", 1.35), ("VhAshSeraph", 1.19), ("LanternWraith", 1.45), ("VhReliquary", 1.12)):
    NOTES[_n + " (scale)"] = "drawn at %.2fx its rig units: sync points above are rig units (x %.2f for pixels)." % (_k, _k)
