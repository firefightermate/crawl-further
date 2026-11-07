"""Builds every Vhorrul-pack sprite sheet from the hand-made key sprites.

Frame counts per animation follow each monster's vanilla base kit, so the clips inherit the base
kit's per-frame timings and gameplay events exactly (see SpriteSheets.MakeClip)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from anim import Spr, pack, preview, interp_poses
import designs as D
import wickling

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "art/out")

# Where the creature's feet sit inside a cell: 'center' = vertical middle of the cell.
FEET_MODE = os.environ.get("FEET_MODE", "bottom")  # exSprite anchor is BotCenter; vanilla feet sit 1px above the cell bottom


def cell_for(sprs, pad_x=10, pad_y=8):
    xs0 = min(s.bbox()[0] for s in sprs); xs1 = max(s.bbox()[2] for s in sprs)
    ys0 = min(s.bbox()[1] for s in sprs)
    half_w = max(-xs0, xs1) + pad_x
    h = -ys0 + pad_y
    w = 2 * half_w
    if FEET_MODE == "center":
        ch = 2 * h
        return w, ch, (half_w, h)
    return w, h + 2, (half_w, h)


def legs_pred(split):
    return lambda x, y, c: y >= -split


def run_cycle(base, n, split, flyer=False):
    out = []
    for i in range(n):
        ph = i / float(n)
        if flyer:
            dy = [0, -1, -2, -1][i % 4]
            out.append(base.shift(0, dy).flame_flicker(i))
            continue
        lx = [1, 1, 0, -1, -1, 0][(i * 6 // n) % 6]
        bob = -1 if i % 2 == 0 else 0
        s = base.region_shift(lambda x, y, c: y >= -split and x < 0, lx, 0)
        s = s.region_shift(lambda x, y, c: y >= -split and x >= 0, -lx, 0)
        s = s.region_shift(lambda x, y, c: y < -split, 0, bob)
        out.append(s.flame_flicker(i))
    return out


def attack(base, n, strike=None, reach=2, flare=False):
    windup = base.shift(-1, 0).shear(-0.08)
    st = strike if strike is not None else base.shear(0.12).shift(reach, 0)
    if flare: st = st.flare(1)
    keys = [base, windup, st, st.shift(1, 0).flame_flicker(1), base.shift(1, 0)]
    return interp_poses(keys, n)


def special(base, n, strike=None):
    keys = [base.flare(1), base.shift(-1, 0).shear(-0.1).flare(2), base.flare(3),
            (strike or base.shear(0.12).shift(2, 0)).flare(2), base.flare(1)]
    return interp_poses(keys, n)


def idle_loop(base, n, flyer=False):
    if n == 1: return [base]
    if flyer: return [base.shift(0, [0, -1, -1, 0, 1, 1, 0][i % 7]).flame_flicker(i) for i in range(n)]
    return [base.flame_flicker(i) for i in range(n)]


def standard(name, base, counts, split=4, flyer=False, strikes=None, special_strike=None, extra=None):
    strikes = strikes or {}
    anims = [("Idle", idle_loop(base, counts["Idle"], flyer), None),
             ("Run", run_cycle(base, counts["Run"], split, flyer), None),
             ("Dead", [base.snuff().rotate_down()], None),
             ("Statue", [base.stone()], None),
             ("Knockback", [base.shear(-0.15).shift(-1, 0)], [0.2]),
             ("Portrait", [base], [0.2])]
    for k, n in counts.items():
        if k.startswith("Attack"):
            anims.append((k, attack(base, n, strikes.get(k)), None))
    if "Special" in counts:
        anims.append(("Special", special(base, counts["Special"], special_strike), None))
    if extra: anims += extra
    w, h, feet = cell_for([f for a in anims for f in a[1]])
    img, man = pack(name, anims, w, h, feet, OUT)
    preview(img, man, os.path.join(OUT, name + "_preview.png"), scale=4)
    print("built", name, "cell", w, h, "frames", sum(len(a[1]) for a in anims))


def main():
    wickling.build(OUT)

    grub = Spr.parse(D.GRUB, feet_x=11)
    grub_bite = grub.stretch_x(1.15).shift(2, 0)
    standard("TallowGrub", grub, {"Idle": 1, "Run": 5, "Attack0": 4, "Special": 5}, split=2,
             strikes={"Attack0": grub_bite})

    moth = Spr.parse(D.MOTH_UP, feet_x=9).shift(0, -9)
    moth_dn = Spr.parse(D.MOTH_DOWN, feet_x=9).shift(0, -9)
    flap = [moth, moth_dn, moth, moth_dn]
    anims = [("Idle", [moth, moth.shift(0, -1), moth_dn.shift(0, -1), moth_dn], None),
             ("Run", [moth, moth_dn.shift(0, -1), moth.shift(0, -2), moth_dn.shift(0, -1)], None),
             ("Dead", [moth.snuff().rotate_down()], None), ("Statue", [moth.stone()], None),
             ("Knockback", [moth_dn.shift(-2, 0)], [0.2]), ("Portrait", [moth], [0.2]),
             ("Attack0", [moth, moth_dn.shift(-1, 0), moth.shift(2, 0).flare(1), moth_dn.shift(2, 0), moth], None),
             ("Special", [(moth if i % 2 == 0 else moth_dn).shift(min(i, 6) - abs(i - 6) // 2, -(i % 3)) for i in range(13)], None)]
    w, h, feet = cell_for([f for a in anims for f in a[1]])
    img, man = pack("AshMoth", anims, w, h, feet, OUT)
    preview(img, man, os.path.join(OUT, "AshMoth_preview.png"), scale=4)
    print("built AshMoth")

    knight = Spr.parse(D.KNIGHT, feet_x=8)
    k_swing = knight.region_shift(lambda x, y, c: x >= 5, 2, -1).shift(1, 0)
    standard("WaxenKnight", knight, {"Idle": 1, "Run": 6, "Attack0": 5, "Attack1": 6, "Special": 9}, split=6,
             strikes={"Attack0": k_swing, "Attack1": k_swing.shift(1, 0)}, special_strike=k_swing.shift(3, 0))

    ch = Spr.parse(D.CHANDLER, feet_x=8)
    ch_throw = ch.region_shift(lambda x, y, c: x >= 6 and y > -8, 1, -3)
    standard("Chandler", ch, {"Idle": 1, "Run": 6, "Attack0": 4, "Attack1": 4, "Attack2": 4, "Attack3": 4, "Special": 2},
             split=4, strikes={"Attack%d" % i: ch_throw for i in range(4)})

    matron = Spr.parse(D.MATRON, feet_x=10)
    standard("MothMatron", matron, {"Idle": 1, "Run": 6, "Attack0": 9, "Special": 5}, split=5)

    cand = Spr.parse(D.CANDELABRA, feet_x=11)
    standard("Candelabra", cand, {"Idle": 1, "Run": 6, "Attack0": 5, "Special": 7}, split=5,
             strikes={"Attack0": cand.flare(2)})

    col = Spr.parse(D.COLOSSUS, feet_x=13)
    slam = col.region_shift(lambda x, y, c: y < -10, 0, 3).stretch_x(1.08)
    standard("TallowColossus", col, {"Idle": 1, "Run": 6, "Attack0": 13, "Attack1": 8, "Special": 8}, split=6,
             strikes={"Attack0": slam, "Attack1": slam}, special_strike=slam)

    wr = Spr.parse(D.WRAITH, feet_x=10).shift(0, -3)
    standard("LanternWraith", wr, {"Idle": 7, "Run": 4, "Attack0": 6, "Special": 6}, flyer=True)


if __name__ == "__main__":
    main()
