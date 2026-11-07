"""Effect / projectile sprites for the Vhorrul pack, drawn procedurally in the pack palette.
Each effect becomes its own sheet (feet point = effect centre/ground contact)."""
import math, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from anim import Spr, pack, preview

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "art/out")


def ellipse(cx, cy, rx, ry, fill, rim=None, hi=None, rnd=None, jitter=0.0):
    px = {}
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            j = (rnd.random() - 0.5) * jitter if rnd else 0
            d = ((x - cx) / max(rx, 0.5)) ** 2 + ((y - cy) / max(ry, 0.5)) ** 2 + j
            if d <= 1.0:
                c = fill
                if rim and d > 0.62: c = rim
                if hi and d < 0.25 and y < cy and x < cx + rx * 0.3: c = hi
                px[(x, y)] = c
    return px


def wax_glob():
    """Thrown blob of molten wax, 4-frame wobble in flight."""
    frames = []
    for i in range(4):
        rx, ry = [(3, 2.5), (3.4, 2.2), (3, 2.6), (2.6, 2.9)][i]
        p = ellipse(0, -3, rx, ry, 'W', rim='w', hi='X')
        p[(int(-rx), -1 + (i % 2))] = 'w'  # trailing drip
        p[(-1, -6 + (i % 2))] = 'O' if i % 2 == 0 else 'o'  # ember fleck
        frames.append(Spr(p))
    return frames


def wax_puddle(n_grow=4, n_idle=2, n_fade=3):
    rnd = random.Random(7)
    grow, idle, fade = [], [], []
    for i in range(n_grow):
        k = (i + 1) / n_grow
        grow.append(Spr(ellipse(0, -2, 9 * k + 1, 3 * k + 0.6, 'w', rim='h', hi='W', rnd=rnd, jitter=0.25)))
    full = ellipse(0, -2, 10, 3.6, 'w', rim='h', hi='W', rnd=random.Random(3), jitter=0.2)
    for i in range(n_idle):
        p = dict(full)
        p[(-4 + i * 3, -3)] = 'X'  # glints
        p[(3 - i * 2, -2)] = 'X'
        idle.append(Spr(p))
    for i in range(n_fade):
        k = 1 - (i + 1) / (n_fade + 1)
        p = {kk: ('h' if v == 'w' else 'g' if v == 'h' else 'w') for kk, v in full.items()
             if random.Random(kk[0] * 31 + kk[1] + i).random() < k + 0.15}
        fade.append(Spr(p))
    return grow, idle, fade


def ember_patch(n=6):
    """Burning ground: a sooty puddle with tongues of flame that dance."""
    base = ellipse(0, -2, 9, 3.2, 'k', rim='K', hi='a', rnd=random.Random(5), jitter=0.3)
    frames = []
    for i in range(n):
        p = dict(base)
        rnd = random.Random(100 + i)
        for fx in range(-7, 8, 3):
            h = rnd.randint(2, 5)
            off = (fx + i) % 2
            for t in range(h):
                c = 'y' if t == 0 and h > 3 else 'Y' if t < 2 else 'O' if t < h - 1 else 'o'
                p[(fx + (off if t > 1 else 0), -3 - t)] = c
        frames.append(Spr(p))
    return frames


def ember_spark(n=4):
    frames = []
    shapes = [[(0, 0, 'y'), (1, 0, 'Y'), (-1, 0, 'O'), (0, -1, 'O'), (0, 1, 'o')],
              [(0, 0, 'Y'), (1, -1, 'O'), (-1, 1, 'o'), (0, -1, 'y')],
              [(0, 0, 'y'), (1, 0, 'O'), (-1, 0, 'Y'), (0, 1, 'O'), (-2, 0, 'o')],
              [(0, 0, 'Y'), (-1, -1, 'O'), (1, 1, 'o'), (0, 1, 'y')]]
    for i in range(n):
        frames.append(Spr({(x, y - 4): c for x, y, c in shapes[i % 4]}))
    return frames


