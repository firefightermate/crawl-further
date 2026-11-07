"""Umbrael effect sheets and the gold idol, drawn with the renderer in umbrael_v2_rigs.py. Each sheet's origin (the
pixel the game puts on the spawn point) is listed in ORIGINS and in art/out_umbrael/TIMING.md; projectiles are drawn
facing right round the cell centre. Coordinates below are pixels from the origin, y up negative."""
import math, os, random
from umbrael_v2_rigs import (Rig, Xf, lerp, J, MASK_LEG, twinkle, arc_smear, wisps, shards, remains, IMP_MASK, BUILT)
from umbrael_v2_t2 import hourglass_body, glass_wing
from umbrael_v2_t3 import sundered, crown, hollow_king, pendulum_blade, glass_moth_tiny, sabre

ORIGINS = {}


def done(r):
    return r.resolve(floor=False, cast=False, contour=False)


def fx(name, cell, origin, anims, outdir, scale=6):
    """Pack an effect sheet. The cell grows to hold every frame (never clips); a projectile whose origin is the cell centre
    stays centred."""
    allf = [f for a in anims for f in a[1] if f.px]
    x0 = min(f.bbox()[0] for f in allf); y0 = min(f.bbox()[1] for f in allf)
    x1 = max(f.bbox()[2] for f in allf); y1 = max(f.bbox()[3] for f in allf)
    cw, ch = cell
    ox, oy = origin
    centred = abs(ox - cw // 2) <= 1 and abs(oy - ch // 2) <= 1 and ox > 0
    if centred:
        hw = max(-x0, x1 + 1) + 1; hh = max(-y0, y1 + 1) + 1
        cw, ch = max(cw, 2 * hw + 1), max(ch, 2 * hh + 1)
        ox, oy = cw // 2, ch // 2
    else:
        ox = max(ox, -x0 + 1) if ox > 0 else ox
        oy = max(oy, -y0 + 1)
        cw = max(cw, ox + x1 + 2); ch = max(ch, oy + y1 + 2)
    cell, origin = (cw, ch), (ox, oy)
    img, man = J.pack(name, anims, cell[0], cell[1], origin, outdir)
    J.preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    BUILT[name] = {"cell": cell, "feet": origin, "anims": [(a, len(f), list(d)) for a, f, d in anims]}
    ORIGINS[name] = origin
    print("built %-22s cell %dx%d  %s" % (name, cell[0], cell[1], ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))


def ring(r, cx, cy, rx, ry, mat, tone, z, n=48, skip=None):
    for i in range(n):
        a = i / n * math.tau
        if skip and skip(a): continue
        r.dot(cx + rx * math.cos(a), cy + ry * math.sin(a), mat, tone, z)


def dither_disc(r, cx, cy, rx, ry, density, mat="dark", seed=1, z=0.0, edge=None, swirl=0.0):
    """A cloud of darkness: checker-dithered so the floor shows through, denser at the centre; edge = lilac rim tone."""
    rnd = random.Random(seed)
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            u, v = (x - cx) / max(0.5, rx), (y - cy) / max(0.5, ry)
            d = u * u + v * v
            wob = 0.08 * math.sin(math.atan2(v, u) * 5 + swirl)
            if d > 1.0 + wob: continue
            keep = density * (1.25 - 0.6 * d)
            if (x + y) % 2 == 0 or rnd.random() < keep - 0.5:
                if rnd.random() < keep:
                    t = 0 if d < 0.35 else 1 if d < 0.75 else 2
                    if edge is not None and d > 0.82 + wob and rnd.random() < 0.35:
                        r.dot(x, y, "lilac", edge, z + 0.01)
                    else:
                        r.dot(x, y, mat, t, z)


def life28(frame_fn, n_idle=4):
    """The 28-frame Life layout every darkness cloud uses (spread 3, idle 22 from n_idle poses, fade 3)."""
    out = [frame_fn("spread", k) for k in range(3)]
    idle = [frame_fn("idle", k) for k in range(n_idle)]
    out += [idle[i % n_idle] for i in range(22)]
    out += [frame_fn("fade", k) for k in range(3)]
    return out


def life_d(seconds):
    idle = max(0.4, seconds - 0.6) / 22.0
    return [0.08] * 3 + [idle] * 22 + [0.12] * 3


# ------------------------------------------------------------------ echoes
def fx_echo(out):
    # EchoSmear (origin = the monster's feet): a smear of shadow rising off the floor and thinning
    sm = []
    for k in range(4):
        r = Rig()
        for i in range(5 - k):
            r.ell(-4 + i * 2.0, -2.0 - i * 1.6 - k * 1.5, 2.6 - k * 0.4, 1.8 - k * 0.3, "shade", 0.0 + i * 0.01, bias=0.1 - 0.1 * k)
        for i in range(3):
            r.dot(-5 + i * 4, -8 - k * 2 - i, "lilac", 3 if k < 2 else 2, 1.0)
        sm.append(done(r))
    fx("FxUmbEchoSmear", (24, 22), (12, 20), [("Play", sm, [0.08, 0.1, 0.12, 0.14])], out)
    # EchoBite (origin = the bite's centre): shadow jaws snapping shut
    bt = []
    for k, gap in enumerate((7, 5, 2, 0, 0)):
        r = Rig()
        for s in (-1, 1):
            y0 = s * gap
            r.poly([(-6, y0), (6, y0 - s * 1.0), (5, y0 + s * 2.4), (-5, y0 + s * 3.0)], "shade", 1.0, bias=0.1 if s < 0 else -0.2)
            for i in range(4):
                r.dot(-4 + i * 3, y0 - s * 0.6 + (s * 1 if i % 2 else 0), "lilac", 3 if k < 4 else 2, 1.1)
        if k == 3: twinkle(r, 0, 0, 2, mat="lilac")
        bt.append(done(r))
    fx("FxUmbEchoBite", (18, 20), (9, 10), [("Play", bt, [0.06, 0.06, 0.05, 0.08, 0.12])], out)
    # EchoMark (origin = the floor centre): where an echo will land. Play: a lilac ring closing in; Quick: a claw outline
    # already forming (the Shade Imp in darkness); Sparkle: glitter on an echo that hits whole (inside glitter)
    pl = []
    for k in range(5):
        r = Rig()
        rr = 8.0 - k * 1.2
        ring(r, 0, -1, rr, rr * 0.45, "lilac", 3 if k < 3 else 4, 0.0, n=36, skip=lambda a: int(a * 6) % 3 == 2)
        r.dot(0, -1, "lilac", 4, 0.1)
        pl.append(done(r))
    qk = []
    for k in range(3):
        r = Rig()
        for f in range(3):
            a0 = -130 + f * 22
            arc_smear(r, 0, -6, 6.0 - f, a0, a0 + 70 + k * 15, mat="lilac", width=1, z=1.0, tones=(1, 2, 3))
        qk.append(done(r))
    sp = []
    for k in range(4):
        r = Rig()
        rnd = random.Random(9 + k)
        for i in range(8):
            a = rnd.uniform(0, math.tau); d = rnd.uniform(2, 7 + k)
            r.dot(d * math.cos(a), -5 + d * 0.7 * math.sin(a) - k, "white" if i % 2 else "cyanl", 4 if i % 3 else 3, 1.0)
        if k < 2: twinkle(r, rnd.uniform(-3, 3), -6 - k, 1)
        sp.append(done(r))
    fx("FxUmbEchoMark", (24, 22), (12, 16),
       [("Play", pl, [0.08, 0.08, 0.1, 0.1, 0.12]), ("Quick", qk, [0.08, 0.1, 0.12]), ("Sparkle", sp, [0.06, 0.08, 0.1, 0.12])], out)


def fx_swap(out):
    fr = []
    for k in range(5):
        r = Rig()
        h = [6, 16, 20, 14, 6][k]
        w = [2, 4, 5, 4, 2][k]
        r.poly([(-w, 0), (0, -h), (w, 0), (0, -2)], "pale", 0.0, bias=0.3)
        r.line(0, -h, 0, 0, "white", 0.1, tone=4)
        if k in (1, 2): twinkle(r, 0, -h - 1, 1)
        shards(r, 0, -h * 0.6, k % 3, n=4 + k, mats=("pale", "glass", "lilac"), seed=k + 3, spread=8)
        fr.append(done(r))
    fx("FxSwapFlash", (24, 26), (12, 24), [("Play", fr, [0.05, 0.05, 0.06, 0.08, 0.1])], out)


def fx_shadowpuff(out):
    """The puff a decoy steps out of: a dense burst of shadow smoke with a lilac core, thinning as it rises."""
    fr = []
    for k in range(5):
        r = Rig()
        rr = [3.0, 5.0, 6.5, 7.0, 7.0][k]
        rnd = random.Random(20)
        for i in range(9):
            a = i / 9 * math.tau + rnd.uniform(-0.3, 0.3)
            d = rr * (0.4 + 0.6 * rnd.random())
            x, y = d * math.cos(a), -6 + d * 0.6 * math.sin(a) - k * 1.2
            sz = max(0.8, (2.6 - 0.45 * k) * (0.8 + 0.4 * rnd.random()))
            if k >= 3 and i % 2: continue
            r.ell(x, y, sz, sz * 0.8, "shade", 0.0 + i * 0.01, bias=0.2 - 0.12 * k)
        if k < 3:
            r.ell(0, -6 - k, 2.0 - 0.5 * k, 1.6 - 0.4 * k, "lilac", 1.0, flat=3)
            twinkle(r, 0, -7 - k * 2, 2, mat="pale")
        fr.append(done(r))
    fx("FxShadowPuff", (22, 22), (11, 20), [("Play", fr, [0.05, 0.06, 0.08, 0.1, 0.12])], out)


def fx_decoyburst(out):
    """A decoy shattering: a flash, then glass shards flying out low and wide and falling."""
    fr = []
    for k in range(5):
        r = Rig()
        if k == 0:
            r.poly([(0, -12), (4.5, -6.5), (0, -1), (-4.5, -6.5)], "pale", 0.0, bias=0.35)
            twinkle(r, 0, -7, 1)
        else:
            if k == 1:
                r.ell(0, -6, 5, 4, "white", 0.5, flat=3); twinkle(r, 0, -6, 1)
            rnd = random.Random(30)
            for i in range(18):
                a = rnd.uniform(-math.pi, 0.2)
                d = (3 + rnd.random() * 5) * k * 0.75
                x, y = d * math.cos(a) * 1.5, -5 + d * math.sin(a) * 0.7 + (k - 1) ** 2 * 0.5
                L = 1.6 + rnd.random() * 1.4
                m = "pale" if i % 3 else ("silver" if i % 2 else "glass")
                r.line(x, y, x + L * math.cos(a + 1.2), y + L * math.sin(a + 1.2), m, 1.0 + i * 0.01, tone=4 if k < 3 else 2)
                if k < 3 and i % 4 == 0: r.dot(x, y, "white", 4, 1.2)
        fr.append(done(r))
    fx("FxDecoyBurst", (34, 18), (17, 14), [("Play", fr, [0.05, 0.06, 0.07, 0.08, 0.1])], out)


# ------------------------------------------------------------------ projectiles (facing right, round the cell centre)
def shard_frame(k, mat="glass", hot=False, ln=5.0):
    r = Rig()
    r.poly([(-ln, 0), (0, -1.6), (ln, 0), (0, 1.6)], mat, 1.0, bias=0.3 if not hot else 0.6, normal=(-0.2, -0.6 + k * 0.1, 1.0))
    r.line(-ln + 1, 0, ln - 1, 0, "white", 1.1, tone=4 if (k % 2 == 0 or hot) else 3)
    for i in range(3):
        r.dot(-ln - 1 - i * 1.5, (i % 2) * 0.6, "white" if hot else mat, max(1, 4 - i), 0.5)
    if hot:
        twinkle(r, ln - 1, -1, 2)
    return done(r)


def fx_projectiles(out):
    fx("FxMirrorShard", (17, 9), (8, 4), [("Fly", [shard_frame(k) for k in range(4)], [0.05] * 4),
                                          ("Hot", [shard_frame(k, mat="pale", hot=True) for k in range(4)], [0.05] * 4)], out)
    fx("FxUmbRingShard", (15, 7), (7, 3), [("Fly", [shard_frame(k, mat="pale", ln=4.0) for k in range(4)], [0.05] * 4)], out)
    # glass nail (Nailshade fan, Bristleback shake)
    def nail(k, mat="glass", black=False):
        r = Rig()
        r.line(-5, 0, 4, 0, "void" if black else mat, 1.0, tone=2 if black else 3)
        r.line(-5, -1 if k % 2 else 1, 3, 0, mat, 0.9, tone=1) if not black else None
        r.dot(5, 0, "white" if not black else "lilac", 4, 1.1)
        r.dot(-6, 0, "silver", 3, 1.0)
        for i in range(2):
            r.dot(-7 - i * 2, 0, "lilac" if black else mat, 2, 0.5)
        return done(r)
    fx("FxUmbNail", (17, 5), (8, 2), [("Fly", [nail(k) for k in range(4)], [0.05] * 4)], out)
    fx("FxUmbPin", (19, 5), (9, 2), [("Fly", [nail(k, black=True) for k in range(4)], [0.05] * 4)], out)
    # Pinned (origin = his feet): the black pin driven into the floor through his shadow, a lilac ring pulsing
    pn = []
    for k in range(6):
        r = Rig()
        ring(r, 0, -1, 7 - k * 0.6, 2.6 - k * 0.2, "lilac", 4 if k < 2 else 3, 0.0, n=30, skip=lambda a: int(a * 5 + k) % 3 == 0)
        h = [10, 6, 5, 5, 5, 5][k]
        r.line(1, -1 - h, 0, -1, "void", 1.0, tone=2); r.dot(1, -1 - h, "lilac", 4, 1.1)
        if k == 1: twinkle(r, 0, -2, 2)
        pn.append(done(r))
    fx("FxUmbPinned", (20, 16), (10, 13), [("Play", pn, [0.05, 0.06, 0.2, 0.2, 0.2, 0.12])], out)

    def bolt(k):
        r = Rig()
        r.ell(0, 0, 3.4, 2.2, "lilac", 1.0, flat=3)
        r.ell(0.6, -0.4, 1.6, 1.0, "white", 1.1, flat=4)
        r.poly([(-1, -3), (1, 0), (-1, 3)], "silver", 1.2, bias=0.3)
        for i in range(4):
            r.dot(-4 - i * 1.6, ((k + i) % 3 - 1) * 0.8, "lilac", max(1, 4 - i), 0.5)
        return done(r)
    fx("FxReflectBolt", (19, 9), (9, 4), [("Fly", [bolt(k) for k in range(4)], [0.05] * 4)], out)

    def scale(k, eye=False):
        r = Rig()
        r.ell(0, 0, 2.6, 1.6, "lwing" if eye else "glass", 1.0, bias=0.2, ang=k * 30)
        if eye:
            r.dot(0, 0, "sand", 4, 1.1); r.dot(1, 0, "void", 0, 1.12)
        else:
            r.dot(-0.6, -0.6, "white", 4, 1.1)
        r.dot(-4, 0, "lilac" if eye else "glass", 2, 0.5)
        return done(r)
    fx("FxUmbMothScale", (13, 7), (6, 3), [("Fly", [scale(k) for k in range(4)], [0.05] * 4)], out)
    fx("FxUmbArgusScale", (13, 7), (6, 3), [("Fly", [scale(k, True) for k in range(4)], [0.05] * 4)], out)

    def sand(k, big=False):
        r = Rig()
        rr = 2.6 if big else 1.8
        r.ell(0, 0, rr, rr * 0.9, "sand", 1.0, bias=0.25, ang=k * 40)
        r.dot(-0.5, -0.8, "sandl", 4, 1.1)
        rnd = random.Random(k)
        for i in range(5 if big else 3):
            r.dot(-3 - i * 1.5, rnd.uniform(-1.4, 1.4), "sandl", 3 if i < 2 else 2, 0.5)
        return done(r)
    fx("FxUmbSandShard", (15, 7), (7, 3), [("Fly", [sand(k) for k in range(4)], [0.05] * 4)], out)
    fx("FxUmbSandBall", (19, 9), (9, 4), [("Fly", [sand(k, True) for k in range(4)], [0.05] * 4)], out)

    def feather(k, split=False):
        r = Rig()
        r.poly([(-5, 0), (-1, -1.8), (4, -0.6), (5, 0), (4, 0.8), (-1, 1.6)], "redg" if k % 2 else "blug", 1.0, bias=0.3)
        r.line(-5, 0, 5, 0, "lead", 1.1, tone=1)
        r.dot(5, 0, "white", 4, 1.2)
        if split: twinkle(r, 4, -1, 1)
        for i in range(2):
            r.dot(-6 - i * 1.6, 0, "glass", 2, 0.5)
        return done(r)
    fx("FxUmbFeather", (17, 7), (8, 3), [("Fly", [feather(k) for k in range(4)], [0.05] * 4),
                                         ("Split", [feather(k, True) for k in range(3)], [0.04, 0.04, 0.05])], out)

    def quill(k):
        r = Rig()
        a = math.radians(k * 90)
        r.line(-3 * math.cos(a), -3 * math.sin(a) - 6, 3 * math.cos(a), 3 * math.sin(a) - 6, "lwing", 1.0, tone=3)
        r.dot(3 * math.cos(a), 3 * math.sin(a) - 6, "white", 4, 1.1)
        r.ell(0, 0, 1.4, 0.6, "dark", 0.0, flat=2)
        return done(r)
    fx("FxUmbQuill", (9, 13), (4, 10), [("Fly", [quill(k) for k in range(4)], [0.06] * 4)], out)


# ------------------------------------------------------------------ darkness
def fx_darkness(out):
    def cloud(rx, ry, mat_edge, seed):
        def f(ph, k):
            r = Rig()
            if ph == "spread":
                dither_disc(r, 0, -ry, rx * (0.45 + 0.27 * k), ry * (0.45 + 0.27 * k), 0.9, seed=seed + k, edge=2)
            elif ph == "idle":
                dither_disc(r, 0, -ry, rx, ry, 0.95, seed=seed + 10 + k, edge=mat_edge, swirl=k * 1.5)
                for i in range(3):
                    a = k * 0.8 + i * 2.1
                    r.dot(rx * 0.6 * math.cos(a), -ry + ry * 0.6 * math.sin(a), "lilac", 2, 0.5)
            else:
                dither_disc(r, 0, -ry, rx * (1.0 + 0.06 * k), ry * (1.0 + 0.06 * k), 0.7 - 0.2 * k, seed=seed + 20 + k)
            return done(r)
        return f
    # FxDarkness: the Gloom Lurker's breath, r 26 (a 52 x 22 cloud on the floor), 4 s
    fx("FxDarkness", (58, 26), (29, 24), [("Life", life28(cloud(26, 11, 2, 1)), life_d(4.0))], out)
    # FxUmbSmokeStep: the Shade Imp's puff at both ends of Smoke Step, r 16, 3 s
    fx("FxUmbSmokeStep", (38, 18), (19, 16), [("Life", life28(cloud(16, 7, 2, 40)), life_d(3.0))], out)
    # FxUmbGloamPool: the Gloamcoil's ink pool, r 13 (flat on the floor), 3.6 s
    fx("FxUmbGloamPool", (32, 14), (16, 12), [("Life", life28(cloud(13, 5, 3, 60)), life_d(3.6))], out)
    # FxUmbBlackout: Lights Out, r 90, 3.5 s
    fx("FxUmbBlackout", (186, 80), (93, 78), [("Life", life28(cloud(90, 38, 2, 80), n_idle=3), life_d(3.5))], out, scale=2)
    # FxUmbDuskEdge: the creeping edge of darkness a Gloamcoil lies in (one loop per radius)
    anims = []
    for R in (16, 20, 24, 28, 32):
        fr = []
        for k in range(4):
            r = Rig()
            ry = R * 0.42
            for i in range(60):
                a = i / 60 * math.tau + k * 0.05
                wob = 1.0 + 0.06 * math.sin(a * 7 + k)
                x, y = R * wob * math.cos(a), -ry + ry * wob * math.sin(a)
                if (i + k) % 3 != 0:
                    r.dot(x, y, "lilac", 2 if (i + k) % 4 else 3, 1.0)
                    r.dot(x * 0.92, -ry + (y + ry) * 0.92, "dark", 1, 0.9)
            fr.append(done(r))
        anims.append(("R%d" % R, fr, [0.12] * 4))
    fx("FxUmbDuskEdge", (70, 30), (35, 28), anims, out, scale=3)
    # FxUmbLurkEyes: what shows of a hidden Gloom Lurker: a faint outline of its eyes (origin = its feet)
    ey = []
    for k in range(4):
        r = Rig()
        for i, (x, y) in enumerate(((3, -6), (5, -6), (4, -5), (6, -5), (3, -4), (5, -4))):
            if k == 3 and i < 2: continue
            r.dot(x, y, "lilac", 3 if (i + k) % 3 else 4, 1.0)
        ey.append(done(r))
    fx("FxUmbLurkEyes", (16, 10), (8, 8), [("Loop", ey, [0.3, 0.2, 0.3, 0.12])], out)
    # FxUmbInkUnder: the Undertow riding under an ally: ink spreads, two eyes blink in it, it drains
    def ink(k, w, eyes, fade=0):
        r = Rig()
        dither_disc(r, 0, -2.5, w, 3.0, 1.0 - 0.3 * fade, mat="ink", seed=70 + k, edge=3 if not fade else None)
        if eyes:
            for x in (-2, 2):
                r.dot(x, -3, "bone", 4 if k % 4 != 3 else 1, 1.0); r.dot(x + 1, -3, "lilac", 3, 1.0)
        return done(r)
    fx("FxUmbInkUnder", (30, 10), (15, 8), [("Spread", [ink(k, 5 + 4 * k, False) for k in range(3)], [0.06, 0.06, 0.08]),
                                           ("Loop", [ink(k, 13, True) for k in range(4)], [0.3, 0.25, 0.3, 0.1]),
                                           ("Fade", [ink(k, 13 - 3 * k, False, fade=1) for k in range(3)], [0.08, 0.08, 0.1])], out)


# ------------------------------------------------------------------ swipes (origin = the strike line at the swing's root)
def swipe(rr, a0, a1, mat, width, k, n_frames, tones=(2, 3, 4), z=1.0, extra=None, cy=0.0):
    r = Rig()
    t = (k + 1) / n_frames
    end = lerp(a0, a1, min(1.0, t * 1.4))
    start = lerp(a0, a1, max(0.0, t * 1.4 - 0.7))
    if k < n_frames - 1:
        arc_smear(r, 0, cy, rr, start, end, mat=mat, width=width, z=z, tones=tones)
    else:
        arc_smear(r, 0, cy, rr, lerp(a0, a1, 0.7), a1, mat=mat, width=1, z=z, tones=(1, 1, 2))
    if extra: extra(r, k)
    return done(r)


PALE_CUT_DUR = [0.08, 0.05, 0.08, 0.1, 0.1, 0.1]


# ------------------------------------------------------------------ the Undertow's jaws (and their shadow echo)
VENOM_DUR = [0.04, 0.04, 0.07, 0.08, 0.1]
VENOM_POSE = [(34, 0), (15, 0), (0, 1), (0, 3), (5, 3)]   # (how far each jaw is open, deg; how far shoved on, px)


def venom_jaws(k, echo=False):
    """Upper and lower jaw hinged at (-3, 0), tips at x = 12, closing on the hitbox centre. Teeth alternate so they interlock
    when shut. echo: the same jaws as a flat shadow (black-violet fill, lilac rim and teeth)."""
    r = Rig()
    ang, dx = VENOM_POSE[k]
    hx, L = -3.0 + dx, 15.0
    body, teeth = ("dark", "lilac") if echo else ("ink", "bone")
    fade = k == 4

    def P(s, u, v):
        # u along the jaw, v away from the mouth; s = -1 upper jaw, +1 lower
        a = math.radians(s * ang)
        x, y = u, s * v
        return (hx + x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a))

    bend = lambda u: 1.8 * (u / L) ** 2                       # the jaws hook in toward the tips
    thick = lambda u: 0.6 + 3.4 * (1 - u / L) ** 0.7
    for s in (-1, 1):
        us = (0, 3, 6, 9, 12, L)
        inner = [P(s, u, 0.5 - bend(u)) for u in us]
        outer = [P(s, u, 0.5 - bend(u) + thick(u)) for u in reversed(us[:-1])]
        if not fade:
            r.poly(inner + outer, body, 1.0 + (0.1 if s > 0 else 0), bias=(0.25 if s < 0 else -0.2) if not echo else 0.0,
                   curve=0.0 if echo else 0.3, flat=(2 if s < 0 else 1) if echo else None)
            r.polyline(inner[:-1], "void" if not echo else "dark", 1.2, tone=0)                                  # the gum line
        # the rim: lit along the upper jaw's back, a lilac edge round the shadow
        rim = [P(s, L, 0.5 - bend(L))] + outer
        r.polyline(rim, "lilac" if echo else body, 1.3, tone=(1 if fade else (3 if s < 0 else 2) if echo else (3 if s < 0 else 1)))
        # fangs: upper three, lower two in between, so they interlock on the snap
        for u in ((3.0, 7.0, 11.0) if s < 0 else (5.0, 9.0)):
            if fade and u > 8: continue
            v0 = 0.5 - bend(u)
            b0, b1, tip = P(s, u - 0.9, v0 + 0.3), P(s, u + 0.9, v0 + 0.3), P(s, u + 0.3, v0 - 2.2)
            r.poly([b0, b1, tip], teeth, 1.6, bias=0.35 if not echo else 0.0, flat=(4 if s < 0 else 3) if echo else None)
            if fade: r.dot(*tip, teeth, 2, 1.7)
    if echo:
        # one eye of light at the hinge, so the shadow reads as a head and not a bar
        r.dot(hx + 1.5, -2.5 if ang < 10 else -3.5, "lilac", 4, 1.8)
    else:
        r.dot(hx + 1.5, -2.5 if ang < 10 else -3.5, "lilac", 3, 1.8)
    if k == 1:
        for i in range(3): r.dot(hx - 2 - i * 1.5, -6 + i * 6, "lilac" if echo else "pale", 2, 0.5)       # the drive
    if k == 2:
        twinkle(r, 13 + dx, 0, 2, mat="lilac" if echo else "white")                                            # the snap
        for s in (-1, 1): r.line(14 + dx, s * 2, 16 + dx, s * 4, "lilac" if echo else "white", 2.0, tone=3)
    if k == 3 and not echo:
        for i, (x, y) in enumerate(((5, 3), (8, 4), (6, 5))): r.dot(x + dx, y, "glass", 4 - i % 2, 2.0)          # venom
    if k == 3 and echo:
        for i, (x, y) in enumerate(((5, 3), (8, 4))): r.dot(x + dx, y, "lilac", 3, 2.0)
    return done(r)


