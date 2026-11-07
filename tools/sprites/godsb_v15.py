"""Umbrael, Bel'Mora and Jinx sheets redrawn at their in-game size and the new perk art.

    python3 godsb_v15.py [--only FxDarkness,FxBelTide,...]

- FxDarkness (umbrael): the Gloom cloud at its real size (was a 31 x 16 sheet scaled x1.4 by the template).
  Drawn by umbrael_rigs.fx_darkness (k 1.4), same 28-frame Life layout.
- FxBelTide (belmora): Rising Tide. A wide sheet of shallow brine that a tide leaves on the floor: the crest washes in
  (Spread 4), the water lies there with a slow sheen (Idle 4, looped), then drains (Fade 4). Low contrast against a dark
  floor (wet-stone tones, a thin foam lip, sparse glints) so a room with three of them still reads as floor, not clutter.
- FxBelTideCrest (belmora): the brief surge that runs ahead of a tide (a low foam line, 6 frames) where a pool forms.
- FxJinxDieShard (jinx): the Dice Imp's Roll shards, a chip of the die drawn at 7 x 7 (was the 15 x 13 die at x0.7).
- FxJinxWildCard (jinx): no change in look, but the card now hangs over the monster's head (code), see JinxPack.

Every sheet: <id>.png + .json + _preview.png via anim.pack, origin listed in TIMING (godsb_v15 section).
"""
import math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from anim import Spr, SprRGB, PALETTE, pack, preview  # noqa: E402

ART = os.path.join(os.path.dirname(os.path.dirname(HERE)), "art")
BUILT = {}


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def emit(name, outdir, anims, cell, origin, scale=6):
    cw, ch = cell
    for an, fr, du in anims:
        assert len(fr) == len(du), (name, an)
        for f in fr:
            for (x, y) in f.px:
                assert -origin[0] <= x < cw - origin[0] and -origin[1] <= y < ch - origin[1], (name, an, x, y)
    img, man = pack(name, anims, cw, ch, origin, outdir)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    BUILT[name] = (cell, origin, [(a, len(f), list(d)) for a, f, d in anims])
    print("built %-16s cell %dx%d origin %s  %s" % (name, cw, ch, origin, ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))


# ================================================================== Umbrael: FxDarkness at its real size
def build_darkness():
    import umbrael_rigs as U
    sp, idl, fd = U.fx_darkness()
    reps = 11
    life = sp + idl * reps + fd
    durs = [0.08] * 3 + [0.2] * (2 * reps) + [0.12] * 3
    allf = sp + idl + fd
    x0 = min(f.bbox()[0] for f in allf); x1 = max(f.bbox()[2] for f in allf)
    y0 = min(f.bbox()[1] for f in allf); y1 = max(f.bbox()[3] for f in allf)
    hw = max(-x0, x1) + 2
    emit("FxDarkness", f"{ART}/out_umbrael", [("Life", life, durs)], (2 * hw, -y0 + 2 + max(0, y1) + 2), (hw, -y0 + 2))


# ================================================================== Bel'Mora: Rising Tide
# wet-stone and brine tones (RGB): the pool must sit on the dark dungeon floor like spilled water, not glow on it
TIDE = {
    "rim": rgb("1a2e32"),      # dark wet edge (where water meets dry stone)
    "deep": rgb("1f3f45"),     # the body of the water (slightly lighter + bluer than the floor)
    "mid": rgb("27525a"),
    "sheen": rgb("3a7076"),    # the long slow light bands across the surface
    "lip": rgb("5c9c96"),      # foam lip at the near edge
    "foam": rgb("9fd2c4"),
    "glint": rgb("d8f2ea"),
    "salt": rgb("8aa69e"),     # a crust of salt left on the far edge
}
RX, RY = 30.0, 9.0           # the full pool: 60 x 18 on the floor (the status-zone box is 52 x 14)


