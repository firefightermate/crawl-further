"""Kaurn tier 3 (Anvil Smith and Wire Gremlin and Lodestone Hound lines): Forge Colossus, Forgemaster, Wire Wyvern, Fuse
Sapper, Thunder Bull, Polarity Warg (built through kaurn_v2_rigs.py). T3 idle limit 42 x 40."""
import math
from kaurn_v2_rigs import (Rig, lerp, ik, msheet, tail_anims, leg, arm, hammer, bolt, crackle, spark, eye, shadow, rod,
                           dust_puff, zig, line_px, arc_smear)
from jinx_v2_rigs import bat_wing
from kaurn_v2_t2 import quad, SMITH_FACE, SMITH_FACES, GREM_FACE, GREM_FACES

HEAT = {0: "coal", 1: "ember", 2: "fire", 3: "steam", -1: None}


# ================================================================== FORGE COLOSSUS: an iron giant, a furnace in its chest
def colossus(heat=0, bob=0.0, lean=0.0, feet=((-6.0, 0.0), (6.0, 0.0)), fists=((14.0, -13.0), (-13.0, -13.0)), squash=0.0,
             whistle=0, steam=0, smoke=1, hurt=False, sparks=(), extra=None, smear=None, head_dx=0.0):
    """heat: 0 dull, 1 orange, 2 yellow, 3 white-hot (venting), -1 cold (vented: dark grille, steam wisps).
    fists: (near, far) anvil-fist centres; whistle: the chimney shrieks (a jet of steam); steam: 0..3 the vent blast."""
    r = Rig()
    by = -21.0 + bob + squash
    tx = lean
    # legs: columns of riveted iron
    for k, f in enumerate(feet):
        z = -2.0 if k == 0 else 2.0
        leg(r, (tx * 0.4 + (-5.0 if k == 0 else 5.0), by + 8.0), f, 6.5, 6.0, "iron", z, rad=(4.0, 3.2), boot="dkiron", boot_len=4.0,
            bias=-0.3 if k == 0 else 0.0)
    # chimney on the back (behind), with its smoke
    cx0, cy0 = tx - 6.0, by - 8.0
    r.tube([(cx0, cy0), (cx0 - 2.5, cy0 - 8.5)], [2.4, 2.1], "dkiron", -3.0, bias=0.1)
    r.ell(cx0 - 2.5, cy0 - 9.0, 2.8, 1.0, "iron", -2.9, bias=0.2)
    if whistle:
        for i in range(6): r.dot(cx0 - 2.0 + (i % 2), cy0 - 10.5 - i * 1.3, "steam", 4 if i < 3 else 3, 6.0)
        r.dot(cx0 + 0.5, cy0 - 14.0, "steam", 3, 6.0); r.dot(cx0 - 4.5, cy0 - 15.0, "steam", 2, 6.0)
    elif smoke and heat >= 0:
        for i in range(smoke + 1): r.dot(cx0 - 2.5 - i * 0.6 + (i % 2), cy0 - 11.0 - i * 1.5, "smoke", 2, -2.8)
    elif heat < 0:
        for i in range(3): r.dot(cx0 - 2.0 + (i % 2) * 2 - 1, cy0 - 11.0 - i * 2.0, "steam", 2, -2.8)
    # far arm and its anvil fist (behind the body)
    def fist_block(c, z, bias):
        x, y = c
        r.poly([(x - 4.2, y - 3.4), (x + 4.2, y - 3.4), (x + 4.2, y + 1.0), (x + 2.4, y + 1.8), (x + 2.4, y + 3.4), (x - 2.8, y + 3.4),
                (x - 2.8, y + 1.8), (x - 4.2, y + 1.0)], "dkiron", z, bias=bias, normal=(-0.3, -0.5, 0.8))
        r.polyline([(x - 4.2, y - 3.4), (x + 4.2, y - 3.4)], "iron", z + 0.01, tone=4 if bias >= 0 else 2)
        r.polyline([(x - 4.2, y - 1.2), (x + 4.2, y - 1.2)], "copper", z + 0.015, tone=3 if bias >= 0 else 1)
        r.dot(x - 2.6, y - 2.2, "brass", 4 if bias >= 0 else 2, z + 0.02); r.dot(x + 2.6, y - 2.2, "brass", 3 if bias >= 0 else 1, z + 0.02)
    near, far = fists
    r.tube([(tx - 10.0, by - 6.0), (lerp(tx - 10.0, far[0], 0.5) - 2.0, lerp(by - 6.0, far[1], 0.5)), far], [3.0, 2.6, 2.4], "iron", -1.5,
           bias=-0.35, thin=True)
    fist_block(far, -1.4, -0.3)
    # torso: a barrel of plate, a broad yoke of shoulders
    P = r.part(False, 0.0)
    r.ell(tx, by, 11.0, 9.4, "iron", 0.0, bias=0.0, part=P)
    r.ell(tx + 0.5, by - 6.5, 13.5, 5.0, "iron", 0.0, bias=0.15, part=P)
    # copper belly plates and brass rivets round the furnace
    r.ell(tx + 1.5, by + 2.5, 8.6, 6.4, "copper", 0.12, bias=0.1, clip=lambda x, y: y > by - 3.0)
    for (x, y) in ((-8, -7), (-3, -10), (3, -10), (8, -7), (-8, 2), (8, 3), (-5, 6), (6, 7)):
        r.dot(tx + x, by + y, "brass", 4, 0.15)
    # the furnace: a grated mouth in the chest
    gx, gy = tx + 2.0 + head_dx * 0.3, by + 0.5
    r.ell(gx, gy, 6.6, 5.6, "brass", 0.18, bias=0.25)
    r.ell(gx, gy, 5.4, 4.6, "dkiron", 0.2, flat=1)
    hm = HEAT.get(heat)
    if hm:
        r.ell(gx, gy + 0.4, 4.6, 3.8, hm, 0.3, flat=2 if heat == 0 else 3)
        r.ell(gx, gy + 1.0, 3.2, 2.4, hm, 0.31, flat=3 if heat < 2 else 4)
        r.dot(gx - 1, gy + 1.5, hm, 4, 0.32)
        # the heat spills out over the plates above the grate
        for i in range(-4, 5):
            if (i + heat) % 2 == 0: r.dot(gx + i, gy - 6.2 + abs(i) * 0.3, hm, 2 if heat < 2 else 3, 0.33)
    for i in range(-2, 3):
        r.polyline([(gx + i * 1.8, gy - 3.5), (gx + i * 1.8, gy + 3.5)], "dkiron", 0.4, tone=2 if i < 0 else 1)
    # small head sunk between the shoulders, a slit visor with storm eyes
    hx, hy = tx + 2.5 + head_dx, by - 11.5 + squash * 0.5
    r.ell(tx - 10.0, by - 7.5, 4.2, 3.4, "copper", -1.2, bias=-0.2)       # far pauldron
    r.ell(hx, hy, 3.6, 3.2, "dkiron", 0.5, bias=0.2)
    r.poly([(hx - 1.0, hy - 3.0), (hx + 1.0, hy - 3.0), (hx + 0.0, hy - 5.0)], "brass", 0.55, bias=0.2)
    r.polyline([(hx - 1.5, hy), (hx + 3.0, hy)], "dkiron", 0.6, tone=0)
    if not hurt:
        r.dot(hx + 0.5, hy, "storm", 4, 0.7); r.dot(hx + 2.5, hy, "storm", 3, 0.7)
    else:
        r.dot(hx + 0.5, hy, "storm", 2, 0.7)
    # near arm and anvil fist
    r.tube([(tx + 10.0, by - 6.0), (lerp(tx + 10.0, near[0], 0.5) + 2.0, lerp(by - 6.0, near[1], 0.5)), near], [3.4, 3.0, 2.6], "iron", 3.0,
           bias=0.05, thin=True)
    r.ell(tx + 10.5, by - 7.0, 4.8, 4.0, "copper", 3.05, bias=0.2)     # pauldron
    r.polyline([(tx + 6.5, by - 5.0), (tx + 14.5, by - 5.5)], "brass", 3.06, tone=3)
    r.dot(tx + 9.0, by - 9.0, "brass", 4, 3.07); r.dot(tx + 12.0, by - 8.5, "brass", 3, 3.07)
    fist_block(near, 3.2, 0.0)
    if steam:
        R = 6.0 + steam * 6.0
        for i in range(24):
            a = i / 24 * math.tau
            if (i + steam) % 3 == 0: continue
            r.ell(gx + math.cos(a) * R, by + 10.0 + math.sin(a) * R * 0.45 - 2, 1.4, 1.1, "steam", 6.0, flat=3 if steam < 3 else 2)
        for i in range(5): r.dot(gx + 6 + i * 2, gy + (i % 2), "steam", 4, 6.1)
    if smear:
        for pts, tn in smear: r.polyline(pts, "steam", 4.6, tone=tn)
    for (x, y, k) in sparks: spark(r, x, y, k, mat="ember" if k == 1 else "storm")
    if extra: extra(r)
    return r.resolve()