def fx_swipes(out):
    def claws(r, k):
        if k == 1:
            for f in range(3):
                arc_smear(r, 0, 0, 9 - f * 2, -60, 40, mat="silver", width=1, z=2.0, tones=(1, 2, 3))
    fx("FxUmbImpClaw", (26, 24), (9, 12), [("Play", [swipe(10, -80, 50, "lilac", 2, k, 4, extra=claws) for k in range(4)],
                                           [0.04, 0.05, 0.06, 0.08])], out)
    fx("FxUmbTwinCut", (30, 28), (10, 14), [("Play", [swipe(12, -100, 50, "silver", 3, k, 4) for k in range(4)], [0.04, 0.05, 0.06, 0.08])], out)
    fx("FxUmbNailRake", (30, 26), (10, 13), [("Play", [swipe(11, -90, 50, "glass", 3, k, 4, extra=lambda r, k: shards(r, 8, -2, k, n=3, seed=k))
                                                       for k in range(4)], [0.04, 0.05, 0.06, 0.08])], out)

    def eclipse(r, k):
        if k in (1, 2):
            arc_smear(r, 0, 0, 13, -130, 30, mat="white", width=1, z=2.0, tones=(2, 3, 4))
    fx("FxUmbKingCleave", (44, 44), (16, 26), [("Play", [swipe(16, -150, 50, "lilac", 4, k, 5, extra=eclipse) for k in range(5)],
                                               [0.04, 0.05, 0.06, 0.07, 0.09])], out)
    fx("FxUmbWidowFang", (24, 26), (8, 14), [("Play", [swipe(9, -110, 40, "silver", 2, k, 4) for k in range(4)], [0.04, 0.05, 0.06, 0.08])], out)

    def scissor(k):
        r = Rig()
        g = [8, 5, 1, 0, 0][k]
        for s in (-1, 1):
            arc_smear(r, -2, s * g, 12, -30 * s - 10 * s, 0, mat="white" if s < 0 else "silver", width=2, z=1.0)
        if k == 2: twinkle(r, 10, 0, 1)
        return done(r)
    fx("FxUmbScissor", (30, 24), (10, 12), [("Play", [scissor(k) for k in range(5)], [0.04, 0.04, 0.05, 0.06, 0.08])], out)

    # The Undertow's bite (origin = the slot's spawn point; the jaws close on (6, 0), the hitbox centre). Play: open wide (0),
    # driving shut (1), SNAP (2 = HIT, teeth interlocked), follow-through (3: shoved on, venom), letting go (4).
    # Echo: the same five frames as a shadow of the same jaws (lilac and black), so the god's echo lands on the bite itself.
    fx("FxUmbVenomBite", (20, 18), (6, 9), [("Play", [venom_jaws(k) for k in range(5)], VENOM_DUR),
                                            ("Echo", [venom_jaws(k, echo=True) for k in range(5)], VENOM_DUR)], out)

    def bite(k):
        r = Rig()
        rnd = random.Random(k)
        for i in range(12):
            x, y = rnd.uniform(-2, 12) + k * 2, rnd.uniform(-8, 6)
            glass_moth_tiny(r, x, y, i + k, 1.0, mat="glass" if i % 2 else "pale")
        if k == 1: twinkle(r, 12, 0, 1)
        return done(r)
    fx("FxUmbSwarmBite", (30, 22), (8, 11), [("Play", [bite(k) for k in range(5)], [0.04, 0.05, 0.06, 0.07, 0.09])], out)


