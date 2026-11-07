"""Ysveld tier 2: Silk Weaver, Rime Lurker, Silkmoth, Veil Witch, Rime Knight, Shard Hermit. Built through
ysveld_v2_rigs.py. T2 idle limit 28 x 26; none is smaller than the sprite it replaces."""
import math
from ysveld_v2_rigs import (Rig, Xf, chain, ik, lerp, lerp_pt, spider, moth, wing, antenna, robe, crystal, sparkle,
                            arc_smear, snow_puff, flakes, rime_fringe, shadow, sheet, tail_anims)


def legs2(r, hip, feet, mat, z, l1, l2, rad=(1.3, 1.1, 0.9), boot=None, back_bias=-0.25):
    """Two legs from a hip point to two feet (far first). Knees bend forward."""
    for k, f in enumerate(feet):
        h = (hip[0] + (-0.8 if k == 0 else 0.8), hip[1])
        kn = ik(h[0], h[1], f[0], f[1], l1, l2, bend=-1)
        r.tube([h, kn, f], list(rad), mat, z + (0 if k else -1.5), bias=back_bias if k == 0 else 0.0)
        if boot: r.ell(f[0] + 0.8, f[1] - 0.6, 1.6, 0.9, boot, z + (0.01 if k else -1.49), bias=back_bias if k == 0 else 0.0)


def arm(r, sh, hand, mat, z, l1, l2, rad=(1.1, 0.9, 0.8), bend=1, bias=0.0):
    el = ik(sh[0], sh[1], hand[0], hand[1], l1, l2, bend=bend)
    r.tube([sh, el, hand], list(rad), mat, z, bias=bias)
    return el


def walk(i, n=6, stride=3.0):
    """Feet for a 6-frame walk: (far foot, near foot) x offsets and lifts."""
    a = i / n * math.tau
    return ((-stride * math.sin(a), -max(0.0, math.cos(a)) * 1.2), (stride * math.sin(a), -max(0.0, -math.cos(a)) * 1.2))


# ================================================================== SILK WEAVER: a stilt-legged frost spider, glowing spinnerets
def weaver(phase=0.0, stride=0.0, lean=0.0, cy=-9.5, fang=0.0, abd_ang=0.0, glow=1, front=None, line=None, extra=None,
           eye="eye", smear=None):
    r = Rig(1.0)
    s = 1.3
    # abdomen: long and silk white, held up behind; abd_ang swings it up and over the back (for the line)
    a = math.radians(212 + abd_ang)
    ax, ay = 2.4 + 7.0 * math.cos(a) * s * 0.85, cy - 1.0 + 7.0 * math.sin(a) * s * 0.85
    spider(r, cx=4.0, cy=cy, s=s, phase=phase, stride=stride, lean=lean, abd=(0.1, 0.1), abd_at=(0, 0), ceph=(3.4, 2.6),
           legs=(6.0, 6.5), spread=(7.6, 3.6, -2.8, -6.6), mats=("chit", "chit", "chit"), eyes=((2.2, -1.0), (1.2, -1.4), (2.6, -0.2)),
           eye_mat=eye, fang=fang, front=front, knee_h=(4.6, 4.0, 3.8, 4.4), leg_rad=(0.85, 0.65, 0.45), near_z=0.5)
    ang = math.degrees(a) + 180
    r.ell(ax, ay, 8.4, 5.6, "chit", 0.2, ang=ang, bias=0.1)
    # silk-white bands across the dark abdomen, a crest of frost along its back, the glowing spinnerets at the tip
    ca, sa = math.cos(a), math.sin(a)
    for k in (-4.0, -1.0, 2.0, 5.0):
        bx, by = ax + ca * k, ay + sa * k
        for w in range(-4, 5):
            r.dot(bx + sa * w * 0.9 + ca * abs(w) * 0.25, by - ca * w * 0.9 + sa * abs(w) * 0.25, "web", 3 if w < 0 else 2, 0.25)
    for k in range(-6, 7, 2):
        bx, by = ax + ca * k, ay + sa * k
        r.dot(bx + sa * 5.2, by - ca * 5.2, "frost", 4, 0.26)
    tx, ty = ax + ca * 8.4, ay + sa * 8.4
    for g in range(glow + 1):
        r.dot(tx - g * ca, ty - g * sa, "eye", 4 - g, 0.4)
    r.dot(tx + ca, ty + sa, "eye", 2, 0.39)
    if line:
        r.polyline([(tx, ty)] + line, "web", 0.5, tone=3)
    if smear:
        for (p, q, m, t) in smear: r.line(*p, *q, m, 4.5, tone=t)
    if extra: extra(r)
    return r.resolve()


def weaver_corpse(stage):
    r = Rig()
    r.ell(-3.0, -3.0, 6.5, 3.0, "web", 0.0, bias=0.1)
    r.ell(4.5, -2.8, 3.0, 2.2, "chit", 0.3)
    for i in range(4):
        x = -1.0 + i * 2.6
        r.tube([(x, -5.0), (x - 1 + i * 0.5, -10.0 + stage * 2), (x + 1.5, -7.0 + stage * 1.5)], [0.7, 0.55, 0.4], "chit", 1.0 + i * 0.01)
    r.dot(-9.5, -3.0, "eye", 2 if stage == 0 else 1, 0.4)
    r.line(7.0, -2.0, 8.0, -4.0, "frost", 0.5, tone=4)
    return r.resolve()