def colossus_sheet(outdir):
    C = colossus
    anims = []
    for suf, heat in (("", 0), ("H1", 1), ("H2", 2), ("Cold", -1)):
        idle = [C(heat=heat, bob=[0, 0.5, 1.0, 0.5][i], fists=((14.0, -13.0 + [0, 0.5, 1, 0.5][i]), (-13.0, -13.0 + [0, 0.5, 1, 0.5][i])),
                  smoke=0) for i in range(4)]
        run = []
        for i in range(6):
            ph = i / 6 * math.tau
            f1 = (5.0 * math.cos(ph) + 1, -max(0.0, 2.4 * math.sin(ph)))
            f2 = (-5.0 * math.cos(ph) - 1, -max(0.0, -2.4 * math.sin(ph)))
            b = -1.0 * abs(math.sin(ph))
            sw = 2.0 * math.sin(ph)
            run.append(C(heat=heat, lean=1.0, bob=b, feet=(f2, f1), fists=((14.0 + sw, -14.0 + b), (-12.0 - sw, -14.0 + b)), smoke=i % 3))
        anims += [("Idle" + suf, idle, [0.2, 0.16, 0.2, 0.16]), ("Run" + suf, run, [0.09] * 6)]
    # Slam: both fists up, smash down 17 px ahead (quake), the floor jumps, heave back up
    sl = [C(heat=1, fists=((12.0, -22.0), (-8.0, -24.0)), bob=-1.0),
          C(heat=1, fists=((8.0, -33.0), (-2.0, -34.0)), bob=-2.0, lean=-1.5),
          C(heat=1, fists=((10.0, -36.0), (2.0, -36.0)), bob=-2.5, lean=-2.0),
          C(heat=2, fists=((17.0, -16.0), (12.0, -18.0)), lean=2.0, smear=[([(4, -44), (14, -38), (19, -26)], 2), ([(8, -42), (17, -32)], 3)]),
          C(heat=2, fists=((18.0, -3.5), (13.0, -4.0)), lean=3.0, squash=2.0, sparks=[(20, -1, 1), (11, -1, 2), (24, -3, 2)],
            extra=lambda r: dust_puff(r, 17.0, 0.0, 0, 1.6)),
          C(heat=2, fists=((18.0, -4.0), (13.0, -4.5)), lean=2.5, squash=1.5, extra=lambda r: dust_puff(r, 17.0, 0.0, 1, 2.0)),
          C(heat=1, fists=((15.0, -10.0), (-10.0, -12.0)), lean=1.0),
          C(heat=1)]
    # Fence: arms wide, both fists pound the floor to either side (rods burst up there), arms back in
    fe = [C(heat=1, fists=((15.0, -20.0), (-14.0, -20.0))), C(heat=1, fists=((16.0, -30.0), (-15.0, -30.0)), bob=-2.0),
          C(heat=1, fists=((15.0, -34.0), (-14.0, -34.0)), bob=-2.5, whistle=0),
          C(heat=2, fists=((17.0, -20.0), (-16.0, -20.0)), smear=[([(15, -38), (18, -26)], 3), ([(-14, -38), (-17, -26)], 3)]),
          C(heat=2, fists=((17.0, -5.0), (-16.0, -5.0)), squash=2.0, sparks=[(19, -2, 1), (-18, -2, 1)]),
          C(heat=2, fists=((17.0, -4.0), (-16.0, -4.0)), squash=2.0, extra=lambda r: (dust_puff(r, 17.0, 0.0, 0, 1.4), dust_puff(r, -16.0, 0.0, 0, 1.4))),
          C(heat=2, fists=((16.0, -8.0), (-15.0, -8.0)), squash=1.0), C(heat=1, fists=((15.0, -12.0), (-14.0, -12.0))), C(heat=1)]
    # Vent: white-hot, the chimney shrieks, shudder, BLAST (steam 30 px round it), sag cold
    vt = [C(heat=3, whistle=1), C(heat=3, whistle=1, lean=-1.0, bob=-0.5), C(heat=3, whistle=1, lean=1.0, bob=-1.0),
          C(heat=3, whistle=1, steam=1, squash=1.0, fists=((15.0, -16.0), (-14.0, -16.0))),
          C(heat=-1, steam=2, squash=1.5, fists=((15.0, -15.0), (-14.0, -15.0))), C(heat=-1, steam=3, squash=2.0),
          C(heat=-1, squash=2.5, fists=((13.0, -10.0), (-12.0, -10.0)), head_dx=1.0), C(heat=-1, squash=2.0)]
    d0 = C(heat=0, hurt=True, lean=-2.0, fists=((12.0, -18.0), (-14.0, -10.0)))
    d1 = C(heat=-1, hurt=True, lean=-4.0, squash=4.0, fists=((10.0, -6.0), (-16.0, -6.0)), smoke=0)
    d2 = colossus_corpse(0)
    corpse = colossus_corpse(1)
    knock = C(heat=0, hurt=True, lean=-3.0, fists=((11.0, -16.0), (-15.0, -12.0)))
    idle0 = anims[0][1][0]
    anims += [("Slam", sl, [0.14, 0.14, 0.12, 0.05, 0.08, 0.12, 0.14, 0.14]),
              ("Fence", fe, [0.12, 0.12, 0.12, 0.05, 0.06, 0.12, 0.12, 0.12, 0.12]),
              ("Vent", vt, [0.12, 0.08, 0.08, 0.06, 0.1, 0.12, 0.16, 0.16])]
    anims += tail_anims(idle0, [d0, d1, d2, corpse], [0.12, 0.14, 0.16, 0.4], knock)
    return msheet("KrnForgeColossus", anims, outdir)


def colossus_corpse(stage):
    r = Rig()
    # toppled on its back, the furnace guttering, an anvil fist beside it
    r.ell(0.0, -6.0, 14.0, 6.0, "iron", 0.0, bias=0.1)
    r.ell(1.0, -9.0, 5.0, 2.6, "dkiron", 0.2, flat=1)
    if stage == 0: r.ell(1.0, -9.0, 3.4, 1.6, "coal", 0.3, flat=2)
    r.ell(15.0, -4.0, 3.2, 2.8, "dkiron", 0.4, bias=0.1)
    r.tube([(-12.0, -6.0), (-19.0, -3.0)], [3.0, 2.6], "iron", 0.3)
    r.poly([(-23.0, -6.0), (-17.0, -6.0), (-17.0, 0.0), (-23.0, 0.0)], "dkiron", 0.4)
    r.tube([(-6.0, -11.0), (-9.0, -18.0 + stage * 2)], [2.0, 1.8], "dkiron", -0.5)
    for i in range(3 - stage * 2): r.dot(-9.0 + i, -20.0 - i * 2, "smoke", 2, -0.4)
    if stage == 0: spark(r, 4.0, -14.0, 2)
    return r.resolve()


