"""UMBRAEL v2: every Umbrael monster and effect sheet, drawn with the material renderer of the
Jinx v2 rigs (jinx_v2_rigs.Rig: lit primitives, 3 tones per material, selective outline, cluster clean-up). This file
adds Umbrael's materials and shared parts, draws the three tier 1 monsters and the Glimmer's decoy, and is the build
entry point; tier 2 is in umbrael_v2_t2.py, tier 3 in umbrael_v2_t3.py, the effects and the gold idol in umbrael_v2_fx.py.

    python3 umbrael_v2_rigs.py [outdir] [--only Name,Name]

Writes to art/out_umbrael/ of the checkout this file lives in. Same manifest format as every other sheet: <id>.png +
<id>.json (cellW, cellH, cols, anims[{name, frames, durations}]) + <id>_preview.png, feet at (cellW // 2, cellH - 2),
facing right. Every sheet is drawn at its final size (no ArtScale entry).

Look: void black-violet bodies kept in the mid-tones (value contrast and a cool rim on the lit side, never a near-black
blob), pale bone-white masks, mirror silver, glass cyan, a cold lilac glow, sand gold for the hourglass line, and one
accent hue per final.
"""
import math, os, sys, random

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import jinx_v2_rigs as J  # noqa: E402
from jinx_v2_rigs import Rig, Xf, chain, ik, lerp, stone, sheet, tail_anims, BUILT  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
DEFAULT_OUT = os.path.join(ROOT, "art", "out_umbrael")

# ================================================================== Umbrael's materials (ink, shadow, base, light, hi)
UMB_RAMPS = {
    "void":   ["150f24", "2c2246", "4a3c70", "6e5c9c", "9a88c6"],   # void black-violet, kept readable
    "shade":  ["1a1430", "36295a", "56448a", "7c68b4", "a898d8"],   # shadow-smoke bodies
    "ink":    ["101022", "262a48", "3c4270", "586094", "7e88b8"],   # ink: blue-black, kept readable
    "bone":   ["3a3048", "7a7088", "b8b0c0", "e0dae4", "fcf8fa"],   # porcelain masks, teeth
    "silver": ["222838", "4c566c", "7e8aa2", "b4bed0", "eef2fa"],   # mirror frames, blades
    "glass":  ["14303e", "235a6c", "3a8a9e", "6ec2d0", "c8f6f8"],   # glass cyan
    "pale":   ["4a4a68", "8486a8", "bcc2dc", "e0e6f4", "ffffff"],   # pale glass halves and ghosts
    "sand":   ["3a2412", "7a5222", "b8862e", "e2b852", "fbe8a2"],   # sand gold
    "brass":  ["2c1c0a", "604016", "966a2c", "c89c4a", "f2d68c"],
    "tarn":   ["20202a", "464852", "70727e", "a0a2ac", "d4d6de"],   # the Hollow King's tarnished silver
    "dusk":   ["1c0e2a", "3c1c56", "60327e", "8a52a8", "b07ec8"],   # Gloamcoil scales
    "lead":   ["1a1a22", "34343e", "52525e", "747482", "9c9cac"],   # leaded-glass cames
    "lwing":  ["2a1a40", "4e3474", "7656a6", "a080ca", "c8b2e8"],   # Argus wings
    "redg":   ["3a0a18", "7a1a2c", "b8343e", "e2685c", "f8ac94"],   # stained glass red
    "blug":   ["0e1438", "1e3070", "3658aa", "5e8ad6", "a6caf6"],   # stained glass blue
    "robe":   ["1e1626", "3a2c46", "5a466a", "7c6890", "a08cb4"],   # robes, cloth
    "wood":   ["1a1018", "3a2228", "5a3a3a", "7c5648", "a07a5c"],   # the clock case
    # emissive (not shaded, no sel-out)
    "lilac":  ["3a1a5a", "6a3aa0", "9a6ad0", "c8a2f0", "f0e2ff"],   # Umbrael's cold glow
    "cyanl":  ["0e3a4a", "1a7088", "40b8d0", "94eaf6", "eaffff"],   # glass light
    "sandl":  ["5a3a10", "a87a26", "e0b444", "f8dc84", "fff6d0"],   # falling sand light
    "dark":   ["0a0812", "161226", "221c38", "302848", "40365c"],   # darkness clouds (flat)
}
for _k, _v in UMB_RAMPS.items():
    J.RAMPS[_k] = [J._h(c) for c in _v]
J.EMISSIVE |= {"lilac", "cyanl", "sandl", "dark"}
J.SHINY |= {"bone", "silver", "glass", "pale", "sand", "brass", "tarn", "redg", "blug"}

RAMPS = J.RAMPS


