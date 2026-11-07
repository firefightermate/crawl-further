"""Ysveld effect sheets, drawn with the material renderer of ysveld_v2_rigs.py. Projectiles fly to the right and are
centred on their cell (the code anchors them mid-centre); ground and overlay sheets name their origin, which the code
passes to Strike.ArtAt / Strike.Ground. Coordinates below are pixels from each sheet's origin, y up negative."""
import math, random
from ysveld_v2_rigs import Rig, Xf, lerp, lerp_pt, crystal, sparkle, arc_smear, flakes, fx, RAMPS

SPEC = ["red", "aurp", "eye", "aurg", "vglow"]


def done(r):
    return r.resolve(floor=False, cast=False, contour=False, outline=False)


def dart(r, x, y, ang, length, width, mat="ice", z=1.0, tail=None):
    """An ice dart pointing ang deg: a sharp diamond, its lit upper face and shaded lower face."""
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a); px, py = -uy, ux
    tip = (x + ux * length / 2, y + uy * length / 2); back = (x - ux * length / 2, y - uy * length / 2)
    mid = (x - ux * length * 0.1, y - uy * length * 0.1)
    up = (mid[0] - px * width / 2, mid[1] - py * width / 2); dn = (mid[0] + px * width / 2, mid[1] + py * width / 2)
    r.poly([back, up, tip], mat, z, normal=(-0.3, -0.8, 0.6), bias=0.2)
    r.poly([back, tip, dn], mat, z - 0.01, normal=(0.3, 0.6, 0.6), bias=-0.1)
    r.dot(tip[0], tip[1], "white", 4, z + 0.1)
    if tail:
        for i in range(1, tail + 1):
            r.dot(back[0] - ux * i * 1.3, back[1] - uy * i * 1.3 + (i % 2) * 0.4, "snow", max(1, 4 - i), z - 0.2)


def ring(r, cx, cy, rx, ry, mat, tone, z, n=40, gap=None, step=1):
    for i in range(0, n, step):
        a = i / n * math.tau
        if gap and gap(a): continue
        r.dot(cx + rx * math.cos(a), cy + ry * math.sin(a), mat, tone, z)


def burst(r, cx, cy, k, n=8, rad=4.0, mat="snow", seed=1, z=5.0):
    rnd = random.Random(seed)
    for i in range(n):
        a = i / n * math.tau + rnd.uniform(-0.2, 0.2)
        d = rad * (0.5 + 0.5 * k) * rnd.uniform(0.8, 1.2)
        r.dot(cx + math.cos(a) * d, cy + math.sin(a) * d * 0.7, mat, max(1, 4 - k), z)
        if k < 2: r.dot(cx + math.cos(a) * (d - 1), cy + math.sin(a) * (d - 1) * 0.7, mat, max(1, 3 - k), z - 0.01)


# ------------------------------------------------------------------ the floor: ice slabs (blizzard paths, death patches, kit ice)
def slab(v, k, melt=False):
    """A floor slab of ice, ~22 x 11, centred: an irregular plate with a lit rim, cracks and a glint. k: grow / melt stage."""
    rnd = random.Random(v * 13 + 5)
    r = Rig()
    n = 12
    pts = []
    sc = (0.4 + 0.2 * k) if not melt else (1.0 - 0.22 * k)
    sc = min(1.0, sc)
    for i in range(n):
        a = i / n * math.tau
        rr = rnd.uniform(0.82, 1.08)
        pts.append((math.cos(a) * 10.5 * rr * sc, math.sin(a) * 5.2 * rr * sc))
    r.poly(pts, "ice", 0.0, flat=2)
    r.poly([(x * 0.7 - 1.5, y * 0.6 - 0.8) for (x, y) in pts], "ice", 0.05, flat=3)
    # edges: a lit rim along the far, upper-left edge, a dark lip along the near, lower-right one
    for i in range(n):
        x0, y0 = pts[i]; x1, y1 = pts[(i + 1) % n]
        up = (y0 + y1) < 0 and (x0 + x1) < 6
        r.line(x0, y0, x1, y1, "ice", 0.1, tone=4 if up else 0 if (y0 + y1) > 0 else 1)
    # a frosted rim on the far (upper) edge and a dark lower lip
    for (x, y) in pts:
        if y < -1.0: r.dot(x * 0.92, y * 0.92, "frost", 4 if x < 0 else 3, 0.1)
    if sc > 0.7:
        for c in range(2):
            x0 = rnd.uniform(-6, 2); y0 = rnd.uniform(-2, 1)
            r.polyline([(x0, y0), (x0 + 3, y0 + 1), (x0 + 5, y0 + 0.5)], "ice", 0.2, tone=1)
        sparkle(r, rnd.uniform(-6, -2), rnd.uniform(-3, -1), 3 if not melt else 2, "white", 0.3)
    if melt:
        for i in range(k * 2):
            r.dot(rnd.uniform(-9, 9) * sc, rnd.uniform(-3, 3) * sc, "eye", 1, 0.25)
    return r.resolve(floor=False, cast=False, contour=False, selout=False, outline=False)


def fx_floe(out):
    anims = []
    for v in range(4):
        anims.append(("Form%d" % v, [slab(v, k) for k in range(4)], [0.05] * 4))
        anims.append(("Idle%d" % v, [slab(v, 3), slab(v, 3)], [0.6, 0.6]))
        anims.append(("Melt%d" % v, [slab(v, k, melt=True) for k in range(1, 5)], [0.08] * 4))
    fx("FxYsvFloe", (30, 16), (15, 8), anims, out)


def fx_gale(out):
    """A band of driven snow, ~70 x 16, centred: streaks and flakes (the blizzard gust)."""
    frames = []
    for k in range(6):
        r = Rig(); rnd = random.Random(9)
        for i in range(26):
            x = rnd.uniform(-36, 30) + k * 4.0; y = rnd.uniform(-7, 7)
            L = rnd.uniform(3, 9)
            fade = 1.0 if k < 4 else (0.6 if k == 4 else 0.3)
            if rnd.random() > fade: continue
            r.line(x, y, x + L, y - 0.6, "snow", 1.0, tone=3 if i % 3 else 4)
        for i in range(12):
            x = rnd.uniform(-36, 34) + k * 5.0; y = rnd.uniform(-8, 8)
            if k < 5: r.dot(x, y, "white", 4, 1.1)
        frames.append(done(r))
    fx("FxYsvGale", (92, 24), (46, 12), [("Blow", frames, [0.15] * 6)], out)


