"""Ossivar tier 3, second half: Cerberus, Church Grim, Carrion Saint, The Ossuary, Marrow Wyrm, Carrion Roc. Built through
ossivar_v2_rigs.py. T3 idle limit 42 x 40."""
import math
from ossivar_v2_rigs import (Rig, Xf, chain, ik, lerp, skullp, lbone, skeleton, vertebrae, bone, heap, bone_bits, dust, smear,
                             arc_pts, sheet, tail_anims, SYNC, NOTES, BONE_LEG, dog_body, gait, wing, J)
from ossivar_v2_t2 import boar_body, BARG_HEADS, BARG_LEG, VULT_HEAD, VULT_LEG


# ================================================================== CERBERUS (T3): three skulls on one iron collar, grave fire in the ribs
DOG_SKULL = {
    "shut": """
.LHL.....
LHHLLHL..
LkeLLLHHL
SBBLLLLLHL
.SBBTtTtS.
""",
    "open": """
.LHL.....
LHHLLHL..
LkeLLLHHL
SBBLLLLLHL
.SBTtT....
..S...tT..
...SBBBS..
""",
}
FIRE_LEG = dict(BONE_LEG, e=("gfire", 3), E=("gfire", 4))


def cerb(lean=0.0, bob=0.0, legs=None, heads=None, glow=(0, 0, 0), extra=None, smear_pts=None, dust_at=None, crouch=0.0,
         stretch=0.0, fire=0):
    """heads: three (x, y, face) points (back, middle, front head) for the backs of the jaws. glow: per head 0/1 (lit throat)."""
    r = Rig()
    legs = legs or ((-8.0, 0.0), (6.0, 0.0), (-7.0, 0.0), (7.0, 0.0))
    T = Xf(lean, (0.0, -11.0))
    hip = T(-8.0 - stretch * 0.5, -11.0 + bob + crouch)
    sh = T(5.0 + stretch * 0.5, -12.0 + bob + crouch * 0.6)
    # grave fire burning inside the ribcage (drawn first, the ribs over it)
    cx, cy = (hip[0] + sh[0]) / 2 + 1.0, (hip[1] + sh[1]) / 2 + 1.5
    r.ell(cx, cy, 6.0, 3.4, "gfire", -0.3, flat=1)
    r.ell(cx + 1.0, cy - 0.5 - fire * 0.5, 2.6, 1.6, "gfire", -0.25, flat=2)
    r.ell(cx + 1.5, cy - 0.5 - fire * 0.5, 1.2, 0.8, "gfire", -0.24, flat=3)
    r.dot(cx + 1.0 + (fire % 2), cy - 3.0 - fire, "gfire", 4, -0.2)
    boar_body(r, hip, sh, legs, chest=6.0, ribs=6, dirt=False, leg_len=(5.4, 5.2), fleg_len=(5.4, 5.8), seed=13, leg_rad=1.4)
    heads = heads or [(sh[0] + 1.0, sh[1] - 6.0, "shut"), (sh[0] + 4.0, sh[1] - 2.5, "shut"), (sh[0] + 3.0, sh[1] + 1.5, "shut")]
    # iron collar
    r.ell(sh[0] + 1.5, sh[1] - 2.0, 2.6, 3.4, "iron", 1.5, bias=0.1)
    for i in range(3): r.dot(sh[0] + 2.5, sh[1] - 4.0 + 2 * i, "iron", 4, 1.51)
    for k, (hx, hy, face) in enumerate(heads):
        z = 1.0 + k * 0.6
        vertebrae(r, [(sh[0] + 1.5, sh[1] - 2.0), (hx - 0.5, hy - 1.5)], z - 0.1, "bone" if k else "dbone", tone_a=3, tone_b=1)
        leg = dict(FIRE_LEG)
        if k == 0: leg.update({c: ("dbone", t) for c, t in (("H", 3), ("L", 2), ("B", 2), ("S", 1))})
        r.stamp(DOG_SKULL[face], hx, hy, z, leg, pivot=(1, 3))
        if glow[k]:
            r.dot(hx + 6, hy - 1, "gfire", 4, z + 0.1); r.dot(hx + 5, hy, "gfire", 3, z + 0.1); r.dot(hx + 7, hy - 2, "gfire", 3, z + 0.1)
    if smear_pts: smear(r, smear_pts, "bone", 4)
    if dust_at: dust(r, *dust_at)
    if extra: extra(r)
    return r.resolve()


CL = ((-8.0, 0.0), (6.0, 0.0), (-7.0, 0.0), (7.0, 0.0))


def hs(dx=0.0, dy=0.0, faces=("shut", "shut", "shut"), spread=1.0):
    """The three head points relative to the default shoulder (5, -12)."""
    base = [(6.0, -18.0), (9.0, -14.5), (8.0, -10.5)]
    return [(base[i][0] + dx, -12.0 + (base[i][1] + 12.0) * spread + dy, faces[i]) for i in range(3)]


