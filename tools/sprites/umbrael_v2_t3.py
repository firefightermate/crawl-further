"""Umbrael tier 3 sheets: The Hollow King, The Sundered, Glass Seraph, Bristleback, The Unblinking,
Glass Widow, Eclipse Wyrm, The Undertow, Argus Moth, Glitterswarm, The Pendulum, Sand Wraith. Drawn with the renderer
and parts in umbrael_v2_rigs.py; feet at y=0, facing right, y up negative."""
import math, random
from umbrael_v2_rigs import (rimlight, SRig, Rig, Xf, chain, ik, lerp, sheet, tail_anims, J, mask_stamp, MASK_LEG, smoke_tail, wisps,
                             shards, claw_hand, arc_smear, floor_shadow, remains, twinkle, dust)
from umbrael_v2_t2 import glass_wing, hourglass_body


def ellipse_ring(r, cx, cy, rx, ry, mat, tone, z, n=48, skip=None, w=1):
    for i in range(n):
        a = i / n * math.tau
        if skip and skip(a): continue
        for k in range(w):
            r.dot(cx + (rx - k) * math.cos(a), cy + (ry - k) * math.sin(a), mat, tone, z)


def armour_leg(r, hip, foot, z, mat="tarn", bias=0.0, bend=-1, l1=5.6, l2=5.4, w=1.6):
    kn = ik(hip[0], hip[1], foot[0], foot[1] - 1.0, l1, l2, bend=bend)
    r.tube([hip, kn], [w + 0.2, w], mat, z, bias=bias - 0.1)
    r.tube([kn, (foot[0], foot[1] - 1.0)], [w, w - 0.2], mat, z + 0.01, bias=bias)
    r.ell(kn[0] + 0.4, kn[1], w * 0.8, w * 0.7, mat, z + 0.02, bias=bias + 0.2)                  # knee cop
    r.poly([(foot[0] - 1.8, foot[1] - 2.0), (foot[0] + 2.8, foot[1] - 1.2), (foot[0] + 2.8, foot[1]), (foot[0] - 1.8, foot[1])],
           mat, z + 0.03, bias=bias + 0.1)
    return kn


# ================================================================== THE HOLLOW KING
HELM = {
    "calm": """
.aSSSs.
aSSSSSs
SSSSSSs
SmmmmmS
SmEmEmS
SSmmmSs
.sSSSs.
""",
    "hurt": """
.aSSSs.
aSSmSSs
SSSmSSs
SmmmmmS
SmmmmmS
SSmmmSs
.sSSSs.
""",
}
KING_LEG = dict(MASK_LEG, S=("tarn", 3), s=("tarn", 2), a=("tarn", 1))


def crown(r, cx, cy, z, tilt=0.0, glow=True, scale=1.0):
    T = Xf(tilt, (cx, cy))
    w = 4.2 * scale
    r.poly([T(cx - w, cy + 1.2), T(cx + w, cy + 1.2), T(cx + w, cy - 0.6), T(cx - w, cy - 0.6)], "tarn", z, bias=0.2)
    for k, dx in enumerate((-w, -w / 2, 0.0, w / 2, w)):
        h = 2.6 if k in (0, 4) else 3.6 if k == 2 else 2.0
        r.poly([T(cx + dx - 0.8, cy - 0.4), T(cx + dx + 0.8, cy - 0.4), T(cx + dx, cy - 0.4 - h * scale)], "tarn", z + 0.01, bias=0.3)
    if glow:
        r.dot(*T(cx, cy + 0.2), "lilac", 4, z + 0.02)
        r.dot(*T(cx - w / 2 - 0.5, cy + 0.3), "lilac", 2, z + 0.02); r.dot(*T(cx + w / 2 + 0.5, cy + 0.3), "lilac", 2, z + 0.02)


def greatsword(r, hx, hy, ang, z, ln=19.0, glow=True):
    """A black greatsword from the grip at (hx, hy) along ang (deg, y down): void blade with a lilac edge, a tarnished
    silver cross-guard and pommel."""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    px, py = -uy, ux
    g = (hx + ux * 1.6, hy + uy * 1.6)
    tip = (g[0] + ux * ln, g[1] + uy * ln)
    r.poly([(g[0] + px * 1.6, g[1] + py * 1.6), (tip[0] + px * 0.4, tip[1] + py * 0.4), tip, (tip[0] - px * 0.6, tip[1] - py * 0.6),
            (g[0] - px * 1.4, g[1] - py * 1.4)], "void", z, normal=(-0.3 * px - 0.2, -0.3 * py - 0.4, 1.0))
    r.line(g[0] + px * 1.2, g[1] + py * 1.2, tip[0], tip[1], "lilac", z + 0.01, tone=3 if glow else 1)
    r.line(g[0] + px * 2.8, g[1] + py * 2.8, g[0] - px * 2.8, g[1] - py * 2.8, "tarn", z + 0.02, tone=3)
    r.line(hx - ux * 2.0, hy - uy * 2.0, g[0], g[1], "robe", z + 0.015, tone=2)
    r.dot(hx - ux * 2.6, hy - uy * 2.6, "tarn", 4, z + 0.03)
    return tip


def hollow_king(lean=0.0, bob=0.0, feet=((-3.5, 0.0), (3.5, 0.0)), hand=None, sword=None, crowned=True, crown_at=None,
                crown_tilt=0.0, face="calm", cape=0.0, smear=None, extra=None, hand2=None, dx=0.0, knee=-1):
    """hand: the sword hand (both hands on the grip unless hand2 is given). sword: blade angle (deg)."""
    r = SRig(1.03)
    hip = (dx, -14.0 + bob)
    T = Xf(lean, hip)
    # cape behind
    cb = T(hip[0] - 0.5, hip[1] - 10.0)
    r.poly([(cb[0] - 3.0, cb[1]), (cb[0] + 4.0, cb[1]), (hip[0] + 1.0 - cape, -0.6), (hip[0] - 8.0 - cape * 2.0, -0.8 - cape),
            (hip[0] - 7.0 - cape, hip[1] - 6.0)], "dusk", -2.0, bias=-0.1, normal=(-0.3, -0.2, 1.0))
    r.polyline([(hip[0] - 8.0 - cape * 2.0, -0.8 - cape), (hip[0] + 1.0 - cape, -0.6)], "lilac", -1.95, tone=2)
    for k, f in enumerate(feet):
        hp = (hip[0] + (-1.2 if k == 0 else 1.4), hip[1] + 0.6)
        armour_leg(r, hp, f, -1.0 if k == 0 else 1.0, bias=-0.3 if k == 0 else 0.0, bend=knee)
    # tabard over a mail skirt
    r.poly([T(hip[0] - 3.4, hip[1] - 1.0), T(hip[0] + 3.6, hip[1] - 1.0), T(hip[0] + 3.0, hip[1] + 4.0), T(hip[0] - 3.0, hip[1] + 4.0)],
           "tarn", 0.0, bias=-0.25)
    r.poly([T(hip[0] - 1.6, hip[1] - 9.0), T(hip[0] + 2.0, hip[1] - 9.0), T(hip[0] + 1.6, hip[1] + 5.0), T(hip[0] - 1.2, hip[1] + 5.0)],
           "void", 0.4, curve=0.4)
    r.line(*T(hip[0] + 0.2, hip[1] - 8.0), *T(hip[0] + 0.2, hip[1] + 4.6), "lilac", 0.45, tone=2)
    # breastplate
    r.ell(*T(hip[0] + 0.4, hip[1] - 6.4), 5.6, 5.4, "tarn", 0.2, bias=0.1, ang=lean)
    r.poly([T(hip[0] - 5.0, hip[1] + 0.6), T(hip[0] + 5.0, hip[1] + 0.6), T(hip[0] + 5.4, hip[1] + 6.0), T(hip[0] - 5.4, hip[1] + 6.0)],
           "tarn", -0.2, bias=-0.35)                                                                # a mail skirt
    r.poly([T(hip[0] - 1.6, hip[1] - 9.0), T(hip[0] + 2.0, hip[1] - 9.0), T(hip[0] + 1.6, hip[1] - 3.0), T(hip[0] - 1.2, hip[1] - 3.0)],
           "void", 0.4, curve=0.4)
    r.line(*T(hip[0] + 0.2, hip[1] - 8.4), *T(hip[0] + 0.2, hip[1] - 3.4), "lilac", 0.45, tone=2)
    r.line(*T(hip[0] - 3.8, hip[1] - 1.4), *T(hip[0] + 4.0, hip[1] - 1.4), "robe", 0.5, tone=1)       # sword belt
    sh_n, sh_f = T(hip[0] + 4.6, hip[1] - 9.6), T(hip[0] - 4.0, hip[1] - 9.8)
    h1 = hand or T(hip[0] + 4.6, hip[1] - 3.0)
    h2 = hand2 or (h1[0] - 1.6, h1[1] - 0.4)
    e = ik(sh_f[0], sh_f[1], h2[0], h2[1], 4.4, 4.2, bend=1)
    r.tube([sh_f, e, h2], [1.5, 1.3, 1.2], "tarn", -0.5, bias=-0.3)
    r.ell(sh_f[0], sh_f[1], 3.2, 2.2, "tarn", -0.4, bias=-0.1)
    # the sword (between the arms)
    sa = 90.0 if sword is None else sword
    tip = greatsword(r, h1[0], h1[1], sa, 3.5 if 0 < sa < 180 else 2.0)
    # helm on a gorget, the crown above it
    hd = T(hip[0] + 1.0, hip[1] - 11.4)
    r.ell(hd[0], hd[1] + 1.2, 2.6, 1.2, "tarn", 2.5, bias=-0.2)
    r.stamp(HELM[face], hd[0] + 0.5, hd[1] + 1.0, 2.6, KING_LEG, pivot=(3, 7), lit=False)
    if crowned:
        cx, cy = crown_at or (hd[0] + 0.5, hd[1] - 9.4 - 0.6 * math.sin(bob * 3.0))
        crown(r, cx, cy, 2.8, tilt=crown_tilt)
        r.dot(cx - 2, cy + 2.4, "lilac", 2, 2.7); r.dot(cx + 2, cy + 2.8, "lilac", 1, 2.7)
    # near arm and pauldron on top
    e = ik(sh_n[0], sh_n[1], h1[0], h1[1], 4.4, 4.2, bend=-1)
    r.tube([sh_n, e, h1], [1.6, 1.4, 1.3], "tarn", 3.0, bias=0.1)
    r.ell(sh_n[0], sh_n[1] - 0.4, 3.6, 2.4, "tarn", 3.1, bias=0.2)
    r.line(sh_n[0] - 3.0, sh_n[1] + 1.4, sh_n[0] + 3.0, sh_n[1] + 1.4, "tarn", 3.12, tone=1)
    r.dot(sh_n[0] + 0.5, sh_n[1] - 1.6, "lilac", 3, 3.15)
    r.ell(h1[0], h1[1], 1.4, 1.3, "tarn", 3.2, bias=0.1)
    if smear:
        for (cx, cy, R, a0, a1) in smear:
            arc_smear(r, cx, cy, R, a0, a1, mat="lilac", width=3, z=6.0)
    if extra: extra(r)
    return r.resolve()


