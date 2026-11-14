"""New props for the chaos biome concepts, painted with paint.py to sit beside the game's own.

Each maker returns (sprite, glow or None, footprint (half-width, half-height), shadow). The footprint is the solid
part at the base only, the way the game's own props have a low capsule collider: the hero walks behind a cap's stem
and the cap hides him.
"""
import math
import random

from PIL import Image

import paint as P
from paint import Mat, Sculpt, ramp, mix


def _done(sc, foot, shadow_w, shadow_h=None):
    im, em = sc.render()
    bb = im.getbbox()
    if bb:
        im = im.crop(bb)
        em = em.crop(bb) if em is not None else None
    return im, em, foot, P.shadow(shadow_w, shadow_h)


# ------------------------------------------------------------------ Rot Gardens
def giant_cap(h, cap, glow, stem=(190, 176, 160), seed=0, kind="parasol", gills=None, spots=True):
    """A towering cap. kind: parasol (wide, flat-topped), bell (tall dome), shelf (low, wavy). Glowing gills and
    spots; a frilled ring on the stem; a flared, rooted foot with two or three small caps round it."""
    rnd = random.Random(seed)
    n = P.Noise(seed)
    capw = {"parasol": 1.05, "bell": 0.72, "shelf": 1.25}[kind] * h
    W, Hh = int(capw + 10), int(h + 6)
    sc = Sculpt(W, Hh, seed)
    cx = W / 2
    bend = rnd.uniform(-0.12, 0.12) * h
    sw = max(2.2, h * (0.085 if kind != "bell" else 0.1))
    capy = h * {"parasol": 0.8, "bell": 0.74, "shelf": 0.62}[kind]
    stem_c = lambda y: cx + bend * math.sin(min(1, y / capy) * math.pi * 0.5) ** 2
    stem_r = lambda y: sw * (1 + 1.3 * max(0, 1 - y / (h * 0.16)) ** 2) * (1 - 0.18 * y / capy)
    fib = lambda x, y: (n.v(x * 2.6, y * 0.22, 1.0) - 0.5) * 2
    smat = Mat(stem, tex=fib, tex_amp=0.22, n=6, dark=0.32, light=1.12)
    sc.lathe(stem_c, 1, capy + 1, stem_r, 0, smat)
    # roots spreading at the foot
    rmat = Mat(mix(stem, (90, 70, 80), 0.45), n=5, dark=0.3, light=1.0, tex=fib, tex_amp=0.15)
    for side in (-1, 1):
        for k in range(rnd.randint(1, 2)):
            x0 = stem_c(2) + side * stem_r(2) * 0.6
            pts = [(x0, 3 + k), (x0 + side * (3 + k * 2), 1.5), (x0 + side * (6 + k * 3 + rnd.uniform(0, 3)), 0.6)]
            sc.line(pts, 1.1, 1, rmat)
    # the ring
    ry = capy * 0.62
    ringmat = Mat(mix(stem, (255, 250, 236), 0.2), n=5, dark=0.35, light=1.15)
    rr = stem_r(ry) + 1.6
    for x in range(int(stem_c(ry) - rr - 1), int(stem_c(ry) + rr + 2)):
        u = (x + 0.5 - stem_c(ry)) / rr
        if abs(u) <= 1:
            drop = 1.2 + (1 - abs(u)) * 0.6 + (0.9 if (x % 2) else 0)
            for yy in range(int(ry - drop), int(ry + 1.4)):
                sc._put(x, yy, math.sqrt(1 - u * u) * rr + 1.5, (u, -0.25 if yy < ry - 0.5 else 0.6, math.sqrt(1 - u * u)), ringmat, (x + 0.5, yy + 0.5))
    # gills under the cap: a dark crescent of radial ribs that glows
    rx, rcap = capw / 2, {"parasol": 0.2, "bell": 0.42, "shelf": 0.16}[kind] * h
    gc = gills or mix(cap, (30, 16, 40), 0.55)
    gmat = Mat(gc, n=5, dark=0.25, light=1.0, edge=False,
               tex=lambda x, y: 0.55 if int((math.atan2(y - capy, x - stem_c(capy)) * 10)) % 2 else -0.4, tex_amp=0.5,
               emit=(lambda x, y, t: 0.75 if int((math.atan2(y - capy, x - stem_c(capy)) * 10)) % 2 else 0.25) if glow else None)
    gtones = gmat.tones
    if glow:
        gmat.tones = [mix(t, glow, 0.25 + 0.12 * i) for i, t in enumerate(gtones)]
    capx = stem_c(capy)
    sc.disc(capx, capy, rx * 0.93, rx * 0.2 + 1, stem_r(capy) * 1.5, gmat, nrm=(0, -1, 0.4))
    # the cap: a dome whose underside is cut flat, rim turned down
    spec_spots = []
    if spots:
        for _ in range(int(capw * 0.35)):
            a = rnd.uniform(-0.95, 0.95)
            b = rnd.uniform(0.15, 0.95)
            spec_spots.append((capx + a * rx * 0.9, capy + b * rcap * 0.95, rnd.uniform(0.7, 1.9)))
    def captex(x, y):
        t = (n.fbm(x, y, 6) - 0.5) * 0.9
        # streaks running from the crown to the rim
        t += (n.v(math.atan2(y - capy + 2, x - capx) * 9, 0, 1) - 0.5) * 0.5
        return t
    def capemit(x, y, t):
        for (sx, sy, r) in spec_spots:
            if (x - sx) ** 2 + ((y - sy) * 1.3) ** 2 < r * r:
                return 0.9
        return 0
    cmat = Mat(cap, tex=captex, tex_amp=0.2, n=7, dark=0.24, light=1.2, spec=0.25)
    spotmat = Mat(mix(cap, glow or (250, 240, 220), 0.7), n=5, dark=0.6, light=1.3, edge=False,
                  emit=(lambda x, y, t: 0.85) if glow else None)
    clipcap = lambda x, y: y >= capy - (0.6 if kind != "bell" else 2.5) - 1.6 * (abs(x - capx) / rx) ** 4
    sc.ellipsoid(capx, capy, rx * 0.6, rx, rcap, rx * 0.7, cmat, clip=clipcap)
    for (sx, sy, r) in spec_spots:
        # each spot sits on the dome, a little raised
        dz = 0
        u, v = (sx - capx) / rx, (sy - capy) / rcap
        q = 1 - u * u - v * v
        if q > 0.02:
            sc.ellipsoid(sx, sy, rx * 0.6 + math.sqrt(q) * rx * 0.7 + 0.3, r, r * 0.8, 0.6, spotmat)
    # little caps at the foot
    for k in range(rnd.randint(2, 3)):
        side = rnd.choice((-1, 1))
        bx = cx + side * rnd.uniform(stem_r(1) + 1.5, stem_r(1) + 6)
        bh = rnd.uniform(3, 6)
        sm = Mat(stem, n=5, dark=0.35, light=1.1)
        sc.lathe(lambda y, bx=bx: bx, 0, bh, lambda y: 0.8, 3 + k, sm)
        sc.ellipsoid(bx, bh, 4 + k, bh * 0.42 + 0.8, bh * 0.3, 1.5, Mat(cap, n=5, dark=0.3, light=1.2,
                     emit=(lambda x, y, t: 0.35) if glow else None), clip=lambda x, y, bh=bh: y >= bh - 0.6)
    foot = (max(3, stem_r(1) + 1.0), max(3.0, stem_r(1) * 1.1))   # round foot: as deep as half its width
    return _done(sc, foot, int(stem_r(1) * 4 + 8))


