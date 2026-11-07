"""GHOST FORMS: six new forms (Banshee, Sexton, Kindler, Mason, Hexer, Miser), their fodder creatures, effects,
in-game ghost bodies and picker portraits, plus the silver / gold slot portraits and the silver / gold mechanic effects.

    python3 ghost_v11.py [--only Name,Name]

Fodder (built on the vanilla slime kit, all possessable, T1 size; drawn by ghosts_v2_fodder.py):
  FodKeener     Banshee     a floating wailing head trailing long hair             Idle 4, Run 6, Shriek 6 (release 3)
  FodRevenant   Sexton      a grave-rag skeleton ghoul clawing out of the earth    Idle 4, Run 6, Claw 6 (hit 3)
  FodFusebelly  Kindler     a round tallow bomb on stubby legs, a lit fuse         Idle 4, Run 6, Lick 5 (hit 2), Blow 7 (burst 5)
  FodGargling   Mason       a squat stone gargoyle, rooted, spits stone            Idle 4, Run 6, Spit 6 (release 3), Fan 7 (release 4)
  FodPoppet     Hexer       a stitched voodoo poppet stuck with pins              Idle 4, Run 6, Jab 6 (hit 3)
  FodMimic      Miser       a treasure chest with teeth on stubby legs           Idle 4, Run 6, Chomp 6 (hit 3), Spit 6 (release 3)
Every fodder also has Death 4, Dead, Statue, Knockback, Portrait and Spawn 5 (vanilla slime timing).

All art lands in art/out_ghosts; TIMING_v11.md there lists every cell, origin and event frame the C# uses.
"""
import math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ghost_v11kit import *  # noqa: F401,F403
import ghost_v11kit as KT  # noqa: E402

Fr = V.Fr


# ===================================================================================================== palettes
GLOW_C = ramp("2a6a78", "5ac8d8", "a8f4ff", "eaffff")           # banshee cyan glow
SKIN_B = ramp("4a5468", "77849a", "a8b4c6", "d6e0ec")           # keener: cold pale skin
HAIR_B = ramp("1c1626", "2e2440", "463a5e", "625480")           # keener: night-violet hair
BONE = ramp("6a5a46", "9a8468", "c4ae86", "e2d0a6", "f6ecd0")
RAG = ramp("23251c", "363a2a", "4c5238", "687048")              # grave rags (moss-black)
SOUL_G = ramp("2c6a3a", "5ab86a", "a8f0a0", "e8ffe0")           # revenant green soul glow
WAX = ramp("7a6a52", "b4a07a", "dccaa0", "f2e6c4", "fffaea")    # tallow
WAX_D = ramp("5a4a38", "8a7658", "b4a07a")
FLAME = ramp("a8301a", "e8701e", "ffc040", "fff0a0")
STONE_R = ramp("33343c", "4c4e58", "6a6c76", "8e909a", "b4b6bc")
MOSS = ramp("2e4626", "4a6e34", "74a048")
AMBER = ramp("8a4a10", "e09a20", "ffe070")
BURLAP = ramp("4a3420", "76563a", "a07c52", "c8a474", "e4c898")
STITCH = hx("2a1a12")
PIN_R = hx("d83a3a")
PIN_B = hx("3a7ad8")
PIN_Y = hx("e8c83a")
STEEL = ramp("5a6070", "a0a8b8", "e8eef8")
HEX = ramp("3a1850", "7a3aa8", "c47ae8", "f0d0ff")              # hex violet
WOOD = ramp("3a2214", "5e3a20", "865630", "ad7a46", "cfa060")
IRON = ramp("26262e", "44464f", "6a6c74", "9a9ca4")
GOLD = ramp("6a4a10", "a87818", "e0b02a", "ffe070", "fff8c8")
TEETH = ramp("a8a090", "e0d8c4", "fffaf0")
TONGUE = ramp("6a1a2a", "b03448", "e86a7a")
# Crawl's palette: the props and glows are muted and grimy (the coins and gold match the gilded secret's old gold)
from ghosts_v2_kit import mute_rgb  # noqa: E402
GLOW_C, SOUL_G, FLAME, AMBER, HEX, GOLD, TONGUE = (mute_rgb(r_, 0.6) for r_ in (GLOW_C, SOUL_G, FLAME, AMBER, HEX, GOLD, TONGUE))
COIN = GOLD


def jit(seed):
    return random.Random(seed)


# ===================================================================================================== FX
def C():
    return Canvas()


def dith(i, j):
    return (i + j) % 2 == 0


def ring_half(c, rx, ry, th, cols, back=False, gaps=0, seed=0, phase=0.0, yoff=0.0):
    """Half an elliptical ring centred on (0, -yoff): front = lower half (y >= centre), back = upper half.
    th = thickness in px, cols = [inner/shade .. outer/lit] colours; gaps: dithered breaks."""
    r = jit(seed)
    n = max(10, int(rx * 3))
    for j in range(n + 1):
        t = math.pi * j / n + (math.pi if back else 0.0)
        for k in range(max(1, int(round(th)))):
            rr = rx - k * 0.8
            x, y = rr * math.cos(t), rr * ry / rx * math.sin(t) - yoff
            if gaps and r.random() < gaps: continue
            c.put(*P(x, y), cols[min(len(cols) - 1, k)] if not back else cols[max(0, min(len(cols) - 1, k) - 1)])


def ring_pair(name, radii, thick, cols, ry_k=0.38, debris=None, cw=40, ch=24, org=(20, 15), durs=(0.067,) * 4, gaps=(0, 0, 0.25, 0.5)):
    """A spawn splash like FxBlobSpawn: Ring (front half) 4 + Back (far half) 4, centred on the cell pixel org
    (C#: RingPair(go, org.x, org.y, name)). debris(c, i, back) adds the material's own bits."""
    front, back = [], []
    for i, (rx, th) in enumerate(zip(radii, thick)):
        for half, out in ((False, front), (True, back)):
            c = C()
            ring_half(c, rx, rx * ry_k, th, cols, back=half, gaps=gaps[min(i, len(gaps) - 1)], seed=i * 7 + (3 if half else 0))
            if debris: debris(c, i, half)
            out.append(R(c.spr()))
    return fixed_sheet(name, [("Ring", front, list(durs)), ("Back", back, list(durs))], cw, ch, org)


# ------------------------------------------------------------------ Banshee
MIST = [hx("2a5a66", 150), hx("4aa0b0", 190), hx("8ae0ee", 220), hx("d8fcff", 240)]


def wail_ring():
    """FxWailRing Play 7: the Banshee's wail, three ghostly sound rings bursting out from the ghost to a 36 px radius,
    pale faces of the dead flickering in them. Centre = cell (40, 22) (the ghost's origin)."""
    frames = []
    for i in range(7):
        c = C()
        for k in range(3):
            u = (i - k * 1.2) / 5.0
            if u < 0 or u > 1.05: continue
            rx = 6 + 30 * u
            ry = rx * 0.5
            n = int(rx * 3.2)
            for j in range(n):
                t = 2 * math.pi * j / n
                if (j + i) % 3 == 0 and u > 0.6: continue
                x, y = rx * math.cos(t), ry * math.sin(t) - 6
                col = MIST[3] if u < 0.35 else MIST[2] if u < 0.7 else MIST[1]
                c.put(*P(x, y), col)
                if u < 0.5: c.put(*P(x * 0.94, y * 0.94 - 0.3), MIST[1])
        # wailing faces carried on the first ring
        if 1 <= i <= 4:
            u = i / 5.0
            for a in (-0.4, 1.3, 2.9, 4.2):
                x, y = (6 + 30 * u) * math.cos(a), (6 + 30 * u) * 0.5 * math.sin(a) - 6
                for (dx, dy, col) in ((0, 0, MIST[2]), (1, 0, MIST[2]), (0, 1, MIST[1]), (1, 1, MIST[1]), (0, -1, MIST[3]), (1, -1, MIST[3])):
                    c.put(*P(x + dx, y + dy), col)
                c.put(*P(x, y - 1), BLACK + (200,)); c.put(*P(x + 1, y + 1), BLACK + (220,))
        frames.append(R(c.spr()))
    return fixed_sheet("FxWailRing", [("Play", frames, [0.06, 0.06, 0.07, 0.08, 0.09, 0.1, 0.12])], 80, 44, (40, 28))


