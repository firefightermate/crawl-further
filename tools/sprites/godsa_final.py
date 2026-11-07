"""v0.9 final-size redraws: monsters that the v0.7 size pass had shrunk with a design scale (ArtScale < 1), which
came out noisy and outline-less, drawn again directly at their in-game size.

    python3 godsa_final.py [--only Name,Name] [outroot]

  OssRattlebones  T1  a hunched skeleton with a big cracked skull (green socket), 2 px bones, a real idle (sway, jaw chatter)
  OssMarrowHound  T1  a skeletal hound: long skull and snout, ribcage, spine, four bone legs, vertebra tail
  OssBoneRat      minion: a little skeletal rat (long skull, ribs, whip tail) + Spawn 3
  OssCairnCrow    T1  a black crow wearing its own bone skull, green eye, ragged wings
  BelCrab         T1  a barnacle crab: a big domed red shell crusted with barnacles, stalk eyes, one big claw; it pulls
                      into the shell (Shell)
  BelDiver        T2  a drowned diver: brass helmet (a violet urchin grown on it), canvas suit, lead boots, an anchor,
                      and a canvas glove studded with urchin spines for its back hand (v0.10: was a crab claw)
  MothMatron      T2  a moth-woman: one furry body, a pale moth mask with ember eyes, feathered antennae, big ash
                      wings with ember eye-spots, mantis-like clawed forearms

Frame counts and per-frame durations are the old sheets' (so every kit event keeps its time); spawn points are listed in
each god's TIMING.md (v0.9 final-size section) and the kits use them directly (no ArtScale entry).
Drawn with the vhorrul_t3 primitives: shaded shapes lit from the top-left, a 1 px dark outline, glow pixels last.
"""
import math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import belmora_rigs as B          # noqa: E402  (palette chars, barnacles, diver helmet, anchor)
import vhorrul_t3 as V            # noqa: E402  (Fr, ell, tube, poly, line, sheet, moth_wing)
from anim import Spr              # noqa: E402

ell, tube, poly, line, P, pick, Fr = V.ell, V.tube, V.poly, V.line, V.P, V.pick, V.Fr
ROOT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "art")
BONE = "hiwWX"
BONE_D = "khiw"
FEATH = "KmsSU"
CRABR = "jpPa"       # lifted crab red: dark -> light
SUITR = "ktgT"
BUILT = {}


def sheet(name, anims, outdir):
    V.sheet(name, anims, outdir, scale=6)
    BUILT[name] = V.BUILT.get(name)


def tail(idle0, death, death_d, knock, dead_d=0.2):
    return [("Death", death, death_d), ("Dead", [death[-1]], [dead_d]), ("Statue", [idle0.stone()], [0.2]),
            ("Knockback", [knock], [0.2]), ("Portrait", [idle0], [0.2])]


def bone(c, pts, r=0.9, ramp=BONE):
    tube(c, pts, [r] * len(pts), ramp, bias=0.15)


def skull(f, x, y, rx=2.6, ry=2.3, jaw=0, eye="lit", snout=0.0, lay="b", dark=False):
    """A bone skull centred (x, y) facing right: dome, a deep socket with a green ember, teeth, a hinged jaw."""
    c = getattr(f, lay)
    ell(c, x, y, rx, ry, BONE, bias=0.2)
    if snout:
        tube(c, [(x + rx * 0.4, y + 0.6), (x + rx + snout, y + 0.9)], [ry * 0.6, ry * 0.42], BONE, bias=0.1)
    sx, sy = P(x + rx * 0.35, y - 0.2)
    c.put(sx, sy, "K"); c.put(sx + 1, sy, "K"); c.put(sx, sy + 1, "k")
    if eye == "lit" and not dark:
        f.g.put(sx + 1, sy, "G"); f.g.put(sx, sy, "V")
    elif eye == "wide" and not dark:
        f.g.put(sx + 1, sy, "G"); f.g.put(sx, sy, "G"); f.g.put(sx + 1, sy - 1, "V")
    c.put(*P(x - rx * 0.4, y - ry * 0.5), "X")
    c.put(*P(x - rx * 0.1, y + 0.6), "h")                         # nasal / crack
    # teeth + jaw
    jx0, jy0 = x - rx * 0.1, y + ry * 0.75
    jx1 = x + rx + snout * 0.9
    for k in range(int(jx1 - jx0) + 1):
        c.put(*P(jx0 + k, jy0), "W" if k % 2 else "i")
    a = math.radians(8 + 22 * jaw)
    line(c, jx0, jy0 + 1, jx0 + (jx1 - jx0) * math.cos(a), jy0 + 1 + (jx1 - jx0) * math.sin(a), "wwW")
    return (jx1, jy0 + 0.5 * jaw)


# ====================================================================================== OSSIVAR: RATTLEBONES (T1)
def rattle(dy=0.0, lean=0.0, legs=((-2.5, 0.0), (2.5, 0.0)), arm_b=(-4.5, -6.5), arm_f=(4.5, -6.0), head=(0.0, 0.0),
           jaw=0, headless=False, held=None, eye="lit", sparks=(), dark=False):
    """Hunched skeleton, ~11 x 16. legs: (foot x, lift). arm_b / arm_f: hand positions. held: skull carried at a point."""
    f = Fr()
    hip = (0.0 + lean * 0.3, -6.0 + dy)
    sh = (0.8 + lean, -9.4 + dy)
    for i, (fx, lift) in enumerate(legs):
        hp = (hip[0] + (-1.0 if i == 0 else 1.0), hip[1])
        foot = (fx, -1.0 - lift)
        (kx, ky), _ = B.ik(hp[0], hp[1], foot[0], foot[1], 3.4, 3.2, bend=-1)
        lay = f.u if i == 0 else f.b
        bone(lay, [hp, (kx, ky), foot], 0.8, BONE_D if i == 0 else BONE)
        lay.put(*P(foot[0] + 1, foot[1] + 1), "w" if i else "i"); lay.put(*P(foot[0], foot[1] + 1), "W" if i else "w")
        lay.put(*P(kx, ky), "X" if i else "w")
    # back arm
    (ex, ey), _ = B.ik(sh[0] - 1.2, sh[1] + 0.8, arm_b[0], arm_b[1] + dy, 3.0, 3.0, bend=1)
    bone(f.u, [(sh[0] - 1.2, sh[1] + 0.8), (ex, ey), (arm_b[0], arm_b[1] + dy)], 0.7, BONE_D)
    # pelvis, spine, ribcage
    ell(f.b, hip[0], hip[1], 2.2, 1.1, BONE, bias=0.1)
    bone(f.b, [hip, sh], 0.7)
    ell(f.b, sh[0] - 0.2, sh[1] + 1.4, 2.8, 2.3, BONE, bias=0.15)
    for k, yy in enumerate((0.8, 2.2)):
        for xx in range(-2, 3):
            if (xx + k) % 2 == 0: f.b.put(*P(sh[0] - 0.2 + xx, sh[1] + yy), "k")
    f.b.put(*P(sh[0] + 0.8, sh[1] + 1.4), "h")
    # head
    hx, hy = sh[0] + 1.6 + head[0], sh[1] - 2.9 + head[1]
    if headless:
        f.b.put(*P(sh[0] + 0.8, sh[1] - 1), "w"); f.g.put(*P(sh[0] + 0.8, sh[1] - 2), "G")
    else:
        bone(f.b, [(sh[0] + 0.6, sh[1]), (hx - 0.4, hy + 1.6)], 0.6)
        skull(f, hx, hy, 2.8, 2.3, jaw=jaw, eye=eye, dark=dark)
    if held is not None:
        skull(f, held[0], held[1] + dy, 2.4, 2.1, jaw=1, eye=eye)
    # front arm (over)
    (ex, ey), _ = B.ik(sh[0] + 1.0, sh[1] + 0.8, arm_f[0], arm_f[1] + dy, 3.0, 3.2, bend=1)
    bone(f.b, [(sh[0] + 1.0, sh[1] + 0.8), (ex, ey), (arm_f[0], arm_f[1] + dy)], 0.75)
    f.b.put(*P(arm_f[0] + 1, arm_f[1] + dy), "W"); f.b.put(*P(arm_f[0] + 1, arm_f[1] + dy + 1), "w")
    for (x, y) in sparks: f.g.put(*P(x, y), "G"); f.g.put(*P(x, y - 1), "V")
    return f.done(ink="k")


def rattle_pile(stage=0, eye="lit"):
    """A heap of bones on the floor (Collapse hold / corpse)."""
    f = Fr()
    for k, (x0, y0, x1, y1) in enumerate(((-6, -1, -1, -2), (0, -1, 5, -1), (-4, -3, 2, -2), (1, -3, 6, -2.5), (-7, -2, -4, -4))):
        bone(f.b if k % 2 else f.u, [(x0, y0), (x1, y1)], 0.75, BONE if k % 2 else BONE_D)
    ell(f.b, -0.5, -3.5, 2.6, 1.6, BONE, bias=0.1)
    for xx in range(-2, 2): f.b.put(xx, -3, "k" if xx % 2 else "w")
    skull(f, 2.5 - stage, -5.0 + stage * 0.5, 2.6, 2.3, jaw=1, eye=eye if stage < 2 else "dark", dark=stage >= 2)
    return f.done(ink="k")


