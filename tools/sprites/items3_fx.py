"""Items wave 3: every world effect and indicator of src/CrawlFurther/Items/ItemPack3.cs.

    python3 tools/sprites/items3_fx.py         -> art/out_items3/FxItem3*.png|json|_preview.png + TIMING_items3.md

Same method as item_fx.py: each frame is drawn fresh from shaded primitives lit from the top-left, a 1 px dark
outline on solid things, glow pixels last. Every sheet's json carries "origin" [x, y]: the cell pixel placed on the
effect's spawn point by ItemArt.Place (pops spawned at the hero's feet have their origin on the feet row; hit sparks
spawned at a body's aim point have it in the middle of the burst). Indicators (ModStatus.Indicator) carry no origin:
head overlays sit with their cell bottom-centre just above the head, feet overlays two rows below the feet line.
"""
import math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from items3_icons import (Cv, hx, R, K, K2, ell, rect, line, line_pts, poly, outline, pick, write_sheet, OUT, BOARDS,  # noqa: E402
                          WOOD, IRON, GOLD, BONE, RED, PINK, TEAL, YEL, ORNG, LEAF, VIO, CREAM, CLOTH, GLASSC, STONE, FUR,
                          icon_cv)
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

TIMING = []
WHITE = hx("ffffff")


def sheet(name, cw, ch, origin, anims, note=""):
    """anims: [(anim, [Cv in cell coords], [durations])]."""
    frames, man = [], []
    for an, cvs, du in anims:
        assert len(cvs) == len(du), (name, an)
        idx = []
        for c in cvs:
            idx.append(len(frames)); frames.append(c.image(cw, ch))
        man.append((an, idx, du))
    write_sheet(name, frames, cw, ch, man, origin=origin, cols=min(8, len(frames)))
    TIMING.append("## %s  (cell %dx%d%s)\n%s\n%s\n" % (name, cw, ch, (", origin %d,%d" % tuple(origin)) if origin else "", note,
                  "\n".join("- %s: %d frames, %.2f s: %s" % (an, len(idx), sum(du), ", ".join(str(d) for d in du)) for an, idx, du in man)))
    return frames


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def dot(c, x, y, col, r=0):
    if r <= 0:
        c.put(x, y, col); return
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        c.put(x + dx, y + dy, col)


def star(c, x, y, col, core=WHITE, size=1):
    for k in range(1, size + 1):
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            c.put(x + dx, y + dy, col)
    c.put(x, y, core)


def ringpts(cx, cy, rx, ry, step=8):
    pts = set()
    n = max(16, int(2 * math.pi * max(rx, ry) * 1.5))
    for i in range(n):
        a = 2 * math.pi * i / n
        pts.add((int(round(cx + rx * math.cos(a))), int(round(cy + ry * math.sin(a)))))
    return pts


# ============================================================================================ potions: quaff bursts
QUAFF = {   # anim: (light, mid, dark) of the brew
    "Marrow": ("b4ba7a", "7f8351", "48552a"),
    "Wyrm": ("ff8a5a", "d03a2a", "6a1018"),
    "Hare": ("d8fff0", "8ee0c8", "4a9688"),
    "Grog": ("f0c890", "b86a34", "6a2c14"),
    "Stone": ("d0cec8", "9a9890", "56544e"),
    "Quick": ("ffffff", "c8d0dc", "7a8494"),
    "Chaos": ("e0a0ff", "8a48c0", "4a1a6e"),
    "Heart": ("fff6d0", "ffd060", "b07a1c"),
}


def quaff(anim, f, n=8):
    """The brew's bubbles rise around the hero and pop, with a ring of droplets at the feet (origin = feet)."""
    L, M, D = (hx(x) for x in QUAFF[anim])
    c = Cv()
    t = f / (n - 1)
    rnd = random.Random(hash(anim) & 0xffff)
    # foot ring: splashes out and fades in the first half
    if f < 5:
        rx = 6 + f * 2.6; ry = 1.6 + f * 0.4
        for (x, y) in ringpts(16, 36, rx, ry):
            if (x + y + f) % 3 == 0 and f > 1: continue
            c.put(x, y, L if f == 0 else M if f < 3 else D)
        for (x, y) in ringpts(16, 36, max(1, rx - 2.5), max(0.6, ry - 0.8)):
            if (x * 7 + y) % 4 == 0: c.put(x, y, L)
    # rising bubbles: 9 of them on their own paths
    for i in range(9):
        bx = 6 + rnd.random() * 20
        start = rnd.random() * 0.3 - (0.12 if i < 3 else 0)
        speed = 18 + rnd.random() * 14
        tt = t - start
        if tt < 0 or tt > 0.75: continue
        y = 36 - tt * speed * 1.6
        x = bx + math.sin(tt * 9 + i) * 1.6
        r = 0.6 + (1.4 if i % 3 == 0 else 0.7) * (1 - abs(tt - 0.35))
        if tt > 0.62:
            # pop: four specks
            for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)): c.put(x + dx * 2, y + dy * 2, L)
            continue
        if r < 1.0:
            c.put(x, y, L); c.put(x + 1, y, M)
        else:
            for (px, py) in ringpts(x, y, r + 0.4, r + 0.4):
                c.put(px, py, M)
            c.put(x - 0.6, y - 0.6, WHITE if anim != "Heart" else hx("fffbe8"))
    # the swallow: a bright gulp-flash at the mouth line on the first frames
    if f in (0, 1):
        star(c, 16, 22, L, core=WHITE, size=2 - f)
    return c


# ================================================================================= chaos roll: which stat moved
GLYPH = {
    "V": ([".##.##.", "#######", "#######", ".#####.", "..###..", "...#..."], hx("e0503a")),   # heart
    "S": (["......#", ".....##", "#...##.", ".#.##..", "..##...", ".#.#...", "#......"], hx("f08a26")),   # sword
    "D": (["...#...", "...##..", "#.####.", "#.#####", "#.####.", "...##..", "...#..."], hx("7fd36a")),   # wing / arrow
}


