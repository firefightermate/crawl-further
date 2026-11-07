"""Mod hero weapons: every hit / projectile effect sheet, and the shop bubbles (drawn in weapon_bubbles.py).

    python3 weapon_rigs.py [outdir]          (default art/out_weapons)

The hero's swing and shoot frames are baked into the vanilla hero atlas (weapon included), so the weapons
keep those frames. What is drawn here is everything the weapon adds: the 34x41 shop bubble (diagonal
portrait like vanilla's, soft-shaded, no outline) and one FX sheet per weapon.

FX convention: every FX cell is drawn with the effect ORIGIN at the cell centre, facing right. The C# side
anchors these sprites MidCenter and offsets them onto the hitbox centre of the vanilla collider they ride on
(see TIMING.md). Solid objects (hooks, dice, arrows...) get a 1px dark outline, light (slashes, rings,
sparks) does not; glow pixels are laid last. Light comes from the top-left.
"""
import json, math, os, random, sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "art", "out_weapons")


# ------------------------------------------------------------------ colours
def hx(s):
    s = s.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


OUTLINE = hx("1e1a1c")
IRON = [hx(c) for c in ("2a2730", "45414c", "6c6874", "9a96a0", "c9c6cc")]
STEEL = [hx(c) for c in ("4a4e5c", "7c8292", "aab0bc", "d6dae0", "f2f4f6")]
RUST = [hx(c) for c in ("4a2618", "7a3c1e", "a85a28", "c88040")]
WOOD = [hx(c) for c in ("3b2418", "5e3a22", "7e5230", "9c6c40", "b88a58")]
BONE = [hx(c) for c in ("6a5e4a", "9c8e72", "c8bc9c", "e8dfc4", "fbf6e6")]
MOON = [hx(c) for c in ("3a4c6a", "6688aa", "9ec4dc", "d2ecf6", "ffffff")]
VOID = [hx(c) for c in ("1c0e2a", "3e1a5c", "6e2a96", "b04ad2", "f08cff")]
RIFT_GLOW = hx("ffd2ff")
GOLD = [hx(c) for c in ("5a3e10", "9a6a1a", "d8a02a", "f6d260", "fff4b8")]
RED = [hx(c) for c in ("3a0a10", "6e1018", "a81c22", "e03a34", "ff8a7a")]
TIDE = [hx(c) for c in ("102a32", "1f4f55", "2f7a7a", "5fb3a8", "a8e0d0", "eafff8")]
LEAF = [hx(c) for c in ("1c2a14", "2e4a1e", "4a7a2a", "7aae3e", "b4dc6a")]
BRONZE = [hx(c) for c in ("36240e", "6a4818", "a0742a", "cfa44a", "f2d890")]
SOUL = [hx(c) for c in ("12302a", "1e5c4a", "3aa07a", "7ee8b4", "d8fff0")]
VOLT = [hx(c) for c in ("101c4a", "2a4ab0", "4a8cf0", "a8d8ff", "ffffff")]
VOLT_Y = hx("fff2a0")


def ramp(r, l):
    """l in [-1, 1] (dark .. light) -> colour from ramp r."""
    i = int((l + 1.0) * 0.5 * len(r))
    return r[max(0, min(len(r) - 1, i))]


# ------------------------------------------------------------------ canvas
# Crawl's palette: effects stay in the muted range of the game's own art. Every colour laid on a canvas is pulled
# towards a warm grey (weapon_bubbles.tame) until it is no more colourful than FX_CAP; glow pixels (the light at the
# heart of an effect, kept small) may go up to FX_GLOW_CAP.
FX_CAP, FX_S, FX_GLOW_CAP, FX_GLOW_S = 0.30, 0.66, 0.44, 0.72
_TAMED = {}


def tamed(c, glow):
    k = (c, glow)
    if k not in _TAMED:
        import weapon_bubbles
        _TAMED[k] = weapon_bubbles.tame(c, FX_GLOW_CAP if glow else FX_CAP, FX_GLOW_S if glow else FX_S)
    return _TAMED[k]


class Cv:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = {}       # (x,y) -> (r,g,b,a)
        self.glow = set()  # pixels never outlined over / laid last

    def put(self, x, y, c, a=255, glow=False, over=True):
        x, y = int(round(x)), int(round(y))
        if not (0 <= x < self.w and 0 <= y < self.h): return
        if not over and (x, y) in self.px: return
        if len(c) == 4: c, a = c[:3], c[3]
        c = tamed(tuple(int(v) for v in c[:3]), glow)
        self.px[(x, y)] = (c[0], c[1], c[2], int(max(0, min(255, a))))
        if glow: self.glow.add((x, y))
        else: self.glow.discard((x, y))

    def line(self, x0, y0, x1, y1, c, a=255, glow=False, w=1):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / max(1, n)
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            self.put(x, y, c, a, glow)
            if w >= 2: self.put(x, y - 1, c, a, glow)
            if w >= 3: self.put(x, y + 1, c, a, glow)

    def disc(self, cx, cy, r, rp, a=255, glow=False, ry=None):
        ry = r if ry is None else ry
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                dx, dy = (x - cx) / max(r, 0.5), (y - cy) / max(ry, 0.5)
                d = dx * dx + dy * dy
                if d > 1.0: continue
                l = -(dx * 0.7 + dy * 0.7) * 0.9 + (0.25 - d * 0.35)
                self.put(x, y, ramp(rp, l), a, glow)

    def ring(self, cx, cy, rx, ry, thick, rp, a=255, glow=False, lit=True):
        R = max(rx, ry) + 2
        for y in range(int(cy - R), int(cy + R) + 1):
            for x in range(int(cx - R), int(cx + R) + 1):
                dx, dy = (x - cx), (y - cy)
                d = math.sqrt((dx / max(rx, 0.5)) ** 2 + (dy / max(ry, 0.5)) ** 2)
                band = thick / max(rx, 1.0)
                if abs(d - 1.0) > band: continue
                l = 0.4
                if lit:
                    ang = math.atan2(dy, dx)
                    l = -math.cos(ang + math.pi * 0.75) * 0.6 + (0.3 - abs(d - 1.0) / band * 0.6)
                self.put(x, y, ramp(rp, l), a, glow)

    def crescent(self, cx, cy, r_out, width, a0, a1, rp, a=255, glow=False, head=1.0):
        """Slash arc around pivot (cx,cy) between angles a0..a1 (deg, 0 = right, y down). Thickest at `head`
        (0..1 along the sweep), tapering to both ends; the outer edge is the bright cutting edge."""
        R = r_out + 1
        for y in range(int(cy - R), int(cy + R) + 1):
            for x in range(int(cx - R), int(cx + R) + 1):
                dx, dy = x - cx, y - cy
                d = math.hypot(dx, dy)
                ang = math.degrees(math.atan2(dy, dx))
                if a1 < a0: a0, a1 = a1, a0
                if not (a0 <= ang <= a1): continue
                t = (ang - a0) / max(1e-3, a1 - a0)
                k = 1.0 - min(1.0, abs(t - head) / max(head, 1 - head, 1e-3))
                wv = max(0.6, width * (0.25 + 0.75 * k))
                if not (r_out - wv <= d <= r_out): continue
                u = (r_out - d) / wv          # 0 at edge .. 1 inner
                self.put(x, y, ramp(rp, 0.95 - u * 1.6 + (k - 0.5) * 0.3), a * (0.55 + 0.45 * k), glow)

    def outline(self, c=OUTLINE, skip_glow=True):
        add = []
        for (x, y), v in self.px.items():
            if skip_glow and (x, y) in self.glow: continue
            if v[3] < 200: continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p = (x + dx, y + dy)
                if p not in self.px and 0 <= p[0] < self.w and 0 <= p[1] < self.h: add.append(p)
        for p in add: self.px[p] = c + (255,)

    def fade(self, k):
        for p, v in list(self.px.items()):
            self.px[p] = (v[0], v[1], v[2], int(v[3] * k))

    def img(self):
        im = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        p = im.load()
        order = sorted(self.px.items(), key=lambda kv: kv[0] in self.glow)
        for (x, y), v in order:
            if v[3] > 0: p[x, y] = v
        return im


# ------------------------------------------------------------------ sheet packer
SHEETS = []


