"""The Gilded Secret, redrawn with the material renderer (ghosts_v2_kit, from jinx_v2_rigs): the Hoard Wyrm.

    python3 goldsecret_v2.py [outdir] [--only GoldWyrm]

goldsecret_rigs.py builds the rest of the line and calls this file for the sheets listed in JOBS. Same anims, frame
counts, durations and spawn points as before (art/out_goldsecret/TIMING.md): Maul HIT on 3 with the jaws at (31, -8),
Breath RELEASE on 4 with the pour reaching the floor at (25, -1).
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ghosts_v2_kit import Rig, stone, chain, ik, lerp, sheet, tail, spark, puff, outdir_for, Xf, add_ramps  # noqa: E402

OUT = outdir_for("out_goldsecret")
# Crawl's palette: tarnished gold and faded crimson; the emerald keyhole eye is the one bright accent
add_ramps({
    "emer":  ["0a2a1c", "125c3c", "34b870", "a8ffcc", "eafff2"],     # the line's emerald keyhole eye
    "ruby":  ["2e1216", "54222a", "7a3440", "9a4e58", "b87078"],
    "molt":  ["3a1e10", "7a4220", "b0702e", "d8a050", "ecd090"],     # molten gold
    "wingc": ["241418", "42222a", "62343c", "7e4a50", "9a6a68"],     # crimson wing membrane
    "ggold": ["3a2a12", "6e5428", "9e8040", "c4a862", "e0cc94"],     # the line's gold leaf
    "ggold1": ["322616", "5e4a2c", "86703e", "a89058", "c0ac80"],    # dulling as it dies
    "ggold2": ["2a2218", "4c4030", "6c5e44", "887a5c", "a09478"],
}, emissive={"emer", "molt"}, shiny={"ruby", "ggold"})
GM = ["ggold"]          # the gold material in use (the death frames dull it)


def keyhole(r, x, y, glow, z, big=False):
    """The line's signature: an emerald keyhole set in a gold plate."""
    r.ell(x, y, 1.9 if big else 1.5, 1.9 if big else 1.6, GM[0], z, bias=0.15)
    r.dot(x, y - 0.5, "emer", 3 if glow else 2, z + 0.01)
    r.dot(x, y + 0.5, "emer", 4 if glow > 1 else 2, z + 0.01)
    if big: r.dot(x, y + 1.3, "emer", 1, z + 0.01)


def coin(r, x, y, z, edge=False):
    if edge:
        r.line(x - 1, y, x + 1, y, GM[0], z, tone=3)
    else:
        r.ell(x, y, 1.2, 1.0, GM[0], z, bias=0.35)
        r.dot(x - 0.3, y - 0.3, GM[0], 4, z + 0.01)