def king_sheet(outdir):
    K = hollow_king
    anims = []
    for tag, crowned in (("", True), ("Bare", False)):
        idle = [K(bob=[0, -0.3, -0.5, -0.3][i], crowned=crowned, hand=(5.0, -18.0 + [0, -0.3, -0.5, -0.3][i]), sword=66,
                  cape=[0, 0.3, 0.6, 0.3][i]) for i in range(4)]
        run = []
        for i in range(6):
            ph = i / 6 * math.tau
            run.append(K(lean=8, bob=-0.6 * abs(math.sin(ph)), crowned=crowned, hand=(6.0, -11.0), sword=150, cape=1.2 + 0.4 * math.sin(ph),
                         feet=((-3.4 * math.cos(ph), -max(0, 2.0 * math.sin(ph))), (3.4 * math.cos(ph), -max(0, -2.0 * math.sin(ph))))))
        # Cleave (9): raise the sword overhead (0-2), hold (3), the cleave comes down (4 = HIT, the eclipse arc), bites
        # the floor (5), drag it back (6-8)
        cl = [K(crowned=crowned, hand=(3.0, -16.0), sword=-80, lean=-4),
              K(crowned=crowned, hand=(0.0, -22.0), sword=-130, lean=-10, cape=0.4),
              K(crowned=crowned, hand=(-1.0, -24.0), sword=-160, lean=-14, cape=0.6),
              K(crowned=crowned, hand=(-1.0, -24.0), sword=-165, lean=-14, cape=0.6, face="calm"),
              K(crowned=crowned, hand=(9.0, -16.0), sword=-10, lean=12, feet=((-4.5, 0.0), (5.0, 0.0)), cape=1.4, dx=1.0,
                smear=[(2, -20, 15, -150, -10)]),
              K(crowned=crowned, hand=(9.0, -8.0), sword=60, lean=16, feet=((-4.5, 0.0), (5.0, 0.0)), cape=1.6, dx=1.0,
                smear=[(2, -20, 15, -60, 40)]),
              K(crowned=crowned, hand=(7.0, -7.0), sword=80, lean=10, feet=((-4.0, 0.0), (4.5, 0.0)), cape=1.0),
              K(crowned=crowned, hand=(5.0, -12.0), sword=75, lean=4), K(crowned=crowned, hand=(5.0, -18.0), sword=66)]
        anims += [("Idle" + tag, idle, [0.16, 0.14, 0.16, 0.14]), ("Run" + tag, run, [0.08] * 6),
                  ("Cleave" + tag, cl, [0.12, 0.1, 0.1, 0.14, 0.05, 0.08, 0.1, 0.12, 0.12])]
    # Throw (8): he lifts the crown off its air (0-2), draws it back (3), hurls it (4 = release), follow (5-7)
    th = [K(hand=(4.4, -9.0), sword=96, hand2=(1.0, -27.0), crown_at=(1.0, -29.0)),
          K(hand=(4.4, -9.0), sword=96, hand2=(-1.0, -27.0), crown_at=(-1.0, -29.0), crown_tilt=-10, lean=-4),
          K(hand=(4.4, -9.0), sword=96, hand2=(-4.0, -22.0), crown_at=(-4.5, -23.5), crown_tilt=-30, lean=-10),
          K(hand=(4.4, -9.0), sword=96, hand2=(-6.0, -20.0), crown_at=(-7.0, -21.0), crown_tilt=-50, lean=-14, cape=0.6),
          K(hand=(5.0, -9.0), sword=100, hand2=(10.0, -18.0), crowned=False, lean=12, cape=1.4, dx=1.0,
            extra=lambda r: (crown(r, 15.0, -19.0, 6.0, tilt=40), arc_smear(r, 2, -18, 12, -170, -40, width=1))),
          K(hand=(5.0, -9.0), sword=100, hand2=(9.0, -12.0), crowned=False, lean=8, cape=1.0),
          K(hand=(4.4, -9.0), sword=96, hand2=(5.0, -10.0), crowned=False, lean=3), K(hand=(4.4, -9.0), sword=96, crowned=False)]
    anims.append(("Throw", th, [0.12, 0.1, 0.1, 0.14, 0.06, 0.1, 0.12, 0.14]))
    d0 = K(lean=-10, face="hurt", hand=(2.0, -14.0), sword=40, crown_at=(0.0, -36.0), crown_tilt=-20)
    d1 = K(lean=-22, bob=4.0, face="hurt", hand=(4.0, -6.0), sword=20, crown_at=(-6.0, -30.0), crown_tilt=-60, knee=1,
           feet=((-4.0, 0.0), (3.0, 0.0)))

    def fallen(r, k):
        greatsword(r, -12.0, -1.5, 0, 1.0, glow=False)
        r.ell(-2.0, -2.4, 6.0, 2.4, "tarn", 1.2, bias=-0.1)
        r.stamp(HELM["hurt"], 5.0, -0.5, 2.0, KING_LEG, pivot=(3, 7))
        crown(r, -9.0 + k * 2, -2.0, 2.2, tilt=70 if k else 30, glow=False)
    d2 = remains(0, stain=12.0, glass=0, stain_mat="dusk", extra=lambda r: fallen(r, 0))
    corpse = remains(1, stain=13.0, glass=0, stain_mat="dusk", extra=lambda r: fallen(r, 1))
    knock = K(lean=-14, face="hurt", hand=(2.0, -12.0), sword=50, crown_at=(-1.0, -33.0), crown_tilt=-15)
    anims += tail_anims(anims[0][1][0], [d0, d1, d2, corpse], [0.1, 0.14, 0.14, 0.4], knock)
    return sheet("UmbHollowKing", anims, outdir, scale=5)


# ================================================================== THE SUNDERED: one figure torn in two
SUND_HEAD = {
    "calm": """
..aWWw
.aWWWw
.WWkew
.WWWWw
..WkWw
...aw.
""",
    "snarl": """
..aWWw
.aWWWw
.WWkEw
.WwWWw
..mmmw
...aw.
""",
    "hurt": """
..aWWw
.aWkWw
.WmkWw
.WkWWw
..WWWw
...aw.
""",
}
PALE_LEG = dict(MASK_LEG, a=("void", 2), w=("void", 3), W=("void", 4), k=("pale", 3), e=("cyanl", 3), E=("cyanl", 4),
                m=("pale", 2))


def sabre(r, hx, hy, ang, z, mat="silver", ln=12.0):
    a = math.radians(ang)
    pts = [(hx, hy)]
    x, y = hx, hy
    for i in range(4):
        x += ln / 4 * math.cos(a + i * 0.08); y += ln / 4 * math.sin(a + i * 0.08); pts.append((x, y))
    r.tube(pts[1:], [1.1, 1.0, 0.7, 0.3], mat, z, bias=0.25)
    px, py = -math.sin(a), math.cos(a)
    r.line(hx + px * 1.6, hy + py * 1.6, hx - px * 1.6, hy - py * 1.6, "tarn", z + 0.01, tone=3)
    return pts[-1]


def sundered(lean=0.0, bob=0.0, feet=((-3.0, 0.0), (3.5, 0.0)), hand=None, hand2=None, ang1=-20.0, ang2=20.0, face="calm",
             pale=False, smear=None, extra=None, dx=0.0, crack=1.0, knee=-1, glow=0):
    """The dark half (pale=False): a lean void swordsman whose back half is torn away along a jagged seam of white light.
    pale=True draws the other half (the follower) in pale glass, torn the other way."""
    r = SRig(1.18)
    body = "pale" if pale else "void"
    hip = (dx, -12.5 + bob)
    T = Xf(lean, hip)
    torn = (lambda x, y: x >= hip[0] - 1.6 + 1.2 * math.sin(y * 1.3)) if not pale else (lambda x, y: x <= hip[0] + 1.6 + 1.2 * math.sin(y * 1.3))
    for k, f in enumerate(feet):
        hp = (hip[0] + (-1.0 if k == 0 else 1.2), hip[1] + 0.6)
        kn = ik(hp[0], hp[1], f[0], f[1] - 0.8, 6.2, 6.0, bend=knee)
        r.tube([hp, kn, (f[0], f[1] - 0.8)], [1.9, 1.5, 1.1], body, -1.0 if k == 0 else 1.0, bias=-0.25 if k == 0 else 0.05)
        r.poly([(f[0] - 1.4, f[1] - 1.6), (f[0] + 2.4, f[1] - 1.0), (f[0] + 2.4, f[1]), (f[0] - 1.4, f[1])], body, 1.05)
    # torso, clipped along the tear
    r.ell(*T(hip[0] + 0.8, hip[1] - 5.6), 6.2, 6.8, body, 0.0, bias=0.1, ang=lean, clip=torn)
    r.ell(*T(hip[0] + 1.6, hip[1] - 9.6), 4.8, 2.6, body, 0.05, bias=0.25, ang=lean, clip=torn)
    # a tattered half-cloak over the near shoulder
    r.poly([T(hip[0] + 0.0, hip[1] - 11.0), T(hip[0] + 5.6, hip[1] - 10.0), T(hip[0] + 6.0, hip[1] - 2.0), T(hip[0] + 4.0, hip[1] - 3.6),
            T(hip[0] + 2.6, hip[1] - 1.0), T(hip[0] + 0.6, hip[1] - 4.0)], "dusk" if not pale else "glass", 0.3, bias=-0.05, curve=0.4)
    if not pale:
        r.line(*T(hip[0] + 2.0, hip[1] - 9.0), *T(hip[0] + 1.0, hip[1] - 1.0), "silver", 0.1, tone=1)       # a sash
    # the seam of light down the tear
    if crack:
        for y in range(int(hip[1] - 12), int(hip[1] + 1)):
            x = hip[0] - 1.6 + 1.2 * math.sin(y * 1.3) + (0 if not pale else 3.2)
            xx, yy = T(x, y)
            r.dot(xx, yy, "white", 4 if (y % 3 == 0) else 3, 0.6)
            r.dot(xx - 1 if not pale else xx + 1, yy, "lilac", 3 if crack > 1 else 2, 0.55)
            if crack > 1 and y % 3 == 1: r.dot(xx - 2 if not pale else xx + 2, yy, "lilac", 2, 0.5)
    # head: a long mask, torn too
    hd = T(hip[0] + 1.6, hip[1] - 11.6)
    r.stamp(SUND_HEAD[face], hd[0], hd[1], 2.0, MASK_LEG if not pale else PALE_LEG, pivot=(3, 5), flip=pale)
    sh_n, sh_f = T(hip[0] + 3.4, hip[1] - 9.4), T(hip[0] + 0.0, hip[1] - 9.8)
    h2 = hand2 or T(hip[0] + 5.0, hip[1] - 4.0)
    e = ik(sh_f[0], sh_f[1], h2[0], h2[1], 4.0, 4.0, bend=1)
    r.tube([sh_f, e, h2], [1.2, 1.0, 0.9], body, -0.5, bias=-0.3)
    sabre(r, h2[0], h2[1], ang2, -0.45, mat="pale" if pale else "silver")
    h1 = hand or T(hip[0] + 6.0, hip[1] - 6.0)
    e = ik(sh_n[0], sh_n[1], h1[0], h1[1], 4.0, 4.0, bend=-1)
    r.tube([sh_n, e, h1], [1.3, 1.1, 1.0], body, 3.0, bias=0.1)
    sabre(r, h1[0], h1[1], ang1, 3.1, mat="pale" if pale else "silver")
    if glow:
        twinkle(r, hip[0] - 1.0, hip[1] - 6.0, glow)
    if smear:
        for (cx, cy, R, a0, a1) in smear:
            arc_smear(r, cx, cy, R, a0, a1, mat="white", width=2, z=6.0)
    if extra: extra(r)
    return r.resolve()


def sundered_frames(pale=False):
    S = lambda **k: sundered(pale=pale, **k)
    idle = [S(bob=[0, -0.3, -0.5, -0.3][i], hand=(7.0, -8.0 + [0, -0.3, -0.5, -0.3][i]), hand2=(4.0, -6.0), ang1=-30, ang2=30,
              crack=1 + (i % 2)) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        run.append(S(lean=10, bob=-0.6 * abs(math.sin(ph)), hand=(8.0, -9.0), hand2=(2.0, -7.0), ang1=170, ang2=160,
                     feet=((-3.4 * math.cos(ph), -max(0, 2.0 * math.sin(ph))), (3.4 * math.cos(ph), -max(0, -2.0 * math.sin(ph))))))
    return idle, run


PALE_GAP = 12      # px the pale half stands behind the dark half at rest (SunderedTorn.Gap)


def with_pale(dark, pale, gap=PALE_GAP, k=0):
    """The whole Sundered in one frame: the pale half `gap` px behind the dark half, a crack of light between them."""
    px, tn = {}, {}
    for (x, y), c in pale.px.items():
        px[(x - gap, y)] = c; tn[(x - gap, y)] = pale.tones[(x, y)]
    for (x, y), c in dark.px.items():
        px[(x, y)] = c; tn[(x, y)] = dark.tones[(x, y)]
    for i, x in enumerate(range(-gap + 2, -1)):
        y = -20 + ((x + k) % 3 == 0)
        if (x, y) not in px:
            m = "white" if (i + k) % 3 else "lilac"
            px[(x, y)] = J.RAMPS[m][4 if m == "white" else 3]; tn[(x, y)] = (m, 4)
    o = J.SprRGB(px); o.tones = tn
    return o


def sundered_sheet(outdir):
    S = sundered
    solo_idle, solo_run = sundered_frames()
    pale_idle, pale_run = sundered_frames(pale=True)
    idle = [with_pale(d, p_, k=i) for i, (d, p_) in enumerate(zip(solo_idle, pale_idle))]
    run = [with_pale(d, p_, k=i) for i, (d, p_) in enumerate(zip(solo_run, pale_run))]
    # Cross (7): sabres open wide (0-1), they scissor shut ahead (2 smear, 3 = HIT), held crossed (4), apart (5-6)
    cr = [S(hand=(5.0, -14.0), hand2=(3.0, -4.0), ang1=-70, ang2=60, face="snarl"),
          S(lean=-6, hand=(3.0, -17.0), hand2=(2.0, -2.0), ang1=-90, ang2=80, face="snarl"),
          S(lean=8, hand=(9.0, -14.0), hand2=(8.0, -5.0), ang1=-10, ang2=10, face="snarl", dx=1.0,
            smear=[(4, -10, 10, -80, -10), (4, -10, 10, 70, 10)]),
          S(lean=12, hand=(10.0, -10.0), hand2=(10.0, -9.0), ang1=20, ang2=-20, face="snarl", dx=2.0, feet=((-3.0, 0.0), (5.0, 0.0))),
          S(lean=10, hand=(10.0, -10.0), hand2=(10.0, -9.0), ang1=25, ang2=-25, dx=2.0, feet=((-3.0, 0.0), (5.0, 0.0))),
          S(lean=4, hand=(8.0, -9.0), hand2=(5.0, -6.0), ang1=-10, ang2=20), S(hand=(7.0, -8.0), hand2=(4.0, -6.0), ang1=-30, ang2=30)]
    # Rejoin (8): it braces, arms wide (0-1), the seam blazes (2-5: the pale half rushes back), it closes the seam (6-7)
    rj = [S(hand=(8.0, -14.0), hand2=(-1.0, -12.0), ang1=-40, ang2=-140, face="snarl", crack=2),
          S(lean=-4, hand=(9.0, -16.0), hand2=(-3.0, -14.0), ang1=-30, ang2=-160, face="snarl", crack=2, glow=2),
          S(lean=-6, hand=(9.0, -16.0), hand2=(-3.0, -14.0), ang1=-30, ang2=-160, face="snarl", crack=2, glow=1),
          S(lean=-6, hand=(9.0, -16.0), hand2=(-3.0, -14.0), ang1=-30, ang2=-160, face="snarl", crack=2, glow=1),
          S(lean=-2, hand=(8.0, -15.0), hand2=(-2.0, -13.0), ang1=-35, ang2=-150, face="snarl", crack=2, glow=2),
          S(lean=6, hand=(9.0, -8.0), hand2=(6.0, -7.0), ang1=10, ang2=20, crack=2, glow=1),
          S(lean=3, hand=(7.0, -8.0), hand2=(4.0, -6.0), ang1=-20, ang2=30, crack=1), S(hand=(7.0, -8.0), hand2=(4.0, -6.0), ang1=-30, ang2=30)]
    d0 = S(lean=-12, face="hurt", hand=(4.0, -16.0), hand2=(0.0, -12.0), ang1=-100, ang2=-140, crack=2)
    d1 = S(lean=-26, bob=4.0, face="hurt", hand=(6.0, -6.0), hand2=(-2.0, -5.0), ang1=10, ang2=170, knee=1, crack=2,
           feet=((-4.0, 0.0), (3.0, 0.0)))
    d2 = remains(0, mask=(SUND_HEAD["hurt"], (3, 5)), mask_at=(3.0, -1.0), stain=11.0, glass=4, glass_mats=("white", "pale"),
                 extra=lambda r: (sabre(r, -10.0, -1.0, 0, 1.0), wisps(r, 0, -6, 1, n=7, spread=8, seed=44, z=4)))
    corpse = remains(1, mask=(SUND_HEAD["hurt"], (3, 5)), mask_at=(4.0, -0.5), stain=12.0, glass=5, glass_mats=("white", "pale"),
                     extra=lambda r: (sabre(r, -11.0, -1.0, 0, 1.0), sabre(r, -2.0, -0.6, 10, 1.1)))
    knock = S(lean=-16, face="hurt", hand=(4.0, -15.0), hand2=(0.0, -12.0), ang1=-90, ang2=-150)
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.08] * 6),
             ("IdleSolo", solo_idle, [0.16, 0.14, 0.16, 0.14]), ("RunSolo", solo_run, [0.08] * 6),
             ("Cross", cr, [0.12, 0.1, 0.05, 0.1, 0.12, 0.1, 0.12]),
             ("Rejoin", rj, [0.1, 0.1, 0.08, 0.08, 0.08, 0.1, 0.12, 0.14])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.14, 0.14, 0.4], knock)
    return sheet("UmbSundered", anims, outdir, scale=5)