def candle_bolt(n=4):
    frames = []
    for i in range(n):
        p = {}
        for x in range(-4, 3):
            p[(x, -4)] = 'Y' if x > 0 else 'O' if x > -3 else 'o'
        p[(2, -4)] = 'y'; p[(1, -5)] = 'O'; p[(1, -3)] = 'O'
        p[(-5 - (i % 2), -4 + (i % 3) - 1)] = 'o'
        p[(-2, -5 + (i % 2))] = 'O'
        frames.append(Spr(p))
    return frames


def lantern_orb(n=4):
    frames = []
    for i in range(n):
        p = ellipse(0, -4, 2.6 + (i % 2) * 0.4, 2.6, 'B', rim='b', hi='c')
        p[(-3 - (i % 2), -4)] = 'b'
        p[(-4, -3 - (i % 2))] = 'b'
        frames.append(Spr(p))
    return frames


def ash_cloud(n=5):
    """v0.10: a billowing ash cloud in pale ash greys (it used to be dark dots that vanished on dark floors):
    filled puffs, lit pale on top, a darker underside, an ember winking in it."""
    frames = []
    rnd0 = random.Random(41)
    puffs = [(rnd0.uniform(0.15, 1.0), rnd0.uniform(-0.55, 0.55), rnd0.uniform(1.3, 2.6)) for _ in range(9)]
    for i in range(n):
        k = (i + 1) / n
        p = {}
        for j, (t, a, r0) in enumerate(puffs):
            if t > 0.45 + k: continue
            d = 2 + t * (4 + 10 * k)
            cx, cy = d * math.cos(a) * 1.1, d * math.sin(a) * 0.5 - 5 - k * 1.2 * t
            r = r0 * (0.7 + 0.6 * k) * (0.75 if i == n - 1 else 1.0)
            R = int(r) + 1
            for y in range(int(cy - R), int(cy + R) + 1):
                for x in range(int(cx - R), int(cx + R) + 1):
                    dd = ((x - cx) ** 2 + (y - cy) ** 2) / max(0.5, r * r)
                    if dd > 1.0: continue
                    if i == n - 1 and random.Random(x * 131 + y * 17).random() < 0.4: continue   # last frame thins out
                    l = -(x - cx + y - cy) / max(1.0, r) * 0.6 + (1 - dd) * 0.5
                    c = 'u' if l > 0.55 else 'U' if l > 0.05 else 'S' if l > -0.45 else 's'
                    if i >= n - 2 and c == 'u': c = 'U'
                    if p.get((x, y)) in ('u', 'U') and c in ('S', 's'): continue
                    p[(x, y)] = c
        if i < 3:
            p[(int(round(3 + 5 * k)), -5)] = 'O'; p[(int(round(3 + 5 * k)), -6)] = 'Y'
        frames.append(Spr(p))
    return frames