def build_rattlebones(out):
    idle = [rattle(dy=[0, 0.5, 1, 0.5][i], head=([0, 0.5, 1, 0.5][i], [0, 0.5, 1, 0.5][i]), jaw=[0, 1, 0, 2][i],
                   arm_b=(-4.5 + [0, -0.5, -1, -0.5][i], -6.0), arm_f=(4.5 + [0, 0.5, 1, 0.5][i], -5.5 + [0, 0.5, 1, 0.5][i]),
                   sparks=[(5, -14)] if i in (1, 2) else ()) for i in range(4)]
    run = []
    for i in range(6):
        t = i / 6.0 * 2 * math.pi
        run.append(rattle(dy=-abs(math.sin(t)) * 0.8, lean=1.0,
                          legs=((-2.5 + 2.5 * math.cos(t), max(0, math.sin(t)) * 1.5), (2.5 - 2.5 * math.cos(t), max(0, -math.sin(t)) * 1.5)),
                          arm_b=(-3.5 + 3 * math.cos(t), -6.5), arm_f=(4.5 - 3 * math.cos(t), -6.0), jaw=i % 2))
    # SkullToss: grab (0), cocked back headless (1), RELEASE (2), follow (3), wait arm up (4), catch (5)
    toss = [rattle(arm_f=(3.0, -14.0), head=(0, -0.5), jaw=1),
            rattle(lean=-1.0, headless=True, arm_f=(-5.0, -14.0), held=(-5.0, -15.5)),
            rattle(lean=1.5, headless=True, arm_f=(7.0, -10.0), sparks=[(9, -11)], legs=((-4, 0), (3.5, 0))),
            rattle(lean=1.5, headless=True, arm_f=(6.0, -6.0), legs=((-4, 0), (3.5, 0))),
            rattle(headless=True, arm_f=(4.0, -15.0), sparks=[(3, -16)]),
            rattle(arm_f=(4.0, -13.0), jaw=2, sparks=[(5, -16), (1, -15)])]
    pile = rattle_pile(0)
    coll = [rattle(dy=1.5, jaw=2, arm_b=(-5, -4), arm_f=(5, -4), legs=((-3.5, 0), (3.5, 0))),
            rattle(dy=3.0, jaw=2, arm_b=(-6, -2), arm_f=(6, -2), legs=((-4.5, 0), (4.5, 0))),
            rattle_pile(0).over(Spr({(-1, -9): "w", (2, -8): "W"})),
            pile, pile.over(Spr({(0, -7): "G", (1, -8): "V"})),
            rattle_pile(0).over(Spr({(-1, -8): "W", (1, -9): "X"})),
            rattle(dy=3.0, jaw=1, arm_b=(-6, -2), arm_f=(6, -2), legs=((-4.5, 0), (4.5, 0))),
            rattle(dy=1.0, jaw=0)]
    death = [rattle(dy=1.0, jaw=2, eye="wide", arm_f=(5, -11)), rattle(dy=3.0, jaw=2, legs=((-4.5, 0), (4.5, 0)), arm_b=(-6, -2), arm_f=(6, -2)),
             rattle_pile(1), rattle_pile(2)]
    knock = rattle(lean=-1.5, jaw=2, head=(-1, 0), arm_b=(-6, -9), arm_f=(1, -12), eye="wide")
    anims = [("Idle", idle, [0.16] * 4), ("Run", run, [0.08] * 6)] + \
        tail(idle[0], death, [0.1, 0.1, 0.12, 0.3], knock) + \
        [("SkullToss", toss, [0.14, 0.16, 0.05, 0.1, 0.12, 0.1]),
         ("Collapse", coll, [0.07, 0.07, 0.08, 0.1, 0.35, 0.09, 0.09, 0.12])]
    sheet("OssRattlebones", anims, os.path.join(ROOT, "out_ossivar"))


# ====================================================================================== OSSIVAR: BONE QUADRUPEDS
def boneq(L=1.0, dy=0.0, lean=0.0, legs=None, head=(0.0, 0.0), jaw=0, tailp=0.0, eye="lit", snout=2.2, crouch=0.0,
          dark=False, sk=(3.0, 2.3), howl=False, ntail=4):
    """A skeletal quadruped facing right. L scales the body (1.0 = Marrow Hound ~19 x 12; 0.62 = Bone Rat).
    legs: 4 (dx, lift) for back-far, back-near, front-far, front-near."""
    f = Fr()
    legs = legs or [(0, 0)] * 4
    hipx, shx = -5.5 * L, 4.0 * L
    by = (-7.5 - crouch) * L + dy
    hip = (hipx, by + 0.5 * L)
    sho = (shx + lean, by - 0.4 * L)
    # far legs
    for i, (x0, root) in enumerate(((hipx - 0.8 * L, hip), (shx - 0.8 * L + lean, sho))):
        ldx, lift = legs[i * 2]
        foot = (x0 + ldx, -1.0 - lift)
        mid = (x0 + (0.8 if i == 0 else -0.4) * L + ldx * 0.5, (root[1] + foot[1]) / 2 + (0.5 if i == 0 else 0))
        bone(f.u, [root, mid, foot], 0.65 * max(0.8, L), BONE_D)
        f.u.put(*P(foot[0] + 1, foot[1] + 1), "i")
    # tail
    tx, ty = hip[0] - 1.0, hip[1] - 0.5
    for k in range(ntail):
        a = math.radians(195 + 18 * math.sin(tailp + k * 0.8) - k * 10)
        nx_, ny_ = tx + 1.6 * L * math.cos(a), ty + 1.6 * L * math.sin(a)
        f.b.put(*P(nx_, ny_), "W" if k % 2 == 0 else "w")
        tx, ty = nx_, ny_
    # pelvis, spine, ribs
    ell(f.b, hip[0], hip[1], 2.0 * L, 1.4 * L, BONE, bias=0.1)
    bone(f.b, [hip, ((hip[0] + sho[0]) / 2, by - 0.8 * L), sho], 0.75 * max(0.8, L))
    rc = ((hip[0] + sho[0]) / 2 + 1.0 * L, by + 1.6 * L)
    ell(f.b, rc[0], rc[1], 3.6 * L, 2.3 * L, BONE, bias=0.15)
    nrib = max(2, int(5 * L))
    for k in range(nrib):
        x = rc[0] - 3.0 * L + k * (6.0 * L / max(1, nrib - 1))
        for yy in range(int(round(rc[1] - 1.0 * L)), int(round(rc[1] + 1.8 * L)) + 1):
            if k % 2 == 1: f.b.put(*P(x, yy), "k")
    f.g.put(*P(rc[0], rc[1] + 0.5), "v" if not dark else "k")         # marrow ember in the ribs
    # neck + skull
    hx, hy = sho[0] + 3.2 * L + head[0], sho[1] - 1.6 * L + head[1]
    bone(f.b, [sho, (hx - 1.2 * L, hy + 0.8 * L)], 0.65 * max(0.8, L))
    jaw_end = skull(f, hx, hy, sk[0] * L, sk[1] * L, jaw=jaw, eye=eye, snout=snout * L, dark=dark)
    if howl:
        for k in range(3): f.g.put(*P(jaw_end[0] + 1.5 + k, jaw_end[1] - 2 - k), "G" if k % 2 else "V")
    # near legs
    for i, (x0, root) in enumerate(((hipx + 0.6 * L, hip), (shx + 0.6 * L + lean, sho))):
        ldx, lift = legs[i * 2 + 1]
        foot = (x0 + ldx, -1.0 - lift)
        mid = (x0 + (1.0 if i == 0 else -0.5) * L + ldx * 0.5, (root[1] + foot[1]) / 2 + (0.5 if i == 0 else 0))
        bone(f.b, [root, mid, foot], 0.75 * max(0.8, L))
        f.b.put(*P(foot[0] + 1, foot[1] + 1), "W"); f.b.put(*P(foot[0], foot[1] + 1), "w")
        f.b.put(*P(mid[0], mid[1]), "X")
    return f.done(ink="k"), jaw_end


def q_run_legs(i, n=6, amp=2.2):
    t = i / float(n) * 2 * math.pi
    s, c = math.sin(t), math.cos(t)
    return [(amp * c, max(0, s) * 1.6), (-amp * c, max(0, -s) * 1.6), (-amp * c, max(0, -s) * 1.6), (amp * c, max(0, s) * 1.6)]


HOUND = dict(L=0.72, snout=1.8, ntail=3)


