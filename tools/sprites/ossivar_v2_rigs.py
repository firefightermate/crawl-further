"""OSSIVAR v2: every Ossivar monster and effect sheet, drawn with the material renderer of
jinx_v2_rigs.py (lit shapes, 3 tones per material, top-left light, selective outline, every frame posed). This file
holds the bone palette and toolkit (skulls, ribs, spines, skeletal limbs), the three tier 1 monsters, the sheet writer
and the build entry point; tier 2 is in ossivar_v2_t2.py, the tier 3s in ossivar_v2_t3a.py / _t3b.py, the effects and
the idol in ossivar_v2_fx.py.

    python3 ossivar_v2_rigs.py [outdir] [--only Name,Name]

Writes to art/out_ossivar/ by default. Manifest format as every other sheet: <id>.png + <id>.json (cellW, cellH, cols,
anims[{name, frames, durations}]) + <id>_preview.png, feet at (cellW // 2, cellH - 2), facing right.
"""
import math, os, sys, random

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import jinx_v2_rigs as J  # noqa: E402  (the renderer: Rig, ramps, resolve)
from jinx_v2_rigs import Xf, chain, ik, lerp, line_px, poly_px, flip_x  # noqa: E402,F401
from anim import SprRGB, pack, preview  # noqa: E402
from PIL import Image  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "art", "out_ossivar")


def _h(s):
    s = s.lstrip("#"); return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


# ================================================================== palette (ink, shadow, base, light, hi)
OSS_RAMPS = {
    "bone":   ["2c2028", "6a5650", "a6927a", "d0c2a0", "eee4c6"],   # bone ivory, shadows go grave-violet
    "obone":  ["2c1e14", "6a5026", "a6864a", "d2b46c", "eedaa0"],   # yellowed tusk ivory
    "dbone":  ["221a1e", "4e4242", "7a6c62", "a0927e", "c4b89c"],   # old dark bone (far limbs, grave-stained)
    "umber":  ["1c1410", "3a2a20", "5a4232", "7c5c44", "9c7c5c"],   # grave dirt, digger's coat
    "dirt":   ["1a120c", "3a2618", "5a3e26", "7a5836", "9a7650"],   # loose soil
    "marrow": ["22070c", "541018", "8a1c22", "b6382e", "da6a4a"],   # marrow-red cloth and flesh
    "iron":   ["0c0c12", "1c1c26", "32323c", "4e4e5a", "747480"],
    "bronze": ["0c1816", "1c3830", "2c5a4a", "488866", "78b690"],   # verdigris grave goods
    "fviol":  ["12081a", "2a1436", "482456", "683a76", "8c5a96"],   # funeral violet
    "hide":   ["181418", "3a3236", "5c5256", "827676", "a69a96"],   # grave dog's grey hide
    "bhide":  ["1e1824", "3a3242", "584e64", "7a6e88", "a094ac"],   # black hide
    "feath":  ["10101a", "242836", "3c4458", "5e6a86", "8896b4"],   # crow-black feathers (blue-violet sheen)
    "rust":   ["1c0a08", "48200e", "723418", "985226", "be7a3e"],
    "stone":  ["181a1a", "343836", "545a56", "788078", "9ea69a"],   # lichen-grey headstone
    "lichen": ["141c0c", "283814", "445820", "687c32", "90a04e"],
    "tar":    ["0e0a0a", "1e1818", "322828", "4a3c3a", "64524e"],
    "rope":   ["1c1208", "3c2a14", "5c4224", "7e5e3e", "9e825e"],
    "moss":   ["0a140a", "182c14", "2a4820", "42682e", "689042"],
    "ghoul":  ["161818", "303634", "505a54", "748070", "9aa692"],   # ghoul skin, grey-green
    "slate":  ["121418", "282c36", "444a56", "666e7a", "8e96a0"],
    "rawred": ["280a10", "661a22", "a03838", "cc6858", "e89a82"],   # vulture neck
    "gold":   ["2e1a10", "6e4618", "a8782a", "dcb04a", "fbe796"],
    "cloth":  ["16121a", "2c2632", "463e4c", "625868", "827888"],   # mourning black
    # emissive
    "mglow":  ["4a0a10", "9a1420", "e0302a", "ff7050", "ffc0a0"],   # marrow glow (eyes, veins)
    "lant":   ["5a3a08", "b07a10", "f0b830", "ffe070", "fff8c0"],   # lantern yellow
    "gfire":  ["0a3a1a", "1a7a3a", "3ac060", "8af090", "d8ffe0"],   # grave fire
    "spirit": ["3a2a4a", "6a5280", "a48ac0", "d2c0ea", "f6eeff"],   # pale soul light
    "dust":   ["2a2420", "4a423a", "6e6458", "948a7c", "b8b0a2"],   # dust puffs
    "gas":    ["0e2416", "1c4a2a", "347a42", "5aa85c", "94d68a"],   # grave gas (shaded, not glowing)
}
J.RAMPS.update({k: [_h(c) for c in v] for k, v in OSS_RAMPS.items()})
J.EMISSIVE.update({"mglow", "lant", "gfire", "spirit", "dust"})
J.SHINY.update({"bone", "obone", "gold", "bronze", "iron", "bhide", "feath", "cloth", "umber", "hide"})
RAMPS = J.RAMPS
LIGHT_MATS = ("bone", "obone", "ivory", "gold", "white", "flesh", "rope", "lichen", "stone")
STONE = [_h(c) for c in ("2a2a30", "4c4c54", "6e6e76", "92929a", "b6b6bc")]


def stone(s):
    """Statue: tones map onto the stone ramp (clusters survive); light materials sit one step up."""
    px = {}
    for k, (m, t) in s.tones.items():
        lift = 1 if m in LIGHT_MATS else 0
        if m in J.EMISSIVE: t = 2
        px[k] = STONE[max(0, min(4, t + lift if t > 0 else 0))]
    out = SprRGB(px); out.tones = {k: ("stone", 0) for k in px}
    return out


# ================================================================== the scaled buffer
# Each sheet is posed in its own units; SCALE stretches a sheet's shapes to its final size (x, y). Hand-pixelled stamps
# (heads, masks) keep their pixels and only move, and 1 px lines stay 1 px, so a bigger body keeps crisp details.
SX = SY = 1.0
SCALE = {
    "OssCairnCrow": (1.35, 1.0),
    "OssBoneLancer": (1.25, 1.04), "OssGravedigger": (1.25, 1.14), "OssGravetusk": (1.06, 1.4), "OssBarghest": (1.0, 1.45),
    "OssCarrionVulture": (1.22, 1.05),
    "OssCharnelRider": (1.22, 1.04), "OssSpinehook": (1.62, 1.32), "OssTombwright": (1.37, 1.25), "OssCoffinBearer": (1.35, 1.04),
    "OssBoneMammoth": (1.13, 1.5), "OssRazorback": (1.25, 1.78), "OssCerberus": (1.4, 1.4), "OssChurchGrim": (1.2, 1.3),
    "OssOssuary": (1.2, 1.0), "OssMarrowWyrm": (1.06, 1.1), "OssCarrionRoc": (1.36, 1.0),
}


def _p(pts):
    return [(x * SX, y * SY) for (x, y) in pts]


class Rig(J.Rig):
    """The jinx_v2 material buffer, with every shape placed through the current sheet's SCALE."""

    def ell(self, cx, cy, rx, ry, *a, **k):
        return super().ell(cx * SX, cy * SY, rx * SX, ry * SY, *a, **k)

    def tube(self, pts, radii, *a, **k):
        rs = (SX + SY) * 0.5
        return super().tube(_p(pts), [r * rs for r in radii], *a, **k)

    def poly(self, pts, *a, **k):
        return super().poly(_p(pts), *a, **k)

    def line(self, x0, y0, x1, y1, *a, **k):
        return super().line(x0 * SX, y0 * SY, x1 * SX, y1 * SY, *a, **k)

    def polyline(self, pts, *a, **k):
        return super().polyline(_p(pts), *a, **k)

    def dot(self, x, y, *a, **k):
        return super().dot(x * SX, y * SY, *a, **k)

    def dots(self, pts, *a, **k):
        return super().dots(_p(pts), *a, **k)

    def stamp(self, grid, x, y, *a, **k):
        return super().stamp(grid, x * SX, y * SY, *a, **k)

    def resolve(self, *a, **k):
        """As the renderer's, plus a rim light: dark materials take one tone up along their open top and left edges, so
        black hide and feathers keep their shape on the crypt floor."""
        s = super().resolve(*a, **k)
        tones = getattr(s, "tones", None)
        if not tones: return s
        for (x, y), (m, t) in list(tones.items()):
            if m not in RIM or t >= 4: continue
            if (x, y - 1) not in s.px or (x - 1, y) not in s.px:
                t2 = min(4, t + 1)
                tones[(x, y)] = (m, t2)
                s.px[(x, y)] = RAMPS[m][t2]
        return s