# ================================================================== FORGEMASTER: master smith, a quiver of rods on his back
def master(rods=3, bob=0.0, lean=0.0, feet=((-4.0, 0.0), (4.0, 0.0)), hands=(9.0, -20.0), ham=-70.0, face="calm", throw=None,
           reach=False, smear=None, sparks=(), squash=0.0, hurt=False, extra=None):
    """rods: 0..3 carried in the quiver (each fans up behind his shoulders); throw: (x, y, ang) of rods leaving the hand."""
    r = Rig()
    if hurt and face == "calm": face = "hurt"
    by = -17.5 + bob + squash
    tx = lean * 0.6
    # quiver and its rods (behind)
    qx, qy = tx - 5.0, by - 8.0
    r.tube([(qx + 1.5, qy + 9.0), (qx - 1.0, qy - 2.0)], [2.4, 2.8], "apron", -3.0, bias=-0.1)
    for t in (0.2, 0.75):
        r.tube([(lerp(qx + 1.5, qx - 1.0, t) - 2.4, lerp(qy + 9.0, qy - 2.0, t)), (lerp(qx + 1.5, qx - 1.0, t) + 2.4, lerp(qy + 9.0, qy - 2.0, t) - 0.4)],
               [0.8, 0.8], "brass", -2.95, bias=0.2, thin=True)
    r.ell(qx - 1.0, qy - 2.0, 3.0, 1.2, "apron", -2.9, bias=0.1)
    for i in range(rods):
        a = math.radians(-128 + i * 20)
        sx, sy = qx - 1.0 + (i - 1) * 1.4, qy - 2.0
        ex, ey = sx + 9.0 * math.cos(a), sy + 9.0 * math.sin(a)
        r.tube([(sx, sy + 3), (ex, ey)], [1.1, 0.9], "iron", -3.5 + i * 0.1, bias=0.2, thin=True)
        r.ell(ex, ey, 1.5, 1.5, "copper", -3.4 + i * 0.1, bias=0.25, thin=True)
        r.dot(ex, ey - 1.6, "storm", 4, -3.35 + i * 0.1)
        for t in (0.35, 0.6):
            mx, my = lerp(sx, ex, t), lerp(sy, ey, t)
            r.dot(mx - 0.5, my, "brass", 4, -3.3 + i * 0.1); r.dot(mx + 0.6, my, "brass", 2, -3.3 + i * 0.1)
    # legs: long, booted
    for k, f in enumerate(feet):
        z = -1.0 if k == 0 else 1.5
        leg(r, (tx * 0.5 + (-2.2 if k == 0 else 2.2), by + 4.0), f, 7.4, 7.0, "apron", z, rad=(2.4, 2.0), boot="dkiron", boot_len=3.0,
            bias=-0.3 if k == 0 else 0.0)
    # torso: tall, a heavy apron, brass-studded belt
    # torso: a soot-black leather jerkin, a riveted iron breastplate, the long smith's apron down to the knees
    P = r.part(False, 0.0)
    r.ell(tx, by - 3.0, 6.4, 8.0, "soot", 0.0, bias=0.0, part=P)
    r.ell(tx + 0.4, by - 9.0, 7.6, 3.4, "soot", 0.0, bias=0.15, part=P)
    r.poly([(tx - 4.2, by - 10.5), (tx + 5.4, by - 10.5), (tx + 5.0, by - 3.0), (tx + 0.5, by - 1.5), (tx - 3.8, by - 3.0)], "iron", 0.3,
           normal=(-0.2, -0.3, 1.0), curve=0.8)
    for (x, y) in ((-3.0, -9.5), (4.0, -9.5), (-2.6, -4.0), (3.6, -4.0)): r.dot(tx + x, by + y, "brass", 4, 0.35)
    r.poly([(tx - 3.6, by - 2.0), (tx + 5.4, by - 2.0), (tx + 7.0, by + 9.0), (tx - 4.8, by + 9.0)], "apron", 0.4, curve=0.7)
    r.polyline([(tx - 4.4, by + 8.5), (tx + 6.8, by + 8.5)], "copper", 0.42, tone=2)
    r.polyline([(tx - 5.8, by + 0.5), (tx + 6.4, by + 0.5)], "apron", 0.5, tone=0)
    for x in (-3, 0, 3): r.dot(tx + x, by + 0.5, "brass", 4, 0.55)
    r.polyline([(tx - 4.5, by - 10.0), (tx + 3.0, by + 0.0)], "apron", 0.45, tone=1)   # quiver strap
    # an iron pauldron on the hammer shoulder
    r.ell(tx + 5.0, by - 9.5, 3.6, 2.8, "iron", 2.7, bias=0.25)
    r.polyline([(tx + 2.0, by - 8.0), (tx + 8.0, by - 8.4)], "copper", 2.71, tone=3)
    r.dot(tx + 5.0, by - 10.5, "brass", 4, 2.72)
    # head: bearded, iron goggles pushed up
    hx, hy = tx + 1.5 + lean * 0.8, by - 15.0 + squash * 0.5
    r.ell(hx, hy, 3.6, 3.8, "skin", 0.6, bias=0.05)
    r.dot(hx - 1.5, hy + 1.0, "soot", 2, 0.61); r.dot(hx - 2.2, hy - 0.5, "soot", 2, 0.61)      # soot smudges
    r.tube([(hx - 3.0, hy - 2.6), (hx + 3.2, hy - 2.4)], [0.8, 0.8], "dkiron", 0.65, thin=True)
    r.dot(hx + 1.0, hy - 2.6, "brass", 4, 0.7); r.dot(hx + 2.8, hy - 2.4, "brass", 3, 0.7)
    r.stamp(SMITH_FACES[face], hx + 0.6, hy - 0.8, 0.8, SMITH_FACE, pivot=(1, 1))
    # sledge in both hands
    if hands is not None:
        hx2, hy2 = hands
        g2 = (hx2 - 2.6 * math.cos(math.radians(ham)), hy2 - 2.6 * math.sin(math.radians(ham)))
        far = g2 if not reach else (qx - 1.0, qy - 4.0)
        ex, ey = arm(r, (tx - 3.0, by - 8.5), far, 5.4, 5.0, "skin", -0.5, rad=(1.8, 1.4), fist="soot", fist_r=1.5, bias=-0.3)
        r.tube([(lerp(ex, far[0], 0.3), lerp(ey, far[1], 0.3)), (lerp(ex, far[0], 0.75), lerp(ey, far[1], 0.75))], [1.7, 1.6], "copper", -0.45,
               bias=-0.1, thin=True)
        hx3, hy3 = hammer(r, g2[0], g2[1], ham, 12.0, 2.0, head=(8.4, 5.2), haft="wood", head_mat="dkiron", glow="ember", back=2.0)
        a = math.radians(ham)
        r.polyline([(hx3 - 3.4 * math.sin(a), hy3 + 3.4 * math.cos(a)), (hx3 + 3.4 * math.sin(a), hy3 - 3.4 * math.cos(a))], "copper", 2.06, tone=3)
        ex, ey = arm(r, (tx + 4.5, by - 8.5), (hx2, hy2), 5.4, 5.0, "skin", 2.6, rad=(2.0, 1.6), fist="soot", fist_r=1.7)
        r.tube([(lerp(ex, hx2, 0.25), lerp(ey, hy2, 0.25)), (lerp(ex, hx2, 0.75), lerp(ey, hy2, 0.75))], [1.9, 1.8], "copper", 2.65, bias=0.1, thin=True)
    if throw:
        x, y, a = throw
        for i in range(3):
            aa = math.radians(a + (i - 1) * 14)
            r.tube([(x, y), (x + 9 * math.cos(aa), y + 9 * math.sin(aa))], [0.8, 0.7], "iron", 5.0 + i * 0.01, thin=True)
            r.ell(x + 9 * math.cos(aa), y + 9 * math.sin(aa), 1.0, 1.0, "copper", 5.05, thin=True)
    if smear:
        for pts, tn in smear: r.polyline(pts, "steam", 4.6, tone=tn)
    for (x, y, k) in sparks: spark(r, x, y, k, mat="ember" if k == 1 else "storm")
    if extra: extra(r)
    return r.resolve()