# ------------------------------------------------------------------ the Mirror Witch's standing mirror
def pane_frame(rise=1.0, flash=0, crack=0, fall=0):
    r = Rig()
    h = 18.0 * rise
    w = 7.0
    if crack < 3:
        r.poly([(-w, -1), (w, -1), (w, -h), (-w, -h)], "silver", 0.0, normal=(-0.2, -0.2, 1.0))
        r.poly([(-w + 1.2, -2.2), (w - 1.2, -2.2), (w - 1.2, -h + 1.2), (-w + 1.2, -h + 1.2)], "glass", 0.05, bias=0.25 + 0.2 * flash,
               normal=(-0.3, -0.3, 1.0))
        for i in range(int(h) - 3):
            if i % 5 < 2: r.dot(-w + 2 + (i % 5), -3 - i, "white", 4, 0.1)
        r.dot(0, -h - 1, "lilac", 4, 0.15)
        r.line(-w - 1, 0, w + 1, 0, "silver", 0.2, tone=2)
        if flash:
            twinkle(r, -1, -h * 0.6, 1)
            for i in range(4):
                r.dot(w + 1 + i, -h * 0.5 + i * 0.5, "lilac", 4, 0.3)
        if crack:
            r.polyline([(-3, -h + 2), (0, -h * 0.6), (-2, -h * 0.4), (2, -4)], "void", 0.15, tone=1)
            if crack > 1: r.polyline([(3, -h + 3), (1, -h * 0.5), (4, -5)], "void", 0.15, tone=1)
    else:
        shards(r, 0, -9, fall, n=14, mats=("glass", "silver", "white"), seed=3, spread=9, fall=2.0)
    return done(r)