# ================================================================== GLASS SERAPH: stained glass, a halo of glass nails
SERA_FACE = """
.aWWw.
aWXWWw
WWWWWw
WknWkn
.WWWW.
..aw..
"""
SERA_PANES = ["redg", "blug", "glass", "redg", "sand", "blug"]


def seraph(alt=4.0, wing=0.0, spread=1.0, lean=0.0, hand=None, halo_k=0, glow=0, extra=None, fold=1.0, dead=False, cast=False):
    r = Rig()
    cy = -alt
    T = Xf(lean, (0.0, cy - 10.0))
    # wings (far then near): leaded red and blue panes
    up = wing * 30.0
    glass_wing(r, -1.0, cy - 17.0, -150 + up, 14.0 * spread * fold, 8.0, -3.0, SERA_PANES, near=False)
    glass_wing(r, -1.0, cy - 15.0, 170 - up * 0.5, 11.0 * spread * fold, 6.0, -3.1, SERA_PANES[::-1], near=False)
    # the robe of glass: a long tapering column of panes, hovering
    body = [T(-3.6, cy - 18.0), T(3.6, cy - 18.0), T(4.6, cy - 6.0), T(2.0, cy - 0.5), T(0.0, cy + 0.5), T(-2.0, cy - 0.5),
            T(-4.4, cy - 6.0)]
    r.poly(body, "blug", 0.0, curve=0.8)
    for (a, b) in (((-1.4, cy - 17.0), (-1.6, cy - 1.0)), ((1.6, cy - 17.0), (1.4, cy - 1.0)), ((-4.0, cy - 9.0), (4.4, cy - 9.0)),
                   ((-3.0, cy - 4.0), (3.4, cy - 4.0))):
        r.line(*T(*a), *T(*b), "lead", 0.05, tone=1)
    for (x, y, m) in ((0.0, cy - 13.0, "redg"), (-2.6, cy - 6.0, "glass"), (2.8, cy - 6.0, "redg"), (0.0, cy - 2.0, "sand")):
        r.ell(*T(x, y), 1.2, 1.6, m, 0.06, bias=0.2)
    # face and the halo of nails
    hx, hy = T(0.6, cy - 20.0)
    r.stamp(SERA_FACE, hx, hy, 1.0, MASK_LEG, pivot=(3, 5))
    n = 9
    for i in range(n):
        a = math.radians(-200 + i * 220 / (n - 1) + halo_k * 6)
        R0, R1 = 5.2, 7.6 + (1.0 if halo_k else 0) * (i % 2)
        x0, y0 = hx + R0 * math.cos(a), hy - 2.4 + R0 * 0.8 * math.sin(a)
        x1, y1 = hx + R1 * math.cos(a), hy - 2.4 + R1 * 0.8 * math.sin(a)
        r.line(x0, y0, x1, y1, "glass", 0.5 if math.sin(a) < 0 else 1.2, tone=3)
        r.dot(x1, y1, "white", 4 if (i + halo_k) % 3 == 0 else 3, 1.3)
    # near wings
    glass_wing(r, 1.0, cy - 17.0, -30 - up, 14.0 * spread * fold, 8.0, 2.0, SERA_PANES, near=True)
    glass_wing(r, 1.0, cy - 15.0, 10 + up * 0.5, 11.0 * spread * fold, 6.0, 1.9, SERA_PANES[::-1], near=True)
    if hand:
        r.tube([T(2.6, cy - 15.0), hand], [1.0, 0.8], "pale", 2.5, bias=0.1)
        r.dot(hand[0], hand[1], "white", 4, 2.6)
    if glow:
        twinkle(r, hx, hy - 3, glow)
    if not dead: floor_shadow(r, 0.0, 5.0)
    if extra: extra(r)
    return r.resolve()


def seraph_sheet(outdir):
    S = seraph
    idle = [S(alt=[4.0, 4.5, 5.0, 4.5][i], wing=[0.0, 0.3, 0.5, 0.3][i], halo_k=i % 2) for i in range(4)]
    run = [S(alt=4.0 + 0.4 * math.sin(i), wing=[0.6, 0.2, -0.3, -0.6, -0.2, 0.3][i], lean=10) for i in range(6)]
    # Feathers (7): wings rise and fold back (0-1), the near wing sweeps forward (2-3: release on 3), (4-6)
    fe = [S(wing=0.6, fold=0.9), S(wing=1.0, fold=0.8, glow=2), S(wing=0.2, lean=6, hand=(8.0, -20.0)),
          S(wing=-0.8, lean=10, hand=(10.0, -18.0), extra=lambda r: [r.dot(13 + i, -19 + i * 0.4, "glass", 4, 6) for i in range(3)]),
          S(wing=-0.5, lean=6), S(wing=0.0), S(wing=0.2)]
    # Prism (9): the halo flares (0-2), wings spread wide (3-4), five feathers burst out (5 = release), settle (6-8)
    pr = [S(wing=0.3, halo_k=1, glow=2), S(wing=0.6, halo_k=2, glow=1), S(wing=0.9, halo_k=3, glow=1, spread=1.05),
          S(wing=1.2, spread=1.1, halo_k=4, glow=1), S(wing=1.3, spread=1.15, halo_k=5, glow=1),
          S(wing=-0.8, spread=1.1, lean=6, halo_k=6, extra=lambda r: [twinkle(r, 10 * math.cos(a), -22 + 8 * math.sin(a), 2) for a in (-1.2, -0.6, 0, 0.6, 1.2)]),
          S(wing=-0.4, halo_k=7), S(wing=0.0, halo_k=8), S(wing=0.2)]
    d0 = S(wing=1.2, lean=-14, fold=0.9)
    d1 = S(alt=1.0, wing=-1.0, lean=-34, fold=0.7, extra=lambda r: shards(r, 0, -16, 1, n=10, mats=("redg", "blug", "glass"), seed=50))
    d2 = remains(0, stain=11.0, glass=12, glass_mats=("redg", "blug", "glass", "sand"), stain_mat="lead",
                 extra=lambda r: r.stamp(SERA_FACE, 3.0, -0.5, 3.0, MASK_LEG, pivot=(3, 5)))
    corpse = remains(1, stain=12.0, glass=16, glass_mats=("redg", "blug", "glass", "sand"), stain_mat="lead",
                     extra=lambda r: r.stamp(SERA_FACE, 4.0, -0.5, 3.0, MASK_LEG, pivot=(3, 5)))
    knock = S(wing=1.0, lean=-18)
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.08] * 6),
             ("Feathers", fe, [0.12, 0.1, 0.08, 0.06, 0.1, 0.12, 0.12]),
             ("Prism", pr, [0.1, 0.1, 0.1, 0.1, 0.12, 0.06, 0.1, 0.12, 0.14])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("UmbGlassSeraph", anims, outdir, scale=5)


# ================================================================== BRISTLEBACK: a hound under a thicket of glass nails
def bristleback(gait=None, lean=0.0, bob=0.0, arch=0.0, shake=0.0, head=0.0, jaw=0.0, nails=1.0, extra=None, dx=0.0,
                eyes=True, crouch=0.0, flung=0):
    r = SRig(1.1)
    by = -9.0 + bob + crouch
    T = Xf(lean, (dx, by))
    # legs: far pair behind, near pair in front
    legs = [(-9.0, True), (5.0, True), (-7.0, False), (7.0, False)]
    for i, (lx, far) in enumerate(legs):
        hx, hy = T(dx + lx * 0.8, by + 2.0)
        fx, fy = dx + lx, 0.0
        if gait is not None:
            ph = gait + (0 if i in (0, 3) else math.pi)
            fx += 2.2 * math.cos(ph); fy = -max(0.0, 1.8 * math.sin(ph))
        kn = ik(hx, hy, fx, fy - 0.6, 4.0, 4.0, bend=1 if lx < 0 else -1)
        z = -1.0 if far else 1.5
        r.tube([(hx, hy), kn, (fx, fy - 0.6)], [2.0, 1.3, 0.9], "void", z, bias=-0.3 if far else 0.15)
        r.dot(fx + 1, fy, "silver", 3 if not far else 2, z + 0.01)
    # body: a deep chest, lower rump; shakes side to side
    sx = shake * 1.6
    r.ell(*T(dx - 1.0 + sx, by - 0.6 - arch), 11.6, 6.4, "void", 0.0, bias=0.15, ang=lean)
    r.ell(*T(dx + 5.0 + sx, by - 0.4), 5.2, 5.2, "shade", 0.1, bias=0.15)
    # the thicket of nails on its back: rows of lilac glass spikes, swept back
    if nails > 0:
        rnd = random.Random(17)
        for i in range(26):
            u = rnd.uniform(-10.0, 6.0)
            base = T(dx + u + sx, by - 4.0 - arch * (1 - abs(u + 2) / 10.0) + rnd.uniform(-1.0, 1.0))
            ln = (3.0 + rnd.random() * 3.0) * nails * (1.0 + arch * 0.15)
            a = math.radians(-100 - 25 * (u + 2) / 8.0 + rnd.uniform(-15, 15) - lean * 0.5 + shake * 25)
            tip = (base[0] + ln * math.cos(a), base[1] + ln * math.sin(a))
            m = "lwing" if i % 3 else "glass"
            r.line(base[0], base[1], tip[0], tip[1], m, 0.5 + i * 0.01, tone=3 if i % 2 else 2)
            r.dot(tip[0], tip[1], "white" if i % 4 == 0 else m, 4, 0.5 + i * 0.01 + 0.005)
    # head: a long hound skull mask
    hx, hy = T(dx + 11.0 + sx + head * 0.4, by - 2.6 + head)
    r.ell(hx - 2.0, hy + 0.6, 3.4, 3.0, "void", 1.0, bias=0.1)
    r.poly([(hx - 2.0, hy - 2.4), (hx + 2.4, hy - 1.6), (hx + 5.4, hy + 0.6), (hx + 5.0, hy + 1.8), (hx - 1.0, hy + 1.6)],
           "bone", 1.2, bias=0.1, normal=(-0.2, -0.6, 1.0))
    r.poly([(hx - 0.6, hy + 2.0), (hx + 4.6, hy + 2.0 + jaw), (hx + 4.0, hy + 3.0 + jaw), (hx - 0.6, hy + 3.2)], "bone", 1.15, bias=-0.2)
    if jaw > 0.5: r.line(hx + 0.4, hy + 2.4, hx + 4.0, hy + 2.4 + jaw * 0.6, "void", 1.16, tone=0)
    if eyes:
        r.dot(hx, hy - 0.6, "lilac", 4, 1.3); r.dot(hx + 1, hy - 0.6, "lilac", 3, 1.3)
    else:
        r.line(hx - 0.5, hy - 0.6, hx + 1.0, hy - 0.6, "void", 1.3, tone=1)
    for k in range(3):
        r.line(hx - 2.6 + k, hy - 2.4, hx - 4.0 + k * 0.5, hy - 5.0, "glass", 1.05, tone=3)
    # tail of nails
    tx, ty = T(dx - 11.0 + sx, by - 1.0)
    for k in range(3):
        a = math.radians(-160 + k * 25)
        r.line(tx, ty, tx + 4.0 * math.cos(a), ty + 4.0 * math.sin(a), "lwing", 0.2, tone=3)
    if flung:
        rnd = random.Random(60 + flung)
        for i in range(6):
            a = rnd.uniform(-math.pi, 0)
            x, y = dx + 14 * math.cos(a), by - 6 + 8 * math.sin(a)
            r.line(x, y, x + 2 * math.cos(a), y + 2 * math.sin(a), "lwing", 7.0, tone=3)
    if extra: extra(r)
    return r.resolve()