class SRig(Rig):
    """A Rig that draws k times larger about the feet: geometry scales before it is rasterised (lines and dots stay one
    pixel, stamps keep their pixel grid), so a figure posed in small units can be drawn at its final size."""

    def __init__(self, k=1.0):
        Rig.__init__(self)
        self.k = k

    def _p(self, x, y):
        return x * self.k, y * self.k

    def ell(self, cx, cy, rx, ry, mat, z, bias=0.0, ang=0.0, flat=None, thin=False, clip=None, part=None):
        k = self.k
        c = (lambda x, y: clip(x / k, y / k)) if clip else None
        return Rig.ell(self, cx * k, cy * k, rx * k, ry * k, mat, z, bias, ang, flat, thin, c, part)

    def tube(self, pts, radii, mat, z, bias=0.0, flat=None, thin=False, part=None, zs=None):
        return Rig.tube(self, [self._p(*q) for q in pts], [r_ * self.k for r_ in radii], mat, z, bias, flat, thin, part, zs)

    def poly(self, pts, mat, z, bias=0.0, normal=(0.0, 0.0, 1.0), curve=0.0, flat=None, thin=False, part=None):
        return Rig.poly(self, [self._p(*q) for q in pts], mat, z, bias, normal, curve, flat, thin, part)

    def line(self, x0, y0, x1, y1, mat, z, tone=2, part=None):
        k = self.k
        return Rig.line(self, x0 * k, y0 * k, x1 * k, y1 * k, mat, z, tone, part)

    def polyline(self, pts, mat, z, tone=2, tones=None, part=None):
        return Rig.polyline(self, [self._p(*q) for q in pts], mat, z, tone, tones, part)

    def dot(self, x, y, mat, tone, z, part=None):
        return Rig.dot(self, x * self.k, y * self.k, mat, tone, z, part)

    def dots(self, pts, mat, tone, z):
        return Rig.dots(self, [self._p(*q) for q in pts], mat, tone, z)

    def stamp(self, grid, x, y, z, legend, pivot=(0, 0), flip=False, part=None, lit=False):
        return Rig.stamp(self, grid, x * self.k, y * self.k, z, legend, pivot, flip, part, lit)


# ================================================================== shared parts
MASK_LEG = {"a": ("bone", 1), "w": ("bone", 2), "W": ("bone", 3), "X": ("bone", 4), "m": ("void", 0),
            "k": ("void", 1), "e": ("lilac", 3), "E": ("lilac", 4), "n": ("lilac", 2), "s": ("silver", 2),
            "S": ("silver", 3), "c": ("cyanl", 3), "g": ("glass", 3), "G": ("glass", 4), "v": ("void", 2),
            "V": ("void", 3), "h": ("void", 3), "H": ("void", 4), "t": ("bone", 2)}

# The Shade Imp's cracked porcelain mask. Pivot (3, 5): the chin.
IMP_MASK = {
    "calm": """
.awWXa.
aWWWWWw
WknWknw
WWWWkWw
.wWkWw.
..aaa..
""",
    "snarl": """
.awWXa.
aWWWWWw
WneWneW
WWWWkWw
.wmmmw.
..aka..
""",
    "hurt": """
.awWXa.
aWWkWWw
WmmkWmm
WWWkkWw
.wkWWw.
..aaa..
""",
    "broken": """
.aW....
aWWk...
WmEk...
WWk....
.Wk....
..a....
""",
}


# The Shade Imp's face: a cracked porcelain half-mask over two lilac eyes, a fanged grin below. Pivot (3, 4).
IMP_FACE = {
    "calm": """
.aWWa.
WknWkn
.wWkw.
.mtmt.
""",
    "snarl": """
.aWWa.
WneWne
.wWkw.
mtmtmt
""",
}


def mask_stamp(r, grid, x, y, z, pivot, flip=False):
    return r.stamp(grid, x, y, z, MASK_LEG, pivot=pivot, flip=flip)


def glow_eye(r, x, y, z, big=False):
    r.dot(x, y, "lilac", 4, z)
    if big:
        r.dot(x - 1, y, "lilac", 3, z - 0.01); r.dot(x + 1, y, "lilac", 3, z - 0.01)


def smoke_tail(r, cx, cy, phase, ln=6.0, w=3.2, z=0.0, mat="shade", lean=0.0, curl=1.0):
    """A body that thins into smoke: from (cx, cy) down to the floor, swaying with phase, ending in a curl."""
    pts, rad = [], []
    n = 5
    for i in range(n + 1):
        t = i / n
        sway = math.sin(phase + t * 3.0) * 1.3 * t + lean * t
        pts.append((cx + sway - curl * 2.2 * t * t, cy + ln * t))
        rad.append(max(0.4, w * (1.0 - 0.75 * t)))
    r.tube(pts, rad, mat, z, bias=0.05)
    # wisps peeling off the tip
    tx, ty = pts[-1]
    for k in range(3):
        a = phase * 1.7 + k * 2.1
        r.dot(tx - 1.5 - k * 1.3 + math.cos(a) * 0.6, ty - 0.5 - (k % 2), mat, max(1, 3 - k), z - 0.2)
    return pts


def wisps(r, x, y, k, n=5, mat="shade", spread=5.0, seed=3, z=6.0, rise=1.0):
    rnd = random.Random(seed)
    for i in range(n):
        a = rnd.uniform(0, math.tau); d = spread * (0.4 + 0.6 * rnd.random())
        px, py = x + d * math.cos(a) * (0.6 + 0.2 * k), y + d * math.sin(a) * 0.5 - k * rise
        r.ell(px, py, max(0.6, 1.6 - 0.35 * k), max(0.6, 1.2 - 0.3 * k), mat, z + i * 0.01, bias=0.15)


