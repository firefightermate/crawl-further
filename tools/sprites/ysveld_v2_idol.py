"""Ysveld's portraits (29 x 24 panels, like every deity portrait): DeityYsveld, the Frost Widow herself, and
DeityYsvIdol, the gold idol a Gold slot god with Ysveld's perk wears (SlotGods.PortraitFor)."""
import math, random
from ysveld_v2_rigs import Rig, SprRGB, RAMPS, crystal, sparkle, fx, lerp

W, H = 29, 24
OX, OY = 14, 22          # the origin inside the panel


def panel(top, bot, figure, flakes=None, web=None):
    """A filled panel: a vertical gradient from top to bot (RGB), optional faint web lines and snow, then the figure."""
    px = {}
    for y in range(H):
        t = y / (H - 1.0)
        c = tuple(int(lerp(top[i], bot[i], t)) for i in range(3))
        for x in range(W):
            px[(x - OX, y - OY)] = c
    if web:
        for (pts, c) in web:
            for (x, y) in pts:
                if (x, y) in px: px[(x, y)] = c
    if flakes:
        for (x, y, c) in flakes:
            if (x, y) in px: px[(x, y)] = c
    for k, v in figure.px.items():
        if k in px: px[k] = v
    return SprRGB(px)


def web_lines(cx, cy, n=8, rings=(4, 7, 10), col=(70, 58, 40)):
    from ysveld_v2_rigs import line_px
    pts = []
    for i in range(n):
        a = i / n * math.tau
        pts += line_px(cx, cy, int(round(cx + math.cos(a) * 14)), int(round(cy + math.sin(a) * 11)))
    for R in rings:
        for i in range(n):
            a0 = i / n * math.tau; a1 = (i + 1) / n * math.tau
            pts += line_px(int(round(cx + math.cos(a0) * R)), int(round(cy + math.sin(a0) * R * 0.8)),
                           int(round(cx + math.cos(a1) * R)), int(round(cy + math.sin(a1) * R * 0.8)))
    return [(pts, col)]


# ------------------------------------------------------------------ the gold idol: a spider seen from above, a veiled face on its back
IDOL_FACE = {"g": ("gold", 2), "G": ("gold", 3), "h": ("gold", 4), "d": ("gold", 1), "k": ("gold", 0),
             "s": ("goldh", 2), "S": ("goldh", 3), "e": ("eye", 4), "E": ("eye", 3)}
FACE = """
..dGGGd..
.dGhhhGd.
dGhGGGhGd
dGsGGGsGd
dGeSGSeGd
dGGGgGGGd
.dGgdgGd.
..dGGGd..
...dgd...
"""


def idol_frame(k):
    r = Rig()
    cx, cy = 0.0, -10.0
    # eight legs spread round the body, their tips icicle points making a crown
    for i in range(8):
        a = math.radians(-160 + i * (140 / 7.0)) if i < 4 else math.radians(20 + (i - 4) * (140 / 7.0))
        side = -1 if i < 4 else 1
        ang = [-150, -125, -100, -75][i] if i < 4 else [-30, -55, 20, 45][i - 4]
        if i >= 4: ang = [-30, -55, 20, 45][i - 4]
        ang = [-155, -125, 160, 130, -25, -55, 20, 50][i]
        a = math.radians(ang)
        knee = (cx + math.cos(a) * 7.0, cy + math.sin(a) * 5.5 - 2.0)
        tip = (cx + math.cos(a) * 12.5, cy + math.sin(a) * 9.5)
        r.tube([(cx + math.cos(a) * 3.0, cy + math.sin(a) * 2.5), knee, tip], [1.0, 0.8, 0.5], "gold", 0.0 + i * 0.01, bias=0.05)
        if math.sin(a) < 0:      # the upper legs end in icicle points: a crown
            crystal(r, tip[0], tip[1] + 1.0, 3.0, 1.4, "goldh", 0.5, ang=math.degrees(a) + 90)
    # the body: an abdomen behind, the cephalothorax with the veiled face
    r.ell(cx, cy + 4.0, 4.6, 3.6, "gold", 1.0, bias=0.1)
    r.ell(cx, cy - 1.0, 5.0, 4.6, "gold", 1.2, bias=0.15)
    r.stamp(FACE, cx, cy - 1.0, 2.0, IDOL_FACE, pivot=(4, 4))
    # a glint that walks across the gold
    gx = [-4, -1, 2, 5][k]
    r.dot(gx, cy - 4 + abs(gx) * 0.3, "white", 4, 3.0)
    s = r.resolve(floor=False, cast=False, outline=False)
    rnd = random.Random(k)
    fl = [(rnd.randint(-14, 14), rnd.randint(-22, 1), (120, 110, 90)) for _ in range(5)]
    return panel((20, 14, 12), (34, 24, 18), s, flakes=fl, web=web_lines(0, -10))


def idol_sheet(out):
    frames = [idol_frame(k) for k in range(4)]
    fx("DeityYsvIdol", (W, H), (OX, OY), [("Idle", frames, [0.3, 0.2, 0.3, 0.2])], out, scale=8)


def widow_sheet(out):
    from deity_portraits import frames  # the god portrait, drawn to DeityZhekra's standard
    fx("DeityYsveld", (W, H), (OX, OY), [("Idle", frames("ysveld", (OX, OY)), [0.3, 0.25, 0.3, 0.25])], out, scale=8)


JOBS = [("DeityYsvIdol", idol_sheet), ("DeityYsveld", widow_sheet)]