def fx_pane(out):
    fx("FxUmbMirrorPane", (22, 24), (11, 22),
       [("Rise", [pane_frame(0.3), pane_frame(0.7), pane_frame(1.0, flash=1)], [0.06, 0.06, 0.1]),
        ("Idle", [pane_frame(1.0), pane_frame(1.0), pane_frame(1.0), pane_frame(1.0, flash=1)], [0.3, 0.3, 0.3, 0.1]),
        ("Flash", [pane_frame(1.0, flash=1), pane_frame(1.0, flash=1, crack=1), pane_frame(1.0)], [0.05, 0.06, 0.08]),
        ("Shatter", [pane_frame(1.0, crack=1), pane_frame(1.0, crack=2), pane_frame(1.0, crack=3, fall=0),
                     pane_frame(1.0, crack=3, fall=1), pane_frame(1.0, crack=3, fall=2)], [0.05, 0.05, 0.06, 0.08, 0.1])], out)


# ------------------------------------------------------------------ glitter, rewind, crown
def fx_glitter(out):
    fr = []
    for k in range(12):
        r = Rig()
        g = min(1.0, (k + 1) / 3.0) * (1.0 if k < 9 else (12 - k) / 3.0)
        rnd = random.Random(5)
        for i in range(30):
            a = rnd.uniform(0, math.tau); d = rnd.uniform(1, 10) * g
            x, y = d * math.cos(a + k * 0.15), -6 + d * 0.6 * math.sin(a + k * 0.15)
            if (i + k) % 4 == 0: continue
            r.dot(x, y, "white" if i % 5 == 0 else "cyanl" if i % 2 else "lilac", 4 if (i + k) % 3 == 0 else 3, 1.0)
        if k % 4 == 1: twinkle(r, rnd.uniform(-5, 5), -7, 2)
        fr.append(done(r))
    fx("FxUmbGlitter", (26, 16), (13, 13), [("Life", fr, [0.08, 0.08, 0.08] + [0.3] * 6 + [0.12] * 3)], out)