def shards(r, x, y, k, n=6, mats=("glass", "silver"), spread=7.0, seed=5, z=7.0, fall=0.0):
    rnd = random.Random(seed)
    for i in range(n):
        a = rnd.uniform(-math.pi, 0.3); d = spread * (0.35 + 0.65 * rnd.random()) * (0.6 + 0.4 * k)
        px, py = x + d * math.cos(a), y + d * math.sin(a) + fall * k * k
        m = mats[i % len(mats)]
        r.dot(px, py, m, 4 if (i + k) % 3 == 0 else 3, z)
        if i % 2 == 0: r.dot(px + 1, py + 1, m, 2, z)


def claw_hand(r, hx, hy, ang, z, ln=2.6, spread=26.0, mat="silver", n=3, tone=None):
    """Long glass-tipped fingers fanning from (hx, hy) along ang (degrees, y down)."""
    for k in range(n):
        a = math.radians(ang + (k - (n - 1) / 2.0) * spread / max(1, n - 1))
        pts = [(hx, hy), (hx + ln * 0.6 * math.cos(a), hy + ln * 0.6 * math.sin(a)),
               (hx + ln * math.cos(a + 0.25), hy + ln * math.sin(a + 0.25))]
        r.polyline(pts, mat, z, tones=[tone or 3, 2 if tone is None else tone])


def arc_smear(r, cx, cy, R, a0, a1, mat="lilac", width=2, z=8.0, tones=(2, 3, 4)):
    """Swing smear along an arc (degrees, y down), brightest at the leading end a1."""
    n = max(3, int(abs(a1 - a0) / 5))
    for i in range(n + 1):
        t = i / n
        a = math.radians(lerp(a0, a1, t))
        tone = tones[0] if t < 0.35 else tones[1] if t < 0.75 else tones[2]
        for w in range(width if t > 0.3 else 1):
            rr = R - w
            r.dot(cx + rr * math.cos(a), cy + rr * math.sin(a), mat, max(1, tone - w), z)


def twinkle(r, x, y, k=1, mat="white", z=9.0):
    """A cold four-point glint: k=1 big, 2 small."""
    r.dot(x, y, mat, 4, z)
    for d in ((1, 2) if k == 1 else (1,)):
        for dx, dy in ((d, 0), (-d, 0), (0, d), (0, -d)):
            r.dot(x + dx, y + dy, "lilac" if d == 2 else mat, 3 if d == 1 else 2, z - 0.01)


def floor_shadow(r, cx, w, z=-9.0, mat="dark", tone=2, cy=0.0, h=1.4):
    """A soft contact shadow on the floor under a hovering body (drawn in the cell, kept flat)."""
    r.ell(cx, cy - 0.4, w, h, mat, z, flat=tone)


def dust(r, x, y, k, w=1.0, mat="shade"):
    for side in (-1, 1):
        for i in range(3 - k):
            px = x + side * (2 + i * 2 + k * 1.5) * w
            py = y - (i % 2) - (1 if k else 0)
            r.ell(px, py, 1.2 - 0.3 * k, 0.9, mat, 5.0 + i * 0.01, flat=2 if i else 3)


def rimlight(spr, mats, step=1, edge=None):
    """Light-side rim: pixels of `mats` with open air up or left of them go `step` tones lighter (or take the `edge`
    material's tone 3), so a dark body separates from the floor on the lit side."""
    tones = getattr(spr, "tones", {})
    px = dict(spr.px)
    out_t = dict(tones)
    for (x, y), (m, t) in tones.items():
        if m not in mats: continue
        if (x - 1, y) in spr.px and (x, y - 1) in spr.px: continue
        if edge:
            px[(x, y)] = RAMPS[edge][3]; out_t[(x, y)] = (edge, 3)
        else:
            nt = min(4, t + step); px[(x, y)] = RAMPS[m][nt]; out_t[(x, y)] = (m, nt)
    o = J.SprRGB(px); o.tones = out_t
    return o


def remains(stage, mask=None, mask_at=(0.0, -2.0), stain=8.0, glass=4, glass_mats=("glass", "silver"), seed=9,
            extra=None, stain_mat="shade"):
    """An Umbrael corpse: a shadow stain soaking into the floor with what did not dissolve (a mask, glass shards)."""
    r = Rig()
    rx = stain * (0.7 + 0.3 * stage)
    r.ell(0.0, -0.8, rx, 1.6 + 0.4 * stage, stain_mat, -1.0, bias=-0.35)
    r.ell(-rx * 0.3, -1.0, rx * 0.45, 1.0, stain_mat, -0.9, bias=0.1)
    if glass:
        rnd = random.Random(seed)
        for i in range(glass):
            x = rnd.uniform(-rx, rx); y = -rnd.uniform(0.5, 2.2)
            m = glass_mats[i % len(glass_mats)]
            r.dot(x, y, m, 4 if i % 2 else 3, 2.0); r.dot(x + 1, y, m, 2, 2.0)
    if mask:
        grid, piv = mask
        mask_stamp(r, grid, mask_at[0], mask_at[1], 3.0, piv)
    if extra: extra(r)
    return r.resolve()