RIM = {"bhide", "feath", "cloth", "umber", "tar", "hide", "slate", "fviol", "coffin"}


# ================================================================== bone toolkit
def bone(r, a, b, rad=0.7, z=0.0, mat="bone", knob=True, bias=0.0, thin=None):
    """A long bone from a to b with knobbed ends."""
    p = r.tube([a, b], [rad, rad * 0.9], mat, z, bias=bias, thin=rad < 0.8 if thin is None else thin)
    if knob and rad >= 0.6:
        for (x, y) in (a, b):
            r.ell(x, y, rad + 0.45, rad + 0.35, mat, z + 0.001, bias=bias, part=p)
    return p


def vertebrae(r, pts, z, mat="bone", proc=0, tone_a=3, tone_b=1, up=(0, -1)):
    """A spine through pts: alternating lit / dark segments (the joints), with spinal processes `proc` px long."""
    p = r.part(True, z)
    k = 0
    for i in range(len(pts) - 1):
        under(r, pts[i], pts[i + 1], mat, z, max(0, min(tone_a, tone_b) - 1) if min(tone_a, tone_b) > 1 else 1)
        a = (pts[i][0] * SX, pts[i][1] * SY); b = (pts[i + 1][0] * SX, pts[i + 1][1] * SY)
        for (x, y) in line_px(int(round(a[0])), int(round(a[1])), int(round(b[0])), int(round(b[1]))):
            r.put(x, y, z, mat, 0.5, p, tone_a if (k // 2) % 2 == 0 else tone_b)
            k += 1
    if proc:
        for i, (x, y) in enumerate(pts[1:-1]):
            if i % 1 == 0:
                for j in range(1, proc + 1):
                    r.put(x * SX + up[0] * j, y * SY + up[1] * j, z - 0.01, mat, 0.5, p, 2 if j < proc else 3)
    return p


def rib(r, x, y, ang, ln, bend, z, mat="bone", tone=3, far=False):
    """One rib from (x, y): leaves at ang, curls by `bend` degrees along its length ln."""
    pts = chain(x, y, [(ln * 0.35, ang), (ln * 0.35, ang + bend * 0.5), (ln * 0.3, ang + bend)])
    tones = [tone, tone - 1 if tone > 1 else tone, max(0, tone - 2)] if not far else [1, 1, 0]
    return r.polyline(pts, mat, z, tones=tones)


def ribcage(r, anchors, ang, ln, bend, z, mat="bone", far=True, shrink=0.12, far_mat="dbone"):
    """Ribs from each spine anchor (front ones longest); the far side's ribs show darker between them."""
    for i, (x, y) in enumerate(anchors):
        L = ln * (1.0 - shrink * i)
        if far:
            rib(r, x + 0.5, y, ang - 6, L * 0.9, bend, z - 0.5, far_mat, far=True)
        rib(r, x, y, ang, L, bend, z, mat, tone=3)


SKULL_EYES = {"sock": None}


def skull(r, x, y, s=1.0, z=0.0, face=1, jaw=0.0, mat="bone", eye=None, tilt=0.0, teeth=True, muzzle=1.0, crest=0,
          brow=False, horn=None, glint=True):
    """A skull in profile. (x, y) = the base of the skull (where the neck meets it). s scales (1.0 is ~6 x 5 px).
    jaw: opening in degrees. eye: None for an empty socket or an emissive material for a lit one."""
    T = Xf(tilt * face, (x, y))
    F = lambda dx, dy: T(x + dx * s * face, y + dy * s)
    cx, cy = F(-0.3, -2.7)
    p = r.ell(cx, cy, 2.7 * s, 2.4 * s, mat, z)
    mx, my = F(1.9, -1.6)
    r.ell(mx, my, 1.9 * s * muzzle, 1.2 * s, mat, z + 0.01, part=p, bias=0.05)
    if crest:
        hx, hy = F(-1.6, -4.6)
        r.line(hx, hy, hx - crest * face, hy - crest * 0.6, mat, z + 0.02, tone=2)
    # jaw hinged under the ear
    a = math.radians(jaw)
    jx, jy = F(-0.6, -0.9)
    tx, ty = F(2.6 * muzzle, -0.3)
    dx, dy = tx - jx, ty - jy
    ex = jx + dx * math.cos(a * face) - dy * math.sin(a * face)
    ey = jy + dx * math.sin(a * face) + dy * math.cos(a * face)
    jp = r.tube([(jx, jy), (ex, ey)], [0.75 * s, 0.6 * s], mat, z - 0.02, bias=-0.15)
    if teeth and s >= 0.9:
        for i in range(2 + int(muzzle * s * 1.5)):
            t = (i + 1.0) / (3.0 + muzzle * s * 1.5)
            px, py = F(0.4 + 2.4 * muzzle * t, -0.55)
            r.dot(px, py, mat, 4 if i % 2 == 0 else 2, z + 0.03)
            if jaw > 8:
                qx, qy = jx + (ex - jx) * (0.35 + 0.6 * t), jy + (ey - jy) * (0.35 + 0.6 * t) - 0.6
                r.dot(qx, qy, mat, 3 if i % 2 else 2, z + 0.03)
    # socket, nose, brow
    sx, sy = F(0.9, -2.5)
    sk = r.part(True, z + 0.05)
    r.put(sx, sy, z + 0.05, "iron", 0.5, sk, 0)
    if s >= 1.2:
        r.put(sx + face, sy, z + 0.05, "iron", 0.5, sk, 0)
        r.put(sx, sy + 1, z + 0.05, "iron", 0.5, sk, 1)
    if eye:
        r.put(sx, sy, z + 0.06, eye, 0.5, sk, 3)
        if s >= 1.2: r.put(sx + face, sy, z + 0.06, eye, 0.5, sk, 2)
        if glint: r.put(sx, sy - 1, z + 0.06, eye, 0.5, sk, 4) if s >= 1.4 else None
    nx, ny = F(2.6 * muzzle, -1.8)
    r.put(nx, ny, z + 0.05, "iron", 0.5, sk, 1)
    if brow:
        bx, by = F(0.4, -3.6)
        r.line(bx, by, bx + 1.6 * s * face, by + 0.2, mat, z + 0.04, tone=4)
    if horn:
        hx, hy = F(-0.8, -4.4)
        r.tube(chain(hx, hy, horn), [0.8, 0.6, 0.4, 0.3], "obone", z - 0.3)
    return p


def dust(r, x, y, k, w=1.0, n=3, z=6.0, mat="dust"):
    """Floor dust kicked up: k = 0 (burst) .. 2 (thinning)."""
    for side in (-1, 1):
        for i in range(max(0, n - k)):
            px = x + side * (2 + i * 2 + k * 1.5) * w
            py = y - (i % 2) - (1 if k else 0)
            r.ell(px, py, max(0.6, 1.3 - 0.3 * k), 0.9, mat, z + i * 0.01, flat=2 if i else 3)


def smear(r, pts, mat="white", tone=3, z=7.0, width=1):
    """A motion arc: thick at the lead, thinning behind."""
    r.polyline(pts, mat, z, tones=[max(1, tone - (len(pts) - 2 - i)) for i in range(len(pts) - 1)])
    if width > 1:
        r.polyline([(x, y + 1) for (x, y) in pts[-3:]], mat, z - 0.01, tone=max(1, tone - 1))


def arc_pts(cx, cy, rx, ry, a0, a1, n=8):
    return [(cx + rx * math.cos(math.radians(lerp(a0, a1, i / (n - 1.0)))), cy + ry * math.sin(math.radians(lerp(a0, a1, i / (n - 1.0)))))
            for i in range(n)]


def bone_bits(r, x, y, k=0, n=5, seed=3, z=6.0, spread=5.0, mat="bone"):
    """Loose bone chips scattering (k 0..3)."""
    rnd = random.Random(seed)
    for i in range(n):
        a = rnd.uniform(math.pi, 2 * math.pi)
        d = spread * (0.4 + 0.6 * rnd.random()) * (0.4 + 0.3 * k)
        px, py = x + d * math.cos(a), y + d * math.sin(a) * 0.7 + k * k * 0.5
        if rnd.random() < 0.5:
            r.line(px, py, px + 1, py, mat, z, tone=3 if i % 2 else 2)
        else:
            r.dot(px, py, mat, 3 if i % 2 else 4, z)


def heap(r, x, y, w=9.0, n=9, seed=5, z=0.0, mat="bone", skull_at=None, s=1.0, eye=None, h=1.0):
    """A heap of loose bones (the collapse and corpse poses)."""
    rnd = random.Random(seed)
    for i in range(n):
        a = rnd.uniform(-35, 35) + (90 if i % 3 == 0 else 0)
        L = rnd.uniform(2.5, 4.5)
        cx = x + rnd.uniform(-w / 2, w / 2)
        cy = y - 0.6 - rnd.uniform(0, 2.2 * h) * (1 - abs(cx - x) / (w * 0.6 + 0.01))
        dx, dy = L / 2 * math.cos(math.radians(a)), L / 2 * math.sin(math.radians(a)) * 0.6
        bone(r, (cx - dx, cy - dy), (cx + dx, cy + dy), 0.6, z + i * 0.01, mat if i % 4 else "dbone")
    if skull_at is not None:
        skull(r, skull_at[0], skull_at[1], s, z + 0.5, face=skull_at[2] if len(skull_at) > 2 else 1, jaw=10, eye=eye)


# ================================================================== the skeletal humanoid
def skel(r, hip, chest, neck, head=None, hands=((4, -6), (-2, -6)), feet=((2, 0), (-2, 0)), z=0.0, mat="bone",
         far_mat="dbone", arm=(3.0, 3.0), leg=(3.0, 3.0), sh_w=1.6, hip_w=1.2, ribs=3, rib_len=3.6, face=1,
         elbows=(1, -1), knees=(-1, -1), skip=(), pelvis=True, hand_mat=None, thick=0.7):
    """A skeleton from hip / chest / neck points, two hands and two feet (index 0 = near side). Returns the
    near shoulder and the near hand so callers can hang weapons on them."""
    out = {}
    # far leg, far arm first (darker)
    for k in (1, 0):
        m = mat if k == 0 else far_mat
        zz = z + (0.6 if k == 0 else -0.8)
        hx, hy = hip[0] + (hip_w * 0.5 if k == 0 else -hip_w * 0.5) * face, hip[1]
        if "legs" not in skip:
            fx_, fy_ = feet[k]
            kx, ky = ik(hx, hy, fx_, fy_ - 0.6, leg[0], leg[1], bend=knees[k] * face)
            bone(r, (hx, hy), (kx, ky), thick + 0.1, zz, m)
            bone(r, (kx, ky), (fx_, fy_ - 0.6), thick, zz + 0.01, m, knob=False)
            r.line(fx_ - 0.5 * face, fy_, fx_ + 1.6 * face, fy_, m, zz + 0.02, tone=2 if k == 0 else 1)
    # pelvis + spine + ribs
    if pelvis:
        r.ell(hip[0], hip[1] - 0.3, 1.6, 1.1, mat, z + 0.1)
    sp = [hip, ((hip[0] + chest[0]) / 2 + 0.4 * face, (hip[1] + chest[1]) / 2), chest, neck]
    vertebrae(r, sp, z + 0.2, mat, proc=0)
    if ribs:
        n = ribs
        anchors = [(lerp(chest[0], hip[0], 0.18 * i) - 0.4 * face, lerp(chest[1], hip[1], 0.18 * i)) for i in range(n)]
        sang = math.degrees(math.atan2(hip[1] - chest[1], hip[0] - chest[0]))
        ribcage(r, anchors, sang - 75 * face, rib_len, 62 * face, z + 0.3, mat, far_mat=far_mat)
    for k in (1, 0):
        m = mat if k == 0 else far_mat
        zz = z + (1.2 if k == 0 else -1.0)
        sx, sy = chest[0] + (sh_w * 0.4 if k == 0 else -sh_w * 0.6) * face, chest[1] - 0.6
        if k == 0: out["shoulder"] = (sx, sy)
        if "arms" in skip or (k == 1 and "far_arm" in skip) or (k == 0 and "near_arm" in skip): continue
        hx, hy = hands[k]
        ex, ey = ik(sx, sy, hx, hy, arm[0], arm[1], bend=elbows[k] * face)
        bone(r, (sx, sy), (ex, ey), thick, zz, m)
        bone(r, (ex, ey), (hx, hy), thick - 0.05, zz + 0.01, m, knob=False)
        hm = hand_mat or m
        r.dot(hx, hy, hm, 3 if k == 0 else 1, zz + 0.02)
        r.dot(hx + face, hy + 1, hm, 2 if k == 0 else 1, zz + 0.02)
        out["hand%d" % k] = (hx, hy)
        out["elbow%d" % k] = (ex, ey)
    r.line(chest[0] - sh_w * 0.6 * face, chest[1] - 0.6, chest[0] + sh_w * 0.4 * face, chest[1] - 0.6, mat, z + 0.25, tone=3)
    return out


# ================================================================== sheet assembly
BUILT = {}
SYNC = {}
NOTES = {}


def sheet(name, anims, outdir, scale=6, pad=2, min_w=0, min_h=0):
    allf = [f for a in anims for f in a[1] if f.px]
    for an, fr, du in anims:
        assert du and len(du) == len(fr), (name, an, len(fr), len(du))
    x0 = min(f.bbox()[0] for f in allf); x1 = max(f.bbox()[2] for f in allf)
    y0 = min(f.bbox()[1] for f in allf)
    hw = max(-x0, x1 + 1) + pad
    cw = max(min_w, 2 * hw)
    ch = max(min_h, -y0 + 1 + pad + 2)
    feet = (cw // 2, ch - 2)
    img, man = pack(name, anims, cw, ch, feet, outdir)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    BUILT[name] = {"cell": (cw, ch), "feet": feet, "anims": [(a, len(f), list(d)) for a, f, d in anims]}
    print("built %-22s cell %dx%d  %s" % (name, cw, ch, ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))
    return img, man


def fx(name, cell, origin, anims, outdir, scale=8):
    """An effect sheet with a fixed cell and origin (the point Strike.ArtAt pins to the effect's position)."""
    img, man = pack(name, anims, cell[0], cell[1], origin, outdir)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    BUILT[name] = {"cell": cell, "feet": origin, "anims": [(a, len(f), list(d)) for a, f, d in anims]}
    print("built %-22s cell %dx%d  %s" % (name, cell[0], cell[1], ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))


def tail_anims(idle0, death, death_d, knock):
    return [("Death", death, death_d), ("Dead", [death[-1]], [0.3]), ("Statue", [stone(idle0)], [0.2]),
            ("Knockback", [knock], [0.2]), ("Portrait", [idle0], [0.2])]


def done(r):
    """Resolve an effect (no floor clip, no cast shadows or contours: effects are small and float)."""
    return r.resolve(floor=False, cast=False, contour=False)


# ================================================================== hand-pixelled heads
# legend: H/L/B/S/K = bone tones 4..0; k = socket (iron ink); n = nose; e/E = lit eye (mglow 3 / 4); T/t = tooth / gap;
# g/G/d = hide (2 / 3 / 1); w = jaw wire (bronze); x = far bone (dbone 2)
BONE_LEG = {"H": ("bone", 4), "L": ("bone", 3), "B": ("bone", 2), "S": ("bone", 1), "K": ("bone", 0), "k": ("iron", 0),
            "n": ("iron", 1), "e": ("mglow", 3), "E": ("mglow", 4), "T": ("bone", 4), "t": ("bone", 1), "w": ("bronze", 3),
            "W": ("bronze", 2), "g": ("hide", 2), "G": ("hide", 3), "d": ("hide", 1), "D": ("hide", 0), "x": ("dbone", 2),
            "X": ("dbone", 1), "o": ("obone", 3), "O": ("obone", 4), "q": ("obone", 2), "Q": ("obone", 1)}
SKULLS = {
    # (cranium rows, jaw rows, pivot (x, y) = the neck joint under the skull)
    "L": ("""
...LHHL..
.LHHHHLB.
LHHLLLLBS
LLkkLLLkS
SLkeLBLeS
.SBLBnBBS
..STtTtTS
""", """
..STtTtS.
...SBBBS.
""", (3, 7)),
    "XL": ("""
....LHHHL...
..LHHHHHHLB.
.LHHHLLLLLBS
LHHLLLLLLLBS
LLkkkLLLkkkS
LLkeekLBkeeS
SLkkkBLBkkkS
.SBLBBnnBBBS
..SBLBnBBBS.
...STtTtTtS.
""", """
...STtTtTS..
....SBBBBS..
""", (4, 10)),
    "M": ("""
..LHL..
.LHHLB.
LHLLLBS
LkkLLkS
SkeBLeS
.SBnBS.
..TtTt.
""", """
..STtS.
...SS..
""", (3, 7)),
    "S": ("""
.LHL.
LkLkS
SeBeS
.TtT.
""", """
.SS..
""", (2, 4)),
}


def skullp(r, x, y, size="M", z=0.0, jaw=0, eye=True, flip=False, wire=False, legend=None, dark=False):
    """A hand-pixelled 3/4 skull; (x, y) = the neck joint. jaw: px the jaw hangs open (0-3)."""
    top, jw, piv = SKULLS[size]
    leg = dict(legend or BONE_LEG)
    if not eye:
        leg["e"] = ("iron", 0); leg["E"] = ("iron", 0)
    if dark:
        for c in "HLBS": leg[c] = ("dbone", {"H": 3, "L": 2, "B": 2, "S": 1}[c])
    p = r.stamp(top, x, y, z, leg, pivot=piv, flip=flip)
    r.stamp(jw, x - (0 if not jaw else (1 if flip else -1) * 0), y + jaw, z - 0.01, leg, pivot=(piv[0], 0), flip=flip)
    if wire:
        r.dot(x + (-1 if flip else 1) * 4, y - 1, "bronze", 3, z + 0.02)
        if jaw: r.dot(x + (-1 if flip else 1) * 4, y + jaw - 1, "bronze", 2, z + 0.02)
    return p


def under(r, a, b, mat, z, tone):
    """The dark under edge of a 2 px bone: the same line one pixel down (or right, for upright bones), in final pixels."""
    ax, ay, bx, by = a[0] * SX, a[1] * SY, b[0] * SX, b[1] * SY
    ox, oy = (0, 1) if abs(bx - ax) >= abs(by - ay) else (1, 0)
    J.Rig.line(r, ax + ox, ay + oy, bx + ox, by + oy, mat, z - 0.005, tone=tone)


def lbone(r, a, b, z, near=True, mat=None, knob=True, tone=None, fine=False):
    """A limb bone 2 px thick: a lit top edge and a dark under edge (1 px only when fine); knob pixels at the joints."""
    m = mat or ("bone" if near else "dbone")
    t = tone if tone is not None else (3 if near else 2)
    p = r.line(a[0], a[1], b[0], b[1], m, z, tone=t)
    if not fine: under(r, a, b, m, z, 1)
    if knob:
        r.dot(a[0], a[1], m, min(4, t + 1), z + 0.01, part=p)
    return p


def rib_rows(r, x, y, w, n, z, face=1, gap=3, shear=0.0, mat="bone", spine=True, curl=1):
    """Ribs as stacked 2 px rows (lit top, dark under edge, a 1 px tip) off a spine at x (the back); each curls down
    at its front end. Drawn in final pixels from the scaled anchor."""
    x, y = x * SX, y * SY
    for i in range(n):
        yy = y + i * gap
        for j in range(max(1, max(2, w - i) - 1)):
            r.put(x + shear * i * gap + (j + 1) * face, yy + 1, z - 0.01, mat, 0.5, r.part(True, z), 1)
        xs = x + shear * i * gap
        ww = max(2, w - i)
        for j in range(ww):
            t = 3 if j < ww - 1 else 1
            if j == 0: t = 2
            r.put(xs + (j + 1) * face, yy, z, mat, 0.5, r.part(True, z), t if i else min(4, t + (1 if j < ww - 2 else 0)))
        for c in range(curl):
            r.put(xs + ww * face, yy + 1 + c, z, mat, 0.5, r.part(True, z), 1)
        if spine:
            r.put(xs, yy, z + 0.01, mat, 0.5, r.part(True, z), 2)
            r.put(xs, yy + 1, z + 0.01, mat, 0.5, r.part(True, z), 1 if i < n - 1 else 2)


def skeleton(r, hip, lean=0.0, hands=((4, -6), (-2, -6)), feet=((2, 0), (-2, 0)), z=0.0, arm=(3.0, 3.0), leg=(3.0, 3.0),
             ribs=3, rib_w=4, torso=5.0, elbows=(1, 1), knees=(1, 1), face=1, skip=(), mat="bone", hand_tone=4):
    """A thin skeleton: pelvis at hip, a spine `torso` px up (leaning `lean` deg forward), rib rows, 1 px limbs.
    Returns the neck point and the shoulder."""
    hx, hy = hip
    a = math.radians(lean)
    nx, ny = hx + torso * math.sin(a) * face, hy - torso * math.cos(a)
    shear = math.tan(a) * face * -1.0
    # far leg / arm (behind)
    sh = (nx - 0.5 * face, ny + 1.0)
    for k in (1, 0):
        near = k == 0
        zz = z + (0.5 if near else -0.8)
        if "legs" not in skip:
            fx_, fy_ = feet[k]
            hipk = (hx + (0.5 if near else -0.5) * face, hy)
            kx, ky = ik(hipk[0], hipk[1], fx_, fy_ - 0.5, leg[0], leg[1], bend=-knees[k] * face)
            lbone(r, hipk, (kx, ky), zz, near)
            lbone(r, (kx, ky), (fx_, fy_ - 0.5), zz, near, knob=False)
            r.line(fx_, fy_, fx_ + 1.4 * face, fy_, "bone" if near else "dbone", zz, tone=2 if near else 1)
    for k in (1, 0):
        near = k == 0
        zz = z + (1.5 if near else -1.0)
        if "arms" in skip or (not near and "far_arm" in skip) or (near and "near_arm" in skip): continue
        hx_, hy_ = hands[k]
        s0 = (sh[0] + (0.5 if near else -0.8) * face, sh[1])
        ex, ey = ik(s0[0], s0[1], hx_, hy_, arm[0], arm[1], bend=elbows[k] * face)
        lbone(r, s0, (ex, ey), zz, near)
        lbone(r, (ex, ey), (hx_, hy_), zz, near, knob=False)
        r.dot(hx_, hy_, "bone" if near else "dbone", hand_tone if near else 2, zz + 0.02)
    # spine, ribs, pelvis
    vertebrae(r, [(hx, hy), (nx, ny)], z, mat, tone_a=2, tone_b=1)
    if ribs:
        rib_rows(r, nx - 0.5 * face, ny + 1, rib_w, ribs, z + 0.2, face, shear=shear, mat=mat)
    r.ell(hx + 0.3 * face, hy - 0.2, 1.5, 0.9, mat, z + 0.1, bias=0.1)
    return (nx, ny), sh


# ================================================================== RATTLEBONES (T1): a hunched skeleton, its skull too big
def rattle(lean=18.0, bob=0.0, feet=((2.5, 0.0), (-1.5, 0.0)), long_hand=(6.5, -2.0), short_hand=(0.0, -7.0), head=True,
           jaw=1, skull_at=None, eye=True, stump_glow=False, extra=None, smear_pts=None, crouch=0.0, dust_at=None, hop=0.0):
    """lean: degrees forward (the hunch). skull_at: (x, y, jaw) draws the skull off the neck (held or flying)."""
    r = Rig()
    hip = (-0.5, -4.6 + bob + crouch - hop)
    neck, sh = skeleton(r, hip, lean, hands=(long_hand, short_hand), feet=feet, arm=(3.2, 3.8), leg=(2.7, 2.6),
                        ribs=2, rib_w=4, torso=4.4 - crouch * 0.4, elbows=(-1, 1), knees=(1, 1))
    if head:
        skullp(r, neck[0] + 1.5, neck[1] + 0.5, "L", 3.0, jaw=jaw, eye=eye, wire=True)
    else:
        r.dot(neck[0], neck[1] - 1, "bone", 3, 2.0)
        r.dot(neck[0], neck[1] - 2, "mglow" if stump_glow else "bone", 2 if stump_glow else 1, 2.0)
    if skull_at is not None:
        skullp(r, skull_at[0], skull_at[1], "L", 5.0, jaw=skull_at[2] if len(skull_at) > 2 else 2, eye=eye, wire=True)
    if smear_pts: smear(r, smear_pts, "bone", 4)
    if dust_at: dust(r, *dust_at)
    if extra: extra(r)
    return r.resolve()


def rattle_sheet(outdir):
    R_ = rattle
    idle = [R_(bob=[0, 0.4, 0.8, 0.4][i], jaw=[1, 2, 1, 0][i], long_hand=(6.5, -2.0 + [0, 0.4, 0.8, 0.4][i]),
               short_hand=(0.0, -7.0 + [0, 0.5, 0.8, 0.5][i])) for i in range(4)]

    def run_pose(i, head=True):
        ph = i / 6.0 * math.tau
        f1 = (1.5 + 2.8 * math.cos(ph), -max(0.0, 1.6 * math.sin(ph)))
        f2 = (0.0 - 2.8 * math.cos(ph), -max(0.0, -1.6 * math.sin(ph)))
        return R_(lean=26, bob=-0.6 * abs(math.sin(ph)), feet=(f1, f2), long_hand=(6.0 - 2.5 * math.cos(ph), -2.0 - 1.2 * abs(math.sin(ph))),
                  short_hand=(1.5 + 2.0 * math.cos(ph), -7.5), jaw=[0, 1, 2, 1, 0, 1][i], head=head, stump_glow=not head and i % 2 == 0)
    run = [run_pose(i) for i in range(6)]
    bare = [R_(bob=[0, 0.4, 0.8, 0.4][i], head=False, stump_glow=i % 2 == 0, long_hand=(6.5, -2.0 + [0, 0.4, 0.8, 0.4][i]),
               short_hand=(0.0, -7.0 + [0, 0.5, 0.8, 0.5][i])) for i in range(4)]
    bare_run = [run_pose(i, head=False) for i in range(6)]
    # Lob (7): grab the skull (0), wrench it off overhead (1), cock it back (2), HURL (3: it leaves the hand at (9, -10)),
    # follow through headless (4), straighten (5-6)
    lob = [R_(lean=10, long_hand=(4.0, -14.0), jaw=2, crouch=0.6),
           R_(lean=-4, head=False, long_hand=(1.0, -17.0), skull_at=(1.0, -15.0, 3), crouch=0.2),
           R_(lean=-16, head=False, long_hand=(-3.5, -15.5), skull_at=(-3.5, -13.5, 3), short_hand=(3.0, -8.0)),
           R_(lean=34, head=False, long_hand=(8.5, -8.0), short_hand=(-2.0, -8.0), feet=((4.0, 0.0), (-2.5, 0.0)), stump_glow=True,
              smear_pts=[(-3, -17), (1, -17), (5, -15), (8, -12)], extra=lambda r: skullp(r, 10.0, -8.0, "L", 6.0, jaw=3, wire=True)),
           R_(lean=38, head=False, long_hand=(7.5, -2.0), short_hand=(-1.5, -7.0), feet=((4.0, 0.0), (-2.5, 0.0)), stump_glow=True),
           R_(lean=26, head=False, long_hand=(6.5, -2.0), stump_glow=True),
           R_(lean=20, head=False, long_hand=(6.5, -2.0))]
    # Swipe (6, headless): crouch (0), long arm back (1), SWIPE (2: knuckles at (9, -5)), through (3: the short hand
    # beckons the skull home), recover (4-5)
    swipe = [R_(head=False, crouch=0.8, long_hand=(3.0, -4.0), stump_glow=True),
             R_(head=False, lean=4, long_hand=(-4.0, -10.0), short_hand=(3.0, -8.0), crouch=0.6),
             R_(head=False, lean=34, long_hand=(9.5, -5.0), short_hand=(-1.0, -8.0), feet=((4.0, 0.0), (-2.0, 0.0)),
                smear_pts=[(-4, -11), (1, -12), (6, -9), (10, -5)]),
             R_(head=False, lean=36, long_hand=(7.5, -1.0), short_hand=(-4.0, -11.0), feet=((4.0, 0.0), (-2.0, 0.0)), stump_glow=True),
             R_(head=False, lean=24, long_hand=(6.5, -2.0), short_hand=(-3.0, -10.0), stump_glow=True),
             R_(head=False, long_hand=(6.5, -2.0))]

    def pile(k):
        r = Rig()
        heap(r, 0.5, 0, 11.0, 11, seed=7 + (k % 2))
        skullp(r, 1.5 + (k % 2) * 0.5, -1.0 - (k % 2), "L", 1.0, jaw=1, eye=k % 2 == 0)
        if k == 0: dust(r, 0.5, 0, 0, 1.2)
        return r.resolve()
    collapse = [R_(bob=0.5, jaw=2, long_hand=(5.0, -2.0), extra=lambda r: bone_bits(r, 0, -8, 0, 3, seed=1, z=4)),
                R_(lean=0, bob=2.5, crouch=1.0, jaw=3, long_hand=(6.5, -1.0), short_hand=(-4.0, -3.0), feet=((4.0, 0.0), (-4.0, 0.0)),
                   extra=lambda r: bone_bits(r, 0, -6, 1, 5, seed=2, z=4)),
                pile(0), pile(1), pile(2), pile(3),
                R_(bob=3.0, crouch=1.5, lean=34, jaw=1, long_hand=(4.0, -1.0), short_hand=(-2.0, -2.0), feet=((3.0, 0.0), (-3.0, 0.0)),
                   extra=lambda r: bone_bits(r, 0, -3, 2, 4, seed=4, z=-1)),
                R_(bob=0.8, lean=22, jaw=2, extra=lambda r: bone_bits(r, 0, -10, 1, 3, seed=6, z=4)),
                R_(jaw=1)]
    d0 = R_(lean=-6, jaw=3, long_hand=(4.0, -9.0), short_hand=(-4.0, -9.0), feet=((3.0, 0.0), (-3.0, 0.0)))
    d1 = R_(lean=-24, bob=3.0, head=False, long_hand=(3.0, -3.0), short_hand=(-6.0, -4.0), feet=((4.0, 0.0), (-4.0, 0.0)),
            skull_at=(-5.0, -12.0, 3))
    d2 = rattle_corpse(0)
    corpse = rattle_corpse(1)
    knock = R_(lean=-10, jaw=3, long_hand=(3.0, -8.0), short_hand=(-4.0, -9.0), feet=((3.0, 0.0), (-2.0, 0.0)))
    anims = [("Idle", idle, [0.16, 0.12, 0.16, 0.12]), ("Run", run, [0.07] * 6),
             ("IdleBare", bare, [0.16, 0.12, 0.16, 0.12]), ("RunBare", bare_run, [0.07] * 6),
             ("Lob", lob, [0.12, 0.1, 0.12, 0.05, 0.08, 0.1, 0.12]),
             ("Swipe", swipe, [0.1, 0.12, 0.05, 0.08, 0.1, 0.12]),
             ("Collapse", collapse, [0.08, 0.08, 0.1, 0.1, 0.12, 0.12, 0.1, 0.08, 0.1])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("OssRattlebones", anims, outdir)


def rattle_corpse(stage):
    r = Rig()
    heap(r, 0.5, 0, 12.0 if stage else 9.0, 12, seed=11, h=0.6 if stage else 1.2)
    skullp(r, -4.0 if stage else -3.0, -0.0 if stage else -2.0, "L", 1.0, jaw=1, eye=False, flip=True)
    if not stage: dust(r, 0, 0, 1, 1.3)
    return r.resolve()


SYNC["OssRattlebones"] = {
    "Lob": [("wrench the skull off (go headless: IdleBare / RunBare from here)", 1),
            ("HURL: the skull leaves the hand at (10, -10); launch FxOssSkull along the floor", 3)],
    "Swipe": [("SWIPE: knuckles at (9, -5); hit box 12 x 10 at (7, -5)", 2), ("beckon: call the skull home", 3)],
    "Collapse": [("falls apart: invulnerable from here", 1), ("heal 1", 4), ("knit back: drop a bone pile", 6),
                 ("standing: invulnerable off", 7)],
}
NOTES["OssRattlebones"] = "Idle/Run wear the skull; IdleBare/RunBare are the headless stance while the skull is on the floor."


# ================================================================== MARROW HOUND (T1): a gaunt grave dog
HOUND_HEADS = {
    # pivot (2, 4): the back of the jaw. Hide on the crown and ears, the long muzzle bare bone.
    "shut": """
.gd......
gGgd.....
dgGgLHL..
.dgeBLLHL
..dSBBBLL
...STtTtS
""",
    "open": """
.gd......
gGgd.....
dgGgLHL..
.dgeBLLHL
..dSBBBLS
...STtt..
....tT...
...SBBL..
""",
    "wide": """
..gd.....
.gGgd....
.dgGLHL..
..dgeBLHL
...dSBLLS
....STt..
....t....
...T.....
..SBL....
..SB.....
""",
}


def hound_head(r, x, y, z, face="shut", flip=False, mat="hide"):
    leg = dict(BONE_LEG)
    if mat != "hide":
        for c, t in (("g", 2), ("G", 3), ("d", 1), ("D", 0)): leg[c] = (mat, t)
    r.stamp(HOUND_HEADS[face], x, y, z, leg, pivot=(2, 4), flip=flip)


def dog_body(r, hip, sh, legs, z=0.0, mat="hide", chest=3.0, haunch=2.2, waist=1.3, ribs=4, thick=1.1, face=1,
             tail=None, spine=True, far_dark=True, leg_len=(3.2, 3.0), fleg_len=(3.2, 3.2), paw="bone", rib_mat="bone"):
    """A lean four-legged body: deep chest at sh, haunch at hip, a tucked waist; ribs as light stripes on the chest.
    legs: (near hind, near fore, far hind, far fore) foot points."""
    hx, hy = hip; sx, sy = sh
    for k in (2, 3, 0, 1):
        fore = k in (1, 3); near = k < 2
        ax, ay = (sx - 0.4 * face, sy + 0.8) if fore else (hx + 0.2 * face, hy + 0.4)
        if not near: ax -= 0.8 * face
        fx_, fy_ = legs[k]
        L = fleg_len if fore else leg_len
        kx, ky = ik(ax, ay, fx_, fy_ - 0.5, L[0], L[1], bend=(1 if fore else -1) * face)
        zz = z + (1.0 if near else -1.0)
        m = mat
        r.tube([(ax, ay), (kx, ky)], [thick + 0.5, thick * 0.6], m, zz, bias=0.0 if near else -0.45)
        r.line(kx, ky, fx_, fy_ - 0.5, m, zz + 0.01, tone=3 if near else 1)
        r.line(fx_, fy_, fx_ + 1.2 * face, fy_, paw if near else "dbone", zz + 0.02, tone=2 if near else 1)
    if tail:
        r.tube(chain(hx - 1.2 * face, hy - 0.8, tail), [0.7, 0.6, 0.5, 0.4, 0.3], mat, z - 0.3, bias=-0.1)
    # chest (deep), waist (thin), haunch
    r.ell(sx, sy + chest * 0.25, chest * 0.9, chest, mat, z, bias=0.05)
    wx, wy = lerp(hx, sx, 0.45), lerp(hy, sy, 0.45) - 0.2
    r.tube([(hx, hy), (wx, wy), (sx, sy)], [haunch, waist, chest * 0.8], mat, z - 0.01)
    r.ell(hx, hy + 0.2, haunch, haunch, mat, z + 0.02, bias=0.0)
    if spine:
        sp = [(hx - 1.0 * face, hy - haunch + 0.4), (wx, wy - waist - 0.2), (sx + 0.5 * face, sy - chest + 0.6)]
        vertebrae(r, sp, z + 0.1, "bone", tone_a=3, tone_b=1)
    for i in range(ribs):
        x0 = sx - (0.5 + 1.3 * i) * face
        y0 = sy - chest + 1.6 + i * 0.2
        r.polyline([(x0, y0), (x0 + 0.6 * face, y0 + chest * 0.7), (x0 + 1.2 * face, y0 + chest * 1.25)], rib_mat, z + 0.2,
                   tones=[3 if i % 2 == 0 else 2, 2, 1])


def hound(lean=0.0, bob=0.0, legs=None, head_at=None, face="shut", tail=0.0, extra=None, smear_pts=None, dust_at=None,
          crouch=0.0, mat="hide", stretch=0.0):
    r = Rig()
    legs = legs or ((-3.5, 0.0), (4.0, 0.0), (-2.5, 0.0), (5.0, 0.0))
    T = Xf(lean, (0.0, -6.0))
    hip = T(-3.2 - stretch * 0.5, -6.5 + bob + crouch)
    sh = T(3.0 + stretch * 0.5, -7.0 + bob + crouch * 0.6)
    dog_body(r, hip, sh, legs, mat=mat, chest=2.6, haunch=1.8, waist=1.1, ribs=3, leg_len=(3.3, 3.0), fleg_len=(3.0, 3.6),
             tail=[(1.6, 195 + tail), (1.4, 215 + tail), (1.2, 240 + tail)])
    hx, hy = head_at or (sh[0] + 1.6, sh[1] - 2.0)
    r.tube([(sh[0] + 0.5, sh[1] - 1.0), (hx - 0.5, hy - 0.5)], [1.6, 1.2], mat, 0.6, bias=0.1)
    hound_head(r, hx, hy, 2.0, face, mat=mat)
    if smear_pts: smear(r, smear_pts, "bone", 4)
    if dust_at: dust(r, *dust_at)
    if extra: extra(r)
    return r.resolve()


def gait(i, n, stride=2.6, lift=1.6, base=((-4.0, 0.0), (4.5, 0.0), (-3.0, 0.0), (5.5, 0.0)), gallop=False):
    """Four feet through one run loop of n frames (trot: diagonal pairs; gallop: hinds then fores)."""
    out = []
    for k, (bx, by) in enumerate(base):
        if gallop:
            ph = i / n * math.tau + (0.0 if k in (0, 2) else math.pi * 0.9) + (0.35 if k >= 2 else 0.0)
        else:
            ph = i / n * math.tau + (0.0 if k in (0, 3) else math.pi)
        out.append((bx + stride * math.cos(ph), by - max(0.0, lift * math.sin(ph))))
    return out


def hound_sheet(outdir):
    H = hound
    idle = [H(bob=[0, 0.3, 0.6, 0.3][i], face=["shut", "shut", "open", "shut"][i], tail=[0, 10, 18, 8][i]) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        run.append(H(lean=-5 * math.sin(ph), bob=-0.8 * abs(math.sin(ph)), legs=gait(i, 6, 3.0, 1.8, gallop=True),
                     face="open", tail=22 + 12 * math.sin(ph), stretch=1.2 * math.cos(ph)))
    # Bite (6): two snaps; jaws at (12, -6) on 2 and 4
    lunge = ((-3.5, 0.0), (6.5, 0.0), (-2.5, 0.0), (7.5, 0.0))
    bite = [H(crouch=0.8, lean=6, face="open"),
            H(crouch=0.4, lean=-8, face="wide", head_at=(5.5, -10.0)),
            H(lean=8, face="shut", head_at=(8.5, -7.5), legs=lunge, stretch=2.0, smear_pts=[(8, -12), (11, -11), (14, -8)]),
            H(lean=-6, face="wide", head_at=(6.0, -10.0)),
            H(lean=10, face="shut", head_at=(9.0, -7.0), legs=lunge, stretch=2.4, smear_pts=[(9, -12), (12, -10), (15, -7)]),
            H(face="shut")]
    # Howl (6): head drops (0), throws the head back (1-2), HOWL: the bleed ring (3), hold (4), shake off (5)
    howl = [H(crouch=1.0, face="shut", head_at=(6.5, -6.0)),
            H(lean=-14, face="open", head_at=(5.0, -11.5), tail=-10),
            H(lean=-22, face="wide", head_at=(4.0, -13.0), tail=-20),
            H(lean=-22, face="wide", head_at=(4.0, -13.5), tail=-24,
              extra=lambda r: r.dots(arc_pts(6.0, -19.0, 3, 2.5, -100, 10, 5), "mglow", 3, 8)),
            H(lean=-20, face="wide", head_at=(4.0, -13.0), tail=-20,
              extra=lambda r: r.dots(arc_pts(6.0, -19.0, 5, 4, -110, 20, 7), "mglow", 2, 8)),
            H(face="shut", tail=6)]
    d0 = H(lean=-14, face="wide", head_at=(5.0, -11.0))
    d1 = H(lean=-30, bob=2.0, face="open", head_at=(3.5, -6.0), legs=((-6.0, 0.0), (4.0, 0.0), (-5.0, 0.0), (6.0, -1.0)))
    d2 = hound_corpse(0)
    corpse = hound_corpse(1)
    knock = H(lean=-14, face="wide", head_at=(4.5, -10.0), legs=((-5.5, 0.0), (3.5, 0.0), (-4.5, 0.0), (4.5, 0.0)))
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.065] * 6),
             ("Bite", bite, [0.1, 0.06, 0.05, 0.06, 0.05, 0.12]),
             ("Howl", howl, [0.12, 0.1, 0.08, 0.08, 0.2, 0.14])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("OssMarrowHound", anims, outdir)


def hound_corpse(stage, mat="hide"):
    r = Rig()
    r.ell(-0.5, -2.2, 5.5, 2.0, mat, 0.0)
    for i in range(4):
        x0 = 2.0 - 1.6 * i
        r.polyline([(x0, -4.0), (x0 + 0.5, -2.6), (x0 + 1.0, -1.4)], "bone", 0.3, tones=[3, 2, 1])
    for (ax, ay, a) in ((-4.5, -3.0, -130), (-3.5, -3.2, -110), (3.0, -3.4, -70), (4.0, -3.2, -50)):
        pts = chain(ax, ay, [(2.5, a), (2.0, a + (10 if stage else 30))])
        r.tube(pts[:2], [1.0, 0.7], mat, 0.5)
        r.line(pts[1][0], pts[1][1], pts[2][0], pts[2][1], mat, 0.6, tone=3)
    hound_head(r, 5.5, -0.5, 1.0, "open", mat=mat)
    if not stage: dust(r, 0, 0, 1, 1.4)
    return r.resolve()


SYNC["OssMarrowHound"] = {"Bite": [("SNAP 1: jaws at (14, -6); box 10 x 10 at (12, -6)", 2), ("SNAP 2", 4)],
                          "Howl": [("HOWL: the bleed ring round the feet", 3), ("sprint from the end", 5)]}


# ================================================================== CAIRN CROW (T1): a crow in a bone-beak mask
CROW_HEAD = {
    # pivot (1, 3): the nape. Black head, the bone beak-mask over the face, a marrow-red eye in the mask's socket.
    "shut": """
.fF....
fFFLHL.
fFkeLHHL
.fSBBBLS
""",
    "open": """
.fF.....
fFFLHL..
fFkeLHHL
.fSBS...
...SBBS.
""",
}
CROW_LEG = dict(BONE_LEG, f=("feath", 2), F=("feath", 3))


def wing(r, base, ang, ln, z, near=True, n=4, chord=3.0, face=1, mat="feath", bone_edge=None):
    """A bird wing from the shoulder `base`. ang: 0 = swept straight back, 90 = straight up, -40 = down-stroke.
    A lit leading edge to the wrist, primaries fanning to the tip, a serrated trailing edge back to the body."""
    bx, by = base
    th = math.radians(180 - ang) if face > 0 else math.radians(ang)
    d = (math.cos(th), -math.sin(th))
    pv = (-d[1] * face, d[0] * face) if False else (d[1] * (1 if face > 0 else -1), -d[0] * (1 if face > 0 else -1))
    # make the trailing side point toward the tail (backwards = -face on x) where possible
    if pv[0] * face > 0: pv = (-pv[0], -pv[1])
    wx, wy = bx + d[0] * ln * 0.45, by + d[1] * ln * 0.45
    bias = 0.1 if near else -0.45
    # three feather groups, each its own part so a contour line separates them: coverts on the arm, secondaries along
    # the trailing edge, primaries fanning from the wrist (tapered quills, the lead one longest)
    tips = []
    for i in range(n):
        fa = th + math.radians(14 * i) * (-1 if face > 0 else 1) * (1 if d[1] < 0 else -1)
        L = ln * (0.62 - 0.07 * i)
        base = (wx + pv[0] * i * 0.7, wy + pv[1] * i * 0.7)
        tip = (base[0] + L * math.cos(fa), base[1] - L * math.sin(fa))
        tips.append(tip)
        r.tube([base, tip], [chord * 0.28, 0.4], mat, z - 0.03 * i, bias=bias - 0.05 * i)
    for j in range(3):
        t = 0.25 + 0.3 * j
        sx_, sy_ = lerp(bx, wx, t) + pv[0] * chord * 0.35, lerp(by, wy, t) + pv[1] * chord * 0.35
        r.tube([(sx_, sy_), (sx_ + pv[0] * chord * 0.85 - d[0] * 0.8, sy_ + pv[1] * chord * 0.85 - d[1] * 0.8)], [chord * 0.3, 0.5],
               mat, z - 0.2 - 0.01 * j, bias=bias - 0.1)
    r.poly([(bx, by), (wx, wy), (wx + pv[0] * chord * 0.55, wy + pv[1] * chord * 0.55), (bx + pv[0] * chord * 0.6, by + pv[1] * chord * 0.6)],
           mat, z + 0.05, bias=bias + 0.15, normal=(-0.3, -0.6, 0.8))
    r.line(bx, by, wx, wy, bone_edge or mat, z + 0.06, tone=4 if near else 2)
    return tips[0]


def crow(r, x, y, z=0.0, wing_a=20.0, wing_b=None, lean=0.0, face="shut", tail=0.0, s=1.0, feet=True, stones=True,
         legs_down=0.0, folded=False, flip=False, eye=True):
    """A crow: (x, y) = the body centre. wing_a: near wing angle (0 folded back .. 110 raised)."""
    f = -1 if flip else 1
    T = Xf(lean * f, (x, y))
    F = lambda dx, dy: T(x + dx * s * f, y + dy * s)
    wb = wing_a if wing_b is None else wing_b
    if not folded:
        wing(r, F(0.5, -1.2), wb + 8, 7.0 * s, z - 1.0, near=False, face=f)
    # tail + tied cairn stones
    tx, ty = F(-2.6, 0.6)
    r.poly([F(-1.4, -0.6), (tx - 2.8 * s * f, ty + 0.6 + tail), (tx - 2.4 * s * f, ty + 1.8 + tail), F(-1.0, 1.2)], "feath",
           z - 0.3, normal=(-0.3, -0.5, 0.8))
    if stones:
        sx, sy = tx - 2.4 * s * f, ty + 2.8 + tail
        r.line(tx - 1.8 * s * f, ty + 1.6 + tail, sx, sy, "rope", z - 0.2, tone=3)
        r.ell(sx, sy + 0.8, 0.9, 0.9, "slate", z - 0.2, bias=0.2)
    bx, by = F(0.0, 0.0)
    r.ell(bx, by, 3.8 * s, 2.9 * s, "feath", z, ang=-14 * f, bias=0.1)
    if feet:
        for k, dx in enumerate((0.8, -0.4)):
            lx, ly = F(dx, 1.8)
            fy = ly + 1.6 + legs_down
            r.line(lx, ly, lx, fy, "iron", z + (0.4 if k == 0 else -0.4), tone=3 if k == 0 else 2)
            r.line(lx - 0.5 * f, fy, lx + 1.2 * f, fy, "iron", z + (0.41 if k == 0 else -0.39), tone=3 if k == 0 else 2)
    leg = dict(CROW_LEG)
    if not eye: leg["e"] = ("iron", 0)
    hx, hy = F(2.0, -1.4)
    r.stamp(CROW_HEAD[face], hx, hy, z + 0.3, leg, pivot=(1, 3), flip=flip)
    if folded or wing_a < 25:
        r.ell(*F(-0.4, -0.3), 2.6 * s, 1.4 * s, "feath", z + 0.6, ang=-16 * f, bias=0.3)
        r.line(*F(-2.6, 0.4), *F(1.4, -1.0), "feath", z + 0.61, tone=4)
    else:
        wing(r, F(0.6, -1.0), wing_a, 7.5 * s, z + 0.6, near=True, face=f)


def crow_frame(x=0.0, alt=4.0, **kw):
    r = Rig()
    extra = kw.pop("extra", None)
    sm = kw.pop("smear_pts", None)
    shadow = kw.pop("shadow", True)
    crow(r, x, -alt - 4.0, **kw)
    if shadow and alt > 1.0:
        r.ell(x, -0.3, 2.6, 0.7, "tar", -5.0, flat=2)
    if sm: smear(r, sm, "bone", 4)
    if extra: extra(r)
    return r.resolve()


def crow_sheet(outdir):
    C = crow_frame
    idle = [C(alt=[1.0, 1.4, 1.8, 1.4][i], wing_a=[60, 90, 40, 10][i], wing_b=[70, 105, 50, 20][i], tail=[0, 0.4, 0.8, 0.4][i])
            for i in range(4)]
    run = [C(alt=3.4 + [0, 0.8, 1.2, 0.8, 0.2, -0.2][i], lean=14, wing_a=[110, 70, 30, 10, 40, 85][i], wing_b=[110, 80, 40, 20, 50, 90][i])
           for i in range(6)]
    # Peck (6): rear back (0-1), DIVE (2: beak at (11, -6)), beak buried (3), pull out (4), back up (5)
    peck = [C(alt=4.0, lean=-14, wing_a=80, face="open"),
            C(alt=5.0, lean=-26, wing_a=110, wing_b=110, face="open"),
            C(x=2.0, alt=2.2, lean=36, wing_a=20, wing_b=30, smear_pts=[(-2, -13), (3, -11), (8, -8), (11, -6)]),
            C(x=2.5, alt=1.6, lean=42, wing_a=10, wing_b=20, extra=lambda r: bone_bits(r, 11, -3, 0, 4, seed=8, z=6)),
            C(x=1.5, alt=3.0, lean=-10, wing_a=90, face="open", extra=lambda r: bone_bits(r, 11, -3, 1, 3, seed=8, z=6)),
            C(alt=3.6, wing_a=40)]
    # Caw (6): fluff up (0), beak to the sky (1-2), CAW (3), hold (4), settle (5)
    caw = [C(alt=3.0, wing_a=15, tail=0.8),
           C(alt=3.4, lean=-18, wing_a=60, face="open"),
           C(alt=4.0, lean=-30, wing_a=105, wing_b=105, face="open"),
           C(alt=4.4, lean=-32, wing_a=110, wing_b=110, face="open",
             extra=lambda r: r.dots(arc_pts(8.0, -16.0, 3, 3, -130, 30, 6), "spirit", 3, 8)),
           C(alt=4.0, lean=-26, wing_a=95, face="open", extra=lambda r: r.dots(arc_pts(8.0, -16.0, 5, 5, -130, 30, 8), "spirit", 2, 8)),
           C(alt=3.4, wing_a=30)]
    d0 = C(alt=4.0, lean=-30, wing_a=115, wing_b=70, face="open")
    d1 = C(alt=1.6, lean=-80, wing_a=130, wing_b=100, face="open", extra=lambda r: bone_bits(r, 0, -4, 1, 4, seed=5, z=6, mat="feath"))
    d2 = crow_corpse(0)
    corpse = crow_corpse(1)
    knock = C(alt=4.0, lean=-34, wing_a=120, wing_b=110, face="open")
    anims = [("Idle", idle, [0.12, 0.1, 0.12, 0.1]), ("Run", run, [0.065] * 6),
             ("Peck", peck, [0.1, 0.1, 0.05, 0.08, 0.1, 0.12]),
             ("Caw", caw, [0.1, 0.1, 0.1, 0.18, 0.14, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("OssCairnCrow", anims, outdir)


def crow_corpse(stage):
    r = Rig()
    crow(r, 0.0, -2.0, 0.0, wing_a=60 if stage else 90, wing_b=30, lean=-90 if stage else -70, face="open", feet=False, eye=False)
    if not stage: bone_bits(r, 0, -2, 2, 4, seed=9, z=6, mat="feath")
    return r.resolve()


SYNC["OssCairnCrow"] = {"Peck": [("DIVE: beak at (11, -6); box 10 x 10 at (9, -6)", 2)],
                        "Caw": [("CAW: bone piles within 60 px hop toward kin", 3)]}




# ================================================================== timing + build
def write_timing(outdir):
    L = ["# Ossivar: sprite timing", "",
         "Generated by `tools/sprites/ossivar_v2_rigs.py` (and the ossivar_v2_*.py modules it loads). Frame indices are",
         "0-based within the anim. Monster sheets: feet = (cellW / 2, cellH - 2), facing right. Points are pixels from the",
         "feet, x right, y up NEGATIVE (Kit.AddEffect offsetX = x, offsetY = -y). Every sheet is at final size (no ArtScale).", "",
         "| Sheet | Cell (w x h) | Feet / origin | Idle bounds (w x h) | Anims (frames) |", "|---|---|---|---|---|"]
    for n, b in sorted(BUILT.items()):
        img = Image.open(os.path.join(outdir, n + ".png")).convert("RGBA")
        cw, ch = b["cell"]
        bb = img.crop((0, 0, cw, ch)).getbbox() or (0, 0, 0, 0)
        L.append("| %s | %d x %d | (%d, %d) | %d x %d | %s |" % (n, cw, ch, b["feet"][0], b["feet"][1], bb[2] - bb[0], bb[3] - bb[1],
                                                               ", ".join("%s %d" % (a, k) for a, k, d in b["anims"])))
    L += ["", "## Sync frames", "", "| Sheet | Anim | Frames | Event | Frame | Time (s) | Length (s) |", "|---|---|---|---|---|---|---|"]
    for n in sorted(SYNC):
        if n not in BUILT: continue
        dd = {a: d for a, k, d in BUILT[n]["anims"]}
        for a, evs in SYNC[n].items():
            d = dd[a]
            for ev, fi in evs:
                L.append("| %s | %s | %d | %s | %d | %.2f | %.2f |" % (n, a, len(d), ev, fi, sum(d[:fi]), sum(d)))
    L += ["", "## Durations", ""]
    for n, b in sorted(BUILT.items()):
        for a, k, d in b["anims"]:
            L.append("- %s %s: %s" % (n, a, ", ".join("%.3g" % x for x in d)))
    L += ["", "## Scale", "", "Sheets posed in their own units and stretched to final size (SCALE in ossivar_v2_rigs.py). The sync",
          "points above are in posing units: multiply x by sx and y by sy for game pixels (the kits already do).", ""]
    L += ["- %s: sx %.2f, sy %.2f" % (n, a, b) for n, (a, b) in sorted(SCALE.items())]
    L += ["", "## Notes", ""] + ["- **%s**: %s" % kv for kv in sorted(NOTES.items())]
    open(os.path.join(outdir, "TIMING.md"), "w").write("\n".join(L) + "\n")


JOBS = [("OssRattlebones", rattle_sheet), ("OssMarrowHound", hound_sheet), ("OssCairnCrow", crow_sheet)]


def all_jobs():
    import importlib
    jobs = list(JOBS)
    for mod in ("ossivar_v2_t2", "ossivar_v2_t3a", "ossivar_v2_t3b", "ossivar_v2_fx"):
        try:
            m = importlib.import_module(mod)
        except ImportError as e:
            if mod not in str(e): raise
            continue
        jobs += m.JOBS
    return jobs


def main():
    argv = sys.argv[1:]
    only = None
    if "--only" in argv:
        i = argv.index("--only")
        only = set(argv[i + 1].split(","))
        argv = argv[:i] + argv[i + 2:]
    outdir = argv[0] if argv else DEFAULT_OUT
    os.makedirs(outdir, exist_ok=True)
    global SX, SY
    for name, fn in all_jobs():
        if only and name not in only: continue
        SX, SY = SCALE.get(name, (1.0, 1.0))
        fn(outdir)
        SX = SY = 1.0
    if not only:
        write_timing(outdir)


if __name__ == "__main__":
    sys.modules["ossivar_v2_rigs"] = sys.modules[__name__]
    main()