def weaver_sheet(out):
    W = weaver
    idle = [W(cy=-8.0 + [0, 0.2, 0.4, 0.2][i], abd_ang=[0, 3, 6, 3][i], glow=[1, 2, 1, 0][i], fang=[0, 0, 0.5, 0][i]) for i in range(4)]
    run = [W(phase=i / 6.0, stride=1.0, lean=5, cy=-8.3 + 0.4 * abs(math.sin(i / 6 * math.tau)), abd_ang=4 * (i % 2)) for i in range(6)]
    # Fangs (7): rear (0-1), stab down and forward (2-3: BITE at frame 3), withdraw
    fangs = [W(lean=-6, cy=-8.6, fang=1.0, front=((4.0, -6.0), (3.5, -5.5))),
             W(lean=-12, cy=-9.2, fang=1.8, front=((5.0, -8.0), (4.0, -7.5)), abd_ang=8),
             W(lean=10, cy=-7.4, fang=1.8, front=((8.0, -2.0), (7.0, -1.5)), smear=[((6, -12), (12, -6), "snow", 2)]),
             W(lean=18, cy=-6.6, fang=0.0, front=((9.0, 3.0), (8.0, 3.5)),
               extra=lambda r: [sparkle(r, 12, -4, 1, "white"), snow_puff(r, 11, 0, 0, 0.8)]),
             W(lean=12, cy=-7.0, fang=0.2, extra=lambda r: snow_puff(r, 11, 0, 1, 0.8)), W(lean=4), W()]
    # Tether (8): the abdomen swings up and over the back (0-2), spinnerets flare (3: the line fires from (6, -19)),
    # it pays out (4-5), settles (6-7)
    teth = [W(abd_ang=20, glow=2), W(abd_ang=45, glow=2, lean=-4), W(abd_ang=70, glow=2, lean=-8),
            W(abd_ang=85, glow=2, lean=-4, line=[(10, -21), (14, -20)], extra=lambda r: sparkle(r, 8, -21, 1, "eye")),
            W(abd_ang=80, glow=1, line=[(12, -19), (18, -17), (22, -16)]), W(abd_ang=60, glow=1), W(abd_ang=30), W(abd_ang=10)]
    d0 = W(lean=-12, eye="white", fang=1.6)
    d1 = W(lean=-28, cy=-6.0, eye="white", front=((2.0, -6.0), (1.0, -5.0)))
    knock = W(lean=-14, eye="white", fang=1.2, abd_ang=-6)
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.07] * 6),
             ("Fangs", fangs, [0.12, 0.1, 0.05, 0.08, 0.1, 0.1, 0.1]),
             ("Tether", teth, [0.08, 0.08, 0.1, 0.06, 0.1, 0.1, 0.1, 0.1])]
    anims += tail_anims(idle[0], [d0, d1, weaver_corpse(0), weaver_corpse(1)], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("YsvWeaver", anims, out, scale=6)


# ================================================================== RIME LURKER: a trapdoor spider under a lid of frost
def lurker(lid=0.0, phase=0.0, stride=0.0, lean=0.0, cy=-4.0, fang=0.0, peek=1.0, front=None, extra=None, eye="red",
           snares=None):
    """lid: 0 shut (only the eyes show) .. 1 flipped up and back."""
    r = Rig(1.3)
    s = 1.05
    spider(r, cx=2.0, cy=cy, s=s, phase=phase, stride=stride, lean=lean, abd=(5.0, 3.4), abd_at=(-5.0, -0.8),
           ceph=(3.6, 2.6), legs=(5.0, 5.4), spread=(9.0, 4.8, -4.0, -9.0), mats=("chit", "chit", "chit"),
           eyes=((2.4, -1.2), (1.2, -1.6), (3.0, -0.4)), eye_mat="eye", fang=fang, front=front, knee_h=(2.6, 2.0, 2.0, 2.4),
           leg_rad=(0.9, 0.7, 0.5), near_z=0.5)
    # the lid: a thick disc of packed frost, hinged at the back; flips up as lid -> 1
    hx, hy = -9.0, cy - 2.0
    ang = -lid * 115.0
    T = Xf(ang, (hx, hy))
    pts = [T(hx + x, hy + (-1.6 if 2 < x < 17 else -0.4) - math.sin(x / 19 * math.pi) * 1.6) for x in range(0, 20)]
    pts += [T(hx + x, hy + 1.6) for x in range(19, -1, -1)]
    r.poly(pts, "frost", 3.0 + (0 if lid < 0.5 else -6), bias=0.05, normal=(-0.3, -0.8, 0.6))
    # rime crust and the blue underside rim of the lid
    for x in range(1, 19, 3): r.dot(*T(hx + x, hy - 2.0), "frost", 4, 3.01 + (0 if lid < 0.5 else -6))
    for x in range(2, 18): r.dot(*T(hx + x, hy + 1.6), "ice", 1, 3.02 + (0 if lid < 0.5 else -6))
    # under a shut lid only the eyes show: red, in a dark slot
    if lid < 0.3:
        for (ex, ey) in ((6.0, 2.6), (8.0, 2.6), (7.0, 3.4)):
            r.dot(hx + ex + 6, hy + ey, eye, 3 if peek else 1, 3.1)
    if snares:
        for (x, y, k) in snares: sparkle(r, x, y, k, "web")
    if extra: extra(r)
    return r.resolve()


def lurker_corpse(stage):
    r = Rig()
    r.ell(0.0, -2.0, 6.0, 2.0, "chit", 0.0)
    for i in range(4):
        x = -3.0 + i * 2.4
        r.tube([(x, -3.0), (x + 0.5, -7.0 + stage * 1.5), (x + 2.0, -5.0 + stage)], [0.7, 0.6, 0.4], "chit", 1 + i * 0.01)
    pts = [(-11.0 + x, -1.5 - math.sin(x / 19 * math.pi) * 1.4) for x in range(0, 20)] + [(-11.0 + x, 0.0) for x in range(19, -1, -1)]
    r.poly([(p[0] - 2, p[1] - 0.5) for p in pts], "frost", 2.0 if stage else -1.0, normal=(-0.3, -0.8, 0.6))
    return r.resolve()


def lurker_sheet(out):
    Lu = lurker
    idle = [Lu(cy=-3.4, lid=[0.0, 0.02, 0.05, 0.02][i], peek=[1, 1, 0, 1][i]) for i in range(4)]
    run = [Lu(phase=i / 6.0, stride=1.0, lean=4, lid=0.1, cy=-3.8) for i in range(6)]
    # Bite (7): the lid cracks (0), bursts open (1), LUNGE (2-3: BITE at frame 3), drop back (4-6)
    bite = [Lu(lid=0.15, cy=-3.4), Lu(lid=0.55, cy=-3.8, fang=1.4, lean=-6),
            Lu(lid=0.9, cy=-4.4, fang=1.8, lean=10, front=((6.0, -2.0), (5.0, -1.5))),
            Lu(lid=1.0, cy=-4.2, fang=0.0, lean=16, front=((7.0, 2.0), (6.5, 2.5)),
               extra=lambda r: [sparkle(r, 11, -3, 1, "white"), snow_puff(r, 9, 0, 0, 0.8)]),
            Lu(lid=0.7, cy=-4.0, lean=10, extra=lambda r: snow_puff(r, 9, 0, 1, 0.8)), Lu(lid=0.35), Lu(lid=0.1)]
    # Snare (8): the lid swings fully open (0-2), two silk snares flick out (3-4: thrown at frame 4), it shuts (5-7)
    snare = [Lu(lid=0.3), Lu(lid=0.7, lean=-6), Lu(lid=1.0, lean=-10, fang=1.0),
             Lu(lid=1.0, lean=-4, fang=1.5, snares=[(8, -10, 2)]), Lu(lid=1.0, lean=6, snares=[(14, -12, 1), (12, -6, 2)]),
             Lu(lid=0.8, lean=2), Lu(lid=0.4), Lu(lid=0.1)]
    d0 = Lu(lid=0.8, lean=-10, eye="white"); d1 = Lu(lid=1.0, lean=-24, cy=-3.0, front=((1.0, -5.0), (0.0, -4.0)))
    knock = Lu(lid=0.6, lean=-14)
    anims = [("Idle", idle, [0.3, 0.15, 0.2, 0.15]), ("Run", run, [0.07] * 6),
             ("Bite", bite, [0.1, 0.08, 0.06, 0.08, 0.1, 0.1, 0.1]),
             ("Snare", snare, [0.1, 0.1, 0.1, 0.08, 0.1, 0.1, 0.1, 0.1])]
    anims += tail_anims(idle[0], [d0, d1, lurker_corpse(0), lurker_corpse(1)], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("YsvLurker", anims, out, scale=6)


# ================================================================== SILKMOTH: a pale moth trailing its own cocoon silk
def silkmoth(alt=10.0, flap=0.0, lean=0.0, body_dy=0.0, ant=0.0, trail=0.0, dive=0.0, needles=None, wake=None, extra=None,
             eye="eye", fold=1.0):
    r = Rig(1.07)
    cx, cy = 0.0, -alt + body_dy
    shadow(r, 0.0, -1.0, 5.5)
    # the cocoon silk still trailing from the tail: a loose strand with a tatter of cocoon at its end
    tx, ty = cx - 1.0 + dive * 2, cy + 5.0
    pts = [(tx, ty)]
    for k in range(1, 6):
        pts.append((tx - k * 1.6 - dive * 2.0 * k, ty + k * 1.0 + math.sin(trail + k * 0.9) * 0.9))
    r.tube(pts, [0.7, 0.6, 0.5, 0.5, 0.4, 0.4], "web", -3.0, bias=0.1)
    r.ell(pts[-1][0] - 0.5, pts[-1][1] + 0.6, 1.6, 1.2, "web", -2.9, bias=0.0)
    moth(r, cx, cy, span=12.5 * fold, chord=7.5, flap=flap, fore="web", hind="silk", body="fur", lean=lean,
         spots=[(0.55, 0.2, "aurp", 3), (0.8, -0.6, "aurp", 2)], hspots=[(0.6, 0.0, "aurp", 2)], eye=eye, ant=ant, far=0.8,
         abd=5.0, head_r=1.8, rim="ice")
    if needles:
        for (x, y, k) in needles:
            r.line(x - 3, y, x, y, "web", 6.0, tone=3); r.dot(x + 1, y, "ice", 4, 6.0)
    if wake:
        for (x0, x1) in wake:
            r.line(x0, -1, x1, -1, "snow", -10, tone=3); r.line(x0 + 1, 0, x1 - 1, 0, "snow", -10, tone=2)
    if extra: extra(r)
    return r.resolve()


def silkmoth_corpse(stage):
    r = Rig()
    wing(r, (-1.0, -2.0), -170, 9.0, 6.5, "silk", -1.0, bias=-0.3)
    wing(r, (0.0, -2.0), -12 - 8 * stage, 10.0, 7.0, "web", 1.0, spots=[(0.55, 0.3, "aurp", 2)])
    r.tube([(2.0, -2.0), (-1.0, -1.5), (-5.0, -1.2)], [1.8, 1.5, 0.9], "fur", 0.5)
    r.tube([(-5.0, -1.2), (-9.0, -0.6), (-12.0, -0.4)], [0.6, 0.5, 0.4], "web", 0.3)
    r.dot(3.0, -2.6, "white", 3, 0.7)
    return r.resolve()


def silkmoth_sheet(out):
    M = silkmoth
    idle = [M(alt=10.0 + [0, -0.5, -1, -0.5][i], flap=[-25, 5, 30, 5][i], ant=[0, 4, 8, 4][i], trail=i * 1.5) for i in range(4)]
    run = [M(alt=10.5 + [0, -0.6, -1, -0.6, 0, 0.4][i], flap=[-35, -10, 25, 40, 15, -15][i], lean=12, trail=i) for i in range(6)]
    # Volley (7): wings up (0-1), a beat flings 3 needles from (8, -12) (3), recover
    volley = [M(flap=-40, lean=-6), M(flap=-55, lean=-10, needles=[(5, -14, 1)]), M(flap=15, lean=6, needles=[(8, -13, 1)]),
              M(flap=40, lean=12, needles=[(13, -14, 1), (13, -11, 1), (12, -16, 1)]), M(flap=20, lean=6), M(flap=-5), M(flap=-20)]
    # Dive (8): rear up (0-1), fold and plunge (2), DIVE through (3-5, moving: the frost wake hardens behind), pull up (6-7)
    dive = [M(flap=-40, lean=-12, alt=11), M(flap=-60, lean=-20, alt=12, fold=1.05),
            M(flap=-80, lean=30, alt=8, fold=0.75, dive=0.5), M(flap=-85, lean=45, alt=5, fold=0.7, dive=1.0, wake=[(-14, -4)]),
            M(flap=-85, lean=40, alt=4, fold=0.7, dive=1.0, wake=[(-16, -2)]), M(flap=-60, lean=25, alt=5, fold=0.8, dive=0.6, wake=[(-14, -6)]),
            M(flap=10, lean=0, alt=8), M(flap=-10, alt=10)]
    d0 = M(flap=-60, lean=-20, eye="white"); d1 = M(alt=6.0, flap=40, lean=-40, eye="white", fold=0.8)
    knock = M(flap=-50, lean=-24, eye="white")
    anims = [("Idle", idle, [0.09] * 4), ("Run", run, [0.06] * 6),
             ("Volley", volley, [0.1, 0.12, 0.06, 0.08, 0.1, 0.1, 0.1]),
             ("Dive", dive, [0.1, 0.12, 0.06, 0.06, 0.06, 0.08, 0.1, 0.1])]
    anims += tail_anims(idle[0], [d0, d1, silkmoth_corpse(0), silkmoth_corpse(1)], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("YsvSilkmoth", anims, out, scale=6)


# ================================================================== VEIL WITCH: a thin witch in frost lace, an ice-shard wand
WITCH_LEG = {"v": ("veil", 3), "V": ("veil", 4), "u": ("veil", 2), "w": ("veil", 1), "s": ("skin", 3), "S": ("skin", 4),
             "k": ("skin", 2), "e": ("vglow", 3), "E": ("vglow", 4), "m": ("robe", 0), "c": ("crys", 3), "C": ("crys", 4)}
WITCH_HEAD = {
    # pivot (3, 7): the neck. A pointed lace hood, a pale face half veiled, violet eyes; a crystal pin at the brow
    "calm": """
...C...
..vcv..
.vVVvu.
vVssskw
vVeSekw
uVsSskw
uvwkkuw
.u...w.
""",
    "cast": """
...C...
..vCv..
.vVVvu.
vVssskw
vVESEkw
uVsmskw
uvwkkuw
.u...w.
""",
    "hurt": """
....C..
..vcv..
.vVVvu.
vVssskw
vVmsmkw
uVsmskw
uvwkkuw
.u...w.
""",
}


def wand(r, hx, hy, ang, z, glow=0):
    """An ice-shard wand: a short dark grip and a violet crystal blade; glow 1-2 lights its tip."""
    tip = chain(hx, hy, [(2.0, ang), (5.5, ang)])
    r.line(*tip[0], *tip[1], "robe", z, tone=1)
    a = math.radians(ang)
    px, py = -math.sin(a), math.cos(a)
    r.poly([tip[1], (tip[1][0] + px * 1.2, tip[1][1] + py * 1.2), tip[2], (tip[1][0] - px * 1.2, tip[1][1] - py * 1.2)], "crys", z + 0.01,
           normal=(-0.5, -0.6, 0.6), bias=0.2)
    if glow: sparkle(r, tip[2][0], tip[2][1], 1 if glow > 1 else 2, "vglow", z + 0.5)
    return tip[2]


def veil_witch(bob=0.0, lean=0.0, sway=0.0, hand=(6.0, -11.0), hand2=(-4.0, -9.0), wand_ang=-30.0, glow=0, face="calm",
               feet=None, extra=None, hem=0.0):
    r = Rig(1.22)
    T = Xf(lean, (0.0, -1.0))
    sh = T(0.0, -15.0 + bob)
    # a long frost-lace gown, spreading at the hem; a lace train behind
    robe(r, (sh[0], sh[1] + 1.0), -0.4, 16.0 + hem, sway=sway, mat="robe", z=0.0, top_w=2.6, flare=1.6, hem_teeth=7, teeth_mat="veil")
    # the veil: a lace overdress from the shoulders to the knees, scalloped
    robe(r, (sh[0], sh[1] + 0.5), -6.0, 12.0 + hem * 0.8, sway=sway * 0.7, mat="veil", z=0.1, top_w=3.2, flare=1.2, hem_teeth=6, teeth_mat="veil")
    r.poly([(sh[0] - 2.0, sh[1] + 3.0), (sh[0] - 7.0 + sway, -0.5), (sh[0] - 9.5 + sway, -0.4), (sh[0] - 3.0, sh[1] + 2.0)],
           "silk", -1.0, bias=-0.2)
    # lace pattern: rows of brighter stitches down the gown
    for row in range(3):
        y = sh[1] + 3.5 + row * 3.0
        w = lerp(3.0, 6.5, (y - sh[1]) / 15.0)
        for i in range(-int(w), int(w) + 1, 2):
            r.dot(sh[0] + i + sway * (row + 1) / 4, y, "silk", 2, 0.15)
    # torso and arms (the far arm behind)
    r.ell(sh[0], sh[1] + 2.0, 2.4, 3.0, "robe", 0.3, bias=0.0)
    arm(r, (sh[0] - 1.5, sh[1] + 0.5), hand2, "veil", -0.5, 3.6, 3.6, rad=(1.0, 0.8, 0.6), bias=-0.25)
    r.dot(hand2[0], hand2[1], "skin", 2, -0.49)
    tip = wand(r, hand[0], hand[1], wand_ang, 1.6, glow)
    arm(r, (sh[0] + 1.5, sh[1] + 0.5), hand, "veil", 1.5, 3.8, 3.8, rad=(1.0, 0.8, 0.7))
    r.dot(hand[0], hand[1], "skin", 3, 1.55)
    r.stamp(WITCH_HEAD[face], sh[0] + 0.5, sh[1] - 0.5, 2.0, WITCH_LEG, pivot=(3, 7))
    if extra: extra(r)
    return r.resolve()


def witch_corpse(stage):
    r = Rig()
    r.poly([(-10.0, -0.3), (8.0, -0.3), (6.0, -3.5), (-6.0, -4.5)], "veil", 0.0, normal=(-0.3, -0.8, 0.6))
    r.poly([(-12.0, -0.3), (-6.0, -0.3), (-7.0, -2.0)], "silk", -0.5)
    r.stamp(WITCH_HEAD["hurt"], 9.0, -1.0, 1.0, WITCH_LEG, pivot=(3, 7))
    crystal(r, -9.0 if stage else -5.0, -0.3, 4.0, 2.0, "crys", 1.5, ang=70 if stage else 50)
    return r.resolve()


def witch_sheet(out):
    Vw = veil_witch
    idle = [Vw(bob=[0, 0.3, 0.6, 0.3][i], sway=[0, -0.4, -0.8, -0.4][i]) for i in range(4)]
    run = [Vw(bob=-0.4 * abs(math.sin(i / 6 * math.tau)), lean=6, sway=-2.0 - math.sin(i / 6 * math.tau), hem=1.0,
              hand=(6.5, -12.0 + math.sin(i / 6 * math.tau)), hand2=(-5.0, -9.0 - math.sin(i / 6 * math.tau))) for i in range(6)]
    # Shard (7): draw the wand back (0-1), flick (2, smear), the shard leaves the tip at (13, -12) (3), follow through
    shard = [Vw(hand=(2.0, -15.0), wand_ang=-110, lean=-4, glow=1, face="cast"),
             Vw(hand=(0.0, -17.0), wand_ang=-140, lean=-8, glow=2, face="cast"),
             Vw(hand=(6.0, -15.0), wand_ang=-40, lean=4, glow=2, face="cast", extra=lambda r: arc_smear(r, 1, -14, 8, -130, -30, "vglow", 1)),
             Vw(hand=(8.0, -12.0), wand_ang=-5, lean=8, glow=1, face="cast", extra=lambda r: sparkle(r, 15, -12, 1, "white")),
             Vw(hand=(7.0, -10.0), wand_ang=20, lean=5), Vw(hand=(6.5, -10.5), wand_ang=-10), Vw()]
    # Crystals (8): both arms rise (0-3), the wand glows brighter (the hero's pips flash), she casts (4), lowers (5-7)
    cr = [Vw(hand=(5.0, -14.0), hand2=(-5.0, -13.0), wand_ang=-60, glow=1, face="cast"),
          Vw(hand=(4.0, -17.0), hand2=(-5.0, -16.0), wand_ang=-80, glow=1, face="cast", bob=-0.4),
          Vw(hand=(3.0, -20.0), hand2=(-4.0, -19.0), wand_ang=-90, glow=2, face="cast", bob=-0.8, hem=1.0),
          Vw(hand=(3.0, -21.0), hand2=(-4.0, -20.0), wand_ang=-90, glow=2, face="cast", bob=-1.0, hem=1.5,
             extra=lambda r: [sparkle(r, -9, -18, 2, "vglow"), sparkle(r, 10, -16, 2, "vglow")]),
          Vw(hand=(7.0, -12.0), hand2=(-7.0, -11.0), wand_ang=10, glow=2, face="cast", hem=2.0, lean=4,
             extra=lambda r: [sparkle(r, 13, -9, 1, "vglow"), flakes(r, [(10, -4, 3), (-9, -6, 3), (12, -16, 2)])]),
          Vw(hand=(6.5, -11.0), hand2=(-5.0, -10.0), wand_ang=0, glow=1), Vw(), Vw()]
    d0 = Vw(lean=-12, face="hurt", hand=(4.0, -16.0), hand2=(-7.0, -14.0), wand_ang=-120)
    d1 = Vw(lean=-34, face="hurt", bob=2.0, hand=(2.0, -13.0), hand2=(-9.0, -10.0), wand_ang=160)
    knock = Vw(lean=-16, face="hurt", hand=(4.0, -15.0), hand2=(-7.0, -13.0), wand_ang=-100)
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.08] * 6),
             ("Shard", shard, [0.12, 0.12, 0.05, 0.08, 0.1, 0.1, 0.1]),
             ("Crystals", cr, [0.1, 0.1, 0.1, 0.12, 0.08, 0.1, 0.1, 0.1])]
    anims += tail_anims(idle[0], [d0, d1, witch_corpse(0), witch_corpse(1)], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("YsvVeilWitch", anims, out, scale=6)


# ================================================================== RIME KNIGHT: rime-crusted plate and a two-handed crystal sword
KNIGHT_LEG = {"a": ("steel", 0), "b": ("steel", 1), "c": ("steel", 2), "d": ("steel", 3), "D": ("steel", 4),
              "f": ("frost", 3), "F": ("frost", 4), "e": ("eye", 3), "E": ("eye", 4)}
KNIGHT_HEAD = {
    # pivot (3, 7): the neck. A great helm crusted with rime, a glowing T visor
    "calm": """
.FFf...
FddddFb
fdcccdb
deEEecb
dcEecbb
dccecbb
bbbbbba
.bccba.
""",
    "hurt": """
.FFf...
FddddFb
fdcccdb
dcaacbb
dcaacbb
dccacbb
bbbbbba
.bccba.
""",
}


def sword(r, hx, hy, ang, z, frost_k=0, length=14.0):
    """A two-handed crystal greatsword from the grip (hx, hy): steel hilt, a long clear-blue crystal blade."""
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a); px, py = -uy, ux
    r.line(hx - ux * 2.5, hy - uy * 2.5, hx + ux * 1.5, hy + uy * 1.5, "steel", z, tone=1)
    gx, gy = hx + ux * 1.5, hy + uy * 1.5
    r.line(gx - px * 2.2, gy - py * 2.2, gx + px * 2.2, gy + py * 2.2, "steel", z + 0.01, tone=3)
    b0 = (gx + ux, gy + uy); tip = (gx + ux * length, gy + uy * length)
    r.poly([(b0[0] + px * 1.4, b0[1] + py * 1.4), (tip[0] + px * 0.4 - ux * 2, tip[1] + py * 0.4 - uy * 2), tip,
            (tip[0] - px * 0.4 - ux * 2, tip[1] - py * 0.4 - uy * 2), (b0[0] - px * 1.4, b0[1] - py * 1.4)],
           "ice", z + 0.02, normal=(-0.5 * px - 0.3, -0.5 * py - 0.5, 0.7), bias=0.1)
    r.line(b0[0], b0[1], tip[0] - ux * 2, tip[1] - uy * 2, "ice", z + 0.03, tone=4)
    if frost_k:
        for k in range(frost_k):
            sparkle(r, tip[0] + ux * k * 1.5, tip[1] + uy * k * 1.5 + 1, 2 if k else 1, "white", z + 1)
    return tip