# ================================================================== HOARD WYRM (T3)
def wyrm_head(r, hx, hy, ang, gape, eye, glow, z, pour=0.0):
    """Lid-jaw head: the upper jaw a gilded chest lid with fangs, the lower jaw iron, a keyhole eye, key-bit horns.
    (hx, hy) = the jaw hinge; ang tilts the head (+ = nose down); gape opens the jaw (deg)."""
    T = Xf(ang, (hx, hy))
    Tl = Xf(ang + gape, (hx, hy))
    # lower jaw (iron), drawn first: it swings down about the hinge
    r.poly([Tl(hx - 1.0, hy), Tl(hx + 9.5, hy + 0.2), Tl(hx + 9.0, hy + 2.0), Tl(hx + 1.0, hy + 3.0)], "iron", z + 0.1,
           normal=(0.1, 0.5, 1.0))
    if gape > 4:
        for k in range(3):
            r.dot(*Tl(hx + 3.0 + k * 2.4, hy - 0.6), "ivory", 4, z + 0.15)
        # the mouth's inside: dark, lit gold when it pours
        r.poly([T(hx, hy), T(hx + 9.0, hy), Tl(hx + 9.0, hy), Tl(hx, hy + 0.5)], "molt" if pour else "mouth", z + 0.05,
               flat=2 if pour else 1)
        if pour: r.dot(*T(hx + 5.5, hy + 1.2), "molt", 4, z + 0.06)
    # skull + upper jaw: an arched chest lid running forward to the snout
    r.ell(*T(hx - 1.5, hy - 2.6), 3.6, 3.2, GM[0], z + 0.2, ang=ang)
    lid = [T(hx - 1.0, hy - 5.0), T(hx + 4.0, hy - 4.6), T(hx + 9.0, hy - 3.0), T(hx + 10.5, hy - 1.2),
           T(hx + 10.0, hy + 0.3), T(hx - 1.0, hy + 0.3)]
    r.poly(lid, GM[0], z + 0.3, normal=(-0.2, -0.7, 1.0), curve=0.3)
    r.line(*T(hx + 0.5, hy - 0.6), *T(hx + 9.8, hy - 0.5), GM[0], z + 0.32, tone=1)        # the lid's lip band
    r.line(*T(hx + 3.0, hy - 4.6), *T(hx + 3.0, hy - 0.8), "iron", z + 0.33, tone=3)          # iron strap
    for k in range(3):
        r.dot(*T(hx + 4.4 + k * 2.2, hy + 0.9), "ivory", 4 if k % 2 == 0 else 3, z + 0.34)  # upper fangs
    r.dot(*T(hx + 10.0, hy - 1.8), "mouth", 1, z + 0.35)                                       # nostril
    # key-bit horns sweeping back from the crown
    for k, (dx, ln, zz) in enumerate(((-2.5, 5.5, -0.4), (-0.8, 5.0, 0.4))):
        b0 = T(hx + dx, hy - 5.0)
        a0 = -160 + ang
        pts = chain(b0[0], b0[1], [(ln * 0.55, a0 - 12), (ln * 0.45, a0 - 30)])
        r.tube(pts, [1.0, 0.8, 0.5], GM[0], z + zz, bias=-0.25 if k == 0 else 0.1)
        ex, ey = pts[-1]
        r.dot(ex, ey - 1, GM[0], 2 if k == 0 else 3, z + zz + 0.01); r.dot(ex - 1, ey - 1, GM[0], 2 if k == 0 else 3, z + zz + 0.01)
    keyhole(r, *T(hx + 1.6, hy - 2.6), glow, z + 0.4)
    if eye == 0:
        r.dot(*T(hx + 1.6, hy - 2.6), "iron", 1, z + 0.45)


def wing(r, root, spread, z, near):
    """A half-folded crimson wing: a gold arm bone rising back from the shoulder, three finger bones fanning down from
    its wrist, the membrane stretched between them in scallops."""
    sx, sy = root
    wr = (sx - 4.0 - spread * 3.0, sy - 9.0 - spread * 3.0)                 # the wrist
    tips = [(wr[0] - 9.0 - spread * 3, wr[1] + 3.0 + k * 3.2 - spread * 2 * (2 - k)) for k in range(3)]
    tips[0] = (tips[0][0] + 2.0, tips[0][1] - 1.5)
    mem = [root, wr, tips[0]]
    for t0, t1 in zip(tips, tips[1:]):
        mem += [((t0[0] + t1[0]) / 2 + 1.6, (t0[1] + t1[1]) / 2), t1]
    mem += [(sx - 6.0, sy + 1.0)]
    r.poly(mem, "wingc", z, normal=(-0.35, -0.55, 1.0), bias=0.1 if near else -0.3)
    for t in tips:
        r.line(wr[0], wr[1], t[0], t[1], GM[0], z + 0.01, tone=2 if near else 1)
    r.tube([root, ((root[0] + wr[0]) / 2 + 0.6, (root[1] + wr[1]) / 2), wr], [1.3, 1.1, 0.9], GM[0], z + 0.02,
           bias=0.15 if near else -0.3)
    r.dot(wr[0] + 0.5, wr[1] - 1, "ivory", 4 if near else 2, z + 0.03)      # thumb claw


