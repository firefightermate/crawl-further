"""Vhorrul tier 1: Wickling, Tallow Grub, Ash Moth. Built through vhorrul_v2_rigs.py (python3 vhorrul_v2_rigs.py --only
Wickling,TallowGrub,AshMoth). T1 idle limit 20 x 16 (flyers count their hover)."""
import math
from vhorrul_v2_rigs import (Rig, chain, ik, lerp, flame, candle, smoke_curl, drip, floor_pool, ember_dots, sheet,
                             tail_anims, line_px)


def bez(p0, p1, p2, p3, n=8):
    out = []
    for i in range(n + 1):
        t = i / float(n); u = 1 - t
        out.append((u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
                    u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1]))
    return out


def dust(r, x, y, k, w=1.0):
    """A low puff of grey dust kicked up at (x, y): k = 0 (fresh) .. 2 (fading)."""
    p = r.part(True, 6.0)
    x, y = x * r.k, y * r.k
    for i, (dx, dy) in enumerate(((-2, 0), (-1, -1), (0, 0), (1, -1), (2, 0), (-3, -1), (3, -1))):
        if i >= 5 - k: break
        r.put(x + dx * w * (1 + 0.4 * k), y + dy - k * 0.5, 6.0, "smoke", 0.5, p, 3 - min(2, k))


# ================================================================== WICKLING
def tail_flame(r, x, y, state, ph, z=6.0, big=1.0):
    """The flame on the wick's end: lit (orange), out (a smoking charred tip), hot (white-hot and taller)."""
    if state == "out":
        r.dot(x, y, "ember", 1, z)
        smoke_curl(r, x, y - 1, ph, z, k=0.8)
    elif state == "hot":
        flame(r, x, y, 4.8 * big, ph, "fire", z, wide=1.2)
        flame(r, x, y - 0.5, 3.4 * big, ph + 1, "spark", z + 0.1, wide=0.7)
        r.dot(x + FLK(ph), y - 5.5 * big, "ember", 3, z)
    else:
        flame(r, x, y, 3.6 * big, ph, "fire", z)


def FLK(ph):
    return (0, 1, -1, 1, 0, -1)[ph % 6]


