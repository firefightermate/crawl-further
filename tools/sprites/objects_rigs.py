#!/usr/bin/env python3
"""Crawl: Further room objects, part one: the traps, the touch objects, the use objects and their effects.

    python3 tools/sprites/objects_rigs.py [outdir] [--only Name,Name]      (default art/out_objects)

Drawn with the material renderer of jinx_v2_rigs.py (Rig): every shape is lit from the top left and quantised to
three tones per material (plus a highlight tone on shiny ones), the bottom edge takes the material's darkest tone so
the object sits on the floor, there is no black ring, and stray pixels are folded. This file also holds the object
kit (Fr frames, prop primitives, the greyed "Off" version, the floor shadow) that objects2_rigs.py builds on.

Vanilla reference (AtlasPropsCrypt): props are 15-30 px wide, olive stone, warm wood and dull brass, 3-5 tones per
material, light from the top left, moss and grime on upward faces, no outline.

Every object sheet puts the floor point at (cellW/2, cellH-2) (ObjectKit anchors it BotCenter with
MonsterFactory.FeetOffset). Effect sheets keep the cell and origin the C# names in Strike.ArtAt / Strike.Ground
(ObjectPack.cs), listed in FX_CELLS below.

Sheets (anims; frames)
  ObjChainHook    trap  Inactive 6, Activate 3, Active 4, Action 6, Deactivate 3, Disabled 1, Vault 1
  ObjSteamVent    trap  same set (Action 6)
  ObjTarSpout     trap  same set (Action 6)
  ObjPendulum     trap  same set, attacks SwingL 7 / SwingR 7 (no Action)
  ObjRunePlate    trap  same set (Action 6)
  ObjTollBell     trap  same set (Action 7)
  ObjScatterIdol  trap  same set (Action 5)
  ObjIronSnare    touch Idle 4, Snap 4, Sprung 1, Reset 4, Off 1, Vault 1
  ObjWarpStone    touch Idle 6, Use 6, Off 1, Vault 1
  ObjMendSpring   use   Idle 6, Use 4, Spent 1, Off 1
  ObjWeaponRack   use   Idle 4, Use 5, Spent 1, Off 1
  ObjCursedAltar  use   Idle 6, Use 6, Spent 1, Off 1
  ObjWardShrine   use   Idle 6, Use 5, Spent 1, Off 1
  ObjSpiritUrn    use   Idle 6, Use 5, Spent 1, Off 1
  ObjStrongbox    use   Idle 4, Use 4, Bite 6, Spent 1, Off 1, Vault 1
  Effects (FxObj*): Hook (Fly 2, Yank 4), Steam (Blast 7), Tar (Fly 2, Pool 8, Fade 3), Rune (Charge 5, Burst 6),
  Toll (Wave 6), Dart (Fly 2), Warp (Flash 6), Urn (Burst 6), Mimic (Coins 6), indicators FxObjIndCurse (Loop 6,
  head) and FxObjIndWard (Loop 6, feet). The pendulum's blade and blur are in its own swing frames.
TIMING.md in the out dir lists durations, release frames and spawn points.
"""
import math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)
from anim import Spr, pack, preview  # noqa: E402
from jinx_v2_rigs import Rig, RAMPS, EMISSIVE, SHINY, lam, poly_px, line_px, Xf  # noqa: E402
from PIL import Image  # noqa: E402

DEFAULT_OUT = os.path.join(ROOT, "art", "out_objects")


# ================================================================== materials
def _h(s):
    s = s.lstrip("#"); return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


OBJ_RAMPS = {
    # ink, shadow, base, light, highlight
    "ostone": ["26241f", "45433a", "656150", "878067", "aaa184"],    # olive statue stone (vanilla crypt props)
    "pstone": ["302e27", "5c5747", "807861", "a2987a", "c6bc98"],    # pale fountain stone
    "dstone": ["120f16", "241f2a", "37303f", "4e4558", "6a6078"],    # black altar stone
    "brick":  ["2a1c18", "4e342a", "6e4a38", "8e6448", "ac825e"],    # fired brick
    "moss":   ["1a2212", "323f20", "4c5a2e", "6a7a3e", "8c9a52"],
    "owood":  ["1e130c", "3d2617", "5e3c24", "7e5432", "a07046"],    # old timber
    "plank":  ["24180f", "4a321e", "6c4a2c", "8e663c", "b08654"],    # newer boards, crates
    "iron":   ["141418", "2a2a32", "45454f", "666672", "9494a0"],
    "rust":   ["1c120e", "3e2418", "5e3820", "7e5430", "9c7448"],
    "brass":  ["2a1a0a", "5e421a", "8c682c", "b88e40", "e8c672"],
    "bronze": ["221608", "4c3216", "70502a", "8e6c3c", "ae905c"],
    "tar":    ["080606", "151011", "241b1d", "382c2e", "54474a"],
    "bone":   ["342a20", "675a46", "958870", "beb08e", "e4d8b6"],
    "clay":   ["2a1912", "553826", "7a5234", "9e6e46", "c29062"],
    "velvet": ["200810", "4a1220", "721e2c", "982e36", "bc4c48"],
    "wax":    ["4a3e30", "8a7a62", "c4b494", "e4d8bc", "faf2e0"],
    "water":  ["0c1a26", "16324a", "245270", "3a7a9a", "78b8cc"],
    "rope":   ["261a10", "523c22", "7e6038", "a6844e", "ccac74"],
    "glassd": ["0e0c14", "1a1824", "2a2838", "3e3c50", "5c5a72"],    # dark glass with the inside behind it
    # emissive (never shaded, no sel-out)
    "ecto":   ["1c4a36", "2a7a54", "44b47c", "86eab0", "dcffe8"],    # spirit green
    "cyan":   ["163e52", "246c88", "40a8c6", "8ae2f0", "e4fcff"],    # ward / water glow
    "rune":   ["4a160a", "8e3010", "d0601c", "f6a03a", "ffe08a"],    # ember-orange runes
    "blood":  ["3e0a0e", "741418", "ac2424", "e04a3a", "ff9a7a"],
    "steam":  ["5a5a60", "86868c", "aeaeb2", "d2d2ce", "f4f4f0"],
    "gleam":  ["8a7a50", "c8b070", "f0dc9a", "fff4cc", "ffffff"],    # specular glints on metal
}
RAMPS.update({k: [_h(c) for c in v] for k, v in OBJ_RAMPS.items()})
EMISSIVE.update({"ecto", "cyan", "rune", "blood", "steam", "gleam"})
SHINY.update({"iron", "brass", "bronze", "glassd", "wax", "water"})
SHADOW = (0x1a, 0x12, 0x10)


def ramp(mat, t):
    return RAMPS[mat][max(0, min(4, t))]


def grey(c, amt=0.75, k=0.7):
    l = 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
    return tuple(max(0, min(255, int(round((v + (l - v) * amt) * k)))) for v in c[:3])


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


# ================================================================== frames
class Px(Spr):
    """A finished frame: (x, y) -> (r, g, b, a), origin on the floor point. tones: (x, y) -> (material, tone)."""

    def __init__(self, px=None, tones=None):
        Spr.__init__(self, px)
        self.tones = dict(tones or {})

    def to_rgba(self):
        return dict(self.px)

    def off(self):
        """The greyed version a fight-locked room shows: desaturated and darker, every glow put out."""
        out = {}
        for k, c in self.px.items():
            m = self.tones.get(k, (None, 0))[0]
            if c[3] < 200:
                out[k] = c
            elif m in EMISSIVE or m is None:
                out[k] = grey(c, 1.0, 0.42) + (c[3],)
            else:
                out[k] = grey(c) + (c[3],)
        return Px(out, self.tones)

    def shift(self, dx, dy, pred=None):
        return Px({(x + dx, y + dy): c for (x, y), c in self.px.items()},
                  {(x + dx, y + dy): t for (x, y), t in self.tones.items()})


class Fr:
    """One object frame: a material Rig (r), free glow pixels drawn over it (glow), and a soft floor shadow."""

    def __init__(self, shadow=None):
        self.r = Rig()
        self.glows = {}         # (x, y) -> (mat, tone, alpha)
        self.under = {}         # pixels drawn under everything (floor stains, puddles): (x, y) -> (mat, tone, alpha)
        self.sh = shadow        # (cx, rx, ry)

    def glow(self, x, y, mat, tone, a=255):
        self.glows[(int(math.floor(x + 0.5)), int(math.floor(y + 0.5)))] = (mat, tone, a)

    def floor(self, x, y, mat, tone, a=255):
        self.under[(int(math.floor(x + 0.5)), int(math.floor(y + 0.5)))] = (mat, tone, a)

    def spark(self, x, y, mat="gleam", size=1, tone=4):
        """A plus-shaped twinkle."""
        self.glow(x, y, mat, tone)
        for k in range(1, size + 1):
            for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
                self.glow(x + dx, y + dy, mat, max(1, tone - k))

    def done(self, floor=True, specks=None, seed=0):
        s = self.r.resolve(floor=floor)
        tones = dict(s.tones)
        if specks:
            speck(tones, specks, seed)
        px = {}
        if self.sh:
            cx, rx, ry = self.sh
            for y in range(-int(ry) - 1, 2):
                for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                    u, v = (x - cx) / rx, (y - 0.3) / ry
                    d = u * u + v * v
                    if d <= 1.0 and y <= 1:
                        px[(x, y)] = SHADOW + (92 if d < 0.5 else 52,)
        for k, (m, t, a) in self.under.items():
            px[k] = ramp(m, t) + (a,); tones[k] = tones.get(k, (m, t))
        for k, (m, t) in s.tones.items():
            if k in tones: m, t = tones[k]
            px[k] = ramp(m, t) + (255,)
        for k, (m, t, a) in self.glows.items():
            if a < 255 and k in px:
                px[k] = mix(px[k], ramp(m, t), a / 255.0) + (255,)
            else:
                px[k] = ramp(m, t) + (a,)
            tones[k] = (m, t)
        if floor:
            px = {k: v for k, v in px.items() if k[1] <= 1}
        return Px(px, tones)


def speck(tones, mats, seed):
    """Stone pits and wood grain: single tone-down pixels inside flat areas (never on an edge or next to another)."""
    rnd = random.Random(seed * 7 + 3)
    picked = set()
    for k in sorted(tones):
        m, t = tones[k]
        if m not in mats or t < 2: continue
        x, y = k
        nb = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        if not all(n in tones and tones[n] == (m, t) for n in nb): continue
        if any(n in picked for n in nb + [(x + 1, y + 1), (x - 1, y - 1), (x + 1, y - 1), (x - 1, y + 1)]): continue
        if rnd.random() < mats[m]:
            picked.add(k)
    for k in picked:
        m, t = tones[k]
        tones[k] = (m, t - 1)


STONE_SPECK = {"ostone": 0.07, "pstone": 0.06, "dstone": 0.05, "owood": 0.05, "plank": 0.04, "rust": 0.06}


# ================================================================== prop primitives (all take a Rig, y up is negative)
def block(r, x0, x1, ytop, ybot, mat, z, top=2, topmat=None, curve=0.0, bias=0.0, lip=True):
    """A block seen from the front and above: a lit top face `top` rows deep, then the front face down to ybot."""
    p = r.part(False, z)
    for y in range(int(ytop), int(ybot) + 1):
        for x in range(int(x0), int(x1) + 1):
            u = 0.0 if x1 == x0 else (x - x0) / float(x1 - x0) * 2 - 1
            if y < ytop + top:
                n = (-0.15 + u * 0.15, -1.0, 0.55)
                m = topmat or mat
            else:
                n = (-0.12 + u * curve, -0.05, 1.0)
                m = mat
            l = math.sqrt(sum(v * v for v in n))
            r.put(x, y, z, m, lam(n[0] / l, n[1] / l, n[2] / l) + bias, p)
    if lip and top > 0:
        # the front edge of the top face catches the most light
        for x in range(int(x0), int(x1)):
            r.put(x, ytop + top - 1, z + 0.001, topmat or mat, 0.0, p, 3)
    return p


