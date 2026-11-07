"""Moth Matron and Tallow Colossus rigs (the Lantern Wraith moved to vhorrul_t3.py in v0.8)."""
import math, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from rig import Part, Canvas
from anim import Spr, pack, preview
from moth_rig import poly_fill
import scalekit as SK

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "art/out")
EMBER = Part("O.o\n.Y.", (1, 1))
EMBER_MOTH = Part("o.o\n.O.\nY.Y", (1, 1))


# ---------------------------------------------------------------- Moth Matron
MASK = Part("""
.XXX.
XXXXX
XrXrX
XXXXX
.XwX.
..X..
""", (2, 5))
MASK_SCREAM = Part("""
.XXX.
XXXXX
XRXRX
XXXXX
.XKX.
..K..
""", (2, 5))
MATRON_BODY = Part("""
..hih..
.hiiih.
.hiXih.
hiihiih
.hiiih.
.hhihh.
..hih..
..h.h..
""", (3, 7))


def big_wing(px, root, length, angle, spread, fill, rim, spots):
    a = math.radians(angle)
    pts = [root,
           (root[0] + length * math.cos(a - spread), root[1] + length * math.sin(a - spread)),
           (root[0] + length * 1.1 * math.cos(a), root[1] + length * 1.1 * math.sin(a)),
           (root[0] + length * 0.9 * math.cos(a + spread), root[1] + length * 0.9 * math.sin(a + spread)),
           (root[0] + length * 0.5 * math.cos(a + spread * 1.4), root[1] + length * 0.5 * math.sin(a + spread * 1.4))]
    sub = {}
    poly_fill(sub, pts, fill, rim)
    # tattered edge: knock out a few rim pixels
    rnd = random.Random(int(angle * 7))
    for k in list(sub.keys()):
        if sub[k] == rim and rnd.random() < 0.18: del sub[k]
    for f in spots:
        sx = int(round(root[0] + length * f * math.cos(a))); sy = int(round(root[1] + length * f * math.sin(a)))
        for dx, dy, c in ((0, 0, 'O'), (1, 0, 'o'), (-1, 0, 'o'), (0, 1, 'a'), (0, -1, 'a')):
            if (sx + dx, sy + dy) in sub: sub[(sx + dx, sy + dy)] = c
    for k, v in sub.items(): px[k] = v


def matron(wing_a=-60, flap=0, arm=(40, 80), mask=MASK, dy=0, lean=0, embers=(), glow=False):
    c = Canvas()
    root = (lean - 1, -16 + dy)
    px = {}
    big_wing(px, (root[0] - 1, root[1]), 13, wing_a - 20 - flap, 0.55, 'k', 'K', [0.6])
    big_wing(px, root, 15, wing_a + flap, 0.6, 'g', 'k', [0.45, 0.8])
    for k, v in px.items(): c.put(k[0], k[1], v)
    c.part(MATRON_BODY, root[0] + 1, root[1] + 8)
    c.part(mask, root[0] + 2, root[1] - 1)
    # antennae plumes
    c.limb(root[0] + 2, root[1] - 6, [(3, -110), (2, -150)], ["w"])
    c.limb(root[0] + 3, root[1] - 6, [(3, -70), (2, -30)], ["w"])
    # clawed arms
    c.limb(root[0] + 3, root[1] + 2, [(4, arm[0]), (4, arm[1])], ["h", "i"], end=Part("w.w\n.w.", (1, 0)))
    for p, x, y in embers: c.part(p, x, y)
    if glow:
        c.px = {k: ('Y' if v == 'O' else v) for k, v in c.px.items()}
    return c.spr()


