"""Mourning Candelabra: a living iron candelabra with a weeping skull and root-feet.
Moves: Five Flames (fan of candle bolts, candles fire in sequence), Vigil (roots in, candles blaze, lights the room)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from rig import Part, Canvas
from anim import pack, preview

CANDLE = {
    "lit0": Part(".O.\n.Y.\nXWX\nWWX\nkKk", (1, 4)),
    "lit1": Part("O..\n.YO\nXWX\nWWX\nkKk", (1, 4)),
    "lit2": Part("..O\nOY.\nXWX\nWWX\nkKk", (1, 4)),
    "blaze": Part(".O.\nOYO\nOyO\n.Y.\nXWX\nWWX\nkKk", (1, 6)),
    "fire": Part("OYO\nYyY\nOyO\n.Y.\nXWX\nWWX\nkKk", (1, 6)),
    "out": Part(".s.\n.S.\nXWX\nWWX\nkKk", (1, 4)),
    "none": Part("XWX\nWWX\nkKk", (1, 2)),
}
SKULL = Part("""
.kSk.
kSXSk
SKXKS
SXXXS
kSRSk
.SXS.
""", (2, 5))
SKULL_WAIL = Part("""
.kSk.
kSXSk
SKXKS
SXXXS
kSKSk
.SKS.
""", (2, 5))
TEAR = Part("b\nB", (0, 0))
ROOT_TIP = Part("k", (0, 0))


def moth_wings(c, x, y, flap=0, ember=True):
    """v0.9 lineage (the Ash Moth parent): a pair of ash-moth wings spread behind the stem, ember eye-spot on each."""
    from moth_rig import wing
    k = getattr(c, "s", 1.0)
    px = {}
    for side, ln in ((-1, 12.0), (1, 12.5)):
        ang = -90 + side * (64 - flap)
        wing(px, ((x + side * 1.5) * k, y * k), ln * k, ang, 0.55, fill=("g" if side < 0 else "h"), rim="k", spot=ember)
    raw = c.raw if hasattr(c, "raw") else c
    for (px_, py_), ch in px.items():
        raw.put(int(round(px_)), int(round(py_)), ch)


def pose(dx=0, dy=0, sway=0, candles=("lit0",) * 5, roots=((120, 100), (90, 90), (60, 80)), skull=SKULL, tear=None, dig=0,
         flap=0, wings=True):
    c = Canvas()
    base = (dx, -6 + dy)
    if wings:
        moth_wings(c, base[0] + sway // 2, base[1] - 7, flap=flap, ember=True)
    # roots
    for i, (a1, a2) in enumerate(roots):
        c.limb(base[0], base[1], [(4, a1), (3 + dig, a2)], ["k", "k"], end=ROOT_TIP)
    # stem
    top = (base[0] + sway, base[1] - 14)
    c.limb(base[0], base[1], [(14, -90 + sway * 4)], [("k", "K")], width=2)
    c.part(skull, base[0] + sway // 2, base[1] - 4)
    if tear is not None:
        c.part(TEAR, base[0] + sway // 2 + 1, base[1] - 3 + tear)
    # arms: outer pair, inner pair, centre
    arm_specs = [(-1, 9, -150, -100), (-1, 5, -160, -95), (0, 0, -90, -90), (1, 5, -20, -85), (1, 9, -30, -80)]
    centre_y = top[1]
    for i, (side, reach, a1, a2) in enumerate(arm_specs):
        if side == 0:
            ex, ey = top[0], top[1]
        else:
            y0 = top[1] + (5 if reach == 9 else 2)
            ex, ey = c.limb(top[0], y0, [(reach * 0.6, 180 if side < 0 else 0), (4, -90)], ["k"])
        c.part(CANDLE[candles[i]], ex + sway // 3, ey - 1)
    return c.spr()


def build(outdir):
    seq = ["lit0", "lit1", "lit2"]
    idle = [pose(candles=tuple(seq[(i + k) % 3] for k in range(5)), tear=(i % 4) if i < 3 else None, flap=[0, 6, 10, 5][i]) for i in range(4)]
    run = []
    gaits = [((140, 110), (90, 70), (40, 80)), ((120, 90), (100, 100), (60, 60)), ((100, 80), (80, 110), (70, 90)),
             ((130, 120), (90, 70), (50, 70)), ((110, 90), (70, 100), (60, 90)), ((120, 100), (100, 80), (60, 80))]
    for i, r in enumerate(gaits):
        run.append(pose(dy=-1 if i % 3 == 0 else 0, sway=[1, 0, -1, 1, 0, -1][i], roots=r, flap=[0, 8, 14, 8, 0, -4][i],
                        candles=tuple(seq[(i + k) % 3] for k in range(5))))
    fan = [pose(sway=-2, candles=("lit0",) * 5),
           pose(sway=-2, candles=("blaze", "lit1", "lit0", "lit1", "blaze"), skull=SKULL_WAIL),
           pose(sway=1, candles=("fire", "blaze", "fire", "blaze", "fire"), skull=SKULL_WAIL),
           pose(sway=2, candles=("out", "fire", "fire", "fire", "out"), skull=SKULL_WAIL),
           pose(sway=1, candles=("out", "out", "fire", "out", "out")),
           pose(sway=0, candles=("lit1", "out", "out", "out", "lit1")),
           pose(sway=0, candles=("lit0",) * 5)]
    vig_roots = ((150, 120), (90, 90), (30, 60))
    # v0.8: Vigil is 8 frames (0.1 s each, looped x4 by the kit = the same 3.2 s and event frames as 4 x 8 before):
    # the roots dig in, the candles blaze in a wave from left to right and back, the skull weeps
    vigil = []
    for i in range(8):
        cand = tuple(("fire" if (k + i) % 4 == 0 else "blaze" if (k + i) % 4 in (1, 3) else ("lit0", "lit1", "lit2")[i % 3]) for k in range(5))
        vigil.append(pose(dy=1, sway=[0, 1, 1, 0, 0, -1, -1, 0][i], roots=vig_roots, dig=1 + (i > 0), candles=cand, skull=SKULL_WAIL,
                          tear=(i % 4) if i % 4 != 3 else None, flap=12 + (i % 2) * 6))
    death = [pose(sway=3, candles=("lit2",) * 5, skull=SKULL_WAIL, flap=-10),
             pose(sway=4, dy=1, candles=("lit0", "out", "lit1", "out", "lit2"), skull=SKULL_WAIL, roots=((150, 130), (100, 95), (60, 60)), flap=-25),
             pose(sway=6, candles=("out",) * 5, skull=SKULL_WAIL, roots=((160, 150), (110, 100), (60, 40))),
             pose(sway=9, dy=2, candles=("none",) * 5, skull=SKULL_WAIL, roots=((175, 170), (120, 110), (20, 10)))]
    knock = [pose(sway=-3, candles=("lit2", "lit1", "lit2", "lit1", "lit2"), skull=SKULL_WAIL, flap=20)]
    anims = [
        ("Idle", idle, [0.16] * 4), ("Run", run, [0.1] * 6), ("Dead", [death[-1]], [0.2]),
        ("Death", death, [0.08, 0.08, 0.12, 0.3]), ("Statue", [idle[0].stone()], [0.2]), ("Knockback", knock, [0.2]),
        ("Portrait", [idle[0]], [0.2]),
        ("Fan", fan, [0.12, 0.14, 0.06, 0.08, 0.08, 0.1, 0.12]),
        ("Vigil", vigil, [0.1] * 8),
    ]
    img, man = pack("Candelabra", anims, cell_w=48, cell_h=40, feet=(24, 38), outdir=outdir, floor=True)
    preview(img, man, os.path.join(outdir, "Candelabra_preview.png"), scale=5)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "art/out"))
