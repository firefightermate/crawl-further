"""Kaurn tier 1: Rivet Imp, Spark Beetle, Coil Wisp (built through kaurn_v2_rigs.py). T1 idle limit 20 x 16."""
import math
from kaurn_v2_rigs import (Rig, lerp, msheet, tail_anims, leg, arm, hammer, bolt, crackle, spark, ember_spark, eye, shadow,
                           dust_puff, arc_smear, zig)


# ================================================================== RIVET IMP: a round soot imp with a rivet hammer bigger than its arm
IMP_FACE = {"k": ("soot", 0), "B": ("storm", 3), "b": ("storm", 2), "W": ("ivory", 3), "w": ("ivory", 2), "m": ("soot", 1),
            "e": ("ember", 2), "d": ("dkiron", 0)}
IMP_FACES = {
    # pivot (1, 0): the near eye
    "grin": "kB.kB\n.....\nmWwWm",
    "shout": "kB.kB\n.....\nmWWWm\n.mem.",
    "hurt": "bk.bk\n.....\n.mkm.",
    "dead": "d...d\n.d.d.\n.mmm.",
}


def imp(lean=0.0, bob=0.0, feet=((-2.5, 0.0), (2.5, 0.0)), hand=(4.8, -6.5), ham=-95.0, ham_ln=7.0, face="grin",
        pouch_open=False, flung=(), smear=None, sparks=(), squash=0.0, tail=0.0, hurt=False, extra=None, clang=False, ham_z=3.0):
    """lean: head lean px; ham: hammer angle (deg, screen space, -90 = straight up), held in the near hand."""
    r = Rig()
    if hurt and face == "grin": face = "hurt"
    by = -5.6 + bob + squash * 0.6
    hx = 0.0 + lean * 0.4
    # tail (behind): a soot whip with an iron barb
    tp = [(hx - 3.0, by + 1.5), (hx - 6.0, by + 0.5 + tail), (hx - 7.0, by - 2.0 + tail * 1.5)]
    r.tube(tp, [0.8, 0.6, 0.5], "soot", -2.0, bias=-0.2, thin=True)
    r.dot(tp[-1][0], tp[-1][1] - 1, "iron", 3, -1.9); r.dot(tp[-1][0] + 1, tp[-1][1] - 1, "iron", 2, -1.9)
    # legs: short, clawed iron-shod feet
    for k, f in enumerate(feet):
        z = -1.0 if k == 0 else 1.2
        leg(r, (hx + (-1.6 if k == 0 else 1.6), by + 2.8), f, 2.0, 2.0, "soot", z, rad=(1.2, 1.0), boot="dkiron",
            boot_len=1.8, bias=-0.3 if k == 0 else 0.0, thin=True)
    # one round soot body with the head sat on it (one part: no seam line through the middle)
    P = r.part(False, 0.0)
    r.ell(hx, by, 4.6, 4.2 - squash * 0.6, "soot", 0.0, bias=0.05, part=P)
    cx, cy = hx + 0.6 + lean * 0.6, by - 4.6 + squash * 0.4
    r.ell(cx, cy, 4.0, 3.4, "soot", 0.0, bias=0.12, part=P)
    # horn nubs and the swept-back ear
    r.tube([(cx - 1.6, cy - 2.6), (cx - 2.8, cy - 4.6)], [0.9, 0.4], "iron", 0.2, thin=True)
    r.tube([(cx + 1.2, cy - 2.8), (cx + 1.6, cy - 4.8)], [0.9, 0.4], "iron", 0.2, thin=True)
    r.poly([(cx - 3.2, cy - 0.8), (cx - 6.0, cy - 2.4), (cx - 3.4, cy + 1.0)], "soot", -0.1, bias=-0.15)
    # the leather pouch on the back hip, hot rivet heads showing
    px, py = hx - 3.4, by + 2.0
    r.poly([(px - 1.8, py - 1.4), (px + 1.6, py - 1.6), (px + 1.8, py + 1.8), (px - 2.0, py + 2.0)], "apron", 0.3, normal=(-0.3, -0.3, 1))
    r.dot(px - 0.2, py - 0.2, "brass", 3, 0.35)
    for i in range(3 if pouch_open else 2):
        r.dot(px - 1 + i * 1.2, py - 2.2, "ember", 3 if i % 2 == 0 else 4, 0.4)
    # the face (stamped: eyes, a grin of iron-filed teeth)
    r.stamp(IMP_FACES[face], cx + 0.6, cy - 0.4, 0.5, IMP_FACE, pivot=(1, 0))
    # the far arm hangs behind; the hammer arm in front
    r.tube([(hx - 2.8, by - 1.0), (hx - 4.2, by + 1.4)], [0.9, 0.8], "soot", -0.5, bias=-0.3, thin=True)
    if hand is not None:
        hammer(r, hand[0], hand[1], ham, ham_ln, ham_z, head=(5.0, 3.4), haft="wood", head_mat="dkiron", glow="ember", back=1.0)
        r.tube([(hx + 2.6, by - 1.2), (lerp(hx + 2.6, hand[0], 0.5) + 0.6, lerp(by - 1.2, hand[1], 0.5) + 0.8), hand],
               [1.1, 0.9, 0.9], "soot", ham_z + 0.2, thin=True)
        r.ell(hand[0], hand[1], 1.1, 1.0, "soot", ham_z + 0.3, bias=0.2, thin=True)
    for (x, y) in flung:
        r.dot(x, y, "ember", 4, 6.0); r.dot(x - 1, y, "ember", 2, 5.9)
    if smear:
        for pts, tn in smear: r.polyline(pts, "steam", 4.6, tone=tn)
    for (x, y, k) in sparks: spark(r, x, y, k, mat="ember" if k == 1 else "storm")
    if clang:
        spark(r, clang[0], clang[1], 1); spark(r, clang[0] + 4, clang[1] - 3, 1)
    if extra: extra(r)
    return r.resolve()