def build_matron():
    idle = [matron(wing_a=-60, flap=[0, 6, 12, 6][i], dy=[0, -1, -1, 0][i], arm=(40, 80 + 5 * (i % 2)),
                   embers=[(EMBER, 9, -24 - (i % 2))]) for i in range(4)]
    run = [matron(wing_a=-50, flap=[0, 10, 20, 25, 15, 5][i], dy=[0, -1, -2, -2, -1, 0][i], lean=1) for i in range(6)]
    slash = [matron(wing_a=-100, flap=-10, arm=(-60, -100), lean=-1),
             matron(wing_a=-120, flap=-20, arm=(-80, -120), lean=-2, mask=MASK_SCREAM),
             matron(wing_a=-10, flap=30, arm=(10, 40), lean=2, mask=MASK_SCREAM),
             matron(wing_a=10, flap=35, arm=(20, 30), lean=3),
             matron(wing_a=-30, flap=10, arm=(40, 70), lean=1),
             matron()]
    # v0.8: Brood 6 (the moths still leave 0.30 s in, on f3 - TIMING.md)
    brood = [matron(wing_a=-80, arm=(80, 100), dy=1),
             matron(wing_a=-85, flap=-5, arm=(85, 105), dy=1, embers=[(EMBER, 4, -8)]),
             matron(wing_a=-90, flap=-10, arm=(90, 110), dy=1, glow=True, embers=[(EMBER, 3, -6)]),
             matron(wing_a=-100, flap=-15, arm=(90, 110), dy=0, glow=True, mask=MASK_SCREAM,
                    embers=[(EMBER_MOTH, -6, -10), (EMBER_MOTH, 8, -12), (EMBER_MOTH, 2, -4)]),
             matron(wing_a=-40, flap=20, arm=(40, 70), mask=MASK_SCREAM,
                    embers=[(EMBER_MOTH, -10, -20), (EMBER_MOTH, 14, -18), (EMBER_MOTH, 4, -30)]),
             matron(wing_a=-60, flap=5)]
    death = [matron(wing_a=-20, flap=20, mask=MASK_SCREAM, dy=1),
             matron(wing_a=0, flap=25, mask=MASK_SCREAM, dy=3, lean=-1),
             matron(wing_a=20, flap=30, mask=MASK_SCREAM, dy=6),
             Spr({(x, y + SK.Si(12)): v for (x, y), v in matron(wing_a=40, flap=40).px.items() if y + SK.Si(12) <= 0})]
    knock = [matron(wing_a=-130, flap=-25, lean=-3, mask=MASK_SCREAM)]
    anims = [("Idle", idle, [0.12] * 4), ("Run", run, [0.07] * 6), ("Dead", [death[-1]], [0.2]),
             ("Death", death, [0.1, 0.1, 0.12, 0.3]), ("Statue", [idle[0].stone()], [0.2]), ("Knockback", knock, [0.2]),
             ("Portrait", [idle[0]], [0.2]),
             ("Slash", slash, [0.1, 0.12, 0.05, 0.08, 0.1, 0.12]),
             ("Brood", brood, [0.12, 0.08, 0.1, 0.12, 0.14, 0.07])]
    img, man = pack("MothMatron", anims, cell_w=60, cell_h=46, feet=(30, 44), outdir=OUT, floor=True)
    preview(img, man, os.path.join(OUT, "MothMatron_preview.png"), scale=4)


# ---------------------------------------------------------------- Tallow Colossus
FACE = [Part("wkw\nkKk\nwkw", (1, 1)), Part(".k.\nkKk\n.k.", (1, 1))]
COL_EYE = Part("RK\nKr", (0, 0))
# v0.10 lineage (one parent, the Waxen Knight): the knight's rust great-helm with its candle crown and red visor sits in
# the wax as its head, a rust pauldron rides the front shoulder, and the hilts of two swords - the knight's own, and
# whoever's it took them from - stand out of its back where they were swallowed. (v0.9 had the Chandler's bucket there.)
COL_HELM = Part("""
..O.O.O..
..Y.Y.Y..
..X.X.X..
.XaaaaaW.
XaaaaaaaW
akRRyRRka
akkkkkkka
.aakkkaa.
..aaaaa..
""", (4, 8))
COL_HELM_DARK = Part("""
..s.s.s..
..S.S.S..
..X.X.X..
.XaaaaaW.
XaaaaaaaW
akKKKKKka
akkkkkkka
.aakkkaa.
..aaaaa..
""", (4, 8))
COL_PAULDRON = Part("""
.aaa.
aakaa
akaka
.a.a.
""", (2, 1))
COL_BUCKET = Part("""
kaaaaak
aOYYOoa
aoOOOoa
akkkkka
.akkka.
""", (3, 4))
COL_BUCKET_COLD = Part("""
kaaaaak
asSSssa
awwwhwa
akkkkka
.akkka.
""", (3, 4))
COL_HILT = Part("""
.k.
.e.
eAe
.a.
.a.
.s.
""", (1, 5))
COL_HILT_B = Part("""
k...
.e..
eAe.
..a.
...a
...s
""", (2, 5))
BACK_CANDLE = [Part("O\nY\nX\nW", (0, 3)), Part(".O\nOY\nX.\nW.", (0, 3)), Part("s\nX\nW", (0, 2))]


