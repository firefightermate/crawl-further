"""Mod weapon art in the hero's hands.

    python3 tools/sprites/weapon_hands.py [contact.png]     (default: build/boards/weapon_hands.png)

The hero swings vanilla frames whose weapon is baked into the hero atlas (AtlasHero). For every hero frame a mod
weapon's clips use (idle, run, every attack clip and its aim-angle variants) this script makes a new frame:

  1. the vanilla frame, rebuilt on its untrimmed canvas (exAtlas trimRect, y counted from the top; BotCenter anchor)
  2. the vanilla weapon pixels found by colour (the base weapon's own palette, which no body pixel uses) and erased
  3. the new weapon drawn in their place: straight weapons are fitted as a grip->tip axis (PCA of the erased
     pixels; grip = hilt colour / end nearest the body, tip = head colour / far end) and re-drawn with the new
     silhouette (scythe blade, mace head, bell, lantern, lance cone...); swing smears are recoloured as smears in
     the weapon's colours; bows, crossbows and slings keep their shape with new colours and added parts
  4. every non-weapon pixel stays byte-identical; new pixels only go where the frame was empty or weapon

New weapon colours are "raw" ramp colours: bin-centred RGB whose _ColorRamp slot is pink (= draw the atlas colour)
in all four player ramps and is not (or next to) any slot a hero-atlas colour uses. So the paletted hero shader
draws them as they are, origin/player colours keep working on the body, and no origin, weapon or status colour swap
(all of which start from hero-atlas slots and fill only their neighbours) can ever recolour them.

Output per weapon: art/out_weapons/WpnHand_<id>.png/.json (+ _preview.png). The json is a normal grid manifest (one
anim "Frames") plus "hero": [[src, cell, origW, origH, x, y, w, h], ...]: AtlasHero element src is replaced by
grid cell `cell` whose top-left w x h pixels go at (x, y) of an origW x origH canvas (trimRect, y from the top).
Deterministic: no randomness, sorted iteration.
"""
import json, math, os, sys, warnings
from collections import Counter

from PIL import Image, ImageDraw

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import weapon_looks as WL  # noqa: E402
import weapon_bubbles as WB  # noqa: E402
from hero_looks import Clips, slot, load_ramp, atlas_colours, RAMPS, BOARDS, PINK, ROLES  # noqa: E402

ROLES_VEST = ROLES["vestM"] + ROLES["vestL"]

ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "art", "out_weapons")
CONTACT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BOARDS, "weapon_hands.png")
H = WL.H

# ------------------------------------------------------------------ vanilla weapon pixels per base (atlas colours)
WEAPON_COLS = {
    "WeaponSpear": [(101, 60, 42), (137, 102, 59), (203, 203, 203), (119, 81, 51), (181, 171, 164)],
    "WeaponThrowingKnives": [(203, 203, 203), (68, 85, 116), (187, 189, 193)],
    "Weapon1HandedSword": [(203, 203, 203), (68, 85, 116)],
    "WeaponClub": [(111, 72, 47), (126, 89, 54), (203, 203, 203), (154, 124, 64), (112, 74, 49)],
    "Weapon2HandedSword": [(203, 203, 203), (68, 85, 116), (68, 71, 97)],
    "WeaponDagger": [(203, 203, 203), (68, 85, 116), (146, 137, 117), (132, 125, 101)],
    "WeaponBow": [(111, 69, 41), (137, 102, 59), (181, 161, 139), (140, 98, 57), (185, 144, 102)],
    "WeaponBattleAxe": [(99, 68, 48), (190, 185, 182), (162, 151, 143)],
    "WeaponMagicStaff": [(101, 60, 42), (239, 50, 109), (137, 102, 59)],
    "WeaponCrossbow": [(96, 69, 37), (132, 96, 53), (193, 177, 134), (208, 190, 160)],
    "WeaponSling": [(114, 78, 54), (199, 178, 153)],
}
HILT = {(68, 85, 116), (68, 71, 97)}
STEEL = (203, 203, 203)
GEM = (239, 50, 109)
AXE_HEAD = {(190, 185, 182), (162, 151, 143)}
BOW_STRING = {(181, 161, 139)}
XB_LIMB = {(193, 177, 134), (208, 190, 160)}
SLING_STONE = {(199, 178, 153)}
CLUB_STUD = {(203, 203, 203)}
# The staff's vanilla swing smear (staff_combo_05/06) is drawn in the same cream as the hero's skin highlight. A real
# highlight is 1-2 px; the smear is an arc of tens: same-colour clusters of SMEAR_MIN px or more are weapon smear.
SMEAR_KEY = {"WeaponMagicStaff": (218, 193, 132)}
SMEAR_MIN = 5


def weapon_pixels(img, base):
    """{pixel: rgb} of the base weapon's vanilla pixels in a hero frame: its weapon colours plus, for a base with a
    SMEAR_KEY, the large clusters of that colour (its swing smear). Everything else is body and stays byte-identical."""
    px = img.load()
    W, Hh = img.size
    wc = set(WEAPON_COLS[base])
    out, key, px_set = {}, [], set()
    for y in range(Hh):
        for x in range(W):
            p = px[x, y]
            if not p[3]: continue
            px_set.add((x, y))
            if p[:3] in wc: out[(x, y)] = p[:3]
            elif p[:3] == SMEAR_KEY.get(base): key.append((x, y))
    keys = set(key)
    for c in components(key):
        # a stray smear pixel floats free of the body: no non-key, non-weapon pixel around it
        loose = not any(n in px_set and n not in keys and n not in out for q in c for n in neigh8(q))
        if len(c) >= SMEAR_MIN or loose:
            for q in c: out[q] = SMEAR_KEY[base]
    return out

# ------------------------------------------------------------------ raw colours (drawn as-is by the ramp shader)
_RAMPS = [load_ramp(RAMPS[k]) for k in sorted(RAMPS)]
_USED = set(atlas_colours().keys())
_BLOCK = set()
for (x, y) in _USED:
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            _BLOCK.add((x + dx, y + dy))
RC = [int((k + 0.5) * 255 / 16) for k in range(16)]
BC = [int((k + 0.5) * 255 / 64) for k in range(64)]
_raw_cache = {}


def safe_slot(s):
    return s not in _BLOCK and all(r[s] == PINK for r in _RAMPS)


# Crawl's palette: every designed colour is pulled into the muted range of the vanilla weapons (weapon_bubbles.tame)
# before it is quantised, except the accents, written "!rrggbb": a weapon's one bright touch (a glint, gem or flame).
TAME_CAP, TAME_S, ACCENT_CAP = 0.24, 0.62, 0.62