def build_hound(out):
    idle = [boneq(**HOUND, dy=[0, 0, 0.5, 0.5][i], head=(0, [0, 0.5, 1, 0.5][i]), jaw=[0, 0, 1, 0][i], tailp=i * 1.5)[0] for i in range(4)]
    run = [boneq(**HOUND, dy=-abs(math.sin(i / 6 * 2 * math.pi)) * 0.8, legs=q_run_legs(i), head=(0.5, 0), tailp=i, lean=0.5)[0] for i in range(6)]
    gnaw, pts = [], []
    for k, (hd, jw, ln, cr) in enumerate((((-1, 1), 0, -0.5, 0.5), ((1.5, 1.5), 2, 1.0, 0.0), ((2.5, 2.5), 0, 1.5, 0.0),
                                          ((1.5, 1.5), 2, 1.0, 0.0), ((2.5, 2.5), 0, 1.5, 0.0), ((0, 0.5), 0, 0, 0))):
        s_, j_ = boneq(**HOUND, head=hd, jaw=jw, lean=ln, crouch=cr, tailp=k)
        gnaw.append(s_); pts.append(j_)
    sniff = [boneq(**HOUND, head=(0.5, 3.0), crouch=0.5, jaw=0)[0], boneq(**HOUND, head=(0.5, 3.5), crouch=0.8, jaw=1)[0],
             boneq(**HOUND, head=(-0.5, -1.5), jaw=1, tailp=1)[0], boneq(**HOUND, head=(-1.0, -3.5), jaw=3, howl=True, eye="wide")[0],
             boneq(**HOUND, head=(-1.0, -3.5), jaw=3, howl=True, eye="wide", tailp=2)[0], boneq(**HOUND, crouch=1.2, lean=1.0, head=(1, 1), tailp=3)[0]]
    death = [boneq(**HOUND, head=(0, -1), jaw=3, eye="wide", crouch=0.5)[0], boneq(**HOUND, crouch=2.5, jaw=3, legs=[(-1, 0), (1, 0), (-1, 0), (1, 0)])[0],
             boneq(**HOUND, crouch=4.0, jaw=1, legs=[(-2, 0), (2, 0), (-2, 0), (2, 0)], dark=True)[0],
             boneq(**HOUND, crouch=5.0, jaw=1, legs=[(-3, 0), (3, 0), (-3, 0), (3, 0)], dark=True, eye="dark")[0]]
    knock = boneq(**HOUND, head=(-1, -2), jaw=2, lean=-1.0, eye="wide")[0]
    anims = [("Idle", idle, [0.15] * 4), ("Run", run, [0.07] * 6)] + tail(idle[0], death, [0.1, 0.1, 0.14, 0.3], knock) + \
        [("Gnaw", gnaw, [0.14, 0.1, 0.05, 0.06, 0.05, 0.12]), ("Sniff", sniff, [0.16, 0.16, 0.08, 0.18, 0.22, 0.1])]
    sheet("OssMarrowHound", anims, os.path.join(ROOT, "out_ossivar"))
    print("  hound jaws on Gnaw f2:", pts[2])


def build_rat(out):
    R = dict(L=0.48, snout=1.6, sk=(3.4, 2.8), ntail=3)
    idle = [boneq(head=(0, [0, 0.5, 1.0, 0.5][i]), jaw=[0, 0, 1, 0][i], tailp=i * 1.5, dy=[0, 0, 0.5, 0][i], **R)[0] for i in range(4)]
    run = [boneq(legs=q_run_legs(i, amp=1.4), tailp=i, head=(0.3, 0), dy=-abs(math.sin(i / 6 * 2 * math.pi)) * 0.5, **R)[0] for i in range(6)]
    bite, pts = [], []
    for k, (hd, jw, ln) in enumerate((((-0.5, 0.5), 0, -0.3), ((0, -1.0), 2, 0), ((1.5, 1.0), 0, 0.8), ((1.5, 1.0), 0, 0.8),
                                      ((1.0, 0.5), 2, 0.5), ((0, 0), 0, 0))):
        s_, j_ = boneq(head=hd, jaw=jw, lean=ln, tailp=k, **R)
        bite.append(s_); pts.append(j_)
    death = [boneq(head=(0, -1), jaw=2, **R)[0], boneq(crouch=1.5, jaw=2, **R)[0], boneq(crouch=3.0, jaw=1, dark=True, **R)[0],
             boneq(crouch=4.0, jaw=1, dark=True, eye="dark", legs=[(-2, 0), (2, 0), (-2, 0), (2, 0)], **R)[0]]
    # Spawn: claws up out of a heap of bones (the fodder rat's spawn clip)
    heap = Spr({(x, 0): ("w" if (x * 3) % 4 else "i") for x in range(-6, 7)})
    heap = heap.over(Spr({(-3, -1): "W", (2, -1): "w", (0, -1): "i", (4, -1): "W"}))
    spawn = [heap.over(boneq(crouch=4.5, jaw=1, **R)[0]), heap.over(boneq(crouch=2.5, jaw=2, **R)[0]), boneq(jaw=2, head=(0, -0.5), **R)[0]]
    knock = boneq(head=(-0.5, -1), jaw=2, lean=-0.5, eye="wide", **R)[0]
    anims = [("Idle", idle, [0.14] * 4), ("Run", run, [0.06] * 6)] + tail(idle[0], death, [0.08, 0.08, 0.12, 0.3], knock) + \
        [("Bite", bite, [0.12, 0.1, 0.05, 0.04, 0.04, 0.05]), ("Spawn", spawn, [0.1, 0.1, 0.1])]
    sheet("OssBoneRat", anims, os.path.join(ROOT, "out_ossivar"))
    print("  rat jaws on Bite f2:", pts[2])


# ====================================================================================== OSSIVAR: CAIRN CROW (T1 flier)
def crow(alt=8.0, dx=0.0, wing=-60.0, tilt=0.0, beak=0, eye="lit", talon=(100, 70), legs_up=False, dark=False, caw=0):
    """A black crow wearing its own bone skull. alt = body height above the floor (hover counts toward the T1 limit)."""
    f = Fr()
    bx, by = dx, -alt
    # far wing
    V.moth_wing(f, "u", (bx - 0.5, by - 1.5), 6.5, wing - 18, 0.45, "KKm", "K", [], 41, tatter=0.15)
    # tail fan
    poly(f.u, [(bx - 3, by - 0.5), (bx - 7.5, by - 2.0 + tilt * 0.05), (bx - 7.0, by + 1.5), (bx - 3, by + 1.5)], "m",
         shade=lambda x, y: "s" if (x + y) % 3 == 0 else "m")
    # body
    ell(f.b, bx, by, 3.8, 2.6, FEATH, ang=tilt, bias=0.3)
    f.b.put(*P(bx - 1, by - 1.5), "S"); f.b.put(*P(bx + 1, by - 2.0), "S")
    # talons
    for k, a in enumerate(talon):
        ar = math.radians(a)
        x0, y0 = bx + (0.5 - k), by + 2.2
        line(f.b, x0, y0, x0 + 2.5 * math.cos(ar), y0 + 2.5 * math.sin(ar), "iw")
    # bone skull head with a long beak
    hx, hy = bx + 4.3, by - 1.8 + tilt * 0.04
    ell(f.b, hx, hy, 2.2, 1.9, BONE, bias=0.2)
    a = math.radians(-6 + 18 * beak)
    line(f.b, hx + 1.6, hy - 0.3, hx + 4.4, hy + 0.6, "WWX")                        # upper beak
    line(f.b, hx + 1.4, hy + 0.9, hx + 1.4 + 3.4 * math.cos(a), hy + 0.9 + 3.4 * math.sin(a), "wwW")  # lower beak
    f.b.put(*P(hx + 0.4, hy - 0.4), "K")
    if not dark and eye != "dark":
        f.g.put(*P(hx + 0.4, hy - 0.4), "G"); f.g.put(*P(hx - 0.6, hy - 0.4), "V" if eye == "wide" else "K")
    # near wing over the body
    V.moth_wing(f, "b", (bx - 0.5, by - 1.0), 7.0, wing, 0.5, FEATH, "K", [], 43, tatter=0.18)
    if caw:
        for k in range(caw + 1): f.g.put(*P(hx + 6 + k, hy - 2 - k), "V" if k % 2 else "G")
    return f.done(ink="K")


def build_crow(out):
    idle = [crow(alt=[7, 7.5, 8, 7.5][i], wing=[-80, -40, 10, -30][i]) for i in range(4)]
    run = [crow(alt=8 + [0, 0.5, 1, 1, 0.5, 0][i], dx=0.5, tilt=-8, wing=[-100, -60, -10, 30, 0, -50][i], talon=(150, 160)) for i in range(6)]
    peck = [crow(alt=10, dx=-1, wing=-90, tilt=8), crow(alt=11, dx=-1.5, wing=-110, tilt=12, beak=1),
            crow(alt=5, dx=3, wing=-150, tilt=-25, talon=(160, 170)), crow(alt=5, dx=3, wing=-140, tilt=-20, talon=(160, 170)),
            crow(alt=6, dx=2.5, wing=-60, tilt=-10, beak=1), crow(alt=8, dx=1, wing=30, tilt=-5)]
    caw = [crow(alt=9, wing=-100), crow(alt=10, dx=-1, wing=-120, tilt=10, beak=1),
           crow(alt=9, dx=1, wing=20, tilt=-8, beak=2, caw=2), crow(alt=9, dx=1, wing=50, tilt=-6, beak=2, caw=1),
           crow(alt=8.5, wing=0), crow(alt=8.5, wing=-50)]
    death = [crow(alt=8, dx=-1, wing=-130, tilt=20, eye="wide"), crow(alt=5, dx=-1.5, wing=-160, tilt=40, beak=1),
             crow(alt=2.5, dx=-2, wing=170, tilt=60, beak=1, dark=True), crow(alt=1.8, dx=-2, wing=175, tilt=80, dark=True, eye="dark", talon=(-40, -60))]
    knock = crow(alt=9, dx=-1.5, wing=-150, tilt=25, eye="wide", beak=1)
    anims = [("Idle", idle, [0.1] * 4), ("Run", run, [0.07] * 6)] + tail(idle[0], death, [0.1, 0.1, 0.12, 0.3], knock) + \
        [("Peck", peck, [0.12, 0.14, 0.05, 0.05, 0.05, 0.1]), ("Caw", caw, [0.12, 0.14, 0.06, 0.18, 0.1, 0.12])]
    sheet("OssCairnCrow", anims, os.path.join(ROOT, "out_ossivar"))