def bristle_sheet(outdir):
    B = bristleback
    idle = [B(bob=[0, -0.3, -0.5, -0.3][i], nails=1.0 + 0.04 * i) for i in range(4)]
    run = [B(gait=i / 6 * math.tau, lean=4, bob=-0.8 * abs(math.sin(i / 6 * math.tau))) for i in range(6)]
    # Lob (7): crouch (0), arch the back (1-2), nails pop up off the back (3 = release), settle (4-6)
    lob = [B(crouch=1.0, arch=0.0), B(crouch=0.6, arch=2.0, nails=1.2), B(arch=3.4, nails=1.4, head=1.0, jaw=1.0),
           B(arch=1.0, nails=0.8, flung=1, jaw=1.5), B(arch=0.4, nails=0.85), B(nails=0.92), B()]
    # Shake (8): plant (0), the shake: left, right, left, right (1-4; nails fly on 3), shake off (5), settle (6-7)
    sk = [B(crouch=1.0), B(shake=-1.0, lean=-4), B(shake=1.0, lean=4, nails=1.2), B(shake=-1.2, lean=-5, nails=1.0, flung=2),
          B(shake=1.2, lean=5, nails=0.8, flung=3), B(shake=-0.4, nails=0.8), B(shake=0.2, nails=0.9), B()]
    d0 = B(lean=-10, eyes=False, jaw=1.5, head=-1.0)
    d1 = B(crouch=4.0, lean=-6, eyes=False, nails=0.7, flung=4)
    d2 = remains(0, stain=13.0, glass=10, glass_mats=("lwing", "glass", "white"), stain_mat="void")
    corpse = remains(1, stain=14.0, glass=14, glass_mats=("lwing", "glass", "white"), stain_mat="void",
                     extra=lambda r: r.poly([(7, -3), (11, -2.4), (14, -1.0), (13.6, 0), (7, 0)], "bone", 1.2))
    knock = B(lean=-12, eyes=False, head=-1.5, jaw=1.0)
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.07] * 6),
             ("Lob", lob, [0.12, 0.1, 0.1, 0.06, 0.1, 0.12, 0.12]),
             ("Shake", sk, [0.12, 0.07, 0.07, 0.07, 0.07, 0.1, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("UmbBristleback", anims, outdir, scale=5)


# ================================================================== THE UNBLINKING: a great eye in a cracked mirror frame
def unblinking(alt=4.0, look=(0.0, 0.0), lid=0.0, iris=1.0, crack_light=0, lash=0.0, tilt=0.0, extra=None, dead=False,
               beam=None, flare=0):
    """lid 0 open .. 1 shut. crack_light: light leaking through a shut lid (the tell before it opens)."""
    r = Rig()
    cx, cy = 0.0, -alt - 14.0
    T = Xf(tilt, (cx, cy))
    # the mirror frame: a thick silver oval ring with cracks, glass between frame and eye
    r.ell(cx, cy, 12.0, 13.0, "silver", -1.0, bias=0.05)
    r.ell(cx, cy, 10.4, 11.4, "glass", -0.9, bias=0.15)
    for (a, b) in (((-9, -6), (-5, -2)), ((-5, -2), (-6, 3)), ((7, 6), (4, 2)), ((8, -7), (5, -9))):
        r.line(cx + a[0], cy + a[1], cx + b[0], cy + b[1], "pale", -0.85, tone=4)
    # lashes of black glass round the eye
    for i in range(11):
        a = math.radians(-170 + i * 16)
        x0, y0 = cx + 8.0 * math.cos(a), cy + 6.2 * math.sin(a)
        L = 3.4 + (i % 2) + lash
        r.line(x0, y0, x0 + L * math.cos(a), y0 + L * math.sin(a), "void", -0.5, tone=2 if i % 3 else 3)
        r.dot(x0 + L * math.cos(a), y0 + L * math.sin(a), "lilac", 2, -0.49)
    # the eye
    r.ell(cx, cy, 8.0, 6.4, "bone", 0.0, bias=0.05)
    ix, iy = cx + look[0] * 2.6, cy + look[1] * 1.8
    r.ell(ix, iy, 4.0 * iris, 4.0 * iris, "lwing", 0.1, bias=0.25)
    r.ell(ix, iy, 2.6 * iris, 2.6 * iris, "lilac", 0.12, flat=3)
    r.ell(ix + 0.2, iy, 1.2 * iris + 0.4, 1.6 * iris + 0.4, "void", 0.14, flat=0)
    r.dot(ix - 1.4, iy - 1.6, "white", 4, 0.15)
    # lids: void glass closing from the top
    if lid > 0.01:
        cut = cy - 6.6 + lid * 13.4
        p = r.part(False, 0.2)
        for y in range(int(cy - 7), int(cy + 7)):
            for x in range(int(cx - 9), int(cx + 9)):
                if ((x - cx) / 8.2) ** 2 + ((y - cy) / 6.6) ** 2 <= 1.0 and y <= cut:
                    r.put(x, y, 0.2, "void", J.lam(-0.2, -0.6 + (y - cy) * 0.05, 0.8), p)
        if lid > 0.95:
            for x in range(int(cx - 8), int(cx + 9)):
                r.dot(x, cy + 0.5 * math.cos(x * 0.6), "lilac" if crack_light else "void", 3 if crack_light else 1, 0.25)
        if crack_light:
            for k in range(crack_light * 3):
                x = cx - 6 + k * 3
                r.dot(x, cy - 1 - k % 2, "white", 4, 0.3)
    # wisps under it
    if not dead:
        for k in range(3):
            r.ell(cx - 3 + k * 3, cy + 15.0 + k % 2, 1.4, 1.0, "shade", -2.0, bias=0.1)
        floor_shadow(r, 0.0, 7.0)
    if flare:
        twinkle(r, cx, cy, 1)
    if beam:
        for i in range(beam):
            r.dot(cx + 9 + i, cy, "lilac", 4 if i % 2 else 3, 2.0)
    if extra: extra(r)
    return r.resolve()


def eye_sheet(outdir):
    U = unblinking
    idle = [U(alt=[4.0, 4.4, 4.8, 4.4][i], look=[(0.3, 0), (0.6, 0.2), (0.3, 0.3), (0.0, 0.1)][i], lash=[0, 0.3, 0.6, 0.3][i])
            for i in range(4)]
    run = [U(alt=4.0 + 0.4 * math.sin(i), look=(0.8, 0.0), tilt=8, lash=0.4 * (i % 2)) for i in range(6)]
    # Gaze (8): the iris narrows on the hero (0-2), the beam (3 = fire, 3-5), the iris relaxes (6-7)
    gz = [U(look=(0.8, 0), iris=0.9), U(look=(0.9, 0), iris=0.75), U(look=(1.0, 0), iris=0.6, flare=1),
          U(look=(1.0, 0), iris=0.6, beam=4), U(look=(1.0, 0), iris=0.65, beam=3), U(look=(1.0, 0), iris=0.7, beam=2),
          U(look=(0.8, 0), iris=0.85), U(look=(0.4, 0))]
    # Blackout (5): the lid comes down (0-3), shut (4)
    bo = [U(lid=0.25), U(lid=0.5, iris=0.8), U(lid=0.75), U(lid=0.95), U(lid=1.0)]
    # Shut (4, loops while the dark lasts): the shut eye breathes; Crack (4): light leaks through the lid before it opens
    sh = [U(lid=1.0, alt=[4.0, 4.3, 4.6, 4.3][i], lash=0.3 * (i % 2)) for i in range(4)]
    ck = [U(lid=1.0, crack_light=1), U(lid=1.0, crack_light=2, lash=0.6), U(lid=0.9, crack_light=3, lash=1.0), U(lid=0.6, crack_light=3, lash=1.0)]
    d0 = U(look=(-0.4, 0.4), iris=1.3, tilt=-10)
    d1 = U(alt=1.0, lid=0.6, tilt=-30, extra=lambda r: shards(r, 0, -16, 1, n=10, mats=("silver", "glass", "pale"), seed=52))
    d2 = remains(0, stain=12.0, glass=12, glass_mats=("silver", "glass", "pale"), stain_mat="lwing",
                 extra=lambda r: (r.ell(1.0, -2.6, 4.0, 2.4, "bone", 2.0), r.ell(1.6, -2.6, 1.6, 1.2, "lilac", 2.1, flat=2)))
    corpse = remains(1, stain=13.0, glass=16, glass_mats=("silver", "glass", "pale"), stain_mat="lwing",
                     extra=lambda r: (r.ell(1.0, -2.0, 4.0, 1.8, "bone", 2.0), r.line(-2, -2, 4, -2, "void", 2.1, tone=1)))
    knock = U(look=(-0.6, 0.0), iris=1.2, tilt=-14)
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.08] * 6),
             ("Gaze", gz, [0.1, 0.1, 0.12, 0.1, 0.1, 0.1, 0.12, 0.12]),
             ("Blackout", bo, [0.08, 0.08, 0.08, 0.1, 0.12]), ("Shut", sh, [0.2, 0.18, 0.2, 0.18]),
             ("Crack", ck, [0.12, 0.12, 0.13, 0.13])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("UmbUnblinking", anims, outdir, scale=5)


# ================================================================== GLASS WIDOW: a black glass spider, a mirrored hourglass
def widow(gait=None, lift=0.0, lean=0.0, fore=0.0, stab=0.0, abd=0.0, fang=0.0, extra=None, eyes=True, crouch=0.0, dx=0.0,
          web=None):
    """fore raises the long front legs (0..1); stab drives them down and forward; abd tilts the abdomen up (the web)."""
    r = SRig(1.1)
    by = -10.0 - lift + crouch
    T = Xf(lean, (dx, by))
    # abdomen behind (big, glossy), the mirrored hourglass on its back
    ab = T(dx - 9.0, by - 3.0 - abd * 3.0)
    r.ell(ab[0], ab[1], 9.6, 7.8, "void", -0.5, bias=0.25, ang=-15 - abd * 25)
    r.polyline([(ab[0] - 6.0, ab[1] - 2.0), (ab[0] - 3.0, ab[1] - 5.6), (ab[0] + 1.0, ab[1] - 6.4)], "silver", -0.44, tones=[3, 4])
    r.polyline([(ab[0] - 7.0, ab[1] + 1.0), (ab[0] - 6.4, ab[1] - 1.0)], "silver", -0.44, tone=3)
    hg = [(ab[0] - 3.0, ab[1] - 3.2), (ab[0] + 3.0, ab[1] - 3.2), (ab[0] + 0.5, ab[1]), (ab[0] + 3.0, ab[1] + 3.2),
          (ab[0] - 3.0, ab[1] + 3.2), (ab[0] - 0.5, ab[1])]
    r.poly(hg, "silver", -0.4, bias=0.3, normal=(-0.3, -0.5, 1.0))
    r.dot(ab[0], ab[1], "lilac", 4, -0.38)
    # legs: four a side; the two front ones long and raised
    for i in range(4):
        for far in (True, False):
            hx, hy = T(dx - 1.0 + i * 1.2, by + 0.5)
            fx = dx + (-15.0 + i * 7.5) + (2.0 if not far else -1.0)
            fy = 0.0
            if gait is not None:
                ph = gait + i * math.pi / 2 + (math.pi if far else 0)
                fx += 1.8 * math.cos(ph); fy = -max(0.0, 1.6 * math.sin(ph))
            z = -1.5 if far else 1.5
            if i == 3:
                # the long front legs
                tx = dx + 14.0 + stab * 6.0 - fore * 3.0
                ty = -fore * 14.0 + stab * 10.0 - (2.0 if far else 0)
                ty = min(ty, 0.0)
                kx, ky = hx + 4.0 - fore * 2.0, hy - 7.0 - fore * 4.0
                r.tube([(hx, hy), (kx, ky)], [1.3, 1.0], "void", z, bias=-0.3 if far else 0.2)
                r.tube([(kx, ky), (tx, ty)], [1.0, 0.5], "void", z + 0.01, bias=-0.3 if far else 0.2)
                r.dot(kx, ky - 0.6, "silver", 4 if not far else 2, z + 0.02)
                r.dot(tx, ty, "silver", 4, z + 0.02)
                continue
            kx, ky = (hx + fx) / 2 + (-1 if fx < hx else 1), hy - 6.0
            r.tube([(hx, hy), (kx, ky), (fx, fy - 0.4)], [1.1, 0.9, 0.5], "void", z, bias=-0.3 if far else 0.2)
            r.dot(kx, ky - 0.5, "silver", 3 if not far else 2, z + 0.01)
    # head and cephalothorax
    hd = T(dx + 3.0, by - 0.4)
    r.ell(hd[0], hd[1], 5.0, 4.0, "void", 1.0, bias=0.2)
    r.polyline([(hd[0] - 3.0, hd[1] - 2.4), (hd[0] + 0.6, hd[1] - 3.4)], "silver", 1.05, tone=3)
    if eyes:
        for (ox, oy, t) in ((2.4, -1.6, 4), (3.6, -1.2, 3), (1.4, -2.2, 3), (3.0, -0.2, 2)):
            r.dot(hd[0] + ox, hd[1] + oy, "lilac", t, 1.1)
    r.line(hd[0] + 3.6, hd[1] + 1.4, hd[0] + 4.6 + fang, hd[1] + 3.0 + fang, "silver", 1.2, tone=4)
    r.line(hd[0] + 2.4, hd[1] + 1.8, hd[0] + 3.0 + fang, hd[1] + 3.6 + fang, "silver", 1.15, tone=3)
    if web:
        k = web
        for i in range(3 + k):
            r.dot(ab[0] - 6 + i, ab[1] - 6 - i * 1.5, "pale", 4 if i % 2 else 3, 6.0)
    if extra: extra(r)
    return r.resolve()