def drum(r, cx, ytop, ybot, rx, mat, z, ry=None, capmat=None, bias=0.0, cap=True):
    """Upright cylinder: lit like a column, with an elliptic top cap of radius ry."""
    ry = ry if ry is not None else max(1.0, rx * 0.35)
    p = r.part(False, z)
    for y in range(int(ytop), int(ybot) + 1):
        for x in range(int(math.floor(cx - rx)), int(math.ceil(cx + rx)) + 1):
            u = (x - cx) / max(rx, 0.5)
            if abs(u) > 1.0: continue
            # the bottom edge follows the ellipse so the drum sits round on the floor
            if y > ybot - ry * (1 - math.sqrt(max(0, 1 - u * u))) + 0.5 and y > ytop: continue
            nz = math.sqrt(max(0.0, 1 - u * u))
            r.put(x, y, z, mat, lam(u, -0.05, nz) + bias, p)
    if cap:
        r.ell(cx, ytop, rx, ry, capmat or mat, z + 0.01, bias=0.25 + bias)
    return p


def bevel_ell(r, cx, cy, rx, ry, mat, z, bias=0.0):
    """A dome / ball lit as a sphere."""
    return r.ell(cx, cy, rx, ry, mat, z, bias=bias)


def rows(r, cx, ytop, profile, mat, z, bias=0.0, lean=0.0):
    """A turned shape (urn, bell, bottle) from half-widths per row, lit like a vessel of revolution."""
    p = r.part(False, z)
    n = len(profile)
    for j, w in enumerate(profile):
        y = ytop + j
        dw = (profile[min(n - 1, j + 1)] - profile[max(0, j - 1)]) / 2.0     # slope: the surface tilts up or down
        for x in range(int(math.floor(cx - w - 0.5)), int(math.ceil(cx + w + 0.5)) + 1):
            u = (x - cx - lean * j) / max(w, 0.5)
            if abs(u) > 1.0 + 0.5 / max(w, 1): continue
            u = max(-1.0, min(1.0, u))
            nz = math.sqrt(max(0.0, 1 - u * u))
            ny = -max(-0.8, min(0.8, dw * 0.9)) * nz
            r.put(x, y, z, mat, lam(u, ny, nz) + bias, p)
    return p


def chainline(r, x0, y0, x1, y1, z, mat="iron"):
    """Chain links along a line: alternating lit and dark links."""
    p = r.part(True, z)
    for i, (x, y) in enumerate(line_px(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1)))):
        r.put(x, y, z, mat, 0.5, p, 3 if i % 2 == 0 else 1)
    return p


def moss(r, pts, z=0.5):
    """Moss tufts over the top faces (fixed tones so they read as clumps)."""
    p = r.part(True, z)
    for i, (x, y) in enumerate(pts):
        r.put(x, y, z, "moss", 0.5, p, 3 if i % 3 == 0 else 2)
    return p


# ================================================================== sheet assembly
SHEETS = []
FEET = {}
OUT = DEFAULT_OUT