def shriek_fx():
    """FxShriek: the Keener's shriek. Fly 4 (three sound arcs travelling right), Wall 4 / Hit 4 (the wave breaking).
    Centre = cell (8, 8)."""
    fly = []
    for i in range(4):
        c = C()
        for k in range(3):
            r = 2.0 + k * 2.2 + (i % 2) * 0.6
            for j in range(-4, 5):
                a = j * 0.22
                c.put(*P(r * math.cos(a) - 3, r * 1.3 * math.sin(a)), MIST[3 - k] if abs(j) < 3 else MIST[2 - min(k, 1)])
        fly.append(R(c.spr()))
    burst = []
    for i in range(4):
        c = C()
        r = 2 + i * 2.2
        for j in range(16):
            a = 2 * math.pi * j / 16
            if (j + i) % 2 and i > 1: continue
            c.put(*P(r * math.cos(a), r * 0.8 * math.sin(a)), MIST[3 - min(3, i)])
        burst.append(R(c.spr()))
    return fixed_sheet("FxShriek", [("Fly", fly, [0.06] * 4), ("Wall", burst, [0.05, 0.05, 0.06, 0.08]),
                                    ("Hit", burst, [0.05, 0.05, 0.06, 0.08])], 22, 22, (11, 11))


def keener_rise():
    def deb(c, i, back):
        if back or i > 2: return
        for k, a in enumerate((0.3, 1.2, 2.2, 2.9)):
            x = (5 + i * 4) * math.cos(a); y = -2 - i * 2 - (k % 2)
            c.put(*P(x, y), MIST[3 - i]); c.put(*P(x, y - 1), MIST[2])
    return ring_pair("FxKeenerRise", [5.0, 9.0, 12.5, 14.0], [1.4, 1.2, 0.9, 0.6], [MIST[1], MIST[2], MIST[3]], debris=deb)


# ------------------------------------------------------------------ Sexton
def dirt_mound(c, w, h, seed=1, x0=0.0):
    r = jit(seed)
    DIRT = ramp("2a1e16", "46321e", "6a4c2c", "8a6a40")
    for x in range(-int(w), int(w) + 1):
        t = abs(x) / max(1.0, w)
        top = int(round(-h * (1 - t * t))) - (1 if r.random() < 0.25 else 0)
        for y in range(top, 1):
            l = 0.6 if y == top and x < 0 else 0.2 if y == top else -0.5
            c.put(int(x + x0), y, pick(DIRT, l))

DIRT = ramp("2a1e16", "46321e", "6a4c2c", "8a6a40")
STONE_G = ramp("3c3e46", "5c5e68", "848690", "aeb0b8")


def grave(stage, glow=0, phase=0):
    """A fresh grave: a mound of turned earth, a crooked little headstone, a soul flame flickering over it.
    stage 0..1 rises (0 = just a crack), glow 1 = a Sexton is near (green soul light, the flame grown)."""
    f = Fr()
    w = 6.5 * min(1.0, 0.4 + stage)
    dirt_mound(f.b, w, 1.8 * stage, seed=5)
    if stage >= 0.6:
        hh = int(round(7 * min(1.0, (stage - 0.4) / 0.6)))
        poly(f.b, [(-1.5, -1.0), (2.5, -1.0), (2.8, -hh), (0.6, -hh - 1.4), (-1.2, -hh)], STONE_G[1])
        line(f.b, -1.2, -hh, -1.5, -1.0, STONE_G[3]); line(f.b, -1.2, -hh, 0.6, -hh - 1.4, STONE_G[3])
        if hh >= 5:
            line(f.b, 0.5, -hh + 1.5, 0.5, -hh + 4.0, STONE_G[0]); line(f.b, -0.5, -hh + 2.5, 1.5, -hh + 2.5, STONE_G[0])
    spr = done(f, INK)
    px = dict(spr.px)
    if stage >= 1.0:
        fy = -10 - (phase % 2)
        cols = SOUL_G if glow else [hx("2c5a3a", 160), hx("4a9a5a", 190), hx("8ad08a", 210), hx("c8f0c0", 230)]
        size = 3 if glow else 2
        for k in range(size):
            px[(1 + ([0, 1, 0, -1][(phase + k) % 4] if k else 0), fy - k)] = cols[min(3, 3 - k)]
        px[(1, fy + 1)] = cols[2]; px[(0, fy + 1)] = cols[1]; px[(2, fy + 1)] = cols[1]
        if glow:
            for (x, y) in ((-4, -3), (5, -4), (-2, -6), (4, -8)):
                if (x + y + phase) % 3 == 0: px[(x, y)] = SOUL_G[2]
            for x in range(-5, 7):
                if (x + phase) % 2 == 0: px[(x, 0)] = SOUL_G[1]
    return RSpr(px)


def grave_fx():
    rise = [grave(0.15), grave(0.45), grave(0.75), grave(1.0)]
    idle = [grave(1.0, 0, i) for i in range(6)]
    glow = [grave(1.0, 1, i) for i in range(6)]
    sink = [dissolve(grave(1.0), 0.8, 1), grave(0.75), grave(0.45), dissolve(grave(0.15), 0.6, 2)]
    return fixed_sheet("FxGrave", [("Rise", rise, [0.08, 0.08, 0.1, 0.12]), ("Idle", idle, [0.14] * 6),
                                   ("Glow", glow, [0.1] * 6), ("Sink", sink, [0.08, 0.08, 0.1, 0.12])], 22, 20, (11, 18))


def grave_raise():
    def deb(c, i, back):
        r = jit(20 + i)
        if back: return
        for k in range(4 - i):
            a = r.uniform(0.2, 2.9)
            x = (4 + i * 4) * math.cos(a) * 1.1; y = -2 - (3 - i) * 1.5 - r.random() * 2
            c.put(*P(x, y), hx("b0905c")); c.put(*P(x + 1, y), DIRT[3]); c.put(*P(x, y + 1), DIRT[2])
    return ring_pair("FxGraveRaise", [5.0, 9.0, 12.0, 13.5], [1.6, 1.4, 1.0, 0.7], [DIRT[2], DIRT[3], hx("b0905c")], debris=deb)


# ------------------------------------------------------------------ Kindler
def blast(r, i, n, small=False):
    """A tallow-bomb burst: a cluster of fire lobes round a white-hot core (outlined in deep red), wax shrapnel flying,
    grey smoke puffs rolling up as it burns out, a scorch ring on the floor."""
    rnd = jit(40 + (100 if small else 0))
    u = i / (n - 1)
    R0 = r * (0.3 + 0.7 * min(1.0, u * 1.8))
    f = Fr()
    lobes = [(rnd.uniform(-0.55, 0.55), rnd.uniform(-0.6, 0.15), rnd.uniform(0.35, 0.55)) for _ in range(7 if not small else 4)]
    if u < 0.72:
        k = 1.0 - max(0.0, u - 0.35) * 1.3
        for (lx, ly, lr) in lobes:
            ell(f.b, lx * R0, -R0 * 0.55 + ly * R0 * 0.7, lr * R0 * k, lr * R0 * 0.85 * k, [FLAME[0], FLAME[1], FLAME[2], FLAME[3]],
                bias=0.35 - u * 0.6)
        if u < 0.45:
            ell(f.b, 0, -R0 * 0.6, R0 * 0.3, R0 * 0.26, [FLAME[2], FLAME[3], WHITE], bias=0.5)
    # smoke puffs taking over
    if u > 0.3:
        SM = [hx("3a3436", 230), hx("5a5052", 220), hx("7e7470", 200)]
        for j, (lx, ly, lr) in enumerate(lobes[:5]):
            sy = -R0 * 0.7 + ly * R0 - (u - 0.3) * r * 0.5
            ell(f.n, lx * R0 * 1.2, sy, lr * R0 * 0.55 * (0.6 + u), lr * R0 * 0.45 * (0.6 + u), SM, bias=0.2)
    spr = done(f, hx("6a1a10")) if u < 0.72 else R(Fr.done(f, outline=False))
    px = dict(spr.px)
    # scorch ring on the floor
    if u > 0.2:
        for j in range(int(R0 * 4)):
            t = 2 * math.pi * j / int(R0 * 4)
            if rnd.random() < u * 0.5: continue
            px[P(R0 * math.cos(t), R0 * 0.35 * math.sin(t))] = hx("2a2020", 220) if j % 2 else hx("4a3a34", 200)
    # wax shrapnel
    for k in range(7 if not small else 3):
        a = rnd.uniform(-math.pi, 0) if k % 2 else rnd.uniform(-math.pi, math.pi)
        d = R0 * (0.7 + 0.9 * u)
        x, y = d * math.cos(a), d * 0.6 * math.sin(a) - R0 * 0.4 - 5 * u * (1 - u)
        px[P(x, y)] = WAX[3]; px[P(x + 1, y)] = WAX[2]
        if u < 0.6: px[P(x - math.cos(a), y - 0.6 * math.sin(a))] = FLAME[2]
    out = RSpr(px)
    return dissolve(out, 0.55, i) if u > 0.85 else out