def fx_puff(out):
    frames = []
    for k in range(4):
        r = Rig(); burst(r, 0, -1, k, n=7, rad=3.5); frames.append(done(r))
    fx("FxYsvPuff", (16, 14), (8, 7), [("Play", frames, [0.05, 0.06, 0.07, 0.08])], out)


def fx_bind(out):
    """The third pip: ice and silk bind the hero's legs (origin = his feet)."""
    frames = []
    for k in range(7):
        r = Rig()
        h = min(8.0, 2.0 + k * 2.0) if k < 5 else 8.0 - (k - 4) * 2.5
        for i in range(-5, 6, 2):
            r.line(i, 0, i + (1 if i < 0 else -1), -h * (1.0 - abs(i) * 0.08), "ice", 1.0, tone=3 if i < 0 else 2)
        for j in range(int(h / 2)):
            r.line(-6, -1 - j * 2, 6, -2 - j * 2, "web", 1.1, tone=3)
        if k == 2: sparkle(r, 0, -h - 1, 1, "white")
        frames.append(done(r))
    fx("FxYsvBind", (28, 25), (14, 23), [("Bind", frames, [0.05, 0.05, 0.06, 0.12, 0.12, 0.1, 0.1])], out)


# ------------------------------------------------------------------ T1
def fx_glob(out):
    fr = []
    for k in range(4):
        r = Rig(); r.ell(2, 0, 2.6, 2.2, "web", 1.0, bias=0.2); r.dot(1, -1, "white", 4, 1.1)
        for i in range(3): r.dot(-1 - i * 1.6, (k + i) % 2 * 0.6, "web", 3 - i, 0.9)
        r.dot(3 + (k % 2), 1, "ice", 2, 1.05)
        fr.append(done(r))
    fx("FxYsvGlob", (20, 10), (10, 5), [("Fly", fr, [0.06] * 4)], out)


def fx_mote(out):
    fr = []
    for k in range(4):
        r = Rig(); sparkle(r, 1, 0, 1 if k % 2 == 0 else 2, "white"); r.dot(-2, 0, "snow", 2, 0.5); fr.append(done(r))
    fx("FxYsvMote", (10, 8), (5, 4), [("Fly", fr, [0.05] * 4)], out)


def gust_frame(k, sleet=False):
    r = Rig()
    for j in range(3):
        R = 8.0 - j * 2.5
        a0, a1 = -60 + k * 4, 60 - k * 4
        arc_smear(r, -4 + j * 2, 0, R, a0, a1, "white" if sleet else "snow", 2 if j == 0 else 1, z=1.0 + j)
    if sleet:
        flakes(r, [(2 + (i * 3 + k) % 7, -9 + i * 3, 4 - i % 2) for i in range(7)], z=5)
    else:
        flakes(r, [(3, -5 + k, 2), (5, 4 - k, 2)], z=5)
    return done(r)


def fx_gust(out):
    fx("FxYsvGust", (28, 26), (14, 13), [("Fly", [gust_frame(k) for k in range(4)], [0.05] * 4),
                                          ("Sleet", [gust_frame(k, True) for k in range(4)], [0.05] * 4)], out)


def icicle_fall(k, iced=False):
    """An icicle dropping from above onto a shadow on the floor (origin (15, 59) = the floor point)."""
    r = Rig()
    sh = 2.0 + k * 0.9
    r.ell(0, 0, sh * 1.4, 1.0 + sh * 0.15, "ice" if iced else "shade", 0.0, flat=1 if iced else 3)
    if iced: ring(r, 0, 0, sh * 1.4 + 1, 1.6 + sh * 0.15, "eye", 2, 0.1, n=24, step=2)
    y = -46.0 + k * 6.2
    r.poly([(-2.0, y - 8), (2.0, y - 8), (0.2, y + 3)], "ice", 1.0, normal=(-0.5, -0.4, 0.7), bias=0.2)
    r.line(-0.5, y - 7, -0.3, y + 1, "white", 1.1, tone=4)
    if k > 1:
        for i in range(1, 3): r.line(0, y - 8 - i * 3, 0, y - 10 - i * 3, "snow", 0.5, tone=3 - i)
    return done(r)


def icicle_shatter(k):
    r = Rig()
    burst(r, 0, -2, k, n=10, rad=5.0, mat="white" if k < 2 else "snow")
    for i in range(4 - k):
        a = i * 1.6 + 0.4
        dart(r, math.cos(a) * (3 + k * 2), -2 - abs(math.sin(a)) * (2 + k * 2), math.degrees(a), 4, 1.6, z=2)
    r.ell(0, 0, 6 - k, 2, "ice", 0.0, flat=2)
    return done(r)


def fx_icicle(out):
    fall = [icicle_fall(k) for k in range(8)]
    fall_ice = [icicle_fall(k, True) for k in range(8)]
    fx("FxYsvIcicle", (32, 68), (16, 60), [("Fall", fall, [0.0875] * 8), ("FallIce", fall_ice, [0.0875] * 8),
                                            ("Shatter", [icicle_shatter(k) for k in range(5)], [0.05, 0.06, 0.07, 0.08, 0.1])], out)


def fx_skidshard(out):
    fr = []
    for k in range(4):
        r = Rig(); dart(r, 1, 0, 0 + (k % 2) * 8, 7, 2.4, z=1.0); r.line(-6, 1, -3, 1, "snow", 0.5, tone=2 + k % 2)
        fr.append(done(r))
    fx("FxYsvSkidShard", (16, 8), (8, 4), [("Fly", fr, [0.05] * 4)], out)


# ------------------------------------------------------------------ T2
def fx_thread(out):
    fly = []
    for k in range(4):
        r = Rig(); r.line(-7, 0, 5, 0, "web", 1.0, tone=3); r.ell(6, 0, 1.6, 1.6, "web", 1.1, bias=0.3); r.dot(6, -1, "white", 4, 1.2)
        r.dot(-3 + k * 2, 0, "white", 4, 1.1)
        fly.append(done(r))
    bead = []
    for k in range(2):
        r = Rig(); r.ell(0, 0, 1.4, 1.4, "web", 1, bias=0.2 + k * 0.2); r.dot(-0.5, -0.5, "white", 4 - k, 1.1); bead.append(done(r))
    snap = []
    for k in range(3):
        r = Rig(); burst(r, 0, 0, k, n=6, rad=3.0, mat="web"); r.line(-3 - k, 0, -1 - k, 1 + k, "web", 1, tone=2)
        r.line(3 + k, 0, 1 + k, -1 - k, "web", 1, tone=2); snap.append(done(r))
    fx("FxYsvThread", (26, 8), (13, 4), [("Fly", fly, [0.05] * 4), ("Bead", bead, [0.12, 0.12]), ("Snap", snap, [0.06, 0.07, 0.08])], out)