def fx_rewind(out):
    # Mark (10 frames over 2.5 s): a ghost of the hourglass in sand on the floor, its sand running out
    mk = []
    for k in range(10):
        r = Rig()
        hourglass_body(r, 0, -9, 0.0, 1.0 - k / 9.0, k / 9.0, 0.0, "shut", stream=True)
        out_r = Rig()
        for (x, y), v in list(r.b.items()):
            v = list(v); v[1] = "sandl" if v[1] in ("sand", "brass") else "sand"
            if (x + y + k) % 2 == 0: out_r.b[(x, y)] = v
        out_r.thin, out_r.zof, out_r.hand, out_r._part = r.thin, r.zof, r.hand, r._part
        ring(out_r, 0, 0, 7, 2, "sandl", 3 if k % 2 else 2, -1.0)
        mk.append(done(out_r))
    sn = []
    for k in range(5):
        r = Rig()
        ring(r, 0, -8, 3 + k * 2.4, 3 + k * 2.4, "sandl", 4 if k < 2 else 3, 1.0, n=32, skip=lambda a: int(a * 5) % 2)
        if k < 2: twinkle(r, 0, -8, 1, mat="sandl")
        sn.append(done(r))
    fx("FxUmbRewind", (26, 26), (13, 22), [("Mark", mk, [0.25] * 10), ("Snap", sn, [0.04, 0.05, 0.06, 0.07, 0.08])], out)