def puffball(r, colour=(214, 200, 172), seed=0):
    """A fat puffball: cracked crown with spores showing through."""
    n = P.Noise(seed)
    sc = Sculpt(r * 2 + 4, r * 1.8 + 4, seed)
    cx, cy = r + 2, r * 0.82 + 1
    def tex(x, y):
        crack = abs(n.v(x * 0.9, y * 0.9, 2.2) - 0.5) < 0.05 and y > cy
        return -0.9 if crack else (n.fbm(x, y, 3) - 0.5) * 0.6
    m = Mat(colour, tex=tex, tex_amp=0.4, n=6, dark=0.3, light=1.15, spec=0.15)
    sc.ellipsoid(cx, cy, 0, r, r * 0.82, r, m)
    return _done(sc, (r * 0.85, r), int(r * 2.2))


def pod_cluster(colour=(150, 70, 130), glow=(120, 255, 210), seed=0, count=5):
    """Egg sacs: glossy, see-through skins with a glowing yolk."""
    rnd = random.Random(seed)
    sc = Sculpt(26, 18, seed)
    m = Mat(colour, n=6, dark=0.3, light=1.3, spec=0.7, emit=lambda x, y, t: 0.35 if t > 0.55 else 0.12)
    m.tones = [mix(t, glow, 0.08 * i) for i, t in enumerate(m.tones)]
    for i in range(count):
        r = rnd.uniform(2.4, 4.4)
        sc.ellipsoid(13 + rnd.uniform(-8, 8), r * 0.9 + rnd.uniform(0, 2), rnd.uniform(0, 4), r, r * 0.92, r, m)
    return _done(sc, (7, 6), 20)


