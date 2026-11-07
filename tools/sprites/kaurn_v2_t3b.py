"""Kaurn tier 3 (Stormcaller, Leyden Golem and Arc Lantern lines): Storm Herald, Scarab Magus, Storm Orrery, Voltaic Pile,
Tesla Spire, Static Moth (built through kaurn_v2_rigs.py). T3 idle limit 42 x 40."""
import math
from kaurn_v2_rigs import (Rig, lerp, ik, msheet, tail_anims, leg, arm, bolt, crackle, spark, eye, shadow, rod, dust_puff, zig,
                           line_px)


# ================================================================== STORM HERALD: a tall herald, blue tabard, lightning lance, brass horn
def herald(bob=0.0, lean=0.0, feet=((-3.0, 0.0), (3.0, 0.0)), lance=(8.0, -15.0), lance_ang=-72.0, horn=0.0, blow=0, hurt=False,
           sparks=(), extra=None, bolt_to=None, cape=0.0):
    """lance: the near hand's grip; lance_ang: its angle (-90 upright, 0 thrust forward); horn: 0..1 the horn raised to the
    lips; blow: 1..3 sound rings out of the bell."""
    r = Rig()
    by = -16.0 + bob
    tx = lean * 0.5
    # cape behind
    r.poly([(tx - 4.5, by - 12.0), (tx + 1.0, by - 12.0), (tx - 3.0 - cape, by + 15.0), (tx - 12.0 - cape, by + 15.5)], "tabard", -2.0, bias=-0.3,
           normal=(-0.3, -0.2, 1.0))
    for k, f in enumerate(feet):
        z = -1.0 if k == 0 else 1.5
        leg(r, (tx * 0.4 + (-2.0 if k == 0 else 2.0), by + 6.0), f, 5.6, 5.4, "iron", z, rad=(1.8, 1.4), boot="dkiron", boot_len=3.0,
            bias=-0.3 if k == 0 else 0.0)
    # body: steel cuirass under a long blue tabard with a brass bolt sigil
    P = r.part(False, 0.0)
    r.ell(tx, by - 4.0, 5.4, 8.4, "iron", 0.0, bias=0.05, part=P)
    r.poly([(tx - 3.8, by - 9.0), (tx + 4.2, by - 9.0), (tx + 5.0, by + 9.0), (tx - 4.6, by + 9.0)], "tabard", 0.3, curve=0.7)
    r.polyline([(tx + 0.8, by - 6.0), (tx - 0.6, by - 2.0), (tx + 1.6, by - 1.5), (tx + 0.0, by + 3.0)], "brass", 0.35, tone=4)
    r.polyline([(tx - 4.6, by + 9.0), (tx + 5.0, by + 9.0)], "brass", 0.35, tone=2)
    r.ell(tx + 0.5, by - 11.0, 7.6, 3.0, "iron", 0.2, bias=0.2)                         # pauldrons
    # helm: tall, winged, a T visor with storm eyes
    hx, hy = tx + 1.0 + lean * 0.6, by - 16.0
    r.ell(hx, hy, 3.4, 3.8, "iron", 0.6, bias=0.15)
    r.poly([(hx - 1.0, hy - 3.0), (hx + 1.0, hy - 3.0), (hx + 0.2, hy - 7.0)], "brass", 0.65, bias=0.2)     # crest
    r.poly([(hx - 3.0, hy - 1.0), (hx - 7.0, hy - 5.0), (hx - 3.6, hy + 0.5)], "brass", 0.55, bias=0.0)     # wing
    r.polyline([(hx + 0.0, hy - 0.5), (hx + 3.4, hy - 0.5)], "dkiron", 0.7, tone=0)
    r.polyline([(hx + 2.0, hy - 0.5), (hx + 2.0, hy + 2.0)], "dkiron", 0.7, tone=0)
    r.dot(hx + 1.0, hy - 0.5, "storm", 2 if hurt else 4, 0.75); r.dot(hx + 3.0, hy - 0.5, "storm", 2 if hurt else 3, 0.75)
    # far arm with the brass horn
    hp = (lerp(tx - 4.0, hx + 2.0, horn), lerp(by - 4.0, hy + 1.5, horn))
    r.tube([(tx - 4.0, by - 10.0), (lerp(tx - 6.0, tx - 1.0, horn), lerp(by - 6.0, by - 9.0, horn)), hp], [1.6, 1.3, 1.2], "iron", -0.5 + horn * 1.5,
           bias=-0.3 + 0.3 * horn, thin=True)
    bell = (hp[0] + 4.0 + horn * 1.0, hp[1] - 1.0 - horn * 2.0)
    r.tube([hp, bell], [0.7, 1.4], "brass", -0.4 + horn * 1.6, bias=0.2, thin=True)
    r.ell(bell[0] + 0.5, bell[1], 1.2, 2.0, "brass", -0.35 + horn * 1.6, bias=0.3, thin=True)
    if blow:
        for k in range(blow):
            R = 3.0 + k * 3.0
            for i in range(7):
                a = math.radians(-60 + i * 20)
                r.dot(bell[0] + 2 + R * math.cos(a), bell[1] + R * math.sin(a), "brass", 4 if k == 0 else 3, 6.0)
    # near arm and the lance: an iron shaft, a copper fork, lightning at the tip
    lx, ly = lance
    a = math.radians(lance_ang)
    ca, sa = math.cos(a), math.sin(a)
    b0 = (lx - 9.0 * ca, ly - 9.0 * sa)
    tip = (lx + 17.0 * ca, ly + 17.0 * sa)
    r.tube([b0, tip], [0.8, 0.7], "iron", 2.0, bias=0.15, thin=True)
    fk = (lx + 14.0 * ca, ly + 14.0 * sa)
    for side in (-1, 1):
        r.polyline([fk, (fk[0] + 3.5 * ca - side * 1.6 * sa, fk[1] + 3.5 * sa + side * 1.6 * ca)], "copper", 2.05, tone=3)
    r.dot(tip[0], tip[1], "storm", 4, 2.1); r.dot(tip[0] - ca, tip[1] - sa, "storm", 3, 2.1)
    r.tube([(tx + 4.0, by - 10.0), (lerp(tx + 4.0, lx, 0.5) + 1.0, lerp(by - 10.0, ly, 0.5) + 1.5), (lx, ly)], [1.8, 1.4, 1.3], "iron", 2.2,
           thin=True)
    r.ell(lx, ly, 1.3, 1.3, "iron", 2.3, bias=0.2, thin=True)
    if bolt_to:
        bolt(r, tip, bolt_to, z=6.0, n=5, amp=1.6, seed=int(bolt_to[0]), fork=1)
    for (x, y, k) in sparks: spark(r, x, y, k)
    if extra: extra(r)
    return r.resolve()