def sheet(name, cw, ch, anims, cols=8):
    """anims: [(animName, [Image], [durations])]. Writes <name>.png/.json/_preview.png."""
    frames, man = [], {"cellW": cw, "cellH": ch, "cols": cols, "anims": []}
    for an, ims, durs in anims:
        idx = []
        for im in ims:
            idx.append(len(frames)); frames.append(im)
        man["anims"].append({"name": an, "frames": idx, "durations": [round(d, 3) for d in durs]})
    rows = (len(frames) + cols - 1) // cols
    W, H = 1, 1
    while W < cols * cw: W *= 2
    while H < rows * ch: H *= 2
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        img.alpha_composite(f, ((i % cols) * cw, (i // cols) * ch))
    os.makedirs(OUT, exist_ok=True)
    img.save(os.path.join(OUT, name + ".png"))
    json.dump(man, open(os.path.join(OUT, name + ".json"), "w"))
    # preview: one row per anim at 4x on a dark floor
    sc = 4
    pw = max(len(a[1]) for a in anims) * (cw + 2) * sc
    ph = len(anims) * (ch + 2) * sc
    pv = Image.new("RGBA", (max(pw, 8), max(ph, 8)), (28, 26, 32, 255))
    for r, (an, ims, _) in enumerate(anims):
        for j, im in enumerate(ims):
            pv.alpha_composite(im.resize((cw * sc, ch * sc), Image.NEAREST), (j * (cw + 2) * sc, r * (ch + 2) * sc))
    pv.convert("RGB").save(os.path.join(OUT, name + "_preview.png"))
    SHEETS.append((name, cw, ch, man))
    return man


# ================================================================== shop bubbles (weapon_bubbles.py)
BW, BH = 34, 41



# ================================================================== FX helpers
def slash_frames(W, H, rp, glint, pivot_dx=-9, r=15, sweep=(-70, 70), width=4.5, spark=None):
    """A melee swipe around a pivot behind the hitbox centre, four posed frames: a narrow lead-in with a bright head,
    the full arc (a heavy body with a honed edge and a faint after-image inside it), the arc tearing away from its
    start, then embers thrown off along the line of the cut."""
    cx, cy = W / 2 + pivot_dx, H / 2
    out = []
    a0, a1 = sweep
    span = a1 - a0
    rnd = random.Random(len(rp) * 7 + r)
    embers = [(rnd.uniform(0.3, 1.0), rnd.uniform(-2.0, 3.0), rnd.uniform(1.0, 3.0)) for _ in range(7)]
    wide = width * 1.3
    for k in range(4):
        cv = Cv(W, H)
        if k == 0:
            s0, s1 = a0, a0 + span * 0.5
            cv.crescent(cx, cy, r, wide * 0.7, s0, s1, rp, head=0.95)
            ang = math.radians(s1)
            sparkle(cv, cx + math.cos(ang) * r, cy + math.sin(ang) * r, glint, 1)
        elif k == 1:
            cv.crescent(cx, cy, r - wide * 0.8, wide * 0.5, a0 + span * 0.1, a1 - span * 0.15, rp, a=90, head=0.8)
            cv.crescent(cx, cy, r, wide, a0, a1, rp, head=0.8)
            for t in (0.5, 0.68, 0.84):
                ang = math.radians(a0 + span * t)
                cv.put(cx + math.cos(ang) * (r + 1), cy + math.sin(ang) * (r + 1), glint, glow=True)
            ang = math.radians(a1 - span * 0.04)
            sparkle(cv, cx + math.cos(ang) * r, cy + math.sin(ang) * r, glint, 2)
        elif k == 2:
            cv.crescent(cx, cy, r + 0.5, wide * 0.6, a0 + span * 0.3, a1, rp, a=215, head=0.85)
            for (t, dr, fly) in embers[:4]:
                ang = math.radians(a0 + span * (0.15 + 0.3 * t))
                cv.put(cx + math.cos(ang) * (r + dr), cy + math.sin(ang) * (r + dr), spark or glint, a=200, glow=True)
        else:
            cv.crescent(cx, cy, r + 1.0, wide * 0.3, a0 + span * 0.65, a1, rp, a=120, head=0.9)
            for (t, dr, fly) in embers:
                ang = math.radians(a0 + span * t)
                tx, ty = -math.sin(ang), math.cos(ang)          # along the sweep
                x = cx + math.cos(ang) * (r + dr) + tx * fly * 2
                y = cy + math.sin(ang) * (r + dr) + ty * fly * 2
                cv.put(x, y, spark or glint, a=150, glow=True)
        out.append(cv.img())
    return out


def thrust_frames(W, H, rp, tip, length, half=2.5, head=None):
    """A straight lunge streak centred in the cell: a pointed spear of light that extends, holds with a bright tip and
    speed lines along it, then thins and breaks into dashes."""
    out = []
    cx, cy = W / 2, H / 2
    for k, (ext, th, al) in enumerate(((0.6, 1.0, 1.0), (1.0, 1.15, 1.0), (1.0, 0.6, 0.8), (1.0, 0.3, 0.45))):
        cv = Cv(W, H)
        x0 = cx - length / 2
        x1 = x0 + length * ext
        for x in range(int(x0), int(x1) + 1):
            t = (x - x0) / max(1.0, x1 - x0)
            if k == 3 and int(x) % 4 == 0: continue
            hw = max(0.5, half * th * (0.25 + 0.75 * t) * (1.0 if t < 0.85 else (1 - t) / 0.15 + 0.2))
            for y in range(int(cy - hw - 1), int(cy + hw + 2)):
                dv = (y - cy) / max(hw, 0.5)
                if abs(dv) > 1.0: continue
                cv.put(x, y, ramp(rp, 0.7 - abs(dv) * 0.9 + t * 0.4 - (y > cy) * 0.35), 255 * al)
        if k in (1, 2):
            for (sx, sy, L) in ((x0 + length * 0.1, cy - half - 2, length * 0.35), (x0 + length * 0.3, cy + half + 2, length * 0.3)):
                for x in range(int(sx), int(sx + L)):
                    cv.put(x, sy, rp[-2], a=110 * al * (1 - (x - sx) / L), glow=True)
        if head and k < 3: head(cv, x1, cy, al)
        cv.put(x1, cy, tip, a=255 * al, glow=True)
        if k == 1:
            sparkle(cv, x1, cy, tip, 2, a=230)
        out.append(cv.img())
    return out


def sparkle(cv, x, y, c, r=2, a=255):
    cv.put(x, y, c, a, True)
    for k in range(1, r + 1):
        al = a * (1 - k / (r + 1.0))
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)): cv.put(x + dx, y + dy, c, al, True, over=False)


# ================================================================== per-weapon FX
def fx_gravehook():
    W, H = 48, 24

    def hookhead(cv, x, y, al):
        for k in range(4):
            cv.put(x - k, y + 1 + k * 0.6, STEEL[2], 255 * al)
        cv.put(x - 3, y + 3, STEEL[3], 255 * al)
    jab = thrust_frames(W, H, IRON + [STEEL[3]], STEEL[4], 36, 2.2, head=hookhead)
    # the thrown hook: a barbed iron hook trailing two chain links (faces right)
    hook = []
    for i in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2 + 4, H // 2
        cv.line(cx - 4, cy, cx + 4, cy, IRON[3])
        cv.line(cx - 4, cy + 1, cx + 3, cy + 1, IRON[1])
        for k in range(5):                                   # curl
            ang = math.radians(90 + k * 40)
            cv.put(cx + 3 + math.cos(ang) * 3, cy - 1 + math.sin(ang) * 3 * (1 if i % 2 == 0 else 0.9), STEEL[3 if k < 2 else 2])
        cv.put(cx + 5, cy, STEEL[4]); cv.put(cx + 6, cy, STEEL[3])
        for j in range(3):                                   # chain trailing back toward the thrower
            x = cx - 7 - j * 4 + (i % 2 if j % 2 else 0)
            yy = cy + (1 if (i // 2 + j) % 2 and j else 0)                # the chain sways as it flies
            cv.put(x, yy, IRON[3]); cv.put(x + 1, yy - 1, IRON[2]); cv.put(x + 2, yy, IRON[3]); cv.put(x + 1, yy + 1, IRON[1])
        cv.outline()
        cv.put(cx + 3 + [-2, 0, 2, 4][i], cy, STEEL[4], glow=True)        # glint running along the shank
        hook.append(cv.img())
    chain = []
    for k in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2 + (k >= 2)                                # the link sags as it fades
        cv.put(cx - 1, cy, IRON[3]); cv.put(cx, cy - 1, IRON[4] if k < 2 else IRON[3]); cv.put(cx + 1, cy, IRON[2]); cv.put(cx, cy + 1, IRON[1])
        cv.put(cx - 2, cy, RUST[2]); cv.put(cx + 2, cy, RUST[1])
        cv.outline()
        cv.fade([1.0, 0.8, 0.55, 0.3][k])
        chain.append(cv.img())
    return sheet("FxWpnGravehook", W, H, [
        ("Jab", jab, [0.04, 0.06, 0.06, 0.06]),
        ("Hook", hook, [0.06, 0.06, 0.06, 0.06]),
        ("Chain", chain, [0.06, 0.06, 0.07, 0.07]),
    ])


def fx_moonglaive():
    W, H = 32, 32
    slash = slash_frames(W, H, MOON, MOON[4], pivot_dx=-9, r=13, width=4.0, spark=MOON[3])
    glaive = []
    for i in range(4):
        # the thrown glaive, spinning: a moon-steel ring with three hooked horns, a wrapped grip across its eye and a
        # faint motion arc trailing each horn
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        rot = -i * math.pi / 6
        for y in range(H):
            for x in range(W):
                dx, dy = x - cx, y - cy
                r = math.hypot(dx, dy)
                ph = ((math.atan2(dy, dx) - rot) % (2 * math.pi / 3)) / (2 * math.pi / 3)
                outer = 5.4 + 3.0 * ph ** 2.2
                if 2.6 <= r <= outer:
                    l = -(dx + dy) / 12.0 + (outer - r) / 4.0 - 0.1
                    if r > outer - 1.0: l += 0.5
                    cv.put(x, y, ramp(MOON, l))
                elif outer < r <= outer + 1.6 and ph > 0.55:
                    cv.put(x, y, MOON[2], a=90, glow=True)
        for t in range(-2, 3):
            cv.put(cx + t * math.cos(rot + 0.8), cy + t * math.sin(rot + 0.8), WOOD[3 if t < 0 else 2])
        for a in (0.0, 2.094, 4.189):
            ang = a + rot - 0.05
            cv.put(cx + math.cos(ang) * 8.2, cy + math.sin(ang) * 8.2, MOON[4], glow=True)
        glaive.append(cv.img())
    return sheet("FxWpnMoonglaive", W, H, [
        ("Slash", slash, [0.05, 0.06, 0.07, 0.07]),
        ("Glaive", glaive, [0.05, 0.05, 0.05, 0.05]),
    ])


def fx_riftblade():
    W, H = 32, 32
    a = slash_frames(W, H, VOID, RIFT_GLOW, pivot_dx=-9, r=14, sweep=(-75, 60), width=4.0, spark=VOID[4])
    b = slash_frames(W, H, VOID, RIFT_GLOW, pivot_dx=-8, r=15, sweep=(-55, 80), width=5.0, spark=VOID[4])
    mark = []
    for i in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        rr = 3.5 + (i % 2) * 0.6
        cv.ring(cx, cy, rr, rr, 0.6, VOID[2:], glow=True, lit=False)
        for k in range(3):                                 # three orbiting motes
            ang = i * math.pi / 6 + k * 2.094
            cv.put(cx + math.cos(ang) * (rr + 2), cy + math.sin(ang) * (rr + 2), VOID[4], glow=True)
        cv.put(cx, cy - 1, RIFT_GLOW, glow=True); cv.put(cx, cy, VOID[3], glow=True); cv.put(cx, cy + 1, RIFT_GLOW, glow=True)
        mark.append(cv.img())
    snap = []
    for i in range(5):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        open_ = [1.0, 0.7, 0.25, 0.0, 0.0][i]
        L = [10, 11, 12, 13, 13][i]
        for y in range(-L, L + 1):                         # a vertical tear that slams shut
            t = 1 - abs(y) / (L + 0.5)
            hw = 3.2 * t * open_
            for x in range(int(-hw - 1), int(hw + 2)):
                if abs(x) <= hw:
                    cv.put(cx + x + y * 0.15, cy + y, ramp(VOID, -0.7 + (hw - abs(x)) * 0.25) if abs(x) > hw - 1 else (12, 4, 20), glow=False)
            if open_ < 0.3 and i < 4 and abs(y) < L * (0.4 + i * 0.2):
                cv.put(cx + y * 0.15, cy + y, RIFT_GLOW, 255 * (1 - (i - 2) * 0.3), glow=True)
        if i >= 2:                                        # snap burst
            rr = 4 + (i - 2) * 4
            cv.ring(cx, cy, rr, rr * 0.8, 0.8, VOID[2:], a=255 * (1 - (i - 2) * 0.3), glow=True, lit=False)
        snap.append(cv.img())
    return sheet("FxWpnRiftblade", W, H, [
        ("SlashA", a, [0.05, 0.06, 0.07, 0.07]),
        ("SlashB", b, [0.05, 0.06, 0.07, 0.07]),
        ("Mark", mark, [0.1, 0.1, 0.1, 0.1]),
        ("Snap", snap, [0.06, 0.05, 0.05, 0.07, 0.09]),
    ])


PIPS = {1: [(0, 0)], 2: [(-2, -2), (2, 2)], 3: [(-2, -2), (0, 0), (2, 2)], 4: [(-2, -2), (2, -2), (-2, 2), (2, 2)],
        5: [(-2, -2), (2, -2), (0, 0), (-2, 2), (2, 2)], 6: [(-2, -2), (2, -2), (-2, 0), (2, 0), (-2, 2), (2, 2)]}


def rig_onto(cv, r, ox, oy, alpha=1.0, glow_mats=()):
    """Resolve a material rig (jinx_v2_rigs.Rig, drawn round (0, 0)) onto a canvas at (ox, oy). The rig's ramps are
    the weapon bubbles' muted materials, so solid things in the effects match the shop art."""
    import weapon_bubbles  # noqa: F401  (registers the w_* ramps)
    s = r.resolve(selout=True, cast=True, contour=True, clean=True, floor=False)
    for (x, y), c in s.px.items():
        cv.put(ox + x, oy + y, tuple(c[:3]), 255 * alpha, s.tones[(x, y)][0] in glow_mats)


def _die_pose(face):
    """(rx, ry) that turns `face` towards the viewer (found by trying the quarter turns)."""
    import jinx_v2_rigs as J
    best = None
    for rx in (0, 90, 180, 270):
        for ry in (0, 90, 180, 270):
            for n, v in J.CUBE:
                z = J.rot3(J.rot3(n, rx, ry, 0), -26.0, 0, 0)[2]
                if v == face and (best is None or z < best[0]): best = (z, rx, ry)
    return best[1], best[2]


def die_img(W, H, face, dy=0, tumble=None, alpha=1.0):
    """An ivory die, a real cube: tumbling (tumble = a seed for its angles) or settled with `face` towards the viewer."""
    import jinx_v2_rigs as J
    cv = Cv(W, H)
    r = J.Rig()
    if tumble is None:
        rx, ry = _die_pose(face)
        J.die3(r, 0.0, 0.0, 8.0, rx=rx - 12, ry=ry + 22, rz=-6, mat="w_bone", pip="w_obsid", one="w_crim", tilt=26.0)
    else:
        rnd = random.Random(tumble)
        J.die3(r, 0.0, 0.0, 8.0, rx=rnd.uniform(0, 360), ry=rnd.uniform(0, 360), rz=rnd.uniform(0, 360),
               mat="w_bone", pip="w_obsid", one="w_crim", tilt=26.0)
    rig_onto(cv, r, W // 2, H // 2 + dy, alpha)
    return cv.img()


def fx_snakeeyes():
    W, H = 32, 32
    rp = [BONE[0], BONE[1], BONE[2], RED[3], BONE[4]]
    swing = slash_frames(W, H, rp, BONE[4], pivot_dx=-9, r=14, sweep=(-80, 65), width=5.0, spark=RED[4])
    anims = [("Swing", swing, [0.05, 0.06, 0.07, 0.08])]
    for f in range(1, 7):
        # pops up tumbling, lands on the face, hangs, fades
        ims = [die_img(W, H, f, dy=2, tumble=f * 11), die_img(W, H, f, dy=-1, tumble=f * 11 + 5), die_img(W, H, f, dy=-2),
               die_img(W, H, f, dy=-2, alpha=0.5)]
        anims.append(("Die%d" % f, ims, [0.06, 0.08, 0.3, 0.1]))
    jack = []
    rnd = random.Random(66)
    coins = [(rnd.uniform(0, 6.28), rnd.uniform(0.6, 1.0), rnd.uniform(0, 3.14)) for _ in range(10)]
    for i in range(5):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        rr = 3 + i * 3.2
        if i < 3: cv.ring(cx, cy, rr, rr * 0.8, 0.9, GOLD[2:], a=255 * (1 - i * 0.25), glow=True, lit=False)
        for (a, s, ph) in coins:
            x, y = cx + math.cos(a) * rr * s * 1.1, cy + math.sin(a) * rr * s * 0.9 - i * 0.8
            if i < 4:
                w = abs(math.cos(ph + i * 0.9))
                cv.put(x, y, GOLD[3]); cv.put(x, y + 1, GOLD[1])
                if w > 0.4: cv.put(x + 1, y, GOLD[2]); cv.put(x + 1, y + 1, GOLD[1])
        if i == 0: sparkle(cv, cx, cy, GOLD[4], 3)
        cv.fade(1.0 - max(0, i - 2) * 0.35)
        jack.append(cv.img())
    anims.append(("Jackpot", jack, [0.05, 0.05, 0.06, 0.07, 0.08]))
    return sheet("FxWpnSnakeEyes", W, H, anims)


def fx_tidebreaker():
    W, H = 48, 40
    cleave = slash_frames(W, H, TIDE, TIDE[5], pivot_dx=-12, r=17, sweep=(-70, 75), width=5.5, spark=TIDE[4])
    crash = slash_frames(W, H, TIDE, TIDE[5], pivot_dx=-12, r=19, sweep=(-100, 40), width=6.5, spark=TIDE[5])
    wave = []
    for i in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        for y in range(-12, 13):                           # a curling wall of water, crest leaning forward
            t = (y + 12) / 24.0
            front = 4 + math.sin(t * math.pi) * 2 - (1 - t) * 3 + math.sin(i * 1.57 + y * 0.6) * 0.8
            back = -7 + t * 2
            for x in range(int(back), int(front) + 1):
                u = (x - back) / max(1.0, front - back)
                c = ramp(TIDE, -0.9 + u * 1.5 + (1 - t) * 0.3)
                cv.put(cx + x, cy + y, c)
            cv.put(cx + front + 1, cy + y, TIDE[5], glow=True)
        for k in range(4):                                 # foam spray off the crest
            cv.put(cx + 6 + k, cy - 12 + ((k + i) % 3), TIDE[5], glow=True)
        wave.append(cv.img())
    splash = []
    for i in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        for k in range(9):
            ang = math.radians(-160 + k * 17.5)
            rr = 4 + i * 3.5
            x, y = cx + math.cos(ang) * rr, cy + math.sin(ang) * rr * 0.8 + i * i * 0.6
            cv.put(x, y, TIDE[4 if k % 2 else 5], a=255 * (1 - i * 0.22), glow=True)
            cv.put(x, y + 1, TIDE[3], a=255 * (1 - i * 0.22))
        if i < 2: cv.ring(cx, cy + 3, 5 + i * 4, (5 + i * 4) * 0.45, 0.7, TIDE[3:], a=200, lit=False)
        splash.append(cv.img())
    return sheet("FxWpnTidebreaker", W, H, [
        ("Cleave", cleave, [0.05, 0.06, 0.07, 0.08]),
        ("Crash", crash, [0.05, 0.07, 0.07, 0.08]),
        ("Wave", wave, [0.07, 0.07, 0.07, 0.07]),
        ("Splash", splash, [0.06, 0.06, 0.07, 0.08]),
    ])


def fx_leechfang():
    W, H = 32, 24
    stab = thrust_frames(W, H, RED, RED[4], 22, 2.0)
    slash = slash_frames(W, H, RED, RED[4], pivot_dx=-8, r=12, sweep=(-65, 65), width=3.5, spark=RED[3])
    bead = []
    for i in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        cv.disc(cx, cy, 1.6 + [0, 0.3, 0.45, 0.3][i], RED)
        cv.put(cx - 2, cy + (i == 3), RED[2], 160); cv.put(cx - 3, cy + (i >= 2) - (i == 0), RED[1], 90)
        cv.put(cx - 1 + (i == 2), cy - 1, RED[4], glow=True)
        bead.append(cv.img())
    heal = []
    rnd = random.Random(5)
    motes = [(rnd.uniform(-6, 6), rnd.uniform(0, 4)) for _ in range(7)]
    for i in range(5):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        for (x, y) in motes:
            yy = cy + 6 - y - i * 2.5
            al = 255 * (1 - i / 5.0)
            cv.put(cx + x, yy, RED[4], al, True); cv.put(cx + x, yy + 1, RED[3], al * 0.6, True)
        if i == 1: sparkle(cv, cx, cy - 2, (255, 210, 200), 2)
        heal.append(cv.img())
    return sheet("FxWpnLeechfang", W, H, [
        ("Stab", stab, [0.04, 0.05, 0.06, 0.06]),
        ("Slash", slash, [0.04, 0.05, 0.06, 0.06]),
        ("Bead", bead, [0.06, 0.06, 0.06, 0.06]),
        ("Heal", heal, [0.06, 0.07, 0.08, 0.09, 0.1]),
    ])


def thorn_patch(W, H, grow, frame, seed=3, dry=0.0):
    """A bramble patch on the floor (footprint ~28 x 12, the 30 x 16 hitbox): a dark soil mound with five thorny canes
    arching out of it, each cane outlined, studded with pale thorns and tipped with a leaf bud. `grow` 0..1 raises the
    canes, `frame` sways them, `dry` 0..1 browns them for the wilt."""
    cx, cy = W // 2, H // 2 + 5
    soil = Cv(W, H)
    rx, ry = 13.0 * min(1.0, 0.55 + grow * 0.6), 4.5 * min(1.0, 0.6 + grow * 0.5)
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d > 1.0: continue
            c = WOOD[1] if d > 0.62 else WOOD[0]
            if d > 0.62 and y < cy: c = WOOD[2]                         # lit rim on the far side
            soil.put(x, y, c, 235)
    cane_c = [LEAF[1], LEAF[2]] if dry < 0.5 else [WOOD[1], WOOD[2]]
    thorn_c = BONE[3] if dry < 0.5 else BONE[1]
    bud_c = [LEAF[3], LEAF[4]] if dry < 0.5 else [RUST[2], RUST[3]]
    canes = [(-9, 1, 8, -1), (-4, -1, 11, 1), (1, 0, 13, -1), (6, -1, 10, 1), (10, 1, 7, -1)]
    cv = Cv(W, H)
    tips = []
    for k, (bx, by, h, lean) in enumerate(canes):
        L = max(1, int(round(h * grow)))
        sway = math.radians(7) * math.sin(frame * math.pi / 2 + k * 1.3)
        x, y = cx + bx, cy + by
        for j in range(L):
            t = j / max(1.0, h - 1.0)
            a = math.radians(-90 + lean * 75 * t * t) + sway * t
            x += math.cos(a); y += math.sin(a)
            cv.put(x, y, cane_c[1] if j % 3 else cane_c[0])
            if j % 2 == 1 and j < L - 1:                               # thorns on alternating sides
                side = 1 if (j // 2) % 2 else -1
                nx, ny = -math.sin(a) * side, math.cos(a) * side
                cv.put(x + nx, y + ny, thorn_c)
        tips.append((x, y))
    cv.outline()
    for k, (x, y) in enumerate(tips):                                   # leaf buds, laid after the outline
        if grow < 0.35: continue
        cv.put(x, y - 1, bud_c[1]); cv.put(x + 1, y - 1, bud_c[0]); cv.put(x, y, bud_c[0])
        if (frame + k) % 4 == 0 and dry < 0.5: cv.put(x, y - 2, LEAF[4], glow=True)
    for pnt, v in cv.px.items():                                        # canes over the soil
        soil.px[pnt] = v
        if pnt in cv.glow: soil.glow.add(pnt)
    return soil


def fx_briarbow():
    W, H = 40, 32
    arrow = []
    for i in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        cv.line(cx - 11, cy, cx + 9, cy, WOOD[3])
        cv.line(cx - 11, cy + 1, cx + 8, cy + 1, WOOD[1])
        for k in range(-8, 8, 4):                         # thorns along the shaft
            cv.put(cx + k, cy - 1, BONE[2]); cv.put(cx + k + 2, cy + 2, BONE[1])
        cv.put(cx + 10, cy, LEAF[3]); cv.put(cx + 11, cy, LEAF[4]); cv.put(cx + 10, cy - 1, LEAF[2]); cv.put(cx + 10, cy + 1, LEAF[2])
        for k in range(3):                                 # leaf fletching
            cv.put(cx - 12 - k, cy - 1 - (k + i) % 2, LEAF[2 + k % 2]); cv.put(cx - 12 - k, cy + 2 + (k + i) % 2, LEAF[1 + k % 2])
        cv.outline()
        cv.put(cx - 8 + i * 5, cy, WOOD[4], glow=True)                       # glint running down the shaft
        arrow.append(cv.img())
    grow = [thorn_patch(W, H, g, 0).img() for g in (0.25, 0.5, 0.75, 0.95)]
    life = [thorn_patch(W, H, 1.0, f).img() for f in range(4)]
    wilt = []
    for k, g in enumerate((0.85, 0.7, 0.5, 0.3)):
        cv = thorn_patch(W, H, g, 1 + k, dry=[0.3, 0.6, 0.8, 1.0][k])
        cv.fade([1.0, 0.8, 0.6, 0.35][k])
        wilt.append(cv.img())
    return sheet("FxWpnBriarbow", W, H, [
        ("Arrow", arrow, [0.066, 0.066, 0.066, 0.066]),
        ("Grow", grow, [0.06, 0.06, 0.07, 0.07]),
        ("Life", life, [0.105, 0.105, 0.105, 0.105]),
        ("Wilt", wilt, [0.06, 0.06, 0.06, 0.06]),
    ])


def fx_dirgemaul():
    W, H = 80, 56
    clang = []
    for i in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        rr = [3, 6, 8, 9][i]
        al = [1.0, 1.0, 0.6, 0.3][i]
        for k in range(8):                                 # star burst of bronze shards
            ang = math.radians(k * 45 + 22)
            cv.line(cx + math.cos(ang) * (rr - 3), cy + math.sin(ang) * (rr - 3),
                    cx + math.cos(ang) * rr, cy + math.sin(ang) * rr, GOLD[3 if k % 2 else 4], 255 * al, True)
        if i < 2: sparkle(cv, cx, cy, GOLD[4], 3 - i)
        clang.append(cv.img())

    def rings(rmax, n, base_a):
        out = []
        for i in range(n):
            cv = Cv(W, H)
            cx, cy = W // 2, H // 2
            t = (i + 1) / float(n)
            rr = 5 + (rmax - 5) * (1 - (1 - t) ** 2)
            al = base_a * (1.0 if i < n - 2 else (0.6 if i == n - 2 else 0.3))
            cv.ring(cx, cy, rr, rr * 0.62, 1.1, BRONZE[1:], a=255 * al, glow=True)
            cv.ring(cx, cy, rr * 0.8, rr * 0.62 * 0.8, 0.6, GOLD[2:], a=150 * al, glow=True, lit=False)
            for k in range(6):                             # sound-wave ticks
                ang = math.radians(k * 60 + i * 12)
                cv.put(cx + math.cos(ang) * (rr + 2), cy + math.sin(ang) * (rr + 2) * 0.62, GOLD[4], 255 * al, True)
            out.append(cv.img())
        return out
    return sheet("FxWpnDirgeMaul", W, H, [
        ("Clang", clang, [0.04, 0.05, 0.06, 0.07]),
        ("Ring", rings(26, 6, 1.0), [0.04, 0.04, 0.05, 0.05, 0.06, 0.07]),
        ("Toll", rings(38, 6, 1.0), [0.05, 0.05, 0.06, 0.06, 0.07, 0.08]),
    ])


def fx_wickstaff():
    W, H = 32, 32
    swing = slash_frames(W, H, SOUL, SOUL[4], pivot_dx=-8, r=13, sweep=(-60, 70), width=3.5, spark=SOUL[3])
    bolt = []
    for i in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        for k in range(5):                                 # wispy tail
            cv.put(cx - 3 - k, cy + math.sin(i * 1.57 + k) * 0.8, SOUL[2 + (k < 2)], 255 * (1 - k * 0.18), True)
        cv.disc(cx, cy, 2.6 + (i % 2) * 0.4, SOUL[1:], glow=True)
        cv.put(cx - 1, cy - 1, SOUL[4], glow=True); cv.put(cx, cy - 1, SOUL[4], glow=True)
        bolt.append(cv.img())
    fire = []
    rnd = random.Random(9)
    tongues = [(rnd.uniform(-8, 8), rnd.uniform(-3, 3), rnd.randint(3, 7)) for _ in range(9)]
    for i in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2 + 3
        for y in range(-3, 4):
            for x in range(-10, 11):
                if (x / 10.0) ** 2 + (y / 3.5) ** 2 <= 1.0: cv.put(cx + x, cy + y, SOUL[1], 140, True)
        for k, (x, y, h) in enumerate(tongues):
            hh = h + ((i + k) % 3) - 1
            for j in range(hh):
                c = SOUL[2] if j < hh * 0.4 else (SOUL[3] if j < hh * 0.8 else SOUL[4])
                cv.put(cx + x + math.sin(j * 0.7 + i + k) * 0.7, cy + y - j, c, 230, True)
        fire.append(cv.img())
    wisp = []
    for i in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        cv.disc(cx, cy, 1.8 + (i % 2) * 0.3, SOUL[2:], glow=True)
        for k in range(4):
            cv.put(cx - 2 - k, cy + [-1, 0, 1, 0][(k + i) % 4], SOUL[3], 200 - k * 40, True)
        cv.put(cx + [0, 0, -1, 1][i], cy - 2, SOUL[4], glow=True)
        wisp.append(cv.img())
    return sheet("FxWpnWickstaff", W, H, [
        ("Swing", swing, [0.05, 0.06, 0.07, 0.07]),
        ("Bolt", bolt, [0.06, 0.06, 0.06, 0.06]),
        ("Fire", fire, [0.1, 0.1, 0.1, 0.1]),
        ("Wisp", wisp, [0.06, 0.06, 0.06, 0.06]),
    ])


def fx_arcbolt():
    W, H = 48, 24
    bolt = []
    for i in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        cv.line(cx - 8, cy, cx + 6, cy, IRON[3]); cv.line(cx - 8, cy + 1, cx + 5, cy + 1, IRON[1])
        cv.put(cx + 7, cy, STEEL[4]); cv.put(cx + 8, cy, STEEL[3]); cv.put(cx + 7, cy - 1, STEEL[2]); cv.put(cx + 7, cy + 1, STEEL[2])
        cv.outline()
        rnd = random.Random(i + 11)
        for k in range(5):                                # crackle wrapped round the bolt
            x = cx - 7 + k * 3
            cv.put(x, cy - 2 + rnd.randint(0, 1), VOLT[3], glow=True)
            cv.put(x + 1, cy + 2 - rnd.randint(0, 1), VOLT[4] if k % 2 else VOLT_Y, glow=True)
        bolt.append(cv.img())
    arc = []
    for i in range(4):
        cv = Cv(W, H)
        rnd = random.Random(40 + i)
        y = H // 2
        pts = [(0, y)]
        for x in range(4, W, 4):
            pts.append((x, H // 2 + rnd.randint(-3, 3)))
        pts.append((W - 1, H // 2))
        al = [1.0, 0.9, 0.65, 0.35][i]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            cv.line(x0, y0 - 1, x1, y1 - 1, VOLT[2], 140 * al, True)
            cv.line(x0, y0, x1, y1, VOLT[4] if i == 0 else VOLT[3], 255 * al, True)
        arc.append(cv.img())
    spark = []
    for i in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        rr = 2 + i * 2
        for k in range(6):
            ang = math.radians(k * 60 + i * 20)
            cv.line(cx + math.cos(ang) * (rr - 2), cy + math.sin(ang) * (rr - 2), cx + math.cos(ang) * rr,
                    cy + math.sin(ang) * rr, VOLT_Y if k % 2 else VOLT[3], 255 * (1 - i * 0.22), True)
        if i < 2: sparkle(cv, cx, cy, VOLT[4], 2)
        spark.append(cv.img())
    return sheet("FxWpnArcbolt", W, H, [
        ("Bolt", bolt, [0.066, 0.066, 0.066, 0.066]),
        ("Arc", arc, [0.04, 0.04, 0.05, 0.05]),
        ("Spark", spark, [0.04, 0.05, 0.06, 0.07]),
    ])


FX = [fx_gravehook, fx_moonglaive, fx_riftblade, fx_snakeeyes, fx_tidebreaker, fx_leechfang, fx_briarbow,
      fx_dirgemaul, fx_wickstaff, fx_arcbolt]


# ================================================================== v0.7.2: fifteen more weapons
ICE = [hx(c) for c in ("1c3448", "2f5f86", "5c9cc8", "a6dcf2", "e8fbff")]
PALE = [hx(c) for c in ("26302c", "4a5a52", "7e9488", "b8ccbe", "eef6ee")]
NIGHT = [hx(c) for c in ("0e0a1a", "241a3c", "3c2e66", "6a5aa8", "b0a4e8")]
STARGOLD = [hx(c) for c in ("4a3410", "8a6a20", "d8b040", "fbe48a", "fffbe0")]
SCALE = [hx(c) for c in ("102a22", "1e4a3a", "2f7a5a", "5ab48a", "a8e8c4")]
CRIMSON = [hx(c) for c in ("2a060c", "5c0e1a", "9a1a2c", "d8344a", "ff8aa0")]
SHADE = [hx(c) for c in ("0a0810", "1c1428", "34264a", "5a4682", "9a86c8")]
BLIGHT = [hx(c) for c in ("1c2008", "3a4a10", "6a8a1a", "aed23a", "eaff9a")]
BRASS = [hx(c) for c in ("3a2a10", "6a4e1e", "a07c34", "d4ae5a", "f6e2a0")]
LEATHER = [hx(c) for c in ("2a1a10", "4a2e1a", "6e4428", "946038", "b88456")]
VENOM = [hx(c) for c in ("102010", "1e4018", "2e6e22", "5aa83a", "a6e070")]
GRUDGE = [hx(c) for c in ("1a0c0c", "3a1616", "5e2424", "8a3a32", "b45a48")]




def burst(W, H, rp, n, rmax, spokes=8, seed=0, ring=True):
    """Generic impact burst: spokes flying out from the cell centre, optional ring, fading."""
    out = []
    rnd = random.Random(seed)
    angs = [rnd.uniform(0, math.pi * 2) for _ in range(spokes)]
    for i in range(n):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        t = (i + 1) / float(n)
        r = 2 + (rmax - 2) * t
        al = 1.0 if i < n - 2 else (0.65 if i == n - 2 else 0.35)
        for a in angs:
            cv.line(cx + math.cos(a) * r * 0.55, cy + math.sin(a) * r * 0.55, cx + math.cos(a) * r, cy + math.sin(a) * r,
                    rp[3 if i else 4], 255 * al, True)
        if ring and i < n - 1: cv.ring(cx, cy, r * 0.8, r * 0.65, 0.6, rp[2:], a=200 * al, glow=True, lit=False)
        if i == 0: sparkle(cv, cx, cy, rp[-1], 3)
        out.append(cv.img())
    return out


def ice_shard(r, x, y, ang, ln, wd, z):
    """A shaded ice crystal: a tapering prism, lit from the top left, with a bright tip."""
    tip = (x + math.cos(ang) * ln, y + math.sin(ang) * ln)
    r.tube([(x, y), tip], [wd, 0.4], "w_ice", z, bias=0.15)
    r.dot(tip[0], tip[1], "w_frost", 3, z + 0.1)


def fx_frostbrand():
    W, H = 48, 40
    import jinx_v2_rigs as J
    slash = slash_frames(W, H, ICE, ICE[4], pivot_dx=-9, r=13, width=4.0, spark=ICE[3])

    def flake(cv, x, y, big):
        cv.put(x, y, ICE[4], glow=True)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            cv.put(x + dx, y + dy, ICE[3], 200 if big else 120, True, over=False)
        if big:
            for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)): cv.put(x + dx, y + dy, ICE[2], 130, True, over=False)
    # Chill = 1 stack (three small flakes circling), Chill2 = 2 stacks (a ring of rime crystals on the floor and five
    # flakes circling: one more chill shatters)
    chill, chill2 = [], []
    for i in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        for k in range(3):
            ang = k * 2 * math.pi / 3 + i * (2 * math.pi / 3) / 4
            flake(cv, cx + math.cos(ang) * 7, cy + math.sin(ang) * 3, False)
        chill.append(cv.img())
        cv = Cv(W, H)
        for k in range(72):                                             # frost creeping on the floor
            a = k * math.pi / 36
            x, y = cx + math.cos(a) * 10, cy + 6 + math.sin(a) * 2.6
            cv.put(x, y, ICE[2] if math.sin(a) > 0 else ICE[1], 200, True)
        r = J.Rig()
        for k in range(8):                                              # rime crystals jutting up out of it
            a = k * math.pi / 4 + math.pi / 8
            x, y = math.cos(a) * 10, 6 + math.sin(a) * 2.6
            grow = [0.7, 0.85, 1.0, 0.92][i]
            ln = (3.0 + 1.6 * ((k * 5 + i) % 3)) * grow
            lean = math.radians(-90 + math.cos(a) * 30)
            ice_shard(r, x, y, lean, ln, 1.2, 1 + math.sin(a))
        rig_onto(cv, r, cx, cy)
        for k in range(5):
            ang = k * 2 * math.pi / 5 + i * (2 * math.pi / 5) / 4
            flake(cv, cx + math.cos(ang) * 9, cy - 4 + math.sin(ang) * 3, k == 0)
        chill2.append(cv.img())
    shatter = []
    rnd = random.Random(12)
    shards = [(rnd.uniform(0, 6.28), rnd.uniform(0.6, 1.0), rnd.uniform(0, 6.28), rnd.uniform(2.0, 4.0)) for _ in range(10)]
    for i in range(5):
        # the frozen monster bursts: a white flash, then shaded ice chunks thrown out and spinning, a cold ring
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        rad = 2 + i * 4.5
        al = [1, 1, 0.9, 0.6, 0.35][i]
        if i < 2: cv.disc(cx, cy, 5 - i * 2, ICE, a=230, glow=True)
        r = J.Rig()
        for (a, s, spin, ln) in shards:
            x, y = math.cos(a) * rad * s, math.sin(a) * rad * s * 0.7 + i * i * 0.3
            ice_shard(r, x, y, spin + i * 0.9, ln * (1 - i * 0.12), 1.0, 2)
        rig_onto(cv, r, cx, cy, al)
        if 1 <= i < 4: cv.ring(cx, cy, rad * 1.15, rad * 0.75, 0.7, ICE[2:], a=180 * al, glow=True, lit=False)
        shatter.append(cv.img())
    return sheet("FxWpnFrostbrand", W, H, [
        ("Slash", slash, [0.05, 0.06, 0.07, 0.07]),
        ("Chill", chill, [0.1, 0.1, 0.1, 0.1]),
        ("Chill2", chill2, [0.1, 0.1, 0.1, 0.1]),
        ("Shatter", shatter, [0.04, 0.05, 0.06, 0.07, 0.08]),
    ])


def fx_mercyblade():
    W, H = 32, 32
    rp = [STEEL[0], STEEL[1], STEEL[2], STARGOLD[3], STEEL[4]]
    slash = slash_frames(W, H, rp, STARGOLD[4], pivot_dx=-9, r=14, sweep=(-75, 60), width=3.2, spark=STARGOLD[3])
    mercy = []
    for i in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        L = [4, 8, 9, 9][i]
        al = [1, 1, 0.6, 0.3][i]
        for s in (1, -1):                                               # the finishing X
            cv.line(cx - L, cy - L * s, cx + L, cy + L * s, CRIMSON[3], 255 * al, True, w=2)
            cv.line(cx - L, cy - L * s, cx + L, cy + L * s, STARGOLD[4], 255 * al, True)
        if i < 2: sparkle(cv, cx, cy, STARGOLD[4], 3)
        mercy.append(cv.img())
    return sheet("FxWpnMercyblade", W, H, [
        ("Slash", slash, [0.05, 0.06, 0.07, 0.07]),
        ("Mercy", mercy, [0.05, 0.06, 0.08, 0.1]),
    ])


def fx_reaper():
    W, H = 48, 40
    reap = slash_frames(W, H, PALE, PALE[4], pivot_dx=-12, r=18, sweep=(-85, 70), width=5.0, spark=PALE[3])
    reap2 = slash_frames(W, H, PALE, PALE[4], pivot_dx=-12, r=19, sweep=(-60, 95), width=6.0, spark=PALE[4])
    soul = []
    for i in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        cv.disc(cx, cy, 2.2 + (i % 2) * 0.3, PALE[1:], glow=True)
        for k in range(4):
            cv.put(cx - 2 - k, cy + [0, 1, 0, -1][(k + i) % 4], PALE[3], 220 - k * 45, True)
        cv.put(cx + (i == 2), cy - 1, PALE[4], glow=True)
        soul.append(cv.img())
    # Stacks1..5: the harvested souls circling the hero's head, one wisp per stack (10% damage each)
    stacks = []
    SW, SH = 32, 16
    for n in range(1, 6):
        frames = []
        for i in range(4):
            cv = Cv(SW, SH)
            cx, cy = SW // 2, SH // 2 + 1
            ws = []
            for k in range(n):
                a = k * 2 * math.pi / n + i * (2 * math.pi / n) / 4
                ws.append((math.sin(a), a))
            for sn, a in sorted(ws):                                     # back ones first, dimmer
                x, y = int(round(cx + math.cos(a) * 10)), int(round(cy + sn * 3))
                al = 255 if sn >= 0 else 170
                for dx, dy in ((-1, 0), (2, 0), (0, 1), (1, 1), (0, -2), (1, -2)):   # soft glow round the flame
                    cv.put(x + dx, y + dy, PALE[2], al * 0.55, True, over=False)
                cv.put(x, y, PALE[4], al, True); cv.put(x + 1, y, PALE[4], al, True)
                cv.put(x, y - 1, (240, 255, 244), al, True); cv.put(x + 1, y - 1, PALE[3], al, True)
                cv.put(x + (i % 2), y - 2, PALE[3], al * 0.9, True)     # flickering tip
                cv.put(x + (i % 2), y - 3, PALE[2], al * 0.6, True, over=False)
            frames.append(cv.img())
        stacks.append(("Stacks%d" % n, frames))
    sheet("FxWpnReaperStacks", SW, SH, [(n, f, [0.1, 0.1, 0.1, 0.1]) for n, f in stacks])
    return sheet("FxWpnReaper", W, H, [
        ("Reap", reap, [0.05, 0.06, 0.07, 0.08]),
        ("Reap2", reap2, [0.05, 0.06, 0.07, 0.08]),
        ("Soul", soul, [0.07, 0.07, 0.07, 0.07]),
    ])


def fx_starfall():
    W, H = 80, 56
    slam = burst(W, H, STARGOLD, 4, 12, spokes=8, seed=3)
    well = []
    for i in range(8):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        if i < 6:                                                       # swirling dark well drawing everything in
            r = 30 - i * 3.5
            for k in range(5):
                for j in range(14):
                    a = k * 1.2566 + i * 0.5 + j * 0.12
                    rr = r * (1 - j / 18.0)
                    cv.put(cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.6, NIGHT[2 + (j > 7)], 230, True)
            cv.disc(cx, cy, 3 + i * 0.4, NIGHT, glow=True)
            cv.put(cx, cy, STARGOLD[4], glow=True)
        else:                                                           # implosion flash
            cv.disc(cx, cy, 8 - (i - 6) * 2, STARGOLD, a=255 - (i - 6) * 90, glow=True)
            cv.ring(cx, cy, 14 + (i - 6) * 6, 8 + (i - 6) * 4, 0.9, STARGOLD[2:], a=230 - (i - 6) * 100, glow=True, lit=False)
        well.append(cv.img())
    return sheet("FxWpnStarfall", W, H, [
        ("Slam", slam, [0.04, 0.05, 0.06, 0.07]),
        ("Well", well, [0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.06, 0.08]),
    ])


def arrowhead_frames(W, H, length, rp_shaft, head, fletch, n=4):
    out = []
    for i in range(n):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        cv.line(cx - length // 2, cy, cx + length // 2 - 2, cy, rp_shaft[3]); cv.line(cx - length // 2, cy + 1, cx + length // 2 - 3, cy + 1, rp_shaft[1])
        hx_ = cx + length // 2
        cv.put(hx_ - 1, cy, head[3]); cv.put(hx_, cy, head[4]); cv.put(hx_ - 1, cy - 1, head[2]); cv.put(hx_ - 1, cy + 1, head[2])
        for k in range(3):
            cv.put(cx - length // 2 - k, cy - 1 - (k + i) % 2, fletch[2 + k % 2]); cv.put(cx - length // 2 - k, cy + 2, fletch[1])
        cv.outline()
        cv.put(cx - length // 2 + 2 + i * (length - 6) // n, cy, rp_shaft[4], glow=True)   # glint running down the shaft
        out.append(cv.img())
    return out


def fx_hydrabow():
    W, H = 40, 24
    arrow = arrowhead_frames(W, H, 20, WOOD, SCALE, SCALE)
    shard = []
    for i in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        cv.line(cx - 5, cy, cx + 3, cy, SCALE[3]); cv.put(cx + 4, cy, SCALE[4]); cv.put(cx + 3, cy - 1, SCALE[2]); cv.put(cx + 3, cy + 1, SCALE[2])
        cv.put(cx - 6 - i % 2, cy + (i >= 2) - (i == 3), SCALE[2], 150)
        cv.outline()
        cv.put(cx - 4 + i * 2, cy, SCALE[4], glow=True)
        shard.append(cv.img())
    split = burst(W, H, SCALE, 5, 8, spokes=6, seed=5, ring=False)
    return sheet("FxWpnHydraBow", W, H, [
        ("Arrow", arrow, [0.066, 0.066, 0.066, 0.066]),
        ("Shard", shard, [0.066, 0.066, 0.066, 0.066]),
        ("Split", split, [0.04, 0.04, 0.05, 0.06, 0.07]),
    ])


def fx_bulwark():
    W, H = 40, 32
    rp = [IRON[0], IRON[1], hx("3e6aa6"), hx("6a96d0"), STEEL[4]]
    bash = slash_frames(W, H, rp, STEEL[4], pivot_dx=-10, r=13, sweep=(-60, 60), width=5.5, spark=hx("9ec4f0"))
    guard = []
    for i in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        cv.ring(cx, cy, 11, 7, 0.55, [hx("2a4a7a"), hx("3e6aa6"), hx("6a96d0"), hx("c8e0ff")], a=170, glow=True, lit=False)
        for k in range(4):                                              # four runes circling
            a = k * math.pi / 2 + i * math.pi / 8
            cv.put(cx + math.cos(a) * 11, cy + math.sin(a) * 7, hx("e0f0ff"), glow=True)
        guard.append(cv.img())
    block = burst(W, H, [hx("1a2a4a"), hx("2a4a7a"), hx("3e6aa6"), hx("9ec4f0"), hx("ffffff")], 4, 13, spokes=10, seed=8)
    return sheet("FxWpnBulwark", W, H, [
        ("Bash", bash, [0.05, 0.06, 0.07, 0.08]),
        ("Guard", guard, [0.1, 0.1, 0.1, 0.1]),
        ("Block", block, [0.04, 0.05, 0.06, 0.08]),
    ])


def fx_heartseeker():
    W, H = 48, 24
    bolt = []
    for i in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        cv.line(cx - 9, cy, cx + 5, cy, CRIMSON[2]); cv.line(cx - 9, cy + 1, cx + 4, cy + 1, CRIMSON[1])
        for (x, y) in ((6, 0), (7, 0), (5, -1), (6, -1), (5, 1), (6, 1), (4, -2), (4, 2)):
            cv.put(cx + x, cy + y, CRIMSON[3] if x > 4 else CRIMSON[4])
        cv.outline()
        j = [0, 1, 2, 1][i]
        cv.put(cx - 10 - j, cy, CRIMSON[3], 140, True); cv.put(cx - 13 - j, cy, CRIMSON[2], 90, True)
        cv.put(cx - 7 + i * 3, cy, CRIMSON[4], glow=True)                  # glint running down the shaft
        bolt.append(cv.img())
    pierce = burst(W, H, CRIMSON, 4, 8, spokes=6, seed=21, ring=False)
    return sheet("FxWpnHeartseeker", W, H, [
        ("Bolt", bolt, [0.066, 0.066, 0.066, 0.066]),
        ("Pierce", pierce, [0.04, 0.05, 0.06, 0.07]),
    ])


def fx_kris():
    W, H = 32, 24
    stab = thrust_frames(W, H, SHADE, SHADE[4], 22, 2.0)
    back = []
    for i in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        al = [1, 1, 0.6, 0.3][i]
        L = [3, 7, 8, 8][i]
        cv.line(cx - L, cy + L * 0.6, cx + L, cy - L * 0.6, SHADE[3], 255 * al, True, w=2)
        cv.line(cx - L, cy + L * 0.6, cx + L, cy - L * 0.6, CRIMSON[4], 255 * al, True)
        cv.line(cx - L * 0.6, cy - L * 0.6, cx + L * 0.6, cy + L * 0.6, SHADE[4], 200 * al, True)
        if i < 2: sparkle(cv, cx, cy, CRIMSON[4], 2)
        back.append(cv.img())
    return sheet("FxWpnKris", W, H, [
        ("Stab", stab, [0.04, 0.05, 0.06, 0.06]),
        ("Backstab", back, [0.04, 0.06, 0.08, 0.1]),
    ])


def fx_blightstaff():
    W, H = 32, 32
    swing = slash_frames(W, H, BLIGHT, BLIGHT[4], pivot_dx=-8, r=13, sweep=(-60, 70), width=3.5, spark=BLIGHT[3])
    bolt = []
    for i in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        cv.disc(cx, cy, 2.8 + (i % 2) * 0.4, BLIGHT[1:], glow=True)
        for k in range(4):
            cv.put(cx - 3 - k, cy + ((k + i) % 3) - 1, BLIGHT[2], 220 - k * 50, True)
        cv.put(cx - 1, cy - 1, BLIGHT[4], glow=True)
        bolt.append(cv.img())
    cloud = []
    rnd = random.Random(31)
    motes = [(rnd.uniform(-7, 7), rnd.uniform(-5, 4)) for _ in range(9)]
    for i in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        for k, (x, y) in enumerate(motes):
            yy = cy + y - ((i + k) % 4)
            cv.put(cx + x, yy, BLIGHT[3 if (i + k) % 2 else 2], 200, True)
            if k % 3 == 0: cv.put(cx + x + 1, yy, BLIGHT[1], 150, True)
        cloud.append(cv.img())
    spore = []
    for i in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        cv.disc(cx, cy, 1.7 + (i % 2) * 0.3, BLIGHT[2:], glow=True)
        cv.put(cx - 2, cy + [0, 1, 0, -1][i], BLIGHT[2], 150, True)
        cv.put(cx - 3, cy + [1, 0, -1, 0][i], BLIGHT[1], 100, True)
        spore.append(cv.img())
    return sheet("FxWpnBlightstaff", W, H, [
        ("Swing", swing, [0.05, 0.06, 0.07, 0.07]),
        ("Bolt", bolt, [0.06, 0.06, 0.06, 0.06]),
        ("Cloud", cloud, [0.1, 0.1, 0.1, 0.1]),
        ("Spore", spore, [0.06, 0.06, 0.06, 0.06]),
    ])


def fx_orrery():
    W, H = 32, 32
    rp = [NIGHT[1], NIGHT[2], NIGHT[3], MOON[3], MOON[4]]
    swing = slash_frames(W, H, rp, MOON[4], pivot_dx=-8, r=13, sweep=(-60, 70), width=3.5, spark=MOON[3])
    bolt = []
    for i in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        for k in range(4):                                              # four-point star bolt
            a = k * math.pi / 2 + (i % 2) * math.pi / 4
            cv.line(cx, cy, cx + math.cos(a) * 3.5, cy + math.sin(a) * 3.5, MOON[3], glow=True)
        cv.put(cx, cy, MOON[4], glow=True)
        cv.put(cx - 4, cy, NIGHT[3], 160, True); cv.put(cx - 6, cy, NIGHT[2], 100, True)
        bolt.append(cv.img())
    star = []
    for i in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        cv.disc(cx, cy, 2.4, MOON, glow=True)
        for k in range(4):
            a = k * math.pi / 2 + i * math.pi / 8
            cv.put(cx + math.cos(a) * 4, cy + math.sin(a) * 4, MOON[4] if k % 2 else STARGOLD[4], glow=True)
        star.append(cv.img())
    return sheet("FxWpnOrrery", W, H, [
        ("Swing", swing, [0.05, 0.06, 0.07, 0.07]),
        ("Bolt", bolt, [0.05, 0.05, 0.05, 0.05]),
        ("Star", star, [0.08, 0.08, 0.08, 0.08]),
    ])


def pebble_frames(W, H, paint, n=4):
    """A lobbed sling shot: drawn sitting on the cell's lower part (vanilla sling art is BotCenter, 2 px up)."""
    out = []
    for i in range(n):
        cv = Cv(W, H)
        paint(cv, W // 2, H - 6, i)
        out.append(cv.img())
    return out


def floor_shadow(W, H, rx, ry):
    """The lobbed shot's ground shadow (replaces the sling's generic 14x3 blob): a soft dark oval on the cell's bottom
    rows (the vanilla Shadow child is BotCenter, offset (-0.5, -1); its tint keeps alpha ~0.54)."""
    cv = Cv(W, H)
    cx, cy = (W - 1) / 2.0, H - 1 - ry
    for y in range(H - 2 * int(ry) - 2, H):
        for x in range(W):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d <= 1.0: cv.put(x, y, hx("120e16"), 255 if d < 0.55 else 150)
    return cv.img()


def fx_grudgestone():
    W, H = 24, 24
    import jinx_v2_rigs as J
    shape = [(-4.0, -0.7), (-2.4, -3.5), (0.7, -4.0), (3.5, -2.4), (4.2, 0.9), (2.4, 3.5), (-0.9, 4.0), (-3.5, 2.6)]

    def stone(cv, x, y, i):
        # a heavy cursed stone tumbling through the air, a red grudge rune cut in it
        a = i * math.pi / 4
        ca, sa = math.cos(a), math.sin(a)
        r = J.Rig()
        r.poly([(px * ca - py * sa, px * sa + py * ca) for px, py in shape], "w_stone", 1, normal=(-0.2, -0.3, 0.9))
        r.ell(-0.6, -0.8, 2.2, 1.8, "w_stone", 1.1, bias=0.25)
        for k, (px, py) in enumerate(((0, -1.4), (0, 0), (0, 1.4), (-1.2, -0.6), (1.2, 0.6))):
            r.dot(px * ca - py * sa, px * sa + py * ca, "w_heart", 3 if k == 1 else 2, 2)
        rig_onto(cv, r, x, y, glow_mats=("w_heart",))
    rock = pebble_frames(W, H, stone, 8)
    mark = []
    for i in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        for k in range(3):                                              # a smouldering grudge brand over a monster
            a = -math.pi / 2 + (k - 1) * 0.5
            cv.put(cx + math.cos(a) * 4, cy + math.sin(a) * 4 - (i % 2), CRIMSON[3 + (k == 1)], 230, True)
        cv.put(cx, cy, CRIMSON[4], glow=True); cv.put(cx, cy + 1, CRIMSON[2], glow=True); cv.put(cx, cy + 3, CRIMSON[4], glow=True)
        mark.append(cv.img())
    return sheet("FxWpnGrudgestone", W, H, [
        ("Stone", rock, [0.05] * 8),
        ("Grudge", mark, [0.12, 0.12, 0.12, 0.12]),
        ("Shadow", [floor_shadow(W, H, 3.6, 1.1)], [1.0]),
    ])


def fx_midas():
    W, H = 24, 24
    import jinx_v2_rigs as J

    def coin(cv, x, y, i, tier=0):
        # a thick gold coin flipping end over end: a lit face, a milled rim showing as it turns, a stamped crown
        wdt = [3.4, 3.0, 2.2, 1.2, 0.8, 1.2, 2.2, 3.0][i]
        back = i in (4, 5, 6)
        r = J.Rig()
        if wdt > 1.0:
            r.ell(0.6, 0.0, wdt, 3.4, "w_gold", 1, bias=0.1 if back else 0.25)
            r.ell(-0.2, -0.3, max(0.6, wdt - 1.2), 2.2, "w_gold", 1.2, bias=0.5 if not back else 0.2)
        r.tube([(0.0 - (0 if wdt > 1 else 0), -3.2), (0.0, 3.2)], [0.8, 0.8], "w_bronze", 0.9)
        if wdt > 2.0 and not back:
            r.dot(-0.4, -0.6, "w_bronze", 1, 1.4); r.dot(0.6, -0.6, "w_bronze", 1, 1.4)
        rig_onto(cv, r, x, y)
        if tier >= 1:                                                   # gold power: a glint riding the coin
            a = i * math.pi / 4
            sparkle(cv, x + math.cos(a) * 5, y - 1 + math.sin(a) * 4, GOLD[4], 1)
        if tier >= 2:                                                   # rich: a halo and a second glint
            for k in range(10):
                a = k * math.pi / 5 + i * math.pi / 20
                cv.put(x + math.cos(a) * 5.5, y + math.sin(a) * 5.5, GOLD[3], 150, True, over=False)
            a = i * math.pi / 4 + math.pi
            sparkle(cv, x + math.cos(a) * 5, y - 1 + math.sin(a) * 4, (255, 255, 236), 2)
    coin_ = [pebble_frames(W, H, lambda cv, x, y, i, t=t: coin(cv, x, y, i, t), 8) for t in range(3)]
    gold = burst(W, H, GOLD, 4, 9, spokes=7, seed=40, ring=False)
    return sheet("FxWpnMidas", W, H, [
        ("Coin", coin_[0], [0.05] * 8),
        ("Coin2", coin_[1], [0.05] * 8),
        ("Coin3", coin_[2], [0.05] * 8),
        ("Gold", gold, [0.05, 0.06, 0.07, 0.09]),
        ("Shadow", [floor_shadow(W, H, 3.6, 1.1)], [1.0]),
    ])


def fx_lance():
    W, H = 64, 32
    thrust = thrust_frames(W, H, STEEL, STEEL[4], 40, 2.2)
    charge = []
    for k, (ext, th, al) in enumerate(((0.6, 1.0, 1.0), (1.0, 1.0, 1.0), (1.0, 0.6, 0.75), (1.0, 0.3, 0.4))):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        x0 = cx - 26
        x1 = x0 + 52 * ext
        for x in range(int(x0), int(x1) + 1):                           # a heavy streak with a red core
            t = (x - x0) / max(1.0, x1 - x0)
            hw = max(0.6, 4.2 * th * (0.3 + 0.7 * t))
            for y in range(int(cy - hw - 1), int(cy + hw + 2)):
                dv = abs(y - cy) / max(hw, 0.6)
                if dv > 1: continue
                c = CRIMSON[3] if dv < 0.3 else ramp(STEEL, 0.7 - dv)
                cv.put(x, y, c, 255 * al)
        for r in (6, 10):                                               # shock rings at the tip
            if k < 3: cv.ring(x1 - 2, cy, r * 0.5, r, 0.6, STEEL[2:], a=200 * al, glow=True, lit=False)
        cv.put(x1, cy, STEEL[4], 255 * al, True)
        charge.append(cv.img())
    # Ready: the next thrust is a charge (shown at the hero's feet while running has built it up)
    ready = []
    for i in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        cv.ring(cx, cy, 10, 3.8, 0.95, [CRIMSON[1], CRIMSON[2], CRIMSON[3], CRIMSON[4]], a=220, glow=True, lit=False)
        for k in range(2):                                              # two glints racing round the ring
            a = k * math.pi + i * math.pi / 4
            sparkle(cv, cx + math.cos(a) * 10, cy + math.sin(a) * 3.6, STEEL[4], 1)
        for k in range(3):                                              # dust and sparks kicked up, rising
            a = k * 2 * math.pi / 3 + 0.5
            x = cx + math.cos(a) * 7
            y = cy - 1 - ((i + k * 2) % 4) * 1.5
            cv.put(x, y, CRIMSON[4] if k % 2 else STEEL[4], 230 - ((i + k * 2) % 4) * 50, True)
        ready.append(cv.img())
    return sheet("FxWpnLance", W, H, [
        ("Thrust", thrust, [0.04, 0.06, 0.06, 0.06]),
        ("Charge", charge, [0.04, 0.06, 0.07, 0.08]),
        ("Ready", ready, [0.08, 0.08, 0.08, 0.08]),
    ])


def fx_lash():
    W, H = 64, 24
    # cell centre = hitbox centre x 19 px from the hand; the lash runs from hand (x -17) to tip (x +25)
    lash = []
    for i in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        reach = [0.55, 1.0, 1.0, 1.0][i]
        al = [1, 1, 0.7, 0.35][i]
        x0, x1 = cx - 17, cx - 17 + 42 * reach
        prev = None
        for x in range(int(x0), int(x1) + 1):
            t = (x - x0) / 42.0
            y = cy + math.sin(t * math.pi * 1.5 + i * 0.9) * (3.5 * (1 - t) + 0.5) * (1 if i < 2 else 0.5)
            if prev: cv.line(prev[0], prev[1], x, y, VENOM[2 + (t > 0.7)], 255 * al)
            cv.put(x, y + 1, VENOM[1], 200 * al)
            prev = (x, y)
        if i >= 1: cv.put(x1, prev[1], VENOM[4], 255 * al, True)
        lash.append(cv.img())
    crack = []
    for i in range(4):                                                  # the crack at the tip: drawn centred on the tip box
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        r = [2, 5, 7, 8][i]
        al = [1, 1, 0.6, 0.3][i]
        for k in range(6):
            a = k * math.pi / 3 + 0.3
            cv.line(cx + math.cos(a) * (r - 2), cy + math.sin(a) * (r - 2) * 0.7, cx + math.cos(a) * r, cy + math.sin(a) * r * 0.7,
                    VENOM[4] if k % 2 else STEEL[4], 255 * al, True)
        if i < 2: sparkle(cv, cx, cy, (255, 255, 230), 2)
        crack.append(cv.img())
    return sheet("FxWpnLash", W, H, [
        ("Lash", lash, [0.04, 0.05, 0.06, 0.07]),
        ("Crack", crack, [0.04, 0.05, 0.06, 0.07]),
    ])


def fx_kunai():
    W, H = 32, 24
    import jinx_v2_rigs as J
    kunai = []
    for i in range(4):
        # the thrown kunai: a dark leaf blade, a red-wrapped grip, a ring pommel, its tassel snapping behind it
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        r = J.Rig()
        r.poly([(1.0, 0.0), (3.5, -2.0), (8.5, 0.0), (3.5, 2.0)], "w_iron", 2, normal=(-0.1, -0.5, 0.85))
        r.line(1.5, 0, 7.5, 0, "w_steel", 2.1, 3 if i % 2 else 2)
        r.tube([(-4.5, 0.0), (1.0, 0.0)], [0.8, 0.8], "w_crim", 1.5)
        for x in (-3.5, -1.5, 0.5):
            r.dot(x, -1, "w_crim", 1, 1.6)
        for a in range(0, 360, 30):
            r.dot(-6.2 + math.cos(math.radians(a)) * 1.5, math.sin(math.radians(a)) * 1.5, "w_steel", 2 if a > 180 else 3, 1.4)
        wav = [0.0, 1.0, 0.0, -1.0][i]
        r.polyline([(-7.6, 0.6), (-9.6, 1.0 + wav), (-11.6, 1.6 - wav * 0.5)], "w_cloth", 1, 3)
        rig_onto(cv, r, cx, cy)
        cv.put(cx + 3 + i, cy - 1, STEEL[4], glow=True)                 # glint running along the blade
        kunai.append(cv.img())
    slash = slash_frames(W, H, [SHADE[0], SHADE[1], SHADE[2], CRIMSON[3], STEEL[4]], STEEL[4], pivot_dx=-8, r=10, sweep=(-70, 70),
                         width=3.0, spark=CRIMSON[4])
    mark = []
    for i in range(4):
        cv = Cv(W, H)
        cx, cy = W // 2, H // 2
        r = 5 - (i % 2) * 0.6
        cv.ring(cx, cy, r, r, 0.5, CRIMSON[2:], glow=True, lit=False)
        for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):             # crosshair ticks
            cv.line(cx + dx * (r + 1), cy + dy * (r + 1), cx + dx * (r + 3), cy + dy * (r + 3), CRIMSON[4], glow=True)
        mark.append(cv.img())
    pop = burst(W, H, CRIMSON, 4, 9, spokes=8, seed=55)
    return sheet("FxWpnKunai", W, H, [
        ("Kunai", kunai, [0.066, 0.066, 0.066, 0.066]),
        ("Slash", slash, [0.04, 0.05, 0.06, 0.06]),
        ("Mark", mark, [0.1, 0.1, 0.1, 0.1]),
        ("Pop", pop, [0.04, 0.05, 0.06, 0.08]),
    ])


FX2 = [fx_frostbrand, fx_mercyblade, fx_reaper, fx_starfall, fx_hydrabow, fx_bulwark, fx_heartseeker, fx_kris,
       fx_blightstaff, fx_orrery, fx_grudgestone, fx_midas, fx_lance, fx_lash, fx_kunai]


# ================================================================== v0.8: projectile impacts
# One sheet per projectile weapon, FxWpn<Id>Impact, replacing the vanilla contacts its template carried
# (ContactSkeletonArcher's 6-frame blood streak on monsters, ContactGenericSmall / ContactGenericWall's 5-frame star
# on walls). Hit: 6 frames over 0.40 s, drawn round the cell centre and spraying toward +x (the contact spawns it
# rotated to point back along the shot, like vanilla). Wall: 5 frames over 0.35 s, radial, never rotated.
IW, IH = 32, 32
HIT_A = [1.0, 1.0, 0.9, 0.7, 0.45, 0.25]
HIT_D = [0.05, 0.06, 0.06, 0.07, 0.08, 0.08]
WALL_A = [1.0, 1.0, 0.8, 0.5, 0.25]
WALL_D = [0.05, 0.06, 0.07, 0.08, 0.09]


def ease(t):
    return 1.0 - (1.0 - t) ** 2


def motes(seed, n, bias, spread, rmin, rmax):
    rnd = random.Random(seed)
    return [(math.radians(bias + rnd.uniform(-spread, spread)), rnd.uniform(rmin, rmax), rnd.random()) for _ in range(n)]


def fly(cv, cx, cy, parts, t, al, head, tail=None, grav=0.0, sq=0.8, streak=1.6, solid=False):
    """Particles thrown out from (cx, cy): head pixel plus a short trailing streak; grav pulls them down (px at t=1).
    Solid particles are little shaded chunks: lit at the top left, the tail colour underneath."""
    for a, r, s in parts:
        rr = r * ease(t)
        dy = grav * t * t
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr * sq + dy
        if solid:
            cv.put(x, y, head, 255 * al); cv.put(x + 1, y, tail or head, 255 * al)
            if s > 0.4: cv.put(x, y + 1, tail or head, 255 * al); cv.put(x + 1, y + 1, OUTLINE, 200 * al, over=False)
        else:
            cv.put(x, y, head, 255 * al, True)
        if tail is not None and rr > 2 and not solid:
            cv.put(cx + math.cos(a) * (rr - streak), cy + math.sin(a) * (rr - streak) * sq + dy * 0.8, tail, 190 * al, True, over=False)


def star(cv, cx, cy, L, core, arm, al=1.0, diag=0):
    cv.put(cx, cy, core, 255 * al, True)
    for k in range(1, L + 1):
        a = 255 * al * (1 - (k - 1) / (L + 0.5))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            cv.put(cx + dx * k, cy + dy * k, core if k == 1 else arm, a, True, over=False)
    for k in range(1, diag + 1):
        for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            cv.put(cx + dx * k, cy + dy * k, arm, 210 * al * (1 - k / (diag + 1.0)), True, over=False)


def flash_ring(cv, cx, cy, t, al, rp, rmax=9, sq=0.75, thick=0.6):
    r = 2 + (rmax - 2) * ease(t)
    cv.ring(cx, cy, r, r * sq, thick, rp, a=220 * al, glow=True, lit=False)


def impact_sheet(name, hit, wall=None):
    """hit(cv, cx, cy, i, t, al) / wall(...) paint one frame each; frames are assembled with the shared timings."""
    anims = []
    fr = []
    for i in range(6):
        cv = Cv(IW, IH)
        hit(cv, IW // 2, IH // 2, i, i / 5.0, HIT_A[i])
        fr.append(cv.img())
    anims.append(("Hit", fr, HIT_D))
    if wall is not None:
        fr = []
        for i in range(5):
            cv = Cv(IW, IH)
            wall(cv, IW // 2, IH // 2, i, i / 4.0, WALL_A[i])
            fr.append(cv.img())
        anims.append(("Wall", fr, WALL_D))
    return sheet(name, IW, IH, anims)


# ---- Gravehook: the barbs bite (two claws snap shut), rust and iron sparks fly back
def imp_gravehook():
    sp = motes(101, 9, 0, 75, 8, 14)

    def hit(cv, cx, cy, i, t, al):
        if i < 5:                                                       # a trap of iron teeth snapping shut on the point
            gap = [7, 4, 2, 1, 1][i]
            for s in (-1, 1):
                by = cy + s * (gap + 3)                                 # the jaw bar
                for x in range(-4, 5):
                    cv.put(cx + x, by, IRON[3] if x < 2 else IRON[2], 255 * al)
                for tx in (-2, 2):                                      # two fangs per jaw, pointing at the bite
                    for h in range(3):
                        for w in range(-(2 - h) // 1, (2 - h) + 1):
                            if abs(w) > 1 - h // 2: continue
                            cv.put(cx + tx + w, by - s * (h + 1), STEEL[4] if (h == 2 or w < 0) else STEEL[2], 255 * al)
        if i == 0: star(cv, cx, cy, 4, (255, 244, 220), RUST[3], diag=2)
        if i in (2, 3): star(cv, cx + 1, cy, 3 - (i - 2), (255, 244, 220), RUST[3], al, diag=1)
        fly(cv, cx, cy, sp, t, al, RUST[3] if i < 3 else RUST[2], IRON[3], grav=4)
    return impact_sheet("FxWpnGravehookImpact", hit)


# ---- Moonglaive: a thin crescent nick of moonlight, silver motes
def imp_moonglaive():
    sp = motes(102, 8, 0, 80, 5, 12)
    rd = motes(112, 10, 0, 180, 11, 14)

    def crescent_cut(cv, cx, cy, i, al):
        sweep = [(-70, -10), (-80, 40), (-80, 70), (-40, 80), (10, 80), (40, 80)][i]
        cv.crescent(cx - 4, cy, 7, 2.2, sweep[0], sweep[1], MOON, a=255 * al, glow=True, head=0.7)

    def hit(cv, cx, cy, i, t, al):
        crescent_cut(cv, cx, cy, i, al)
        if i == 0: star(cv, cx + 2, cy, 4, MOON[4], MOON[3], diag=2)
        if i == 1: star(cv, cx + 2, cy, 2, MOON[4], MOON[3], diag=1)
        fly(cv, cx, cy, sp, t, al, MOON[4] if i < 3 else MOON[3], MOON[2])

    def wall(cv, cx, cy, i, t, al):
        if i == 0: star(cv, cx, cy, 5, MOON[4], MOON[3], diag=2)
        if 1 <= i: flash_ring(cv, cx, cy, t, al, MOON[1:], 9)
        if i == 1: star(cv, cx, cy, 3, MOON[4], MOON[3], al, diag=1)
        fly(cv, cx, cy, rd, t, al, MOON[4], MOON[2], grav=3)
    return impact_sheet("FxWpnMoonglaiveImpact", hit, wall)


# ---- Tidebreaker: a burst of spray and a flat foam ring
def imp_tidebreaker():
    dr = motes(103, 12, -20, 110, 6, 14)

    def hit(cv, cx, cy, i, t, al):
        if i == 0:
            cv.disc(cx, cy, 3, TIDE[2:], glow=True); star(cv, cx, cy, 5, TIDE[5], TIDE[4], diag=2)
        if i >= 1:
            r = 3 + 9 * ease(t)
            cv.ring(cx, cy + 3, r, r * 0.35, 0.7, TIDE[2:], a=210 * al, glow=True, lit=False)   # foam on the floor
        for a, rr, s in dr:                                              # droplets: up and out, then falling
            d = rr * ease(t)
            x = cx + math.cos(a) * d
            y = cy + math.sin(a) * d * 0.7 - 6 * math.sin(math.pi * min(1.0, t * 1.2)) * s + 5 * t * t
            cv.put(x, y, TIDE[5] if s > 0.6 else TIDE[4], 255 * al, True)
            if s > 0.4 and i < 4: cv.put(x, y + 1, TIDE[3], 180 * al, True, over=False)
    return impact_sheet("FxWpnTidebreakerImpact", hit)


# ---- Wickstaff: the soul flame bursts and licks upward
def imp_wickstaff():
    rnd = random.Random(104)
    tongues = [(rnd.uniform(-5, 5), rnd.randint(5, 10), rnd.random()) for _ in range(7)]
    sp = motes(114, 8, 0, 80, 7, 12)
    rd = motes(124, 9, -90, 120, 8, 12)

    def tongues_at(cv, cx, cy, t, al, flat=1.0):
        for k, (x, h, s) in enumerate(tongues):
            hh = int(h * min(1.0, 0.45 + t * 1.6) * (1.25 - t)) + 1
            for j in range(hh):
                c = SOUL[2] if j < hh * 0.4 else (SOUL[3] if j < hh * 0.8 else SOUL[4])
                cv.put(cx + x * flat + math.sin(j * 0.8 + k) * 0.7, cy + 1 - j - t * 4, c, 240 * al, True)

    def hit(cv, cx, cy, i, t, al):
        if i == 0: cv.disc(cx, cy, 3.2, SOUL[1:], glow=True); star(cv, cx, cy, 5, SOUL[4], SOUL[3], diag=2)
        else: tongues_at(cv, cx, cy, t, al)
        fly(cv, cx, cy, sp, t, al, SOUL[4], SOUL[2], grav=-5)

    def wall(cv, cx, cy, i, t, al):
        if i == 0: star(cv, cx, cy, 5, SOUL[4], SOUL[3], diag=2)
        else:
            flash_ring(cv, cx, cy + 2, t, al, SOUL[1:], 8, sq=0.4)
            tongues_at(cv, cx, cy + 2, t, al * 0.9, 1.3)
        fly(cv, cx, cy, rd, t, al, SOUL[4], SOUL[2], grav=-4)
    return impact_sheet("FxWpnWickstaffImpact", hit, wall)


# ---- Arcbolt: forked lightning crackles out of the struck point
def fork(cv, cx, cy, ang, length, seed, c, al, jitter=1.6):
    rnd = random.Random(seed)
    x, y = cx, cy
    steps = max(2, int(length / 2.5))
    for k in range(steps):
        a = ang + rnd.uniform(-0.9, 0.9) * (0.6 if k == 0 else 1.0)
        nx, ny = x + math.cos(a) * 2.5, y + math.sin(a) * 2.5 * 0.8 + rnd.uniform(-jitter, jitter) * 0.3
        cv.line(x, y, nx, ny, c, 255 * al, True)
        x, y = nx, ny
    cv.put(x, y, VOLT[4], 255 * al, True)


def imp_arcbolt():
    def hit(cv, cx, cy, i, t, al):
        n = [5, 5, 4, 3, 2, 1][i]
        L = [5, 9, 11, 10, 8, 6][i]
        for k in range(n):
            a = math.radians(-70 + k * (140.0 / max(1, n - 1)) if n > 1 else 0)
            fork(cv, cx, cy, a, L, 300 + i * 10 + k, VOLT[3] if (k + i) % 2 else VOLT_Y, al)
        if i < 2: star(cv, cx, cy, 4 - i * 2, VOLT[4], VOLT_Y, al, diag=2 - i)
        elif i < 4: cv.put(cx, cy, VOLT[3], 255 * al, True)

    sp = motes(105, 10, 90, 70, 4, 9)

    def wall(cv, cx, cy, i, t, al):
        if i == 0: star(cv, cx, cy, 5, VOLT[4], VOLT_Y, diag=2)
        if i >= 1:
            n = [0, 6, 5, 3, 2][i]
            for k in range(n):
                fork(cv, cx, cy, k * 2 * math.pi / max(1, n) + i, [0, 6, 9, 9, 7][i], 400 + i * 10 + k, VOLT[3] if k % 2 else VOLT_Y, al)
            fly(cv, cx, cy, sp, t, al, VOLT_Y, VOLT[2], grav=6)     # sparks dropping off the wall
    return impact_sheet("FxWpnArcboltImpact", hit, wall)


# ---- Hydra Bow: three fang gashes and green venom; on walls the arrow splinters
def imp_hydrabow():
    sp = motes(106, 9, 0, 70, 7, 13)
    chips = motes(116, 8, -90, 130, 10, 14)

    def hit(cv, cx, cy, i, t, al):
        shown = [1, 2, 3, 3, 3, 3][i]
        for k in range(shown):                                          # three fang gashes, one per head
            ox = (k - 1) * 3
            L = 5 if k == 1 else 4
            for j in range(L):
                c = SCALE[4] if j < 2 and i < 3 else SCALE[3]
                cv.put(cx + ox - 1 + j * 0.5, cy - 2 + j, c, 255 * al * (1 if i < 4 else 0.7), True)
        if i == 0: star(cv, cx, cy, 4, SCALE[4], SCALE[3], diag=2)
        fly(cv, cx, cy, sp, t, al, SCALE[4] if i < 3 else SCALE[3], SCALE[2], grav=5)

    def wall(cv, cx, cy, i, t, al):
        if i == 0: star(cv, cx, cy, 5, SCALE[4], SCALE[3], diag=2)
        if 1 <= i <= 3: flash_ring(cv, cx, cy, t, al, SCALE[1:], 8)
        fly(cv, cx, cy, chips, t, al, WOOD[3], WOOD[1], grav=7, solid=True)   # splintered shaft
    return impact_sheet("FxWpnHydraBowImpact", hit, wall)


# ---- Heartseeker: a heart-red diamond flash as the bolt punches through
def imp_heartseeker():
    sp = motes(107, 10, 0, 60, 6, 14)
    chips = motes(117, 8, -90, 120, 10, 14)

    def diamond(cv, cx, cy, r, al, c):
        for k in range(int(r * 4) + 4):
            a = k * 2 * math.pi / (int(r * 4) + 4)
            x, y = math.cos(a), math.sin(a)
            n = abs(x) + abs(y)
            cv.put(cx + x / n * r, cy + y / n * r * 0.9, c, 255 * al, True)

    def hit(cv, cx, cy, i, t, al):
        if i == 0: star(cv, cx, cy, 4, CRIMSON[4], CRIMSON[3], diag=2)
        if 1 <= i <= 4: diamond(cv, cx, cy, [0, 3, 5, 7, 8][i], al, CRIMSON[4] if i < 3 else CRIMSON[3])
        if i in (1, 2): cv.put(cx, cy, (255, 236, 240), 255, True)
        fly(cv, cx, cy, sp, t, al, CRIMSON[4], CRIMSON[2], grav=4)

    def wall(cv, cx, cy, i, t, al):
        if i == 0: star(cv, cx, cy, 5, (255, 236, 240), CRIMSON[3], diag=2)
        if 1 <= i <= 3: diamond(cv, cx, cy, [0, 4, 7, 9][i], al, CRIMSON[3])
        fly(cv, cx, cy, chips, t, al, IRON[3], IRON[1], grav=7, solid=True)
    return impact_sheet("FxWpnHeartseekerImpact", hit, wall)


# ---- Blightstaff: a toxic splat of blobs and drips
def imp_blightstaff():
    blobs = motes(108, 8, 0, 85, 5, 11)
    drips = motes(118, 9, 0, 180, 5, 10)

    def splat(cv, cx, cy, parts, t, al, grav):
        for a, r, s in parts:
            d = r * ease(t)
            x, y = cx + math.cos(a) * d, cy + math.sin(a) * d * 0.8 + grav * t * t
            rr = 1.4 if s > 0.5 else 0.9
            cv.disc(x, y, rr * (1.2 - t * 0.5), BLIGHT[1:], a=255 * al, glow=True)
            if t > 0.3: cv.put(x, y + 1 + (s > 0.6), BLIGHT[2], 200 * al, True, over=False)

    def hit(cv, cx, cy, i, t, al):
        if i == 0: cv.disc(cx, cy, 3.6, BLIGHT[1:], glow=True); star(cv, cx, cy, 5, BLIGHT[4], BLIGHT[3], diag=1)
        if 1 <= i <= 3: cv.ring(cx, cy, 2 + i * 2.2, (2 + i * 2.2) * 0.8, 0.5, BLIGHT[2:], a=180 * al, glow=True, lit=False)
        splat(cv, cx, cy, blobs, t, al, 4)

    def wall(cv, cx, cy, i, t, al):
        if i == 0: cv.disc(cx, cy, 4, BLIGHT[1:], glow=True); star(cv, cx, cy, 2, BLIGHT[4], BLIGHT[3])
        else: splat(cv, cx, cy, drips, t, al, 7)
    return impact_sheet("FxWpnBlightstaffImpact", hit, wall)


# ---- Orrery: a four-point star twinkles with motes orbiting it
def imp_orrery():
    sp = motes(109, 7, 0, 80, 5, 11)
    rd = motes(119, 10, 0, 180, 11, 14)

    def twinkle(cv, cx, cy, L, rot, al):
        for k in range(4):
            a = k * math.pi / 2 + rot
            for j in range(1, L + 1):
                cv.put(cx + math.cos(a) * j, cy + math.sin(a) * j, MOON[4] if j < L * 0.5 else MOON[3], 255 * al * (1 - j / (L + 1.5)), True)
        cv.put(cx, cy, (255, 255, 255), 255 * al, True)

    def hit(cv, cx, cy, i, t, al):
        twinkle(cv, cx, cy, [4, 6, 5, 4, 3, 2][i], (i % 2) * math.pi / 4, al)
        for k in range(3):                                              # three motes orbiting the twinkle
            a = k * 2 * math.pi / 3 + i * 0.6
            cv.put(cx + math.cos(a) * (4 + i), cy + math.sin(a) * (3 + i * 0.7), STARGOLD[4] if k else NIGHT[4], 255 * al, True)
        if i >= 2: fly(cv, cx, cy, sp, t, al, STARGOLD[3], NIGHT[3])

    def wall(cv, cx, cy, i, t, al):
        if i == 0: twinkle(cv, cx, cy, 6, 0, 1.0); star(cv, cx, cy, 2, (255, 255, 255), MOON[3], diag=3)
        else:
            flash_ring(cv, cx, cy, t, al, [NIGHT[2], NIGHT[3], MOON[3], MOON[4]], 9)
            twinkle(cv, cx, cy, [0, 3, 2, 2, 1][i], math.pi / 4, al)
            fly(cv, cx, cy, rd, t, al, STARGOLD[4], STARGOLD[2], grav=3)
    return impact_sheet("FxWpnOrreryImpact", hit, wall)


# ---- Grudgestone: rock chips and a smouldering ember; on walls a dust puff
def imp_grudgestone():
    chips = motes(110, 7, 0, 80, 5, 11)
    embers = motes(120, 5, -60, 60, 4, 9)
    wchips = motes(130, 8, -90, 140, 8, 12)
    rnd = random.Random(140)
    dust = [(rnd.uniform(-6, 6), rnd.uniform(-3, 3), rnd.uniform(1.6, 2.6)) for _ in range(6)]

    def puff(cv, cx, cy, t, al, k=1.0):
        for x, y, r in dust:
            rr = r * (0.6 + t) * k
            cv.disc(cx + x * (0.5 + t) * k, cy + y * (0.5 + t) * k - t * 3, rr, [GRUDGE[4], BONE[0], BONE[1], BONE[2]],
                    a=170 * al * (1 - t * 0.5), glow=True)

    def hit(cv, cx, cy, i, t, al):
        if i == 0: star(cv, cx, cy, 4, CRIMSON[4], CRIMSON[3], diag=2)
        if 1 <= i <= 4: puff(cv, cx, cy, t, al * 0.8, 0.7)
        fly(cv, cx, cy, chips, t, al, GRUDGE[4], BONE[1], grav=8, solid=True)
        fly(cv, cx, cy, embers, t, al, CRIMSON[4], CRIMSON[2], grav=-3)

    def wall(cv, cx, cy, i, t, al):
        if i == 0: star(cv, cx, cy, 5, BONE[4], GRUDGE[4], diag=2)
        else: puff(cv, cx, cy, t, al, 1.0)
        fly(cv, cx, cy, wchips, t, al, GRUDGE[4], BONE[1], grav=9, solid=True)
    return impact_sheet("FxWpnGrudgestoneImpact", hit, wall)


# ---- Midas Sling: a gold clink glint and a spray of gold flecks
def imp_midas():
    sp = motes(111, 10, 0, 75, 5, 12)
    rd = motes(121, 10, 0, 180, 10, 13)

    def glint(cv, cx, cy, L, al):
        for k in range(4):
            a = k * math.pi / 2
            for j in range(1, L + 1):
                cv.put(cx + math.cos(a) * j, cy + math.sin(a) * j * 1.2, GOLD[4] if j < 3 else GOLD[3], 255 * al * (1 - j / (L + 1.0)), True)
        cv.put(cx, cy, (255, 255, 236), 255 * al, True)

    def hit(cv, cx, cy, i, t, al):
        if i < 3: glint(cv, cx, cy, [5, 6, 3][i], al)
        if 1 <= i <= 4: cv.ring(cx, cy, 2 + i * 2, (2 + i * 2) * 0.7, 0.55, GOLD[2:], a=200 * al, glow=True, lit=False)
        fly(cv, cx, cy, sp, t, al, GOLD[4] if i % 2 == 0 else GOLD[3], GOLD[2], grav=6)

    def wall(cv, cx, cy, i, t, al):
        if i < 2: glint(cv, cx, cy, [6, 3][i], al)
        if i >= 1: flash_ring(cv, cx, cy, t, al, GOLD[1:], 8)
        fly(cv, cx, cy, rd, t, al, GOLD[4], GOLD[2], grav=6)
    return impact_sheet("FxWpnMidasImpact", hit, wall)


# ---- Hunter's Kunai: a dark X nick with a crimson spurt; on walls steel sparks
def imp_kunai():
    sp = motes(112, 8, 0, 60, 5, 12)
    rd = motes(122, 9, -90, 120, 9, 13)

    def hit(cv, cx, cy, i, t, al):
        L = [3, 5, 6, 6, 5, 4][i]
        for s in (1, -1):
            cv.line(cx - L, cy - L * s * 0.8 + 1, cx + L, cy + L * s * 0.8 + 1, CRIMSON[2], 220 * al, True)
            cv.line(cx - L, cy - L * s * 0.8, cx + L, cy + L * s * 0.8, STEEL[4] if i < 2 else (STEEL[3] if i < 4 else SHADE[4]), 255 * al, True)
        if i < 3: star(cv, cx, cy, 2 - (i > 0), (255, 240, 240), CRIMSON[4], al)
        fly(cv, cx, cy, sp, t, al, CRIMSON[3], CRIMSON[1], grav=5)

    def wall(cv, cx, cy, i, t, al):
        if i == 0: star(cv, cx, cy, 5, STEEL[4], STEEL[2], diag=2)
        if i == 1: star(cv, cx, cy, 2, STEEL[4], STEEL[2], 0.8, diag=1)
        if 1 <= i <= 3: flash_ring(cv, cx, cy, t, al, [SHADE[2], SHADE[3], STEEL[2], STEEL[3]], 8)
        fly(cv, cx, cy, rd, t, al, STEEL[4] if i < 3 else STEEL[3], CRIMSON[2], grav=7)
    return impact_sheet("FxWpnKunaiImpact", hit, wall)


IMPACTS = [imp_gravehook, imp_moonglaive, imp_tidebreaker, imp_wickstaff, imp_arcbolt, imp_hydrabow, imp_heartseeker,
           imp_blightstaff, imp_orrery, imp_grudgestone, imp_midas, imp_kunai]



def build_bubbles():
    """The shop bubbles (drawn in weapon_bubbles.py) and their contact board in the art dir."""
    import weapon_bubbles
    for name in weapon_bubbles.ICONS:
        sheet("IconWpn%sBubble" % name, BW, BH, [("Bubble", weapon_bubbles.frames(name), [0.5, 0.5])])
    names = list(weapon_bubbles.ICONS)
    cols = 9
    rows = (len(names) + cols - 1) // cols
    board = Image.new("RGBA", (cols * (BW + 4) + 4, rows * (BH + 4) + 4), (28, 26, 32, 255))
    for i, name in enumerate(names):
        b = Image.open(os.path.join(OUT, "IconWpn%sBubble.png" % name)).crop((0, 0, BW, BH))
        board.alpha_composite(b, (4 + (i % cols) * (BW + 4), 4 + (i // cols) * (BH + 4)))
    board.resize((board.width * 4, board.height * 4), Image.NEAREST).save(os.path.join(OUT, "board.png"))


def build():
    os.makedirs(OUT, exist_ok=True)
    build_bubbles()
    for fn in FX + FX2 + IMPACTS:
        fn()
    for n, cw, ch, m in SHEETS:
        print("built %-26s %dx%d  %s" % (n, cw, ch, ", ".join("%s %d" % (a["name"], len(a["frames"])) for a in m["anims"])))


if __name__ == "__main__":
    build()