def rime_knight(bob=0.0, lean=0.0, feet=((-3.0, 0.0), (3.0, 0.0)), hands=((3.0, -12.0), (5.0, -11.0)), sword_ang=-120.0,
                face="calm", extra=None, frost_k=0, plates=0, sword_z=-2.0):
    r = Rig(1.1)
    T = Xf(lean, (0.0, -1.0))
    hip = T(0.0, -7.2 + bob)
    # a frost-stiff cloak behind, hanging from the shoulders and flaring at the hem
    r.poly([T(-4.0, -14.5 + bob), T(3.0, -14.5 + bob), T(1.0, -1.0), T(-8.0, -0.6), T(-10.5, -2.0)], "robe", -3.0, bias=-0.1, curve=0.5)
    rime_fringe(r, [(x, -1.5) for x in range(-10, 1)], -2.9, step=2, seed=7)
    legs2(r, hip, feet, "steel", 0.0, 4.2, 3.8, rad=(1.7, 1.4, 1.2), boot="steel")
    # plate: a broad breastplate under rime, a fauld of steel bands
    ch = T(0.0, -11.8 + bob)
    r.ell(ch[0], ch[1], 5.8, 4.8, "steel", 0.5, bias=0.05)
    r.ell(ch[0] - 1.0, ch[1] - 2.6, 3.6, 1.2, "frost", 0.52, bias=0.1)        # rime crust on the breastplate
    r.dot(ch[0] + 0.5, ch[1] + 0.5, "ice", 3, 0.55); r.dot(ch[0] + 0.5, ch[1] + 1.5, "ice", 2, 0.55)
    # plate edges: a lit rim along the breastplate and each fauld band
    for x in range(-4, 5): r.dot(*T(x, -11.8 - 4.2 + abs(x) * 0.35 + bob), "steel", 4, 0.53)
    for yb in (-8.2, -7.0): r.line(*T(-4.0, yb + bob), *T(4.0, yb + bob), "steel", 0.61, tone=4 if yb < -8 else 1)
    r.poly([T(-4.4, -8.2 + bob), T(4.4, -8.2 + bob), T(3.4, -5.8 + bob), T(-3.8, -5.8 + bob)], "steel", 0.6, normal=(-0.2, -0.3, 1.0))
    rime_fringe(r, [T(x, -8.4 + bob) for x in range(-4, 5)], 0.65, step=2, seed=5)
    # rime crust across the shoulders, pauldrons
    for sx, zz in ((-5.2, -0.6), (5.0, 1.2)):
        r.ell(*T(sx, -14.6 + bob), 3.2, 2.4, "steel", zz, bias=0.15 if sx > 0 else -0.2)
        r.ell(*T(sx - 0.4, -16.2 + bob), 2.4, 0.9, "frost", zz + 0.01, flat=3 if sx < 0 else 4)
    # the sword (behind the body when it rests on the shoulder), then the arms over it
    sword(r, hands[0][0], hands[0][1], sword_ang, sword_z, frost_k)
    arm(r, T(-4.2, -13.8 + bob), hands[0], "steel", -0.5 if sword_z < 0 else 2.0, 3.6, 3.8, rad=(1.2, 1.0, 1.0), bias=-0.2)
    arm(r, T(4.2, -13.8 + bob), hands[1], "steel", 2.1, 3.6, 3.8, rad=(1.3, 1.1, 1.1))
    hx, hy = T(0.5, -16.4 + bob)
    r.stamp(KNIGHT_HEAD[face], hx, hy, 3.0, KNIGHT_LEG, pivot=(3, 7))
    for k in range(plates):
        r.ell(*T(-7.5 + k * 15.0, -12.0 + bob), 1.8, 3.0, "ice", 4.0, bias=0.3)
    if extra: extra(r)
    return r.resolve()