def emit(name, anims, cell=None, feet=None):
    """Object sheets: the cell grows to fit (floor point at cellW/2, cellH-2). Effect sheets: a fixed cell and origin."""
    for an, fr, du in anims:
        assert du and len(du) == len(fr), (name, an)
    if feet is None:
        xs, ys = [], []
        for _, frames, _ in anims:
            for f in frames:
                for (x, y) in f.to_rgba():
                    xs.append(x); ys.append(y)
        hw = max(-min(xs), max(xs) + 1) + 2
        cw = max(cell[0] if cell else 0, 2 * hw)
        ch = max(cell[1] if cell else 0, -min(ys) + 1 + 2 + 2)
        feet = (cw // 2, ch - 2)
    else:
        cw, ch = cell
        for an, frames, _ in anims:
            for i, f in enumerate(frames):
                for (x, y) in f.to_rgba():
                    if not (-feet[0] <= x < cw - feet[0] and -feet[1] <= y < ch - feet[1]):
                        raise SystemExit("%s/%s[%d]: pixel (%d, %d) outside the %dx%d cell" % (name, an, i, x, y, cw, ch))
    FEET[name] = feet
    img, man = pack(name, anims, cw, ch, feet, OUT, cols=8)
    preview(img, man, os.path.join(OUT, name + "_preview.png"), scale=5)
    SHEETS.append((name, img, man))
    print("built %-16s cell %dx%d feet %s" % (name, cw, ch, feet))
    return img, man


INACT_D = [1.0, 0.1, 0.1, 0.1, 0.1, 0.1]       # vanilla trap "inactive": a long hold, then a quick blink
ACTIVATE_D = [0.1, 0.1, 0.1]
ACTIVE_D = [0.1, 0.1, 0.1, 0.1]
DEACT_D = [0.1, 0.1, 0.1]


def trap_sheet(name, draw, attacks, cell=None):
    """draw(mode, t, f) -> Px with mode in sleep / wake / alert / act. attacks: [(anim, frames, durations, mode[, draw])]."""
    anims = [("Inactive", [draw("sleep", i / 6.0, i) for i in range(6)], INACT_D),
             ("Activate", [draw("wake", (i + 1) / 3.0, i) for i in range(3)], ACTIVATE_D),
             ("Active", [draw("alert", i / 4.0, i) for i in range(4)], ACTIVE_D)]
    for at in attacks:
        an, n, durs, mode = at[:4]
        dfn = at[4] if len(at) > 4 else draw
        anims.append((an, [dfn(mode, i / float(n - 1), i) for i in range(n)], durs))
    anims.append(("Deactivate", [draw("wake", 1.0 - (i + 1) / 3.0, i) for i in range(3)], DEACT_D))
    anims.append(("Disabled", [draw("sleep", 0.0, 0).off()], [0.167]))
    anims.append(("Vault", [draw("alert", 0.0, 1)], [0.2]))
    return emit(name, anims, cell)


def lamp_on(mode, t, f):
    """How lit a trap's warning eye is: blinks once while asleep, fades in on waking, full when alert or firing."""
    return {"sleep": 0.45 if f in (2, 4) else 0.0, "wake": t, "alert": 1.0, "act": 1.0}[mode]


def hcyl(r, x0, x1, cy, ry, mat, z, bias=0.0):
    """A horizontal cylinder (a drum on its side), lit across its height."""
    p = r.part(False, z)
    for y in range(int(math.floor(cy - ry)), int(math.ceil(cy + ry)) + 1):
        v = (y - cy) / max(ry, 0.5)
        if abs(v) > 1.0: continue
        for x in range(int(x0), int(x1) + 1):
            u = (x - (x0 + x1) / 2.0) / max(1.0, (x1 - x0) / 2.0) * 0.25
            nz = math.sqrt(max(0.0, 1 - v * v - u * u))
            r.put(x, y, z, mat, lam(u - 0.1, v, nz) + bias, p)
    return p


HOOK = """
.aa.
a..b
...b
b..b
.bb.
"""


def hook_px(r, x, y, z, swing=0):
    """A forged hook hanging from (x, y): ring eye, thick shank and a barbed curl, 5 x 8."""
    p = r.part(True, z)
    pts = [(0, 0, 1), (-1, 1, 3), (1, 1, 1), (0, 2, 2),                       # ring eye
           (0, 3, 4), (1, 3, 2), (0, 4, 3), (1, 4, 1), (0, 5, 3), (1, 5, 1),      # shank
           (-1, 6, 3), (0, 6, 2), (-1, 7, 2), (0, 7, 1), (1, 8, 1), (2, 8, 1), (2, 7, 2), (3, 6, 3), (3, 5, 4), (4, 4, 4)]
    for dx, dy, t in pts:
        r.put(x + dx + (swing if dy > 3 else 0), y + dy, z, "brass" if dy > 2 else "iron", 0.5, p, t)
    return p


# ================================================================== TRAPS
def winch(mode, t, f):
    """Chain Winch: an iron drum wound with chain on a timber post, an arm with a hook hanging over the floor. 19 x 22."""
    fr = Fr((0, 9, 1.5)); r = fr.r
    # stone footing and the post
    block(r, -7, 6, -5, 0, "ostone", 0.0, top=2)
    block(r, -3, 0, -21, -5, "owood", 0.1, top=0, curve=0.7)
    r.tube([(-7, -5), (-3, -12)], [1.0, 0.8], "owood", 0.05)                    # brace
    r.tube([(5, -5), (1, -10)], [0.9, 0.7], "owood", 0.05)
    # the arm: a beam out to the right with an iron cap and a pulley
    kick = 1 if mode == "act" and 0.15 < t < 0.45 else 0
    block(r, -4, 9, -22 - kick, -20 - kick, "owood", 0.3, top=1)
    r.tube([(1, -19 - kick), (6, -21 - kick)], [0.8, 0.6], "owood", 0.25)        # strut under the arm
    r.ell(8.5, -19.5 - kick, 1.6, 1.6, "iron", 0.4)
    r.dot(8, -20 - kick, "iron", 4, 0.41)
    for x in (-3, 0):
        r.dot(x, -14, "iron", 3, 0.2); r.dot(x, -7, "iron", 2, 0.2)              # bolts
    # the drum: wound chain that slides as it turns
    spin = {"act": int(t * 9), "alert": f, "wake": int(t * 2)}.get(mode, 0)
    hcyl(r, -6, 4, -10.5, 3.2, "rust", 0.5)
    lp = r.part(True, 0.55)
    for y in range(-13, -7):
        for x in range(-5, 4):
            ph = (x + spin + (2 if y % 2 else 0)) % 4                               # links: two lit, a gap, a side link
            if ph == 3: continue
            tone = (4 if ph == 1 else 3) if y <= -11 else (3 if ph == 1 else 2) if y <= -9 else (2 if ph == 1 else 1)
            r.put(x, y, 0.55, "iron", 0.5, lp, tone)
    if mode == "act" and 0.15 < t < 0.75:
        for y in range(-12, -8):                                                  # spin blur
            r.put(-2 + (y % 3) * 2, y, 0.56, "steam", 0.5, lp, 2)
    r.ell(-6.5, -10.5, 1.0, 3.6, "iron", 0.6); r.ell(4.5, -10.5, 1.0, 3.6, "iron", 0.6)
    r.dot(-7, -12, "iron", 4, 0.61); r.dot(4, -12, "iron", 4, 0.61)
    # crank on the near flange
    ang = {"act": -2.4 + t * 9.0, "alert": f * math.pi / 2, "wake": t * 1.5}.get(mode, 0.9)
    hx, hy = 5 + 2.6 * math.cos(ang), -10.5 + 2.6 * math.sin(ang)
    r.tube([(5.5, -10.5), (hx + 1, hy)], [0.7, 0.7], "iron", 0.7)
    r.ell(hx + 1.5, hy, 1.2, 1.2, "owood", 0.75)
    r.dot(5, -10, "brass", 3, 0.71)
    # chain and hook (the hook leaves on frame 1 and swings back in on frames 4-5)
    if mode == "act":
        drop = [-4, None, None, None, 2, 1][f]
        sw = [0, 0, 0, 0, 2, -1][f]
    else:
        drop = {"sleep": 0, "wake": int(round(2 * (1 - t))), "alert": -1 + (f % 2)}[mode]
        sw = 0
    if drop is None:
        chainline(r, 9, -18 - kick, 11 + 2 * (f - 1), -13 + f, 0.45)
        if f == 1:
            fr.spark(10, -18, "gleam", 1, 4)
    else:
        bot = -12 + drop
        chainline(r, 9, -18 - kick, 9 + sw, bot, 0.45)
        hook_px(r, 9 + sw, bot + 1, 0.46, swing=sw // 2)
    # warning lamp on the post head
    on = lamp_on(mode, t, f)
    r.ell(-1.5, -23 - kick, 1.6, 1.3, "iron", 0.35)
    if on > 0:
        fr.glow(-2, -23 - kick, "rune", 2 + int(on * 2)); fr.glow(-1, -23 - kick, "rune", 1 + int(on * 2))
        if on >= 1: fr.glow(-2, -24 - kick, "rune", 4, 150)
    moss(r, [(-7, -5), (-6, -5), (-5, -5), (4, -5), (5, -5), (-7, -4)])
    return fr.done(specks=STONE_SPECK, seed=1)


def rot_rows(r, px_, py_, ang, y0, profile, mat, z, bias=0.0):
    """A turned shape hanging from a pivot (px_, py_) and swung `ang` degrees: profile half-widths per row, rows
    starting y0 below the pivot. Lit by the rotated surface normal."""
    p = r.part(False, z)
    a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)
    n = len(profile); R = y0 + n + max(profile) + 2
    for y in range(int(py_ - R), int(py_ + R) + 1):
        for x in range(int(px_ - R), int(px_ + R) + 1):
            dx, dy = x - px_, y - py_
            u, v = dx * ca + dy * sa, -dx * sa + dy * ca          # back into the shape's own frame
            j = int(math.floor(v - y0 + 0.5))
            if j < 0 or j >= n: continue
            w = profile[j]
            if abs(u) > w + 0.5: continue
            uu = max(-1.0, min(1.0, u / max(w, 0.5)))
            dw = (profile[min(n - 1, j + 1)] - profile[max(0, j - 1)]) / 2.0
            nz = math.sqrt(max(0.0, 1 - uu * uu))
            ny = -max(-0.8, min(0.8, dw * 0.9)) * nz
            nx, ny = uu * ca - ny * sa, uu * sa + ny * ca
            r.put(x, y, z, mat, lam(nx, ny, nz) + bias, p)
    return p


def vent(mode, t, f):
    """Steam Vent: an iron grate in a stone collar over a boiler, with a riser pipe, a gauge and a valve wheel. 21 x 17."""
    fr = Fr((0, 10, 1.5)); r = fr.r
    shake = 1 if mode == "act" and f == 0 else 0
    block(r, -10, 9, -6, 0, "ostone", 0.0, top=3)
    for x in (-9, -5, 4, 8):
        r.dot(x, -2, "ostone", 1, 0.01)                                           # joints in the collar
    # the grate over the top face; heat shows between the bars when awake
    heat = {"sleep": 0.0, "wake": t, "alert": 0.75 + 0.25 * (f % 2), "act": [1.0, 1.0, 0.9, 0.8, 0.6, 0.4][f]}[mode]
    lift = 1 if mode == "act" and f in (0, 1) else 0
    gp = r.part(True, 0.2)
    for y in range(-6, -3):
        for x in range(-8, 3):
            yy = y - lift
            if x % 2 == 0:
                r.put(x, yy, 0.2, "iron", 0.5, gp, 3 if y == -6 else 2)
            elif heat > 0.1:
                r.put(x, yy, 0.2, "rune", 0.5, gp, min(4, int(heat * 3) + (1 if y == -4 else 0)))
            else:
                r.put(x, yy, 0.2, "tar", 0.5, gp, 0)
    for x in range(-8, 3):
        r.put(x, -7 - lift, 0.21, "iron", 0.5, gp, 4 if x < -3 else 3)
    # riser pipe on the right with a brass flange, a gauge and a valve wheel on top
    sx = 5 + shake
    drum(r, sx + 1.5, -15, -5, 2.3, "iron", 0.3, ry=0.9)
    r.ell(sx + 1.5, -9, 2.8, 0.9, "brass", 0.35)
    r.ell(sx + 1.5, -12, 2.0, 2.0, "brass", 0.4)
    r.ell(sx + 1.5, -12, 1.2, 1.2, "bone", 0.41, flat=3)
    needle = {"sleep": -2.2, "wake": -2.2 + t * 1.6, "alert": -0.6 + 0.3 * math.sin(f * 1.6),
              "act": [0.4, 0.5, 0.2, -0.3, -0.9, -1.6][f]}[mode]
    r.dot(sx + 1.5 + math.cos(needle - math.pi / 2), -12 + math.sin(needle - math.pi / 2), "blood", 2, 0.42)
    r.dot(sx + 1.5, -12, "iron", 1, 0.42)
    wheel = {"act": f, "alert": f // 2}.get(mode, 0)
    r.ell(sx + 1.5, -16, 2.6, 0.9, "brass", 0.45)
    r.ell(sx + 1.5, -16, 1.4, 0.4, "iron", 0.46, flat=1)
    r.dot(sx + 1.5 + [-2, 0, 2, 0][wheel % 4], -16 + [0, -1, 0, 1][wheel % 4] * 0.5, "brass", 4, 0.47)
    # steam
    if mode in ("alert", "act"):
        rnd = random.Random(f * 13 + (5 if mode == "act" else 0))
        n = 2 if mode == "alert" else [3, 7, 6, 5, 3, 2][f]
        for i in range(n):
            x = rnd.randint(-8, 2); y = -8 - rnd.randint(0, 3 + (4 if mode == "act" and f in (1, 2) else 0)) - (f % 2)
            fr.glow(x, y, "steam", 3, 200); fr.glow(x, y - 1, "steam", 2, 150)
            if mode == "act" and f in (1, 2): fr.glow(x + 1, y, "steam", 4, 220)
        if mode == "act" and f == 1:
            for x in range(-7, 3):
                fr.glow(x, -8 - (x % 2), "steam", 4, 230)
    moss(r, [(-10, -6), (-9, -6), (8, -6), (9, -5)])
    return fr.done(specks=STONE_SPECK, seed=2)


def tarspout(mode, t, f):
    """Tar Spout: a riveted iron cauldron on three legs over live coals, brimming with tar, a spout aimed up-right. 19 x 19."""
    fr = Fr((0, 9, 1.5)); r = fr.r
    heat = {"sleep": 0.0, "wake": t, "alert": 0.7 + 0.3 * (f % 2), "act": 1.0}[mode]
    for lx, z in ((-6, 0.3), (5, 0.3), (-0.5, -0.2)):
        r.tube([(lx * 0.8, -6), (lx, 0)], [1.0, 0.8], "iron", z)
    if heat > 0.1:
        for x in range(-4, 4):
            fr.glow(x, -1, "rune", 1 + int(heat * 2) + (1 if (x + f) % 3 == 0 else 0))
        fr.glow(-1, -2, "rune", 3 + (f % 2)); fr.glow(1, -2, "rune", 2 + int(heat))
    else:
        for x in range(-4, 4): r.dot(x, -1, "tar", 2 if x % 2 else 1, -0.1)
    # pot body, belly band, ears
    rows(r, 0, -13, [6.5, 7.5, 8.0, 8.0, 7.8, 7.4, 6.8, 5.8, 4.4], "iron", 0.5)
    for x in range(-8, 9):
        r.dot(x, -9, "iron", 4 if x < -4 else 3 if x < 2 else 2, 0.51)
        if x % 3 == 0: r.dot(x, -8, "brass", 3 if x < 0 else 2, 0.52)
    r.ell(-8.8, -11, 1.0, 1.4, "iron", 0.45); r.ell(8.6, -11, 1.0, 1.4, "iron", 0.45)
    # rim and tar
    rise = {"act": [2, 0, -1, 0, 0, 0][f]}.get(mode, 0)
    r.ell(0, -13, 7.0, 2.0, "iron", 0.55, flat=3)
    r.ell(0, -13, 5.8, 1.3, "tar", 0.56, flat=2)
    for x in range(-5, 6):
        r.dot(x, -13, "tar", 1, 0.57)
    if rise > 0:
        r.ell(-0.5, -13 - rise * 0.5, 3.5, 1.0 + rise * 0.5, "tar", 0.58, bias=0.2)
    bub = (f + (2 if mode == "act" else 0)) % 4
    if mode != "sleep" or f in (3, 4):
        bx = [-3, 2, 0, -1][bub]
        r.dot(bx, -14, "tar", 3, 0.6); r.dot(bx, -15 if bub % 2 else -14, "tar", 4, 0.6)
    r.dot(-5, -14, "iron", 4, 0.56); r.dot(-4, -14, "iron", 4, 0.56)
    # spout up-right: recoils on the shot
    k = 1 if mode == "act" and f in (1, 2) else 0
    r.tube([(5, -10), (8 - k, -14 + k), (10 - k, -17 + k)], [1.6, 1.3, 1.1], "iron", 0.62)
    r.ell(10.5 - k, -17.5 + k, 1.6, 1.0, "iron", 0.63, ang=-50)
    r.dot(11 - k, -18 + k, "tar", 0, 0.64)
    if mode == "act" and f == 1:
        for i, (x, y) in enumerate([(12, -20), (13, -21), (11, -21), (14, -19)]):
            r.dot(x, y, "tar", 3 if i == 0 else 2, 0.7)
    if mode == "act" and f in (2, 3):
        r.dot(11, -16 + f, "tar", 3, 0.7); r.dot(11, -15 + f, "tar", 2, 0.7)                 # drip
    return fr.done()


def pendulum(mode, t, f, side=0):
    """Pendulum Blade: a timber gallows on stone footings with an iron rod and a honed crescent blade. 25 x 27."""
    fr = Fr((0, 12, 1.7)); r = fr.r
    for x in (-10, 9):
        block(r, x - 2, x + 2, -4, 0, "ostone", 0.0, top=1)
        block(r, x - 1, x + 1, -24, -4, "owood", 0.1, top=0, curve=0.8)
        for y in (-17, -9):
            r.dot(x - 1, y, "iron", 3, 0.12); r.dot(x, y, "iron", 2, 0.12); r.dot(x + 1, y, "iron", 1, 0.12)
    block(r, -12, 11, -27, -24, "owood", 0.3, top=1)
    for s_ in (-1, 1):
        x = -10 if s_ < 0 else 9
        r.tube([(x, -19), (x - s_ * 5, -24)], [0.8, 0.8], "owood", 0.25)
    r.ell(-0.5, -23.5, 2.0, 1.6, "iron", 0.35)
    r.dot(-1, -24, "iron", 4, 0.36)
    on = lamp_on(mode, t, f)
    for lx in (-8, 7):
        r.ell(lx, -28.3, 1.3, 1.0, "iron", 0.32)
        if on > 0: fr.glow(lx, -28, "rune", 2 + int(on * 2))
    if mode == "act":
        a0, a1 = (-64, 64) if side == 0 else (64, -64)
        e = [0.0, 0.08, 0.25, 0.5, 0.75, 0.92, 1.0][f]
        ang = a0 + (a1 - a0) * e
    elif mode == "alert":
        ang = 9 * math.sin(f * math.pi / 2)
    elif mode == "wake":
        ang = -6 * t
    else:
        ang = 2 * math.sin(f * math.pi / 3) if f else 0
    ra = math.radians(ang)
    L = 14
    sx, sy = math.sin(-ra), math.cos(ra)
    bx, by = -0.5 + L * sx, -23 + L * sy
    # motion smear behind the blade on the fast frames
    if mode == "act" and 2 <= f <= 4:
        for back, al in ((12, 170), (24, 110), (36, 60)):
            rb = math.radians(ang - back * (1 if side == 0 else -1))
            for i in range(-6, 7):
                bend = 2.4 - (i * i) / 15.0
                x = -0.5 + (L + 1 + bend) * math.sin(-rb) + math.cos(rb) * i
                y = -23 + (L + 1 + bend) * math.cos(rb) + math.sin(rb) * i
                if y <= 0: fr.glow(x, y, "steam", 3 if back == 12 else 2, al)
    r.tube([(-0.5, -23), (bx, by)], [0.7, 0.7], "iron", 0.5)
    r.dot(-0.5 + 6 * sx, -23 + 6 * sy, "brass", 3, 0.52)
    # crescent: dark spine, steel body, honed bright edge on the outside of the curve
    bp = r.part(False, 0.6)
    for i in range(-7, 8):
        bend = 2.6 - (i * i) / 16.0
        for d, tone in ((-1, 1), (0, 2), (1, 3), (2, 3), (3, 4)):
            if abs(i) >= 6 and d < 1: continue
            if abs(i) == 7 and d > 2: continue
            x = bx + math.cos(ra) * i + sx * (bend + d)
            y = by + math.sin(ra) * i + sy * (bend + d)
            if y > 0: continue
            if d == 3 and abs(i) < 6: fr.glow(x, y, "gleam", 3 if abs(i) < 4 else 2)       # the honed edge catches light
            else: r.put(x, y, 0.6, "steel", 0.5, bp, tone)
    r.ell(bx, by, 1.4, 1.4, "brass", 0.62)
    if mode == "act" and f == 3:
        fr.spark(bx + sx * 5, by + sy * 5, "gleam", 1)
    moss(r, [(-12, -4), (-11, -4), (10, -4), (11, -4), (-12, -27), (-11, -27)])
    return fr.done(specks=STONE_SPECK, seed=4)


RUNE_RING = [(-7, -4), (-5, -6), (-2, -7), (1, -7), (4, -6), (6, -4), (5, -2), (2, -2), (-2, -2), (-5, -2)]


def runeplate(mode, t, f):
    """Rune Plate: an octagonal flagstone set in the floor, a ring of carved runes and a sun at its heart. 21 x 9."""
    fr = Fr(); r = fr.r
    p = r.part(False, 0.0)
    for y in range(-8, 1):
        w = 10 - max(0, abs(y + 4) - 2)
        for x in range(-w, w + 1):
            if y <= -2:
                n = (-0.1 + 0.2 * x / 10.0, -1.0, 0.7)
            else:
                n = (-0.1 + 0.3 * x / 10.0, 0.0, 1.0)
            l = math.sqrt(sum(v * v for v in n))
            r.put(x, y, 0.0, "ostone", lam(n[0] / l, n[1] / l, n[2] / l), p)
    for x in range(-8, 9):
        r.put(x, -2, 0.001, "ostone", 0.0, p, 3)                                  # front lip catches the light
    gp = r.part(True, 0.005)
    for i in range(40):                                                           # the carved ring
        a = i * 2 * math.pi / 40
        r.put(-0.5 + 7.6 * math.cos(a), -4.6 + 2.7 * math.sin(a), 0.005, "ostone", 0.5, gp, 1)
    lit = {"sleep": 0.0, "wake": t, "alert": 0.55 + 0.45 * (f % 2), "act": 1.0}[mode]
    for i, (x, y) in enumerate(RUNE_RING):
        k = lit if mode != "act" else (1.0 if i <= f * 2.5 else 0.3)
        if lit > 0.05 and k > 0.1:
            fr.glow(x, y, "rune", min(4, 1 + int(k * 3))); fr.glow(x + 1, y, "rune", min(3, int(k * 3)))
        else:
            r.dot(x, y, "ostone", 0, 0.01); r.dot(x + 1, y, "ostone", 0, 0.01)
    core = mode == "act" and f >= 3
    for (x, y) in ((-1, -5), (0, -5), (-1, -4), (0, -4)):
        if core: fr.glow(x, y, "rune", 4 if f < 5 else 3)
        else: r.dot(x, y, "ostone", 1 if y == -5 else 0, 0.01)
    if core:
        for (x, y) in ((-3, -5), (2, -5), (-1, -7), (0, -3), (-2, -6), (1, -6)):
            fr.glow(x, y, "rune", 3 if f == 4 else 2)
        if f == 4:
            for x in range(-6, 6, 3): fr.glow(x, -9 - (x % 2), "rune", 3, 200)
    if mode == "sleep" and f in (2, 4):
        fr.glow(-2, -7, "rune", 1)
    moss(r, [(-10, -4), (-9, -3), (9, -5), (10, -4), (-6, -8)])
    return fr.done()


BELL = [1.2, 2.2, 2.8, 3.1, 3.3, 3.5, 3.8, 4.1, 4.5, 5.0, 5.6, 6.2]


def tollbell(mode, t, f):
    """Toll Bell: a bronze bell on an iron yoke over a carved stone foot. 15 x 26."""
    fr = Fr((0, 8, 1.4)); r = fr.r
    block(r, -7, 6, -4, 0, "ostone", 0.0, top=1)
    block(r, -5, 4, -6, -4, "ostone", 0.05, top=1)
    for x in (-6, 5):
        r.tube([(x, -6), (x, -23)], [0.9, 0.9], "iron", 0.2)
        r.ell(x, -24.5, 1.3, 1.3, "brass", 0.25)
    r.tube([(-6, -22), (5, -22)], [0.9, 0.9], "iron", 0.22)
    if mode == "act":
        ang = [-12, 18, -15, 11, -7, 4, -1][f]
    elif mode == "alert":
        ang = [3, 0, -3, 0][f]
    elif mode == "wake":
        ang = 4 * t
    else:
        ang = 0
    rot_rows(r, -0.5, -22, ang, 1, BELL, "bronze", 0.4)
    a = math.radians(ang)
    # lip band and the clapper (which lags the bell)
    for i in range(-6, 7):
        x = -0.5 + i * math.cos(a) - 12.4 * math.sin(a)
        y = -22 + i * math.sin(a) + 12.4 * math.cos(a)
        r.dot(x, y, "bronze", 0 if i > -4 else 1, 0.42)
    ca = math.radians(ang * 0.4)
    r.ell(-0.5 - 13 * math.sin(ca), -22 + 13 * math.cos(ca), 1.2, 1.2, "iron", 0.38)
    r.dot(-0.5 - 3 * math.sin(a) - 1, -22 + 3 * math.cos(a), "bronze", 4, 0.43)
    if mode == "act" and 1 <= f <= 4:
        for s_ in (-1, 1):
            for k in range(3):
                if (f + k) % 2 == 0:
                    fr.glow(s_ * (9 + k), -15 + k * 3 - 2, "gleam", 3, 220)
    on = lamp_on(mode, t, f)
    if on > 0:
        fr.glow(-1, -23, "rune", 2 + int(on * 2)); fr.glow(0, -23, "rune", 1 + int(on * 2))
    moss(r, [(-7, -4), (-6, -4), (5, -4), (-5, -6)])
    return fr.done(specks=STONE_SPECK, seed=6)


def idol(mode, t, f):
    """Scatter Idol: a carved stone head with a gaping mouth on a squat pillar; it spits a fan of bone darts. 15 x 21."""
    fr = Fr((0, 7, 1.4)); r = fr.r
    block(r, -6, 5, -3, 0, "ostone", 0.0, top=1)
    block(r, -4, 3, -9, -3, "ostone", 0.05, top=1, curve=0.5)
    puff = 1 if mode == "act" and f == 1 else 0
    open_ = [0.3, 0.6, 1.0, 1.0, 0.5][f] if mode == "act" else {"sleep": 0.0, "wake": t * 0.5, "alert": 0.5}[mode]
    # head: a rounded block, heavy brow, flat nose
    hp = r.part(False, 0.3)
    for y in range(-20, -8):
        for x in range(-6 - puff, 6 + puff):
            u = (x + 0.5) / (6.0 + puff); v = (y + 14) / 6.5
            if u * u * 0.6 + max(0, abs(v) - 0.5) ** 2 > 1.0: continue
            nx = u * 0.9; ny = max(-0.9, min(0.9, v * 0.6)) if abs(v) > 0.6 else 0.0
            nz = math.sqrt(max(0.05, 1 - nx * nx - ny * ny))
            r.put(x, y, 0.3, "ostone", lam(nx, ny, nz), hp)
    for x in range(-5, 5):
        r.dot(x, -16, "ostone", 3 if x < 2 else 2, 0.31)                          # brow ledge
        r.dot(x, -15, "ostone", 1, 0.31)
    on = lamp_on(mode, t, f)
    for ex in (-3, 1):
        if on > 0:
            fr.glow(ex, -14, "rune", 2 + int(on * 2)); fr.glow(ex + 1, -14, "rune", 1 + int(on * 2))
        else:
            r.dot(ex, -14, "ostone", 0, 0.31); r.dot(ex + 1, -14, "ostone", 0, 0.31)
    r.dot(-1, -13, "ostone", 3, 0.31); r.dot(-1, -12, "ostone", 1, 0.31); r.dot(0, -12, "ostone", 0, 0.31)
    m = int(round(open_ * 3))
    for y in range(-11, -10 + m):
        w = 2 if y < -11 + m else 1
        for x in range(-1 - w, w + 1):
            r.dot(x, y, "tar", 1 if y == -11 else 0, 0.32)
    for x in range(-2 - (1 if m else 0), 2 + (1 if m else 0)):
        r.dot(x, -12 if m else -11, "ostone", 3, 0.33)                             # upper lip
        r.dot(x, -10 + m, "ostone", 2, 0.33)                                       # lower lip
    if m >= 2 and not (mode == "act" and f == 2):
        r.dot(-1, -10 + m - 1, "bone", 4, 0.34); r.dot(0, -10 + m - 1, "bone", 3, 0.34)
    if mode == "act" and f == 2:
        for (x, y) in ((-5, -10), (4, -10), (-4, -8), (3, -8), (0, -6)):
            fr.glow(x, y, "steam", 3, 200)
    r.dot(-6, -18, "ostone", 0, 0.31); r.dot(-5, -19, "ostone", 0, 0.31); r.dot(4, -10, "ostone", 0, 0.31)   # chips
    moss(r, [(-4, -20), (-3, -20), (-2, -20), (3, -19), (-6, -17), (2, -9), (-4, -9), (-6, -3)])
    return fr.done(specks=STONE_SPECK, seed=7)


# ================================================================== TOUCH
def snare(state, f):
    """Iron Snare: toothed steel jaws on a staked base plate round a brass pressure pan; open, or snapped shut. 19 x 9."""
    fr = Fr((0, 10, 1.5)); r = fr.r
    block(r, -8, 7, -2, 0, "iron", 0.0, top=1)
    for x in (-9, 8):
        r.ell(x, -1.5, 1.6, 1.6, "iron", 0.1)                                     # spring eyes
        r.dot(x, -2, "iron", 4, 0.11)
    chainline(r, 9, -1, 11, 0, 0.05)
    r.dot(12, 0, "rust", 3, 0.06); r.dot(12, -1, "rust", 2, 0.06)                 # the stake
    if state == "open":
        # two jaws lying open round the pan: a lit steel ring seen from above, sawteeth along its inner edge
        cx, cy, RX, RY = -0.5, -3.2, 9.0, 3.6
        jp = r.part(True, 0.3)
        for y in range(int(cy - RY) - 1, int(cy + RY) + 2):
            for x in range(int(cx - RX) - 1, int(cx + RX) + 2):
                u, v = (x - cx) / RX, (y - cy) / RY
                d = math.sqrt(u * u + v * v)
                if 0.74 <= d <= 1.0 and abs(u) > 0.12:
                    t = 4 if v < -0.35 and u < 0.3 else 3 if v < 0.2 else 2 if u < 0.5 else 1
                    r.put(x, y, 0.3, "steel", 0.5, jp, t)
        for i in range(16):                                                        # teeth pointing in, gaps dark
            a = i * 2 * math.pi / 16 + 0.2
            if abs(math.cos(a)) < 0.2: continue
            x, y = cx + RX * 0.62 * math.cos(a), cy + RY * 0.55 * math.sin(a)
            if i % 2 == 0:
                r.put(x, y, 0.31, "steel", 0.5, jp, 4)
                r.put(cx + RX * 0.7 * math.cos(a), cy + RY * 0.68 * math.sin(a), 0.31, "steel", 0.5, jp, 3)
            else:
                r.put(x, y, 0.31, "tar", 0.5, jp, 0)
        r.ell(cx, cy, 3.0, 1.3, "brass", 0.2)
        r.dot(-2, -4, "brass", 4, 0.21)
    else:
        h = {"shut": 7, "mid": 4, "snap": 8}[state]
        for s_ in (-1, 1):
            base = -0.5 + s_ * (1.2 if state != "mid" else 3.0)
            jp = r.part(True, 0.3 + (0.01 if s_ < 0 else 0))
            for i in range(h):
                x = base + s_ * (1.0 if state == "mid" and i > h // 2 else 0)
                r.put(x, -2 - i, 0.3, "iron", 0.5, jp, 4 if s_ < 0 else 2)
                r.put(x + s_, -2 - i, 0.3, "iron", 0.5, jp, 3 if s_ < 0 else 1)
            for i in range(1, h, 2):
                r.put(base - s_ * (0.6 if s_ > 0 else 1), -2 - i - (0 if s_ < 0 else 1), 0.32, "iron", 0.5, jp, 4)
        if state == "snap":
            for (x, y) in [(-5, -9), (4, -9), (-0.5, -11), (-6, -5), (5, -5)]:
                fr.glow(x, y, "gleam", 4)
            fr.spark(-0.5, -6, "gleam", 1)
    if f % 4 == 2:
        fr.spark(-5 if state == "open" else -2, -4, "gleam", 1, 3)
    return fr.done()


def warp(mode, f, t=0.0):
    """Warp Stone: a low drum of dark stone, its top cut with a violet sigil that pulses; flares on use. 19 x 9."""
    fr = Fr((0, 10, 1.7)); r = fr.r
    drum(r, -0.5, -6, 0, 9.0, "ostone", 0.0, ry=3.0, capmat="ostone")
    gp = r.part(True, 0.05)
    for i in range(48):
        a = i * 2 * math.pi / 48
        r.put(-0.5 + 6.6 * math.cos(a), -6 + 2.1 * math.sin(a), 0.05, "ostone", 0.5, gp, 1)
    for x in range(-8, 8, 4):
        r.dot(x, -2, "ostone", 1, 0.06); r.dot(x + 1, -2, "ostone", 1, 0.06)      # carved notches round the side
    pulse = 0.5 + 0.5 * math.sin(f * math.pi / 3) if mode == "idle" else (1.0 - abs(t - 0.4) if mode == "use" else 0)
    sig = [(-4, -6), (-3, -7), (-1, -7), (0, -7), (2, -7), (3, -6), (2, -5), (0, -5), (-1, -5), (-3, -5), (-0.5, -6)]
    for i, (x, y) in enumerate(sig):
        if mode == "off":
            r.dot(x, y, "ostone", 0, 0.07)
        else:
            fr.glow(x, y, "glow", min(4, 1 + int(pulse * 3) + (1 if i == len(sig) - 1 else 0)))
    if mode == "use":
        hgt = int(4 + 20 * math.sin(math.pi * min(1.0, t * 1.2)))
        for y in range(-7, -7 - hgt, -1):
            for x in range(-3, 3):
                d = abs(x + 0.5)
                if d < 2.6 and ((x + y + f) % 5 != 0 or d < 1):
                    fr.glow(x, y, "glow", 4 if d < 0.8 else 3 if d < 1.8 else 2, 255 if d < 1.8 else 190)
        for k in range(3):
            fr.glow(-6 + k * 5, -9 - ((f + k) % 3) * 3, "glow", 4)
    moss(r, [(-9, -3), (8, -3), (-7, -6), (-8, -5)])
    return fr.done(specks=STONE_SPECK, seed=9)


# ================================================================== USE
def spring(mode, f, t=0.0):
    """Mending Spring: a wide carved basin of pale stone on a pedestal, a fish-head spout feeding glowing water. 21 x 21."""
    fr = Fr((0, 10, 1.7)); r = fr.r
    block(r, -6, 5, -2, 0, "pstone", 0.0, top=1)
    block(r, -3, 2, -7, -2, "pstone", 0.05, top=0, curve=0.8)
    rows(r, -0.5, -12, [9.5, 10.0, 9.8, 9.2, 8.0, 6.0, 4.0], "pstone", 0.2)
    r.ell(-0.5, -12, 10.0, 2.4, "pstone", 0.25, flat=3)
    full = mode != "spent"
    if full:
        for y in range(-13, -10):
            for x in range(-8, 8):
                if ((x + 0.5) / 8.5) ** 2 + ((y + 12) / 1.6) ** 2 <= 1.0:
                    rip = (x + f + (y * 2)) % 6
                    if mode == "off":
                        r.dot(x, y, "water", 2, 0.3)
                    else:
                        fr.glow(x, y, "cyan", 3 if rip == 0 else 2 if rip in (1, 5) else 1)
    else:
        r.ell(-0.5, -12, 8.5, 1.6, "pstone", 0.3, flat=1)
        r.dot(-3, -12, "moss", 2, 0.31); r.dot(2, -12, "moss", 1, 0.31)
    # the back spout: a carved fish standing on its tail
    rows(r, -0.5, -21, [1.0, 1.8, 2.2, 2.2, 2.0, 1.6, 1.4, 1.6, 2.0], "pstone", 0.1)
    r.dot(-2, -19, "tar", 0, 0.12); r.dot(1, -18, "pstone", 0, 0.12); r.dot(1, -17, "pstone", 1, 0.12)
    if full and mode != "off":
        for y in range(-17, -12):
            if (y + f) % 3 != 0:
                fr.glow(2, y, "cyan", 3 if (y + f) % 3 == 1 else 2)
    if mode == "use":
        for i in range(5):
            y = -14 - int(t * 12) - i * 3
            fr.spark([-5, 4, -1, 6, -7][i], y, "ecto", 1 if i % 2 else 0, 4)
        fr.glow(-0.5, -13, "cyan", 4)
    elif mode == "idle" and f % 3 == 1:
        fr.glow([-5, 4, 0][f // 3 % 3], -14, "ecto", 3)
    moss(r, [(-10, -12), (-9, -11), (9, -12), (8, -10), (-5, -7), (2, -2), (-6, -2), (-1, -21)])
    return fr.done(specks=STONE_SPECK, seed=10)


def rack(mode, f, t=0.0, taken=False):
    """Weapon Rack: a pegged timber frame holding a war axe, a sword and a spear. 19 x 25."""
    fr = Fr((0, 10, 1.5)); r = fr.r
    for x in (-8, 8):
        block(r, x - 1, x + 1, -20, 0, "owood", 0.0, top=1, curve=0.8)
        r.ell(x, -21, 1.4, 1.0, "owood", 0.05)
    block(r, -9, 9, -16, -14, "owood", 0.05, top=1)
    block(r, -9, 9, -5, -3, "owood", 0.05, top=1)
    for x in (-8, 8):
        r.dot(x, -15, "iron", 3, 0.06); r.dot(x, -4, "iron", 3, 0.06)
    lift = 0 if mode != "use" else int(round(t * 9))
    # axe (left): haft and a bearded head
    r.tube([(-5, -2), (-5, -19)], [0.7, 0.7], "owood", 0.2)
    ap = r.part(False, 0.25)
    for (x, y) in [(-4, -19), (-3, -19), (-2, -20), (-4, -18), (-3, -18), (-2, -18), (-1, -19), (-4, -17), (-3, -17),
                   (-2, -17), (-1, -17), (-4, -16), (-3, -16), (-2, -15), (-1, -15), (-6, -18), (-7, -18), (-7, -17)]:
        r.put(x, y, 0.25, "iron", lam(-0.3, -0.3, 0.9), ap)
    for (x, y) in [(-1, -19), (-1, -18), (-1, -17), (-1, -16), (-1, -15)]:
        r.put(x, y, 0.26, "iron", 0.5, ap, 4)                                        # honed edge
    # sword (middle, the one that is taken)
    if not taken:
        dy = -lift
        bp = r.part(False, 0.3)
        for y in range(-20, -6):
            r.put(-1, y + dy, 0.3, "iron", 0.5, bp, 4 if y > -19 else 3)
            r.put(0, y + dy, 0.3, "iron", 0.5, bp, 3)
            r.put(1, y + dy, 0.3, "iron", 0.5, bp, 1)
        r.put(0, -21 + dy, 0.3, "iron", 0.5, bp, 4)
        block(r, -3, 3, -6 + dy, -5 + dy, "brass", 0.32, top=1)
        r.tube([(0, -4 + dy), (0, -2 + dy)], [0.7, 0.7], "velvet", 0.31)
        r.ell(0, -1 + dy, 1.0, 1.0, "brass", 0.32)
        if mode == "use":
            fr.spark(0, -18 + dy, "gleam", 1 if f % 2 else 2)
        elif f == 1:
            fr.spark(-1, -16, "gleam", 1)
    else:
        r.dot(-1, -16, "owood", 0, 0.3); r.dot(1, -16, "owood", 0, 0.3)
        r.dot(-1, -5, "owood", 0, 0.3); r.dot(1, -5, "owood", 0, 0.3)
    # spear (right)
    r.tube([(5, -1), (5, -21)], [0.6, 0.6], "owood", 0.2)
    sp = r.part(False, 0.25)
    for (x, y, tn) in [(5, -26, 4), (4, -25, 3), (5, -25, 4), (6, -25, 2), (4, -24, 3), (5, -24, 3), (6, -24, 1),
                       (4, -23, 2), (5, -23, 3), (6, -23, 1), (5, -22, 2)]:
        r.put(x, y, 0.25, "iron", 0.5, sp, tn)
    r.dot(4, -21, "velvet", 3, 0.26); r.dot(6, -20, "velvet", 2, 0.26); r.dot(4, -19, "velvet", 2, 0.26)
    moss(r, [(-9, -1), (9, -2), (-9, -16)])
    return fr.done(specks=STONE_SPECK, seed=11)


def altar(mode, f, t=0.0):
    """Cursed Altar: a cracked black-stone altar with a blood channel, a horned skull and a violet flame. 21 x 22."""
    fr = Fr((0, 10, 1.7)); r = fr.r
    lit = mode not in ("spent", "off")
    block(r, -10, 9, -2, 0, "dstone", 0.0, top=1)
    block(r, -8, 7, -9, -2, "dstone", 0.05, top=2, curve=0.4)
    for x in (-8, 7):
        block(r, x - 1, x + 1, -10, -2, "dstone", 0.1, top=1)
    for (x, y) in [(-5, -6), (-4, -5), (-4, -4), (-5, -3), (3, -7), (4, -6), (4, -5), (5, -4), (5, -3)]:
        if lit: fr.glow(x, y, "glow", 1 + (1 if (x + y + f) % 3 == 0 else 0))
        else: r.dot(x, y, "dstone", 0, 0.06)
    for x in range(-6, 6):
        if lit: fr.glow(x, -9, "blood", 2 if (x + f) % 4 else 3)
        else: r.dot(x, -9, "dstone", 1, 0.06)
    if lit:
        fr.glow(-6, -8, "blood", 1); fr.glow(-7, -7, "blood", 1)                   # drip over the edge
    # horned skull
    r.ell(-0.5, -12.5, 3.4, 2.8, "bone", 0.3)
    r.ell(-0.5, -10.4, 2.0, 1.0, "bone", 0.31)
    r.dot(-2, -12, "tar", 0, 0.32); r.dot(1, -12, "tar", 0, 0.32); r.dot(-0.5, -10, "tar", 1, 0.32)
    for s_ in (-1, 1):
        r.tube([(-0.5 + s_ * 2.5, -14), (-0.5 + s_ * 5, -16), (-0.5 + s_ * 6.5, -18.5)], [1.0, 0.8, 0.5], "bone", 0.29)
    if lit:
        for ex in (-2, 1):
            fr.glow(ex, -12, "glow", 3 if f % 3 else 4)
    if lit:
        big = 1.0 if mode == "idle" else 1.0 + 1.3 * math.sin(math.pi * t)
        h = int(round((5 + (f % 3 == 1)) * big))
        for i in range(h):
            y = -16 - i
            w = max(0, int(round((2.0 - i / float(h) * 2.0) * (1.0 if big < 1.5 else 1.4))))
            sway = [0, 1, 0, -1][(f + i) % 4] if i > h // 2 else 0
            for x in range(-w, w + 1):
                fr.glow(-0.5 + x + sway, y, "glow", 4 if x == 0 and i < h - 1 else 3 if abs(x) <= 1 else 2)
    else:
        fr.glow(-0.5, -16, "smoke", 2, 200); fr.glow(0.5, -18, "smoke", 1, 150)
    if mode == "use":
        for i in range(6):
            a = i * 1.05 + t * 3
            rr = 3 + t * 8
            fr.glow(-0.5 + rr * math.cos(a), -12 + rr * 0.6 * math.sin(a), "glow", 4 - (i % 2))
    return fr.done(specks=STONE_SPECK, seed=12)


def shrine(mode, f, t=0.0):
    """Ward Shrine: a little gabled stone shrine; in its niche an iron kite shield carries a cyan ward sigil. 15 x 26."""
    fr = Fr((0, 8, 1.5)); r = fr.r
    block(r, -7, 6, -4, 0, "ostone", 0.0, top=1)
    block(r, -6, 5, -19, -4, "ostone", 0.05, top=0, curve=0.5)
    rp = r.part(False, 0.2)
    for i in range(6):
        y = -20 - i
        for x in range(-7 + i, 7 - i):
            r.put(x, y, 0.2, "ostone", lam(-0.3 if x < -0.5 else 0.5, -0.8, 0.5), rp)
    for x in range(-7, 7):
        r.put(x, -20, 0.21, "ostone", 0.5, rp, 3 if x < 3 else 2)
    r.ell(-0.5, -26.5, 1.0, 1.0, "brass", 0.22)
    # niche
    for y in range(-17, -5):
        for x in range(-4, 4):
            if y > -15 or abs(x + 0.5) < 3.5 - (-15 - y) * 0.8:
                r.dot(x, y, "ostone", 0, 0.1)
    lit = mode not in ("spent", "off")
    pulse = (0.6 + 0.4 * math.sin(f * math.pi / 3)) if mode == "idle" else (1.0 if mode == "use" else 0)
    sp = r.part(False, 0.3)
    for y in range(-15, -6):
        w = 3 if y < -10 else [3, 2, 2, 1, 0][min(4, y + 10)]
        for x in range(-w, w + 1):
            u = x / 3.5
            r.put(-0.5 + x, y, 0.3, "iron", lam(u * 0.7 - 0.2, -0.2, 0.8), sp)
    for (x, y) in [(-0.5, -14), (-0.5, -13), (-0.5, -12), (-0.5, -11), (-0.5, -10), (-0.5, -9), (-2.5, -12), (1.5, -12),
                   (-1.5, -12), (0.5, -12)]:
        if lit: fr.glow(x, y, "cyan", min(4, 1 + int(pulse * 3)))
        else: r.dot(x, y, "iron", 1, 0.31)
    if mode == "use":
        rr = 2 + t * 10
        for i in range(28):
            a = i * 2 * math.pi / 28
            fr.glow(-0.5 + rr * math.cos(a), -11 + rr * math.sin(a), "cyan", 3 if t < 0.6 else 2)
    moss(r, [(-7, -4), (-6, -4), (5, -4), (-7, -20), (-6, -21), (4, -21)])
    return fr.done(specks=STONE_SPECK, seed=13)


URN = [2.2, 2.4, 3.0, 4.0, 5.0, 5.6, 5.8, 5.8, 5.6, 5.2, 4.6, 4.0, 3.4, 3.0]


def urn(mode, f, t=0.0):
    """Spirit Urn: a fat clay funeral urn bound with green-glowing seals; it can be smashed. 13 x 18."""
    fr = Fr((0, 7, 1.4)); r = fr.r
    if mode == "spent":
        for (x, y, tn) in [(-5, -1, 3), (-4, -1, 2), (2, -1, 3), (3, 0, 2), (-1, 0, 3), (0, -2, 2), (4, -2, 3),
                           (-6, 0, 1), (5, 0, 1), (-2, -1, 2), (1, 0, 1)]:
            r.dot(x, y, "clay", tn, 0.1)
        r.dot(-3, 0, "clay", 4, 0.1); r.dot(-4, 0, "clay", 2, 0.1)
        fr.glow(1, -1, "ecto", 1)
        return fr.done()
    if mode == "use" and t >= 0.4:
        k = (t - 0.4) / 0.6
        rnd = random.Random(4)
        for i in range(12):
            a = rnd.uniform(-math.pi, 0)
            d = 2 + k * rnd.uniform(4, 9)
            x, y = d * math.cos(a), -7 + d * math.sin(a) * 0.8 + k * k * 7
            r.dot(x, min(0, y), "clay", rnd.randint(1, 4), 0.2)
            if i % 3 == 0: r.dot(x + 1, min(0, y), "clay", 2, 0.2)
        for i in range(6):
            y = -7 - int(k * 14) - i * 2
            fr.glow(((i * 3) % 5) - 2, y, "ecto", 4 - i % 3)
        return fr.done()
    sx = [1, -1, 1][int(t * 7) % 3] if mode == "use" else 0
    rows(r, -0.5 + sx, -15, URN, "clay", 0.2)
    r.ell(-0.5 + sx, -15.5, 2.6, 1.0, "clay", 0.22, flat=1)
    r.ell(-0.5 + sx, -16.5, 1.4, 1.2, "clay", 0.23)
    lit = mode != "off"
    for x in range(-6, 6):
        if lit: fr.glow(x + sx, -8, "ecto", 2 + (1 if (x + f) % 3 == 0 else 0))
        else: r.dot(x + sx, -8, "clay", 1, 0.24)
    for x in range(-3, 3):
        if lit: fr.glow(x + sx, -13, "ecto", 2)
        else: r.dot(x + sx, -13, "clay", 1, 0.24)
    for (x, y) in [(-3, -11), (-3, -10), (-2, -11), (2, -6), (2, -5)]:                  # glyphs on the belly
        if lit: fr.glow(x + sx, y, "ecto", 3)
        else: r.dot(x + sx, y, "clay", 1, 0.24)
    if mode == "use":
        for (x, y) in [(1, -12), (2, -11), (2, -10), (3, -9), (3, -7), (4, -6)]:
            r.dot(x + sx, y, "clay", 0, 0.25)
    if mode == "idle" and f % 3 == 0:
        fr.glow(-0.5, -18 - (f // 3), "ecto", 2)
    return fr.done()


def strongbox(mode, f, t=0.0):
    """Strongbox: an iron-banded plank chest with a brass lock. It opens on a bed of coins, or it is a mimic. 17 x 15."""
    fr = Fr((0, 9, 1.5)); r = fr.r
    block(r, -8, 7, -8, 0, "plank", 0.0, top=0)
    for y in (-6, -3):
        r.polyline([(-8, y), (7, y)], "plank", 0.01, tone=1)
    for x in (-6, 5):
        block(r, x, x + 1, -8, 0, "iron", 0.05, top=0)
        r.dot(x, -7, "iron", 4, 0.06); r.dot(x, -2, "iron", 3, 0.06)
    block(r, -2, 1, -7, -4, "brass", 0.1, top=0)
    r.dot(-1, -6, "tar", 0, 0.11); r.dot(-1, -5, "tar", 0, 0.11)
    if mode == "bite":
        open_ = [0.3, 1.0, 0.2, 1.0, 0.6, 0.0][f]
    else:
        open_ = {"idle": 0.0, "use": t, "spent": 1.0, "off": 0.0}[mode]
    if open_ < 0.5:
        lift = int(round(open_ * 5))
        block(r, -8, 7, -13 - lift, -9 - lift, "plank", 0.3, top=2)
        for x in (-6, 5):
            block(r, x, x + 1, -13 - lift, -9 - lift, "iron", 0.32, top=1)
        block(r, -2, 1, -10 - lift, -9 - lift, "brass", 0.33, top=0)
        if lift:
            for x in range(-7, 7):
                if mode == "use": fr.glow(x, -9, "gleam", 2 + (1 if x % 3 == 0 else 0))
                else: r.dot(x, -9, "tar", 0, 0.2)
    else:
        # lid thrown back, seen edge-on above the box
        block(r, -8, 7, -15, -12, "plank", 0.05, top=1, bias=-0.15)
        for x in (-6, 5):
            block(r, x, x + 1, -15, -12, "iron", 0.06, top=1)
        for y in range(-11, -8):
            for x in range(-7, 7):
                r.dot(x, y, "tar", 1 if y == -11 else 0, 0.1)
        if mode == "bite":
            for x in range(-7, 7, 2):
                r.dot(x, -11, "bone", 4, 0.2); r.dot(x + 1, -10 + (1 if open_ < 0.9 else 0), "bone", 3, 0.2)
            for x in range(-3, 2):
                r.dot(x, -9, "blood", 3 if x < 0 else 2, 0.15)
            fr.glow(-5, -13, "blood", 4); fr.glow(4, -13, "blood", 3)
        elif mode in ("use", "spent"):
            coins = mode == "use"
            for x in range(-6, 6):
                if coins:
                    fr.glow(x, -10, "gleam", 3 if (x + f) % 3 == 0 else 2)
                    fr.glow(x, -9, "brass", 3)
                else:
                    r.dot(x, -10, "plank", 0, 0.12)
            if coins: fr.spark(-2, -11, "gleam", 1)
    if mode == "idle" and f == 2:
        fr.spark(-1, -6, "gleam", 1, 3)
    moss(r, [(-8, -1), (7, -2)])
    return fr.done(specks=STONE_SPECK, seed=14)


# ================================================================== EFFECTS (origins fixed: ObjectPack.cs places them)
def fxdone(fr):
    return fr.done(floor=False)


def hook_fly(f):
    """The thrown hook pointing right (+x), centred, trailing a run of chain."""
    fr = Fr(); r = fr.r
    for i in range(-11, -2):
        lit = (i + f) % 2 == 0
        r.dot(i, 0, "iron", 3 if lit else 1, 0.1)
        if lit: r.dot(i, -1, "iron", 4, 0.1)
        else: r.dot(i, 1, "iron", 1, 0.1)
    hp = r.part(True, 0.3)
    for (x, y, tn) in [(-2, 0, 3), (-1, 0, 3), (0, 0, 3), (1, 0, 4), (2, 0, 4), (3, 0, 3), (-1, -1, 2), (0, -1, 4),
                       (3, -1, 2), (2, -2, 3), (1, -3, 4), (0, -3, 3), (3, 1, 2), (2, 2, 2), (1, 3, 1), (0, 3, 2),
                       (4, 0, 4), (5, 0, 3)]:
        r.put(x, y, 0.3, "brass", 0.5, hp, tn)
    fr.glow(-12, f - 1, "steam", 2, 150)
    return fxdone(fr)


def hook_yank(f):
    """The tug when the hook bites: rust-brass streaks bursting off the hero's body (centred)."""
    fr = Fr()
    rr = [2, 4, 6, 7][f]
    for i in range(8):
        a = i * math.pi / 4 + 0.3
        for k in range(max(0, rr - 3), rr):
            tn = 4 if k >= rr - 1 and f < 2 else 3 if f < 2 else 2
            fr.glow(k * math.cos(a), k * math.sin(a), "brass" if f < 3 else "rust", tn)
    if f < 2:
        fr.spark(0, 0, "gleam", 2 - f)
    for i in range(3):
        a = i * 2.1 + f
        fr.glow((3 + f) * math.cos(a), (3 + f) * math.sin(a) * 0.6, "iron", 4 - f // 2)
    return fxdone(fr)


def steam_blast(f):
    """A scalding jet of steam rolling along the floor to the right from x = 0 (the vent mouth). Shaded puffs swell,
    a hot white core leads, and the last frames tear apart and thin out."""
    fr = Fr(); r = fr.r
    rnd = random.Random(77)
    head = [9, 21, 33, 39, 41, 41, 41][f]
    fade = [0, 0, 0, 0, 1, 2, 3][f]
    puffs = []
    for i in range(13):
        u = (i + 0.5) / 13
        x = u * head + rnd.uniform(-1.0, 1.0)
        rad = 1.6 + x * 0.1 + rnd.uniform(-0.3, 0.5)
        y = -2.4 - rad * 0.55 + rnd.uniform(-0.8, 0.8) * (x / 20.0)
        puffs.append((x, y, rad))
    for (x0, y0, rad) in puffs:                                                    # shaded puffs, later ones in front
        rx, ry = rad * 1.25, rad * 0.95
        for y in range(int(y0 - ry) - 1, int(y0 + ry) + 2):
            for x in range(int(x0 - rx) - 1, int(x0 + rx) + 2):
                u, v = (x - x0) / rx, (y - y0) / ry
                d = u * u + v * v
                if d > 1.0: continue
                l = lam(u, v, math.sqrt(1 - d))
                fr.glow(x, y, "steam", 1 if l < 0.05 else 2 if l < 0.45 else 3 if l < 0.8 else 4)
    s = fxdone(fr)
    px = dict(s.px)
    if fade:
        hole = random.Random(5 + fade)
        for k in list(px):
            if hole.random() < 0.26 * fade: del px[k]
            else:
                c = px[k]; px[k] = c[:3] + (max(60, 255 - 50 * fade),)
    if f < 3:
        for x in range(0, 3 + f * 2):
            px[(x, -3)] = (255, 255, 250, 255); px[(x, -4)] = (240, 240, 236, 255)
    if 1 <= f <= 3:
        rnd2 = random.Random(f)
        for i in range(5):
            x = rnd2.uniform(4, head); y = rnd2.uniform(-9, -6)
            px[(int(x), int(y))] = (230, 236, 240, 220)
    return Px(px, s.tones)


def tar_fly(f):
    """A tar glob in flight (centred), a highlight on top and drips peeling off behind."""
    fr = Fr(); r = fr.r
    r.ell(0, 0, 2.8, 2.3, "tar", 0.2)
    r.dot(-1, -1, "tar", 4, 0.21); r.dot(0, -2, "tar", 3, 0.21)
    r.dot(-3 - f, 0, "tar", 2, 0.1); r.dot(-4 - f, 1, "tar", 1, 0.1); r.dot(-6 - f, 0, "tar", 1, 0.1)
    return fxdone(fr)


def tar_pool(f, fade=0):
    """A black tar puddle centred on the origin: it splats out (3 frames), bubbles (5) and shrinks away (Fade 3)."""
    fr = Fr()
    grow = [0.45, 0.8, 1.0][f] if f < 3 else 1.0
    rx, ry = 12 * grow, 4.5 * grow
    if fade:
        rx, ry = 12 - fade * 2.6, 4.5 - fade * 0.9
    a = 150 if fade else 240
    for y in range(int(-ry) - 1, int(ry) + 2):
        for x in range(int(-rx) - 1, int(rx) + 2):
            wob = 1.0 + 0.13 * math.sin(x * 0.9 + y * 1.7)
            u, v = x / (rx * wob), y / ry
            d = u * u + v * v
            if d <= 1.0:
                tn = 1 if d > 0.72 else (3 if v < -0.35 else 2)
                fr.glow(x, y, "tar", tn, a)
    if f == 0:
        for (x, y) in ((-8, -2), (7, -1), (-6, 2), (9, 1)):
            fr.glow(x, y, "tar", 2, a)
    for (x, y) in ((-6, -2), (-5, -2), (-4, -2), (-3, -3), (3, -2), (4, -2)):
        if abs(x) < rx - 1: fr.glow(x, y, "tar", 4, a)                             # a wet sheen
    if 3 <= f and not fade:
        b = f - 3
        bx = [-5, 3, 0, 6, -2][b]
        fr.glow(bx, -1, "tar", 3); fr.glow(bx, -2 if b % 2 else -1, "tar", 4)
        if b % 2: fr.glow(bx - 1, -1, "tar", 3); fr.glow(bx + 1, -1, "tar", 2)
    return fxdone(fr)


def rune_charge(f):
    """Runes lifting off the plate before it erupts (centred on the plate): a tightening ring, sparks climbing."""
    fr = Fr()
    rx = 9 + f * 0.5
    for i in range(56):
        a = i * 2 * math.pi / 56
        fr.glow(rx * math.cos(a), rx * 0.42 * math.sin(a), "rune", 1 + min(3, f), 230)
    for i in range(6):
        a = i * math.pi / 3 + f * 0.35
        x, y = rx * 0.8 * math.cos(a), rx * 0.35 * math.sin(a) - f * 1.6
        fr.glow(x, y, "rune", 4 if (i + f) % 2 else 3); fr.glow(x, y - 1, "rune", 2); fr.glow(x + 1, y, "rune", 2)
    if f >= 3:
        fr.spark(0, 0, "rune", 1, 4)
    return fxdone(fr)


def rune_burst(f):
    """The eruption: a ring of fire bursting out to 18 x 8 along the floor, flame tongues licking up from it."""
    fr = Fr()
    rr = [5, 11, 16, 18, 18, 17][f]
    for k in range(3):
        rk = rr - k * 2
        if rk <= 1: continue
        tn = 4 - k if f < 4 else 2 - min(1, k)
        for i in range(int(rk * 7)):
            a = i * 2 * math.pi / int(rk * 7)
            fr.glow(rk * math.cos(a), rk * 0.45 * math.sin(a), "rune", tn, 255 if f < 4 else 190)
    if f < 4:
        for i in range(12):
            a = i * math.pi / 6 + 0.2
            hgt = (5 - f) - (i % 3)
            for h in range(0, max(0, hgt)):
                fr.glow(rr * math.cos(a), rr * 0.45 * math.sin(a) - h - 1, "rune", 4 - min(3, h))
    if f < 2:
        for y in range(-2, 2):
            for x in range(-4 + f, 4 - f):
                fr.glow(x, y, "gleam", 4)
    if 2 <= f <= 4:
        rnd = random.Random(f)
        for i in range(6):
            fr.glow(rnd.uniform(-rr, rr), rnd.uniform(-10, -4), "rune", 3)
    return fxdone(fr)


def toll_wave(f):
    """The bell's toll: a brassy double ring of sound spreading over the floor to 30 x 14, ripples flickering on it."""
    fr = Fr()
    rr = [6, 13, 20, 26, 30, 32][f]
    for k in range(2):
        rk = rr - k * 3
        if rk <= 1: continue
        tn = 4 - k if f < 4 else 3 - k
        for i in range(int(rk * 7)):
            a = i * 2 * math.pi / int(rk * 7)
            fr.glow(rk * math.cos(a), rk * 0.46 * math.sin(a), "brass" if k else "gleam", tn, 255 if f < 4 else 170)
    for i in range(8):
        a = i * math.pi / 4 + 0.2
        fr.glow(rr * 0.85 * math.cos(a), rr * 0.4 * math.sin(a) - 3, "gleam", 4 if f % 2 else 3)
    return fxdone(fr)


def dart_fly(f):
    """A bone dart pointing right, centred, with red fletching."""
    fr = Fr(); r = fr.r
    for x in range(-4, 3):
        r.dot(x, 0, "bone", 4 if x > -1 else 3, 0.1); r.dot(x, 1, "bone", 2, 0.1)
    r.dot(3, 0, "bone", 4, 0.1); r.dot(4, 0, "bone", 3, 0.1); r.dot(3, 1, "bone", 1, 0.1)
    r.dot(-5, -1, "velvet", 3, 0.2); r.dot(-6, -1 + (f % 2), "velvet", 2, 0.2)
    r.dot(-5, 2, "velvet", 2, 0.2); r.dot(-6, 2 - (f % 2), "velvet", 1, 0.2)
    return fxdone(fr)


def warp_flash(f):
    """A violet pillar of light where someone arrives or leaves (bottom centre on the floor), motes rising off it."""
    fr = Fr()
    h = [10, 22, 27, 25, 17, 8][f]
    w = [3, 3, 2, 2, 1, 1][f]
    for y in range(0, -h, -1):
        for x in range(-w, w + 1):
            d = abs(x) / float(w + 0.5)
            if (y * 7 + x * 3 + f) % 6 == 0 and d > 0.3: continue
            fr.glow(x, y, "glow", 4 if d < 0.3 else 3 if d < 0.7 else 2, 255 if d < 0.7 else 200)
    for i in range(48):
        a = i * 2 * math.pi / 48
        fr.glow((4 + f * 1.6) * math.cos(a), (1.6 + f * 0.5) * math.sin(a), "glow", 3 if f < 3 else 2)
    for i in range(5):
        fr.glow(((i * 5 + f * 3) % 11) - 5, -h + 2 - i * 2 - f, "glow", 4)
    return fxdone(fr)


def urn_burst(f):
    """Ectoplasm spilling out of the smashed urn (centred): green wisps that swirl up and thin out."""
    fr = Fr()
    rnd = random.Random(9)
    for i in range(11):
        a = rnd.uniform(0, 2 * math.pi)
        d = 1 + f * rnd.uniform(1.5, 2.6)
        x, y = d * math.cos(a), d * math.sin(a) * 0.7 - f * 1.3
        fr.glow(x, y, "ecto", 4 - (i + f) % 3)
        if f < 4: fr.glow(x, y + 1, "ecto", 2, 200)
    if f < 3:
        rr = 3.2 - f
        for y in range(-3, 4):
            for x in range(-4, 5):
                d = (x / rr) ** 2 + (y / (rr * 0.8)) ** 2
                if d <= 1.0: fr.glow(x, y, "ecto", 4 if d < 0.4 else 3)
    return fxdone(fr)


def mimic_coins(f):
    """Gold coins tossed up out of the strongbox, each a lit 3 x 2 coin that flips."""
    fr = Fr()
    for i in range(6):
        vx = (i - 2.5) * 1.3
        vy = -5.0 + (i % 3) * 0.9
        x = vx * f
        y = vy * f + 0.8 * f * f
        flip = (i + f) % 3
        if flip == 1:
            fr.glow(x, y, "brass", 4); fr.glow(x, y + 1, "brass", 2)
        else:
            for dx in (-1, 0, 1):
                fr.glow(x + dx, y, "brass", 4 if flip == 0 else 3); fr.glow(x + dx, y + 1, "brass", 2)
            fr.glow(x - 1, y, "gleam", 4)
    return fxdone(fr)


def ind_curse(f):
    """Over-head mark of the Cursed Altar: a small horned skull with violet eyes and a pulsing red rim."""
    fr = Fr(); r = fr.r
    pulse = [0, 1, 2, 2, 1, 0][f]
    r.ell(0, -4, 2.6, 2.2, "bone", 0.2)
    r.dot(0, -2, "bone", 2, 0.21)
    r.dot(0, -3, "tar", 1, 0.22)
    r.tube([(-2, -6), (-4, -8)], [0.5, 0.5], "bone", 0.19); r.tube([(2, -6), (4, -8)], [0.5, 0.5], "bone", 0.19)
    fr.glow(-1, -4, "glow", 3 + (pulse > 1)); fr.glow(1, -4, "glow", 3 + (pulse > 1))
    for (x, y) in [(-3, -3), (3, -3), (-2, -1), (2, -1)]:
        fr.glow(x, y, "blood", 2 + pulse)
    return fxdone(fr)


def ind_ward(f):
    """Feet ring of the Ward Shrine: a cyan rune circle turning round the feet."""
    fr = Fr()
    for i in range(12):
        a = i * math.pi / 6 + f * math.pi / 18
        x, y = 8 * math.cos(a), 3 * math.sin(a)
        fr.glow(x, y, "cyan", 4 if i % 3 == 0 else 3 if i % 3 == 1 else 2, 255 if y > -1 else 170)
    fr.glow(8 * math.cos(f * math.pi / 3), 3 * math.sin(f * math.pi / 3) - 1, "cyan", 4)
    return fxdone(fr)


# ================================================================== build
FX_CELLS = {   # sheet: (cell, origin) as ObjectPack.cs places them
    "FxObjHook": ((24, 14), (12, 7)), "FxObjSteam": ((50, 20), (4, 15)), "FxObjTar": ((32, 14), (16, 7)),
    "FxObjRune": ((44, 24), (22, 14)), "FxObjToll": ((72, 36), (36, 18)), "FxObjDart": ((16, 8), (8, 4)),
    "FxObjWarp": ((25, 41), (12, 36)), "FxObjUrn": ((28, 28), (14, 18)), "FxObjMimic": ((35, 28), (18, 22)),
    "FxObjIndCurse": ((12, 12), (6, 11)), "FxObjIndWard": ((20, 10), (10, 6)),
}


def fx(name, anims):
    cell, origin = FX_CELLS[name]
    return emit(name, anims, cell, feet=origin)


BUILDS = {}


def build(name):
    def deco(fn):
        BUILDS[name] = fn
        return fn
    return deco


@build("traps")
def build_traps():
    trap_sheet("ObjChainHook", winch, [("Action", 6, [0.08, 0.06, 0.12, 0.12, 0.12, 0.12], "act")])
    trap_sheet("ObjSteamVent", vent, [("Action", 6, [0.1, 0.06, 0.1, 0.12, 0.12, 0.1], "act")])
    trap_sheet("ObjTarSpout", tarspout, [("Action", 6, [0.1, 0.08, 0.1, 0.12, 0.12, 0.1], "act")])
    sw = [0.07, 0.06, 0.05, 0.05, 0.06, 0.08, 0.12]
    trap_sheet("ObjPendulum", lambda m, t, f: pendulum(m, t, f, 0),
               [("SwingL", 7, sw, "act"), ("SwingR", 7, sw, "act", lambda m, t, f: pendulum(m, t, f, 1))])
    trap_sheet("ObjRunePlate", runeplate, [("Action", 6, [0.08, 0.08, 0.08, 0.08, 0.1, 0.12], "act")])
    trap_sheet("ObjTollBell", tollbell, [("Action", 7, [0.06, 0.07, 0.08, 0.1, 0.12, 0.12, 0.12], "act")])
    trap_sheet("ObjScatterIdol", idol, [("Action", 5, [0.1, 0.06, 0.1, 0.12, 0.1], "act")])


@build("touch")
def build_touch():
    emit("ObjIronSnare", [
        ("Idle", [snare("open", f) for f in range(4)], [0.6, 0.15, 0.15, 0.6]),
        ("Snap", [snare("mid", 0), snare("snap", 0), snare("shut", 1), snare("shut", 0)], [0.04, 0.06, 0.08, 0.12]),
        ("Sprung", [snare("shut", 0)], [0.2]),
        ("Reset", [snare("mid", 0), snare("mid", 1), snare("open", 0), snare("open", 0)], [0.12, 0.12, 0.1, 0.1]),
        ("Off", [snare("open", 0).off()], [0.2]),
        ("Vault", [snare("open", 2)], [0.2]),
    ])
    emit("ObjWarpStone", [
        ("Idle", [warp("idle", f) for f in range(6)], [0.12] * 6),
        ("Use", [warp("use", f, f / 5.0) for f in range(6)], [0.05, 0.05, 0.06, 0.07, 0.08, 0.1]),
        ("Off", [warp("off", 0).off()], [0.2]),
        ("Vault", [warp("idle", 2)], [0.2]),
    ])


@build("use")
def build_use():
    emit("ObjMendSpring", [
        ("Idle", [spring("idle", f) for f in range(6)], [0.14] * 6),
        ("Use", [spring("use", f, f / 3.0) for f in range(4)], [0.1, 0.12, 0.12, 0.14]),
        ("Spent", [spring("spent", 0)], [0.2]),
        ("Off", [spring("off", 0).off()], [0.2]),
    ])
    emit("ObjWeaponRack", [
        ("Idle", [rack("idle", f) for f in range(4)], [0.8, 0.1, 0.1, 0.8]),
        ("Use", [rack("use", i, i / 4.0) for i in range(4)] + [rack("idle", 0, taken=True)], [0.06, 0.06, 0.08, 0.1, 0.12]),
        ("Spent", [rack("idle", 0, taken=True)], [0.2]),
        ("Off", [rack("idle", 0).off()], [0.2]),
    ])
    emit("ObjCursedAltar", [
        ("Idle", [altar("idle", f) for f in range(6)], [0.1] * 6),
        ("Use", [altar("use", f, f / 5.0) for f in range(6)], [0.06, 0.06, 0.08, 0.1, 0.1, 0.12]),
        ("Spent", [altar("spent", 0)], [0.2]),
        ("Off", [altar("off", 0).off()], [0.2]),
    ])
    emit("ObjWardShrine", [
        ("Idle", [shrine("idle", f) for f in range(6)], [0.14] * 6),
        ("Use", [shrine("use", f, f / 4.0) for f in range(5)], [0.06, 0.07, 0.08, 0.1, 0.12]),
        ("Spent", [shrine("spent", 0)], [0.2]),
        ("Off", [shrine("off", 0).off()], [0.2]),
    ])
    emit("ObjSpiritUrn", [
        ("Idle", [urn("idle", f) for f in range(6)], [0.16] * 6),
        ("Use", [urn("use", f, f / 4.0) for f in range(5)], [0.05, 0.05, 0.06, 0.08, 0.1]),
        ("Spent", [urn("spent", 0)], [0.2]),
        ("Off", [urn("off", 0).off()], [0.2]),
    ])
    emit("ObjStrongbox", [
        ("Idle", [strongbox("idle", f) for f in range(4)], [0.8, 0.1, 0.1, 0.8]),
        ("Use", [strongbox("use", i, i / 3.0) for i in range(4)], [0.08, 0.08, 0.1, 0.14]),
        ("Bite", [strongbox("bite", i) for i in range(6)], [0.06, 0.08, 0.06, 0.08, 0.1, 0.14]),
        ("Spent", [strongbox("spent", 0)], [0.2]),
        ("Off", [strongbox("off", 0).off()], [0.2]),
        ("Vault", [strongbox("idle", 2)], [0.2]),
    ])


@build("fx")
def build_fx():
    fx("FxObjHook", [("Fly", [hook_fly(f) for f in range(2)], [0.08, 0.08]),
                     ("Yank", [hook_yank(f) for f in range(4)], [0.04, 0.05, 0.06, 0.08])])
    fx("FxObjSteam", [("Blast", [steam_blast(f) for f in range(7)], [0.05, 0.05, 0.06, 0.08, 0.08, 0.08, 0.1])])
    fx("FxObjTar", [("Fly", [tar_fly(f) for f in range(2)], [0.08, 0.08]),
                    ("Pool", [tar_pool(f) for f in range(8)], [0.05, 0.05, 0.08, 0.5, 0.5, 0.5, 0.5, 0.5]),
                    ("Fade", [tar_pool(7, fade=k) for k in (1, 2, 3)], [0.12, 0.12, 0.12])])
    fx("FxObjRune", [("Charge", [rune_charge(f) for f in range(5)], [0.14] * 5),
                     ("Burst", [rune_burst(f) for f in range(6)], [0.05, 0.05, 0.06, 0.07, 0.08, 0.1])])
    fx("FxObjToll", [("Wave", [toll_wave(f) for f in range(6)], [0.05, 0.06, 0.06, 0.07, 0.08, 0.1])])
    fx("FxObjDart", [("Fly", [dart_fly(f) for f in range(2)], [0.08, 0.08])])
    fx("FxObjWarp", [("Flash", [warp_flash(f) for f in range(6)], [0.04, 0.05, 0.06, 0.07, 0.08, 0.1])])
    fx("FxObjUrn", [("Burst", [urn_burst(f) for f in range(6)], [0.05, 0.06, 0.07, 0.08, 0.1, 0.12])])
    fx("FxObjMimic", [("Coins", [mimic_coins(f) for f in range(6)], [0.06] * 6)])
    fx("FxObjIndCurse", [("Loop", [ind_curse(f) for f in range(6)], [0.12] * 6)])
    fx("FxObjIndWard", [("Loop", [ind_ward(f) for f in range(6)], [0.1] * 6)])


TIMING_NOTES = {
    "ObjChainHook": "Action: hook released on frame 1 (AnimAttack), from the node (0, 7) at floor level (offset y -7.5).",
    "ObjSteamVent": "Action: jet on frame 1, at the grate's mouth on the floor (node 0,7 / offset 4, -7.5).",
    "ObjTarSpout": "Action: glob on frame 1 from the spout, launched along the floor (offset 6, -7.5).",
    "ObjPendulum": "SwingL / SwingR: blade passes the bottom on frame 3: the invisible floor hitbox (24 x 8) fires there.",
    "ObjRunePlate": "Action: the charge effect spawns on frame 0 at the plate centre (offset 0, -7.5); it bursts 0.7 s later.",
    "ObjTollBell": "Action: the toll wave spawns on frame 1 at the bell's foot (offset 0, -7.5).",
    "ObjScatterIdol": "Action: three darts on frame 2 from the mouth, along the floor (offset 3, -7.5), angles -16 / 0 / +16.",
    "ObjIronSnare": "Snap -> Sprung (held 6 s by code) -> Reset -> Idle.",
    "ObjStrongbox": "Use (coins) or Bite (mimic) -> Spent.",
    "FxObjHook": "Fly: centred on the effect origin (rotates with the flight). Yank: centred on the hero's body.",
    "FxObjSteam": "Blast: origin = the vent mouth on the floor; jet runs +x, rotates with the aim. Damage frames 1-4.",
    "FxObjTar": "Fly: centred. Pool: origin = puddle centre (Strike.Ground), slow zone live from frame 1 to the Fade.",
    "FxObjRune": "Charge (0.7 s, inert) then Burst: origin = plate centre; damage frames 1-3, 36 x 16 footprint.",
    "FxObjToll": "Wave: origin = bell foot; damage + daze frames 1-4, 60 x 28 footprint.",
    "FxObjWarp": "Flash: origin = the stone's floor point.",
    "FxObjIndCurse": "head indicator (offset 1), FxObjIndWard: feet indicator (offset -2).",
}


def timing():
    lines = ["# Objects (part one) timing", "", "Generated by tools/sprites/objects_rigs.py. Feet = the sheet pixel that sits on",
             "the object's floor point / the effect origin (x right, y down, from the cell's top-left).", ""]
    for name, img, man in SHEETS:
        fx_, fy = FEET[name]
        lines.append("## %s  (cell %dx%d, feet %d,%d)" % (name, man["cellW"], man["cellH"], fx_, fy))
        for a in man["anims"]:
            lines.append("- %s: %d frames, %s s" % (a["name"], len(a["frames"]), " ".join("%.3g" % d for d in a["durations"])))
        if name in TIMING_NOTES:
            lines.append("- " + TIMING_NOTES[name])
        lines.append("")
    open(os.path.join(OUT, "TIMING.md"), "w").write("\n".join(lines))


def main():
    global OUT
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
        args = [a for a in args if a != sys.argv[sys.argv.index("--only") + 1]]
    OUT = args[0] if args else DEFAULT_OUT
    os.makedirs(OUT, exist_ok=True)
    for name, fn in BUILDS.items():
        if only and name not in only: continue
        fn()
    if not only:
        timing()


if __name__ == "__main__":
    main()
