"""Wickling, fully rigged: every frame is its own pose.
Moves: Flare Bite (hop + bite), Gutter Dash (flaming dash that leaves ember patches)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from rig import Part, Canvas
from anim import pack, preview
import scalekit as SK

TORSO = {
    "hunch": Part("""
.....hgw..
...hgggghw
..hgkgggg.
.hgkkgkg..
.gkkgkg...
..kgkk....
""", (3, 5)),
    "low": Part("""
......hgww
..hhggggh.
.hgkkggg..
hgkkgkg...
.gkkkg....
""", (3, 4)),
    "up": Part("""
......hw.
.....hggw
....hggg.
...hgkg..
..hgkkg..
..gkkg...
..kgk....
""", (3, 6)),
    "slump": Part("""
..........
..hgghhw..
.hgkkgggh.
hgkkgkkgg.
.kkkgkkk..
""", (4, 4)),
}
SHOULDER = {"hunch": (5, -5), "low": (6, -4), "up": (5, -6), "slump": (5, -3)}

HEAD = {
    "calm": Part("""
.XXXX.
XWWWWX
WWWRrW
WwWWWW
hWw.wW
.w..w.
""", (1, 5)),
    "open": Part("""
.XXXX.
XWWWWX
WWWRrW
WwWWWk
hWw.Kk
.w.wWX
""", (1, 5)),
    "chomp": Part("""
.XXXX..
XWWWWX.
WWWRrWX
WwWWWWW
hWwwwW.
.w..w..
""", (1, 5)),
    "down": Part("""
.XXXX.
XWWWWX
WWWWWW
WwWRrW
hWw.wW
.w..w.
""", (1, 5)),
    "melt1": Part("""
......
.XXXX.
XWWWWX
WWWRrW
hwWwWW
wwwwww
""", (1, 5)),
    "melt2": Part("""
......
......
.XXXX.
XWWWrWX
wwWwWww
whwwwwh
""", (1, 5)),
}
WICK = Part("kK", (0, 0))
FLAME = {
    0: Part("""
.O.
.YO
OYO
oYo
""", (1, 4)),
    1: Part("""
..O
.OY
OYO
oYo
""", (1, 4)),
    2: Part("""
O..
OY.
OYO
oYo
""", (1, 4)),
    3: Part("""
.O.
OY.
OYY
oYo
""", (1, 4)),
    "tall": Part("""
.O.
.YO
OyO
OYO
OYY
oYo
""", (1, 6)),
    "stream": Part("""
oO.....
.oOOY..
..oOYyY
...oYY.
""", (6, 3)),
    "smoke": Part("""
.s.
s..
.S.
""", (1, 3)),
    "ember": Part("""