def wickling(crouch=0.0, stretch=1.0, lift=0.0, lean=0.0, head=(0.0, 0.0), jaw=0.0, legs=None, tail=0.0, tail_up=0.0,
             state="lit", ph=0, smear=None, eye=True, extra=None, roll=0.0, tail_pts=None):
    """crouch: px the body sinks; stretch: body length factor; lift: px off the floor (a leap); head: (dx, dy) of the
    head; jaw: 0 shut .. 1 wide; legs: 4 foot points (back far, back near, front far, front near); tail: sway (px);
    tail_up: how high the tail rears; state: lit / out / hot (the tail flame)."""
    r = Rig()
    by = -4.2 + crouch - lift
    bx = 0.0
    L = 5.2 * stretch
    # ---- the tail: a braided wick from the rump, curling up; the flame on its end is the tallest point
    rump = (bx - L + 0.6, by - 0.6)
    if tail_pts is None:
        tip = (rump[0] - 2.5 + tail * 0.6, by - 6.6 - tail_up)
        pts = bez(rump, (rump[0] - 3.5, by + 0.5), (rump[0] - 4.5 + tail * 0.5, by - 4.5 - tail_up * 0.5), tip, 9)
    else:
        pts = tail_pts(rump, by)
        tip = pts[-1]
    pr = r.part(True, -0.6)
    for i, (x, y) in enumerate(pts):
        # braided: tallow-caked twists between bare black cord
        m, t = ("tallow", 2) if i % 3 == 1 else ("rat", 2) if i % 3 == 2 else ("wick", 4)
        r.put(x, y, -0.6, m, 0.5, pr, t)
        if i < 5: r.put(x + 0.6, y + 1, -0.6, "rat", 0.5, pr, 1)
    tail_flame(r, tip[0], tip[1] - 0.5, state, ph)
    # ---- legs (far pair behind the body, near pair in front)
    if legs is None:
        legs = ((-L + 1.8, 0.0), (-L + 2.6, 0.0), (L - 1.6, 0.0), (L - 0.6, 0.0))
    hips = ((bx - L + 2.2, by + 1.6), (bx - L + 2.8, by + 1.8), (bx + L - 1.8, by + 1.4), (bx + L - 1.0, by + 1.6))
    for k, ((fx, fy), (hx, hy)) in enumerate(zip(legs, hips)):
        near = k % 2 == 1
        z = 1.2 if near else -0.8
        kx, ky = ik(hx, hy, fx, fy - 0.4, 1.8, 1.8, bend=1 if k < 2 else -1)
        r.tube([(hx, hy), (kx, ky), (fx, fy - 0.4)], [0.9, 0.6, 0.6], "rat", z, bias=0.0 if near else -0.35)
        r.dot(fx + 0.6, fy, "rat", 1 if near else 0, z + 0.01)
    # ---- the body: mangy rat under a coat of tallow, drips hanging off it
    r.ell(bx - 0.4, by, L, 3.1, "rat", 0.0, ang=-4.0 + roll)
    r.ell(bx - 1.0, by - 1.2, L * 0.82, 2.2, "tallow", 0.4, ang=-4.0 + roll,
          clip=lambda x, y: y <= by - 0.6 + 0.25 * (x - bx))
    for dx, ln in ((-L * 0.6, 1.6), (-L * 0.15, 2.4), (L * 0.35, 1.2)):
        drip(r, bx + dx, by - 0.4 + 0.25 * dx, ln, "tallow", 0.45)
    # a few mangy tufts on the belly
    for dx in (-2.0, 0.5, 2.6):
        r.dot(bx + dx, by + 2.6, "rat", 1, 0.5)
    # ---- the head: wedge skull, long snout, ragged ear, an ember eye
    hx, hy = bx + L + 0.6 + head[0], by - 0.6 + head[1]
    r.tube([(bx + L - 1.5, by - 0.2), (hx - 0.6, hy + 0.2)], [2.2, 2.0], "rat", 1.9)   # neck
    r.ell(hx, hy, 2.6, 2.2, "rat", 2.0)
    snout = [(hx + 1.2, hy - 0.4), (hx + 3.4, hy + 0.2 - jaw * 0.6), (hx + 4.6, hy + 0.6 - jaw * 0.9)]
    r.tube(snout, [1.4, 1.0, 0.6], "rat", 2.1)
    r.dot(snout[-1][0] + 0.4, snout[-1][1], "pink", 3, 2.2)   # nose
    if jaw > 0.05:
        jx, jy = hx + 1.0, hy + 1.4
        r.tube([(jx, jy), (jx + 2.6 + jaw, jy + 1.0 + jaw * 1.6)], [0.8, 0.5], "rat", 2.05, bias=-0.3)
        r.dot(jx + 2.4 + jaw, jy + 0.4 + jaw * 1.2, "bone", 3, 2.3)
        r.dot(snout[-1][0] - 0.3, snout[-1][1] + 0.8, "bone", 3, 2.3)
        r.dot(jx + 1.6, jy + 0.2 + jaw * 0.6, "votive", 1, 2.04)    # the open mouth
    r.poly([(hx - 1.4, hy - 1.4), (hx - 0.6, hy - 4.0), (hx + 0.6, hy - 1.8)], "rat", 2.3, normal=(-0.4, -0.5, 1.0))
    r.dot(hx - 0.5, hy - 2.6, "pink", 1, 2.31)
    if eye:
        r.dot(hx + 0.8, hy - 0.6, "ember", 3, 2.4)
    # wax capping the skull, one drip over the brow
    r.ell(hx - 0.8, hy - 1.6, 1.6, 0.9, "tallow", 2.25)
    if smear:
        for pts_, m, tn in smear:
            r.polyline(pts_, m, 4.6, tone=tn)
    if extra: extra(r)
    return r.resolve()


def run_legs(i, n=6, L=5.2, reach=2.0, lift=1.4):
    ph = i / float(n) * math.tau
    out = []
    for k, off in enumerate((0.0, 0.5, math.pi, math.pi + 0.5)):
        a = ph + off
        base = (-L + 2.2 + 0.4 * (k % 2)) if k < 2 else (L - 1.4 + 0.6 * (k % 2))
        out.append((base + reach * math.cos(a), -max(0.0, lift * math.sin(a))))
    return out