def master_sheet(outdir):
    M = master
    anims = []
    for n in (2, 0, 1, 3):
        suf = "" if n == 2 else "R%d" % n
        idle = [M(rods=n, bob=[0, 0.4, 0.8, 0.4][i], ham=-70 + [0, 2, 4, 2][i], hands=(9.0, -20.0 + [0, 0.4, 0.8, 0.4][i])) for i in range(4)]
        run = []
        for i in range(6):
            ph = i / 6 * math.tau
            f1 = (4.0 * math.cos(ph), -max(0.0, 2.2 * math.sin(ph)))
            f2 = (-4.0 * math.cos(ph), -max(0.0, -2.2 * math.sin(ph)))
            b = -0.9 * abs(math.sin(ph))
            run.append(M(rods=n, lean=1.0, bob=b, feet=(f2, f1), ham=-85 + 6 * math.sin(ph), hands=(9.0, -20.5 + b)))
        anims += [("Idle" + suf, idle, [0.18, 0.14, 0.18, 0.14]), ("Run" + suf, run, [0.08] * 6)]
    sw = [M(rods=1, ham=-130, hands=(5.0, -22.0), lean=-1.0, face="roar"), M(rods=1, ham=-175, hands=(0.0, -25.0), lean=-2.0, bob=-1.0, face="roar"),
          M(rods=1, ham=-40, hands=(10.0, -19.0), lean=2.0, face="roar", smear=[([(-4, -40), (10, -38), (20, -26), (24, -12)], 2)]),
          M(rods=1, ham=20, hands=(12.0, -9.0), lean=3.0, squash=1.5, face="roar", sparks=[(23, -2, 1), (19, -1, 2)],
            extra=lambda r: dust_puff(r, 21.0, 0.0, 0, 1.4)),
          M(rods=1, ham=15, hands=(12.0, -9.5), lean=2.5, squash=1.0, extra=lambda r: dust_puff(r, 21.0, 0.0, 1, 1.6)),
          M(rods=1, ham=-30, hands=(10.0, -14.0), lean=1.0), M(rods=1)]
    vo = [M(rods=3), M(rods=3, reach=True, ham=-60, face="roar"), M(rods=3, reach=True, ham=-60, lean=-1.5, face="roar"),
          M(rods=0, ham=-60, lean=-2.5, throw=(-4.0, -34.0, -80), face="roar"),
          M(rods=0, ham=-60, lean=2.5, throw=(10.0, -32.0, -40), face="roar", sparks=[(14, -38, 1)]),
          M(rods=0, ham=-60, lean=1.5, sparks=[(18, -36, 2)]), M(rods=0, lean=0.5), M(rods=0), M(rods=0)]
    d0 = M(rods=1, hurt=True, lean=-2.0, ham=-120, hands=(4.0, -20.0))
    d1 = M(rods=1, hurt=True, lean=-4.0, squash=3.0, ham=-170, hands=(-3.0, -16.0))
    d2 = master_corpse(0)
    corpse = master_corpse(1)
    knock = M(rods=1, hurt=True, lean=-3.0, ham=-110, hands=(4.0, -19.0))
    idle0 = anims[0][1][0]
    anims += [("Swing", sw, [0.14, 0.14, 0.05, 0.08, 0.12, 0.12, 0.12]),
              ("Volley", vo, [0.1, 0.12, 0.12, 0.08, 0.06, 0.1, 0.12, 0.12, 0.1])]
    anims += tail_anims(idle0, [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return msheet("KrnForgemaster", anims, outdir)


def master_corpse(stage):
    r = Rig()
    r.ell(0.0, -3.4, 10.0, 3.4, "skin", 0.0, bias=0.05)
    r.poly([(-6.0, -5.0), (7.0, -5.0), (7.0, 0.0), (-6.0, 0.0)], "apron", 0.2, curve=0.5)
    r.ell(11.0, -3.0, 3.4, 3.0, "skin", 0.4, bias=0.1)
    r.tube([(-13.0, -1.0), (-6.0, -4.0)], [1.8, 1.6], "apron", -0.2)
    hammer(r, 15.0, -1.0, -10 if stage else -30, 9.0, 0.6, head=(6.5, 4.4))
    for i in range(2): r.tube([(-8.0 + i * 4, -6.0), (-4.0 + i * 4, -12.0 + stage)], [0.7, 0.6], "iron", -0.4, thin=True)
    if stage == 0: spark(r, 0.0, -10.0, 2)
    return r.resolve()


# ================================================================== WIRE WYVERN: copper wings, green hide, wire round neck and tail
def wyvern(hover=4.5, flap=0.0, neck=0.0, jaw=0.0, beam=None, fade=0.0, lean=0.0, tail=0.0, hurt=False, sparks=(), extra=None,
           head_at=None, wings=1.0):
    """neck: -1 drawn back .. 1 thrust forward; fade: 0..1 dissolving into a streak of light (Ride the Arc)."""
    r = Rig()
    by = -hover - 12.0
    if fade < 0.9: shadow(r, 0.0, 0.0, 6.0)
    mat = "wyv" if fade < 0.5 else "storm"
    # tail (behind): a long whip with a wire wrapped round it and a barbed tip
    tl = [(-6.0, by + 3.0), (-12.0, by + 5.0 + tail), (-17.0, by + 3.0 + tail * 1.5), (-20.0, by - 1.0 + tail * 2.0)]
    r.tube(tl, [2.2, 1.6, 1.1, 0.7], mat, -2.0, bias=-0.1, thin=True)
    for i in range(1, 3):
        x, y = lerp(tl[i][0], tl[i + 1][0], 0.5), lerp(tl[i][1], tl[i + 1][1], 0.5)
        r.dot(x, y, "copper", 3, -1.95); r.dot(x, y + 1, "copper", 1, -1.95)
    r.poly([(tl[-1][0], tl[-1][1] - 1.5), (tl[-1][0] - 3.0, tl[-1][1] - 0.5), (tl[-1][0], tl[-1][1] + 1.5)], "copper", -1.9)
    # far wing
    if fade < 0.8:
        bat_wing(r, -1.0, by - 3.0, -130 + flap, 75 * wings, 14.0, -3.0, mat="copper", near=False, fingers=4)
    # legs tucked under
    for k, dx in enumerate((-3.0, 2.0)):
        r.tube([(dx, by + 3.0), (dx + 1.5, by + 6.5), (dx + 3.0, by + 7.0)], [1.4, 1.0, 0.8], mat, -0.5 + k, bias=-0.3 + 0.3 * k, thin=True)
        r.dot(dx + 3.8, by + 7.2, "ivory", 2, -0.4 + k)
    # body
    P = r.part(False, 0.0)
    r.ell(lean, by, 7.5, 5.0, mat, 0.0, bias=0.05, part=P)
    r.tube([(lean - 4.0, by + 3.4), (lean + 5.0, by + 3.0)], [1.4, 1.4], "brass" if fade < 0.5 else "storm", 0.1, thin=True)  # belly plates
    # neck: an S rising to the head, copper wire coiled round it
    hx, hy = head_at if head_at else (12.0 + neck * 4.0 + lean, by - 9.0 + abs(neck) * 1.5)
    nk = [(lean + 5.0, by - 2.0), (lean + 8.0 + neck, by - 5.0), (hx - 2.5, hy + 1.5)]
    r.tube(nk, [3.0, 2.4, 2.0], mat, 0.6, bias=0.1)
    for t in (0.3, 0.55, 0.8):
        x, y = lerp(nk[0][0], nk[2][0], t), lerp(nk[0][1], nk[2][1], t)
        r.polyline([(x - 2.0, y + 0.6), (x + 1.5, y - 0.8)], "copper", 0.7, tone=3)
    # head: long jaw, swept horns, storm eye
    r.ell(hx, hy, 3.6, 2.6, mat, 1.0, bias=0.12)
    r.tube([(hx + 1.0, hy - 0.4), (hx + 5.5, hy + 0.2)], [1.8, 1.2], mat, 1.05, bias=0.1)
    r.tube([(hx + 0.5, hy + 1.6 + jaw * 0.8), (hx + 4.8, hy + 2.0 + jaw * 2.6)], [1.1, 0.8], mat, 0.95, bias=-0.2)
    if jaw > 0.3:
        r.dots([(hx + 2.5, hy + 1.4 + jaw), (hx + 4.0, hy + 1.6 + jaw * 1.6)], "ivory", 3, 1.1)
    r.tube([(hx - 1.5, hy - 1.5), (hx - 5.0, hy - 4.0), (hx - 7.0, hy - 3.5)], [0.9, 0.6, 0.3], "copper", 0.9, thin=True)
    r.dot(hx + 0.5, hy - 0.6, "storm", 2 if hurt else 4, 1.2)
    # near wing
    if fade < 0.8:
        bat_wing(r, 1.5, by - 3.5, -60 - flap, -75 * wings, 14.0, 0.3, mat="copper", near=True, fingers=4)
    if beam:
        bolt(r, (hx + 5.5, hy + 1.2), beam, z=6.0, n=5, amp=1.4, seed=int(beam[0]), fork=2)
    if fade > 0:
        for i in range(int(10 * fade)):
            a = i * 0.9
            spark(r, lean + 9 * math.cos(a), by + 5 * math.sin(a), 2 if i % 2 else 3)
        if fade > 0.8:
            bolt(r, (-12, by + 2), (16, by - 4), z=7.0, n=6, amp=2.0, seed=7, fork=2)
    for (x, y, k) in sparks: spark(r, x, y, k)
    if extra: extra(r)
    return r.resolve()


def wyvern_sheet(outdir):
    W = wyvern
    idle = [W(hover=4.5 + [0, 0.5, 1.0, 0.5][i], flap=[0, -8, -14, -8][i], tail=[0, 0.6, 1, 0.6][i]) for i in range(4)]
    run = [W(hover=5.0 + 0.8 * math.sin(i / 6 * math.tau), flap=[0, 30, 55, 30, 0, -15][i], neck=0.4, lean=1.0, tail=1.0) for i in range(6)]
    br = [W(neck=-0.6, jaw=0.3), W(neck=-1.0, jaw=0.6, flap=20, sparks=[(10, -26, 2)]), W(neck=-0.8, jaw=1.0, flap=35, sparks=[(13, -27, 1)]),
          W(neck=0.8, jaw=1.0, flap=-10, beam=(34.0, -18.0)), W(neck=0.9, jaw=1.0, flap=-5, beam=(36.0, -17.0)),
          W(neck=0.4, jaw=0.4, flap=10), W()]
    dv = [W(flap=40, neck=-0.5), W(flap=60, neck=-0.8, wings=0.7, sparks=[(0, -30, 2)]), W(flap=70, neck=-0.8, wings=0.5, fade=0.3),
          W(flap=70, wings=0.4, fade=0.6, hover=4.0), W(flap=70, wings=0.3, fade=0.95, hover=3.0), W(fade=1.0, hover=2.0, wings=0.2)]
    bu = [W(fade=0.9, hover=4.0, wings=0.4), W(fade=0.5, hover=5.0, neck=0.8, jaw=1.0, flap=-20),
          W(neck=1.0, jaw=0.2, flap=-30, sparks=[(22, -20, 1)]), W(neck=0.6, jaw=0.6, flap=0), W(neck=0.2, flap=20), W()]
    d0 = W(hurt=True, flap=-20, neck=-0.8, jaw=0.8)
    d1 = W(hurt=True, hover=3.0, flap=60, wings=0.6, neck=-0.5, jaw=1.0, sparks=[(2, -22, 1)])
    d2 = wyvern_corpse(0)
    corpse = wyvern_corpse(1)
    knock = W(hurt=True, flap=50, neck=-1.0, jaw=0.6)
    anims = [("Idle", idle, [0.12, 0.12, 0.12, 0.12]), ("Run", run, [0.08] * 6),
             ("Breath", br, [0.12, 0.12, 0.12, 0.06, 0.12, 0.12, 0.12]),
             ("Dive", dv, [0.1, 0.1, 0.08, 0.06, 0.06, 0.06]),
             ("Burst", bu, [0.05, 0.05, 0.08, 0.12, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return msheet("KrnWireWyvern", anims, outdir)


def wyvern_corpse(stage):
    r = Rig()
    bat_wing(r, -2.0, -5.0, -170, 40, 13.0, -0.5, mat="copper", near=False, fingers=4)
    r.ell(0.0, -4.0, 8.0, 4.0, "wyv", 0.0, bias=0.05)
    r.tube([(-7.0, -3.0), (-14.0, -1.5), (-19.0, -2.0)], [2.0, 1.2, 0.7], "wyv", -0.2)
    r.tube([(6.0, -4.0), (11.0, -3.0), (14.0, -2.0)], [2.6, 2.0, 1.8], "wyv", 0.3)
    r.ell(16.0, -2.0, 3.0, 2.2, "wyv", 0.5, bias=0.1)
    bat_wing(r, 2.0, -6.0, -40, -50, 12.0, 1.0, mat="copper", near=True, fingers=4)
    if stage == 0: spark(r, 2.0, -12.0, 2)
    return r.resolve()


# ================================================================== FUSE SAPPER: a gremlin too heavy to fly, a satchel of charges
def sapper(bob=0.0, lean=0.0, feet=((-3.5, 0.0), (3.5, 0.0)), hand=(10.0, -13.0), held=None, face="grin", flung=(), hurt=False,
           sparks=(), extra=None, wingflap=0.0, squash=0.0):
    """held: 'can' (a canister in the near hand) or 'charge'; flung: [(x, y)] charges in flight."""
    r = Rig()
    by = -11.0 + bob + squash
    tx = lean * 0.5
    # stubby folded wings (behind) that can't lift it any more
    bat_wing(r, tx - 3.0, by - 8.0, -140 + wingflap, 50, 7.5, -3.0, mat="ghide", near=False)
    for k, f in enumerate(feet):
        z = -1.0 if k == 0 else 1.5
        leg(r, (tx + (-3.0 if k == 0 else 3.0), by + 4.5), f, 3.4, 3.2, "ghide", z, rad=(2.0, 1.6), boot="ghide", boot_len=2.4,
            bias=-0.3 if k == 0 else 0.0)
    # fat body and the satchel of charges on its belly
    P = r.part(False, 0.0)
    r.ell(tx, by, 9.0, 8.4 - squash * 0.4, "ghide", 0.0, bias=0.05, part=P)
    r.poly([(tx - 5.0, by - 1.0), (tx + 6.5, by - 1.5), (tx + 7.0, by + 5.5), (tx - 4.5, by + 6.0)], "apron", 0.4, curve=0.6)
    r.polyline([(tx - 6.0, by - 6.0), (tx + 5.5, by - 1.0)], "apron", 0.45, tone=1)
    for i, x in enumerate((-3.0, 0.0, 3.0)):
        r.tube([(tx + x, by + 1.0), (tx + x, by - 2.5)], [1.2, 1.2], "copper", 0.5, bias=0.1, thin=True)
        r.ell(tx + x, by - 3.0, 1.3, 0.9, "magred", 0.55, bias=0.2, thin=True)
    # head: wide grin, ears down
    hx, hy = tx + 1.5 + lean, by - 11.5 + squash * 0.5
    r.ell(hx, hy, 5.6, 4.6, "ghide", 0.6, bias=0.12)
    r.poly([(hx - 3.0, hy - 1.0), (hx - 11.0, hy + 1.0), (hx - 3.5, hy + 1.5)], "ghide", 0.5, bias=-0.05)
    r.poly([(hx + 2.5, hy - 2.8), (hx + 8.0, hy - 6.0), (hx + 5.0, hy - 0.6)], "ghide", 0.7, bias=0.15)
    r.stamp(GREM_FACES["hurt" if hurt else face], hx + 0.4, hy - 0.6, 0.9, GREM_FACE, pivot=(1, 0))
    r.tube([(hx - 2.0, hy - 3.6), (hx + 3.0, hy - 4.0)], [0.9, 0.9], "dkiron", 0.95, thin=True)      # goggles strap
    r.ell(hx + 2.5, hy - 3.8, 1.2, 1.1, "brass", 1.0, bias=0.2, thin=True)
    # far arm, near arm with whatever it holds
    r.tube([(tx - 7.0, by - 3.0), (tx - 10.5, by + 2.0)], [1.8, 1.5], "ghide", -0.5, bias=-0.3, thin=True)
    r.tube([(tx + 6.0, by - 3.5), (lerp(tx + 6.0, hand[0], 0.5) + 1.0, lerp(by - 3.5, hand[1], 0.5) + 1.0), hand], [1.8, 1.5, 1.3], "ghide", 2.4,
           thin=True)
    r.ell(hand[0], hand[1], 1.4, 1.3, "ghide", 2.5, bias=0.2, thin=True)
    if held == "can":
        r.tube([(hand[0], hand[1] + 1.5), (hand[0], hand[1] - 3.5)], [1.8, 1.8], "copper", 2.3, bias=0.1, thin=True)
        r.ell(hand[0], hand[1] - 4.0, 1.8, 0.8, "magred", 2.35, thin=True)
        r.dot(hand[0], hand[1] - 5.2, "ember", 4, 2.4)
    elif held == "charge":
        r.ell(hand[0], hand[1] - 1.5, 1.4, 1.4, "copper", 2.3, bias=0.1, thin=True); r.dot(hand[0], hand[1] - 3.0, "magred", 3, 2.4)
    for (x, y) in flung:
        r.ell(x, y, 1.3, 1.3, "copper", 6.0, bias=0.1); r.dot(x, y - 1.5, "magred", 3, 6.1)
    for (x, y, k) in sparks: spark(r, x, y, k, mat="ember" if k == 1 else "storm")
    if extra: extra(r)
    return r.resolve()


def sapper_sheet(outdir):
    Sp = sapper
    idle = [Sp(bob=[0, 0.5, 1.0, 0.5][i], hand=(10.0, -13.0 + [0, 0.5, 1, 0.5][i]), wingflap=[0, 6, 10, 6][i]) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        f1 = (3.0 * math.cos(ph), -max(0.0, 1.6 * math.sin(ph)))
        f2 = (-3.0 * math.cos(ph), -max(0.0, -1.6 * math.sin(ph)))
        run.append(Sp(lean=1.0 + 0.8 * math.sin(ph), bob=-0.8 * abs(math.sin(ph)), feet=(f2, f1), hand=(7.5, -11.0), wingflap=20 * math.sin(ph)))
    lb = [Sp(hand=(7.0, -10.0), held="can"), Sp(hand=(2.0, -22.0), held="can", lean=-1.5, face="shout"),
          Sp(hand=(-1.0, -24.0), held="can", lean=-2.5, face="shout", sparks=[(-1, -30, 3)]),
          Sp(hand=(9.0, -20.0), lean=2.0, face="shout", flung=[(13.0, -26.0)], sparks=[(13, -29, 2)]),
          Sp(hand=(10.0, -14.0), lean=1.5), Sp()]
    ly = [Sp(hand=(4.0, -7.0)), Sp(hand=(3.0, -7.5), held="charge", lean=-0.5), Sp(hand=(-2.0, -14.0), held="charge", lean=-1.5, face="shout"),
          Sp(hand=(-3.0, -16.0), held="charge", lean=-2.0, face="shout"),
          Sp(hand=(10.0, -12.0), lean=2.0, face="shout", flung=[(14.0, -18.0), (16.0, -14.0), (12.0, -22.0)]),
          Sp(hand=(10.0, -11.0), lean=1.5, flung=[(20.0, -16.0), (22.0, -10.0), (17.0, -22.0)]),
          Sp(hand=(8.0, -11.0), lean=0.5), Sp()]
    d0 = Sp(hurt=True, lean=-2.0, hand=(5.0, -16.0))
    d1 = Sp(hurt=True, lean=-4.0, squash=3.0, hand=(3.0, -8.0), sparks=[(0, -18, 1)])
    d2 = sapper_corpse(0)
    corpse = sapper_corpse(1)
    knock = Sp(hurt=True, lean=-3.0, hand=(4.0, -15.0))
    anims = [("Idle", idle, [0.16, 0.12, 0.16, 0.12]), ("Run", run, [0.08] * 6),
             ("Lob", lb, [0.12, 0.12, 0.12, 0.06, 0.12, 0.12]),
             ("Lay", ly, [0.1, 0.1, 0.12, 0.1, 0.06, 0.1, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return msheet("KrnFuseSapper", anims, outdir)


def sapper_corpse(stage):
    r = Rig()
    r.ell(0.0, -4.4, 8.0, 4.4, "ghide", 0.0, bias=0.05)
    r.ell(9.0, -3.4, 4.4, 3.4, "ghide", 0.4, bias=0.1)
    r.poly([(-4.0, -6.0), (5.0, -6.0), (5.0, -1.0), (-4.0, -1.0)], "apron", 0.3)
    for i, x in enumerate((-6.0, 12.0)):
        r.ell(x + stage, -1.2, 1.3, 1.3, "copper", 0.5); r.dot(x + stage, -2.6, "magred", 3, 0.55)
    r.dots([(9, -4), (11, -4)], "ghide", 0, 0.6)
    if stage == 0: ember = spark(r, 2.0, -11.0, 1, mat="ember")
    return r.resolve()


# ================================================================== THUNDER BULL: a storm bull, plated in copper and riveted iron
def bull_leg(r, root, foot, l1, l2, z, fore, bias=0.0, lift=0.0):
    """One leg: a thick upper (thigh or forearm) and a slim lower bending the way a bull's does (knee forward on the fore
    legs, hock back on the hind), a dark iron-shod hoof."""
    kx, ky = ik(root[0], root[1], foot[0], foot[1] - 1.2, l1, l2, 1 if fore else -1)
    r.tube([root, (kx, ky)], [3.0 if not fore else 2.6, 1.7], "bull", z, bias=bias, thin=True)
    r.tube([(kx, ky), (foot[0], foot[1] - 1.2)], [1.7, 1.3], "bull", z + 0.01, bias=bias - 0.05, thin=True)
    r.poly([(foot[0] - 1.6, foot[1] - 2.0), (foot[0] + 2.2, foot[1] - 2.0), (foot[0] + 2.6, foot[1]), (foot[0] - 1.6, foot[1])], "dkiron", z + 0.02,
           bias=bias + 0.1)
    r.dot(foot[0] + 0.5, foot[1] - 2.2, "copper", 3 if bias >= 0 else 1, z + 0.03)


def bull(phase=None, bob=0.0, lean=0.0, head=(14.0, -13.0), head_ang=0.0, crouch=0.0, paw=None, charge=False, stuck=0, hurt=False,
         sparks=(), extra=None, gallop=False, k=0):
    """head_ang: + tips the horns down (hook / charge); paw: the near fore hoof lifted 0..1; stuck: horns in a wall
    (quiver phase); phase: gallop angle (None = standing)."""
    r = Rig()
    hip = (-9.0, -17.0 + crouch * 0.5 - bob + lean * 0.4)
    sh = (4.0, -19.0 + crouch - bob - lean * 0.6)
    # legs: far pair behind the body, near pair in front (rotary gallop: hind then fore)
    for far in (True, False):
        z = -2.0 if far else 2.0
        bias = -0.35 if far else 0.0
        for fore in (False, True):
            root = (sh[0] - 1.0, sh[1] + 4.0) if fore else (hip[0] + 1.0, hip[1] + 3.0)
            if phase is None:
                fx = root[0] + (1.5 if fore else -1.5) + (1.2 if far else 0.0)
                fy = 0.0
                if fore and not far and paw is not None:
                    fx, fy = root[0] + 1.0 + paw * 1.5, -8.0 * paw
            else:
                a = phase + (math.pi if fore else 0.0) + (0.5 if far else 0.0)
                fx = root[0] + 5.0 * math.cos(a) + (1.0 if fore else -1.0)
                fy = -max(0.0, 3.6 * math.sin(a))
            bull_leg(r, root, (fx, fy), 8.0 if fore else 8.5, 8.0, z, fore, bias)
    # tail with a crackling tuft
    tl = [(hip[0] - 4.0, hip[1] - 2.0), (hip[0] - 5.5, hip[1] + 2.0 + bob), (hip[0] - 5.5, hip[1] + 8.0 + bob)]
    r.tube(tl, [1.0, 0.7, 0.6], "bull", -1.0, bias=-0.1, thin=True)
    r.ell(tl[-1][0], tl[-1][1] + 1.0, 1.2, 1.6, "dkiron", -0.9, thin=True)
    r.dot(tl[-1][0], tl[-1][1] + 2.0, "storm", 3 + (k % 2), -0.8)
    # body: haunch to a deep chest under a huge humped neck
    P = r.part(False, 0.0)
    r.tube([hip, sh], [6.4, 8.6], "bull", 0.0, bias=0.05, part=P)
    r.ell(hip[0] - 0.5, hip[1] - 0.5, 6.8, 6.6, "bull", 0.0, bias=0.1, part=P)
    # riveted iron flank plate and the copper hump plate with its crest of sparks
    fl = [(hip[0] + 1.0, hip[1] - 5.0), (sh[0] - 2.0, sh[1] - 6.0), (sh[0] - 1.0, sh[1] + 4.5), (hip[0] + 2.0, hip[1] + 5.0)]
    r.poly(fl, "iron", 0.3, normal=(-0.2, -0.3, 1.0), curve=0.6)
    for t in (0.15, 0.4, 0.65, 0.9):
        r.dot(lerp(fl[0][0], fl[1][0], t), lerp(fl[0][1], fl[1][1], t) + 1.0, "brass", 4, 0.35)
        r.dot(lerp(fl[3][0], fl[2][0], t), lerp(fl[3][1], fl[2][1], t) - 1.0, "brass", 2, 0.35)
    hx0, hy0 = sh[0] - 1.5, sh[1] - 7.0
    r.ell(hx0, hy0, 8.5, 6.0, "bull", 0.0, bias=0.15, part=P)
    # copper bands strapped over the hump, a brass rivet on each
    for i in range(3):
        x = hx0 - 4.5 + i * 4.0
        top = hy0 - 4.2 + abs(i - 1) * 0.9
        r.tube([(x - 0.5, top), (x + 1.0, hy0 + 2.0), (x + 1.5, hy0 + 6.0)], [1.2, 1.2, 1.0], "copper", 0.5, bias=0.15, thin=True)
        r.dot(x, top + 1.0, "brass", 4, 0.56)
    for i in range(4):
        crackle(r, hx0 - 6 + i * 4, hy0 - 7.0 - (i % 2), i + k + (2 if charge else 0), seed=i)
    # neck and head, low and heavy
    hx, hy = head[0] + lean, head[1] + crouch
    a = math.radians(head_ang)
    ca, sa = math.cos(a), math.sin(a)
    T = lambda u, v: (hx + u * ca - v * sa, hy + u * sa + v * ca)
    r.tube([(sh[0] + 2.0, sh[1] - 3.0), T(-2.5, 0.0)], [6.0, 4.4], "bull", 0.8, bias=0.05)
    for t in (0.35, 0.7):
        x, y = lerp(sh[0] + 2.0, T(-2.5, 0.0)[0], t), lerp(sh[1] - 3.0, T(-2.5, 0.0)[1], t)
        r.polyline([(x - 1.0, y - 4.5), (x + 1.0, y + 4.0)], "copper", 0.85, tone=3)
    r.ell(hx, hy, 5.6, 5.0, "bull", 1.0, bias=0.12, ang=head_ang)
    r.tube([T(1.5, 1.2), T(5.2, 3.2)], [3.0, 2.4], "bull", 1.05, bias=0.1)            # muzzle
    r.dot(*T(6.0, 3.0), "dkiron", 0, 1.1); r.dot(*T(5.6, 4.0), "dkiron", 0, 1.1)
    r.ell(*T(4.0, 5.0), 1.2, 1.2, "brass", 1.15, thin=True)                           # nose ring
    r.poly([T(-1.0, -3.6), T(1.6, -3.4), T(1.2, -1.6), T(-1.4, -1.8)], "iron", 1.08, normal=(-0.3, -0.6, 0.8))   # brow plate
    r.dot(*T(0.2, -2.6), "brass", 4, 1.09)
    r.dot(*T(1.8, -0.6), "storm", 2 if hurt else 4, 1.2); r.dot(*T(2.8, -0.6), "storm", 2 if hurt else 3, 1.2)
    # horns: wide, sweeping out and up, then forward to copper points that crackle
    q = 0.5 if stuck % 2 else 0.0
    far_h = [T(-1.5, -3.8), T(-4.5, -6.5), T(-5.0, -10.5), T(-3.0, -13.0 + q)]
    near_h = [T(1.0, -4.0), T(4.5, -6.5), T(5.5, -10.5), T(3.5, -13.5 + q)]
    r.tube(far_h, [2.0, 1.5, 1.0, 0.5], "copper", 0.6, bias=-0.25, thin=True)
    r.tube(near_h, [2.4, 1.8, 1.1, 0.5], "copper", 1.4, bias=0.1, thin=True)
    r.dot(*far_h[-1], "brass", 3, 0.65); r.dot(*near_h[-1], "brass", 4, 1.45)
    for i, tip in enumerate((far_h[-1], near_h[-1])):
        if (k + i) % 2 == 0 or charge: spark(r, tip[0] + 1, tip[1] - 1, 2 if not charge else 1)
        else: r.dot(tip[0] + 1, tip[1] - 1, "storm", 3, 9.0)
    r.poly([T(-2.0, -1.0), T(-6.0, -1.5), T(-2.5, 1.0)], "bull", 0.95, bias=-0.05)    # ear
    if charge:
        for i in range(3): r.dot(hip[0] - 6 - i * 3, hip[1] + 4 + i, "storm", 3 - (i > 1), -1.0)
    if stuck:
        for i in range(3):
            a2 = stuck * 0.9 + i * 2.1
            spark(r, hx - 2 + 3 * math.cos(a2), hy - 13 + 1.2 * math.sin(a2), 3, mat="brass")
    for (x, y, kk) in sparks: spark(r, x, y, kk)
    if extra: extra(r)
    return r.resolve()


def bull_sheet(outdir):
    B = bull
    idle = [B(bob=[0, 0.4, 0.8, 0.4][i], head=(17.0, -13.0 + [0, 0.4, 0.8, 0.4][i]), k=i) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        run.append(B(phase=ph, bob=1.2 * math.sin(ph) - 0.6, lean=1.5 * math.sin(ph + 0.8), head=(18.0, -12.5 - 1.0 * math.sin(ph)), k=i))
    hk = [B(head_ang=20, head=(13.0, -11.0), crouch=1.0), B(head_ang=35, head=(12.0, -9.0), crouch=2.0, k=1),
          B(head_ang=-35, head=(15.0, -16.0), lean=2.0, sparks=[(26, -30, 1)], k=2), B(head_ang=-45, head=(15.0, -17.0), lean=2.0, sparks=[(28, -31, 2)]),
          B(head_ang=-10, head=(14.0, -14.0), lean=1.0, k=1), B(head_ang=5, head=(14.0, -13.0)), B()]
    pw = []
    for j in range(3):
        pw += [B(paw=0.7, head_ang=-5, head=(14.0, -14.0), k=j), B(paw=1.0, head_ang=-5, head=(14.0, -14.5), k=j + 1),
               B(paw=0.0, head_ang=20, head=(13.0, -11.0), crouch=0.5, sparks=[(10, -1, 1), (7, 0, 2)],
                 extra=lambda r: dust_puff(r, 9.0, 0.0, 0, 1.0))]
    ch = [B(phase=i / 4 * math.tau, charge=True, head_ang=30, head=(16.0, -10.0), lean=2.0, crouch=1.0, bob=1.0 * math.sin(i / 4 * math.tau), k=i)
          for i in range(4)]
    st = [B(stuck=i + 1, head_ang=35, head=(16.0, -9.0), lean=2.5, crouch=2.0, bob=0.3 * (i % 2), k=i) for i in range(6)]
    d0 = B(hurt=True, head_ang=-20, head=(13.0, -15.0), lean=-2.0)
    d1 = B(hurt=True, head_ang=30, head=(12.0, -7.0), crouch=6.0)
    d2 = bull_corpse(0)
    corpse = bull_corpse(1)
    knock = B(hurt=True, head_ang=-25, head=(12.0, -15.0), lean=-3.0)
    anims = [("Idle", idle, [0.18, 0.14, 0.18, 0.14]), ("Run", run, [0.07] * 6),
             ("Hook", hk, [0.12, 0.12, 0.05, 0.1, 0.12, 0.12, 0.12]),
             ("Paw", pw, [0.1, 0.08, 0.12] * 3),
             ("Charge", ch, [0.06] * 4), ("Stuck", st, [0.08] * 6)]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return msheet("KrnThunderBull", anims, outdir)


def bull_corpse(stage):
    r = Rig()
    r.tube([(-12.0, -5.0), (8.0, -6.0)], [5.4, 6.4], "bull", 0.0, bias=0.05)
    r.ell(2.0, -9.5, 7.0, 3.5, "copper", 0.2, bias=0.1)
    r.poly([(-9.0, -4.0), (4.0, -4.0), (4.0, -1.0), (-9.0, -1.0)], "iron", 0.3)
    r.ell(15.0, -4.0, 4.4, 3.6, "bull", 0.5, bias=0.1)
    r.tube([(15.0, -7.0), (19.0, -11.0), (23.0, -10.0 + stage)], [1.8, 1.0, 0.5], "copper", 0.6)
    for i in range(4):
        r.tube([(-8.0 + i * 5.0, -9.0), (-7.0 + i * 5.0, -14.0 + stage)], [1.8, 1.4], "bull", 0.3 - i * 0.05, thin=True)
    if stage == 0: spark(r, 0.0, -15.0, 1)
    return r.resolve()


# ================================================================== POLARITY WARG: iron mane on end, half red, half blue
def warg(phase=None, bob=0.0, lean=0.0, head=(14.5, -16.0), jaw=0.0, crouch=0.0, stretch=0.0, gather=0.0, flare=0.0, field=0, hurt=False,
         sparks=(), extra=None):
    """flare: 0..1 the mane spikes stand straighter and glow (Magnetize); field: 1..3 field lines out of the mane."""
    r = Rig()
    tail = [(-10.0, -14.0 + crouch + bob), (-14.0, -16.0 + bob), (-17.5, -14.5 + bob)]
    hip, sh = quad(r, L=17.0, H=14.0 - bob, rb=(4.8, 6.4), mat="fur", phase=phase, crouch=crouch, lean=lean, legs=(6.4, 6.0),
                   leg_r=(1.8, 1.2), stretch=stretch, gather=gather, tail=tail)
    hx, hy = head[0] + lean, head[1] + crouch + bob
    r.tube([(sh[0] - 1.0, sh[1] - 1.0), (hx - 2.0, hy + 0.5)], [4.0, 3.0], "fur", 0.6, bias=0.05)
    r.ell(hx, hy, 3.8, 3.2, "fur", 1.0, bias=0.12)
    r.tube([(hx + 1.5, hy - 0.2), (hx + 7.5, hy + 0.8)], [2.0, 1.1], "fur", 1.1, bias=0.1)
    r.tube([(hx + 1.5, hy + 1.4 + jaw * 0.6), (hx + 6.5, hy + 2.0 + jaw * 2.8)], [1.2, 0.7], "fur", 0.95, bias=-0.2)
    if jaw > 0.3: r.dots([(hx + 3.5, hy + 1.2 + jaw), (hx + 5.5, hy + 1.4 + jaw * 1.8), (hx + 4.5, hy + 0.8)], "ivory", 3, 1.15)
    r.dot(hx + 8.0, hy + 0.6, "dkiron", 0, 1.2)
    r.dot(hx + 0.8, hy - 1.0, "storm", 2 if hurt else 4, 1.2); r.dot(hx + 1.8, hy - 1.0, "storm", 2, 1.2)
    r.poly([(hx - 1.0, hy - 1.8), (hx - 2.5, hy - 7.0), (hx + 1.0, hy - 2.2)], "fur", 1.05, bias=0.1)
    # the mane: a crest of iron spikes from the skull down the back, red toward the head, blue toward the tail
    n = 11
    for i in range(n):
        t = i / (n - 1.0)
        x = lerp(hx - 2.5, hip[0] + 3.0, t)
        y = lerp(hy - 2.5, hip[1] - 3.0, t) - 2.0 * math.sin(t * math.pi)
        h = (4.5 + 2.5 * math.sin(t * math.pi) + 0.8 * (i % 2)) * (1.0 + 0.35 * flare)
        col = "magred" if t < 0.5 else "magblu"
        lean_s = -1.6 * (1.0 - flare)
        r.tube([(x, y + 1.0), (x + lean_s, y - h)], [1.1, 0.3], col, 0.7 - t * 0.3, bias=0.15, thin=True)
        if flare > 0.5 and i % 2 == 0: r.dot(x + lean_s, y - h - 1, "storm", 4, 0.8)
    if field:
        for k in range(field):
            R = 6.0 + k * 4.0
            for i in range(14):
                a = i / 14.0 * math.pi
                x = hx - 9.0 + R * 1.5 * math.cos(a)
                y = hy - 6.0 - R * 0.7 * math.sin(a)
                r.dot(x, y, "magred" if math.cos(a) > 0 else "magblu", 3 if k == 0 else 2, 6.0)
    for (x, y, k) in sparks: spark(r, x, y, k)
    if extra: extra(r)
    return r.resolve()


def warg_sheet(outdir):
    Wg = warg
    idle = [Wg(bob=[0, 0.4, 0.8, 0.4][i], flare=[0, 0.1, 0.2, 0.1][i]) for i in range(4)]
    run = [Wg(phase=i / 6 * math.tau, bob=-0.8 * abs(math.sin(i / 6 * math.tau)), head=(15.5, -15.0), lean=1.0) for i in range(6)]
    bt = [Wg(crouch=1.0, gather=1.5, head=(13.5, -14.0)), Wg(crouch=1.5, gather=2.0, head=(12.5, -13.5), jaw=0.6),
          Wg(stretch=1.5, head=(17.5, -16.0), jaw=0.0, sparks=[(26, -13, 2)]), Wg(crouch=1.0, head=(15.5, -15.0), jaw=0.8),
          Wg(crouch=2.0, gather=2.0, head=(13.5, -13.0), jaw=1.0),
          Wg(stretch=3.0, lean=2.5, head=(19.5, -16.0), jaw=0.0, sparks=[(30, -13, 1)]), Wg(lean=1.0, head=(16.5, -16.0), jaw=0.3), Wg()]
    mg = [Wg(flare=0.2), Wg(flare=0.5, crouch=1.0, head=(13.5, -14.0)), Wg(flare=0.9, crouch=1.5, head=(13.5, -14.0), jaw=0.6, field=1),
          Wg(flare=1.0, head=(14.5, -18.0), jaw=1.0, field=2, sparks=[(6, -28, 1)]), Wg(flare=1.0, head=(14.5, -18.0), jaw=1.0, field=3),
          Wg(flare=0.8, head=(14.5, -17.0), jaw=0.6, field=2), Wg(flare=0.5, field=1), Wg()]
    d0 = Wg(hurt=True, crouch=1.0, head=(13.5, -14.0), jaw=0.8)
    d1 = Wg(hurt=True, crouch=4.0, head=(12.5, -10.0), jaw=1.0)
    d2 = warg_corpse(0)
    corpse = warg_corpse(1)
    knock = Wg(hurt=True, lean=-2.5, head=(12.5, -17.0), jaw=0.7)
    anims = [("Idle", idle, [0.16, 0.12, 0.16, 0.12]), ("Run", run, [0.06] * 6),
             ("Bites", bt, [0.1, 0.1, 0.05, 0.08, 0.08, 0.05, 0.1, 0.12]),
             ("Magnetize", mg, [0.12, 0.12, 0.1, 0.06, 0.12, 0.12, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return msheet("KrnPolarityWarg", anims, outdir)


def warg_corpse(stage):
    r = Rig()
    r.tube([(-11.0, -3.6), (9.0, -4.0)], [3.6, 4.4], "fur", 0.0, bias=0.05)
    r.ell(14.0, -3.0, 3.4, 2.8, "fur", 0.5, bias=0.1)
    r.tube([(15.0, -2.4), (20.0, -1.6)], [1.6, 1.0], "fur", 0.6)
    for i in range(8):
        t = i / 7.0
        x = lerp(10.0, -9.0, t)
        r.tube([(x, -7.0), (x - 1.0, -10.0 + stage + (i % 2))], [0.9, 0.3], "magred" if t < 0.5 else "magblu", 0.3, thin=True)
    if stage == 0: spark(r, 0.0, -12.0, 2)
    return r.resolve()


SYNC = {
    "KrnForgeColossus": {"Slam": [("HIT: both fists on the floor at (17, -1); quake 48 x 18 there", 4)],
                         "Fence": [("both fists pound the floor at x = +-17: the four rods burst up", 5)],
                         "Vent": [("the chimney whistles (white-hot)", 0), ("BLAST: steam 30 px round the feet", 3), ("cooled", 4)]},
    "KrnForgemaster": {"Swing": [("HIT: sledge head on the floor at (23, -1)", 3)],
                       "Volley": [("reaches into the quiver", 1), ("THROW: the rods leave the hand at (10, -32)", 4)]},
    "KrnWireWyvern": {"Breath": [("beam leaves the mouth at (19, -24)", 3)],
                      "Dive": [("the route lights (plan)", 0), ("gone: it rides the arcs (hide the body)", 5)],
                      "Burst": [("BITE: jaws at (22, -20)", 2)]},
    "KrnFuseSapper": {"Lob": [("canister leaves the hand at (13, -26)", 3)], "Lay": [("three charges scatter from (14, -18)", 4)]},
    "KrnThunderBull": {"Hook": [("HOOK: horn tips at (22, -24); box at (20, -16)", 2)],
                       "Paw": [("hoof strike 1: a stud drops", 1), ("hoof strike 2", 4), ("hoof strike 3", 7)]},
    "KrnPolarityWarg": {"Bites": [("first bite: jaws at (24, -14)", 2), ("lunge bite: jaws at (28, -14)", 5)],
                        "Magnetize": [("the field opens", 3)]},
}
NOTES = {
    "KrnForgeColossus": "Idle/Run: furnace dull; IdleH1/RunH1: orange (heat 1); IdleH2/RunH2: yellow (heat 2); IdleCold/RunCold: "
                        "after the vent (dark grille, steam wisps). Vent starts white-hot (heat 3).",
    "KrnForgemaster": "Idle/Run: empty quiver; IdleR1..R3 / RunR1..R3: 1-3 rods carried.",
    "KrnThunderBull": "Charge (loop) is played while it runs at the hero; Stuck (loop) while its horns are in a wall.",
}
JOBS = [("KrnForgeColossus", colossus_sheet), ("KrnForgemaster", master_sheet), ("KrnWireWyvern", wyvern_sheet),
        ("KrnFuseSapper", sapper_sheet), ("KrnThunderBull", bull_sheet), ("KrnPolarityWarg", warg_sheet)]