def rotten_log(length, colour=(96, 70, 58), cap=(170, 90, 150), glow=None, seed=0):
    """A fallen trunk lying across the floor, cut end to the right, bracket fungi along its top."""
    rnd = random.Random(seed)
    n = P.Noise(seed)
    r = 5.5
    sc = Sculpt(length + 6, 18, seed)
    bark = lambda x, y: (n.v(x * 0.35, y * 2.2, 1.0) - 0.5) * 2 * (0.6 if (int(x * 0.5 + y) % 7) else 1.2)
    m = Mat(colour, tex=bark, tex_amp=0.32, n=6, dark=0.3, light=1.08)
    rings = Mat(mix(colour, (220, 180, 130), 0.45), n=5, dark=0.45, light=1.1,
                tex=lambda x, y: 0.5 if int(math.hypot(x - length - 1, (y - r - 1) * 0.5) * 1.6) % 2 else -0.3, tex_amp=0.6)
    sc.hcyl(2, length + 1, r + 1, r, 0, m, end=rings)
    fm = Mat(cap, n=6, dark=0.28, light=1.2, spec=0.2, emit=(lambda x, y, t: 0.45 if t > 0.6 else 0) if glow else None)
    um = Mat(mix(cap, (30, 16, 40), 0.5), n=4, dark=0.4, light=1.0, emit=(lambda x, y, t: 0.3) if glow else None)
    for i in range(rnd.randint(4, 6)):
        fx = rnd.uniform(5, length - 5)
        fy = rnd.uniform(r * 0.8, 2 * r)
        fr = rnd.uniform(2.4, 4.2)
        sc.disc(fx, fy - 0.6, fr * 0.9, fr * 0.3, 2 + r + 0.9, um, nrm=(0, -1, 0.5))
        sc.ellipsoid(fx, fy, 2 + r, fr, fr * 0.5, fr * 0.7, fm, clip=lambda x, y, fy=fy: y > fy - 0.4)
    return _done(sc, (length / 2, 6), length + 4, 7)        # a lying trunk: as deep as it is thick


def wall_roots(w, h, colour=(98, 74, 70), seed=0, tips=None, moss=None):
    """Roots and hyphae hanging down the back wall from its top, in a curtain; tips may glow."""
    rnd = random.Random(seed)
    n = P.Noise(seed)
    sc = Sculpt(w, h + 2, seed)
    m = Mat(colour, n=5, dark=0.34, light=1.12, tex=lambda x, y: (n.v(x, y * 2, 2) - 0.5), tex_amp=0.3)
    tm = Mat(tips, n=4, dark=0.7, light=1.3, edge=False, emit=lambda x, y, t: 0.9) if tips else m
    for i in range(int(w / 1.6)):
        x = rnd.uniform(1, w - 1)
        L = h * rnd.uniform(0.25, 1.0) ** 0.7
        pts = [(x, h)]
        xx = x
        for k in range(1, 7):
            xx += rnd.uniform(-1.2, 1.2)
            pts.append((xx, h - L * k / 6))
        sc.line(pts, rnd.uniform(0.7, 1.5), rnd.uniform(0, 2), m)
        if tips and rnd.random() < 0.3:
            sc.ellipsoid(pts[-1][0], pts[-1][1], 4, 0.9, 1.1, 0.8, tm)
    if moss:
        mm = Mat(moss, n=5, dark=0.35, light=1.15, tex=lambda x, y: (n.v(x * 2, y * 2, 1.5) - 0.5), tex_amp=0.5)
        for i in range(int(w / 3)):
            sc.ellipsoid(rnd.uniform(0, w), h - rnd.uniform(0, 3), 5, rnd.uniform(1.5, 3.5), rnd.uniform(1.2, 2.4), 1.5, mm)
    im, em = sc.render()
    return im, em


