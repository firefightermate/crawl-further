"""Zhekra effect sheets, the god portrait and the gold idol, drawn with the same material renderer as the monsters
(zhekra_v2_rigs.py). Each sheet's origin (the pixel Strike.ArtAt pins to the effect's position, or the bottom centre for
status overlays) is listed in TIMING.md. Coordinates below are pixels from that origin, y up negative. The Acid Pool,
Resin, Glue Field, Egg, Acid Rain, Glue Shell and Resin Burst keep their frame counts and durations (item effects and
templates time themselves from them)."""
import math, random
from zhekra_v2_rigs import (Rig, Xf, chain, lerp, line_px, eye, mandible, wing, dust, smear, splat, drip, puddle, arc_pts,
                            fx, done, NOTES, BUILT)
from zhekra_v2_t2 import amber_ball, acid_sac
from zhekra_v2_t3b import sun_ball


def R():
    return Rig()


def blob(r, x, y, rx, ry, mat, z=0.0, glint=True, flat=None, ang=0.0):
    r.ell(x, y, rx, ry, mat, z, ang=ang, bias=0.25, flat=flat)
    if glint and rx >= 1.2: r.dot(x - rx * 0.4, y - ry * 0.4, mat, 4, z + 0.01)


def ring(r, cx, cy, rx, ry, mat, tone, z=0.0, n=40, step=1, gap=None):
    for i in range(n):
        if i % step: continue
        a = i / float(n) * math.tau
        if gap and gap(a): continue
        r.dot(cx + rx * math.cos(a), cy + ry * math.sin(a), mat, tone, z)


