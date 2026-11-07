"""Sylvene tier 3, ground finals: Briar Behemoth, Briar Champion (four lance lengths), Puffball Brute, Cordyceps Saint
(and its Shambler), Rot Mother, Nightshade. Built through sylvene_v2_rigs.py. T3 idle limit 42 x 40; none is smaller than
the sheet it replaces."""
import math
from sylvene_v2_rigs import (Rig, Xf, chain, ik, lerp, sheet, tail_anims, cap, vine, thorn, leaf, wing, pod, motes, puff,
                             smears, sparks, soil, dust_puff)
from sylvene_v2_t2 import arm, legs, shelf


def dirt_ring(r, x, y, rx, k, mat="sporec", z=6.0, gap=3):
    for i in range(36):
        a = i / 36 * math.tau
        if (i + k) % gap == 0: continue
        r.dot(x + rx * math.cos(a), y - 1 + rx * 0.35 * math.sin(a), mat, max(1, 4 - k), z)


# ================================================================== BRIAR BEHEMOTH: a bramble-backed boar with thorn tusks
BEHE_LEG = {"k": ("bark", 0), "d": ("bark", 1), "b": ("bark", 2), "B": ("bark", 3), "m": ("chitin", 0), "e": ("eye", 3),
            "E": ("eye", 4), "t": ("tusk", 2), "T": ("tusk", 3), "X": ("tusk", 4), "r": ("blood", 3), "n": ("bark", 4)}


def boar_head(r, hx, hy, face, z=1.0, tilt=0.0):
    """A big boar head from the neck point (hx, hy): a heavy skull, a long snout, an ear laid back, a red eye under a
    bristling brow, and two thick tusks that curl up out of the jaw and back over the snout."""
    T = Xf(tilt, (hx, hy))
    sk = T(hx + 3.5, hy)
    r.ell(*sk, 5.8, 4.8, "bark", z, bias=0.1, ang=15 + tilt)
    r.tube([T(hx + 6.0, hy + 0.5), T(hx + 10.5, hy + 2.2)], [3.0, 2.4], "bark", z + 0.05, bias=0.05)
    nose = T(hx + 11.2, hy + 2.4)
    r.ell(*nose, 1.3, 2.3, "podf", z + 0.1, bias=-0.2)
    r.dot(nose[0] + 0.5, nose[1] - 0.6, "chitin", 0, z + 0.11); r.dot(nose[0] + 0.5, nose[1] + 0.8, "chitin", 0, z + 0.11)
    # the jaw: shut, or gaping in the roar
    jaw_open = 2.2 if face == "roar" else 0.0
    r.tube([T(hx + 3.0, hy + 3.2), T(hx + 9.5, hy + 4.2 + jaw_open)], [2.0, 1.4], "bark", z - 0.05, bias=-0.25)
    if jaw_open:
        r.poly([T(hx + 4.5, hy + 2.6), T(hx + 10.0, hy + 3.2), T(hx + 9.0, hy + 4.4 + jaw_open)], "blood", z + 0.02, flat=1)
    # ear laid back, bristle crest on the brow
    r.poly([T(hx + 1.0, hy - 3.5), T(hx - 3.5, hy - 7.5), T(hx + 3.0, hy - 4.5)], "bark", z + 0.08, normal=(-0.4, -0.6, 0.7))
    r.dot(*T(hx - 1.5, hy - 5.8), "podf", 2, z + 0.09)
    for k in range(4):
        thorn(r, *T(hx + 1.5 + k * 1.4, hy - 4.0 + k * 0.3), -110 + k * 12, 2.0, z + 0.1, tip="blood")
    # eye
    ex, ey = T(hx + 5.5, hy - 1.6)
    if face == "dead":
        r.dot(ex - 0.5, ey - 0.5, "chitin", 0, z + 0.2); r.dot(ex + 0.5, ey + 0.5, "chitin", 0, z + 0.2)
    else:
        r.dot(ex, ey, "eye", 4, z + 0.2); r.dot(ex - 1, ey, "eye", 2, z + 0.2)
        r.line(ex - 2, ey - 1.2, ex + 1.5, ey - 1.6, "bark", z + 0.21, tone=0)
    # tusks: thick ivory, curling up and back, blood-red tips
    for side, dz in ((-1, -0.4), (1, 0.4)):
        b = T(hx + 8.0 + (0 if side > 0 else -1.2), hy + 3.4 + jaw_open * 0.5)
        pts = [b, (b[0] + 2.2, b[1] - 1.4), (b[0] + 2.8, b[1] - 4.0), (b[0] + 1.6, b[1] - 6.6), (b[0] - 0.6, b[1] - 7.6)]
        r.tube(pts, [1.5, 1.3, 1.0, 0.7, 0.5], "tusk", z + dz + 0.3, bias=0.15 if side > 0 else -0.15)
        r.dot(*pts[-1], "blood", 3, z + dz + 0.31)


def behemoth(lean=0.0, bob=0.0, legs4=None, head=(12.0, -15.0), face="calm", smear=None, spark=None, extra=None, vine_k=0.0,
             body_dy=0.0, hook=0.0, squash=0.0):
    r = Rig()
    by = -12.0 + bob + body_dy
    legs4 = legs4 or [(-9.0, 0.0), (-6.0, 0.0), (6.0, 0.0), (9.0, 0.0)]
    T = Xf(lean, (0.0, by))
    hips = [T(-8.5, by + 2.5), T(-7.0, by + 2.5), T(5.0, by + 2.0), T(6.5, by + 2.0)]
    for k, ((fx, fy), hp) in enumerate(zip(legs4, hips)):
        far = k in (0, 2)
        kn = ik(hp[0], hp[1], fx, fy - 1.0, 5.2, 4.6, bend=1 if k < 2 else -1)
        z = -1.0 if far else 1.0
        r.tube([hp, kn, (fx, fy - 1.0)], [3.0, 2.0, 1.5], "bark", z, bias=-0.35 if far else 0.0)
        r.ell(fx + 0.6, fy - 0.8, 1.8, 1.0, "chitin", z + 0.01, bias=-0.2 if far else 0.1)
    # the vine that drags the bush: from the rump back and down off the left edge
    rx, ry = T(-12.5, by - 1.0)
    vine(r, [(rx, ry), (rx - 3.0, ry + 4.0 + vine_k), (rx - 5.5, -1.0 - vine_k * 0.5)], [1.1, 0.9, 0.7], -1.5, mat="moss", thorns=2,
         seed=5, tlen=1)
    # a boar's body: a lean rump rising to a great hump of shoulder
    r.ell(*T(-3.0, by - 0.5), 10.5, 6.6 - squash, "bark", 0.0, bias=0.05)
    r.ell(*T(4.0, by - 3.0), 8.0, 7.8 - squash, "bark", 0.05, bias=0.1)
    r.ell(*T(-2.0, by + 3.4), 9.0, 2.6, "bark", 0.06, bias=-0.3)
    # a dark bristle mane down the spine, with thorns bristling out of it
    spine = [T(-12.5, by - 4.0), T(-6.0, by - 6.8), T(0.0, by - 9.6), T(5.0, by - 10.8), T(9.5, by - 8.0)]
    r.tube(spine, [1.4, 1.8, 2.2, 2.0, 1.2], "bark", 0.2, bias=-0.45)
    for k in range(10):
        f = k / 9.0
        i = min(len(spine) - 2, int(f * (len(spine) - 1))); t = f * (len(spine) - 1) - i
        x = lerp(spine[i][0], spine[i + 1][0], t); y = lerp(spine[i][1], spine[i + 1][1], t)
        thorn(r, x, y - 1.2, -95 - 25 * (1 - f) + (8 if k % 2 else -8), 3.5 + 2.0 * math.sin(f * math.pi), 0.3 + k * 0.01, tip="blood")
    for k, (x, y) in enumerate(((-8.0, -4.6), (-2.0, -7.6), (4.0, -9.6))):
        leaf(r, *T(x, by + y), -140 + k * 30, 3.0, 0.32)
    for k in range(3):
        thorn(r, *T(9.0 + k * 0.6, by - 3.0 + k * 2.2), -40 + k * 20, 2.2, 0.35, tip="blood")
    hx, hy = head
    boar_head(r, hx - 3.0, hy + hook + 1.0, face, z=1.0, tilt=hook * 4.0)
    smears(r, smear); sparks(r, spark)
    if extra: extra(r)
    return r.resolve()