def knight_corpse(stage):
    r = Rig()
    r.ell(-1.0, -3.0, 6.5, 3.0, "steel", 0.0)
    r.tube([(4.0, -2.0), (9.0, -1.5)], [1.4, 1.2], "steel", 0.2)
    r.stamp(KNIGHT_HEAD["hurt"], -9.0, -0.5, 1.0, KNIGHT_LEG, pivot=(3, 7))
    sword(r, 2.0, -6.0 if stage == 0 else -1.0, -10 if stage == 0 else 0, 2.0)
    rime_fringe(r, [(x, -5.8) for x in range(-6, 5)], 0.5, step=2)
    return r.resolve()


def knight_sheet(out):
    K = rime_knight
    rest = dict(hands=((4.0, -10.5), (5.5, -11.5)), sword_ang=78, sword_z=3.0)
    idle = [K(bob=[0, 0.3, 0.6, 0.3][i], **rest) for i in range(4)]
    run = []
    for i in range(6):
        (fa, la), (fb, lb) = walk(i, stride=3.4)
        run.append(K(bob=-0.5 * abs(math.sin(i / 6 * math.tau)), lean=6, feet=((-1.0 + fa, la), (1.0 + fb, lb)),
                     hands=((4.5, -11.0 + 0.5 * math.sin(i / 6 * math.tau)), (6.0, -12.0)), sword_ang=35, sword_z=3.0))
    # Cleave (8): lift the blade high behind (0-2), swing over (3, smear), STRIKE the floor ahead (4: frost spreads from
    # the tip at (17, -2)), hold (5), lift (6-7)
    cleave = [K(hands=((1.0, -16.0), (2.5, -15.5)), sword_ang=-150, lean=-4),
              K(hands=((-1.0, -19.0), (0.5, -18.5)), sword_ang=-175, lean=-10, bob=-0.5),
              K(hands=((-1.5, -20.0), (0.0, -19.5)), sword_ang=170, lean=-12, bob=-0.6),
              K(hands=((5.0, -18.0), (6.5, -17.0)), sword_ang=-60, lean=4, sword_z=3.0,
                extra=lambda r: arc_smear(r, 2, -14, 15, -175, -60, "snow", 2)),
              K(hands=((8.0, -9.0), (9.5, -8.5)), sword_ang=30, lean=14, sword_z=3.0, frost_k=3, bob=1.0,
                extra=lambda r: [snow_puff(r, 18, 0, 0, 1.2), flakes(r, [(20, -3, 4), (22, -1, 3), (15, -1, 3)])]),
              K(hands=((8.0, -9.0), (9.5, -8.5)), sword_ang=30, lean=12, sword_z=3.0, frost_k=2, bob=1.0,
                extra=lambda r: snow_puff(r, 18, 0, 1, 1.2)),
              K(hands=((5.0, -12.0), (6.5, -11.0)), sword_ang=-40, lean=4, sword_z=3.0), K(**rest)]
    # Plate (7): plant the sword point-down (0-2), frost climbs it (3), two ice plates form (4), stand (5-6)
    plate = [K(hands=((4.0, -12.0), (5.5, -12.0)), sword_ang=80, sword_z=3.0),
             K(hands=((4.5, -14.0), (6.0, -14.0)), sword_ang=88, sword_z=3.0, bob=-0.5),
             K(hands=((4.5, -11.0), (6.0, -11.0)), sword_ang=90, sword_z=3.0, bob=0.8, extra=lambda r: snow_puff(r, 5, 0, 0)),
             K(hands=((4.5, -11.0), (6.0, -11.0)), sword_ang=90, sword_z=3.0, bob=0.8, frost_k=1),
             K(hands=((4.5, -11.0), (6.0, -11.0)), sword_ang=90, sword_z=3.0, plates=2,
               extra=lambda r: [sparkle(r, -8, -18, 1, "white"), sparkle(r, 8, -18, 1, "white")]),
             K(hands=((4.0, -12.0), (5.5, -12.0)), sword_ang=80, sword_z=3.0), K(**rest)]
    d0 = K(lean=-12, face="hurt", hands=((0.0, -15.0), (2.0, -14.0)), sword_ang=-160)
    d1 = K(lean=-30, face="hurt", bob=2.0, hands=((-2.0, -12.0), (0.0, -11.0)), sword_ang=160)
    knock = K(lean=-14, face="hurt", hands=((1.0, -15.0), (3.0, -14.0)), sword_ang=-150)
    anims = [("Idle", idle, [0.18, 0.16, 0.18, 0.16]), ("Run", run, [0.09] * 6),
             ("Cleave", cleave, [0.12, 0.12, 0.1, 0.05, 0.08, 0.12, 0.1, 0.1]),
             ("Plate", plate, [0.1, 0.1, 0.1, 0.12, 0.12, 0.1, 0.1])]
    anims += tail_anims(idle[0], [d0, d1, knight_corpse(0), knight_corpse(1)], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("YsvRimeKnight", anims, out, scale=6)


# ================================================================== SHARD HERMIT: a bent old hermit with a cracked geode on his back
HERMIT_LEG = {"h": ("robe", 1), "H": ("robe", 2), "j": ("robe", 3), "s": ("skin", 2), "S": ("skin", 3), "k": ("skin", 1),
              "b": ("frost", 4), "B": ("frost", 3), "c": ("frost", 2), "e": ("vglow", 3), "m": ("robe", 0)}
HERMIT_HEAD = {
    # pivot (2, 6): the neck. A deep hood, a long nose, a beard of hoarfrost
    "calm": """
.hHj..
hHjjH.
hmSSSk
hmeSSs
hhSkSk
.hbBbc
..bBc.
...c..
""",
    "hurt": """
.hHj..
hHjjH.
hmSSSk
hmmSSs
hhSkSk
.hbBbc
..bBc.
...c..
""",
}


def geode_lump(r, cx, cy, rad, z, crack=0):
    """The cracked geode he carries: rough rind outside, violet crystal teeth in the crack."""
    r.ell(cx, cy, rad, rad * 0.9, "rock", z, bias=0.05)
    for k in range(3 + crack):
        a = math.radians(-60 + k * 22)
        crystal(r, cx + math.cos(a) * rad * 0.35, cy + math.sin(a) * rad * 0.35 + 1.0, 2.5 + (k % 2) + crack * 0.4, 1.8, "crys", z + 0.1,
                ang=math.degrees(a) + 90)


def hermit(bob=0.0, lean=0.0, feet=((-2.5, 0.0), (2.5, 0.0)), hand=(6.0, -9.0), staff_ang=-95.0, face="calm", extra=None,
           glow=0, staff_len=17.0):
    r = Rig(1.25)
    T = Xf(lean, (0.0, -1.0))
    legs2(r, T(0.0, -6.0 + bob), feet, "robe", 0.0, 3.4, 3.2, rad=(1.3, 1.1, 0.9), boot="wood")
    # a bent back: robe hunched forward, the geode lump high on the back
    pts = [T(-5.0, -7.0 + bob), T(-5.5, -12.0 + bob), T(-2.0, -16.0 + bob), T(3.0, -15.0 + bob), T(5.0, -11.0 + bob),
           T(4.0, -6.5 + bob), T(5.0, -1.0), T(-5.5, -1.0)]
    r.poly(pts, "robe", 0.5, curve=0.8)
    for x in range(-5, 5, 2): r.dot(*T(x, -1.0), "frost", 3, 0.55)
    geode_lump(r, *T(-3.8, -15.0 + bob), 5.8, -0.5, crack=2)
    # staff: wood shaft, a crystal head
    sx, sy = hand
    a = math.radians(staff_ang)
    top = (sx + math.cos(a) * staff_len * 0.45, sy + math.sin(a) * staff_len * 0.45)
    bot = (sx - math.cos(a) * staff_len * 0.55, sy - math.sin(a) * staff_len * 0.55)
    r.line(*bot, *top, "wood", 1.6, tone=2)
    crystal(r, top[0], top[1] + 1.0, 4.5, 2.6, "crys", 1.7, ang=staff_ang + 90)
    if glow:
        tip = (top[0] + math.cos(a) * 4.0, top[1] + math.sin(a) * 4.0)
        sparkle(r, tip[0], tip[1], 1 if glow > 1 else 2, "vglow", 2.5)
    arm(r, T(2.5, -13.0 + bob), hand, "robe", 1.8, 3.4, 3.4, rad=(1.1, 0.9, 0.8))
    r.dot(hand[0], hand[1], "skin", 3, 1.9)
    r.stamp(HERMIT_HEAD[face], *T(4.0, -14.0 + bob), 2.0, HERMIT_LEG, pivot=(2, 6))
    if extra: extra(r)
    return r.resolve()


def hermit_corpse(stage):
    r = Rig()
    r.poly([(-8.0, -0.3), (6.0, -0.3), (5.0, -4.0), (-6.0, -4.5)], "robe", 0.0, curve=0.6)
    geode_lump(r, -8.0, -4.0, 4.5, 0.5, crack=2)
    r.stamp(HERMIT_HEAD["hurt"], 8.0, -1.0, 1.0, HERMIT_LEG, pivot=(2, 6))
    r.line(-2.0, -0.5, 12.0, -0.5 - stage, "wood", 1.0, tone=2)
    crystal(r, 13.0, -0.5 - stage, 3.0, 2.0, "crys", 1.2, ang=80)
    return r.resolve()


def hermit_sheet(out):
    Hm = hermit
    idle = [Hm(bob=[0, 0.3, 0.6, 0.3][i], hand=(6.0, -9.0 + [0, 0.2, 0.4, 0.2][i])) for i in range(4)]
    run = []
    for i in range(6):
        (fa, la), (fb, lb) = walk(i, stride=2.6)
        run.append(Hm(bob=-0.4 * abs(math.sin(i / 6 * math.tau)), lean=8, feet=((-1.0 + fa, la), (1.0 + fb, lb)),
                      hand=(7.0, -9.0 + 0.6 * math.sin(i / 6 * math.tau)), staff_ang=-80))
    # Jab (7): draw the staff back (0-1), THRUST the crystal end forward (2-3: hit at frame 3, tip at (22, -10)), return
    jab = [Hm(hand=(3.0, -10.0), staff_ang=-170, lean=-4), Hm(hand=(1.0, -10.5), staff_ang=-178, lean=-8, glow=1),
           Hm(hand=(9.0, -10.0), staff_ang=-180, lean=8, glow=1, extra=lambda r: r.line(0, -10, 6, -10, "snow", 4, tone=2)),
           Hm(hand=(11.0, -10.0), staff_ang=-180, lean=12, glow=2, extra=lambda r: sparkle(r, 23, -10, 1, "white")),
           Hm(hand=(8.0, -10.0), staff_ang=-175, lean=6), Hm(hand=(6.0, -9.5), staff_ang=-120), Hm()]
    # Plant (8): raise the staff (0-2), the crystal head glows (3), SLAM it down (4: a spike rises by the hero), hold (5-7)
    plant = [Hm(hand=(5.0, -12.0), staff_ang=-95, glow=1), Hm(hand=(5.0, -15.0), staff_ang=-92, glow=1, bob=-0.4),
             Hm(hand=(5.0, -18.0), staff_ang=-90, glow=2, bob=-0.8), Hm(hand=(5.0, -18.5), staff_ang=-90, glow=2, bob=-0.9),
             Hm(hand=(6.0, -8.0), staff_ang=-90, glow=2, bob=0.6, lean=6,
                extra=lambda r: [snow_puff(r, 7, 0, 0), sparkle(r, 12, -4, 1, "vglow"), sparkle(r, 2, -3, 2, "vglow")]),
             Hm(hand=(6.0, -8.0), staff_ang=-90, glow=1, bob=0.6, lean=6, extra=lambda r: snow_puff(r, 7, 0, 1)),
             Hm(hand=(6.0, -9.0), staff_ang=-92), Hm()]
    d0 = Hm(lean=-10, face="hurt", hand=(4.0, -12.0), staff_ang=-130)
    d1 = Hm(lean=-30, face="hurt", bob=2.0, hand=(2.0, -9.0), staff_ang=150)
    knock = Hm(lean=-12, face="hurt", hand=(4.0, -11.0), staff_ang=-120)
    anims = [("Idle", idle, [0.2, 0.16, 0.2, 0.16]), ("Run", run, [0.09] * 6),
             ("Jab", jab, [0.12, 0.12, 0.05, 0.08, 0.1, 0.1, 0.1]),
             ("Plant", plant, [0.1, 0.1, 0.1, 0.12, 0.06, 0.12, 0.1, 0.1])]
    anims += tail_anims(idle[0], [d0, d1, hermit_corpse(0), hermit_corpse(1)], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("YsvHermit", anims, out, scale=6)


JOBS = [("YsvWeaver", weaver_sheet), ("YsvLurker", lurker_sheet), ("YsvSilkmoth", silkmoth_sheet),
        ("YsvVeilWitch", witch_sheet), ("YsvRimeKnight", knight_sheet), ("YsvHermit", hermit_sheet)]
SYNC = {
    "YsvWeaver": {"Fangs": [("BITE: fangs at (12, -4); box 16 x 14 at (11, -4)", 3)],
                  "Tether": [("the silk line fires from the spinnerets at (6, -19)", 3)]},
    "YsvLurker": {"Bite": [("BITE: fangs at (11, -3); box 14 x 12 at (11, -4)", 3)],
                  "Snare": [("two snares are flicked at the hero", 4)]},
    "YsvSilkmoth": {"Volley": [("three needles leave at (8, -12)", 3)],
                    "Dive": [("DIVE: moving 210 px/s, the body hit on (4, -8); frost wake laid 3-5", 3)]},
    "YsvVeilWitch": {"Shard": [("shard leaves the wand tip at (13, -12)", 3)],
                     "Crystals": [("the crystals start growing round the hero", 4)]},
    "YsvRimeKnight": {"Cleave": [("STRIKE: the blade hits the floor ahead (OrcSwipe box from (3, -8)); Frozen Edge ice at (18, 0)", 4)],
                      "Plate": [("two ice plates form", 4)]},
    "YsvHermit": {"Jab": [("THRUST: the crystal tip at (22, -10); box 16 x 10 at (14, -10)", 3)],
                  "Plant": [("SLAM: a crystal spike is planted by the hero", 4)]},
}
NOTES = {
    "YsvSilkmoth": "Flies 10 px over its shadow; the trailing cocoon silk sways with the idle and run.",
    "YsvLurker": "The frost lid hides all but its red eyes while it waits (Idle); Run lifts it a crack.",
}