def raw(c):
    """Nearest bin-centred colour to c (tamed unless it is an accent) whose ramp slot is a safe pink slot."""
    accent = isinstance(c, str) and c.startswith("!")
    if accent: c = c[1:]
    if isinstance(c, str): c = H(c)
    key = (tuple(c), accent)
    if key in _raw_cache: return _raw_cache[key]
    c = WB.tame(tuple(c), ACCENT_CAP if accent else TAME_CAP, 0.9 if accent else TAME_S)
    best, bd = None, 1e9
    ri, gi, bi = min(15, c[0] * 16 // 256), min(15, c[1] * 16 // 256), min(63, c[2] * 64 // 256)
    for r in range(max(0, ri - 2), min(16, ri + 3)):
        for g in range(max(0, gi - 2), min(16, gi + 3)):
            for b in range(max(0, bi - 8), min(64, bi + 9)):
                cand = (RC[r], RC[g], BC[b])
                if slot(cand) != (r + 16 * g, b) or not safe_slot((r + 16 * g, b)): continue
                d = (cand[0] - c[0]) ** 2 * 3 + (cand[1] - c[1]) ** 2 * 4 + (cand[2] - c[2]) ** 2 * 2
                if not accent:                   # the coarse bins must not push a muted colour out of range
                    ch = max(cand) - min(cand)
                    d += 40000 * max(0.0, ch / max(1.0, max(cand)) - TAME_S) + 40 * max(0.0, ch - TAME_CAP * 255)
                if d < bd: bd, best = d, cand
    assert best is not None, c
    _raw_cache[key] = best
    return best


# ------------------------------------------------------------------ geometry helpers
def neigh8(p):
    x, y = p
    return [(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]


def neigh4(p):
    x, y = p
    return [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]


def components(pix):
    pix = set(pix); out = []
    for p in sorted(pix):
        if p not in pix: continue
        stack, comp = [p], []
        pix.discard(p)
        while stack:
            q = stack.pop(); comp.append(q)
            for n in neigh8(q):
                if n in pix: pix.discard(n); stack.append(n)
        out.append(sorted(comp))
    return out


def pca(pts):
    n = len(pts)
    mx = sum(p[0] for p in pts) / n; my = sum(p[1] for p in pts) / n
    sxx = sum((p[0] - mx) ** 2 for p in pts) / n
    syy = sum((p[1] - my) ** 2 for p in pts) / n
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pts) / n
    ang = 0.5 * math.atan2(2 * sxy, sxx - syy)
    u = (math.cos(ang), math.sin(ang))
    ts = [(p[0] - mx) * u[0] + (p[1] - my) * u[1] for p in pts]
    w = math.sqrt(sum(((p[0] - mx) * -u[1] + (p[1] - my) * u[0]) ** 2 for p in pts) / n)
    return (mx, my), u, min(ts), max(ts), w


class Frame:
    """One hero frame on its untrimmed canvas, with the base weapon's pixels erased and a pen for the new weapon."""

    def __init__(self, img, base):
        self.img = img
        self.W, self.H = img.size
        px = img.load()
        self.orig = {}
        for y in range(self.H):
            for x in range(self.W):
                p = px[x, y]
                if p[3]: self.orig[(x, y)] = p
        self.weapon = weapon_pixels(img, base)
        self.body = {p for p in self.orig if p not in self.weapon}
        self.new = {}                                  # pixel -> rgb (raw colours)
        bx = [p[0] for p in self.body] or [self.W / 2]; by = [p[1] for p in self.body] or [self.H / 2]
        self.bc = (sum(bx) / len(bx), sum(by) / len(by))

    def ok(self, p):
        return 0 <= p[0] < self.W and 0 <= p[1] < self.H and p not in self.body

    def put(self, p, c, over=True):
        p = (int(round(p[0])), int(round(p[1])))
        if not self.ok(p): return False
        if not over and p in self.new: return False
        self.new[p] = raw(c)
        return True

    def line(self, a, b, col, over=True):
        """col: colour or f(t) -> colour, t in 0..1 along a->b."""
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) + 1
        out = []
        for i in range(n + 1):
            t = i / max(1, n)
            p = (int(round(a[0] + (b[0] - a[0]) * t)), int(round(a[1] + (b[1] - a[1]) * t)))
            if out and out[-1][0] == p: continue
            c = col(t) if callable(col) else col
            if self.put(p, c, over): out.append((p, t))
        return out

    def outline(self, pts, c="1e1a1c"):
        for p in list(pts):
            for n in neigh4(p):
                if n not in self.new and self.ok(n) and n not in self.weapon_kept():
                    self.put(n, c, over=False)

    def weapon_kept(self):
        return ()

    def render(self):
        im = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
        px = im.load()
        for p in self.body: px[p] = self.orig[p]
        for p, c in self.new.items(): px[p] = c + (255,)
        return im


class Stick:
    """A straight weapon part: grip G, tip T (floats), unit u (G->T), perpendicular n (forward/down side)."""

    def __init__(self, pts, G, T, cols):
        self.pts, self.G, self.T, self.cols = pts, G, T, cols
        dx, dy = T[0] - G[0], T[1] - G[1]
        self.L = max(1.0, math.hypot(dx, dy))
        self.u = (dx / self.L, dy / self.L)
        n1, n2 = (-self.u[1], self.u[0]), (self.u[1], -self.u[0])
        self.n = n1 if n1[0] + n1[1] >= n2[0] + n2[1] else n2

    def at(self, t, s=0.0):
        """point at fraction t along G->T (may exceed 1), offset s along n."""
        return (self.G[0] + self.u[0] * self.L * t + self.n[0] * s, self.G[1] + self.u[1] * self.L * t + self.n[1] * s)

    def along(self, d, s=0.0):
        return (self.T[0] + self.u[0] * d + self.n[0] * s, self.T[1] + self.u[1] * d + self.n[1] * s)

    def t_of(self, p):
        return ((p[0] - self.G[0]) * self.u[0] + (p[1] - self.G[1]) * self.u[1]) / self.L


def stick_like(comp):
    if len(comp) < 2: return False
    (mx, my), u, t0, t1, w = pca(comp)
    L = t1 - t0
    return L >= 2.5 and w <= 0.95 and len(comp) <= L * 2.6 + 3