def herald_sheet(outdir):
    H = herald
    idle = [H(bob=[0, -0.4, -0.8, -0.4][i], lance=(8.0, -15.0 + [0, -0.4, -0.8, -0.4][i]), cape=[0, 0.5, 1, 0.5][i]) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        f1 = (3.6 * math.cos(ph), -max(0.0, 2.0 * math.sin(ph)))
        f2 = (-3.6 * math.cos(ph), -max(0.0, -2.0 * math.sin(ph)))
        run.append(H(lean=1.0, bob=-0.8 * abs(math.sin(ph)), feet=(f2, f1), lance=(7.5, -16.0), lance_ang=-70, cape=1.5 + math.sin(ph)))
    ln = [H(lance=(5.0, -18.0), lance_ang=-60), H(lance=(2.0, -18.0), lance_ang=-20, lean=-1.5, sparks=[(18, -22, 3)]),
          H(lance=(1.0, -18.0), lance_ang=-5, lean=-2.0, sparks=[(18, -19, 2)]),
          H(lance=(9.0, -18.0), lance_ang=0, lean=2.0, bolt_to=(34.0, -19.0)), H(lance=(9.0, -18.0), lance_ang=0, lean=1.5, sparks=[(28, -19, 2)]),
          H(lance=(7.0, -17.0), lance_ang=-50, lean=0.5), H()]
    hn = [H(), H(horn=0.4), H(horn=0.8, lean=-0.5), H(horn=1.0, lean=-1.0, bob=-0.5), H(horn=1.0, blow=1, lean=0.5),
          H(horn=1.0, blow=2, lean=0.5), H(horn=1.0, blow=3, lean=0.5), H(horn=0.6, blow=1), H(horn=0.2)]
    d0 = H(hurt=True, lean=-2.0, lance=(5.0, -14.0), lance_ang=-110)
    d1 = H(hurt=True, lean=-4.0, bob=4.0, lance=(2.0, -10.0), lance_ang=-150)
    d2 = herald_corpse(0)
    corpse = herald_corpse(1)
    knock = H(hurt=True, lean=-3.0, lance=(5.0, -15.0), lance_ang=-115)
    anims = [("Idle", idle, [0.18, 0.14, 0.18, 0.14]), ("Run", run, [0.08] * 6),
             ("Lance", ln, [0.12, 0.12, 0.1, 0.06, 0.12, 0.12, 0.12]),
             ("Horn", hn, [0.1, 0.1, 0.1, 0.1, 0.08, 0.1, 0.12, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return msheet("KrnStormHerald", anims, outdir)


def herald_corpse(stage):
    r = Rig()
    r.poly([(-14.0, -5.0), (6.0, -5.0), (7.0, 0.0), (-15.0, 0.0)], "tabard", 0.0, curve=0.6)
    r.ell(-2.0, -4.0, 8.0, 3.0, "iron", 0.2, bias=0.1)
    r.ell(10.0, -3.0, 3.4, 3.0, "iron", 0.4, bias=0.15)
    r.poly([(13.0, -4.0), (16.0, -7.0), (13.5, -2.0)], "brass", 0.5)
    r.tube([(-16.0, -1.0), (16.0, -8.0)], [0.6, 0.6], "iron", 1.0, thin=True)
    r.ell(-12.0, -1.5, 1.2, 1.8, "brass", 1.1)
    if stage == 0: spark(r, 16.0, -9.0, 1)
    return r.resolve()


# ================================================================== SCARAB MAGUS: a beetle sorcerer, its shell a cloak
def magus(bob=0.0, lean=0.0, open_=0.2, hands=((7.0, -18.0), (-6.0, -17.0)), orb=None, balls=(), hurt=False, sparks=(), extra=None,
          feet=((-3.0, 0.0), (3.0, 0.0)), glow=1.0):
    """open_: 0..1 the shell parts like a cloak, showing the lightning core inside; balls: released orbs."""
    r = Rig()
    by = -15.0 + bob
    tx = lean * 0.5
    # the shell halves behind (they swing out as it opens)
    for side in (-1, 1):
        sw = open_ * 9.0
        x0 = tx + side * (2.0 + sw * 0.5) - 1.0
        pts = [(tx - 1.0, by - 14.0), (x0 + side * (7.5 + sw), by - 10.0), (x0 + side * (9.0 + sw * 1.2), by + 2.0),
               (x0 + side * (6.0 + sw * 0.8), by + 14.0), (tx - 1.0 + side * 1.0, by + 14.0)]
        r.poly(pts, "scarab", -2.0 if side < 0 else -1.5, bias=0.15 if side > 0 else -0.1,
               normal=(-0.4 * side - 0.2, -0.4, 0.8), curve=0.5)
        # gold markings on the shell
        for k in range(3):
            y = by - 6.0 + k * 6.0
            r.polyline([(x0 + side * (4.0 + sw * 0.6), y), (x0 + side * (6.5 + sw), y + 1.5)], "gold", -1.4 if side > 0 else -1.9, tone=3)
    if open_ > 0.2:
        # the lightning core exposed between the halves
        r.ell(tx - 1.0, by - 2.0, 3.0 + open_ * 2, 7.0, "storm", -1.0, flat=2)
        bolt(r, (tx - 1.0, by + 5.0), (tx - 1.5, by - 9.0), z=-0.9, n=4, amp=1.6, seed=int(open_ * 10), glow=None)
    # legs: four thin chitin legs under the shell, two arms out front
    for k, f in enumerate(feet):
        z = -1.0 if k == 0 else 0.8
        leg(r, (tx + (-2.0 if k == 0 else 2.0), by + 6.0), f, 5.0, 4.8, "dkiron", z, rad=(1.4, 1.0), boot="dkiron", boot_len=2.4,
            bias=-0.3 if k == 0 else 0.0, thin=True)
    # body: an upright segmented abdomen
    P = r.part(False, 0.0)
    r.ell(tx, by - 1.0, 4.6, 8.0, "dkiron", 0.0, bias=0.1, part=P)
    for k in range(4): r.polyline([(tx - 3.0, by - 5.0 + k * 3.0), (tx + 3.4, by - 4.4 + k * 3.0)], "gold", 0.1, tone=2 if k % 2 else 3)
    # head: horned beetle head with mandibles, storm eyes
    hx, hy = tx + 1.0 + lean * 0.6, by - 11.0
    r.ell(hx, hy, 3.6, 3.0, "dkiron", 0.6, bias=0.25)
    r.tube([(hx + 0.5, hy - 2.0), (hx + 2.5, hy - 6.0), (hx + 1.0, hy - 8.5)], [1.4, 0.9, 0.4], "gold", 0.65, bias=0.1)
    r.polyline([(hx + 2.6, hy + 2.0), (hx + 4.6, hy + 2.6), (hx + 4.0, hy + 3.6)], "gold", 0.7, tone=3)
    r.dot(hx + 1.0, hy - 0.5, "storm", 2 if hurt else 4, 0.75); r.dot(hx + 2.6, hy - 0.5, "storm", 2 if hurt else 3, 0.75)
    # arms with lightning between the hands
    near, far = hands
    r.tube([(tx - 3.0, by - 7.0), (lerp(tx - 3.0, far[0], 0.5), lerp(by - 7.0, far[1], 0.5) + 1.5), far], [1.2, 1.0, 0.9], "dkiron", -0.5,
           bias=-0.3, thin=True)
    r.tube([(tx + 3.5, by - 7.0), (lerp(tx + 3.5, near[0], 0.5), lerp(by - 7.0, near[1], 0.5) + 1.5), near], [1.3, 1.1, 1.0], "dkiron", 2.0,
           thin=True)
    for hp in (near, far):
        r.ell(hp[0], hp[1], 1.4 * glow, 1.4 * glow, "storm", 2.1 if hp is near else -0.4, flat=3)
    if glow > 0.8 and orb is None:
        bolt(r, near, far, z=1.9, n=3, amp=1.2, seed=int(bob * 10 + 3), glow=None, core=3)
    if orb:
        r.ell(orb[0], orb[1], 2.6, 2.6, "storm", 5.0, flat=2); r.ell(orb[0], orb[1], 1.6, 1.6, "storm", 5.1, flat=4)
    for (x, y) in balls:
        r.ell(x, y, 3.0, 3.0, "storm", 5.0, flat=2); r.ell(x, y, 1.8, 1.8, "spark", 5.1, flat=4)
    for (x, y, k) in sparks: spark(r, x, y, k)
    if extra: extra(r)
    return r.resolve()


def magus_sheet(outdir):
    Mg = magus
    idle = [Mg(bob=[0, -0.4, -0.8, -0.4][i], glow=[1.0, 1.1, 1.0, 0.9][i], open_=0.25) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        f1 = (3.2 * math.cos(ph), -max(0.0, 1.8 * math.sin(ph)))
        f2 = (-3.2 * math.cos(ph), -max(0.0, -1.8 * math.sin(ph)))
        run.append(Mg(lean=1.0, bob=-0.6 * abs(math.sin(ph)), feet=(f2, f1), open_=0.1 + 0.08 * math.sin(ph)))
    ob = [Mg(hands=((5.0, -17.0), (-4.0, -17.0))), Mg(hands=((1.0, -20.0), (-3.0, -21.0)), glow=1.4, orb=(-1.0, -24.0), lean=-1.0),
          Mg(hands=((6.0, -19.0), (0.0, -20.0)), glow=1.4, orb=(5.0, -22.0)),
          Mg(hands=((11.0, -18.0), (6.0, -18.0)), lean=2.0, orb=(14.0, -17.0), sparks=[(14, -17, 1)]),
          Mg(hands=((10.0, -17.0), (2.0, -17.0)), lean=1.0, glow=0.7), Mg()]
    kd = [Mg(open_=0.1), Mg(open_=0.3, bob=-0.5), Mg(open_=0.6, bob=-1.0, sparks=[(-1, -32, 2)]), Mg(open_=0.9, bob=-1.2, glow=1.5),
          Mg(open_=1.0, bob=-1.2, glow=1.5, sparks=[(-1, -12, 1)]),
          Mg(open_=1.0, glow=0.6, balls=[(12.0, -22.0), (12.0, -10.0)], hands=((10.0, -20.0), (8.0, -12.0))),
          Mg(open_=0.7, glow=0.6, balls=[(17.0, -24.0), (17.0, -8.0)], hands=((9.0, -19.0), (6.0, -14.0))), Mg(open_=0.3), Mg()]
    d0 = Mg(hurt=True, lean=-2.0, open_=0.3, glow=0.4)
    d1 = Mg(hurt=True, lean=-4.0, bob=4.0, open_=0.8, glow=0.2)
    d2 = magus_corpse(0)
    corpse = magus_corpse(1)
    knock = Mg(hurt=True, lean=-3.0, open_=0.4, glow=0.5)
    anims = [("Idle", idle, [0.16, 0.12, 0.16, 0.12]), ("Run", run, [0.08] * 6),
             ("Orb", ob, [0.12, 0.12, 0.1, 0.06, 0.12, 0.12]),
             ("Kindle", kd, [0.1, 0.1, 0.1, 0.1, 0.08, 0.06, 0.12, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return msheet("KrnScarabMagus", anims, outdir)


def magus_corpse(stage):
    r = Rig()
    # on its back, the shell split open, legs curled
    r.ell(0.0, -4.0, 12.0, 4.0, "scarab", 0.0, bias=0.1)
    r.polyline([(-10.0, -5.0), (10.0, -6.0)], "gold", 0.1, tone=3)
    r.ell(13.0, -3.0, 3.0, 2.6, "scarab", 0.4, bias=0.1)
    for i in range(4):
        r.polyline([(-6.0 + i * 4, -8.0), (-7.0 + i * 4, -11.0 + stage), (-5.5 + i * 4, -12.0 + stage)], "dkiron", 0.5, tones=[2, 1])
    if stage == 0: r.ell(0.0, -6.0, 2.0, 1.0, "storm", 0.6, flat=2); spark(r, 0.0, -11.0, 2)
    return r.resolve()


# ================================================================== STORM ORRERY: a floating brass orrery round a lightning core
PLANETS = ("pred", "pgreen", "pviol")


def orrery(hover=9.0, spin=0.0, align=0.0, core=1.0, fling=None, hurt=False, sparks=(), extra=None, tilt=0.0, beam=False, rings=1.0):
    """spin: ring rotation; align: 0..1 the three planets slide into a horizontal line pointing forward."""
    r = Rig()
    shadow(r, 0.0, 0.0, 6.0)
    cy = -hover - 14.0
    # a brass stand-off stem and the base ring under it (it floats)
    # a dark iron armature: a stand with a brass foot, a meridian hoop round the core, an iron cage of bands
    r.ell(0.0, cy + 14.0, 5.0, 1.8, "brass", -0.5, bias=0.15)
    r.poly([(-2.2, cy + 13.5), (2.2, cy + 13.5), (1.2, cy + 5.0), (-1.2, cy + 5.0)], "dkiron", -0.45, normal=(-0.3, -0.2, 1.0), curve=0.6)
    for i in range(60):
        a = i / 60 * math.tau
        x, y = 5.6 * math.cos(a) * 0.35, cy + 6.4 * math.sin(a) * 1.0
        front = math.cos(a) > 0
        r.dot(x + 4.2 * math.cos(a) * 0.0, y, "dkiron", 3 if math.sin(a) < 0 else 2, 0.6 if front else -0.6)
    for i in range(40):
        a = i / 40 * math.tau
        r.dot(6.0 * math.cos(a), cy + 2.0 * math.sin(a), "dkiron", 3 if math.sin(a) > 0 else 1, 0.62 if math.sin(a) > 0 else -0.6)
    r.ell(0.0, cy - 6.8, 1.6, 1.2, "dkiron", 0.65, bias=0.3)
    # the core
    cr = 4.2 * core
    r.ell(0.0, cy, cr + 1.4, cr + 1.4, "storm", 0.0, flat=2)
    r.ell(0.0, cy, cr, cr, "storm", 0.1, flat=3)
    r.dot(-0.8, cy - 0.8, "storm", 4, 0.2)
    bolt(r, (-cr, cy + 1), (cr, cy - 1), z=0.15, n=2, amp=1.0, seed=int(spin * 3), glow=None)
    # three rings, each tilted differently, each carrying a planet
    tilts = (20.0 + tilt, -35.0 + tilt, 75.0 + tilt)
    radii = (14.5, 12.0, 9.5)
    for k in range(3):
        R = radii[k] * rings
        ta = math.radians(tilts[k])
        flat_y = 0.38
        n = int(R * 6)
        for i in range(n):
            a = i / n * math.tau
            x, y = R * math.cos(a), R * math.sin(a) * flat_y
            xx, yy = x * math.cos(ta) - y * math.sin(ta), x * math.sin(ta) + y * math.cos(ta)
            front = math.sin(a) > 0
            t = (3 if math.cos(a + 0.8) > 0 else 2) if front else 1
            zz = 1.0 + k * 0.01 if front else -1.0
            r.dot(xx, cy + yy, "brass", t, zz)
            r.dot(xx, cy + yy + 1, "brass", max(0, t - 2), zz - 0.001)
        # the planet: rides the ring, or slides into the line
        pa = spin * (1.0 + k * 0.4) + k * 2.1
        x, y = R * math.cos(pa), R * math.sin(pa) * flat_y
        px_, py_ = x * math.cos(ta) - y * math.sin(ta), x * math.sin(ta) + y * math.cos(ta)
        lx, ly = 6.0 + k * 6.5, 0.0
        px_, py_ = lerp(px_, lx, align), lerp(py_, ly, align)
        front = math.sin(pa) > 0 or align > 0.5
        pr = 2.2 - k * 0.3
        r.ell(px_, cy + py_, pr, pr, PLANETS[k], 2.0 if front else -1.5, bias=0.2)
    if align > 0.6:
        for i in range(4, 26, 2): r.dot(i, cy, "storm", 3 if i % 4 else 4, 3.0)
    if beam:
        for i in range(0, 34): r.dot(i + 4, cy + (1 if i % 7 == 3 else 0), "storm", 4, 3.2)
        for i in range(0, 34, 2): r.dot(i + 4, cy - 1, "storm", 2, 3.1); r.dot(i + 5, cy + 1, "storm", 2, 3.1)
    if fling:
        r.ell(fling[0], fling[1], 2.4, 2.4, "storm", 5.0, flat=3); r.dot(fling[0], fling[1], "storm", 4, 5.1)
    # two storm eyes on the core
    r.dot(0.5, cy - 0.5, "dkiron", 1 if hurt else 0, 0.3); r.dot(2.0, cy - 0.5, "dkiron", 1 if hurt else 0, 0.3)
    for (x, y, k) in sparks: spark(r, x, y, k)
    if extra: extra(r)
    return r.resolve()


def orrery_sheet(outdir):
    O = orrery
    idle = [O(hover=9.0 + [0, 0.6, 1.0, 0.6][i], spin=i * 0.4) for i in range(4)]
    run = [O(hover=9.5 + 0.6 * math.sin(i / 6 * math.tau), spin=i * 0.5, tilt=8.0) for i in range(6)]
    fl = [O(spin=0.0, core=1.2), O(spin=0.6, core=1.4, sparks=[(6, -24, 3)]), O(spin=1.4, core=1.5, fling=(10.0, -21.0)),
          O(spin=2.4, core=0.8, fling=(16.0, -21.0), sparks=[(16, -21, 1)]), O(spin=3.0, core=0.9), O(spin=3.4)]
    al = [O(spin=0.0), O(spin=1.0, core=1.2), O(spin=2.4, core=1.3, rings=1.05), O(spin=4.2, core=1.4, rings=1.05, sparks=[(0, -34, 2)]),
          O(spin=5.0, core=1.4, align=0.3), O(spin=5.4, core=1.5, align=0.6), O(spin=5.6, core=1.5, align=0.85), O(spin=5.7, core=1.6, align=1.0),
          O(spin=5.7, core=0.8, align=1.0, beam=True, sparks=[(38, -21, 1)]), O(spin=6.0, core=0.9, align=0.4)]
    d0 = O(hurt=True, tilt=-15, core=0.6)
    d1 = O(hurt=True, tilt=-35, core=0.4, hover=3.0, rings=0.9, sparks=[(4, -14, 1)])
    d2 = orrery_corpse(0)
    corpse = orrery_corpse(1)
    knock = O(hurt=True, tilt=-20, core=0.7)
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.08] * 6),
             ("Fling", fl, [0.12, 0.12, 0.1, 0.06, 0.12, 0.12]),
             ("Align", al, [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.08, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return msheet("KrnStormOrrery", anims, outdir)


def orrery_corpse(stage):
    r = Rig()
    for k, (cx, R) in enumerate(((-6.0, 7.0), (5.0, 6.0), (0.0, 9.0))):
        for i in range(int(R * 6)):
            a = i / (R * 6) * math.tau
            r.dot(cx + R * math.cos(a), -2.0 + R * 0.3 * math.sin(a), "brass", 2 if math.sin(a) > 0 else 1, k * 0.1)
    for k, (x, m) in enumerate(((-10.0, "pred"), (9.0, "pgreen"), (14.0, "pviol"))):
        r.ell(x + stage * (k - 1), -1.6, 1.8, 1.6, m, 1.0, bias=0.2)
    r.ell(0.0, -2.0, 2.4, 2.0, "dkiron", 0.5)
    if stage == 0: spark(r, 0.0, -6.0, 2)
    return r.resolve()


# ================================================================== VOLTAIC PILE: a tower of copper and zinc discs, a lightning whip
def pile(bob=0.0, lean=0.0, feet=((-4.0, 0.0), (4.0, 0.0)), lit=0, whip=None, flash=False, hand=(13.0, -20.0), hurt=False, sparks=(),
         extra=None, sway=0.0):
    """lit: 0..9 discs lit from the bottom (Surge); flash: every disc white; whip: points of the lash from the hand."""
    r = Rig()
    by = -6.0 + bob
    for k, f in enumerate(feet):
        z = -1.0 if k == 0 else 1.5
        leg(r, (lean * 0.3 + (-3.0 if k == 0 else 3.0), by), f, 3.6, 3.4, "copper", z, rad=(2.0, 1.6), boot="dkiron", boot_len=3.0,
            bias=-0.3 if k == 0 else 0.0)
    # the base plate
    r.ell(lean * 0.3, by - 1.0, 7.5, 2.2, "dkiron", 0.0, bias=0.1)
    # the stack: alternating copper and zinc discs with green brine cloth between
    n = 8
    dy = 3.0
    for i in range(n):
        y = by - 3.0 - i * dy
        x = lean * (i / n) + sway * math.sin(i * 0.7)
        w = 8.6 - abs(i - 3.5) * 0.3
        mat = "copper" if i % 2 == 0 else "zinc"
        p = r.part(False, 0.1 + i * 0.01)
        r.ell(x, y, w, 1.6, mat, 0.1 + i * 0.01, bias=0.05, part=p)
        r.tube([(x - w + 0.5, y + 1.2), (x + w - 0.5, y + 1.2)], [0.6, 0.6], mat, 0.1 + i * 0.01, bias=-0.3, part=p)
        r.polyline([(x - w + 1.0, y + 2.0), (x + w - 1.0, y + 2.0)], "brine", 0.105 + i * 0.01, tone=2 if i % 2 else 3)
        if flash or i < lit:
            r.polyline([(x - w + 2.0, y - 0.2), (x + w - 2.0, y - 0.2)], "storm", 0.2 + i * 0.01, tone=4 if flash else 3)
    # the cap: a brass dome with storm eyes and a terminal spike
    tx, ty = lean + sway * math.sin(n * 0.7), by - 3.0 - n * dy - 0.5
    r.ell(tx, ty, 5.0, 3.0, "brass", 0.5, bias=0.15)
    r.tube([(tx, ty - 2.5), (tx, ty - 5.5)], [0.8, 0.4], "copper", 0.55, thin=True)
    r.dot(tx, ty - 6.0, "storm", 4, 0.6)
    r.dot(tx + 1.5, ty, "storm", 2 if hurt else 4, 0.6); r.dot(tx + 3.5, ty, "storm", 2 if hurt else 3, 0.6)
    # two arms out of the stack: the far one braced, the near one holding the whip's grip
    mid = by - 3.0 - 5 * dy
    r.tube([(lean * 0.6 - 7.5, mid), (lean * 0.6 - 13.5, mid + 4.0), (lean * 0.6 - 15.5, mid + 8.0)], [1.4, 1.2, 1.0], "copper", -1.0,
           bias=-0.3, thin=True)
    r.ell(lean * 0.6 - 15.5, mid + 8.5, 1.6, 1.4, "brass", -0.95, thin=True)
    r.tube([(lean * 0.6 + 7.5, mid), (lerp(lean * 0.6 + 6.0, hand[0], 0.5) + 1.0, lerp(mid, hand[1], 0.5) + 2.0), hand], [1.6, 1.3, 1.1], "copper",
           2.0, thin=True)
    r.ell(hand[0], hand[1], 1.5, 1.4, "brass", 2.1, bias=0.2, thin=True)
    if whip:
        pts = [hand] + list(whip)
        for i in range(len(pts) - 1):
            bolt(r, pts[i], pts[i + 1], z=5.0, n=2, amp=0.8, seed=i * 3 + int(pts[-1][0]), core=4 if i > len(pts) - 3 else 3)
    else:
        bolt(r, hand, (hand[0] + 2.0, hand[1] + 6.0 + bob), z=2.2, n=3, amp=1.0, seed=int(bob * 5), glow=None, core=3)
    for (x, y, k) in sparks: spark(r, x, y, k)
    if extra: extra(r)
    return r.resolve()


def pile_sheet(outdir):
    P = pile
    idle = [P(bob=[0, 0.3, 0.6, 0.3][i], sway=[0, 0.3, 0, -0.3][i], hand=(14.0, -20.0 + [0, 0.3, 0.6, 0.3][i])) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        f1 = (3.6 * math.cos(ph), -max(0.0, 1.8 * math.sin(ph)))
        f2 = (-3.6 * math.cos(ph), -max(0.0, -1.8 * math.sin(ph)))
        run.append(P(lean=1.5, bob=-0.7 * abs(math.sin(ph)), feet=(f2, f1), sway=0.6 * math.sin(ph), hand=(13.5, -20.0)))
    wh = [P(hand=(6.0, -25.0)), P(hand=(2.0, -30.0), lean=-1.5, whip=[(-6.0, -34.0), (-12.0, -30.0)]),
          P(hand=(4.0, -31.0), lean=-1.0, whip=[(0.0, -38.0), (-6.0, -38.0)], sparks=[(-6, -38, 2)]),
          P(hand=(12.0, -24.0), lean=2.0, whip=[(22.0, -22.0), (34.0, -18.0), (40.0, -16.0)], sparks=[(40, -16, 1)]),
          P(hand=(12.0, -23.0), lean=1.5, whip=[(20.0, -16.0), (26.0, -10.0)]), P(hand=(10.0, -22.0), lean=0.5), P()]
    sg = [P(lit=k, bob=-0.2 * k, sparks=[(0, -34 + 0, 3)] if k > 6 else ()) for k in (0, 1, 2, 3, 5, 7, 9)]
    sg += [P(flash=True, bob=-1.5, sparks=[(-9, -20, 1), (9, -12, 1), (0, -40, 1)]), P(lit=2)]
    d0 = P(hurt=True, lean=-2.0, sway=1.0)
    d1 = P(hurt=True, lean=-5.0, sway=2.0, bob=1.0, sparks=[(0, -30, 1)])
    d2 = pile_corpse(0)
    corpse = pile_corpse(1)
    knock = P(hurt=True, lean=-3.0, sway=1.5)
    anims = [("Idle", idle, [0.16, 0.12, 0.16, 0.12]), ("Run", run, [0.08] * 6),
             ("Whip", wh, [0.12, 0.12, 0.1, 0.06, 0.12, 0.12, 0.12]),
             ("Surge", sg, [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.12, 0.08, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return msheet("KrnVoltaicPile", anims, outdir)


def pile_corpse(stage):
    r = Rig()
    # the stack toppled: discs fanned along the floor
    for i in range(9):
        x = -14.0 + i * 3.4 + (i % 2) * 0.5
        y = -2.0 - (0.6 if i % 3 == 0 else 0)
        r.ell(x, y, 1.8, 2.6, "copper" if i % 2 == 0 else "zinc", 0.1 + i * 0.01, bias=0.1)
    r.ell(17.0, -2.6, 3.0, 2.6, "brass", 0.4, bias=0.15)
    if stage == 0: spark(r, 0.0, -8.0, 1)
    return r.resolve()


# ================================================================== TESLA SPIRE: a walking Tesla coil on three iron legs
def spire(bob=0.0, lean=0.0, legs=(0.0, 0.0, 0.0), crown=1.0, flare=0, rooted=False, hurt=False, sparks=(), extra=None, aim=None):
    """legs: three foot offsets (x) for the walk; crown: torus glow; flare: 1..2 arcs leaping off the torus; aim: a beam point."""
    r = Rig()
    by = -12.0 + bob
    # three iron legs: back, far, near
    for k, (hx, fx0, z) in enumerate(((-2.0, -7.0, -1.5), (0.0, 1.0, -1.0), (2.0, 7.0, 1.5))):
        fx = fx0 + legs[k] + lean * 0.3
        fy = 0.0 if not rooted else 1.0
        kx, ky = ik(hx + lean * 0.5, by + 2.0, fx, fy - 1.0, 7.0, 6.5, 1 if k == 2 else -1)
        r.tube([(hx + lean * 0.5, by + 2.0), (kx, ky - 1.0), (fx, fy - 1.0)], [1.4, 1.0, 0.8], "iron", z, bias=-0.3 if z < 0 else 0.0, thin=True)
        r.poly([(fx - 1.6, fy - 1.0), (fx + 1.6, fy - 1.0), (fx + 0.6, fy - 0.0), (fx - 0.6, fy - 0.0)], "dkiron", z + 0.01)
        if rooted: r.dot(fx, -0.5, "storm", 3, z + 0.02)
    # the base housing
    r.ell(lean * 0.6, by + 1.0, 4.8, 2.4, "dkiron", 0.0, bias=0.15)
    # the wound column: a copper coil on a tall core
    top = by - 18.0
    cx = lean
    # the winding: bright copper turns over dark gaps, lit from the left like a cylinder
    P = r.part(True, 0.0)
    for y in range(int(top), int(by)):
        turn = (y - int(top)) % 2 == 0
        for x in range(-3, 4):
            if turn: t = 4 if x == -2 else 3 if x < 1 else 2 if x < 3 else 1
            else: t = 1 if x < 2 else 0
            r.put(cx + x + (0.5 if turn and x == 3 else 0), y, 0.0, "copper", 0.5, P, t)
    # a brass collar and the copper torus with its violet glow
    r.ell(cx, top + 0.5, 4.0, 1.4, "brass", 0.2, bias=0.15)
    tr = top - 3.0
    r.ell(cx, tr, 8.0, 3.2, "copper", 0.4, bias=0.1)
    r.ell(cx, tr, 4.8, 1.4, "violetg", 0.45, flat=2 if crown < 1.2 else 3)
    r.dot(cx - 2.0, tr - 0.5, "violetg", 4 if crown > 0.6 else 2, 0.5)
    r.dot(cx + 3.0, tr + 1.5, "storm", 2 if hurt else 4, 0.5); r.dot(cx + 5.0, tr + 1.2, "storm", 2 if hurt else 3, 0.5)
    r.tube([(cx, tr - 2.0), (cx, tr - 5.0)], [0.6, 0.4], "brass", 0.5, thin=True)
    r.dot(cx, tr - 5.5, "violetg", 4, 0.55)
    for k in range(flare):
        a = k * 2.3 + bob
        bolt(r, (cx + 7.0 * math.cos(a), tr + 2.0 * math.sin(a)), (cx + 11.0 * math.cos(a), tr - 4.0 + 3 * math.sin(a)), z=6.0, n=2, amp=1.0,
             seed=k * 5 + int(bob * 7), mat="violetg")
    if aim:
        bolt(r, (cx + 7.0, tr), aim, z=6.0, n=4, amp=1.4, seed=int(aim[0]), fork=1)
    for (x, y, k) in sparks: spark(r, x, y, k)
    if extra: extra(r)
    return r.resolve()


def spire_sheet(outdir):
    T = spire
    idle = [T(bob=[0, -0.3, -0.6, -0.3][i], crown=[1.0, 1.2, 1.4, 1.2][i], flare=i % 2) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        run.append(T(bob=-0.6 * abs(math.sin(ph)), lean=1.5, legs=(2.0 * math.cos(ph), 2.0 * math.cos(ph + 2.1), 2.0 * math.cos(ph + 4.2))))
    rl = [T(crown=1.2), T(crown=1.5, bob=0.8, flare=1), T(crown=1.8, bob=1.0, flare=2, sparks=[(0, -40, 2)]), T(crown=1.8, flare=2),
          T(crown=0.6, bob=-0.5, sparks=[(9, -35, 1)]), T(crown=0.8)]
    an = [T(crown=1.2), T(crown=1.4, bob=1.0, legs=(-1.0, 0.0, 1.0)), T(crown=1.6, bob=2.0, legs=(-2.0, 0.0, 2.0), rooted=True),
          T(crown=1.8, bob=2.0, legs=(-2.0, 0.0, 2.0), rooted=True, flare=2),
          T(crown=2.0, bob=1.5, legs=(-2.0, 0.0, 2.0), rooted=True, flare=2, sparks=[(-9, -38, 1), (9, -38, 1)]),
          T(crown=1.6, bob=2.0, legs=(-2.0, 0.0, 2.0), rooted=True, flare=1), T(crown=1.4, bob=2.0, legs=(-2.0, 0.0, 2.0), rooted=True),
          T(crown=1.4, bob=2.0, legs=(-2.0, 0.0, 2.0), rooted=True)]
    ro = [T(crown=1.4 + 0.2 * (i % 2), bob=2.0, legs=(-2.0, 0.0, 2.0), rooted=True, flare=1 + i % 2) for i in range(4)]
    d0 = T(hurt=True, lean=-2.0, crown=0.5)
    d1 = T(hurt=True, lean=-5.0, crown=0.3, bob=3.0, legs=(-3.0, 1.0, 3.0), sparks=[(-4, -30, 1)])
    d2 = spire_corpse(0)
    corpse = spire_corpse(1)
    knock = T(hurt=True, lean=-3.0, crown=0.6)
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.08] * 6),
             ("Relay", rl, [0.12, 0.1, 0.1, 0.1, 0.08, 0.12]),
             ("Answer", an, [0.1, 0.1, 0.1, 0.1, 0.08, 0.1, 0.1, 0.1]), ("Rooted", ro, [0.1] * 4)]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return msheet("KrnTeslaSpire", anims, outdir)


def spire_corpse(stage):
    r = Rig()
    for y in range(-5, -1):
        for x in range(-12, 8):
            r.put(x, y, 0.0, "copper", 0.2 - (y + 3) * 0.2, 1)
    for x in range(-11, 8, 2): r.polyline([(x, -5), (x, -2)], "copper", 0.05, tone=1)
    r.ell(11.0, -4.0, 3.0, 5.0, "copper", 0.4, bias=0.1)
    for k in range(3): r.tube([(-12.0, -3.0), (-16.0 + k * 2, -0.5 - k)], [1.0, 0.7], "iron", -0.2 + k * 0.1, thin=True)
    if stage == 0: r.dot(11.0, -4.0, "violetg", 3, 0.5); spark(r, 10.0, -11.0, 2, mat="violetg")
    return r.resolve()


# ================================================================== STATIC MOTH: a big moth, copper-dust wings, coil antennae
def moth(hover=8.0, flap=0.0, full=False, k=0, dart=None, drink=0.0, hurt=False, sparks=(), extra=None, tilt=0.0, wings=1.0):
    """flap: -1 (down) .. 1 (up); full: three sparks stored, its wings fizz white (Spark Fall)."""
    r = Rig()
    shadow(r, 0.0, 0.0, 5.5)
    by = -hover - 9.0
    # wings: a big forewing and a smaller hindwing each side, copper dust with a blue eye spot
    for side, z in ((-1, -2.0), (1, 1.5)):
        up = flap * 6.0 * wings
        root = (side * 1.0, by - 2.0)
        fw = [root, (side * 6.0, by - 13.0 - up), (side * 15.0 * wings, by - 12.0 - up * 0.8), (side * 14.0 * wings, by - 5.0 - up * 0.3),
              (side * 4.0, by + 0.0)]
        hw = [(side * 1.0, by + 0.0), (side * 11.0 * wings, by + 2.0 - up * 0.2), (side * 10.0 * wings, by + 8.0), (side * 3.0, by + 5.0)]
        bias = 0.05 if side > 0 else -0.3
        r.poly(hw, "mwing", z - 0.1, bias=bias - 0.1, normal=(-0.3 * side, -0.3, 0.9))
        r.poly(fw, "mwing", z, bias=bias, normal=(-0.3 * side, -0.4, 0.9))
        # veins of copper wire fanning from the root, a darker scalloped margin
        for tip in (fw[1], fw[2], fw[3]):
            r.polyline([root, (lerp(root[0], tip[0], 0.85), lerp(root[1], tip[1], 0.85))], "copper", z + 0.012, tone=3 if side > 0 else 1)
        r.polyline([fw[1], fw[2], fw[3]], "mwing", z + 0.011, tone=1 if side > 0 else 0)
        r.polyline([hw[1], hw[2]], "mwing", z - 0.09, tone=1 if side > 0 else 0)
        ex, ey = side * 9.0 * wings, by - 8.0 - up * 0.6
        r.ell(ex, ey, 2.6 * wings, 2.0, "brass", z + 0.008, bias=0.1, thin=True)
        r.ell(ex, ey, 1.8 * wings, 1.4, "magblu", z + 0.01, bias=0.2, thin=True)
        r.dot(ex, ey, "storm", 4, z + 0.02); r.dot(ex + side, ey, "storm", 3, z + 0.02)
        hx_, hy_ = side * 6.5 * wings, by + 4.0 - up * 0.1
        r.dot(hx_, hy_, "storm", 3, z - 0.05)
        r.polyline([root, (side * 14.0 * wings, by - 11.5 - up * 0.8)], "copper", z + 0.015, tone=1 if side < 0 else 2)
        if full:
            for i in range(4):
                x = side * (4.0 + i * 3.0) * wings
                y = by - 9.5 - up * 0.7 + (i % 2) * 2
                spark(r, x + (k % 2), y, 2 if (i + k) % 2 else 3, z=z + 0.03, mat="spark")
            for i in range(2):
                r.dot(side * (7 + i * 4) * wings, by - 2 + i * 3 + k % 2, "spark", 3, z + 0.03)
    # body: a furred soot thorax and abdomen
    P = r.part(False, 0.0)
    r.ell(0.0, by - 1.0, 2.8, 3.4, "soot", 0.0, bias=0.15, part=P)
    r.tube([(0.0, by + 1.0), (-0.8 + tilt, by + 9.0)], [2.4, 1.2], "soot", 0.0, bias=0.05, part=P)
    for i in range(3): r.polyline([(-2.0 + tilt * 0.3 * i, by + 3.0 + i * 2.0), (1.8 + tilt * 0.3 * i, by + 3.0 + i * 2.0)], "copper", 0.1, tone=1)
    # head, eyes, coiled antennae
    hx, hy = 1.0, by - 5.0
    r.ell(hx, hy, 2.4, 2.0, "soot", 0.5, bias=0.2)
    r.dot(hx + 1.0, hy, "storm", 2 if hurt else 4, 0.6); r.dot(hx - 0.6, hy, "storm", 2, 0.6)
    for side in (-1, 1):
        pts = [(hx + side * 0.8, hy - 1.5), (hx + side * 2.0 + 1.0, hy - 4.0), (hx + side * 1.0 + 1.5, hy - 5.5), (hx + side * 2.6 + 2.0, hy - 6.6),
               (hx + side * 3.4 + 2.5, hy - 8.0)]
        r.polyline(pts, "brass", 0.7, tones=[3, 2, 3, 2])
        r.dot(pts[-1][0], pts[-1][1], "storm", 4, 0.75)
    if dart:
        for (x, y) in dart:
            r.poly([(x - 2, y - 1), (x + 2, y), (x - 2, y + 1)], "mwing", 6.0, bias=0.3); r.dot(x + 1, y, "storm", 3, 6.1)
    if drink > 0:
        for i in range(int(6 * drink)):
            r.dot(hx + 2 + i * 1.5, hy + 4 + i * 1.6, "storm", 4 if i % 2 else 3, 6.0)
    for (x, y, kk) in sparks: spark(r, x, y, kk)
    if extra: extra(r)
    return r.resolve()


def moth_sheet(outdir):
    Mo = moth
    flaps = [1.0, 0.3, -1.0, 0.3]

    def idle(full):
        return [Mo(hover=8.0 + [0, 0.8, 1.6, 0.8][i], flap=flaps[i], full=full, k=i) for i in range(4)]

    def run(full):
        return [Mo(hover=8.5 + 0.6 * math.sin(i / 6 * math.tau), flap=[1.0, 0.2, -1.0, -0.4, 0.4, 1.0][i], full=full, k=i, tilt=1.0) for i in range(6)]
    dt = [Mo(flap=0.6), Mo(flap=1.0, wings=1.05, sparks=[(14, -30, 3)]), Mo(flap=0.0), Mo(flap=-1.0, dart=[(12.0, -19.0), (10.0, -15.0)]),
          Mo(flap=-0.2), Mo(flap=0.6)]
    dk = [Mo(flap=0.6), Mo(flap=1.0, hover=10.0), Mo(flap=-1.0, hover=6.0, drink=0.3), Mo(flap=0.2, hover=6.0, drink=0.7, sparks=[(10, -6, 2)]),
          Mo(flap=1.0, hover=6.0, drink=1.0, full=True), Mo(flap=-0.4, hover=7.0, full=True, k=1), Mo(flap=0.4, hover=8.0, full=True, k=2),
          Mo(flap=0.8, full=True)]
    d0 = Mo(hurt=True, flap=-0.6, tilt=-2.0)
    d1 = Mo(hurt=True, flap=1.0, hover=3.0, wings=0.7, sparks=[(2, -16, 1)])
    d2 = moth_corpse(0)
    corpse = moth_corpse(1)
    knock = Mo(hurt=True, flap=1.0, tilt=-2.0, hover=9.0)
    idle0 = idle(False)
    anims = [("Idle", idle0, [0.1, 0.1, 0.1, 0.1]), ("Run", run(False), [0.07] * 6),
             ("IdleFull", idle(True), [0.1, 0.1, 0.1, 0.1]), ("RunFull", run(True), [0.07] * 6),
             ("Darts", dt, [0.12, 0.12, 0.1, 0.06, 0.12, 0.12]),
             ("Drink", dk, [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.12])]
    anims += tail_anims(idle0[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return msheet("KrnStaticMoth", anims, outdir)


def moth_corpse(stage):
    r = Rig()
    for side in (-1, 1):
        r.poly([(side * 1.0, -2.0), (side * 14.0, -5.0 + stage), (side * 13.0, 0.0), (side * 2.0, 0.0)], "mwing", 0.0 if side < 0 else 0.1,
               bias=-0.1)
        r.dot(side * 8.0, -2.0, "magblu", 2, 0.2)
    r.tube([(0.0, -2.0), (0.0, -1.0)], [2.4, 2.0], "soot", 0.5)
    if stage == 0: spark(r, 0.0, -8.0, 2)
    return r.resolve()


SYNC = {
    "KrnStormHerald": {"Lance": [("bolt leaves the lance tip at (26, -18)", 3)], "Horn": [("BLOW: the storm starts", 4)]},
    "KrnScarabMagus": {"Orb": [("orb leaves the hands at (14, -17)", 3)], "Kindle": [("the two balls leave the open shell at (12, -22) / (12, -10)", 5)]},
    "KrnStormOrrery": {"Fling": [("orb leaves the ring at (16, -21)", 3)], "Align": [("the line shows (aiming)", 1), ("FIRE along the line", 8)]},
    "KrnVoltaicPile": {"Whip": [("CRACK: the lash reaches (40, -16)", 3)], "Surge": [("discs lighting (0..6)", 0), ("FLASH: every arc joined to it", 7)]},
    "KrnTeslaSpire": {"Relay": [("the rod picked to fire glows (aim)", 1), ("the rod FIRES", 4)], "Answer": [("rooted: every rod answers", 4)]},
    "KrnStaticMoth": {"Darts": [("darts leave the wings at (12, -19)", 3)], "Drink": [("drinks the rods dry", 3)]},
}
NOTES = {
    "KrnStaticMoth": "IdleFull/RunFull: wings fizz white (3 sparks stored: Spark Fall).",
    "KrnTeslaSpire": "Rooted (loop) is held for Every Rod Answers' 3 s.",
}
JOBS = [("KrnStormHerald", herald_sheet), ("KrnScarabMagus", magus_sheet), ("KrnStormOrrery", orrery_sheet),
        ("KrnVoltaicPile", pile_sheet), ("KrnTeslaSpire", spire_sheet), ("KrnStaticMoth", moth_sheet)]
