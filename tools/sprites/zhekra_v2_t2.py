"""Zhekra tier 2: Acid Spitter, Hive Soldier, Hive Hornet, Blood Siphon, Nasute, Amber Scarab. Built through
zhekra_v2_rigs.py (python3 zhekra_v2_rigs.py --only ZhkSpitter,...). Same renderer and rules as tier 1. T2 idle limit
28 x 26, and never a smaller footprint than the v1 sheet it replaces."""
import math
from zhekra_v2_rigs import (ZRig, Rig, Xf, chain, ik, lerp, segs, leg, gait6, legs6, antenna, wing, wing_blur, eye, mandible,
                            drip, puddle, dust, smear, splat, ground_shadow, arc_pts, sheet, tail_anims, SYNC, NOTES)
from zhekra_v2_t1 import banded


def walk_feet(i, n, base, stride, lift=1.2):
    """Feet for a list of legs alternating in two groups (even / odd index)."""
    out = []
    for k, (bx, by) in enumerate(base):
        t = (i / float(n) + (k % 2) * 0.5) % 1.0
        if t < 0.5:
            out.append((bx + lerp(stride, -stride, t / 0.5), by))
        else:
            u = (t - 0.5) / 0.5
            out.append((bx + lerp(-stride, stride, u), by - lift * math.sin(u * math.pi)))
    return out


def acid_sac(r, cx, cy, rx, ry, z, stage=1.0, ang=0.0, wob=0.0):
    """The Spitter's translucent acid sac: a glowing green bag whose size and glow follow `stage` (0 slack .. 3 full)."""
    k = 0.62 + 0.14 * stage
    rx, ry = rx * k + wob, ry * k - wob * 0.5
    r.ell(cx, cy, rx, ry, "acid", z, ang=ang, bias=0.25)
    if stage >= 1:
        r.ell(cx - rx * 0.15, cy + ry * 0.2, rx * (0.35 + 0.1 * stage), ry * (0.35 + 0.1 * stage), "aglow", z + 0.01, ang=ang,
              flat=2 if stage < 3 else 3)
    r.dot(cx - rx * 0.45, cy - ry * 0.5, "acid", 4, z + 0.02)
    if stage >= 2:
        r.dot(cx - rx * 0.1, cy + ry * 0.1, "aglow", 4, z + 0.02)
    # veins over the bag
    r.line(cx - rx * 0.7, cy + ry * 0.1, cx + rx * 0.3, cy - ry * 0.6, "acid", z + 0.015, tone=1)
    return (cx, cy, rx, ry)


# ================================================================== ACID SPITTER: an upright beetle with a sac on its back
def spitter(lean=0.0, bob=0.0, i=0, n=6, stride=0.0, stage=1.0, head=(0.0, 0.0), jaw=0.2, spout=0.0, arms=0.0,
            rear=0.0, hurt=False, dead=False, glob=None, extra=None, dust_at=None, wob=0.0, egg=None):
    r = ZRig(1.1)
    T = Xf(lean, (0.0, -7.0))
    # four walking legs under the abdomen, two raised forelegs
    hips = [T(-3.5, -6.5 + bob), T(0.5, -6.0 + bob), T(-2.5, -6.8 + bob), T(1.5, -6.4 + bob)]
    base = [(-12.5, 0.0), (5.5, 0.0), (-9.5, 0.0), (9.0, 0.0)]
    feet = walk_feet(i, n, base, stride) if stride else base
    if dead: feet = [(h[0] + [-2, 2, -1, 3][k], h[1] - 2.5) for k, h in enumerate(hips)]
    for k in (2, 3):
        leg(r, hips[k], feet[k], 4.4, 5.0, -2.0, "dchit", near=False, bend=-1 if k == 2 else 1, rad=0.5)
    # abdomen (low, behind) and the upright thorax
    ab = T(-2.5, -8.5 + bob)
    r.ell(ab[0] - 0.6, ab[1], 7.7, 5.2, "ochit", 0.0, ang=-15 + lean * 0.3, bias=0.05)
    for kk in range(3):
        r.line(ab[0] - 4 + kk * 2.6, ab[1] - 3.4 + kk * 0.6, ab[0] - 4.6 + kk * 2.6, ab[1] + 3.0, "ochit", 0.002, tone=1)
    r.ell(ab[0] + 0.5, ab[1] + 2.0, 4.0, 1.6, "dchit", 0.01)
    th = T(2.2 + rear * -0.8, -12.5 + bob - rear)
    r.ell(th[0], th[1], 3.6, 5.0, "ochit", 0.2, ang=20 - rear * 8, bias=0.1)
    for k in (0, 1):
        leg(r, hips[k], feet[k], 4.4, 5.0, 1.5, "ochit", near=True, bend=-1 if k == 0 else 1, rad=0.7)
    # the sac, slung on the back like a pack
    sc = acid_sac(r, *T(-4.0, -14.6 + bob - rear * 0.5), 6.8, 6.8, 0.6, stage=stage, ang=-20, wob=wob)
    # strap plates over the sac
    r.line(sc[0] + sc[2] * 0.6, sc[1] - sc[3] * 0.6, sc[0] + sc[2] * 0.9, sc[1] + sc[3] * 0.5, "ochit", 0.65, tone=2)
    # head with a spout mouth
    hx, hy = T(4.5 + head[0], -17.5 + bob - rear + head[1])
    r.ell(hx, hy, 3.0, 2.7, "ochit", 0.8, bias=0.1)
    eye(r, hx + 0.6, hy - 0.8, 0.85, glint=not dead, big=True)
    if hurt and not dead: r.dot(hx + 0.6, hy - 0.8, "white", 2, 0.86)
    sa = -15 + spout
    sp = chain(hx + 2.2, hy + 0.6, [(2.2, sa), (2.0, sa + 10)])
    r.tube(sp, [1.2, 1.0, 0.8 + jaw * 0.4], "ochit", 0.82)
    r.dot(sp[-1][0], sp[-1][1], "aglow", 3 if jaw > 0.4 else 2, 0.83)
    antenna(r, (hx - 0.6, hy - 2.0), -140, 3.6, 60, 0.79)
    antenna(r, (hx + 0.4, hy - 2.1), -110, 3.2, 70, 0.78, tone=1)
    # raised forelegs (the "arms"), clawing the air
    sh = T(4.0, -12.0 + bob - rear)
    for k, (dx, dy) in enumerate(((3.5 + arms * 2.0, 1.5 - arms * 3.0), (2.5 + arms, 2.8 - arms * 1.5))):
        leg(r, (sh[0] - k * 0.8, sh[1] + k * 0.5), (sh[0] + dx, sh[1] + dy), 2.4, 2.6, 1.0 if k == 0 else -0.5,
            "ochit" if k == 0 else "dchit", near=k == 0, bend=1)
    if glob:
        gx, gy, gk = glob
        r.ell(sp[-1][0] + gx, sp[-1][1] + gy, 1.6, 1.3, "aglow", 3.0, flat=3)
        r.dot(sp[-1][0] + gx - 0.5, sp[-1][1] + gy - 0.4, "aglow", 4, 3.01)
        if gk: smear(r, [(sp[-1][0] + gx - 3, sp[-1][1] + gy), (sp[-1][0] + gx - 1.5, sp[-1][1] + gy)], "aglow", 2, 3.0)
    if egg:
        ex, ey, ek = egg
        r.ell(ex, ey, 1.6, 2.0, "cream", 2.0, bias=0.2)
        if ek: r.dot(ex - 0.4, ey - 0.6, "aglow", 3, 2.01)
    if dust_at: dust(r, *dust_at)
    if extra: extra(r, sp[-1], sc)
    return r.resolve()