def glyph(c, ch, x0, y0, tone=1.0):
    rows, col = GLYPH[ch]
    g = Cv()
    for y, r in enumerate(rows):
        for x, v in enumerate(r):
            if v == "#":
                light = lerp(col, WHITE, 0.35) if (x + y) < 4 else col
                g.put(x0 + x, y0 + y, lerp(light, (40, 30, 34), 1 - tone))
    c.merge(outline(g))


def arrow(c, x0, y0, up, tone=1.0):
    col = hx("8cf07a") if up else hx("ff6a5a")
    g = Cv()
    rows = ["..#..", ".###.", "#####", "..#..", "..#.."] if up else ["..#..", "..#..", "#####", ".###.", "..#.."]
    for y, r in enumerate(rows):
        for x, v in enumerate(r):
            if v == "#": g.put(x0 + x, y0 + y, lerp(col, (40, 30, 34), 1 - tone))
    c.merge(outline(g))


def chaos_roll(up, down, f):
    """+2 stat (green arrow + glyph) on the left, -1 stat (red arrow + glyph) on the right, rising over the head."""
    c = Cv()
    lift = [6, 3, 1, 0, 0, -1, -2][f]
    tone = [0.6, 1, 1, 1, 1, 0.75, 0.45][f]
    y = 14 + lift
    arrow(c, 2, y + 1, True, tone); glyph(c, up, 8, y, tone)
    arrow(c, 19, y + 1, False, tone); glyph(c, down, 25, y, tone)
    if f in (1, 2):
        for x, yy in ((4, y - 3), (16, y - 2), (30, y - 3)): c.put(x, yy, hx("fff8c4"))
    return c


# ========================================================================================== tally notches pop
def tally_pop(n, f):
    c = Cv()
    lift = [5, 2, 0, 0, 0, -1, -2][f]
    tone = [0.6, 1, 1, 1, 1, 0.75, 0.5][f]
    y0 = 8 + lift
    s = Cv()
    for x in range(1, 19):
        s.put(x, y0 + 1, pick(WOOD, 0.6)); s.put(x, y0 + 2, pick(WOOD, 0.1)); s.put(x, y0 + 3, pick(WOOD, -0.4))
    s = outline(s)
    for k in range(n):
        x = 3 + k * 3
        col = K if k < n - 1 or f > 2 else hx("fff0a0")
        s.put(x, y0 + 1, col); s.put(x, y0 + 2, col)
    if n == 5:
        for k in range(4): s.put(3 + k * 3.2, y0 + 3 - k * 0.7, RED[2])
    for (x, y), v in s.px.items():
        c.put(x, y, lerp(v, (40, 30, 34), 1 - tone))
    if f in (1, 2, 3):
        star(c, 3 + (n - 1) * 3, y0 - 2, hx("fff0a0"))
    return c


# ================================================================================================ party hat + confetti
CONF = [PINK[3], TEAL[3], YEL[3], hx("8cf07a"), ORNG[3], hx("b48ae8")]


def confetti(f, n=10):
    """Burst of confetti from the body's middle (origin 20,24), pieces flutter down and spin."""
    c = Cv()
    rnd = random.Random(7)
    t = f / (n - 1)
    for i in range(22):
        a = rnd.random() * math.pi * 2
        v = 9 + rnd.random() * 13
        x = 20 + math.cos(a) * v * min(1.0, t * 2.2)
        y = 22 + math.sin(a) * v * 0.7 * min(1.0, t * 2.2) - 8 * t + 30 * t * t
        if y > 39: continue
        col = CONF[i % len(CONF)]
        if t > 0.75 and i % 3 == f % 3: continue                 # thins out at the end
        spin = (f + i) % 3
        if spin == 0: c.put(x, y, col); c.put(x + 1, y, col)
        elif spin == 1: c.put(x, y, col); c.put(x, y + 1, col)
        else: c.put(x, y, col)
    if f < 2:
        star(c, 20, 22, YEL[4], size=2 if f == 0 else 1)
    return c


def hat_frame(f):
    """The Party Hat worn on the head, sized to the hero's 4-5 px head: a 7 px striped cone with a gold pompom,
    tilting a pixel as it bobs (cell 12x12, the brim on the bottom row)."""
    c = Cv()
    tilt = [0, 0, 1, 0][f]
    g = Cv()
    poly(g, [(3, 10.6), (9.6, 10.6), (6.6 + tilt, 3)], PINK)
    for (x, y) in list(g.px):
        if (x + y * 2) % 5 in (0, 1): g.px[(x, y)] = TEAL[3] if x < 6 else TEAL[2]
    for x in range(3, 10): g.put(x, 10, GOLD[2] if x < 7 else GOLD[1])
    g = outline(g)
    ell(g, 6.6 + tilt, 2.2, 1.2, 1.2, YEL, spec=YEL[4])
    g = outline(g)
    c.merge(g)
    if f in (1, 3):
        c.put(1, 4 + f % 2, CONF[f]); c.put(11, 6, CONF[(f + 2) % len(CONF)])
    return c

# ================================================================================================= bard's lute token
def lute_token(state, f):
    """Follower token (cell 14x16, origin 7,14): the lute hovering, strings shimmering; Activate strums."""
    c = Cv()
    bob = [0, 0, -1, -1, -1, 0, 0, 1, 1, 1, 0, 0][f % 12] if state in ("Idle", "Ready") else 0
    grey = state == "Wait"
    wood = R("2e2a2c", "46424a", "5e5a62", "76727a", "8e8a92") if grey else WOOD
    oy = bob
    # neck up-right
    for i in range(6):
        c.put(8 + i * 0.8, 6 - i + oy, wood[1]); c.put(9 + i * 0.8, 6 - i + oy, wood[2])
    c.put(13, 0 + oy, wood[3])
    ell(c, 6.0, 9.5 + oy, 4.2, 3.8, wood, spec=wood[4], ang=-35)
    ell(c, 6.2, 9.3 + oy, 1.1, 1.1, [K2, K2, K, K])
    c = outline(c)
    strum = state == "Activate" and f in (2, 3, 4)
    for i in range(5):
        col = hx("fff6c0") if strum and (i + f) % 2 == 0 else (CREAM[3] if not grey else hx("8a8a90"))
        c.put(7 + i * 0.9, 9 - i + oy + (1 if strum and i % 2 else 0), col)
    if state == "Activate" and f == 3:
        for x, y in ((1, 3), (2, 2), (12, 10), (13, 11)): c.put(x, y, YEL[4])
        star(c, 7, 9 + oy, YEL[4])
    if state == "Ready" and f == 1:
        c.put(2, 3, YEL[3])
    if state == "WakeUp":
        for (x, y) in ringpts(7, 9, 2 + f * 1.6, 2 + f * 1.4):
            if 0 <= x < 14 and 0 <= y < 16: c.put(x, y, YEL[3] if f < 2 else YEL[2], over=False)
    return c