# ====================================================================================== BEL'MORA: BARNACLE CRAB (T1)
def crab(dx=0.0, dy=0.0, tilt=0.0, sink=0.0, near=(0.0, 0.0, 0.6), far=(0.0, 0.0, 0.6), legs=0.0, eyes=1.0, eye="open",
         dark=False, tuck=0.0, plates=0, spray=0, splay=0.0):
    """A barnacle crab ~23 x 15 seen from the front (the classic crab read): a wide red carapace under a high dome of
    grey barnacle crust (the shell it hides in), two stalk eyes, two raised pincers (near/right one bigger) and three
    spindly legs a side. near/far = (dx, dy, open 0..1) of each claw hand; tuck 0..1 pulls legs in and folds both claws
    down over its face; sink lowers the body; splay spreads the legs flat (death)."""
    f = Fr()
    cx, cy = dx, -5.0 + dy + sink
    lift = tilt * 0.08
    # legs: three a side, spindly, splayed outward to the floor; they fold under as `tuck` -> 1
    for side in (-1, 1):
        for k in range(3):
            ph = legs + k * 2.1 + (0 if side > 0 else math.pi)
            root = (cx + side * (2.6 + k * 0.8), cy + 1.2 + side * lift)
            reach = (4.8 + k * 1.2) * (1 - 0.55 * tuck) + splay * 1.2
            knee = (cx + side * (reach - 1.2), cy - 1.6 + 2.2 * tuck - splay * 0.5 + side * lift - max(0.0, math.sin(ph)) * 0.6)
            foot = (cx + side * (reach + 0.4) + 0.5 * math.cos(ph), -0.4 - max(0.0, math.sin(ph)) * 1.2 + sink * 0.2)
            ramp = "jpP" if side > 0 else "jjp"
            line(f.u, root[0], root[1], knee[0], knee[1], ramp[1:])
            line(f.u, knee[0], knee[1], foot[0], foot[1], ramp)
    # carapace: a wide red oval with a pale serrated front rim
    ell(f.b, cx, cy, 6.0, 2.7, "pPPaa", ang=tilt, bias=0.35)
    for x in range(int(cx - 4), int(cx + 5), 2):
        f.b.put(x, int(round(cy + 1.6 + (x - cx) * lift / 6)), "a")
    for x in range(int(cx - 2), int(cx + 3)):
        f.b.put(x, int(round(cy + 2.0)), "Z")                                       # mouth
    # the shell it hides in: a high dome of barnacle crust (grey-white, holed)
    def crust(nu, nv, d, l, ch, x, y):
        if (x * 5 + y * 3) % 7 == 0 and d < 0.8: return "z"
        return ch
    ell(f.b, cx - 0.2, cy - 2.6, 4.8, 5.2, "xfHH", ang=tilt, bias=0.2, vmax=0.0, shader=crust)
    B.barnacles(f.b, [(cx - 2.6, cy - 5.0), (cx + 0.4, cy - 6.8), (cx + 2.4, cy - 4.6)], seed=11, big=True)
    f.b.put(*P(cx - 2, cy - 6.0), "H")
    for x in range(int(cx - 4), int(cx + 5)):
        if x % 3 != 1: f.b.put(x, int(round(cy - 2.6)), "z")                   # dark lip where the dome meets the body
    # stalk eyes, in front of the dome
    if eyes > 0.05:
        for k, ex_ in enumerate((cx - 2.0, cx + 2.0)):
            top = cy - 0.2 - 1.6 * eyes * (1 - 0.7 * tuck)
            line(f.b, ex_, cy + 0.2, ex_, top, "P")
            ex2 = ex_ + (1 if k else -1)
            for (qx, qy) in ((ex_, top - 1), (ex2, top - 1), (ex_, top - 2), (ex2, top - 2)):
                f.b.put(*P(qx, qy), "z" if dark else "a")
            if not dark:
                f.g.put(*P(ex2 if eye != "wide" else ex_, top - 1), "Z" if eye != "wide" else "c")
    # claws: stout arm from the carapace side up to a raised pincer opening upward; near (right) one is bigger
    for side, (hx, hy, op), big, lay in ((-1, far, 0.85, f.b), (1, near, 1.0, f.b)):
        ax, ay = cx + side * 4.8, cy - 0.6 + side * lift
        hx_ = cx + side * (6.6 - 4.4 * tuck) + hx
        hy_ = cy - 3.8 + 3.6 * tuck + hy
        mid = (ax + side * 2.0, ay + 0.4 - 0.8 * tuck)
        tube(lay, [(ax, ay), mid, (hx_, hy_ + 1.2)], [1.3, 1.2, 1.1], "jpP", bias=0.05)
        ell(lay, hx_, hy_, 2.3 * big, 2.1 * big, "pPPaa", bias=0.45)
        o = op * (1 - tuck)
        # fixed finger (outer) and moving finger (inner), pointing up
        for fs, ln, ramp in ((side, 2.8 * big, "Paa"), (-side, 2.4 * big, "pPa")):
            a = math.radians(-90 + fs * (4 + 20 * o))
            bx_, by_ = hx_ + fs * 1.0 * big, hy_ - 1.6 * big
            ex2, ey2 = bx_ + ln * math.cos(a), by_ + ln * math.sin(a)
            line(lay, bx_, by_, ex2, ey2, ramp)
            lay.put(*P(ex2 - fs * 0.9, ey2 + 0.2), ramp[-1])            # tip hooks inward
        lay.put(*P(hx_ - 0.8 * side, hy_ - 0.6), "a")
    for k in range(plates):     # barnacle plates welling up while it hides
        f.g.put(*P(cx - 4 + k * 3, cy - 6.2 - (k % 2)), "H"); f.g.put(*P(cx - 4 + k * 3, cy - 5.2 - (k % 2)), "f")
    for k in range(spray):
        f.g.put(*P(cx + 12 + k, cy - 6 - k), "Q" if k % 2 else "E")
    return f.done(ink="Z")


def build_crab(out):
    idle = [crab(dy=[0, -0.4, 0, 0.2][i], legs=i * 0.6, near=(0, [0, -0.6, 0, 0.3][i], [0.6, 0.9, 0.6, 0.3][i]),
                 far=(0, [0.3, 0, -0.5, 0][i], [0.4, 0.3, 0.8, 0.5][i]), eyes=[1, 1, 0.85, 1][i]) for i in range(4)]
    run = [crab(dy=-0.4 if i % 2 else 0, legs=i * 1.05, near=(0, 0.6 * (i % 2), 0.4), far=(0, 0.6 * ((i + 1) % 2), 0.4),
                tilt=[0, 2, 0, -2, 0, 2][i]) for i in range(6)]
    # Pinch: wind up (0-1), SNAP across to the right (2-3, HIT f3), hold (4), recover (5). Claw tip lands ~(+14, -10).
    pinch = [crab(near=(-1.5, -1.0, 1.0), tilt=-3), crab(dx=-0.5, near=(-2.5, -1.8, 1.0), tilt=-5, eye="wide"),
             crab(dx=1.0, near=(3.0, 0.5, 0.6), tilt=3), crab(dx=1.5, near=(4.5, 1.5, 0.0), tilt=4, spray=2),
             crab(dx=1.0, near=(4.0, 1.5, 0.0), tilt=2, spray=1), crab(near=(0.5, 0, 0.5))]
    shell = [crab(tuck=0.35, sink=0.5, eyes=0.6), crab(tuck=0.8, sink=1.5, eyes=0.3), crab(tuck=1.0, sink=2.2, eyes=0.15, plates=2),
             crab(tuck=1.0, sink=2.2, eyes=0.15, plates=3), crab(tuck=1.0, sink=2.0, plates=3, eyes=0.35), crab(tuck=0.3, sink=0.4)]
    death = [crab(tilt=-6, eye="wide", near=(-1, -2, 1.0), far=(1, -1, 1.0)),
             crab(tilt=-10, sink=1.0, tuck=0.3, eyes=0.6, splay=0.4, near=(1, 2, 0.2), far=(-1, 2, 0.2)),
             crab(tilt=-12, sink=2.0, tuck=0.4, dark=True, eyes=0.3, splay=0.8, near=(2, 3, 0.0), far=(-2, 3, 0.0)),
             crab(tilt=-12, sink=2.6, tuck=0.5, dark=True, eyes=0.0, splay=1.0, near=(2.5, 3.5, 0.0), far=(-2.5, 3.5, 0.0))]
    knock = crab(dx=-1, tilt=-8, eye="wide", near=(-1.5, -2, 1.0), far=(1.0, -1.5, 1.0))
    anims = [("Idle", idle, [0.22, 0.16, 0.22, 0.16]), ("Run", run, [0.07] * 6),
             ("Pinch", pinch, [0.14, 0.14, 0.07, 0.06, 0.12, 0.14]), ("Shell", shell, [0.1, 0.3, 0.3, 0.3, 0.3, 0.14])] + \
        tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock, dead_d=0.3)
    sheet("BelCrab", anims, os.path.join(ROOT, "out_belmora"))