def widow_sheet(outdir):
    W = widow
    idle = [W(lift=[0, 0.3, 0.5, 0.3][i], fore=[0.3, 0.35, 0.4, 0.35][i]) for i in range(4)]
    run = [W(gait=i / 6 * math.tau, lean=4, fore=0.15, lift=0.3 * abs(math.sin(i))) for i in range(6)]
    # Fang (7): rear up, front legs high (0-2), STAB down (3 = HIT), held in (4), pull back (5-6)
    fg = [W(fore=0.6, lift=0.6), W(fore=0.9, lift=1.2, lean=-6, fang=1.0), W(fore=1.0, lift=1.4, lean=-8, fang=1.5),
          W(fore=0.0, stab=1.0, lean=8, fang=1.5, dx=1.0), W(fore=0.0, stab=0.8, lean=6, fang=0.5, dx=1.0), W(fore=0.3, lean=2), W()]
    # Web (8): the abdomen tilts up (0-2), the web is shot high (3 = release), (4-7)
    wb = [W(abd=0.3), W(abd=0.7, crouch=1.0), W(abd=1.0, crouch=1.5), W(abd=1.0, crouch=0.5, web=1), W(abd=0.8, web=2),
          W(abd=0.5, web=3), W(abd=0.2), W()]
    d0 = W(lean=-10, fore=1.0, lift=1.0, eyes=False, fang=1.0)
    d1 = W(lean=-6, crouch=4.0, fore=0.0, eyes=False)
    d2 = remains(0, stain=14.0, glass=10, glass_mats=("silver", "void", "lilac"), stain_mat="void")
    corpse = remains(1, stain=15.0, glass=14, glass_mats=("silver", "void", "lilac"), stain_mat="void",
                     extra=lambda r: r.poly([(-4, -1.5), (-1, -3.5), (2, -1.5), (-1, 0.5)], "silver", 2.0, bias=0.3))
    knock = W(lean=-12, fore=0.8, lift=1.0, eyes=False)
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.07] * 6),
             ("Fang", fg, [0.12, 0.1, 0.1, 0.06, 0.1, 0.12, 0.12]),
             ("Web", wb, [0.1, 0.1, 0.12, 0.06, 0.1, 0.1, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("UmbGlassWidow", anims, outdir, scale=5)


# ================================================================== ECLIPSE WYRM: two heads, void and glass
def wyrm_head(r, x, y, ang, z, kind, jaw=0.0, eyes=True):
    T0 = Xf(ang, (x, y))
    k_ = 1.3 if kind == "void" else 1.55
    T = lambda px, py: T0(x + (px - x) * k_, y + (py - y) * k_)
    if kind == "void":
        m = "void"
        r.poly([T(x - 3.0, y - 2.6), T(x + 2.0, y - 3.0), T(x + 5.6, y - 1.4 - jaw * 0.5), T(x + 6.2, y - 0.2 - jaw * 0.5),
                T(x + 1.0, y + 0.6), T(x - 3.0, y + 2.4)], m, z, bias=0.15, normal=(-0.2, -0.6, 1.0))
        r.poly([T(x - 1.0, y + 1.0), T(x + 5.6, y + 0.8 + jaw), T(x + 4.6, y + 2.2 + jaw), T(x - 1.6, y + 2.6)], m, z - 0.01, bias=-0.2)
        for k in range(3):                                                        # horns swept back
            r.line(*T(x - 2.0 + k, y - 2.4), *T(x - 5.0 + k * 0.6, y - 4.8 - k * 0.4), "silver", z - 0.02, tone=3)
    else:
        # the glass head in facets: a lit crown, a mid cheek, a dark jaw, a crest of glass spines
        crown_ = [T(x - 3.0, y - 2.8), T(x + 2.0, y - 3.2), T(x + 5.8, y - 1.6 - jaw * 0.5), T(x + 1.0, y - 0.6)]
        cheek = [T(x - 3.0, y - 2.8), T(x + 1.0, y - 0.6), T(x + 5.8, y - 1.6 - jaw * 0.5), T(x + 6.4, y - 0.2 - jaw * 0.5),
                 T(x + 1.0, y + 0.8), T(x - 3.0, y + 2.4)]
        jaw_ = [T(x - 1.0, y + 1.0), T(x + 5.8, y + 0.8 + jaw), T(x + 4.8, y + 2.4 + jaw), T(x - 1.6, y + 2.8)]
        r.poly(cheek, "glass", z, flat=2)
        r.poly(crown_, "glass", z + 0.005, flat=3)
        r.poly(jaw_, "glass", z - 0.01, flat=1)
        r.line(*T(x + 1.0, y - 0.6), *T(x + 5.8, y - 1.6 - jaw * 0.5), "white", z + 0.006, tone=4)       # the facet edge
        for k in range(4):                                                        # the crest
            bx, by = T(x - 2.6 + k * 1.4, y - 2.8 - k * 0.1)
            tx, ty = T(x - 4.6 + k * 1.2, y - 5.6 - (k % 2) * 1.2)
            r.line(bx, by, tx, ty, "glass", z - 0.02, tone=3)
            r.dot(tx, ty, "white", 4, z - 0.019)
    if jaw > 0.5:
        r.dot(*T(x + 4.0, y + 0.4 + jaw * 0.5), "bone", 4, z + 0.01); r.dot(*T(x + 2.4, y + 0.6 + jaw * 0.5), "bone", 3, z + 0.01)
        r.line(*T(x + 0.6, y + 0.9 + jaw * 0.4), *T(x + 4.6, y + 0.9 + jaw * 0.6), "void", z + 0.008, tone=0)
    if eyes:
        ex, ey = T(x + 1.2, y - 1.6)
        if kind == "void":
            r.dot(ex, ey, "lilac", 4, z + 0.02); r.dot(ex + 1, ey, "lilac", 3, z + 0.02)
        else:
            r.dots([(ex, ey), (ex + 1, ey)], "void", 0, z + 0.02)
            r.dot(ex + 1, ey, "cyanl", 4, z + 0.021)


def outline(spr, mats, against=None):
    """A darker edge round `mats` wherever they meet open air or another material (not against those in `against`)."""
    against = set(against or ()) | set(mats)
    px, tn = dict(spr.px), dict(spr.tones)
    for (x, y), (m, t) in spr.tones.items():
        if m not in mats: continue
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q not in spr.tones or spr.tones[q][0] not in against:
                px[(x, y)] = J.RAMPS[m][0]; tn[(x, y)] = (m, 0); break
    o = J.SprRGB(px); o.tones = tn
    return o


def eclipse_wyrm(phase=0.0, vh=None, gh=None, vjaw=0.0, gjaw=0.0, lean=0.0, extra=None, eyes=True, coil=1.0, swallow=0.0,
                 gone_glass=False, dx=0.0):
    """Coiled body on the floor, two necks: void head (vh) in front, glass head (gh) behind and higher."""
    r = Rig()
    # the coil: two stacked rings of a thick body
    for k, (cy, rx, ry, z) in enumerate(((-3.6, 11.0, 3.6, -0.5), (-7.6, 8.4, 3.0, 0.0))):
        pts = [(dx + rx * math.cos(a) - 1.0, cy + ry * math.sin(a)) for a in [i / 14 * math.tau + phase * 0.3 + k for i in range(15)]]
        r.tube(pts, [3.8 - k * 0.4] * 15, "void", z, bias=0.08)
        for i in range(0, 15, 3):
            x, y = pts[i]
            if math.sin(i / 14 * math.tau + phase * 0.3 + k) > 0:
                r.dot(x, y - 1.6, "lilac", 2, z + 0.01)
    vhx, vhy = vh or (dx + 10.0, -24.0 + math.sin(phase) * 0.6)
    ghx, ghy = gh or (dx - 1.5, -28.6 + math.cos(phase) * 0.6)
    base = (dx + 2.0, -9.0)
    # glass neck behind
    if not gone_glass:
        gp = [base, (base[0] - 1.0, base[1] - 7.0), (ghx - 3.0, ghy + 6.0), (ghx - 2.0, ghy + 1.0)]
        r.tube(gp, [2.2, 1.9, 1.7, 1.5], "glass", -1.0, bias=-0.15)
        for i in range(1, 4):
            r.dot(gp[i][0] - 0.8, gp[i][1], "white", 4, -0.95)
            r.line(gp[i][0] - 1.5, gp[i][1] + 1.0, gp[i][0] + 1.5, gp[i][1] + 0.4, "glass", -0.96, tone=1)
        wyrm_head(r, ghx, ghy, -10 + lean, -0.9, "glass", jaw=gjaw, eyes=eyes)
    # void neck in front
    vp = [(base[0] + 1.0, base[1]), (base[0] + 3.5, base[1] - 6.0), (vhx - 3.5, vhy + 6.0), (vhx - 2.0, vhy + 1.0)]
    r.tube(vp, [3.4, 3.0, 2.6, 2.2], "void", 1.0, bias=0.15)
    for i in range(1, 4):
        x, y = vp[i]
        r.dot(x + 1.6, y, "bone", 1, 1.05)
    wyrm_head(r, vhx, vhy, -6 + lean, 1.2, "void", jaw=vjaw + swallow * 2.0, eyes=eyes)
    if swallow > 0:
        twinkle(r, vhx + 4, vhy - 1, 2)
    if extra: extra(r)
    return outline(r.resolve(), ("glass",), against=("white", "cyanl"))


def eclipse_disc(k=0, extra=None, burst=0):
    """The eclipse: a black disc with a burning white corona, hovering (k = flame phase). burst: the glass head breaking
    out of it (1-3)."""
    r = Rig()
    cx, cy = 0.0, -15.0
    r.ell(cx, cy, 9.0, 9.0, "dark", 0.0, flat=0)
    r.ell(cx - 2.0, cy - 2.0, 5.6, 5.6, "dark", 0.01, flat=1)
    rnd = random.Random(80 + k)
    for i in range(36):
        a = i / 36 * math.tau
        R = 9.6 + (rnd.random() * 2.6 if i % 2 == k % 2 else 0.6)
        for t in range(int(R - 9.0) + 1):
            rr = 9.4 + t
            r.dot(cx + rr * math.cos(a), cy + rr * math.sin(a), "white" if t == 0 else "lilac", 4 if t == 0 else (3 if t == 1 else 2), 0.5)
    r.ell(cx, cy + 15.0, 6.0, 1.2, "dark", -2.0, flat=2)
    if burst:
        for i in range(6 + burst * 2):
            a = i / (6 + burst * 2) * math.tau
            d = 6 + burst * 3
            r.line(cx + 4 * math.cos(a), cy + 4 * math.sin(a), cx + d * math.cos(a), cy + d * math.sin(a), "pale", 1.0, tone=4)
    if extra: extra(r)
    return r.resolve()


def wyrm_sheet(outdir):
    E = eclipse_wyrm
    idle = [E(phase=i * 1.57) for i in range(4)]
    run = [E(phase=i * 1.05, lean=6, vh=(12.0, -22.0 + 0.6 * math.sin(i)), gh=(6.0, -29.0 + 0.6 * math.cos(i))) for i in range(6)]
    # Fangs (9): the void head draws back (0-1), BITES (2-3: HIT on 3), the glass head comes over (4), BITES (5 = HIT), (6-8)
    fg = [E(vh=(8.0, -26.0), vjaw=1.0), E(vh=(6.0, -27.0), vjaw=2.0), E(vh=(16.0, -18.0), vjaw=2.0, lean=10),
          E(vh=(17.0, -16.0), vjaw=0.0, lean=12), E(vh=(12.0, -20.0), gh=(8.0, -33.0), gjaw=2.0),
          E(vh=(10.0, -22.0), gh=(17.0, -22.0), gjaw=2.0, lean=10), E(vh=(10.0, -22.0), gh=(16.0, -21.0), gjaw=0.0),
          E(gh=(8.0, -28.0)), E()]
    # Swallow (8): the void head turns on the glass head (0-2), gapes (3), swallows it (4-6), it becomes the eclipse (7)
    sw = [E(vh=(8.0, -28.0), lean=-10), E(vh=(6.0, -31.0), vjaw=2.0, lean=-20), E(vh=(5.0, -33.0), vjaw=3.0, gh=(4.0, -30.0), lean=-30),
          E(vh=(4.0, -33.0), swallow=1.0, gh=(4.0, -31.0), lean=-30), E(vh=(4.0, -32.0), swallow=0.6, gone_glass=True, lean=-20),
          E(vh=(4.0, -30.0), swallow=0.2, gone_glass=True), eclipse_disc(0, extra=lambda r: None), eclipse_disc(1)]
    disc = [eclipse_disc(k) for k in range(4)]
    # Burst (6): the glass head bursts out (0-2), the wyrm uncoils (3-5)
    bu = [eclipse_disc(0, burst=1), eclipse_disc(1, burst=2), eclipse_disc(2, burst=3),
          E(gh=(6.0, -32.0), gjaw=2.0, vh=(12.0, -20.0)), E(gh=(5.0, -30.0)), E()]
    d0 = E(vh=(4.0, -26.0), gh=(0.0, -30.0), vjaw=2.0, gjaw=2.0, lean=-20, eyes=False)
    d1 = E(vh=(14.0, -10.0), gh=(-6.0, -14.0), vjaw=1.0, gjaw=1.0, lean=-40, eyes=False)
    d2 = remains(0, stain=15.0, glass=8, glass_mats=("pale", "glass"), stain_mat="void",
                 extra=lambda r: (wyrm_head(r, 8.0, -2.4, 10, 2.0, "void", eyes=False), wyrm_head(r, -8.0, -2.4, -10, 2.0, "glass", eyes=False)))
    corpse = remains(1, stain=16.0, glass=10, glass_mats=("pale", "glass"), stain_mat="void",
                     extra=lambda r: (wyrm_head(r, 9.0, -2.0, 14, 2.0, "void", eyes=False), wyrm_head(r, -9.0, -2.0, -14, 2.0, "glass", eyes=False)))
    knock = E(vh=(6.0, -26.0), gh=(1.0, -31.0), vjaw=1.0, lean=-14, eyes=False)
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.08] * 6),
             ("Fangs", fg, [0.12, 0.1, 0.05, 0.1, 0.08, 0.06, 0.1, 0.12, 0.12]),
             ("Swallow", sw, [0.1, 0.1, 0.1, 0.12, 0.1, 0.1, 0.08, 0.1]), ("Disc", disc, [0.08] * 4),
             ("Burst", bu, [0.06, 0.06, 0.08, 0.1, 0.12, 0.14])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("UmbEclipseWyrm", anims, outdir, scale=5)