def note(anim, f):
    """The strummed note (cell 14x16, origin 7,9): a golden quaver bobbing with a little glow trail."""
    c = Cv()
    if anim == "Fly":
        bob = [0, -1, 0, 1][f]
        g = Cv()
        ell(g, 5.5, 11.0 + bob, 2.2, 1.7, YEL, spec=YEL[4], ang=-20)
        for y in range(3 + bob, 11 + bob): g.put(7, y, YEL[2])
        g.put(8, 3 + bob, YEL[3]); g.put(9, 4 + bob, YEL[3]); g.put(10, 5 + bob, YEL[2]); g.put(10, 6 + bob, YEL[1])
        c.merge(outline(g))
        for k in range(3):
            c.put(1 + k, 9 + bob + (k + f) % 2, lerp(YEL[3], (60, 50, 40), 0.3 * (3 - k)), over=False)
    else:
        r = 1 + f * 1.4
        for (x, y) in ringpts(7, 9, r, r * 0.9):
            if (x + y + f) % 2 == 0: c.put(x, y, YEL[3] if f < 3 else YEL[1])
        if f < 2: star(c, 7, 9, YEL[4])
        if f in (2, 3):
            for x, y in ((3, 3), (11, 4), (12, 13)): c.put(x, y, hx("fff6c0"))
    return c


# ================================================================================================= pet ferret
def ferret(anim, f):
    """A brown ferret with a cream mask, facing right (cell 24x14, feet at 12,12)."""
    c = Cv()
    if anim == "Idle":
        body_y = 9.0 + (0 if f in (0, 1) else 0.4)
        head = (17.5, 6.6 + (0 if f != 2 else -0.6))
        tail = [(4, 7), (3, 6), (2, 6)] if f < 2 else [(4, 7), (3, 7), (2, 6)]
        legs = [(8, 11), (10, 11), (14, 11), (16, 11)]
    else:
        ph = f / 6.0 * 2 * math.pi
        body_y = 8.6 + 0.8 * abs(math.sin(ph))                         # the ferret's bouncing lope
        head = (18.0, 6.4 + 0.8 * abs(math.sin(ph + 0.6)))
        tail = [(4, 7 + round(math.sin(ph))), (3, 6 + round(math.sin(ph))), (2, 6)]
        s = math.sin(ph)
        legs = [(8 + s * 1.5, 11), (10 - s * 1.5, 11), (14 + s * 1.5, 11), (16 - s * 1.5, 11)]
    g = Cv()
    ell(g, 11.5, body_y, 6.6, 2.4, FUR, spec=FUR[4])
    ell(g, head[0], head[1], 3.0, 2.4, FUR, spec=FUR[4])
    for x, y in tail: g.put(x, y, FUR[1])
    for x, y in legs: g.put(x, y, FUR[1]); g.put(x, y - 1, FUR[1])
    g.put(head[0] - 1, head[1] - 2.6, FUR[3]); g.put(head[0] + 0.6, head[1] - 2.6, FUR[2])   # ears
    ell(g, head[0] + 1.6, head[1] + 0.8, 1.6, 1.0, CREAM)
    for x in range(8, 16): g.put(x, int(body_y) + 2, FUR[1], over=False)
    c.merge(outline(g))
    hx0, hy0 = int(round(head[0])), int(round(head[1]))
    c.put(hx0 + 1, hy0 - 1, FUR[0]); c.put(hx0, hy0 - 1, FUR[0])                        # mask band
    blink = anim == "Idle" and f == 3
    c.put(hx0 + 1, hy0 - 1, FUR[0] if blink else K)
    c.put(hx0 + 4, hy0 + 1, K)                                                          # nose
    for x in range(7, 17, 3): c.put(x, int(body_y) - 1, FUR[3])                         # fur sheen
    return c


# ====================================================================================================== bubble pipe
def bubble(anim, f):
    """A soap bubble (cell 14x14, origin 7,7): a thin teal-violet rim with a white glint, wobbling as it drifts."""
    c = Cv()
    if anim == "Fly":
        rx, ry = [(4.4, 4.0), (4.2, 4.2), (4.0, 4.4), (4.2, 4.2)][f]
        rim = ringpts(7, 7, rx, ry)
        for (x, y) in rim:
            a = math.atan2(y - 7, x - 7)
            c.put(x, y, lerp(TEAL[3], hx("d090ff"), (math.sin(a * 2 + f) + 1) / 2))
        c.put(5, 4, WHITE); c.put(4, 5, hx("e6fffa")); c.put(9, 9, TEAL[2])
        for (x, y) in ringpts(7, 7, rx - 1, ry - 1):
            if (x + y + f) % 4 == 0: c.put(x, y, hx("2a5058"), over=False)
    else:
        r = 4 + f * 1.3
        for i in range(8):
            a = i * math.pi / 4 + f * 0.2
            x, y = 7 + math.cos(a) * r, 7 + math.sin(a) * r
            c.put(x, y, TEAL[3] if f < 3 else TEAL[1])
            if f < 2: c.put(7 + math.cos(a) * (r - 1.5), 7 + math.sin(a) * (r - 1.5), WHITE)
        if f == 0: star(c, 7, 7, WHITE)
    return c


