"""The silver ghost's Ascension tells, drawn with the material renderer (jinx_v2_rigs, through ghosts_v2_kit).

    python3 silver_tell_fx.py [outdir]          (default: art/out_silvertell)

FxSilverHalo   Halo (loop)  8: eight orbs banked, the next body goes one level deeper: a moonlit ring behind the
                            ghost (the code keeps it a step behind the ghost, so it never covers it), a pale pool on
                            the floor under it and motes rising at its sides. Origin = the ghost's position.
FxSilverMark   Loop         the same news over the player's head (ghost or monster): a small crescent moon with an
                            up chevron, so every player can read it in a busy fight. Origin = the mark's bottom.
FxSilverInhabit Play        the upgraded body is taken: a column of moonlight falls on it, a silver ring bursts out
                            along the floor and sparkles settle round its feet (about one second). Origin = the feet.

Crawl's muted palette (the vanilla ghosts' cold greys) with a cool moonlit silver as the one accent.
"""
import math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ghosts_v2_kit import Rig, sheet, spark, add_ramps, outdir_for  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else outdir_for("out_silvertell")

add_ramps({
    "moon":   ["1a1e2a", "343c4e", "5e6a80", "9aa6b8", "d6dee8"],     # moonlit silver (lit, shiny)
    "moonl":  ["2a3040", "4e5a6e", "8a96aa", "c4ccd8", "eef2f6"],     # moonlight itself (emissive)
    "mink":   ["0e1016", "161a22", "20242e", "2a2e3a", "343846"],     # the mark's ink
}, emissive={"moonl"}, shiny={"moon"})


def done(r, lift=0):
    """Resolve; lift moves the frame up by that many pixels (for art that reaches below the anchor: the sheet keeps
    its anchor pixel two rows above the cell bottom, so the code's origin pixel is that many rows higher)."""
    s = r.resolve(selout=False, cast=False, contour=False, floor=False)
    if lift: s.px = {(x, y - lift): c for (x, y), c in s.px.items()}
    return s


HALO_LIFT, INHABIT_LIFT = 5, 11     # the code's origin pixels: FxSilverHalo (22, 37), FxSilverInhabit (36, 87)


def ring(r, cx, cy, rx, ry, mat, tone, z, n=48, keep=None):
    for i in range(n):
        a = i / n * math.tau
        if keep and not keep(i, a): continue
        r.dot(cx + rx * math.cos(a), cy + ry * math.sin(a), mat, tone, z)


# ================================================================== the ready halo (behind the ghost)
HALO_N = 8


def halo(i):
    r = Rig()
    cy, rx, ry = -12.0, 14.0, 15.0
    pulse = 0.5 + 0.5 * math.cos(i / HALO_N * math.tau)          # 1 at frame 0, 0 at frame 4
    glint = i / HALO_N * math.tau                               # a bright arc travelling round the ring
    # the soft inner ring (every other pixel, dim) and the moonlit outer ring
    ring(r, 0, cy, rx - 2, ry - 2, "moonl", 0, 1.0, n=56, keep=lambda k, a: k % 2 == 0)
    def tone_at(a):
        d = abs((a - glint + math.pi) % math.tau - math.pi)
        return 4 if d < 0.35 else 3 if d < 0.9 else 2 if pulse > 0.35 or d < 1.6 else 1
    for k in range(72):
        a = k / 72 * math.tau
        t = tone_at(a)
        r.dot(rx * math.cos(a), cy + ry * math.sin(a), "moonl", t, 2.0)
        r.dot((rx + 1) * math.cos(a), cy + (ry + 1) * math.sin(a), "moonl", max(1, t - 1), 1.9)
        r.dot((rx + 2) * math.cos(a), cy + (ry + 2) * math.sin(a), "mink", 1, 0.2)    # a dark backing: reads on any floor
    # four short rays on the diagonals, longer on the pulse
    ln = 2 + int(round(2 * pulse))
    for a in (0.25 * math.pi, 0.75 * math.pi, 1.25 * math.pi, 1.75 * math.pi):
        for s in range(ln):
            d = 1.0 + s
            r.dot((rx + d) * math.cos(a), cy + (ry + d) * math.sin(a), "moonl", 3 if s == 0 else 1, 1.5)
    # the glint itself twinkles
    gx, gy = rx * math.cos(glint), cy + ry * math.sin(glint)
    spark(r, gx, gy, 1 if i % 2 else 2, mat="moonl", z=3.0)
    # a pale pool on the floor under the ghost
    ring(r, 0, 0, 9, 2, "moonl", 2 if pulse > 0.5 else 1, 0.5, n=36)
    for x in range(-6, 7):
        if (x + i) % 2 == 0: r.dot(x, 0, "moonl", 1, 0.4)
    # motes rising at the sides (outside the ghost's own outline)
    rnd = random.Random(11)
    for k in range(6):
        side = -1 if k % 2 else 1
        x0 = side * rnd.uniform(16.5, 18.5)
        ph = (k / 6.0 + i / HALO_N) % 1.0
        y = -2 - ph * 30
        if ph < 0.85:
            r.dot(x0 + 0.8 * math.sin(ph * 6 + k), y, "moonl", 4 if ph < 0.4 else 3 if ph < 0.65 else 1, 2.5)
    return done(r, HALO_LIFT)


