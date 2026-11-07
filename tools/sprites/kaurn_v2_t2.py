"""Kaurn tier 2: Anvil Smith, Wire Gremlin, Lodestone Hound, Stormcaller, Leyden Golem, Arc Lantern (built through
kaurn_v2_rigs.py). T2 idle limit 28 x 26."""
import math
from kaurn_v2_rigs import (Rig, lerp, ik, msheet, tail_anims, leg, arm, hammer, bolt, crackle, spark, eye, shadow, rod,
                           dust_puff, zig, line_px)
from jinx_v2_rigs import bat_wing


# ================================================================== a quadruped (hound, warg, bull share it)
def quad(r, L=14.0, H=8.0, rb=(3.6, 3.2), mat="fur", belly=None, phase=None, stance=0.0, lean=0.0, crouch=0.0,
         legs=(4.0, 4.2), leg_r=(1.3, 0.9), paw="dkiron", neck=(3.0, -4.0), head=None, tail=None, tail_mat=None, z=0.0,
         stretch=0.0, gather=0.0):
    """Body from hip (-L/2, -H) to shoulder (L/2, -H); phase: gait angle (None = standing); crouch lowers the body;
    stretch / gather spread or pull the feet for a leap. Returns (hip, shoulder) points for the caller's head and mane."""
    hip = (-L / 2.0, -H + crouch + lean * 0.3)
    sh = (L / 2.0, -H + crouch - lean * 0.6)
    # legs: far pair first (behind the body), then near pair
    for far in (True, False):
        zz = z - 1.5 if far else z + 1.5
        bias = -0.35 if far else 0.0
        for k, (root, fore) in enumerate(((hip, False), (sh, True))):
            off = (0.0 if far else math.pi) + (math.pi * 0.5 if fore else 0.0)
            if phase is None:
                fx = root[0] + (1.0 if fore else -0.6) + (0.8 if far else 0.0) + (stretch if fore else -stretch) + (-gather if fore else gather)
                fy = 0.0
            else:
                a = phase + off
                fx = root[0] + 3.2 * math.cos(a) + (0.6 if fore else -0.4)
                fy = -max(0.0, 1.8 * math.sin(a))
            if stretch > 0 and not fore: fy = min(fy, -stretch * 0.4)
            l1, l2 = legs
            bend = 1 if fore else -1
            kx, ky = ik(root[0], root[1] + 1.0, fx, fy - 0.8, l1, l2, bend)
            r.tube([(root[0], root[1] + 1.0), (kx, ky), (fx, fy - 0.8)], [leg_r[0] + 0.3, leg_r[1], leg_r[1]], mat, zz, bias=bias, thin=True)
            r.ell(fx + 0.6, fy - 0.6, 1.3, 0.8, paw, zz + 0.01, bias=bias, thin=True)
    # body: a tapered tube from haunch to chest, one part
    P = r.part(False, z)
    r.tube([hip, sh], [rb[0], rb[1]], mat, z, bias=0.05, part=P)
    r.ell(sh[0] - 0.5, sh[1] - 0.2, rb[1] + 0.8, rb[1] + 0.6, mat, z, bias=0.1, part=P)
    if belly:
        r.tube([(hip[0] + 1, hip[1] + rb[0] * 0.6), (sh[0] - 1, sh[1] + rb[1] * 0.7)], [1.0, 1.0], belly, z + 0.1, thin=True)
    if tail:
        r.tube(tail, [1.0] + [0.7] * (len(tail) - 1), tail_mat or mat, z - 0.5, bias=-0.1, thin=True)
    return hip, sh


# ================================================================== ANVIL SMITH: a stocky smith, anvil on his back, two-handed hammer
SMITH_FACE = {"k": ("skin", 0), "B": ("storm", 3), "d": ("dkiron", 1), "D": ("dkiron", 2), "m": ("skin", 1), "e": ("ember", 3),
              "w": ("ivory", 3)}
SMITH_FACES = {
    # pivot (1, 0): the near eye, under a scorched brow
    "calm": "kk.kk\nkB.kB\n.....\n.mmm.\nDdDdD\n.dDd.",
    "roar": "kk.kk\nkB.kB\n.....\n.mwm.\nDkekD\n.dDd.",
    "hurt": "kk.kk\n.k..k\n.....\n.mkm.\nDdDdD\n.dDd.",
    "dead": "kk.kk\nk..k.\n.....\n.mmm.\nDdDdD\n.dDd.",
}


def smith(lean=0.0, bob=0.0, feet=((-3.5, 0.0), (3.5, 0.0)), hands=(7.0, -10.0), ham=-60.0, face="calm", rod_at=None,
          plate=0, smear=None, sparks=(), squash=0.0, extra=None, ham_ln=10.0, anvil_glow=0):
    """hands: where both fists grip the haft; ham: hammer angle. rod_at: (x, y, h, hot) a rod he is planting."""
    r = Rig()
    by = -10.0 + bob + squash
    tx = lean * 0.5
    # the anvil strapped on his back (behind everything): a horned block standing over his shoulders
    ax, ay = tx - 6.0 + lean * 0.3, by - 10.0
    r.poly([(ax - 5.0, ay - 3.6), (ax + 5.0, ay - 3.6), (ax + 5.0, ay + 0.5), (ax + 3.0, ay + 1.5), (ax + 3.0, ay + 7.0),
            (ax - 2.5, ay + 7.0), (ax - 2.5, ay + 1.5), (ax - 5.0, ay + 0.5)], "dkiron", -3.0, normal=(-0.3, -0.5, 0.8))
    r.poly([(ax - 5.0, ay - 3.6), (ax - 7.4, ay - 2.8), (ax - 5.0, ay - 0.8)], "dkiron", -2.9, normal=(-0.6, -0.4, 0.7))   # horn
    r.polyline([(ax - 5.0, ay - 3.6), (ax + 5.0, ay - 3.6)], "iron", -2.8, tone=4)
    if anvil_glow: r.polyline([(ax - 3.0, ay - 3.0), (ax + 3.5, ay - 3.0)], "ember", -2.7, tone=3)
    # legs: short and thick, iron-capped boots
    for k, f in enumerate(feet):
        z = -1.0 if k == 0 else 1.5
        leg(r, (tx + (-2.6 if k == 0 else 2.6), by + 3.5), f, 4.0, 3.8, "apron", z, rad=(2.2, 1.8), boot="dkiron", boot_len=2.6,
            bias=-0.3 if k == 0 else 0.0)
    # torso: a broad barrel, apron over it, a belt with a brass buckle
    P = r.part(False, 0.0)
    r.ell(tx, by - 1.5, 8.2, 7.0 - squash * 0.4, "skin", 0.0, bias=0.0, part=P)
    r.ell(tx + 0.5, by - 6.0, 6.6, 3.0, "skin", 0.0, bias=0.1, part=P)
    r.poly([(tx - 5.0, by - 3.5), (tx + 6.2, by - 3.5), (tx + 6.8, by + 5.5), (tx - 5.6, by + 5.5)], "apron", 0.4,
           normal=(-0.2, -0.2, 1.0), curve=0.7)
    r.polyline([(tx - 5.6, by + 0.6), (tx + 6.2, by + 0.6)], "apron", 0.5, tone=0)
    r.dot(tx + 2.0, by + 0.6, "brass", 3, 0.55); r.dot(tx + 3.0, by + 0.6, "brass", 2, 0.55)
    r.polyline([(tx - 3.5, by - 6.0), (tx - 4.5, by - 2.0)], "apron", 0.45, tone=1)   # anvil strap
    # head: bald, broad, a soot-black beard, storm-blue eyes under the brow
    hx, hy = tx + 1.5 + lean, by - 8.0 + squash * 0.5
    r.ell(hx, hy, 4.0, 3.8, "skin", 0.6, bias=0.15)
    r.stamp(SMITH_FACES[face], hx + 0.6, hy - 1.0, 0.8, SMITH_FACE, pivot=(1, 1))
    r.dot(hx - 2.6, hy - 1.0, "skin", 1, 0.7)                                       # ear
    # far arm (behind the haft) and near arm, both on the hammer
    if hands is not None:
        hx2, hy2 = hands
        g2 = (hx2 - 2.2 * math.cos(math.radians(ham)), hy2 - 2.2 * math.sin(math.radians(ham)))
        arm(r, (tx - 3.0, by - 5.0), g2, 4.6, 4.2, "skin", -0.5, rad=(2.0, 1.6), fist="skin", fist_r=1.6, bias=-0.3)
        hammer(r, g2[0], g2[1], ham, ham_ln, 2.0, head=(6.0, 4.2), haft="wood", head_mat="dkiron", glow="ember", back=1.5)
        arm(r, (tx + 5.0, by - 5.0), (hx2, hy2), 4.4, 4.0, "skin", 2.6, rad=(2.4, 1.8), fist="skin", fist_r=1.9)
    if rod_at:
        x, y, h, hot = rod_at
        rod(r, x, y, h, 1.8, hot=hot)
    if plate:
        for i in range(plate * 6):
            a = i / 6.0 * math.tau
            r.dot(tx + 8.0 * math.cos(a), by - 2.0 + 7.0 * math.sin(a), "iron", 4, 6.0)
    if smear:
        for pts, tn in smear: r.polyline(pts, "steam", 4.6, tone=tn)
    for (x, y, k) in sparks: spark(r, x, y, k, mat="ember" if k == 1 else "storm")
    if extra: extra(r)
    return r.resolve()


