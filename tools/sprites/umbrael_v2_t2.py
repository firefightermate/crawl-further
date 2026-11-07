"""Umbrael tier 2 sheets: The Twinned, Nailshade, Mirror Witch, Gloamcoil, Glassmoth, Hourglass.
Drawn with the renderer and parts in umbrael_v2_rigs.py; feet at y=0, facing right, y up negative."""
import math, random
from umbrael_v2_rigs import (SRig, Rig, Xf, chain, ik, lerp, sheet, tail_anims, J, mask_stamp, MASK_LEG, smoke_tail, wisps,
                             shards, claw_hand, arc_smear, floor_shadow, remains, twinkle, dust)


# ================================================================== THE TWINNED: two bodies joined at the back
TWIN_DARK = """
.awWw.
aWWWWw
WkWWkw
WWWWWw
.wkkw.
"""
TWIN_PALE = """
.hHVh.
hVVVVh
VcVVcV
VVVVVh
.hVVh.
"""
TWIN_SNARL = """
.awWw.
aWWWWw
WnWWnw
WWWWWw
.wmmw.
"""
TWIN_HURT = """
.awWw.
aWkWkw
WWkWWw
WkWkWw
.wWWw.
"""


def sickle(r, hx, hy, ang, z, mat="silver", ln=8.0, curve=1.0):
    """A crescent blade from the hand at (hx, hy) along ang (deg, y down), curving back at the tip."""
    pts = [(hx, hy)]
    a = ang
    x, y = hx, hy
    for i in range(5):
        x += ln / 5 * math.cos(math.radians(a)); y += ln / 5 * math.sin(math.radians(a))
        pts.append((x, y)); a += 22 * curve
    r.tube(pts[:2], [0.7, 0.6], "void", z)
    r.tube(pts[1:], [0.9, 1.0, 0.9, 0.6, 0.3], mat, z + 0.01, bias=0.2)
    return pts[-1]


def twinned(lean=0.0, bob=0.0, feet=((-2.5, 0.0), (2.5, 0.0)), dark_hand=None, pale_hand=None, dark_ang=-40.0,
            pale_ang=-140.0, face="calm", pale_face="calm", smear=None, flash=None, spread=0.0, extra=None, dx=0.0):
    """Two masked torsos from one pelvis: the dark one faces right (front), the pale glass one faces left (back).
    spread leans them apart (the Swap's pointing pose)."""
    r = Rig()
    hip = (dx, -8.0 + bob)
    T = Xf(lean, hip)
    for k, f in enumerate(feet):
        hp = (hip[0] + (-1.0 if k == 0 else 1.0), hip[1] + 0.5)
        kn = ik(hp[0], hp[1], f[0], f[1] - 0.8, 4.4, 4.2, bend=1 if k == 0 else -1)
        mat = "pale" if k == 0 else "void"
        z = -1.0 if k == 0 else 1.0
        r.tube([hp, kn, (f[0], f[1] - 0.8)], [1.2, 1.0, 0.8], mat, z, bias=0.05 if k else -0.15)
        r.poly([(f[0] - 1.6 + (0 if k else 0.4), f[1] - 1.6), (f[0] + 1.6, f[1] - 1.2), (f[0] + 1.6, f[1]), (f[0] - 1.6, f[1])],
               mat, z + 0.01, bias=0.1)
    # the seam where they join: a lilac crack up the spine
    sp0, sp1 = T(hip[0], hip[1]), T(hip[0], hip[1] - 9.0)
    # pale torso (behind, leans back-left)
    Tp = Xf(-14 - spread, hip)
    pc = Tp(hip[0] - 1.6, hip[1] - 4.8)
    r.ell(pc[0], pc[1], 2.8, 4.6, "pale", -0.5, bias=0.0, ang=-10 - spread)
    psh = Tp(hip[0] - 2.4, hip[1] - 7.6)
    ph = pale_hand or Tp(hip[0] - 7.0, hip[1] - 5.0)
    e = ik(psh[0], psh[1], ph[0], ph[1], 3.2, 3.2, bend=1)
    r.tube([psh, e, ph], [1.1, 0.9, 0.8], "pale", -0.4, bias=-0.05)
    sickle(r, ph[0], ph[1], pale_ang, -0.3, mat="glass", curve=-1.0)
    phd = Tp(hip[0] - 2.0, hip[1] - 10.4)
    r.stamp(TWIN_PALE if pale_face == "calm" else TWIN_HURT, phd[0], phd[1], -0.2, MASK_LEG, pivot=(3, 4), flip=True)
    # dark torso (front, leans forward-right)
    Td = Xf(10 + spread, hip)
    dc = Td(hip[0] + 1.4, hip[1] - 4.8)
    r.ell(dc[0], dc[1], 3.0, 4.8, "void", 0.5, bias=0.1, ang=8 + spread)
    r.dot(dc[0] - 1.8, dc[1] - 2.6, "lilac", 2, 0.6)
    dsh = Td(hip[0] + 2.2, hip[1] - 7.8)
    dh = dark_hand or Td(hip[0] + 6.6, hip[1] - 5.0)
    e = ik(dsh[0], dsh[1], dh[0], dh[1], 3.2, 3.2, bend=-1)
    r.tube([dsh, e, dh], [1.2, 1.0, 0.8], "void", 3.0, bias=0.15)
    sickle(r, dh[0], dh[1], dark_ang, 3.1)
    dhd = Td(hip[0] + 2.0, hip[1] - 10.6)
    r.stamp({"calm": TWIN_DARK, "snarl": TWIN_SNARL}.get(face, TWIN_HURT), dhd[0], dhd[1], 2.0, MASK_LEG, pivot=(3, 4))
    r.polyline([sp0, ((sp0[0] + sp1[0]) / 2 + 0.6, (sp0[1] + sp1[1]) / 2), sp1], "lilac", 1.5, tones=[3, 4])
    if smear:
        for (cx, cy, R, a0, a1, m) in smear:
            arc_smear(r, cx, cy, R, a0, a1, mat=m, width=2, z=6.0)
    if flash:
        x, y, k = flash
        twinkle(r, x, y, k)
    if extra: extra(r)
    return r.resolve()