def fuse_spark(i):
    """FxFuseSpark Loop 4: the sizzle on the fuse of the Fusebelly the Kindler's Attack will light: a white-hot bead
    in a flickering flame tongue, sparks spitting off it to both sides. Centre = sprite (0, -7)."""
    c = C()
    cx, cy = 0, -7
    tip = [3, 4, 3, 2][i]
    lean = [0, 1, 0, -1][i]
    for k in range(tip):
        c.put(cx + (lean if k >= tip - 1 else 0), cy - 2 - k, FLAME[1] if k == tip - 1 else FLAME[2])
    for (x, y) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        c.put(cx + x, cy + y, FLAME[1])
    for (x, y) in ((0, -1), (-1, 0), (1, 0), (0, 1)):
        c.put(cx + x, cy + y, FLAME[2])
    c.put(cx, cy, FLAME[3])
    if i % 2 == 0:
        c.put(cx + 1, cy - 1, FLAME[3])
    rnd = jit(70 + i)
    for k in range(5):
        a = -math.pi * (0.1 + 0.8 * (k + rnd.uniform(0.0, 0.8)) / 5.0) + (0.5 if k in (0, 4) else 0.0) * (1 if k == 0 else -1)
        r = rnd.uniform(3.0, 6.0)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a) * 0.9
        c.put(*P(x, y), FLAME[3] if k % 2 == 0 else FLAME[2])
        if r > 4.2:
            c.put(*P(x - math.cos(a) * 1.4, y - math.sin(a) * 1.2), FLAME[1] + (170,))
    return R(c.spr())


def fuse_spark_fx():
    return fixed_sheet("FxFuseSpark", [("Loop", [fuse_spark(i) for i in range(4)], [0.07, 0.06, 0.07, 0.06])], 16, 16, (8, 15))


def fuse_blast_fx():
    play = [blast(22, i, 9) for i in range(9)]
    pop = [blast(10, i, 6, small=True) for i in range(6)]
    return fixed_sheet("FxFuseBlast", [("Play", play, [0.04, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.12]),
                                       ("Pop", pop, [0.04, 0.05, 0.06, 0.07, 0.09, 0.1])], 72, 56, (36, 46))


def wax_ring():
    def deb(c, i, back):
        if back or i > 2: return
        for k, a in enumerate((0.4, 1.4, 2.4)):
            x = (5 + i * 4) * math.cos(a); y = -2 - (2 - i) * 2
            c.put(*P(x, y), WAX[4 - i]); c.put(*P(x, y + 1), WAX[2])
    return ring_pair("FxWaxRing", [5.0, 9.0, 12.0, 13.5], [1.5, 1.3, 1.0, 0.7], [WAX[1], WAX[2], WAX[3]], debris=deb)


# ------------------------------------------------------------------ Mason
def stone_shard_fx():
    fly = []
    for i in range(4):
        f = Fr()
        poly(f.b, [(-3, -1), (2, -2), (4, 0), (1, 2), (-3, 1)], STONE_R[2])
        line(f.b, -3, -1, 2, -2, STONE_R[4]); line(f.b, 1, 2, 4, 0, STONE_R[1])
        f.b.put(0, 0, STONE_R[3])
        s = done(f, INK)
        s = rot(s, i * 90)
        # dust trail
        for k in range(3):
            s.px[(-6 - k * 2, (k + i) % 2 - 1)] = hx("9a9690", 200 - k * 50)
        fly.append(RSpr(s.px))
    crack = []
    for i in range(4):
        c = C()
        rnd = jit(60 + i)
        for k in range(7):
            a = rnd.uniform(0, 2 * math.pi); d = 1 + i * 1.8 + rnd.random()
            c.put(*P(d * math.cos(a), d * 0.8 * math.sin(a)), STONE_R[4 - min(3, i)] if k % 2 else STONE_R[2])
        if i < 2: ell(c, 0, 0, 2.0 - i * 0.6, 1.6 - i * 0.5, [hx("b8b4ac"), hx("d8d4cc")])
        crack.append(R(c.spr()))
    return fixed_sheet("FxStoneShard", [("Fly", fly, [0.07] * 4), ("Wall", crack, [0.05, 0.05, 0.07, 0.08]),
                                        ("Hit", crack, [0.05, 0.05, 0.07, 0.08])], 22, 16, (11, 8))


def rubble_ring():
    def deb(c, i, back):
        if back: return
        rnd = jit(70 + i)
        for k in range(4 - i):
            a = rnd.uniform(0.3, 2.8)
            x = (4 + i * 4) * math.cos(a); y = -1 - (3 - i) * 1.4 - rnd.random()
            c.put(*P(x, y), STONE_R[3]); c.put(*P(x + 1, y), STONE_R[2]); c.put(*P(x, y + 1), STONE_R[1])
    return ring_pair("FxRubbleRing", [5.0, 9.0, 12.0, 13.5], [1.6, 1.4, 1.0, 0.7], [STONE_R[1], STONE_R[2], hx("a8a49c")], debris=deb)


# ------------------------------------------------------------------ Hexer
def hex_pin_fx():
    fly = []
    for i in range(3):
        c = C()
        line(c, -4, 0, 3, 0, [STEEL[1], STEEL[2]])
        c.put(4, 0, STEEL[2]); c.put(-5, 0, PIN_Y); c.put(-5, -1, PIN_Y); c.put(-6, 0, hx("a8901a"))
        for k in range(4):
            c.put(-7 - k * 2 - (i % 2), (k + i) % 3 - 1, HEX[3 - min(3, k)] + (230 - k * 40,))
        c.put(5, 0, HEX[3]); c.put(4, -1, HEX[2]); c.put(4, 1, HEX[2])
        fly.append(R(c.spr()))
    burst = []
    for i in range(4):
        c = C()
        r = 1.5 + i * 2.0
        for j in range(12):
            a = 2 * math.pi * j / 12 + i * 0.3
            if (j + i) % 2 and i > 1: continue
            c.put(*P(r * math.cos(a), r * math.sin(a)), HEX[3 - min(3, i)])
        if i < 2:
            for (x, y) in ((0, 0), (1, 0), (0, -1)): c.put(x, y, HEX[3])
        burst.append(R(c.spr()))
    return fixed_sheet("FxHexPin", [("Fly", fly, [0.06] * 3), ("Wall", burst, [0.05, 0.06, 0.07, 0.08]),
                                    ("Hit", burst, [0.05, 0.06, 0.07, 0.08])], 26, 20, (14, 10))