# ====================================================================================== BEL'MORA: BELL DIVER (T2)
def diver(dx=0.0, dy=0.0, lean=0.0, feet=((-3, 0), (3, 0)), anchor_g=(5.0, -8.0), anchor_a=80.0, anchor_L=10.0,
          claw_h=(-5.0, -9.0), claw_open=0.4, glow=1, crack=False, hook=None, bubbles=(), planted=None, head_tilt=0.0,
          smear=None, show_anchor=True):
    """Drowned diver ~20 x 25: lead boots, a waterlogged canvas suit, the brass helmet with a violet urchin grown on it,
    a rusty anchor in the near hand and a red crab claw for the far hand."""
    f = Fr()
    hip = (dx, -7.0 + dy)
    lt = math.tan(math.radians(lean))
    sh_y = hip[1] - 6.5
    chest = (hip[0] + lt * 3.5, hip[1] - 3.5)
    head = (hip[0] + lt * 8 + 0.8, sh_y - 4.2)
    if planted is not None:
        B.anchor(f.u, planted[0], planted[1], planted[2], L=anchor_L)
    for i, (fx, fy) in enumerate(feet):
        hp = (hip[0] + (-1.3 if i == 0 else 1.3), hip[1])
        foot = (dx + fx, -1.8 - fy)
        (kx, ky), (ax, ay) = B.ik(hp[0], hp[1], foot[0], foot[1], 3.4, 3.0, bend=-1)
        lay = f.u if i == 0 else f.b
        tube(lay, [hp, (kx, ky), (ax, ay)], [1.6, 1.5, 1.4], "Zkt" if i == 0 else SUITR)
        bxp, byp = P(ax, ay)
        for yy in range(byp, min(0, byp + 1) + 1):
            for xx in range(bxp - 2, bxp + 3):
                lay.put(xx, yy, "x" if yy == byp else "z")
        lay.put(bxp + 2, byp, "f")
    # far arm: v0.10 (one parent, the Bell Urchin): a canvas diving glove studded with violet urchin spines
    # (was the Barnacle Crab's red claw)
    sb = (chest[0] - 2.5, sh_y + 1.2)
    hb = (dx + claw_h[0], claw_h[1] + dy)
    (ebx, eby), _ = B.ik(sb[0], sb[1], hb[0], hb[1], 3.2, 3.2, bend=1)
    tube(f.u, [sb, (ebx, eby), hb], [1.4, 1.3, 1.2], "Zkt")
    ell(f.u, hb[0], hb[1], 1.9, 1.7, SUITR, bias=0.2)
    a0, a1 = math.radians(-160 - 25 * claw_open), math.radians(160 + 25 * claw_open)
    for aa, ln in ((a0, 2.4), (a1, 2.0), (math.radians(-110), 1.8)):
        line(f.u, hb[0] - 0.8, hb[1], hb[0] - 0.8 + ln * math.cos(aa), hb[1] + ln * math.sin(aa), "nNH")
    # suit
    ell(f.b, chest[0], chest[1], 3.8, 4.4, SUITR, ang=lean, bias=0.15)
    line(f.b, hip[0] - 3.2, hip[1] - 0.6, hip[0] + 3.4, hip[1] - 0.6, "z")
    for k in (-2, 0, 2): f.b.put(*P(hip[0] + k + 0.5, hip[1] - 0.6), "f")
    B.barnacles(f.b, [(chest[0] - 2.0, chest[1] + 0.5)], seed=31)
    B.kelp(f.b, int(round(chest[0] - 3)), int(round(chest[1] - 1)), 5, 0.8, seed=2)
    crown = None
    if show_anchor and anchor_g is not None:
        crown = B.anchor(f.b, dx + anchor_g[0], anchor_g[1] + dy, anchor_a, L=anchor_L)
    if smear:
        for (x, y, ch) in smear: f.g.put(x, y, ch, over=False)
    # helmet, with a violet urchin grown onto its back (the Bell Urchin line)
    ux_, uy_ = head[0] - 2.8, head[1] - 3.2
    for k in range(9):
        a = math.radians(-215 + k * 27)
        line(f.b, ux_ + 1.4 * math.cos(a), uy_ + 1.2 * math.sin(a), ux_ + 3.2 * math.cos(a), uy_ + 2.8 * math.sin(a), "fH")
    ell(f.b, ux_, uy_, 2.1, 1.8, B.URCH, bias=0.3)
    B.diver_helmet(f.b, f.g, head[0], head[1], tilt=head_tilt, glow=glow, crack=crack)
    # near arm gripping the anchor
    sf = (chest[0] + 1.6, sh_y + 1.2)
    hf = (dx + anchor_g[0], anchor_g[1] + dy) if anchor_g is not None else (chest[0] + 4, chest[1])
    (efx, efy), _ = B.ik(sf[0], sf[1], hf[0], hf[1], 3.2, 3.4, bend=1)
    tube(f.b, [sf, (efx, efy), hf], [1.4, 1.3, 1.2], SUITR)
    ell(f.b, hf[0], hf[1], 1.4, 1.3, "zxf")
    if hook is not None:
        hook(f, hf)
    for (bx, by) in bubbles:
        f.g.put(*P(head[0] + bx, head[1] + by), "Q"); f.g.put(*P(head[0] + bx + 1, head[1] + by + 1), "E", over=False)
    return f.done(ink="Z"), crown


def build_diver(out):
    idle = [diver(dy=[0, 0.4, 0.6, 0.3][i], anchor_g=(4.0, -12.0), anchor_a=-150 + [0, 3, 5, 2][i], claw_open=[0.3, 0.7, 0.4, 0.1][i],
                  bubbles=[(), ((2, -4),), ((3, -5), (1, -3)), ((3, -6),)][i])[0] for i in range(4)]
    run = []
    for i in range(6):
        t = i / 6.0 * 2 * math.pi
        run.append(diver(dy=-abs(math.sin(t)) * 0.6, lean=6, feet=((-3 + 2.5 * math.cos(t), max(0, math.sin(t)) * 1.2),
                                                                     (3 - 2.5 * math.cos(t), max(0, -math.sin(t)) * 1.2)),
                         anchor_g=(4.0, -12.5), anchor_a=-155, claw_h=(-4.5, -10), claw_open=0.3 + 0.3 * (i % 2))[0])
    # Anchor: raise (0-2), SLAM (3), quake / hit (4), hold (5), recover (6). The anchor crown lands at (13, 0) on f3-f4.
    an_spec = [((3.0, -13.0), -60, -8), ((1.0, -18.0), -95, -12), ((2.0, -19.0), -70, -14),
               ((9.0, -8.0), 70, 12), ((9.5, -7.0), 80, 14), ((9.0, -7.0), 82, 12), ((6.0, -7.0), 88, 4)]
    anch, crowns = [], []
    for k, (g, a, ln) in enumerate(an_spec):
        sm = [(int(13 - j), int(-6 + j * 1.5), "E") for j in range(4)] if k == 3 else None
        s_, cr = diver(anchor_g=g, anchor_a=a, lean=ln, crack=False, glow=2 if 2 <= k <= 4 else 1, smear=sm,
                       claw_h=(-5, -12 if k < 3 else -8), claw_open=1.0 if k < 3 else 0.2)
        anch.append(s_); crowns.append(cr)
    # Hook: the anchor is planted; the diver whirls the chain hook and throws it (RELEASE f2) from the hand at (11, -16)
    def hookf(ang):
        def h(f, at):
            B.iron_hook(f, at[0] + 1.5 * math.cos(math.radians(ang)), at[1] + 1.5 * math.sin(math.radians(ang)), ang=ang)
        return h
    pl = (-6.0, -2.0, -80)
    hk_spec = [((4.0, -17.0), -4, hookf(-75)), ((-3.0, -16.0), -9, hookf(-150)), ((11.0, -16.0), 10, None),
               ((10.0, -14.0), 8, None), ((9.0, -13.0), 6, None), ((8.0, -12.0), 4, None), ((6.0, -11.0), 2, hookf(10)),
               ((5.5, -9.0), 0, hookf(60))]
    hookA = [diver(anchor_g=g, show_anchor=False, planted=pl, lean=l, hook=h, glow=2 if k == 2 else 1, claw_open=0.6)[0]
             for k, (g, l, h) in enumerate(hk_spec)]
    death = [diver(lean=-8, crack=True, glow=1, anchor_g=(5, -6), anchor_a=120)[0],
             diver(lean=-18, dy=2, crack=True, glow=0, anchor_g=(6, -3), anchor_a=170, feet=((-4, 0), (4, 0)))[0],
             diver(lean=-30, dy=4, crack=True, glow=0, show_anchor=False, feet=((-5, 0), (5, 0)), claw_h=(-7, -3))[0],
             diver(lean=-40, dy=5.5, crack=True, glow=0, show_anchor=False, feet=((-6, 0), (6, 0)), claw_h=(-8, -2))[0]]
    knock = diver(lean=-12, anchor_g=(3, -10), anchor_a=-120, glow=2, claw_h=(-6, -13), claw_open=1.0)[0]
    anims = [("Idle", idle, [0.24, 0.2, 0.24, 0.2]), ("Run", run, [0.1] * 6),
             ("Anchor", anch, [0.16, 0.14, 0.16, 0.05, 0.07, 0.18, 0.16]),
             ("Hook", hookA, [0.12, 0.14, 0.06, 0.1, 0.14, 0.14, 0.14, 0.18])] + \
        tail(idle[0], death, [0.1, 0.12, 0.16, 0.4], knock, dead_d=0.3)
    sheet("BelDiver", anims, os.path.join(ROOT, "out_belmora"))
    print("  diver anchor crown f3/f4:", crowns[3], crowns[4])