def cerb_sheet(outdir):
    C = cerb
    idle = [C(bob=[0, 0.3, 0.6, 0.3][i], fire=i, heads=hs(0, [0, 0.3, 0.6, 0.3][i], faces=[("shut", "shut", "open"), ("open", "shut", "shut"),
                                                                                             ("shut", "open", "shut"), ("shut", "shut", "shut")][i]))
            for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        b = -0.8 * abs(math.sin(ph))
        run.append(C(lean=-3 * math.sin(ph), bob=b, legs=gait(i, 6, 3.4, 2.0, gallop=True, base=CL), fire=i, stretch=0.8 * math.cos(ph),
                     heads=hs(1.0, b, faces=("open", "open", "open"))))
    # Bite (6): heads pull back (0-1), wide (2), ALL THREE SNAP on one frame (3: fan, jaws at (20, -16 / -12 / -7)), hold, settle
    bite = [C(heads=hs(-1.0, 0.0), crouch=0.6), C(heads=hs(-2.0, -1.0, ("open",) * 3, 1.2), crouch=1.0),
            C(heads=hs(1.0, -1.0, ("open",) * 3, 1.3), lean=-4),
            C(heads=hs(5.0, 0.0, ("shut",) * 3, 1.4), lean=8, legs=((-7.0, 0.0), (8.0, 0.0), (-6.0, 0.0), (9.0, 0.0)),
              smear_pts=[(12, -22), (17, -20), (21, -16)], extra=lambda r: smear(r, [(14, -10), (18, -9), (22, -7)], "bone", 4)),
            C(heads=hs(4.0, 0.0), lean=6), C()]
    # Breath (10): the outer heads glow (0-1, the tell), outer heads breathe (2), the middle joins (3), the cones sweep in (4-8),
    # the flames gutter (9)
    br = [C(heads=hs(0.0, 0.0, ("shut", "shut", "shut"), 1.3), glow=(1, 0, 1)),
          C(heads=hs(0.0, -0.5, ("open", "shut", "open"), 1.35), glow=(1, 0, 1), crouch=0.6),
          C(heads=hs(1.0, -0.5, ("open", "shut", "open"), 1.4), glow=(1, 0, 1), crouch=0.8, fire=1),
          C(heads=hs(1.0, -0.5, ("open", "open", "open"), 1.35), glow=(1, 1, 1), crouch=0.8, fire=2)]
    for i in range(5):
        sp = 1.3 - 0.07 * i
        br.append(C(heads=hs(1.0 + 0.3 * i, -0.5, ("open", "open", "open"), sp), glow=(1, 1, 1), crouch=0.8, fire=i % 3))
    br.append(C(heads=hs(0.0, 0.0), fire=0))
    d0 = C(lean=-14, heads=hs(-1.0, -2.0, ("open",) * 3, 1.3))
    d1 = C(lean=-24, bob=3.0, crouch=3.0, heads=hs(-2.0, 4.0, ("open",) * 3, 0.8), legs=((-9.0, 0.0), (4.0, 0.0), (-8.0, 0.0), (6.0, -1.0)))
    d2 = cerb_corpse(0); corpse = cerb_corpse(1)
    knock = C(lean=-14, heads=hs(-2.0, -1.0, ("open",) * 3), legs=((-9.0, 0.0), (4.0, 0.0), (-8.0, 0.0), (5.0, 0.0)))
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.07] * 6),
             ("Bite", bite, [0.1, 0.1, 0.06, 0.06, 0.1, 0.12]),
             ("Breath", br, [0.14, 0.14, 0.12, 0.12, 0.16, 0.16, 0.16, 0.16, 0.16, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("OssCerberus", anims, outdir)


def cerb_corpse(stage):
    r = Rig()
    heap(r, -2.0, 0, 20.0 if stage else 16.0, 18, seed=101, h=0.8 if stage else 1.6)
    r.ell(6.0, -2.0, 2.0, 1.4, "iron", 0.6)
    for k, (x, y) in enumerate(((6.0, -1.0), (10.0, 0.0), (3.0, 0.0))):
        r.stamp(DOG_SKULL["open"], x, y if stage else y - 1, 1.0 + k * 0.1, dict(FIRE_LEG, e=("iron", 0)), pivot=(1, 3))
    if not stage:
        r.dot(-2, -3, "gfire", 3, 2.0); dust(r, 0, 0, 1, 2.0)
    return r.resolve()


SYNC["OssCerberus"] = {"Bite": [("SNAP: all three jaws on one frame (20, -16 / -12 / -7); one hit box 18 x 18 at (15, -12)", 3)],
                       "Breath": [("outer heads glow (tell)", 0), ("the outer cones start (at -40 / +40 deg)", 2),
                                  ("the middle cone starts; the outer ones sweep in over 1 s", 3), ("cones fade", 9)]}


# ================================================================== CHURCH GRIM (T3): a huge black dog, lantern eyes, a bell rope, moss
def grim(lean=0.0, bob=0.0, legs=None, head_at=None, face="shut", tail=0.0, extra=None, smear_pts=None, dust_at=None, crouch=0.0,
         stretch=0.0, bell=0.0, lowered=0.0):
    r = Rig()
    legs = legs or ((-8.0, 0.0), (7.0, 0.0), (-7.0, 0.0), (8.0, 0.0))
    T = Xf(lean, (0.0, -12.0))
    hip = T(-8.0 - stretch * 0.5, -12.0 + bob + crouch)
    sh = T(6.0 + stretch * 0.5, -14.0 + bob + crouch * 0.6 + lowered)
    dog_body(r, hip, sh, legs, mat="bhide", chest=5.6, haunch=4.0, waist=3.0, ribs=0, thick=2.0, leg_len=(5.6, 5.4),
             fleg_len=(5.8, 6.4), tail=[(3.0, 190 + tail), (3.0, 205 + tail), (2.6, 225 + tail), (2.0, 245 + tail)], paw="bhide",
             rib_mat="bhide")
    # moss along the back
    for i in range(7):
        t = i / 6.0
        x0, y0 = lerp(hip[0], sh[0], t), lerp(hip[1], sh[1], t) - (4.0 if 0.2 < t < 0.8 else 3.0) - math.sin(t * math.pi) * 0.8
        r.ell(x0, y0, 1.6, 1.0, "moss", 0.6 + i * 0.01, bias=0.2)
    hx, hy = head_at or (sh[0] + 3.0, sh[1] - 4.0)
    r.tube([(sh[0] + 0.5, sh[1] - 1.5), (hx - 0.5, hy - 0.5)], [3.0, 2.2], "bhide", 0.8, bias=0.15)
    # frayed bell rope round the neck, a little bronze bell
    nx, ny = lerp(sh[0], hx, 0.5), lerp(sh[1], hy, 0.5)
    r.polyline([(nx - 2.0, ny - 2.0), (nx - 1.0, ny + 0.5), (nx + 1.0, ny + 2.0)], "rope", 1.0, tones=[3, 2])
    bx, by = nx + 1.0 + bell, ny + 3.5
    r.line(nx + 1.0, ny + 2.0, bx, by - 1.0, "rope", 1.01, tone=2)
    r.poly([(bx - 1.2, by + 1.0), (bx + 1.2, by + 1.0), (bx + 0.8, by - 1.0), (bx - 0.8, by - 1.0)], "bronze", 1.02, bias=0.2)
    leg = dict(BARG_LEG, e=("lant", 4), E=("white", 4))
    r.stamp(BARG_HEADS[face], hx, hy, 2.0, leg, pivot=(2, 4))
    r.dot(hx + 1, hy - 1, "lant", 4, 2.1); r.dot(hx + 2, hy - 1, "lant", 3, 2.1)
    if smear_pts: smear(r, smear_pts, "bone", 4)
    if dust_at: dust(r, *dust_at)
    if extra: extra(r)
    return r.resolve()


GL = ((-8.0, 0.0), (7.0, 0.0), (-7.0, 0.0), (8.0, 0.0))


def grim_heap(k=0, rise=0.0, eyes=True):
    """Fallen into bones, the lantern eyes still lit (k flickers)."""
    r = Rig()
    heap(r, 0.0, 0, 18.0, 18, seed=111, h=1.4 + rise * 3.0)
    r.ell(-1.0, -1.2, 7.0, 1.6, "bhide", -0.5, bias=-0.2)
    for i in range(4): r.ell(-5.0 + 3 * i, -2.0 - rise, 1.4, 0.8, "moss", 0.4, bias=0.2)
    r.stamp(DOG_SKULL["open"], 4.0, -1.0 - rise * 2.0, 1.0, dict(BONE_LEG, e=("lant", 4 if (eyes and k % 2 == 0) else 3) if eyes else ("iron", 0)),
            pivot=(1, 3))
    if eyes:
        r.dot(5 + (k % 2), -5 - rise * 2.0, "lant", 4 if k % 2 == 0 else 3, 3.0)
    return r.resolve()


def grim_sheet(outdir):
    G = grim
    idle = [G(bob=[0, 0.3, 0.6, 0.3][i], face="shut" if i != 2 else "open", tail=[0, 6, 12, 6][i], bell=[0, 0.5, 1, 0.5][i]) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        run.append(G(lean=-4 * math.sin(ph), bob=-1.0 * abs(math.sin(ph)), legs=gait(i, 6, 4.0, 2.4, gallop=True, base=GL), face="open",
                     tail=22 + 10 * math.sin(ph), stretch=1.6 * math.cos(ph), bell=-1.5 + math.sin(ph)))
    lunge = ((-7.0, 0.0), (10.0, 0.0), (-6.0, 0.0), (11.0, 0.0))
    # Bite (6): rear back (0-1), LUNGE (2: jaws at (24, -14)), hold (3), back (4-5)
    bite = [G(crouch=1.0, lean=6, face="open"), G(lean=-8, face="open", head_at=(8.0, -21.0)),
            G(lean=8, face="shut", head_at=(16.0, -15.0), legs=lunge, stretch=4.0, smear_pts=[(14, -22), (19, -20), (24, -16)]),
            G(lean=8, face="shut", head_at=(15.0, -15.0), legs=lunge, stretch=3.6), G(lean=2), G()]
    # Lunge (7): crouch low (0-1), RUN THROUGH (2-5: low, jaws at (20, -9)), skid and turn (6)
    ln = [G(crouch=2.4, lean=10, face="open", lowered=2.0), G(crouch=3.0, lean=12, face="open", lowered=3.0, dust_at=(0.0, 0.0, 0, 1.4))]
    for i in range(4):
        ph = i / 4 * math.tau
        ln.append(G(crouch=2.0, lean=10, lowered=3.0, face="open" if i % 2 else "shut", head_at=(13.0, -11.0), stretch=3.0,
                    legs=gait(i, 4, 4.4, 2.0, gallop=True, base=GL), dust_at=(-10.0, 0.0, i % 2, 1.2),
                    smear_pts=[(-18, -12), (-12, -12)] if i % 2 == 0 else None))
    ln.append(G(lean=-8, legs=((-5.0, 0.0), (10.0, 0.0), (-4.0, 0.0), (11.0, 0.0)), dust_at=(9.0, 0.0, 0, 1.8)))
    # Fall (4): undying: it buckles into a heap of bones, the lantern eyes stay lit
    fall = [G(lean=-10, face="open", head_at=(8.0, -20.0)),
            G(lean=10, crouch=5.0, face="open", head_at=(10.0, -8.0), legs=((-9.0, 0.0), (9.0, 0.0), (-8.0, 0.0), (10.0, 0.0)),
              extra=lambda r: bone_bits(r, 0, -10, 1, 8, seed=6, z=5)),
            grim_heap(0, 0.3), grim_heap(0)]
    hp = [grim_heap(k) for k in range(2)]
    rise = [grim_heap(0, 0.4), grim_heap(1, 0.8),
            G(crouch=4.0, lean=8, face="open", extra=lambda r: bone_bits(r, 0, -4, 1, 6, seed=8, z=-1)),
            G(crouch=1.5, face="open", extra=lambda r: bone_bits(r, 0, -8, 2, 4, seed=8, z=-1)), G()]
    d0 = G(lean=-12, face="open", head_at=(7.0, -20.0))
    d1 = G(lean=10, crouch=5.0, face="open", head_at=(10.0, -8.0), legs=((-9.0, 0.0), (9.0, 0.0), (-8.0, 0.0), (10.0, 0.0)))
    d2 = grim_heap(0, eyes=False)
    corpse = grim_heap(1, eyes=False)
    knock = G(lean=-14, face="open", head_at=(7.0, -19.0), legs=((-9.0, 0.0), (5.0, 0.0), (-8.0, 0.0), (6.0, 0.0)))
    anims = [("Idle", idle, [0.16, 0.12, 0.16, 0.12]), ("Run", run, [0.065] * 6),
             ("Bite", bite, [0.1, 0.1, 0.05, 0.08, 0.1, 0.12]),
             ("Lunge", ln, [0.12, 0.12, 0.06, 0.06, 0.06, 0.06, 0.14]),
             ("Fall", fall, [0.08, 0.1, 0.1, 0.2]), ("Heap", hp, [0.2, 0.2]), ("Rise", rise, [0.1, 0.1, 0.1, 0.1, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("OssChurchGrim", anims, outdir)


SYNC["OssChurchGrim"] = {"Bite": [("LUNGE: jaws at (24, -14); hit box 16 x 14 at (20, -13); move 20 px", 2)],
                         "Lunge": [("RUN THROUGH: move from here, low jaws box at (16, -9)", 2), ("stop", 6)],
                         "Fall": [("undying: lie as a heap (Heap loops) for 3 s", 3)],
                         "Rise": [("standing again with 3 health", 4)]}
NOTES["OssChurchGrim"] = "Fall -> Heap (looped) -> Rise is the one-time Undying revive; Death plays only for the real death."


# ================================================================== CARRION SAINT (T3): feather cloak, arms out, bone crows perched
PERCH = """
.fFf...
fFFeLH.
fFFFLHH
.fff...
..i.i..
"""
PERCH_LEG = {"f": ("slate", 2), "F": ("slate", 3), "L": ("bone", 3), "H": ("bone", 4), "i": ("iron", 3), "e": ("mglow", 3)}
PERCH_SPOTS = [(-11.0, -24.0), (12.0, -25.0), (-7.0, -24.5), (2.0, -36.0)]   # far arm, near arm, far forearm, halo


def saint(crows=4, lean=0.0, bob=0.0, arms=1.0, hand=None, hand2=None, halo=1.0, extra=None, hem=0.0, flutter=0):
    """arms: 1 = held out level (the cross), lower values drop them. crows: how many are perched (0-4)."""
    r = Rig()
    T = Xf(lean, (0.0, 0.0))
    top = T(0.0, -26.0 + bob)
    # feather cloak to the floor
    pts = [(top[0] - 3.0, top[1]), (top[0] + 3.0, top[1])]
    for i in range(7):
        t = i / 6.0
        pts.append((lerp(7.0 + hem, -7.0, t), -0.2 - (1.0 if i % 2 else 0.0)))
    r.poly(pts, "feath", 0.0, curve=0.8, normal=(-0.2, -0.2, 1.0))
    for i in range(4):
        y = top[1] + 5 + i * 5
        r.polyline([(top[0] - 2 - i, y), (top[0] + 2 + i, y + 1)], "feath", 0.05, tones=[4, 3])
    # arms out like a cross
    hand = hand or (14.0, -23.0 + (1 - arms) * 10)
    hand2 = hand2 or (-13.0, -22.0 + (1 - arms) * 10)
    for k, (hx, hy) in enumerate((hand2, hand)):
        near = k == 1
        s0 = (top[0] + (2.5 if near else -2.5), top[1] + 1.5)
        ex, ey = lerp(s0[0], hx, 0.5), lerp(s0[1], hy, 0.5) + 0.5
        r.tube([s0, (ex, ey), (hx, hy)], [1.6, 1.3, 1.0], "feath", 1.2 if near else -0.6, bias=0.1 if near else -0.4)
        lbone(r, (lerp(ex, hx, 0.4), lerp(ey, hy, 0.4)), (hx, hy), 1.3 if near else -0.5, near)
        # feather fringe hanging from the arm
        for j in range(4):
            fx_ = lerp(s0[0], hx, 0.2 + 0.2 * j); fy_ = lerp(s0[1], hy, 0.2 + 0.2 * j)
            r.line(fx_, fy_ + 1, fx_ - 0.5, fy_ + 4 + (j % 2), "feath", 1.1 if near else -0.7, tone=3 if near else 1)
    # gaunt skull face under a feather hood, the halo of gold behind
    if halo:
        r.dots(arc_pts(top[0] + 1.0, top[1] - 7.0, 6.0, 3.0, 0, 360, 22), "gold", 3, -1.5)
        r.dots(arc_pts(top[0] + 1.0, top[1] - 7.0, 6.0, 3.0, 200, 340, 8), "gold", 4, -1.49)
    r.poly([(top[0] - 4.0, top[1] + 1.0), (top[0] - 3.0, top[1] - 8.0), (top[0] + 2.5, top[1] - 9.0), (top[0] + 4.5, top[1] + 0.5)],
           "feath", 2.0, curve=0.5)
    skullp(r, top[0] + 1.0, top[1] + 0.5, "M", 2.5)
    spots = [(hand2[0] + 2.0, hand2[1] - 1.0), (hand[0] - 2.0, hand[1] - 1.0), (lerp(top[0], hand2[0], 0.55), lerp(top[1], hand2[1], 0.5) - 1.0),
             (top[0] + 1.0, top[1] - 8.0)]
    for i in range(min(4, crows)):
        x, y = spots[i]
        r.stamp(PERCH, x, y - (1 if (flutter + i) % 3 == 0 else 0), 3.0 + i * 0.05, PERCH_LEG, pivot=(3, 4))
        if (flutter + i) % 3 == 0: r.dot(x - 1, y - 3, "feath", 4, 3.1)
    if extra: extra(r)
    return r.resolve()


def saint_sheet(outdir):
    S = saint
    anims = []
    for c in range(5):
        idle = [S(c, bob=[0, 0.4, 0.8, 0.4][i], flutter=i) for i in range(4)]
        run = [S(c, lean=6, bob=[0, -0.5, -0.8, -0.5, 0, 0.3][i], hem=[-1, 0, 1, 0, -1, -1.5][i], arms=0.8, flutter=i) for i in range(6)]
        anims += [("Idle" if c == 4 else "Idle%d" % c, idle, [0.16, 0.12, 0.16, 0.12]),
                  ("Run" if c == 4 else "Run%d" % c, run, [0.09] * 6)]
    crow_fly = lambda x, y, k: (lambda r: r.stamp(PERCH, x, y, 6.0, PERCH_LEG, pivot=(2, 3)) if k == 0 else
                                [r.stamp(PERCH, x, y, 6.0, PERCH_LEG, pivot=(2, 3)), r.line(x - 4, y - 1, x - 7, y - 3, "feath", 6.0, tone=3)])
    # Send (6): point (0-1), the crow leaves the arm (2: at (14, -26)), gesture (3), settle (4-5). Shown with 3 crows left.
    send = [S(4, hand=(15.0, -25.0)), S(4, hand=(17.0, -27.0), lean=-4),
            S(3, hand=(18.0, -24.0), lean=6, extra=lambda r: [r.stamp(PERCH, 20.0, -26.0, 6.0, PERCH_LEG, pivot=(2, 3)),
                                                               smear(r, [(12, -28), (16, -28), (19, -27)], "feath", 4)]),
            S(3, hand=(17.0, -23.0), lean=4), S(3), S(3)]
    # Murder (8): arms high (0-1), the flock lifts (2), WALL: every crow flies at once (3: they leave the arms), arms sweep (4-7)
    mur = [S(4, arms=1.2, hand=(13.0, -29.0), hand2=(-12.0, -28.0)), S(4, arms=1.3, hand=(12.0, -33.0), hand2=(-11.0, -32.0), flutter=0),
           S(4, arms=1.3, hand=(12.0, -33.0), hand2=(-11.0, -32.0), flutter=1, extra=lambda r: r.dots([(-8, -34), (14, -36), (2, -42)], "feath", 4, 7)),
           S(0, lean=10, hand=(18.0, -20.0), hand2=(10.0, -20.0),
             extra=lambda r: [r.stamp(PERCH, 22.0, -12.0 - 6 * i, 6.0, PERCH_LEG, pivot=(2, 3)) for i in range(4)]),
           S(0, lean=8, hand=(16.0, -16.0), hand2=(8.0, -16.0)), S(0, lean=4), S(0), S(0)]
    d0 = S(2, lean=-10, arms=1.3, hand=(12.0, -32.0), hand2=(-11.0, -31.0))
    d1 = saint_fall(0); d2 = saint_fall(1); corpse = saint_fall(2)
    knock = S(4, lean=-12, arms=1.2)
    anims += [("Send", send, [0.12, 0.1, 0.05, 0.1, 0.1, 0.12]), ("Murder", mur, [0.12, 0.12, 0.1, 0.06, 0.1, 0.1, 0.12, 0.12])]
    anims += tail_anims(saint(4), [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("OssCarrionSaint", anims, outdir)


def saint_fall(stage):
    r = Rig()
    if stage == 0:
        r.poly([(-8, -12), (4, -15), (9, -0.2), (-9, -0.2)], "feath", 0.0, curve=0.7)
        skullp(r, 3.0, -13.0, "M", 1.0)
        r.dots(arc_pts(4.0, -20.0, 6.0, 3.0, 0, 360, 18), "gold", 2, -1.0)
    else:
        r.poly([(-12, -3), (10, -4), (13, -0.2), (-13, -0.2)], "feath", 0.0, curve=0.4)
        heap(r, -2.0, 0, 8.0, 6, seed=121, z=0.3, h=0.5)
        skullp(r, 10.0, 0.0, "M", 0.5, eye=stage < 2)
        r.dots(arc_pts(-8.0, -1.0, 5.0, 1.0, 0, 360, 16), "gold", 2 if stage == 1 else 1, 0.4)
        for i in range(3): r.line(-10 + 6 * i, -3, -8 + 6 * i, -1, "feath", 0.6, tone=4)
    return r.resolve()


SYNC["OssCarrionSaint"] = {"Send": [("SEND: the next crow leaves the arm at (18, -26)", 2)],
                           "Murder": [("WALL: every perched crow flies at once from (20, -20)", 3)]}
NOTES["OssCarrionSaint"] = "Idle/Run show the full flock of 4; IdleN/RunN show N perched crows (0..3)."


# ================================================================== THE OSSUARY (T3): a walking charnel house of skulls and long bones
CANDLE_LEG = dict(BONE_LEG, e=("lant", 3), E=("lant", 4))


def ossuary(lean=0.0, bob=0.0, fist=(13.0, -10.0), fist2=(-12.0, -10.0), legs=((5.0, 0.0), (-5.0, 0.0)), extra=None,
            smear_pts=None, dust_at=None, crouch=0.0, eyes=3, jaw=0):
    r = Rig()
    T = Xf(lean, (0.0, -12.0))
    base = -7.0 + bob + crouch
    # stumpy legs of stacked femurs
    for k, (fx_, fy_) in enumerate(legs):
        near = k == 0
        hx, hy = fx_ * 0.6, base
        bone(r, (hx, hy), (fx_, fy_ - 1.0), 1.8, 0.5 if near else -1.0, "bone" if near else "dbone")
        r.ell(fx_ + 0.5, fy_ - 0.8, 2.6, 1.0, "bone" if near else "dbone", 0.6 if near else -0.9)
    # the block: rows of skulls between long bones, a peaked roof of crossed femurs
    x0, x1 = -11.0, 11.0
    rows = 4
    for j in range(rows):
        y = base - 2.0 - j * 6.0
        w = (x1 - x0) - j * 2.0
        bx = (x0 + x1) / 2.0 - w / 2.0
        p0, p1 = T(bx - 0.5, y + 1.5), T(bx + w + 0.5, y + 1.5)
        bone(r, p0, p1, 1.0, 0.1 + j * 0.01, "bone")
        n = int(w // 5)
        for i in range(n):
            sx, sy = T(bx + 2.5 + i * (w / n), y)
            leg = CANDLE_LEG if (j == rows - 2 and i in (n // 2 - 1, n // 2)) else dict(BONE_LEG, e=("iron", 0), E=("iron", 0))
            r.stamp("""
.LHL.
LkLkS
SeBeS
.TtT.
""", sx, sy, 0.2 + j * 0.01 + i * 0.001, leg if j != rows - 2 else CANDLE_LEG, pivot=(2, 4))
        # dark mortar behind
        r.poly([T(bx, y + 1.0), T(bx + w, y + 1.0), T(bx + w, y - 5.0), T(bx, y - 5.0)], "dbone", -0.5, bias=-0.5)
    # roof: crossed femurs and a crowning skull with candle-gold sockets (the face)
    ry = base - 2.0 - rows * 6.0 + 2.0
    bone(r, T(-7.0, ry + 1.0), T(4.0, ry - 5.0), 1.0, 0.6, "bone")
    bone(r, T(7.0, ry + 1.0), T(-4.0, ry - 5.0), 1.0, 0.5, "dbone")
    hx, hy = T(1.0, ry - 1.0)
    skullp(r, hx, hy, "L", 0.8, jaw=jaw, legend=dict(CANDLE_LEG, e=("lant", eyes), E=("lant", 4)))
    # arms of femurs ending in knuckle-bone fists
    for k, (fx_, fy_) in enumerate((fist2, fist)):
        near = k == 1
        s0 = T(9.5 if near else -9.5, base - 18.0)
        ex, ey = ik(s0[0], s0[1], fx_, fy_, 8.0, 7.5, bend=-1 if near else 1)
        z = 1.5 if near else -1.2
        bone(r, s0, (ex, ey), 1.4, z, "bone" if near else "dbone")
        bone(r, (ex, ey), (fx_, fy_), 1.2, z + 0.01, "bone" if near else "dbone")
        r.ell(fx_, fy_, 2.4, 2.2, "bone" if near else "dbone", z + 0.02, bias=0.1)
        r.dot(fx_ + 1, fy_ - 1, "bone", 4 if near else 2, z + 0.03)
    if smear_pts: smear(r, smear_pts, "bone", 4)
    if dust_at: dust(r, *dust_at)
    if extra: extra(r)
    return r.resolve()


def ossuary_sheet(outdir):
    O = ossuary
    idle = [O(bob=[0, 0.4, 0.8, 0.4][i], eyes=[3, 3, 4, 3][i], fist=(13.0, -10.0 + [0, 0.4, 0.8, 0.4][i]),
              fist2=(-12.0, -10.0 + [0, 0.4, 0.8, 0.4][i])) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        f1 = (1.0 + 3.0 * math.cos(ph), -max(0.0, 1.8 * math.sin(ph)))
        f2 = (-1.0 - 3.0 * math.cos(ph), -max(0.0, -1.8 * math.sin(ph)))
        b = -0.8 * abs(math.sin(ph))
        run.append(O(lean=4 * math.sin(ph), bob=b, legs=((f1[0] + 4, f1[1]), (f2[0] - 4, f2[1])), fist=(13.0, -11.0 + b + math.sin(ph)),
                     fist2=(-12.0, -11.0 + b - math.sin(ph))))
    # Slam (8): fists up (0-2), SLAM both on the floor ahead (3: spike ring at (24, 0)), shudder (4-5), lift (6-7)
    sl = [O(fist=(10.0, -26.0), fist2=(-6.0, -27.0), eyes=4), O(lean=-4, fist=(8.0, -31.0), fist2=(-4.0, -31.0), eyes=4, jaw=1),
          O(lean=-6, fist=(7.0, -33.0), fist2=(-3.0, -33.0), eyes=4, jaw=2),
          O(lean=10, crouch=2.0, fist=(18.0, -2.0), fist2=(14.0, -2.0), eyes=4, smear_pts=[(6, -36), (14, -30), (18, -16), (19, -4)],
            dust_at=(18.0, 0.0, 0, 2.4, 4)),
          O(lean=10, crouch=2.4, fist=(18.0, -1.5), fist2=(14.0, -1.5), dust_at=(18.0, 0.0, 1, 2.6, 4)),
          O(lean=8, crouch=1.6, fist=(17.0, -3.0), fist2=(13.0, -3.0), dust_at=(18.0, 0.0, 2, 2.8, 4)),
          O(lean=2, fist=(14.0, -8.0)), O()]
    # Rib (8): reach out (0-1), fingers splay (2-3), WRENCH up (4: the ribs burst round the hero), hold (5-7)
    rb = [O(fist=(15.0, -16.0), fist2=(-12.0, -16.0), eyes=3), O(lean=6, fist=(18.0, -14.0), fist2=(14.0, -15.0), eyes=4),
          O(lean=8, crouch=1.0, fist=(19.0, -6.0), fist2=(15.0, -6.0), eyes=4),
          O(lean=10, crouch=1.6, fist=(19.0, -3.0), fist2=(15.0, -3.0), eyes=4, extra=lambda r: r.polyline([(16, 0), (21, -1), (26, 0)], "iron", 7, tone=0)),
          O(lean=-6, fist=(16.0, -26.0), fist2=(12.0, -27.0), eyes=4, jaw=2, smear_pts=[(19, -4), (19, -12), (17, -22), (16, -26)]),
          O(lean=-6, fist=(16.0, -27.0), fist2=(12.0, -28.0), eyes=4, jaw=2), O(lean=-2, fist=(14.0, -20.0), eyes=3), O()]
    d0 = O(lean=-8, eyes=4, jaw=2, fist=(10.0, -26.0), fist2=(-10.0, -26.0))
    d1 = ossuary_fall(0); d2 = ossuary_fall(1); corpse = ossuary_fall(2)
    knock = O(lean=-10, eyes=4, jaw=1, fist=(10.0, -18.0), fist2=(-13.0, -16.0))
    anims = [("Idle", idle, [0.18, 0.14, 0.18, 0.14]), ("Run", run, [0.1] * 6),
             ("Slam", sl, [0.12, 0.12, 0.12, 0.05, 0.1, 0.1, 0.12, 0.12]),
             ("Rib", rb, [0.12, 0.12, 0.1, 0.1, 0.06, 0.12, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("OssOssuary", anims, outdir)


def ossuary_fall(stage):
    r = Rig()
    heap(r, 0.0, 0, 30.0 if stage else 24.0, 30 if stage else 24, seed=131, h=1.0 + (2 - stage) * 1.6)
    for i in range(5 if stage else 4):
        skullp(r, -12.0 + 6.0 * i, -1.0 - (2 - stage) * (2 if i % 2 else 3), "S", 1.0 + i * 0.01, eye=False)
    skullp(r, 2.0, -2.0 - (2 - stage) * 3, "L", 1.5, eye=stage < 2, legend=dict(CANDLE_LEG, e=("lant", 2)))
    if stage < 2: dust(r, 0, 0, stage, 3.0, 4)
    return r.resolve()


SYNC["OssOssuary"] = {"Slam": [("SLAM: both fists on the floor; spike ring centred at (24, 0)", 3)],
                      "Rib": [("cracks under the hero (0.4 s tell from here)", 2), ("WRENCH: six ribs burst up round the hero", 4)]}


# ================================================================== MARROW WYRM (T3): a long-necked wyrm of bone, split jaw red with marrow
WYRM_HEAD = {
    "shut": """
..LHHL....
.LHHHLLHL.
LLkeLLLLHL
SBBLLLmLLS
.SBTmTmTS.
""",
    "open": """
..LHHL....
.LHHHLLHL.
LLkeLLLLHL
SBBLLLLLLS
.SBTmT....
..SmmmmT..
...STmTS..
""",
}
WYRM_LEG = dict(BONE_LEG, m=("marrow", 3), e=("mglow", 3))


def wyrm(lean=0.0, bob=0.0, legs=None, neck=None, face="shut", wing_a=40.0, extra=None, smear_pts=None, dust_at=None, crouch=0.0,
         stretch=0.0, tail=0.0):
    """neck: the head point; the neck runs as an S of vertebrae from the shoulder to it."""
    r = Rig()
    legs = legs or ((-7.0, 0.0), (5.0, 0.0), (-6.0, 0.0), (6.0, 0.0))
    T = Xf(lean, (0.0, -9.0))
    hip = T(-7.0 - stretch * 0.5, -9.0 + bob + crouch)
    sh = T(4.0 + stretch * 0.5, -10.0 + bob + crouch * 0.6)
    # long tail of vertebrae
    tp = chain(hip[0] - 1.0, hip[1] - 0.5, [(3.0, 175 + tail), (3.0, 165 + tail), (3.0, 175 + tail * 1.4), (3.0, 195 + tail * 1.6)])
    vertebrae(r, tp, -0.5, "bone", proc=1, tone_a=3, tone_b=1)
    wing(r, (lerp(hip[0], sh[0], 0.6), sh[1] - 3.0), wing_a + 10, 9.0, -1.2, near=False, n=4, chord=3.5, mat="tar", bone_edge="dbone")
    boar_body(r, hip, sh, legs, chest=6.6, ribs=5, dirt=False, leg_len=(4.6, 4.4), fleg_len=(4.8, 5.0), seed=33, leg_rad=1.3)
    # marrow-red glow in the chest
    r.ell(lerp(hip[0], sh[0], 0.6), sh[1] + 1.0, 2.5, 1.6, "mglow", -0.2, flat=2)
    nx, ny = neck or (sh[0] + 6.0, sh[1] - 22.0)
    s0 = (sh[0] + 0.5, sh[1] - 2.0)
    # S-curve: out forward, back, then forward to the head
    c1 = (lerp(s0[0], nx, 0.25) + 4.0, lerp(s0[1], ny, 0.3))
    c2 = (lerp(s0[0], nx, 0.6) - 3.0, lerp(s0[1], ny, 0.65))
    pts = []
    for i in range(13):
        t = i / 12.0
        a = (1 - t) ** 3; b = 3 * (1 - t) ** 2 * t; c = 3 * (1 - t) * t * t; d = t ** 3
        pts.append((a * s0[0] + b * c1[0] + c * c2[0] + d * nx, a * s0[1] + b * c1[1] + c * c2[1] + d * ny))
    r.tube(pts, [2.4 - 0.1 * i for i in range(13)], "bone", 1.0, bias=0.05)
    vertebrae(r, [(x - 0.6, y - 1.0) for (x, y) in pts], 1.05, "bone", tone_a=4, tone_b=2)
    r.stamp(WYRM_HEAD[face], nx, ny, 1.5, WYRM_LEG, pivot=(1, 3))
    wing(r, (lerp(hip[0], sh[0], 0.7), sh[1] - 3.0), wing_a, 11.0, 1.2, near=True, n=4, chord=4.5, mat="tar", bone_edge="bone")
    if smear_pts: smear(r, smear_pts, "bone", 4)
    if dust_at: dust(r, *dust_at)
    if extra: extra(r)
    return r.resolve()


WL = ((-7.0, 0.0), (5.0, 0.0), (-6.0, 0.0), (6.0, 0.0))


def wyrm_sheet(outdir):
    W = wyrm
    idle = [W(bob=[0, 0.3, 0.6, 0.3][i], neck=(10.0 + [0, 0.5, 1, 0.5][i], -32.0 + [0, 0.5, 1, 0.5][i]), wing_a=[40, 50, 60, 50][i],
              face="shut" if i != 2 else "open", tail=[0, 5, 10, 5][i]) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        run.append(W(lean=-3 * math.sin(ph), bob=-0.8 * abs(math.sin(ph)), legs=gait(i, 6, 3.0, 1.8, base=WL),
                     neck=(12.0, -30.0 - math.sin(ph)), wing_a=40 + 30 * math.sin(ph), tail=10 * math.sin(ph)))
    # Lunge (6): neck back (0-1), STRIKE (2: jaws at (30, -14)), hold (3), back (4-5)
    lg = [W(neck=(6.0, -34.0), face="open"), W(neck=(2.0, -33.0), face="open", wing_a=80),
          W(neck=(24.0, -16.0), face="shut", lean=6, legs=((-6.0, 0.0), (7.0, 0.0), (-5.0, 0.0), (8.0, 0.0)),
            smear_pts=[(8, -36), (18, -30), (26, -20), (30, -15)]),
          W(neck=(23.0, -15.0), face="open", lean=6), W(neck=(14.0, -26.0)), W()]
    # Lash (9): cock the head back (0-4, 0.6 s), LASH round the arc (5-6: in front, high to low), recover (7-8)
    la = [W(neck=(4.0, -32.0), face="open", wing_a=60), W(neck=(0.0, -32.0), face="open", wing_a=70, lean=-4),
          W(neck=(-4.0, -30.0), face="open", wing_a=80, lean=-6), W(neck=(-6.0, -28.0), face="open", wing_a=90, lean=-8),
          W(neck=(-6.0, -27.0), face="open", wing_a=90, lean=-8, extra=lambda r: r.dot(-1, -30, "mglow", 4, 6)),
          W(neck=(22.0, -30.0), face="open", wing_a=20, lean=4, smear_pts=[(-4, -36), (6, -40), (16, -38), (24, -32)]),
          W(neck=(24.0, -8.0), face="shut", wing_a=10, lean=8, smear_pts=[(26, -30), (30, -22), (28, -12), (24, -6)]),
          W(neck=(18.0, -14.0), wing_a=30, lean=4), W()]
    d0 = W(neck=(4.0, -34.0), face="open", lean=-10, wing_a=100)
    d1 = W(neck=(18.0, -6.0), face="open", crouch=3.0, lean=8, wing_a=-20)
    d2 = wyrm_corpse(0); corpse = wyrm_corpse(1)
    knock = W(neck=(4.0, -30.0), face="open", lean=-12, wing_a=90)
    anims = [("Idle", idle, [0.16, 0.12, 0.16, 0.12]), ("Run", run, [0.075] * 6),
             ("Lunge", lg, [0.12, 0.12, 0.05, 0.08, 0.1, 0.12]),
             ("Lash", la, [0.12, 0.12, 0.12, 0.12, 0.12, 0.05, 0.05, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("OssMarrowWyrm", anims, outdir)


def wyrm_corpse(stage):
    r = Rig()
    heap(r, -6.0, 0, 16.0, 16, seed=141, h=0.8 if stage else 1.6)
    pts = [(2.0, -1.5), (8.0, -2.0), (14.0, -1.5), (20.0, -1.0)]
    r.tube(pts, [1.4, 1.2, 1.0, 0.9], "bone", 0.4)
    vertebrae(r, [(x, y - 1) for (x, y) in pts], 0.45, "bone", tone_a=4, tone_b=2)
    r.stamp(WYRM_HEAD["open"], 21.0, 0.0 if stage else -1.0, 0.6, dict(WYRM_LEG, e=("iron", 0)), pivot=(1, 3))
    if not stage: dust(r, 0, 0, 1, 2.0)
    return r.resolve()


SYNC["OssMarrowWyrm"] = {"Lunge": [("STRIKE: jaws at (30, -14); hit box 14 x 14 at (27, -14)", 2)],
                         "Lash": [("cocked back (0.6 s tell)", 0), ("LASH: the half-circle in front, radius 30; box 32 x 56 at (16, -12)", 5)]}


# ================================================================== CARRION ROC (T3): an enormous carrion bird, half its feathers gone to bone
ROC_HEAD = {
    "shut": """
...rR.....
..rRRr....
.rRkeRLL..
.rRRRLLHHL
..rrSBBLLL
.....SBBS.
""",
    "open": """
...rR.....
..rRRr....
.rRkeRLL..
.rRRRLLHHL
..rrSB....
.....SBL..
......SBS.
""",
}


def roc(r, x, y, z=0.0, wing_a=20.0, wing_b=None, lean=0.0, face="shut", talons=0.0, neck=(4.0, -5.0), grip=False, flip=False):
    f = -1 if flip else 1
    T = Xf(lean * f, (x, y))
    F = lambda dx, dy: T(x + dx * f, y + dy)
    wb = wing_a if wing_b is None else wing_b
    wing(r, F(0.5, -2.5), wb + 6, 20.0, z - 1.0, near=False, n=5, chord=8.5, face=f, bone_edge="dbone")
    r.poly([F(-3.0, -1.0), F(-10.0, 1.5), F(-9.0, 3.4), F(-3.0, 2.4)], "feath", z - 0.3, normal=(-0.3, -0.5, 0.8))
    # talons like grave hooks
    for k, dx in enumerate((1.8, -1.0)):
        lx, ly = F(dx, 3.6)
        tx, ty = lx + talons * f * 2.0, ly + 4.0 - talons * 0.6
        r.tube([(lx, ly), (tx, ty)], [0.9, 0.7], "obone", z + (0.4 if k == 0 else -0.4), bias=0.0 if k == 0 else -0.4)
        claw = [(tx, ty), (tx + 1.5 * f, ty + 0.5), (tx + 2.2 * f, ty + 1.8)] if not grip else [(tx, ty), (tx + 1.0 * f, ty + 1.6), (tx, ty + 2.6)]
        r.polyline(claw, "iron", z + (0.41 if k == 0 else -0.39), tones=[3, 2] if k == 0 else [1, 1])
    bx, by = F(0.0, 0.0)
    r.ell(bx, by, 10.0, 7.4, "feath", z, ang=-10 * f, bias=0.1)
    # bare bone patches: ribs where the feathers are gone
    for i in range(4):
        px, py = F(-2.0 + 1.4 * i, -1.0)
        r.line(px, py, px + 0.6 * f, py + 3.0, "bone", z + 0.1, tone=3 if i % 2 == 0 else 2)
    n0 = F(3.0, -3.0); hx, hy = F(neck[0] + 3.0, neck[1] - 3.0)
    r.tube([n0, ((n0[0] + hx) / 2, (n0[1] + hy) / 2 - 0.8), (hx, hy)], [1.6, 1.2, 1.0], "rawred", z + 0.25, bias=0.1)
    for i in range(5):
        a = math.radians(-150 + i * 30)
        cx, cy = F(3.0, -3.0)
        r.line(cx, cy, cx + 3.0 * math.cos(a) * f, cy + 2.4 * math.sin(a), "feath", z + 0.2, tone=4 if i % 2 == 0 else 3)
    r.stamp(ROC_HEAD[face], hx, hy, z + 0.3, VULT_LEG, pivot=(2, 4), flip=flip)
    wing(r, F(1.0, -2.0), wing_a, 20.0, z + 0.6, near=True, n=5, chord=8.0, face=f, bone_edge="bone")


def roc_frame(x=0.0, alt=8.0, **kw):
    r = Rig()
    extra = kw.pop("extra", None); sm = kw.pop("smear_pts", None); shadow = kw.pop("shadow", True)
    cargo = kw.pop("cargo", None)
    roc(r, x, -alt - 9.0, **kw)
    if cargo == "bones":
        heap(r, x + 1.0, -alt + 2.0, 6.0, 6, seed=151, z=-0.5, h=0.6)
    elif cargo == "ally":
        skullp(r, x + 2.0, -alt + 4.0, "M", -0.5, jaw=1)
        r.line(x - 1.0, -alt + 4.0, x - 1.0, -alt + 9.0, "dbone", -0.6, tone=2); r.line(x + 3.0, -alt + 4.0, x + 3.0, -alt + 9.0, "dbone", -0.6, tone=2)
    if shadow:
        r.ell(x, -0.3, 5.0, 1.0, "tar", -5.0, flat=2)
    if sm: smear(r, sm, "bone", 4)
    if extra: extra(r)
    return r.resolve()


def roc_sheet(outdir):
    Rc = roc_frame
    idle = [Rc(alt=[4.0, 4.6, 5.2, 4.6][i], wing_a=[60, 110, 70, 40][i], wing_b=[70, 115, 80, 50][i]) for i in range(4)]
    run = [Rc(alt=8.0 + [0, 1, 1.5, 1, 0.3, -0.3][i], lean=12, wing_a=[115, 80, 30, -5, 40, 90][i], wing_b=[115, 90, 40, 5, 50, 95][i])
           for i in range(6)]
    # Stab (6): rear (0-1), DIVE (2: beak at (16, -12)), hold (3), climb (4-5)
    st = [Rc(alt=9.0, lean=-12, wing_a=100, face="open"), Rc(alt=10.0, lean=-20, wing_a=130, wing_b=125, face="open"),
          Rc(x=4.0, alt=4.0, lean=34, wing_a=10, wing_b=20, face="shut", smear_pts=[(-4, -26), (4, -22), (12, -16), (17, -12)]),
          Rc(x=4.0, alt=4.0, lean=30, wing_a=20, face="open", extra=lambda r: bone_bits(r, 17, -9, 0, 4, seed=4, z=6, mat="rawred")),
          Rc(x=2.0, alt=8.0, lean=-8, wing_a=110), Rc(alt=8.0, wing_a=50)]
    # Grab (4): drop on the friend (0-1), SEIZE (2: talons close), lift (3)
    gr = [Rc(alt=5.0, lean=10, wing_a=120, talons=1.0), Rc(alt=2.0, lean=6, wing_a=130, wing_b=130, talons=1.5),
          Rc(alt=2.5, wing_a=100, grip=True, talons=0.5, cargo="ally"), Rc(alt=5.0, wing_a=20, wing_b=30, grip=True, cargo="ally")]
    # Carry (4, loops): heavy beats, the friend dangling from the talons (its own body is drawn by the game under the roc)
    ca = [Rc(alt=7.0 + [0, 0.8, 1.2, 0.6][i], lean=10, wing_a=[110, 60, 0, 50][i], wing_b=[115, 70, 10, 60][i], grip=True) for i in range(4)]
    # Drop (4): open the talons (0: DROP), rise (1-3)
    dr = [Rc(alt=7.0, lean=-6, wing_a=120, talons=1.5, face="open"), Rc(alt=9.0, lean=-10, wing_a=30, face="open"),
          Rc(alt=10.0, wing_a=100), Rc(alt=8.0, wing_a=40)]
    d0 = Rc(alt=8.0, lean=-30, wing_a=130, wing_b=80, face="open")
    d1 = Rc(alt=3.0, lean=-80, wing_a=150, wing_b=110, face="open", extra=lambda r: bone_bits(r, 0, -6, 1, 6, seed=5, z=6, mat="feath"))
    d2 = roc_corpse(0); corpse = roc_corpse(1)
    knock = Rc(alt=8.0, lean=-30, wing_a=130, wing_b=120, face="open")
    anims = [("Idle", idle, [0.16, 0.12, 0.16, 0.12]), ("Run", run, [0.08] * 6),
             ("Stab", st, [0.1, 0.12, 0.05, 0.08, 0.1, 0.12]), ("Grab", gr, [0.1, 0.1, 0.1, 0.12]),
             ("Carry", ca, [0.1] * 4), ("Drop", dr, [0.08, 0.1, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("OssCarrionRoc", anims, outdir)


def roc_corpse(stage):
    r = Rig()
    roc(r, 0.0, -4.0, 0.0, wing_a=-30 if stage else 10, wing_b=170, lean=-90 if stage else -60, face="open")
    if not stage: bone_bits(r, 0, -2, 2, 6, seed=9, z=6, mat="feath")
    return r.resolve()


SYNC["OssCarrionRoc"] = {"Stab": [("DIVE: beak at (17, -12); hit box 16 x 14 at (13, -11)", 2)],
                         "Grab": [("SEIZE the nearest friend (or bone pile) within 40 px", 2)],
                         "Carry": [("loops while it flies the friend at the hero (up to 1.5 s)", 0)],
                         "Drop": [("DROP: the friend falls on the hero (hit 1.0), lands with a plate", 0)]}
NOTES["OssCarrionRoc"] = "Flies (hover 8 px). Grab/Carry draw the talons only; the carried friend keeps its own sprite under it."

JOBS = [("OssCerberus", cerb_sheet), ("OssChurchGrim", grim_sheet), ("OssCarrionSaint", saint_sheet),
        ("OssOssuary", ossuary_sheet), ("OssMarrowWyrm", wyrm_sheet), ("OssCarrionRoc", roc_sheet)]
