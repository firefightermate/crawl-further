"""Chandler: hunched candlemaker with a bucket of molten wax and a long ladle.
Moves: Ladle Toss (lobbed burning wax), Pour (tips the bucket into a line of puddles)."""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from rig import Part, Canvas
from anim import pack, preview

BUCKET = Part("""
.aaaaa.
aOYYOOa
aoOOOoa
akkkkka
akKkKka
.akkka.
""", (3, 5))
BUCKET_TIP = Part("""
..aaaa.
.aOYOYa
aoOOOoa
akOOOka
akkkkkk
.aakkk.
""", (3, 5))
BUCKET_GLOW = Part("""
.aaaaa.
aYOOYOa
aoOYOoa
akkkkka
akKkKka
.akkka.
""", (3, 5))
# v0.9 lineage: the Chandler is what a Wickling (candle head, red eyes, a wick that burns) and a Tallow Grub (soft
# segmented tallow) become together - a hunched tallow-man whose head is a guttering candle, wearing a chandler's
# leather apron. (It used to be a grey-headed man in a red robe that read like the Waxen Knight.)
HEAD = Part("""
..O..
..Y..
..k..
.XWW.
XWWWw
WRwRw
wWWWh
.wWh.
""", (1, 7))
HEAD_DOWN = Part("""
.....
...O.
..Yo.
..k..
.XWW.
XWWWw
WWRwR
.wWWh
""", (1, 7))
TORSO = Part("""
...hwW...
..hwWXWw.
.hwWWWWWw
.whWhWWhw
..kgggkWh
..kgkgkwh
...kgkg..
""", (4, 6))
TORSO_BENT = Part("""
.........
....hwW..
..hwWWXWw
.hwWhWWWw
whWkgggkh
.hWkgkgkw
..kgkgk..
""", (4, 6))
FOOT = Part("hh", (0, 0))
HAND = Part("Ww", (0, 0))
LADLE_CUP = {"full": Part("kKk\nkOk\n.o.", (1, 0)), "empty": Part("kKk\n.k.", (1, 0))}
DRIP = Part("o\n.\nO", (0, 0))


def ladle(c, x, y, ang, length=8, full=True):
    ex, ey = c.limb(x, y, [(length, ang)], ["k"])
    c.part(LADLE_CUP["full" if full else "empty"], ex, ey)
    if full and 40 < (ang % 360) < 140:
        c.part(DRIP, ex, ey + 3)


def pose(torso=TORSO, head=HEAD, bucket=BUCKET, dx=0, dy=0, legs=((105, 80), (75, 100)),
         arm=(20, 40), ladle_ang=30, full=True, bucket_off=(-4, -3), extra=None):
    c = Canvas()
    hip = (dx, -7 + dy)
    c.limb(hip[0] - 1, hip[1], [(4, legs[0][0]), (3, legs[0][1])], ["h"], end=FOOT)
    c.part(bucket, hip[0] + bucket_off[0], hip[1] - 4 + bucket_off[1])
    c.part(torso, hip[0], hip[1])
    c.part(head, hip[0] + 3, hip[1] - 7)
    c.limb(hip[0] + 1, hip[1], [(4, legs[1][0]), (3, legs[1][1])], ["i", "h"], end=FOOT)
    hx, hy = c.limb(hip[0] + 3, hip[1] - 4, [(3, arm[0]), (3, arm[1])], ["W", "w"])
    ladle(c, hx, hy, ladle_ang, full=full)
    c.part(HAND, hx, hy)
    if extra:
        for p, x, y in extra: c.part(p, x, y)
    return c.spr()


BLOB = Part(".W.\nWXW\n.w.", (1, 1))