# ================================================================== SHADE IMP (T1): a smoke imp in a cracked porcelain mask
def shade_imp(phase=0.0, lean=0.0, bob=0.0, near=None, far=None, near_ang=10.0, far_ang=20.0, face="calm", head=(0.0, 0.0),
              tail_len=6.0, tail_w=3.0, smoke=None, smear=None, fade=None, extra=None, horn=0.0, claws_open=26.0, dx=0.0):
    """Feet (the smoke's tip) at y=0. near / far: hand points. fade=k dissolves the body into puffs (k 1..3)."""
    r = Rig()
    hip = (dx - 0.5, -4.0 + bob)
    T = Xf(lean, hip)
    if fade is None or fade < 2:
        smoke_tail(r, hip[0] + 0.5, hip[1] + 0.5, phase, ln=-hip[1] - 0.5, w=tail_w, z=-1.0, lean=-lean * 0.04)
    chest = T(hip[0] + 0.6, hip[1] - 3.2)
    sh_n, sh_f = T(hip[0] + 2.2, hip[1] - 4.6), T(hip[0] - 1.6, hip[1] - 4.8)
    nh = near or T(hip[0] + 5.5, hip[1] - 1.8)
    fh = far or T(hip[0] - 3.4, hip[1] - 1.2)
    if fade is None or fade < 2:
        # far arm (behind), torso (a hunched shadow with a lilac rim), near arm
        e = ik(sh_f[0], sh_f[1], fh[0], fh[1], 2.8, 2.8, bend=1)
        r.tube([sh_f, e, fh], [0.9, 0.8, 0.6], "void", -0.6, bias=-0.25)
        claw_hand(r, fh[0], fh[1], far_ang, -0.5, ln=2.6, spread=claws_open * 0.8, tone=2)
        r.ell(chest[0], chest[1], 2.8, 3.2, "shade", 0.0, bias=0.15, ang=lean)
        r.ell(chest[0] - 0.6, chest[1] - 1.6, 2.4, 1.5, "void", 0.05, bias=0.3, ang=lean)      # hunched shoulders
        r.dot(chest[0] - 2.4, chest[1] - 0.8, "lilac", 2, 0.2)                                 # rim glow
        e = ik(sh_n[0], sh_n[1], nh[0], nh[1], 3.0, 3.0, bend=-1)
        r.tube([sh_n, e, nh], [1.0, 0.9, 0.7], "void", 3.0, bias=0.1)
        claw_hand(r, nh[0], nh[1], near_ang, 3.1, ln=3.2, spread=claws_open)
        # head: a horned imp's skull of shadow with a cracked porcelain half-mask over the eyes and a fanged grin
        hx, hy = T(hip[0] + 1.4, hip[1] - 5.0)
        hx += head[0]; hy += head[1]
        r.tube([(hx - 1.4, hy - 3.8), (hx - 2.6, hy - 5.0 - horn), (hx - 4.0, hy - 5.6 - horn)], [1.0, 0.7, 0.35], "bone", 0.9, bias=-0.35)
        r.ell(hx, hy - 2.0, 2.9, 2.6, "shade", 1.5, bias=0.15)
        r.poly([(hx - 2.6, hy - 2.6), (hx - 5.2, hy - 3.2), (hx - 2.4, hy - 1.0)], "shade", 1.45, bias=0.0)      # pointed ear
        r.tube([(hx + 0.8, hy - 4.0), (hx + 2.0, hy - 5.2 - horn), (hx + 3.4, hy - 5.8 - horn)], [1.1, 0.8, 0.35], "bone", 1.6, bias=-0.1)
        r.dot(hx + 3.4, hy - 5.8 - horn, "bone", 3, 1.65); r.dot(hx - 4.0, hy - 5.6 - horn, "bone", 2, 0.95)
        mask_stamp(r, IMP_FACE[face] if face in IMP_FACE else IMP_MASK[face], hx + 1.0, hy + 0.5, 3.0, (3, 4))
    if fade:
        wisps(r, hip[0], hip[1] - 3.0, fade, n=7, spread=5.0 + fade, seed=4 + fade, z=5.0)
        if fade == 1:
            mask_stamp(r, IMP_MASK[face], hip[0] + 1.7, hip[1] - 5.5, 6.0, (3, 5))
    if smoke:
        x, y, k = smoke
        wisps(r, x, y, k, n=6, spread=6.0, seed=11 + k, z=-2.0)
    if smear:
        for (cx, cy, R, a0, a1) in smear:
            arc_smear(r, cx, cy, R, a0, a1, mat="lilac", width=2, z=5.0)
    if extra: extra(r)
    return r.resolve()