def wyrm(dx=0.0, dy=0.0, stride=0.0, ph=0.0, head=(12.0, -18.0), hang=0.0, gape=6.0, eye=1, glow=1, spread=0.0,
         tail_ph=0.0, rear=0.0, crouch=0.0, pour=0.0, feet=None, roll=0.0, spill=0, glint=None, legs_fold=0.0, dull=0):
    """Gold-scaled wyrm on four legs. head = the jaw hinge from the feet. rear lifts the chest (0..1); pour 0..1 the
    molten stream from the mouth to the floor; feet overrides the four foot points (far hind, far fore, near hind,
    near fore); roll tips the whole body over (death)."""
    GM[0] = ("ggold", "ggold1", "ggold2")[dull]
    r = Rig()
    bx, by = -2.0 + dx, -11.0 + dy + crouch
    tilt = -rear * 12.0 + roll
    T = Xf(tilt, (bx - 6.0, by + 4.0))
    hips, chest = T(bx - 7.0, by), T(bx + 5.0, by - 1.0)
    # gait: diagonal pairs (far fore + near hind, then the other two)
    s = stride
    if feet is None:
        feet = [(-10.0 + 2.6 * s * math.cos(ph + math.pi) + dx, -max(0.0, 1.6 * s * math.sin(ph + math.pi))),
                (6.0 + 2.6 * s * math.cos(ph) + dx, -max(0.0, 1.6 * s * math.sin(ph))),
                (-7.0 + 2.6 * s * math.cos(ph) + dx, -max(0.0, 1.6 * s * math.sin(ph))),
                (9.0 + 2.6 * s * math.cos(ph + math.pi) + dx, -max(0.0, 1.6 * s * math.sin(ph + math.pi)))]
    # far legs, far wing (behind the body)
    for k, (root, (fx, fy)) in enumerate(((hips, feet[0]), (chest, feet[1]))):
        kn = ik(root[0], root[1] + 2, fx, fy - 1.5, 5.0, 5.2, bend=1 if k == 0 else -1)
        r.tube([(root[0], root[1] + 2), kn, (fx, fy - 1.5)], [2.0, 1.4, 1.1], GM[0], -4.0, bias=-0.4)
        r.tube([(fx, fy - 1.5), (fx + 1.6, fy - 0.3)], [1.0, 0.8], GM[0], -3.9, bias=-0.4)
        r.dot(fx + 2.6, fy, "ivory", 2, -3.8)
    wing(r, T(bx - 1.0, by - 5.5), spread * 0.8, -3.0, False)
    # tail: from the hips, curling up and back, the key-bit tip
    tp = chain(*T(bx - 10.0, by + 0.5), [(2.0, 178 + 8 * math.sin(tail_ph)), (2.6, 205 + 12 * math.sin(tail_ph + 0.6)),
                                        (2.6, 235 + 14 * math.sin(tail_ph + 1.2)), (2.2, 270 + 16 * math.sin(tail_ph + 1.8))])
    if roll > 40: tp = [(x, min(y, -1.0)) for x, y in tp]
    r.tube(tp, [2.6, 2.1, 1.6, 1.1, 0.7], GM[0], -1.5, bias=-0.05)
    ex, ey = tp[-1]
    r.ell(ex, ey - 1.0, 1.6, 1.4, GM[0], -1.4, bias=0.2)       # key bow
    r.dot(ex, ey - 1.0, "mouth", 1, -1.35)
    # body: barrel of gold scale, iron-banded belly, gem-studded spine
    r.ell(*T(bx, by), 10.0, 6.4, GM[0], 0.0, ang=tilt)
    r.ell(*T(bx - 6.5, by + 0.6), 5.0, 5.0, GM[0], 0.05, ang=tilt)      # haunch
    r.ell(*T(bx + 6.0, by - 1.4), 4.8, 5.2, GM[0], 0.08, ang=tilt)      # shoulder
    for k in range(5):                                                   # belly plates
        x0 = bx - 7.0 + k * 3.4
        r.line(*T(x0, by + 4.2), *T(x0 + 2.6, by + 4.4), GM[0], 0.2, tone=1)
    r.line(*T(bx - 8.5, by + 2.6), *T(bx + 8.0, by + 2.8), "iron", 0.21, tone=2)       # the iron girth band
    for k in range(4):
        r.dot(*T(bx - 6.0 + k * 4.4, by + 2.7), "ivory", 3, 0.22)                   # rivets
    # the hoard stuck to its back: coins, a ruby, a sapphire, ridge spikes between them
    for k, (u, kind) in enumerate(((-7.5, "c"), (-4.5, "r"), (-1.5, "c"), (1.5, "s"), (4.5, "c"))):
        x, y = T(bx + u, by - 5.2 + abs(u) * 0.08)
        if kind == "c": coin(r, x, y, 0.4)
        elif kind == "r": r.ell(x, y, 1.1, 1.1, "ruby", 0.4, bias=0.2)
        else: r.ell(x, y, 1.1, 1.1, "chipb", 0.4, bias=0.2)
        sx_, sy_ = T(bx + u + 1.5, by - 5.6)
        r.poly([(sx_ - 1.0, sy_ + 0.6), (sx_ + 0.2, sy_ - 2.2), (sx_ + 1.0, sy_ + 0.6)], GM[0], 0.3, normal=(-0.4, -0.6, 1.0))
    # neck: from the shoulder up to the head
    nb = T(bx + 7.5, by - 3.0)
    hx, hy = head
    mid = ((nb[0] + hx) / 2 - 1.0, (nb[1] + hy) / 2 - 1.5 - rear * 1.5)
    r.tube([nb, mid, (hx - 1.0, hy - 1.5)], [3.6, 2.8, 2.4], GM[0], 0.6, bias=0.05)
    for k in range(3):                                                   # throat plates
        t = 0.25 + k * 0.25
        px_, py_ = lerp(nb[0], hx, t) + 1.4, lerp(nb[1], hy, t) + 1.2
        r.dot(px_, py_, GM[0], 1, 0.62)
    # near wing, near legs
    wing(r, T(bx + 1.5, by - 4.6), spread, 0.7, True)
    for k, (root, (fx, fy)) in enumerate(((hips, feet[2]), (chest, feet[3]))):
        kn = ik(root[0], root[1] + 2, fx, fy - 1.5, 5.0, 5.2, bend=1 if k == 0 else -1)
        if legs_fold: kn = (kn[0] - legs_fold * 2, kn[1] - legs_fold)
        r.tube([(root[0], root[1] + 1.5), kn, (fx, fy - 1.5)], [2.6, 1.8, 1.3], GM[0], 1.0, bias=0.0)
        r.tube([(fx, fy - 1.5), (fx + 1.8, fy - 0.3)], [1.2, 1.0], GM[0], 1.05)
        r.dots([(fx + 3.0, fy), (fx + 2.6, fy - 1)], "ivory", 4, 1.1)
    wyrm_head(r, hx, hy, hang, gape, eye, glow, 2.0, pour=pour)
    if pour > 0:
        # the molten stream from the jaws down to the floor, pooling where it lands
        Tm = Xf(hang, (hx, hy))
        mx, my = Tm(hx + 7.0, hy + 1.5)
        n = int(-my)
        for i in range(n + 1):
            y = my + i
            wob = 0.6 * math.sin(i * 0.9 + pour * 6)
            r.dot(mx + wob + i * 0.08, y, "molt", 4 if i % 3 == 0 else 3, 3.0)
            if pour > 0.5: r.dot(mx + wob + 1 + i * 0.08, y, "molt", 2, 2.99)
        r.ell(25.0, -0.6, 2.6 * pour + 0.8, 0.9, "molt", 3.0, flat=3)
    if spill:
        for (x, y) in ((14.0, -0.8), (17.0, -0.6), (-14.0, -0.8), (20.0, -1.0))[:spill]:
            coin(r, x, y, 3.0)
    if glint:
        for (x, y, k) in glint: spark(r, x, y, k, mat=GM[0], z=5.0)
    GM[0] = "ggold"
    return r.resolve()