def tide_mask(spread=1.0, seed=3):
    """Lumpy flat pool: a long main lobe and four offset lobes, so it reads as water that ran across the floor."""
    lobes = [(0, 0, RX * 0.78, RY * 0.78), (-RX * 0.48, 1.0, RX * 0.42, RY * 0.62), (RX * 0.5, -0.8, RX * 0.44, RY * 0.66),
             (-RX * 0.1, -2.2, RX * 0.5, RY * 0.5), (RX * 0.2, 2.4, RX * 0.46, RY * 0.48)]
    rnd = random.Random(seed)
    m = {}
    for (lx, ly, rx, ry) in lobes:
        rx *= spread; ry = max(1.5, ry * (0.35 + 0.65 * spread)); lx *= spread
        for y in range(int(ly - ry) - 1, int(ly + ry) + 2):
            for x in range(int(lx - rx) - 1, int(lx + rx) + 2):
                d = ((x - lx) / rx) ** 2 + ((y - ly) / ry) ** 2
                if d <= 1.0: m[(x, y)] = min(m.get((x, y), 9.0), d)
    # nibble the outline a little (no perfect ellipses on a dungeon floor)
    for (x, y) in list(m):
        edge = sum((x + a, y + b) not in m for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge and rnd.random() < 0.18: del m[(x, y)]
    return m


def tide_frame(spread=1.0, phase=0, fade=0.0, seed=3, crest=None):
    m = tide_mask(spread, seed)
    px = {}
    for (x, y), d in m.items():
        if fade and ((x * 7 + y * 13 + seed * 5) % 17) / 17.0 < fade * (0.4 + 0.6 * d): continue
        near_edge = any((x + a, y + b) not in m for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if near_edge:
            col = TIDE["lip"] if (y > 0 and (x + phase) % 3 != 0) else TIDE["rim"]
            if y < -1 and (x * 3 + seed) % 5 == 0: col = TIDE["salt"]
        else:
            col = TIDE["deep"] if d > 0.35 else TIDE["mid"]
            # long diagonal light bands that drift one pixel per idle frame
            band = (x - 3 * y + phase * 2 + seed) % 23
            if band in (0, 1) and d < 0.8: col = TIDE["sheen"]
            if band == 2 and d < 0.5: col = TIDE["mid"]
        px[(x, y)] = col
    if fade < 0.6:
        rnd = random.Random(seed * 31 + phase)
        for _ in range(4):
            x = rnd.randint(int(-RX * 0.6 * spread), int(RX * 0.6 * spread)); y = rnd.randint(-3, 3)
            if (x, y) in m: px[(x, y)] = TIDE["glint"] if rnd.random() < 0.4 else TIDE["foam"]
    if crest is not None:   # the surge line rolling over the pool as it forms
        cx, w = crest
        for y in range(int(-RY * spread) - 1, int(RY * spread) + 2):
            x = int(round(cx + y * 0.6))
            for k in range(w):
                p = (x - k, y)
                if p in m or k == 0:
                    px[p] = TIDE["foam"] if k == 0 else TIDE["lip"]
            if (y + phase) % 3 == 0: px[(x + 1, y)] = TIDE["glint"]
    return SprRGB(px)


def build_tide():
    spread = [tide_frame(0.35, 0, crest=(-6, 2)), tide_frame(0.6, 1, crest=(4, 2)), tide_frame(0.85, 2, crest=(14, 2)),
              tide_frame(1.0, 3, crest=(26, 1))]
    idle = [tide_frame(1.0, p) for p in range(4)]
    fade = [tide_frame(0.9, 0, 0.12), tide_frame(0.72, 1, 0.2), tide_frame(0.52, 2, 0.28), tide_frame(0.3, 3, 0.35)]   # drains back to a puddle
    cell = (66, 24)
    origin = (33, 12)
    emit("FxBelTide", f"{ART}/out_belmora", [("Spread", spread, [0.07, 0.07, 0.08, 0.1]), ("Idle", idle, [0.3] * 4),
                                              ("Fade", fade, [0.12, 0.12, 0.14, 0.16])], cell, origin, scale=5)
    # the crest that runs in ahead of a pool: a low foam line with spray, rolling right 6 px a frame (flipped in code)
    crest = []
    for i in range(6):
        px = {}
        L = 9 + (i if i < 3 else 5 - i) * 2
        for y in range(-L // 2, L // 2 + 1):
            x = int(round(-12 + i * 5 + y * 0.6))
            px[(x, y)] = TIDE["foam"]
            px[(x - 1, y)] = TIDE["lip"]
            if i < 5: px[(x - 2, y)] = TIDE["mid"]
            if (y + i) % 3 == 0 and i < 5: px[(x + 1, y - 1)] = TIDE["glint"]
        if i >= 1:
            rnd = random.Random(i)
            for _ in range(3 if i < 4 else 1):
                px[(int(-14 + i * 5 + rnd.randint(-2, 1)), rnd.randint(-L // 2 - 3, -L // 2 - 1))] = TIDE["foam"]
        crest.append(SprRGB(px))
    emit("FxBelTideCrest", f"{ART}/out_belmora", [("Play", crest, [0.05] * 6)], (40, 20), (20, 10), scale=6)


# ================================================================== Jinx: die shard
def build_die_shard():
    IV, IV2, IV3, OUT, PIP, PIP2 = rgb("f4eac6"), rgb("dcc998"), rgb("9a8468"), rgb("2a1e1c"), rgb("be3a34"), rgb("6c141e")
    frames = []
    for i in range(4):
        px = {}
        # a broken corner of the die: a small rough cube (5 px) with one red pip, tumbling 90 degrees a frame
        body = [(x, y) for x in range(-2, 3) for y in range(-2, 3) if not (x == 2 and y == -2) and not (x == -2 and y == 2 and i % 2)]
        rot = lambda p: [(p[0], p[1]), (-p[1], p[0]), (-p[0], -p[1]), (p[1], -p[0])][i]
        for (x, y) in body:
            X, Y = rot((x, y))
            px[(X, Y)] = IV if (x + y) < 0 else IV2 if (x + y) < 3 else IV3
        X, Y = rot((0, 0)); px[(X, Y)] = PIP
        X, Y = rot((1, 1)); px[(X, Y)] = PIP2 if i % 2 else IV3
        # chipped broken edge (the side it broke off)
        X, Y = rot((2, -1)); px[(X, Y)] = IV3
        s = SprRGB(px)
        # outline
        out = dict(s.px)
        for (x, y) in list(s.px):
            for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (x + a, y + b) not in s.px: out.setdefault((x + a, y + b), OUT)
        # a two-pixel motion streak behind (the shard flies right)
        out.setdefault((-5, 0), IV3); out.setdefault((-6, 0 if i % 2 else 1), IV3)
        frames.append(SprRGB(out))
    emit("FxJinxDieShard", f"{ART}/out_jinx", [("Fly", frames, [0.05] * 4)], (14, 9), (7, 4), scale=10)


# ================================================================== Umbrael: the echo of an unseen bite
def build_echo_bite():
    """FxUmbEchoBite: the Twice Struck echo of a bite (whose hitbox has no art of its own): a pair of shadow jaws that
    snap shut where the first bite landed, then smoke away. 5 frames, about 15 x 13, origin at the bite centre."""
    VI = [rgb(h) for h in ("2b1a36", "4a2a5e", "6e3c8c", "9a5cbf", "c6a0ec", "efe2ff")]
    OUT = rgb("170f1e")
    frames = []
    gaps = [6, 3, 0, 0, 0]
    for i in range(5):
        px = {}
        g = gaps[i]
        for jaw, sgn in ((0, -1), (1, 1)):
            for x in range(-7, 8):
                t = abs(x) / 7.0
                y = sgn * (g + 1 + int(round(3.2 * (1 - t * t))))
                if i >= 3 and (x * 3 + i + jaw) % (5 - i + 3) == 0: continue          # breaking up into smoke
                px[(x, y)] = VI[2] if i < 3 else VI[1]
                px[(x, y - sgn)] = VI[3] if i < 3 else VI[2]
                # fangs: three teeth per jaw pointing at the other jaw
                if x in (-4, 0, 4) and i < 4:
                    px[(x, y - 2 * sgn)] = VI[5] if i == 2 else VI[4]
                    if g > 0 or i == 2: px[(x, y - 3 * sgn)] = VI[4] if i == 2 else VI[3]
        if i == 2:   # the snap: a bright seam and a few flecks
            for x in range(-6, 7): px[(x, 0)] = VI[5] if abs(x) < 3 else VI[4]
            for (fx, fy) in ((-8, -2), (8, 1), (-6, 3), (7, -3)): px[(fx, fy)] = VI[4]
        if i >= 3:
            rnd = random.Random(i)
            for _ in range(8 if i == 3 else 5):
                px[(rnd.randint(-7, 7), rnd.randint(-8, -2) - (i - 3) * 2)] = rnd.choice(VI[1:4])
        s = SprRGB(px)
        out = dict(s.px)
        if i < 3:
            for (x, y) in list(s.px):
                for a2, b2 in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if (x + a2, y + b2) not in s.px: out.setdefault((x + a2, y + b2), OUT)
        frames.append(SprRGB(out))
    emit("FxUmbEchoBite", f"{ART}/out_umbrael", [("Play", frames, [0.05, 0.05, 0.08, 0.09, 0.1])], (22, 28), (11, 14), scale=8)


JOBS = {"FxUmbEchoBite": build_echo_bite, "FxDarkness": build_darkness, "FxBelTide": build_tide, "FxBelTideCrest": None, "FxJinxDieShard": build_die_shard}


def main():
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
    done = set()
    for n, fn in JOBS.items():
        if fn is None or (only and n not in only and not (n == "FxBelTide" and "FxBelTideCrest" in only)): continue
        if fn in done: continue
        done.add(fn)
        fn()


if __name__ == "__main__":
    main()