def fx_strumbead(out):
    """Strum: a frost bead sliding down the silk line (Run), and the twang where she plucks it (Twang)."""
    run = []
    for k in range(2):
        r = Rig(); r.ell(0, 0, 1.7, 1.7, "eye", 1.0, flat=2); r.dot(0, 0, "white", 4, 1.1)
        r.dot(-2, 0, "eye", 3 - k, 0.9); r.dot(-3, 0, "eye", 2 - k, 0.8); run.append(done(r))
    tw = []
    for k in range(3):
        r = Rig(); ring(r, 0, 0, 2 + k * 1.5, 1.4 + k, "eye", 3 - k, 1.0, n=16, step=1 + k % 2); tw.append(done(r))
    fx("FxYsvStrumBead", (12, 10), (6, 5), [("Run", run, [0.06, 0.06]), ("Twang", tw, [0.05, 0.06, 0.08])], out)


def snare_frame(open_, iced=False, glint=False, fade=0):
    r = Rig()
    # a silk snare: a little ring of sticky threads pinned to the floor
    rx, ry = 6.0 * open_, 3.0 * open_
    r.ell(0, 0.2, rx + 0.5, ry * 0.6 + 0.5, "shade", -0.5, flat=1)            # its shadow on the floor
    if iced:
        r.ell(0, -0.5, 7.0, 3.4, "ice", 0.0, flat=2)
        ring(r, 0, -0.5, 7.0, 3.4, "ice", 1, 0.05, n=24, gap=lambda a: math.sin(a) < 0)
        ring(r, 0, -0.5, 7.0, 3.4, "ice", 4, 0.05, n=24, gap=lambda a: math.sin(a) >= 0 or math.cos(a) > 0.3)
    ring(r, 0, -0.5, rx, ry, "web", 1, 0.45, n=20, gap=lambda a: math.sin(a) < 0.2)
    ring(r, 0, -0.5, rx, ry, "web", 4 if not fade else 2, 0.5, n=20, gap=lambda a: math.sin(a) >= 0.2)
    for i in range(4):
        a = i / 4 * math.tau + 0.4
        r.line(math.cos(a) * rx * 0.3, -0.5 + math.sin(a) * ry * 0.3, math.cos(a) * rx, -0.5 + math.sin(a) * ry, "web", 0.6,
               tone=2 if not fade else 1)
    if glint: sparkle(r, -2, -2, 2, "eye")
    return done(r)


def fx_snare(out):
    land = [snare_frame(t) for t in (0.4, 0.7, 1.0, 1.0)]
    idle = [snare_frame(1.0), snare_frame(1.0, glint=False)]
    snap = []
    for k in range(6):
        r = Rig()
        h = [2, 5, 7, 7, 5, 3][k]
        for i in range(-4, 5, 2):
            r.line(i, 0, i * 0.3, -h, "web", 1.0, tone=3)
        if k < 3: sparkle(r, 0, -h - 1, 2, "white")
        snap.append(done(r))
    fade = [snare_frame(1.0, fade=1), snare_frame(0.8, fade=1), snare_frame(0.5, fade=1)]
    iced = [snare_frame(1.0, iced=True), snare_frame(1.0, iced=True, glint=True)]
    fx("FxYsvSnare", (20, 20), (10, 15), [("Land", land, [0.075] * 4), ("Idle", idle, [0.3, 0.3]), ("Snap", snap, [0.04, 0.05, 0.06, 0.08, 0.08, 0.08]),
                                          ("Fade", fade, [0.1, 0.1, 0.12]), ("Iced", iced, [0.5, 0.3])], out)


def fx_needle(out):
    fr = []
    for k in range(4):
        r = Rig(); dart(r, 2, 0, 0, 8, 1.6, mat="ice", z=1.0); r.line(-7, 0 + (k % 2) * 0.5, -3, 0, "web", 0.5, tone=3)
        r.dot(-1, 1, "aurp", 2 + k % 2, 1.2); fr.append(done(r))
    fx("FxYsvNeedle", (18, 6), (9, 3), [("Fly", fr, [0.05] * 4)], out)


def fx_frostwake(out):
    """Frost Wake: a white streak hardening into ice behind the Silkmoth's dive (origin = centre, on the floor)."""
    fr = []
    for k in range(5):
        r = Rig()
        L = 4 + k * 2
        r.ell(0, 0, L, 1.8, "snow" if k < 2 else "ice", 0.0, flat=3 if k < 2 else 2)
        if k >= 2: r.line(-L + 1, -1, L - 1, -1, "frost", 0.1, tone=4)
        if k == 3: sparkle(r, -2, -2, 2, "white")
        fr.append(done(r))
    fx("FxYsvFrostWake", (24, 8), (12, 4), [("Streak", fr, [0.05, 0.05, 0.06, 0.08, 0.3])], out)


def fx_shard(out):
    fr = []
    for k in range(4):
        r = Rig(); dart(r, 2, 0, 0, 10, 3.0, mat="crys", z=1.0, tail=3); sparkle(r, 7, 0, 3, "vglow"); fr.append(done(r))
    fx("FxYsvShard", (22, 8), (11, 4), [("Fly", fr, [0.05] * 4)], out)


def witch_crystal(h, crack=0):
    r = Rig()
    r.ell(0, 0, 5.0, 1.6, "shade", -1, flat=3)
    for k, (dx, hh, a) in enumerate(((0, h, 0), (-3, h * 0.6, -25), (3, h * 0.55, 22))):
        if hh > 0.5: crystal(r, dx, 0, hh, 3.0 if k == 0 else 2.2, "crys", 1.0 + k * 0.01, ang=a)
    for c in range(crack):
        r.line(-1 + c, -h * 0.3, 1 - c, -h * 0.7, "white", 2, tone=4)
    return done(r)