# ====================================================================================================== rubber duck
def duck_ring(f, n=6):
    """Squeak ring on the floor (cell 88x40, origin 44,22: 80 x 34 hitbox), a duck head pops up in the middle."""
    c = Cv()
    t = f / (n - 1)
    rx, ry = 10 + t * 30, 4 + t * 12
    col = lerp(YEL[4], YEL[1], t)
    for (x, y) in ringpts(44, 22, rx, ry):
        c.put(x, y, col)
    if f < 4:
        for (x, y) in ringpts(44, 22, rx * 0.72, ry * 0.72):
            if (x + y) % 2 == 0: c.put(x, y, lerp(YEL[3], YEL[1], t))
    # squeak lines over the duck
    if f < 4:
        for k, (dx, dy) in enumerate(((-6, -10), (0, -12), (6, -10))):
            line(c, 44 + dx, 22 + dy - f, 44 + dx * 1.3, 22 + dy - 3 - f, hx("fff8c4"))
    # little duck head
    if f < 5:
        dy = [4, 0, -1, 0, 2][f]
        g = Cv()
        ell(g, 44.0, 14.0 + dy, 3.0, 2.8, YEL, spec=YEL[4])
        g.put(47, 14 + dy, ORNG[2]); g.put(48, 14 + dy, ORNG[2]); g.put(47, 15 + dy, ORNG[1])
        g = outline(g)
        g.put(45, 13 + dy, K)
        c.merge(g)
    return c


# ====================================================================================================== firefly jar
def firefly(anim, f):
    """One firefly (cell 12x12, origin 6,6): Glow (bright, pulsing), Dim (resting), Zap (a spark on the monster)."""
    c = Cv()
    if anim == "Glow":
        k = [1.0, 0.8, 0.6, 0.8][f]
        core = lerp(hx("fffbb0"), hx("d8e060"), 1 - k)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)): c.put(6 + dx, 6 + dy, lerp(hx("b8d040"), hx("6a7a20"), 1 - k))
        if k > 0.75:
            for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)): c.put(6 + dx, 6 + dy, hx("6a7a20"))
        c.put(6, 6, core)
        c.put(5, 4, hx("c8d8e8")); c.put(7, 4, hx("c8d8e8"))                       # wings
    elif anim == "Dim":
        c.put(6, 6, hx("8a9040")); c.put(5, 5, hx("4a4a2a")); c.put(7, 5 + f, hx("4a4a2a"))
    else:
        r = 1 + f
        for i in range(6):
            a = i * math.pi / 3 + f * 0.4
            line(c, 6, 6, 6 + math.cos(a) * r, 6 + math.sin(a) * r, hx("fffbb0") if f < 2 else hx("b8d040"))
        if f < 3: star(c, 6, 6, WHITE)
    return c


# ================================================================================================= dancing shoes
def dance_step(f):
    """A sparkly footprint left on the floor while dancing (cell 16x12, origin 8,10)."""
    c = Cv()
    tone = [1, 1, 0.8, 0.6, 0.4, 0.2][f]
    pr = [(6, 9), (7, 9), (8, 9), (9, 9), (7, 10), (8, 10), (6, 8), (9, 8)]
    for x, y in pr: c.put(x, y, lerp(PINK[3], (60, 40, 50), 1 - tone))
    sp = [(4, 6 - f), (11, 5 - f), (8, 3 - f)]
    for i, (x, y) in enumerate(sp):
        if (i + f) % 2 == 0 and y >= 0: star(c, x, y, lerp(hx("fff8c4"), (80, 70, 60), 1 - tone), core=lerp(WHITE, (90, 80, 70), 1 - tone))
    return c


# ========================================================================================================= whetstone
def whet_spark(f):
    """Bright sharpened-edge spark on the first hit (cell 20x20, origin 10,10)."""
    c = Cv()
    L = [6, 8, 7, 4, 2][f]
    col = [WHITE, YEL[4], YEL[3], ORNG[3], ORNG[2]][f]
    line(c, 10 - L, 10 + L * 0.6, 10 + L, 10 - L * 0.6, col)
    line(c, 10 - L * 0.5, 10 - L * 0.5, 10 + L * 0.5, 10 + L * 0.5, IRON[4] if f < 3 else IRON[2])
    if f < 3: star(c, 10, 10, WHITE, size=2 if f == 1 else 1)
    for k in range(3):
        a = k * 2.1 + f
        c.put(10 + math.cos(a) * (L + 1), 10 + math.sin(a) * (L + 1), YEL[3])
    return c