# ------------------------------------------------------------------ projectiles (fly to the right)
def fx_projectiles(outdir):
    # Acid Spit: a wobbling glob with a dripping tail
    fr = []
    for k in range(4):
        r = R(); blob(r, 3.0, -0.2 + [0, -0.3, 0, 0.3][k], 2.4 + [0, 0.3, 0, -0.2][k], 2.0, "acid")
        r.ell(3.4, 0.2, 1.2, 1.0, "aglow", 0.01, flat=3)
        for j in range(3): r.dot(-1 - j * 2.0, [0, 1, -1][(j + k) % 3] * 0.6, "aglow", 3 - j % 2, 0.0)
        r.dot(1 - k % 2, 2, "aglow", 2, 0.0)
        fr.append(done(r))
    fx("FxZhkAcidSpit", (24, 8), (12, 4), [("Fly", fr, [0.07] * 4)], outdir)
    # Drone dart: a black needle, an acid tip, a buzz streak
    def needle(name, body, tip, glow, cell):
        frs = []
        for k in range(4):
            r = R()
            r.line(-5, 0, 4, 0, body, 1.0, tone=2)
            r.line(-5, -1 if k % 2 else 1, -2, -1 if k % 2 else 1, body, 1.0, tone=1)
            r.dot(5, 0, tip, 3, 1.1); r.dot(6, 0, tip, 4, 1.1)
            for j in range(3 + k % 2): r.dot(-7 - j * 2, 0, glow, 2 if j == 0 else 1, 0.5)
            frs.append(done(r))
        fx(name, cell, (cell[0] // 2, cell[1] // 2), [("Fly", frs, [0.05] * 4)], outdir)
    needle("FxZhkStinger", "hblk", "aglow", "wblur", (26, 6))
    needle("FxZhkHornetStinger", "hblk", "amber", "hyel", (26, 6))
    # Mark dart: a glowing amber dart leaving a scent trail
    fr = []
    for k in range(4):
        r = R()
        r.ell(2.0, 0.0, 2.6, 1.2, "jelly", 1.0, flat=3); r.dot(4.5, 0, "jelly", 4, 1.1)
        for j in range(5): r.dot(-2 - j * 2, [0, -1, 0, 1][(j + k) % 4] * 0.7, "jelly", 3 if j < 2 else 2, 0.5)
        fr.append(done(r))
    fx("FxZhkMarkDart", (28, 6), (14, 3), [("Fly", fr, [0.06] * 4)], outdir)
    # Glue speck
    fr = []
    for k in range(4):
        r = R(); blob(r, 1.0, 0.0, 1.8, 1.5 + 0.2 * (k % 2), "glue")
        r.dot(-2, 0, "glue", 2, 0.0); r.dot(-4, (k % 2), "glue", 1, 0.0)
        fr.append(done(r))
    fx("FxZhkGlueJet", (18, 7), (9, 3), [("Fly", fr, [0.05] * 4)], outdir)
    # Egg dart: a pale egg with a slime tail
    fr = []
    for k in range(4):
        r = R(); blob(r, 2.0, 0.0, 2.6, 1.7, "cream")
        r.dot(1.2 + k * 0.4, -0.4, "aglow", 3, 0.02)
        for j in range(4): r.dot(-2 - j * 2, (j + k) % 2 * 0.8 - 0.4, "glue", 2, 0.0)
        fr.append(done(r))
    fx("FxZhkEggDart", (22, 7), (11, 3), [("Fly", fr, [0.07] * 4)], outdir)
    # Droplet
    fr = []
    for k in range(4):
        r = R(); blob(r, 0.5, 0.0, 1.4, 1.1, "acid", glint=False); r.dot(-1.5, 0, "aglow", 2, 0.0)
        fr.append(done(r))
    fx("FxZhkDroplet", (8, 5), (4, 2), [("Fly", fr, [0.06] * 4)], outdir)
    # Bubble: a slow quivering acid bubble
    fr = []
    for k in range(6):
        r = R(); w = 0.3 * math.sin(k / 6 * math.tau)
        r.ell(0, 0, 4.4 + w, 4.2 - w, "acid", 0.0, flat=1)
        r.ell(0, 0, 3.4 + w, 3.2 - w, "aglow", 0.01, flat=1)
        r.ell(0.4, 0.6, 2.0, 1.6, "aglow", 0.02, flat=2)
        r.dot(-2, -2, "white", 4, 0.03); r.dot(-1, -3, "white", 3, 0.03)
        fr.append(done(r))
    fx("FxZhkBubble", (18, 12), (9, 6), [("Fly", fr, [0.1] * 6)], outdir)
    # the Amber Scarab's rolling resin ball, three sizes
    anims = []
    for size, Rr in ((1, 2.8), (2, 3.9), (3, 4.9)):
        frs = []
        for k in range(6):
            r = R(); amber_ball(r, 0.0, 0.0, Rr, 0.0, rot=k * 60)
            dust(r, -Rr - 2, 0, k % 3, w=0.6, n=2)
            frs.append(done(r))
        anims.append(("Fly%d" % size, frs, [0.06] * 6))
    fx("FxZhkRollBall", (26, 14), (13, 12), anims, outdir)
    # the Sun Scarab's fossil ball, 0-3 larvae inside
    anims = []
    for lv in range(4):
        frs = []
        for k in range(6):
            r = R(); sun_ball(r, 0.0, 0.0, 7.0, 0.0, rot=k * 60, larvae=lv)
            dust(r, -9, 0, k % 3, w=0.7, n=2)
            frs.append(done(r))
        anims.append(("Fly%d" % lv, frs, [0.06] * 6))
    fx("FxZhkFossilBall", (32, 18), (16, 16), anims, outdir)
    # the floor-skimming lobs: the acid glob (drawn up at the Spitter's spout) and the resin glob (the Beetle's jaws)
    fr = []
    for k in range(4):
        r = R(); blob(r, 0.0, -17.0 + [0, -0.4, 0, 0.4][k], 2.8, 2.4, "acid"); r.ell(0.4, -16.6, 1.4, 1.2, "aglow", 0.01, flat=3)
        for j in range(3): r.dot(-3 - j * 2, -17 + j * 0.8, "aglow", 3 - j % 2, 0.0)
        r.ell(0, -0.5, 2.0, 0.6, "dchit", -1.0, flat=1)
        fr.append(done(r))
    fx("FxZhkAcidGlob", (28, 24), (14, 22), [("Fly", fr, [0.08] * 4)], outdir)
    fr = []
    for k in range(4):
        r = R(); blob(r, 0.0, -4.0 + [0, -0.3, 0, 0.3][k], 2.2, 1.8, "amber")
        r.dot(-3, -4, "amber", 3, 0.0); r.dot(-5, -3.5, "amber", 2, 0.0)
        r.ell(0, -0.5, 1.6, 0.5, "dchit", -1.0, flat=1)
        fr.append(done(r))
    fx("FxZhkResinGlob", (18, 12), (9, 10), [("Fly", fr, [0.08] * 4)], outdir)
    # the hornet swarm cloud: a knot of hornets buzzing round a centre
    fr = []
    for k in range(6):
        r = R(); rnd = random.Random(3)
        for j in range(7):
            a = rnd.uniform(0, math.tau) + k * 0.5 * (1 if j % 2 else -1); d = rnd.uniform(1.5, 6.0)
            x, y = d * math.cos(a), -6.5 + d * 0.8 * math.sin(a)
            r.ell(x, y, 1.1, 0.7, "hyel", 1.0, flat=3); r.dot(x - 1, y, "hblk", 1, 1.01); r.dot(x, y - 1, "white", 2, 1.02)
        r.ell(0, -0.4, 4.0, 0.8, "dchit", -1.0, flat=1)
        fr.append(done(r))
    fx("FxZhkSwarmCloud", (18, 14), (9, 13), [("Loop", fr, [0.07] * 6)], outdir)


# ------------------------------------------------------------------ floor puddles and their lifetimes
def floor_life(name, cell, origin, mat, edge, w, spread_d, idle_n, idle_d, fade_d, idle_frames=4, glint="white", out=None):
    """Spread (3) + Idle (looped idle_n frames) + Fade (3) and the same pieces on their own."""
    def pud(k, scale, ph, fade=0):
        r = R()
        rnd = random.Random(5)
        ww = w * scale
        hh = ww * 0.34 if w < 12 else ww * 0.22
        r.ell(0, -0.6, ww, hh, mat, 0.0, flat=2 if not fade else 1)
        r.ell(-ww * 0.2, -0.9, ww * 0.55, hh * 0.47, mat, 0.01, flat=3 if fade < 2 else 2)
        if edge: ring(r, 0, -0.6, ww, hh, edge, 2 if not fade else 1, 0.005, n=int(ww * 4), step=1 + fade)
        for j in range(3):
            if (j + ph) % 3 == 0 and not fade:
                r.dot(-ww * 0.5 + rnd.uniform(0, ww), -0.8 + rnd.uniform(-0.5, 0.5), glint, 3, 0.02)
        return done(r)
    spread = [pud(0, s, 0) for s in (0.45, 0.75, 1.0)]
    idle = [pud(0, 1.0, k) for k in range(idle_frames)]
    fade = [pud(0, s, 0, f) for s, f in ((0.95, 1), (0.8, 2), (0.6, 2))]
    life = spread + [idle[k % idle_frames] for k in range(idle_n)] + fade
    anims = [("Life", life, list(spread_d) + [idle_d] * idle_n + list(fade_d)), ("Spread", spread, list(spread_d)),
             ("Idle", idle, [idle_d] * idle_frames), ("Fade", fade, list(fade_d))]
    fx(name, cell, origin, anims, out)


def fx_floor(outdir):
    floor_life("FxZhkAcidPool", (26, 10), (13, 6), "acid", "aglow", 11.0, (0.1, 0.1, 0.1), 12, 0.2, (0.13, 0.13, 0.13), glint="aglow", out=outdir)
    floor_life("FxZhkAcidPoolWide", (48, 16), (24, 9), "acid", "aglow", 22.0, (0.1, 0.1, 0.1), 12, 0.2, (0.13, 0.13, 0.13), glint="aglow", out=outdir)
    floor_life("FxZhkResin", (26, 10), (13, 6), "amber", None, 11.0, (0.1, 0.1, 0.1), 16, 0.22, (0.15, 0.15, 0.15), idle_frames=2, glint="jelly", out=outdir)
    floor_life("FxZhkGlueField", (32, 12), (16, 7), "glue", None, 14.0, (0.1, 0.1, 0.1), 12, 0.2, (0.15, 0.15, 0.15), idle_frames=3, out=outdir)
    # the Hive's amber drips: a small puddle that wells up, sits and fades (6 s)
    fr = []
    for k in range(8):
        r = R(); s = [0.4, 0.7, 1.0, 1.0, 1.0, 1.0, 0.8, 0.5][k]
        r.ell(0, -0.6, 5.0 * s, 1.6 * s, "amber", 0.0, flat=2 if k < 6 else 1)
        r.ell(-1, -0.8, 2.4 * s, 0.6 * s, "amber", 0.01, flat=4 if k < 6 else 2)
        if k in (2, 4): r.dot(1, -2, "jelly", 3, 0.02)
        fr.append(done(r))
    fx("FxZhkDrip", (14, 6), (7, 3), [("Life", fr, [0.1, 0.1, 0.4, 1.2, 1.2, 1.5, 0.8, 0.6])], outdir)
    # the scent prints a Marked hero leaves (4 s): two little glowing feet that fade
    fr = []
    for k in range(6):
        r = R(); t = [3, 4, 3, 3, 2, 1][k]
        for (x, y) in ((-1.5, -0.5), (1.5, 0.5)):
            r.ell(x, y - 0.5, 1.0, 0.6, "jelly", 0.0, flat=t)
            r.dot(x + 1, y - 1, "jelly", max(1, t - 1), 0.01)
        fr.append(done(r))
    fx("FxZhkPrints", (8, 5), (4, 3), [("Life", fr, [0.1, 0.6, 1.0, 1.0, 0.8, 0.5])], outdir)
    # the Sand Pit: 60 px across, a raised sand rim round a dark funnel; the floor shows through the hollow middle.
    # Open, Loop (grains slide down the inner wall), Close
    def pit(scale, ph, close=0.0):
        r = R(); W, H = 30.0 * scale, 12.0 * scale
        rnd = random.Random(5)
        for yy in range(-int(H) - 1, int(H) + 2):
            for xx in range(-int(W) - 1, int(W) + 2):
                e = math.hypot(xx / W, yy / H)
                if e > 1.0: continue
                far = yy < 0                         # the far wall faces the viewer and catches the light
                if e > 0.8:                           # the rim crest
                    t = 4 if (far and e < 0.88) else 3 if far else 2
                    if rnd.random() < 0.12: t -= 1
                    r.dot(xx, yy, "sand", t, 0.0)
                elif e > 0.6:                         # the inner wall sloping down
                    t = 2 if far else 1
                    if rnd.random() < 0.15: t -= 1
                    r.dot(xx, yy, "sand", max(0, t), 0.01)
                elif e > 0.42:                        # the dark throat
                    r.dot(xx, yy, "dchit", 0 if far else 1, 0.02)
                elif e > 0.3 and (xx + yy) % 2 == 0:  # the hollow fading out to the floor
                    r.dot(xx, yy, "dchit", 0, 0.02)
        # grains sliding down the inner wall into the throat (they move with ph)
        for j in range(14):
            a = j / 14.0 * math.tau + 0.2
            f = ((ph * 0.22 + j * 0.37) % 1.0)
            e = 0.88 - 0.42 * f
            r.dot(W * e * math.cos(a), H * e * math.sin(a), "sand", 4 if f < 0.5 else 3, 0.06)
        if close: ring(r, 0, 0, W, H, "dust", 2, 0.07, n=48, step=2)
        return done(r)
    op = [pit(s, 0) for s in (0.3, 0.6, 0.85, 1.0)]
    lp = [pit(1.0, k) for k in range(4)]
    cl = [pit(s, 0, close=1) for s in (1.0, 0.8, 0.55, 0.3)]
    fx("FxZhkPit", (66, 30), (33, 15), [("Open", op, [0.08] * 4), ("Loop", lp, [0.15] * 4), ("Close", cl, [0.12] * 4)], outdir)


# ------------------------------------------------------------------ impacts, bursts, drops
def fx_bursts(outdir):
    def splash(name, mat, glow, cell, origin, spread, n, durs, base_w=None, root=False):
        frs = []
        for k in range(len(durs)):
            r = R()
            if base_w: r.ell(0, -0.6, base_w * min(1.0, 0.4 + k * 0.3), base_w * 0.3 * min(1.0, 0.4 + k * 0.3), mat, 0.0, flat=2 if k < 3 else 1)
            rnd = random.Random(9)
            for j in range(n):
                a = rnd.uniform(-math.pi, 0.0); d = spread * (0.35 + 0.65 * rnd.random()) * min(1.0, 0.35 + k * 0.3)
                x, y = d * math.cos(a), d * math.sin(a) * 0.7 + k * k * 0.25
                if k < len(durs) - 1 or j % 2:
                    r.dot(x, min(-0.0, y), glow if j % 3 == 0 else mat, 4 if k < 2 else 3 - (k > 3), 1.0)
                    if k < 2: r.dot(x - math.cos(a), min(0.0, y - math.sin(a) * 0.7), mat, 2, 0.9)
            if k == 0: r.ell(0, -1.5, 3.0, 2.0, glow, 1.1, flat=4)
            frs.append(done(r))
        fx(name, cell, origin, [("Play", frs, durs)], outdir)
    splash("FxZhkSplash", "acid", "aglow", (30, 12), (15, 10), 12.0, 14, [0.05, 0.06, 0.07, 0.08, 0.1], base_w=6.0)
    splash("FxZhkSacBurst", "acid", "aglow", (44, 22), (22, 17), 20.0, 26, [0.04, 0.05, 0.06, 0.08, 0.1, 0.12], base_w=14.0)
    splash("FxZhkResinBurst", "amber", "jelly", (32, 14), (16, 8), 14.0, 16, [0.05, 0.06, 0.07, 0.09, 0.12], base_w=10.0)
    splash("FxZhkFossilCrack", "amber", "jelly", (34, 22), (17, 18), 15.0, 20, [0.04, 0.05, 0.07, 0.09, 0.12, 0.14], base_w=9.0)
    # bubble pop: a ring of spray
    frs = []
    for k in range(5):
        r = R(); R_ = 3 + k * 2.4
        ring(r, 0, -6, R_, R_ * 0.8, "aglow" if k < 2 else "acid", 4 - min(2, k), 1.0, n=24, step=1 + k // 2)
        if k == 0: r.ell(0, -6, 3, 3, "aglow", 1.1, flat=4)
        frs.append(done(r))
    fx("FxZhkBubblePop", (30, 22), (15, 16), [("Play", frs, [0.04, 0.05, 0.06, 0.08, 0.1])], outdir)
    # the Beetle's shove skid and the Uproot landing (dust)
    frs = []
    for k in range(4):
        r = R(); dust(r, 0, 0, min(2, k), w=1.2 - k * 0.1)
        for j in range(3 - k // 2): r.line(-4 - j * 2 - k * 2, -1 + j % 2, -1 - j * 2 - k * 2, -1 + j % 2, "dust", 0.5, tone=2)
        frs.append(done(r))
    fx("FxZhkSkid", (24, 9), (12, 7), [("Play", frs, [0.05, 0.07, 0.09, 0.1])], outdir)
    frs = []
    for k in range(6):
        r = R(); dust(r, 0, 0, min(2, k // 2), w=1.2 + 0.22 * k, n=4)
        if k < 2: ring(r, 0, -0.5, 6 + k * 5, 2 + k, "dust", 3, 0.5, n=30, step=2)
        frs.append(done(r))
    fx("FxZhkTossLand", (48, 16), (24, 12), [("Play", frs, [0.05, 0.06, 0.07, 0.08, 0.1, 0.12])], outdir)
    frs = []
    for k in range(5):
        r = R(); dust(r, 0, 0, min(2, k // 2), w=1.2 + 0.2 * k, n=4, mat="sand")
        for j in range(4): r.dot((j - 1.5) * (3 + k * 2), -2 - (3 - k) * (j % 2), "sand", 3, 1.0)
        frs.append(done(r))
    fx("FxZhkDirt", (46, 12), (23, 9), [("Play", frs, [0.06, 0.07, 0.08, 0.09, 0.1])], outdir)
    # the falling drops: a target ring blooms while the drop falls; it splats on frame 4
    def drop(name, cell, origin, mat, glow, ball=None):
        frs = []
        for k in range(7):
            r = R()
            if k < 4:
                ring(r, 0, -0.5, 4 + k * 1.5, 1.6 + k * 0.5, glow, 2 + (k > 1), 0.0, n=26, step=2 if k < 2 else 1)
                y = -36 + k * 10.5
                if ball: ball(r, y)
                else:
                    blob(r, 0, y, 2.2, 2.8, mat); r.dot(0, y - 4, glow, 2, 0.0)
            else:
                kk = k - 4
                r.ell(0, -0.6, 6 + kk * 1.5, 2.0 + kk * 0.3, mat, 0.0, flat=2)
                splat(r, 0, -1, kk, 1.0, mat=glow, n=8, spread=6 + kk * 2)
            frs.append(done(r))
        fx(name, cell, origin, [("Play", frs, [0.12, 0.12, 0.12, 0.1, 0.06, 0.1, 0.12])], outdir)
    drop("FxZhkAcidRain", (22, 45), (11, 40), "acid", "aglow")
    drop("FxZhkGlueShell", (24, 47), (12, 43), "glue", "glue", ball=lambda r, y: [blob(r, 0, y, 2.6, 2.6, "glue"), r.dot(0, y - 4, "dust", 2, 0.0)])
    drop("FxZhkHurl", (24, 47), (12, 43), "amber", "jelly", ball=lambda r, y: amber_ball(r, 0, y + 4, 3.9, 0.0, rot=y * 8))
    # the larva bursting out of an implanted hero (Hatchery)
    frs = []
    for k in range(7):
        r = R()
        if k < 3:
            splat(r, 0, -5, k, 1.0, mat="glue", n=8, spread=4 + k * 2)
            r.ell(0, -5 + k, 1.6, 2.0 - k * 0.4, "cream", 1.1, bias=0.2)
        else:
            x = (k - 3) * 2.0
            r.ell(x, -1.4, 2.4, 1.3, "cream", 1.0, bias=0.2); r.dot(x + 2.4, -1.6, "amber", 2, 1.01)
            if k < 5: splat(r, 0, -2, 2, 1.0, mat="glue", n=4, spread=5)
        frs.append(done(r))
    fx("FxZhkImplantBurst", (22, 13), (11, 11), [("Play", frs, [0.08, 0.08, 0.05, 0.08, 0.08, 0.1, 0.12])], outdir)


# ------------------------------------------------------------------ eggs, plates, heals, swarms
def fx_misc(outdir):
    # the egg: Life (laid, wobbles, hatches), Hatch (a corpse bursting into an egg that cracks at once)
    def egg(r, crack=0, wob=0.0, open_=0.0):
        r.ell(wob, -3.6, 3.0, 3.6, "cream", 0.0, bias=0.2)
        r.dot(-1 + wob, -5.6, "cream", 4, 0.01); r.dot(0.6 + wob, -2.2, "aglow", 2, 0.01)
        if crack:
            r.polyline([(-1 + wob, -6.6), (0 + wob, -4.6), (1 + wob, -5.4), (2 + wob, -3.2)][:crack + 1], "dchit", 0.02, tones=[0] * crack)
        if open_:
            r.ell(wob, -6.5, 2.4 * open_, 1.0, "glue", 0.03, flat=4)
    life = []
    for k in range(11):
        r = R()
        if k < 8: egg(r, crack=max(0, k - 4), wob=[0, 0, 0.5, -0.5, 0.6, -0.6, 0.8, -0.8][k])
        else:
            egg(r, crack=3, open_=1.0 if k == 8 else 0.0)
            splat(r, 0, -6, k - 8, 1.0, mat="glue", n=6, spread=4)
            if k > 8: r.ell(2.0 + (k - 9) * 1.5, -1.4, 2.2, 1.2, "cream", 1.0, bias=0.2)
        life.append(done(r))
    # Hatch: goo wells up (0), sets into an egg (1), cracks (2, 3), the cap pops (4), the shell lies open (5)
    hatch = []
    for k in range(6):
        r = R()
        if k == 0:
            r.ell(0, -1.0, 4.0, 1.4, "glue", 0.0, bias=0.2); r.ell(0, -2.4, 2.0, 2.0, "cream", 0.01, bias=0.2)
            r.dot(-2.6, -3.0, "glue", 3, 0.02); r.dot(2.8, -2.4, "glue", 3, 0.02)
        elif k < 4:
            r.ell(0, -0.5, 3.6, 0.9, "glue", -0.1, flat=2)
            egg(r, crack=(0, 0, 2, 3)[k], wob=(0, 0, 0.5, -0.5)[k])
            if k == 3: r.dot(0.2, -5.0, "aglow", 4, 0.05)
        else:
            r.ell(0, -0.5, 3.6, 0.9, "glue", -0.1, flat=2)
            # the bottom half of the shell, jagged rim, and the cap flipped off to the side
            r.ell(0, -2.0, 3.0, 2.0, "cream", 0.0, bias=0.2)
            r.polyline([(-3, -3.4), (-1.6, -4.4), (-0.4, -3.6), (0.8, -4.6), (2.0, -3.6), (3, -3.8)], "cream", 0.02, tone=4)
            r.ell(0, -3.6, 2.2, 0.7, "glue", 0.03, flat=3 if k == 4 else 2)
            cx = 4.4 if k == 4 else 5.2; cy = -6.5 if k == 4 else -1.4
            r.ell(cx, cy, 1.8, 1.2, "cream", 0.04, bias=0.25, ang=30 if k == 4 else 160)
            if k == 4:
                r.dot(-2.0, -6.0, "glue", 3, 0.05); r.dot(1.6, -7.0, "glue", 3, 0.05)
        hatch.append(done(r))
    fx("FxZhkEgg", (16, 11), (8, 10), [("Hatch", hatch, [0.1, 0.1, 0.1, 0.08, 0.08, 0.1]),
                                       ("Life", life, [0.12, 0.14, 0.14, 0.12, 0.14, 0.14, 0.1, 0.1, 0.08, 0.08, 0.1])], outdir)
    # the resin plates orbiting a shored-up monster: three big amber hexes with a dark rim and a jelly glint
    frs = []
    for k in range(6):
        r = R()
        for j in range(3):
            a = k / 6.0 * math.tau + j * math.tau / 3
            x, y = 12 * math.cos(a), -7 + 4.0 * math.sin(a)
            z = 1.0 if math.sin(a) > 0 else -1.0
            w = 2.6 * (0.75 + 0.25 * abs(math.sin(a)))     # edge-on at the sides, face-on front and back
            hexp = [(x - w, y), (x - w * 0.5, y - 2.4), (x + w * 0.5, y - 2.4), (x + w, y), (x + w * 0.5, y + 2.4), (x - w * 0.5, y + 2.4)]
            r.poly(hexp, "amber", z, normal=(-0.3, -0.5, 0.8))
            r.polyline(hexp + [hexp[0]], "amber", z + 0.005, tone=1)
            r.dot(x - w * 0.35, y - 1.0, "jelly", 4 if z > 0 else 3, z + 0.01)
            r.dot(x - w * 0.35 + 1, y - 1.0, "amber", 4, z + 0.01)
        frs.append(done(r))
    fx("FxZhkPlate", (32, 18), (16, 15), [("Play", frs, [0.08] * 6)], outdir)
    # Shore Up: resin rains onto an ally and sets into a plate
    frs = []
    for k in range(5):
        r = R()
        for j in range(5):
            x = (j - 2) * 3.0; y = -13 + k * 3 + (j % 2) * 2
            if y < -3: blob(r, x, y, 1.0, 1.2, "amber", glint=False)
        if k >= 3: r.ell(0, -5, 6 - (k - 3), 3, "amber", 0.0, flat=3 - (k - 3))
        frs.append(done(r))
    fx("FxZhkSeal", (20, 15), (10, 14), [("Play", frs, [0.06, 0.07, 0.08, 0.1, 0.12])], outdir)
    # heal sparkle (the Siphon's burst, the Gorger's pump target)
    frs = []
    for k in range(7):
        r = R()
        for j in range(4):
            x = (j - 1.5) * 3.0; y = -4 - k * 2.4 - (j % 2) * 3
            if y > -22:
                r.dot(x, y, "blood", 3 if k < 5 else 2, 1.0); r.dot(x, y - 1, "blood", 4 if k < 4 else 2, 1.0)
                r.dot(x - 1, y, "blood", 2, 1.0); r.dot(x + 1, y, "blood", 2, 1.0)
        if k < 2: r.ell(0, -1, 5 + k * 2, 1.6, "blood", 0.5, flat=3)
        frs.append(done(r))
    fx("FxZhkMend", (16, 24), (8, 23), [("Play", frs, [0.08] * 7)], outdir)
    # the frenzy pheromone wave
    frs = []
    for k in range(6):
        r = R(); R_ = 6 + k * 6
        ring(r, 0, -6, R_, R_ * 0.4, "jelly", 3 if k < 3 else 2, 1.0, n=60, step=1 + k // 2)
        for j in range(8):
            a = j / 8.0 * math.tau + k * 0.3
            r.dot(R_ * 0.8 * math.cos(a), -6 + R_ * 0.32 * math.sin(a) - k, "royal", 3, 1.1)
        frs.append(done(r))
    fx("FxZhkPheromone", (76, 32), (38, 22), [("Play", frs, [0.09] * 6)], outdir)


# ------------------------------------------------------------------ status overlays (bottom-centre origin)
def fx_overlays(outdir):
    def ov(name, cell, anims):
        fx(name, cell, (cell[0] // 2, cell[1] - 1), anims, outdir)
    # Corroded: an acid drop over the head
    frs = []
    for k in range(4):
        r = R(); y = [-6, -6.5, -7, -6.5][k]
        r.poly([(0, y - 3.4), (2.0, y), (0, y + 2.2), (-2.0, y)], "acid", 0.0, normal=(-0.3, -0.4, 0.8))
        r.ell(0, y + 0.2, 1.8, 2.0, "acid", 0.0, bias=0.2); r.dot(-0.6, y - 0.6, "white", 3, 0.1)
        r.dot(1 if k % 2 else -1, -1, "aglow", 2, 0.0)
        frs.append(done(r))
    ov("FxZhkAcidMark", (10, 12), [("Loop", frs, [0.12, 0.1, 0.12, 0.1])])
    # Marked: an amber chevron, pulsing
    frs = []
    for k in range(6):
        r = R(); y = -4 - 0.5 * math.sin(k / 6 * math.tau); t = 3 if k % 3 else 4
        for d in (0, 3):
            r.polyline([(-5, y - 3 + d), (0, y + d), (5, y - 3 + d)], "jelly", 0.0, tones=[t - (d > 0), t - (d > 0)])
        frs.append(done(r))
    ov("FxZhkMark", (16, 10), [("Loop", frs, [0.1] * 6)])
    # Swarm buff: tiny motes buzzing over the head
    frs = []
    for k in range(6):
        r = R()
        for j in range(4):
            a = k / 6.0 * math.tau + j * 1.6
            r.dot(5 * math.cos(a), -3 + 1.6 * math.sin(a * 1.3), "hyel", 3, 0.0); r.dot(5 * math.cos(a) - 1, -3 + 1.6 * math.sin(a * 1.3), "hblk", 1, 0.0)
        frs.append(done(r))
    ov("FxZhkSwarm", (16, 7), [("Loop", frs, [0.08] * 6)])
    # Frenzy: a ring of pheromone motes at the feet (ring centre on row 9 of 13: offset -3.5 puts it on the feet)
    anims = []
    for nm, rx, ry, n in (("Loop", 9.0, 3.2, 10), ("LoopBig", 15.0, 4.0, 14)):
        frs = []
        for k in range(4):
            r = R()
            for j in range(n):
                a = j / float(n) * math.tau + k * 0.4
                x, y = rx * math.cos(a), -3.5 + ry * math.sin(a) - (1 if j % 3 == k % 3 else 0)
                z = 0.1 if math.sin(a) > 0 else 0.0
                if j % 2:   # a gold mote: a plus of light
                    r.dot(x, y, "jelly", 4, z); r.dot(x - 1, y, "jelly", 2, z); r.dot(x + 1, y, "jelly", 2, z); r.dot(x, y - 1, "jelly", 3, z)
                else:       # kicked dust
                    r.dot(x, y, "dust", 3, z); r.dot(x + 1, y, "dust", 2, z)
                    if (j + k) % 4 == 0: r.dot(x, y - 2, "dust", 2, z)
            frs.append(done(r))
        anims.append((nm, frs, [0.08] * 4))
    ov("FxZhkFrenzy", (36, 14), anims)
    # Hatchery: the eggs left in an implanted hero (L3 = three to hatch) and lumps moving under the skin
    anims = []
    for n in range(4):
        frs = []
        for k in range(4):
            r = R()
            for j in range(3):
                x = (j - 1) * 4.0
                if j < n:
                    r.ell(x, -2.4, 1.4, 1.8, "cream", 0.0, bias=0.2); r.dot(x - 0.4, -3.2, "white", 3, 0.01)
                    if (j + k) % 4 == 0: r.dot(x + 0.6, -1.6, "aglow", 3, 0.02)
                else:
                    r.ell(x, -2.4, 1.2, 1.5, "dchit", 0.0, flat=1)
            if n: r.dot(-3 + k * 2, -6, "glue", 2, 0.0)
            frs.append(done(r))
        anims.append(("L%d" % n, frs, [0.12] * 4))
    ov("FxZhkImplantLumps", (14, 9), anims)
    # Royal Jelly: the larva being fed glows gold (a halo and rising motes)
    frs = []
    for k in range(4):
        r = R()
        ring(r, 0, -2.5, 6, 2, "jelly", 3 if k % 2 else 4, 0.0, n=20, step=1)
        for j in range(3): r.dot((j - 1) * 3, -3 - ((k + j) % 4) * 1.5, "jelly", 4 - (k + j) % 2, 0.1)
        frs.append(done(r))
    ov("FxZhkJellyGlow", (16, 12), [("Loop", frs, [0.1] * 4)])


# ------------------------------------------------------------------ new mechanic tells
def fx_tells(outdir):
    # the royal jelly bead (a thread of them runs from the Mother's mouth to the larva she feeds)
    frs = []
    for k in range(3):
        r = R(); r.ell(0, 0, 1.2 - 0.2 * (k == 2), 1.2 - 0.2 * (k == 2), "jelly", 0.0, flat=3 + (k == 0)); frs.append(done(r))
    fx("FxZhkJelly", (5, 5), (2, 2), [("Bead", frs, [0.08] * 3)], outdir)
    # the Gorger's blood bead (the pump line to its kin)
    frs = []
    for k in range(2):
        r = R(); r.ell(0, 0, 1.2, 1.0, "blood", 0.0, flat=3 + k); r.dot(-1, 0, "blood", 2, 0.0); frs.append(done(r))
    fx("FxZhkPump", (5, 5), (2, 2), [("Bead", frs, [0.08] * 2)], outdir)
    # the Mortar's spotter crosshair over an ally
    frs = []
    for k in range(4):
        r = R(); s = 4.0 + (0.6 if k % 2 else 0.0)
        ring(r, 0, -6, s, s, "rglow", 3, 0.0, n=20, step=1)
        for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            r.line(dx * (s - 1.5), -6 + dy * (s - 1.5), dx * (s + 1.5), -6 + dy * (s + 1.5), "rglow", 0.1, tone=4 if k < 2 else 3)
        frs.append(done(r))
    fx("FxZhkSpot", (13, 13), (6, 12), [("Loop", frs, [0.12] * 4)], outdir)
    # the Mantis's reach: a faint crescent of acid light on the floor, 28 px round it
    frs = []
    for k in range(4):
        r = R()
        ring(r, 0, 0, 28, 28, "aglow", 2, 0.0, n=72, step=3, gap=lambda a: math.cos(a) < -0.2)
        ring(r, 0, 0, 28, 28, "aglow", 3, 0.1, n=72, step=6, gap=lambda a, k=k: math.cos(a) < 0.4 or int(a * 10 + k) % 3)
        frs.append(done(r))
    fx("FxZhkReach", (60, 60), (30, 30), [("Loop", frs, [0.15] * 4)], outdir)
    # the Antlion's sand flick landing on the hero
    frs = []
    for k in range(5):
        r = R(); rnd = random.Random(2)
        for j in range(10):
            x = rnd.uniform(-6, 6); y = -12 + k * 3 + rnd.uniform(-2, 2)
            if y < 0: r.dot(x, y, "sand", 4 if j % 2 else 3, 1.0)
        if k >= 2: dust(r, 0, 0, k - 2, mat="sand")
        frs.append(done(r))
    fx("FxZhkSandFlick", (20, 16), (10, 14), [("Play", frs, [0.05, 0.05, 0.06, 0.08, 0.1])], outdir)
    # the acid mist the Bloater leaves where it zips (coats the hero in acid)
    frs = []
    for k in range(8):
        r = R(); rnd = random.Random(6)
        s = [0.6, 1.0, 1.0, 1.0, 0.9, 0.8, 0.6, 0.4][k]
        for j in range(9):
            x = rnd.uniform(-6, 6) * s; y = -4 + rnd.uniform(-3, 3) * s - k * 0.4
            r.ell(x, y, 1.6 * s, 1.2 * s, "mist", 0.0 + j * 0.01, flat=3 if k < 5 and j % 2 else 2)
        frs.append(done(r))
    fx("FxZhkSpiracleMist", (18, 14), (9, 11), [("Play", frs, [0.08, 0.15, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2])], outdir)
    # the shadow left on the floor under a lifted hero (Carry Off, Uproot)
    frs = []
    for k in range(2):
        r = R(); r.ell(0, -1, 5.0 - k * 0.5, 1.4, "dchit", 0.0, flat=1); r.ell(0, -1, 3.0 - k * 0.5, 0.8, "dchit", 0.01, flat=0); frs.append(done(r))
    fx("FxZhkCarry", (14, 5), (7, 3), [("Loop", frs, [0.12, 0.12])], outdir)


# ------------------------------------------------------------------ the god portrait and the gold idol
def queen_head(r, M, hx, hy, ph, eyes="jelly", eye_mat=None, z=0.0, sc=1.0, horn="royal", gem="jelly", ant=None):
    """The Brood Queen's head front on: a five-spired crown, two feathered antennae sweeping out, a heart-shaped
    capsule with great faceted eyes, and curved mandibles crossed below. M = shell material."""
    S = lambda v: v * sc
    # the antennae: long, sweeping out and up from under the crown, barbed along their length
    for sx in (-1, 1):
        pts = [(hx + sx * S(1.6), hy - S(5.0)), (hx + sx * S(5.0), hy - S(8.4)), (hx + sx * S(9.5), hy - S(9.6)), (hx + sx * S(12.5), hy - S(8.0))]
        A = ant or M
        r.polyline(pts, A, z - 0.2, tones=[2, 3, 3])
        for (px, py) in pts[1:]:
            r.dot(px, py + 1, A, 1, z - 0.21); r.dot(px + sx * 0.5, py - 1, A, 2, z - 0.21)
        r.dot(pts[-1][0], pts[-1][1], gem, 4 if (ph + (sx > 0)) % 2 else 3, z - 0.19)
    # the capsule: broad at the brow, narrowing to the jaws
    r.poly([(hx - S(7.5), hy - S(3.5)), (hx - S(5.5), hy - S(7.0)), (hx + S(5.5), hy - S(7.0)), (hx + S(7.5), hy - S(3.5)),
            (hx + S(5.0), hy + S(3.0)), (hx + S(2.0), hy + S(5.5)), (hx - S(2.0), hy + S(5.5)), (hx - S(5.0), hy + S(3.0))],
           M, z, normal=(-0.25, -0.35, 0.9), curve=0.6)
    r.ell(hx, hy - S(1.0), S(2.0), S(4.6), M, z + 0.01, bias=0.2)          # the raised mid-ridge
    r.dot(hx - S(0.6), hy - S(4.0), M, 4, z + 0.015)
    # the eyes: big faceted ovals that glow
    em = eye_mat or eyes
    for sx in (-1, 1):
        cx = hx + sx * S(4.4)
        r.ell(cx, hy - S(1.6), S(2.6), S(3.4), em, z + 0.05, flat=2, ang=sx * 20)
        r.ell(cx - S(0.5), hy - S(2.4), S(1.5), S(1.9), em, z + 0.06, flat=3, ang=sx * 20)
        r.dot(cx - S(0.9), hy - S(3.4), em, 4, z + 0.07)
        for j in range(3):
            r.dot(cx + sx * S(0.9), hy - S(0.4) + j, em, 1, z + 0.065)    # the facets in the shade
    # the crown: a band over the brow and five spires tipped with gems
    r.ell(hx, hy - S(6.6), S(6.0), S(1.4), horn, z + 0.1, bias=0.2)
    for k, dx in enumerate((-4.6, -2.4, 0.0, 2.4, 4.6)):
        L = S((5.4, 4.0, 3.0, 4.0, 5.4)[k] if False else (2.6, 3.8, 5.4, 3.8, 2.6)[k])
        bx, by = hx + S(dx), hy - S(7.2)
        tip = (bx + S(dx) * 0.25, by - L)
        r.tube([(bx, by), tip], [S(1.0), S(0.4)], horn, z + 0.11)
        r.dot(tip[0], tip[1] - 1, gem, 4 if (k + ph) % 4 == 0 else 3, z + 0.12)
    r.ell(hx, hy - S(6.8), S(1.1), S(1.0), gem, z + 0.13, flat=3)          # the centre jewel
    r.dot(hx - S(0.3), hy - S(7.2), "white", 4, z + 0.14)
    # the mandibles, crossed under the face
    mandible(r, (hx - S(2.4), hy + S(3.6)), 60, S(4.4), -110, z + 0.2, mat="amber", rad=S(0.9))
    mandible(r, (hx + S(2.4), hy + S(3.6)), 120, S(4.4), 110, z + 0.21, mat="amber", rad=S(0.9))


def idol(ph):
    """The gold idol: a bust of the Brood Queen, crowned, her wings fanned out behind her head, an amber heart set in
    her collar, on a comb plinth. All gold but the amber heart and the crown's gems."""
    r = Rig()
    G = "gidol"
    # the plinth: a slab with a row of comb cells cut in its face
    r.poly([(-8, -2.5), (8, -2.5), (9, 1.5), (-9, 1.5)], G, -1.0, normal=(0, -0.6, 0.8))
    for k in range(4):
        x = -6 + k * 4
        r.polyline([(x - 1.4, -0.5), (x - 0.7, -1.7), (x + 0.7, -1.7), (x + 1.4, -0.5), (x + 0.7, 0.7), (x - 0.7, 0.7), (x - 1.4, -0.5)],
                   G, -0.99, tones=[1] * 6)
    # the wings fanned behind her head: two long vanes a side, each with one raised vein
    for sx in (-1, 1):
        for k, (ang, ln, w) in enumerate(((-38, 13.0, 2.6), (-8, 12.0, 2.2))):
            root = (sx * 2.5, -8.0)
            tip = (root[0] + sx * ln * math.cos(math.radians(ang)), root[1] + ln * math.sin(math.radians(ang)))
            mid = ((root[0] + tip[0]) / 2, (root[1] + tip[1]) / 2)
            nx, ny = (tip[1] - root[1]) / ln, -(tip[0] - root[0]) / ln
            if ny > 0: nx, ny = -nx, -ny
            r.poly([root, (mid[0] + nx * w, mid[1] + ny * w), tip, (mid[0] - nx * w * 0.4, mid[1] - ny * w * 0.4)],
                   G, -0.6 - k * 0.1, normal=(-0.35 * sx, -0.5, 0.8))
            r.line(root[0] + sx, root[1], lerp(root[0], tip[0], 0.85), lerp(root[1], tip[1], 0.85), G, -0.59 - k * 0.1, tone=1)
    # the collar: a broad gold gorget with the amber heart in it
    r.ell(0, -3.6, 6.4, 2.4, G, 0.0, bias=0.15)
    r.line(-5.6, -3.0, 5.6, -3.0, G, 0.01, tone=1)
    r.ell(0, -3.8, 1.8, 1.6, "amber", 0.3, bias=0.2)
    r.dot(-0.5, -4.4, "jelly", 4 if ph % 2 else 3, 0.31)
    queen_head(r, G, 0.0, -10.4, ph, eye_mat="amber", z=0.6, sc=0.72, horn=G, gem="jelly")
    return r.resolve(floor=False)


def portrait(ph):
    """The Brood Queen's face filling the frame: a jewelled crown, feathered antennae, great amber eyes, crossed
    mandibles and a gold-plated collar, lit from behind by the amber glow of her hive."""
    r = Rig()
    # the hive behind her: dark comb walls round an amber glow
    for row in range(8):
        for col in range(8):
            x = -16 + col * 4.6 + (2.3 if row % 2 else 0); y = -23 + row * 3.4
            d = math.hypot(x / 14.0, (y + 13) / 11.0)
            t = 2 if d < 0.55 else 1
            r.polyline([(x - 2.0, y), (x - 1.0, y - 1.6), (x + 1.0, y - 1.6), (x + 2.0, y), (x + 1.0, y + 1.6), (x - 1.0, y + 1.6), (x - 2.0, y)],
                       "honey", -5.0, tones=[t] * 6)
            if d < 0.9 and (row * 3 + col) % 4 == 0:
                r.ell(x, y, 0.9, 0.8, "amber", -4.9, flat=3 if d < 0.5 else 2)
    # her wings flaring behind the shoulders: clear membranes, only the veins and the edge catch the light
    for sx in (-1, 1):
        root = (sx * 5.0, -4.0)
        for k, (tx, ty) in enumerate(((15.0, -10.0), (15.0, -3.0))):
            tip = (sx * tx, ty)
            up = (sx * (tx - 4), ty - 2.6 + k * 0.8); dn = (sx * (tx - 5), ty + 1.6)
            r.poly([root, up, tip, dn], "honey", -1.2 - k * 0.1, flat=1 + (k == 0))
            r.polyline([root, up, tip, dn], "amber", -1.0 - k * 0.1, tones=[3, 3, 2])
            r.line(root[0], root[1], lerp(root[0], tip[0], 0.8), lerp(root[1], tip[1], 0.8), "amber", -0.99 - k * 0.1, tone=2)
    # the collar: gold plates over the thorax and a pale ruff
    r.ell(0, -1.0, 9.0, 3.6, "chit", -0.5, bias=0.1)
    for k, dx in enumerate((-6.0, -3.0, 0.0, 3.0, 6.0)):
        r.ell(dx, -1.8 + abs(dx) * 0.12, 1.8, 1.5, "royal", -0.4 + k * 0.001, bias=0.2)
    r.ell(0, -4.6, 6.0, 1.4, "cream", -0.3, bias=0.2)
    queen_head(r, "chit", 0.5, -10.2, ph, eyes="jelly", z=0.0, sc=0.92, ant="royal")
    return r.resolve(floor=False, cast=False)


def gold_shade(s, glint=None):
    """Recolour the hollows (tone 0-1) dark honey, keep the gold lit; an optional travelling glint column."""
    from zhekra_v2_rigs import RAMPS
    from anim import SprRGB
    px = {}
    for k, (m, t) in s.tones.items():
        if m == "gidol" and t <= 1: px[k] = RAMPS["honey"][1 + t]
        else: px[k] = s.px[k]
        if glint is not None and m == "gidol" and abs((k[0] - k[1] * 0.5) - glint) < 1.0 and t >= 2:
            px[k] = RAMPS["gidol"][4]
    out = SprRGB(px); out.tones = s.tones
    return out


BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def backdrop(spr, origin, cell=(29, 24), warm=True, fill=None):
    """Lay a sprite over the slot portraits' backdrop (ui_slots.py: a dark frame, a dithered glow toward the centre), so
    the portrait is opaque like every other god's. fill: one colour instead of the glow."""
    from anim import SprRGB
    cols = [(0x14, 0x0c, 0x0c), (0x24, 0x15, 0x14), (0x33, 0x1d, 0x19), (0x45, 0x27, 0x1d)]
    px = {}
    W, H = cell
    for yy in range(H):
        for xx in range(W):
            k = (xx - origin[0], yy - origin[1])
            if fill is not None:
                c = fill
            elif xx in (0, W - 1) or yy in (0, H - 1):
                c = cols[0]
            else:
                d = ((xx - 14) ** 2 / 196.0 + (yy - 10) ** 2 / 110.0) ** 0.5
                v = max(0.0, 1.0 - d) * 3.0 + (BAYER[yy % 4][xx % 4] / 16.0 - 0.47)
                c = cols[max(0, min(3, int(v) + 1))]
            px[k] = spr.px.get(k, c)
    out = SprRGB(px); out.tones = getattr(spr, "tones", {})
    return out


def fx_portraits(outdir):
    from zhekra_v2_rigs import RAMPS
    # the portrait (29 x 24, Idle 4): her face in the comb, opaque like every god portrait
    po = (14, 23)
    fx("DeityZhekra", (29, 24), po, [("Idle", [backdrop(portrait(k), po, fill=RAMPS["honey"][0]) for k in range(4)],
                                      [0.3, 0.25, 0.3, 0.25])], outdir)
    # the gold idol (29 x 24, Idle 8) on the gold slot's warm backdrop: a glint sweeps across, then rests
    io = (14, 20)
    frs = [backdrop(gold_shade(idol(k % 4), glint=-14 + k * 6 if k < 5 else None), io) for k in range(8)]
    fx("DeityGoldIdolZhekra", (29, 24), io, [("Idle", frs, [0.06, 0.06, 0.06, 0.06, 0.06, 0.22, 0.2, 0.5])], outdir)


NOTES["FxZhk*"] = ("Effects: origins are the pack origins in the table above; status overlays (AcidMark, Mark, Swarm, Frenzy, "
                   "ImplantLumps L0-L3, JellyGlow) sit on their bottom centre. FxZhkPit plays Open, Loop (repeat) and Close.")
NOTES["DeityGoldIdolZhekra"] = "Zhekra's gold idol portrait (SlotGods.PortraitFor, gold tier)."

JOBS = [("FxZhkProjectiles", fx_projectiles), ("FxZhkFloor", fx_floor), ("FxZhkBursts", fx_bursts), ("FxZhkMisc", fx_misc),
        ("FxZhkOverlays", fx_overlays), ("FxZhkTells", fx_tells), ("DeityZhekra", fx_portraits)]
