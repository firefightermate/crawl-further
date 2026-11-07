"""Waxen Knight: wax-sealed knight with a guttering sword.
Moves: Guttering Combo (3-hit string: slash, backslash, overhead that drops wax), Seal (wax armour, then burst)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from rig import Part, Canvas
from anim import pack, preview

HELM = Part("""
.O.O.O.
.Y.Y.Y.
.X.X.X.
XWXWXWX
WaaaaaW
akKRKka
akkkkka
.aaaaa.
""", (3, 7))
HELM_DOWN = Part("""
.......
.O.O.O.
.Y.Y.Y.
XXWXWXW
WaaaaaW
aakKRKk
.akkkka
..aaaa.
""", (3, 7))
TORSO = Part("""
.WXwaaaWX.
WaaaWaaaaW
waaawaWaaw
.aaaaaaaa.
.wa.aa.aw.
..aaaaaa..
..aKkkKa..
""", (5, 6))
TORSO_LEAN = Part("""
..WXwaaaWX
.WaaaWaaaaW
.waaawaWaaw
..aaaaaaaa.
..wa.aa.aw
..aaaaaa..
.aKkkKa...
""", (5, 6))
TORSO_SEALED = Part("""
.XXWWWWXX.
XWWWWWWWWX
WWwWWWWwWW
WWWWWWWWWW
wWWwWWWWWw
.wWWWWWWw.
..wWwwWw..
""", (5, 6))
GAUNT = Part("aa\nak", (0, 0))
BOOT = Part("aaa\nKkk", (1, 0))
LEG = ["a", "a"]
ARM = ["a", "a"]


def sword(c, x, y, ang, length=9):
    hilt_end = c.limb(x, y, [(2, ang + 180)], ["k"])  # pommel behind the hand
    c.limb(x, y, [(length, ang)], [("W", "X")], width=2)
    # crossguard
    import math
    a = math.radians(ang + 90)
    for s in (-1, 1):
        c.put(int(round(x + 1.5 * math.cos(math.radians(ang)) + s * math.cos(a))),
              int(round(y + 1.5 * math.sin(math.radians(ang)) + s * math.sin(a))), "k")
    # wax drips along the blade
    for k in (4, 7):
        bx = x + k * math.cos(math.radians(ang)); by = y + k * math.sin(math.radians(ang))
        c.put(int(round(bx)), int(round(by)) + 1, "w", over=False)


def pose(torso=TORSO, helm=HELM, dx=0, dy=0, legs=((100, 85), (80, 95)), back_arm=(110, 60),
         sword_arm=(30, 60), sword_ang=-30, sword_len=9, extra=None, helm_off=(0, 0)):
    c = Canvas()
    hip = (dx, -9 + dy)
    sh_b = (hip[0] - 3, hip[1] - 5)
    sh_f = (hip[0] + 3, hip[1] - 5)
    c.limb(hip[0] - 2, hip[1], [(4, legs[0][0]), (4, legs[0][1])], LEG, width=2, end=BOOT)
    c.limb(sh_b[0], sh_b[1], [(3, back_arm[0]), (3, back_arm[1])], ["k", "k"], width=2, end=GAUNT)
    c.part(torso, hip[0], hip[1])
    c.part(helm, hip[0] + 1 + helm_off[0], hip[1] - 7 + helm_off[1])
    c.limb(hip[0] + 2, hip[1], [(4, legs[1][0]), (4, legs[1][1])], LEG, width=2, end=BOOT)
    hx, hy = c.limb(sh_f[0], sh_f[1], [(3, sword_arm[0]), (3, sword_arm[1])], ARM, width=2)
    sword(c, hx, hy, sword_ang, sword_len)
    c.part(GAUNT, hx, hy)
    if extra:
        for p, x, y in extra: c.part(p, x, y)
    return c.spr()


SLASH = Part("""
....XX
..XXW.
.XWw..
XW....
W.....
""", (0, 4))
SLASH_UP = SLASH.flipped_v()
EMBER = Part("O.o\n.Y.", (1, 1))


def build(outdir):
    idle = [pose(dy=0 if i < 2 else 1, sword_ang=-30 + 3 * (i % 2)) for i in range(4)]
    cyc = [((60, 100), (120, 90)), ((80, 110), (100, 80)), ((100, 85), (80, 95)),
           ((120, 90), (60, 100)), ((100, 80), (80, 110)), ((80, 95), (100, 85))]
    run = [pose(dy=-1 if i % 3 == 0 else 0, legs=cyc[i], back_arm=(110 - 20 * ((i // 3) * 2 - 1), 60),
                sword_arm=(40, 70), sword_ang=-15) for i in range(6)]
    # combo: hit 1 slash down-forward, hit 2 backhand up, hit 3 overhead slam
    # v0.8: 6-frame swings (the hit and step land at the same time as before: TIMING.md). The arc itself is
    # the FxVhKnightSlash / FxVhKnightCleave sheet now, so the old in-sprite SLASH smears are gone.
    hit1 = [pose(sword_arm=(-30, -70), sword_ang=-80, legs=((105, 82), (75, 98))),
            pose(sword_arm=(-60, -100), sword_ang=-120, dx=-1, legs=((110, 80), (70, 100))),
            pose(torso=TORSO_LEAN, sword_arm=(10, 30), sword_ang=20, dx=1, legs=((130, 80), (50, 100))),
            pose(torso=TORSO_LEAN, sword_arm=(40, 70), sword_ang=60, dx=2, legs=((130, 80), (50, 100))),
            pose(torso=TORSO_LEAN, sword_arm=(35, 65), sword_ang=40, dx=2, legs=((120, 80), (60, 100))),
            pose(sword_arm=(30, 60), sword_ang=20, dx=1)]
    hit2 = [pose(torso=TORSO_LEAN, sword_arm=(50, 75), sword_ang=80, dx=2),
            pose(torso=TORSO_LEAN, sword_arm=(60, 80), sword_ang=100, dx=2),
            pose(torso=TORSO_LEAN, sword_arm=(-10, -40), sword_ang=-50, dx=3),
            pose(sword_arm=(-40, -70), sword_ang=-90, dx=2),
            pose(sword_arm=(-20, -40), sword_ang=-60, dx=1),
            pose(sword_arm=(10, 40), sword_ang=-40, dx=1)]
    hit3 = [pose(sword_arm=(-60, -90), sword_ang=-120, legs=((105, 75), (75, 105))),
            pose(sword_arm=(-100, -110), sword_ang=-150, dy=-1, helm=HELM, legs=((110, 70), (70, 110))),
            pose(sword_arm=(-95, -100), sword_ang=-170, dy=-2, legs=((120, 70), (60, 110))),
            pose(torso=TORSO_LEAN, helm=HELM_DOWN, sword_arm=(40, 80), sword_ang=80, dx=3, dy=1, legs=((140, 80), (40, 100)),
                 extra=[(EMBER, 14, -2)]),
            pose(torso=TORSO_LEAN, helm=HELM_DOWN, sword_arm=(50, 90), sword_ang=90, dx=3, dy=1, legs=((140, 80), (40, 100))),
            pose(sword_arm=(30, 60), sword_ang=0, dx=1)]
    seal = [pose(sword_arm=(60, 100), sword_ang=100, dy=1),
            pose(torso=TORSO_SEALED, sword_arm=(70, 110), sword_ang=110, dy=1),
            pose(torso=TORSO_SEALED, sword_arm=(70, 110), sword_ang=110, dy=1, helm=HELM_DOWN),
            pose(torso=TORSO_SEALED, sword_arm=(70, 110), sword_ang=110, dy=1, helm=HELM_DOWN, extra=[(EMBER, -6, -12), (EMBER, 7, -18)]),
            pose(sword_arm=(-60, -30), sword_ang=-40, dy=-1, back_arm=(-140, -120), extra=[(EMBER, -9, -10), (EMBER, 10, -20), (EMBER, 3, -24)]),
            pose(sword_arm=(30, 60), sword_ang=-30)]
    death = [pose(helm=HELM_DOWN, sword_arm=(80, 100), sword_ang=120, dx=-1, dy=1),
             pose(helm=HELM_DOWN, sword_arm=(85, 110), sword_ang=150, dx=-1, dy=2, legs=((130, 90), (50, 90))),
             pose(torso=TORSO_SEALED, helm=HELM_DOWN, sword_arm=(90, 120), sword_ang=170, dy=3, legs=((150, 100), (30, 80))),
             pose(torso=TORSO_SEALED, helm=HELM_DOWN, sword_arm=(170, 175), sword_ang=180, dy=5, legs=((175, 170), (5, 10)))]
    knock = [pose(helm=HELM_DOWN, dx=-2, sword_arm=(-20, 20), sword_ang=-60, back_arm=(-150, -120))]
    anims = [
        ("Idle", idle, [0.2] * 4), ("Run", run, [0.08] * 6), ("Dead", [death[-1]], [0.2]),
        ("Death", death, [0.08, 0.08, 0.1, 0.3]), ("Statue", [idle[0].stone()], [0.2]), ("Knockback", knock, [0.2]),
        ("Portrait", [idle[0]], [0.2]),
        ("Combo1", hit1, [0.07, 0.05, 0.03, 0.03, 0.1, 0.05]),
        ("Combo2", hit2, [0.03, 0.03, 0.03, 0.03, 0.1, 0.05]),
        ("Combo3", hit3, [0.07, 0.07, 0.12, 0.05, 0.16, 0.08]),
        ("Seal", seal, [0.1, 0.2, 0.3, 0.3, 0.12, 0.15]),
    ]
    img, man = pack("WaxenKnight", anims, cell_w=60, cell_h=46, feet=(28, 44), outdir=outdir, floor=True)
    preview(img, man, os.path.join(outdir, "WaxenKnight_preview.png"), scale=5)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "art/out"))