def behemoth_sheet(outdir):
    B = behemoth
    idle = [B(bob=[0, 0.4, 0.8, 0.4][i], head=(12.0, -15.0 + [0, 0.4, 0.8, 0.4][i]), vine_k=[0, 0.5, 1, 0.5][i]) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        s1, s2 = math.cos(ph), math.cos(ph + math.pi)
        run.append(B(lean=-3 * math.sin(ph), bob=-1.2 * abs(math.sin(ph)), vine_k=1.5 * math.sin(ph),
                     legs4=[(-9.0 + 3.5 * s1, -max(0, 2 * math.sin(ph))), (-6.0 + 3.5 * s2, -max(0, -2 * math.sin(ph))),
                            (6.0 + 3.5 * s1, -max(0, 2 * math.sin(ph + 1))), (9.0 + 3.5 * s2, -max(0, -2 * math.sin(ph + 1)))],
                     head=(13.0, -14.5 - abs(math.sin(ph)))))
    # Hook (7): lowers its head (0-1), HOOKS the tusks up (2-3: tusk tips sweep x 18..26, y -16..-4), tosses (4), recover (5-6)
    hk = [B(head=(12.0, -12.0), lean=4, face="roar"), B(head=(13.0, -9.0), lean=8, face="roar", body_dy=1.0),
          B(head=(15.0, -12.0), lean=-2, face="roar", smear=[("arc", 20.0, -8.0, 7.0, 100, -40, "tusk", 2)]),
          B(head=(15.0, -18.0), lean=-8, face="roar", spark=[(26.0, -16.0, 1)]),
          B(head=(14.0, -17.0), lean=-6), B(head=(13.0, -15.5)), B()]
    # Charge (10): paws the floor (0-2), CHARGES (3-7: head down, legs at full stretch, smears), SKIDS to a stop (8: the bush
    # swings in), recover (9)
    ch = [B(head=(12.0, -13.0), face="roar", legs4=[(-9.0, 0.0), (-6.0, 0.0), (6.0, 0.0), (10.0, -3.0)]),
          B(head=(12.0, -13.0), face="roar", legs4=[(-9.0, 0.0), (-6.0, 0.0), (6.0, 0.0), (8.0, 0.0)], extra=lambda r: soil(r, 9.0, 0.0, 0)),
          B(head=(12.0, -12.0), face="roar", lean=4, legs4=[(-9.0, 0.0), (-6.0, 0.0), (6.0, 0.0), (11.0, -3.0)], extra=lambda r: soil(r, 9.0, 0.0, 1))]
    for k in range(5):
        ph = k / 5 * math.tau
        ch.append(B(head=(14.0, -11.0), face="roar", lean=6, bob=-1.0 * abs(math.sin(ph)), vine_k=2.0,
                    legs4=[(-12.0 + 4 * math.cos(ph), -max(0, 2.5 * math.sin(ph))), (-8.0 - 4 * math.cos(ph), 0.0),
                           (8.0 + 4 * math.cos(ph), -max(0, 2.5 * math.sin(ph + 1))), (12.0 - 4 * math.cos(ph), 0.0)],
                    smear=[("line", [(-20, -16), (-14, -16)], "bark", 2), ("line", [(-22, -10), (-15, -10)], "bark", 1)]))
    ch.append(B(head=(13.0, -13.0), lean=-8, face="roar", legs4=[(-8.0, 0.0), (-5.0, 0.0), (9.0, 0.0), (12.0, 0.0)], vine_k=-2.0,
                extra=lambda r: soil(r, 12.0, 0.0, 0, 1.4)))
    ch.append(B(head=(12.5, -14.5)))
    d0 = B(face="roar", lean=-10, head=(11.0, -18.0))
    d1 = B(face="dead", lean=10, body_dy=4.0, head=(13.0, -8.0), legs4=[(-10.0, 0.0), (-7.0, -2.0), (5.0, 0.0), (9.0, -2.0)], squash=1.0)
    d2 = _behemoth_corpse(0)
    corpse = _behemoth_corpse(1)
    knock = B(face="roar", lean=-10, head=(11.0, -17.0))
    anims = [("Idle", idle, [0.18, 0.15, 0.18, 0.15]), ("Run", run, [0.08] * 6),
             ("Hook", hk, [0.12, 0.12, 0.05, 0.08, 0.1, 0.12, 0.12]),
             ("Charge", ch, [0.12, 0.12, 0.12, 0.06, 0.06, 0.06, 0.06, 0.06, 0.12, 0.14])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("SylBriarBehemoth", anims, outdir, scale=4)


def _behemoth_corpse(stage):
    r = Rig()
    r.ell(-2.0, -5.0, 12.0, 4.6, "bark", 0.0)
    r.ell(5.0, -5.5, 7.0, 5.0, "bark", 0.05)
    for k in range(7):
        thorn(r, -11.0 + k * 3.2, -9.0 - (k % 2), -100 + k * 6, 3.0 - stage * 0.5, 0.3, tip="blood")
    for (x, up) in ((-8.0, 3.0), (-4.0, 4.0), (5.0, 3.0)):
        r.tube([(x, -7.0), (x + 1.0, -8.0 - up)], [2.0, 1.4], "bark", -0.3)
    boar_head(r, 10.0, -4.0 + stage, "dead", z=1.0, tilt=30)
    if stage == 0: dust_puff(r, 0.0, 0, 1, 2.0)
    return r.resolve()


# ================================================================== BRIAR CHAMPION: woven briar, a thorn lance, a crown of roses
CHAMP_LEG = {"k": ("bramble", 0), "g": ("bramble", 2), "G": ("bramble", 3), "H": ("bramble", 4), "m": ("chitin", 0),
             "E": ("glowg", 4), "e": ("glowg", 3), "r": ("blood", 2), "R": ("blood", 3), "P": ("blood", 4), "t": ("thorn", 3)}


CHAMP_HEAD = {
    # pivot (3, 8): the neck. A great helm of woven living bramble, a crown of roses, a dark visor slit lit green
    "calm": "\n.RP.RP.\nrRRrRRr\ngGHHHGg\ngHHHHGk\nkmmmmmk\nkmEmEmk\ngGGtGGk\n.gGGGk.\n..gkk..\n",
    "roar": "\n.RP.RP.\nrRRrRRr\ngGHHHGg\ngHHHHGk\nkmmmmmk\nkEEmEEk\ngGmmmGk\n.gGGGk.\n..gkk..\n",
    "dead": "\n.......\n.r..r..\ngGHHHG.\ngHHHHGk\nkmmmmmk\nkmmmmmk\ngGGGGGk\n.gGGGk.\n..gkk..\n",
}


LANCE0, LANCE_STEP = 20.0, 6.0


def lance(r, hx, hy, ang, ln, z, grown=0):
    a = math.radians(ang); c, s = math.cos(a), math.sin(a)
    # a thick shaft of knotted thornwood wrapped in living bramble, a long thorn for its point
    r.tube([(hx - c * 5.0, hy - s * 5.0), (hx + c * ln * 0.55, hy + s * ln * 0.55), (hx + c * (ln - 3.0), hy + s * (ln - 3.0))],
           [2.2, 1.8, 1.4], "bark", z, bias=0.08)
    for k in range(int(ln / 3.5)):
        f = (k + 0.5) * 3.5
        r.line(hx + c * f - s * 1.6, hy + s * f + c * 1.6, hx + c * (f + 1.6) + s * 1.6, hy + s * (f + 1.6) - c * 1.6, "bramble", z + 0.02, tone=3)
    for k in range(int(ln / 4.5)):
        f = 3.0 + k * 4.5
        side = 1 if k % 2 else -1
        thorn(r, hx + c * f - s * side * 1.8, hy + s * f + c * side * 1.8, ang + side * 70 - 20, 2.6, z + 0.03)
    tip0 = (hx + c * (ln - 4.0), hy + s * (ln - 4.0))
    r.poly([(tip0[0] - s * 1.6, tip0[1] + c * 1.6), (hx + c * (ln + 1.0), hy + s * (ln + 1.0)), (tip0[0] + s * 1.6, tip0[1] - c * 1.6)],
           "thorn", z + 0.04, normal=(-0.4, -0.6, 0.7))
    r.dot(hx + c * (ln + 1.0), hy + s * (ln + 1.0), "blood", 3, z + 0.05)
    # vamplate of knotted root at the grip
    r.ell(hx + c * 1.5, hy + s * 1.5, 2.2, 2.8, "bramble", z + 0.05, ang=ang, bias=0.15)
    # the fresh green growth: one bright bud per grown length
    for g in range(grown):
        f = ln - 6.0 * g - 5.0
        r.dot(hx + c * f - s * 2.0, hy + s * f + c * 2.0, "moss", 4, z + 0.06)
        leaf(r, hx + c * f + s * 1.6, hy + s * f - c * 1.6, ang - 60, 2.4, z + 0.06, mat="moss", w=1.0)


def champion(lean=0.0, bob=0.0, feet=((-4.0, 0.0), (4.0, 0.0)), hand=(8.0, -17.0), hand2=(-5.0, -15.0), lance_ang=-6.0, grown=0,
             face="calm", smear=None, spark=None, extra=None, knee=1, reach=0.0, head_d=(0.0, 0.0)):
    r = Rig()
    hip = (0.0, -13.0 + bob)
    T = Xf(lean, hip)
    legs(r, hip, feet, 6.6, 6.2, "bark", rad=(1.9, 1.5), foot="bramble", knee=knee, spread=2.0, foot_len=3.0)
    # bramble greaves on the shins
    for k, f in enumerate(feet):
        z = 1.1 * (k * 2 - 1) + 0.05
        r.tube([(f[0] - 0.4, f[1] - 2.0), (f[0] - 0.1, f[1] - 6.5)], [1.8, 1.6], "bramble", z, bias=0.1 if k else -0.2)
        thorn(r, f[0] + 1.2, f[1] - 5.0, -20, 1.6, z + 0.02)
    # a cape of leaves behind, its hem ragged with thorns
    cp = [T(-6.0, hip[1] - 13.0), T(3.0, hip[1] - 13.0), T(-2.0, hip[1] + 8.0), T(-6.0, hip[1] + 9.0), T(-10.0 - lean * 0.05, hip[1] + 7.0)]
    r.poly(cp, "rot", -2.0, normal=(-0.4, -0.2, 0.9), curve=0.5)
    for k in range(4):
        thorn(r, *T(-9.5 + k * 2.2, hip[1] + 7.5 + (k % 2)), 100 - k * 8, 1.5, -1.9)
    # far arm in bramble vambraces
    arm(r, T(-5.0, hip[1] - 11.6), hand2, 5.0, 4.8, "bramble", -1.0, rad=(1.8, 1.5, 1.4), bend=1, bias=-0.3)
    # cuirass of living bramble plate: woven bands, a thorned rim
    tp = [T(-6.6, hip[1] - 13.4), T(6.4, hip[1] - 13.4), T(5.0, hip[1] + 1.0), T(-5.2, hip[1] + 1.0)]
    r.poly(tp, "bramble", 0.0, normal=(-0.3, -0.3, 0.9), curve=0.7)
    for k in range(5):
        y = hip[1] - 11.4 + k * 2.6
        r.line(*T(-5.6, y), *T(5.4, y + 1.2 * (1 if k % 2 else -1)), "bark", 0.05, tone=2 if k % 2 else 1)
    r.poly([T(-1.6, hip[1] - 12.0), T(1.8, hip[1] - 12.0), T(1.2, hip[1] - 4.0), T(0.0, hip[1] - 2.6), T(-1.2, hip[1] - 4.0)], "blood", 0.08,
           normal=(-0.3, -0.4, 0.8))
    for side in (-1, 1):
        r.ell(*T(side * 6.2, hip[1] - 12.4), 3.6, 3.0, "bramble", 0.2, bias=0.2)
        for k in range(3):
            thorn(r, *T(side * (4.8 + k * 1.4), hip[1] - 14.6 + k * 0.8), -90 + side * (20 + k * 25), 2.4, 0.3)
    # tabard of rose petals hanging from the belt
    r.line(*T(-5.0, hip[1] + 0.4), *T(5.0, hip[1] + 0.4), "bark", 0.25, tone=1)
    r.poly([T(-4.0, hip[1] + 0.6), T(4.0, hip[1] + 0.6), T(3.2, hip[1] + 7.0), T(0.0, hip[1] + 8.0), T(-3.2, hip[1] + 7.0)], "blood", 0.3,
           normal=(-0.2, -0.2, 0.9))
    hx, hy = T(0.6 + head_d[0], hip[1] - 13.6 + head_d[1])
    r.stamp(CHAMP_HEAD[face], hx, hy, 0.6, CHAMP_LEG, pivot=(3, 8))
    # near arm and the lance (couched along the forearm)
    arm(r, T(5.0, hip[1] - 11.6), hand, 5.0, 4.8, "bramble", 2.2, rad=(1.9, 1.6, 1.5), bend=-1)
    lance(r, hand[0], hand[1], lance_ang, LANCE0 + LANCE_STEP * grown + reach, 2.6, grown)
    r.ell(hand[0], hand[1], 1.6, 1.6, "bramble", 2.9, bias=0.15)
    smears(r, smear); sparks(r, spark)
    if extra: extra(r)
    return r.resolve()


def champion_sheet(outdir):
    C = champion
    anims = []
    for g in range(4):
        sfx = "" if g == 0 else str(g)
        idle = [C(grown=g, bob=[0, 0.4, 0.8, 0.4][i], hand=(8.0, -17.0 + [0, 0.4, 0.8, 0.4][i]), lance_ang=-6 + [0, 1, 2, 1][i])
                for i in range(4)]
        run = []
        for i in range(6):
            ph = i / 6 * math.tau
            run.append(C(grown=g, lean=6, bob=-1.0 * abs(math.sin(ph)), hand=(8.5, -16.0 + 0.6 * math.sin(ph)), lance_ang=-2 + 3 * math.sin(ph),
                         hand2=(-4.5 - 1.6 * math.sin(ph), -14.0),
                         feet=((-4.0 + 3.6 * math.cos(ph), -max(0, 2.0 * math.sin(ph))), (4.0 - 3.6 * math.cos(ph), -max(0, -2.0 * math.sin(ph))))))
        # Thrust (7): draws the lance back (0-1), THRUSTS (2-3: tip at hand + lance length; hit box along the shaft), holds, recover
        th = [C(grown=g, hand=(4.0, -16.0), lance_ang=-4, lean=-6, face="roar"), C(grown=g, hand=(1.0, -15.5), lance_ang=-2, lean=-10, face="roar"),
              C(grown=g, hand=(11.0, -15.0), lance_ang=0, lean=8, face="roar", smear=[("line", [(-2, -14), (8, -14)], "thorn", 2)]),
              C(grown=g, hand=(12.0, -15.0), lance_ang=0, lean=10, face="roar", spark=[(12.0 + LANCE0 + LANCE_STEP * g, -15.0, 2)]),
              C(grown=g, hand=(10.0, -15.5), lance_ang=-2, lean=6), C(grown=g, hand=(9.0, -16.5), lance_ang=-4, lean=2), C(grown=g)]
        # Lunge (8): PLANTS its feet, lance couched (0-3, 0.5 s), LUNGES (4: tip reaches lance length + 20), holds (5), recover
        ln = [C(grown=g, hand=(3.0, -15.0), lance_ang=0, lean=-8, feet=((-7.0, 0.0), (5.0, 0.0)), bob=1.0, face="roar"),
              C(grown=g, hand=(2.0, -14.5), lance_ang=0, lean=-10, feet=((-7.0, 0.0), (5.0, 0.0)), bob=1.4, face="roar",
                extra=lambda r: soil(r, 5.0, 0.0, 0)),
              C(grown=g, hand=(1.5, -14.5), lance_ang=0, lean=-12, feet=((-7.0, 0.0), (5.0, 0.0)), bob=1.6, face="roar"),
              C(grown=g, hand=(1.0, -14.5), lance_ang=0, lean=-12, feet=((-7.0, 0.0), (5.0, 0.0)), bob=1.6, face="roar",
                extra=lambda r: motes(r, 10.0, -15.0, 0, n=5, mat="glowg", spread=4.0)),
              C(grown=g, hand=(14.0, -14.0), lance_ang=0, lean=18, feet=((-4.0, 0.0), (10.0, 0.0)), face="roar", reach=6.0,
                smear=[("line", [(-4, -14), (12, -14)], "thorn", 2), ("line", [(-2, -12), (10, -12)], "moss", 1)],
                spark=[(14.0 + LANCE0 + LANCE_STEP * g + 6.0, -14.0, 1)]),
              C(grown=g, hand=(13.0, -14.0), lance_ang=0, lean=14, feet=((-4.0, 0.0), (10.0, 0.0)), reach=6.0),
              C(grown=g, hand=(9.0, -15.5), lance_ang=-3, lean=4, feet=((-4.0, 0.0), (6.0, 0.0))), C(grown=g)]
        anims += [("Idle" + sfx, idle, [0.18, 0.15, 0.18, 0.15]), ("Run" + sfx, run, [0.08] * 6),
                  ("Thrust" + sfx, th, [0.12, 0.1, 0.05, 0.08, 0.1, 0.12, 0.12]),
                  ("Lunge" + sfx, ln, [0.12, 0.12, 0.13, 0.13, 0.06, 0.12, 0.12, 0.12])]
        if g == 0: base_idle = idle[0]
    d0 = C(face="roar", lean=-14, hand=(4.0, -18.0), lance_ang=-40)
    d1 = C(face="dead", lean=-26, bob=3.0, hand=(2.0, -9.0), lance_ang=30, feet=((-4.0, 0.0), (5.0, -1.0)))
    d2 = _champ_corpse(0)
    corpse = _champ_corpse(1)
    knock = C(face="roar", lean=-16, hand=(5.0, -18.0), lance_ang=-25)
    anims += tail_anims(base_idle, [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("SylBriarChampion", anims, outdir, scale=3)


def _champ_corpse(stage):
    r = Rig()
    r.poly([(-8.0, -6.0), (6.0, -6.0), (6.0, 0.0), (-8.0, 0.0)], "bramble", 0.0, curve=0.5)
    for k in range(3):
        r.line(-7.0, -5.0 + k * 1.6, 5.0, -4.0 + k * 1.6, "bark", 0.05, tone=1)
    r.stamp(CHAMP_HEAD["dead"], -11.0, 0.0 + (0 if stage else 1), 0.4, CHAMP_LEG, pivot=(3, 8))
    lance(r, 4.0, -2.0, 4.0, 20.0, 0.5)
    for (x, y) in ((-14.0, -1.0), (-9.0, 0.0)):
        r.dot(x, y, "blood", 3, 0.6)
    if stage == 0: dust_puff(r, 0.0, 0, 1, 1.8)
    return r.resolve()


# ================================================================== PUFFBALL BRUTE: a giant puffball with arms, a slit of a mouth
PUFF_LEG = {"k": ("spore", 0), "d": ("spore", 1), "s": ("spore", 2), "m": ("chitin", 0), "e": ("glowg", 3), "E": ("glowg", 4),
            "w": ("mould", 3), "W": ("mould", 4)}


def puffball(sq=0.0, bob=0.0, lean=0.0, hands=((11.0, -10.0), (-10.0, -9.0)), feet=((-5.0, 0.0), (5.0, 0.0)), face="calm",
             air=0.0, smear=None, spark=None, extra=None, wall=0.0, cracks=1):
    """One fungus: a giant puffball for a body on stubby mould legs, with stubby arms, a face and spore vents on top.
    sq > 0 squashes flat, < 0 stretches tall. air lifts it off the floor. wall > 0 flattens it against a wall behind it."""
    r = Rig()
    R = 12.0
    rx, ry = R * (1 + 0.35 * sq) * (1 - 0.35 * wall), R * (1 - 0.35 * sq) * (1 + 0.1 * wall)
    cx, cy = -wall * 3.0, -ry - 2.2 + bob - air
    T = Xf(lean, (cx, cy))
    if air < 1.0:
        for k, f in enumerate(feet):
            top = T(cx + (-4.5 if k == 0 else 4.5), cy + ry - 3.0)
            r.tube([top, (f[0], f[1] - 1.0)], [2.6, 2.4], "mould", -0.5 if k == 0 else 0.5, bias=-0.3 if k == 0 else -0.1)
            r.ell(f[0] + 0.4, f[1] - 0.9, 2.6, 1.1, "spore", 0.6 if k else -0.4)
    # far arm: a stubby mould limb
    sh2 = T(cx - rx + 2.5, cy + 1.0)
    arm(r, sh2, hands[1], 4.2, 3.8, "mould", -1.0, rad=(2.2, 1.9, 1.7), bend=1, bias=-0.35)
    r.ell(hands[1][0], hands[1][1], 2.2, 2.0, "mould", -0.9, bias=-0.3)
    # the ball: mould-white skin browning to spore at the base, cracked
    r.ell(cx, cy, rx, ry, "mould", 0.0, bias=0.1)
    r.ell(cx + 0.5, cy + ry * 0.62, rx * 0.8, ry * 0.36, "spore", 0.02, bias=0.1, clip=lambda x, y: y > cy + ry * 0.4)
    cr = [((-5, -7), (-3, -4), (-5, -2)), ((3, -9), (5, -6), (4, -4), (6, -2)), ((-2, 2), (0, 4), (-1, 6))][:2 + cracks]
    for pts in cr:
        r.polyline([T(cx + x * rx / R, cy + y * ry / R) for (x, y) in pts], "spore", 0.05, tone=1)
    for (x, y) in ((-6, -3), (6, 1), (-3, 5), (2, -6)):
        r.dot(*T(cx + x * rx / R, cy + y * ry / R), "mould", 4, 0.06)
    # spore vents on its crown, each breathing a wisp
    for k, (x, a) in enumerate(((-4.5, 0), (0.5, 2), (5.0, 1))):
        vx, vy = T(cx + x * rx / R, cy - ry * 0.86 + abs(x) * 0.18)
        r.ell(vx, vy, 1.4, 0.8, "spore", 0.1, flat=0)
        r.dot(vx, vy - 0.4, "spore", 1, 0.11)
        r.dot(vx + (1 if k % 2 else -1), vy - 2 - a % 2, "sporec", 3, 0.2)
        r.dot(vx, vy - 3 - a, "sporec", 2, 0.2)
    # face: two pinprick eyes and a slit of a mouth
    fx, fy = T(cx + 5.0 * rx / R, cy - 1.0)
    if face == "calm":
        r.stamp("\ne..e\n....\nmmmm\n", fx, fy, 0.2, PUFF_LEG, pivot=(2, 1))
    elif face == "roar":
        r.stamp("\nE..E\n.mm.\nmddm\n.mm.\n", fx, fy, 0.2, PUFF_LEG, pivot=(2, 1))
    else:
        r.stamp("\nm..m\n....\n.mm.\n", fx, fy, 0.2, PUFF_LEG, pivot=(2, 1))
    # near arm
    sh1 = T(cx + rx - 3.0, cy + 2.0)
    arm(r, sh1, hands[0], 4.2, 3.8, "mould", 2.0, rad=(2.4, 2.1, 1.9), bend=-1, bias=-0.1)
    r.ell(hands[0][0], hands[0][1], 2.5, 2.2, "mould", 2.1, bias=0.0)
    r.dot(hands[0][0] + 1, hands[0][1] + 1, "spore", 1, 2.15)
    smears(r, smear); sparks(r, spark)
    if extra: extra(r)
    return r.resolve()


def puffball_sheet(outdir):
    P = puffball
    idle = [P(sq=[0, 0.04, 0.08, 0.04][i], hands=((11.0, -10.0 + [0, 0.4, 0.8, 0.4][i]), (-10.0, -9.0 + [0, 0.4, 0.8, 0.4][i])))
            for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        run.append(P(sq=0.08 * math.cos(ph * 2), lean=6, bob=-0.8 * abs(math.sin(ph)), hands=((11.0, -9.0 + math.sin(ph)), (-9.0, -9.0 - math.sin(ph))),
                     feet=((-5.0 + 3.0 * math.cos(ph), -max(0, 1.6 * math.sin(ph))), (5.0 - 3.0 * math.cos(ph), -max(0, -1.6 * math.sin(ph))))))
    # Slam (7): both fists up (0-1), SLAM (2: fists land at (13, -1), the spore ring at (16, 0)), the ring spreads (3), recover
    sl = [P(sq=-0.1, hands=((8.0, -26.0), (-4.0, -27.0)), face="roar"), P(sq=-0.16, hands=((6.0, -29.0), (-2.0, -29.0)), face="roar", bob=-0.6),
          P(sq=0.18, lean=8, hands=((14.0, -2.0), (10.0, -2.0)), face="roar", spark=[(14.0, -1.0, 1)],
            extra=lambda r: dirt_ring(r, 15.0, 0.0, 6.0, 0)),
          P(sq=0.12, lean=6, hands=((14.0, -2.0), (10.0, -2.0)), face="roar", extra=lambda r: dirt_ring(r, 15.0, 0.0, 10.0, 1)),
          P(sq=0.05, hands=((12.0, -6.0), (-6.0, -6.0))), P(hands=((11.0, -9.0), (-9.0, -9.0))), P()]
    # Bounce (9): SQUASHES flat (0-1, 0.4 s), LAUNCHES (2), in the air, round and untouchable (3-5), LANDS in a spore ring (6),
    # wobbles (7-8)
    bn = [P(sq=0.35, face="roar", hands=((13.0, -4.0), (-12.0, -4.0))), P(sq=0.5, face="roar", hands=((14.0, -3.0), (-13.0, -3.0)), bob=0.5),
          P(sq=-0.3, air=4.0, face="roar", hands=((8.0, -30.0), (-6.0, -30.0)), extra=lambda r: soil(r, 0.0, 0.0, 0, 1.6)),
          P(sq=-0.15, air=9.0, face="roar", hands=((9.0, -32.0), (-8.0, -32.0))), P(sq=0.0, air=10.0, face="roar", hands=((11.0, -26.0), (-10.0, -26.0))),
          P(sq=0.05, air=5.0, face="roar", hands=((12.0, -16.0), (-11.0, -16.0))),
          P(sq=0.45, face="roar", hands=((14.0, -3.0), (-13.0, -3.0)), extra=lambda r: dirt_ring(r, 0.0, 0.0, 12.0, 0)),
          P(sq=-0.1, extra=lambda r: dirt_ring(r, 0.0, 0.0, 16.0, 2)), P(sq=0.05)]
    # WallSquash (3): knocked flat against a wall behind it, then springs off it at the hero
    ws = [P(wall=0.5, face="roar", hands=((8.0, -12.0), (-8.0, -14.0))), P(wall=0.7, face="roar", hands=((7.0, -12.0), (-8.0, -16.0))),
          P(wall=-0.3, lean=10, face="roar", hands=((14.0, -10.0), (-6.0, -12.0)), smear=[("line", [(-14, -16), (-8, -16)], "mould", 2)])]
    d0 = P(face="roar", sq=-0.15, lean=-12)
    d1 = P(face="dead", sq=0.4, cracks=3, extra=lambda r: puff(r, 0.0, -16.0, 6.0, 6.0, "sporec", 0, 4, 6))
    d2 = P(face="dead", sq=0.75, cracks=3, extra=lambda r: puff(r, 0.0, -14.0, 8.0, 6.0, "sporec", 2, 4, 6))
    corpse = _puff_corpse()
    knock = P(face="roar", sq=-0.1, lean=-14)
    anims = [("Idle", idle, [0.18, 0.15, 0.18, 0.15]), ("Run", run, [0.08] * 6),
             ("Slam", sl, [0.14, 0.12, 0.05, 0.1, 0.12, 0.12, 0.12]),
             ("Bounce", bn, [0.2, 0.2, 0.06, 0.08, 0.08, 0.08, 0.06, 0.12, 0.12]),
             ("WallSquash", ws, [0.08, 0.08, 0.06])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("SylPuffball", anims, outdir, scale=4)


def _puff_corpse():
    r = Rig()
    r.ell(0.0, -3.4, 13.0, 3.4, "mould", 0.0)
    r.ell(1.0, -1.6, 10.0, 1.6, "spore", 0.02)
    for x in (-7.0, -1.0, 6.0):
        r.polyline([(x, -6.0), (x + 1, -4.0), (x, -2.0)], "spore", 0.05, tone=1)
    r.tube([(10.0, -2.0), (15.0, -1.0)], [2.0, 1.8], "mould", 0.3)
    r.tube([(-10.0, -2.0), (-15.0, -1.0)], [2.0, 1.8], "mould", -0.3)
    puff(r, 0.0, -7.0, 3.0, 1.0, "sporec", 2, 3, 4)
    return r.resolve()


# ================================================================== CORDYCEPS SAINT: a saintly corpse crowned with fungal antlers
SAINT_LEG = {"k": ("corpse", 0), "d": ("corpse", 1), "c": ("corpse", 2), "C": ("corpse", 3), "m": ("chitin", 0), "o": ("cordy", 2),
             "O": ("cordy", 3), "Q": ("cordy", 4), "g": ("gold", 3), "G": ("gold", 4), "e": ("glowg", 4)}
SAINT_HEAD = {
    # pivot (3, 7): the neck. A gaunt grey face under a gold circlet, orange stalks splitting the brow
    "calm": """
.O.o.O.
.oOoOo.
gGgggGg
.cCCCc.
dcmCmCk
dCCCCCk
.dcmcdk
..dkk..
""",
    "cast": """
QO.O.OQ
.oOoOo.
gGgggGg
.cCCCc.
dceCeCk
dCCCCCk
.dcmcdk
..dmk..
""",
    "dead": """
.......
.o...o.
gGgggGg
.cCCCc.
dmCCmCk
dCCCCCk
.dcmcdk
..dkk..
""",
}


def stalk(r, x, y, ang, ln, z, branches=2, swell=1.0, seed=1, caps=True):
    """A cordyceps stalk: an orange tine with branches, amber fruiting caps on the tips."""
    pts = chain(x, y, [(ln * 0.5, ang), (ln * 0.5, ang + 10)])
    r.tube(pts, [1.1 * swell, 0.85 * swell, 0.6], "cordy", z, bias=0.05)
    for b in range(branches):
        f = 0.35 + 0.3 * b
        bx, by = lerp(pts[0][0], pts[-1][0], f), lerp(pts[0][1], pts[-1][1], f)
        side = 1 if (b + seed) % 2 else -1
        bp = chain(bx, by, [(ln * 0.35, ang + side * 40)])
        r.tube(bp, [0.6, 0.5], "cordy", z + 0.01)
        r.ell(bp[-1][0], bp[-1][1], 0.9, 0.9, "amber", z + 0.02, bias=0.4)
    tx, ty = pts[-1]
    if caps:
        # a little fruiting cap, lit amber on top, a dark gill under it
        r.ell(tx, ty - 0.3, 1.9 * swell, 1.2 * swell, "amber", z + 0.03, bias=0.3, clip=lambda px, py: py <= ty + 0.2)
        r.line(tx - 1.6 * swell, ty + 0.4, tx + 1.6 * swell, ty + 0.4, "cordy", z + 0.031, tone=1)
    else:
        r.ell(tx, ty, 1.2 * swell, 1.4 * swell, "cordy", z + 0.02, bias=0.4)


def saint(lean=0.0, bob=0.0, hand=(7.0, -19.0), hand2=(-6.0, -17.0), face="calm", pulse=0.0, hem=0.0, smear=None, spark=None,
          extra=None, spine=None, sink=0.0, stalks=1.0):
    r = Rig()
    hip = (0.0, -11.0 + bob + sink)
    T = Xf(lean, (0.0, 0.0))
    # a thicket of stalks from the back (behind)
    for k, (dx, a, ln) in enumerate(((-3.0, -140, 10.0), (-1.5, -115, 9.0), (0.5, -95, 7.0), (2.0, -60, 9.5))):
        stalk(r, *T(dx, hip[1] - 12.0), a + pulse * 4 * (1 if k % 2 else -1), ln * stalks, -1.5 + k * 0.01, branches=2, swell=1 + 0.15 * pulse, seed=k)
    # robe: a saint's habit gone to rot: white above, stained brown and orange from the hem up
    rp = [T(-3.6, hip[1] - 14.0), T(3.6, hip[1] - 14.0), T(5.0, hip[1] - 4.0), T(8.4 + hem, hip[1] + 11.0), T(3.0, hip[1] + 12.0),
          T(-1.0, hip[1] + 11.0), T(-5.0, hip[1] + 12.0), T(-8.6 + hem, hip[1] + 11.0), T(-5.0, hip[1] - 4.0)]
    r.poly(rp, "mould", 0.0, normal=(-0.25, -0.2, 0.9), curve=0.8)
    stain_top = lambda x: hip[1] + 3.0 + 2.2 * math.sin(x * 0.9) + 1.4 * math.sin(x * 2.3 + 1)
    r.poly([T(-9.0 + hem, hip[1] + 12.0), T(9.0 + hem, hip[1] + 12.0)] + [T(x, stain_top(x)) for x in (8.0, 5.0, 2.0, -1.0, -4.0, -7.0)],
           "spore", 0.03, normal=(-0.25, -0.2, 0.9))
    for k in (-1, 1):
        r.line(*T(k * 1.8, hip[1] - 9.0), *T(k * 4.4 + hem, hip[1] + 11.0), "mould", 0.05, tone=1)
    r.poly([T(-1.2, hip[1] - 13.6), T(1.4, hip[1] - 13.6), T(1.6, hip[1] + 6.0), T(-1.4, hip[1] + 6.0)], "gold", 0.08, normal=(-0.3, -0.3, 0.9))
    # orange mycelium creeping up the robe, fruiting in little amber caps
    for k, x0 in enumerate((-6.0, -3.0, 2.5, 6.0)):
        pts = [T(x0 + hem, hip[1] + 11.0), T(x0 * 0.8, hip[1] + 5.0 - k % 2), T(x0 * 0.6 + (1 if k % 2 else -1), hip[1] - 1.0 - 2 * (k % 2))]
        r.polyline(pts, "cordy", 0.1, tone=3 if k % 2 else 2)
        r.ell(*pts[-1], 1.2, 0.8, "amber", 0.11, bias=0.3)
    for (x, y) in ((-4.0, 7.0), (3.0, 9.0), (6.0, 6.0), (-6.0, 10.0)):
        r.dot(*T(x, hip[1] + y), "cordy", 3, 0.12)
    # far arm, sleeve
    arm(r, T(-3.2, hip[1] - 12.4), hand2, 4.6, 4.4, "mould", -0.8, rad=(1.4, 1.6, 1.8), bend=1, bias=-0.3)
    r.ell(hand2[0], hand2[1], 1.0, 1.0, "corpse", -0.75, bias=-0.2)
    # stalks bursting out of the shoulders
    for side in (-1, 1):
        sx, sy = T(side * 3.6, hip[1] - 13.4)
        r.ell(sx, sy, 2.0, 1.6, "cordy", 0.3, bias=0.1)
        stalk(r, sx, sy, -90 + side * 55 + pulse * 3 * side, 8.0 * stalks, 0.32, branches=1, swell=1.1 + 0.15 * pulse, seed=side + 4)
    hx, hy = T(0.4, hip[1] - 13.8)
    r.stamp(SAINT_HEAD[face], hx, hy, 0.6, SAINT_LEG, pivot=(3, 7))
    # an antler of stalks bursting from the head (in front)
    for k, (dx, a, ln) in enumerate(((-2.0, -125, 6.5), (-0.5, -100, 5.0), (1.0, -78, 5.5), (2.5, -55, 6.5))):
        stalk(r, hx + dx, hy - 6.0, a + pulse * 5 * (1 if k % 2 else -1), ln * stalks, 0.7 + k * 0.01, branches=1, swell=1 + 0.2 * pulse, seed=k + 3)
    arm(r, T(3.2, hip[1] - 12.4), hand, 4.6, 4.4, "mould", 2.0, rad=(1.4, 1.6, 1.9), bend=-1)
    r.ell(hand[0], hand[1], 1.0, 1.0, "corpse", 2.1, bias=0.1)
    r.dot(hand[0] + 0.5, hand[1] - 1.0, "cordy", 3, 2.15)
    if spine:
        x0, y0, x1, y1 = spine
        r.line(x0, y0, x1, y1, "cordy", 5.0, tone=3); r.dot(x1, y1, "amber", 4, 5.1)
    smears(r, smear); sparks(r, spark)
    if extra: extra(r)
    return r.resolve()


def saint_sheet(outdir):
    S = saint
    idle = [S(bob=[0, -0.4, -0.8, -0.4][i], pulse=[0, 0.5, 1, 0.5][i], hem=[0, 0.3, 0.6, 0.3][i],
              hand=(7.0, -19.0 + [0, -0.4, -0.8, -0.4][i])) for i in range(4)]
    run = [S(lean=6, bob=-0.6 * abs(math.sin(i / 6 * math.tau)), hem=-1.0 + 0.6 * math.sin(i / 6 * math.tau), pulse=0.3,
             hand=(6.0, -18.0), hand2=(-6.0, -16.0)) for i in range(6)]
    # Flick (6): draws a spine from its stalks (0-1), FLICKS it (2: the spine leaves the fingers at (11, -22)), recover
    fl = [S(hand=(3.0, -28.0), face="cast", pulse=1.0), S(hand=(1.0, -30.0), face="cast", pulse=1.5, lean=-6),
          S(hand=(11.0, -22.0), face="cast", lean=8, spine=(11.0, -22.0, 16.0, -22.0), smear=[("arc", 5.0, -24.0, 7.0, -120, -10, "cordy", 2)]),
          S(hand=(10.0, -21.0), lean=6), S(hand=(8.0, -20.0), lean=2), S()]
    # Infect (8): raises both hands, the stalks swell and pulse (0-3), DRIVES spines out (4: they leave at (0, -38)), recover (5-7)
    inf = [S(hand=(6.0, -26.0), hand2=(-6.0, -26.0), face="cast", pulse=1.0), S(hand=(6.0, -29.0), hand2=(-6.0, -29.0), face="cast", pulse=2.0, bob=-0.6),
           S(hand=(6.0, -30.0), hand2=(-6.0, -30.0), face="cast", pulse=2.5, bob=-1.0, extra=lambda r: motes(r, 0.0, -38.0, 0, n=6, mat="cordy", spread=6.0)),
           S(hand=(6.0, -30.0), hand2=(-6.0, -30.0), face="cast", pulse=3.0, bob=-1.0, stalks=1.1),
           S(hand=(10.0, -24.0), hand2=(-10.0, -24.0), face="cast", pulse=0.0, stalks=1.15,
             extra=lambda r: [r.line(0.0, -38.0, x, y, "cordy", 6.0, tone=3) for (x, y) in ((-12.0, -40.0), (12.0, -40.0), (0.0, -40.0))]),
           S(hand=(9.0, -22.0), hand2=(-9.0, -21.0), pulse=0.5), S(hand=(8.0, -20.0)), S()]
    d0 = S(face="cast", lean=-12, pulse=2.0)
    d1 = S(face="dead", lean=-24, sink=3.0, stalks=0.8, hand=(3.0, -12.0), hand2=(-8.0, -11.0))
    d2 = _saint_corpse(0)
    corpse = _saint_corpse(1)
    knock = S(face="cast", lean=-14, hand=(4.0, -21.0), hand2=(-7.0, -19.0))
    anims = [("Idle", idle, [0.18, 0.15, 0.18, 0.15]), ("Run", run, [0.08] * 6),
             ("Flick", fl, [0.12, 0.12, 0.05, 0.1, 0.1, 0.12]),
             ("Infect", inf, [0.12, 0.12, 0.12, 0.12, 0.06, 0.12, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("SylCordyceps", anims, outdir, scale=3)


def _saint_corpse(stage):
    r = Rig()
    r.poly([(-10.0, -5.0), (8.0, -5.5), (10.0, 0.0), (-11.0, 0.0)], "mould", 0.0, curve=0.5)
    r.poly([(-8.0, -4.0), (6.0, -4.5), (6.0, -3.0), (-8.0, -2.6)], "gold", 0.05)
    r.stamp(SAINT_HEAD["dead"], 12.0, 0.0, 0.6, SAINT_LEG, pivot=(3, 7))
    for k, a in enumerate((-60, -20, 20)):
        stalk(r, 13.0 + k, -6.0, a - 30, 7.0 - stage, 0.7 + k * 0.01, branches=1, seed=k)
    if stage == 0: dust_puff(r, 0.0, 0, 1, 1.8)
    return r.resolve()


# ------------------------------------------------------------------ the Shambler: an infected corpse fighting on
def shambler(lean=0.0, bob=0.0, feet=((-2.5, 0.0), (2.5, 0.0)), sink=0.0, puff_k=None, stalk_k=1.0, extra=None, head_dx=0.0):
    r = Rig()
    hip = (0.0, -4.6 + bob + sink)
    T = Xf(lean, hip)
    legs(r, hip, feet, 2.4, 2.2, "corpse", rad=(1.1, 0.9), foot="corpse", spread=1.0)
    r.ell(*T(0.0, hip[1] - 3.4), 3.6, 3.8, "corpse", 0.0, bias=0.05)
    r.poly([T(-3.4, hip[1] - 2.0), T(3.4, hip[1] - 2.0), T(3.8, hip[1] + 1.4), T(-3.6, hip[1] + 1.4)], "spore", 0.1)
    for k in (-1, 1):
        r.tube([T(k * 3.0, hip[1] - 6.6), T(k * 4.4 + 1.0, hip[1] - 2.0)], [1.0, 0.8], "corpse", 0.5 * k, bias=-0.2 if k < 0 else 0.0)
    hx, hy = T(1.0 + head_dx, hip[1] - 6.6)
    r.ell(hx, hy, 2.6, 2.2, "corpse", 0.3, bias=0.1)
    r.dot(hx + 1, hy, "chitin", 0, 0.4); r.dot(hx - 0.5, hy, "chitin", 0, 0.4)
    for k, a in enumerate((-125, -90, -55)):
        stalk(r, hx - 1 + k, hy - 1.5, a, 2.4 * stalk_k, 0.6 + 0.01 * k, branches=1, seed=k)
    if puff_k is not None:
        puff(r, hx + 5.0, hy + 2.0, 2.6, 5.0, "sporec", puff_k, 3, 5)
    if extra: extra(r)
    return r.resolve()


def shambler_sheet(outdir):
    S = shambler
    idle = [S(lean=[-6, -2, 4, -2][i], bob=[0, 0.2, 0.4, 0.2][i], head_dx=[0, -0.5, 0.5, 0][i]) for i in range(4)]
    run = [S(lean=10 + 6 * math.sin(i / 6 * math.tau), bob=-0.6 * abs(math.sin(i / 6 * math.tau)),
             feet=((-2.5 + 2.2 * math.cos(i / 6 * math.tau), -max(0, 1.2 * math.sin(i / 6 * math.tau))),
                   (2.5 - 2.2 * math.cos(i / 6 * math.tau), -max(0, -1.2 * math.sin(i / 6 * math.tau))))) for i in range(6)]
    pf = [S(lean=-8), S(lean=-12, bob=0.4), S(lean=8, puff_k=0), S(lean=6, puff_k=1), S(lean=2, puff_k=2), S()]
    rise = [S(sink=4.0, lean=-30, stalk_k=1.2), S(sink=2.0, lean=-14, stalk_k=1.2), S(lean=-4)]
    # Burst (4): it swells and bursts into three seeds (the code spawns them on the last frame)
    burst = [S(lean=-6, stalk_k=1.3), S(stalk_k=1.5, extra=lambda r: motes(r, 0.0, -10.0, 0, n=6, mat="cordy", spread=4.0)),
             S(sink=2.0, stalk_k=0.6, extra=lambda r: puff(r, 0.0, -6.0, 5.0, 6.0, "sporec", 0, 5, 6)),
             _shambler_corpse()]
    knock = S(lean=-24)
    anims = [("Idle", idle, [0.14] * 4), ("Run", run, [0.08] * 6), ("Puff", pf, [0.12, 0.1, 0.06, 0.1, 0.1, 0.1]),
             ("Rise", rise, [0.1, 0.1, 0.1])]
    anims += tail_anims(idle[0], burst, [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("SylShambler", anims, outdir, scale=6)


def _shambler_corpse():
    r = Rig()
    r.ell(0.0, -1.6, 5.0, 1.6, "corpse", 0.0)
    for k, x in enumerate((-2.0, 1.0, 3.0)):
        r.ell(x, -1.0, 1.0, 1.1, "gall", 0.5 + 0.01 * k, bias=0.2); r.dot(x, -2.2, "moss", 3, 0.6)
    return r.resolve()


# ================================================================== ROT MOTHER: a towering tree-woman, a belly of rotting wood
MOTHER_LEG = {"k": ("bark", 0), "d": ("bark", 1), "b": ("bark", 2), "B": ("bark", 3), "W": ("bark", 4), "m": ("chitin", 0),
              "e": ("glowg", 3), "E": ("glowg", 4), "p": ("podf", 3), "P": ("podf", 4), "g": ("moss", 3)}


MOTHER_HEAD = {
    # pivot (3, 8): the neck. A long, fine face of pale bark, green knothole eyes, pink lips, a circlet of buds
    "calm": "\n.p.g.p.\n.gPgPg.\n.dBWBd.\ndBWWWBk\ndmEBEmk\n.dBWBk.\n.dbpbk.\n..dbk..\n...d...\n",
    "cast": "\npPgPgPp\n.gPgPg.\n.dBWBd.\ndBWWWBk\ndEEBEEk\n.dBWBk.\n.dmpmk.\n..dbk..\n...d...\n",
    "dead": "\n.......\n.......\n.dBWBd.\ndBWWWBk\ndmmBmmk\n.dBWBk.\n.dbmbk.\n..dbk..\n...d...\n",
}


def rot_bloom(r, x, y, z, s=1.0):
    """A rot bloom: four bruise-purple petals round a pink heart."""
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        r.dot(x + dx * s, y + dy * s, "bruise", 3, z)
    r.dot(x, y, "podf", 4, z + 0.01)


def rot_mother(lean=0.0, bob=0.0, hand=(9.0, -20.0), hand2=(-8.0, -19.0), face="calm", sway=0.0, buds=0, smear=None, spark=None,
               extra=None, sink=0.0, belly_glow=0):
    r = Rig()
    hip = (0.0, -12.0 + bob + sink)
    T = Xf(lean, (0.0, 0.0))
    hx, hy = T(0.4, hip[1] - 14.0)
    # long hair of hanging roots behind her, pink fruit swinging at the ends
    for k in range(6):
        side = -1 if k < 3 else 1
        x0 = hx + side * (1.5 + (k % 3) * 1.0)
        x2 = x0 + side * (2.5 + (k % 3) * 2.2) + sway
        y2 = hip[1] + 1.0 + (k % 3) * 2.0
        r.tube([(x0, hy - 5.0), (lerp(x0, x2, 0.5) + sway * 0.5, hy + 3.0), (x2, y2)], [0.9, 0.8, 0.6], "bark", -2.0 + k * 0.01,
               bias=-0.55 if side < 0 else -0.4)
        if k % 2 == 0: pod(r, x2, y2 + 3.0, 3.2, -1.9, ripe=1.0 if buds > k // 2 else 0.7)
    # the skirt of roots: a narrow bell of bark from her hips, splitting into roots that spread over the floor
    r.poly([T(-3.6, hip[1]), T(3.6, hip[1]), T(6.5 + sway * 0.3, -3.0), T(-6.5 + sway * 0.3, -3.0)], "bark", -0.2, normal=(-0.3, -0.2, 0.9), curve=0.7)
    for k in range(11):
        x = -12.0 + k * 2.4
        r.tube([T(x * 0.3, hip[1] + 6.0), (x * 0.75 + 0.5 * math.sin(sway + k), -2.2), (x + math.sin(sway + k), 0.0)], [1.2, 0.9, 0.6], "bark",
               -0.1 + 0.01 * k, bias=-0.2 * (k % 2))
    for (x, y) in ((-4.0, -4.0), (4.5, -3.0)):
        rot_bloom(r, *T(x, y), 0.0)
    # a slender trunk of a body: narrow waist, the rot split open at the belly on two pink pods
    r.poly([T(-4.0, hip[1] - 13.0), T(4.0, hip[1] - 13.0), T(2.3, hip[1] - 6.0), T(3.8, hip[1] + 0.5), T(-3.8, hip[1] + 0.5), T(-2.3, hip[1] - 6.0)],
           "bark", 0.0, bias=0.2, normal=(-0.3, -0.2, 0.9), curve=0.8)
    for k in range(3):
        r.line(*T(-2.0 + k * 2.0, hip[1] - 12.0), *T(-1.5 + k * 1.6, hip[1]), "bark", 0.05, tone=2)
    r.ell(*T(0.3, hip[1] - 5.5), 1.8, 3.0, "chitin", 0.1, bias=-0.5)
    pod(r, *T(0.3, hip[1] - 3.2), 2.6, 0.12, ripe=1.0)
    pod(r, *T(0.6, hip[1] - 5.8), 2.4, 0.13, ripe=1.0)
    if belly_glow:
        motes(r, *T(0.4, hip[1] - 5.0), 0, n=3 + belly_glow * 2, mat="glowg", spread=3.0, seed=belly_glow)
    # a shawl of moss and rot blooms at the shoulders
    r.ell(*T(0.0, hip[1] - 12.6), 5.0, 1.8, "moss", 0.2, bias=0.1)
    rot_bloom(r, *T(-3.0, hip[1] - 12.6), 0.25); rot_bloom(r, *T(3.6, hip[1] - 9.0), 0.25)
    # long branch arms, twig fingers, fruit hanging from the forearms
    for k, (sh, hd, z) in enumerate(((T(-3.6, hip[1] - 12.0), hand2, -0.8), (T(3.6, hip[1] - 12.0), hand, 2.0))):
        el = arm(r, sh, hd, 7.0, 6.6, "bark", z, rad=(1.4, 1.1, 0.8), bend=1 if k == 0 else -1, bias=-0.1 if k == 0 else 0.2)
        vine(r, [sh, el, (lerp(el[0], hd[0], 0.7), lerp(el[1], hd[1], 0.7))], [0.5], z + 0.015, mat="moss", thorns=0)
        a0 = math.atan2(hd[1] - el[1], hd[0] - el[0])
        for f in (-35, 0, 35):
            a = a0 + math.radians(f)
            r.line(hd[0], hd[1], hd[0] + 3.4 * math.cos(a), hd[1] + 3.4 * math.sin(a), "bark", z + 0.01, tone=3)
        fx, fy = lerp(el[0], hd[0], 0.4), lerp(el[1], hd[1], 0.4)
        r.line(fx, fy, fx, fy + 2.0, "moss", z + 0.02, tone=2)
        pod(r, fx, fy + 4.6, 2.6, z + 0.03, ripe=1.0)
        leaf(r, *el, -60 if k else -120, 2.6, z + 0.02)
    # a crown of bare branches, pink buds opening on them as she feeds
    for k, (a, ln) in enumerate(((-150, 5.0), (-115, 4.5), (-65, 4.5), (-30, 5.0))):
        bp = chain(hx, hy - 7.0, [(ln * 0.6, a), (ln * 0.5, a + (15 if k < 2 else -15))])
        r.tube(bp, [0.9, 0.7, 0.5], "bark", -0.3 + k * 0.01, bias=0.05)
        r.dot(bp[-1][0], bp[-1][1], "podf", 4 if buds > k else 2, -0.2)
        if buds > k: r.dot(bp[-1][0] + 1, bp[-1][1], "podf", 3, -0.2)
    r.tube([T(0.3, hip[1] - 13.0), (hx, hy)], [1.0, 0.9], "bark", 0.4)
    r.stamp(MOTHER_HEAD[face], hx, hy, 0.6, MOTHER_LEG, pivot=(3, 8))
    smears(r, smear); sparks(r, spark)
    if extra: extra(r)
    return r.resolve()


def mother_sheet(outdir):
    M = rot_mother
    idle = [M(bob=[0, -0.4, -0.8, -0.4][i], sway=[0, 0.4, 0.8, 0.4][i], hand=(9.0, -20.0 + [0, -0.4, -0.8, -0.4][i])) for i in range(4)]
    run = [M(lean=5, bob=-0.6 * abs(math.sin(i / 6 * math.tau)), sway=-1.5 + 0.8 * math.sin(i / 6 * math.tau), hand=(8.0, -19.0),
             hand2=(-8.0, -18.0)) for i in range(6)]
    # Erupt (8): claws dig the air (0-1), DRIVES her hands down (2: first eruption under the hero), (3) holds, PULLS (4: the second),
    # recover (5-7)
    er = [M(hand=(8.0, -28.0), hand2=(-7.0, -27.0), face="cast"), M(hand=(7.0, -31.0), hand2=(-6.0, -30.0), face="cast", bob=-0.8),
          M(hand=(12.0, -10.0), hand2=(-11.0, -10.0), face="cast", bob=0.8, extra=lambda r: soil(r, 0.0, 0.0, 0, 2.0)),
          M(hand=(12.0, -9.0), hand2=(-11.0, -9.0), face="cast", bob=0.8),
          M(hand=(10.0, -24.0), hand2=(-9.0, -24.0), face="cast", bob=-0.6), M(hand=(9.0, -22.0), hand2=(-8.0, -21.0)), M(), M()]
    # Sprouting (8): kneels, hands to the floor (0-2), the floor heaves (3), SPROUTS burst up round the hero (4), rises (5-7)
    sp = [M(hand=(10.0, -14.0), hand2=(-9.0, -14.0), sink=1.0), M(hand=(11.0, -6.0), hand2=(-10.0, -6.0), sink=2.5, face="cast"),
          M(hand=(11.0, -2.0), hand2=(-10.0, -2.0), sink=3.0, face="cast", belly_glow=1),
          M(hand=(11.0, -2.0), hand2=(-10.0, -2.0), sink=3.0, face="cast", belly_glow=2, extra=lambda r: soil(r, 0.0, 0.0, 0, 2.4)),
          M(hand=(10.0, -12.0), hand2=(-9.0, -12.0), sink=1.5, face="cast", belly_glow=2, extra=lambda r: soil(r, 0.0, 0.0, 1, 2.4)),
          M(hand=(9.0, -18.0), hand2=(-8.0, -18.0), sink=0.5), M(), M()]
    # Feed (4): a husk wisp reaches her: the buds in her hair open, her belly glows
    fd = [M(buds=1, belly_glow=1, face="cast"), M(buds=2, belly_glow=2, face="cast"), M(buds=3, belly_glow=2), M(buds=3, belly_glow=1)]
    d0 = M(face="cast", lean=-10)
    d1 = M(face="dead", lean=-16, sink=4.0, hand=(6.0, -12.0), hand2=(-10.0, -12.0))
    d2 = _mother_corpse(0)
    corpse = _mother_corpse(1)
    knock = M(face="cast", lean=-12, hand=(6.0, -24.0), hand2=(-10.0, -22.0))
    anims = [("Idle", idle, [0.2, 0.16, 0.2, 0.16]), ("Run", run, [0.09] * 6),
             ("Erupt", er, [0.12, 0.12, 0.06, 0.34, 0.06, 0.12, 0.12, 0.12]),
             ("Sprouting", sp, [0.12, 0.12, 0.12, 0.12, 0.08, 0.12, 0.12, 0.12]),
             ("Feed", fd, [0.1, 0.1, 0.14, 0.14])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.12, 0.14, 0.14, 0.4], knock)
    return sheet("SylRotMother", anims, outdir, scale=3)


def _mother_corpse(stage):
    r = Rig()
    r.poly([(-12.0, -5.0), (8.0, -6.0), (10.0, 0.0), (-13.0, 0.0)], "bark", 0.0, curve=0.5)
    r.ell(-1.0, -3.6, 2.4, 1.6, "chitin", 0.1)
    pod(r, -1.0, -2.0, 2.4, 0.15, ripe=1.0)
    for k in range(6):
        r.tube([(9.0 + k * 0.6, -3.0), (15.0 + k, -1.0 + (k % 2))], [0.8, 0.6], "bark", -0.2)
    r.tube([(-10.0, -4.0), (-16.0, -2.0)], [1.0, 0.7], "bark", 0.2)
    r.stamp(MOTHER_HEAD["dead"], 12.0, -1.0 + stage, 0.6, MOTHER_LEG, pivot=(3, 8))
    for x in (-8.0, 4.0):
        pod(r, x, -5.0 + (stage * 2), 2.6, 0.5, ripe=0.4)
    rot_bloom(r, -5.0, -4.0, 0.6)
    if stage == 0: dust_puff(r, 0.0, 0, 1, 2.0)
    return r.resolve()


# ================================================================== NIGHTSHADE: a pale lady in a gown of purple bell-flowers
SHADE_LEG = {"l": ("lily", 1), "L": ("lily", 2), "W": ("lily", 3), "X": ("lily", 4), "m": ("chitin", 0), "b": ("berry", 3),
             "B": ("berry", 4), "v": ("glowp", 3), "V": ("glowp", 4), "h": ("hair", 1), "H": ("hair", 2)}


SHADE_HEAD = {
    # pivot (3, 7): the neck. A fine pale face, long violet eyes, berry-dark lips, black hair at the temples
    "calm": "\nhHHHHHh\nhlWXWlh\nhWvWvWh\nhWWWWWh\nhlWbWlh\n.hlWlh.\n..lLl..\n...l...\n",
    "cast": "\nhHHHHHh\nhlWXWlh\nhVvWvVh\nhWWWWWh\nhlbbblh\n.hlWlh.\n..lLl..\n...l...\n",
    "dead": "\nhHHHHHh\nhlWXWlh\nhWmWmWh\nhWWWWWh\nhlWmWlh\n.hlWlh.\n..lLl..\n...l...\n",
}


def bell_hood(r, hx, hy, z, sway=0.0, open_=0.0):
    """A deadly-nightshade bell-flower worn as a hood: a purple bell over the head with five flared, curled petal tips,
    a green calyx and stem on top, black berries hanging at its rim."""
    top = hy - 10.5
    rim = hy - 2.0
    w = 6.4 + open_
    r.poly([(hx - 2.0, top + 1.0), (hx + 2.0, top + 1.0), (hx + w * 0.8, rim - 3.0), (hx + w + sway, rim), (hx - w + sway, rim), (hx - w * 0.8, rim - 3.0)],
           "bell", z, normal=(-0.3, -0.4, 0.85), curve=0.9)
    for k in range(5):
        x = hx - w + sway + k * (2 * w) / 4.0
        out = (k - 2) * 0.6
        r.poly([(x - 1.4, rim - 0.6), (x + 1.4, rim - 0.6), (x + out * 1.6, rim + 2.2)], "bell", z + 0.02 + k * 0.001, normal=(-0.2, 0.3, 0.9))
        r.dot(x + out * 1.6, rim + 2.2, "bell", 4, z + 0.03)
    r.line(hx - 1.0, top + 2.0, hx - w * 0.6, rim - 1.0, "bell", z + 0.01, tone=1)
    r.line(hx + 1.0, top + 2.0, hx + w * 0.6, rim - 1.0, "bell", z + 0.01, tone=3)
    for side in (-1, 1):
        leaf(r, hx, top + 1.5, -90 + side * 60, 3.2, z + 0.05, mat="moss", w=1.0)
    r.tube([(hx, top + 1.0), (hx + 1.0 + sway * 0.3, top - 1.5)], [0.6, 0.4], "moss", z + 0.06)
    for side in (-1, 1):
        bx = hx + side * (w - 0.5) + sway
        r.line(bx, rim, bx, rim + 2.0, "moss", z + 0.04, tone=2)
        r.ell(bx, rim + 3.2, 1.3, 1.3, "berry", z + 0.05, bias=0.4)


def nightshade(lean=0.0, bob=0.0, hand=(7.0, -20.0), hand2=(-6.0, -18.0), face="calm", sway=0.0, berry=None, smear=None, spark=None,
               extra=None, sink=0.0, kneel=0.0):
    r = Rig()
    hip = (0.0, -12.5 + bob + sink + kneel)
    T = Xf(lean, (0.0, 0.0))
    hx, hy = T(0.4, hip[1] - 11.0)
    # long black hair falling behind her to the hips
    r.poly([(hx - 3.5, hy - 6.0), (hx + 3.5, hy - 6.0), (hx + 4.5 + sway, hip[1] + 1.0), (hx - 5.5 + sway, hip[1] + 2.0)], "hair", -1.0,
           normal=(-0.3, -0.3, 0.9), curve=0.6)
    # the gown: a fitted bodice, then one bell of five long petals sweeping to the floor, tips curling out
    r.poly([T(-2.8, hip[1] - 11.0), T(2.8, hip[1] - 11.0), T(2.0, hip[1] - 4.0), T(-2.0, hip[1] - 4.0)], "bell", 0.0, normal=(-0.3, -0.3, 0.9), curve=0.7)
    petals = ((-11.0, 0), (-6.0, 1), (0.0, 0), (6.0, 1), (11.0, 0))
    for k, (tx, d) in enumerate(petals):
        base = T(tx * 0.18, hip[1] - 4.0)
        tip = (tx + sway * (1.0 + 0.2 * k), -0.3 - d * 0.5)
        mid = ((base[0] + tip[0]) / 2.0, (base[1] + tip[1]) / 2.0)
        w = 3.4 + d * 0.4
        r.poly([base, (mid[0] - w, mid[1]), (tip[0] - 1.0, tip[1] - 1.5), tip, (tip[0] + 1.0, tip[1] - 1.5), (mid[0] + w, mid[1])],
               "bell", 0.05 + d * 0.02 + k * 0.001, normal=(-0.25 + tx * 0.03, -0.2, 0.9), curve=0.5)
        r.line(base[0], base[1] + 1.0, tip[0], tip[1] - 1.0, "bell", 0.08 + d * 0.02, tone=1 if d else 3)
        r.dot(tip[0] + (1 if tx > 0 else -1), tip[1] - 0.5, "bell", 4, 0.1 + d * 0.02)
    # green sepals at the waist, a cluster of black berries at the hip
    for k in range(5):
        a = math.radians(60 + k * 15)
        sx, sy = T(-2.2 + k * 1.1, hip[1] - 4.0)
        r.poly([(sx - 0.8, sy), (sx + 0.8, sy), (sx + 2.6 * math.cos(a) - 1.3, sy + 3.0 * math.sin(a))], "moss", 0.15, normal=(-0.2, -0.3, 0.9))
    for (x, y) in ((-2.6, -2.0), (-1.4, -1.2), (-3.4, -0.8)):
        r.ell(*T(x, hip[1] + y), 1.1, 1.1, "berry", 0.2, bias=0.4)
    arm(r, T(-2.6, hip[1] - 10.4), hand2, 4.6, 4.2, "lily", -0.8, rad=(0.9, 0.8, 0.7), bend=1, bias=-0.3)
    r.stamp(SHADE_HEAD[face], hx, hy, 0.6, SHADE_LEG, pivot=(3, 7))
    bell_hood(r, hx, hy - 4.0, 0.7, sway=sway * 0.4, open_=0.6 if face == "cast" else 0.0)
    arm(r, T(2.6, hip[1] - 10.4), hand, 4.6, 4.2, "lily", 2.0, rad=(0.9, 0.8, 0.7), bend=-1)
    if berry:
        bx, by, s = berry
        r.ell(bx, by, s, s, "berry", 2.5, bias=0.3)
    smears(r, smear); sparks(r, spark)
    if extra: extra(r)
    return r.resolve()


def shade_sheet(outdir):
    N = nightshade
    idle = [N(bob=[0, -0.4, -0.8, -0.4][i], sway=[0, 0.4, 0.8, 0.4][i], hand=(7.0, -20.0 + [0, -0.4, -0.8, -0.4][i]), berry=(7.0, -21.0, 1.2))
            for i in range(4)]
    run = [N(lean=5, bob=-0.5 * abs(math.sin(i / 6 * math.tau)), sway=-1.6 + 0.6 * math.sin(i / 6 * math.tau), hand=(6.0, -19.0),
             hand2=(-6.0, -17.0), berry=(6.0, -20.0, 1.2)) for i in range(6)]
    # Toss (7): weighs a berry (0-1), draws back (2), TOSSES it (3: it leaves her fingers at (11, -25)), follow (4), recover
    ts = [N(hand=(5.0, -22.0), berry=(5.0, -23.0, 1.6), face="cast"), N(hand=(0.0, -27.0), berry=(0.0, -28.0, 1.8), face="cast", lean=-6),
          N(hand=(-3.0, -28.0), berry=(-3.0, -29.0, 1.8), face="cast", lean=-10),
          N(hand=(11.0, -25.0), face="cast", lean=8, berry=(13.0, -25.0, 1.6), smear=[("arc", 4.0, -24.0, 8.0, -140, -20, "bell", 2)]),
          N(hand=(10.0, -21.0), lean=6), N(hand=(8.0, -20.0), lean=2), N()]
    # Garden (8): a slow curtsey, sweeping her hand over the floor (0-3), the SHADE falls (4: violet motes, pods go unseen),
    # she plants two more by the hero (5), rises (6-7)
    gd = [N(hand=(6.0, -16.0), kneel=1.0), N(hand=(9.0, -10.0), hand2=(-8.0, -12.0), kneel=2.5, face="cast"),
          N(hand=(11.0, -6.0), hand2=(-10.0, -8.0), kneel=3.5, face="cast", extra=lambda r: motes(r, 10.0, -4.0, 0, n=6, mat="glowp", spread=5.0)),
          N(hand=(11.0, -6.0), hand2=(-10.0, -8.0), kneel=3.5, face="cast", extra=lambda r: motes(r, 0.0, -6.0, 1, n=10, mat="glowp", spread=12.0, seed=3)),
          N(hand=(10.0, -10.0), hand2=(-9.0, -10.0), kneel=2.5, face="cast", extra=lambda r: motes(r, 0.0, -10.0, 2, n=10, mat="glowp", spread=14.0, seed=5)),
          N(hand=(9.0, -16.0), kneel=1.0), N(hand=(8.0, -19.0)), N()]
    d0 = N(face="cast", lean=-12, hand=(4.0, -24.0))
    d1 = N(face="dead", lean=-20, kneel=6.0, hand=(5.0, -10.0), hand2=(-8.0, -9.0))
    d2 = _shade_corpse(0)
    corpse = _shade_corpse(1)
    knock = N(face="cast", lean=-14, hand=(4.0, -23.0), hand2=(-7.0, -21.0))
    anims = [("Idle", idle, [0.2, 0.16, 0.2, 0.16]), ("Run", run, [0.08] * 6),
             ("Toss", ts, [0.12, 0.12, 0.1, 0.05, 0.1, 0.12, 0.12]),
             ("Garden", gd, [0.12, 0.12, 0.12, 0.12, 0.1, 0.12, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("SylNightshade", anims, outdir, scale=3)


def _shade_corpse(stage):
    r = Rig()
    for k, tx in enumerate((-12.0, -7.0, -2.0, 3.0)):
        r.poly([(tx, -1.5), (tx + 4.0, -4.5), (tx + 8.0, -1.5), (tx + 4.0, 0.0)], "bell", k * 0.01, normal=(-0.2, -0.3, 0.9))
    r.poly([(6.0, -4.0), (13.0, -6.0), (14.0, -1.0), (7.0, 0.0)], "hair", 0.2)
    r.stamp(SHADE_HEAD["dead"], 11.0, 0.0 + stage, 0.5, SHADE_LEG, pivot=(3, 7))
    if stage == 0: bell_hood(r, 16.0, -1.0, 0.4, open_=0.4)
    for x in (14.0, 17.0, 9.0):
        r.ell(x, -1.0, 1.0, 1.0, "berry", 0.6, bias=0.3)
    if stage == 0: dust_puff(r, 0.0, 0, 1, 1.8)
    return r.resolve()


JOBS = [("SylBriarBehemoth", behemoth_sheet), ("SylBriarChampion", champion_sheet), ("SylPuffball", puffball_sheet),
        ("SylCordyceps", saint_sheet), ("SylShambler", shambler_sheet), ("SylRotMother", mother_sheet), ("SylNightshade", shade_sheet)]

SYNC = {
    "SylBriarBehemoth": {"Hook": [("HOOK: tusks sweep x 18..26, y -16..-4", 2)], "Charge": [("CHARGE starts", 3), ("skids to a stop: the bush swings in", 8)]},
    "SylBriarChampion": {"Thrust": [("THRUST: tip at x 30 + 6 per grown length, y -15", 2)],
                         "Lunge": [("feet planted (0.5 s)", 0), ("LUNGE: tip at x 38 + 6 per grown length, y -14", 4)]},
    "SylPuffball": {"Slam": [("SLAM: fists land at (13, -1), spore ring at (16, 0)", 2)],
                    "Bounce": [("squash (0.4 s)", 0), ("LAUNCH (untouchable)", 2), ("LAND: spore ring at (0, 0)", 6)],
                    "WallSquash": [("springs off the wall", 2)]},
    "SylCordyceps": {"Flick": [("spine leaves the fingers at (11, -22)", 2)], "Infect": [("spines leave the stalks at (0, -38)", 4)]},
    "SylRotMother": {"Erupt": [("first eruption under the hero", 2), ("second, 0.4 s later", 4)], "Sprouting": [("SPROUTS burst up round the hero", 4)]},
    "SylNightshade": {"Toss": [("berry leaves her fingers at (11, -25)", 3)], "Garden": [("the shade falls (pods go unseen)", 4),
                                                                                       ("two more pods planted by the hero", 5)]},
}
NOTES = {
    "SylBriarChampion": "Idle/Run/Thrust/Lunge carry the lance at its base length (18 px); Idle1-3, Run1-3, Thrust1-3 and Lunge1-3 "
                        "at +6, +12, +18 px with one fresh green tip per grown length.",
    "SylShambler": "Death is the burst: the corpse swells and splits into three seeds (spawned by the code on frame 3).",
}