def imp_sheet(outdir):
    S = shade_imp
    idle = [S(phase=i * 1.57, bob=[0, -0.3, -0.6, -0.3][i], near=(5.0, -7.5 + [0, -0.3, -0.6, -0.3][i]),
              far=(-3.6, -6.5 + [0, -0.3, -0.6, -0.3][i]), claws_open=[26, 30, 34, 30][i]) for i in range(4)]
    run = [S(phase=i * 1.05, lean=14, bob=-0.5 * abs(math.sin(i / 6 * math.tau)), tail_len=7, tail_w=2.8,
             near=(5.8 + 0.8 * math.cos(i / 6 * math.tau), -6.0), far=(-4.4 - 0.8 * math.cos(i / 6 * math.tau), -5.4),
             near_ang=30, far_ang=40) for i in range(6)]
    # Rake (7): wind the near claw back (0), first rake down-forward (1 smear, 2 = HIT), the far claw comes over (3, 4 = HIT),
    # follow-through (5), settle (6)
    rake = [S(lean=-10, near=(-1.0, -12.5), far=(-4.0, -6.0), near_ang=-60, face="snarl", claws_open=40, horn=0.5),
            S(lean=4, near=(4.0, -12.0), far=(-4.2, -6.4), near_ang=-20, face="snarl", claws_open=36,
              smear=[(1.0, -7.0, 8.0, -110, -40)]),
            S(lean=16, near=(8.5, -4.5), far=(-3.6, -7.0), near_ang=60, face="snarl", claws_open=30, dx=1.0,
              smear=[(1.0, -7.0, 8.0, -60, 40)]),
            S(lean=6, near=(5.5, -3.8), far=(0.0, -12.0), near_ang=70, far_ang=-50, face="snarl", claws_open=30),
            S(lean=18, near=(4.0, -4.0), far=(8.0, -5.0), near_ang=70, far_ang=50, face="snarl", dx=1.5,
              smear=[(1.0, -8.0, 7.5, -80, 30)]),
            S(lean=10, near=(4.4, -4.6), far=(5.4, -3.8), near_ang=70, far_ang=70, face="calm", dx=1.0),
            S(lean=2, near=(5.0, -7.0), far=(-3.6, -6.4))]
    # Step (8): sink into its smoke (0-1), burst into smoke (2), only smoke (3), the blink (4: an empty puff), re-form out of
    # smoke (5-6), claws up (7)
    step = [S(lean=-6, bob=1.0, near=(4.0, -5.5), far=(-3.6, -5.0), face="snarl", claws_open=40),
            S(lean=-2, bob=2.4, near=(3.2, -4.0), far=(-3.0, -3.6), face="snarl", tail_w=3.6, smoke=(0.0, -2.0, 0)),
            S(fade=1, smoke=(0.0, -2.0, 1)),
            S(fade=2, smoke=(0.0, -3.0, 2)),
            S(fade=3),
            S(fade=2, smoke=(0.0, -3.0, 0)),
            S(lean=8, bob=1.4, near=(6.0, -8.0), far=(-2.6, -9.0), face="snarl", claws_open=40, smoke=(0.0, -2.0, 1)),
            S(lean=4, near=(5.5, -9.5), far=(-3.6, -8.5), face="snarl", claws_open=36, horn=0.5)]
    d0 = S(lean=-18, near=(2.0, -11.0), far=(-5.5, -9.0), face="hurt", head=(-0.5, 0.5), claws_open=44)
    d1 = S(lean=-34, bob=2.0, near=(0.0, -6.0), far=(-6.0, -4.0), face="hurt", fade=1, smoke=(-1.0, -3.0, 1))
    d2 = remains(0, mask=(IMP_MASK["hurt"], (3, 5)), mask_at=(-1.0, -1.0), stain=6.0, glass=0,
                 extra=lambda r: wisps(r, 0, -4, 2, n=6, spread=6, seed=21, z=4))
    corpse = remains(1, mask=(IMP_MASK["broken"], (3, 5)), mask_at=(1.0, -0.5), stain=6.5, glass=3, glass_mats=("bone", "lilac"))
    knock = S(lean=-24, near=(1.0, -10.5), far=(-6.0, -8.0), face="hurt", claws_open=40, head=(-0.5, 0.0))
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.08] * 6),
             ("Rake", rake, [0.12, 0.05, 0.1, 0.06, 0.1, 0.12, 0.12]),
             ("Step", step, [0.1, 0.1, 0.06, 0.06, 0.06, 0.06, 0.08, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("UmbShadeImp", anims, outdir, scale=8)


# ================================================================== GLIMMER (T1): a floating shard of mirror glass
def glimmer(alt=2.0, tilt=0.0, wing=0.0, glint=0.0, eye="open", flash=0, squash=1.0, decoy=False, extra=None, spin=1.0,
            shadow=True, crack=False):
    """A tall diamond of mirror glass hovering alt px up: silver bevel, cyan pane, a diagonal sheen band (glint 0..1 runs
    it down the face), one eye, two tiny glass wings. spin < 1 narrows the diamond (it is turning edge-on)."""
    r = Rig()
    cx, cy = 0.0, -alt - 5.6
    T = Xf(tilt, (cx, cy))
    hw, hh = 4.0 * spin, 5.4 * squash
    pts = [T(cx, cy - hh), T(cx + hw, cy - 0.8), T(cx, cy + hh), T(cx - hw, cy - 0.8)]
    base = "pale" if decoy else "glass"
    # wings behind: two thin glass slips that flick up and down
    for side in (-1, 1):
        a = math.radians(-20 - wing * 0.8) if side > 0 else math.radians(-160 + wing * 0.8)
        sx, sy = T(cx + side * hw * 0.55, cy - 0.6)
        tip = (sx + 4.6 * math.cos(a), sy + 4.6 * math.sin(a))
        mid = ((sx + tip[0]) / 2, (sy + tip[1]) / 2)
        z = -1.0 if side < 0 else 2.0
        r.poly([(sx, sy - 0.6), (mid[0], mid[1] - 1.0), tip, (mid[0], mid[1] + 0.8), (sx, sy + 0.8)],
               "pale" if decoy else "glass", z, bias=0.2 if side > 0 else -0.15, normal=(0.0, -0.5, 1.0))
        r.dot(*tip, "white", 4 if side > 0 else 3, z + 0.01)
    if spin > 0.3:
        r.poly(pts, "silver", 0.0, normal=(-0.2, -0.2, 1.0))
        inner = [((p[0] - cx) * 0.62 + cx, (p[1] - cy + 0.4) * 0.72 + cy - 0.3) for p in pts]
        r.poly(inner, base, 0.1, curve=0.6, normal=(-0.3, -0.35, 1.0))
        # sheen band, clipped to the pane
        inside = set(J.poly_px(inner))
        g = lerp(-5.0, 5.0, glint)
        for i in range(-6, 7):
            for w in (0, 1):
                x, y = int(round(cx + i * 0.5 * spin + w)), int(round(cy + g - i * 0.7))
                if (x, y) in inside:
                    r.dot(x, y, "white" if w == 0 else "glass", 4 if abs(i) < 3 else 3, 0.2)
        if crack:
            r.polyline([T(cx - 1.0, cy - 4.0), T(cx + 0.5, cy - 1.0), T(cx - 0.5, cy + 2.0), T(cx + 1.2, cy + 4.5)], "void", 0.25, tone=1)
        # the eye: a white glint with a lilac iris
        ex, ey = T(cx + 0.6 * spin, cy + 0.2)
        if eye == "open":
            r.dots([(ex, ey), (ex + 1, ey), (ex, ey + 1), (ex + 1, ey + 1)], "void", 1, 0.3)
            r.dot(ex + 1, ey, "lilac", 3, 0.31); r.dot(ex, ey, "white", 4, 0.31)
        elif eye == "wide":
            r.ell(ex + 0.5, ey + 0.5, 1.4, 1.3, "void", 0.3, flat=0); r.dot(ex + 1, ey + 1, "lilac", 4, 0.31)
            r.dot(ex, ey, "lilac", 3, 0.31); r.dot(ex, ey + 1, "white", 4, 0.31)
        elif eye == "shut":
            r.line(ex - 1, ey, ex + 1, ey, "void", 0.3, tone=1)
    else:
        r.line(*T(cx, cy - hh), *T(cx, cy + hh), "silver", 0.0, tone=4)
    if flash:
        if flash == 1: twinkle(r, *T(cx + 0.5, cy - hh - 1), 1)
        if flash == 2:
            for (dx, dy) in ((-6, -2), (6, -2), (0, -10), (0, 8)):
                r.dot(cx + dx, cy + dy, "white", 4, 9)
    if shadow:
        floor_shadow(r, 0.0, 3.0 + alt * 0.1)
    if extra: extra(r)
    return r.resolve()


def glimmer_frames(decoy=False):
    G = lambda **k: glimmer(decoy=decoy, **k)
    idle = [G(alt=[2.0, 2.4, 2.8, 2.4][i], wing=[0, 15, 30, 15][i], glint=[0.1, 0.3, 0.5, 0.7][i]) for i in range(4)]
    run = [G(alt=2.4 + 0.6 * math.sin(i / 6 * math.tau), tilt=18, wing=[0, 30, 45, 30, 0, -15][i], glint=i / 6.0)
           for i in range(6)]
    # Shard (6): rear back (0), the tip flashes (1), FLICK forward (2: release), recoil (3), settle (4-5)
    shard = [G(tilt=-18, wing=30, glint=0.2, eye="wide"), G(tilt=-26, wing=45, glint=0.3, eye="wide", flash=1),
             G(tilt=24, wing=-10, glint=0.6), G(tilt=14, wing=0, glint=0.8), G(tilt=6, wing=10, glint=0.9), G(tilt=0, wing=15, glint=0.1)]
    return idle, run, shard


def glimmer_sheet(outdir):
    G = glimmer
    idle, run, shard = glimmer_frames()
    # Split (7): spins up edge-on (0-2), a white flash (3: the decoys appear), spins back (4-5), settles (6)
    split = [G(spin=0.8, wing=30, eye="wide"), G(spin=0.45, wing=45), G(spin=0.15, wing=60), G(spin=0.15, flash=2, wing=60),
             G(spin=0.5, wing=40), G(spin=0.85, wing=20, glint=0.6), G(wing=10, glint=0.3)]
    d0 = G(tilt=-20, eye="shut", crack=True, alt=2.5, wing=40)
    d1 = G(tilt=-50, alt=3.0, eye="shut", crack=True, wing=60, extra=lambda r: shards(r, 0, -8, 0, n=5, seed=3))
    d2 = remains(0, stain=4.0, glass=6, stain_mat="glass", extra=lambda r: shards(r, 0, -6, 1, n=7, seed=4, fall=1.0))
    corpse = remains(1, stain=4.5, glass=7, stain_mat="glass")
    knock = G(tilt=-24, alt=3.0, eye="shut", wing=50)
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.08] * 6),
             ("Shard", shard, [0.12, 0.1, 0.06, 0.08, 0.1, 0.12]),
             ("Split", split, [0.08, 0.06, 0.06, 0.1, 0.06, 0.08, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("UmbGlimmer", anims, outdir, scale=8)


def decoy_sheet(outdir):
    """The Glimmer's decoy: the same shard in pale glass (a copy is never quite the colour of the real one)."""
    G = lambda **k: glimmer(decoy=True, **k)
    idle, run, shard = glimmer_frames(decoy=True)
    spawn = [G(spin=0.15, flash=2), G(spin=0.5, wing=40), G(spin=0.9, wing=20)]
    d0 = G(tilt=-20, eye="shut", crack=True)
    d1 = G(tilt=-50, alt=3.0, eye="shut", crack=True, extra=lambda r: shards(r, 0, -8, 0, n=5, seed=3, mats=("pale", "silver")))
    d2 = remains(0, stain=3.5, glass=5, stain_mat="pale", glass_mats=("pale", "silver"))
    corpse = remains(1, stain=4.0, glass=6, stain_mat="pale", glass_mats=("pale", "silver"))
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.08] * 6),
             ("Shard", shard, [0.12, 0.1, 0.06, 0.08, 0.1, 0.12]), ("Spawn", spawn, [0.08, 0.08, 0.1])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], G(tilt=-24, eye="shut"))
    return sheet("UmbGlimmerDecoy", anims, outdir, scale=8)