def hex_mark(i):
    """FxHexMark Loop 6: the Hexed overlay over the victim's head: a little pin-stuck heart of violet hex light."""
    c = C()
    s = [1.0, 1.1, 1.2, 1.1, 1.0, 0.9][i]
    cy = -4.0
    for y in range(-8, 8):
        for x in range(-7, 8):
            X, Y = x / (4.0 * s), -(y + 0.5) / (3.6 * s)
            v = (X * X + Y * Y - 1) ** 3 - X * X * Y ** 3      # heart curve (Y up)
            if v <= 0:
                l = -(x + y) / 6.0
                c.put(x, int(cy + y - 1), pick(HEX, l + 0.1))
    # pins through it
    for (x0, y0, a, col) in ((-3, -6, -130, PIN_R), (3, -7, -50, PIN_B), (0, -2, 100, PIN_Y)):
        ex_, ey_ = x0 + 3 * math.cos(math.radians(a)), y0 + 3 * math.sin(math.radians(a))
        line(c, x0, y0, ex_, ey_, STEEL[1]); c.put(*P(ex_, ey_), col)
    # sparks
    for k in range(3):
        a = (i / 6.0 + k / 3.0) * 2 * math.pi
        c.put(*P(7 * math.cos(a), cy - 1 + 3 * math.sin(a)), HEX[3] if k == i % 3 else HEX[2])
    return R(c.spr())


def hex_mark_fx():
    return fixed_sheet("FxHexMark", [("Loop", [hex_mark(i) for i in range(6)], [0.1] * 6)], 22, 20, (11, 17))


def stuffing_ring():
    def deb(c, i, back):
        if back or i > 2: return
        rnd = jit(80 + i)
        for k in range(4 - i):
            a = rnd.uniform(0.3, 2.8)
            x = (4 + i * 4) * math.cos(a); y = -2 - (3 - i) * 1.5
            c.put(*P(x, y), hx("f0eadc")); c.put(*P(x + 1, y), hx("d8d0c0"))
        c.put(*P(-6 + i, -4 + i), HEX[2])
    return ring_pair("FxStuffingRing", [5.0, 9.0, 12.0, 13.5], [1.3, 1.2, 0.9, 0.6], [BURLAP[1], BURLAP[2], BURLAP[3]], debris=deb)


# ------------------------------------------------------------------ Miser
def coin(c, x, y, phase, big=False):
    w = [2, 1, 0, 1][phase % 4]
    for dx in range(-w, w + 1):
        c.put(*P(x + dx, y), GOLD[3] if dx <= 0 else GOLD[2])
        if big: c.put(*P(x + dx, y + 1), GOLD[1])
    c.put(*P(x, y - 1), GOLD[4] if w else GOLD[3])


def coin_shot_fx():
    fly = []
    for i in range(4):
        c = C()
        coin(c, 0, 0, i, big=True)
        c.put(-3, 0, GOLD[2] + (180,)); c.put(-5, 1, GOLD[1] + (120,))
        fly.append(R(c.spr()))
    clink = []
    for i in range(4):
        c = C()
        r = 1 + i * 1.8
        for j in range(8):
            a = 2 * math.pi * j / 8
            if (j + i) % 2 and i > 1: continue
            c.put(*P(r * math.cos(a), r * math.sin(a)), GOLD[4 - min(3, i)])
        if i < 2: c.put(0, 0, GOLD[4])
        clink.append(R(c.spr()))
    return fixed_sheet("FxCoinShot", [("Fly", fly, [0.05] * 4), ("Wall", clink, [0.04, 0.05, 0.06, 0.08]),
                                      ("Hit", clink, [0.04, 0.05, 0.06, 0.08])], 16, 14, (8, 7))


def hoard_burst_fx():
    """FxHoardBurst Play 8: the Miser opens its hoard: a fountain of coins and ectoplasm bursting from the ghost."""
    frames = []
    ECTO = [hx("33846a", 200), hx("72cc9e", 220), hx("a8e8c4", 240)]
    for i in range(8):
        c = C()
        u = i / 7.0
        rnd = jit(90)
        for k in range(24):
            a = rnd.uniform(-math.pi * 0.95, -math.pi * 0.05)
            v = rnd.uniform(18, 34)
            x = v * u * math.cos(a)
            y = v * u * math.sin(a) + 30 * u * u - 6
            if y > 4: continue
            if k % 3 == 0:
                c.put(*P(x, y), ECTO[2 - min(2, int(u * 3))]); c.put(*P(x, y + 1), ECTO[0])
            else:
                coin(c, x, y, i + k)
        if i < 4:
            ell(c, 0, -6, 6 - i * 1.4, 5 - i * 1.2, [GOLD[2], GOLD[3], GOLD[4]], bias=0.3)
        frames.append(R(c.spr()))
    return fixed_sheet("FxHoardBurst", [("Play", frames, [0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.11, 0.12])], 76, 48, (38, 42))


def hoard_aura_fx():
    """FxHoardAura Loop 6: coins circling the Miser ghost while its hoard is ready to open (2+ fodder stored)."""
    frames = []
    for i in range(6):
        c = C()
        for k in range(4):
            a = (i / 6.0 + k / 4.0) * 2 * math.pi
            x, y = 12 * math.cos(a), -10 + 4 * math.sin(a)
            coin(c, x, y, i + k)
            c.put(*P(x - 2 * math.sin(a), y + 0.7 * math.cos(a)), GOLD[1] + (150,))
        frames.append(R(c.spr()))
    return fixed_sheet("FxHoardAura", [("Play", frames, [0.1] * 6)], 32, 22, (16, 20))


def coin_ring():
    def deb(c, i, back):
        if back or i > 2: return
        for k, a in enumerate((0.5, 1.6, 2.6)):
            coin(c, (5 + i * 3.5) * math.cos(a), -3 - (2 - i) * 2 - (k % 2), i + k)
    return ring_pair("FxCoinRing", [5.0, 9.0, 12.0, 13.5], [1.2, 1.1, 0.8, 0.6], [GOLD[1], GOLD[2], GOLD[3]], debris=deb)


# ------------------------------------------------------------------ silver: Haunt
SILV = [hx("6a7486", 200), hx("a4aec0", 220), hx("d8e0ec", 240), hx("ffffff", 255)]


def sheen_aura(cols, seed, name, n=6, coins_=False):
    frames = []
    for i in range(n):
        c = C()
        for k in range(5):
            a = (i / float(n) + k / 5.0) * 2 * math.pi + k
            r = 10 + 2 * math.sin(i + k)
            x, y = r * math.cos(a), -11 + 6 * math.sin(a)
            tw = (i + k) % 3
            c.put(*P(x, y), cols[3] if tw == 0 else cols[2])
            if tw == 0:
                for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)): c.put(*P(x + dx, y + dy), cols[1])
        frames.append(R(c.spr()))
    return fixed_sheet(name, [("Play", frames, [0.1] * n)], 30, 22, (15, 20))


# ------------------------------------------------------------------ gold: Soul Leap + Tithe
# ------------------------------------------------------------------ silver: SOULSTORM
SOUL = [hx("4a5a78", 200), hx("8a9cc0", 225), hx("c8d8f4", 245), hx("ffffff", 255)]
SOULB = [hx("6a7cb0", 215), hx("a8c0ff", 235), hx("e0ecff", 250), hx("ffffff", 255)]