# ================================================================== THE UNDERTOW: an eel in a pool of ink that goes where it goes
def ink_pool(r, cx, w, k=0, z=-2.0, eyes=False, depth=1.0):
    """A pool of ink on the floor: a deep middle, a lit near lip, a lilac far rim and two broken rings of ripples."""
    h = 3.6 * depth
    r.ell(cx, -h, w, h, "ink", z, flat=1)
    r.ell(cx + 0.5, -h + 0.4, w * 0.72, h * 0.66, "ink", z + 0.001, flat=0)
    for i in range(64):
        a = i / 64 * math.tau
        x, y = cx + w * math.cos(a), -h + h * math.sin(a)
        if math.sin(a) < -0.15:
            if (i + k) % 5: r.dot(x, y, "lilac", 3 if math.cos(a) < 0 else 2, z + 0.01)
        elif math.sin(a) > 0.3:
            r.dot(x, y - 0.4, "ink", 3, z + 0.01)
    for (f, tone) in ((0.48, 3), (0.8, 2)):
        for i in range(40):
            a = i / 40 * math.tau
            if (i + k * 3) % 7 < 3: continue
            r.dot(cx + 0.5 + w * f * math.cos(a), -h + 0.4 + h * f * 0.8 * math.sin(a), "lilac" if tone == 2 else "ink", tone, z + 0.005)
    if eyes:
        for x in (cx - 2.0, cx + 2.0):
            r.dot(x, -h - 0.5, "bone", 4 if k % 4 != 3 else 1, z + 0.03)
            r.dot(x + 1, -h - 0.5, "lilac", 3, z + 0.03)


def eel_head(r, hx, hy, ang, jaw, eyes, z):
    """The eel's head: a blunt skull and a hinged jaw full of pale teeth, a pale eye, gill slits."""
    T = Xf(ang, (hx, hy))
    r.poly([T(hx - 4.0, hy - 3.0), T(hx + 1.0, hy - 4.0), T(hx + 6.4, hy - 2.4 - jaw * 0.3), T(hx + 7.2, hy - 0.4),
            T(hx + 1.0, hy + 0.6), T(hx - 4.0, hy + 1.6)], "ink", z, bias=0.3, normal=(-0.3, -0.7, 1.0))
    r.poly([T(hx - 2.6, hy + 1.0), T(hx + 6.4, hy + 0.8 + jaw), T(hx + 5.6, hy + 2.6 + jaw), T(hx - 2.6, hy + 3.2)], "ink", z - 0.01,
           bias=-0.1)
    r.line(*T(hx - 2.4, hy + 1.4), *T(hx + 5.4, hy + 1.4 + jaw * 0.8), "bone", z - 0.005, tone=1)        # pale throat
    for i in range(5):
        r.dot(*T(hx + 0.4 + i * 1.4, hy + 0.2 + (0.6 if i % 2 else 0)), "bone", 4 if i % 2 else 3, z + 0.02)
        if jaw > 0.4: r.dot(*T(hx + 0.6 + i * 1.3, hy + 0.4 + jaw - (0.6 if i % 2 else 0)), "bone", 3, z + 0.02)
    if jaw > 0.8:
        r.line(*T(hx + 0.4, hy + 0.8 + jaw * 0.4), *T(hx + 5.0, hy + 0.8 + jaw * 0.6), "void", z + 0.015, tone=0)
    for i in range(3):
        r.line(*T(hx - 3.0 + i * 1.2, hy - 1.6), *T(hx - 2.6 + i * 1.2, hy + 0.4), "ink", z + 0.02, tone=1)
    ex, ey = T(hx + 1.8, hy - 2.0)
    if eyes:
        r.dot(ex, ey, "bone", 4, z + 0.03); r.dot(ex + 1, ey, "lilac", 3, z + 0.03); r.dot(ex, ey + 1, "bone", 2, z + 0.03)
    else:
        r.line(ex - 1, ey, ex + 1, ey, "void", z + 0.03, tone=1)


def undertow(rear=1.0, phase=0.0, head=None, jaw=0.0, sink=0.0, extra=None, eyes=True, pool_w=15.0, smear=None, dx=0.0):
    """An eel surging out of the ink pool that goes everywhere with it. sink 0..1 draws the body down into the pool."""
    r = SRig(1.1)
    ink_pool(r, dx - 2.0, pool_w, k=int(phase * 2), z=-2.0)
    if sink < 0.98:
        hx, hy = head or (dx + 7.0, -19.0 * rear + math.sin(phase) * 0.6)
        hy = lerp(hy, -2.0, sink); hx = lerp(hx, dx + 2.0, sink * 0.5)
        base = (dx - 2.5, -3.2)
        mid = (dx - 6.0 + math.sin(phase) * 0.8, lerp(-8.0, -3.0, sink))
        pts = [base, mid, (lerp(mid[0], hx, 0.5) - 3.0, lerp(mid[1], hy, 0.55)), (hx - 3.0, hy + 2.6), (hx - 0.6, hy + 0.4)]
        rad = [5.6, 5.0, 4.2, 3.4, 3.0]
        r.tube(pts, rad, "ink", 0.0, bias=0.28)
        # dorsal spines down the back, a pale belly down the front, rings of scale
        for i in range(1, 4):
            (x0, y0), (x1, y1) = pts[i - 1], pts[i]
            for t in (0.3, 0.8):
                x, y = lerp(x0, x1, t), lerp(y0, y1, t)
                ang = math.atan2(y1 - y0, x1 - x0)
                nx, ny = math.sin(ang), -math.cos(ang)
                rr = rad[i] * 0.95
                r.line(x - nx * rr, y - ny * rr, x - nx * (rr + 2.4), y - ny * (rr + 2.4) - 0.8, "ink", -0.1, tone=3)
                r.dot(x - nx * (rr + 2.4), y - ny * (rr + 2.4) - 0.8, "lilac", 3, -0.09)
                r.dot(x + nx * rr * 0.75, y + ny * rr * 0.75, "bone", 2 if t < 0.5 else 1, 0.06)
                r.line(x - nx * rr * 0.6, y - ny * rr * 0.6, x + nx * rr * 0.4, y + ny * rr * 0.4, "ink", 0.05, tone=1)
        # where it breaks the surface: a lip of ink and thrown drops
        for i in range(6):
            a = i / 6 * math.pi
            r.dot(base[0] + 6.5 * math.cos(a), -2.4 - 2.0 * math.sin(a) - (i % 2), "ink", 3 if i % 2 else 2, 0.2)
        ang = math.degrees(math.atan2(pts[-1][1] - pts[-2][1], pts[-1][0] - pts[-2][0]))
        eel_head(r, hx, hy, ang * 0.4, jaw, eyes, 0.6)
    else:
        ink_pool(r, dx - 2.0, pool_w * 0.8, k=int(phase * 2), z=-1.9, eyes=eyes)
    if smear:
        for (a, b) in smear:
            r.line(*a, *b, "lilac", 4.0, tone=3)
    if extra: extra(r)
    return rimlight(r.resolve(), ("ink",))


def undertow_sheet(outdir):
    U = undertow
    idle = [U(phase=i * 1.57, rear=[1.0, 1.03, 1.06, 1.03][i]) for i in range(4)]
    run = [U(phase=i * 1.05, rear=0.8, head=(10.0, -15.0 + math.sin(i)), pool_w=13.0) for i in range(6)]
    # Venom (7): rear back (0-1), jaw gapes (2), STRIKE (3 = HIT), hold (4), back (5-6)
    vn = [U(head=(5.0, -22.0)), U(head=(3.0, -23.0), jaw=1.0), U(head=(2.0, -22.0), jaw=2.0),
          U(head=(16.0, -12.0), jaw=2.0, smear=[((4, -18), (12, -13))]), U(head=(15.0, -11.0), jaw=0.5), U(head=(10.0, -17.0)), U()]
    # Dive (7): the body arches (0-1), dives into its ink (2-5), only the pool with two eyes (6)
    dv = [U(head=(6.0, -23.0)), U(head=(10.0, -18.0), jaw=1.0), U(sink=0.3, head=(8.0, -10.0)), U(sink=0.6, head=(6.0, -6.0)),
          U(sink=0.85, head=(4.0, -4.0)), U(sink=1.0, pool_w=10.0), U(sink=1.0, pool_w=8.0)]
    # LurkBite (6): from a pool: bursts up (0-1), BITES (2 = HIT), sinks (3-5)
    lb = [U(sink=0.6, head=(6.0, -8.0), pool_w=9.0, jaw=1.0), U(sink=0.2, head=(10.0, -14.0), pool_w=9.0, jaw=2.0),
          U(sink=0.0, head=(14.0, -10.0), pool_w=9.0, jaw=2.0), U(sink=0.4, head=(10.0, -8.0), pool_w=9.0),
          U(sink=0.8, pool_w=9.0), U(sink=1.0, pool_w=8.0)]
    # Surface (5): the pool spreads (0), it rises out (1-3), (4)
    sf = [U(sink=1.0, pool_w=10.0), U(sink=0.7, head=(6.0, -8.0)), U(sink=0.4, head=(8.0, -14.0)), U(sink=0.1, head=(8.0, -19.0)), U()]
    # Lurk (4): only ink and two eyes (hidden where it lies)
    lk = [U(sink=1.0, pool_w=8.0, phase=k * 0.5) for k in range(4)]
    d0 = U(head=(2.0, -24.0), jaw=2.0, eyes=False)
    d1 = U(sink=0.5, head=(12.0, -6.0), jaw=1.0, eyes=False)
    d2 = U(sink=0.8, head=(14.0, -3.0), jaw=1.0, eyes=False, pool_w=14.0)
    corpse = remains(1, stain=15.0, glass=0, stain_mat="ink",
                     extra=lambda r: [r.dot(6 + k * 1.4, -1.5, "bone", 3 + k % 2, 2.0) for k in range(4)])
    knock = U(head=(1.0, -23.0), jaw=1.0, eyes=False)
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.08] * 6),
             ("Venom", vn, [0.12, 0.1, 0.1, 0.06, 0.1, 0.12, 0.12]), ("Dive", dv, [0.08, 0.08, 0.06, 0.06, 0.06, 0.08, 0.1]),
             ("LurkBite", lb, [0.06, 0.06, 0.1, 0.08, 0.08, 0.1]), ("Surface", sf, [0.1, 0.08, 0.08, 0.1, 0.12]),
             ("Lurk", lk, [0.2, 0.18, 0.2, 0.18])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("UmbUndertow", anims, outdir, scale=5)


# ================================================================== ARGUS MOTH: wings of a hundred painted eyes
def eye_wing(r, sx, sy, ang, ln, wid, z, near=True, look=0.0, glow=False):
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    px, py = -uy, ux
    tip = (sx + ux * ln, sy + uy * ln)
    outline = [(sx, sy), (sx + ux * ln * 0.4 + px * wid * 0.7, sy + uy * ln * 0.4 + py * wid * 0.7),
               (sx + ux * ln * 0.9 + px * wid * 0.55, sy + uy * ln * 0.9 + py * wid * 0.55), tip,
               (sx + ux * ln * 0.8 - px * wid * 0.5, sy + uy * ln * 0.8 - py * wid * 0.5),
               (sx + ux * ln * 0.3 - px * wid * 0.4, sy + uy * ln * 0.3 - py * wid * 0.4)]
    r.poly(outline, "lwing", z, bias=0.15 if near else -0.3, normal=(-0.2, -0.4, 1.0))
    # the rim
    for a_, b_ in zip(outline, outline[1:] + outline[:1]):
        r.line(*a_, *b_, "robe", z + 0.005, tone=1 if near else 0)
    # painted eyes: gold rings, dark pupils turned by `look`
    spots = [(0.35, 0.2, 2.0), (0.65, 0.25, 1.6), (0.85, -0.1, 1.2), (0.5, -0.25, 1.3), (0.2, -0.15, 1.0)]
    for (t, s, rad) in spots:
        ex = sx + ux * ln * t + px * wid * s
        ey = sy + uy * ln * t + py * wid * s
        r.ell(ex, ey, rad + 0.6, rad + 0.4, "lilac" if glow else "sand", z + 0.01, flat=3 if not glow else 4)
        r.ell(ex, ey, rad, rad - 0.2, "void" if not glow else "lilac", z + 0.015, flat=1 if not glow else 2)
        r.dot(ex + look * rad * 0.6, ey, "void", 0, z + 0.02)
        if glow: r.dot(ex + look * rad * 0.6 - 0.6, ey - 0.6, "lilac", 4, z + 0.03)
        elif rad > 1.5 and near: r.dot(ex - 0.6, ey - 0.6, "white", 4, z + 0.03)
    return tip