# ====================================================================================== VHORRUL: MOTH MATRON (T2)
def matron(dy=0.0, lean=0.0, wing=-118.0, wing_f=-92.0, arm_f=((5.0, -12.0), (8.0, -10.0)), arm_b=((-2.0, -12.0), (1.0, -9.0)),
           mask="calm", ember=1, embers=(), fade=0, legs=((-2.0, 0.0), (2.0, 0.0)), rake=0, dark=False):
    """Moth Matron ~22 x 24: a furry ash moth-woman standing on thin legs; big ash wings with ember eye-spots, a pale mask
    with ember eyes, feathered antennae, and two mantis-like clawed forearms (elbow, hand) in front of her."""
    f = Fr()
    hip = (0.0 + lean * 0.3, -6.8 + dy)
    sh = (0.8 + lean, -13.2 + dy)
    # wings: far fore + hind (dark), near hind + fore (ash, ember spots)
    root = (sh[0] - 1.8, sh[1] + 0.5)
    V.moth_wing(f, "u", (root[0] + 1.5, root[1]), 10.0, wing_f, 0.45, "Kkg", "K", [(0.65, 0.0, False)], 51)
    V.moth_wing(f, "u", (root[0] + 1, root[1] + 3), 7.5, wing_f - 50, 0.5, "Kkg", "K", [], 52, tatter=0.1)
    V.moth_wing(f, "u", (root[0], root[1] + 3), 8.5, wing - 48, 0.5, "kgh", "k", [(0.6, 0.0, False)], 53, tatter=0.12)
    V.moth_wing(f, "u", root, 11.5, wing, 0.5, "kghi", "k", [(0.62, -0.05, ember >= 1), (0.9, 0.1, False)], 54)
    # legs: thin, furred at the thigh
    for i, (fx, lift) in enumerate(legs):
        hp = (hip[0] + (-1.0 if i == 0 else 1.0), hip[1])
        foot = (fx, -1.0 - lift)
        (kx, ky), _ = B.ik(hp[0], hp[1], foot[0], foot[1], 3.4, 3.0, bend=-1)
        lay = f.u if i == 0 else f.b
        tube(lay, [hp, (kx, ky), foot], [1.3, 0.8, 0.7], "Kkg" if i == 0 else "kgh")
        lay.put(*P(foot[0] + 1, foot[1] + 1), "k"); lay.put(*P(foot[0], foot[1] + 1), "g")
    # far clawed forearm
    (ex, ey), (hx, hy) = arm_b
    tube(f.u, [(sh[0] - 1, sh[1] + 2), (ex, ey + dy), (hx, hy + dy)], [1.0, 0.9, 0.7], "Kkg")
    line(f.u, hx, hy + dy, hx + 1.5, hy + dy + 1.5, "hi")
    # body: one furry mass - abdomen, thorax with a pale ruff
    ell(f.b, hip[0] - 0.5, hip[1] - 1.5, 3.2, 4.2, "kghi", ang=-10 + lean * 2, bias=0.05)
    for k in range(3):
        y = hip[1] - 3 + k * 1.6
        for x in range(int(hip[0] - 2), int(hip[0] + 2)):
            if (x + k) % 2: f.b.put(*P(x, y), "g")
    ell(f.b, sh[0], sh[1] + 1.8, 3.4, 3.2, "ghiw", bias=0.15)
    for k in range(5): f.b.put(*P(sh[0] - 2 + k, sh[1] + 0.2 + (k % 2)), "W" if k % 2 else "w")   # ruff
    # head: pale moth mask, ember eyes, feathered antennae
    hx_, hy_ = sh[0] + 1.6, sh[1] - 2.6
    ell(f.b, hx_, hy_, 2.4, 2.4, "hwWX", bias=0.25)
    for k, (a0, a1) in enumerate(((-120, -160), (-70, -25))):
        pts = V.chain(hx_ - 0.5 + k * 1.5, hy_ - 2.0, [(2.0, a0), (2.0, a1)])
        line(f.b, pts[0][0], pts[0][1], pts[1][0], pts[1][1], "w"); line(f.b, pts[1][0], pts[1][1], pts[2][0], pts[2][1], "W")
        f.b.put(*P(pts[1][0] + (1 if k else -1), pts[1][1]), "w")
    ex_, ey_ = P(hx_ + 0.8, hy_ - 0.2)
    if dark:
        f.g.put(ex_, ey_, "k"); f.g.put(ex_ + 2, ey_, "k")
    elif mask == "scream":
        f.g.put(ex_, ey_, "Y"); f.g.put(ex_ + 2, ey_, "Y"); f.b.put(ex_ + 1, ey_ + 2, "K"); f.b.put(ex_ + 1, ey_ + 3, "K")
    else:
        f.g.put(ex_, ey_, "O"); f.g.put(ex_ + 2, ey_, "O"); f.b.put(ex_ + 1, ey_ + 2, "h")
    # near clawed forearm: upper arm, a long scythe forearm, three hooked claws
    (ex, ey), (hx, hy) = arm_f
    tube(f.b, [(sh[0] + 1.5, sh[1] + 2), (ex, ey + dy), (hx, hy + dy)], [1.1, 1.0, 0.8], "kghi")
    ha = math.atan2((hy - ey), (hx - ex))
    for k, da in enumerate((-50, 0, 45)):
        a = ha + math.radians(da + 70 * rake)
        line(f.b, hx, hy + dy, hx + 2.4 * math.cos(a), hy + dy + 2.4 * math.sin(a), "wWX")
    for (p, x, y) in embers:
        for (ddx, ddy, ch) in p: f.g.put(*P(x + ddx, y + ddy), ch)
    out = f.done(ink="K")
    if fade:
        out = Spr({k: v for k, v in out.px.items() if random.Random(k[0] * 31 + k[1] * 7).random() > fade * 0.3 or v in "OYy"})
    return out


EMB = [(0, 0, "Y"), (-1, 0, "O"), (1, 0, "O"), (0, 1, "o"), (-1, -1, "o"), (1, -1, "o")]


def build_matron(out):
    idle = [matron(dy=[0, -0.2, -0.4, -0.2][i], wing=-118 + [0, 8, 14, 6][i], wing_f=-92 + [0, 6, 10, 4][i],
                   arm_f=((5.0, -12.0 + [0, 0.5, 1, 0.5][i]), (8.0, -10.0 + [0, 0.5, 1, 0.5][i])), ember=1 + i % 2) for i in range(4)]
    run = []
    for i in range(6):
        t = i / 6.0 * 2 * math.pi
        run.append(matron(dy=-abs(math.sin(t)), lean=1.5, wing=-140 + math.sin(t) * 20, wing_f=-118 + math.sin(t) * 16,
                          legs=((-2 + 2 * math.cos(t), max(0, math.sin(t)) * 1.2), (2 - 2 * math.cos(t), max(0, -math.sin(t)) * 1.2)),
                          arm_f=((5.5, -12.5), (8.5, -11.0))))
    # Slash: claws raised (0-1), RAKE across (2: hit), follow (3: ash puff), recover (4-5)
    slash = [matron(arm_f=((4.0, -17.0), (7.0, -20.0)), arm_b=((-1.0, -16.0), (2.0, -19.0)), wing=-100, mask="scream", lean=-1),
             matron(arm_f=((3.0, -18.5), (5.0, -22.0)), arm_b=((-1.5, -17.0), (1.0, -21.0)), wing=-90, wing_f=-70, mask="scream", lean=-1.5),
             matron(arm_f=((7.0, -12.0), (12.0, -8.0)), arm_b=((3.0, -12.0), (8.0, -9.0)), wing=-150, wing_f=-125, lean=2.5, rake=1, mask="scream"),
             matron(arm_f=((7.0, -10.0), (11.0, -5.0)), arm_b=((3.0, -10.0), (7.0, -6.0)), wing=-145, wing_f=-120, lean=2.5, rake=1),
             matron(arm_f=((6.0, -11.0), (9.5, -8.0)), lean=1.0, wing=-125),
             matron()]
    brood = [matron(wing=-80, wing_f=-60, arm_f=((4.0, -13.0), (5.0, -16.0))),
             matron(wing=-75, wing_f=-55, arm_f=((4.0, -14.0), (5.0, -17.0)), ember=2, embers=[(EMB, 4, -18)]),
             matron(wing=-70, wing_f=-50, arm_f=((4.0, -15.0), (5.5, -18.5)), ember=2, mask="scream", embers=[(EMB, 4, -19), (EMB, 1, -16)]),
             matron(wing=-150, wing_f=-125, arm_f=((6.0, -12.0), (9.0, -12.0)), mask="scream",
                    embers=[(EMB, -6, -22), (EMB, 10, -20), (EMB, 3, -25)]),
             matron(wing=-130, wing_f=-105, embers=[(EMB, -9, -26), (EMB, 13, -24)]),
             matron()]
    # v0.10: a drawn crumble (shards + ember burst) instead of the random-pixel dissolve
    death = [matron(wing=-60, wing_f=-40, mask="scream", lean=-1),
             V.crumble(matron(dy=2, wing=-30, wing_f=-20, mask="scream", lean=-2), seed=3, cx=1.0, cy=-12.0, push=1.2, drop=1.2, burst=6.0),
             V.crumble(matron(dy=5, wing=0, wing_f=10, dark=True, lean=-3), seed=4, cx=1.0, cy=-8.0, push=2.2, drop=3.0, burst=3.0),
             matron(dy=7, wing=10, wing_f=20, dark=True, lean=-3)]
    death[2] = Spr({k: v for k, v in death[2].px.items() if k[1] <= 0})
    death[3] = Spr({k: v for k, v in death[3].px.items() if k[1] <= 0})
    knock = matron(lean=-2.5, wing=-160, wing_f=-140, mask="scream", arm_f=((3.0, -16.0), (1.0, -19.0)))
    anims = [("Idle", idle, [0.12] * 4), ("Run", run, [0.07] * 6)] + tail(idle[0], death, [0.1, 0.1, 0.12, 0.3], knock) + \
        [("Slash", slash, [0.1, 0.12, 0.05, 0.08, 0.1, 0.12]), ("Brood", brood, [0.12, 0.08, 0.1, 0.12, 0.14, 0.07])]
    sheet("MothMatron", anims, os.path.join(ROOT, "out"))