def build(outdir):
    # v0.8: four distinct frames: it stirs the ladle, nods, and the bucket's wax glows and drips in turn
    idle = [pose(dy=[0, 0, 1, 0][i], ladle_ang=[30, 40, 50, 38][i], arm=[(20, 40), (25, 50), (30, 60), (24, 48)][i],
                 head=HEAD if i != 2 else HEAD_DOWN, bucket=BUCKET if i % 2 == 0 else BUCKET_GLOW) for i in range(4)]
    cyc = [((60, 100), (120, 90)), ((80, 110), (100, 80)), ((105, 80), (75, 100)),
           ((120, 90), (60, 100)), ((100, 80), (80, 110)), ((75, 100), (105, 80))]
    run = [pose(dy=-1 if i % 3 == 0 else 0, legs=cyc[i], ladle_ang=50 + 10 * (i % 2), arm=(30, 60)) for i in range(6)]
    toss = [pose(arm=(60, 90), ladle_ang=110, legs=((110, 80), (70, 100))),           # scoop from bucket
            pose(arm=(-120, -150), ladle_ang=-160, torso=TORSO, head=HEAD, dx=-1),     # wind back
            pose(arm=(-60, -80), ladle_ang=-70, dx=0),
            pose(arm=(-10, -20), ladle_ang=-30, full=False, dx=1, extra=[(BLOB, 10, -22)]),  # release
            pose(arm=(20, 40), ladle_ang=20, full=False, dx=1),
            pose(arm=(20, 40), ladle_ang=30, full=False)]
    pour = [pose(torso=TORSO_BENT, head=HEAD_DOWN, arm=(60, 80), ladle_ang=100, dy=1),
            pose(torso=TORSO_BENT, head=HEAD_DOWN, bucket=BUCKET_TIP, bucket_off=(-1, 2), arm=(70, 90), ladle_ang=110, dy=1),
            pose(torso=TORSO_BENT, head=HEAD_DOWN, bucket=BUCKET_TIP, bucket_off=(2, 4), arm=(70, 90), ladle_ang=110, dy=2,
                 extra=[(DRIP, 6, -4), (DRIP, 8, -2)]),
            pose(torso=TORSO_BENT, head=HEAD_DOWN, bucket=BUCKET_TIP, bucket_off=(2, 4), arm=(70, 90), ladle_ang=110, dy=2,
                 extra=[(DRIP, 7, -5), (DRIP, 9, -2)]),
            pose(torso=TORSO_BENT, head=HEAD, bucket=BUCKET, bucket_off=(-2, -1), arm=(40, 60), ladle_ang=60, dy=1),
            pose()]
    death = [pose(head=HEAD_DOWN, dx=-1, arm=(80, 100), ladle_ang=140),
             pose(torso=TORSO_BENT, head=HEAD_DOWN, bucket=BUCKET_TIP, bucket_off=(-5, 0), dy=1, dx=-1, legs=((130, 100), (60, 90)),
                  arm=(90, 120), ladle_ang=160),
             pose(torso=TORSO_BENT, head=HEAD_DOWN, bucket=BUCKET_TIP, bucket_off=(-6, 2), dy=3, legs=((150, 120), (40, 70)), arm=(100, 140), ladle_ang=170),
             pose(torso=TORSO_BENT, head=HEAD_DOWN, bucket=BUCKET_TIP, bucket_off=(-9, 6), dy=5, legs=((175, 170), (5, 10)), arm=(160, 175), ladle_ang=180)]
    knock = [pose(head=HEAD_DOWN, dx=-2, arm=(-60, -20), ladle_ang=-80, bucket_off=(-6, -4))]
    anims = [
        ("Idle", idle, [0.2] * 4), ("Run", run, [0.09] * 6), ("Dead", [death[-1]], [0.2]),
        ("Death", death, [0.08, 0.08, 0.12, 0.3]), ("Statue", [idle[0].stone()], [0.2]), ("Knockback", knock, [0.2]),
        ("Portrait", [idle[0]], [0.2]),
        ("Toss", toss, [0.14, 0.12, 0.06, 0.08, 0.1, 0.12]),
        ("Pour", pour, [0.12, 0.12, 0.25, 0.25, 0.12, 0.12]),
    ]
    img, man = pack("Chandler", anims, cell_w=48, cell_h=40, feet=(24, 38), outdir=outdir, floor=True)
    preview(img, man, os.path.join(outdir, "Chandler_preview.png"), scale=5)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "art/out"))