def spitter_sheet(outdir):
    S = spitter
    anims = []
    for st, sfx in ((0, ""), (1, "1"), (2, "2"), (3, "3")):
        g = 1.0 if st == 3 else 0.0
        idle = [S(stage=st, bob=[0, 0.3, 0.6, 0.3][i], wob=[0, 0.3, 0.5 + g * 0.3, 0.3][i], jaw=[0.2, 0.3, 0.5, 0.3][i],
                  arms=[0.0, 0.2, 0.4, 0.2][i]) for i in range(4)]
        run = [S(stage=st, i=i, n=6, stride=2.2, bob=0.5 * abs(math.sin(i / 6 * math.tau)), lean=6,
                 wob=0.4 * math.sin(i / 6 * math.tau), arms=0.3) for i in range(6)]
        anims += [("Idle" + sfx, idle, [0.14, 0.12, 0.14, 0.12]), ("Run" + sfx, run, [0.08] * 6)]
    # Lob: the sac squeezes (0, 1), the head rears (2), SPIT along the floor (3), follow (4, 5)
    lob = [S(stage=1.5, rear=0.8, lean=-6, jaw=0.3, arms=0.5), S(stage=1.0, rear=1.6, lean=-10, jaw=0.6, arms=0.9, spout=-20),
           S(stage=0.8, rear=2.0, lean=-12, jaw=0.9, arms=1.0, spout=-25),
           S(stage=0.6, rear=0.0, lean=10, jaw=1.0, spout=25, glob=(2.0, 1.0, 1), arms=0.2),
           S(stage=0.6, lean=6, jaw=0.6, spout=15, glob=(6.0, 3.0, 1)), S(stage=0.8, jaw=0.3)]
    # LobFull: the full sac pumps empty into a double glob
    full = [S(stage=3.0, rear=0.8, lean=-6, jaw=0.3, arms=0.5, wob=0.6), S(stage=3.2, rear=1.6, lean=-10, jaw=0.6, arms=0.9, spout=-20, wob=1.0),
            S(stage=2.0, rear=2.2, lean=-14, jaw=1.0, arms=1.0, spout=-25, wob=0.8),
            S(stage=0.6, rear=0.0, lean=12, jaw=1.0, spout=25, glob=(2.5, 1.0, 1), arms=0.2,
              extra=lambda r, sp, sc: r.ell(sp[0] + 4.5, sp[1] + 1.5, 2.2, 1.8, "aglow", 3.1, flat=3)),
            S(stage=0.0, lean=8, jaw=0.6, spout=15, glob=(7.0, 3.0, 1)), S(stage=0.0, jaw=0.3)]
    # Egg: crouch (0, 1), the abdomen tips (2, 3), LAY (4: the egg drops behind at (-8, -2)), rise (5, 6)
    egg = [S(stage=1, bob=0.5, lean=4), S(stage=1, bob=1.2, lean=8, jaw=0.4), S(stage=1, bob=1.6, lean=12, jaw=0.6),
           S(stage=1, bob=1.8, lean=14, egg=(-8.5, -4.0, 0)), S(stage=1, bob=1.4, lean=10, egg=(-8.5, -2.0, 1)),
           S(stage=1, bob=0.6, lean=4), S(stage=1)]
    anims += [("Lob", lob, [0.12, 0.1, 0.1, 0.06, 0.1, 0.12]), ("LobFull", full, [0.12, 0.1, 0.1, 0.06, 0.1, 0.12]),
              ("Egg", egg, [0.12, 0.1, 0.1, 0.12, 0.12, 0.1, 0.12])]
    idle0 = anims[0][1][0]
    d = [S(stage=1, hurt=True, rear=1.5, lean=-14, arms=1.0, jaw=1.0), S(stage=0.5, hurt=True, lean=-35, bob=2.0, arms=0.6),
         S(stage=0.0, dead=True, lean=-60, bob=5.0, dust_at=(-4, 0, 0)), S(stage=0.0, dead=True, lean=-75, bob=6.5,
                                                                         extra=lambda r, sp, sc: puddle(r, -2.0, 5.0, -3.0))]
    knock = S(stage=1, hurt=True, rear=1.8, lean=-16, arms=1.0, jaw=0.9)
    anims += tail_anims(idle0, d, [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("ZhkSpitter", anims, outdir, scale=6)


SYNC["ZhkSpitter"] = {"Lob": [("SPIT: the glob leaves the spout at (10, -18), launched along the floor at (10, -1)", 3)],
                      "LobFull": [("SPIT the full sac: a double glob, the sac empties", 3)],
                      "Egg": [("LAY: the egg drops behind at (-8, -2)", 4)]}
NOTES["ZhkSpitter"] = "Acid Sac: Idle/Run (slack), Idle1/Run1 .. Idle3/Run3 (full, glowing). LobFull empties a full sac."


# ================================================================== HIVE SOLDIER: armoured ant with scythe mandibles
def scythe(r, base, ang, ln, z, mat="soot", rad=0.9, smear_from=None):
    """A sickle mandible: a thick root curving into a long point."""
    pts = chain(base[0], base[1], [(ln * 0.35, ang), (ln * 0.3, ang + 25), (ln * 0.2, ang + 55), (ln * 0.15, ang + 85)])
    r.tube(pts, [rad, rad * 0.9, rad * 0.7, rad * 0.45, 0.35], mat, z)
    r.dot(pts[-1][0], pts[-1][1], "white", 3, z + 0.01)
    r.line(pts[1][0], pts[1][1] + 0.6, pts[3][0], pts[3][1] + 0.4, "amber", z + 0.005, tone=3)   # the honed inner edge
    if smear_from is not None:
        a0 = smear_from
        for k in range(3):
            aa = math.radians(lerp(a0, ang + 40, k / 2.0))
            r.dot(base[0] + ln * 0.8 * math.cos(aa), base[1] + ln * 0.8 * math.sin(aa), "white", 2, z - 0.01)
    return pts[-1]


def soldier(lean=0.0, bob=0.0, i=0, n=6, stride=0.0, near=-20.0, far=-5.0, head=(0.0, 0.0), raised=0.0, crouch=0.0,
            antn=0.0, hurt=False, dead=False, glint=False, smear_near=None, smear_far=None, dust_at=None, extra=None):
    r = ZRig(1.05)
    T = Xf(lean, (2.0, -6.0))
    c = crouch
    bob = bob - 2.2
    gaster = T(-5.2, -8.8 + bob + c * 0.5)
    pet = T(-2.2, -9.0 + bob + c * 0.6)
    tho = T(0.0, -9.4 + bob + c)
    hips = [T(1.6, -7.8 + bob + c), T(0.0, -7.6 + bob + c), T(-1.6, -7.6 + bob + c),
            T(2.0, -8.0 + bob + c), T(0.4, -7.9 + bob + c), T(-1.2, -8.0 + bob + c)]
    base = [(9.5, 0.0), (2.0, 0.0), (-8.5, 0.0), (11.0, 0.0), (3.5, 0.0), (-7.0, 0.0)]
    feet = gait6(i, n, hips, base, stride=stride, lift=1.6) if stride else base
    if dead: feet = [(h[0] + [3, 0.5, -2, 4, 1, -1.5][k], h[1] - 3.0) for k, h in enumerate(hips)]
    legs6(r, hips, feet, [6.5, 5.5, 5.6], [8.5, 8.0, 8.6], 1.4, -2.0, mat="soot", far_mat="dchit", rad=0.6, far_rad=0.5)
    # gaster, waist knot, thorax
    r.ell(gaster[0], gaster[1], 5.8, 5.0, "soot", 0.0, ang=-20, bias=0.08)
    r.line(gaster[0] - 3.0, gaster[1] - 2.0, gaster[0] - 2.0, gaster[1] + 3.0, "soot", 0.005, tone=1)
    r.line(gaster[0] - 0.6, gaster[1] - 3.4, gaster[0] + 0.4, gaster[1] + 3.4, "soot", 0.005, tone=1)
    r.ell(gaster[0] - 0.8, gaster[1] - 1.8, 2.6, 1.0, "soot", 0.01, flat=4)
    r.ell(pet[0], pet[1], 1.3, 1.5, "soot", 0.1)
    r.ell(tho[0], tho[1], 3.8, 2.8, "soot", 0.2, ang=-10, bias=0.1)
    r.dot(tho[0] - 1.0, tho[1] - 1.8, "soot", 4, 0.21)
    # the heavy head, held forward
    hx, hy = T(5.0 + head[0], -12.0 + bob + c + head[1] - raised * 2.0)
    r.ell(hx - 0.3, hy + 0.3, 5.0, 4.6, "soot", 0.4, bias=0.06)
    r.ell(hx - 1.0, hy - 1.6, 2.4, 1.1, "soot", 0.41, flat=4)
    eye(r, hx + 1.6, hy - 1.0, 0.45, glow="rglow" if not dead else None, glint=False)
    if glint and not dead:
        r.dot(hx + 2.4, hy - 2.0, "white", 4, 0.46); r.dot(hx + 3.0, hy - 2.6, "white", 3, 0.46)
    if hurt and not dead: r.dot(hx + 1.6, hy - 1.0, "white", 3, 0.47)
    a_n = antn
    antenna(r, (hx + 0.5, hy - 3.2), -100 + a_n, 6.0, 70 - a_n * 0.6, 0.38)
    antenna(r, (hx - 0.6, hy - 3.0), -120 + a_n, 5.5, 60 - a_n * 0.6, 0.37, tone=1)
    # scythe mandibles: near / far angles (deg, 0 = straight ahead, - = raised)
    tips = []
    tips.append(scythe(r, (hx + 2.6, hy + 1.4), far, 9.0, 0.3, mat="rchit", rad=1.2, smear_from=smear_far))
    tips.append(scythe(r, (hx + 3.0, hy + 1.8), near, 9.5, 0.6, mat="rchit", rad=1.4, smear_from=smear_near))
    if dust_at: dust(r, *dust_at)
    if extra: extra(r, tips)
    return r.resolve()


def soldier_sheet(outdir):
    S = soldier
    idle = [S(bob=[0, 0.3, 0.5, 0.3][i], near=[-62, -65, -68, -64][i], far=[-48, -51, -54, -50][i], antn=[0, 6, 10, 4][i]) for i in range(4)]
    run = [S(i=i, n=6, stride=2.4, bob=0.6 * abs(math.sin(i / 6 * math.tau)), lean=6, near=-40, far=-28) for i in range(6)]
    # Scythe: wind back high (0, 1), SWEEP 1 near blade (2), recoil (3), SWEEP 2 far blade (4), follow (5), settle (6)
    scy = [S(lean=-6, near=-70, far=-40, head=(-1.0, -0.5)), S(lean=-10, near=-95, far=-55, head=(-1.5, -1.0), crouch=0.5),
           S(lean=10, near=45, far=-60, head=(2.0, 0.5), smear_near=-90, dust_at=(8, 0, 0)),
           S(lean=6, near=60, far=-80, head=(1.5, 0.5)),
           S(lean=12, near=40, far=50, head=(2.5, 0.8), smear_far=-80),
           S(lean=6, near=30, far=60, head=(1.5, 0.5)), S(near=-10, far=0)]
    # Guard: plant the feet (0), scythes rise (1, 2), held high (3); GuardHold loops antenna-flat, eyes glinting
    guard = [S(crouch=0.6, near=-35, far=-20, antn=20), S(crouch=1.0, near=-75, far=-55, antn=40, raised=0.5),
             S(crouch=1.2, near=-105, far=-85, antn=60, raised=1.0), S(crouch=1.2, near=-110, far=-92, antn=70, raised=1.0, glint=True)]
    hold = [S(crouch=1.2, near=-110, far=-92, antn=70, raised=1.0, glint=k == 0, bob=[0, 0.3][k]) for k in range(2)]
    # Strike: the ambush: both scythes slam down at once (0 is already the strike), hold (1), recover (2, 3)
    strike = [S(lean=16, near=50, far=40, head=(3.0, 1.0), crouch=0.4, smear_near=-110, smear_far=-95, dust_at=(9, 0, 0)),
              S(lean=14, near=60, far=55, head=(3.0, 1.0), crouch=0.4, dust_at=(9, 0, 1)),
              S(lean=6, near=20, far=10, head=(1.0, 0.5)), S(near=-15, far=-5)]
    d = [S(hurt=True, lean=-14, near=-80, far=-60, head=(-1, -1)), S(hurt=True, lean=-30, bob=1.5, near=-30, far=-10),
         S(dead=True, lean=10, bob=4.0, near=40, far=30, dust_at=(0, 0, 0)), S(dead=True, lean=12, bob=5.0, near=50, far=45)]
    knock = S(hurt=True, lean=-16, near=-85, far=-65, head=(-1.5, -1.5))
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.08] * 6),
             ("Scythe", scy, [0.12, 0.12, 0.05, 0.08, 0.05, 0.08, 0.12]),
             ("Guard", guard, [0.08, 0.08, 0.08, 0.1]), ("GuardHold", hold, [0.2, 0.2]),
             ("Strike", strike, [0.05, 0.12, 0.1, 0.12])]
    anims += tail_anims(idle[0], d, [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("ZhkSoldier", anims, outdir, scale=6)


SYNC["ZhkSoldier"] = {"Scythe": [("SWEEP 1: near blade to (16, -6); box 20 x 18 at (11, -9)", 2), ("SWEEP 2", 4)],
                      "Strike": [("AMBUSH: both blades down at (15, -5) on the first frame", 0)]}
NOTES["ZhkSoldier"] = "Scythe Guard: Guard raises the scythes, GuardHold loops while it waits, Strike is the 0.1 s ambush."


# ================================================================== HIVE HORNET: a big hunter hornet
def hornet(alt=7.0, tilt=0.0, curl=0.0, wing_a=-115.0, blur=1, jaw=0.2, hurt=False, dead=False, glow=0.0, legs=0.0,
           extra=None, shadow=True, x=0.0, streak=0, fold=0.0):
    r = ZRig(1.08)
    if shadow: ground_shadow(r, x, 4.5 if alt < 10 else 3.5)
    wx, wy = x - 1.0, -alt - 6.0
    T = Xf(tilt, (wx, wy)); C = Xf(-curl, (wx, wy))
    ab = [T(*C(wx + dx, wy + dy)) for dx, dy in ((-0.8, 0.4), (-4.2, 2.0), (-8.2, 4.2), (-11.0, 6.4))]
    r.tube(ab, [2.0, 3.6, 3.0, 1.2], banded(ab[0], ab[3], 4.0, "hblk", "hyel", phase=0.6), 0.1, bias=0.05)
    # the amber chevrons on the abdomen
    for k in (1, 2):
        cx, cy = ab[k]
        r.polyline([(cx - 1.2, cy - 1.8), (cx, cy - 0.8), (cx + 1.2, cy - 1.8)], "amber", 0.12, tones=[4, 4])
    sa = math.atan2(ab[3][1] - ab[2][1], ab[3][0] - ab[2][0])
    st = (ab[3][0] + 3.0 * math.cos(sa), ab[3][1] + 3.0 * math.sin(sa))
    r.tube([ab[3], st], [0.8, 0.35], "hblk", 0.13)
    r.dot(st[0], st[1], "aglow", 3 + (1 if glow else 0), 0.14)
    root = T(wx + 2.6, wy - 2.8)
    wa = wing_a + fold * 60
    wing(r, root, wa - 10, 11.0 - fold * 3, 4.4, -0.6, near=False)
    wing(r, (root[0] + 1.0, root[1] + 0.3), wa + 8, 10.4 - fold * 3, 4.0, -0.4, near=True)
    if blur: wing_blur(r, root, wa + 45, wa + 75, 7.0, -0.7, n=2)
    th = T(wx + 3.4, wy - 0.8)
    r.ell(th[0], th[1], 3.4, 3.0, "hblk", 0.2, bias=0.12)
    r.ell(th[0] - 0.4, th[1] - 2.0, 1.8, 0.7, "hyel", 0.21, flat=3)
    hd = T(wx + 7.6, wy - 0.4)
    r.ell(hd[0], hd[1], 2.6, 2.5, "hyel", 0.3, bias=0.05)
    r.ell(hd[0] - 0.6, hd[1] - 1.0, 1.8, 1.4, "hblk", 0.31, bias=0.1)
    eye(r, hd[0] + 0.2, hd[1] - 0.6, 0.32, glint=not dead, big=True)
    if hurt and not dead: r.dot(hd[0] + 0.2, hd[1] - 0.6, "white", 2, 0.33)
    a = 60 + 40 * jaw
    mandible(r, (hd[0] + 2.0, hd[1] + 1.3), a, 2.6, -55, 0.34, rad=0.55, mat="amber")
    antenna(r, (hd[0] + 0.8, hd[1] - 2.2), -80 + tilt * 0.3, 5.6, 65 if not dead else 110, 0.29)
    for k, dx in enumerate((-1.6, 0.4, 2.2)):
        hip = T(wx + 3.2 + dx, wy + 2.0)
        foot = (hip[0] - 1.8 + legs * (k - 1) * 0.7 - fold * 2 + k * 0.8, hip[1] + 4.4 - fold)
        leg(r, hip, foot, 2.4, 2.8, 0.4 if k != 1 else 0.05, "hblk" if k != 1 else "dchit", near=k != 1, bend=-1, rad=0.45 if k != 1 else 0)
    if streak:
        for k in range(streak): smear(r, [(hd[0] - 10 - 3 * k, hd[1] + k), (hd[0] - 6 - 3 * k, hd[1] + k)], "wblur", 2, -1.0)
    if extra: extra(r, hd, st)
    return r.resolve()


def hornet_sheet(outdir):
    H = hornet
    idle = [H(alt=[5.0, 5.3, 5.6, 5.3][i], wing_a=[-150, -132, -146, -128][i], curl=[0, 4, 8, 4][i], legs=[0, 0.5, 1, 0.5][i]) for i in range(4)]
    run = [H(alt=6.5 + 0.6 * math.sin(i / 6 * math.tau), tilt=12, wing_a=[-150, -100, -140, -95, -145, -105][i], curl=-5,
             legs=1.0, streak=1 if i % 2 else 0) for i in range(6)]
    # Volley: the abdomen curls under (0-2), FIRE the fan (3, a flash at the sting), recoil (4), settle (5)
    vol = [H(alt=7, curl=30), H(alt=7.5, curl=70, tilt=-6), H(alt=7.5, curl=105, tilt=-10),
           H(alt=7.5, curl=115, tilt=-12, extra=lambda r, h, s: [r.dot(s[0] + 1, s[1] + dy, "white", 3, 2.0) for dy in (-1, 0, 1)]),
           H(alt=8.0, curl=70, tilt=4), H(alt=7.0, curl=15)]
    # Mark: the scent gland glows (0-2), FLICK the dart (4), hover (5, 6)
    mark = [H(alt=7, curl=20, glow=1), H(alt=7.5, curl=60, glow=1, tilt=-6,
                                          extra=lambda r, h, s: r.dot(s[0], s[1] - 1, "jelly", 3, 2.0)),
            H(alt=8.0, curl=95, glow=1, tilt=-10, extra=lambda r, h, s: [r.dot(s[0], s[1] - 1, "jelly", 4, 2.0), r.dot(s[0] + 1, s[1] - 2, "jelly", 3, 2.0)]),
            H(alt=8.0, curl=110, glow=1, tilt=-12, extra=lambda r, h, s: r.ell(s[0] + 0.5, s[1], 1.4, 1.2, "jelly", 2.0, flat=3)),
            H(alt=8.0, curl=115, tilt=-12, extra=lambda r, h, s: r.dot(s[0] + 2, s[1], "white", 4, 2.0)),
            H(alt=7.5, curl=60, tilt=2), H(alt=7.0, curl=10)]
    d = [H(alt=7, tilt=-30, blur=0, wing_a=-165, hurt=True, curl=30), H(alt=4, tilt=-50, blur=0, wing_a=-178, hurt=True, curl=20, fold=0.4),
         H(alt=-3.0, tilt=12, blur=0, wing_a=175, dead=True, curl=-10, fold=1.0, shadow=False, extra=lambda r, h, s: dust(r, 0, 0, 0)),
         H(alt=-3.5, tilt=14, blur=0, wing_a=178, dead=True, curl=-14, fold=1.0, shadow=False)]
    knock = H(alt=8, tilt=-28, blur=0, wing_a=-165, hurt=True, curl=25)
    anims = [("Idle", idle, [0.06] * 4), ("Run", run, [0.06] * 6), ("Volley", vol, [0.12, 0.1, 0.1, 0.06, 0.1, 0.12]),
             ("Mark", mark, [0.12, 0.1, 0.1, 0.1, 0.06, 0.1, 0.12])]
    anims += tail_anims(idle[0], d, [0.08, 0.1, 0.12, 0.4], knock)
    return sheet("ZhkHornet", anims, outdir, scale=6)


SYNC["ZhkHornet"] = {"Volley": [("FIRE: three stingers leave the curled sting at (8, -9)", 3)],
                     "Mark": [("FLICK: the pheromone dart leaves the sting at (8, -9)", 4)]}


# ================================================================== BLOOD SIPHON: a mosquito drone with a blood belly
def siphon(alt=8.0, tilt=0.0, fill=0.0, wing_a=-120.0, blur=1, nose=0.0, reach=0.0, legs=0.0, hurt=False, dead=False,
           extra=None, shadow=True, x=0.0, streak=0, fold=0.0, sag=0.0):
    r = ZRig(1.18)
    if shadow: ground_shadow(r, x, 4.0)
    wx, wy = x - 1.0, -alt - 5.0
    T = Xf(tilt, (wx, wy))
    # long dangling legs (they reach the floor when it lands)
    for k, dx in enumerate((-1.0, 0.6, 2.2)):
        hip = T(wx + 2.4 + dx, wy + 1.8)
        for side in (0, 1):
            fx = hip[0] + (-6.0 + k * 4.0 + legs * (k - 1)) * (1.0 if side else 0.8) - fold * 2
            fy = min(-0.0, hip[1] + 7.5 - fold * 2) if not dead else hip[1] + 2
            leg(r, hip, (fx, fy), 4.2, 4.6, 0.4 if side else -0.4, "fuzz" if side else "dchit", near=bool(side),
                bend=-1 if k < 1 else 1)
    # belly: thin when empty, a swollen red bag when full
    k = fill / 3.0
    ab = [T(wx + dx, wy + dy) for dx, dy in ((-0.8, 0.4), (-4.0 - k, 1.6 + k + sag), (-7.6 - k * 1.5, 3.0 + k * 1.2 + sag))]
    rads = [1.8, 2.5 + 2.2 * k, 1.9 + 1.8 * k]
    r.tube(ab, rads, banded(ab[0], ab[2], 3.0, "fuzz", "dchit", phase=0.4) if fill < 0.5 else "blood", 0.1, bias=0.1)
    if fill >= 0.5:
        r.ell(ab[1][0] - 0.5, ab[1][1] - rads[1] * 0.35, rads[1] * 0.5, rads[1] * 0.3, "blood", 0.11, flat=4)
        r.line(ab[0][0] - 1, ab[0][1] + 0.5, ab[2][0] + 1, ab[2][1] - 0.5, "blood", 0.12, tone=1)
    root = T(wx + 2.0, wy - 2.2)
    wa = wing_a + fold * 60
    wing(r, root, wa - 15, 9.0 - fold * 3, 2.8, -0.6, near=False)
    wing(r, (root[0] + 0.8, root[1] + 0.3), wa + 5, 8.6 - fold * 3, 2.6, -0.4, near=True)
    if blur: wing_blur(r, root, wa + 45, wa + 75, 7.0, -0.7, n=2)
    th = T(wx + 2.6, wy - 0.6)
    r.ell(th[0], th[1], 3.0, 2.7, "fuzz", 0.2, bias=0.12)
    r.ell(th[0] - 0.4, th[1] - 1.8, 1.4, 0.6, "fuzz", 0.21, flat=4)
    hd = T(wx + 5.8, wy - 0.2)
    r.ell(hd[0], hd[1], 2.1, 2.0, "fuzz", 0.3, bias=0.05)
    eye(r, hd[0] + 0.3, hd[1] - 0.5, 0.32, glint=not dead, big=True)
    if hurt and not dead: r.dot(hd[0] + 0.3, hd[1] - 0.5, "white", 2, 0.33)
    na = 20 + nose
    tip = chain(hd[0] + 1.4, hd[1] + 0.6, [(6.5 + reach, na)])[-1]
    r.line(hd[0] + 1.4, hd[1] + 0.6, tip[0], tip[1], "dchit", 0.35, tone=3)
    r.dot(tip[0], tip[1], "blood", 3, 0.36)
    antenna(r, (hd[0] + 0.6, hd[1] - 1.4), -50 + tilt * 0.3, 4.2, 40, 0.29)
    antenna(r, (hd[0] + 0.2, hd[1] - 1.4), -70 + tilt * 0.3, 3.8, 50, 0.28, tone=1)
    if streak:
        for kk in range(streak): smear(r, [(hd[0] - 9 - 3 * kk, hd[1] + kk), (hd[0] - 5 - 3 * kk, hd[1] + kk)], "wblur", 2, -1.0)
    if extra: extra(r, hd, tip)
    return r.resolve()


def siphon_sheet(outdir):
    Sp = siphon
    anims = []
    for st, sfx in ((0, ""), (1, "1"), (2, "2"), (3, "3")):
        al = 5.5 - st * 0.5
        idle = [Sp(fill=st, alt=al + [0, 0.5, 1.0, 0.5][i], wing_a=[-150, -105, -140, -100][i], legs=[0, 0.4, 0.8, 0.4][i],
                   sag=[0, 0.2, 0.4, 0.2][i] * st) for i in range(4)]
        run = [Sp(fill=st, alt=al + 0.6 * math.sin(i / 6 * math.tau), tilt=10, wing_a=[-150, -100, -140, -95, -145, -105][i],
                  legs=1.0, streak=1 if i % 2 else 0) for i in range(6)]
        anims += [("Idle" + sfx, idle, [0.06] * 4), ("Run" + sfx, run, [0.07] * 6)]
    # Stab: rear back (0, 1), STAB (2, the needle shoots out), hold (3), pull out (4, 5)
    stab = [Sp(tilt=-10, nose=-10, reach=-1), Sp(tilt=-16, nose=-20, reach=-2, alt=9),
            Sp(tilt=18, nose=10, reach=4, x=2, streak=1), Sp(tilt=20, nose=12, reach=5, x=2),
            Sp(tilt=8, nose=5, reach=1, x=1), Sp(nose=0)]
    # Feed: rise (0), DIVE onto the hero (1), stab x3 (2-4, 5-7: the needle pumps in and out), lift off (8)
    feed = [Sp(alt=11, tilt=-12, nose=-20),
            Sp(alt=5, tilt=25, nose=20, reach=2, x=3, streak=2)]
    for k in range(3):
        feed += [Sp(alt=4, tilt=30, nose=40, reach=4, x=4, fill=k * 0.3), Sp(alt=4.5, tilt=24, nose=34, reach=1, x=4, fill=k * 0.3 + 0.15)]
    feed += [Sp(alt=8, tilt=0, nose=5, x=2)]
    anims += [("Stab", stab, [0.12, 0.1, 0.05, 0.08, 0.1, 0.12]),
              ("Feed", feed, [0.14, 0.08, 0.06, 0.1, 0.06, 0.1, 0.06, 0.1, 0.14])]
    idle0 = anims[0][1][0]
    d = [Sp(alt=8, tilt=-30, blur=0, wing_a=-165, hurt=True), Sp(alt=4, tilt=-45, blur=0, wing_a=-178, hurt=True, fold=0.4),
         Sp(alt=0.5, tilt=10, blur=0, wing_a=175, dead=True, fold=1.0, shadow=False, extra=lambda r, h, t: dust(r, 0, 0, 0)),
         Sp(alt=0.0, tilt=12, blur=0, wing_a=178, dead=True, fold=1.0, shadow=False)]
    knock = Sp(alt=9, tilt=-28, blur=0, wing_a=-165, hurt=True)
    anims += tail_anims(idle0, d, [0.08, 0.1, 0.12, 0.4], knock)
    return sheet("ZhkSiphon", anims, outdir, scale=6)


SYNC["ZhkSiphon"] = {"Stab": [("STAB: needle tip at (16, -6); box 12 x 10 at (14, -6)", 2)],
                     "Feed": [("DIVE onto the hero", 1), ("stab 1", 2), ("stab 2", 4), ("stab 3", 6)]}
NOTES["ZhkSiphon"] = "Engorge: Idle/Run (empty) .. Idle3/Run3 (full: a swollen red belly, it hangs lower)."


# ================================================================== NASUTE: a termite soldier whose head is a glue nozzle
def nasute(lean=0.0, bob=0.0, i=0, n=6, stride=0.0, aim=-20.0, swell=0.0, puff=0.0, rear=0.0, hurt=False, dead=False,
           extra=None, dust_at=None, specks=None):
    r = ZRig(1.18)
    T = Xf(lean, (0.0, -5.0))
    bob = bob - 2.8
    hips = [T(1.2, -4.0 + bob), T(-0.6, -3.8 + bob), T(-2.4, -3.8 + bob), T(1.8, -4.2 + bob), T(0.0, -4.0 + bob), T(-1.8, -4.2 + bob)]
    base = [(4.0, 0.0), (0.0, 0.0), (-4.5, 0.0), (5.0, 0.0), (1.0, 0.0), (-3.5, 0.0)]
    feet = gait6(i, n, hips, base, stride=stride, lift=1.2) if stride else base
    if dead: feet = [(h[0] + [2, 0, -2, 3, 1, -1][k], h[1] - 2.5) for k, h in enumerate(hips)]
    legs6(r, hips, feet, 3.4, 3.8, 1.2, -2.0, mat="chit", far_mat="dchit", rad=0.5, far_rad=0.45)
    ab = T(-5.5, -5.0 + bob)
    r.ell(ab[0], ab[1], 4.8, 4.0, "pale", 0.0, bias=0.05)
    for k in range(3):
        r.line(ab[0] - 3 + k * 2.4, ab[1] - 2.8, ab[0] - 3.5 + k * 2.4, ab[1] + 2.6, "pale", 0.001, tone=1)
    tho = T(-0.5, -5.6 + bob)
    r.ell(tho[0], tho[1], 2.6, 2.0, "pale", 0.2, bias=0.1)
    # the head: a big brown bulb drawn up into a nozzle that aims at `aim` degrees
    hc = T(4.5, -9.5 + bob - rear)
    s = 1.0 + 0.12 * swell
    r.ell(hc[0], hc[1], 6.4 * s, 6.0 * s, "chit", 0.4, bias=0.12)
    r.ell(hc[0] - 1.6, hc[1] - 2.4, 2.4, 1.2, "chit", 0.41, flat=4)
    a = math.radians(aim)
    nz = [(hc[0] + 3.4 * math.cos(a), hc[1] + 3.4 * math.sin(a)), (hc[0] + 6.2 * math.cos(a), hc[1] + 6.2 * math.sin(a)),
          (hc[0] + 8.2 * math.cos(a), hc[1] + 8.2 * math.sin(a))]
    r.tube([(hc[0] + 1.0 * math.cos(a), hc[1] + 1.0 * math.sin(a))] + nz, [3.0, 2.2, 1.3, 0.8], "chit", 0.42, bias=0.05)
    r.ell(nz[-1][0], nz[-1][1], 1.0 + puff * 0.6, 0.9 + puff * 0.5, "glue", 0.45, flat=3 if puff else 2)
    if puff:
        r.ell(nz[-1][0] + math.cos(a) * 2.0, nz[-1][1] + math.sin(a) * 2.0, 1.6 * puff, 1.4 * puff, "glue", 0.46, flat=4)
    drip(r, nz[-1][0], nz[-1][1] + 1.0, 1 + int(swell), 0.44, mat="glue")
    # little eye spot and mandible nubs under the bulb
    r.dot(hc[0] + 1.0, hc[1] + 1.4, "dchit", 0, 0.43)
    mandible(r, (hc[0] + 1.6, hc[1] + 3.6), 50, 2.0, -40, 0.43, mat="pale", rad=0.45)
    if specks:
        for (sx, sy) in specks:
            r.ell(nz[-1][0] + sx, nz[-1][1] + sy, 0.9, 0.8, "glue", 3.0, flat=3)
    if dust_at: dust(r, *dust_at)
    if extra: extra(r, nz[-1], hc)
    return r.resolve()


def nasute_sheet(outdir):
    N = nasute
    idle = [N(bob=[0, 0.3, 0.5, 0.3][i], aim=[-20, -22, -25, -22][i], swell=[0, 0.5, 1, 0.5][i]) for i in range(4)]
    run = [N(i=i, n=6, stride=2.0, bob=0.4 * abs(math.sin(i / 6 * math.tau)), lean=4, aim=-12) for i in range(6)]
    # Specks: the bulb swells (0, 1), SQUIRT three specks (2, 3, 4), shake off (5)
    sp = [N(swell=1.5, aim=-8, rear=0.5), N(swell=2.5, aim=-4, rear=1.0, lean=-4),
          N(swell=1.5, aim=-2, puff=1.0, lean=4, specks=[(3, 0)]), N(swell=1.0, aim=-6, puff=0.8, lean=4, specks=[(5, 0), (2, -1)]),
          N(swell=0.5, aim=-10, puff=0.6, lean=3, specks=[(7, 1), (4, 0)]), N(aim=-18)]
    # ShoreUp: rear up (0, 1), the bulb pumps (2, 3), SPRAY resin up over itself and its kin (4), settle (5, 6)
    sh = [N(rear=1.0, lean=-6, aim=-40), N(rear=2.0, lean=-12, aim=-70, swell=1.5), N(rear=2.4, lean=-14, aim=-85, swell=3.0),
          N(rear=2.6, lean=-14, aim=-90, swell=3.5),
          N(rear=2.4, lean=-12, aim=-90, puff=1.6, extra=lambda r, t, h: [r.ell(t[0] + dx, t[1] - 4 + abs(dx) * 0.5, 1.0, 1.0, "amber", 3.0, flat=3) for dx in (-4, -1.5, 1.5, 4)]),
          N(rear=1.0, lean=-6, aim=-50, extra=lambda r, t, h: [r.ell(h[0] + dx, h[1] - 9 + abs(dx) * 0.3, 0.9, 0.9, "amber", 3.0, flat=2) for dx in (-6, 0, 6)]),
          N(aim=-20)]
    # Puff: the Bodyguard reaction: the nozzle whips round and puffs one speck (2)
    pf = [N(aim=-5, swell=1.0, lean=3), N(aim=0, swell=1.8, lean=6, rear=0.5), N(aim=0, puff=1.2, lean=8, specks=[(3, 0)]), N(aim=-12)]
    d = [N(hurt=True, rear=1.5, lean=-12, aim=-60), N(hurt=True, lean=-25, bob=1.0, aim=-20),
         N(dead=True, lean=15, bob=3.0, aim=30, dust_at=(0, 0, 0)), N(dead=True, lean=18, bob=3.5, aim=35,
                                                                    extra=lambda r, t, h: puddle(r, 4.0, 3.0, -3.0, mat="glue"))]
    knock = N(hurt=True, rear=1.8, lean=-14, aim=-65)
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.08] * 6),
             ("Specks", sp, [0.12, 0.12, 0.06, 0.06, 0.06, 0.12]), ("ShoreUp", sh, [0.12, 0.1, 0.1, 0.1, 0.12, 0.12, 0.12]),
             ("Puff", pf, [0.05, 0.05, 0.08, 0.1])]
    anims += tail_anims(idle[0], d, [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("ZhkNasute", anims, outdir, scale=6)


SYNC["ZhkNasute"] = {"Specks": [("speck 1 leaves the nozzle at (16, -12)", 2), ("speck 2", 3), ("speck 3", 4)],
                     "ShoreUp": [("SPRAY: resin plates for it and its kin", 4)],
                     "Puff": [("PUFF: one speck at the hero", 2)]}


# ================================================================== AMBER SCARAB: a dung beetle with a resin ball
def amber_ball(r, x, y, R, z, rot=0.0, glow=0.0, bugs=0, mat="amber"):
    """A ball of resin resting with its bottom at y; rot turns its inner streaks."""
    cy = y - R
    r.ell(x, cy, R, R, mat, z, bias=0.1)
    if R >= 2.5:
        for k in range(2):
            a = math.radians(rot + k * 140)
            r.line(x + math.cos(a) * R * 0.6, cy + math.sin(a) * R * 0.6, x + math.cos(a + 1.2) * R * 0.5,
                   cy + math.sin(a + 1.2) * R * 0.5, mat, z + 0.001, tone=1)
        r.dot(x - R * 0.4, cy - R * 0.45, mat, 4, z + 0.002)
        r.dot(x - R * 0.2, cy - R * 0.6, mat, 4, z + 0.002)
    if glow: r.ell(x + R * 0.1, cy + R * 0.15, R * 0.5, R * 0.45, "jelly", z + 0.003, flat=2)
    return (x, cy)


BALL_R = {0: 1.2, 1: 2.8, 2: 3.9, 3: 4.9}


def scarab(lean=0.0, bob=0.0, i=0, n=6, stride=0.0, size=3, bx=0.0, by=0.0, rot=0.0, head=0.0, rear=0.0, kick=0.0,
           hurt=False, dead=False, extra=None, dust_at=None, ball=True, butt=0.0):
    r = ZRig(1.1)
    R = BALL_R[size]
    T = Xf(lean, (-2.0, -4.0))
    cx, cy = T(-3.0, -5.0 + bob - rear)
    hips = [T(0.8, -3.0 + bob - rear), T(-2.4, -3.0 + bob - rear * 0.6), T(-5.0, -3.2 + bob),
            T(1.6, -3.4 + bob - rear), T(-1.6, -3.4 + bob - rear * 0.6), T(-4.2, -3.6 + bob)]
    base = [(3.5, 0.0), (-1.5, 0.0), (-8.0, 0.0), (4.5, 0.0), (-0.5, 0.0), (-7.0, 0.0)]
    feet = gait6(i, n, hips, base, stride=stride, lift=1.0) if stride else list(base)
    if kick:   # hind legs kick up and back
        feet[2] = (hips[2][0] - 3.0 - kick * 2, hips[2][1] - 4.0 * kick); feet[5] = (hips[5][0] - 2.5 - kick * 2, hips[5][1] - 3.5 * kick)
    if dead: feet = [(h[0] + [2, 0, -2, 3, 1, -1][k], h[1] - 3.0) for k, h in enumerate(hips)]
    legs6(r, hips, feet, 3.0, 3.4, 1.4, -2.0, mat="bshell", far_mat="dchit", rad=0.5, far_rad=0.45)
    r.ell(cx, cy + 1.6, 5.4, 1.8, "dchit", -0.5)
    r.ell(cx - 0.2, cy - 0.6, 6.6, 4.9, "bshell", 0.0, bias=0.1)
    r.ell(cx + 4.0, cy - 0.4, 2.6, 2.8, "bshell", 0.05, bias=0.05)
    r.line(cx - 5.0, cy - 0.6, cx + 3.0, cy - 3.4, "bshell", 0.01, tone=1)
    r.ell(cx - 1.4, cy - 2.6, 2.6, 0.8, "bshell", 0.02, flat=4)
    # the head, clypeus rake down at the ball
    hx, hy = T(3.8 + head, -3.6 + bob - rear * 0.4 + butt * 0.5)
    r.ell(hx - 0.8, hy - 0.6, 2.4, 2.2, "bshell", 0.3, bias=0.05)
    r.poly([(hx - 1.0, hy - 2.4), (hx + 2.8, hy - 0.4), (hx + 2.2, hy + 1.2), (hx - 0.6, hy + 1.0)], "bshell", 0.32,
           normal=(-0.2, -0.6, 0.8))
    for k in range(3): r.dot(hx + 2.6 - k * 0.3, hy - 0.6 + k * 0.7, "bshell", 4 if k == 0 else 3, 0.33)
    eye(r, hx - 0.2, hy - 1.0, 0.34, glint=not dead)
    if hurt and not dead: r.dot(hx - 0.2, hy - 1.0, "white", 2, 0.35)
    antenna(r, (hx, hy - 2.0), -70, 2.8, 50, 0.31, club="bshell")
    out = None
    if ball:
        out = amber_ball(r, hx + 2.2 + R + bx, by, R, 0.5 if bx >= 0 else -0.6, rot=rot)
    if dust_at: dust(r, *dust_at)
    if extra: extra(r, (hx, hy), out)
    return r.resolve()


def scarab_sheet(outdir):
    Sc = scarab
    anims = []
    for size, sfx in ((3, ""), (2, "2"), (1, "1"), (0, "0")):
        idle = [Sc(size=size, bob=[0, 0.3, 0.5, 0.3][i], rot=i * 5, head=[0, 0.2, 0.3, 0.2][i]) for i in range(4)]
        run = [Sc(size=size, i=i, n=6, stride=1.8, bob=0.4 * abs(math.sin(i / 6 * math.tau)), lean=4, rot=i * 30, head=0.3) for i in range(6)]
        anims += [("Idle" + sfx, idle, [0.14, 0.12, 0.14, 0.12]), ("Run" + sfx, run, [0.08] * 6)]
    for size in (3, 2, 1):
        sfx = "" if size == 3 else str(size)
        # Bowl: draw the ball back (0, 1), HEAVE it forward (2), it rolls away (3: gone at 4), follow, settle
        bowl = [Sc(size=size, bx=-0.5, lean=-4, rear=0.6, head=-0.8), Sc(size=size, bx=-1.2, lean=-8, rear=1.0, head=-1.2),
                Sc(size=size, bx=3.0, lean=10, head=1.5, rot=60, dust_at=(4, 0, 0)), Sc(size=size, bx=9.0, lean=8, head=1.5, rot=140),
                Sc(size=size, ball=False, lean=4, head=1.0, dust_at=(4, 0, 2)), Sc(size=0, lean=2, head=0.3), Sc(size=0)]
        # Hurl: rear up on the ball (0-2), KICK it over the head (3, the ball arcs up behind), gone (4), land (5-7)
        R = BALL_R[size]
        hurl = [Sc(size=size, rear=1.0, lean=-6), Sc(size=size, rear=2.0, lean=-14, bx=-2.0, by=-2.0),
                Sc(size=size, rear=3.0, lean=-24, bx=-5.0, by=-5.0, kick=0.4),
                Sc(size=size, rear=2.0, lean=-16, kick=1.0, ball=False,
                   extra=lambda r, h, o, R=R: amber_ball(r, h[0] - 4.0, h[1] - 9.0, R, 1.0, rot=80)),
                Sc(size=0, rear=1.0, lean=-6, kick=0.6, extra=lambda r, h, o: smear(r, [(h[0] - 2, h[1] - 14), (h[0] + 6, h[1] - 16)], "amber", 2)),
                Sc(size=0, lean=4), Sc(size=0, lean=2), Sc(size=0)]
        anims += [("Bowl" + sfx, bowl, [0.12, 0.12, 0.05, 0.08, 0.1, 0.1, 0.12]),
                  ("Hurl" + sfx, hurl, [0.12, 0.12, 0.1, 0.06, 0.1, 0.1, 0.1, 0.12])]
    # Butt: with no ball, it can only headbutt
    butt = [Sc(size=0, lean=-6, head=-1.0, rear=0.6), Sc(size=0, lean=-10, head=-1.6, rear=1.0),
            Sc(size=0, lean=10, head=2.0, butt=1.0, dust_at=(5, 0, 0)), Sc(size=0, lean=6, head=1.0), Sc(size=0, lean=2), Sc(size=0)]
    anims += [("Butt", butt, [0.12, 0.1, 0.05, 0.1, 0.1, 0.12])]
    idle0 = anims[0][1][0]
    d = [Sc(size=3, hurt=True, rear=1.5, lean=-14), Sc(size=3, hurt=True, lean=-30, bob=1.0, bx=3),
         Sc(size=3, dead=True, lean=8, bob=2.5, bx=6, dust_at=(0, 0, 0)), Sc(size=3, dead=True, lean=10, bob=3.0, bx=7)]
    knock = Sc(size=3, hurt=True, rear=1.8, lean=-16)
    anims += tail_anims(idle0, d, [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("ZhkScarab", anims, outdir, scale=6)


SYNC["ZhkScarab"] = {"Bowl": [("HEAVE: the ball leaves at (14, -5) and rolls along the floor", 2)],
                     "Hurl": [("KICK: the ball arcs over its back toward the hero's spot", 3)],
                     "Butt": [("BUTT: head at (9, -4); box 12 x 10 at (8, -4)", 2)]}
NOTES["ZhkScarab"] = ("Rolling Stock: Idle/Run carry the big ball (size 3), Idle2/Run2 mid, Idle1/Run1 small, Idle0/Run0 a pebble. "
                      "Bowl/Hurl (size 3), Bowl2/Hurl2, Bowl1/Hurl1; Butt is its only attack with no ball.")

JOBS = [("ZhkSpitter", spitter_sheet), ("ZhkSoldier", soldier_sheet), ("ZhkHornet", hornet_sheet),
        ("ZhkSiphon", siphon_sheet), ("ZhkNasute", nasute_sheet), ("ZhkScarab", scarab_sheet)]