# ====================================================================================== VHORRUL: WICKLING (T1)
FLAME = "oOYy"


def flame(f, x, y, ang=-90.0, L=3.0, w=1.0, flick=0):
    """A small candle flame from its wick at (x, y) pointing ang (deg; -90 = up). Glow layer (no outline)."""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    for i in range(int(L * 2) + 1):
        t = i / (L * 2.0)
        r = w * (1.0 - t) * (1.2 if t < 0.35 else 1.0)
        cx, cy = x + ux * L * t + nx * 0.4 * math.sin(flick + t * 3), y + uy * L * t + ny * 0.4 * math.sin(flick + t * 3)
        for k in (-1, 0, 1):
            if abs(k) > r + 0.2: continue
            ch = "y" if t < 0.3 and k == 0 else ("Y" if t < 0.6 and k == 0 else ("O" if t < 0.75 else "o"))
            f.g.put(*P(cx + nx * k * 0.8, cy + ny * k * 0.8), ch)


def wickling(dx=0.0, dy=0.0, tilt=0.0, head=(0.0, 0.0), jaw=0, legs=None, tail_a=0.0, fl_a=-90.0, fl_L=3.0, flick=0,
             eye="lit", stretch=0.0, dark=False):
    """Wickling ~16 x 15: a crouched sooty wax rat with a pale tallow candle-skull for a head (lit wick on top, red eyes)
    and a long wick tail with an ember at its tip. head = (dx, dy) of the skull; stretch lengthens the body (dash)."""
    f = Fr()
    bx, by = dx - 0.5, -4.8 + dy
    # tail: a long wick curling up behind, ember tip
    t0 = (bx - 4.0 - stretch, by - 0.2)
    pts = V.chain(t0[0], t0[1], [(2.5, 190 + tail_a), (2.5, 230 + tail_a), (2.2, 265 + tail_a * 1.5)])
    for i in range(3):
        line(f.u, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], "Kk" if i < 2 else "k")
    if not dark:
        f.g.put(*P(*pts[3]), "O"); f.g.put(*P(pts[3][0], pts[3][1] - 1), "Y")
    # legs: thin, pale-wax; far pair darker
    if legs is None:
        legs = ((-3.0, 0.0), (3.0, 0.0), (-2.0, 0.0), (4.0, 0.0))
    for i, (fx, lift) in enumerate(legs):
        far = i >= 2
        hp = (bx + (-2.5 if i % 2 == 0 else 2.5) + (0.8 if far else 0), by + 1.2)
        foot = (dx + fx, -0.8 - lift)
        (kx, ky), _ = B.ik(hp[0], hp[1], foot[0], foot[1], 2.6, 2.6, bend=-1 if i % 2 == 0 else 1)
        lay = f.u
        tube(lay, [hp, (kx, ky), foot], [1.0, 0.7, 0.6], "Kkg" if far else "kgh")
        lay.put(*P(foot[0] + 1, foot[1] + 0.6), "h" if not far else "g")
    # body: a hunched sooty wax lump with drips
    ell(f.b, bx, by, 4.4 + stretch, 3.0 - stretch * 0.25, "kghi", ang=-12 + tilt, bias=0.1)
    for k, x in enumerate(range(int(bx - 3), int(bx + 4), 2)):
        f.b.put(x, int(round(by + 2.0 + (k % 2))), "w")                                # wax drips on the belly
    f.b.put(*P(bx - 1, by - 2), "w"); f.b.put(*P(bx + 1, by - 2.4), "W")
    # head: tallow candle-skull
    hx, hy = bx + 4.6 + stretch + head[0], by - 3.2 + head[1]
    ell(f.b, hx, hy, 2.6, 2.5, "hwWX", bias=0.3)
    ell(f.b, hx + 1.8, hy + 1.0 + jaw * 0.5, 1.5, 1.0, "hwW", bias=0.2)                 # snout
    if jaw:
        for k in range(3):
            f.b.put(*P(hx + 1.0 + k, hy + 1.8 + jaw * 0.8), "K" if k < 2 else "w")
        f.b.put(*P(hx + 1.2, hy + 2.4 + jaw), "W"); f.b.put(*P(hx + 2.6, hy + 2.4 + jaw), "W")   # lower jaw
    f.b.put(*P(hx - 1.6, hy + 2.0), "w"); f.b.put(*P(hx - 1.0, hy + 2.6), "W")          # tallow drip
    ex, ey = P(hx + 0.6, hy - 0.2)
    if dark:
        f.g.put(ex, ey, "K")
    else:
        f.b.put(ex, ey, "K"); f.g.put(ex, ey, "R" if eye == "lit" else "Y")
        f.g.put(ex - 1, ey, "r")
    # wick + flame on the crown
    wx, wy = hx - 0.4, hy - 2.6
    f.b.put(*P(wx, wy), "K"); f.b.put(*P(wx, wy - 1), "K")
    if not dark:
        flame(f, wx, wy - 1.6, fl_a, fl_L, 1.0, flick)
    return f.done(ink="K")


def q_legs(i, n=6, amp=2.2):
    t = i / float(n) * 2 * math.pi
    return ((-3 + amp * math.cos(t), max(0, math.sin(t)) * 1.2), (3 - amp * math.cos(t), max(0, -math.sin(t)) * 1.2),
            (-2 - amp * math.cos(t), max(0, -math.sin(t)) * 1.0), (4 + amp * math.cos(t), max(0, math.sin(t)) * 1.0))


def build_wickling(out):
    idle = [wickling(dy=[0, -0.3, -0.5, -0.3][i], tail_a=[0, 6, 10, 4][i], fl_L=[2.4, 2.8, 2.4, 2.0][i], flick=i * 1.6,
                     head=(0, [0, -0.3, -0.5, -0.3][i])) for i in range(4)]
    run = [wickling(dy=-abs(math.sin(i / 6.0 * 2 * math.pi)) * 0.8, tilt=-4, legs=q_legs(i), tail_a=-10 + 6 * math.sin(i),
                    fl_a=-130, fl_L=3.5, flick=i * 1.3) for i in range(6)]
    # Bite: crouch (0), hop (1-2), BITE (3: jaws at ~(9, -6)), land (4), recover (5)
    bite = [wickling(dy=0.6, head=(-0.5, 0.6), tilt=6, legs=((-2, 0), (2, 0), (-1, 0), (3, 0)), fl_L=2.5),
            wickling(dy=-2.0, head=(0.8, -0.8), tilt=-8, legs=((-4, 1.5), (4, 1.0), (-3, 1.2), (5, 0.8)), fl_a=-145, fl_L=4, jaw=1),
            wickling(dx=1.0, dy=-1.5, head=(2.0, 0.6), tilt=-4, legs=((-4, 1.0), (5, 0.5), (-3, 1.0), (6, 0.5)), fl_a=-160, fl_L=4, jaw=2),
            wickling(dx=1.5, dy=-0.4, head=(2.4, 1.4), tilt=4, legs=((-3, 0), (5, 0), (-2, 0), (6, 0)), fl_a=-150, fl_L=3.5, jaw=0),
            wickling(dx=1.0, head=(1.2, 0.8), tilt=4, fl_a=-110, fl_L=3),
            wickling(dx=0.5, fl_L=3)]
    # Dash: wind-up (0-1, flame flares), STREAK (2-4: body stretched, flame trailing), skid (5), recover (6)
    dash = [wickling(dy=0.8, head=(-0.6, 0.8), tilt=8, legs=((-2, 0), (2, 0), (-1, 0), (3, 0)), fl_L=4),
            wickling(dy=1.0, head=(-0.8, 1.0), tilt=10, legs=((-2, 0), (2, 0), (-1, 0), (3, 0)), fl_L=5, fl_a=-95, eye="hot"),
            wickling(dy=-0.6, stretch=1.5, tilt=-2, legs=((-6, 0.5), (6, 0.5), (-5, 0.8), (7, 0.3)), fl_a=-170, fl_L=5, tail_a=-30, eye="hot"),
            wickling(dy=-0.6, stretch=1.5, tilt=-2, legs=((-5, 1.0), (5, 1.0), (-6, 0.4), (6, 0.6)), fl_a=-172, fl_L=5.5, tail_a=-32, flick=2, eye="hot"),
            wickling(dy=-0.4, stretch=1.2, tilt=-2, legs=((-6, 0.4), (6, 0.4), (-5, 1.0), (7, 1.0)), fl_a=-168, fl_L=5, tail_a=-28, flick=4),
            wickling(dx=1.0, dy=0.4, head=(0.6, 0.6), tilt=6, legs=((-2, 0), (5, 0), (-1, 0), (6, 0)), fl_a=-120, fl_L=3.5),
            wickling(fl_L=3)]
    death = [wickling(head=(-0.6, -0.8), tilt=-10, eye="hot", fl_a=-60, fl_L=4, jaw=2),
             wickling(dy=1.2, head=(-0.2, 1.0), tilt=10, legs=((-4, 0), (4, 0), (-3, 0), (5, 0)), fl_a=-40, fl_L=2, jaw=1),
             wickling(dy=2.2, head=(0.4, 2.2), tilt=14, legs=((-5, 0), (5, 0), (-4, 0), (6, 0)), fl_L=1, dark=True),
             wickling(dy=2.8, head=(0.6, 2.8), tilt=16, legs=((-6, 0), (6, 0), (-5, 0), (7, 0)), dark=True)]
    knock = wickling(dx=-0.5, head=(-1.0, -1.2), tilt=-12, eye="hot", fl_a=-40, fl_L=4, jaw=2)
    anims = [("Idle", idle, [0.16] * 4), ("Run", run, [0.07] * 6)] + tail(idle[0], death, [0.08, 0.1, 0.14, 0.3], knock) + \
        [("Bite", bite, [0.08, 0.07, 0.06, 0.12, 0.08, 0.12]), ("Dash", dash, [0.1, 0.12, 0.06, 0.06, 0.06, 0.18, 0.12])]
    sheet("Wickling", anims, os.path.join(ROOT, "out"))