def smith_sheet(outdir):
    S = smith
    idle = [S(bob=[0, 0.4, 0.8, 0.4][i], ham=-62, hands=(7.6, -9.6 + [0, 0.4, 0.8, 0.4][i])) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        f1 = (3.0 * math.cos(ph), -max(0.0, 1.8 * math.sin(ph)))
        f2 = (-3.0 * math.cos(ph), -max(0.0, -1.8 * math.sin(ph)))
        b = -0.8 * abs(math.sin(ph))
        run.append(S(lean=1.0, bob=b, feet=(f2, f1), ham=-75 + 6 * math.sin(ph), hands=(7.0, -10.0 + b)))
    # Hammer: heave it over the head, smear down, HIT at (18, -1) (the surge runs on), shudder, recover
    hm = [S(lean=-1.0, ham=-110, hands=(4.0, -15.0), squash=0.5, face="roar"),
          S(lean=-2.0, ham=-160, hands=(1.0, -18.0), bob=-1.0, face="roar", feet=((-4.0, 0.0), (4.0, 0.0))),
          S(lean=2.0, ham=-30, hands=(8.0, -12.0), face="roar",
            smear=[([(-2, -30), (8, -28), (16, -20), (19, -10)], 2), ([(2, -29), (12, -25), (18, -15)], 3)]),
          S(lean=3.0, squash=1.2, ham=25, hands=(9.5, -6.0), face="roar", feet=((-4.0, 0.0), (5.0, 0.0)),
            sparks=[(19, -2, 1), (22, -4, 2), (15, -1, 2)], extra=lambda r: dust_puff(r, 18.0, 0.0, 0, 1.2)),
          S(lean=2.5, squash=0.8, ham=20, hands=(9.5, -6.5), sparks=[(24, -3, 2)], extra=lambda r: dust_puff(r, 18.0, 0.0, 1, 1.4)),
          S(lean=1.0, ham=-20, hands=(8.0, -9.0)),
          S(ham=-62, hands=(7.0, -9.6))]
    # Plant: draw a rod off the anvil, set it at (11, 0), one blow drives it in red hot, the iron plate gathers on him
    pl = [S(ham=-62, hands=(7.0, -9.6), rod_at=(4.0, -16.0, 10, 0)),
          S(lean=1.0, ham=-120, hands=(4.0, -14.0), rod_at=(11.0, -2.0, 11, 0), face="roar"),
          S(lean=-1.0, ham=-170, hands=(1.0, -17.0), rod_at=(11.0, -1.0, 11, 0), face="roar", bob=-1.0),
          S(lean=2.5, squash=1.0, ham=-10, hands=(8.0, -9.0), rod_at=(11.0, 0.0, 10, 1.0), face="roar", anvil_glow=1,
            sparks=[(11, -12, 1), (14, -9, 2), (8, -11, 2)]),
          S(lean=1.5, squash=0.5, ham=-20, hands=(7.5, -9.5), rod_at=(11.0, 0.0, 10, 0.8), plate=1, anvil_glow=1),
          S(lean=0.5, ham=-50, hands=(7.0, -9.6), rod_at=(11.0, 0.0, 10, 0.6), plate=1),
          S(ham=-62, hands=(7.0, -9.6), rod_at=(11.0, 0.0, 10, 0.4)),
          S(ham=-62, hands=(7.0, -9.6))]
    d0 = S(lean=-2.0, ham=-120, hands=(3.0, -13.0), face="hurt")
    d1 = S(lean=-4.0, bob=2.0, squash=1.5, ham=-170, hands=(-2.0, -12.0), face="hurt", feet=((-4.0, 0.0), (2.0, 0.0)))
    d2 = smith_corpse(0)
    corpse = smith_corpse(1)
    knock = S(lean=-3.0, ham=-110, hands=(3.0, -12.0), face="hurt")
    anims = [("Idle", idle, [0.18, 0.14, 0.18, 0.14]), ("Run", run, [0.08] * 6),
             ("Hammer", hm, [0.14, 0.14, 0.05, 0.08, 0.12, 0.12, 0.12]),
             ("Plant", pl, [0.12, 0.12, 0.12, 0.06, 0.12, 0.12, 0.1, 0.1])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return msheet("KrnAnvilSmith", anims, outdir)


def smith_corpse(stage):
    r = Rig()
    # face down over his anvil, the hammer beyond his hand
    r.poly([(-12.0, -6.0), (-4.0, -6.0), (-4.0, 0.0), (-12.0, 0.0)], "dkiron", 0.0, normal=(-0.3, -0.5, 0.8))
    r.ell(0.0, -3.4, 7.0, 3.4, "skin", 1.0, bias=0.05)
    r.poly([(-4.0, -4.0), (5.0, -4.0), (5.0, 0.0), (-4.0, 0.0)], "apron", 1.2, curve=0.5)
    r.ell(7.5, -2.6, 3.0, 2.6, "skin", 1.4, bias=0.1)
    r.dots([(9, -1), (8, -1), (10, -2)], "dkiron", 1, 1.5)
    hammer(r, 11.0, -1.0, -5 if stage else -25, 7.0, 1.6, head=(6.0, 4.2))
    if stage == 0: spark(r, -8.0, -9.0, 2)
    return r.resolve()


# ================================================================== WIRE GREMLIN: bat-winged, wrapped in copper wire, a staple gun
GREM_FACE = {"k": ("ghide", 0), "B": ("storm", 3), "W": ("ivory", 3), "w": ("ivory", 2), "m": ("ghide", 1), "e": ("ember", 2)}
GREM_FACES = {
    "grin": "kB.kB\n.....\nWwWwW\n.mmm.",
    "shout": "kB.kB\n.....\nWkkkW\n.WeW.",
    "hurt": "k..k.\n.....\n.mkm.",
}


def gremlin(hover=2.5, flap=0.0, lean=0.0, gun=(6.0, -14.0), gun_ang=0.0, face="grin", wire=None, wire_spin=None,
            staple=None, sparks=(), hurt=False, extra=None, wings=1.0):
    """flap: wing angle offset (deg); gun: the staple gun's grip; wire: points of the hooked wire it whirls / flicks."""
    r = Rig()
    by = -hover - 7.0
    shadow(r, 0.0, 0.0, 4.0)
    # wings (bat): far wing behind, near wing in front of the body edge
    bat_wing(r, -1.5, by - 4.0, -150 + flap, 70 * wings, 9.5, -3.0, mat="ghide", near=False)
    # legs dangling, clawed
    for k, dx in enumerate((-1.5, 1.5)):
        r.tube([(dx, by + 3.0), (dx + 0.8, by + 6.0), (dx + 1.6, by + 7.5)], [1.1, 0.9, 0.7], "ghide", -0.5 + k, bias=-0.3 + 0.3 * k, thin=True)
        r.dot(dx + 2.2, by + 7.8, "ivory", 2, -0.4 + k)
    # body: pot-bellied, wrapped in copper wire
    P = r.part(False, 0.0)
    r.ell(lean * 0.3, by, 5.0, 5.2, "ghide", 0.0, bias=0.05, part=P)
    for i, (y, d) in enumerate(((by - 2.0, 0.6), (by + 0.0, 0.4), (by + 2.0, 0.2))):
        r.polyline([(-3.8 + d, y + 0.8), (0.0, y - 0.4), (3.8 - d, y + 0.6)], "copper", 0.5, tones=[3, 2])
    # head: wide grin, huge ears
    hx, hy = 1.0 + lean, by - 6.6
    r.ell(hx, hy, 4.8, 3.8, "ghide", 0.6, bias=0.12)
    r.poly([(hx - 2.5, hy - 1.5), (hx - 8.5, hy - 5.5), (hx - 3.5, hy + 0.5)], "ghide", 0.5, bias=-0.05, normal=(-0.4, -0.6, 0.7))
    r.poly([(hx + 2.0, hy - 2.2), (hx + 6.0, hy - 7.5), (hx + 3.6, hy - 0.4)], "ghide", 0.7, bias=0.15, normal=(-0.2, -0.6, 0.8))
    r.dot(hx - 5.0, hy - 3.0, "ghide", 1, 0.55); r.dot(hx + 4.0, hy - 3.8, "ghide", 1, 0.75)   # inner ears
    r.stamp(GREM_FACES["hurt" if hurt else face], hx + 0.4, hy - 0.6, 0.9, GREM_FACE, pivot=(1, 0))
    # near wing over the shoulder
    bat_wing(r, 1.5, by - 4.0, -30 - flap, -70 * wings, 9.0, 0.3, mat="ghide", near=True)
    # the staple gun: a brass-and-iron block in its fist, muzzle forward
    if gun is not None:
        gx, gy = gun
        ca, sa = math.cos(math.radians(gun_ang)), math.sin(math.radians(gun_ang))
        T = lambda u, v: (gx + u * ca - v * sa, gy + u * sa + v * ca)
        r.poly([T(-1.5, -2.0), T(4.5, -2.0), T(4.5, 0.5), T(-1.5, 0.5)], "brass", 2.0, normal=(-0.3, -0.6, 0.7))
        r.poly([T(-1.0, 0.5), T(1.0, 0.5), T(0.5, 3.0), T(-1.2, 3.0)], "dkiron", 1.9)
        r.dot(*T(4.8, -0.8), "ember", 3, 2.1)
        r.tube([(2.8 + lean * 0.3, by - 1.5), (gx - 0.5, gy + 1.0)], [1.0, 0.9], "ghide", 2.2, thin=True)
        r.ell(gx - 0.2, gy + 0.8, 1.1, 1.0, "ghide", 2.3, thin=True)
    if wire:
        r.polyline(wire, "copper", 5.0, tones=[3, 2] * len(wire))
        hx_, hy_ = wire[-1]
        r.polyline([(hx_, hy_), (hx_ + 1, hy_ - 1), (hx_ + 2, hy_), (hx_ + 1.5, hy_ + 1.5)], "brass", 5.1, tone=4)
    if staple:
        r.dots([(staple[0], staple[1]), (staple[0] + 1, staple[1]), (staple[0] + 2, staple[1])], "brass", 4, 6.0)
    for (x, y, k) in sparks: spark(r, x, y, k)
    if extra: extra(r)
    return r.resolve()


def gremlin_sheet(outdir):
    G = gremlin
    idle = [G(hover=2.5 + [0, 0.4, 0.8, 0.4][i], flap=[0, -8, -14, -8][i]) for i in range(4)]
    run = [G(hover=3.0 + 0.6 * math.sin(i / 6 * math.tau), flap=[0, 30, 50, 30, 0, -15][i], lean=1.0) for i in range(6)]
    st = [G(gun=(5.0, -14.5), gun_ang=-10), G(gun=(4.0, -15.0), gun_ang=-25, lean=-1.0, face="shout"),
          G(gun=(6.5, -14.0), gun_ang=0, face="shout"), G(gun=(7.5, -14.0), gun_ang=5, face="shout", staple=(13, -14), sparks=[(12, -15, 1)]),
          G(gun=(6.0, -15.0), gun_ang=-20, sparks=[(13, -16, 2)]), G(gun=(6.0, -14.0)), G()]
    def whirl(a, R=6.0, cx=2.0, cy=-24.0):
        pts = [(4.0, -16.0)]
        for i in range(1, 5):
            t = i / 4.0
            pts.append((lerp(4.0, cx + R * math.cos(a), t), lerp(-16.0, cy + R * 0.5 * math.sin(a), t)))
        return pts
    wu = [G(gun=None, wire=whirl(0.0), face="shout"), G(gun=None, wire=whirl(2.0), flap=20, face="shout"),
          G(gun=None, wire=whirl(4.0), flap=40, face="shout", sparks=[(0, -26, 2)]),
          G(gun=None, wire=[(4.0, -15.0), (9.0, -16.0), (14.0, -15.0), (19.0, -13.0)], lean=2.0, face="shout", sparks=[(20, -13, 1)]),
          G(gun=None, wire=[(4.0, -15.0), (8.0, -15.0), (12.0, -14.5)], lean=1.0), G(gun=None, wire=[(4.0, -15.0), (6.0, -12.0)]),
          G(gun=(5.0, -14.5), gun_ang=-10), G()]
    d0 = G(hurt=True, flap=-20, lean=-2.0)
    d1 = G(hurt=True, hover=2.0, flap=60, wings=0.6, lean=-3.0, sparks=[(2, -14, 1)])
    d2 = gremlin_corpse(0)
    corpse = gremlin_corpse(1)
    knock = G(hurt=True, flap=50, lean=-3.0, hover=3.5)
    anims = [("Idle", idle, [0.1, 0.1, 0.1, 0.1]), ("Run", run, [0.07] * 6),
             ("Staple", st, [0.12, 0.12, 0.1, 0.06, 0.1, 0.12, 0.12]),
             ("WireUp", wu, [0.1, 0.1, 0.1, 0.06, 0.1, 0.1, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return msheet("KrnWireGremlin", anims, outdir)


def gremlin_corpse(stage):
    r = Rig()
    bat_wing(r, -2.0, -3.0, -170, 40, 9.0, 0.0, mat="ghide", near=False)
    r.ell(0.0, -3.2, 4.6, 3.2, "ghide", 1.0, bias=0.05)
    r.ell(5.6, -3.0, 3.4, 2.8, "ghide", 1.2, bias=0.1)
    r.poly([(7.0, -4.0), (12.0, -6.0 + stage), (8.0, -2.0)], "ghide", 1.1)
    r.polyline([(-3.0, -2.0), (0.0, -4.0), (3.0, -2.0)], "copper", 1.3, tones=[2, 2])
    r.dots([(6, -3), (7.5, -3)], "ghide", 0, 1.4)
    if stage == 0: spark(r, 0.0, -8.0, 2)
    return r.resolve()


# ================================================================== LODESTONE HOUND: lean iron-maned hound, lodestone collar
HOUND_FACE = {"k": ("fur", 0), "B": ("storm", 4), "b": ("storm", 2), "W": ("ivory", 3), "m": ("fur", 1)}


def hound(phase=None, collar="magred", head=(9.0, -15.5), jaw=0.0, crouch=0.0, lean=0.0, stretch=0.0, gather=0.0, howl=0.0,
          field=0, hurt=False, sparks=(), extra=None, mane=1.0, bob=0.0, tail_up=0.0):
    """collar: magred (pull) or magblu (push); howl: 0..1 head thrown back; field: 1..3 field lines bending in or out."""
    r = Rig()
    tail = [(-6.0, -10.0 + crouch + bob), (-8.5, -12.0 - tail_up + bob), (-10.5, -11.5 - tail_up * 1.5 + bob)]
    hip, sh = quad(r, L=11.5, H=9.8 - bob, rb=(3.3, 4.6), mat="lode", phase=phase, crouch=crouch, lean=lean, legs=(4.8, 4.6),
                   leg_r=(1.3, 0.9), stretch=stretch, gather=gather, tail=tail)
    # head on a strong neck
    hx, hy = head[0], head[1] + crouch + bob
    if howl: hx, hy = hx - 2.0 * howl, hy - 3.0 * howl
    r.tube([(sh[0] - 1.0, sh[1] - 0.5), (hx - 1.5, hy + 0.5)], [3.0, 2.0], "lode", 0.6, bias=0.05)
    a = math.radians(-35 * howl)
    ca, sa = math.cos(a), math.sin(a)
    T = lambda u, v: (hx + u * ca - v * sa, hy + u * sa + v * ca)
    r.ell(hx, hy, 3.2, 2.8, "lode", 1.0, bias=0.12, ang=-35 * howl)
    r.tube([T(1.5, -0.2), T(6.0, 0.8)], [1.8, 0.9], "lode", 1.1, bias=0.1)              # muzzle
    r.tube([T(1.5, 1.4 + jaw * 0.6), T(5.2, 2.0 + jaw * 2.4)], [1.0, 0.6], "lode", 0.95, bias=-0.2)   # jaw
    if jaw > 0.3:
        r.dots([T(3.0, 1.0 + jaw), T(4.5, 1.2 + jaw * 1.6)], "ivory", 3, 1.15)
    r.dot(*T(6.5, 0.6), "dkiron", 0, 1.2)                                               # nose
    r.dot(*T(0.8, -1.0), "storm", 2 if hurt else 4, 1.2)                                # eye
    r.poly([T(-1.0, -1.5), T(-2.5, -6.5), T(0.8, -2.0)], "lode", 1.05, bias=0.1)        # ear
    # copper bands riveted round the barrel and the haunch
    for t in (0.2, 0.5, 0.8):
        x, y = lerp(hip[0], sh[0], t), lerp(hip[1], sh[1], t)
        rr = lerp(3.3, 4.6, t)
        r.tube([(x - 0.6, y - rr + 0.4), (x + 0.4, y + rr - 0.6)], [0.9, 0.9], "copper", 0.4, bias=0.1, thin=True)
        r.dot(x - 0.4, y - rr + 1.4, "brass", 4, 0.45)
    r.tube([(hx - 2.2, hy - 1.2), (hx - 1.6, hy + 2.2)], [0.7, 0.7], "copper", 1.08, thin=True)
    # the iron mane standing up along the neck and back
    if mane:
        for i in range(6):
            t = i / 5.0
            x, y = lerp(hx - 2.0, sh[0] - 7.0, t), lerp(hy - 2.0, sh[1] - 3.5, t)
            h = (3.0 + 1.4 * math.sin(i * 1.7)) * mane
            r.tube([(x, y), (x - 1.2, y - h)], [0.9, 0.3], "iron", 0.8 - t * 0.2, thin=True)
    # the lodestone collar
    cx, cy = lerp(sh[0] - 0.5, hx - 1.5, 0.55), lerp(sh[1] - 1.0, hy + 0.5, 0.55)
    glow = "glowred" if collar == "magred" else "storm"
    for i in range(10):
        ang = i / 10.0 * math.tau
        r.dot(cx + 3.2 * math.cos(ang) * 0.7, cy + 3.6 * math.sin(ang), glow, 2 if i % 2 else 3, 1.25)
    r.tube([(cx - 0.8, cy - 3.0), (cx + 0.8, cy + 2.8)], [1.6, 1.6], collar, 1.3, bias=0.15, thin=True)
    r.dot(cx - 0.6, cy - 1.0, glow, 4, 1.35)
    r.dot(cx + 0.8, cy + 0.2, "storm", 4, 1.35)
    if field:
        col = "magred" if collar == "magred" else "magblu"
        for k in range(field):
            R = 5.0 + k * 3.5
            for i in range(9):
                ang = math.radians(-70 + i * 17)
                inward = collar == "magred"
                bend = (-1.0 if inward else 1.0) * 1.2
                r.dot(cx + R * math.cos(ang) + bend * math.sin(ang * 2), cy + R * math.sin(ang) * 0.8, col, 3 if k == 0 else 2, 6.0)
    for (x, y, k) in sparks: spark(r, x, y, k)
    if extra: extra(r)
    return r.resolve()


def hound_sheet(outdir):
    H = hound
    anims = []
    for suf, col in (("", "magred"), ("Blue", "magblu")):
        idle = [H(collar=col, bob=[0, 0.3, 0.6, 0.3][i], tail_up=[0, 0.5, 1, 0.5][i]) for i in range(4)]
        run = [H(collar=col, phase=i / 6 * math.tau, bob=-0.6 * abs(math.sin(i / 6 * math.tau)), head=(11.0, -15.5), tail_up=1.0)
               for i in range(6)]
        leap = [H(collar=col, crouch=2.0, gather=2.0, head=(10.0, -14.0)), H(collar=col, crouch=3.0, gather=3.0, head=(9.0, -13.0), jaw=0.3),
                H(collar=col, stretch=3.0, lean=2.0, head=(13.0, -17.0), jaw=1.0, bob=2.0),
                H(collar=col, stretch=3.5, lean=1.0, head=(14.0, -15.0), jaw=0.0, bob=1.0, sparks=[(21, -14, 1)]),
                H(collar=col, crouch=1.0, head=(11.0, -15.0), jaw=0.2), H(collar=col, head=(10.0, -16.0)), H(collar=col)]
        howl = [H(collar=col, crouch=1.0), H(collar=col, howl=0.5, jaw=0.5),
                H(collar=col, howl=1.0, jaw=1.0, field=1), H(collar=col, howl=1.0, jaw=1.0, field=2, sparks=[(6, -20, 2)]),
                H(collar=col, howl=1.0, jaw=1.0, field=3), H(collar=col, howl=0.9, jaw=0.8, field=2),
                H(collar=col, howl=0.5, jaw=0.3, field=1), H(collar=col)]
        anims += [("Idle" + suf, idle, [0.16, 0.12, 0.16, 0.12]), ("Run" + suf, run, [0.06] * 6),
                  ("Leap" + suf, leap, [0.1, 0.1, 0.06, 0.08, 0.1, 0.1, 0.1]),
                  ("Howl" + suf, howl, [0.12, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.12])]
    idle0 = anims[0][1][0]
    d0 = H(hurt=True, crouch=1.0, head=(9.0, -14.0), jaw=0.6)
    d1 = H(hurt=True, crouch=4.0, head=(8.0, -9.0), jaw=0.8, mane=0.5)
    d2 = hound_corpse(0)
    corpse = hound_corpse(1)
    knock = H(hurt=True, lean=-2.0, head=(8.0, -16.0), jaw=0.6)
    anims += tail_anims(idle0, [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return msheet("KrnLodeHound", anims, outdir)


def hound_corpse(stage):
    r = Rig()
    r.tube([(-7.0, -3.0), (5.0, -3.5)], [3.2, 3.4], "fur", 0.0, bias=0.05)
    r.ell(9.0, -2.6, 3.0, 2.4, "fur", 0.5, bias=0.1)
    r.tube([(10.0, -2.0), (13.5, -1.4)], [1.4, 1.0], "fur", 0.6)
    for i in range(4):
        r.tube([(-5.0 + i * 3.0, -5.5), (-4.0 + i * 3.0, -8.0 + stage)], [0.9, 0.7], "fur", 0.4 - 0.1 * i, thin=True)
    r.tube([(5.0, -6.0), (7.0, -6.8)], [1.0, 1.0], "magred", 0.7, thin=True)
    r.tube([(-8.0, -3.0), (-12.0, -1.0)], [0.9, 0.6], "fur", -0.1, thin=True)
    if stage == 0: spark(r, 0.0, -9.0, 2)
    return r.resolve()


# ================================================================== STORMCALLER: hooded caller with a lightning-rod staff
def caller(bob=0.0, lean=0.0, staff=(6.5, -10.5), staff_h=10.6, staff_lean=0.0, palm=None, crackle_k=None, face="calm",
           hem=0.0, sparks=(), orb=None, hurt=False, extra=None, raise_=0.0):
    """staff: the near hand's grip; staff_h: rod length above the grip; palm: the free hand thrust (None = at its side);
    raise_: 0..1 the staff lifted overhead (Static Build); crackle_k: lightning crawling up the staff."""
    r = Rig()
    by = bob
    # robe: a long cone, singed hem (ember flecks in the ink tone)
    P = r.part(False, 0.0)
    pts = [(-4.0 + lean, -17.0 + by), (4.2 + lean, -17.0 + by), (9.2 + hem, 0.0), (-9.6 - hem * 0.5, 0.0)]
    r.poly(pts, "robe", 0.0, normal=(-0.15, -0.2, 1.0), curve=0.8, part=P)
    for i in range(7):
        x = -5.0 + i * 1.6 + hem * 0.3
        r.dot(x, -0.5 - (i % 2), "robe", 0, 0.2)
        if i % 3 == 1: r.dot(x, -1.0, "ember", 2, 0.25)
    # cloth folds: shadowed creases with a lit edge beside each
    for fx0, fx1 in ((-2.0, -4.5), (0.6, 1.5), (3.0, 6.0)):
        r.polyline([(fx0 + lean, -15.0 + by), (fx1 + hem * 0.4, -1.5)], "robe", 0.1, tone=1)
        r.polyline([(fx0 + lean - 1, -14.0 + by), (fx1 + hem * 0.4 - 1, -2.5)], "robe", 0.1, tone=3)
    # storm-blue trim at the hem and down the front, a copper-buckled belt
    r.polyline([(-9.0 - hem * 0.5, -1.0), (8.6 + hem, -1.0)], "tabard", 0.15, tone=3)
    r.polyline([(-9.2 - hem * 0.5, -2.0), (8.8 + hem, -2.0)], "tabard", 0.15, tone=2)
    r.polyline([(1.6 + lean, -16.0 + by), (2.8 + hem * 0.4, -2.0)], "tabard", 0.16, tone=3)
    r.polyline([(-3.6 + lean * 0.6, -10.0 + by), (4.0 + lean * 0.6, -10.0 + by)], "apron", 0.2, tone=1)
    r.ell(1.6 + lean * 0.6, -10.0 + by, 1.2, 1.0, "copper", 0.25, bias=0.3, thin=True)
    # hood: a pointed cowl, dark mouth, storm eyes
    hx, hy = 0.8 + lean * 1.2, -19.5 + by
    r.ell(hx, hy, 4.4, 3.8, "robe", 0.5, bias=0.12)
    r.ell(hx - 0.5, hy + 3.0, 5.0, 2.0, "robe", 0.45, bias=0.0)
    r.poly([(hx - 2.0, hy - 2.6), (hx - 3.8, hy - 6.0), (hx + 0.5, hy - 3.2)], "robe", 0.45, bias=0.1)
    # the face in the hood: lean and pale, eyes lit storm blue, a grey beard
    r.ell(hx + 1.4, hy + 1.0, 2.4, 2.8, "dkiron", 0.6, flat=0)
    r.ell(hx + 1.8, hy + 0.8, 1.8, 2.2, "skin", 0.62, bias=0.2)
    r.polyline([(hx + 0.6, hy + 2.4), (hx + 1.6, hy + 4.4), (hx + 2.8, hy + 2.6)], "robe", 0.64, tone=4)
    r.dot(hx + 1.6, hy + 3.2, "robe", 3, 0.64)
    if hurt:
        r.dot(hx + 1.2, hy + 0.2, "storm", 2, 0.7); r.dot(hx + 2.8, hy + 0.6, "storm", 2, 0.7)
    else:
        r.dot(hx + 1.2, hy + 0.2, "storm", 4, 0.7); r.dot(hx + 2.8, hy + 0.2, "storm", 4, 0.7)
        r.dot(hx + 1.2, hy - 0.8, "storm", 2, 0.69)
    # the free arm (sleeve)
    if palm:
        r.tube([(2.0 + lean, -16.0 + by), palm], [1.6, 1.2], "robe", 1.5, bias=0.05, thin=True)
        r.ell(palm[0] + 0.6, palm[1], 1.0, 1.0, "skin", 1.6, thin=True)
        r.dot(palm[0] + 1.6, palm[1] - 1.0, "storm", 3, 1.7)
    else:
        r.tube([(-2.4 + lean, -16.0 + by), (-5.8, -9.5 + by)], [2.2, 1.8], "robe", -0.5, bias=-0.25, thin=True)
        r.dot(-6.2, -8.0 + by, "tabard", 3, -0.45); r.dot(-6.0, -7.4 + by, "storm", 3, -0.44)
    # the staff: iron, a copper finial and a storm tip, taller than its head
    sx, sy = staff
    tx, ty = sx + staff_lean, sy - staff_h + raise_ * -4.0
    bx, by2 = sx - staff_lean * 0.4, min(0.0, sy + 8.0 - raise_ * 6.0)
    # the staff: a copper lightning rod with brass collars, an iron fork at the top and storm light caught in it
    r.tube([(bx, by2), (tx, ty)], [0.8, 0.8], "copper", 2.0, bias=0.15, thin=True)
    for t in (0.25, 0.55):
        r.dot(lerp(bx, tx, t), lerp(by2, ty, t), "brass", 4, 2.05)
    r.polyline([(tx - 1.6, ty - 2.8), (tx - 1.0, ty), (tx + 1.0, ty), (tx + 1.6, ty - 2.8)], "iron", 2.1, tone=3)
    r.ell(tx, ty - 1.6, 1.3, 1.5, "storm", 2.15, flat=3)
    r.dot(tx, ty - 1.8, "storm", 4, 2.2); r.dot(tx, ty - 3.6, "storm", 3, 2.2)
    r.tube([(2.8 + lean, -16.0 + by), (sx, sy)], [2.2, 1.6], "robe", 2.3, bias=0.1, thin=True)
    r.ell(sx, sy, 1.1, 1.1, "skin", 2.4, thin=True)
    if crackle_k is not None:
        bolt(r, (tx, ty - 1), (tx + 1.5, ty - 6), z=6.0, n=2, amp=1.0, seed=crackle_k)
        bolt(r, (tx, ty - 1), (tx - 2.5, ty - 5), z=6.0, n=2, amp=1.0, seed=crackle_k + 9)
        crackle(r, sx + 0.5 + staff_lean * 0.3, sy - 6, crackle_k, seed=5)
    if orb:
        r.ell(orb[0], orb[1], 2.4, 2.4, "storm", 5.0, flat=2); r.ell(orb[0], orb[1], 1.4, 1.4, "storm", 5.1, flat=4)
    for (x, y, k) in sparks: spark(r, x, y, k)
    if extra: extra(r)
    return r.resolve()


def caller_sheet(outdir):
    C = caller
    idle = [C(bob=[0, -0.4, -0.8, -0.4][i], staff=(6.5, -10.5 + [0, -0.4, -0.8, -0.4][i]), crackle_k=None) for i in range(4)]
    run = [C(bob=-0.6 * abs(math.sin(i / 6 * math.tau)), lean=1.0, hem=0.8 * math.sin(i / 6 * math.tau),
             staff=(6.5, -12.5), staff_lean=2.0) for i in range(6)]
    ob = [C(palm=(1.0, -13.0)), C(palm=(-1.0, -14.0), lean=-1.0, orb=(-1.0, -15.0)),
          C(palm=(6.0, -14.0), lean=1.0, orb=(8.0, -14.5), sparks=[(5, -16, 3)]),
          C(palm=(9.0, -14.0), lean=2.0, orb=(12.0, -14.0), sparks=[(12, -14, 1)]), C(palm=(7.0, -13.0), lean=1.0), C()]
    bd = [C(staff=(6.0, -12.0)), C(staff=(5.0, -15.0), raise_=0.4, lean=-0.5, crackle_k=1),
          C(staff=(4.0, -18.0), raise_=1.0, lean=-1.0, crackle_k=2, sparks=[(4, -38, 1)])]
    bd += [C(staff=(4.0, -18.0), raise_=1.0, lean=-1.0, crackle_k=3 + i, sparks=[(4 + (i % 2) * 2, -37 - i % 3, 2)]) for i in range(4)]
    bd += [C(staff=(5.0, -14.0), raise_=0.4, crackle_k=9), C()]
    d0 = C(hurt=True, lean=-2.0, staff=(4.0, -11.0), staff_lean=-3.0)
    d1 = C(hurt=True, lean=-4.0, bob=3.0, staff=(1.0, -8.0), staff_lean=-7.0)
    d2 = caller_corpse(0)
    corpse = caller_corpse(1)
    knock = C(hurt=True, lean=-3.0, staff=(4.0, -12.0), staff_lean=-2.0)
    anims = [("Idle", idle, [0.16, 0.12, 0.16, 0.12]), ("Run", run, [0.08] * 6),
             ("Orb", ob, [0.12, 0.12, 0.1, 0.06, 0.12, 0.12]),
             ("Build", bd, [0.12, 0.12, 0.08, 0.08, 0.08, 0.08, 0.08, 0.1, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return msheet("KrnStormcaller", anims, outdir)


def caller_corpse(stage):
    r = Rig()
    r.poly([(-10.0, -4.0), (6.0, -5.0), (7.0, 0.0), (-11.0, 0.0)], "robe", 0.0, curve=0.6)
    r.ell(9.0, -2.8, 3.0, 2.8, "robe", 0.5, bias=0.1)
    r.ell(10.0, -2.4, 1.6, 1.6, "dkiron", 0.6, flat=0)
    r.tube([(-12.0, -1.0), (12.0, -6.0)], [0.6, 0.6], "iron", 1.0, thin=True)
    r.ell(12.5, -6.4, 1.2, 1.2, "copper", 1.1)
    if stage == 0: r.dot(13.0, -8.0, "storm", 3, 1.2); spark(r, 13.0, -9.0, 2)
    return r.resolve()


# ================================================================== LEYDEN GOLEM: a glass jar of lightning on brass legs
def leyden(level=0, bob=0.0, feet=((-3.0, 0.0), (3.0, 0.0)), clamp=(9.0, -14.0), clamp_open=0.0, jolt=False, ring=0.0,
           flash=0, lean=0.0, hurt=False, sparks=(), extra=None, crack=False):
    """level: 0..6 sparks stored (the jar fills with light, one mark per spark)."""
    r = Rig()
    by = -6.0 + bob
    # stumpy brass legs
    for k, f in enumerate(feet):
        z = -1.0 if k == 0 else 1.5
        leg(r, (lean * 0.3 + (-2.8 if k == 0 else 2.8), by), f, 2.8, 2.6, "brass", z, rad=(1.6, 1.4), boot="dkiron", boot_len=2.2,
            bias=-0.3 if k == 0 else 0.0)
    jx = lean * 0.5
    top, bot = by - 13.0, by
    # the jar: a glass barrel, the storm light inside filling from the bottom
    G = r.part(False, 0.0)
    for y in range(int(top), int(bot) + 1):
        t = (y - top) / (bot - top)
        w = 6.0 + 0.8 * math.sin(t * math.pi)
        for x in range(int(jx - w), int(jx + w) + 1):
            dx = (x - jx) / w
            nz = math.sqrt(max(0.0, 1 - dx * dx))
            r.put(x, y, 0.0, "glassk", 0.25 + (-dx) * 0.45 + nz * 0.2, G)
    fill = level / 6.0
    lvl_y = bot - 1 - (bot - top - 2) * fill
    if level > 0 or flash:
        L = r.part(True, 0.1)
        for y in range(int(lvl_y), int(bot)):
            t = (y - top) / (bot - top)
            w = 4.8 + 0.8 * math.sin(t * math.pi)
            for x in range(int(jx - w), int(jx + w) + 1):
                r.put(x, y, 0.1, "storm", 0.5, L, 3 if abs(x - jx) < w - 1.5 else 2)
        bolt(r, (jx, bot - 1), (jx + 0.5, max(lvl_y, top + 2)), z=0.2, n=3, amp=1.2, seed=level + flash, glow=None, core=4)
    # tally marks on the glass, one per stored spark (they light as it fills)
    for i in range(6):
        y = bot - 2 - i * 1.8
        r.polyline([(jx + 4.2, y), (jx + 5.8, y)], "storm" if i < level else "brass", 0.3, tone=4 if i < level else 1)
    if crack: r.polyline([(jx - 2, top + 3), (jx, top + 6), (jx - 1, top + 9)], "glassk", 0.4, tone=0)
    # copper hoops top and bottom, the cap with its terminal knob, a chain inside
    for y, w in ((top + 0.5, 6.2), (bot - 0.5, 6.2)):
        r.tube([(jx - w, y), (jx + w, y)], [1.0, 1.0], "copper", 0.5, bias=0.1)
    r.ell(jx, top - 1.2, 5.0, 1.8, "copper", 0.6, bias=0.15)
    r.tube([(jx, top - 2.0), (jx, top - 4.0)], [0.7, 0.7], "brass", 0.7, thin=True)
    r.ell(jx, top - 5.0, 1.4, 1.4, "brass", 0.8, bias=0.2)
    r.dot(jx - 0.5, top - 5.5, "storm" if level >= 3 else "brass", 4, 0.85)
    # two storm eyes on the cap's front plate
    r.dot(jx + 1.0, top + 2.0, "storm", 2 if hurt else 4, 0.6); r.dot(jx + 3.0, top + 2.0, "storm", 2 if hurt else 3, 0.6)
    # the copper clamp arm (near) and a stub arm (far)
    r.tube([(jx - 5.6, by - 8.0), (jx - 8.0, by - 5.0)], [1.2, 1.0], "copper", -0.5, bias=-0.3, thin=True)
    cx, cy = clamp
    r.tube([(jx + 5.6, by - 9.0), (lerp(jx + 5.6, cx, 0.5), lerp(by - 9.0, cy, 0.5) + 1.5), (cx, cy)], [1.3, 1.1, 1.0], "copper", 1.5, bias=0.05, thin=True)
    o = 1.0 + clamp_open * 1.5
    r.polyline([(cx, cy), (cx + 2.5, cy - o)], "brass", 1.6, tone=3); r.polyline([(cx, cy), (cx + 2.5, cy + o)], "brass", 1.6, tone=2)
    if jolt:
        bolt(r, (cx + 2.5, cy), (cx + 6.0, cy - 1.0), z=6.0, n=2, amp=0.8, seed=3)
    if ring > 0:
        R = 4.0 + ring * 12.0
        for i in range(32):
            a = i / 32 * math.tau
            if (i + int(ring * 8)) % 4 == 0: continue
            r.dot(jx + math.cos(a) * R, -1.0 + math.sin(a) * R * 0.4, "storm", 4 if ring < 0.6 else 2, 6.0)
    for (x, y, k) in sparks: spark(r, x, y, k)
    if extra: extra(r)
    return r.resolve()


def leyden_sheet(outdir):
    Lg = leyden
    anims = []
    for lv in range(7):
        idle = [Lg(level=lv, bob=[0, 0.4, 0.8, 0.4][i], flash=i) for i in range(4)]
        run = []
        for i in range(6):
            ph = i / 6 * math.tau
            f1 = (2.6 * math.cos(ph), -max(0.0, 1.4 * math.sin(ph)))
            f2 = (-2.6 * math.cos(ph), -max(0.0, -1.4 * math.sin(ph)))
            run.append(Lg(level=lv, bob=-0.6 * abs(math.sin(ph)), feet=(f2, f1), lean=1.0, flash=i))
        sfx = "" if lv == 0 else "J%d" % lv
        anims += [("Idle" + sfx, idle, [0.16, 0.12, 0.16, 0.12]), ("Run" + sfx, run, [0.08] * 6)]
    jo = [Lg(level=3, clamp=(8.0, -13.0)), Lg(level=3, clamp=(7.0, -15.0), clamp_open=1.0, lean=-1.0, sparks=[(9, -16, 3)]),
          Lg(level=3, clamp=(9.0, -15.0), clamp_open=1.0, sparks=[(11, -16, 2)]),
          Lg(level=2, clamp=(10.5, -15.0), clamp_open=0.6, jolt=True, lean=1.0, sparks=[(16, -16, 1)]),
          Lg(level=2, clamp=(9.5, -14.5)), Lg(level=2)]
    rg = [Lg(level=6, flash=1), Lg(level=6, bob=1.0, flash=2, sparks=[(0, -26, 2)]), Lg(level=6, bob=-1.0, flash=3, sparks=[(-3, -24, 1)]),
          Lg(level=6, bob=-1.5, flash=4, sparks=[(2, -27, 1)]), Lg(level=0, bob=1.0, ring=0.15), Lg(level=0, ring=0.4),
          Lg(level=0, ring=0.7), Lg(level=0, ring=0.95)]
    d0 = Lg(hurt=True, lean=-2.0, crack=True)
    d1 = Lg(hurt=True, lean=-4.0, bob=2.0, crack=True, sparks=[(-2, -20, 1)])
    d2 = leyden_corpse(0)
    corpse = leyden_corpse(1)
    knock = Lg(hurt=True, lean=-3.0, crack=True)
    idle0 = anims[0][1][0]
    anims += [("Jolts", jo, [0.12, 0.12, 0.1, 0.06, 0.12, 0.12]), ("Ring", rg, [0.1, 0.1, 0.1, 0.1, 0.06, 0.08, 0.1, 0.12])]
    anims += tail_anims(idle0, [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return msheet("KrnLeydenGolem", anims, outdir)


def leyden_corpse(stage):
    r = Rig()
    # the jar burst on its side: glass shards, the cap rolled off
    r.poly([(-8.0, -6.0), (4.0, -7.0), (5.0, 0.0), (-8.0, 0.0)], "glassk", 0.0, normal=(-0.3, -0.5, 0.8))
    r.tube([(-8.0, -3.0), (5.0, -3.5)], [0.8, 0.8], "copper", 0.2, thin=True)
    r.ell(9.0, -2.0, 3.0, 2.0, "copper", 0.4, bias=0.15)
    for (x, y) in ((-10, -1), (7, -1), (-4, -8), (0, -8)):
        r.dot(x, y, "glassk", 3, 0.5)
    for k in range(2):
        r.tube([(-3.0 + k * 4.0, -1.0), (-2.0 + k * 4.0, 0.0)], [1.2, 1.2], "brass", 0.3)
    if stage == 0: spark(r, -2.0, -8.0, 1)
    return r.resolve()


# ================================================================== ARC LANTERN: an iron cage with a lightning wick on its own chain
def lantern(hover=2.5, swing=0.0, wick=1.0, door=0.0, hurt=False, sparks=(), wisp=None, field=0.0, extra=None, dark=False):
    """swing: tilt (deg) on its chain; wick: flame size; door: 0..1 the front pane swung open (casting)."""
    r = Rig()
    shadow(r, 0.0, 0.0, 3.0)
    by = -hover
    a = math.radians(swing)
    ca, sa = math.cos(a), math.sin(a)
    piv = (0.0, by - 20.0)
    T = lambda x, y: (piv[0] + (x - piv[0]) * ca - (y - piv[1]) * sa, piv[1] + (x - piv[0]) * sa + (y - piv[1]) * ca)
    # the chain rising out of the top (it hangs from nothing)
    for i in range(3):
        x, y = T(0.0, by - 17.0 - i * 1.6)
        r.dot(x, y, "dkiron", 2 if i % 2 else 3, 1.0)
        if i % 2 == 0: r.dot(x + 0.6, y, "dkiron", 1, 0.95)
    # the cage: a top hood, four bars, a base, glass panes faintly lit
    r.poly([T(-6.6, by - 13.0), T(6.6, by - 13.0), T(3.0, by - 16.4), T(-3.0, by - 16.4)], "dkiron", 0.5, normal=(-0.3, -0.7, 0.6))
    r.dot(*T(0.0, by - 16.5), "brass", 3, 0.6)
    r.poly([T(-7.0, by - 1.5), T(7.0, by - 1.5), T(4.5, by + 0.5), T(-4.5, by + 0.5)], "dkiron", 0.5, normal=(-0.3, 0.3, 0.9))
    pane = r.part(False, 0.0)
    for y in range(int(by - 13), int(by - 1)):
        for x in range(-6, 7):
            px, py = T(x, y)
            r.put(px, py, 0.0, "glassk", 0.1 + (-x) * 0.12, pane)
    # the wick: blue-white flame in the middle
    fx, fy = T(0.0, by - 6.5)
    if not dark:
        h = 3.2 * wick
        r.ell(fx, fy - h * 0.3, 2.8 * wick, h, "storm", 0.2, flat=2)
        r.ell(fx, fy - h * 0.2, 1.2 * wick, h * 0.7, "storm", 0.3, flat=3)
        r.dot(fx, fy - 0.5, "storm", 4, 0.35)
        bolt(r, (fx, fy + 2.5), (fx, fy - h), z=0.4, n=2, amp=0.8, seed=int(wick * 10), glow=None)
    r.dot(fx, fy + 3.0, "brass", 2, 0.35)
    for x in (-6.5, -2.2, 2.2, 6.5):
        p0, p1 = T(x if abs(x) > 2 else x, by - 13.0), T(x, by - 1.5)
        r.polyline([p0, p1], "dkiron", 1.0, tone=3 if x < 0 else 1)
    if door > 0:
        d0, d1 = T(5.5, by - 13.0), T(5.5, by - 1.5)
        r.polyline([d0, (d1[0] + 3 * door, d1[1] - 2 * door)], "dkiron", 1.2, tone=2)
    # eyes in the hood's shadow
    r.dot(*T(1.0, by - 11.5), "storm", 2 if hurt else 4, 1.1); r.dot(*T(2.5, by - 11.5), "storm", 2 if hurt else 3, 1.1)
    if wisp:
        r.ell(wisp[0], wisp[1], 1.8, 1.8, "storm", 5.0, flat=2); r.dot(wisp[0], wisp[1], "storm", 4, 5.1)
    if field > 0:
        for i in range(10):
            ang = i / 10 * math.tau + field * 3
            r.dot(fx + math.cos(ang) * (4 + field * 4), fy + math.sin(ang) * (3 + field * 3), "storm", 3, 6.0)
    for (x, y, k) in sparks: spark(r, x, y, k)
    if extra: extra(r)
    return r.resolve()


def lantern_sheet(outdir):
    Ln = lantern
    idle = [Ln(hover=2.5 + [0, 0.5, 1, 0.5][i], swing=[0, 4, 0, -4][i], wick=[1.0, 1.15, 0.9, 1.1][i]) for i in range(4)]
    run = [Ln(hover=3.0, swing=-8 + 3 * math.sin(i / 6 * math.tau), wick=1.0 + 0.1 * (i % 2)) for i in range(6)]
    sk = [Ln(wick=1.2), Ln(wick=1.5, swing=-8), Ln(wick=1.6, swing=-4, door=0.6, sparks=[(5, -14, 3)]),
          Ln(wick=0.7, swing=6, door=1.0, wisp=(9.0, -12.0), sparks=[(8, -12, 1)]), Ln(wick=0.8, swing=3, door=0.5), Ln()]
    fd = [Ln(wick=1.2), Ln(wick=1.5, hover=5.0), Ln(wick=1.8, hover=6.0, field=0.2), Ln(wick=1.9, hover=6.0, field=0.5),
          Ln(wick=0.6, hover=3.0, field=0.9, sparks=[(0, -2, 1)]), Ln(wick=0.8, hover=3.5), Ln(wick=0.9, hover=4.0), Ln()]
    d0 = Ln(hurt=True, swing=15, wick=0.6)
    d1 = Ln(hurt=True, swing=35, wick=0.3, hover=2.0, sparks=[(3, -8, 1)])
    d2 = lantern_corpse(0)
    corpse = lantern_corpse(1)
    knock = Ln(hurt=True, swing=20, wick=0.7)
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.08] * 6),
             ("Seek", sk, [0.12, 0.12, 0.1, 0.06, 0.12, 0.12]),
             ("Field", fd, [0.1, 0.1, 0.12, 0.1, 0.06, 0.1, 0.1, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return msheet("KrnArcLantern", anims, outdir)


def lantern_corpse(stage):
    r = Rig()
    r.poly([(-7.0, -8.0), (5.0, -8.0), (5.0, 0.0), (-7.0, 0.0)], "glassk", 0.0)
    for x in (-7, -3, 1, 5): r.polyline([(x, -8), (x, 0)], "dkiron", 0.5, tone=2)
    r.polyline([(-7, -8), (5, -8)], "dkiron", 0.5, tone=3)
    r.poly([(5.0, -7.0), (8.0, -5.0), (8.0, -2.0), (5.0, -1.0)], "dkiron", 0.6)
    for i in range(3): r.dot(-9 - i * 1.6, -1, "dkiron", 2, 0.7)
    if stage == 0: r.dot(-1.0, -3.0, "storm", 3, 0.8); spark(r, -1.0, -10.0, 2)
    return r.resolve()


SYNC = {
    "KrnAnvilSmith": {"Hammer": [("HIT: hammer head on the floor at (18, -1); the surge runs on from (20, -3)", 3)],
                      "Plant": [("the rod is driven in at (11, 0), red hot", 3), ("the iron plate gathers", 4)]},
    "KrnWireGremlin": {"Staple": [("staple leaves the muzzle at (12, -14)", 3)],
                       "WireUp": [("the hooked wire is flicked from (9, -15)", 3)]},
    "KrnLodeHound": {"Leap": [("BITE: jaws at (19, -12)", 3)], "LeapBlue": [("BITE: jaws at (19, -12)", 3)],
                     "Howl": [("the field opens (pull)", 2)], "HowlBlue": [("the field opens (push)", 2)]},
    "KrnStormcaller": {"Orb": [("ball leaves the palm at (11, -14)", 3)],
                       "Build": [("staff raised: Static Build starts", 2)]},
    "KrnLeydenGolem": {"Jolts": [("jolts leave the clamp at (14, -15)", 3)], "Ring": [("RING: the jar empties", 4)]},
    "KrnArcLantern": {"Seek": [("wisp leaves the open pane at (9, -12)", 3)], "Field": [("the field drops on the hero", 4)]},
}
NOTES = {
    "KrnLodeHound": "Idle/Run/Leap/Howl wear the RED collar (the next howl pulls); the *Blue anims wear the BLUE collar (pushes).",
    "KrnLeydenGolem": "Idle/Run = an empty jar; IdleJ1..IdleJ6 / RunJ1..RunJ6 show 1..6 stored sparks (tally marks light up).",
}
JOBS = [("KrnAnvilSmith", smith_sheet), ("KrnWireGremlin", gremlin_sheet), ("KrnLodeHound", hound_sheet),
        ("KrnStormcaller", caller_sheet), ("KrnLeydenGolem", leyden_sheet), ("KrnArcLantern", lantern_sheet)]