def wyrm_sheet(outdir):
    W = wyrm
    idle = [W(), W(dy=-0.4, tail_ph=0.6, gape=8, spread=0.08), W(dy=-0.6, tail_ph=1.2, gape=10, spread=0.15, glow=2,
            glint=[(-6.0, -17.0, 1)]), W(dy=-0.3, tail_ph=1.8, gape=7, spread=0.05)]
    run = [W(stride=1.0, ph=i * math.pi / 3, dy=-0.8 * abs(math.sin(i * math.pi / 3)), tail_ph=i * 0.9,
             spread=0.12 * (i % 2), head=(13.0, -17.0 + 0.7 * math.sin(i * math.pi / 3)), hang=6) for i in range(6)]
    # MAUL: rear back (0-1), lunge with the jaws wide (2), HIT on 3 (the jaws shut at (31, -8)), worry, recover
    maul = [W(head=(11.0, -21.0), hang=-12, gape=14, crouch=0.5, rear=0.3),
            W(head=(8.0, -23.0), hang=-22, gape=30, rear=0.6, glow=2, spread=0.3, tail_ph=0.8),
            W(dx=3.0, head=(22.0, -12.0), hang=18, gape=34, crouch=1.0, spread=0.5, tail_ph=1.6,
              feet=[(-8.0, 0.0), (10.0, 0.0), (-4.0, 0.0), (14.0, 0.0)]),
            W(dx=3.5, head=(22.0, -9.0), hang=24, gape=2, crouch=1.6, spread=0.4, glow=2, tail_ph=2.2,
              feet=[(-8.0, 0.0), (10.0, 0.0), (-4.0, 0.0), (14.0, 0.0)]),
            W(dx=3.0, head=(21.0, -9.5), hang=16, gape=4, crouch=1.4, tail_ph=2.8,
              feet=[(-8.0, 0.0), (10.0, 0.0), (-4.0, 0.0), (14.0, 0.0)]),
            W(dx=1.5, head=(16.0, -14.0), hang=6, gape=8, crouch=0.6, tail_ph=3.4),
            W(head=(12.5, -17.5), hang=0, gape=6, tail_ph=4.0)]
    # BREATH: rear up and swell (0-2), the head drops and opens (3), the molten gold pours (RELEASE on 4), thins, recover
    breath = [W(rear=0.4, head=(10.0, -21.0), hang=-14, gape=6, spread=0.3),
              W(rear=0.8, head=(9.0, -24.0), hang=-26, gape=12, spread=0.7, glow=2),
              W(rear=1.0, head=(9.0, -25.0), hang=-30, gape=16, spread=1.0, glow=2, glint=[(9.0, -14.0, 1)]),
              W(rear=0.2, head=(17.0, -15.0), hang=30, gape=30, spread=0.8, glow=2, pour=0.2),
              W(rear=0.0, head=(17.5, -14.0), hang=36, gape=34, spread=0.6, glow=2, pour=1.0),
              W(rear=0.0, head=(17.5, -14.0), hang=36, gape=32, spread=0.5, glow=2, pour=0.9),
              W(rear=0.0, head=(17.0, -14.5), hang=30, gape=24, spread=0.4, pour=0.5),
              W(head=(15.0, -16.0), hang=14, gape=12, spread=0.2),
              W(head=(12.5, -17.5), hang=2, gape=7)]
    death = [W(rear=0.7, head=(9.0, -24.0), hang=-34, gape=30, eye=0, glow=0, spread=1.0),
             W(crouch=3.0, legs_fold=1.0, head=(15.0, -10.0), hang=30, gape=20, eye=0, glow=0, spread=0.6, spill=2,
               feet=[(-11.0, 0.0), (5.0, 0.0), (-8.0, 0.0), (8.0, 0.0)]),
             W(crouch=6.0, legs_fold=1.5, head=(16.0, -5.5), hang=40, gape=18, eye=0, glow=0, spread=1.2, spill=3, dull=1,
               feet=[(-12.0, 0.0), (4.0, 0.0), (-9.0, 0.0), (8.0, 0.0)], tail_ph=1.0),
             W(crouch=7.5, legs_fold=2.0, head=(17.0, -3.5), hang=50, gape=14, eye=0, glow=0, spread=1.4, spill=4, dull=2,
               feet=[(-12.0, 0.0), (3.0, 0.0), (-9.0, 0.0), (7.0, 0.0)], tail_ph=1.6)]
    knock = W(rear=0.5, dx=-1.5, head=(9.0, -22.0), hang=-24, gape=20, eye=0, spread=0.6)
    anims = [("Idle", idle, [0.24, 0.2, 0.24, 0.2]), ("Run", run, [0.08] * 6),
             ("Maul", maul, [0.12, 0.14, 0.05, 0.07, 0.12, 0.12, 0.12]),
             ("Breath", breath, [0.12, 0.14, 0.14, 0.06, 0.08, 0.08, 0.10, 0.12, 0.12])] + \
        tail(idle[0], death, [0.08, 0.12, 0.16, 0.4], knock)
    return sheet("GoldWyrm", anims, outdir, min_cell=(80, 54))


JOBS = [("GoldWyrm", wyrm_sheet)]


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    only = None
    if "--only" in a:
        i = a.index("--only"); only = set(a[i + 1].split(",")); del a[i:i + 2]
    outdir = a[0] if a else OUT
    os.makedirs(outdir, exist_ok=True)
    for n, fn in JOBS:
        if only is None or n in only: fn(outdir)


if __name__ == "__main__":
    main()