# ====================================================================================== VHORRUL: ASH MOTH (T1)
def ashmoth(dx=0.0, alt=6.6, tilt=0.0, wing=-110.0, wing_f=-85.0, ember=1, eye="lit", puff=0, dark=False, fall=0.0):
    """Ash Moth ~18 x 16 hovering (body centre ~7 px up): a fuzzy sooty moth facing right; two broad ash wings with an
    ember eye-spot, a pale fuzzy head, a red eye and feathered antennae (the Moth Matron line)."""
    f = Fr()
    cx, cy = dx, -alt
    ta = math.radians(tilt)
    def R(x, y):  # rotate about the body centre by tilt
        return (cx + x * math.cos(ta) - y * math.sin(ta), cy + x * math.sin(ta) + y * math.cos(ta))
    root = R(-0.5, -1.2)
    V.moth_wing(f, "u", (root[0] + 1.0, root[1]), 7.0, wing_f + tilt, 0.5, "kgh", "K", [(0.6, 0.0, False)], 61, tatter=0.1)
    # body: abdomen behind, thorax, head forward
    ab = R(-3.2, 0.6)
    ell(f.b, ab[0], ab[1], 3.0, 1.8, "kgh", ang=tilt + 8, bias=0.05)
    for k in range(3):
        sx, sy = R(-4.5 + k * 1.3, 0.4)
        f.b.put(*P(sx, sy), "K")                                                       # abdomen bands
    th = R(0.0, 0.0)
    ell(f.b, th[0], th[1], 2.2, 2.0, "ghiw", bias=0.15)
    hd = R(2.6, -0.4)
    ell(f.b, hd[0], hd[1], 1.7, 1.6, "hwWX", bias=0.3)
    for k, a0 in enumerate((-115, -70)):                                               # feathered antennae
        b0 = R(2.6 + k * 0.8, -1.8)
        pts = V.chain(b0[0], b0[1], [(1.8, a0 + tilt), (1.8, a0 + 30 + tilt)])
        line(f.b, pts[0][0], pts[0][1], pts[1][0], pts[1][1], "w"); line(f.b, pts[1][0], pts[1][1], pts[2][0], pts[2][1], "W")
    ex, ey = P(*R(3.4, -0.6))
    if dark:
        f.g.put(ex, ey, "K")
    else:
        f.g.put(ex, ey, "R" if eye == "lit" else "Y")
    # legs dangling under the thorax
    for k in range(2):
        l0 = R(-0.5 + k * 1.4, 1.6)
        line(f.u, l0[0], l0[1], l0[0] + 0.6, l0[1] + 1.2 - fall * 0.6, "Kk")
    # near wing over the body
    V.moth_wing(f, "b", root, 7.6, wing + tilt, 0.55, "hiwW", "g", [(0.6, -0.05, ember >= 1 and not dark)], 62, tatter=0.12)
    for k in range(puff):                                                              # ash cloud out of the mouth
        px_, py_ = R(4.6 + k * 1.2, 0.2 + (k % 2) * 0.8)
        f.g.put(*P(px_, py_), "i" if k % 2 else "h")
        f.g.put(*P(px_ + 0.6, py_ - 1.0), "w" if k == puff - 1 else "g")
    return f.done(ink="K")


def build_ashmoth(out):
    flap = [(-115, -92), (-95, -72), (-62, -46), (-38, -24), (-62, -46), (-95, -72)]
    alt = [6.6, 6.7, 7.0, 7.0, 6.8, 6.6]
    idle = [ashmoth(alt=alt[i], wing=flap[i][0], wing_f=flap[i][1], ember=1) for i in range(6)]
    run = [ashmoth(alt=alt[i] - 0.3, tilt=6, wing=flap[i][0] - 10, wing_f=flap[i][1] - 8) for i in range(6)]
    # Puff: rear back (0-2), PUFF (3: cloud from the mouth at ~(5, -7)), recoil (4-5)
    puff = [ashmoth(alt=7.2, tilt=-8, wing=-118, wing_f=-95), ashmoth(alt=7.6, tilt=-14, wing=-95, wing_f=-72, eye="hot"),
            ashmoth(alt=7.8, tilt=-16, wing=-130, wing_f=-110, eye="hot"),
            ashmoth(dx=0.5, alt=7.0, tilt=6, wing=-20, wing_f=-10, puff=3, ember=2),
            ashmoth(dx=-0.5, alt=7.0, tilt=0, wing=-70, wing_f=-50, puff=1), ashmoth(alt=6.8, wing=-110, wing_f=-88)]
    # Dive: rise (0-1), PLUNGE forward-down (2-4: wings swept back), burst (5), recover (6)
    dive = [ashmoth(alt=7.4, tilt=-10, wing=-120, wing_f=-96), ashmoth(alt=8.2, tilt=-16, wing=-90, wing_f=-70, eye="hot", ember=2),
            ashmoth(dx=1.0, alt=6.0, tilt=22, wing=-172, wing_f=-160, eye="hot", ember=2),
            ashmoth(dx=1.5, alt=5.0, tilt=26, wing=-175, wing_f=-165, eye="hot", ember=2),
            ashmoth(dx=2.0, alt=4.4, tilt=28, wing=-170, wing_f=-160, eye="hot", ember=2),
            ashmoth(dx=1.0, alt=5.6, tilt=-6, wing=-20, wing_f=-5, puff=3),
            ashmoth(alt=6.4, wing=-100, wing_f=-80)]
    death = [ashmoth(alt=6.0, tilt=-20, wing=-60, wing_f=-40, eye="hot"),
             ashmoth(alt=4.0, tilt=-35, wing=-10, wing_f=10, eye="hot", fall=1),
             ashmoth(alt=2.2, tilt=-10, wing=10, wing_f=25, dark=True, fall=1.5),
             ashmoth(alt=1.4, tilt=0, wing=-170, wing_f=-190, dark=True, fall=1.8)]
    knock = ashmoth(alt=7.0, tilt=-22, wing=-160, wing_f=-140, eye="hot")
    anims = [("Idle", idle, [0.07] * 6), ("Run", run, [0.06] * 6)] + tail(idle[0], death, [0.08, 0.08, 0.08, 0.3], knock) + \
        [("Puff", puff, [0.07, 0.07, 0.06, 0.12, 0.08, 0.1]), ("Dive", dive, [0.1, 0.14, 0.05, 0.05, 0.05, 0.12, 0.1])]
    sheet("AshMoth", anims, os.path.join(ROOT, "out"))


BUILDERS = {"OssRattlebones": build_rattlebones, "OssMarrowHound": build_hound, "OssBoneRat": build_rat,
            "OssCairnCrow": build_crow, "BelCrab": build_crab, "BelDiver": build_diver, "MothMatron": build_matron,
            "Wickling": build_wickling, "AshMoth": build_ashmoth}


if __name__ == "__main__":
    a = sys.argv[1:]
    only = None
    if "--only" in a:
        i = a.index("--only"); only = set(a[i + 1].split(",")); del a[i:i + 2]
    if a: ROOT = a[0]
    for n, fn in BUILDERS.items():
        if only and n not in only: continue
        fn(ROOT)