def twinned_sheet(outdir):
    W = twinned
    idle = [W(bob=[0, -0.3, -0.5, -0.3][i], dark_hand=(6.4, -12.0 + [0, -0.3, -0.5, -0.3][i]),
              pale_hand=(-6.6, -11.6 + [0, -0.3, -0.5, -0.3][i])) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        run.append(W(lean=8, bob=-0.5 * abs(math.sin(ph)), feet=((-2.8 * math.cos(ph), -max(0, 1.6 * math.sin(ph))),
                                                                 (2.8 * math.cos(ph), -max(0, -1.6 * math.sin(ph)))),
                     dark_hand=(7.0, -11.0 + math.sin(ph)), pale_hand=(-6.0, -12.0 - math.sin(ph))))
    # Cut (8): the dark body winds up (0-1), slashes ahead (2 = HIT), they turn on the hips (3), the pale body slashes
    # behind (4 = HIT), follow-through (5-6), settle (7)
    cut = [W(lean=-8, dark_hand=(1.0, -19.0), dark_ang=-120, face="snarl"),
           W(lean=-4, dark_hand=(4.0, -19.0), dark_ang=-80, face="snarl", smear=[(2, -12, 8, -120, -60, "lilac")]),
           W(lean=14, dark_hand=(10.0, -6.0), dark_ang=40, face="snarl", feet=((-3.0, 0.0), (3.6, 0.0)), dx=1.0,
             smear=[(2, -12, 9, -70, 40, "lilac")]),
           W(lean=4, dark_hand=(8.0, -5.0), dark_ang=60, pale_hand=(-2.0, -19.0), pale_ang=-60),
           W(lean=-14, dark_hand=(6.0, -8.0), pale_hand=(-10.0, -6.0), pale_ang=140, feet=((-3.6, 0.0), (3.0, 0.0)), dx=-1.0,
             smear=[(-2, -12, 9, -110, -220, "white")]),
           W(lean=-8, pale_hand=(-8.0, -5.0), pale_ang=120), W(lean=-2), W()]
    # Swap (9): both point at the hero (0-2), the mirror flash (3-4: the swap), the dark body recovers (5) and cuts (6 = HIT),
    # back (7-8)
    swap = [W(spread=6, dark_hand=(9.0, -13.0), dark_ang=-10, pale_hand=(-9.0, -13.0), pale_ang=-170),
            W(spread=10, dark_hand=(10.0, -14.0), dark_ang=-5, pale_hand=(-10.0, -14.0), pale_ang=-175, flash=(10, -16, 2)),
            W(spread=12, dark_hand=(10.0, -15.0), dark_ang=0, pale_hand=(-10.0, -15.0), pale_ang=-180, flash=(0, -14, 2)),
            W(spread=12, dark_hand=(10.0, -15.0), dark_ang=0, pale_hand=(-10.0, -15.0), pale_ang=-180, flash=(0, -12, 1)),
            W(spread=4, lean=-6, dark_hand=(3.0, -18.0), dark_ang=-110, flash=(-4, -18, 2), face="snarl"),
            W(lean=-8, dark_hand=(2.0, -19.0), dark_ang=-120, face="snarl"),
            W(lean=14, dark_hand=(10.0, -6.0), dark_ang=40, face="snarl", dx=1.0, smear=[(2, -12, 9, -70, 40, "lilac")]),
            W(lean=6, dark_hand=(8.0, -6.0), dark_ang=50), W()]
    d0 = W(lean=-12, face="hurt", pale_face="hurt", dark_hand=(4.0, -16.0), pale_hand=(-8.0, -9.0))
    d1 = W(lean=-24, bob=3.0, face="hurt", pale_face="hurt", spread=14, dark_hand=(6.0, -8.0), pale_hand=(-9.0, -4.0),
           feet=((-4.0, 0.0), (3.0, 0.0)))
    d2 = remains(0, mask=(TWIN_DARK, (3, 4)), mask_at=(2.0, -1.0), stain=8.0, glass=5, glass_mats=("pale", "glass"),
                 extra=lambda r: wisps(r, 0, -5, 1, n=6, spread=7, seed=8, z=4))
    corpse = remains(1, mask=(TWIN_HURT, (3, 4)), mask_at=(2.5, -0.5), stain=9.0, glass=6, glass_mats=("pale", "glass"),
                     extra=lambda r: r.stamp(TWIN_PALE, -4.0, -0.5, 3.0, MASK_LEG, pivot=(3, 4), flip=True))
    knock = W(lean=-16, face="hurt", pale_face="hurt", dark_hand=(3.0, -16.0), pale_hand=(-9.0, -10.0))
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.08] * 6),
             ("Cut", cut, [0.12, 0.06, 0.1, 0.08, 0.1, 0.1, 0.1, 0.12]),
             ("Swap", swap, [0.1, 0.1, 0.1, 0.08, 0.06, 0.06, 0.1, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("UmbTwinned", anims, outdir, scale=6)


# ================================================================== NAILSHADE: a gaunt shade stuck with glass nails
NAIL_HEAD = {
    "calm": """
..aww..
.aWWWw.
.WknWk.
.WWWWw.
..wkw..
..aw...
""",
    "snarl": """
..aww..
.aWWWw.
.WneWn.
.wWWWw.
..kmk..
..akw..
""",
    "hurt": """
..aww..
.aWkWw.
.WmkWm.
.wWkkw.
..wWw..
..aw...
""",
}
# where glass nails stick out of it (x, y from the hip, angle deg y down, length)
NAILS_IN = [(-3.0, -4.4, -150, 2.6), (-3.0, -7.0, -165, 3.0), (-1.8, -9.4, -125, 2.6), (1.6, -9.6, -60, 2.2),
            (-3.2, -2.0, 170, 2.2), (1.2, -2.6, -30, 1.6), (-0.6, -10.4, -100, 2.4), (-2.4, -8.4, -140, 2.0)]


def nails_in(r, T, hip, z, k=0):
    for i, (x, y, a, ln) in enumerate(NAILS_IN):
        bx, by = T(hip[0] + x, hip[1] + y)
        a2 = math.radians(a)
        tx, ty = bx + ln * math.cos(a2), by + ln * math.sin(a2)
        r.line(bx, by, tx, ty, "glass", z + 0.01 * i, tone=3)
        r.dot(tx, ty, "white", 4 if (i + k) % 3 else 3, z + 0.01 * i + 0.005)


def held_nails(r, hx, hy, ang, spread, z, n=3, ln=4.0):
    for k in range(n):
        a = math.radians(ang + (k - (n - 1) / 2.0) * spread / max(1, n - 1))
        tx, ty = hx + ln * math.cos(a), hy + ln * math.sin(a)
        r.line(hx, hy, tx, ty, "glass", z + 0.01 * k, tone=3)
        r.dot(tx, ty, "white", 4, z + 0.01 * k + 0.005)


def nailshade(lean=0.0, bob=0.0, feet=((-2.0, 0.0), (2.4, 0.0)), hand=None, hand2=None, hold=30.0, hold_ang=-20.0,
              face="calm", smear=None, fade=None, extra=None, hold_n=3, dx=0.0, crouch=0.0):
    """Tall and thin: long legs, a narrow hunched body full of nails, arms that hang to the knees with long fingers.
    hold = the spread (degrees) of the nails fanned in the near hand (None: empty hand)."""
    r = Rig()
    hip = (dx, -8.0 + bob + crouch)
    T = Xf(lean, hip)
    if fade is None or fade < 2:
        for k, f in enumerate(feet):
            hp = (hip[0] + (-0.8 if k == 0 else 0.8), hip[1] + 0.4)
            kn = ik(hp[0], hp[1], f[0], f[1] - 0.6, 4.4, 4.2, bend=-1)
            z = -1.0 if k == 0 else 1.0
            r.tube([hp, kn, (f[0], f[1] - 0.6)], [1.4, 1.1, 0.8], "shade", z, bias=-0.25 if k == 0 else 0.0)
            r.line(f[0], f[1], f[0] + 1.8, f[1], "shade", z + 0.01, tone=1)
            r.dot(f[0] + 2.2, f[1], "silver", 3, z + 0.02)
        # body: narrow, hunched forward
        top = T(hip[0] + 1.6, hip[1] - 8.0)
        r.tube([T(*hip), T(hip[0] + 0.6, hip[1] - 4.4), top], [3.0, 3.6, 3.0], "shade", 0.0, bias=0.1)
        # a ragged shroud of smoke hanging off the back
        r.poly([T(hip[0] - 2.0, hip[1] - 8.0), T(hip[0] - 5.4, hip[1] - 3.0), T(hip[0] - 4.6, hip[1] + 1.0),
                T(hip[0] - 3.4, hip[1] - 0.6), T(hip[0] - 2.6, hip[1] + 2.0), T(hip[0] - 1.0, hip[1])], "void", -0.8, bias=-0.1)
        r.ell(*T(hip[0] - 0.4, hip[1] - 7.4), 2.6, 2.0, "void", 0.05, bias=0.25)        # the hunch
        r.dot(*T(hip[0] - 1.8, hip[1] - 6.0), "lilac", 2, 0.1)
        nails_in(r, T, hip, 0.5)
        sh_n, sh_f = T(hip[0] + 2.6, hip[1] - 7.4), T(hip[0] - 0.8, hip[1] - 7.8)
        h2 = hand2 or T(hip[0] - 3.0, hip[1] + 1.0)
        e = ik(sh_f[0], sh_f[1], h2[0], h2[1], 4.2, 4.2, bend=1)
        r.tube([sh_f, e, h2], [1.1, 0.9, 0.7], "shade", -0.6, bias=-0.3)
        claw_hand(r, h2[0], h2[1], 100, -0.5, ln=3.6, spread=30, tone=2)
        # head on a forward neck
        hd = T(hip[0] + 3.4, hip[1] - 9.6)
        r.stamp(NAIL_HEAD[face], hd[0], hd[1], 2.0, MASK_LEG, pivot=(3, 5))
        for (ox, oy, a) in ((-1.5, -5.0, -150), (0.0, -5.6, -110), (2.0, -5.0, -40)):     # a crown of nails
            x0, y0 = hd[0] + ox, hd[1] + oy
            r.line(x0, y0, x0 + 1.6 * math.cos(math.radians(a)), y0 + 1.6 * math.sin(math.radians(a)), "glass", 2.1, tone=3)
        h1 = hand or T(hip[0] + 6.0, hip[1] - 2.0)
        e = ik(sh_n[0], sh_n[1], h1[0], h1[1], 4.4, 4.4, bend=-1)
        r.tube([sh_n, e, h1], [1.2, 1.0, 0.8], "shade", 3.0, bias=0.1)
        if hold is None:
            claw_hand(r, h1[0], h1[1], 20, 3.1, ln=3.8, spread=34)
        else:
            claw_hand(r, h1[0], h1[1], hold_ang + 40, 3.0, ln=2.6, spread=30, tone=2)
            held_nails(r, h1[0] + 0.5, h1[1], hold_ang, hold, 3.2, n=hold_n)
    if fade:
        wisps(r, hip[0] + 1, hip[1] - 6, fade, n=8, spread=6 + fade, seed=30 + fade, z=5)
        shards(r, hip[0] + 1, hip[1] - 6, fade, n=5, seed=31)
    if smear:
        for pts, m in smear:
            r.polyline(pts, m, 5.0, tone=3)
    if extra: extra(r)
    return r.resolve()


SPREADS = {"": 30.0, "Mid": 20.0, "Tight": 10.0}


def nailshade_sheet(outdir):
    N = nailshade
    anims = []
    for tag, sp in SPREADS.items():
        idle = [N(bob=[0, -0.3, -0.5, -0.3][i], hold=sp, hand=(6.6, -10.0 + [0, -0.3, -0.5, -0.3][i])) for i in range(4)]
        run = []
        for i in range(6):
            ph = i / 6 * math.tau
            run.append(N(lean=10, bob=-0.6 * abs(math.sin(ph)), hold=sp, hand=(7.0, -9.5 + 0.6 * math.sin(ph)),
                         feet=((-3.2 * math.cos(ph), -max(0, 1.8 * math.sin(ph))), (3.2 * math.cos(ph), -max(0, -1.8 * math.sin(ph))))))
        # Fling (7): draw the fan back past the ear (0-1), whip the arm through (2 = release), follow (3-4), a new fan (5-6)
        fl = [N(lean=-8, hold=sp, hand=(-1.0, -22.0), hold_ang=-110, face="snarl"),
              N(lean=-12, hold=sp, hand=(-3.0, -21.0), hold_ang=-140, face="snarl"),
              N(lean=12, hold=None, hand=(10.0, -13.0), face="snarl", dx=1.0, feet=((-2.5, 0.0), (3.4, 0.0)),
                smear=[([(0, -22), (5, -20), (9, -15)], "lilac")]),
              N(lean=10, hold=None, hand=(9.0, -8.0), dx=1.0, feet=((-2.5, 0.0), (3.4, 0.0))),
              N(lean=4, hold=None, hand=(7.0, -6.0)),
              N(lean=0, hold=sp * 0.5, hand=(4.0, -12.0), hold_n=2, hold_ang=-60),
              N(hold=sp, hand=(6.6, -10.0))]
        if tag == "":
            anims += [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.08] * 6)]
        else:
            anims += [("Idle" + tag, idle, [0.14, 0.12, 0.14, 0.12]), ("Run" + tag, run, [0.08] * 6)]
        anims.append(("Fling" + tag, fl, [0.12, 0.1, 0.06, 0.08, 0.1, 0.12, 0.12]))
    # Pin (9): a single black pin between two fingers (0-1), THROW (2-3: release on 3), melt into smoke (4-5), gone (6),
    # re-form beside the hero (7: the rake lands), back (8)
    pin = [N(lean=-6, hold=0.0, hold_n=1, hand=(2.0, -20.0), hold_ang=-100, face="snarl"),
           N(lean=-10, hold=0.0, hold_n=1, hand=(-1.0, -21.0), hold_ang=-130, face="snarl"),
           N(lean=6, hold=0.0, hold_n=1, hand=(6.0, -18.0), hold_ang=-30, face="snarl"),
           N(lean=14, hold=None, hand=(11.0, -12.0), face="snarl", dx=1.0, smear=[([(1, -21), (6, -19), (10, -14)], "lilac")]),
           N(lean=8, hold=None, hand=(8.0, -8.0), fade=1),
           N(fade=2), N(fade=3),
           N(lean=16, hold=None, hand=(11.0, -6.0), face="snarl", dx=2.0, crouch=1.0,
             smear=[([(4, -18), (9, -14), (12, -7)], "lilac")]),
           N(lean=4, hold=20.0, hand=(6.6, -10.0))]
    anims.append(("Pin", pin, [0.12, 0.1, 0.08, 0.08, 0.06, 0.06, 0.1, 0.1, 0.14]))
    d0 = N(lean=-14, face="hurt", hold=None, hand=(3.0, -20.0), hand2=(-5.0, -14.0))
    d1 = N(lean=-26, crouch=3.0, face="hurt", hold=None, hand=(2.0, -10.0), hand2=(-7.0, -6.0), fade=1)
    d2 = remains(0, mask=(NAIL_HEAD["hurt"], (3, 5)), mask_at=(2.0, -1.0), stain=9.0, glass=8, glass_mats=("glass", "white"),
                 extra=lambda r: wisps(r, 0, -6, 2, n=6, spread=7, seed=9, z=4))
    corpse = remains(1, mask=(NAIL_HEAD["hurt"], (3, 5)), mask_at=(3.0, -0.5), stain=10.0, glass=10, glass_mats=("glass", "white"))
    knock = N(lean=-18, face="hurt", hold=20.0, hand=(4.0, -18.0), hand2=(-5.0, -12.0))
    anims += tail_anims(anims[0][1][0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("UmbNailshade", anims, outdir, scale=6)


# ================================================================== MIRROR WITCH: her face shows only in the glass
WITCH_FACE = {
    "calm": """
.awwa.
aWXWWw
WkWWkw
WnWWnw
.WkkW.
..aa..
""",
    "cast": """
.awwa.
aWXWWw
WeWWew
WnWWnw
.WmmW.
..aa..
""",
    "hurt": """
.awwa.
aWkWWw
WmkWmw
WWkkWw
.WkWW.
..aa..
""",
}


def hand_mirror(r, cx, cy, ang, z, face="calm", flash=0, crack=False, tilt=0.0):
    """An oval mirror in a silver frame on a handle below (cx, cy = the glass centre); her face looks out of it."""
    T = Xf(ang, (cx, cy + 6.0))
    r.tube([T(cx, cy + 4.0), T(cx, cy + 7.5)], [0.7, 0.6], "silver", z)
    r.dot(*T(cx, cy + 8.0), "lilac", 3, z + 0.01)
    r.ell(*T(cx, cy), 4.0, 5.0, "silver", z + 0.02, ang=ang)
    r.ell(*T(cx, cy), 3.0, 4.0, "glass", z + 0.03, ang=ang, bias=0.2)
    r.dot(*T(cx, cy - 5.4), "lilac", 3, z + 0.025)
    fx, fy = T(cx + 0.5, cy + 1.6)
    if face:
        r.stamp(WITCH_FACE[face], fx, fy, z + 0.04, MASK_LEG, pivot=(3, 5))
    if crack:
        r.polyline([T(cx - 2, cy - 3), T(cx, cy - 1), T(cx - 1, cy + 1), T(cx + 2, cy + 3)], "void", z + 0.05, tone=1)
    if flash:
        twinkle(r, *T(cx - 1.0, cy - 2.6), flash, z=z + 0.1)


def mirror_witch(lean=0.0, bob=0.0, mirror=None, m_ang=0.0, face="calm", hand2=None, sway=0.0, flash=0, extra=None,
                 crack=False, dx=0.0, hem=0.0):
    """A tall robed witch under a hood that holds only darkness; the near hand holds the mirror up at `mirror`."""
    r = Rig()
    base = (dx, 0.0)
    T = Xf(lean, (dx, -2.0))
    # robe: a long bell to the floor, ragged hem that sways
    hem_pts = [(dx - 5.0 - hem, 0.0), (dx - 3.0, -0.8 + 0.4 * math.sin(sway)), (dx - 1.0, 0.0), (dx + 1.2, -0.6),
               (dx + 3.2, 0.0), (dx + 4.6 + hem, -0.6)]
    body = [T(dx - 2.6, -14.0 + bob), T(dx + 2.8, -14.0 + bob), T(dx + 4.8 + hem * 0.5, -4.0)] + hem_pts[::-1][:1] + \
           hem_pts[::-1][1:] + [T(dx - 4.8 - hem * 0.5, -4.0)]
    r.poly(body, "dusk", 0.0, curve=0.9)
    r.poly([T(dx - 1.0, -13.6 + bob), T(dx + 1.6, -13.6 + bob), T(dx + 2.4, -1.0), T(dx - 1.6, -1.0)], "void", 0.05, curve=0.4)
    for (x, y) in hem_pts:
        r.dot(x, y - 0.6, "silver", 2, 0.12)                                                # silver-stitched hem
    for x in (-2.0, 1.0):
        r.line(dx + x, -2.0, dx + x + 0.6, -10.0 + bob, "robe", 0.1, tone=1)              # folds
    r.line(*T(dx - 2.8, -8.0 + bob), *T(dx + 2.8, -8.0 + bob), "silver", 0.15, tone=3)  # a silver girdle
    r.dot(*T(dx + 0.4, -8.0 + bob), "lilac", 3, 0.16)
    # far arm
    sh_f = T(dx - 1.8, -12.6 + bob)
    h2 = hand2 or T(dx - 4.0, -6.0 + bob)
    e = ik(sh_f[0], sh_f[1], h2[0], h2[1], 3.6, 3.6, bend=1)
    r.tube([sh_f, e, h2], [1.2, 1.0, 0.8], "robe", -0.5, bias=-0.3)
    r.dot(h2[0], h2[1] + 0.5, "bone", 2, -0.45)
    # hood: a tall pointed cowl, its opening black
    hc = T(dx + 0.4, -17.0 + bob)
    r.poly([(hc[0] - 3.8, hc[1] + 3.6), (hc[0] - 3.2, hc[1] - 2.0), (hc[0] - 5.0, hc[1] - 7.6), (hc[0] + 0.4, hc[1] - 3.8),
            (hc[0] + 3.6, hc[1] - 1.0), (hc[0] + 3.6, hc[1] + 3.6)], "dusk", 1.0, curve=0.6)
    r.ell(hc[0] + 1.2, hc[1] + 0.6, 2.0, 2.4, "void", 1.1, flat=0)
    r.dot(hc[0] + 2.0, hc[1] + 0.2, "lilac", 2, 1.12)                                     # one cold glint in the dark
    r.polyline([(hc[0] - 3.6, hc[1] + 3.4), (hc[0] - 3.0, hc[1] - 1.6), (hc[0] - 4.6, hc[1] - 7.0)], "silver", 1.05, tones=[2, 3])
    r.dot(hc[0] - 5.0, hc[1] - 7.6, "lilac", 3, 1.2)                                        # a lilac bead on the tip
    # near arm holding the mirror
    sh_n = T(dx + 2.0, -12.4 + bob)
    mc = mirror or (dx + 6.0, -15.0 + bob)
    hand = (mc[0] - 0.4 + 6.0 * math.sin(math.radians(m_ang)) * 0.9, mc[1] + 7.0)
    e = ik(sh_n[0], sh_n[1], hand[0], hand[1], 3.8, 3.8, bend=-1)
    r.tube([sh_n, e, hand], [1.2, 1.0, 0.8], "robe", 3.0, bias=0.1)
    hand_mirror(r, mc[0], mc[1], m_ang, 3.2, face=face, flash=flash, crack=crack)
    r.ell(hand[0], hand[1], 0.9, 0.9, "bone", 3.3)
    if extra: extra(r)
    return r.resolve()


def witch_sheet(outdir):
    M = mirror_witch
    idle = [M(bob=[0, -0.3, -0.5, -0.3][i], sway=i * 1.57, mirror=(6.0, -15.0 + [0, -0.3, -0.5, -0.3][i]),
              m_ang=[0, 3, 6, 3][i], flash=1 if i == 2 else 0) for i in range(4)]
    run = [M(lean=8, sway=i * 1.05, hem=0.6 + 0.6 * math.sin(i), bob=-0.4 * abs(math.sin(i / 6 * math.tau)),
             mirror=(7.0, -14.0), m_ang=10) for i in range(6)]
    # Reflect (7): turn the glass to the light (0-1), her reflection opens its eyes (2), the bolt leaves the glass
    # (3 = release), the glass dims (4-5), back (6)
    ref = [M(mirror=(5.0, -17.0), m_ang=-10), M(mirror=(5.0, -18.0), m_ang=-20, face="cast", flash=2),
           M(lean=4, mirror=(7.0, -17.0), m_ang=10, face="cast", flash=1),
           M(lean=8, mirror=(9.0, -16.0), m_ang=30, face="cast", flash=1, extra=lambda r: [r.dot(14 + i, -17, "lilac", 3 + (i > 1), 6) for i in range(3)]),
           M(lean=4, mirror=(8.0, -15.0), m_ang=20), M(mirror=(7.0, -15.0), m_ang=10), M()]
    # Mirror (8): lift the mirror high (0-2), her reflection steps out of the glass (3-4: the pane stands), she lowers
    # the empty mirror (5-6), back (7)
    mir = [M(mirror=(5.0, -18.0), m_ang=-10), M(mirror=(4.0, -21.0), m_ang=-20, face="cast"),
           M(lean=-4, mirror=(4.0, -22.0), m_ang=-30, face="cast", flash=1),
           M(lean=6, mirror=(9.0, -19.0), m_ang=40, face=None, flash=2),
           M(lean=8, mirror=(9.0, -18.0), m_ang=50, face=None, flash=1),
           M(lean=4, mirror=(7.0, -15.0), m_ang=20, face=None), M(mirror=(6.0, -15.0), m_ang=6), M()]
    d0 = M(lean=-12, mirror=(4.0, -18.0), m_ang=-40, face="hurt", crack=True, hand2=(-6.0, -12.0))
    d1 = M(lean=-26, bob=3.0, mirror=(-2.0, -10.0), m_ang=-110, face="hurt", crack=True, hand2=(-6.0, -6.0), hem=1.5)
    d2 = remains(0, stain=8.0, glass=6, glass_mats=("glass", "silver"), stain_mat="robe",
                 extra=lambda r: hand_mirror(r, 2.0, -4.0, 80, 2.0, face="hurt", crack=True))
    corpse = remains(1, stain=9.0, glass=8, glass_mats=("glass", "silver"), stain_mat="robe",
                     extra=lambda r: hand_mirror(r, 3.0, -3.0, 90, 2.0, face=None, crack=True))
    knock = M(lean=-16, mirror=(3.0, -17.0), m_ang=-30, face="hurt", hand2=(-6.0, -11.0))
    anims = [("Idle", idle, [0.16, 0.12, 0.16, 0.12]), ("Run", run, [0.08] * 6),
             ("Reflect", ref, [0.12, 0.1, 0.1, 0.06, 0.1, 0.1, 0.12]),
             ("Mirror", mir, [0.1, 0.1, 0.1, 0.08, 0.1, 0.1, 0.1, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("UmbMirrorWitch", anims, outdir, scale=6)


# ================================================================== GLOAMCOIL: a serpent made of dusk
def gloam_path(rear=1.0, phase=0.0, head=None, flat=0.0, dx=0.0):
    """Spine points from the tail tip (back, on the floor) to the head. rear 0..1.4 lifts the neck; flat lays it low."""
    pts = []
    n = 14
    for i in range(n):
        t = i / (n - 1)
        x = dx - 14.0 + 24.0 * t
        wob = math.sin(phase + t * 6.0) * (2.4 * (1 - t)) * (1 - flat)
        y = -2.4 - wob * 0.8
        if t > 0.55:
            u = (t - 0.55) / 0.45
            y -= (14.0 * rear) * (u ** 1.4) * (1 - flat)
            x -= 4.0 * rear * u * u * (1 - flat)
        pts.append((x, y))
    if head:
        hx, hy = head
        k = 4
        for j in range(k):
            t = (j + 1) / k
            i = n - k + j
            pts[i] = (lerp(pts[n - k - 1][0], hx, t), lerp(pts[n - k - 1][1], hy, t))
    return pts


GLOAM_HEAD = {"calm": (False, 0.0), "open": (True, 1.0), "wide": (True, 2.0)}


def gloamcoil(rear=1.0, phase=0.0, head=None, jaw=0.0, flat=0.0, dx=0.0, eyes=True, smear=None, extra=None, dead=False,
              pools=None):
    r = Rig()
    pts = gloam_path(rear, phase, head, flat, dx)
    rad = [0.7, 1.2, 1.8, 2.4, 2.9, 3.2, 3.4, 3.4, 3.1, 2.8, 2.5, 2.3, 2.3, 2.4]
    # the body: dusk violet on top fading to black at the tail
    if flat < 0.5:
        # the tail end lies in a loop on the floor behind it
        lc = (dx - 8.0, -3.6)
        loop = [(lc[0] + 5.0 * math.cos(a), lc[1] + 2.6 * math.sin(a)) for a in [i / 10 * math.tau + phase * 0.2 for i in range(11)]]
        r.tube(loop, [2.0] * 11, "void", -1.0, bias=-0.05)
    r.tube(pts[:6], rad[:6], "void", 0.0, bias=0.05)
    r.tube(pts[5:], rad[5:], "dusk", 0.5, bias=0.12)
    # stars in the dusk of its scales, and the pale belly line along the near side
    for i in range(1, len(pts) - 1):
        x, y = pts[i]
        if i % 2 == 0: r.dot(x, y + rad[i] * 0.6, "bone", 1, 0.9)
        sx_, sy_ = x - 0.6 + (i % 3) * 0.6, y - rad[i] * (0.3 + 0.2 * (i % 2))
        r.dot(sx_, sy_, "lilac" if i % 3 else "sandl", 4 if i % 4 == 0 else 3, 0.9)
    # head: a wedge with two lilac star eyes
    hx, hy = pts[-1]
    ang = math.degrees(math.atan2(pts[-1][1] - pts[-3][1], pts[-1][0] - pts[-3][0]))
    T = Xf(ang, (hx, hy))
    r.poly([T(hx - 2.6, hy - 3.2), T(hx + 1.0, hy - 3.2), T(hx + 4.6, hy - 1.8 - jaw * 0.6), T(hx + 5.4, hy - 0.2 - jaw * 0.6),
            T(hx + 1.0, hy + 0.4), T(hx - 2.6, hy + 2.4)], "dusk", 1.5, bias=0.15, normal=(-0.2, -0.6, 1.0))
    r.poly([T(hx - 1.0, hy + 0.8), T(hx + 4.8, hy + 0.6 + jaw), T(hx + 3.8, hy + 2.0 + jaw), T(hx - 1.6, hy + 2.6)],
           "dusk", 1.45, bias=-0.2)
    r.polyline([T(hx - 2.4, hy - 3.0), T(hx + 1.0, hy - 3.0), T(hx + 4.4, hy - 1.8 - jaw * 0.6)], "lilac", 1.52, tones=[2, 3])
    if jaw > 0.5:
        r.dot(*T(hx + 3.0, hy + 0.2 + jaw * 0.5), "bone", 4, 1.6)
        r.dot(*T(hx + 1.6, hy + 0.4 + jaw * 0.6), "bone", 3, 1.6)
        r.dot(*T(hx + 2.4, hy + 0.5 + jaw * 0.5), "void", 0, 1.55)
    if eyes:
        ex, ey = T(hx + 0.6, hy - 1.2)
        twinkle(r, ex, ey, 2, mat="lilac", z=1.7)
        r.dot(*T(hx + 2.6, hy - 1.4), "lilac", 3, 1.7)
    else:
        r.line(*T(hx, hy - 1.2), *T(hx + 1.4, hy - 1.2), "void", 1.7, tone=1)
    if pools:
        for (x, k) in pools:
            r.ell(x, -0.5, 3.0 + k, 1.2, "dark", -2.0, flat=1)
    if smear:
        for (x0, x1, y) in smear:
            for i, x in enumerate(range(int(x0), int(x1))):
                r.dot(x, y, "lilac", 2 if i < 3 else 3, 6.0)
    if extra: extra(r)
    return r.resolve()


def gloam_sheet(outdir):
    G = gloamcoil
    idle = [G(phase=i * 1.57, rear=[1.0, 1.04, 1.08, 1.04][i]) for i in range(4)]
    run = [G(phase=i * 1.05 + 0.5, rear=0.8, dx=0.5 * math.sin(i)) for i in range(6)]
    # Strike (7): coil back (0-1), the head draws back with the jaw opening (2), LUNGE (3 = bite), hold (4), recoil (5-6)
    st = [G(rear=1.1, head=(2.0, -15.0)), G(rear=1.2, head=(0.0, -16.0), jaw=1.0), G(rear=1.2, head=(-1.0, -15.0), jaw=2.0),
          G(rear=0.9, head=(13.0, -10.0), jaw=2.0, smear=[(2, 9, -12)]), G(rear=0.9, head=(12.0, -9.0), jaw=0.0),
          G(rear=1.0, head=(7.0, -13.0)), G()]
    # Slither (8): flatten (0-1), the dash (2-5: a low streak), rise again (6-7)
    sl = [G(rear=0.6), G(rear=0.2, flat=0.6, head=(12.0, -3.0)),
          G(rear=0.0, flat=1.0, phase=0.0, head=(13.0, -2.5), smear=[(-14, -6, -3)]),
          G(rear=0.0, flat=1.0, phase=1.5, head=(13.0, -2.5), smear=[(-16, -8, -2)]),
          G(rear=0.0, flat=1.0, phase=3.0, head=(13.0, -2.5), smear=[(-16, -8, -3)]),
          G(rear=0.0, flat=1.0, phase=4.5, head=(13.0, -2.5)),
          G(rear=0.5, flat=0.4, head=(10.0, -7.0)), G(rear=0.9)]
    d0 = G(rear=1.2, head=(-2.0, -16.0), jaw=2.0, eyes=False)
    d1 = G(rear=0.4, flat=0.5, head=(8.0, -4.0), jaw=1.0, eyes=False)
    d2 = G(rear=0.0, flat=1.0, head=(10.0, -2.0), eyes=False, extra=lambda r: wisps(r, 0, -3, 1, n=7, spread=8, seed=40, mat="dusk"))
    corpse = remains(1, stain=11.0, glass=0, stain_mat="dusk",
                     extra=lambda r: (r.ell(6.0, -1.6, 2.4, 1.4, "dusk", 1.0), r.dot(6.5, -2.2, "lilac", 1, 1.1)))
    knock = G(rear=1.3, head=(-3.0, -16.0), jaw=1.0, eyes=False)
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.08] * 6),
             ("Strike", st, [0.12, 0.1, 0.1, 0.06, 0.1, 0.12, 0.12]),
             ("Slither", sl, [0.08, 0.08, 0.08, 0.08, 0.08, 0.08, 0.1, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("UmbGloamcoil", anims, outdir, scale=6)


# ================================================================== GLASSMOTH: leaded-glass wings, a lantern body
PANES = ["glass", "lwing", "glass", "sand", "lwing", "glass"]


def glass_wing(r, sx, sy, ang, ln, wid, z, mats, near=True, flap=1.0):
    """A wing of leaded glass: an outline polygon split into panes by lead cames (lines) from the root."""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    px, py = -uy, ux
    ln2, wid2 = ln * flap, wid
    tip = (sx + ux * ln2, sy + uy * ln2)
    outline = [(sx, sy), (sx + ux * ln2 * 0.45 + px * wid2 * 0.6, sy + uy * ln2 * 0.45 + py * wid2 * 0.6),
               (sx + ux * ln2 * 0.85 + px * wid2 * 0.5, sy + uy * ln2 * 0.85 + py * wid2 * 0.5), tip,
               (sx + ux * ln2 * 0.75 - px * wid2 * 0.45, sy + uy * ln2 * 0.75 - py * wid2 * 0.45),
               (sx + ux * ln2 * 0.3 - px * wid2 * 0.35, sy + uy * ln2 * 0.3 - py * wid2 * 0.35)]
    region = J.poly_px(outline)
    bias = 0.15 if near else -0.3
    p = r.part(False, z)
    for (x, y) in region:
        # which pane: by the angle from the root
        dx, dy = x - sx, y - sy
        along = dx * ux + dy * uy
        side = dx * px + dy * py
        k = int((side / max(0.1, wid2) + 1.0) * 1.6 + along / max(1.0, ln2) * 1.4) % len(mats)
        m = mats[k]
        lv = J.lam(-0.3 + side * 0.03, -0.5, 0.8) + bias + (0.25 if along < ln2 * 0.5 else 0.0)
        r.put(x, y, z, m, lv, p)
    # the lead cames: the rim and three ribs
    lead = r.part(True, z + 0.01)
    for a_, b_ in zip(outline, outline[1:] + outline[:1]):
        for (x, y) in J.line_px(int(round(a_[0])), int(round(a_[1])), int(round(b_[0])), int(round(b_[1]))):
            r.put(x, y, z + 0.01, "lead", 0.5, lead, 2 if near else 1)
    for k in (1, 2, 4):
        q = outline[k]
        for (x, y) in J.line_px(int(round(sx)), int(round(sy)), int(round(q[0])), int(round(q[1]))):
            r.put(x, y, z + 0.01, "lead", 0.5, lead, 1)
    return tip


def lantern_body(r, cx, cy, z, glow=3, tilt=0.0):
    T = Xf(tilt, (cx, cy))
    r.ell(*T(cx, cy), 2.0, 3.6, "brass", z, ang=tilt)
    r.ell(*T(cx, cy + 0.4), 1.2, 2.4, "cyanl" if glow else "glass", z + 0.01, flat=glow if glow else None)
    r.dot(*T(cx, cy - 0.4), "white", 4, z + 0.02) if glow >= 3 else None
    r.line(*T(cx, cy - 4.4), *T(cx, cy + 4.6), "brass", z + 0.03, tone=1)
    # head with feathered antennae
    hx, hy = T(cx + 0.6, cy - 4.8)
    r.ell(hx, hy, 1.6, 1.4, "lead", z + 0.04)
    r.dot(hx + 0.8, hy - 0.2, "lilac", 4, z + 0.05)
    for s in (-1, 1):
        r.polyline([(hx, hy - 1), (hx + 1.0 * s + 0.5, hy - 3.4), (hx + 2.4 * s + 1, hy - 4.6)], "brass", z + 0.02, tones=[2, 3])


def glassmoth(alt=2.0, flap=0.0, tilt=0.0, glow=3, extra=None, dust_k=None, fold=1.0, dead=False):
    """Hovering moth: two forewings and two hindwings of leaded glass round a brass lantern. flap -1..1."""
    r = Rig()
    cx, cy = 0.0, -alt - 8.0
    up = flap * 35.0
    # far wings (left, behind)
    glass_wing(r, cx - 0.8, cy - 1.0, -150 + up, 12.0 * fold, 8.0, -2.0, PANES, near=False)
    glass_wing(r, cx - 0.6, cy + 1.6, 155 - up * 0.5, 9.0 * fold, 6.0, -2.1, PANES[::-1], near=False)
    lantern_body(r, cx, cy, 0.0, glow=glow, tilt=tilt)
    glass_wing(r, cx + 0.8, cy - 1.0, -30 - up, 12.0 * fold, 8.0, 2.0, PANES, near=True)
    glass_wing(r, cx + 0.6, cy + 1.6, 25 + up * 0.5, 9.0 * fold, 6.0, 1.9, PANES[::-1], near=True)
    if dust_k is not None:
        rnd = random.Random(7 + dust_k)
        for i in range(10):
            x = cx + 6 + rnd.random() * (8 + 5 * dust_k); y = cy - 4 + rnd.random() * 10
            r.dot(x, y, "white" if i % 3 == 0 else "lilac", 4 if i % 2 else 3, 6.0)
    if not dead: floor_shadow(r, 0.0, 6.0)
    if extra: extra(r)
    return r.resolve()


def glassmoth_sheet(outdir):
    G = glassmoth
    idle = [G(alt=[2.0, 2.3, 2.6, 2.3][i], flap=[0.0, 0.3, 0.55, 0.2][i], glow=[3, 3, 4, 3][i]) for i in range(4)]
    run = [G(alt=6.0 + 0.5 * math.sin(i), flap=[1.0, 0.4, -0.4, -1.0, -0.4, 0.4][i], tilt=12) for i in range(6)]
    # Scales (6): wings rise (0-1), downbeat throws two scales (2 = release), rise (3), settle (4-5)
    sc = [G(flap=0.8), G(flap=1.2, glow=4), G(flap=-1.0, tilt=10, extra=lambda r: [r.dot(10 + i, -14 - i * 0.5, "glass", 4, 6) for i in range(3)]),
          G(flap=-0.6, tilt=6), G(flap=0.2), G(flap=0.5)]
    # Dust (7): wings fold high (0-1), the lantern flares (2), the great fanning beat (3 = release, glitter), (4-5), settle
    du = [G(flap=1.0), G(flap=1.4, fold=0.9, glow=4), G(flap=1.4, glow=4, extra=lambda r: twinkle(r, 0, -16, 1)),
          G(flap=-1.2, tilt=14, dust_k=0), G(flap=-0.8, tilt=10, dust_k=1), G(flap=0.0, dust_k=2), G(flap=0.4)]
    d0 = G(flap=1.4, tilt=-20, glow=1)
    d1 = G(alt=3.0, flap=-1.0, tilt=-40, glow=0, fold=0.8, extra=lambda r: shards(r, 0, -10, 0, n=6, seed=12, mats=("glass", "sand", "lwing")))
    d2 = remains(0, stain=7.0, glass=8, glass_mats=("glass", "sand", "lwing"), stain_mat="lead",
                 extra=lambda r: lantern_body(r, 0.0, -2.5, 2.0, glow=0, tilt=80))
    corpse = remains(1, stain=8.0, glass=10, glass_mats=("glass", "sand", "lwing"), stain_mat="lead",
                     extra=lambda r: lantern_body(r, 1.0, -2.0, 2.0, glow=0, tilt=90))
    knock = G(flap=1.2, tilt=-26, glow=2)
    anims = [("Idle", idle, [0.1, 0.08, 0.1, 0.08]), ("Run", run, [0.06] * 6),
             ("Scales", sc, [0.12, 0.1, 0.06, 0.1, 0.1, 0.12]),
             ("Dust", du, [0.1, 0.1, 0.12, 0.06, 0.1, 0.1, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("UmbGlassmoth", anims, outdir, scale=6)


# ================================================================== HOURGLASS: a living hourglass on spindle legs
def hourglass_body(r, cx, cy, z, top=0.6, bot=0.4, ang=0.0, eye="open", stream=True, flip_k=0.0, crack=False):
    """Frame centre (cx, cy): two glass bulbs (sand `top` / `bot` full, 0..1), black posts with brass caps, an eye in the
    waist. ang turns the whole glass (the Rewind flip)."""
    T = Xf(ang, (cx, cy))
    hb = 6.4
    # bulbs (glass), sand inside
    for s, fill in ((-1, top), (1, bot)):
        bc = T(cx, cy + s * 3.8)
        r.ell(bc[0], bc[1], 4.8, 3.8, "glass", z, bias=0.15, ang=ang)
        if fill > 0.05:
            # sand settles at the bottom of each bulb (bottom in screen space once turned)
            lvl = bc[1] + 3.2 - fill * 6.4
            for (x, y) in J.poly_px([(bc[0] - 3.4, bc[1] - 3.4), (bc[0] + 3.4, bc[1] - 3.4), (bc[0] + 3.4, bc[1] + 3.4), (bc[0] - 3.4, bc[1] + 3.4)]):
                if (x - bc[0]) ** 2 / 17.0 + (y - bc[1]) ** 2 / 10.0 <= 1.0 and y >= lvl:
                    r.put(x, y, z + 0.01, "sand", J.lam(-0.3, -0.6, 0.7) + (0.3 if y < lvl + 1.2 else 0.0), r.part(False, z + 0.01))
        r.dot(bc[0] - 1.8, bc[1] - 1.6, "white", 4, z + 0.02)
    # the waist with an eye
    wx, wy = T(cx, cy)
    r.ell(wx, wy, 1.8, 1.4, "bone", z + 0.03)
    if eye == "open":
        r.dot(wx + 0.4, wy, "lilac", 2, z + 0.04); r.dot(wx - 0.4, wy, "void", 0, z + 0.04)
    elif eye == "wide":
        r.dot(wx, wy, "lilac", 3, z + 0.04); r.dot(wx + 1, wy, "lilac", 2, z + 0.04)
    else:
        r.line(wx - 1, wy, wx + 1, wy, "void", z + 0.04, tone=1)
    if stream and top > 0.05 and abs(ang) < 1:
        r.line(wx, wy + 1.4, wx, wy + 1.4 + (6.0 - bot * 5.0), "sandl", z + 0.035, tone=3)
    # frame: two posts and two caps
    for s in (-1, 1):
        p0, p1 = T(cx + s * 4.2, cy - hb - 1.0), T(cx + s * 4.2, cy + hb + 1.0)
        r.tube([p0, p1], [0.7, 0.7], "void", z + 0.05 if s > 0 else z - 0.05, bias=0.2)
    for s in (-1, 1):
        cc = T(cx, cy + s * (hb + 1.4))
        r.poly([T(cx - 6.4, cy + s * (hb + 0.6)), T(cx + 6.4, cy + s * (hb + 0.6)), T(cx + 6.0, cy + s * (hb + 2.4)),
                T(cx - 6.0, cy + s * (hb + 2.4))], "brass", z + 0.06, normal=(-0.2, -0.6 if s < 0 else 0.3, 1.0))
        r.dot(*T(cx + 6.6, cy + s * (hb + 1.4)), "lilac", 3, z + 0.07)
    if crack:
        r.polyline([T(cx - 2, cy - 6), T(cx, cy - 4), T(cx - 1, cy - 2)], "white", z + 0.07, tone=3)


def hourglass(alt=0.0, gait=None, top=0.6, bot=0.4, ang=0.0, eye="open", lean=0.0, legs=1.0, extra=None, crack=False, dx=0.0,
              spit=None):
    r = SRig(1.05)
    cy = -15.0 - alt
    cx = dx
    # four spindle legs from the bottom cap
    for i, (fx, far) in enumerate(((-8.0, True), (-3.4, False), (3.6, True), (8.2, False))):
        hx, hy = cx + fx * 0.5, cy + 7.6
        x = cx + fx * legs
        fy = 0.0
        if gait is not None:
            ph = gait + i * math.pi / 2
            x += 1.2 * math.cos(ph); fy = -max(0.0, 1.2 * math.sin(ph))
        kx, ky = (hx + x) / 2 + (1.6 if fx > 0 else -1.6), cy + 9.6
        z = -1.0 if far else 1.0
        r.tube([(hx, hy), (kx, ky), (x, fy - 0.4)], [0.8, 0.6, 0.4], "void", z, bias=-0.25 if far else 0.15)
        r.dot(kx, ky, "brass", 2, z + 0.01)
        r.dot(x, fy, "brass", 3, z + 0.01)
    hourglass_body(r, cx, cy, 0.0, top, bot, ang + lean, eye, crack=crack)
    if spit:
        for i in range(spit):
            r.dot(cx + 3 + i * 1.5, cy - 0.5, "sandl", 3 + (i == spit - 1), 6.0)
    if extra: extra(r)
    return r.resolve()


def hourglass_sheet(outdir):
    H = hourglass
    idle = [H(top=0.62 - 0.02 * i, bot=0.38 + 0.02 * i, alt=[0, 0.3, 0.5, 0.3][i]) for i in range(4)]
    run = [H(gait=i / 6 * math.tau, lean=8, alt=0.4 * abs(math.sin(i)), top=0.6, bot=0.4) for i in range(6)]
    # Shard (6): the glass leans back (0), the eye narrows (1), it spits a fused shard from the waist (2 = release), (3-5)
    sh = [H(lean=-10, eye="wide"), H(lean=-14, eye="shut"), H(lean=12, eye="wide", spit=3), H(lean=8), H(lean=3), H()]
    # Rewind (8): crouch (0), flip over (1-4, the sand runs the wrong way), land upside up (5), the eye opens (6-7)
    rw = [H(legs=1.3, alt=-1.0)] + [H(alt=2.0 + 2 * math.sin(k / 3 * math.pi), ang=45 * (k + 1), top=0.6 - 0.1 * k, bot=0.4 + 0.1 * k,
                                      eye="shut", legs=0.7) for k in range(4)] + \
         [H(legs=1.3, alt=-1.0, top=0.2, bot=0.8, eye="shut"), H(top=0.25, bot=0.75, eye="wide",
                                                                 extra=lambda r: twinkle(r, 0, -24, 1, mat="sandl")),
          H(top=0.3, bot=0.7)]
    # Snap (4): the snap back (a sudden half turn and a flash)
    sn = [H(ang=-60, eye="wide", alt=1.0, extra=lambda r: twinkle(r, 0, -14, 1, mat="sandl")), H(ang=-20, eye="wide", alt=1.0),
          H(legs=1.2, alt=-0.5), H()]
    d0 = H(lean=-18, eye="shut", crack=True)
    d1 = H(lean=-60, eye="shut", crack=True, legs=1.6, alt=-3.0)
    d2 = remains(0, stain=7.0, glass=8, glass_mats=("glass", "sand"), stain_mat="sand",
                 extra=lambda r: hourglass_body(r, 1.0, -5.0, 2.0, 0.3, 0.3, 90, "shut", stream=False, crack=True))
    corpse = remains(1, stain=9.0, glass=10, glass_mats=("glass", "sand"), stain_mat="sand",
                     extra=lambda r: hourglass_body(r, 1.0, -4.6, 2.0, 0.0, 0.0, 92, "shut", stream=False, crack=True))
    knock = H(lean=-22, eye="shut")
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.07] * 6),
             ("Shard", sh, [0.12, 0.1, 0.06, 0.1, 0.1, 0.12]),
             ("Rewind", rw, [0.1, 0.06, 0.06, 0.06, 0.06, 0.1, 0.12, 0.12]),
             ("Snap", sn, [0.06, 0.08, 0.1, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("UmbHourglass", anims, outdir, scale=6)


JOBS = [("UmbTwinned", twinned_sheet), ("UmbNailshade", nailshade_sheet), ("UmbMirrorWitch", witch_sheet),
        ("UmbGloamcoil", gloam_sheet), ("UmbGlassmoth", glassmoth_sheet), ("UmbHourglass", hourglass_sheet)]