def blob(px, cx, cy, rx, ry, seed):
    rnd = random.Random(seed)
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + (rnd.random() - 0.5) * 0.12
            if d > 1: continue
            if d > 0.78: c = 'w'
            elif y < cy - ry * 0.35 and x < cx + rx * 0.3: c = 'X'
            elif (x * 3 + y * 5 + seed) % 11 == 0: c = 'w'
            else: c = 'W'
            px[(x, y)] = c


def colossus(dx=0, dy=0, squash=1.0, fist_f=(14, -8), fist_b=(-12, -6), legs=(0, 0), candles_lit=True, size=1.0,
             eyes=True, extra=(), phase=None):
    px = {}
    s = size
    # legs
    for i, lx in enumerate((-5, 5)):
        o = legs[i]
        blob(px, dx + lx * s + o, -3 * s, 3.2 * s, 3.2 * s, 10 + i)
    # body: big hunched mass
    blob(px, dx - 1 * s, (-14 + dy) * s * squash, 12 * s, 10 * s * squash, 1)
    blob(px, dx + 6 * s, (-17 + dy) * s * squash, 6 * s, 6 * s * squash, 2)
    # faces sunk into the wax
    c = Canvas(); c.px = px
    for i, (fx, fy) in enumerate(((-6, -16), (2, -12), (-2, -20))):
        c.part(FACE[i % 2], int(dx + fx * s), int((fy + dy) * s * squash))
    # v0.10: two swallowed sword hilts standing out of its back (the Waxen Knight's), wax creeping up the blades
    c.part(COL_HILT, int(dx - 6 * s), int((-23 + dy) * s * squash))
    c.part(COL_HILT_B, int(dx - 12 * s), int((-19 + dy) * s * squash))
    # the knight's helm as its head
    c.part(COL_HELM if eyes else COL_HELM_DARK, int(dx + 8 * s), int((-15 + dy) * s * squash))
    # back candles
    for i, bx in enumerate(range(-10, 6, 3)):
        top = int((-23 + dy) * s * squash) + abs(bx + 2) // 3
        cand = BACK_CANDLE[(i + int(dx) + (phase or 0)) % 2] if candles_lit else BACK_CANDLE[2]
        c.part(cand, int(dx + bx * s), top)
    # arms + fists
    for (fx, fy), back in ((fist_b, True), (fist_f, False)):
        sx, sy = dx + (-6 if back else 7) * s, (-16 + dy) * s * squash
        if not back:
            c.part(COL_PAULDRON, int(sx), int(sy))
        c.limb(int(sx), int(sy), [(math.hypot(fx * s - (sx - dx), fy * s - sy) * 0.95, math.degrees(math.atan2(fy * s - sy, fx * s + dx - sx)))],
               [("w", "W")], width=2)
        fp = {}
        blob(fp, dx + fx * s, fy * s, 3.4 * s, 3 * s, 20 + back)
        for k, v in fp.items(): c.put(k[0], k[1], 'w' if back and v == 'X' else v)
    for p, x, y in extra: c.part(p, x, y)
    sp = c.spr()
    return Spr({k: v for k, v in sp.px.items() if k[1] <= 0})


SHOCK = Part("""
X.........X
.XWW...WWX.
...WWWWW...
""", (5, 2))