# ------------------------------------------------------------------ decals and specks (no collision)
def pins(colour=(170, 90, 150), glow=None, seed=0, count=6, spread=7):
    """A clump of little mushrooms for the floor: stems two to four pixels, caps three wide, shaded."""
    rnd = random.Random(seed)
    w = spread * 2 + 5
    im = Image.new("RGBA", (w, 11), (0, 0, 0, 0))
    em = Image.new("RGBA", (w, 11), (0, 0, 0, 0)) if glow else None
    px = im.load()
    tones = ramp(colour, n=4, dark=0.4, light=1.2)
    stem = ramp((184, 170, 160), n=3, dark=0.55, light=1.1)
    spots = sorted(((max(2, min(w - 3, int(spread + 2 + rnd.gauss(0, spread / 2.4)))), 10 - int(abs(rnd.gauss(0, 1.2))))
                    for _ in range(count)), key=lambda p: p[1])
    for (x, b) in spots:
        hgt = rnd.randint(2, 4)
        for k in range(hgt):
            px[x, b - k] = stem[2 if k else 0] + (255,)
        t = b - hgt
        px[x - 1, t] = tones[1] + (255,)
        px[x, t] = tones[2] + (255,)
        px[x + 1, t] = tones[1] + (255,)
        px[x, t - 1] = tones[3] + (255,)
        px[x - 1, t + 1] = tones[0] + (255,)
        px[x + 1, t + 1] = tones[0] + (255,)
        if em is not None:
            em.load()[x, t + 1] = mix(tones[3], glow, 0.7) + (200,)
    return im, em