# ================================================================== the head mark
def mark(i):
    r = Rig()
    bob = [0, 0, -1, -1, -1, 0][i]
    cx, cy, R = -1.0, -6.5 + bob, 5.2              # the moon's disc
    ix, iy, ir = cx + 2.6, cy - 1.4, 4.1           # the shadow that bites it into a crescent
    lit = {}
    for y in range(int(cy - 7), int(cy + 7)):
        for x in range(int(cx - 7), int(cx + 7)):
            d = math.hypot(x - cx, y - cy)
            if d <= R and math.hypot(x - ix, y - iy) > ir:
                # lit from the top left: the outer rim brightest, the lower horn in shade
                t = 4 if (d > R - 1.3 and (x - cx) + (y - cy) < -1.5) else 3 if (x - cx) + (y - cy) < 2.5 else 2
                lit[(x, y)] = ("moon", t)
    # an up chevron in the crescent's bowl: the next body goes up
    ux, uy = int(round(ix)), int(round(iy + 2))
    for (dx, dy, t) in ((0, -2, 4), (-1, -1, 4), (1, -1, 4), (-2, 0, 3), (2, 0, 3)):
        lit[(ux + dx, uy + dy)] = ("moonl", t)
    # a one-pixel ink ring round both, so it reads over anything
    ink = set()
    for (x, y) in lit:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if (x + dx, y + dy) not in lit: ink.add((x + dx, y + dy))
    for (x, y) in ink: r.dot(x, y, "mink", 1, 0.0)
    for (x, y), (m, t) in lit.items(): r.dot(x, y, m, t, 1.0)
    # a twinkle on the upper horn, cycling
    k = [2, 1, 0, -1, 0, 1][i]
    if k >= 0: spark(r, cx + 1.5, cy - R - 1.5, k, mat="moonl", z=3.0)
    return done(r)


# ================================================================== the inhabit moment
INHABIT_D = [0.04, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.1, 0.11, 0.12, 0.14]   # 1.0 s


def column(r, w, top, bottom, bright, solid=False, z=2.0):
    """A falling shaft of moonlight: bright edges and a lit core, dithered between them (unless solid, the impact
    frame) so the body inside still shows through."""
    for y in range(int(top), int(bottom) + 1):
        for x in range(-w, w + 1):
            t = abs(x) / max(1.0, float(w))
            if t > 0.8 and (x + y) % 2: continue
            if not solid and 0.15 < t < 0.75 and (x + y) % 2: continue
            tone = (4 if t < 0.3 else 3 if t < 0.65 or t > 0.85 else 2) - (0 if bright else 1)
            r.dot(x, y, "moonl", max(0, tone), z)


def inhabit(i):
    r = Rig()
    rnd = random.Random(5)
    sparks = [(rnd.uniform(-5, 5), rnd.uniform(-60, -8), rnd.uniform(-14, 14), rnd.random()) for _ in range(12)]
    top = -84
    # the column: falls (0-1), lands and swells (2-3), thins away (4-7)
    if i == 0:
        column(r, 1, top, -46, True)
        spark(r, 0, -46, 2, mat="moonl", z=3.0)
    elif i <= 7:
        w = [0, 2, 5, 7, 6, 4, 2, 1][i]
        column(r, w, top, 0, i < 5, solid=i == 2)
        # the moon's face at the top of the shaft
        if i < 6: r.ell(0, top + 3, 3.0, 2.0, "moonl", 2.5, flat=4 if i < 4 else 3)
    # the ground flare where it lands
    if 1 <= i <= 4:
        fw = [0, 5, 10, 9, 6][i]
        r.ell(0, -1, fw, 2.0, "moonl", 2.6, flat=4 if i < 3 else 3)
    # the silver ring bursting out along the floor: two rows thick while it is young, breaking up as it spreads
    if 2 <= i <= 8:
        u = (i - 2) / 6.0
        rr = 7 + u * 25
        tone = 4 if u < 0.4 else 3 if u < 0.7 else 2
        keep = (lambda k, a: True) if u < 0.6 else (lambda k, a: k % 2 == 0) if u < 0.9 else (lambda k, a: k % 3 == 0)
        ring(r, 0, -1, rr, rr * 0.32, "moonl", tone, 2.8, n=72, keep=keep)
        if u < 0.7:
            ring(r, 0, -1, rr + 1, rr * 0.32 + 1, "moonl", tone - 1, 2.75, n=72, keep=keep)
            ring(r, 0, -1, rr - 2, (rr - 2) * 0.32, "moon", 3, 2.7, n=48, keep=lambda k, a: k % 2 == 0)
    # sparkles: caught in the shaft, then drifting down to settle round the feet and wink out
    if i >= 4:
        u = (i - 4) / 7.0
        for (x0, y0, x1, ph) in sparks:
            k = min(1.0, u * (1.2 + ph))
            x = x0 + (x1 - x0) * k
            y = y0 + (-1.5 - ph * 3 - y0) * (1 - (1 - k) ** 2)
            if i >= 10 and (ph * 10 + i) % 3 < 1.2: continue      # winking out
            if i == 11 and ph > 0.5: continue
            size = 2 if (i < 8 and ph < 0.35) else 1 if i < 10 else 0
            spark(r, x, y, size, mat="moonl", z=3.2)
    return done(r, INHABIT_LIFT)


def main():
    os.makedirs(OUT, exist_ok=True)
    sheet("FxSilverHalo", [("Halo", [halo(i) for i in range(HALO_N)], [0.1] * HALO_N)], OUT, cell=(44, 44), floor_max=1)
    sheet("FxSilverMark", [("Loop", [mark(i) for i in range(6)], [0.12] * 6)], OUT, cell=(18, 20), floor_max=1)
    sheet("FxSilverInhabit", [("Play", [inhabit(i) for i in range(12)], INHABIT_D)], OUT, cell=(72, 100), floor_max=1)


if __name__ == "__main__":
    main()