def build_colossus():
    # v0.8: four distinct breaths (the candles flicker in turn; frames 1 and 3 used to be identical)
    idle = [colossus(squash=[1, 0.98, 0.96, 0.98][i], fist_f=(14, -8 + (i % 2)), fist_b=(-12, -6 + (1 if i == 2 else 0)),
                     phase=[0, 0, 1, 1][i]) for i in range(4)]
    run = [colossus(dx=[0, 1, 1, 0, -1, -1][i], squash=[1, 0.96, 0.98, 1, 0.96, 0.98][i], legs=[(2, -2), (1, -1), (0, 0), (-2, 2), (-1, 1), (0, 0)][i],
                    fist_f=(13 + [1, 0, -1, -1, 0, 1][i], -8), fist_b=(-12 + [-1, 0, 1, 1, 0, -1][i], -6)) for i in range(6)]
    hammer = [colossus(fist_f=(6, -20), fist_b=(-12, -6), dx=-1),
              colossus(fist_f=(20, -10), fist_b=(-10, -8), dx=2),
              colossus(fist_f=(21, -10), fist_b=(-6, -12), dx=2),
              colossus(fist_f=(10, -14), fist_b=(18, -10), dx=3),
              colossus(fist_f=(9, -14), fist_b=(19, -10), dx=3),
              colossus(fist_f=(14, -8), fist_b=(-12, -6), dx=1)]
    # v0.8: 6 frames; the slam (wave) still lands 0.38 s in, on f3 (TIMING.md)
    slam = [colossus(fist_f=(8, -28), fist_b=(-4, -28), squash=1.05),
            colossus(fist_f=(6, -30), fist_b=(-2, -30), squash=1.08, dy=-1),
            colossus(fist_f=(12, -22), fist_b=(6, -22), squash=1.0, phase=1),
            colossus(fist_f=(16, -4), fist_b=(10, -4), squash=0.88, extra=[(SHOCK, 13, 0)]),
            colossus(fist_f=(16, -4), fist_b=(10, -4), squash=0.9),
            colossus(fist_f=(15, -6), fist_b=(-2, -5), squash=0.96, phase=1)]
    roll = []
    for i in range(6):
        p = {}
        blob(p, 0, -11, 11, 11, 1)
        c = Canvas(); c.px = p
        for k in range(4):
            a = math.radians(i * 30 + k * 90)
            c.part(FACE[k % 2], int(7 * math.cos(a)), int(-11 + 7 * math.sin(a)))
            c.part(BACK_CANDLE[k % 2], int(9 * math.cos(a + 0.6)), int(-11 + 9 * math.sin(a + 0.6)))
        roll.append(Spr({k: v for k, v in c.px.items() if k[1] <= 0}))
    # v0.8: Curl 6 (0.25 s, as before): hunch, pull the fists in, fold into the ball
    def balling(k):
        p = {}
        blob(p, 0, -11 - (2 - k), 11 + (2 - k), 11 - (2 - k) * 0.5, 1)
        c = Canvas(); c.px = p
        for j in range(3):
            a = math.radians(-60 + j * 110 + k * 15)
            c.part(FACE[j % 2], int(6 * math.cos(a)), int(-11 + 6 * math.sin(a)))
            c.part(BACK_CANDLE[(j + k) % 2], int(-6 + j * 5), int(-21 + (2 - k) + abs(j - 1)))
        for sd in (-1, 1):
            fp = {}
            blob(fp, sd * (9 - k * 2), -4, 3.2, 2.8, 20 + k + sd)
            for kk, v in fp.items(): c.put(kk[0], kk[1], v)
        return Spr({kk: v for kk, v in c.px.items() if kk[1] <= 0})
    curl = [colossus(squash=0.95, fist_f=(10, -7), fist_b=(-9, -6)),
            colossus(squash=0.9, fist_f=(6, -6), fist_b=(-6, -6), phase=1),
            colossus(squash=0.84, fist_f=(4, -5), fist_b=(-4, -5), legs=(1, -1)),
            balling(0), balling(1), roll[0]]
    # v0.8: Death 4: candles gutter, it sags, slumps, and melts into a puddle
    death = [colossus(eyes=False, squash=0.9, candles_lit=False),
             colossus(eyes=False, squash=0.8, candles_lit=False, fist_f=(15, -4), fist_b=(-13, -4)),
             colossus(eyes=False, squash=0.65, candles_lit=False, fist_f=(15, -2), fist_b=(-15, -2)),
             colossus(eyes=False, squash=0.45, candles_lit=False, fist_f=(16, -1), fist_b=(-16, -1))]
    knock = [colossus(dx=-2, fist_f=(4, -22), fist_b=(-16, -14), squash=1.02)]
    anims = [("Idle", idle, [0.22] * 4), ("Run", run, [0.11] * 6), ("Dead", [death[-1]], [0.2]),
             ("Death", death, [0.12, 0.12, 0.14, 0.3]), ("Statue", [idle[0].stone()], [0.2]), ("Knockback", knock, [0.2]),
             ("Portrait", [idle[0]], [0.2]),
             ("Hammer", hammer, [0.14, 0.05, 0.12, 0.05, 0.12, 0.14]),
             ("Slam", slam, [0.2, 0.12, 0.06, 0.05, 0.25, 0.1]),
             ("Curl", curl, [0.05, 0.05, 0.04, 0.04, 0.04, 0.03]), ("Roll", roll, [0.05] * 6)]
    img, man = pack("TallowColossus", anims, cell_w=72, cell_h=56, feet=(32, 54), outdir=OUT)
    preview(img, man, os.path.join(OUT, "TallowColossus_preview.png"), scale=3)


# The Lantern Wraith was redrawn in v0.8 and now lives in vhorrul_t3.py (build_wraith).


if __name__ == "__main__":
    build_matron(); build_colossus()