# ========================================================================================================= phoenix
def phoenix(f, n=10):
    """The feather burns and a firebird rises from the hero (cell 48x56, origin 24,52)."""
    c = Cv()
    t = f / (n - 1)
    # flame column
    rnd = random.Random(f * 13 + 5)
    h = 10 + t * 30
    for y in range(int(52 - h), 53):
        u = (52 - y) / max(1, h)
        w = (1 - u) * (6 + 4 * math.sin(t * 3)) * (1 - t * 0.5)
        for x in range(int(24 - w), int(24 + w) + 1):
            if rnd.random() < 0.25 + 0.5 * (1 - u): continue
            l = 0.8 - abs(x - 24) / max(1, w) * 0.9 - u * 0.5
            c.put(x, y, pick([RED[1], RED[2], ORNG[2], ORNG[3], YEL[3], YEL[4]], l))
    # wings spreading from the body
    if f >= 2:
        span = min(1.0, (f - 2) / 4.0)
        cy = 30 - t * 10
        for side in (-1, 1):
            for k in range(12):
                x = 24 + side * (3 + k * 1.6 * span)
                y = cy - math.sin(k / 11 * math.pi) * 8 * span + k * 0.4
                depth = int(2 + (11 - k) * 0.45 * span)                       # feathers hang deeper near the body
                for d in range(depth + 1):
                    col = [YEL[3], ORNG[3], ORNG[2], RED[2], RED[1]][min(4, d * 5 // (depth + 1))]
                    if (k + d + f) % 5 == 0 and d > 1: continue                 # ragged flame edge
                    c.put(x, y + d, col)
                c.put(x, y - 1, YEL[4] if k % 3 == 0 else ORNG[3])
        # head
        ell(c, 24, cy - 3, 2, 2, [ORNG[2], ORNG[3], YEL[3], YEL[4]])
        c.put(26, cy - 3, YEL[4])
    if f < 3:
        star(c, 24, 40, WHITE, size=2)
    if f > 6:
        for k in range(6):
            c.put(18 + k * 2.4, 12 + ((k * 5 + f) % 9), YEL[3] if k % 2 else ORNG[3])
    return c


# ============================================================================================================ siphon
def siphon(f, n=8):
    """A violet wisp spirals down into the hero (cell 24x36, origin 12,34)."""
    c = Cv()
    t = f / (n - 1)
    for k in range(5):
        tt = t - k * 0.06
        if tt < 0 or tt > 0.95: continue
        a = tt * 9
        r = 9 * (1 - tt)
        x = 12 + math.cos(a) * r
        y = 6 + tt * 22
        col = lerp(hx("e6d2ff"), VIO[1], k / 5)
        dot(c, x, y, col, r=1 if k < 2 else 0)
        if k == 0: c.put(x, y, WHITE)
    if f >= n - 3:
        for (x, y) in ringpts(12, 28, 3 + (f - n + 3) * 2, 2 + (f - n + 3)):
            c.put(x, y, VIO[3])
        star(c, 12, 28, hx("e6d2ff"))
    return c


# ============================================================================================================= fork
def fork_heal(f, n=7):
    """Extra helping: little red hearts and crumbs rise off the hero (cell 24x32, origin 12,30)."""
    c = Cv()
    t = f / (n - 1)
    hearts = [(6, 0.0), (17, 0.15), (11, 0.3)]
    for hx0, st in hearts:
        tt = t - st
        if tt < 0 or tt > 0.8: continue
        y = 26 - tt * 26
        tone = 1 - max(0, tt - 0.5) * 2
        col = lerp(hx("ff6a5a"), (70, 30, 34), 1 - tone)
        for dx, dy in ((0, 0), (1, 0), (-1, -1), (2, -1), (0, 1), (1, 1), (0, -1), (1, -1)):
            c.put(hx0 + dx, y + dy, col)
        c.put(hx0, y - 1, lerp(hx("ffc0b0"), (70, 30, 34), 1 - tone))
    for k in range(4):
        tt = t - k * 0.1
        if 0 < tt < 0.7: c.put(4 + k * 5, 28 - tt * 18, hx("e8c070"))
    return c


# ============================================================================================================= coin
def coin(face, f, n=12):
    """A coin flips up over the head and lands on its face (cell 20x48, origin 10,46)."""
    c = Cv()
    t = f / (n - 1)
    y = 30 - math.sin(min(1.0, t * 1.4) * math.pi) * 18 - (t > 0.7) * 0
    if f >= 8: y = 14 - (f - 8) * 0.5
    spin = f < 8
    w = abs(math.cos(f * 1.3)) * 4.4 + 0.8 if spin else 4.4
    g = Cv()
    ramp = GOLD if face == "Heads" else R("3a3a44", "6c6a74", "a4a2ac", "d4d2dc", "f4f4fc")
    ell(g, 10, y, w, 4.4, ramp, spec=ramp[4])
    g = outline(g)
    if not spin:
        if face == "Heads":     # crown
            for x, yy in ((7, 1), (8, 1), (9, 1), (10, 1), (11, 1), (12, 1), (13, 1), (7, 0), (10, 0), (13, 0), (7, -1), (10, -1), (13, -1)):
                g.put(x - 0.5, y + yy, GOLD[0])
        else:                   # wing
            for x, yy in ((7, 1), (8, 0), (9, 0), (10, -1), (11, -1), (12, -2), (8, 1), (10, 0), (12, -1)):
                g.put(x, y + yy, ramp[0])
        star(g, 13, int(y) - 3, WHITE)
    c.merge(g)
    if f == 8:
        for x, yy in ((3, -4), (17, -4), (2, 2), (18, 2)): c.put(x, y + yy, hx("fff6c0") if face == "Heads" else hx("e0f0ff"))
    return c


# ========================================================================================================= bandage
def bandage_absorb(f, n=7):
    """Linen wraps flash round the hero's body as the hit is halved (cell 32x36, origin 16,34)."""
    c = Cv()
    t = f / (n - 1)
    for k in range(3):
        y = 30 - k * 7 - t * 2
        rx = 8 + t * 4 - k
        tone = 1 - t * 0.8
        for (x, yy) in ringpts(16, y, rx, 2.2):
            if yy < y and (x + f) % 3 == 0: continue              # the back half is broken (behind the hero)
            col = lerp(CLOTH[4], CLOTH[1], 1 - tone)
            c.put(x, yy, col)
    if f < 3:
        for x, y in ((16, 12), (16, 13), (15, 13), (17, 13), (16, 14)): c.put(x, y, RED[3])
        star(c, 22, 14, WHITE)
    return c


# ============================================================================================================ boots
def boots_clank(f):
    """Iron boots plant themselves: grey grit kicks up and sparks fly at the heels (cell 28x12, origin 14,10)."""
    c = Cv()
    for i in range(7):
        a = math.pi * (0.08 + 0.84 * i / 6)
        r = 3 + f * 2.4
        x, y = 14 - math.cos(a) * r * 1.6, 10 - math.sin(a) * r * 0.7
        dot(c, x, y, STONE[4] if f < 2 else STONE[3] if f < 4 else STONE[1], r=1 if f < 2 and i % 2 == 0 else 0)
    if f < 3:
        star(c, 10, 9, YEL[4], size=1 + (f == 0)); star(c, 18, 9, WHITE, size=1)
    if f < 4:
        line(c, 7, 11, 21, 11, IRON[3] if f < 2 else IRON[2])
        line(c, 9, 10, 19, 10, IRON[1])
    return c

# ============================================================================================================== key
def key_frames(anim, f):
    """Skeleton Key on the floor (Lie) and its collect sparkle (cell 28x28, origin 14,22)."""
    c = Cv()
    if anim == "Lie":
        k = icon_cv("SkeletonKey", 0)
        # lie it on the floor: icon 16x16 drawn with its bottom on row 23
        c.merge(k.shift(6, 8))
        # soft blue shimmer around it so a sharp eye spots it; glint every 8 frames
        if f in (0, 1):
            star(c, 8 + f * 2, 9, hx("e8f4ff"), size=1 + (f == 0))
        if f == 4:
            c.put(20, 14, hx("c8d8ff"))
        for x in range(9, 21): c.put(x, 24, hx("2c3040"), over=False)                   # contact shadow
    else:
        t = f / 5.0
        for i in range(8):
            a = i * math.pi / 4
            r = 3 + t * 9
            star(c, 14 + math.cos(a) * r, 16 + math.sin(a) * r * 0.8, hx("c8e0ff") if f < 4 else hx("6a7aa0"), core=WHITE if f < 3 else hx("a0b0d0"))
        if f < 2: star(c, 14, 16, WHITE, size=2)
    return c


def heart_frames(anim, f):
    """Gilded Heart on the floor (Lie), collected (Collect), and its golden beat at each fight start (Beat)."""
    c = Cv()
    if anim == "Lie":
        h = icon_cv("GildedHeart", 1 if f in (2, 3) else 0)
        c.merge(h.shift(8, 20))
        if f == 0: star(c, 21, 21, WHITE)
        for x in range(10, 23): c.put(x, 36, hx("3a2c18"), over=False)
    elif anim == "Collect":
        t = f / 5.0
        for i in range(10):
            a = i * math.pi / 5
            r = 3 + t * 12
            star(c, 16 + math.cos(a) * r, 26 + math.sin(a) * r * 0.8, YEL[4] if f < 4 else GOLD[2], core=WHITE if f < 3 else YEL[3])
        if f < 2: star(c, 16, 26, WHITE, size=2)
    else:
        # Beat: a golden pulse ring rises off the hero, two heart flashes
        t = f / 6.0
        for (x, y) in ringpts(16, 34, 6 + t * 10, 2 + t * 3):
            c.put(x, y, lerp(YEL[4], GOLD[1], t))
        if f in (1, 2, 4):
            h = icon_cv("GildedHeart", 0).shift(8, 6 - f)
            c.merge(h)
    return c


# ====================================================================================================== indicators
def ind_sluggish(f):
    """Troll Marrow: brown-green sludge dripping off the legs (feet overlay, cell 24x12)."""
    c = Cv()
    for x in range(5, 20):
        y = 9 + (1 if (x + f) % 4 == 0 else 0)
        c.put(x, y, hx("5a5a2a") if x % 3 else hx("7f8351"))
    for k, x in enumerate((7, 12, 17)):
        y0 = 3 + ((f + k * 2) % 4) * 1.5
        c.put(x, y0, hx("9aa064")); c.put(x, y0 + 1, hx("6e7a3a"))
        if (f + k) % 4 == 3: c.put(x, 8, hx("b4ba7a"))
    return c


def ind_burn(f):
    """Wyrm Blood: little dragon-fire licks round the hero's legs (feet overlay, cell 24x20)."""
    c = Cv()
    rnd = random.Random(f * 31 + 1)
    for k, x in enumerate((6, 10, 14, 18)):
        h = 4 + ((f + k * 3) % 4) * 1.6
        for y in range(int(18 - h), 18):
            u = (18 - y) / h
            c.put(x + (1 if (y + f + k) % 3 == 0 else 0), y, pick([RED[1], RED[2], ORNG[2], ORNG[3], YEL[3]], 0.7 - u * 1.4))
            if u < 0.4: c.put(x + 1, y, RED[2])
    for k in range(2):
        c.put(5 + rnd.random() * 14, 2 + rnd.random() * 6, ORNG[3])
    return c


def ind_shaky(f):
    """Hare's Dew: shaky hands, sweat drops flicking off both sides of the head (head overlay, cell 18x10)."""
    c = Cv()
    for side in (-1, 1):
        x = 9 + side * (4 + (f % 2))
        y = 5 + (f % 4) * 0.7
        c.put(x, y, hx("a8e0ff")); c.put(x, y + 1, hx("78b0e0"))
        if f % 2: c.put(x + side, y - 1, hx("e6f8ff"))
    for x in (6, 9, 12):
        c.put(x + (1 if f % 2 else -1) * (x == 9), 1 + (x == 9), hx("78c8b4"))
    return c


def ind_key(f):
    """Skeleton Key carried: the key hangs on a cord at the hip and glints now and then (feet overlay, cell 24x16)."""
    c = Cv()
    sway = [0, 0, 1, 1, 0, 0, -1, -1][f]
    g = Cv()
    line(g, 17, 4, 17 + sway, 6, CLOTH[1])
    ell(g, 17.5 + sway, 8.0, 1.6, 1.5, BONE)
    for y in range(9, 14): g.put(17 + sway, y, BONE[2])
    g.put(18 + sway, 12, BONE[2]); g.put(18 + sway, 13, BONE[1])
    c.merge(outline(g))
    c.put(17 + sway, 8, K)
    if f == 2: star(c, 19 + sway, 7, hx("e8f4ff"))
    return c


def ind_bandage(f):
    """Patchwork Bandage armed: a little linen roll with a red cross over the head (head overlay, cell 12x10)."""
    c = Cv()
    bob = [0, 0, -1, -1][f]
    g = Cv()
    rect(g, 2, 2 + bob, 9, 7 + bob, CLOTH)
    for x, y in ((5, 3), (6, 3), (4, 4), (5, 4), (6, 4), (7, 4), (5, 5), (6, 5), (5, 6), (6, 6)):
        pass
    c.merge(outline(g))
    for x, y in ((5, 3), (6, 3), (4, 4), (5, 4), (6, 4), (7, 4), (5, 5), (6, 5)):
        c.put(x, y + bob, RED[2])
    c.put(3, 2 + bob, CLOTH[4])
    return c


def wanted_mark(f):
    """Wanted Poster: a red crosshair pinned over the marked monster's head, slowly turning (head overlay, cell 15x15)."""
    c = Cv()
    r = 4.0 + [0, 0.4, 0.8, 0.4][f]
    for (x, y) in ringpts(7, 7, r, r):
        a = math.degrees(math.atan2(y - 7, x - 7)) % 90
        if 25 < a < 65: continue
        c.put(x, y, hx("ff4a3a"))
    o = Cv(); o.px = dict(c.px); c = outline(o, col=hx("3a0e10"))
    for d in (1, 2):
        for dx, dy in ((d, 0), (-d, 0), (0, d), (0, -d)):
            pass
    for (x, y) in ((7, 1), (7, 2), (7, 12), (7, 13), (1, 7), (2, 7), (12, 7), (13, 7)):
        c.put(x, y, hx("ff7a5a"))
    for (x, y) in ((7, 3), (7, 11), (3, 7), (11, 7)):
        c.put(x, y, hx("ff7a5a"))
    c.put(7, 7, hx("ffd0a0") if f % 2 == 0 else hx("ff4a3a"))
    return c


def ind_heart(f):
    """Gilded Heart carried: gold motes rise round the feet (feet overlay, cell 24x14)."""
    c = Cv()
    for k in range(4):
        x = 5 + k * 5
        y = 12 - ((f * 2 + k * 3) % 10)
        if y < 2: continue
        c.put(x, y, YEL[4] if (f + k) % 3 == 0 else GOLD[2])
    return c


# ============================================================================================================ build
def build():
    os.makedirs(OUT, exist_ok=True)
    TIMING.append("# Items wave 3 world art (tools/sprites/items3_fx.py)\n\nOrigin = the cell pixel ItemArt.Place puts on the "
                  "spawn point. Feet pops spawn at the hero's feet; hit sparks at the body's aim point.\n")
    sheet("FxItem3Quaff", 32, 40, (16, 38), [(a, [quaff(a, f) for f in range(8)], [0.06, 0.06, 0.07, 0.07, 0.08, 0.08, 0.09, 0.1])
                                             for a in QUAFF], "A potion is drunk: its brew bubbles up round the hero (spawned at the feet).")
    sheet("FxItem3ChaosRoll", 36, 48, (18, 46), [(u + d, [chaos_roll(u, d, f) for f in range(7)], [0.06, 0.06, 0.1, 0.3, 0.4, 0.15, 0.15])
                                                 for u, d in (("V", "S"), ("V", "D"), ("S", "V"), ("S", "D"), ("D", "V"), ("D", "S"))],
          "Chaos Brew: which stat went up 2 (green arrow) and which down 1 (red), over the head (art 14-26 px above the feet).")
    sheet("FxItem3Tally", 20, 44, (10, 42), [(nm, [tally_pop(n, f) for f in range(7)], [0.06, 0.06, 0.1, 0.25, 0.3, 0.12, 0.12])
                                             for n, nm in enumerate(("One", "Two", "Three", "Four", "Five"), 1)],
          "Tally Stick: a new notch is carved (over the head).")
    sheet("FxItem3Confetti", 40, 40, (20, 24), [("Burst", [confetti(f) for f in range(10)], [0.04, 0.05, 0.06, 0.07, 0.08, 0.08, 0.09, 0.1, 0.1, 0.12])],
          "Party Hat: confetti from the killed monster's body.")
    sheet("FxItem3PartyHat", 12, 12, None, [("Hat", [hat_frame(f) for f in range(4)], [0.3, 0.15, 0.3, 0.15])],
          "Party Hat worn: head overlay (offset -3: the brim sits 3 px into the head).")
    sheet("FxItem3TokenLute", 14, 16, (7, 14), [
        ("Idle", [lute_token("Idle", f) for f in range(12)], [0.117] * 12),
        ("Ready", [lute_token("Ready", f) for f in range(2)], [0.1, 0.1]),
        ("Activate", [lute_token("Activate", f) for f in range(10)], [0.1, 0.067, 0.067, 0.067, 0.1, 0.1, 0.1, 0.12, 0.12, 0.12]),
        ("Wait", [lute_token("Wait", f) for f in range(6)], [0.167] * 6),
        ("WakeUp", [lute_token("WakeUp", f) for f in range(4)], [0.05] * 4)],
        "Bard's Lute follower (Book of Tears states). The note leaves on Activate frame 3 (the strum flash).")
    sheet("FxItem3Note", 14, 16, (7, 9), [("Fly", [note("Fly", f) for f in range(4)], [0.08] * 4),
                                          ("Pop", [note("Pop", f) for f in range(5)], [0.04, 0.05, 0.06, 0.07, 0.08])],
          "Bard's Lute note: skeleton-mage bolt collider at the origin.")
    sheet("FxItem3Ferret", 24, 14, (12, 12), [("Idle", [ferret("Idle", f) for f in range(4)], [0.3, 0.25, 0.3, 0.12]),
                                              ("Run", [ferret("Run", f) for f in range(6)], [0.07] * 6)],
          "Pet Ferret, faces right; code flips it (feet at the origin).")
    sheet("FxItem3Bubble", 14, 14, (7, 7), [("Fly", [bubble("Fly", f) for f in range(4)], [0.12] * 4),
                                            ("Pop", [bubble("Pop", f) for f in range(5)], [0.03, 0.04, 0.05, 0.06, 0.07])],
          "Bubble Pipe bubble: drifts 45 px/s for 2.6 s, pops on a monster (0.3 + slow) or at the end.")
    sheet("FxItem3Duck", 88, 40, (44, 22), [("Squeak", [duck_ring(f) for f in range(6)], [0.05, 0.06, 0.07, 0.08, 0.1, 0.12])],
          "Rubber Duck squeak ring: damage frames 0..3, hitbox 80 x 34 on the feet (the TrollGroundPound ring, Strike.Collider).")
    sheet("FxItem3Firefly", 12, 12, (6, 6), [("Glow", [firefly("Glow", f) for f in range(4)], [0.1, 0.1, 0.12, 0.1]),
                                             ("Dim", [firefly("Dim", f) for f in range(2)], [0.4, 0.4]),
                                             ("Zap", [firefly("Zap", f) for f in range(5)], [0.03, 0.04, 0.05, 0.06, 0.07])],
          "Firefly Jar: each firefly orbits 17 x 7 px round the hero's chest (code); Zap pops on the monster it touched.")
    sheet("FxItem3Dance", 16, 12, (8, 10), [("Step", [dance_step(f) for f in range(6)], [0.06, 0.06, 0.08, 0.1, 0.12, 0.14])],
          "Dancing Shoes: a sparkly footprint every 0.16 s while dancing.")
    sheet("FxItem3Whet", 20, 20, (10, 10), [("Spark", [whet_spark(f) for f in range(5)], [0.03, 0.04, 0.05, 0.06, 0.08])],
          "Whetstone: first hit on a monster (at its aim point).")
    sheet("FxItem3Phoenix", 48, 56, (24, 52), [("Burst", [phoenix(f) for f in range(10)], [0.05, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.1, 0.12, 0.14])],
          "Phoenix Feather burns instead of the hero (at the feet).")
    sheet("FxItem3Siphon", 24, 36, (12, 34), [("Wisp", [siphon(f) for f in range(8)], [0.05] * 8)],
          "Siphon Gem: a kill's wisp spirals into the hero (at the feet).")
    sheet("FxItem3Fork", 24, 32, (12, 30), [("Heal", [fork_heal(f) for f in range(7)], [0.06, 0.07, 0.08, 0.09, 0.1, 0.11, 0.12])],
          "Glutton's Fork: the extra half of a health pickup.")
    sheet("FxItem3Coin", 20, 48, (10, 46), [(face, [coin(face, f) for f in range(12)], [0.05] * 8 + [0.2, 0.3, 0.3, 0.2]) for face in ("Heads", "Tails")],
          "Gambler's Coin: flips over the head as a fight starts; Heads = damage (gold crown), Tails = speed (silver wing).")
    sheet("FxItem3Bandage", 32, 36, (16, 34), [("Absorb", [bandage_absorb(f) for f in range(7)], [0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1])],
          "Patchwork Bandage halves the first monster hit of a fight.")
    sheet("FxItem3Boots", 28, 12, (14, 10), [("Clank", [boots_clank(f) for f in range(5)], [0.04, 0.05, 0.06, 0.07, 0.08])],
          "Iron Boots: hit but not knocked back.")
    sheet("FxItem3Key", 28, 28, (14, 22), [("Lie", [key_frames("Lie", f) for f in range(8)], [0.12, 0.08, 0.2, 0.2, 0.15, 0.2, 0.2, 0.3]),
                                           ("Collect", [key_frames("Collect", f) for f in range(6)], [0.04, 0.05, 0.06, 0.07, 0.08, 0.1])],
          "Skeleton Key pickup on the floor (origin on the pickup point) and the sparkle when it is picked up.")
    sheet("FxItem3Heart", 32, 40, (16, 36), [("Lie", [heart_frames("Lie", f) for f in range(6)], [0.25, 0.2, 0.12, 0.12, 0.25, 0.3]),
                                             ("Collect", [heart_frames("Collect", f) for f in range(6)], [0.04, 0.05, 0.06, 0.07, 0.08, 0.1]),
                                             ("Beat", [heart_frames("Beat", f) for f in range(7)], [0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.12])],
          "Gilded Heart pickup (beats), collect sparkle, and the golden beat that heals 0.5 as a fight starts.")
    sheet("FxItem3IndSluggish", 24, 12, None, [("Loop", [ind_sluggish(f) for f in range(4)], [0.15] * 4)], "Troll Marrow slow: feet overlay.")
    sheet("FxItem3IndBurn", 24, 20, None, [("Loop", [ind_burn(f) for f in range(4)], [0.08] * 4)], "Wyrm Blood burn: feet overlay.")
    sheet("FxItem3IndShaky", 18, 10, None, [("Loop", [ind_shaky(f) for f in range(4)], [0.09] * 4)], "Hare's Dew shaky hands: head overlay.")
    sheet("FxItem3IndKey", 24, 16, None, [("Loop", [ind_key(f) for f in range(8)], [0.2, 0.15, 0.15, 0.2, 0.2, 0.15, 0.15, 0.2])],
          "Skeleton Key carried: feet overlay (the key hangs at the hip).")
    sheet("FxItem3IndBandage", 12, 10, None, [("Loop", [ind_bandage(f) for f in range(4)], [0.25] * 4)], "Bandage armed: head overlay.")
    sheet("FxItem3Wanted", 15, 15, None, [("Mark", [wanted_mark(f) for f in range(4)], [0.15] * 4)], "Wanted mark: head overlay on the monster.")
    sheet("FxItem3IndHeart", 24, 14, None, [("Loop", [ind_heart(f) for f in range(5)], [0.12] * 5)], "Gilded Heart carried: feet overlay.")
    open(os.path.join(OUT, "TIMING.md"), "w").write("\n".join(TIMING))
    contact()


def contact():
    """Every FxItem3 sheet's frames on one board at 3x, on Crawl's dark floor, for looking at."""
    import json, glob
    os.makedirs(BOARDS, exist_ok=True)
    font = ImageFont.load_default(size=11)
    rows = []
    for j in sorted(glob.glob(os.path.join(OUT, "FxItem3*.json"))):
        m = json.load(open(j)); im = Image.open(j[:-5] + ".png").convert("RGBA")
        for a in m["anims"]:
            cells = []
            for fi in a["frames"]:
                x, y = (fi % m["cols"]) * m["cellW"], (fi // m["cols"]) * m["cellH"]
                cells.append(im.crop((x, y, x + m["cellW"], y + m["cellH"])))
            rows.append((os.path.basename(j)[:-5] + "/" + a["name"], cells, m.get("origin")))
    S = 3
    W = max(sum(c.width * S + 4 for c in cells) for _, cells, _ in rows) + 170
    H = sum(max(c.height for c in cells) * S + 6 for _, cells, _ in rows)
    out = Image.new("RGBA", (W, H), (34, 30, 36, 255))
    d = ImageDraw.Draw(out)
    y = 0
    for name, cells, origin in rows:
        d.text((4, y + 4), name, fill=(220, 210, 190), font=font)
        x = 170
        for c in cells:
            bg = Image.new("RGBA", c.size, (52, 46, 44, 255)); bg.alpha_composite(c)
            if origin: bg.putpixel(tuple(origin), (0, 255, 255, 255)) if False else None
            out.alpha_composite(bg.resize((c.width * S, c.height * S), Image.NEAREST), (x, y))
            x += c.width * S + 4
        y += max(c.height for c in cells) * S + 6
    out.convert("RGB").save(os.path.join(BOARDS, "items3_fx.png"))
    print("fx contact:", os.path.join(BOARDS, "items3_fx.png"), out.size)


if __name__ == "__main__":
    build()