def fx_crown(out):
    fl = []
    for k in range(4):
        r = Rig()
        crown(r, 0, 0, 1.0, tilt=k * 90)
        r.dot(-6, 0, "lilac", 3, 0.5); r.dot(-8, 1, "lilac", 2, 0.5)
        fl.append(done(r))
    fx("FxUmbCrown", (21, 15), (10, 7), [("Fly", fl, [0.05] * 4)], out)
    # CrownShade (origin = the crown on the floor): Rise, Idle (loop), Swing (a cleave), Fade. The crown lies at its feet.
    def shade(k, phase, swing=None):
        base = hollow_king(hand=(5.0, -18.0) if swing is None else swing[0], sword=66 if swing is None else swing[1], crowned=False,
                           bob=[0, -0.3, -0.5, -0.3][k % 4] if phase == "idle" else 0.0, lean=0.0 if swing is None else swing[2],
                           cape=0.0 if swing is None else abs(swing[2]) / 10.0)
        r = Rig()
        for (x, y), c in base.px.items():
            t = base.tones[(x, y)][1]
            if phase == "rise" and y < -6 - k * 13: continue
            if phase == "fade" and (x * 3 + y + k) % (4 - min(3, k)) != 0: continue
            edge = any((x + dx, y + dy) not in base.px for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if edge:
                r.dot(x, y, "lilac", 3 if t >= 2 else 2, 0.0)
            elif (x + y) % 2 == 0 or t >= 3:
                r.dot(x, y, "shade" if t >= 2 else "void", 2 if t >= 3 else 1, 0.0)
        crown(r, 0, -1.0, 1.0)
        if swing is not None and swing[3]:
            arc_smear(r, *swing[3], mat="lilac", width=3, z=2.0)
        if phase == "rise": wisps(r, 0, -4, k % 3, n=5, spread=7, seed=k, z=0.5)
        return done(r)
    # the wind-up over the head (0-1), the swing (2) and its follow-through to the floor (3), the recovery (4)
    swings = [((-1.0, -25.0), -160, -14, None), ((-2.0, -26.0), -170, -18, None),
              ((10.0, -17.0), -10, 12, (2.0, -21.0, 17.0, -160.0, -10.0)), ((10.0, -7.0), 60, 16, (2.0, -21.0, 17.0, -70.0, 45.0)),
              ((6.0, -11.0), 80, 6, None)]
    fx("FxUmbCrownShade", (60, 48), (22, 46),
       [("Rise", [shade(k, "rise") for k in range(4)], [0.08, 0.08, 0.08, 0.1]),
        ("Idle", [shade(k, "idle") for k in range(4)], [0.16, 0.14, 0.16, 0.14]),
        ("Swing", [shade(0, "swing", s) for s in swings], [0.08, 0.06, 0.05, 0.1, 0.12]),
        ("Fade", [shade(k, "fade") for k in range(3)], [0.08, 0.1, 0.12])], out, scale=4)


# ------------------------------------------------------------------ the Sundered's pale half, cracks and threads of light
def fx_pale(out):
    """The Sundered's pale half, a real fighter in play (SunderedTorn drives it). Origin = its feet. Idle (4): breathing,
    sabres swaying, the seam flickering. Drift (6): gliding after the dark half. Cut (6): its own strike, an overhead
    double cut a beat after the dark half's scissor (1 = the slash, the hit effect FxUmbPaleCut spawns then). Rush (4):
    Rejoin, thrusting through the hero on a streak of light."""
    def motes(k, n=3, x=-4.0, y=-14.0, spread=4.0):
        rnd = random.Random(31 + k)
        return lambda r: [r.dot(x + rnd.uniform(-spread, spread * 0.5), y - rnd.uniform(0, 8) - k, "white" if i % 2 else "pale",
                                4 - i % 2, 6.0) for i in range(n)]
    bob = [0, -0.5, -0.8, -0.5]
    idle = [sundered(pale=True, bob=bob[i], hand=(7.0, -8.0 + bob[i]), hand2=(4.0, -6.0 + bob[i] * 0.5), ang1=-30 + [0, -5, -8, -4][i],
                     ang2=30 + [0, 4, 7, 3][i], crack=1 + i % 2, extra=motes(i, 2)) for i in range(4)]
    drift = []
    for i in range(6):
        ph = i / 6 * math.tau
        drift.append(sundered(pale=True, lean=8, bob=-0.5 * abs(math.sin(ph)), hand=(7.0, -9.0), hand2=(2.0, -7.0), ang1=165, ang2=155,
                              feet=((-3.0 * math.cos(ph), -max(0, 1.6 * math.sin(ph))), (3.0 * math.cos(ph), -max(0, -1.6 * math.sin(ph)))),
                              crack=1 + i % 2, extra=motes(i, 3, x=-7.0, y=-6.0, spread=3.0)))
    cut = [sundered(pale=True, lean=-10, hand=(2.0, -17.0), hand2=(-1.0, -15.0), ang1=-120, ang2=-140, face="snarl", crack=2),
           sundered(pale=True, lean=10, dx=1.0, hand=(9.0, -12.0), hand2=(8.0, -9.0), ang1=-20, ang2=-5, face="snarl", crack=2, glow=2,
                    smear=[(2, -12, 12, -120, -10), (1, -10, 10, -140, -20)]),
           sundered(pale=True, lean=14, dx=2.0, hand=(10.0, -6.0), hand2=(9.0, -4.0), ang1=25, ang2=40, face="snarl", crack=2,
                    feet=((-3.0, 0.0), (5.0, 0.0))),
           sundered(pale=True, lean=12, dx=2.0, hand=(10.0, -6.0), hand2=(9.0, -4.0), ang1=30, ang2=45, crack=2, feet=((-3.0, 0.0), (5.0, 0.0))),
           sundered(pale=True, lean=5, dx=1.0, hand=(8.0, -8.0), hand2=(5.0, -6.0), ang1=0, ang2=30, crack=1),
           sundered(pale=True, hand=(7.0, -8.0), hand2=(4.0, -6.0), ang1=-30, ang2=30, crack=1)]

    def streak(k):
        def f(r):
            for i, y in enumerate((-17, -13, -9, -5)):
                ln = 10 + ((i + k) % 3) * 4
                for x in range(-ln, -2):
                    if (x + k + i) % 4 != 0: r.dot(x - 2, y, "white" if x > -ln / 2 else "pale", 4 if x > -6 else 3, 6.0)
            motes(k, 4, x=-14.0, y=-6.0, spread=5.0)(r)
        return f
    rush = [sundered(pale=True, lean=22, dx=1.0, hand=(12.0, -11.0), hand2=(11.0, -9.0), ang1=-4 + k, ang2=6 - k, face="snarl", crack=2,
                     glow=k % 2 + 1, feet=((-5.0, -1.0 - k % 2), (3.0, -2.0 + k % 2)), extra=streak(k)) for k in range(4)]
    fx("FxUmbPaleHalf", (52, 36), (26, 34), [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Rush", rush, [0.05] * 4),
                                             ("Drift", drift, [0.09] * 6), ("Cut", cut, PALE_CUT_DUR)], out, scale=4)

    # PaleCut: the pale half's own strike (origin = where it spawns, ahead of the pale half's chest): two arcs cutting down
    def pale_cut(k):
        r = Rig()
        seg = [(-160, -90), (-120, -10), (-50, 35), (0, 40)][k]
        for j, (mat, R) in enumerate((("white", 11), ("pale", 8))):
            if k < 3:
                arc_smear(r, -2, 0, R, seg[0] + j * 15, seg[1] + j * 10, mat=mat, width=2, z=1.0 + j * 0.1)
            else:
                arc_smear(r, -2, 0, R, seg[0], seg[1], mat=mat, width=1, z=1.0, tones=(1, 1, 2))
        if k == 1: twinkle(r, 9, -1, 1)
        return done(r)
    fx("FxUmbPaleCut", (28, 26), (12, 13), [("Play", [pale_cut(k) for k in range(4)], [0.04, 0.05, 0.06, 0.08])], out)
    # Crack / Thread: a 32 px horizontal strip the code stretches and turns between two points (origin = its left end)
    def strip(k, mats, n=32):
        r = Rig()
        rnd = random.Random(k)
        for x in range(n):
            y = 0 if mats[0] != "white" else (1 if rnd.random() < 0.2 else 0)
            r.dot(x, y, mats[(x + k) % len(mats)], 4 if (x + k) % 5 == 0 else 3, 1.0)
        return done(r)
    fx("FxUmbCrack", (33, 3), (0, 1), [("Line", [strip(k, ("white", "white", "lilac")) for k in range(3)], [0.06, 0.06, 0.08])], out)
    fx("FxUmbLightThread", (33, 3), (0, 1), [("Line", [strip(k, ("cyanl", "white", "cyanl", "lilac")) for k in range(3)],
                                             [0.06, 0.06, 0.1])], out)

    def cut(k):
        r = Rig()
        arc_smear(r, 0, 4, 9, -150 + k * 10, -30 + k * 10, mat="white", width=2, z=1.0)
        if k == 0: twinkle(r, 0, -4, 1)
        return done(r)
    fx("FxUmbRejoinCut", (24, 16), (12, 10), [("Play", [cut(k) for k in range(4)], [0.04, 0.05, 0.06, 0.08])], out)


# ------------------------------------------------------------------ Bristleback: caltrops, stuck shots
def fx_bristle(out):
    cal = []
    for k in range(12):
        r = Rig()
        if k < 2:
            r.line(0, -2 - (1 - k) * 3, 0, -1, "lwing", 1.0, tone=3)
        else:
            for (dx, a) in ((-1, -120), (1, -60), (0, -90)):
                r.line(dx, -1, dx + 2.4 * math.cos(math.radians(a)), -1 + 2.4 * math.sin(math.radians(a)), "lwing" if k < 10 else "lead", 1.0,
                       tone=3)
            r.dot(0, -3.6, "white" if (k % 4 == 0 and k < 10) else "lwing", 4 if k < 10 else 2, 1.1)
            r.ell(0, -0.4, 2.0, 0.6, "dark", 0.0, flat=2)
        cal.append(done(r))
    fx("FxUmbCaltrop", (12, 9), (6, 7), [("Life", cal, [0.06, 0.06] + [0.4] * 8 + [0.12, 0.12])], out)
    anims = []
    for n, name in ((1, "One"), (2, "Two"), (3, "Three")):
        fr = []
        for k in range(2):
            r = Rig()
            for i in range(n):
                x = -6 + i * 5
                a = math.radians(-120 + i * 25)
                r.line(x, -12, x + 5 * math.cos(a), -12 + 5 * math.sin(a), "wood", 1.0 + i * 0.01, tone=3)
                r.dot(x + 5 * math.cos(a), -12 + 5 * math.sin(a), "silver" if (k + i) % 2 else "white", 4, 1.1)
                r.dot(x, -12, "lilac", 3, 1.05)
            fr.append(done(r))
        anims.append((name, fr, [0.3, 0.3]))
    fx("FxUmbStuckShot", (24, 20), (12, 2), anims, out)


# ------------------------------------------------------------------ The Unblinking: beam, the flash when its eye opens
def fx_eye(out):
    def beam(k, end=False):
        r = Rig()
        L = 50
        if not end:
            for x in range(L):
                w = 1 if x < 4 or x > L - 4 else 2
                for y in range(-w + 1, w):
                    r.dot(x, y, "lilac", 4 if y == 0 else 3, 1.0)
                if (x + k * 3) % 7 == 0: r.dot(x, -2, "white", 4, 1.1)
        else:
            for x in range(0, L, 2 + k):
                r.dot(x, 0, "lilac", 3 - min(2, k), 1.0)
        return done(r)
    fx("FxUmbBeam", (51, 5), (0, 2), [("Play", [beam(k) for k in range(6)], [0.06] * 6),
                                      ("End", [beam(k, True) for k in range(4)], [0.05] * 4)], out, scale=4)
    fl = []
    for k in range(6):
        r = Rig()
        R = 20 + k * 14
        ring(r, 0, -R * 0.42, R, R * 0.42, "white" if k < 3 else "lilac", 4 if k < 4 else 3, 1.0, n=96, skip=lambda a: k > 3 and int(a * 9) % 2)
        ring(r, 0, -R * 0.42, R - 2, R * 0.42 - 1, "lilac", 3, 0.9, n=96, skip=lambda a: int(a * 7) % 3 == 0)
        if k < 2:
            r.ell(0, -12, 6, 6, "white", 1.2, flat=4)
        fl.append(done(r))
    fx("FxUmbEyeFlash", (186, 80), (93, 78), [("Play", fl, [0.05, 0.05, 0.06, 0.07, 0.08, 0.1])], out, scale=2)


# ------------------------------------------------------------------ Glass Widow: the glaze web, the glaze on him
def fx_glaze(out):
    web = []
    for k in range(10):
        r = Rig()
        if k < 4:
            # the shadow of the falling web, growing
            s = 0.4 + 0.2 * k
            dither_disc(r, 0, -3, 12 * s, 4 * s, 0.9, seed=k)
            r.ell(0, -30 + k * 7, 2 + k, 1.4 + k * 0.6, "pale", 2.0, bias=0.2)
        else:
            f = 1.0 if k < 8 else 1.0 - (k - 7) * 0.3
            for i in range(8):
                a = i / 8 * math.tau
                r.line(0, -3, 12 * f * math.cos(a), -3 + 4.6 * f * math.sin(a), "pale", 1.0, tone=4 if k == 4 else 3)
            for R in (4, 8, 11):
                ring(r, 0, -3, R * f, R * 0.4 * f, "pale" if R < 11 else "glass", 3, 1.0, n=24)
            if k == 4: twinkle(r, 0, -4, 1)
        web.append(done(r))
    fx("FxUmbGlazeWeb", (30, 40), (15, 36), [("Play", web, [0.1, 0.1, 0.1, 0.1, 0.06, 0.2, 0.2, 0.2, 0.1, 0.1])], out)
    gl = []
    for k in range(4):
        r = Rig()
        for (x0, y0, x1, y1) in ((-5, -18, -2, -21), (3, -14, 6, -17), (-4, -8, -1, -11), (2, -5, 5, -8)):
            sh = (k * 2) % 6 - 2
            r.line(x0, y0 + sh, x1, y1 + sh, "white" if (x0 + k) % 3 else "cyanl", 1.0, tone=4)
        for (x, y) in ((-6, -12), (6, -20), (0, -2), (-7, -4), (7, -9)):
            r.dot(x, y, "cyanl", 3, 0.9)
        gl.append(done(r))
    fx("FxUmbGlaze", (18, 26), (9, 24), [("Loop", gl, [0.12, 0.12, 0.12, 0.12])], out)
    cr = []
    for k in range(5):
        r = Rig()
        shards(r, 0, -10, k % 3, n=8 + k, mats=("white", "cyanl", "glass"), seed=4, spread=6 + k * 2, fall=1.0)
        if k < 2: twinkle(r, 0, -10, 1)
        cr.append(done(r))
    fx("FxUmbGlazeCrack", (30, 28), (15, 24), [("Play", cr, [0.04, 0.05, 0.06, 0.07, 0.09])], out)


# ------------------------------------------------------------------ Eclipse Wyrm: corona, burst
def fx_eclipse(out):
    co = []
    for k in range(4):
        r = Rig()
        rnd = random.Random(k)
        # an inner ring of white fire, flame tongues licking out of it, a lilac outer glow
        for i in range(96):
            a = i / 96 * math.tau
            L = 2 + int(rnd.random() * 2.5 + (((i + k * 5) % 9) < 2) * 3)
            for t in range(L):
                R = 21.5 + t
                m, tone = ("white", 4) if t < 2 else ("lilac", 4 if t < 3 else 3)
                r.dot(R * math.cos(a), -15 + R * 0.5 * math.sin(a), m, tone, 1.0 + 0.001 * t)
            if (i + k) % 6 == 0:
                r.dot(27 * math.cos(a), -15 + 13.5 * math.sin(a), "lilac", 2, 0.9)
        co.append(done(r))
    fx("FxUmbCorona", (60, 34), (30, 18), [("Loop", co, [0.07] * 4)], out, scale=4)
    bu = []
    for k in range(6):
        r = Rig()
        rnd = random.Random(3)
        for i in range(16):
            a = i / 16 * math.tau
            d = 4 + k * 4
            x, y = d * math.cos(a), -8 + d * 0.5 * math.sin(a)
            r.line(x, y, x + 2 * math.cos(a), y + math.sin(a), "pale" if i % 2 else "glass", 1.0, tone=4 if k < 4 else 2)
        if k < 2: twinkle(r, 0, -8, 1)
        bu.append(done(r))
    fx("FxUmbEclipseBurst", (56, 30), (28, 18), [("Play", bu, [0.04, 0.05, 0.06, 0.07, 0.08, 0.1])], out, scale=4)


# ------------------------------------------------------------------ Argus catch, Glitterswarm glint and ghost
def fx_moths(out):
    ca = []
    for k in range(4):
        r = Rig()
        R = 4 + k * 2
        ring(r, 0, -16, R, R * 0.8, "lilac", 4 if k < 2 else 3, 1.0, n=24, skip=lambda a: int(a * 4) % 2 == 1)
        r.ell(0, -16, 2.4 - k * 0.4, 1.8 - k * 0.3, "sand", 1.1, flat=4)
        r.dot(0, -16, "void", 0, 1.2)
        ca.append(done(r))
    fx("FxUmbArgusCatch", (24, 26), (12, 24), [("Play", ca, [0.05, 0.06, 0.08, 0.1])], out)
    gl = []
    for k in range(6):
        r = Rig()
        rnd = random.Random(11)
        for i in range(6 - k // 2):
            x, y = rnd.uniform(-6, 6), rnd.uniform(-14, -4)
            if (i + k) % 3 == 0: twinkle(r, x, y, 2)
            else: glass_moth_tiny(r, x, y, i + k, 1.0)
        gl.append(done(r))
    fx("FxUmbSwarmGlint", (20, 18), (10, 16), [("Play", gl, [0.1] * 6)], out)
    gh = []
    for k in range(4):
        r = Rig()
        rnd = random.Random(21)
        for i in range(18):
            a = rnd.uniform(0, math.tau) + k * 0.4; d = rnd.uniform(2, 9)
            x, y = d * math.cos(a) * 1.3, -11 + d * 0.7 * math.sin(a)
            r.dot(x, y, "pale", 3, 1.0); r.dot(x - 1, y - (k + i) % 2, "glass", 4, 1.0)
        for i in range(4):
            r.dot(-12 - i * 2, -11 + (i % 2), "pale", 3 - i % 2, 0.5)
        gh.append(done(r))
    fx("FxUmbSwarmGhost", (34, 22), (17, 11), [("Fly", gh, [0.06] * 4)], out)


# ------------------------------------------------------------------ The Pendulum: the blade, the spin, the tick, time ring
def fx_pendulum(out):
    # (the blade that swings by itself is drawn in the Pendulum's own idle and run)
    # Spin (the heavy swing round the pivot: origin = the pivot; the blade runs a full circle)
    sp = []
    for k in range(6):
        r = Rig()
        a0 = -90 + k * 60
        arc_smear(r, 0, 0, 13, a0 - 120, a0, mat="glass", width=3, z=1.0, tones=(2, 3, 4))
        arc_smear(r, 0, 0, 10, a0 - 60, a0, mat="white", width=1, z=1.1, tones=(3, 4, 4))
        sp.append(done(r))
    fx("FxUmbPendulumSpin", (32, 32), (16, 16), [("Play", sp, [0.04, 0.04, 0.05, 0.05, 0.06, 0.07])], out)
    ti = []
    for k in range(4):
        r = Rig()
        r.line(-2, -6 - k, 2, -6 - k, "lilac", 1.0, tone=4 - min(k, 2))
        r.line(0, -8 - k, 0, -4 - k, "lilac", 1.0, tone=4 - min(k, 2))
        if k == 0: twinkle(r, 0, -6, 2)
        ti.append(done(r))
    fx("FxUmbTick", (10, 14), (5, 12), [("Play", ti, [0.06, 0.08, 0.1, 0.12])], out)
    rg = []
    for k in range(4):
        r = Rig()
        ring(r, 0, -17, 40, 17, "sandl", 3, 1.0, n=120, skip=lambda a: int(a * 19 + k) % 4 == 0)
        for i in range(12):
            a = i / 12 * math.tau + k * 0.04
            r.line(36 * math.cos(a), -17 + 15.3 * math.sin(a), 40 * math.cos(a), -17 + 17 * math.sin(a), "sandl", 1.1, tone=4)
        a = -math.pi / 2 - k * 0.5
        r.line(0, -17, 30 * math.cos(a), -17 + 12 * math.sin(a), "sandl", 1.2, tone=4)
        rg.append(done(r))
    fx("FxUmbTimeRing", (84, 38), (42, 36), [("Loop", rg, [0.12, 0.12, 0.12, 0.12])], out, scale=3)


# ------------------------------------------------------------------ Sand Wraith: the glass over him, the column
def fx_sand(out):
    anims = []
    for n in range(5):
        fr = []
        for k in range(2):
            r = Rig()
            hourglass_body(r, 0, -8, 0.0, 0.9 - n * 0.15, 0.05 + n * 0.2, 0.0, "open" if k == 0 else "wide", stream=True)
            fr.append(done(r))
        anims.append(("Fill%d" % n, fr, [0.2, 0.2]))
    fx("FxUmbSandGlass", (16, 20), (8, 1), anims, out)
    sh = []
    for k in range(4):
        r = Rig()
        dither_disc(r, 0, -2, 6 + k * 1.6, 2.4 + k * 0.5, 0.9, mat="dark", seed=k, edge=3)
        sh.append(done(r))
    fa = []
    for k in range(6):
        r = Rig()
        top = [-60, -30, -8, 0, 0, 0][k]
        w = [3, 4, 5, 9, 11, 12][k]
        if k < 3:
            r.poly([(-w, top - 22), (w, top - 22), (w - 1, top), (-w + 1, top)], "sand", 1.0, bias=0.2, curve=0.6)
            for i in range(6): r.dot(-w + 1 + i * 1.4, top - 20 + i * 3, "sandl", 4, 1.1)
        else:
            r.ell(0, -2, w, 3.0, "sand", 1.0, bias=0.2)
            r.ell(-2, -3, w * 0.5, 1.4, "sandl", 1.1, flat=3)
            rnd = random.Random(k)
            for i in range(8 - k):
                r.dot(rnd.uniform(-w, w), -3 - rnd.uniform(1, 8) * (6 - k) / 3.0, "sandl", 4, 1.2)
        fa.append(done(r))
    fx("FxUmbSandColumn", (28, 86), (14, 6), [("Shadow", sh, [0.125] * 4), ("Fall", fa, [0.04, 0.04, 0.05, 0.08, 0.1, 0.14])], out, scale=4)


# ------------------------------------------------------------------ the deity portrait and the gold idol (29 x 24)
def idol_figure(r, dx, z, mat="sand", dark="brass", arm=True):
    """The hooded figure: robe flaring to the base, sloped shoulders, a peaked hood with a dark opening."""
    r.poly([(dx - 7, -3), (dx - 5, -11), (dx - 3, -13), (dx + 3, -13), (dx + 5, -11), (dx + 7, -3)], mat, z, curve=0.9)
    r.poly([(dx - 4, -12), (dx - 3.4, -18), (dx - 1, -21.5), (dx + 0.6, -22.5), (dx + 3.4, -18), (dx + 4, -12)], mat, z + 0.1,
           curve=0.7, bias=0.05)
    r.ell(dx + 0.6, -16.4, 1.7, 2.4, dark, z + 0.15, flat=0)                       # inside the hood, darkest gold
    r.line(dx - 1, -4, dx - 2, -11, dark, z + 0.12, tone=1)                          # a fold in the robe
    if arm:
        r.tube([(dx + 4, -12), (dx + 6.5, -14.5), (dx + 7.5, -16.5)], [1.3, 1.1, 1.0], mat, z + 0.3, bias=0.15)


def idol(tier, k):
    """The gold idol in Umbrael's likeness: a faceless hooded figure in gold holding up a hand mirror of real silver glass
    with a lilac eye; its gold shadow falls the wrong way (toward the light). T2: the glass cracked and a fainter echo of
    the figure behind; T3: the glass shattered into a halo of shards round the head."""
    r = Rig()
    r.poly([(-11, 0), (11, 0), (10, -3), (-10, -3)], "sand", 0.0, bias=0.1, normal=(0, -0.6, 1))
    r.poly([(-4, -3), (-12, -6), (-12, -5), (-3, -3)], "brass", 0.05, flat=1)       # the shadow, cast toward the light
    if tier >= 2:
        echo = Rig()
        idol_figure(echo, -5.0, -1.0, mat="brass", dark="brass", arm=False)
        for (x, y), v in echo.b.items():
            if (x + y) % 2 == 0: r.put(x, y, -1.0, "brass", 0.5, r.part(False, -1.0), 1)   # the fainter echo behind
    idol_figure(r, 0.0, 0.0)
    mx, my = 8.0, -20.0
    r.tube([(7.5, -16.5), (mx, my + 3.4)], [0.6, 0.5], "sand", 0.35)
    r.ell(mx, my, 3.0, 3.6, "silver", 0.4)
    if tier < 3:
        r.ell(mx, my, 2.1, 2.7, "glass", 0.45, bias=0.2)
        r.dot(mx, my, "lilac", 3, 0.5); r.dot(mx + 1, my, "lilac", 2, 0.5)
        r.dot(mx - 1, my - 1 - (k % 2), "white", 4, 0.55)
        if tier == 2:
            r.polyline([(mx - 2, my - 2), (mx, my), (mx - 1, my + 2)], "void", 0.6, tone=1)
    else:
        r.ell(mx, my, 1.8, 2.4, "void", 0.45, flat=1)
        r.dot(mx, my, "lilac", 4, 0.5)
        for i in range(9):
            a = i / 9 * math.tau + k * 0.25
            x, y = 0.5 + 8.0 * math.cos(a), -18.0 + 4.6 * math.sin(a)
            zz = 2.0 if math.sin(a) > 0 else -2.0
            r.poly([(x - 1, y), (x, y - 1.6), (x + 1, y), (x, y + 1.6)], "glass" if i % 2 else "silver", zz, bias=0.35)
            r.dot(x, y - 1, "white", 4 if (i + k) % 3 == 0 else 3, zz + 0.1)
    if k % 4 == 1: twinkle(r, -2, -22, 2, mat="sandl")
    return done(r)


def fx_portraits(out):
    from deity_portraits import frames  # the god portrait, drawn to DeityZhekra's standard
    # the portrait fills its 29 x 24 cell edge to edge, so it is packed at that cell as it is (fx() would pad it)
    anims = [("Idle", frames("umbrael", (14, 23)), [1.4, 0.1, 0.1, 0.1])]
    img, man = J.pack("DeityUmbrael", anims, 29, 24, (14, 23), out)
    J.preview(img, man, os.path.join(out, "DeityUmbrael_preview.png"), scale=8)
    BUILT["DeityUmbrael"] = {"cell": (29, 24), "feet": (14, 23), "anims": [(a, len(f), list(d)) for a, f, d in anims]}
    ORIGINS["DeityUmbrael"] = (14, 23)
    print("built %-22s cell 29x24  Idle:4" % "DeityUmbrael")
    fx("DeityGoldIdolUmbrael", (29, 24), (14, 23),
       [("Idle", [idol(3, k) for k in range(4)], [0.3, 0.2, 0.3, 0.2]), ("T1", [idol(1, k) for k in range(2)], [0.4, 0.4]),
        ("T2", [idol(2, k) for k in range(2)], [0.4, 0.4]), ("T3", [idol(3, k) for k in range(4)], [0.3, 0.2, 0.3, 0.2])], out, scale=8)


def write_timing(out):
    lines = ["# Umbrael art: effect origins (tools/sprites/umbrael_v2_fx.py)", "",
             "Pixel in the cell that sits on the spawn point (x from the left, y from the top). Projectiles are drawn facing",
             "right round that point; ground effects stand on it. Monster sheets keep the feet at (cellW / 2, cellH - 2).", ""]
    for n in sorted(ORIGINS):
        b = BUILT[n]
        lines.append("- %s: cell %dx%d, origin (%d, %d); %s" % (n, b["cell"][0], b["cell"][1], ORIGINS[n][0], ORIGINS[n][1],
                                                                 ", ".join("%s %d" % (a, c) for a, c, d in b["anims"])))
    open(os.path.join(out, "TIMING.md"), "w").write("\n".join(lines) + "\n")


def all_fx(out):
    for f in (fx_echo, fx_swap, fx_shadowpuff, fx_decoyburst, fx_projectiles, fx_darkness, fx_swipes, fx_pane, fx_glitter,
              fx_rewind, fx_crown, fx_pale, fx_bristle, fx_eye, fx_glaze, fx_eclipse, fx_moths, fx_pendulum, fx_sand, fx_portraits):
        f(out)
    write_timing(out)


JOBS = [("UmbraelFx", all_fx)]