def wick_sheet(outdir):
    W = wickling
    sets = {}
    for st in ("lit", "out", "hot"):
        idle = [W(crouch=[0, 0.3, 0.5, 0.3][i], tail=[0, 0.6, 1.0, 0.4][i], head=(0, [0, 0.2, 0.4, 0.2][i]), state=st, ph=i)
                for i in range(4)]
        run = []
        for i in range(6):
            s = math.sin(i / 6.0 * math.tau)
            run.append(W(stretch=1.0 + 0.08 * s, lift=max(0.0, 0.8 * s), crouch=max(0.0, -0.6 * s), legs=run_legs(i),
                         tail=-1.5 - s, tail_up=-1.0 + 0.6 * s, head=(0.3 * s, 0.4 * s), state=st, ph=i))
        sets[st] = (idle, run)
    idle, run = sets["lit"]
    # Flare Bite: crouch, coil back, lunge, BITE (f3), hold, settle
    bite = [W(crouch=1.0, head=(-0.6, 0.6), tail=0.8, ph=0),
            W(crouch=1.4, stretch=0.9, head=(-1.2, 0.8), tail=1.4, tail_up=0.6, jaw=0.3, ph=1),
            W(stretch=1.15, lift=1.2, head=(1.5, -0.4), jaw=0.8, tail=-2.0, legs=((-4.5, -0.6), (-3.6, 0.0), (6.6, -1.2), (7.4, -0.6)), ph=2,
              smear=[([(3, -9), (7, -9), (11, -8)], "white", 2)]),
            W(stretch=1.2, head=(2.6, 0.4), jaw=1.0, tail=-2.4, legs=((-4.2, 0.0), (-3.4, 0.0), (6.8, 0.0), (7.8, 0.0)), ph=3,
              extra=lambda r: ember_dots(r, [(14, -3, 4), (15, -5, 3), (13, -1, 2), (16, -2, 2)])),
            W(stretch=1.1, head=(1.6, 0.6), jaw=0.4, tail=-1.0, ph=4),
            W(crouch=0.4, head=(0.4, 0.2), ph=5)]
    # Gutter Dash: crouch low, the tail flame flares, sprint (f2-f5), stumble (f6), the tail gutters out (f7)
    dash = [W(crouch=1.6, stretch=0.9, head=(-0.6, 1.0), tail=1.0, tail_up=1.0, ph=0),
            W(crouch=1.8, stretch=0.85, head=(-1.0, 1.2), tail=1.6, tail_up=1.8, state="hot", ph=1)]
    for i in range(4):
        s = math.sin(i / 4.0 * math.tau)
        dash.append(W(stretch=1.25 + 0.06 * s, crouch=0.6, lift=max(0.0, 0.7 * s), legs=run_legs(i, 4, 6.0, 2.8, 1.2), head=(1.2, 0.8),
                      tail_pts=lambda rump, by: bez(rump, (rump[0] - 3, by + 0.2), (rump[0] - 6, by - 1.2), (rump[0] - 8.5, by - 2.5), 9),
                      ph=i, extra=(lambda k: lambda r: _streak(r, k))(i)))
    dash.append(W(crouch=0.0, stretch=1.0, head=(1.8, 2.4), roll=12.0, tail=-3.0, tail_up=1.5, ph=4,
                  legs=((-3.0, -2.0), (-2.4, -1.4), (5.8, 0.0), (6.4, 0.0)), extra=lambda r: dust(r, 10.0, 0.0, 0)))
    dash.append(W(crouch=0.6, head=(0.6, 0.8), tail=0.6, state="out", ph=5, extra=lambda r: dust(r, 8.0, 0.0, 2)))
    knock = W(crouch=0.2, head=(-1.4, -1.0), jaw=0.5, tail=2.5, tail_up=1.5, roll=-10.0, ph=2, eye=True)
    d0 = W(crouch=0.4, head=(-1.0, -0.8), jaw=0.8, roll=-14.0, tail=2.0, state="hot", ph=1)
    d1 = W(crouch=1.6, head=(0.4, 1.6), jaw=0.6, roll=18.0, tail=-2.0, state="lit", ph=3,
           legs=((-3.0, -2.6), (-2.0, -3.0), (4.0, -2.4), (5.0, -3.0)))
    d2 = wick_corpse(0)
    corpse = wick_corpse(1)
    anims = [("Idle", idle, [0.16, 0.13, 0.16, 0.13]), ("Run", run, [0.07] * 6),
             ("IdleOut", sets["out"][0], [0.16, 0.13, 0.16, 0.13]), ("RunOut", sets["out"][1], [0.07] * 6),
             ("IdleHot", sets["hot"][0], [0.1] * 4), ("RunHot", sets["hot"][1], [0.07] * 6),
             ("Bite", bite, [0.1, 0.08, 0.05, 0.08, 0.1, 0.1]),
             ("Dash", dash, [0.12, 0.1, 0.045, 0.045, 0.045, 0.045, 0.12, 0.14])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("Wickling", anims, outdir, scale=8)


def _streak(r, k):
    """Speed streaks of flame behind the sprinting rat."""
    p = r.part(True, -1.5)
    for j, (y, ln) in enumerate(((-3, 5), (-6, 4), (-1, 3))):
        x0 = -9 - (k + j) % 2
        for i in range(ln):
            r.put(x0 - i, y, -1.5, "fire" if i < 2 else "ember", 0.5, p, 3 if i == 0 else 2 if i < 3 else 1)


def wick_corpse(stage):
    """The rat on its side, legs up, a smoking wick and a skin of wax going grey."""
    r = Rig()
    r.ell(0.0, -2.4, 5.6, 2.4, "rat", 0.0, ang=4.0)
    r.ell(-0.6, -1.6, 4.6, 1.6, "tallow", 0.4, clip=lambda x, y: y >= -1.6)
    for x0 in (-2.5, -1.5, 2.0, 3.0):
        r.tube([(x0, -4.0), (x0 + 0.6, -6.2)], [0.6, 0.5], "rat", -0.2 if x0 < 0 else 0.2)
    r.ell(6.0, -2.4, 2.4, 2.0, "rat", 0.5)
    r.tube([(7.2, -2.0), (9.6, -1.4)], [1.0, 0.6], "rat", 0.6)
    r.dot(6.8, -3.0, "ash", 1, 0.7)
    pts = bez((-5.2, -2.0), (-7.5, -1.0), (-9.5, -1.6), (-11.0, -1.0), 7)
    r.polyline(pts, "wick", -0.2, tones=[3, 2] * 4)
    if stage == 0:
        r.dot(-11.0, -1.8, "ember", 2, 6.0)
        smoke_curl(r, -11.0, -3.0, 1, 6.0, k=1.0)
    else:
        r.dot(-11.0, -1.4, "ash", 2, 6.0)
        floor_pool(r, 0.0, -0.6, 7.0, 0.8, "tallow", -2.0, tone=2)
    return r.resolve()


# ================================================================== TALLOW GRUB
def grub(squash=0.0, stretch=1.0, rear=0.0, mouth=0.0, ph=0, sink=0.0, lean=0.0, stub_out=False, extra=None, wob=0.0, eye=True):
    """A fat tallow maggot: five greasy segments, a guttered candle stub on its back, a round sucker mouth.
    squash: flattens it (melting); rear: lifts the front segments; sink: px sunk into its own puddle."""
    r = Rig()
    n = 5
    segs = []
    for i in range(n):
        t = i / float(n - 1)
        x = (-6.5 + 13.0 * t) * stretch
        rr = 2.6 + 0.9 * math.sin(math.pi * min(1.0, t * 1.1 + 0.05)) - 0.4 * t
        ry = rr * (1.0 - 0.45 * squash)
        y = -ry - 0.1 + sink - rear * t * t * 3.0 + wob * math.sin(i * 1.4 + ph)
        segs.append((x + lean * t, y, rr * (1 + 0.25 * squash), ry))
    for i, (x, y, rx, ry) in enumerate(segs):
        r.ell(x, y, rx, ry, "tallow", 0.1 * i, ang=0.0)
        if i < n - 1:   # the crease between segments
            r.line(x + rx * 0.7, y - ry * 0.6, x + rx * 0.8, y + ry * 0.4, "tallow", 0.1 * i + 0.05, tone=1)
    hx, hy, hrx, hry = segs[-1]
    # sucker mouth: a dark ring on the front, opening for the spit
    mo = 0.6 + mouth * 0.9
    r.ell(hx + hrx * 0.75, hy + 0.2, 0.7 + mouth * 0.4, mo, "soot", 0.9)
    r.dot(hx + hrx * 0.75 + 0.4, hy + 0.2, "votive", 1 if mouth < 0.5 else 2, 0.95)
    if eye:
        r.dot(hx + 0.2, hy - hry * 0.6, "ember", 2, 0.92)
    # drips along the underside and a greasy shine on top
    for i in (1, 2, 3):
        x, y, rx, ry = segs[i]
        r.dot(x - 0.6, y - ry + 0.6, "tallow", 4, 0.1 * i + 0.06)
    # the guttered candle stub on the middle segment
    x, y, rx, ry = segs[2]
    if sink < 3.5:
        candle(r, x - 0.5, y - ry + 0.8, 3.0, 2.0, z=1.2, ph=ph, out=stub_out, flh=2.6)
    if extra: extra(r)
    return r.resolve()


def puddle_grub(ph=0, glide=0.0, bubble=0, extra=None):
    """Melted: a puddle of tallow with the candle stub gliding across it (the stub is the only thing that sticks up)."""
    r = Rig()
    floor_pool(r, -glide, -1.6, 8.5, 2.3, "tallow", -1.0, tone=2)
    floor_pool(r, 1.0 - glide * 0.5, -1.9, 4.0, 1.0, "tallow", -0.9, tone=3, rim=False)
    for k in range(bubble):
        bx = (-3, 2, 5, -1)[k % 4]
        r.dot(bx, -2.2 - (k % 2), "tallow", 4, -0.5)
        r.dot(bx + 1, -1.8, "tallow", 1, -0.5)
    if glide:   # the wake behind it
        for i in range(3):
            r.dot(-8 - i * 2 - glide, -1.2 + (i % 2) * 0.6, "tallow", 2, -1.1)
    candle(r, 1.0, -2.0, 3.0, 2.0, z=0.4, ph=ph, flh=2.6)
    r.dot(4.6, -1.6, "ember", 2, 0.5)   # one ember eye under the surface
    if extra: extra(r)
    return r.resolve()


def grub_sheet(outdir):
    G = grub
    idle = [G(wob=0.25, ph=i, squash=[0, 0.05, 0.1, 0.05][i]) for i in range(4)]
    run = []
    for i in range(6):
        s = math.sin(i / 6.0 * math.tau)
        run.append(G(stretch=1.0 + 0.1 * s, squash=0.1 * max(0.0, -s), rear=max(0.0, 0.25 * s), lean=0.8 * s, wob=0.4, ph=i))
    spit = [G(rear=0.3, mouth=0.2, ph=0), G(rear=0.6, squash=0.15, stretch=0.92, mouth=0.4, ph=1),
            G(rear=0.9, stretch=0.88, mouth=0.7, ph=2),
            G(rear=0.2, stretch=1.08, mouth=1.0, ph=3, extra=lambda r: _glob_out(r)),
            G(rear=0.0, stretch=1.02, mouth=0.5, ph=4), G(mouth=0.2, ph=5)]
    melt = [G(squash=0.25, ph=0), G(squash=0.5, stretch=1.08, ph=1, wob=0.3), G(squash=0.75, stretch=1.15, sink=1.0, ph=2, eye=False),
            G(squash=0.9, stretch=1.25, sink=2.2, ph=3, eye=False, extra=lambda r: floor_pool(r, 0, -1.4, 8.0, 2.0, "tallow", -1.0)),
            puddle_grub(4)]
    puddle = [puddle_grub(i, bubble=0) for i in range(4)]
    glide = [puddle_grub(i, glide=[0, 0.5, 1.0, 0.5][i]) for i in range(4)]
    rise = [puddle_grub(0, bubble=2), puddle_grub(1, bubble=4),
            G(squash=0.5, rear=1.2, mouth=1.0, ph=2, extra=lambda r: _upwell(r, 0)),
            G(squash=0.2, rear=0.8, mouth=0.6, ph=3, extra=lambda r: _upwell(r, 1)),
            G(rear=0.3, ph=4, extra=lambda r: _upwell(r, 2)), G(ph=5)]
    knock = G(rear=0.6, squash=0.2, lean=-1.5, mouth=0.6, ph=2)
    d0 = G(rear=0.8, mouth=1.0, squash=0.2, ph=1)
    d1 = G(squash=0.6, stretch=1.15, mouth=0.8, ph=3, stub_out=True)
    d2 = G(squash=0.9, stretch=1.3, sink=1.4, ph=4, stub_out=True, eye=False,
           extra=lambda r: floor_pool(r, 0, -1.2, 9.0, 1.8, "tallow", -1.0))
    corpse = puddle_corpse()
    anims = [("Idle", idle, [0.18, 0.15, 0.18, 0.15]), ("Run", run, [0.09] * 6),
             ("Spit", spit, [0.1, 0.1, 0.1, 0.06, 0.1, 0.12]),
             ("Melt", melt, [0.08, 0.08, 0.08, 0.08, 0.1]),
             ("Puddle", puddle, [0.14] * 4), ("Glide", glide, [0.09] * 4),
             ("Rise", rise, [0.2, 0.2, 0.06, 0.08, 0.1, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("TallowGrub", anims, outdir, scale=8)


def _glob_out(r):
    r.ell(10.5, -3.6, 1.6, 1.3, "tallow", 3.0)
    r.dot(10.0, -4.2, "tallow", 4, 3.1)
    for i in range(3): r.dot(8.4 - i, -3.4 + (i % 2), "tallow", 3, 2.9)


def _upwell(r, k):
    """Wax bursting up round the rising grub."""
    p = r.part(True, 3.0)
    for i, (dx, dy) in enumerate(((-7, -3), (-5, -6), (6, -5), (8, -2), (-2, -8), (3, -8))):
        s = 1.0 + 0.5 * k
        r.put(dx * s * 0.9, dy * (1.2 - 0.25 * k) + k * 1.5, 3.0, "tallow", 0.5, p, 4 if k == 0 else 3 if k == 1 else 2)
    floor_pool(r, 0, -1.0, 8.0 + k, 1.6, "tallow", -1.0)


def puddle_corpse():
    r = Rig()
    floor_pool(r, 0.0, -1.4, 9.0, 1.8, "tallow", -1.0, tone=2)
    floor_pool(r, -1.0, -2.0, 5.0, 1.2, "tallow", -0.9, tone=3, rim=False)
    candle(r, 1.0, -2.0, 2.0, 2.0, z=0.4, out=True, ph=2)
    r.dot(-3, -2.4, "tallow", 1, -0.5)
    return r.resolve()


# ================================================================== ASH MOTH
def moth(alt=4.0, flap=0.0, glow=False, ph=0, lean=0.0, body_ang=0.0, puff=0, dive=0.0, extra=None, hurt=False):
    """A moth hovering alt px up, seen from the front: ragged ash wings spread in a wide flat V, an ember body like a
    coal, a soot eye-spot on each wing. flap: -1 (wings down) .. 1 (wings up); glow: wing edges burning (near fire);
    body_ang tips the whole moth (a dive)."""
    r = Rig()
    cx, cy = lean, -alt - 4.0
    r.ell(0.0, -0.3, 2.8, 0.6, "soot", -6.0, flat=1)
    tilt = math.radians(body_ang)

    def T(x, y):   # tip the moth about its body
        dx, dy = x - cx, y - cy
        return cx + dx * math.cos(tilt) - dy * math.sin(tilt), cy + dx * math.sin(tilt) + dy * math.cos(tilt)
    for s, z in ((-1, -1.0), (1, 2.0)):
        near = s > 0
        up = flap * 2.8
        pts = [(cx + s * 0.6, cy - 1.2), (cx + s * 4.0, cy - 3.2 - up * 0.6), (cx + s * 8.2, cy - 3.6 - up),
               (cx + s * 8.6, cy - 2.2 - up), (cx + s * 7.2, cy + 0.2 - up * 0.6), (cx + s * 7.6, cy + 1.2 - up * 0.4),
               (cx + s * 5.0, cy + 1.6 - up * 0.3), (cx + s * 4.2, cy + 3.6 - up * 0.2), (cx + s * 2.6, cy + 2.4),
               (cx + s * 0.8, cy + 1.2)]
        pts = [T(*q) for q in pts]
        r.poly(pts, "moth", z, bias=0.15 if near else -0.3, normal=(-0.35, -0.45, 1.0))
        ex, ey = T(cx + s * 4.4, cy - 0.6 - up * 0.5)
        r.dot(ex, ey, "soot", 0, z + 0.02); r.dot(ex + s, ey, "soot", 1, z + 0.02)
        r.dot(ex, ey - 1, "ember" if glow else "ash", 2 if glow else 4, z + 0.03)
        pe = r.part(True, z + 0.04)
        edge = []
        for a_, b_ in zip(pts[1:4], pts[2:5]):
            edge += line_px(int(round(a_[0])), int(round(a_[1])), int(round(b_[0])), int(round(b_[1])))
        for i, (x, y) in enumerate(edge):
            if glow: r.put(x, y, z + 0.04, "ember", 0.5, pe, 3 if (i + ph) % 3 else 2)
            elif i % 2 == 0: r.put(x, y, z + 0.04, "ash", 0.5, pe, 4 if near else 3)
    # the ember body: a glowing coal under a crust of ash, head on top, feathered antennae
    bx, by = T(cx, cy + 0.6)
    r.ell(bx, by, 1.6, 2.8, "ash", 3.0, ang=body_ang)
    ember_dots(r, [(bx, by - 0.5, 4 if not hurt else 3), (bx, by + 0.6, 3), (bx - 1, by + 1.4, 2), (bx + 0.5, by + 2.0, 2),
                   (bx + 1, by - 0.2, 3)], z=3.05)
    hx, hy = T(cx + 0.3, cy - 2.6)
    r.ell(hx, hy, 1.2, 1.1, "ash", 3.2)
    r.dot(hx + 0.6, hy, "ember", 3, 3.3)
    for s in (-1, 1):
        r.line(hx + s * 0.5, hy - 1, hx + s * 2.0, hy - 3.2, "ash", 3.25, tone=3)
        r.dot(hx + s * 2.3, hy - 3.4, "ash", 4, 3.26)
    if puff:
        _ash_cloud(r, hx + 2.5 + puff * 1.5, hy + 1.5, puff)
    if extra: extra(r)
    return r.resolve()


def _ash_cloud(r, x, y, k):
    p = r.part(True, 3.0)
    rnd = [(0, 0), (1, -1), (-1, 1), (2, 1), (1, 1), (-1, -1), (2, -1), (3, 0)]
    for i, (dx, dy) in enumerate(rnd[:3 + 2 * k]):
        r.put(x + dx * (1 + 0.3 * k), y + dy, 3.0, "smoke", 0.5, p, 3 if i < 3 else 2)
    if k >= 2: r.put(x + 1, y, 3.1, "ember", 0.5, p, 3)


def moth_sheet(outdir):
    M = moth
    flaps = [1.0, 0.4, -0.5, -1.0, -0.3, 0.6]
    idle = [M(alt=4.0 + [0, 0.5, 1, 1, 0.5, 0][i], flap=flaps[i], ph=i) for i in range(6)]
    run = [M(alt=4.5 + [0, 0.5, 1, 1, 0.5, 0][i], flap=flaps[i], ph=i, lean=0.6, body_ang=-8.0) for i in range(6)]
    gidle = [M(alt=4.0 + [0, 0.5, 1, 1, 0.5, 0][i], flap=flaps[i], ph=i, glow=True) for i in range(6)]
    grun = [M(alt=4.5 + [0, 0.5, 1, 1, 0.5, 0][i], flap=flaps[i], ph=i, lean=0.6, body_ang=-8.0, glow=True) for i in range(6)]
    puff = [M(alt=7.0, flap=0.8, ph=0, lean=-0.5), M(alt=7.5, flap=1.0, ph=1, lean=-1.0, body_ang=-6),
            M(alt=7.0, flap=0.0, ph=2, lean=0.0, body_ang=8),
            M(alt=6.5, flap=-1.0, ph=3, lean=1.0, body_ang=10, puff=1), M(alt=6.5, flap=-0.4, ph=4, lean=0.5, puff=2),
            M(alt=6.5, flap=0.5, ph=5, puff=3)]
    dive = [M(alt=8.0, flap=1.0, ph=0, lean=-1.0, body_ang=-10), M(alt=9.0, flap=1.0, ph=1, lean=-1.5, body_ang=-14, glow=True),
            M(alt=5.0, flap=-0.8, ph=2, lean=2.0, body_ang=22, glow=True, extra=lambda r: _dive_streak(r, 0)),
            M(alt=4.0, flap=-1.0, ph=3, lean=3.0, body_ang=24, glow=True, extra=lambda r: _dive_streak(r, 1)),
            M(alt=3.5, flap=-0.6, ph=4, lean=3.0, body_ang=18, glow=True, extra=lambda r: _dive_streak(r, 2)),
            M(alt=4.5, flap=0.6, ph=5, lean=2.0, body_ang=0, puff=2),
            M(alt=6.0, flap=1.0, ph=0, lean=0.5, puff=3)]
    knock = M(alt=6.0, flap=1.0, ph=2, lean=-1.5, body_ang=-20, hurt=True)
    d0 = M(alt=5.0, flap=1.0, ph=1, body_ang=-25, hurt=True)
    d1 = M(alt=2.5, flap=-1.0, ph=3, body_ang=40, hurt=True)
    anims = [("Idle", idle, [0.08] * 6), ("Run", run, [0.07] * 6), ("IdleGlow", gidle, [0.08] * 6), ("RunGlow", grun, [0.07] * 6),
             ("Puff", puff, [0.1, 0.1, 0.08, 0.06, 0.1, 0.12]),
             ("Dive", dive, [0.1, 0.1, 0.05, 0.05, 0.05, 0.1, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, moth_corpse(0), moth_corpse(1)], [0.1, 0.1, 0.14, 0.4], knock)
    return sheet("AshMoth", anims, outdir, scale=8)


def _dive_streak(r, k):
    p = r.part(True, -2.0)
    for i in range(4 + k):
        r.put(-6 - i, -9 + i * 0.6 - k, -2.0, "ember" if i < 2 else "smoke", 0.5, p, 3 if i == 0 else 2)


def moth_corpse(stage):
    r = Rig()
    r.poly([(-6, -1), (-1, -3), (2, -1), (-2, 0)], "moth", -0.5, bias=-0.2)
    r.poly([(-1, -1), (5, -4), (7, -1), (3, 0)], "moth", 0.5)
    r.ell(0.5, -1.4, 3.0, 1.2, "ash", 1.0)
    if stage == 0:
        ember_dots(r, [(0, -1.6, 3), (1, -1.4, 2)], 1.1)
        smoke_curl(r, 0, -3, 2, 2.0, 0.7)
    else:
        r.dot(0, -1.6, "ember", 1, 1.1)
    return r.resolve()


JOBS_LATE = [("TallowGrub", grub_sheet), ("AshMoth", moth_sheet)]
SYNC_LATE = ({
    "TallowGrub": {"Spit": [("glob leaves the mouth at (10, -4); launch along the floor at (12, -1)", 3)],
                   "Melt": [("collide off, can't be hit", 0), ("melted: the Glide stance takes over (Puddle / Glide)", 4)],
                   "Rise": [("bubbling: the 0.4 s warning", 0), ("BURST: upwelling box 24 x 10 on the feet", 2)]},
    "AshMoth": {"Puff": [("ash cloud leaves the head at (7, -9)", 3)],
                "Dive": [("dive: move 230 px/s, body box on", 2), ("pull out, ash burst at (4, -6)", 5)]},
})
NOTES_LATE = ({"TallowGrub": "Puddle / Glide are the melted stance (only the candle stub shows). Rise starts from the puddle.",
              "AshMoth": "IdleGlow / RunGlow: wing edges burning (within 40 px of fire). Hovers 6-7 px; idle 16 px tall with the hover."})


JOBS = [("Wickling", wick_sheet)]
SYNC = {"Wickling": {"Bite": [("jaws at (14, -3): bite box 10 x 11 centred (10, -6)", 3)],
                     "Dash": [("SPRINT: move 190 px/s, body box on, burning pools dropped behind", 2), ("stumble: move stops", 6),
                              ("the tail has guttered out (Relight)", 7)]}}
NOTES = {"Wickling": "IdleOut/RunOut: the tail guttered (smoke curl, no burns). IdleHot/RunHot: relit white-hot (next bite +0.3, always burns)."}

JOBS += JOBS_LATE
SYNC.update(SYNC_LATE)
NOTES.update(NOTES_LATE)