def find_sticks(fr, comp, base, tipmark=None):
    """Turn a (possibly occlusion-split) group of weapon pixels into a stick with grip/tip, or None for a smear."""
    if not stick_like(comp): return None
    (mx, my), u, t0, t1, w = pca(comp)
    e0 = (mx + u[0] * t0, my + u[1] * t0); e1 = (mx + u[0] * t1, my + u[1] * t1)
    cols = [fr.weapon[p] for p in comp]
    marks = None
    if base in ("Weapon1HandedSword", "Weapon2HandedSword", "WeaponDagger", "WeaponThrowingKnives"):
        hp = [p for p in comp if fr.weapon[p] in HILT]
        if hp and len(hp) < len(comp): marks = ("grip", hp)
    elif base == "WeaponSpear":
        sp = [p for p in comp if fr.weapon[p] in (STEEL, (181, 171, 164))]
        if sp and len(sp) < len(comp): marks = ("tip", sp)
    elif base == "WeaponMagicStaff" and tipmark:
        marks = ("tip", tipmark)
    d = lambda a, b: math.hypot(a[0] - b[0], a[1] - b[1])
    if marks:
        c = (sum(p[0] for p in marks[1]) / len(marks[1]), sum(p[1] for p in marks[1]) / len(marks[1]))
        near0 = d(e0, c) < d(e1, c)
        G, T = (e0, e1) if (near0 == (marks[0] == "grip")) else (e1, e0)
    else:
        def body_dist(e):
            return min((d(e, b) for b in fr.body), default=99)
        G, T = (e0, e1) if body_dist(e0) <= body_dist(e1) else (e1, e0)
    return Stick(comp, G, T, cols)


# ------------------------------------------------------------------ palettes (designed colours; raw() quantises them)
def ramp_fn(*hexes):
    cs = [H(h) for h in hexes]
    return lambda t: cs[min(len(cs) - 1, int(t * len(cs)))]


# ================================================================== per-weapon drawers
# A line drawer gets (fr, st) for each stick and draws the new weapon; smear(fr, comp) recolours swing smears.
def smear_with(light, mid, spark=None):
    def f(fr, comp):
        cs = set(comp)
        for i, p in enumerate(comp):
            edge = any(n not in cs and n not in fr.body for n in neigh4(p))
            fr.put(p, light if edge else mid)
        if spark:
            for i, p in enumerate(comp):
                if i % 9 == 4: fr.put(p, spark)
    return f