def soul_wisp(i, big=False):
    """One tally wisp: a soft 3 px pearl (white core, pale plus around it) inside a 1 px see-through glow, with a
    2 px fading tail that sways. Bright (all 8 banked): warmer white, a stronger glow and a twinkle."""
    c = C()
    core = hx("ffffff", 255)
    mid = hx("e0ecff", 235) if big else hx("c8d8f4", 220)
    rim = hx("a8c0ff", 150) if big else hx("8a9cc0", 120)      # the pearl's corners: softer than its plus
    glow = hx("a8c0ff", 95) if big else hx("8a9cc0", 60)       # the 1 px glow
    for (dx, dy) in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, -1), (-1, 1), (1, 1)):
        c.put(dx, dy, glow)
    for (dx, dy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        c.put(dx, dy, rim)
    for (dx, dy) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        c.put(dx, dy, mid)
    c.put(0, 0, core)
    # tail behind (left), swaying a pixel up and down
    sway = [0, -1, 0, 1][i % 4]
    c.put(-3, sway, hx("a8c0ff", 130) if big else hx("8a9cc0", 110), over=False)
    c.put(-4, sway + (1 if sway >= 0 else -1) * (i % 2), hx("6a7cb0", 70) if big else hx("4a5a78", 60), over=False)
    if big and i % 2 == 0:
        c.put(0, -3, hx("ffffff", 200)); c.put(0, 3, hx("ffffff", 120))
    return R(c.spr())


def soul_wisp_fx():
    orbit = [soul_wisp(i) for i in range(4)]
    bright = [soul_wisp(i, big=True) for i in range(4)]
    # the silver ghost's orb tally: one per banked orb circling the ghost; Bright = all 8 banked (ascension ready)
    return fixed_sheet("FxSoulWisp", [("Orbit", orbit, [0.1] * 4), ("Bright", bright, [0.08] * 4)], 22, 16, (12, 8))


def silver_orb(i, big=False):
    """A silver orb on the floor: a bright pearl with a glint, a soft shadow, bobbing."""
    c = C()
    bob = [0, -1, -1, 0, 0, 0][i % 6]
    for x in range(-2, 3): c.put(x, 0, hx("1e1c26", 120))
    r = 2.4 if not big else 3.2
    ell(c, 0, -4 + bob, r, r, SOULB, bias=0.3)
    c.put(-1, -5 + bob, hx("ffffff")); c.put(0, -6 + bob, hx("ffffff")) if i % 3 == 0 else None
    if i in (1, 4):
        for (dx, dy) in ((3, -7), (4, -8), (3, -9)): c.put(dx, dy + bob, SOULB[3])
    return R(c.spr())


def silver_orb_fx():
    idle = [silver_orb(i) for i in range(6)]
    collect = []
    for i in range(5):
        c = C()
        r = 1 + i * 2.2
        for k in range(10):
            a = 2 * math.pi * k / 10 + i * 0.4
            if (k + i) % 2 and i > 1: continue
            c.put(*P(r * math.cos(a), -5 + r * 0.8 * math.sin(a) - i), SOULB[3 - min(3, i)])
        if i < 2: ell(c, 0, -5 - i * 2, 2.5 - i, 2.5 - i, SOULB[1:], bias=0.3)
        collect.append(R(c.spr()))
    return fixed_sheet("FxSilverOrb", [("Idle", idle, [0.12] * 6), ("Collect", collect, [0.04, 0.05, 0.06, 0.07, 0.09])], 24, 22, (12, 18))


def ascend_flash_fx():
    """ASCENSION: a column of silver light slams down on the body, a ring blasts out, motes rise and fade."""
    frames = []
    rnd = jit(77)
    motes = [(rnd.uniform(-12, 12), rnd.uniform(0, 1)) for _ in range(14)]
    for i in range(10):
        c = C()
        u = i / 9.0
        # pillar
        if i < 7:
            w = [2, 5, 7, 6, 5, 3, 1][i]
            top = -60 if i > 0 else -60 + 30
            for y in range(top, 1):
                for x in range(-w, w + 1):
                    t = abs(x) / max(1.0, w)
                    col = SOULB[3] if t < 0.35 else SOULB[2] if t < 0.7 else SOULB[1]
                    if t > 0.85 and (x + y + i) % 2: continue
                    c.put(x, y, col if i < 5 else SOULB[1])
        # ground ring
        if i >= 1:
            r = 4 + u * 26
            for k in range(28):
                a = 2 * math.pi * k / 28
                if u > 0.6 and k % 2: continue
                c.put(*P(r * math.cos(a), -1 + r * 0.33 * math.sin(a)), SOULB[3] if u < 0.5 else SOULB[2])
        # rising motes
        for (x, ph) in motes:
            y = -4 - (u + ph) % 1.0 * 40
            if i >= 2 and (i + int(x)) % 3: c.put(*P(x, y), SOULB[2] if u < 0.7 else SOULB[1])
        frames.append(R(c.spr()))
    return fixed_sheet("FxAscendFlash", [("Play", frames, [0.04, 0.04, 0.05, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.12])], 70, 76, (35, 64))


def ascend_aura_fx():
    """An ascended body: silver sparkles turning slowly round its feet."""
    frames = []
    for i in range(6):
        c = C()
        for k in range(6):
            a = 2 * math.pi * k / 6 + i * (math.pi / 18)
            x, y = 11 * math.cos(a), -2 + 3.6 * math.sin(a)
            tw = (k + i) % 3
            c.put(*P(x, y), SOULB[3] if tw == 0 else SOULB[1])
            if tw == 0:
                for (dx, dy) in ((1, 0), (-1, 0), (0, -1)): c.put(*P(x + dx, y + dy), SOULB[2])
        frames.append(R(c.spr()))
    return fixed_sheet("FxAscendAura", [("Loop", frames, [0.11] * 6)], 28, 12, (14, 8))


def ascend_spark_fx():
    """An ascended monster's hit: a spray of silver sparks."""
    frames = []
    rnd = jit(55)
    pts = [(rnd.uniform(-math.pi, math.pi), rnd.uniform(4, 9)) for _ in range(9)]
    for i in range(5):
        c = C()
        u = i / 4.0
        for (a, v) in pts:
            x, y = v * u * math.cos(a), v * u * math.sin(a) + 4 * u * u
            c.put(*P(x, y), SOULB[3] if u < 0.5 else SOULB[1])
            if u < 0.6: c.put(*P(x - math.cos(a), y - math.sin(a)), SOULB[2])
        if i == 0: ell(c, 0, 0, 2, 2, SOULB[2:], bias=0.4)
        frames.append(R(c.spr()))
    return fixed_sheet("FxAscendSpark", [("Play", frames, [0.04, 0.05, 0.06, 0.07, 0.09])], 28, 28, (14, 12))


# ------------------------------------------------------------------ gold: THRALLS
GOLDA = mute_rgb([hx("6a4a10", 230), hx("a87818", 240), hx("e0b02a", 250), hx("ffe070", 255), hx("fff8c8", 255)], 0.6)
ECTO = [hx("4a6a5e", 220), hx("6a8f78", 235), hx("9ab89a", 245), hx("d0dccc", 255)]      # the blobs' gel


def thrall_mark_fx():
    """Over a thrall's head: a little gold crown on a loop of chain (it is bound to its gold ghost)."""
    frames = []
    for i in range(6):
        c = C()
        bob = [0, -1, -1, 0, 0, 0][i]
        # chain hoop
        for k in range(10):
            a = 2 * math.pi * k / 10 + i * 0.25
            c.put(*P(5 * math.cos(a), -2 + bob + 1.6 * math.sin(a)), GOLDA[1] if k % 2 else GOLDA[2])
        # crown
        for x in range(-3, 4):
            c.put(x, -4 + bob, GOLDA[2] if x < 1 else GOLDA[1])
            c.put(x, -5 + bob, GOLDA[3] if x < 1 else GOLDA[2])
        for x in (-3, 0, 3):
            c.put(x, -6 + bob, GOLDA[3]); c.put(x, -7 + bob, GOLDA[4] if (x + i) % 2 == 0 else GOLDA[3])
        c.put(0, -5 + bob, hx("d83a3a"))
        frames.append(R(c.spr()))
    return fixed_sheet("FxThrallMark", [("Loop", frames, [0.12] * 6)], 14, 12, (7, 10))


def thrall_sigil_fx():
    """Under a thrall's feet: a slowly turning gold binding rune."""
    frames = []
    for i in range(6):
        c = C()
        for k in range(16):
            a = 2 * math.pi * k / 16 + i * (math.pi / 24)
            x, y = 10 * math.cos(a), -2 + 3.4 * math.sin(a)
            c.put(*P(x, y), GOLDA[2] if k % 4 else GOLDA[3])
        for k in range(3):
            a = 2 * math.pi * k / 3 - i * (math.pi / 18)
            x, y = 6 * math.cos(a), -2 + 2.0 * math.sin(a)
            c.put(*P(x, y), GOLDA[1]); c.put(*P(x + 1, y), GOLDA[2])
        frames.append(R(c.spr()))
    return fixed_sheet("FxThrallSigil", [("Loop", frames, [0.12] * 6)], 26, 10, (13, 7))


def thrall_count_fx():
    """Over the gold player's head: one or two little gold crowns = thralls out (a third releases the oldest)."""
    def crowns(n):
        c = C()
        for j in range(n):
            ox = int((j - (n - 1) / 2.0) * 8)
            for x in range(-2, 3):
                c.put(*P(ox + x, -1), GOLDA[2]); c.put(*P(ox + x, -2), GOLDA[3] if x < 1 else GOLDA[2])
            for x in (-2, 0, 2): c.put(*P(ox + x, -3), GOLDA[4] if x == 0 else GOLDA[3])
            for x in range(-3, 4): c.put(*P(ox + x, 0), GOLDA[0])
        return R(c.spr())
    return fixed_sheet("FxThrallCount", [("One", [crowns(1)], [0.2])], 18, 6, (9, 5))


def thrall_locked_fx():
    """Jump-out refused (a thrall is already out): a gold chain snaps shut round the monster, a padlock flickers."""
    frames = []
    for i in range(6):
        c = C()
        on = i in (0, 1, 3)
        r = 9 - (1 if i == 0 else 0)
        for k in range(18):
            a = 2 * math.pi * k / 18 + i * 0.15
            x, y = r * math.cos(a), -9 + r * 0.9 * math.sin(a)
            if not on and k % 3 == 0: continue
            c.put(*P(x, y), (GOLDA[3] if k % 2 else GOLDA[1]) if on else GOLDA[0])
        # the padlock on the chain's front
        if i < 5:
            lx, ly = 0, -1
            for x in range(-2, 3):
                for y in range(0, 3): c.put(lx + x, ly + y - 2, GOLDA[2] if on else GOLDA[1])
            c.put(lx - 1, ly - 3, GOLDA[3]); c.put(lx + 1, ly - 3, GOLDA[3]); c.put(lx - 1, ly - 4, GOLDA[3]); c.put(lx + 1, ly - 4, GOLDA[3]); c.put(lx, ly - 5, GOLDA[4])
            c.put(lx, ly - 1, BLACK)
        frames.append(R(c.spr()))
    return fixed_sheet("FxThrallLocked", [("Play", frames, [0.05, 0.06, 0.05, 0.08, 0.08, 0.1])], 24, 22, (12, 20))


def thrall_jump_fx():
    """Jumping out: a gold soul tears up out of the body, a ring of gold light at its feet."""
    frames = []
    for i in range(7):
        c = C()
        u = i / 6.0
        r = 3 + u * 12
        for k in range(14):
            a = 2 * math.pi * k / 14
            if u > 0.6 and k % 2: continue
            c.put(*P(r * math.cos(a), -2 + r * 0.35 * math.sin(a)), GOLDA[3] if u < 0.5 else GOLDA[2])
        sy = -6 - u * 18
        if i < 6:
            ell(c, 0, sy, 2.6, 3.0, [GOLDA[2], GOLDA[3], GOLDA[4]], bias=0.3)
            for k in range(4):
                c.put(*P((k - 1.5) * 1.2, sy + 3 + k * 1.6), GOLDA[3 - min(2, k)])
            c.put(*P(-1, sy - 0.5), BLACK); c.put(*P(1, sy - 0.5), BLACK)
        frames.append(R(c.spr()))
    return fixed_sheet("FxThrallJump", [("Play", frames, [0.04, 0.05, 0.05, 0.06, 0.07, 0.08, 0.1])], 34, 34, (17, 30))


def thrall_burst_fx():
    """A thrall dies: it bursts into ectoplasm (with gold flecks), which flies off to its gold ghost."""
    frames = []
    rnd = jit(44)
    parts = [(rnd.uniform(-math.pi, 0), rnd.uniform(10, 18), k % 4 == 0) for k in range(16)]
    for i in range(7):
        c = C()
        u = i / 6.0
        for (a, v, gold) in parts:
            x = v * u * math.cos(a); y = -8 + v * u * math.sin(a) * 0.8 + 8 * u * u
            if u > 0.8 and rnd.random() < 0.4: continue
            col = (GOLDA[3] if gold else ECTO[2 if u < 0.5 else 1])
            c.put(*P(x, y), col)
            if not gold and u < 0.6: c.put(*P(x, y + 1), ECTO[0])
        if i < 3:
            ell(c, 0, -8, 4 - i, 4 - i, [ECTO[1], ECTO[2], ECTO[3]], bias=0.3)
        frames.append(R(c.spr()))
    return fixed_sheet("FxThrallBurst", [("Play", frames, [0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.12])], 40, 30, (20, 24))


FX = {"FxWailRing": wail_ring, "FxShriek": shriek_fx, "FxKeenerRise": keener_rise, "FxGrave": grave_fx,
      "FxGraveRaise": grave_raise, "FxFuseBlast": fuse_blast_fx, "FxFuseSpark": fuse_spark_fx, "FxWaxRing": wax_ring, "FxStoneShard": stone_shard_fx,
      "FxRubbleRing": rubble_ring, "FxHexPin": hex_pin_fx, "FxHexMark": hex_mark_fx, "FxStuffingRing": stuffing_ring,
      "FxCoinShot": coin_shot_fx, "FxHoardBurst": hoard_burst_fx, "FxHoardAura": hoard_aura_fx, "FxCoinRing": coin_ring,
      "FxSilverAura": lambda: sheen_aura(SILV, 1, "FxSilverAura"),
      "FxGoldAura": lambda: sheen_aura([hx("8a6010", 200)] + GOLD[2:], 2, "FxGoldAura"),
      "FxThrallMark": thrall_mark_fx, "FxThrallSigil": thrall_sigil_fx, "FxThrallCount": thrall_count_fx,
      "FxSoulWisp": soul_wisp_fx, "FxSilverOrb": silver_orb_fx, "FxAscendFlash": ascend_flash_fx,
      "FxAscendAura": ascend_aura_fx, "FxAscendSpark": ascend_spark_fx, "FxThrallLocked": thrall_locked_fx, "FxThrallJump": thrall_jump_fx, "FxThrallBurst": thrall_burst_fx}


# ===================================================================================================== PORTRAITS
def _ghost_base(ph, arms):
    """The vanilla-style portrait hag (ghost_rigs primitives, palette chars) on the portrait background, as RGB.
    arms(c, bob, sw) draws the arms (chars). Returns (rgb dict, bob, sw)."""
    import ghost_rigs as GR
    from anim import PALETTE
    c = GR.cv(); GR.portrait_bg(c)
    bob = [0, -1, -1, 0][ph]; sw = [0, 1, 0, -1][ph]
    GR.ghost_body(c, ph, bob, sw)
    GR.ghost_hair(c, bob, sw)
    arms(c, bob, sw)
    return c, bob, sw


def _finish_portrait(c, over):
    import ghost_rigs as GR
    from anim import PALETTE
    spr = GR.crop_portrait(c)
    px = {k: PALETTE[v] + (255,) for k, v in spr.px.items() if PALETTE.get(v)}
    for k, v in over.items():
        if -14 <= k[0] <= 14 and -23 <= k[1] <= 0:
            a = (v[3] if len(v) == 4 else 255) / 255.0
            b = px.get(k, (0, 0, 0, 255))
            px[k] = tuple(int(round(v[j] * a + b[j] * (1 - a))) for j in range(3)) + (255,)
    return RSpr(px)


def portrait_banshee(ph):
    import ghost_rigs as GR
    def arms(c, bob, sw):
        GR.ghost_arm(c, (-1.5, -9 + bob), (1, -12 + bob), (4, -11.5 + bob), fingers=False)
        GR.ghost_arm(c, (6.5, -9 + bob), (9, -12 + bob), (7.5, -12 + bob), fingers=False)
    c, bob, sw = _ghost_base(ph, arms)
    # wild hair flung up and back
    for (x0, y0, x1, y1) in ((-3, -18, -10, -22), (0, -19, -4, -23), (-5, -15, -13, -16)):
        GR.tube(c, [(x0, y0 + bob), ((x0 + x1) / 2, (y0 + y1) / 2 + bob - sw), (x1, y1 + bob)], [1.1, 0.8, 0.4], "DC")
    GR.ghost_face(c, bob, mouth="wail", ph=ph)
    o = Canvas()
    for k in range(3):
        r = 3 + ((ph + k * 2) % 6) * 1.6
        for j in range(-3, 4):
            a = j * 0.3
            o.put(*P(6 + r * math.cos(a), -10 + bob + r * 1.1 * math.sin(a)), MIST[3] if r < 6 else MIST[2] if r < 10 else MIST[1])
    return _finish_portrait(c, o.px)


def portrait_sexton(ph):
    import ghost_rigs as GR
    def arms(c, bob, sw):
        GR.ghost_arm(c, (-1.5, -9 + bob), (-5, -12 + bob), (-6, -16 + bob), fingers=False)
        GR.ghost_arm(c, (6.5, -9 + bob), (9, -8 + bob), (10, -6 + bob), fingers=False)
    c, bob, sw = _ghost_base(ph, arms)
    GR.ghost_face(c, bob, mouth="hum", ph=ph)
    o = Canvas()
    # the spade over her shoulder, blade up behind
    line(o, -6, -14 + bob, -12, -21 + bob, [WOOD[3], WOOD[2]])
    for (dx, dy) in ((0, 0), (1, 0), (-1, 0), (0, -1), (1, -1), (-1, -1), (0, -2), (-1, -2), (0, 1)):
        o.put(-13 + dx, -22 + dy + bob, IRON[3] if dx < 0 else IRON[2])
    # lantern with a green soul flame
    line(o, 10, -6 + bob, 10, -4 + bob, IRON[2])
    for yy in range(-3, 2):
        for xx in (9, 10, 11):
            o.put(xx, yy + bob, IRON[1] if xx != 10 or yy in (-3, 1) else (SOUL_G[2] if (ph + yy) % 2 else SOUL_G[3]))
    # a fresh grave in the corner
    for x in range(-14, -6):
        o.put(x, 0, hx("46321e")); o.put(x, -1, hx("6a4c2c") if x % 2 else hx("8a6a40"))
    for y in range(-6, -1):
        o.put(-11, y, STONE_G[2]); o.put(-10, y, STONE_G[1])
    o.put(-11, -7, STONE_G[3])
    return _finish_portrait(c, o.px)


def portrait_kindler(ph):
    import ghost_rigs as GR
    def arms(c, bob, sw):
        GR.ghost_arm(c, (-1.5, -9 + bob), (-6, -12.5 + bob), (-8, -17 + bob + sw * 0.5))
        GR.ghost_arm(c, (6.5, -9 + bob), (9, -13 + bob), (10, -17 + bob), fingers=False)
    c, bob, sw = _ghost_base(ph, arms)
    GR.ghost_face(c, bob, mouth="hum", ph=ph)
    o = Canvas()
    line(o, 10, -16 + bob, 12, -22 + bob, [WAX[3], WAX[2]])          # the taper
    fl = [0, 1, 0, -1][ph]
    for (dx, dy, col) in ((12, -23, FLAME[3]), (12 + fl, -24, FLAME[2]), (12, -25, FLAME[1]), (11, -23, FLAME[1]), (13, -23, FLAME[2])):
        o.put(dx, dy + bob, col)
    # a little Fusebelly at her feet, fuse lit
    ell(o, 9, -3, 3.2, 2.8, WAX, bias=0.2)
    o.put(9, -3, INK); o.put(11, -3, INK); o.put(10, -2, INK)
    o.put(8, -6, hx("3a2a1a")); o.put(8, -7, FLAME[2] if ph % 2 else FLAME[3])
    for k in range(2):
        o.put(13 - k * 3 + (ph % 2), -18 - ((ph + k) % 3) + bob, FLAME[2])
    return _finish_portrait(c, o.px)


def portrait_mason(ph):
    import ghost_rigs as GR
    mal = [-80, -110, -60, -20][ph]
    def arms(c, bob, sw):
        GR.ghost_arm(c, (-1.5, -9 + bob), (-5, -13 + bob), (-6, -17 + bob), fingers=False)
        GR.ghost_arm(c, (6.5, -9 + bob), (9, -9 + bob), (11, -8 + bob), fingers=False)
    c, bob, sw = _ghost_base(ph, arms)
    GR.ghost_face(c, bob, eyes="normal", mouth="grit", ph=ph)
    o = Canvas()
    a = math.radians(mal)
    ex, ey = -6 + 5 * math.cos(a), -17 + bob + 5 * math.sin(a)
    line(o, -6, -17 + bob, ex, ey, [WOOD[2], WOOD[3]])
    for s_ in (-1, 0, 1):
        for t in (0, 1):
            o.put(*P(ex - math.sin(a) * s_ + math.cos(a) * t, ey + math.cos(a) * s_ + math.sin(a) * t), WOOD[1] if s_ > 0 else WOOD[3])
    line(o, 11, -8 + bob, 14, -9 + bob, [IRON[3], IRON[2]])
    # a gargling's horned head in the corner
    ell(o, -9, -3, 3.4, 2.8, STONE_R, bias=0.2)
    line(o, -11, -5, -12, -8, STONE_R[3]); line(o, -8, -6, -8, -8, STONE_R[3])
    o.put(-8, -3, AMBER[2]); o.put(-6, -3, AMBER[2])
    if ph == 3:
        for (x, y) in ((13, -12), (14, -10), (12, -11)): o.put(x, y + bob, FLAME[2])
    return _finish_portrait(c, o.px)


def portrait_hexer(ph):
    import ghost_rigs as GR
    def arms(c, bob, sw):
        GR.ghost_arm(c, (-1.5, -9 + bob), (-6, -12.5 + bob), (-8, -15 + bob), fingers=False)
        GR.ghost_arm(c, (6.5, -9 + bob), (10, -12 + bob), (11, -15 + bob), fingers=False)
    c, bob, sw = _ghost_base(ph, arms)
    GR.ghost_face(c, bob, eyes="angry", mouth="grit", ph=ph)
    o = Canvas()
    # the poppet held up in her far hand
    ell(o, -9, -18 + bob, 2.6, 2.4, BURLAP, bias=0.2)
    ell(o, -9, -14 + bob, 1.8, 2.0, BURLAP, bias=0.1)
    o.put(-9, -18 + bob, BLACK); o.put(-8, -18 + bob, WHITE); o.put(-9, -16 + bob, STITCH); o.put(-8, -16 + bob, STITCH)
    line(o, -12, -21 + bob, -9, -18 + bob, STEEL[1]); o.put(-12, -21 + bob, PIN_R)
    # a hex pin in the near hand, glowing
    line(o, 11, -15 + bob, 14, -20 + bob, [STEEL[1], STEEL[2]]); o.put(10, -14 + bob, PIN_B)
    o.put(14, -21 + bob, HEX[3]); o.put(13, -21 + bob, HEX[2])
    for k in range(3):
        a = (ph / 4.0 + k / 3.0) * 2 * math.pi
        o.put(*P(-9 + 5 * math.cos(a), -16 + bob + 3 * math.sin(a)), HEX[2] if k else HEX[3])
    return _finish_portrait(c, o.px)


def portrait_miser(ph):
    import ghost_rigs as GR
    def arms(c, bob, sw):
        GR.ghost_arm(c, (-1, -8.5 + bob), (0, -5 + bob), (4, -5.5 + bob), fingers=False)
        GR.ghost_arm(c, (7, -8.5 + bob), (10, -5.5 + bob), (8, -5 + bob), fingers=False)
    c, bob, sw = _ghost_base(ph, arms)
    GR.ghost_face(c, bob, eyes="normal", mouth="hum", ph=ph)
    o = Canvas()
    # the strongbox hugged to her belly, lid ajar, gold light
    for yy in range(-4, 1):
        for xx in range(1, 12):
            edge = xx in (1, 11) or yy == 0
            o.put(xx, yy, WOOD[1] if edge else WOOD[3] if yy == -4 else WOOD[2])
    for yy in range(-4, 1): o.put(4, yy, IRON[2]); o.put(8, yy, IRON[2])
    for xx in range(2, 11): o.put(xx, -5, GOLD[3] if xx % 3 else GOLD[4])
    o.put(6, -2, GOLD[3]); o.put(6, -1, GOLD[1])
    for k in range(4):
        a = (ph / 4.0 + k / 4.0) * 2 * math.pi
        x, y = 1 + 11 * math.cos(a), -14 + 4 * math.sin(a) + bob
        o.put(*P(x, y), GOLD[3]); o.put(*P(x + 1, y), GOLD[2]); o.put(*P(x, y - 1), GOLD[4])
    return _finish_portrait(c, o.px)


PORTRAIT_SRC = {"GhostBanshee": portrait_banshee, "GhostSexton": portrait_sexton, "GhostKindler": portrait_kindler,
                "GhostMason": portrait_mason, "GhostHexer": portrait_hexer, "GhostMiser": portrait_miser}
# every regular mod form's portrait = its own colour vignette + the ghost (shifted left) + its signature
# fodder creature standing bottom-right, so the ten cells tell apart at 1x. (tint centre, tint edge, fodder sheet, ghost dx)
PORTRAIT_LOOK = {
    "GhostGleaner": ("2e6a52", "0e1c18", "BlobMote", -3),
    "GhostBinder": ("2a6a7a", "0c1a20", "BlobGel", -4),
    "GhostPoltergeist": ("6a3434", "200c0e", "BlobSpitter", -4),
    "GhostBanshee": ("3e4a6e", "0e1026", "FodKeener", -4),
    "GhostSexton": ("4e5a2a", "141808", "FodRevenant", -4),
    "GhostKindler": ("6e4a2a", "221a14", "FodFusebelly", -3),
    "GhostMason": ("5a5e6a", "16181c", "FodGargling", -5),
    "GhostHexer": ("4e3460", "1c1622", "FodPoppet", -1),
    "GhostMiser": ("6a5a2e", "201c12", "FodMimic", -5),
}
PORTRAITS = list(PORTRAIT_LOOK)
BG_RGB = None


def _old_three(name, ph):
    import ghost_rigs as GR
    from anim import PALETTE
    fn = {"GhostGleaner": GR.ghost_gleaner, "GhostBinder": GR.ghost_binder, "GhostPoltergeist": GR.ghost_poltergeist}[name]
    spr = fn(ph)
    return RSpr({k: PALETTE[v] + (255,) for k, v in spr.px.items() if PALETTE.get(v)})


def _fodder_frame(sheet):
    """The fodder's Portrait frame (its idle pose) as {(x, y): rgba}, feet at (0, 0)."""
    import json
    from PIL import Image
    d = KT.OUT_DIR[0] if os.path.exists(os.path.join(KT.OUT_DIR[0], sheet + ".json")) else KT.OUT
    m = json.load(open(os.path.join(d, sheet + ".json")))
    im = Image.open(os.path.join(d, sheet + ".png")).convert("RGBA")
    a = [x for x in m["anims"] if x["name"] == "Portrait"][0]
    f = a["frames"][0]
    x0, y0 = (f % m["cols"]) * m["cellW"], (f // m["cols"]) * m["cellH"]
    fx, fy = m["cellW"] // 2, m["cellH"] - 2
    px = {}
    for y in range(m["cellH"]):
        for x in range(m["cellW"]):
            v = im.getpixel((x0 + x, y0 + y))
            if v[3] > 0: px[(x - fx, y - fy)] = v
    return px


def styled_portrait(name, ph):
    from anim import PALETTE
    centre, edge, fodder, gdx = PORTRAIT_LOOK[name]
    base = PORTRAIT_SRC[name](ph) if name in PORTRAIT_SRC else _old_three(name, ph)
    bgset = {PALETTE[c] for c in "#%&"}
    C0, C1 = hx(centre), hx(edge)
    out = {}
    # the form's own colour: a glow behind the ghost fading to a dark edge, dithered at the band edges
    for y in range(-23, 1):
        for x in range(-14, 15):
            d = math.hypot((x + 2) / 14.0, (y + 13) / 12.0) + (0.05 if (x + y) % 2 else -0.05)
            t = max(0.0, min(1.0, (d - 0.25) / 0.85))
            t = round(t * 4) / 4.0
            out[(x, y)] = tuple(int(C0[j] * (1 - t) + C1[j] * t) for j in range(3)) + (255,)
    # the ghost, shifted left to make room for the fodder
    for (x, y), v in base.px.items():
        if v[:3] in bgset: continue
        X = x + gdx
        if -14 <= X <= 14: out[(X, y)] = v
    # a floor shadow and the signature fodder standing bottom-right
    fpx = _fodder_frame(fodder)
    xs = [k[0] for k in fpx]
    fx0 = 13 - max(xs)
    for x in range(min(xs) + fx0 - 1, max(xs) + fx0 + 2):
        if -14 <= x <= 14 and (x, 0) in out:
            v = out[(x, 0)]; out[(x, 0)] = tuple(int(c * 0.55) for c in v[:3]) + (255,)
    for (x, y), v in fpx.items():
        X, Y = x + fx0, y
        if -14 <= X <= 14 and -23 <= Y <= 0:
            a = v[3] / 255.0
            b = out[(X, Y)]
            out[(X, Y)] = tuple(int(v[j] * a + b[j] * (1 - a)) for j in range(3)) + (255,)
    # a 1 px frame in the form's colour, lit top-left
    hi = tuple(min(255, int(c * 1.6) + 30) for c in C0)
    lo = tuple(int(c * 0.7) for c in C0)
    for x in range(-14, 15):
        out[(x, -23)] = hi + (255,); out[(x, 0)] = lo + (255,) if (x, 0) not in fpx else out[(x, 0)]
    for y in range(-23, 1):
        out[(-14, y)] = hi + (255,); out[(14, y)] = lo + (255,)
    return RSpr(out)


def build_portrait(name):
    frames = [styled_portrait(name, i) for i in range(4)]
    b = fixed_sheet(name, [("Idle", frames, [0.25, 0.2, 0.25, 0.2])], 29, 24, (14, 23), scale=10, kind="portrait")
    crop = b["img"].crop((0, 0, 29 * 4, 24)).load()
    assert all(crop[x, y][3] == 255 for x in range(29 * 4) for y in range(24)), name + " must be opaque"
    return b


def _fodder_job(fn):
    return lambda: fn(KT.OUT_DIR[0])


# the fodder creatures are drawn by ghosts_v2_fodder.py (material renderer); run here so a full build still makes them
import ghosts_v2_fodder as FOD  # noqa: E402
FODDER = {n: _fodder_job(fn) for n, fn in FOD.JOBS}


def main():
    args = sys.argv[1:]
    only = None
    if "--only" in args:
        i = args.index("--only"); only = set(args[i + 1].split(",")); del args[i:i + 2]
    if "--out" in args:
        i = args.index("--out"); KT.OUT_DIR[0] = args[i + 1]; del args[i:i + 2]
        os.makedirs(KT.OUT_DIR[0], exist_ok=True)
    for n, fn in list(FODDER.items()) + list(FX.items()):
        if only is None or n in only: fn()
    for n in PORTRAITS:
        if only is None or n in only: build_portrait(n)


if __name__ == "__main__":
    main()