def fx_crystal(out):
    grow = [witch_crystal(h) for h in (2, 5, 8, 11, 12, 12)] + [witch_crystal(12, 2)]
    sh = []
    for k in range(5):
        r = Rig(); burst(r, 0, -6, k, n=10, rad=6, mat="vglow" if k < 2 else "snow", z=3)
        for i in range(3 - k // 2): dart(r, (i - 1) * (3 + k), -6 - k, -90 + (i - 1) * 40, 4, 1.6, mat="crys", z=2)
        sh.append(done(r))
    fx("FxYsvCrystal", (36, 30), (18, 26), [("Grow", grow, [0.08, 0.08, 0.1, 0.2, 0.25, 0.2, 0.15]),
                                             ("Shatter", sh, [0.04, 0.05, 0.06, 0.07, 0.08])], out)


def fx_pipflash(out):
    """Cold Read: the frost pips over the hero flash violet as the witch reads them (origin = bottom centre)."""
    fr = []
    for k in range(4):
        r = Rig()
        for i in (-4, 0, 4):
            sparkle(r, i, -3, 1 if k in (1, 2) else 2, "vglow" if k % 2 else "white")
        fr.append(done(r))
    fx("FxYsvPipFlash", (16, 10), (8, 8), [("Flash", fr, [0.06, 0.08, 0.08, 0.1])], out)


def fx_cleave(out):
    """The Rime Knight's cleave: an ice crescent falling forward and down (origin (16, 18))."""
    fr = []
    for k in range(4):
        r = Rig()
        a0, a1 = -150 + k * 20, -10 + k * 25
        for w in range(3):
            arc_smear(r, 2, -6, 15 - w, a0, a1, "ice" if w else "white", 1, z=2 - w * 0.1)
        if k >= 1: flakes(r, [(16, 4, 4), (18, 2, 3), (14, 5, 3)], z=3)
        fr.append(done(r))
    fx("FxYsvCleave", (40, 40), (16, 24), [("Slash", fr, [0.04, 0.05, 0.06, 0.08])], out)


def fx_plates(out):
    fr = []
    for k in range(8):
        r = Rig()
        for j in range(2):
            a = k / 8 * math.tau + j * math.pi
            x, y = math.cos(a) * 11, -8 + math.sin(a) * 3
            front = math.sin(a) > 0
            r.ell(x, y, 1.8, 3.0, "ice", 2 if front else -2, bias=0.25 if front else -0.2)
            r.dot(x - 0.5, y - 1.5, "white", 4 if front else 2, 2.1 if front else -1.9)
        fr.append(done(r))
    fx("FxYsvPlates", (28, 22), (14, 21), [("Orbit", fr, [0.08] * 8)], out)


def fx_platebreak(out):
    fr = []
    for k in range(5):
        r = Rig(); burst(r, 0, -10, k, n=9, rad=5, mat="ice" if k < 2 else "snow", z=3)
        for i in range(3 - min(2, k)): dart(r, (i - 1) * (2 + k * 2), -10 + k * 2, 90 + (i - 1) * 50, 4, 2, z=2)
        fr.append(done(r))
    fx("FxYsvPlateBreak", (30, 24), (15, 23), [("Play", fr, [0.04, 0.05, 0.06, 0.07, 0.08])], out)


def hermit_crystal(h, glow=0, melt=0):
    r = Rig()
    r.ell(0, 0, 5.0, 1.8, "ice", -1, flat=2)
    crystal(r, 0, 0, h, 4.0, "crys", 1.0)
    crystal(r, -2.6, 0, h * 0.55, 2.4, "crys", 0.9, ang=-20)
    crystal(r, 2.4, 0, h * 0.45, 2.2, "crys", 1.1, ang=18)
    if glow:
        sparkle(r, 0, -h - 1, 1 if glow > 1 else 2, "vglow")
    if melt:
        for i in range(melt): r.dot(-3 + i * 2, -1, "eye", 2, 1.2)
    return done(r)


def fx_hermitcrystal(out):
    """A Shard Hermit's planted crystal (origin = its foot on the floor). Flash: the pulse when a Triangle forms."""
    grow = [hermit_crystal(h) for h in (3, 7, 11, 14, 13)]
    idle = [hermit_crystal(13), hermit_crystal(13, glow=1)]
    melt = [hermit_crystal(h, melt=m) for h, m in ((11, 1), (8, 2), (5, 3), (2, 3))]
    flash = [hermit_crystal(13, glow=2), hermit_crystal(13, glow=1), hermit_crystal(13)]
    fx("FxYsvHermitCrystal", (18, 24), (9, 22), [("Grow", grow, [0.06, 0.06, 0.07, 0.08, 0.1]), ("Idle", idle, [0.5, 0.25]),
                                                  ("Melt", melt, [0.08, 0.08, 0.1, 0.12]), ("Flash", flash, [0.06, 0.08, 0.1])], out)


def fx_triangle(out):
    """Triangle: the bead of light strung between crystals (Link), and the frosted floor inside (Frost, Pulse)."""
    link = []
    for k in range(2):
        r = Rig(); r.dot(0, 0, "vglow", 3 + k, 1); r.dot(-1, 0, "vglow", 2, 0.9); r.dot(1, 0, "vglow", 2, 0.9); link.append(done(r))
    frost = []
    for k in range(4):
        r = Rig(); rnd = random.Random(3)
        for i in range(10 + k * 3):
            x, y = rnd.uniform(-7, 7), rnd.uniform(-3.5, 3.5)
            if (x / 7) ** 2 + (y / 3.5) ** 2 > 1: continue
            r.dot(x, y, "snow", 3 if i % 3 else 4, 0.5)
        r.ell(0, 0, 6, 3, "ice", 0.0, flat=1)
        frost.append(r.resolve(floor=False, cast=False, contour=False, selout=False, outline=False))
    pulse = []
    for k in range(3):
        r = Rig(); ring(r, 0, 0, 4 + k * 2, 2 + k, "vglow", 3 - k, 1, n=20, step=1); pulse.append(done(r))
    fx("FxYsvTriangle", (20, 12), (10, 6), [("Link", link, [0.2, 0.2]), ("Frost", frost[3:] + frost[3:], [0.5, 0.5]),
                                            ("Form", frost, [0.06] * 4), ("Pulse", pulse, [0.06, 0.08, 0.1])], out)


# ------------------------------------------------------------------ T3
def eggsac(k, shake=0.0, crack=0):
    r = Rig()
    r.ell(0, 0, 5.0, 1.6, "ice", -1, flat=2)
    r.ell(shake, -4.2, 3.6, 4.0, "web", 1.0, bias=0.1)
    for i in range(3): r.line(-3 + shake, -6 + i * 2, 3 + shake, -5 + i * 2, "silk", 1.1, tone=2)
    for j in range(k): r.dot(-1 + j + shake, -4, "chit", 1, 1.2)
    if crack:
        r.polyline([(-1 + shake, -8), (0 + shake, -5), (-1 + shake, -3), (1 + shake, -1)], "eye", 1.3, tone=3)
        if crack > 1: burst(r, shake, -5, crack - 2, n=6, rad=4, mat="web", z=2)
    return done(r)


def fx_eggsac(out):
    """Egg Sacs: set down (0-2), the brood stirs inside for 2 s (3-12), bursts (13-15); the Broodling is released at the end."""
    hatch = [eggsac(0), eggsac(1), eggsac(1)]
    hatch += [eggsac(2, shake=[0, 0.6, 0, -0.6][i % 4]) for i in range(10)]
    hatch += [eggsac(3, crack=1), eggsac(3, crack=2), eggsac(0, crack=3)]
    fx("FxYsvEggSac", (28, 20), (14, 18), [("Hatch", hatch, [0.06, 0.06, 0.1] + [0.17] * 10 + [0.08, 0.06, 0.08])], out)


def fx_wrap(out):
    """Wrap: silk spiralling round a hero pinned near the Widow Matron (origin = his feet)."""
    start, loop = [], []
    for k in range(7):
        r = Rig()
        turns = min(3, 1 + k)
        for t in range(turns):
            y = -2 - t * 4 - (k % 2) * 0.5
            ring(r, 0, y, 6, 1.6, "web", 3, 1.0, n=18, gap=lambda a: math.sin(a) < -0.2)
            ring(r, 0, y + 1, 6, 1.6, "web", 1, 0.99, n=18, gap=lambda a: math.sin(a) < 0.3)        # the band's shaded underside
            ring(r, 0, y, 6, 1.6, "silk", 1, -1.0, n=18, gap=lambda a: math.sin(a) >= -0.2)
            for hx in (-4, -1): r.dot(hx, y + 1.4, "white", 4, 1.01)                                 # a glint on the silk
        if k == 2: sparkle(r, 5, -12, 2, "white")
        (start if k < 3 else loop).append(done(r))
    fx("FxYsvWrap", (20, 18), (10, 16), [("Start", start, [0.05, 0.05, 0.06]), ("Loop", loop, [0.12] * 4)], out)


def fx_spool(out):
    """Spool: the Loom Widow's line head (Fly), a frost pip running up the line into her (Bead), the snap, and the spool
    on her loom wound with 1-3 pips (S1..S3: origin = the spool's centre)."""
    fly = []
    for k in range(4):
        r = Rig(); r.line(-7, 0, 4, 0, "silver", 1.0, tone=3); r.poly([(4, -2), (7, 0), (4, 2)], "silver", 1.1, bias=0.3)
        r.dot(-2 + k * 2, 0, "white", 4, 1.1); fly.append(done(r))
    bead = []
    for k in range(2):
        r = Rig(); sparkle(r, 0, 0, 2 - k, "eye"); r.dot(-1, 0, "eye", 3, 0.9); bead.append(done(r))
    snap = []
    for k in range(4):
        r = Rig(); burst(r, 0, 0, min(2, k), n=6, rad=3.0, mat="silver"); snap.append(done(r))
    anims = [("Fly", fly, [0.05] * 4), ("Bead", bead, [0.08, 0.08]), ("Snap", snap, [0.05, 0.06, 0.07, 0.08])]
    for n in (1, 2, 3):
        fr = []
        for k in range(2):
            r = Rig()
            r.ell(0, 0, 1.6 + n * 0.5, 2.2 + n * 0.4, "silver", 1.0, bias=0.2)
            for j in range(n):
                r.line(-1.5 - n * 0.4, -1.5 + j * 1.4, 1.5 + n * 0.4, -1.0 + j * 1.4, "eye", 1.1, tone=3 + (k if j == n - 1 else 0))
            if n == 3 and k: sparkle(r, 0, -5, 2, "eye")
            fr.append(done(r))
        anims.append(("S%d" % n, fr, [0.25, 0.25]))
    fx("FxYsvSpool", (16, 12), (8, 6), anims, out)


def fx_hairs(out):
    fr = []
    for k in range(3):
        r = Rig()
        for i in range(3):
            y = (i - 1) * 2.0 + (k % 2) * 0.5
            r.line(-3 + i, y, 3 + i, y - 0.5, "frost", 1.0 + i * 0.01, tone=4 if i == 1 else 3)
            r.dot(4 + i, y - 0.5, "ice", 4, 1.1)
        fr.append(done(r))
    fx("FxYsvHairs", (16, 10), (8, 5), [("Fly", fr, [0.05] * 3)], out)


def fx_broodfur(out):
    """A Broodling shaken off the Tarantula's back: it tumbles down out of the fur in a puff of frost (origin = feet)."""
    fr = []
    for k in range(5):
        r = Rig()
        y = -12 + k * 3.0
        r.ell(0, y, 1.6, 1.2, "chit", 1.0, bias=0.1); r.dot(0, y - 1, "red", 3, 1.1)
        for s in (-1, 1): r.line(0, y, s * 2.5, y + (1 if k % 2 else -1), "chit", 1.0, tone=1)
        burst(r, 0, -12, k, n=6, rad=4, mat="frost", z=0.5)
        fr.append(done(r))
    fx("FxYsvBroodFur", (20, 20), (10, 17), [("Drop", fr, [0.05, 0.05, 0.05, 0.06, 0.08])], out)


def fx_grab(out):
    hold = []
    for k in range(2):
        r = Rig()
        for s in (-1, 1):
            r.ell(s * 4, -2, 2.0, 1.4, "ice", 1, bias=0.2)
        ring(r, 0, -2, 6, 1.5, "ice", 3 - k, 1.1, n=16, step=2)
        hold.append(done(r))
    fling = []
    for k in range(4):
        r = Rig(); burst(r, 0, -4, k, n=8, rad=5, mat="ice" if k < 2 else "snow"); fling.append(done(r))
    fx("FxYsvGrab", (30, 24), (15, 19), [("Hold", hold, [0.1, 0.1]), ("Fling", fling, [0.05, 0.06, 0.07, 0.08])], out)


def fx_curltrail(out):
    """Curling Stone: frost puffs left behind the sliding hero (Trail), the spin lines round him (Spin), and the crash
    at the wall (Crash). Origin = his feet."""
    trail = []
    for k in range(4):
        r = Rig(); r.ell(0, 0, 3.0 - k * 0.6, 1.2, "snow", 1, flat=4 - k); r.dot(-2, -1, "white", 4 - k, 1.1); trail.append(done(r))
    spin = []
    for k in range(4):
        r = Rig()
        a0 = k * 90
        arc_smear(r, 0, -8, 8, a0, a0 + 120, "white", 1, z=2)
        arc_smear(r, 0, -8, 8, a0 + 180, a0 + 300, "snow", 1, z=-2)
        spin.append(done(r))
    crash = []
    for k in range(5):
        r = Rig(); burst(r, 0, -6, k, n=10, rad=7, mat="white" if k < 2 else "snow")
        if k < 3: sparkle(r, 0, -8, 1, "eye")
        crash.append(done(r))
    fx("FxYsvCurlTrail", (28, 24), (14, 21), [("Trail", trail, [0.06, 0.06, 0.08, 0.1]), ("Spin", spin, [0.05] * 4),
                                               ("Crash", crash, [0.04, 0.05, 0.06, 0.08, 0.1])], out)


def fx_auroramote(out):
    fr = []
    for k in range(4):
        r = Rig(); m = "aurg" if k % 2 == 0 else "aurp"
        sparkle(r, 2, 0, 1, m); r.line(-6, 0, 0, 0, m, 0.5, tone=2); r.dot(-3, 1 if k % 2 else -1, m, 3, 0.6); fr.append(done(r))
    fx("FxYsvAuroraMote", (22, 8), (11, 4), [("Fly", fr, [0.05] * 4)], out)


def fx_storm(out):
    """The Pale Empress' blizzard: a whirling knot of snow and aurora light, ~26 x 16."""
    fr = []
    for k in range(6):
        r = Rig(); rnd = random.Random(k)
        for i in range(30):
            a = rnd.uniform(0, math.tau) + k * 0.5
            d = rnd.uniform(2, 12)
            x, y = math.cos(a) * d, math.sin(a) * d * 0.6
            r.line(x, y, x + math.cos(a + 1.6) * 2.5, y + math.sin(a + 1.6) * 1.5, "snow", 1.0, tone=3 if i % 2 else 4)
        for i in range(4):
            a = k * 1.0 + i * 1.6
            r.dot(math.cos(a) * 8, math.sin(a) * 4, "aurg" if i % 2 else "aurp", 3, 1.2)
        fr.append(done(r))
    fx("FxYsvStorm", (36, 22), (18, 11), [("Loop", fr, [0.08] * 6)], out)


def fx_aurora(out):
    """Storm Queen: the aurora ribbons over the Pale Empress (Loop), flaring before each blizzard gust (Flare).
    Origin = the bottom centre of the ribbons (place it over her head)."""
    def rib(k, flare):
        r = Rig()
        for j, m in enumerate(("aurg", "aurp", "aurg")):
            pts = [(x, -3 - j * 2.5 - math.sin(x * 0.4 + k * 0.9 + j) * (1.5 + flare)) for x in range(-10, 11, 2)]
            r.polyline(pts, m, 1 + j * 0.1, tone=4 if flare and j == 1 else 3 if flare else 2)
        if flare: sparkle(r, (k * 5) % 16 - 8, -10, 1, "white")
        return done(r)
    fx("FxYsvAurora", (26, 16), (13, 14), [("Loop", [rib(k, 0) for k in range(4)], [0.15] * 4),
                                           ("Flare", [rib(k, 1 + (k % 2)) for k in range(4)], [0.08] * 4)], out)


def cocoon(cracks, glow, burst_k=-1, shatter_k=-1):
    r = Rig()
    if burst_k < 0 and shatter_k < 0:
        r.ell(0, -12, 8.5, 12, "glass", 0.0, bias=0.15)
        r.ell(-2.5, -16, 2.5, 4.0, "glass", 0.01, flat=4)
        if glow:
            r.ell(0, -11, 2 + glow * 1.2, 3 + glow * 1.4, "cyan", 0.02, flat=min(4, 1 + glow))
        rnd = random.Random(5)
        for c in range(cracks):
            x0 = [-4, 4, 0][c]; y0 = [-18, -10, -4][c]
            pts = [(x0, y0)]
            for i in range(4): pts.append((pts[-1][0] + rnd.uniform(-2, 2), pts[-1][1] + rnd.uniform(1.5, 3)))
            r.polyline(pts, "white", 0.05, tone=4)
            r.polyline([(p[0] + 1, p[1]) for p in pts], "glass", 0.04, tone=1)
    elif burst_k >= 0:
        burst(r, 0, -12, burst_k, n=12, rad=7, mat="cyan" if burst_k < 2 else "white", z=2)
        for i in range(5 - burst_k):
            a = i * 1.26
            dart(r, math.cos(a) * (5 + burst_k * 2), -12 + math.sin(a) * (5 + burst_k * 2), math.degrees(a), 5, 2.4, mat="glass", z=1)
    else:
        for i in range(6):
            a = i * 1.05 + 0.3
            x, y = math.cos(a) * (5 + shatter_k * 2.5), -10 + math.sin(a) * (5 + shatter_k * 2) + shatter_k * 2
            r.poly([(x, y), (x + 2, y + 1), (x + 0.5, y + 3)], "glass", 1.0, bias=0.2)
        burst(r, 0, -10, shatter_k, n=8, rad=8, mat="white", z=2)
    return done(r)


def fx_cocoon(out):
    """Glass Cocoon over the Glasswing (origin = her feet): C0..C3 = 0-3 cracks (the glow inside builds), Burst = she hatches
    healed, Shatter = three cracks broke it."""
    anims = [("C%d" % c, [cocoon(c, g) for g in (1 + c // 2, 2 + c // 2)], [0.2, 0.2]) for c in range(4)]
    anims += [("Grow", [cocoon(0, g) for g in (0, 1, 2, 3)], [0.25, 0.25, 0.25, 0.25])]
    anims += [("Burst", [cocoon(0, 0, burst_k=k) for k in range(5)], [0.04, 0.05, 0.06, 0.07, 0.08]),
              ("Shatter", [cocoon(0, 0, shatter_k=k) for k in range(5)], [0.04, 0.05, 0.06, 0.07, 0.08])]
    fx("FxYsvCocoon", (36, 38), (18, 34), anims, out)


def breath_frame(k, black=False):
    r = Rig(); rnd = random.Random(k + 3)
    m = "black" if black else "snow"
    for i in range(5 + k):
        x, y = rnd.uniform(-3, 3) + k * 0.8, rnd.uniform(-3, 3)
        r.ell(x, y, 1.6 + k * 0.3, 1.3 + k * 0.2, m, 1 + i * 0.01, flat=4 - min(3, k // 2) if not black else 2 + (i % 2))
    if not black: r.dot(k, -1, "white", 4, 2)
    else: r.dot(k, -1, "eye", 3, 2)
    return done(r)


def fx_breath(out):
    fx("FxYsvBreath", (28, 20), (14, 10), [("Puff", [breath_frame(k) for k in range(6)], [0.06] * 6),
                                           ("Black", [breath_frame(k, True) for k in range(6)], [0.06] * 6)], out)


def fx_trainsweep(out):
    """Train Sweep: the snow train swept through a half circle round the Bride, r 40 (origin = her feet; the sweep runs
    from behind her over the top to in front; flip it for the other side)."""
    fr = []
    for k in range(5):
        r = Rig()
        a0 = 200 + k * 30; a1 = a0 + 60
        for w in range(4):
            R = 36 - w * 2.5
            n = 14
            for i in range(n + 1):
                t = i / n
                a = math.radians(lerp(a0, a1, t))
                tone = 1 if t < 0.3 else 2 if t < 0.7 else 3
                r.dot(math.cos(a) * R, -4 + math.sin(a) * R * 0.55, "white" if w == 0 and t > 0.7 else "snow", tone + (1 if w == 0 else 0), 1 + w * 0.1)
            a = math.radians(a1)
            r.dot(math.cos(a) * (R - 1), -4 + math.sin(a) * (R - 1) * 0.55, "frost", 4, 1.5)
        fr.append(done(r))
    fx("FxYsvTrainSweep", (82, 48), (41, 28), [("Sweep", fr, [0.06] * 5)], out)


def fx_blackveil(out):
    """Widowed: black lace bursting out over the Bride as her veil turns (origin = her feet)."""
    fr = []
    for k in range(6):
        r = Rig(); rnd = random.Random(11)
        for i in range(14):
            a = rnd.uniform(-2.8, -0.3)
            d = 4 + k * 2.5 + rnd.uniform(-1, 1)
            x, y = math.cos(a) * d, -28 + math.sin(a) * d * 0.8 + k
            r.line(x, y, x + math.cos(a) * 2, y + math.sin(a) * 2, "black", 1, tone=3 if i % 2 else 4)
        if k < 3: sparkle(r, 0, -32, 1, "rglow")
        fr.append(done(r))
    fx("FxYsvBlackVeil", (40, 44), (20, 42), [("Play", fr, [0.05, 0.06, 0.07, 0.08, 0.1, 0.12])], out)


def fx_coldring(out):
    """Cold Presence: a ring of frost creeping over the floor round the Snow Wraith, r 30 (origin = its feet)."""
    fr = []
    for k in range(4):
        r = Rig(); rnd = random.Random(k)
        for i in range(48):
            a = i / 48 * math.tau + k * 0.04
            rr = 30 + rnd.uniform(-1.5, 1.5)
            r.dot(math.cos(a) * rr, math.sin(a) * rr * 0.45, "snow" if i % 3 else "eye", 3 if (i + k) % 4 else 4, 0.5)
            if i % 4 == k: r.dot(math.cos(a) * (rr - 2), math.sin(a) * (rr - 2) * 0.45, "ice", 2, 0.4)
        fr.append(r.resolve(floor=False, cast=False, contour=False, selout=False, outline=False))
    fx("FxYsvColdRing", (68, 32), (34, 16), [("Loop", fr, [0.15] * 4)], out)


def fx_vortex(out):
    def vframe(k, rad, burst_k=-1):
        r = Rig()
        if burst_k < 0:
            for j in range(3):
                for i in range(18):
                    a = i / 18 * math.tau + k * 0.6 + j * 0.7
                    d = rad * (1 - j * 0.28)
                    r.dot(math.cos(a) * d, -2 + math.sin(a) * d * 0.45, "snow" if j else "ice", 4 - j, 1 - j * 0.1)
            r.ell(0, -2, 2.5, 1.2, "eye", 1.2, flat=2)
        else:
            for i in range(10):
                a = i / 10 * math.tau
                h = 6 + burst_k * 3
                r.line(math.cos(a) * 6, -2 + math.sin(a) * 2.5, math.cos(a) * (6 + burst_k), -2 - h + math.sin(a) * 2, "snow", 1, tone=4 - min(3, burst_k))
            burst(r, 0, -10, burst_k, n=10, rad=8, mat="white", z=2)
        return done(r)
    fx("FxYsvVortex", (42, 32), (21, 24), [("Open", [vframe(k, 6 + k * 5) for k in range(3)], [0.08] * 3),
                                           ("Spin", [vframe(k, 18) for k in range(4)], [0.07] * 4),
                                           ("Burst", [vframe(0, 0, b) for b in range(5)], [0.04, 0.05, 0.06, 0.07, 0.08])], out)


def fx_quake(out):
    fr = []
    for k in range(5):
        r = Rig()
        ring(r, 0, 0, 6 + k * 4.5, 2 + k * 1.6, "snow" if k < 3 else "ice", 4 - min(3, k), 1, n=40, step=1)
        for i in range(5 - k):
            a = i * 1.25
            dart(r, math.cos(a) * (6 + k * 3), -2 - abs(math.sin(a)) * 2 - k, -90, 3 + (2 - abs(i - 2)), 2, z=2)
        fr.append(done(r))
    fx("FxYsvQuake", (52, 24), (26, 12), [("Play", fr, [0.05, 0.06, 0.07, 0.08, 0.1])], out)


def fx_spike(out):
    fr = []
    for k in range(6):
        r = Rig(); h = [3, 8, 11, 10, 7, 3][k]
        crystal(r, 0, 0, h, 4, "ice", 1)
        crystal(r, -2.5, 0, h * 0.6, 2.4, "ice", 0.9, ang=-25)
        if k == 2: sparkle(r, 0, -h - 1, 2, "white")
        fr.append(done(r))
    fx("FxYsvSpike", (18, 17), (9, 15), [("Play", fr, [0.05, 0.05, 0.08, 0.1, 0.08, 0.06])], out)


def fx_bellyslide(out):
    """Glacier Run: the snow sprayed up by the Colossus' belly slide (origin = its feet; spray to the rear)."""
    fr = []
    for k in range(4):
        r = Rig(); rnd = random.Random(k)
        for i in range(16):
            x = rnd.uniform(-18, -4); y = -rnd.uniform(0, 8) * (1 - (x + 18) / 20)
            r.dot(x, y, "snow" if i % 3 else "white", 4 if i % 4 == 0 else 3, 1)
        r.line(-16, 0, 6, 0, "ice", 0.5, tone=3)
        fr.append(done(r))
    fx("FxYsvBellySlide", (44, 14), (22, 12), [("Spray", fr, [0.06] * 4)], out)


def sigil(k, brand=False):
    """A frost sigil: a hexagonal snow-crystal ring with a red heart (the Warden's challenge); the brand is its twin."""
    r = Rig()
    R = 4.0 if brand else 5.0
    for i in range(6):
        a = i / 6 * math.tau + k * 0.15
        x, y = math.cos(a) * R, -6 + math.sin(a) * R * 0.8
        r.line(0, -6, x, y, "ice", 1, tone=3)
        r.dot(x, y, "white", 4, 1.1)
    r.dot(0, -6, "rglow", 4 if k % 2 else 3, 1.2)
    if not brand and k % 2: sparkle(r, 0, -12, 2, "rglow")
    return done(r)


def fx_challenge(out):
    """Challenge: the frost sigil over the Rime Warden (Sigil), the matching brand over the hero (Brand), the bang of mace
    on shield (Bang). Origin = the bottom centre (lift it over the head)."""
    bang = []
    for k in range(4):
        r = Rig(); burst(r, 0, -6, k, n=8, rad=5, mat="white" if k < 2 else "rglow"); bang.append(done(r))
    fx("FxYsvChallenge", (16, 16), (8, 14), [("Sigil", [sigil(k) for k in range(4)], [0.12] * 4),
                                             ("Brand", [sigil(k, True) for k in range(4)], [0.12] * 4),
                                             ("Bang", bang, [0.04, 0.05, 0.06, 0.08])], out)


def fx_shieldblock(out):
    fr = []
    for k in range(4):
        r = Rig(); burst(r, 0, -2, k, n=8, rad=4, mat="white" if k < 2 else "snow")
        r.line(0, -6 + k, 0, 2 - k, "steel", 1, tone=4); fr.append(done(r))
    fx("FxYsvShieldBlock", (16, 14), (8, 8), [("Play", fr, [0.04, 0.05, 0.06, 0.08])], out)


def fx_geodeshard(out):
    fr = []
    for k in range(4):
        r = Rig(); dart(r, 1, 0, k * 20 - 30, 7, 3.0, mat="crys", z=1.0, tail=2); fr.append(done(r))
    fx("FxYsvGeodeShard", (16, 10), (8, 5), [("Fly", fr, [0.05] * 4)], out)


def fx_geodecrack(out):
    fr = []
    for k in range(6):
        r = Rig(); burst(r, 0, -12, k, n=14, rad=12, mat="vglow" if k < 3 else "snow", z=2)
        for i in range(4 - min(3, k)):
            a = -2.5 + i * 0.6
            crystal(r, math.cos(a) * (6 + k * 3), -10 + math.sin(a) * (6 + k * 2), 3, 1.6, "crys", 1, ang=math.degrees(a) + 90)
        fr.append(done(r))
    fx("FxYsvGeodeCrack", (52, 46), (26, 36), [("Play", fr, [0.05, 0.05, 0.06, 0.07, 0.08, 0.1])], out)


def fx_prismbolt(out):
    def f(k, lens=False):
        r = Rig()
        dart(r, 2, 0, 0, 7, 3.0, mat="glass", z=1.0)
        for i, m in enumerate(SPEC):
            r.dot(-2 - i, (i - 2) * 0.5 + (k % 2) * 0.3, m, 3, 0.8)
        if lens: sparkle(r, 2, 0, 1, "white", 2)
        return done(r)
    fx("FxYsvPrismBolt", (20, 8), (10, 4), [("Fly", [f(k) for k in range(4)], [0.05] * 4), ("Lens", [f(k, True) for k in range(4)], [0.04] * 4)], out)


def fx_slabflash(out):
    """Sunburst: a slab of ice flashing with prism light as the Oracle's light runs through it (origin = the slab centre)."""
    fr = []
    for k in range(5):
        r = Rig()
        r.ell(0, 0, 10 - k * 0.5, 5 - k * 0.3, "white" if k < 2 else "eye", 0.0, flat=4 - min(3, k))
        for i, m in enumerate(SPEC):
            a = math.radians(-160 + i * 35)
            L = 6 + k * 2
            r.line(0, -1, math.cos(a) * L, -1 + math.sin(a) * L * 0.8, m, 1, tone=4 if k < 2 else 3)
        fr.append(r.resolve(floor=False, cast=False, contour=False, selout=False, outline=False))
    fx("FxYsvSlabFlash", (32, 20), (16, 12), [("Flash", fr, [0.04, 0.05, 0.06, 0.07, 0.08])], out)


JOBS = [("FxYsvFloe", fx_floe), ("FxYsvGale", fx_gale), ("FxYsvPuff", fx_puff), ("FxYsvBind", fx_bind), ("FxYsvGlob", fx_glob),
        ("FxYsvMote", fx_mote), ("FxYsvGust", fx_gust), ("FxYsvIcicle", fx_icicle), ("FxYsvSkidShard", fx_skidshard),
        ("FxYsvThread", fx_thread), ("FxYsvStrumBead", fx_strumbead), ("FxYsvSnare", fx_snare), ("FxYsvNeedle", fx_needle),
        ("FxYsvFrostWake", fx_frostwake), ("FxYsvShard", fx_shard), ("FxYsvCrystal", fx_crystal),
        ("FxYsvPipFlash", fx_pipflash), ("FxYsvCleave", fx_cleave), ("FxYsvPlates", fx_plates), ("FxYsvPlateBreak", fx_platebreak),
        ("FxYsvHermitCrystal", fx_hermitcrystal), ("FxYsvTriangle", fx_triangle), ("FxYsvEggSac", fx_eggsac), ("FxYsvWrap", fx_wrap),
        ("FxYsvSpool", fx_spool), ("FxYsvHairs", fx_hairs), ("FxYsvBroodFur", fx_broodfur), ("FxYsvGrab", fx_grab),
        ("FxYsvCurlTrail", fx_curltrail), ("FxYsvAuroraMote", fx_auroramote), ("FxYsvStorm", fx_storm), ("FxYsvAurora", fx_aurora),
        ("FxYsvCocoon", fx_cocoon), ("FxYsvBreath", fx_breath), ("FxYsvTrainSweep", fx_trainsweep), ("FxYsvBlackVeil", fx_blackveil),
        ("FxYsvColdRing", fx_coldring), ("FxYsvVortex", fx_vortex), ("FxYsvQuake", fx_quake), ("FxYsvSpike", fx_spike),
        ("FxYsvBellySlide", fx_bellyslide), ("FxYsvChallenge", fx_challenge), ("FxYsvShieldBlock", fx_shieldblock),
        ("FxYsvGeodeShard", fx_geodeshard), ("FxYsvGeodeCrack", fx_geodecrack), ("FxYsvPrismBolt", fx_prismbolt),
        ("FxYsvSlabFlash", fx_slabflash)]