def blade(fr, st, edge, core, hilt, tip=None, guard=0, guard_col=None, wave=0, extra=None):
    """Recolour the stick: hilt part (vanilla hilt pixels) and blade part, optional guard/wave/tip."""
    hilt_ts = [st.t_of(p) for p in st.pts if fr.weapon[p] in HILT]
    tg = max(hilt_ts) if hilt_ts else 0.18
    for p in st.pts:
        t = st.t_of(p)
        if t <= tg + 1e-6:
            fr.put(p, hilt)
        else:
            s = 0
            if wave: s = wave * (1 if int(t * st.L) % 4 in (1, 2) else 0) * (1 if (int(t * st.L) // 4) % 2 else -1)
            q = (p[0] + st.n[0] * s, p[1] + st.n[1] * s)
            fr.put(q, core if (int(t * st.L) % 3) else edge)
    if tip: fr.put(st.T, tip)
    if guard:
        g = st.at(tg + 0.6 / st.L)
        for s in range(1, guard + 1):
            fr.put((g[0] + st.n[0] * s, g[1] + st.n[1] * s), guard_col or hilt, over=False)
            fr.put((g[0] - st.n[0] * s, g[1] - st.n[1] * s), guard_col or hilt, over=False)
    if extra: extra(fr, st)


def stick_recolour(fr, st, fn):
    for p in st.pts: fr.put(p, fn(max(0.0, min(0.999, st.t_of(p)))))


# ---- 1H sword
def d_riftblade(fr, st):
    # void steel split by the rift: the crack is the one bright touch
    blade(fr, st, "a8a2b8", "5a4a72", "3a2a26", tip="!ffd2ff",
          extra=lambda fr, st: [fr.put(st.at(t), "9a6ac0") for t in (0.5, 0.7)])


def d_frostbrand(fr, st):
    def ex(fr, st):
        for t, s in ((0.5, 1), (0.72, -1), (0.9, 1)):
            fr.put(st.at(t, s), "e8fbff", over=False)
    blade(fr, st, "e8fbff", "7cc8ee", "e4f6ff", tip="ffffff", guard=1, guard_col="a6dcf2", extra=ex)


def d_mercyblade(fr, st):
    def ex(fr, st):
        fr.put((st.G[0], st.G[1] + 1), "a81e2c", over=False); fr.put((st.G[0], st.G[1] + 2), "d8344a", over=False)
    blade(fr, st, "fff4d0", "e0c890", "8a1420", tip="ffffff", guard=2, guard_col="e0a830", extra=ex)


# ---- 2H sword
def d_tidebreaker(fr, st):
    blade(fr, st, "dafff4", "3f9a94", "b08a40", wave=1, guard=1, guard_col="cfa44a")


def d_reaper(fr, st):
    stick_recolour(fr, st, ramp_fn("4a2e1a", "5e3a22", "6e4428"))
    # scythe blade: leaves the top of the snath on the forward side and sweeps back toward the grip
    r = max(4.0, min(8.0, st.L * 0.6))
    pts = []
    for k in range(15):
        a = math.radians(k * 6.0)
        s_ = r * math.sin(a) + 1
        back = r * (1 - math.cos(a)) * 0.9
        thick = 2 if k < 10 else 1
        for w in range(thick):
            p = st.along(-back - w, s_)
            if fr.put(p, "f2fff6" if w == 0 else "6ea888"): pts.append((int(round(p[0])), int(round(p[1]))))
    fr.put(st.along(0, 1), "3a3e3c")
    fr.put(st.T, "3a3e3c")
    fr.outline(pts, "1c2a22")


# ---- dagger
def d_leechfang(fr, st):
    # a pale steel fang with a blood groove; a drop of blood running off the point
    def ex(fr, st):
        for t in (0.45, 0.65):
            fr.put(st.at(t), "8c2a28")
        fr.put(st.along(0.6, 1), "!e04040", over=False)
    blade(fr, st, "d8d2cc", "7e7a78", "5a1a20", tip="d8d2cc", extra=ex)


def d_kris(fr, st):
    blade(fr, st, "8a84a0", "3a3448", "a87a20", wave=1, guard=1, guard_col="b0903c", tip="!e0d8ff")


# ---- throwing knives
def d_moonglaive(fr, st):
    # a crescent glaive held at the grip: a 3 px ring-blade around a point just past the hand
    c = st.at(min(1.0, 2.6 / st.L))
    pts = []
    for k in range(16):
        a = 2 * math.pi * k / 16
        if math.cos(a) * -st.u[0] + math.sin(a) * -st.u[1] > 0.75: continue        # open toward the hand
        p = (c[0] + 2.6 * math.cos(a), c[1] + 2.6 * math.sin(a))
        lit = math.cos(a) * -0.7 + math.sin(a) * -0.7
        if fr.put(p, "f2fbff" if lit > 0.3 else ("b4dcf0" if lit > -0.4 else "6a92b4")):
            pts.append((int(round(p[0])), int(round(p[1]))))
    fr.put(c, "5a7aa6", over=False)
    fr.outline(pts, "1a2436")


def d_lash(fr, st):
    # a whip: the thin lash leaves the hand and runs out past the old knife tip with a wave, cracking at the end
    n = int(st.L * 1.9) + 3
    prev = None
    for i in range(n + 1):
        t = i / float(n) * 1.9
        s = math.sin(t * 5.0) * (0.9 if t > 0.3 else 0.3)
        p = st.at(t, s)
        q = (int(round(p[0])), int(round(p[1])))
        if q == prev: continue
        prev = q
        fr.put(q, "6e4428" if t < 0.25 else ("5aa83a" if i % 3 else "2e6e22"))
    fr.put(st.at(1.95), "!fff2a0")


def d_kunai(fr, st):
    for p in st.pts:
        t = st.t_of(p)
        fr.put(p, "b01e30" if t < 0.35 else ("aaa6bc" if int(t * st.L) % 3 == 0 else "5a566c"))
    fr.put(st.T, "d8d4e8")
    # ring pommel behind the hand
    r = st.at(-1.6 / st.L)
    for p in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        fr.put((r[0] + p[0], r[1] + p[1]), "9a96aa", over=False)


# ---- spear
def d_gravehook(fr, st):
    stick_recolour(fr, st, lambda t: H("3c3a44") if int(t * st.L) % 2 else H("7a7684"))
    # rusted harpoon point with a hooked barb curling back toward the hand
    fr.put(st.along(0), "c87a3a"); fr.put(st.along(1), "e09a50")
    hook = [st.along(-1, 1), st.along(-2, 2), st.along(-3, 2), st.along(-4, 1)]
    pts = []
    for p in hook:
        if fr.put(p, "b4642e"): pts.append((int(round(p[0])), int(round(p[1]))))
    fr.put(st.along(-1, -1), "8a4a24", over=False)
    fr.outline(pts, "2a1a14")


def d_lance(fr, st):
    stick_recolour(fr, st, lambda t: H("8a1a22") if t < 0.22 else (H("eceff4") if int(t * st.L) % 3 else H("aab0bc")))
    # the lance runs well past the old spear point, tapering to a steel tip
    for k in range(1, 7):
        fr.put(st.along(k), "c9ced8" if k < 6 else "ffffff")
    # vamplate: a steel cone just ahead of the hand
    g = st.at(min(0.45, 3.0 / st.L))
    pts = []
    for s in (-2, -1, 1, 2):
        p = (g[0] + st.n[0] * s, g[1] + st.n[1] * s)
        if fr.put(p, "aab0bc" if s < 0 else "6c7280", over=False): pts.append((int(round(p[0])), int(round(p[1]))))
    for s in (-1, 1):
        g2 = st.at(min(0.55, 4.0 / st.L), s)
        if fr.put(g2, "c9ced8", over=False): pts.append((int(round(g2[0])), int(round(g2[1]))))
    # pennant streaming back from behind the point
    for k, s in ((3, -1), (4, -1), (4, -2), (5, -1)):
        fr.put(st.along(-k, s), "d83a3a", over=False)
    fr.outline(pts, "1e1a1c")


# ---- magic staff
def d_wickstaff(fr, st):
    stick_recolour(fr, st, ramp_fn("4a3420", "6a4a2c", "8a6440"))
    # iron crook past the tip and a hanging lantern with a flame inside
    c1 = st.along(1); fr.put(c1, "45414c")
    hang = (c1[0], c1[1] + 1)
    fr.put(hang, "45414c")
    pts = []
    for dx in (-1, 0, 1):
        for dy in (1, 2, 3, 4):
            p = (hang[0] + dx, hang[1] + dy)
            col = "3a3640" if dy in (1, 4) else ("!d8fff0" if (dx == 0 and dy == 3) else ("!7ee8b4" if dx == 0 else "3c4c44"))
            if fr.put(p, col): pts.append((int(round(p[0])), int(round(p[1]))))
    fr.outline(pts, "1e1a1c")


def d_blightstaff(fr, st):
    for p in st.pts:
        t = st.t_of(p)
        q = (p[0] + (st.n[0] if int(t * st.L) % 5 == 2 else 0), p[1] + (st.n[1] if int(t * st.L) % 5 == 2 else 0))
        fr.put(q, "4a5a1a" if int(t * st.L) % 2 else "6a7a2a")
    c = st.along(1.5)
    pts = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if abs(dx) + abs(dy) == 2 and (dx, dy) != (-1, -1): continue
            p = (c[0] + dx, c[1] + dy)
            if fr.put(p, "!eaff9a" if (dx, dy) == (-1, -1) else ("aed23a" if dy < 1 else "6a8a1a")):
                pts.append((int(round(p[0])), int(round(p[1]))))
    fr.put((c[0], c[1] + 2), "aed23a", over=False)
    fr.outline(pts, "1c2008")


def d_orrery(fr, st):
    stick_recolour(fr, st, ramp_fn("6a4e1e", "a07c34", "d4ae5a"))
    c = st.along(2.2)
    pts = []
    for k in range(12):                                # brass armillary ring
        a = 2 * math.pi * k / 12
        p = (c[0] + 2.4 * math.cos(a), c[1] + 2.4 * math.sin(a))
        if fr.put(p, "d4ae5a" if math.sin(a) < 0 else "8a6a2c"): pts.append((int(round(p[0])), int(round(p[1]))))
    fr.put(c, "!fffbe0")                               # the star at the heart
    fr.put((c[0] + 4, c[1] - 2), "d2ecf6", over=False)
    fr.outline(pts, "2a1e0c")


d_gravehook.shaft = "5c5866"
d_lash.single = True                     # a whip is one-handed (the knives base holds a knife in each hand)
d_lance.shaft = "eceff4"
d_reaper.shaft = "5e3a22"
d_wickstaff.shaft = "6a4a2c"
d_blightstaff.shaft = "4a5a1a"
d_orrery.shaft = "a07c34"
d_tidebreaker.shaft = "3f9a94"


# ================================================================== base handlers
def one_hand(fr, base, groups, rest):
    """A one-handed weapon on a paired base (the knives' frames hold a knife in each hand): keep the active hand's
    knife (the clearly longer one, else the leading hand = furthest forward, the hero faces +x) and leave the other
    hand empty. Small loose pieces away from the kept one go too; real swing smears (> 8 px) stay."""
    def info(g):
        st = find_sticks(fr, sorted(g), base)
        L = st.L if st else 0
        gx = st.G[0] if st else sum(p[0] for p in g) / len(g)
        return L, gx
    inf = [info(g) for g in groups]
    best = max(range(len(groups)), key=lambda i: (round(inf[i][0] / 2.0), inf[i][1]))
    keep = groups[best]
    near = lambda c: min(math.hypot(a[0] - b[0], a[1] - b[1]) for a in c for b in keep) <= 2.0
    return [keep], [c for c in rest if len(c) > 8 or near(c)]


def handle_line(fr, base, draw, smear):
    gem = sorted(p for p, c in fr.weapon.items() if c == GEM)          # staff glow: head marker + magic aura
    sk = SMEAR_KEY.get(base)
    for c in components([p for p, col in fr.weapon.items() if col == sk]):
        smear(fr, c)                                                    # the vanilla swing arc: the weapon's own smear
    pix = {p: c for p, c in fr.weapon.items() if c != GEM and c != sk}
    comps = sorted(components(pix), key=len, reverse=True)
    # parts of one weapon split by the hand/arm in front of it are re-joined if they stay on one line
    groups, rest = [], []
    for c in comps:
        if not (stick_like(c) or len(c) <= 2):
            rest.append(c); continue
        for g in groups:
            if stick_like(g + c):
                g.extend(c); break
        else:
            if stick_like(c): groups.append(list(c))
            else: rest.append(c)
    if getattr(draw, "single", False) and len(groups) >= 1:
        groups, rest = one_hand(fr, base, groups, rest)
    for c in rest:
        if len(c) <= 2:
            for p in c: fr.put(p, smear_col_mid(smear))
        else:
            smear(fr, c)
    if gem:
        if groups: smear(fr, gem)                                      # aura in the weapon's glow colours
        else: rest.append(gem); smear(fr, gem)
    # one weapon per hand: knives are a pair, everything else gets one head (the group with the head marker, else
    # the longest); other pieces of a bent or split shaft are only recoloured
    if base != "WeaponThrowingKnives" and len(groups) > 1:
        def score(g):
            mk = sum(1 for p in g if fr.weapon[p] in (STEEL, (181, 171, 164))) if base == "WeaponSpear" else 0
            if base in ("Weapon1HandedSword", "Weapon2HandedSword", "WeaponDagger"):
                mk = sum(1 for p in g if fr.weapon[p] in HILT)
            return (mk > 0, len(g))
        groups.sort(key=score, reverse=True)
        for g in groups[1:]:
            for p in g: fr.put(p, getattr(draw, "shaft", smear_col_mid(smear)))
        groups = groups[:1]
    for g in groups:
        st = find_sticks(fr, sorted(g), base, tipmark=gem or None)
        if st is None: smear(fr, g)
        else: draw(fr, st)


def smear_col_mid(smear):
    return getattr(smear, "mid", "808080")


def handle_axe(fr, base, head, haft):
    for comp in components(fr.weapon):
        hp = [p for p in comp if fr.weapon[p] in AXE_HEAD]
        sp = [p for p in comp if fr.weapon[p] not in AXE_HEAD]
        if not hp:
            for p in sp: fr.put(p, haft[0])
            continue
        hc = (sum(p[0] for p in hp) / len(hp), sum(p[1] for p in hp) / len(hp))
        if sp:
            far = max(sp, key=lambda p: (p[0] - hc[0]) ** 2 + (p[1] - hc[1]) ** 2)
            st = Stick(sp, far, hc, None)
        else:
            st = Stick(hp, (hc[0] - 3, hc[1] + 3), hc, None)
        for p in sp:
            t = st.t_of(p)
            fr.put(p, haft[0] if int(t * st.L) % 3 else haft[1])
        fr.line(st.G, st.T, haft[0], over=False)
        head(fr, st, hc)


def h_bell(fr, st, c):
    # an upright bronze bell across the haft end: crown on the inner side, flaring mouth outward
    a, n = st.u, st.n
    rows = [(0, 1), (1, 1), (2, 2), (3, 2), (4, 3)]      # (along-u from crown, half-width)
    pts = []
    base = (c[0] - a[0] * 2, c[1] - a[1] * 2)
    for d, hw in rows:
        for s in range(-hw, hw + 1):
            p = (base[0] + a[0] * d + n[0] * s, base[1] + a[1] * d + n[1] * s)
            col = "f6d890" if s <= -hw + 1 else ("dcac52" if s < hw else "9a6a24")
            if d == 4: col = "fff0b0" if s < 0 else "c89a48"
            if fr.put(p, col): pts.append((int(round(p[0])), int(round(p[1]))))
    cl = (base[0] + a[0] * 5, base[1] + a[1] * 5)
    fr.put(cl, "5a3a22", over=False)
    fr.outline(pts, "2a1a08")


def h_star(fr, st, c):
    # a black iron maul head with a fallen star set in its face
    a, n = st.u, st.n
    pts = []
    for d in range(-2, 3):
        for s in range(-2, 3):
            if abs(d) == 2 and abs(s) == 2: continue
            p = (c[0] + a[0] * d + n[0] * s, c[1] + a[1] * d + n[1] * s)
            col = "6a5aa8" if s <= -1 else ("3c2e66" if s < 2 else "241a3c")
            if fr.put(p, col): pts.append((int(round(p[0])), int(round(p[1]))))
    fr.put(c, "!fffbe0")
    for d, s in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        fr.put((c[0] + a[0] * d + n[0] * s, c[1] + a[1] * d + n[1] * s), "fbe48a")
    fr.outline(pts, "0e0a1a")


def handle_club(fr, base, head, handle, smear):
    for comp in components(fr.weapon):
        if len(comp) < 3:
            for p in comp: fr.put(p, handle[0])
            continue
        (mx, my), u, t0, t1, w = pca(comp)
        L = t1 - t0
        if len(comp) > 34 or w > 1.7 or L < 3:
            smear(fr, comp)
            continue
        e0 = (mx + u[0] * t0, my + u[1] * t0); e1 = (mx + u[0] * t1, my + u[1] * t1)
        studs = [p for p in comp if fr.weapon[p] in CLUB_STUD]
        dd = lambda a, b: math.hypot(a[0] - b[0], a[1] - b[1])
        if studs:
            sc = (sum(p[0] for p in studs) / len(studs), sum(p[1] for p in studs) / len(studs))
            G, T = (e1, e0) if dd(e0, sc) < dd(e1, sc) else (e0, e1)
        else:
            bd = lambda e: min((dd(e, b) for b in fr.body), default=99)
            G, T = (e0, e1) if bd(e0) <= bd(e1) else (e1, e0)
        st = Stick(comp, G, T, None)
        fr.line(st.G, st.at(0.75), handle[0])
        fr.line((st.G[0] + st.n[0] * 0, st.G[1]), st.at(0.3), handle[1])
        head(fr, st, st.at(0.9))


def h_die(fr, st, c):
    # an ivory die, axis-aligned (dice are square), red snake-eye pips
    pts = []
    cx, cy = int(round(c[0])) - 1, int(round(c[1])) - 1
    for dx in range(4):
        for dy in range(4):
            col = "fbf6e6" if dx + dy <= 2 else ("e8dfc4" if dx + dy <= 4 else "b8aa86")
            if fr.put((cx + dx, cy + dy), col): pts.append((cx + dx, cy + dy))
    fr.put((cx + 1, cy + 1), "!d02a2a"); fr.put((cx + 2, cy + 2), "!d02a2a")
    fr.outline(pts, "2a2420")


def h_mace(fr, st, c):
    # a flanged iron mace head: a core with four flanges and blue-steel studs
    pts = []
    cx, cy = int(round(c[0])), int(round(c[1]))
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if fr.put((cx + dx, cy + dy), "aeaebe" if dx + dy < 0 else ("767686" if dx + dy == 0 else "4e4e5c")):
                pts.append((cx + dx, cy + dy))
    for (dx, dy) in ((2, 0), (-2, 0), (0, 2), (0, -2)):
        if fr.put((cx + dx, cy + dy), "c8c8d6" if dx + dy < 0 else "62626e"): pts.append((cx + dx, cy + dy))
    fr.put((cx, cy), "!6a96d0")
    fr.outline(pts, "1a1a22")


def handle_bow(fr, base, wood, string, extra):
    pix = fr.weapon
    st_px = [p for p in pix if pix[p] in BOW_STRING]
    wd = [p for p in pix if pix[p] not in BOW_STRING]
    for i, p in enumerate(sorted(wd)):
        fr.put(p, wood[0] if (p[0] + p[1]) % 3 else wood[1])
    for p in st_px: fr.put(p, string)
    if wd: extra(fr, sorted(wd), st_px)


def x_briar(fr, wd, sp):
    c = (sum(p[0] for p in (sp or wd)) / len(sp or wd), sum(p[1] for p in (sp or wd)) / len(sp or wd))
    for i, p in enumerate(wd):
        if i % 3 != 1: continue
        dx, dy = p[0] - c[0], p[1] - c[1]
        m = max(1e-3, math.hypot(dx, dy))
        q = (p[0] + dx / m, p[1] + dy / m)
        fr.put(q, "e0d8b8" if i % 2 else "9ad04e", over=False)


def x_hydra(fr, wd, sp):
    s = set(wd)
    ends = [p for p in wd if sum(1 for n in neigh8(p) if n in s) == 1]
    for e in ends:
        nb = [n for n in neigh8(e) if n in s][0]
        d = (e[0] - nb[0], e[1] - nb[1])
        h1 = (e[0] + d[0], e[1] + d[1])
        fr.put(h1, "5ab48a", over=False)
        fr.put((h1[0] + d[0], h1[1] + d[1]), "!e03040", over=False)


def handle_crossbow(fr, base, stock, limb, extra):
    for p, c in fr.weapon.items():
        fr.put(p, limb[0] if c in XB_LIMB and c == (208, 190, 160) else (limb[1] if c in XB_LIMB else (stock[0] if c == (96, 69, 37) else stock[1])))
    extra(fr)


def x_arc(fr):
    lp = [p for p, c in fr.weapon.items() if c in XB_LIMB]
    s = set(lp)
    for i, e in enumerate(sorted(lp)):
        if sum(1 for n in neigh8(e) if n in s) == 1:
            fr.put((e[0] + (1 if i % 2 else 0), e[1] - 1), "!fff2a0", over=False)


def x_heart(fr):
    sp = [p for p, c in fr.weapon.items() if c not in XB_LIMB]
    if not sp: return
    tip = max(sp, key=lambda p: (p[0] - fr.bc[0]) ** 2 + (p[1] - fr.bc[1]) ** 2)
    d = (1 if tip[0] >= fr.bc[0] else -1)
    for dx, dy, col in ((d, 0, "d8344a"), (d, -1, "!ff8aa0"), (d, 1, "9a1a2c"), (2 * d, 0, "d8344a")):
        fr.put((tip[0] + dx, tip[1] + dy), col, over=False)


def handle_sling(fr, base, cord, stone):
    sp = [p for p, c in fr.weapon.items() if c in SLING_STONE]
    cp = set(p for p, c in fr.weapon.items() if c not in SLING_STONE)
    for p in sorted(cp):
        edge = any(n not in cp and n not in fr.body for n in neigh4(p))
        fr.put(p, cord[0] if edge else cord[1])
    if sp:
        cx = sum(p[0] for p in sp) / len(sp); cy = sum(p[1] for p in sp) / len(sp)
        stone(fr, (cx, cy), sp)


def s_grudge(fr, c, sp):
    pts = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if abs(dx) + abs(dy) == 2 and (dx, dy) != (1, 1): continue
            if fr.put((c[0] + dx, c[1] + dy), "8a3a32" if dx + dy < 0 else "5e2424"): pts.append((int(round(c[0] + dx)), int(round(c[1] + dy))))
    fr.put(c, "!ff5a4a")
    fr.outline(pts, "1a0c0c")


def s_coin(fr, c, sp):
    pts = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if abs(dx) + abs(dy) == 2: continue
            if fr.put((c[0] + dx, c[1] + dy), "fff4b8" if (dx, dy) in ((-1, 0), (0, -1)) else "d8a02a"):
                pts.append((int(round(c[0] + dx)), int(round(c[1] + dy))))
    fr.put((c[0] + 1, c[1] + 1), "9a6a1a", over=False)
    fr.put((c[0] + 2, c[1] - 2), "!fffbe0", over=False)
    fr.outline(pts, "3a2a08")


def mk_smear(light, mid, spark=None):
    f = smear_with(light, mid, spark)
    f.mid = mid
    return f


# ================================================================== the 25 weapons
DESIGNS = {
    "Riftblade": ("line", d_riftblade, mk_smear("c8c0d8", "6a5a88", "d8b8f0")),
    "Frostbrand": ("line", d_frostbrand, mk_smear("e8fbff", "7cc8ee", "ffffff")),
    "Mercyblade": ("line", d_mercyblade, mk_smear("fff4d0", "e0c890", "e0a830")),
    "Tidebreaker": ("line", d_tidebreaker, mk_smear("dafff4", "3f9a94", "ffffff")),
    "Reaper": ("line", d_reaper, mk_smear("d8f0e0", "7eb294")),
    "Leechfang": ("line", d_leechfang, mk_smear("d8c8c4", "8c2a28")),
    "Kris": ("line", d_kris, mk_smear("8a7ad0", "3c2c66", "d8a02a")),
    "Moonglaive": ("line", d_moonglaive, mk_smear("f2fbff", "8ab4d8")),
    "Lash": ("line", d_lash, mk_smear("8ad05a", "3a7e2a", "fff2a0")),
    "Kunai": ("line", d_kunai, mk_smear("aaa6bc", "5a566c", "b01e30")),
    "Gravehook": ("line", d_gravehook, mk_smear("9a96a0", "5c5866", "c87a3a")),
    "Lance": ("line", d_lance, mk_smear("eceff4", "b82830")),
    "Wickstaff": ("line", d_wickstaff, mk_smear("b4d8c4", "4a7a66")),
    "Blightstaff": ("line", d_blightstaff, mk_smear("eaff9a", "8aa632")),
    "Orrery": ("line", d_orrery, mk_smear("d2ecf6", "6a5aa8", "fbe48a")),
    "DirgeMaul": ("axe", h_bell, ("5a3a22", "7e5230")),
    "Starfall": ("axe", h_star, ("c89a34", "8a6a20")),
    "SnakeEyes": ("club", h_die, ("8a6a44", "b8aa86"), mk_smear("fbf6e6", "c8bc98", "d02a2a")),
    "Bulwark": ("club", h_mace, ("3a3844", "5c5a6a"), mk_smear("c8c8d6", "767686", "6a96d0")),
    "Briarbow": ("bow", ("2e4a1e", "4a7a2a"), "d0c8a8", x_briar),
    "HydraBow": ("bow", ("1e4a3a", "2f7a5a"), "cce8d4", x_hydra),
    "Arcbolt": ("xbow", ("3a3844", "5c5a6a"), ("d0ecff", "78b4f0"), x_arc),
    "Heartseeker": ("xbow", ("5c0e1a", "9a1a2c"), ("f0e4c8", "c8b890"), x_heart),
    "Grudgestone": ("sling", ("6a2c26", "4a1c1a"), s_grudge),
    "Midas": ("sling", ("8a5a30", "6e4428"), s_coin),
}


TORSO_SLOTS = set(ROLES_VEST)


def back_shield(fr):
    """Bulwark Mace: a round blue shield with a white cross and an iron rim slung on the hero's back. Anchored to the
    torso (vest-coloured pixels): centre 2 px behind the back edge of the torso's middle rows, at the torso's middle
    height. Frames face +x (the game flips the whole sprite), so the back is -x. Drawn only into empty pixels, so the
    body and arms stay in front of it; drawn after the weapon, which stays in front too."""
    tor = [p for p in fr.body if slot(fr.orig[p][:3]) in TORSO_SLOTS]
    if len(tor) < 6:
        # torso turned away (crouches, lunges): the upper body minus skin and hair stands in for it
        ys = sorted(p[1] for p in fr.body)
        cut = ys[0] + (ys[-1] - ys[0]) * 0.65
        skin = {(199, 156, 110), (182, 116, 80), (218, 193, 132), (115, 91, 56)}
        tor = [p for p in fr.body if p[1] <= cut and fr.orig[p][:3] not in skin]
    if len(tor) < 4: return
    # height: a fixed drop from the top of the hair (the head moves with the body; the vest's middle does not, it is
    # half hidden by whichever arm swings past). x: the back edge of the torso on that row band.
    hair = [p[1] for p in fr.body if fr.orig[p][:3] == (115, 91, 56)]
    top = min(hair) if hair else min(p[1] for p in fr.body)
    cy = top + 8
    band = [p for p in tor if abs(p[1] - cy) <= 2] or tor
    back = min(p[0] for p in band)
    cx = back - 2
    R = 3.3
    pts = []
    for dy in range(-4, 5):
        for dx in range(-4, 5):
            d = math.hypot(dx, dy)
            if d > R: continue
            if d > 2.4: col = "c0c4cc" if dx + dy < 0 else "6c707c"            # iron rim lit top-left
            elif dx == 0 or dy == 0: col = "e8eef8"                            # the cross
            else: col = "4a7ac0" if dx + dy < 0 else "2a4a7a"
            if fr.put((cx + dx, cy + dy), col, over=False): pts.append((cx + dx, cy + dy))
    fr.outline(pts, "16182a")


def redraw(img, base, wid):
    fr = Frame(img, base)
    d = DESIGNS[wid]
    if d[0] == "line": handle_line(fr, base, d[1], d[2])
    elif d[0] == "axe": handle_axe(fr, base, d[1], d[2])
    elif d[0] == "club": handle_club(fr, base, d[1], d[2], d[3])
    elif d[0] == "bow": handle_bow(fr, base, d[1], d[2], d[3])
    elif d[0] == "xbow": handle_crossbow(fr, base, d[1], d[2], d[3])
    elif d[0] == "sling": handle_sling(fr, base, d[1], d[2])
    if wid == "Bulwark": back_shield(fr)
    return fr.render()


# ================================================================== clips, packing
def canvas(clips, idx):
    """A hero frame on its untrimmed canvas exactly as ex2D places it: trimRect.y counts from the TOP (exSprite's
    anchor maths; with the hero's BotCenter anchor this is what puts the feet 1 px above the canvas bottom in 1609 of
    AtlasHero's 2514 frames). hero_looks.Clips.frame pastes from the bottom, which is fine for colour previews only."""
    W, Hh = clips.img.size
    e = clips.elements[idx]; c = e["coords"]
    x0 = round(c["x"] * W); y1 = Hh - round(c["y"] * Hh)
    w = round(c["width"] * W); h = round(c["height"] * Hh)
    crop = clips.img.crop((x0, y1 - h, x0 + w, y1))
    assert not e["rotated"]
    t = e["trimRect"]
    cv = Image.new("RGBA", (e["originalWidth"], e["originalHeight"]), (0, 0, 0, 0))
    cv.paste(crop, (int(t["x"]), int(t["y"])))
    return cv


def weapon_clips(wid, base, combo, srcs):
    idle, run, atk = WL.clip_names(base, combo, srcs)
    return idle, run, atk


def build():
    clips = Clips()
    weapons = WL.mod_weapons()
    missing = [w[0] for w in weapons if w[0] not in DESIGNS]
    if missing: raise SystemExit("no in-hand design for: " + ", ".join(missing))
    els = clips.elements
    results = []
    for wid, name, base, combo, srcs in weapons:
        idle, run, atk = weapon_clips(wid, base, combo, srcs)
        names = [idle, run] + atk
        idx = sorted(set(f["index"] for n in names for f in clips.clips[n]["frameInfos"]))
        new = {}
        for i in idx:
            new[i] = redraw(canvas(clips, i), base, wid)
        # pack: each frame trimmed to its opaque bounds, laid in a uniform grid
        boxes = {i: (new[i].getbbox() or (0, 0, 1, 1)) for i in idx}
        cw = max(b[2] - b[0] for b in boxes.values()); ch = max(b[3] - b[1] for b in boxes.values())
        cols = max(1, min(len(idx), 1024 // cw))
        rows = (len(idx) + cols - 1) // cols
        Wt, Ht = 1, 1
        while Wt < cols * cw: Wt *= 2
        while Ht < rows * ch: Ht *= 2
        sheet = Image.new("RGBA", (Wt, Ht), (0, 0, 0, 0))
        table = []
        for k, i in enumerate(idx):
            b = boxes[i]
            x0, y0 = (k % cols) * cw, (k // cols) * ch
            sheet.paste(new[i].crop(b), (x0, y0))
            e = els[i]
            table.append([i, k, e["originalWidth"], e["originalHeight"], b[0], b[1], b[2] - b[0], b[3] - b[1]])
        sid = "WpnHand_" + wid
        sheet.save(os.path.join(OUT, sid + ".png"))
        man = {"cellW": cw, "cellH": ch, "cols": cols,
               "anims": [{"name": "Frames", "frames": list(range(len(idx))), "durations": [0.1] * len(idx)}],
               "atlas": "AtlasHero", "hero": table}
        json.dump(man, open(os.path.join(OUT, sid + ".json"), "w"))
        results.append((wid, name, base, names, idx, new))
    return clips, results


def contact(clips, results):
    ramp_blue = load_ramp(RAMPS["P1"])
    used = set(atlas_colours().keys())
    sc = 3
    blocks = []
    for wid, name, base, names, idx, new in results:
        ramp = WL.ramp_with(WL.swaps(wid, base), ramp_blue, used)
        seq = []
        for n in names:
            fs = [f["index"] for f in clips.clips[n]["frameInfos"]]
            if n == names[0]: fs = fs[:1]
            seen = []
            for f in fs:
                if f not in seen: seen.append(f)
            seq += [(n, f) for f in seen]
        def stage(im):
            # the game draws each canvas with its bottom-centre on the hero (BotCenter anchor): align them the same way
            st = Image.new("RGBA", (96, 64), (0, 0, 0, 0))
            st.alpha_composite(im, ((96 - im.width) // 2, 64 - im.height))
            return st
        van = [stage(WL.simulate(canvas(clips, f), ramp_blue)) for _, f in seq]
        mod = [stage(WL.simulate(new[f], ramp)) for _, f in seq]
        box = None
        for im in van + mod:
            b = im.getbbox()
            if b: box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
        fw, fh = box[2] - box[0], box[3] - box[1]
        per_row = max(1, 1800 // (fw * sc + 2))
        nrow = (len(seq) + per_row - 1) // per_row
        img = Image.new("RGBA", (150 + per_row * (fw * sc + 2), nrow * (2 * fh * sc + 10) + 4), (34, 32, 40, 255))
        dr = ImageDraw.Draw(img)
        dr.text((4, 4), name, fill=(235, 228, 210, 255))
        dr.text((4, 18), base.replace("Weapon", ""), fill=(150, 144, 160, 255))
        dr.text((4, 32), "%d frames" % len(idx), fill=(150, 144, 160, 255))
        for k, (a, b) in enumerate(zip(van, mod)):
            x = 150 + (k % per_row) * (fw * sc + 2)
            y = (k // per_row) * (2 * fh * sc + 10)
            img.alpha_composite(a.crop(box).resize((fw * sc, fh * sc), Image.NEAREST), (x, y))
            img.alpha_composite(b.crop(box).resize((fw * sc, fh * sc), Image.NEAREST), (x, y + fh * sc + 2))
        blocks.append(img)
    Wt = max(b.width for b in blocks); Ht = sum(b.height + 6 for b in blocks)
    out = Image.new("RGBA", (Wt, Ht), (22, 20, 26, 255))
    y = 0
    for b in blocks:
        out.alpha_composite(b, (0, y)); y += b.height + 6
    os.makedirs(os.path.dirname(os.path.abspath(CONTACT)), exist_ok=True)
    out.convert("RGB").save(CONTACT)
    # per-sheet previews (art dir): the new frames, vanilla-ramp rendered, in the sheet's order
    for (wid, name, base, names, idx, new), blk in zip(results, blocks):
        blk.convert("RGB").save(os.path.join(OUT, "WpnHand_%s_preview.png" % wid))
    return out.size


def check_body(clips, results):
    """Every non-weapon pixel must be byte-identical to the vanilla frame."""
    bad = 0
    for wid, name, base, names, idx, new in results:
        for i in idx:
            src = canvas(clips, i)
            wp = weapon_pixels(src, base)
            a = src.load(); b = new[i].load()
            W, Hh = new[i].size
            for y in range(Hh):
                for x in range(W):
                    p = a[x, y]
                    if p[3] and (x, y) not in wp and b[x, y] != p: bad += 1
    return bad


def check_vanilla_left(clips, results):
    """No vanilla weapon or smear pixel may survive unchanged in a mod frame."""
    left = []
    for wid, name, base, names, idx, new in results:
        for i in idx:
            src = canvas(clips, i)
            a = src.load(); b = new[i].load()
            n = sum(1 for (x, y) in weapon_pixels(src, base) if b[x, y] == a[x, y])
            if n: left.append((wid, i, n))
    return left


def check_placement(clips, results):
    """A frame whose redraw stays inside the vanilla trim box must get back the vanilla trimRect exactly."""
    bad = 0
    for wid, name, base, names, idx, new in results:
        rows = {r[0]: r for r in json.load(open(os.path.join(OUT, "WpnHand_%s.json" % wid)))["hero"]}
        for i in idx:
            t = clips.elements[i]["trimRect"]
            r = rows[i]
            inside = r[4] >= t["x"] and r[5] >= t["y"] and r[4] + r[6] <= t["x"] + t["width"] and r[5] + r[7] <= t["y"] + t["height"]
            if inside and canvas(clips, i).getbbox() == new[i].getbbox() and (r[4], r[5]) != (int(t["x"]), int(t["y"])): bad += 1
    return bad


if __name__ == "__main__":
    clips, results = build()
    if check_placement(clips, results): raise SystemExit("frame placement differs from the vanilla trimRect")
    bad = check_body(clips, results)
    if bad: raise SystemExit("body pixels changed: %d" % bad)
    left = check_vanilla_left(clips, results)
    if left: raise SystemExit("vanilla weapon pixels left unchanged: %s" % left[:8])
    size = contact(clips, results)
    print("weapon hands: %d weapons, %d frames, contact %s %s" % (len(results), sum(len(r[4]) for r in results), CONTACT, size))