def imp_sheet(outdir):
    I = imp
    idle = [I(bob=[0, 0.4, 0.8, 0.4][i], ham=-62 + [0, 2, 3, 2][i], hand=(6.0, -5.8 + [0, 0.4, 0.8, 0.4][i]),
              tail=[0, 0.5, 1, 0.5][i]) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        f1 = (2.6 * math.cos(ph), -max(0.0, 1.6 * math.sin(ph)))
        f2 = (-2.6 * math.cos(ph), -max(0.0, -1.6 * math.sin(ph)))
        b = -0.8 * abs(math.sin(ph))
        run.append(I(lean=1.0, bob=b, feet=(f2, f1), ham=-100 + 8 * math.sin(ph), hand=(5.4, -6.8 + b), tail=math.sin(ph) * 1.5))
    # Bonk: hammer cocked over the back, heaved up, smear down, HIT on the floor at (12, -1), bounce, recover
    bonk = [I(lean=-1.0, squash=0.6, ham=-160, hand=(2.5, -10.0), face="shout"),
            I(lean=-1.5, bob=-0.8, ham=-185, hand=(1.0, -12.0), face="shout", feet=((-3.0, 0.0), (3.0, 0.0))),
            I(lean=1.5, ham=-40, hand=(5.5, -9.5), face="shout",
              smear=[([(2, -18), (7, -17), (11, -13), (13, -8)], 2), ([(4, -17), (9, -15), (12, -10)], 3)]),
            I(lean=2.0, squash=1.0, ham=28, hand=(6.0, -6.0), face="shout", feet=((-3.0, 0.0), (3.5, 0.0)),
              sparks=[(13, -2, 1), (10, -1, 2)], extra=lambda r: dust_puff(r, 12.0, 0.0, 0, 0.9)),
            I(lean=1.5, squash=0.4, ham=10, hand=(6.0, -7.0), sparks=[(14, -4, 2)], extra=lambda r: dust_puff(r, 12.0, 0.0, 1, 1.0)),
            I(lean=0.5, ham=-50, hand=(5.0, -8.5)),
            I(ham=-58, hand=(6.4, -5.8))]
    # Rivets: dig into the pouch, toss three hot rivets up, cock the hammer like a bat, swing (release at (10, -12))
    rivets = [I(lean=-0.5, pouch_open=True, ham=-120, hand=(3.5, -7.5)),
              I(lean=-0.5, ham=-140, hand=(3.0, -9.0), flung=[(3, -15), (5, -16), (7, -15)]),
              I(lean=-1.5, ham=-200, hand=(-1.0, -9.0), flung=[(4, -14), (6, -14), (8, -13)], face="shout"),
              I(lean=1.5, ham=-10, hand=(5.5, -9.5), face="shout", sparks=[(10, -12, 1)],
                smear=[([(-2, -16), (3, -16), (8, -14), (11, -11)], 3)]),
              I(lean=1.5, ham=40, hand=(5.0, -8.5), flung=[(15, -14), (16, -12), (15, -10)]),
              I(lean=0.5, ham=-40, hand=(5.0, -8.5)),
              I(ham=-58, hand=(6.4, -5.8))]
    d0 = I(lean=-2.0, ham=-150, hand=(1.0, -10.0), hurt=True, face="shout")
    d1 = I(lean=-3.5, bob=1.0, squash=1.0, ham=-200, hand=(-3.0, -7.0), hurt=True, face="shout")
    d2 = imp_corpse(0)
    corpse = imp_corpse(1)
    knock = I(lean=-2.5, ham=-140, hand=(1.5, -9.5), hurt=True, face="shout")
    anims = [("Idle", idle, [0.16, 0.12, 0.16, 0.12]), ("Run", run, [0.07] * 6),
             ("Bonk", bonk, [0.12, 0.12, 0.05, 0.08, 0.12, 0.12, 0.12]),
             ("Rivets", rivets, [0.12, 0.12, 0.12, 0.06, 0.12, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return msheet("KrnRivetImp", anims, outdir)


def imp_corpse(stage):
    r = Rig()
    # on its back, legs up, the hammer dropped beside it, the pouch spilt
    r.ell(0.0, -2.8, 4.6, 2.8, "soot", 0.0, bias=0.1)
    r.ell(-4.6, -2.6, 3.0, 2.4, "soot", 0.5)
    r.tube([(1.5, -4.0), (3.0, -7.0 + stage)], [1.0, 0.8], "soot", 0.8)
    r.tube([(3.0, -3.5), (5.5, -6.0 + stage)], [1.0, 0.8], "soot", 0.9)
    r.dot(-5.6, -3.4, "dkiron", 0, 0.7); r.dot(-3.8, -3.4, "dkiron", 0, 0.7)
    r.tube([(-9.0, -3.0), (-11.0, -6.0)], [0.6, 0.4], "iron", 0.4)
    hammer(r, 4.0, -1.0, -10 if stage else -30, 6.0, 1.5, head=(4.6, 3.4), head_mat="dkiron")
    for i in range(3): r.dot(-2 + i * 2, -0.5, "ember", 3 - stage, 1.6)
    if stage == 0: spark(r, -1.0, -6.0, 2)
    return r.resolve()


# ================================================================== SPARK BEETLE: a copper beetle with coiled antennae
def beetle(bob=0.0, legs=0.0, shell_open=0.0, ant=0.0, charged=False, ball=None, zap=None, sparks=(), hurt=False, roll=None,
           tip=False, extra=None):
    """legs: gait phase (rad); ant: antenna lift; charged: the shell sparks burn white (3 sparks stored);
    ball: (k, big) draws it curled into ball lightning instead (k = spin frame)."""
    r = Rig()
    if ball is not None:
        k, big = ball
        R = 6.5 if big else 4.5
        cy = -R - 0.5
        r.ell(0.0, cy, R, R, "copper", 1.0, bias=0.1)
        # shell ribs rotating
        for i in range(4):
            a = math.radians(k * 25 + i * 90)
            r.polyline([(math.cos(a) * 1.0, cy + math.sin(a) * 1.0), (math.cos(a) * R * 0.9, cy + math.sin(a) * R * 0.9)],
                       "verd", 1.1, tone=1)
        # the lightning sheath
        n = 14 if big else 10
        for i in range(n):
            a = i / n * math.tau + k * 0.7
            rr = R + 1.2 + (1 if (i + k) % 3 == 0 else 0)
            r.dot(math.cos(a) * rr, cy + math.sin(a) * rr, "storm" if not big else "spark", 3 if i % 2 else 4, 3.0)
        if big:
            for i in range(3):
                a = k * 1.3 + i * 2.1
                bolt(r, (math.cos(a) * R * 0.6, cy + math.sin(a) * R * 0.6), (math.cos(a) * (R + 4), cy + math.sin(a) * (R + 4)),
                     z=3.2, n=2, amp=1.0, seed=k * 3 + i, mat="spark")
        if extra: extra(r)
        return r.resolve()
    by = -4.0 + bob
    # six legs, jointed, copper
    for side, z in ((-1, -1.0), (1, 2.0)):
        for i, x in enumerate((-4.0, 0.0, 4.0)):
            ph = legs + i * 2.1 + (0 if side > 0 else math.pi)
            fx = x + 1.2 * math.cos(ph) + (1.0 if i == 2 else -0.5 if i == 0 else 0)
            fy = -max(0.0, 1.0 * math.sin(ph))
            kx = x + 0.8 * (1 if i == 2 else -1 if i == 0 else 0.3)
            r.polyline([(x, by + 1.5), (kx, by - 0.5 + side * -0.3), (fx, fy)], "copper", z, tones=[1 if side < 0 else 2, 1 if side < 0 else 2])
    # body: a ribbed copper dome over a darker underside, head and mandibles forward
    r.ell(0.0, by + 1.2, 7.4, 2.0, "dkiron", 0.0, bias=-0.2)
    r.ell(-0.5, by - 1.2, 7.8, 5.0, "copper", 0.5, bias=0.05, clip=lambda x, y: y <= by + 1.2)
    for i, x in enumerate((-4.5, -1.5, 1.5)):
        r.polyline([(x, by - 4.4 + abs(x) * 0.12), (x + 0.8, by + 0.8)], "verd", 0.6, tones=[2])
    if shell_open > 0:
        # elytra lift: a lit plate tilted up behind, wing membrane under it
        r.poly([(-7.0, by - 1.0), (-1.0, by - 4.8 - shell_open * 2), (1.0, by - 3.6 - shell_open * 3), (-6.0, by + 0.0)], "copper", 0.9,
               normal=(-0.5, -0.8, 0.4))
    r.ell(7.2, by + 0.4, 2.8, 2.4, "dkiron", 0.7, bias=0.1)
    r.dot(8.4, by - 0.2, "storm", 4, 0.9); r.dot(7.6, by - 0.2, "storm", 2, 0.9)   # eye
    r.polyline([(9.2, by + 1.4), (10.6, by + 2.0)], "verd", 0.8, tone=2)     # mandible
    # coiled antennae with blue-white tips
    for k, (sx, z) in enumerate(((6.0, 0.4), (7.6, 0.9))):
        lift = ant + k * 0.8
        pts = [(sx, by - 1.8), (sx + 1.0, by - 4.0 - lift), (sx + 0.2, by - 5.4 - lift), (sx + 1.6, by - 6.6 - lift * 1.2),
               (sx + 2.6, by - 7.6 - lift * 1.3)]
        r.polyline(pts, "brass", z, tones=[2, 3, 2, 3])
        r.dot(pts[-1][0], pts[-1][1], "storm", 4, z + 0.05)
        if zap: r.dot(pts[-1][0] + 1, pts[-1][1], "storm", 3, z + 0.05)
    # stored sparks on the shell: blue when building, white-hot when the beetle is full (the Overcharge tell)
    if charged:
        for i, (x, y) in enumerate(((-4.0, by - 5.6), (-0.5, by - 6.6), (3.0, by - 5.8))):
            spark(r, x, y, 2 if (i + int(bob * 4)) % 2 else 1, mat="spark")
    if hurt: r.dot(8.4, by - 0.4, "storm", 2, 0.95)
    if zap:
        bolt(r, (10.0, by - 8.4 - ant), zap, z=6.0, n=3, amp=1.2, seed=int(zap[0]))
    for (x, y, k) in sparks: spark(r, x, y, k)
    if tip:
        pass
    if extra: extra(r)
    return r.resolve()


def beetle_sheet(outdir):
    B = beetle

    def idle(ch):
        return [B(bob=[0, 0.3, 0.5, 0.3][i], ant=[0, 0.5, 1, 0.5][i], legs=0.0, charged=ch) for i in range(4)]

    def run(ch):
        return [B(bob=-0.4 * abs(math.sin(i / 6 * math.tau)), legs=i / 6 * math.tau, ant=-0.5, charged=ch) for i in range(6)]
    zap = [B(ant=1.0), B(ant=2.0, bob=0.5), B(ant=-0.5, bob=-0.5, sparks=[(10, -12, 3)]),
           B(ant=-1.0, zap=(15.0, -9.0), sparks=[(15, -9, 1)]), B(ant=0.0, sparks=[(16, -9, 2)]), B(ant=0.5)]

    def rush(big):
        return [B(bob=1.0, shell_open=0.6, ant=-1.0, charged=big), B(ball=(0, big)), B(ball=(1, big)), B(ball=(2, big)),
                B(ball=(3, big)), B(ball=(4, big)), B(bob=0.5, shell_open=0.4, sparks=[(-4, -9, 2)])]
    d0 = B(bob=-1.0, hurt=True, ant=2.0)
    d1 = beetle_corpse(0)
    d2 = beetle_corpse(1)
    corpse = beetle_corpse(2)
    knock = B(bob=-1.0, hurt=True, ant=1.5, shell_open=0.4)
    idle0 = idle(False)
    anims = [("Idle", idle0, [0.16, 0.12, 0.16, 0.12]), ("Run", run(False), [0.06] * 6),
             ("IdleCharged", idle(True), [0.16, 0.12, 0.16, 0.12]), ("RunCharged", run(True), [0.06] * 6),
             ("Zap", zap, [0.12, 0.12, 0.1, 0.06, 0.1, 0.12]),
             ("Rush", rush(False), [0.14, 0.06, 0.06, 0.06, 0.06, 0.08, 0.12]),
             ("RushBig", rush(True), [0.14, 0.06, 0.06, 0.06, 0.06, 0.08, 0.12])]
    anims += tail_anims(idle0[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return msheet("KrnSparkBeetle", anims, outdir)


def beetle_corpse(stage):
    r = Rig()
    # flipped on its back, legs curled up, the antennae limp
    r.ell(0.0, -3.0, 7.4, 3.2, "copper", 0.5, bias=0.05)
    r.ell(0.0, -5.4, 6.4, 1.6, "dkiron", 0.6)
    for i, x in enumerate((-4.0, 0.0, 4.0)):
        r.polyline([(x, -6.0), (x - 1 + stage * 0.3, -8.0 + stage * 0.5), (x + 0.5, -9.0 + stage)], "copper", 0.8, tones=[1, 2])
    r.polyline([(7.0, -3.0), (10.0, -2.0), (12.0, -1.0)], "brass", 0.7, tones=[2, 1])
    if stage < 2: spark(r, 2.0, -9.0 - stage, 2 if stage else 1)
    return r.resolve()


# ================================================================== COIL WISP: a floating copper coil with a lightning heart
def wisp(hover=3.5, spin=0.0, glow=1.0, linked=False, pulse=0.0, mote=None, sparks=(), hurt=False, dead=False, tilt=0.0, extra=None):
    """A brass-capped copper spiral round a blue heart, two loose wires trailing; linked: its coil glows (the Relay tell);
    pulse: 0..1 a ring of discharge round it."""
    r = Rig()
    cy = -hover - 5.0
    shadow(r, 0.0, -0.0, 3.5)
    # heart
    hr = 2.4 + 0.4 * glow
    r.ell(0.0, cy, hr + 1.0, hr + 1.0, "storm", 1.0, flat=2)
    r.ell(0.0, cy, hr, hr, "storm", 1.1, flat=3)
    r.dot(-0.5, cy - 0.5, "storm", 4, 1.2)
    if hurt: r.ell(0.0, cy, 1.0, 1.0, "storm", 1.3, flat=1)
    # the coil: turns of copper wire round the heart (front turns over it, back turns behind)
    turns = 5
    for i in range(turns * 12):
        t = i / (turns * 12.0)
        a = t * turns * math.tau + spin
        y = cy - 4.0 + t * 8.4
        rx = 7.2 - abs(t - 0.5) * 3.0
        x = rx * math.cos(a) + tilt * (t - 0.5)
        front = math.sin(a) > 0
        mat = "copper"
        tone = (3 if math.cos(a) < 0.2 else 2) if front else 1
        if linked and front: mat, tone = "ember", 3 if math.cos(a) < 0.3 else 2
        r.dot(x, y, mat, tone, 2.0 if front else 0.5)
    # brass caps top and bottom
    r.ell(tilt * -0.5, cy - 5.2, 2.8, 1.1, "brass", 2.2, bias=0.2)
    r.dot(tilt * -0.5, cy - 6.4, "brass", 3, 2.3)
    r.ell(tilt * 0.5, cy + 5.6, 1.8, 0.9, "brass", 2.2)
    # two loose wires trailing down
    for k, sx in enumerate((-1.0, 1.2)):
        pts = [(sx, cy + 6.0), (sx - 1.0 - spin * 0.2, cy + 8.0), (sx - 0.4 + math.sin(spin + k) * 1.0, cy + 10.0)]
        r.polyline(pts, "copper", 1.5 + k, tones=[2, 1])
        r.dot(pts[-1][0], pts[-1][1], "storm", 3, 1.6 + k)
    if linked:
        crackle(r, 4.0, cy - 2.0, int(spin * 3) % 4, seed=3)
    if pulse > 0:
        R = 4.0 + pulse * 10.0
        for i in range(28):
            a = i / 28 * math.tau
            if (i + int(pulse * 10)) % 3 == 0: continue
            r.dot(math.cos(a) * R, cy + math.sin(a) * R * 0.8, "storm", 4 if pulse < 0.6 else 2, 4.0)
    if mote:
        r.ell(mote[0], mote[1], 1.6, 1.6, "storm", 5.0, flat=3); r.dot(mote[0], mote[1], "storm", 4, 5.1)
    for (x, y, k) in sparks: spark(r, x, y, k)
    if extra: extra(r)
    return r.resolve()


def wisp_sheet(outdir):
    W = wisp

    def idle(lk):
        return [W(hover=3.3 + [0, 0.3, 0.6, 0.3][i], spin=i * math.pi / 2, linked=lk) for i in range(4)]

    def run(lk):
        return [W(hover=4.0 + 0.6 * math.sin(i / 6 * math.tau), spin=i * math.pi / 3, tilt=1.5, linked=lk) for i in range(6)]
    spk = [W(spin=0.0, glow=1.4), W(spin=0.6, glow=1.8, hover=3.0), W(spin=1.2, glow=2.0, hover=2.5, sparks=[(4, -10, 3)]),
           W(spin=2.0, glow=0.8, hover=4.5, mote=(7.0, -9.0), sparks=[(6, -9, 1)]), W(spin=2.6, glow=1.0, sparks=[(8, -9, 2)]),
           W(spin=3.2)]
    pul = [W(spin=0.0, glow=1.4), W(spin=1.0, glow=1.8, hover=4.5), W(spin=2.2, glow=2.2, hover=5.0),
           W(spin=3.6, glow=2.4, hover=3.5, pulse=0.1), W(spin=4.6, glow=0.6, hover=2.5, pulse=0.35),
           W(spin=5.4, glow=0.6, hover=3.0, pulse=0.65), W(spin=6.0, glow=0.8, pulse=0.95), W(spin=6.6)]
    d0 = W(hurt=True, glow=0.5, tilt=-3.0)
    d1 = W(hurt=True, glow=0.3, hover=1.5, tilt=-6.0, sparks=[(3, -6, 1)])
    d2 = wisp_corpse(0)
    corpse = wisp_corpse(1)
    knock = W(hurt=True, glow=0.6, tilt=-4.0, hover=4.5)
    idle0 = idle(False)
    anims = [("Idle", idle0, [0.14, 0.12, 0.14, 0.12]), ("Run", run(False), [0.07] * 6),
             ("IdleLinked", idle(True), [0.1, 0.1, 0.1, 0.1]), ("RunLinked", run(True), [0.07] * 6),
             ("Spark", spk, [0.12, 0.12, 0.1, 0.06, 0.1, 0.12]),
             ("Pulse", pul, [0.1, 0.1, 0.12, 0.06, 0.06, 0.08, 0.1, 0.12])]
    anims += tail_anims(idle0[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return msheet("KrnCoilWisp", anims, outdir)


def wisp_corpse(stage):
    r = Rig()
    # the coil fallen on its side, sprung loose, the heart guttered
    for i in range(36):
        t = i / 36.0
        a = t * 4 * math.tau
        x = -6.0 + t * 12.0 + (0.6 if stage else 0) * math.sin(a * 0.5)
        y = -2.4 + 2.2 * math.sin(a)
        r.dot(x, y, "copper", 2 if math.sin(a) > 0 else 1, 1.0 if math.sin(a) > 0 else 0.0)
    r.ell(0.0, -2.4, 1.4, 1.2, "storm" if stage == 0 else "dkiron", 0.5, flat=1 if stage else 2)
    r.ell(-6.8, -2.4, 1.0, 1.8, "brass", 1.2)
    if stage == 0: spark(r, 1.0, -6.0, 2)
    return r.resolve()


SYNC = {
    "KrnRivetImp": {"Bonk": [("HIT: hammer head on the floor at (12, -1), two bolt slots light", 3)],
                    "Rivets": [("three rivets leave the swing at (10, -12)", 3)]},
    "KrnSparkBeetle": {"Zap": [("bolt leaves the antenna tips at (10, -9)", 3)],
                       "Rush": [("curls into the ball: roll starts", 1), ("uncurls", 6)],
                       "RushBig": [("overcharged ball (r 7, white sheath): roll starts", 1)]},
    "KrnCoilWisp": {"Spark": [("mote leaves the coil front at (7, -10)", 3)], "Pulse": [("RING: the discharge leaves the heart", 3)]},
}
NOTES = {
    "KrnSparkBeetle": "IdleCharged/RunCharged: the shell's three sparks burn white (3 sparks stored: the next roll is the overcharged one).",
    "KrnCoilWisp": "IdleLinked/RunLinked: the coil glows ember while an arc is joined to it (Relay, 110 px arcs).",
}
JOBS = [("KrnRivetImp", imp_sheet), ("KrnSparkBeetle", beetle_sheet), ("KrnCoilWisp", wisp_sheet)]