def shockwave_ring(n=4):
    """v0.10: a full floor ellipse (it was only the front arc, so the stripped vanilla back half left it a half ring):
    a thick pale wax front edge, a duller back edge, molten drips thrown up off the rim."""
    frames = []
    for i in range(n):
        rx, ry = 6 + 9 * i, 2.4 + 2.9 * i
        p = {}
        steps = max(24, int((rx + ry) * 5))
        for s_ in range(steps):
            a = 2 * math.pi * s_ / steps
            if i == 3 and (s_ // 3) % 3 == 0: continue                                # breaking up
            x = int(round(rx * math.cos(a))); y = int(round(ry * math.sin(a)))
            front = math.sin(a) > -0.15
            if front:
                p[(x, y)] = 'X' if i < 2 else 'W' if i < 3 else 'w'
                if i < 3: p[(x, y + 1)] = 'w' if i < 2 else 'h'
                if i < 2: p.setdefault((x, y - 1), 'W')
            else:
                p.setdefault((x, y), 'w' if i < 2 else 'h')
        rnd = random.Random(70 + i)
        for _ in range(4 + i * 2):                                                     # drips flung off the rim
            a = rnd.uniform(0, 2 * math.pi)
            x = int(round(rx * 0.95 * math.cos(a))); y = int(round(ry * 0.95 * math.sin(a) - rnd.uniform(1, 2 + i)))
            p[(x, y)] = 'O' if i < 2 and rnd.random() < 0.5 else 'W'
        if i == 0:
            for x in range(-3, 4): p[(x, 0)] = 'O' if abs(x) < 2 else 'o'
        frames.append(Spr(p))
    return frames


def wax_plate_orbit(n=6):
    """Two wax shards orbiting a monster's chest (centred 10px above the feet)."""
    frames = []
    for i in range(n):
        p = {}
        for k in range(2):
            a = math.radians(i * (360 / n) + k * 180)
            cx, cy = int(round(9 * math.cos(a))), int(round(-10 + 3 * math.sin(a)))
            front = math.sin(a) > 0
            for dx, dy, c in ((0, 0, 'X' if front else 'w'), (1, 0, 'W'), (0, 1, 'w'), (1, 1, 'h' if not front else 'w'), (0, -1, 'W')):
                p[(cx + dx, cy + dy)] = c
        frames.append(Spr(p))
    return frames


def wax_shatter(n=5):
    frames = []
    rnd = random.Random(9)
    pieces = [(rnd.uniform(-1, 1), rnd.uniform(-1.4, -0.2)) for _ in range(8)]
    for i in range(n):
        p = {}
        for (vx, vy) in pieces:
            x = int(round(vx * 3 * (i + 1))); y = int(round(-10 + vy * 3 * (i + 1) + 0.6 * i * i))
            if y <= 0: p[(x, y)] = 'X' if i < 2 else 'W' if i < 4 else 'w'
        frames.append(Spr(p))
    return frames


def build():
    sheets = {
        "FxWaxGlob": [("Fly", wax_glob(), [0.08] * 4)],
        "FxEmberPatch": [("Loop", ember_patch(), [0.09] * 6)],
        "FxEmber": [("Fly", ember_spark(), [0.06] * 4)],
        "FxCandleBolt": [("Fly", candle_bolt(), [0.06] * 4)],
        "FxLanternOrb": [("Fly", lantern_orb(), [0.08] * 4)],
        "FxAshCloud": [("Puff", ash_cloud(), [0.07] * 5)],
        "FxWaxShockwave": [("Ring", shockwave_ring(), [0.06] * 4)],
        "FxWaxPlate": [("Loop", wax_plate_orbit(), [0.08] * 6)],
        "FxWaxShatter": [("Play", wax_shatter(), [0.05] * 5)],
    }
    g, idl, fd = wax_puddle()
    life = g + idl * 9 + fd
    sheets["FxWaxPuddle"] = [("Grow", g, [0.05] * len(g)), ("Idle", idl, [0.3] * len(idl)), ("Fade", fd, [0.12] * len(fd)),
                             ("Life", life, [0.05] * len(g) + [0.3] * (len(idl) * 9) + [0.12] * len(fd))]
    for name, anims in sheets.items():
        allf = [f for a in anims for f in a[1]]
        x0 = min(f.bbox()[0] for f in allf); x1 = max(f.bbox()[2] for f in allf)
        y0 = min(f.bbox()[1] for f in allf); y1 = max(f.bbox()[3] for f in allf)
        hw = max(-x0, x1) + 2
        h = -y0 + 2
        img, man = pack(name, anims, 2 * hw, h + max(0, y1) + 2, (hw, h), OUT)
        preview(img, man, os.path.join(OUT, name + "_preview.png"), scale=8)
        print("built", name, 2 * hw, h + 2)


if __name__ == "__main__":
    build()