def argus(alt=6.0, flap=0.0, tilt=0.0, look=0.0, glow=False, extra=None, fold=1.0, dead=False, scales=None):
    r = Rig()
    cx, cy = 0.0, -alt - 12.0
    up = flap * 30.0
    eye_wing(r, cx - 1.0, cy - 1.0, -150 + up, 19.5 * fold, 12.0, -2.0, near=False, look=look, glow=glow)
    eye_wing(r, cx - 1.0, cy + 2.0, 145 - up * 0.5, 13.5 * fold, 9.0, -2.1, near=False, look=look, glow=glow)
    # furred body, feathered antennae
    T = Xf(tilt, (cx, cy))
    r.ell(*T(cx, cy), 2.6, 6.0, "robe", 0.0, bias=0.1, ang=tilt)
    for i in range(3):
        r.line(*T(cx - 2.0, cy - 2.0 + i * 2.6), *T(cx + 2.0, cy - 1.4 + i * 2.6), "sand", 0.05, tone=1)
    hx, hy = T(cx + 0.8, cy - 6.4)
    r.ell(hx, hy, 2.2, 2.0, "robe", 0.1, bias=0.2)
    r.dot(hx + 1, hy - 0.4, "sand", 4, 0.15); r.dot(hx - 0.4, hy - 0.4, "sand", 3, 0.15)
    for s in (-1, 1):
        r.polyline([(hx, hy - 1.6), (hx + 1.4 * s, hy - 4.6), (hx + 3.2 * s, hy - 6.0)], "sand", 0.12, tones=[2, 3])
    eye_wing(r, cx + 1.0, cy - 1.0, -30 - up, 19.5 * fold, 12.0, 2.0, near=True, look=look, glow=glow)
    eye_wing(r, cx + 1.0, cy + 2.0, 35 + up * 0.5, 13.5 * fold, 9.0, 1.9, near=True, look=look, glow=glow)
    if scales:
        for (x, y) in scales:
            r.dot(x, y, "sand", 4, 6.0); r.dot(x - 1, y, "lwing", 3, 6.0)
    if not dead: floor_shadow(r, 0.0, 8.0)
    if extra: extra(r)
    return r.resolve()