O.o
.Y.
""", (1, 1)),
}
CLAW = Part("""
w.w
ww.
""", (0, 0))
FOOT = Part("kk", (0, 0))

LEG_COL = ["k", "g"]
ARM_COL = ["g", "h"]


def pose(torso="hunch", head="calm", flame=0, dx=0, dy=0, head_off=(0, 0),
         legs=((115, 75), (60, 105)), arms=((25, 55), (40, 80)), extra=None, no_back_arm=False):
    """legs/arms: ((upper, lower) back, (upper, lower) front) joint angles."""
    c = Canvas()
    hip = (dx, -6 + dy)
    sh = (hip[0] + SHOULDER[torso][0], hip[1] + SHOULDER[torso][1])
    # back limbs first
    c.limb(hip[0] - 1, hip[1], [(3, legs[0][0]), (3, legs[0][1])], ["k", "k"], end=FOOT)
    if not no_back_arm:
        c.limb(sh[0] - 1, sh[1] + 1, [(3, arms[0][0]), (2, arms[0][1])], ["k", "g"], end=CLAW)
    c.part(TORSO[torso], hip[0], hip[1])
    # head on the neck, wick + flame on top of the candle
    nx, ny = sh[0] + head_off[0], sh[1] + head_off[1]
    c.part(HEAD[head], nx, ny)
    if flame is not None:
        c.part(WICK, nx + 2, ny - 6)
        if flame == "stream":
            c.part(FLAME["stream"], nx + 2, ny - 6)
        else:
            c.part(FLAME[flame], nx + 2, ny - 7)
    # front limbs on top
    c.limb(hip[0] + 1, hip[1], [(3, legs[1][0]), (3, legs[1][1])], LEG_COL, end=FOOT)
    c.limb(sh[0], sh[1] + 1, [(3, arms[1][0]), (3, arms[1][1])], ARM_COL, end=CLAW)
    if extra:
        for part, x, y in extra: c.part(part, x, y)
    return c.spr()


def build(outdir):
    idle = [pose(flame=i, dy=(0 if i in (0, 3) else 0), arms=((25 + 3 * (i % 2), 55), (40 - 3 * (i % 2), 80)),
                 head_off=(0, 1 if i == 2 else 0)) for i in range(4)]

    run = []
    cyc = [((140, 95), (40, 95)), ((120, 80), (60, 120)), ((95, 70), (90, 110)),
           ((40, 95), (140, 95)), ((60, 120), (120, 80)), ((90, 110), (95, 70))]
    for i, (lb, lf) in enumerate(cyc):
        bob = -1 if i in (0, 3) else 0
        swing = 20 if i < 3 else -20
        run.append(pose(flame=i % 4, dy=bob, legs=(lb, lf),
                        arms=((25 - swing, 70), (25 + swing, 60)), torso="hunch"))

    # Flare Bite: crouch, hop, open, chomp, land, recover
    bite = [
        pose(torso="low", head="calm", flame=0, dy=1, legs=((150, 60), (50, 130)), arms=((60, 100), (70, 110))),
        pose(torso="hunch", head="open", flame="stream", dx=1, dy=-3, legs=((170, 40), (150, 60)), arms=((-10, 30), (0, 30))),
        pose(torso="low", head="open", flame="stream", dx=3, dy=-2, head_off=(1, 0), legs=((175, 120), (160, 80)), arms=((0, 10), (-5, 15))),
        pose(torso="low", head="chomp", flame=1, dx=4, dy=0, head_off=(1, 1), legs=((140, 70), (60, 120)), arms=((20, 60), (10, 50)),
             extra=[(FLAME["ember"], 14, -10)]),
        pose(torso="low", head="calm", flame=2, dx=3, dy=1, legs=((150, 60), (40, 120)), arms=((40, 90), (50, 90))),
        pose(torso="hunch", head="calm", flame=3, dx=1, legs=((120, 80), (60, 105)), arms=((25, 60), (40, 80))),
    ]
    # Gutter Dash: crouch back, flare, 3 dash frames, stumble, recover
    dash = [
        pose(torso="up", head="down", flame=0, dx=-1, dy=1, legs=((150, 70), (60, 130)), arms=((80, 110), (90, 120))),
        pose(torso="up", head="calm", flame="tall", dx=-1, legs=((130, 80), (70, 110)), arms=((-40, -10), (-60, -20))),
        pose(torso="low", head="calm", flame="stream", dx=2, dy=1, legs=((170, 140), (20, 60)), arms=((170, 150), (160, 140))),
        pose(torso="low", head="calm", flame="stream", dx=3, dy=0, legs=((150, 110), (50, 90)), arms=((165, 140), (170, 150))),
        pose(torso="low", head="calm", flame="stream", dx=4, dy=1, legs=((175, 150), (30, 70)), arms=((170, 150), (160, 145))),
        pose(torso="slump", head="down", flame=2, dx=3, dy=1, legs=((100, 60), (70, 100)), arms=((90, 100), (60, 90))),
        pose(torso="hunch", head="calm", flame=3, dx=1, legs=((115, 75), (60, 105)), arms=((25, 55), (40, 80))),
    ]
    dead = [
        pose(torso="slump", head="down", flame="smoke", dy=2, legs=((170, 175), (10, 5)), arms=((150, 170), (20, 10))),
    ]
    death_anim = [
        pose(torso="up", head="down", flame=1, dx=-1, legs=((120, 90), (80, 100)), arms=((-60, -30), (-80, -40))),
        pose(torso="slump", head="down", flame=2, dy=1, legs=((150, 120), (40, 60)), arms=((120, 150), (60, 40))),
        pose(torso="slump", head="melt1", flame="smoke", dy=2, legs=((170, 175), (10, 5)), arms=((150, 170), (20, 10))),
        pose(torso="slump", head="melt2", flame=None, dy=2, legs=((170, 175), (10, 5)), arms=((150, 170), (20, 10))),
    ]
    knock = [pose(torso="up", head="down", flame=2, dx=-2, legs=((130, 90), (80, 110)), arms=((-120, -80), (-100, -70)))]
    statue = [idle[0].stone()]

    anims = [
        ("Idle", idle, [0.16] * 4),
        ("Run", run, [0.07] * 6),
        ("Dead", dead, [0.2]),
        ("Death", death_anim, [0.08, 0.1, 0.14, 0.3]),
        ("Statue", statue, [0.2]),
        ("Knockback", knock, [0.2]),
        ("Portrait", [idle[0]], [0.2]),
        ("Bite", bite, [0.08, 0.07, 0.06, 0.12, 0.08, 0.12]),
        ("Dash", dash, [0.1, 0.12, 0.06, 0.06, 0.06, 0.18, 0.12]),
    ]
    img, man = pack("Wickling", anims, cell_w=48, cell_h=34, feet=(24, 32), outdir=outdir, floor=True)
    preview(img, man, os.path.join(outdir, "Wickling_preview.png"), scale=6)
    return img, man


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "art/out"))


# ---------------------------------------------------------------- v0.7 small render (design scale ~0.68)
# Hand-drawn 5 px heads and 3 px flames: carving the 6 px head down loses the eye and jaw.
for _sc in (0.65, 0.68, 0.7):
    SK.subst(HEAD["calm"], _sc, """
.XXX.
XWWWX
WWRrW
WwWWW
hW.wW
""", (1, 4))
    SK.subst(HEAD["open"], _sc, """
.XXX.
XWWWX
WWRrW
WwWWk
hW.Kk
""", (1, 4))
    SK.subst(HEAD["chomp"], _sc, """
.XXX.
XWWWX
WWRrX
WwWWW
hWwwW
""", (1, 4))
    SK.subst(HEAD["down"], _sc, """
.XXX.
XWWWX
WWWWW
WwRrW
hW.wW
""", (1, 4))
    SK.subst(HEAD["melt1"], _sc, """
.....
.XXX.
XWRrX
hwWwW
wwwww
""", (1, 4))
    SK.subst(HEAD["melt2"], _sc, """
.....
.....
.XXX.
wWwrW
whwwh
""", (1, 4))
    SK.subst(FLAME[0], _sc, ".O.\nOYO\noYo", (1, 2))
    SK.subst(FLAME[1], _sc, "..O\nOYO\noYo", (1, 2))
    SK.subst(FLAME[2], _sc, "O..\nOYO\noYo", (1, 2))
    SK.subst(FLAME[3], _sc, ".O.\nOYY\noYo", (1, 2))
    SK.subst(FLAME["tall"], _sc, ".O.\nOYO\nOYY\noYo", (1, 3))
