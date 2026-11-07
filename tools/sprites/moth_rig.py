"""Ash Moth: flier with a 6-pose wing cycle drawn from wing polygons.
Moves: Dust Puff (ash cone), Moth to Flame (locked-on dive)."""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from anim import Spr, pack, preview
import scalekit as SK

HOVER_DROP_SMALL = 5   # design px the moth flies lower in small renders (hover counts toward the T1 limit)


def poly_fill(px, pts, fill, rim, spot=None):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    for y in range(int(min(ys)) - 1, int(max(ys)) + 2):
        for x in range(int(min(xs)) - 1, int(max(xs)) + 2):
            inside = False
            j = len(pts) - 1
            for i in range(len(pts)):
                xi, yi = pts[i]; xj, yj = pts[j]
                if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi):
                    inside = not inside
                j = i
            if inside:
                px[(x, y)] = fill
    # rim: pixels with an empty neighbour
    for (x, y), c in list(px.items()):
        if c == fill and any((x + dx, y + dy) not in px for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            px[(x, y)] = rim
    if spot:
        sx, sy = spot
        for dx, dy, c in ((0, 0, 'O'), (1, 0, 'o'), (0, 1, 'o'), (-1, 0, 'o'), (0, -1, 'o')):
            if (sx + dx, sy + dy) in px: px[(sx + dx, sy + dy)] = c


def wing(px, root, length, angle, spread, fill='g', rim='k', spot=True):
    """Wing as a quad fanned from the root; angle: direction of the wing tip (deg, -90 = up)."""
    a = math.radians(angle); s = spread  # spread already in radians
    rx, ry = root
    tip1 = (rx + length * math.cos(a - s), ry + length * math.sin(a - s))
    tip2 = (rx + length * 0.8 * math.cos(a + s), ry + length * 0.8 * math.sin(a + s))
    mid = (rx + length * 0.55 * math.cos(a), ry + length * 0.55 * math.sin(a))
    sub = {}
    outer = (rx + length * 1.05 * math.cos(a), ry + length * 1.05 * math.sin(a))
    poly_fill(sub, [(rx, ry), tip1, outer, tip2],
              fill, rim, spot=(int(round(mid[0])), int(round(mid[1]))) if spot else None)
    for k, v in sub.items():
        px.setdefault(k, v) if v == rim else px.__setitem__(k, v)


def moth(phase, lean=0, dive=False, body_dy=0, flare=False):
    """phase 0..5 wing cycle. Body is fixed; wings rotate around the shoulder."""
    px = {}
    K = SK.cur()   # design scale (v0.7): geometry is placed at K before rasterising
    up = [-115, -95, -60, -20, 10, -60][phase]
    drop = HOVER_DROP_SMALL if SK.small() else 0
    root = ((-1 + lean) * K, (-13 + body_dy + drop) * K)
    # far wing (darker, behind)
    wing(px, (root[0] + K, root[1]), 10 * K, up - 14, 0.75, fill='k', rim='K', spot=False)
    # body
    body = {}
    bx, by = SK.rnd(root[0] - 4 * K), SK.rnd(root[1] + K)
    nb = max(5, SK.rnd(9 * K))
    for i in range(nb):
        x = bx + i if not dive else bx + i
        y = by + (i // 3 if dive else 0)
        for dy in (-1, 0, 1):
            if i in (0, nb - 1) and dy != 0: continue
            body[(x, y + dy)] = 'i' if dy < 0 else 'h' if dy == 0 else 'g'
    for (x, y), c in body.items(): px[(x, y)] = c
    hx, hy = bx + nb, by + ((nb - 1) // 3 if dive else 0)
    for (dx, dy, c) in ((0, -1, 'i'), (1, -1, 'h'), (0, 0, 'h'), (1, 0, 'R'), (2, 0, 'r'), (0, 1, 'g'), (1, 1, 'g')):
        px[(hx + dx, hy + dy)] = c
    # antennae
    na = 3 if K > 0.85 else 2
    for k in range(1, na + 1):
        px[(hx + k, hy - 1 - k)] = 'w'
    px[(hx + na + 1, hy - na - 1)] = 'W'
    # legs dangling
    for lx in (bx + SK.rnd(3 * K), bx + SK.rnd(5 * K), bx + SK.rnd(7 * K)):
        px[(lx, by + 2)] = 'k'; px[(lx - 1, by + 3)] = 'k'
    # near wing on top
    wing(px, root, 12 * K, up, 0.8, fill='g', rim='k', spot=True)
    if flare:
        for (x, y), c in list(px.items()):
            if c in 'oO': px[(x, y)] = 'Y'
    if drop:   # flying lower: the dive can touch the floor, never go through it
        px = {k: v for k, v in px.items() if k[1] <= 0}
    return Spr(px)


def _floor(spr):
    """The moth fallen on the floor (old art: shifted 12 px down and clipped at the ground)."""
    d = SK.rnd(12 * SK.cur()) + (SK.rnd(HOVER_DROP_SMALL * SK.cur()) * -1 if SK.small() else 0)
    return Spr({(x, y + d): c for (x, y), c in spr.px.items() if y + d <= 0})


def build(outdir):
    idle = [moth(p, body_dy=[0, 0, 1, 1, 0, -1][p]) for p in range(6)]
    # v0.8: the run leans into the flight (it used to repeat three Idle frames)
    run = [moth(p, lean=2, body_dy=[0, 1, 1, 0, -1, -1][p]) for p in range(6)]
    puff = [moth(0, lean=-1), moth(1, lean=-1, body_dy=-1), moth(3, lean=1), moth(4, lean=2, flare=True), moth(5, lean=1), moth(2)]
    dive = [moth(0, body_dy=-2), moth(1, body_dy=-3, flare=True), moth(4, dive=True, lean=2, flare=True),
            moth(4, dive=True, lean=3, flare=True), moth(4, dive=True, lean=4, flare=True), moth(2, lean=2), moth(1)]
    death = [moth(3, body_dy=2, lean=-2, flare=True), moth(4, body_dy=4, dive=True), moth(4, body_dy=8, dive=True),
             _floor(moth(4, dive=True))]
    dead = [death[-1]]
    knock = [moth(1, lean=-3, body_dy=-1)]
    anims = [
        ("Idle", idle, [0.07] * 6), ("Run", run, [0.06] * 6), ("Dead", dead, [0.2]),
        ("Death", death, [0.08, 0.08, 0.08, 0.3]), ("Statue", [idle[0].stone()], [0.2]),
        ("Knockback", knock, [0.2]), ("Portrait", [idle[0]], [0.2]),
        ("Puff", puff, [0.07, 0.07, 0.06, 0.12, 0.08, 0.1]),
        ("Dive", dive, [0.1, 0.14, 0.05, 0.05, 0.05, 0.12, 0.1]),
    ]
    img, man = pack("AshMoth", anims, cell_w=40, cell_h=30, feet=(20, 28), outdir=outdir)
    preview(img, man, os.path.join(outdir, "AshMoth_preview.png"), scale=6)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "art/out"))