# ================================================================== GLOOM LURKER (T1): an ink-drop body on long legs, many eyes
def lurker(lift=0.0, lean=0.0, legs=0.0, gait=None, crouch=0.0, jaw=0.0, eyes="open", reach=0.0, breath=None, extra=None,
           dx=0.0, stretch=1.0):
    """Low and wide. lift raises the body; crouch drops it; legs spreads the knees; gait = phase for a scuttle; reach
    pushes the face plate forward (the lunge); jaw opens the fangs; breath = k for a darkness exhale."""
    r = Rig()
    by = -4.6 - lift + crouch
    bx = dx
    T = Xf(lean, (bx, by))
    # legs: four a side seen as pairs, knees high, thin pale-tipped feet
    feet = [(-9.0, 0.0), (-5.0, 0.0), (5.5, 0.0), (9.5, 0.0)]
    hips = [(-2.0, -0.5), (-0.8, -0.2), (0.8, -0.2), (2.0, -0.5)]
    for i, (f, h) in enumerate(zip(feet, hips)):
        fx = f[0] * (1.0 + 0.1 * legs) + bx
        fy = 0.0
        if gait is not None:
            ph = gait + i * math.pi / 2
            fx += 1.4 * math.cos(ph); fy = -max(0.0, 1.4 * math.sin(ph))
        hx, hy = T(bx + h[0], by + h[1] + 1.0)
        kx = (hx + fx) / 2 + (1.0 if fx > hx else -1.0) * 0.6
        ky = by - 3.6 - 0.6 * legs + crouch * 0.6
        far = i in (1, 2)
        z = -1.5 if far else 1.5
        r.tube([(hx, hy), (kx, ky)], [0.8, 0.6], "ink", z, bias=-0.2 if far else 0.15)
        r.tube([(kx, ky), (fx, fy - 0.4)], [0.6, 0.4], "ink", z + 0.01, bias=-0.2 if far else 0.15)
        r.dot(fx, fy, "bone", 2 if far else 3, z + 0.02)
    # the body: an ink drop, rounded at the back, narrowing into the face plate
    r.ell(bx - 1.2, by, 4.6 * stretch, 3.4, "ink", 0.0, bias=0.15, ang=lean)
    r.ell(bx - 2.2, by - 1.4, 2.6, 1.6, "ink", 0.05, bias=0.35, ang=lean)
    r.dot(bx - 3.6, by - 2.6, "lilac", 2, 0.1)                # a lilac sheen on the ink
    r.dot(bx - 2.6, by - 3.0, "lilac", 3, 0.1)
    # the pale face plate with six eyes
    fx_, fy_ = T(bx + 3.4 + reach, by - 0.4)
    r.ell(fx_, fy_, 2.8, 2.6, "bone", 2.0, bias=-0.15)
    pts = [(-1, -1), (1, -1), (0, 0), (2, 0), (-1, 1), (1, 1)]
    for k, (ex, ey) in enumerate(pts):
        x, y = fx_ + ex, fy_ + ey - 0.4
        if eyes == "open":
            r.dot(x, y, "lilac", 2 if k % 2 else 3, 2.1)
        elif eyes == "wide":
            r.dot(x, y, "lilac", 3, 2.1)
        elif eyes == "shut":
            r.dot(x, y, "void", 1, 2.1)
    # fangs under the plate
    ox, oy = fx_ + 1.4, fy_ + 2.0
    r.line(ox, oy, ox + 0.6 + jaw * 0.4, oy + 1.6 + jaw * 0.6, "bone", 2.2, tone=3)
    r.line(ox - 1.4, oy, ox - 1.2 + jaw * 0.2, oy + 1.4 + jaw * 0.8, "bone", 2.15, tone=2)
    if jaw > 0.5:
        r.dot(ox - 0.3, oy + 1.0, "void", 0, 2.12)
    if breath is not None:
        k = breath
        for i in range(4 + k):
            px = fx_ + 3 + i * 1.6 * (1 + 0.3 * k)
            py = fy_ + 1 - math.sin(i * 1.3) * (0.6 + 0.4 * k)
            r.ell(px, py, 1.2 + 0.4 * k + i * 0.2, 0.9 + 0.3 * k, "dark", 4.0 + i * 0.01, flat=1 + (i + k) % 2)
    if extra: extra(r)
    return r.resolve()