def argus_sheet(outdir):
    A = argus
    idle = [A(alt=[6.0, 6.4, 6.8, 6.4][i], flap=[0.0, 0.4, 0.7, 0.3][i]) for i in range(4)]
    run = [A(alt=6.0 + 0.4 * math.sin(i), flap=[0.8, 0.3, -0.3, -0.8, -0.3, 0.3][i], tilt=10) for i in range(6)]
    # Volley (6): wings up (0-1), the downbeat flicks three scales (2 = release), (3-5)
    vo = [A(flap=0.8), A(flap=1.1, glow=True), A(flap=-0.9, tilt=8, scales=[(18, -20), (19, -17), (18, -14)]), A(flap=-0.5), A(flap=0.0), A(flap=0.3)]
    # Storm (9): three wing beats, a wave of scales on each down-stroke (1, 4, 7)
    st = []
    for w in range(3):
        st += [A(flap=1.1, glow=w > 0), A(flap=-1.0, tilt=8, scales=[(18, -21 - w), (20, -17), (18, -12 + w)]), A(flap=-0.2)]
    # Catch (4): every painted eye snaps to a passing shot and glows
    ca = [A(look=1.0, glow=True, flap=0.3), A(look=-1.0, glow=True, flap=0.5), A(look=0.0, glow=True, flap=0.2), A(flap=0.0)]
    d0 = A(flap=1.0, tilt=-16, look=-1.0)
    d1 = A(alt=2.0, flap=-1.0, tilt=-40, fold=0.8)
    d2 = remains(0, stain=14.0, glass=10, glass_mats=("sand", "lwing"), stain_mat="lwing")
    corpse = remains(1, stain=15.0, glass=14, glass_mats=("sand", "lwing"), stain_mat="lwing",
                     extra=lambda r: [r.ell(x, -1.4, 1.4, 0.8, "sand", 2.0) for x in (-8, -2, 5, 10)])
    knock = A(flap=0.9, tilt=-20, look=-1.0)
    anims = [("Idle", idle, [0.12, 0.1, 0.12, 0.1]), ("Run", run, [0.07] * 6),
             ("Volley", vo, [0.12, 0.1, 0.06, 0.1, 0.1, 0.12]),
             ("Storm", st, [0.1, 0.06, 0.14] * 3), ("Catch", ca, [0.06, 0.08, 0.1, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("UmbArgusMoth", anims, outdir, scale=5)


# ================================================================== GLITTERSWARM: a mirror heart in a whirl of glass moths
def glass_moth_tiny(r, x, y, k, z, mat="glass"):
    up = (k % 2) == 0
    r.dot(x, y, "silver", 2, z); r.dot(x, y + 1, "silver", 1, z)
    for s in (-1, 1):
        r.dot(x + s, y - (1 if up else 0), mat, 4 if up else 3, z)
        r.dot(x + 2 * s, y - (2 if up else 0), mat, 3, z)
    if up: r.dot(x, y - 1, "white", 4, z + 0.001)


def glitterswarm(alt=6.0, phase=0.0, stretch=0.0, heart=True, n=42, beat=0, extra=None, dead=False, lean=0.0, spread=1.0):
    r = SRig(1.14)
    cx, cy = 0.0, -alt - 11.0
    if heart:
        T = Xf(lean, (cx, cy))
        hb = 1.5 + 0.12 * beat
        pts = [T(cx, cy + 5.0 * hb), T(cx - 5.0 * hb, cy - 0.6), T(cx - 4.0 * hb, cy - 4.0 * hb), T(cx - 1.6, cy - 4.4 * hb), T(cx, cy - 2.6),
               T(cx + 1.6, cy - 4.4 * hb), T(cx + 4.0 * hb, cy - 4.0 * hb), T(cx + 5.0 * hb, cy - 0.6)]
        r.poly(pts, "silver", 0.0, normal=(-0.2, -0.3, 1.0))
        inner = [((p[0] - cx) * 0.66 + cx, (p[1] - cy) * 0.66 + cy - 0.2) for p in pts]
        r.poly(inner, "glass", 0.05, curve=0.6, normal=(-0.3, -0.3, 1.0))
        r.line(cx - 2.6, cy - 2.6, cx - 0.6, cy + 1.0, "white", 0.1, tone=4)
        r.dot(cx + 1.4, cy - 0.6, "lilac", 4, 0.1); r.dot(cx + 0.4, cy - 0.6, "lilac", 3, 0.1)
    rnd = random.Random(90)
    for i in range(n):
        a = i / n * math.tau + phase + rnd.uniform(-0.2, 0.2)
        R = (6.0 + rnd.uniform(0.0, 7.0)) * spread
        x = cx + R * math.cos(a) * (1.0 + stretch * max(0.0, math.cos(a)))
        y = cy + R * 0.75 * math.sin(a)
        z = 1.0 if math.sin(a) > 0 else -1.0
        glass_moth_tiny(r, x + stretch * 6.0 * max(0.0, math.cos(a)), y, i + int(phase * 4), z, mat="glass" if i % 3 else "pale")
    # the glitter haze the moths shed
    for i in range(22):
        a = rnd.uniform(0, math.tau); R = rnd.uniform(3, 12) * spread
        r.dot(cx + R * math.cos(a) * (1 + stretch * 0.5), cy + R * 0.7 * math.sin(a), "lilac", 2 + (i % 2), -1.5)
    if not dead: floor_shadow(r, 0.0, 8.0)
    if extra: extra(r)
    return r.resolve()


def swarm_sheet(outdir):
    G = glitterswarm
    idle = [G(phase=i * 0.4, beat=i % 2) for i in range(4)]
    run = [G(phase=i * 0.5, lean=10, stretch=0.2, alt=6.0 + 0.4 * math.sin(i)) for i in range(6)]
    # Bite (7): the cloud draws in (0-1), surges ahead (2 = HIT), (3), pulls back (4-6)
    bt = [G(phase=0.0, spread=0.8), G(phase=0.3, spread=0.7, beat=1), G(phase=0.6, stretch=1.0, lean=8), G(phase=0.9, stretch=0.8),
          G(phase=1.2, stretch=0.4), G(phase=1.5), G(phase=1.8)]
    # Surge (8): the cloud gathers (0-1), streams out into a line (2-5), gathers again (6-7)
    sg = [G(phase=0.0, spread=0.7, beat=1), G(phase=0.4, spread=0.6, beat=1), G(phase=0.8, stretch=1.6, lean=10),
          G(phase=1.2, stretch=1.8, lean=12), G(phase=1.6, stretch=1.8, lean=12), G(phase=2.0, stretch=1.4, lean=8),
          G(phase=2.4, stretch=0.6), G(phase=2.8)]
    d0 = G(phase=0.0, spread=1.3)
    d1 = G(phase=0.4, spread=1.7, alt=3.0, heart=True, n=12)
    d2 = remains(0, stain=11.0, glass=14, glass_mats=("glass", "silver", "pale"), stain_mat="glass")
    corpse = remains(1, stain=12.0, glass=18, glass_mats=("glass", "silver", "pale"), stain_mat="glass",
                     extra=lambda r: r.ell(0.0, -2.0, 3.0, 1.6, "silver", 2.0))
    knock = G(phase=0.2, spread=1.2, lean=-14)
    anims = [("Idle", idle, [0.1, 0.1, 0.1, 0.1]), ("Run", run, [0.07] * 6),
             ("Bite", bt, [0.1, 0.1, 0.06, 0.1, 0.1, 0.1, 0.12]), ("Surge", sg, [0.08, 0.08, 0.06, 0.06, 0.06, 0.06, 0.1, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("UmbGlitterswarm", anims, outdir, scale=5)


# ================================================================== THE PENDULUM: a clock case with an eye for a face
def pendulum_blade(r, px, py, ang, z, ln=13.0, smear=0):
    """The glass blade on its rod from the pivot (px, py), swung ang degrees from straight down."""
    a = math.radians(90 + ang)
    ux, uy = math.cos(a), math.sin(a)
    rod_end = (px + ux * ln * 0.55, py + uy * ln * 0.55)
    r.line(px, py, *rod_end, "brass", z, tone=3)
    # a crescent blade across the rod's end
    qx, qy = -uy, ux
    c = (px + ux * ln, py + uy * ln)
    pts = [(rod_end[0] + qx * 6.0, rod_end[1] + qy * 6.0), (c[0] + qx * 4.0, c[1] + qy * 4.0), (c[0] + ux * 1.2, c[1] + uy * 1.2),
           (c[0] - qx * 4.0, c[1] - qy * 4.0), (rod_end[0] - qx * 6.0, rod_end[1] - qy * 6.0), (c[0] - ux * 1.6, c[1] - uy * 1.6)]
    r.poly(pts, "glass", z + 0.01, bias=0.2, normal=(-0.3, -0.4, 1.0))
    r.line(pts[0][0], pts[0][1], pts[2][0], pts[2][1], "white", z + 0.02, tone=4)
    r.dot(*rod_end, "brass", 4, z + 0.03)
    for k in range(smear):
        b = math.radians(90 + ang - (k + 1) * 12 * (1 if ang >= 0 else -1))
        r.dot(px + math.cos(b) * ln, py + math.sin(b) * ln, "glass", 3 - min(k, 1), z - 0.1)


def pendulum(alt=11.2, lean=0.0, blade=None, look=0.0, lid=0.0, hands=0.0, extra=None, dead=False, tick=0, door=0.0, bob=0.0,
             crack=False):
    """The case hovers alt px up; blade = swing angle (None: no blade, the effect draws it)."""
    r = Rig()
    by = -alt + bob
    T = Xf(lean, (0.0, by - 12.0))
    # the case: a tall wooden box with brass trim and a pediment
    box = [T(-6.0, by), T(6.0, by), T(6.0, by - 22.0), T(-6.0, by - 22.0)]
    # brass scrollwork wings either side of the dial, glass pennants on them
    for s in (-1, 1):
        sc = [T(s * 6.0, by - 19.0), T(s * 9.0, by - 21.0), T(s * 12.0, by - 19.0), T(s * 11.0, by - 16.0), T(s * 8.0, by - 15.0)]
        r.polyline(sc, "brass", -0.3 if s < 0 else 0.3, tones=[3, 3, 2, 2])
        r.poly([T(s * 9.0, by - 20.4), T(s * 13.5, by - 23.5), T(s * 12.0, by - 18.0)], "glass", -0.35 if s < 0 else 0.35, bias=0.2)
        r.dot(*T(s * 6.6, by - 23.4), "brass", 4, 0.3)                                        # finials
    for s in (-1, 1):
        r.line(*T(s * 6.6, by - 1.0), *T(s * 6.6, by - 21.0), "brass", 0.07, tone=2 if s < 0 else 1)
    r.poly(box, "wood", 0.0, curve=0.6)
    r.poly([T(-7.4, by - 21.0), T(7.4, by - 21.0), T(0.0, by - 27.0)], "wood", 0.05, bias=0.2, normal=(-0.2, -0.8, 0.8))
    r.line(*T(-7.4, by - 21.0), *T(0.0, by - 27.0), "brass", 0.06, tone=3)
    r.line(*T(0.0, by - 27.0), *T(7.4, by - 21.0), "brass", 0.06, tone=2)
    r.dot(*T(0.0, by - 27.0), "lilac", 4, 0.07)
    for y in (by, by - 22.0):
        r.line(*T(-5.6, y), *T(5.6, y), "brass", 0.06, tone=2)
    # the glass door (with the rod slot), a brass key
    r.poly([T(-3.0, by - 2.0), T(3.0, by - 2.0), T(3.0, by - 10.0), T(-3.0, by - 10.0)], "glass", 0.08, bias=0.1 + door)
    r.line(*T(0.0, by - 2.0), *T(0.0, by - 10.0), "brass", 0.09, tone=1)
    # the dial: bone with an eye for a hub
    dc = T(0.0, by - 15.6)
    r.ell(dc[0], dc[1], 5.4, 5.4, "brass", 0.1)
    r.ell(dc[0], dc[1], 4.4, 4.4, "bone", 0.11, bias=0.1)
    for k in range(12):
        a = k / 12 * math.tau
        r.dot(dc[0] + 3.2 * math.cos(a), dc[1] + 3.2 * math.sin(a), "void", 1 if k % 3 else 0, 0.12)
    if lid < 0.5:
        r.ell(dc[0] + look, dc[1], 1.8, 1.6, "lilac", 0.13, flat=3)
        r.dot(dc[0] + look, dc[1], "void", 0, 0.14); r.dot(dc[0] + look - 1, dc[1] - 1, "white", 4, 0.14)
    else:
        r.line(dc[0] - 2, dc[1], dc[0] + 2, dc[1], "void", 0.13, tone=1)
    # clock hands as lashes
    a = math.radians(-90 + hands * 30)
    r.line(dc[0], dc[1], dc[0] + 2.6 * math.cos(a), dc[1] + 2.6 * math.sin(a), "brass", 0.15, tone=4)
    if crack:
        r.polyline([T(-3, by - 20), T(-1, by - 16), T(-2, by - 13)], "white", 0.2, tone=3)
    # brass feet that dangle (it floats)
    for s in (-1, 1):
        r.line(*T(s * 4.0, by), *T(s * 4.6, by + 2.0), "brass", 0.2, tone=2)
    if blade is not None:
        pendulum_blade(r, *T(0.0, by), blade, 1.0, ln=11.0)
    if tick:
        for (dx, dy) in ((-8, -26), (8, -26)):
            r.dot(dx, by + dy + 4, "lilac", 4 if tick == 1 else 3, 6.0)
    if not dead: floor_shadow(r, 0.0, 6.0)
    if extra: extra(r)
    return r.resolve()


def pendulum_sheet(outdir):
    P = pendulum
    # Idle and Run (8 frames, 2 s): the blade swings by itself, right then left, crossing the middle on each whole second
    swing = [0, 28, 42, 28, 0, -28, -42, -28]
    idle = [P(bob=[0, -0.3, -0.5, -0.3][i % 4], look=[0, 0.4, 0.8, 0.4][i % 4], hands=i // 2, blade=swing[i]) for i in range(8)]
    run = [P(lean=8, bob=-0.4 * abs(math.sin(i)), look=1.0, hands=i // 2, blade=swing[i]) for i in range(8)]
    # Swing (7): the heavy swing goes all the way round: wind back (0-1), round (2-4: HIT on 3), settle (5-6)
    sw = [P(blade=-60, look=1.0), P(blade=-110, look=1.0, lean=-6), P(blade=0, look=1.0, lean=4, crack=False, extra=None),
          P(blade=120, look=1.0, lean=8), P(blade=230, look=0.6, lean=4), P(blade=330, look=0.3), P(blade=360, look=0.0)]
    # Stop (8): the eye shuts (0-1), the hands spin back (2-5), the eye opens wide (6), (7)
    sp = [P(lid=0.6, blade=0), P(lid=1.0, blade=0, hands=-1), P(lid=1.0, hands=-3, tick=1, blade=0), P(lid=1.0, hands=-5, tick=2, blade=0),
          P(lid=1.0, hands=-7, tick=1, blade=0), P(lid=1.0, hands=-9, blade=0), P(look=0.0, blade=0, extra=lambda r: twinkle(r, 0, -24, 1)), P(blade=0)]
    d0 = P(lean=-12, lid=1.0, blade=-40, crack=True)
    d1 = P(alt=3.0, lean=-40, lid=1.0, blade=-80, crack=True, dead=True)
    d2 = remains(0, stain=12.0, glass=8, glass_mats=("glass", "brass"), stain_mat="wood",
                 extra=lambda r: r.poly([(-10, -1), (8, -1), (8, -5), (-10, -5)], "wood", 1.0))
    corpse = remains(1, stain=13.0, glass=12, glass_mats=("glass", "brass"), stain_mat="wood",
                     extra=lambda r: (r.poly([(-10, -0.5), (9, -0.5), (9, -4.5), (-10, -4.5)], "wood", 1.0),
                                      r.ell(5.0, -2.6, 2.0, 1.6, "bone", 1.1), pendulum_blade(r, -12.0, -2.0, -80, 1.2)))
    portrait = P(blade=0)
    knock = P(lean=-14, lid=1.0)
    anims = [("Idle", idle, [0.25] * 8), ("Run", run, [0.25] * 8),
             ("Swing", sw, [0.12, 0.12, 0.05, 0.05, 0.06, 0.1, 0.12]),
             ("Stop", sp, [0.1, 0.1, 0.08, 0.08, 0.08, 0.1, 0.12, 0.12])]
    anims += [("Death", [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4]), ("Dead", [corpse], [0.3]),
              ("Statue", [J.stone(portrait)], [0.2]), ("Knockback", [knock], [0.2]), ("Portrait", [portrait], [0.2])]
    return sheet("UmbPendulum", anims, outdir, scale=5)


# ================================================================== SAND WRAITH: a robed wraith of falling sand
def sand_wraith(lean=0.0, bob=0.0, hand=None, hand2=None, pour=1, glass_fill=0.5, face=True, extra=None, flow=0, hood=0.0,
                crumble=0.0, dx=0.0, held=True):
    """A robed wraith of falling sand holding a great hourglass up in its far hand (held=False: the hand is empty)."""
    r = SRig(1.0)
    hip = (dx, -12.0 + bob)
    T = Xf(lean, hip)
    # the lower body: a falling column of sand pooling on the floor
    rnd = random.Random(70 + flow)
    r.ell(dx, -1.2, 7.0 + crumble * 4, 1.8 + crumble, "sand", -1.0, bias=0.1)
    col = [T(dx - 3.6, hip[1] - 2.0), T(dx + 3.8, hip[1] - 2.0), T(dx + 2.6, -1.2), T(dx - 2.4, -1.2)]
    if crumble < 0.9:
        r.poly(col, "sand", -0.5, curve=0.8, bias=-0.1)
        for i in range(10):
            y = hip[1] + rnd.uniform(0, -hip[1] - 1)
            x = dx + rnd.uniform(-2.4, 2.4)
            r.dot(x, y, "sandl", 3 if i % 3 else 4, -0.4)
    # robe over the shoulders (dark, ragged), hood
    robe = [T(hip[0] - 5.0, hip[1] - 1.0), T(hip[0] - 3.6, hip[1] - 12.0), T(hip[0] + 3.8, hip[1] - 12.0), T(hip[0] + 5.4, hip[1] - 1.0),
            T(hip[0] + 3.0, hip[1] + 2.0), T(hip[0] + 1.0, hip[1]), T(hip[0] - 1.6, hip[1] + 2.6), T(hip[0] - 3.4, hip[1])]
    r.poly(robe, "robe", 0.0, curve=0.8)
    # sand runs down the robe in streams and trails off the hem
    for i, x in enumerate((-3.0, -0.6, 1.8, 4.0)):
        top = hip[1] - 10.0 + (i % 2) * 2.0
        for j in range(int(-top + hip[1] + 2)):
            y = top + j
            if (j + flow + i) % 4 == 0: continue
            r.dot(*T(hip[0] + x + 0.15 * math.sin(y * 0.7 + i), y), "sandl" if (j + flow) % 3 else "sand", 3, 0.05)
    for k in range(5):
        r.dot(hip[0] - 4.0 - k * 1.2, hip[1] + 1.0 + k * 0.6 + (flow + k) % 2, "sandl", 3 if k < 3 else 2, -0.3)
    r.ell(*T(hip[0] + 0.6, hip[1] - 7.0), 1.6, 1.8, "sandl", 0.1, flat=3)                    # the heart of falling sand
    hd = T(hip[0] + 1.0, hip[1] - 15.4)
    r.poly([(hd[0] - 4.0, hd[1] + 3.6), (hd[0] - 3.4, hd[1] - 2.6), (hd[0] - 1.0 - hood, hd[1] - 5.0), (hd[0] + 3.0, hd[1] - 3.0),
            (hd[0] + 4.2, hd[1] + 3.6)], "robe", 1.0, curve=0.6)
    r.ell(hd[0] + 1.0, hd[1] + 0.6, 2.4, 2.6, "sand", 1.1, bias=-0.35)
    if face:
        r.dot(hd[0] + 0.4, hd[1], "sandl", 4, 1.2); r.dot(hd[0] + 2.2, hd[1], "sandl", 4, 1.2)
    # arms in wide sleeves; sand pours from them
    sh_n, sh_f = T(hip[0] + 3.4, hip[1] - 10.6), T(hip[0] - 3.0, hip[1] - 10.8)
    h2 = hand2 or T(hip[0] - 6.0, hip[1] - 9.4)
    if held:
        # the great hourglass, held up by its bottom cap
        hourglass_body(r, h2[0] - 0.4, h2[1] - 8.4, -0.7, glass_fill, 1.0 - glass_fill, 0.0, "open", stream=True)
    for k, (sh, h, z) in enumerate(((sh_f, h2, -0.6), (sh_n, hand or T(hip[0] + 7.0, hip[1] - 3.0), 3.0))):
        e = ik(sh[0], sh[1], h[0], h[1], 4.2, 4.2, bend=1 if k == 0 else -1)
        r.tube([sh, e], [1.8, 2.0], "robe", z, bias=-0.3 if k == 0 else 0.1)
        r.tube([e, h], [2.0, 2.6], "robe", z + 0.01, bias=-0.3 if k == 0 else 0.1)
        if pour:
            for i in range(4 + pour):
                y = h[1] + 1.0 + i * 1.6
                if y > -0.5: break
                r.dot(h[0] + 0.4 + (i % 2) * 0.6, y, "sandl", 3 if i % 2 else 4, z + 0.02)
    if extra: extra(r)
    return r.resolve()


def wraith_sheet(outdir):
    W = sand_wraith
    idle = [W(bob=[0, -0.3, -0.5, -0.3][i], flow=i, glass_fill=0.55 - 0.02 * i) for i in range(4)]
    run = [W(lean=10, bob=-0.4 * abs(math.sin(i)), flow=i + 4, hand=(8.0, -6.0), hand2=(-5.0, -21.0 + 0.5 * math.sin(i))) for i in range(6)]
    # Fist (6): gather sand in the fist (0-1), hurl (2 = release), (3-5)
    fi = [W(hand=(2.0, -20.0), lean=-6, pour=2), W(hand=(-1.0, -22.0), lean=-10, pour=0,
                                                  extra=lambda r: r.ell(-1.0, -24.0, 2.4, 2.2, "sand", 4.0)),
          W(hand=(11.0, -14.0), lean=12, pour=0, dx=1.0, extra=lambda r: [r.dot(5 + i * 2, -22 + i * 2, "sandl", 3, 5) for i in range(3)]),
          W(hand=(10.0, -10.0), lean=8, pour=1), W(hand=(8.0, -7.0), lean=3), W()]
    # TimeOut (8): both arms rise (0-2), the glass in its chest flips (3), an hourglass is cast up (4 = cast), (5-7)
    to = [W(hand=(6.0, -18.0), hand2=(-6.0, -18.0), pour=2), W(hand=(5.0, -24.0), hand2=(-5.0, -24.0), pour=2, hood=1.0),
          W(hand=(4.0, -27.0), hand2=(-4.0, -27.0), pour=3, hood=1.5, glass_fill=0.8),
          W(hand=(4.0, -27.0), hand2=(-4.0, -27.0), pour=3, hood=1.5, glass_fill=0.2, extra=lambda r: twinkle(r, 0, -32, 1, mat="sandl")),
          W(hand=(10.0, -20.0), hand2=(-2.0, -22.0), lean=8, pour=2, glass_fill=0.3, held=False,
            extra=lambda r: hourglass_body(r, 14.0, -26.0, 6.0, 0.9, 0.1, 0.0, "open", stream=True)),
          W(hand=(8.0, -14.0), hand2=(-5.0, -10.0), lean=4, glass_fill=0.35, held=False), W(glass_fill=0.45), W()]
    d0 = W(lean=-12, face=False, hand=(4.0, -20.0), hand2=(-7.0, -16.0), pour=3)
    d1 = W(lean=-20, bob=4.0, face=False, crumble=0.5, pour=4, hand=(6.0, -8.0), hand2=(-7.0, -6.0))
    d2 = remains(0, stain=10.0, glass=6, glass_mats=("glass", "sandl"), stain_mat="sand",
                 extra=lambda r: (r.ell(0.0, -2.0, 8.0, 3.0, "sand", 0.5), hourglass_body(r, 2.0, -5.0, 2.0, 0.2, 0.2, 80, "shut", stream=False)))
    corpse = remains(1, stain=11.0, glass=8, glass_mats=("glass", "sandl"), stain_mat="sand",
                     extra=lambda r: (r.ell(0.0, -1.6, 9.0, 2.4, "sand", 0.5), hourglass_body(r, 3.0, -4.6, 2.0, 0.0, 0.0, 90, "shut",
                                                                                               stream=False, crack=True)))
    knock = W(lean=-16, face=False, hand=(4.0, -18.0), hand2=(-7.0, -15.0))
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.08] * 6),
             ("Fist", fi, [0.12, 0.12, 0.06, 0.1, 0.1, 0.12]),
             ("TimeOut", to, [0.1, 0.1, 0.12, 0.1, 0.08, 0.1, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("UmbSandWraith", anims, outdir, scale=5)


JOBS = [("UmbHollowKing", king_sheet), ("UmbSundered", sundered_sheet), ("UmbGlassSeraph", seraph_sheet),
        ("UmbBristleback", bristle_sheet), ("UmbUnblinking", eye_sheet), ("UmbGlassWidow", widow_sheet),
        ("UmbEclipseWyrm", wyrm_sheet), ("UmbUndertow", undertow_sheet), ("UmbArgusMoth", argus_sheet),
        ("UmbGlitterswarm", swarm_sheet), ("UmbPendulum", pendulum_sheet), ("UmbSandWraith", wraith_sheet)]