def mycelium(w, h, colour=(200, 196, 182), seed=0, glow=None):
    """White threads webbing across the floor."""
    rnd = random.Random(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    em = Image.new("RGBA", (w, h), (0, 0, 0, 0)) if glow else None
    px = im.load()
    for i in range(int(w * h / 60)):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        a = rnd.uniform(0, math.tau)
        for k in range(rnd.randint(5, 16)):
            a += rnd.uniform(-0.6, 0.6)
            x += math.cos(a); y += math.sin(a) * 0.6
            if 0 <= x < w and 0 <= y < h:
                al = int(110 + 80 * rnd.random())
                px[int(x), int(y)] = colour + (al,)
                if em is not None and rnd.random() < 0.06:
                    em.load()[int(x), int(y)] = glow + (200,)
    return im, em


def motes(w, h, colour, count, seed=0, size=1):
    """Floating specks (spores, embers, dust): an emissive layer."""
    rnd = random.Random(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for i in range(count):
        x, y = rnd.randrange(w), rnd.randrange(h)
        a = rnd.randint(120, 255)
        px[x, y] = colour + (a,)
        if size > 1 and rnd.random() < 0.3 and x + 1 < w:
            px[x + 1, y] = colour + (a // 2,)
    return im


def ink_cap(h, colour=(190, 184, 204), glow=(150, 200, 255), seed=0):
    """A clump of slender, shaggy ink caps: tall closed bells whose frayed rims drip glowing ink."""
    rnd = random.Random(seed)
    n = P.Noise(seed)
    W = int(h * 0.75 + 8)
    sc = Sculpt(W, h + 4, seed)
    sm = Mat((160, 150, 158), n=5, dark=0.35, light=1.1, tex=lambda x, y: (n.v(x * 3, y * 0.3, 1) - 0.5) * 2, tex_amp=0.2)
    shag = lambda x, y: -0.7 if (int(x * 1.4 + n.v(x, y, 2) * 3) + int(y * 0.8)) % 3 == 0 else (n.v(x * 2, y, 2) - 0.5) * 0.8
    cm = Mat(colour, tex=shag, tex_amp=0.4, n=6, dark=0.28, light=1.12)
    inkm = Mat((40, 36, 70), n=4, dark=0.6, light=1.4, edge=False, emit=lambda x, y, t: 0.85)
    inkm.tones = [mix(t, glow, 0.35 + 0.15 * i) for i, t in enumerate(inkm.tones)]
    stems = [(W / 2, h, 0)] + [(W / 2 + s * rnd.uniform(h * 0.2, h * 0.28), h * rnd.uniform(0.5, 0.7), 1 + k)
                                 for k, s in enumerate((-1, 1)[:rnd.randint(1, 2)])]
    for (cx, hh, z) in stems:
        capy0 = hh * 0.45
        sc.lathe(lambda y, cx=cx: cx, 0, capy0 + 2, lambda y: 1.3 + 1.0 * max(0, 1 - y / 4) ** 2, z, sm)
        rad = lambda y, hh=hh, capy0=capy0: (hh * 0.13 + 0.8) * math.sin(min(1, (y - capy0 + 1.5) / (hh - capy0)) * math.pi * 0.62 + 0.55) if y > capy0 - 1.5 else 0
        sc.lathe(lambda y, cx=cx: cx, capy0 - 1.5, hh, rad, z + 0.5, cm)
        rr = rad(capy0 - 1)
        for x in range(int(cx - rr), int(cx + rr) + 1):
            if rnd.random() < 0.5:
                for k in range(rnd.randint(1, 3)):
                    sc.pixel(x, capy0 - 2 - k, z + 5, inkm)
    return _done(sc, (3.5, 3.5), 12)


def lantern(colour=(255, 190, 110), seed=0, chain=6):
    """A small iron lantern hanging on a short chain, its flame glowing."""
    sc = Sculpt(9, 12 + chain, seed)
    iron = Mat((70, 64, 66), n=5, dark=0.35, light=1.3, spec=0.4)
    glass = Mat(colour, n=4, dark=0.7, light=1.3, edge=False, emit=lambda x, y, t: 0.95)
    for y in range(11, 11 + chain):
        sc.pixel(4.5, y, 2, iron, nrm=(0.3 if y % 2 else -0.3, 0, 1))
    sc.box(2, 2, 7, 9, 0, 0, glass)
    sc.box(1, 9, 8, 10, 1, 1, iron)
    sc.box(2, 1, 7, 2, 0, 1, iron)
    for x in (2, 6):
        sc.box(x, 2, x + 1, 9, 0, 1.5, iron)
    im, em = sc.render()
    return im, em


def kelp(h, colour=(56, 100, 70), seed=0):
    """Strands of kelp standing up out of shallow water, swaying."""
    rnd = random.Random(seed)
    sc = Sculpt(14, h + 2, seed)
    m = Mat(colour, n=6, dark=0.3, light=1.2, spec=0.2)
    for i in range(rnd.randint(3, 5)):
        x0 = 7 + rnd.uniform(-4, 4)
        L = h * rnd.uniform(0.5, 1)
        ph = rnd.uniform(0, 6)
        pts = [(x0 + math.sin(ph + k * 0.9) * 1.6 * k / 6, L * k / 6) for k in range(7)]
        sc.line(pts, rnd.uniform(0.9, 1.4), i * 0.3, m)
        for k in range(1, 6, 2):
            px_, py_ = pts[k]
            sc.ellipsoid(px_ + 1.3, py_, 3, 1.4, 0.7, 0.6, m)
    return _done(sc, (2.5, 3), 9)


def barnacles(w=12, seed=0, colour=(170, 166, 150)):
    """A crust of barnacles and a mussel or two, for a column's foot or a rock."""
    rnd = random.Random(seed)
    sc = Sculpt(w + 2, 7, seed)
    m = Mat(colour, n=5, dark=0.35, light=1.2, spec=0.3)
    mus = Mat((40, 44, 70), n=4, dark=0.4, light=1.5, spec=0.8)
    for i in range(int(w * 0.9)):
        x, y = rnd.uniform(1, w), rnd.uniform(1, 4)
        r = rnd.uniform(0.8, 1.6)
        sc.ellipsoid(x, y, rnd.uniform(0, 2), r, r * 0.9, r, m)
        sc.pixel(x, y + r * 0.3, 4, Mat((30, 26, 30), n=2, edge=False))
    for i in range(2):
        sc.ellipsoid(rnd.uniform(2, w - 2), rnd.uniform(1, 3), 3, 1.8, 0.9, 0.8, mus)
    im, em = sc.render()
    return im


def starfish(colour=(200, 110, 70), seed=0):
    sc = Sculpt(9, 7, seed)
    m = Mat(colour, n=5, dark=0.4, light=1.2, tex=lambda x, y: 0.4 if (int(x) + int(y)) % 2 else -0.2, tex_amp=0.3)
    cx, cy = 4.5, 3.5
    for k in range(5):
        a = k / 5 * math.tau + 0.3
        sc.line([(cx, cy), (cx + math.cos(a) * 3.6, cy + math.sin(a) * 2.6)], 0.9, 0, m)
    im, em = sc.render()
    return im


def shell(colour=(226, 206, 180), seed=0):
    sc = Sculpt(6, 5, seed)
    m = Mat(colour, n=5, dark=0.45, light=1.2, spec=0.4,
            tex=lambda x, y: 0.5 if int(math.atan2(y - 0.5, x - 3) * 4) % 2 else -0.3, tex_amp=0.4)
    sc.ellipsoid(3, 1.5, 0, 2.6, 2.4, 1.4, m, clip=lambda x, y: y > 0)
    im, em = sc.render()
    return im


def skull(colour=(220, 208, 182), seed=0):
    sc = Sculpt(7, 7, seed)
    m = Mat(colour, n=5, dark=0.4, light=1.18)
    sc.ellipsoid(3.5, 3.6, 0, 2.8, 2.6, 2.5, m)
    sc.box(2, 0.5, 5, 2, 0, 1, m)
    hole = Mat((30, 22, 26), n=2, edge=False, flat=0.0)
    for x in (2, 4):
        sc.pixel(x + 0.5, 3, 5, hole)
    sc.pixel(3.5, 1.6, 5, hole)
    im, em = sc.render()
    return im


def grave(w=14, soil=(84, 66, 56), seed=0):
    """A fresh grave: a long mound of turned soil."""
    n = P.Noise(seed)
    sc = Sculpt(w + 2, 8, seed)
    m = Mat(soil, n=6, dark=0.32, light=1.2, tex=lambda x, y: (n.v(x * 2, y * 2, 1.4) - 0.5) * 2, tex_amp=0.35)
    sc.ellipsoid(w / 2 + 1, 2.2, 0, w / 2, 3.2, 3, m, clip=lambda x, y: y > 0)
    return _done(sc, (w / 2, 5), w + 2, 5)


def anvil(seed=0):
    sc = Sculpt(20, 14, seed)
    iron = Mat((76, 72, 78), n=6, dark=0.3, light=1.35, spec=0.6)
    wood = Mat((96, 66, 46), n=5, dark=0.35, light=1.1, tex=lambda x, y: (int(y) % 3 == 0) * -0.5, tex_amp=0.6)
    sc.box(6, 0, 14, 6, 2, 0, wood)
    sc.box(7, 6, 13, 8, 0, 1, iron)
    sc.box(3, 8, 17, 11, 2, 1.5, iron)
    sc.ellipsoid(17, 9.5, 2, 2.6, 1.5, 1.2, iron)
    return _done(sc, (6, 4), 18, 5)


def crucible(glow=(255, 170, 60), seed=0):
    """An iron pot of molten metal on three feet."""
    sc = Sculpt(18, 14, seed)
    iron = Mat((70, 62, 64), n=6, dark=0.3, light=1.3, spec=0.5)
    melt = Mat(glow, n=4, dark=0.8, light=1.3, edge=False, emit=lambda x, y, t: 1.0,
               tex=lambda x, y: 0.4 if (int(x * 0.7 + y * 2) % 4 == 0) else 0, tex_amp=0.5)
    for x in (4, 9, 14):
        sc.box(x - 1, 0, x + 1, 3, 0, 0.5, iron)
    sc.lathe(lambda y: 9, 2, 11, lambda y: 7.2 - (11 - y) * 0.25 - max(0, 4 - y) * 0.6, 0, iron)
    sc.disc(9, 11, 6.2, 2.0, 9, melt)
    return _done(sc, (7, 6), 16, 5)


def slag(r=5, glow=(255, 120, 40), seed=0):
    """A lump of cooling slag, its cracks still glowing."""
    n = P.Noise(seed)
    sc = Sculpt(r * 2 + 3, r * 1.4 + 3, seed)
    crack = lambda x, y: abs(n.v(x, y, 1.8) - 0.5) < 0.07
    m = Mat((50, 42, 44), n=5, dark=0.35, light=1.3, tex=lambda x, y: (n.fbm(x, y, 2) - 0.5), tex_amp=0.5,
            emit=lambda x, y, t: 0.95 if crack(x, y) else 0)
    hot = Mat(glow, n=4, dark=0.8, light=1.3, edge=False)
    sc.ellipsoid(r + 1.5, r * 0.6, 0, r, r * 0.65, r, m)
    im, em = sc.render()
    # the cracks themselves are hot
    if em is not None:
        ep = em.load()
        ip = im.load()
        for y in range(im.height):
            for x in range(im.width):
                if ep[x, y][3]:
                    ip[x, y] = glow + (255,)
                    ep[x, y] = glow + (230,)
    bb = im.getbbox()
    im, em = im.crop(bb), (em.crop(bb) if em else None)
    return im, em, (r * 0.85, r * 0.9), P.shadow(r * 2 + 2)


def chain(h, seed=0):
    """A chain hanging from a beam."""
    sc = Sculpt(5, h, seed)
    iron = Mat((84, 78, 82), n=5, dark=0.3, light=1.35, spec=0.6)
    for y in range(0, h - 1, 3):
        if (y // 3) % 2:
            sc.ellipsoid(2.5, y + 1.5, 0, 1.0, 1.6, 0.8, iron)
        else:
            sc.ellipsoid(2.5, y + 1.5, 0, 1.6, 1.4, 1.2, iron)
    sc.box(1, 0, 4, 2, 0, 2, iron)
    im, em = sc.render()
    return im


def book_stack(seed=0, count=None):
    rnd = random.Random(seed)
    count = count or rnd.randint(3, 6)
    sc = Sculpt(14, count * 2.4 + 4, seed)
    y = 0
    cols = [(120, 40, 40), (52, 70, 110), (60, 90, 56), (130, 96, 50), (90, 56, 90), (150, 130, 96)]
    page = Mat((214, 202, 170), n=4, dark=0.5, light=1.1)
    for i in range(count):
        w = rnd.uniform(7, 11)
        x0 = 7 - w / 2 + rnd.uniform(-1.2, 1.2)
        th = rnd.choice((2, 2, 3))
        m = Mat(rnd.choice(cols), n=5, dark=0.35, light=1.25)
        sc.box(x0, y, x0 + w, y + th, 1, i * 0.1, m, mat_top=m)
        sc.box(x0 + w - 1.2, y + 0.5, x0 + w - 0.2, y + th - 0.5, 0, i * 0.1 + 1.2, page)
        y += th
    return _done(sc, (5, 4), 14, 4)


def papers(seed=0, count=5, colour=(214, 204, 176)):
    """Loose pages and a playing card or two on the floor."""
    rnd = random.Random(seed)
    im = Image.new("RGBA", (22, 12), (0, 0, 0, 0))
    px = im.load()
    for i in range(count):
        x0, y0 = rnd.randint(0, 15), rnd.randint(0, 7)
        card = rnd.random() < 0.3
        w, h = (3, 4) if card else (5, 3)
        base = (230, 224, 210) if card else colour
        for y in range(h):
            for x in range(w):
                c = base if (x + y) % 5 else mix(base, (0, 0, 0), 0.1)
                if not card and y == 1 and 0 < x < w - 1:
                    c = mix(base, (60, 50, 50), 0.35)
                px[x0 + x, y0 + y] = c + (255,)
        if card:
            px[x0 + 1, y0 + 1] = (rnd.choice(((170, 30, 40), (30, 30, 40))) + (255,))
    return im


def fog_layer(w, h, n, colour=(200, 190, 220), alpha=70, scale=10):
    """Low ground mist: soft noise, thickest at the bottom of each band."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for y in range(h):
        for x in range(w):
            v = n.fbm(x, y * 1.8, scale)
            if v > 0.5:
                px[x, y] = colour + (int(alpha * min(1, (v - 0.5) * 4)),)
    return im


def bone_pile(w=16, seed=0, colour=(214, 202, 176)):
    """A heap of long bones and skulls."""
    rnd = random.Random(seed)
    sc = Sculpt(w + 4, w * 0.75 + 4, seed)
    m = Mat(colour, n=6, dark=0.32, light=1.15)
    dk = Mat((40, 30, 30), n=2, edge=False, flat=0.0)
    hgt = w * 0.55
    for i in range(int(w * 1.6)):
        t = i / (w * 1.6)
        y = rnd.uniform(0.5, hgt * (1 - t * 0.6))
        half = (w / 2) * (1 - y / (hgt + 2)) ** 0.8
        x = w / 2 + 2 + rnd.uniform(-half, half)
        a = rnd.uniform(-0.6, 0.6)
        L = rnd.uniform(3, 6)
        x0, y0, x1, y1 = x - math.cos(a) * L / 2, y - math.sin(a) * L / 2, x + math.cos(a) * L / 2, y + math.sin(a) * L / 2
        sc.line([(x0, y0), (x1, y1)], 0.75, i * 0.15, m, taper=False)
        for (ex, ey) in ((x0, y0), (x1, y1)):
            sc.ellipsoid(ex, ey, i * 0.15 + 0.4, 1.0, 1.0, 0.9, m)
    for k in range(rnd.randint(1, 3)):
        sx, sy = w / 2 + 2 + rnd.uniform(-w / 4, w / 4), rnd.uniform(1.5, hgt * 0.7)
        sc.ellipsoid(sx, sy + 1.2, 30 + k, 2.3, 2.1, 2.0, m)
        sc.pixel(sx - 0.8, sy + 1, 33 + k, dk)
        sc.pixel(sx + 0.9, sy + 1, 33 + k, dk)
    return _done(sc, (w * 0.42, w * 0.38), w + 2, 5)


def furnace(seed=0, glow=(255, 150, 60)):
    """A brick furnace: an arched mouth full of fire, a chimney going up the wall."""
    n = P.Noise(seed)
    sc = Sculpt(30, 40, seed)
    brick = lambda x, y: -0.55 if (int(y) % 3 == 0 or (int(x + (int(y) // 3) * 2) % 5 == 0)) else (n.v(x, y, 2) - 0.5) * 0.6
    bm = Mat((120, 70, 52), tex=brick, tex_amp=0.5, n=6, dark=0.3, light=1.1)
    soot = Mat((56, 46, 44), tex=brick, tex_amp=0.4, n=5, dark=0.35, light=1.1)
    fire = Mat(glow, n=5, dark=0.7, light=1.35, edge=False, emit=lambda x, y, t: 1.0,
               tex=lambda x, y: (n.v(x * 1.5, y * 0.8, 2) - 0.5) * 2 + (y - 5) * -0.12, tex_amp=0.4)
    sc.box(2, 0, 28, 18, 3, 0, bm, mat_top=soot)
    sc.box(10, 18, 20, 39, 1, -1, soot)
    for y in range(1, 11):
        half = 6 if y < 7 else 6 * math.sqrt(max(0, 1 - ((y - 7) / 4.2) ** 2))
        for x in range(int(15 - half), int(15 + half) + 1):
            sc._put(x, y, 3, (0, 0, 1), fire, (x + 0.5, y + 0.5))
    return _done(sc, (13, 7), 30, 7)