def lurker_sheet(outdir):
    L = lurker
    idle = [L(lift=[0, 0.3, 0.5, 0.3][i], legs=[0, 0.2, 0.3, 0.2][i]) for i in range(4)]
    run = [L(gait=i / 6 * math.tau, lean=6, lift=0.4 * abs(math.sin(i / 6 * math.tau * 2))) for i in range(6)]
    # Ambush (7): sink low (0-1), eyes flare (2), LUNGE (3: fangs out, body stretched), bite shut (4), back (5-6)
    amb = [L(crouch=1.2, legs=0.6), L(crouch=2.0, legs=0.9, lean=-6, eyes="wide"), L(crouch=2.2, legs=1.0, lean=-10, eyes="wide", jaw=1.0),
           L(lift=1.0, lean=10, reach=3.5, jaw=2.0, stretch=1.15, dx=2.0, eyes="wide", legs=-0.4),
           L(lift=0.6, lean=6, reach=2.5, jaw=0.0, dx=2.0, legs=-0.2), L(lift=0.2, lean=2, reach=1.0, dx=1.0), L()]
    # Gloom (7): rear up (0-1), draw breath (2), exhale darkness (3-5), settle (6)
    gl = [L(lift=0.8, lean=-6), L(lift=1.6, lean=-12, jaw=1.0, eyes="wide"), L(lift=1.8, lean=-14, jaw=0.5, legs=0.4),
          L(lift=1.0, lean=4, jaw=2.0, breath=0), L(lift=0.8, lean=6, jaw=2.0, breath=1), L(lift=0.6, lean=4, jaw=1.5, breath=2), L()]
    d0 = L(lift=0.6, lean=-14, eyes="shut", legs=0.8, jaw=1.0)
    d1 = L(crouch=2.5, lean=-20, eyes="shut", legs=1.6)
    d2 = remains(0, stain=8.0, glass=0, stain_mat="ink", extra=lambda r: [r.dot(x, -1, "bone", 2, 2) for x in (-6, -3, 4, 7)])
    corpse = remains(1, stain=9.0, glass=0, stain_mat="ink",
                     extra=lambda r: (r.ell(2.0, -1.5, 2.2, 1.6, "bone", 2.0), [r.dot(x, -1, "bone", 2, 2) for x in (-7, -4, 5, 8)]))
    knock = L(lift=1.2, lean=-16, eyes="shut", legs=0.6)
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.07] * 6),
             ("Ambush", amb, [0.1, 0.1, 0.12, 0.06, 0.1, 0.1, 0.12]),
             ("Gloom", gl, [0.1, 0.1, 0.12, 0.1, 0.1, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("UmbGloomLurker", anims, outdir, scale=8)


# ================================================================== build
def all_jobs():
    import umbrael_v2_t2 as T2
    import umbrael_v2_t3 as T3
    import umbrael_v2_fx as FX
    jobs = [("UmbShadeImp", imp_sheet), ("UmbGlimmer", glimmer_sheet), ("UmbGlimmerDecoy", decoy_sheet),
            ("UmbGloomLurker", lurker_sheet)]
    return jobs + T2.JOBS + T3.JOBS + FX.JOBS


def main():
    argv = sys.argv[1:]
    args = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] != "--only")]
    out = args[0] if args else DEFAULT_OUT
    only = None
    for i, a in enumerate(sys.argv):
        if a == "--only" and i + 1 < len(sys.argv): only = set(sys.argv[i + 1].split(","))
    os.makedirs(out, exist_ok=True)
    for name, fn in all_jobs():
        if only and name not in only: continue
        fn(out)


if __name__ == "__main__":
    main()
