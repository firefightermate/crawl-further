"""Room objects, part two: the fun and secret objects of Crawl: Further and every effect sheet they use.

    python3 tools/sprites/objects2_rigs.py [outdir] [--only Name,Name]      (default art/out_objects2)

Drawn with the object kit of objects_rigs.py (the jinx_v2_rigs.py material renderer): top-left light, three tones per
material, bottom edges in the material's darkest tone, no black ring. Party accents (pink, cyan, gold, lime, violet)
sit on earthy dungeon materials so the objects still belong on a crypt floor.

Object sheets follow ObjectKit (src/CrawlFurther.Core/Objects/ObjectKit.cs): floor point at (cellW//2, cellH-2);
"Idle" loops, "Use" plays once on use, "Spent" loops once used up, "Vault" is the vault / secrets picture, any other
anim is a custom state. Effect sheets keep the cell and origin pixel ObjectPack2.cs pins them by (FX_CELLS), and the
anchor points the code uses (ANCHORS, also written to TIMING.md) are drawn where they always were.

  ObjBJukebox        arched music cabinet, bubble-tube arch, brass horn, crank       Idle 4, Use 6, Vault
  ObjBDiscoBall      mirror ball on a chain over its floor point                      Idle 4, Spin 4, Vault
  ObjBPinata         striped papier-mache goat on a rope                              Idle 4, Hit 3, Torn1 4, Torn2 4, Burst 6, Broken, Vault
  ObjBConfettiCannon striped party cannon on a wheeled carriage, pull tassel          Idle 4, Use 7, Spent 2, Vault
  ObjBSlotMachine    one-armed bandit with a crowned skull crest and three reels     Idle 4, Use 8, Win 4, Spent 2, Vault
  ObjBFortuneTeller  booth with a veiled skull mystic and a crystal ball             Idle 4, Use 7, Spent 2, Vault
  ObjBBounceShroom   big springy spotted mushroom with a happy face                   Idle 4, Use 6, Vault
  ObjBFireworkCrate  crate of striped rockets with a fuse                             Idle 2, Lit 4, Launch 4, Spent, Vault
  ObjBLeverTrio      stone console with three lever slots and glyph plaques          Idle, Buzz 3, Jam, Vault
  ObjBHatch          floor hatch the lever puzzle opens                               Idle, Use 5, Spent, Vault
  ObjBCrackedWall    brick wall section with a hairline crack, a niche behind        Idle, Crack1-3, Hit 2, Crumble 7, Spent, Vault
  ObjBKeyhole        stone slab with an ornate keyhole                                Idle 4, Locked 3, Unlock 8, Spent, Vault
  ObjBReliquary      golden reliquary the keyhole reveals                             Rise 5, Idle 4, Use 5, Spent, Vault
  ObjBSculptorAltar  altar with hammer, chisel and an empty plinth                    Idle 4, Use 8, Spent, Vault
  ObjBWishingWell    round stone well, little roof, bucket                            Idle 4, Use 5, Wish 6, Vault
  ObjBPortrait       cabinet whose door is a gilt portrait; the eyes follow you      Idle, EyesL, EyesR, Wink 5, Swing 6, Spent, Vault
  ObjBGoldenDuck     a tiny golden rubber duck                                        Idle 4, Use 4, Vault
  FX: FxObjBDanceTile, FxObjBSlotSymbols, FxObjBLever, FxObjBGlyphs, FxObjBNotes, FxObjBConfetti (Burst, Rain, Gold),
      FxObjBConfettiBlast, FxObjBRocket, FxObjBFirework (Pink, Gold, Cyan, Lime), FxObjBSpores, FxObjBCoins,
      FxObjBWellSpirit, FxObjBCard, FxObjBSparkle, FxObjBDust, FxObjBJackpot, FxObjBStatueForm,
      FxObjBInd (head indicators: Groove1-4, Hat), FxObjBIndFever (feet indicator).
"""
import math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)
import objects_rigs as K                      # noqa: E402  (object kit + material renderer)
from objects_rigs import Fr, Px, block, drum, rows, rot_rows, hcyl, moss, chainline, lam  # noqa: E402
from jinx_v2_rigs import RAMPS, EMISSIVE, SHINY, line_px, poly_px  # noqa: E402
from anim import Spr, PALETTE                 # noqa: E402

DEFAULT_OUT = os.path.join(ROOT, "art", "out_objects2")


def _h(s):
    s = s.lstrip("#"); return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


PARTY = {
    # party colours pulled into Crawl's grimy prop palette: faded and darkened toward its browns, never pure hues
    "ppink":  ["2e1418", "5a2a30", "844246", "a45e58", "c08676"],     # dusty rose
    "pcyan":  ["141e1e", "2a3e3a", "445e56", "608072", "86a292"],     # washed-out teal
    "plime":  ["1a1e10", "343e1e", "52602e", "707e40", "929c5c"],     # moss olive
    "pyel":   ["2a1e0c", "584020", "866632", "a88644", "c6aa6c"],     # faded mustard
    "pviol":  ["1e1420", "3a2a3a", "584254", "765c6c", "967e88"],     # dusty plum
    "cream":  ["382e26", "6a5e4c", "968a70", "b6a888", "d0c4a2"],     # sun-bleached cream
    "mirror": ["1c2028", "424a58", "6e7886", "a2aab2", "dadcd8"],     # tarnished mirror
    "mush":   ["241418", "4a2c30", "6e4446", "8c5e5a", "aa7e72"],     # mauve cap
    "dwood":  ["1a0e0c", "3a1e16", "5a3020", "7a4428", "9a5e36"],     # varnished cabinet wood
    "paper":  ["3a3026", "7c6c56", "aa9a7c", "c8b898", "e0d4b4"],     # card stock
    "kraft":  ["241810", "48321e", "6a4e30", "8a6a44", "a8885e"],     # bare brown paper under the tissue
    "ogold":  ["2a1a0c", "5c4018", "86662c", "aa8a40", "ccb068"],     # old tarnished gilt
}
RAMPS.update({k: [_h(c) for c in v] for k, v in PARTY.items()})
for k in ("ppink", "pcyan", "plime", "pyel", "pviol"):
    RAMPS["l" + k[1:]] = RAMPS[k]                 # lpink, lcyan, llime, lyel, lviol: the same colours, lit from within
EMISSIVE.update({"lpink", "lcyan", "llime", "lyel", "lviol"})
SHINY.update({"mirror", "dwood", "ogold"})
LIGHTS = ("lpink", "lcyan", "lyel", "llime")
PAPERS = ("ppink", "pcyan", "pyel", "plime", "pviol")

# palette characters for the few particle effects that are still drawn as palette sprites (confetti, fireworks...)
PALETTE.update({
    'Ж': (0xff, 0x5f, 0xa8), 'ж': (0xb4, 0x36, 0x76), 'Ц': (0x56, 0xd8, 0xea), 'ц': (0x2a, 0x88, 0xa6),
    'Л': (0xa4, 0xec, 0x5a), 'л': (0x4e, 0x9c, 0x34), 'Ф': (0xa8, 0x78, 0xf0), 'ф': (0x5e, 0x3c, 0xa4),
    'Д': (0x9a, 0x98, 0xa0), 'д': (0xc4, 0xc2, 0xc6), 'Э': (0xff, 0xff, 0xf0), 'Р': (0xe0, 0x80, 0xc8),
    'р': (0x96, 0x46, 0x8e), 'С': (0xf4, 0xe6, 0xd8), 'Ч': (0x2c, 0x22, 0x36),
})


def gl(fr, x, y, mat, tone, a=255):
    fr.glow(x, y, mat, tone, a)


# ================================================================== sheets
SHEETS = []          # (name, kind) in build order
REGISTRY = {}
BUILT = {}


def obj(name):
    def deco(fn):
        REGISTRY[name] = fn
        return fn
    return deco


def osheet(name, anims):
    assert any(a[0] == "Vault" for a in anims), name
    img, man = K.emit(name, anims)
    BUILT[name] = {"cell": (man["cellW"], man["cellH"]), "anims": [(a, len(f), list(d)) for a, f, d in anims]}
    SHEETS.append((name, "obj"))


FX_CELLS = {   # sheet: (cell, origin pixel) as ObjectPack2.cs pins them
    "FxObjBDanceTile": ((18, 12), (9, 6)), "FxObjBSlotSymbols": ((8, 8), (4, 4)), "FxObjBLever": ((20, 11), (10, 9)),
    "FxObjBGlyphs": ((8, 6), (4, 3)), "FxObjBNotes": ((26, 29), (13, 26)), "FxObjBConfetti": ((76, 58), (38, 31)),
    "FxObjBConfettiBlast": ((94, 34), (47, 22)), "FxObjBRocket": ((28, 5), (14, 3)), "FxObjBFirework": ((34, 31), (17, 24)),
    "FxObjBSpores": ((26, 13), (13, 11)), "FxObjBCoins": ((48, 16), (24, 15)), "FxObjBWellSpirit": ((40, 36), (20, 35)),
    "FxObjBCard": ((12, 26), (6, 25)), "FxObjBSparkle": ((28, 26), (14, 21)), "FxObjBDust": ((40, 11), (20, 10)),
    "FxObjBJackpot": ((56, 34), (28, 29)), "FxObjBStatueForm": ((16, 26), (8, 25)), "FxObjBInd": ((20, 11), (10, 9)),
    "FxObjBIndFever": ((20, 11), (10, 9)),
}


def fxsheet(name, anims):
    cell, origin = FX_CELLS[name]
    img, man = K.emit(name, anims, cell, feet=origin)
    BUILT[name] = {"cell": cell, "anims": [(a, len(f), list(d)) for a, f, d in anims]}
    SHEETS.append((name, "fx"))


def pal(px):
    """A palette-character sprite (the particle effects) as a finished frame."""
    return Px({k: PALETTE[c] + (255,) for k, c in px.items() if PALETTE.get(c)})


# ================================================================== 1. JUKEBOX
HORN = (8, -34)          # horn mouth: FxObjBNotes spawn point


def jukebox(phase=0, crank=90.0, bounce=0, flash=False, horn=0, lights=True):
    """An arched varnished cabinet with bubble-tube lights, a spinning record behind glass, a brass grille and horn."""
    fr = Fr((0, 12, 1.6)); r = fr.r
    by = bounce
    block(r, -12, 11, -4, 0, "dwood", 0.0, top=1)
    for x in range(-9, 10, 3):
        r.dot(x, -2, "brass", 2, 0.01)
    top = -25 + by
    # cabinet body and arched crown
    block(r, -10, 9, top + 7, -5, "dwood", 0.1, top=0, curve=0.6)
    r.ell(-0.5, top + 8, 10.0, 8.6, "dwood", 0.09, clip=lambda x, y: y <= top + 8)
    # bubble-tube arch and side tubes, lit in a chase
    lp = r.part(True, 0.2)
    for i in range(30):
        a = math.pi + i * math.pi / 29
        x, y = -0.5 + 7.2 * math.cos(a), top + 8 + 6.4 * math.sin(a)
        k = (i // 3 + phase) % 4
        on = lights and ((i // 3 + phase) % 2 == 0 or flash)
        if on: gl(fr, x, y, LIGHTS[k], 3 if i % 3 else 4)
        else: r.put(x, y, 0.2, "p" + LIGHTS[k][1:], 0.5, lp, 1)
    for y in range(top + 8, -5):
        k = ((y // 2) + phase) % 4
        on = lights and (((y // 2) + phase) % 2 == 0 or flash)
        for x, kk in ((-8, k), (7, (k + 2) % 4)):
            mat = LIGHTS[kk]
            if on: gl(fr, x, y, mat, 3)
            else: r.put(x, y, 0.2, "p" + mat[1:], 0.5, lp, 1)
    # record window: a dark arch with the disc spinning in it
    r.ell(-0.5, top + 9, 4.6, 3.6, "glassd", 0.25, flat=1)
    r.ell(-0.5, top + 10, 3.6, 1.6, "tar", 0.26, flat=1)
    sp = [(-2, 0), (-1, -1), (1, -1), (2, 0)][phase % 4]
    r.dot(-0.5 + sp[0], top + 10 + sp[1], "tar", 4, 0.27)
    r.dot(-1, top + 10, "velvet", 3, 0.27); r.dot(0, top + 10, "velvet", 2, 0.27)
    gl(fr, -4, top + 7, "gleam", 2, 180)
    # brass band, grille, buttons
    block(r, -7, 6, top + 13, top + 14, "brass", 0.3, top=1)
    block(r, -6, 5, top + 15, -8, "tar", 0.25, top=0)
    for x in range(-5, 5, 2):
        for y in range(top + 16, -8):
            r.dot(x, y, "brass", 3 if y < top + 18 else 2, 0.26)
    r.dot(-4, -6, "tar", 0, 0.3); r.dot(-3, -6, "tar", 0, 0.3)
    gl(fr, 1, -6, "blood", 3); gl(fr, 3, -6, "lcyan", 3)
    # horn on top, mouth at HORN
    hb = top - 1
    r.tube([(1, hb + 2), (3, hb - 2), (6, hb - 5)], [1.2, 1.4, 1.9], "brass", 0.4)
    hx, hy = HORN[0] + (1 if horn else 0), HORN[1] + by + 1
    r.ell(hx, hy, 3.0 + horn * 0.5, 3.4 + horn * 0.5, "brass", 0.42, ang=-35)
    r.ell(hx + 0.8, hy - 0.6, 1.5, 1.9, "tar", 0.43, ang=-35, flat=0)
    # crank on the right side
    cx, cy = 10, -12 + by // 2
    r.ell(9.5, cy, 1.0, 1.2, "iron", 0.3)
    ex, ey = cx + 3 * math.cos(math.radians(crank)), cy + 3 * math.sin(math.radians(crank))
    r.tube([(cx, cy), (ex, ey)], [0.6, 0.6], "iron", 0.31)
    r.ell(ex, ey, 1.0, 1.0, "velvet", 0.32)
    if flash:
        fr.spark(hx + 2, hy - 2, "gleam", 1)
    return fr.done()


@obj("ObjBJukebox")
def build_jukebox():
    idle = [jukebox(phase=i) for i in range(4)]
    play = [jukebox(phase=i, crank=90 + 60 * i, bounce=[1, 0, 1, 0, 1, 0][i], flash=(i % 2 == 0), horn=(i + 1) % 2)
            for i in range(6)]
    osheet("ObjBJukebox", [("Idle", idle, [0.18] * 4), ("Use", play, [0.08] * 6),
                           ("Vault", [jukebox(phase=0, flash=True)], [0.2])])


# ================================================================== 2. DISCO BALL + DANCE FLOOR
BALL = (0.0, -27.0)      # ball centre (code anchor)


def disco_ball(spin=0, fast=False, swing=0.0):
    """A mirror ball of little square facets on a chain; glints cycle as it turns."""
    fr = Fr((0, 5, 1.2)); r = fr.r
    cx, cy, R = BALL[0] + swing, BALL[1], 8.6
    cp = r.part(True, 0.1)
    for y in range(-44, int(cy - R)):
        x = swing * (y + 44) / 17.0
        r.put(x, y, 0.1, "iron", 0.5, cp, 3 if y % 2 else 1)
    r.ell(cx, cy - R - 0.5, 1.6, 1.0, "brass", 0.2)
    rnd = random.Random(7)
    hashes = {}
    bp = r.part(False, 0.3)
    turn = spin * (2 if fast else 1) * 0.5
    glints = []
    for y in range(int(cy - R) - 1, int(cy + R) + 2):
        for x in range(int(cx - R) - 1, int(cx + R) + 2):
            dx, dy = (x - cx) / R, (y - cy) / R
            d = dx * dx + dy * dy
            if d > 1.0: continue
            lat = math.asin(max(-1, min(1, dy)))
            lon = math.asin(max(-1, min(1, dx / max(0.2, math.cos(lat)))))
            fu = (lon + math.pi / 2) / (math.pi / 6) + turn
            fv = (lat + math.pi / 2) / (math.pi / 7)
            key = (int(fu) % 12, int(fv))
            if key not in hashes: hashes[key] = rnd.random()
            h = hashes[key]
            l = lam(dx, dy, math.sqrt(max(0, 1 - d)))
            tone = 2 if l < 0.45 else 3
            if h > 0.75 and tone < 4: tone += 1
            if h < 0.2 and tone > 1: tone -= 1
            if (fu % 1.0) < 0.2 or (fv % 1.0) < 0.22: tone = min(tone, 2) - 1
            r.put(x, y, 0.3, "mirror", 0.5, bp, max(1, tone))
            if h > 0.88 and (fu % 1.0) > 0.3 and (fv % 1.0) > 0.3 and l > 0.1: glints.append((x, y, h))
    for (x, y, h) in glints:
        if fast: gl(fr, x, y, LIGHTS[int(h * 100 + spin) % 4], 4)
        else: gl(fr, x, y, "gleam", 4)
    # the specular glint travels across the lit side as the ball turns
    ga = math.radians(205 + (spin % 4) * (22 if fast else 9))
    gx, gy = cx + R * 0.62 * math.cos(ga), cy + R * 0.62 * math.sin(ga)
    fr.spark(int(round(gx)), int(round(gy)), "gleam", 2 if fast and spin % 2 == 0 else 1)
    n = 8 if fast else 4
    for k in range(n):                                                             # coloured light flecks thrown off it
        a = spin * (0.9 if fast else 0.35) + k * 2 * math.pi / n
        rr = 12 + (k % 3) * 2
        gl(fr, cx + rr * math.cos(a), cy + 6 + rr * 0.7 * math.sin(a), LIGHTS[(k + spin) % 4], 4)
        if fast and k % 2 == 0: gl(fr, cx + rr * math.cos(a) + 1, cy + 6 + rr * 0.7 * math.sin(a), LIGHTS[(k + spin) % 4], 2)
    return fr.done()


def dance_tile(col=None, beat=0):
    """One dance-floor tile, 13 x 9, centred on its origin: a glass square lit from below in one colour."""
    fr = Fr()
    W, H = 6, 4
    for y in range(-H, H + 1):
        for x in range(-W, W + 1):
            edge = abs(x) == W or abs(y) == H
            if col is None:
                tone = 1 if edge else (0 if (x + y) % 4 else 1)
                gl(fr, x, y, "glassd", tone)
                continue
            d = max(abs(x) / float(W), abs(y) / float(H))
            tone = 1 if edge else (3 if d < 0.45 else 2)
            if beat and d < 0.3: tone = 4
            gl(fr, x, y, col, tone)
    if col is not None:
        for (x, y) in ((-W + 1, -H + 1), (-W + 2, -H + 1), (-W + 1, -H + 2)):
            gl(fr, x, y, col, 4)
        if beat == 2:
            for x in range(-W - 1, W + 2):
                gl(fr, x, -H - 1, col, 2); gl(fr, x, H + 1, col, 2)
    else:
        gl(fr, -W + 1, -H + 1, "glassd", 3); gl(fr, -W + 2, -H + 1, "glassd", 3)
    return fr.done(floor=False)


TILE_COLS = {"Pink": "lpink", "Cyan": "lcyan", "Gold": "lyel", "Lime": "llime"}


@obj("ObjBDiscoBall")
def build_disco():
    idle = [disco_ball(spin=i, swing=[0, 0.5, 0, -0.5][i]) for i in range(4)]
    spin = [disco_ball(spin=i, fast=True) for i in range(4)]
    osheet("ObjBDiscoBall", [("Idle", idle, [0.2] * 4), ("Spin", spin, [0.09] * 4),
                             ("Vault", [disco_ball(spin=1, fast=True)], [0.2])])
    anims = [("Off", [dance_tile(None)], [0.2])]
    for n, c in TILE_COLS.items():
        anims.append((n, [dance_tile(c), dance_tile(c, beat=1)], [0.25, 0.25]))
    anims.append(("Beat", [dance_tile("lpink", beat=2), dance_tile("lcyan", beat=1), dance_tile("lyel")], [0.06, 0.06, 0.08]))
    fxsheet("FxObjBDanceTile", anims)


# ================================================================== 3. PINATA
PIVOT = (0, -46)         # the rope's top
HOLES1 = [(-3, -1), (-2, -1), (-1, -1), (-3, 0), (-2, 0), (-1, 0), (-2, 1)]
HOLES2 = [(3, 1), (4, 1), (5, 1), (3, 2), (4, 2), (5, 2), (-7, 1), (-6, 1), (-6, 2)]
TISSUE = ("ppink", "pyel", "pcyan", "ppink", "cream")


def pinata(dx=0, lean=0, trail=0, squash=0, torn=0, eye=1):
    """A battered papier-mache donkey that has hung in the dungeon for years: faded tissue fringe in torn, uneven rows
    (dusty rose, mustard, teal, bleached cream), bare brown paper where tufts have gone, a stitched seam, a frayed rope,
    one button eye, one stitched shut, and a crooked grin. Swing frames are posed: dx moves it along the rope's arc,
    lean slants its rows, trail drags the legs and tail behind."""
    fr = Fr((dx * 0.5, 8, 1.4)); r = fr.r
    rnd = random.Random(17)
    cy, rx, ry = -24, 9.0, 5.5 - squash * 0.6
    top = int(round(cy - ry))
    # frayed rope with a knot and two loose strands
    for i, (x, y) in enumerate(line_px(PIVOT[0], PIVOT[1], dx, top - 1)):
        r.dot(x, y, "rope", 2 if i % 3 else 1, 0.05)
    r.dot(dx - 1, top - 1, "rope", 3, 0.06); r.dot(dx + 1, top - 1, "rope", 2, 0.06)
    r.dot(dx + 1, top - 3, "rope", 1, 0.06); r.dot(dx + 2, top - 2, "rope", 1, 0.06)
    holes = set()
    if torn >= 1: holes |= set(HOLES1)
    if torn >= 2: holes |= set(HOLES2)
    edge = [rnd.randint(0, 1) for _ in range(30)]           # uneven band edges, per column
    bare = {(-6, -2), (-5, -2), (-5, -3), (-4, -2), (3, 1), (4, 1), (4, 0)}   # tufts torn away down to the brown paper
    grime = {(rnd.randint(-8, 8), rnd.randint(-4, 4)) for _ in range(6)}
    bp = r.part(True, 0.3)

    def sh(y):
        return int(round(lean * (cy - y) / ry))

    def tissue(row, x, u, ky):
        """Tone of a fringe pixel, 4 rows per band: a frilled lit lip, the band face, the shadow under the next band."""
        t = (3 if (x + ky) % 2 else 2) if row == 0 else 1 if row == 3 else 2
        if u < -0.45 and row in (1, 2): t = 3
        if u > 0.55: t -= 1
        return max(1, min(3, t))

    for y in range(top, int(cy + ry) + 1):
        for x in range(-10, 11):
            u, v = x / (rx + 0.4 * squash), (y - cy) / ry
            if u * u + v * v > 1.0: continue
            X = x + dx + sh(y)
            lx, ly = x, y - cy
            if (lx, ly) in holes:
                r.put(X, y, 0.3, "kraft" if (lx + ly) % 4 == 0 else "tar", 0.5, bp, 1 if (lx + ly) % 4 == 0 else 0)
                continue
            k = y - top + edge[x + 10]
            band, row = k // 4, k % 4
            m = TISSUE[band % len(TISSUE)]
            t = tissue(row, x, u, band)
            if (lx, ly) in bare: m, t = "kraft", 2
            if (lx, ly) in grime: t = max(0, t - 1)
            r.put(X, y, 0.3, m, 0.5, bp, t)
    for x in range(-8, 9):                                     # torn hanging fringe under the belly, uneven
        if rnd.random() < 0.6:
            y = int(round(cy + ry)) + 1
            r.put(x + dx + sh(y), y, 0.31, TISSUE[(x + 9) % len(TISSUE)], 0.5, bp, 1)
            if rnd.random() < 0.3: r.put(x + dx + sh(y), y + 1, 0.31, "kraft", 0.5, bp, 1)
    for y in range(top + 1, int(cy + ry)):                      # the stitched seam behind the shoulder
        r.put(5 + dx + sh(y), y, 0.33, "kraft", 0.5, bp, 0 if y % 2 else 2)
        if y % 2: r.put(4 + dx + sh(y), y, 0.33, "rope", 0.5, bp, 1)
    # legs: short stubby tubes of tissue over card, scuffed cream hooves, dragging behind the swing
    for li, lx in enumerate((-7, -3, 2, 6)):
        for k, y in enumerate(range(-19, -13)):
            off = int(round(trail * k / 5.0))
            for w in range(3):
                X = lx - 1 + w + dx + off + sh(-19)
                if y == -14: r.put(X, y, 0.25, "kraft", 0.5, bp, 1 if w else 2)                # scuffed hooves
                else: r.put(X, y, 0.25, "pyel" if li % 2 else "pcyan", 0.5, bp, 3 if w == 0 else 2 if w == 1 else 1)
    # a scraggly tail tuft
    for i, (x, y) in enumerate([(-10, -26), (-11, -27), (-12, -27), (-12, -26), (-13, -25)]):
        r.put(x + dx + sh(y) + int(round(trail * 0.5)), y, 0.32, "ppink" if i % 2 else "kraft", 0.5, bp, 2 if i < 2 else 1)
    # neck and head, the donkey's long face hanging a little low
    hx = dx + sh(-30)
    for y in range(-34, -27):
        k = -27 - y
        for w in range(3):
            r.put(hx + 6 + k // 2 + w, y, 0.35, "pcyan", 0.5, bp, tissue(y % 3, w, (w - 1) / 1.5, 0))
        r.put(hx + 5 + k // 2, y, 0.36, "ppink", 0.5, bp, 2 if y % 2 else 1)              # ragged mane
    for y in range(-38, -31):
        for x in range(7, 17):
            u, v = (x - 11.5) / 5.0, (y + 34.8) / 3.3
            if u * u + v * v > 1.0: continue
            t = 3 if (u + v < -0.5) else 1 if (u > 0.5 or v > 0.6) else 2
            r.put(hx + x, y, 0.4, "pyel", 0.5, bp, t)
    for y in range(-36, -31):
        for x in range(15, 19):
            if (x, y) in ((18, -36), (18, -32)): continue
            r.put(hx + x, y, 0.42, "cream", 0.5, bp, 3 if y == -36 else 1 if y == -32 or x == 18 else 2)   # grubby muzzle
    for (x, y) in ((13, -33), (14, -32), (15, -32), (16, -32), (17, -33)):                  # the crooked grin
        r.put(hx + x, y, 0.43, "tar", 0.5, bp, 0)
    r.put(hx + 15, -33, 0.44, "bone", 0.5, bp, 3)                                            # one yellowed tooth
    r.put(hx + 17, -35, 0.43, "tar", 0.5, bp, 0)
    for k in range(5):                                                                       # one ear up, one torn and flopped
        r.put(hx + 9 - k // 3, -38 - k, 0.38, "pyel", 0.5, bp, 3)
        r.put(hx + 10 - k // 3, -38 - k, 0.38, "ppink" if 0 < k < 4 else "pyel", 0.5, bp, 2)
        r.put(hx + 11 - k // 3, -38 - k, 0.38, "pyel", 0.5, bp, 1)
    for (x, y, t) in ((12, -38, 2), (13, -39, 2), (14, -39, 1), (15, -38, 1), (13, -38, 1), (14, -38, 1)):
        r.put(hx + x, y, 0.38, "pyel", 0.5, bp, t)
    if eye == 2:
        for (ex, ey) in ((10, -36), (11, -35), (12, -36)): r.put(hx + ex, ey, 0.45, "tar", 0.5, bp, 0)
    else:
        r.put(hx + 10, -36, 0.45, "tar", 0.5, bp, 0); r.put(hx + 11, -36, 0.45, "tar", 0.5, bp, 0)
        r.put(hx + 10, -35, 0.45, "tar", 0.5, bp, 0)
        fr.glow(hx + 11, -35, "blood", 2)                                                     # a dull red glint in the button eye
    r.put(hx + 13, -36, 0.45, "tar", 0.5, bp, 1); r.put(hx + 14, -35, 0.45, "tar", 0.5, bp, 1)  # the other eye stitched shut
    r.put(hx + 14, -36, 0.45, "tar", 0.5, bp, 1); r.put(hx + 13, -35, 0.45, "tar", 0.5, bp, 1)
    return fr.done()


def pinata_pieces(t):
    """Burst frames: paper scraps and treats fly out and fall, the rope swings empty."""
    fr = Fr((0, 9 - t, 1.3)); r = fr.r
    rnd = random.Random(11)
    end = (int(round(2 * math.sin(t))), -31 + t)
    for i, (x, y) in enumerate(line_px(PIVOT[0], PIVOT[1], end[0], end[1])):
        r.dot(x, y, "rope", 3 if i % 2 else 2, 0.05)
    for k in range(26):
        a = rnd.uniform(0, 2 * math.pi); sp = rnd.uniform(3, 6)
        x = math.cos(a) * sp * (t + 1)
        y = -24 + math.sin(a) * sp * (t + 1) * 0.7 + 0.9 * (t + 1) ** 2
        if y > -1: y = -1 - (k % 2)
        m = TISSUE[k % len(TISSUE)]
        r.dot(x, y, m, 3 if (k + t) % 2 else 2, 0.2)
        r.dot(x + 1, y, m, 1, 0.2)
        if k % 3 == 0: r.dot(x, y + 1, m, 1, 0.2)
    return fr.done()


def broken_pinata():
    fr = Fr(); r = fr.r
    for i, (x, y) in enumerate(line_px(PIVOT[0], PIVOT[1], 0, -31)):
        r.dot(x, y, "rope", 3 if i % 2 else 2, 0.05)
    for (x, y, m, t) in [(0, -30, "ppink", 3), (-1, -29, "kraft", 2), (1, -29, "pyel", 2), (0, -28, "pcyan", 2), (0, -27, "pcyan", 1)]:
        r.dot(x, y, m, t, 0.2)
    for (x, y, m, t) in [(-6, 0, "ppink", 3), (-5, 0, "ppink", 1), (4, 0, "pcyan", 3), (5, -1, "pyel", 3), (8, 0, "plime", 3),
                         (-9, 0, "pviol", 3), (1, 0, "pyel", 2), (-2, 0, "plime", 2), (10, 0, "ppink", 2), (-11, -1, "pcyan", 3)]:
        r.dot(x, y, m, t, 0.1)
    return fr.done()


@obj("ObjBPinata")
def build_pinata():
    sway = [dict(dx=0, lean=0, trail=0), dict(dx=1, lean=1, trail=-1), dict(dx=0, lean=0, trail=0), dict(dx=-1, lean=-1, trail=1)]
    idle = [pinata(**k) for k in sway]
    hit = [pinata(dx=-4, lean=-1, trail=3, squash=1, eye=2), pinata(dx=3, lean=1, trail=-2), pinata(dx=-1, lean=0, trail=1)]
    t1 = [pinata(torn=1, **k) for k in sway]
    t2 = [pinata(torn=2, **k) for k in sway]
    burst = [pinata(dx=-3, lean=-1, trail=2, torn=2, squash=2, eye=2)] + [pinata_pieces(t) for t in range(5)]
    osheet("ObjBPinata", [("Idle", idle, [0.24] * 4), ("Hit", hit, [0.06, 0.1, 0.12]), ("Torn1", t1, [0.24] * 4),
                          ("Torn2", t2, [0.24] * 4), ("Burst", burst, [0.05, 0.06, 0.07, 0.08, 0.1, 0.12]),
                          ("Broken", [broken_pinata()], [0.2]), ("Vault", [pinata(dx=1, lean=1, trail=-1)], [0.2])])


# ================================================================== 4. CONFETTI CANNON
MUZZLE = (11, -9)        # code anchor: the blast origin (its art runs 6 px above it, at the barrel mouth)


def cannon(recoil=0.0, elev=-22.0, tassel=0.0, flash=0, spent=False, smoke=0):
    """A striped party cannon on a timber carriage with a spoked wheel and a pull tassel."""
    fr = Fr((0, 13, 1.6)); r = fr.r
    r.poly([(-13, -1), (-12, -8), (5, -10), (9, -3), (9, 0), (-13, 0)], "plank", 0.0, normal=(-0.15, -0.2, 1.0))
    r.polyline([(-10, -6), (5, -8)], "plank", 0.01, tone=3)
    for x in (-8, -2, 4):
        r.dot(x, -4, "iron", 3, 0.02)
    px_, py_ = -3.0 - recoil, -10.0
    a = math.radians(elev); ca, sa = math.cos(a), math.sin(a)
    L = 15
    bp = r.part(False, 0.3)
    for i in range(-3, L + 1):
        bx, by = px_ + i * ca, py_ + i * sa
        rad = 4.0 if i < 0 else 3.5 - 0.02 * i
        if i >= L - 1: rad = 4.2
        for k in range(-8, 9):
            o = k * 0.5
            if abs(o) > rad: continue
            X, Y = bx - sa * o, by + ca * o
            v = o / rad
            if i >= L - 1 or i < -1: m = "brass"
            elif spent: m = "iron"
            else: m = "ppink" if (i // 3) % 2 else "pcyan"
            nz = math.sqrt(max(0.0, 1 - v * v))
            r.put(X, Y, 0.3, m, lam(-sa * v, ca * v, nz), bp)
            r.put(X + 0.5, Y, 0.3, m, lam(-sa * v, ca * v, nz), bp)
    mx, my = px_ + (L + 0.6) * ca, py_ + (L + 0.6) * sa
    r.ell(mx, my, 1.0, 2.6, "tar", 0.35, ang=elev, flat=0)
    # spoked wheel in front of the carriage
    wp = r.part(False, 0.5)
    for y in range(-11, 1):
        for x in range(-7, 6):
            d = math.hypot(x + 1, y + 5)
            if d <= 5.2:
                if d > 3.9: r.put(x, y, 0.5, "plank", lam((x + 1) / 5.2, (y + 5) / 5.2, 0.5), wp)
                else: r.put(x, y, 0.5, "plank", 0.5, wp, 0)
    for k in range(4):
        aa = math.radians(45 * k + recoil * 25)
        r.line(-1 - 3.6 * math.cos(aa), -5 - 3.6 * math.sin(aa), -1 + 3.6 * math.cos(aa), -5 + 3.6 * math.sin(aa),
               "plank", 0.51, tone=3 if k % 2 else 2)
    r.ell(-1, -5, 1.2, 1.2, "brass", 0.52)
    # tassel on a cord from the breech
    tx, ty = px_ - 3 * ca, py_ - 3 * sa
    ex, ey = tx - 2 + tassel, ty + 6
    r.line(tx, ty, ex, ey, "velvet", 0.45, tone=3)
    r.dot(ex, ey + 1, "pyel", 4, 0.46); r.dot(ex - 1, ey + 1, "pyel", 2, 0.46); r.dot(ex, ey + 2, "pyel", 2, 0.46)
    if flash:
        rnd = random.Random(flash)
        for i in range(flash * 4):
            fx_, fy_ = mx + rnd.uniform(0, 4 + flash * 2), my + rnd.uniform(-3 - flash, 3)
            gl(fr, fx_, fy_, LIGHTS[i % 4] if i % 5 else "gleam", 4)
        fr.spark(int(round(mx + 2)), int(round(my)), "gleam", 1 + (flash > 2))
    for s in range(smoke):
        gl(fr, mx + 1 + s, my - 2 - s * 2, "smoke", 3 if s % 2 else 2, 200)
        gl(fr, mx + 2 + s, my - 3 - s * 2, "smoke", 2, 150)
    return fr.done()


@obj("ObjBConfettiCannon")
def build_cannon():
    idle = [cannon(tassel=t) for t in (0, 0.6, 1, 0.4)]
    fire = [cannon(tassel=1.5, elev=-20), cannon(recoil=0.5, tassel=2, elev=-19),
            cannon(recoil=3, elev=-30, flash=3), cannon(recoil=2.5, elev=-28, flash=2),
            cannon(recoil=1.5, elev=-25, flash=1, smoke=1), cannon(recoil=0.5, elev=-23, smoke=2), cannon(smoke=2)]
    spent = [cannon(spent=True, smoke=2), cannon(spent=True, smoke=1)]
    osheet("ObjBConfettiCannon", [("Idle", idle, [0.22] * 4), ("Use", fire, [0.18, 0.06, 0.05, 0.06, 0.08, 0.1, 0.12]),
                                  ("Spent", spent, [0.35, 0.35]), ("Vault", [cannon(flash=1)], [0.2])])


# ================================================================== 5. SLOT MACHINE
REEL_X = (-6, 0, 6)          # reel centres (x) from the floor point; y = REEL_Y (FxObjBSlotSymbols land here)
REEL_Y = -16
CREST = (0, -24)             # FxObjBJackpot spawn point


def slot_machine(bulbs=0, lever=0.0, blur=None, win=0, broken=False, shake=0):
    """A one-armed bandit: velvet-red cabinet in brass trim, a row of bulbs, three reels behind glass, a crowned skull
    crest and a pull lever with a red knob."""
    fr = Fr((0, 13, 1.6)); r = fr.r
    sx = shake
    block(r, -11 + sx, 10 + sx, -6, 0, "iron", 0.0, top=1)
    block(r, -5 + sx, 4 + sx, -4, -2, "tar", 0.05, top=0)                         # payout tray
    for x, m, t in ((-4, "pyel", 4), (-3, "pyel", 2), (-1, "pyel", 3), (1, "pyel", 4), (2, "pyel", 2)):
        if broken: r.dot(x + sx, -3, "tar", 2, 0.06)
        else: gl(fr, x + sx, -3, "gleam" if t == 4 else "brass", t)
    body = "iron" if broken else "velvet"
    block(r, -10 + sx, 9 + sx, -27, -6, body, 0.1, top=0, curve=0.5)
    block(r, -11 + sx, 10 + sx, -28, -27, "brass", 0.2, top=1)
    block(r, -11 + sx, 10 + sx, -8, -7, "brass", 0.2, top=1)
    for y in range(-26, -8):
        r.dot(-10 + sx, y, "brass", 3, 0.15); r.dot(9 + sx, y, "brass", 1, 0.15)
    for i, x in enumerate(range(-8, 9, 2)):
        on = (i + bulbs) % 2 == 0 and not broken
        if win: on = (win % 2 == 1) or i % 2 == 0
        if on: gl(fr, x + sx, -25, "lyel", 4); gl(fr, x + sx, -24, "lyel", 2, 160)
        else: r.dot(x + sx, -25, "brass", 1 if broken else 2, 0.2)
    # reel window
    block(r, -10 + sx, 9 + sx, -21, -11, "glassd", 0.25, top=0)
    for i, rx in enumerate(REEL_X):
        for y in range(-19, -12):
            for x in range(rx - 2, rx + 3):
                v = (y - REEL_Y) / 3.5
                tone = 3 if abs(v) < 0.45 else 2 if abs(v) < 0.85 else 1                # the drum curves away
                if blur is not None and not broken:
                    tone = [3, 2, 4, 2][(y + blur * 2 + i + (x % 2)) % 4]
                if broken: tone = 1 if (x + y) % 3 else 0
                r.dot(x + sx, y, "paper", tone, 0.26)
    gl(fr, -9 + sx, -20, "gleam", 4, 200); gl(fr, -8 + sx, -20, "gleam", 3, 120)
    for x in range(-8, 8):
        r.dot(x + sx, -10, "brass", 3 if x % 2 else 1, 0.27)
    # crest: a skull wearing a little crown
    r.ell(-0.5 + sx, -31, 3.8, 3.3, "bone", 0.3)
    r.ell(-0.5 + sx, -28.6, 2.2, 1.0, "bone", 0.31)
    for x in (-2, 1):
        if win: gl(fr, x + sx, -31, "lyel", 4)
        else: r.dot(x + sx, -31, "tar", 0, 0.32)
    r.dot(-1 + sx, -29, "tar", 1, 0.32); r.dot(0 + sx, -29, "tar", 1, 0.32)
    for x, y in ((-3, -36), (-1, -37), (2, -36), (-3, -35), (-2, -35), (-1, -35), (0, -35), (1, -35), (2, -35), (-1, -36), (0, -36)):
        r.dot(x + sx, y, "brass" if broken else "ogold", 3 if x < 0 else 2, 0.33)
    if win:
        gl(fr, -1 + sx, -37, "gleam", 4 if win % 2 else 3)
        fr.spark(4 + sx, -36, "gleam", 1 if win % 2 else 0)
    # lever on the right side: 0 = up, 1 = pulled
    bx, by = 11 + sx, -15
    a = math.radians(-80 + 150 * lever)
    kx, ky = bx + 9 * math.cos(a) * 0.9, by + 10 * math.sin(a)
    r.ell(bx - 0.5, by, 1.2, 2.0, "iron", 0.35)
    r.tube([(bx, by), (kx, ky)], [0.6, 0.6], "iron" if broken else "brass", 0.36)
    r.ell(kx, ky, 1.7, 1.7, "iron" if broken else "velvet", 0.37, bias=0.3)
    if not broken: gl(fr, kx - 0.6, ky - 0.6, "gleam", 3)
    if broken:
        for (x, y) in ((-5, -22), (-4, -23), (-3, -22), (3, -19), (4, -18), (-7, -12), (6, -9)):
            r.dot(x + sx, y, "tar", 0, 0.4)
        gl(fr, 7 + sx, -30, "smoke", 2, 170); gl(fr, 8 + sx, -32, "smoke", 1, 130)
    return fr.done()


def slot_symbol(kind, blur=0):
    """Reel symbols, 5 x 7, centred on the reel (child sprites the code shows when a reel stops)."""
    G = {
        "Bone": ["..3..", ".343.", "..2..", "..2..", "..2..", ".343.", "..3.."],
        "Coin": [".333.", "34432", "34322", "33322", "33222", "23221", ".222."],
        "Heart": ["33.32", "34332", "33322", "33221", ".322.", "..2..", "....."],
        "Skull": [".333.", "34332", "30302", "33332", ".232.", ".303.", "....."],
        "Crown": ["4.3.3", "3.3.2", "34332", "3p3c2", "33222", "22221", "....."],
    }
    MAT = {"Bone": "bone", "Coin": "lyel", "Heart": "blood", "Skull": "bone", "Crown": "lyel"}
    fr = Fr()
    if kind == "Blur":
        for y in range(7):
            for x in range(5):
                if (x + y + blur) % 3 == 0: gl(fr, x - 2, y - 3, "paper", 4)
                elif (x * 2 + y + blur) % 5 == 0: gl(fr, x - 2, y - 3, "paper", 1)
        return fr.done(floor=False)
    for y, row in enumerate(G[kind]):
        for x, c in enumerate(row):
            if c == ".": continue
            if c == "p": gl(fr, x - 2, y - 3, "lpink", 3)
            elif c == "c": gl(fr, x - 2, y - 3, "lcyan", 3)
            else: gl(fr, x - 2, y - 3, MAT[kind], int(c))
    return fr.done(floor=False)


@obj("ObjBSlotMachine")
def build_slot():
    idle = [slot_machine(bulbs=i) for i in range(4)]
    pull = [slot_machine(lever=0.15), slot_machine(lever=0.6), slot_machine(lever=1.0, blur=0, shake=1),
            slot_machine(lever=0.8, blur=1), slot_machine(lever=0.5, blur=2, shake=-1), slot_machine(lever=0.3, blur=3),
            slot_machine(lever=0.1, blur=0), slot_machine(lever=0.0, blur=1)]
    win = [slot_machine(win=i + 1) for i in range(4)]
    broken = [slot_machine(broken=True), slot_machine(broken=True, shake=1)]
    osheet("ObjBSlotMachine", [("Idle", idle, [0.3] * 4), ("Use", pull, [0.06, 0.06, 0.08] + [0.09] * 5),
                               ("Win", win, [0.1] * 4), ("Spent", broken, [0.6, 0.08]),
                               ("Vault", [slot_machine(win=1)], [0.2])])
    anims = [(k, [slot_symbol(k)], [0.2]) for k in ("Bone", "Coin", "Heart", "Skull", "Crown")]
    anims.append(("Blur", [slot_symbol("Blur", b) for b in range(3)], [0.05] * 3))
    fxsheet("FxObjBSlotSymbols", anims)


# ================================================================== 6. FORTUNE TELLER
CARD_SLOT = (0, -3)          # FxObjBCard spawn point


def fortune(swirl=0, hands=0.0, flare=0, card=0, spent=False, eyes=1):
    """A booth: carved wooden base, a glass case under a brass arch, a veiled skull mystic over a crystal ball."""
    fr = Fr((0, 13, 1.6)); r = fr.r
    block(r, -11, 10, -12, 0, "dwood", 0.0, top=1, curve=0.4)
    for y in (-9, -4):
        r.polyline([(-10, y), (9, y)], "dwood", 0.01, tone=1)
    block(r, -4, 3, -10, -6, "brass", 0.05, top=0)
    for (x, y) in ((-1, -9), (-2, -8), (-1, -8), (0, -8), (-1, -7)):
        if spent: r.dot(x, y, "brass", 1, 0.06)
        else: gl(fr, x, y, "lviol", 3)
    for x in range(-3, 3):
        r.dot(x, CARD_SLOT[1], "tar", 0, 0.06)
    # glass case and the dark inside
    block(r, -10, 9, -31, -12, "glassd", 0.1, top=0)
    r.ell(-0.5, -31, 9.6, 5.4, "glassd", 0.1, clip=lambda x, y: y <= -31)
    # the mystic: violet hood, skull face, shawl with coins
    hy = -27 - (1 if flare else 0)
    poly_pts = [(-7, -14), (-5, hy + 3), (4, hy + 3), (6, -14)]
    r.poly(poly_pts, "pviol", 0.2, normal=(-0.2, -0.1, 1.0), curve=0.6)
    r.ell(-0.5, hy, 4.8, 4.6, "pviol", 0.25)
    r.ell(-0.5, hy + 1, 2.8, 2.7, "bone", 0.3)
    e = "lcyan" if not spent else None
    if flare: e = "gleam"
    for ex in (-2, 1):
        if eyes and e: gl(fr, ex, hy + 1, e, 4 if flare else 3)
        else: r.dot(ex, hy + 1, "tar", 0, 0.31)
    r.dot(-1, hy + 3, "tar", 1, 0.31); r.dot(0, hy + 3, "tar", 1, 0.31)
    for x in (-4, -1, 2):
        gl(fr, x, hy + 5, "brass", 4 if (x + swirl) % 3 == 0 else 3)
    # table and crystal ball
    block(r, -8, 7, -14, -12, "dwood", 0.35, top=1)
    bx, by = -0.5, -17.5
    if spent:
        r.ell(bx, by, 3.3, 3.1, "glassd", 0.4)
    else:
        for y in range(int(by - 4), int(by + 4)):
            for x in range(int(bx - 4), int(bx + 5)):
                d = ((x - bx) / 3.3) ** 2 + ((y - by) / 3.1) ** 2
                if d <= 1.0:
                    gl(fr, x, y, "lcyan" if not flare else "gleam", 2 if d > 0.6 else 3)
        for k in range(3):
            a = swirl * 0.8 + k * 2.1
            gl(fr, bx + 1.6 * math.cos(a), by + 1.4 * math.sin(a), "lviol", 4)
        gl(fr, bx - 1, by - 2, "gleam", 4)
    for side in (-1, 1):
        hx = bx + side * 4.5
        hy2 = by + 1 - hands * 4
        r.dot(hx, hy2, "bone", 4, 0.45); r.dot(hx + side, hy2, "bone", 2, 0.45); r.dot(hx, hy2 + 1, "pviol", 2, 0.45)
    if flare:
        for k in range(6):
            a = k * math.pi / 3 + flare
            gl(fr, bx + 5 * math.cos(a), by + 4 * math.sin(a), "lcyan", 4)
    if card:
        cy = -4 - card * 2
        for y in range(cy - 3, cy + 1):
            for x in range(-2, 2):
                gl(fr, x, y, "paper", 4 if x < 0 else 3)
        gl(fr, -1, cy - 2, "lviol", 3); gl(fr, 0, cy - 1, "lviol", 3)
    # brass frame: pillars and arch, a star finial
    for y in range(-31, -12):
        r.dot(-11, y, "brass", 3, 0.5); r.dot(10, y, "brass", 1, 0.5)
    for i in range(32):
        a = math.pi + i * math.pi / 31
        r.dot(-0.5 + 10.4 * math.cos(a), -31 + 6.0 * math.sin(a), "brass", 3 if i < 16 else 2, 0.5)
    r.ell(-0.5, -38, 1.4, 1.4, "brass", 0.51)
    if not spent: gl(fr, -0.5, -39, "lpink", 3)
    for (x, y) in ((-9, -29), (-9, -28), (-8, -30)):
        gl(fr, x, y, "gleam", 3, 170)
    if spent:
        for (x, y) in ((-6, -21), (-5, -20), (4, -25), (5, -26)): r.dot(x, y, "tar", 0, 0.55)
    return fr.done()


@obj("ObjBFortuneTeller")
def build_fortune():
    idle = [fortune(swirl=i) for i in range(4)]
    read = [fortune(swirl=0, hands=0.4), fortune(swirl=1, hands=1.0, eyes=0), fortune(swirl=2, hands=1.0, flare=1),
            fortune(swirl=3, hands=0.8, flare=2), fortune(swirl=4, hands=0.4, flare=1, card=1),
            fortune(swirl=5, card=2), fortune(swirl=6, card=3)]
    spent = [fortune(spent=True, eyes=0), fortune(spent=True, swirl=2, eyes=0)]
    osheet("ObjBFortuneTeller", [("Idle", idle, [0.22] * 4), ("Use", read, [0.12, 0.14, 0.1, 0.1, 0.1, 0.12, 0.14]),
                                 ("Spent", spent, [0.5, 0.5]), ("Vault", [fortune(swirl=1, flare=1)], [0.2])])


# ================================================================== 7. BOUNCE SHROOM
CAP_TOP = (0, -12)           # FxObjBSpores spawn point


def shroom(sq=1.0, lean=0.0, puff=0):
    """A big springy mushroom with a spotted orchid cap and a smiling stem; sq < 1 squashes, > 1 stretches."""
    fr = Fr((0, 11, 1.6)); r = fr.r
    stem_h = 8 * sq
    capy = -stem_h - 4.5 * min(1.0, sq)
    rxc, ryc = 11.5 / math.sqrt(sq), 6.2 * min(1.2, sq ** 0.5)
    r.tube([(0, 0), (lean * 0.5, -stem_h * 0.5), (lean, -stem_h)], [4.2, 3.4, 3.0], "cream", 0.1)
    r.ell(lean, capy + 2.4, rxc - 0.6, 2.0, "mush", 0.2, flat=1)
    for x in range(int(-rxc + 2), int(rxc - 1), 2):
        r.dot(lean + x, capy + 2.4, "mush", 0, 0.21)                               # gills
    r.ell(lean, capy, rxc, ryc, "mush", 0.3, clip=lambda x, y: y <= capy + 1.5)
    for (sx_, sy_, rr) in ((-4.5, -2.4, 1.6), (2.4, -3.8, 1.8), (6.6, -0.8, 1.3), (-1, 0.5, 1.1), (-8.0, 0.6, 1.0)):
        X, Y = lean + sx_ / math.sqrt(sq), capy + sy_ * min(1.2, sq ** 0.5)
        r.ell(X, Y, rr, rr * 0.9, "cream", 0.31)
    gl(fr, lean - 5, capy - 3, "gleam", 3, 200)
    fy = int(round(-stem_h * 0.45))
    fx = int(round(lean * 0.5))
    r.dot(fx - 1, fy, "tar", 0, 0.12); r.dot(fx + 1, fy, "tar", 0, 0.12)
    if sq < 0.8: r.dot(fx, fy + 1, "velvet", 3, 0.12)
    else: r.dot(fx, fy + 1, "tar", 1, 0.12)
    r.dot(fx - 2, fy + 1, "ppink", 3, 0.12); r.dot(fx + 2, fy + 1, "ppink", 3, 0.12)              # cheeks
    if puff:
        rnd = random.Random(puff)
        for k in range(6 + puff * 2):
            a = rnd.uniform(math.pi, 2 * math.pi)
            rr = 9 + puff * 3 + rnd.uniform(-1, 2)
            gl(fr, math.cos(a) * rr, capy + math.sin(a) * rr * 0.5, "lpink" if k % 2 else "lviol", 3)
    return fr.done()


@obj("ObjBBounceShroom")
def build_shroom():
    idle = [shroom(sq=s) for s in (1.0, 0.96, 0.93, 0.96)]
    bounce = [shroom(sq=0.7), shroom(sq=0.52), shroom(sq=1.4, puff=1), shroom(sq=1.18, lean=1, puff=2),
              shroom(sq=0.84, lean=-1), shroom(sq=1.06), ]
    osheet("ObjBBounceShroom", [("Idle", idle, [0.25, 0.2, 0.25, 0.2]), ("Use", bounce, [0.04, 0.05, 0.06, 0.08, 0.08, 0.1]),
                                ("Vault", [shroom()], [0.2])])


# ================================================================== 8. FIREWORK CRATE
LAUNCH = (0, -20)            # rocket launch point
ROCKETS = [(-6, 9, "ppink"), (-3, 13, "pcyan"), (0, 11, "pyel"), (3, 14, "pviol"), (6, 8, "plime")]


def crate(rockets=5, fuse=0.0, spark=0, charred=False, smoke=0):
    """A slatted crate packed with striped rockets, a curling fuse on its side."""
    fr = Fr((0, 12, 1.6)); r = fr.r
    for i, (x, h, m) in enumerate(ROCKETS[:rockets]):
        rp = r.part(False, 0.05)
        h += 2
        for y in range(-h - 7, -8):
            band = (y // 2) % 2
            r.put(x, y, 0.05, m if band else "cream", 0.5, rp, 3 if band else 4)
            r.put(x + 1, y, 0.05, m if band else "cream", 0.5, rp, 1 if band else 2)
        r.dot(x, -h - 8, m, 3, 0.06); r.dot(x + 1, -h - 8, m, 1, 0.06); r.dot(x, -h - 9, m, 4, 0.06)
    wm = "plank" if not charred else "tar"
    block(r, -12, 11, -12, 0, wm, 0.2, top=2)
    for y in (-7, -3):
        r.polyline([(-12, y), (11, y)], wm, 0.21, tone=1)
    for x in (-12, 11):
        block(r, x, x, -11, 0, wm, 0.22, top=0, bias=-0.2)
    r.line(-11, -2, 10, -10, wm, 0.23, tone=1)
    if not charred:
        for (x, y) in ((3, -7), (2, -6), (3, -6), (4, -6), (3, -5), (2, -4), (4, -4)):
            r.dot(x, y, "velvet", 3, 0.24)
        r.dot(-6, -8, "iron", 3, 0.24); r.dot(6, -8, "iron", 3, 0.24); r.dot(-6, -1, "iron", 2, 0.24); r.dot(6, -1, "iron", 2, 0.24)
    else:
        for (x, y) in ((-4, -6), (-3, -3), (5, -2), (2, -7)): gl(fr, x, y, "rune", 2)
    fz = [(12, -4), (13, -3), (14, -5), (15, -7), (14, -9), (16, -10)]
    burnt = int(round(fuse * (len(fz) - 1)))
    for i, (x, y) in enumerate(fz):
        if i < len(fz) - burnt: r.dot(x, y, "rope", 3 if i % 2 else 2, 0.3)
    if spark and burnt < len(fz):
        x, y = fz[len(fz) - 1 - burnt]
        gl(fr, x, y, "gleam", 4)
        for k in range(3):
            a = spark * 1.9 + k * 2.1
            gl(fr, x + 1.6 * math.cos(a), y + 1.6 * math.sin(a), "rune", 4 - k)
    for s in range(smoke):
        gl(fr, -3 + s * 3, -13 - s * 2, "smoke", 3, 200); gl(fr, -2 + s * 3, -14 - s * 2, "smoke", 2, 160)
    return fr.done()


@obj("ObjBFireworkCrate")
def build_crate():
    idle = [crate(), crate(spark=0)]
    lit = [crate(fuse=k / 4.0, spark=k + 1) for k in range(4)]
    launch = [crate(rockets=4, fuse=1.0, smoke=1), crate(rockets=3, fuse=1.0, smoke=2), crate(rockets=1, fuse=1.0, smoke=3),
              crate(rockets=0, fuse=1.0, smoke=2, charred=True)]
    osheet("ObjBFireworkCrate", [("Idle", idle, [0.4, 0.4]), ("Lit", lit, [0.15] * 4), ("Launch", launch, [0.12] * 4),
                                 ("Spent", [crate(rockets=0, fuse=1.0, charred=True, smoke=1)], [0.2]),
                                 ("Vault", [crate(spark=2, fuse=0.0)], [0.2])])


# ================================================================== 9. LEVER TRIO (console, levers, glyphs, hatch)
LEVER_X = (-9, 0, 9)         # lever pivots from the console's floor point; y = LEVER_Y (FxObjBLever lands here)
LEVER_Y = -10
PLAQUE_Y = -19               # glyph plaque centres (x = LEVER_X); FxObjBGlyphs lands here


def lever_console(buzz=0, jam=False):
    """A carved stone console: a low step, a raised back board with three brass-framed plaques and three lever slots."""
    fr = Fr((0, 16, 1.6)); r = fr.r
    sx = [0, 1, -1, 0][buzz % 4] if buzz else 0
    block(r, -16 + sx, 15 + sx, -8, 0, "ostone", 0.0, top=2)
    block(r, -15 + sx, 14 + sx, -24, -9, "ostone", 0.1, top=0, curve=0.3)
    block(r, -16 + sx, 15 + sx, -26, -24, "ostone", 0.15, top=1)
    for x in range(-13, 14, 3):
        r.dot(x + sx, -25, "ostone", 1, 0.16)                                       # dentils under the cap
    for y in (-16, -12):
        for x in range(-14, 14):
            if (x + (y // 4)) % 7 == 0: r.dot(x + sx, y, "ostone", 1, 0.11)          # block joints
    for lx in LEVER_X:
        for y in range(-13, -6):
            r.dot(lx + sx, y, "tar", 0, 0.2); r.dot(lx + 1 + sx, y, "tar", 1, 0.2)
        r.dot(lx + sx, -14, "ostone", 3, 0.2); r.dot(lx + 1 + sx, -14, "ostone", 3, 0.2)
        block(r, lx - 3 + sx, lx + 3 + sx, PLAQUE_Y - 3, PLAQUE_Y + 3, "brass", 0.25, top=0)
        block(r, lx - 2 + sx, lx + 2 + sx, PLAQUE_Y - 2, PLAQUE_Y + 2, "tar", 0.26, top=0)
        r.dot(lx - 3 + sx, PLAQUE_Y - 3, "brass", 4, 0.27)
    if buzz:
        rnd = random.Random(buzz)
        for k in range(5):
            gl(fr, rnd.randint(-16, 15), rnd.randint(-28, -2), "smoke", 3 if k % 2 else 2, 200)
    if jam:
        for (x, y) in ((-6, -23), (-5, -22), (-5, -21), (-4, -20), (-4, -18), (-3, -17), (5, -12), (6, -11), (6, -10), (-12, -6), (-11, -5)):
            r.dot(x, y, "ostone", 0, 0.3)
        for (x, y) in ((-2, -28), (-1, -29), (3, -28)): gl(fr, x, y, "smoke", 2, 170)
    moss(r, [(-16, -8), (-15, -8), (14, -8), (15, -8), (-16, -26), (-15, -26), (13, -26)])
    return fr.done(specks=K.STONE_SPECK, seed=21)


def lever(t):
    """A lever (child sprite): t 0 = up (leaning back left), 1 = pulled down (forward right). Origin = the slot pivot."""
    fr = Fr(); r = fr.r
    a = math.radians(-120 + 90 * t)
    ex, ey = 6.5 * math.cos(a), 6.5 * math.sin(a)
    r.tube([(0.5, 0), (ex + 0.5, ey)], [1.0, 0.8], "iron", 0.1, bias=0.25)
    r.ell(ex + 0.5, ey, 2.2, 2.2, "velvet", 0.2, bias=0.15)
    r.dot(ex - 0.3, ey - 0.9, "gleam", 3, 0.21)
    r.ell(0.5, 0.2, 1.6, 1.0, "brass", 0.15)
    return fr.done(floor=False)


GLYPHS = {
    "Sun": ["1.1.1", ".222.", "12221", ".222.", "1.1.1"],
    "Moon": [".111.", "11...", "1....", "11...", ".111."],
    "Star": ["..1..", "11211", ".111.", ".1.1.", "1...1"],
}


def glyph(kind, scratch=False):
    """Plaque glyphs (5 x 5, centred) and the faint floor scratches of the same glyph (the order clue)."""
    fr = Fr()
    mat = {"Sun": "lyel", "Moon": "lcyan", "Star": "lviol"}[kind]
    for y, row in enumerate(GLYPHS[kind]):
        for x, c in enumerate(row):
            if c == ".": continue
            if scratch:
                if (x + 2 * y) % 4 == 0: continue
                gl(fr, x - 2, y - 2, "ostone", 3 if c == "2" else 2)
            else:
                gl(fr, x - 2, y - 2, mat, 4 if c == "2" else 3)
    return fr.done(floor=False)


def hatch(open_=0.0):
    """A plank floor hatch in a stone frame, 19 x 11, centred; open_ 0..1 swings the lid up and back."""
    fr = Fr(); r = fr.r
    fp = r.part(False, 0.0)
    for y in range(-5, 6):
        for x in range(-9, 10):
            if abs(x) == 9 or abs(y) == 5:
                r.put(x, y, 0.0, "ostone", 0.5, fp, 3 if (y == -5 or x == -9) else 1 if (y == 5 or x == 9) else 2)
    for y in range(-4, 5):
        for x in range(-8, 9):
            r.dot(x, y, "tar", 0 if y > -3 else 1, 0.01)
    if open_ > 0.5:
        for (x, y) in ((-6, -3), (-6, -1), (-6, 1), (-5, -3), (-5, -1), (-5, 1)):
            r.dot(x, y, "owood", 2, 0.02)                                          # ladder rungs
        for (x, y, t) in ((2, 2, 4), (3, 2, 3), (4, 3, 4), (1, 3, 3), (3, 3, 2), (2, 3, 4)):
            gl(fr, x, y, "brass", t)
    h = int(round(9 * math.cos(open_ * math.pi * 0.55)))
    top = 4 - h
    if h > 0:
        for y in range(top, 5):
            for x in range(-8, 9):
                t = 3 if (y - top) % 3 == 0 else (2 if x % 6 else 1)
                r.dot(x, y, "plank", t, 0.1)
        r.dot(-1, top + h // 2, "iron", 3, 0.11); r.dot(0, top + h // 2, "iron", 2, 0.11)
        for x in (-6, 5):
            for y in range(top, 5, 2): r.dot(x, y, "iron", 2, 0.11)
    if open_ > 0.3:
        up = int(round(open_ * 7))
        for y in range(-5 - up, -5):
            for x in range(-8, 9):
                r.dot(x, y, "plank", 1 if x % 6 else 0, 0.05)
    return fr.done(floor=False)


@obj("ObjBLeverTrio")
def build_levers():
    osheet("ObjBLeverTrio", [("Idle", [lever_console()], [0.2]), ("Buzz", [lever_console(buzz=k) for k in (1, 2, 3)], [0.05] * 3),
                             ("Jam", [lever_console(jam=True)], [0.2]), ("Vault", [console_picture()], [0.2])])
    fxsheet("FxObjBLever", [("Up", [lever(0)], [0.2]), ("Pull", [lever(0.35), lever(0.7), lever(1.05)], [0.05, 0.05, 0.06]),
                            ("Down", [lever(1)], [0.2])])
    fxsheet("FxObjBGlyphs", [(k, [glyph(k)], [0.2]) for k in ("Sun", "Moon", "Star")] +
            [("Scratch" + k, [glyph(k, True)], [0.2]) for k in ("Sun", "Moon", "Star")])
    hz = lambda t: hatch(t).shift(0, -5)
    osheet("ObjBHatch", [("Idle", [hz(0)], [0.2]), ("Use", [hz(t) for t in (0.2, 0.4, 0.6, 0.8, 1.0)], [0.06] * 5),
                         ("Spent", [hz(1.0)], [0.2]), ("Vault", [hz(1.0)], [0.2])])


def console_picture():
    """The vault picture: the console with its plaques and levers composited."""
    base = lever_console()
    px, tones = dict(base.px), dict(base.tones)
    for i, (lx, k) in enumerate(zip(LEVER_X, ("Moon", "Star", "Sun"))):
        for part in (glyph(k).shift(lx, PLAQUE_Y), lever(1.0 if i == 0 else 0.0).shift(lx, LEVER_Y)):
            px.update(part.px); tones.update(part.tones)
    return Px(px, tones)


# ================================================================== 10. CRACKED WALL
NICHE = (0, -10)             # the shelf the key drops from


def brick_wall(cracks=0, gone=0.0, alcove=False, shake=0, seed=3):
    """A 28 x 30 brick wall section. cracks 0 = a hairline only a sharp eye spots, 1-3 = growing; gone 0..1 crumbles
    the bricks from the top down onto a rubble heap; alcove = the niche behind (dark arch, shelf, candle, skull)."""
    fr = Fr((0, 16, 1.6)); r = fr.r
    W0, W1, T = -15 + shake, 15 + shake, -32
    # the niche behind (the bricks cover it until they fall)
    for y in range(T + 4, -1):
        for x in range(W0 + 3, W1 - 2):
            d = ((x - shake) / 10.5) ** 2 + ((y + 16) / 14.0) ** 2
            if y > -15 or d < 1.0:
                r.dot(x, y, "tar", 0 if y > -8 else (1 if d < 0.6 else 2), -0.5)
    block(r, W0 + 3, W1 - 3, -9, -7, "owood", -0.4, top=1)
    r.tube([(-4 + shake, -10), (-4 + shake, -13)], [0.8, 0.8], "wax", -0.35)
    r.dot(-4 + shake, -14, "rune", 4, -0.34); r.dot(-4 + shake, -15, "rune", 3, -0.34); r.dot(-4 + shake, -16, "rune", 2, -0.34)
    r.ell(3.5 + shake, -10.5, 1.6, 1.4, "bone", -0.35)
    r.dot(3 + shake, -10, "tar", 0, -0.34); r.dot(4 + shake, -10, "tar", 0, -0.34)
    rnd = random.Random(seed)
    cut = T + (2 - T) * gone if gone else T - 1
    bp = r.part(False, 0.2)
    for row, y0 in enumerate(range(T, 0, 4)):
        off = 0 if row % 2 else 3
        for x0 in range(W0 - off, W1, 7):
            m = rnd.choice(["brick", "brick", "ostone", "brick"])
            for y in range(y0, min(y0 + 4, 1)):
                for x in range(max(x0, W0), min(x0 + 7, W1 + 1)):
                    if alcove or y < cut: continue
                    if row == 0 and (x0 // 7) % 2 == 0 and y < y0 + 2: continue
                    mortar = (y == y0 + 3) or (x == x0 + 6)
                    if mortar: tone = 0
                    elif y == y0 or x == x0: tone = 3
                    elif y == y0 + 2 or x == x0 + 5: tone = 1
                    else: tone = 2
                    r.put(x, y, 0.2, m, 0.5, bp, tone)
    if not alcove:
        hair = [(1, -27), (2, -26), (1, -25), (2, -24), (3, -23), (2, -22), (3, -21), (4, -20), (3, -19), (3, -18)]
        paths = [hair]
        if cracks >= 1: paths.append([(3, -18), (2, -17), (1, -16), (0, -15), (-1, -14), (0, -13), (-1, -12), (-2, -11)])
        if cracks >= 2: paths += [[(4, -20), (5, -20), (6, -19), (7, -19), (8, -18)], [(0, -15), (-2, -15), (-3, -16), (-5, -16), (-6, -17)],
                                  [(1, -25), (0, -26), (-1, -26), (-2, -27)]]
        if cracks >= 3: paths += [[(-2, -11), (-3, -9), (-4, -8), (-4, -6), (-5, -4)], [(8, -18), (9, -16), (10, -15)],
                                  [(-6, -17), (-8, -18), (-9, -20)], [(3, -18), (5, -16), (6, -14), (6, -12)]]
        for pi_, pth in enumerate(paths):
            for (x, y) in pth:
                if (x + shake, y) in r.b and y >= cut:
                    if pi_ or cracks: r.dot(x + shake, y, "tar", 0, 0.3)
                    else: r.dot(x + shake, y, r.b[(x + shake, y)][1], 1, 0.3)          # the hairline: one tone down
                    if (pi_ or cracks) and (x + shake + 1, y) in r.b:
                        r.dot(x + shake + 1, y, "brick", 4, 0.29)                     # the crack's lit far lip
        if cracks >= 2:
            for (x, y) in ((5, -21), (-3, -14), (7, -17)):
                if (x + shake, y) in r.b and y >= cut: gl(fr, x + shake, y, "smoke", 3, 200)
    heap = gone if not alcove else 1.0
    if heap > 0:
        r2 = random.Random(9)
        hp = r.part(False, 0.4)
        for k in range(int(46 * heap)):
            x = r2.randint(W0, W1); h = int((1 - abs(x - shake) / 14.0) * 4 * heap) + r2.randint(0, 1)
            m = r2.choice(["brick", "ostone", "brick"])
            for y in range(-h, 1):
                r.put(x, y, 0.4, m, 0.5, hp, 3 if y == -h else 2 if y > -h + 1 else 1)
    if 0 < gone < 1:
        r3 = random.Random(int(gone * 10))
        for k in range(7):
            x = r3.randint(W0 + 2, W1 - 2); y = int(cut + r3.randint(2, 10))
            if y < -1:
                r.dot(x, y, "brick", 3, 0.5); r.dot(x + 1, y, "brick", 2, 0.5); r.dot(x, y + 1, "brick", 1, 0.5)
        for k in range(5):
            gl(fr, r3.randint(W0, W1), cut + r3.randint(-2, 3), "smoke", 3, 170)
    return fr.done()


@obj("ObjBCrackedWall")
def build_wall():
    crumble = [brick_wall(cracks=3, shake=1), brick_wall(cracks=3, gone=0.15, shake=-1), brick_wall(gone=0.35),
               brick_wall(gone=0.55), brick_wall(gone=0.75), brick_wall(gone=0.92), brick_wall(alcove=True)]
    osheet("ObjBCrackedWall", [("Idle", [brick_wall()], [0.2]), ("Crack1", [brick_wall(cracks=1)], [0.2]),
                               ("Crack2", [brick_wall(cracks=2)], [0.2]), ("Crack3", [brick_wall(cracks=3)], [0.2]),
                               ("Hit", [brick_wall(shake=1), brick_wall(shake=-1)], [0.04, 0.05]),
                               ("Crumble", crumble, [0.06, 0.06, 0.07, 0.08, 0.08, 0.1, 0.2]),
                               ("Spent", [brick_wall(alcove=True)], [0.2]), ("Vault", [brick_wall(cracks=1)], [0.2])])


# ================================================================== 11. MYSTERIOUS KEYHOLE + RELIQUARY
KEYHOLE = (0, -14)


def keyhole_slab(glow=0, sink=0, key=-1, rattle=0, beams=0, red=False):
    """An arched stone slab with a carved rune border and an ornate brass escutcheon whose keyhole glows violet.
    sink lowers the slab into the floor (px); key >= 0 shows the key in the hole turned key * 45 degrees."""
    fr = Fr((0, 14, 1.6)); r = fr.r
    sx = rattle
    top = -32 + sink
    sp = r.part(False, 0.0)
    for y in range(top, 1):
        for x in range(-13, 14):
            d = (x / 13.0) ** 2 + ((y - (top + 9)) / 9.0) ** 2
            if y < top + 9 and d > 1.0: continue
            u = x / 13.0
            nz = 1.0
            if y < top + 9:
                v = (y - (top + 9)) / 9.0
                n = (u * 0.6, v * 0.6, 0.8)
            else:
                n = (u * 0.5 - 0.1, 0.0, 1.0)
            edge = abs(x) >= 12 or (y < top + 9 and d > 0.74)
            l = lam(*[c / math.sqrt(sum(q * q for q in n)) for c in n]) + (0.2 if edge else 0.0)
            r.put(x + sx, y, 0.0, "ostone", l, sp)
    for y in range(top + 2, 1):
        for x in (-10, 10):
            if (x + sx, y) in r.b and y > top + 7: r.dot(x + sx, y, "ostone", 1, 0.01)    # the carved border groove
    rune = "lviol" if not red else "blood"
    for (x, y) in ((-11.5, -22), (-11.5, -17), (-11.5, -12), (-11.5, -7), (11.5, -22), (11.5, -17), (11.5, -12), (11.5, -7),
                   (-7, -29), (7, -29), (0, -31)):
        if top <= y + sink <= 0:
            gl(fr, x + sx, y + sink, rune, 3 if glow % 2 == 0 else 2)
    ey = KEYHOLE[1] + sink
    if ey < 0:
        r.ell(-0.5 + sx, ey, 4.0, 5.2, "brass", 0.2)
        for (x, y) in ((-4, -4), (3, -4), (-4, 4), (3, 4)):
            if ey + y < 0: r.dot(x + sx, ey + y, "brass", 4, 0.21)
        inner = rune
        for (x, y) in ((-1, -2), (0, -2), (-1, -1), (0, -1), (-2, -1), (1, -1), (-1, 0), (0, 0), (-1, 1), (0, 1), (-1, 2), (0, 2)):
            if ey + y < 0:
                if (x, y) in ((-2, -1), (1, -1), (-1, 2), (0, 2)): r.dot(x + sx, ey + y, "tar", 0, 0.22)
                else: gl(fr, x + sx, ey + y, inner, 4 if glow in (1, 2) else 3)
        if key >= 0:
            a = math.radians(-90 + key * 45)
            for t in range(0, 7):
                X = -0.5 + t * math.cos(a) * 0.9
                Y = ey - 1 + t * math.sin(a) * 0.4 - (t if key == 0 else 0) * 0.6
                r.dot(X + sx, Y, "ogold", 4 if t < 4 else 3, 0.3)
            r.dot(-1 + sx, ey - 1, "ogold", 2, 0.31)
    if not sink:
        for k in range(2):
            my = ey - 6 - ((glow + k * 2) % 4) * 2
            gl(fr, -1 + (k * 3 - 1.5) * 0.6 + sx, my, rune, 4 if k else 3)
    for b in range(beams):
        for (dx, dy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            for t in range(4, 4 + b * 3):
                X, Y = -0.5 + dx * t, ey + dy * t * 0.8
                if Y < 0: gl(fr, X, Y, "lviol", 4 if t % 2 else 3)
    moss(r, [(-13, -1), (-12, -1), (13, -2), (-11, top + 4)] if sink < 20 else [])
    return fr.done(specks=K.STONE_SPECK, seed=31)


def slab_gone():
    """Only a stone rim and a dark slot left in the floor, a last violet twinkle over it."""
    fr = Fr(); r = fr.r
    for x in range(-11, 12):
        r.dot(x, 0, "ostone", 2 if x % 3 else 1, 0.0); r.dot(x, -1, "tar", 0 if abs(x) < 10 else 1, 0.0)
        if abs(x) >= 10: r.dot(x, -1, "ostone", 3, 0.01)
    fr.spark(0, -4, "lviol", 1)
    return fr.done()


def reliquary(rise=1.0, lid=0.0, glow=0):
    """A gilded reliquary chest with a violet velvet band and a jewel; rise 0..1 lifts it out of the floor slot,
    lid 0..1 opens it and light pours out."""
    fr = Fr((0, 9 * rise + 1, 1.3)); r = fr.r
    dy = int(round((1 - rise) * 10))
    clip = lambda x, y: y <= 0
    block(r, -10, 10, -10 + dy, 0 + dy, "ogold", 0.2, top=0, curve=0.6)
    for x in range(-10, 11):
        if -5 + dy <= 0: r.dot(x, -5 + dy, "velvet", 3 if x < 3 else 2, 0.21)
        if -4 + dy <= 0: r.dot(x, -4 + dy, "velvet", 1, 0.21)
    for x in (-10, 0, 10):
        for y in range(-10, 1):
            if y + dy <= 0: r.dot(x, y + dy, "ogold", 4 if x < 0 else 3 if x == 0 else 1, 0.22)
    if -6 + dy <= 0:
        gl(fr, -0.5, -6.5 + dy, "lviol", 4); gl(fr, 0.5, -6.5 + dy, "lviol", 3)
    if lid < 0.2:
        r.ell(0, -10.5 + dy, 10.6, 5.0, "ogold", 0.3, clip=lambda x, y: y <= -10 + dy and y <= 0)
        for x in range(-9, 10, 3):
            if -12 + dy <= 0: r.dot(x, -12 + dy, "ogold", 4, 0.31)
    else:
        up = int(round(lid * 7))
        for y in range(-10 - up, -9):
            for x in range(-7, 8):
                if y + dy <= 0: r.dot(x, y + dy, "ogold", 2 if y > -10 - up else 4, 0.1)
        for x in range(-7, 8):
            for y in (-10, -9):
                if y + dy <= 0:
                    if abs(x) > 3: r.dot(x, y + dy, "velvet", 2, 0.3)
                    else: gl(fr, x, y + dy, "lviol", 4 if lid > 0.6 else 3)
        for k, x in enumerate((-3, 0, 3)):
            for t in range(int(lid * (7 + k % 2 * 3))):
                Y = -12 - up - t
                if Y + dy <= 0 and (t + k) % 3 != 2: gl(fr, x, Y + dy, "lyel", 4 if t < 3 else 3, 255 if t < 5 else 170)
    if glow:
        fr.spark(-5 + glow * 2, -12 + dy, "gleam", 1)
    if rise < 1.0:
        for x in range(-11, 12):
            r.dot(x, 0, "ostone", 2 if x % 3 else 1, 0.5)
    return fr.done()


@obj("ObjBKeyhole")
def build_keyhole():
    idle = [keyhole_slab(glow=g) for g in range(4)]
    locked = [keyhole_slab(glow=1, rattle=1, red=True), keyhole_slab(glow=1, rattle=-1, red=True), keyhole_slab(glow=0)]
    unlock = [keyhole_slab(glow=1, key=0), keyhole_slab(glow=2, key=1), keyhole_slab(glow=2, key=2, beams=1),
              keyhole_slab(glow=1, key=2, beams=2, rattle=1), keyhole_slab(glow=2, sink=4, beams=2, rattle=-1),
              keyhole_slab(glow=1, sink=10, beams=1), keyhole_slab(glow=1, sink=18), keyhole_slab(glow=1, sink=26)]
    osheet("ObjBKeyhole", [("Idle", idle, [0.25] * 4), ("Locked", locked, [0.05, 0.05, 0.12]),
                           ("Unlock", unlock, [0.14, 0.14, 0.12, 0.1, 0.1, 0.1, 0.1, 0.12]),
                           ("Spent", [slab_gone()], [0.2]), ("Vault", [keyhole_slab(glow=1)], [0.2])])
    osheet("ObjBReliquary", [("Rise", [reliquary(rise=r_) for r_ in (0.1, 0.3, 0.55, 0.8, 1.0)], [0.08] * 5),
                             ("Idle", [reliquary(glow=g) for g in (0, 1, 2, 0)], [0.25] * 4),
                             ("Use", [reliquary(lid=l) for l in (0.2, 0.4, 0.6, 0.8, 1.0)], [0.07] * 5),
                             ("Spent", [reliquary(lid=1.0)], [0.2]), ("Vault", [reliquary(glow=1)], [0.2])])


# ================================================================== 12. SCULPTOR'S ALTAR
STATUE_AT = (0, 18)          # the statue appears in front of the altar (code), FxObjBStatueForm with it


def altar(glow=0, carve=-1, spent=False, dust=0):
    """A long stone altar: mallet and chisel resting on the left, an empty pale plinth on the right, glowing runes cut
    along the front. carve >= 0: the tools float over the plinth and strike (pose 0..3)."""
    fr = Fr((0, 15, 1.6)); r = fr.r
    block(r, -16, 15, -10, 0, "ostone", 0.0, top=2, curve=0.3)
    block(r, -17, 16, -2, 0, "ostone", 0.05, top=1)
    for i, x in enumerate(range(-12, 12, 4)):
        pat = [((0, 0), (0, 1), (1, 2)), ((0, 0), (1, 1), (0, 2)), ((1, 0), (0, 1), (1, 2))][i % 3]
        for (dx, dy) in pat:
            if spent: r.dot(x + dx, -6 + dy, "ostone", 0, 0.06)
            else: gl(fr, x + dx, -6 + dy, "lviol", 3 if (glow + i) % 2 == 0 else 2)
    block(r, 2, 11, -16, -10, "pstone", 0.2, top=2)
    if spent:
        for (x, y) in ((5, -14), (6, -13), (6, -12), (7, -11), (8, -10)): r.dot(x, y, "pstone", 0, 0.21)
    if carve < 0:
        r.tube([(-12, -10), (-5, -12)], [0.7, 0.7], "owood", 0.3)                    # mallet
        block(r, -7, -4, -14, -11, "owood", 0.31, top=1)
        r.tube([(-11, -13), (-6, -16)], [0.5, 0.5], "iron", 0.32, bias=0.2)           # chisel
        r.dot(-11, -13, "owood", 2, 0.33); r.dot(-12, -12, "owood", 1, 0.33)
    else:
        hy = [-27, -23, -19, -24][carve % 4]
        cx, cy = 6, -19
        r.tube([(cx, cy), (cx - 2, cy - 5)], [0.5, 0.5], "iron", 0.4, bias=0.2)
        r.dot(cx - 2, cy - 5, "owood", 2, 0.41); r.dot(cx - 3, cy - 6, "owood", 2, 0.41)
        r.tube([(cx - 9, hy + 3), (cx - 3, hy)], [0.7, 0.7], "owood", 0.42)
        block(r, cx - 5, cx - 2, hy - 2, hy + 1, "owood", 0.43, top=1)
        if carve % 4 == 2:
            for k in range(6):
                a = math.radians(-170 + k * 32)
                gl(fr, cx + 3 * math.cos(a), cy + 2 * math.sin(a), "lyel" if k % 2 else "gleam", 4)
    for d in range(dust):
        rnd = random.Random(d * 5 + glow)
        gl(fr, rnd.randint(2, 10), rnd.randint(-23, -16), "smoke", 4 if d % 2 else 3, 220)
    if not spent and carve < 0:
        my = -17 - (glow % 4) * 2
        gl(fr, 4 + glow % 3, my, "lviol", 3); gl(fr, 8 - glow % 2, my + 3, "lviol", 2)
    moss(r, [(-14, -9), (-13, -9), (12, -9), (13, -9), (-15, -2)])
    return fr.done(specks=K.STONE_SPECK, seed=41)


@obj("ObjBSculptorAltar")
def build_altar():
    idle = [altar(glow=g) for g in range(4)]
    carve = [altar(glow=1, carve=0), altar(glow=0, carve=1), altar(glow=1, carve=2, dust=3), altar(glow=0, carve=3, dust=2),
             altar(glow=1, carve=1), altar(glow=0, carve=2, dust=4), altar(glow=1, carve=3, dust=3), altar(glow=0, dust=5)]
    osheet("ObjBSculptorAltar", [("Idle", idle, [0.28] * 4), ("Use", carve, [0.1, 0.06, 0.08, 0.1, 0.06, 0.08, 0.1, 0.16]),
                                 ("Spent", [altar(spent=True)], [0.2]), ("Vault", [altar(glow=0)], [0.2])])


# ================================================================== 13. WISHING WELL
WATER = (0, -8)              # water centre (FxObjBWellSpirit)


def well(shim=0, coin=-1, splash=0, wish=0):
    """A round stone well the size of Crawl's own (PropActionable_Well, 18 x 31): a drum of fitted stones, two posts,
    a shingled roof, a crank and a bucket. coin 0..3: a tossed coin's arc; splash: ripple size; wish: glow + sparkles."""
    fr = Fr((0, 11, 1.5)); r = fr.r
    cy_top, RX, RY = WATER[1], 10.0, 3.6
    for px_ in (-10, 10):
        block(r, px_ - 1, px_ + 1, -26, cy_top, "owood", 0.0, top=0, curve=0.8)
    rp = r.part(False, 0.05)
    for i, y in enumerate(range(-35, -26)):
        w = 2 + int(round(i * 1.75))
        for x in range(-w, w + 1):
            shingle = (x + (i % 2) * 2) % 4 == 0
            t = 1 if shingle else (3 if x < 0 else 2)
            if y == -27: t = 1
            r.put(x, y, 0.05, "plank", 0.5, rp, t)
    r.dot(-1, -35, "plank", 4, 0.06); r.dot(0, -35, "plank", 3, 0.06)
    r.tube([(-9, -24), (11, -24)], [0.7, 0.7], "iron", 0.1)
    r.dot(13, -24, "iron", 3, 0.11); r.dot(13, -23, "iron", 2, 0.11); r.dot(14, -22, "velvet", 3, 0.11)
    for y in range(-23, -18): r.dot(0, y, "rope", 3 if y % 2 else 2, 0.12)
    block(r, -3, 3, -18, -13, "plank", 0.13, top=1)
    r.dot(-3, -18, "iron", 3, 0.14); r.dot(2, -18, "iron", 2, 0.14)
    # water inside the rim
    for y in range(int(cy_top - RY) + 1, int(cy_top + RY) + 1):
        for x in range(int(-RX) + 1, int(RX)):
            d = (x / (RX - 1.5)) ** 2 + ((y - cy_top) / (RY - 1.0)) ** 2
            if d <= 1.0:
                if y == int(cy_top - RY) + 1: r.dot(x, y, "water", 0, 0.2)
                elif wish: gl(fr, x, y, "lcyan", 3 if (x + y + shim) % 3 == 0 else 2)
                else: r.dot(x, y, "water", 3 if (x + y + shim) % 5 == 0 else 2, 0.2)
    # rim ring of stones and the front wall of fitted stone courses
    for i in range(44):
        a = i * 2 * math.pi / 44
        x, y = RX * math.cos(a), cy_top + RY * math.sin(a)
        r.dot(x, y, "pstone", 4 if math.sin(a) < 0.2 and math.cos(a) < 0.3 else 3, 0.3)
        if math.sin(a) < 0.3:                                                        # the coping's outer lip
            r.dot((RX + 0.9) * math.cos(a), cy_top + (RY + 0.9) * math.sin(a), "pstone", 2 if math.cos(a) > 0.3 else 3, 0.29)
    wp = r.part(False, 0.25)
    for y in range(cy_top, 1):
        for x in range(-10, 11):
            if y < cy_top + RY * math.sqrt(max(0, 1 - (x / RX) ** 2)) - 0.5: continue
            row = (y - cy_top) // 3
            mortar = (y - cy_top) % 3 == 0 or (x + (row % 2) * 2) % 5 == 0
            u = x / RX
            if mortar: t = 1
            else: t = 3 if u < -0.45 else 2 if u < 0.5 else 1
            m = "pstone" if ((x + (row % 2) * 2) // 5) % 2 else "ostone"
            r.put(x, y, 0.25, m, 0.5, wp, t if y < 0 else 0)
    block(r, -14, 13, -2, 0, "ostone", 0.3, top=1)                                  # a step of flagstones round its foot
    moss(r, [(-10, -5), (-9, -4), (9, -2), (10, -3), (-12, -2), (11, -2)])
    if splash:
        for i in range(20):
            a = i * 2 * math.pi / 20
            x, y = (splash * 1.8) * math.cos(a), cy_top + (splash * 0.7) * math.sin(a)
            if (x / (RX - 1.5)) ** 2 + ((y - cy_top) / (RY - 1.0)) ** 2 <= 1.0:
                gl(fr, x, y, "lcyan", 4 if splash < 3 else 3)
        if splash == 1:
            gl(fr, 0, cy_top - 1, "gleam", 4); gl(fr, -1, cy_top - 2, "lcyan", 4); gl(fr, 1, cy_top - 2, "lcyan", 4)
    if coin >= 0:
        cx, cy = [(-11, -15), (-7, -18), (-3, -15), (-1, -10)][coin]
        gl(fr, cx, cy, "brass", 4); gl(fr, cx + 1, cy, "brass", 2); gl(fr, cx, cy - 1, "gleam", 4)
    if wish:
        for k in range(3 + wish):
            rnd = random.Random(k * 13 + wish)
            x = rnd.randint(-5, 5); y = cy_top - 2 - ((wish * 3 + k * 4) % 14)
            gl(fr, x, y, "lcyan" if k % 2 else "gleam", 4)
            if k % 3 == 0: gl(fr, x - 1, y, "lcyan", 3); gl(fr, x + 1, y, "lcyan", 3)
    return fr.done(specks=K.STONE_SPECK, seed=51)


@obj("ObjBWishingWell")
def build_well():
    idle = [well(shim=i) for i in range(4)]
    toss = [well(shim=0, coin=0), well(shim=1, coin=1), well(shim=2, coin=2), well(shim=3, coin=3, splash=1), well(shim=0, splash=2)]
    wish = [well(shim=i, wish=i + 1, splash=3 if i == 0 else 0) for i in range(6)]
    osheet("ObjBWishingWell", [("Idle", idle, [0.25] * 4), ("Use", toss, [0.07, 0.07, 0.07, 0.08, 0.12]),
                               ("Wish", wish, [0.12] * 6), ("Vault", [well(shim=1, wish=2)], [0.2])])


# ================================================================== 14. WATCHING PORTRAIT
NICHE_GOLD = (0, -8)


def portrait_cab(eyes=0, wink=0, swing=0.0, sparkle_=0):
    """A tall varnished cabinet whose door is a gilt-framed portrait of a stern noble (black hat, white ruff,
    moustache). eyes -1/0/1 look left/centre/right; wink 0..2 closes the right eye; swing 0..1 opens the door on its
    left hinge onto shelves of gold."""
    fr = Fr((0, 13, 1.6)); r = fr.r
    block(r, -12, 11, -37, 0, "dwood", 0.0, top=0, curve=0.5)
    block(r, -13, 12, -39, -37, "dwood", 0.05, top=1)
    block(r, -12, 11, -3, 0, "dwood", 0.05, top=1)
    for x in (-10, 9):
        r.dot(x, -1, "brass", 3, 0.06)
    # the niche behind the door
    for y in range(-34, -4):
        for x in range(-9, 9):
            r.dot(x, y, "tar", 1 if y < -20 else 0, 0.1)
    block(r, -9, 8, -19, -18, "dwood", 0.11, top=1)
    block(r, -9, 8, -6, -5, "dwood", 0.11, top=1)
    for (x, y, m, t) in ((-6, -7, "ogold", 4), (-5, -7, "ogold", 2), (-4, -7, "ogold", 3), (-5, -8, "ogold", 4), (2, -7, "ogold", 2),
                         (3, -7, "ogold", 4), (3, -8, "ogold", 3), (-3, -20, "ogold", 4), (-2, -20, "ogold", 2)):
        r.dot(x, y, m, t, 0.12)
    r.dot(4, -20, "lviol", 4, 0.12); r.dot(4, -21, "lviol", 3, 0.12)
    # the door, squeezed toward the hinge at x = -10 as it swings
    W, Hh = 19, 31
    w = max(1, int(round(W * math.cos(swing * math.pi * 0.5))))

    def dx(u): return -10 + int(round(u * (w - 1) / (W - 1)))

    face = {}
    for v in range(Hh):
        for u in range(W):
            fr1 = u in (0, W - 1) or v in (0, Hh - 1)
            fr2 = u in (1, W - 2) or v in (1, Hh - 2)
            if fr1: face[(u, v)] = ("ogold", 4 if (u == 0 or v == 0) else 1)
            elif fr2: face[(u, v)] = ("ogold", 3 if (u + v) % 4 else 2)
            else: face[(u, v)] = ("dwood", 0 if (u + v) % 7 else 1)
    for v in range(4, 10):
        for u in range(6, 13): face[(u, v)] = ("tar", 2 if u < 9 else 1)
    for u in range(4, 15): face[(u, 9)] = ("tar", 2)
    face[(7, 6)] = ("velvet", 3)
    for v in range(10, 17):
        for u in range(7, 12): face[(u, v)] = ("wax", 3 if u > 7 else 2)
    for u in range(7, 12): face[(u, 10)] = ("wax", 2)
    ex = 1 + eyes
    face[(7 + ex, 12)] = ("tar", 0)
    face[(10 + ex, 12)] = ("tar", 0) if wink == 0 else ("wax", 1)
    if wink: face[(9 + ex, 12)] = ("wax", 1); face[(11 + ex, 12)] = ("wax", 1)
    face[(8, 11)] = ("dwood", 1); face[(11, 11)] = ("dwood", 1)
    for u in range(7, 12): face[(u, 14)] = ("dwood", 0)
    face[(6, 14)] = ("dwood", 0); face[(12, 14)] = ("dwood", 0)
    face[(9, 15)] = ("velvet", 2)
    for u in range(5, 14): face[(u, 17)] = ("paper", 4); face[(u, 18)] = ("paper", 3 if u % 2 else 2)
    for v in range(19, 29):
        for u in range(4, 15): face[(u, v)] = ("tar", 1) if u == 9 else ("tar", 2 if u < 9 else 1)
    face[(9, 21)] = ("ogold", 4); face[(9, 24)] = ("ogold", 3)
    dp = r.part(False, 0.4)
    for (u, v), (m, t) in face.items():
        if swing > 0.55 and not (u in (0, 1, W - 1, W - 2) or v in (0, 1, Hh - 2, Hh - 1)):
            m, t = "dwood", 3 if (u + v) % 4 else 2
        if w > 2:
            r.put(dx(u), -35 + v, 0.4, m, 0.5, dp, t)
    if w <= 2:
        for v in range(Hh):
            r.dot(-10, -35 + v, "ogold", 3, 0.4); r.dot(-9, -35 + v, "dwood", 3, 0.4)
    if sparkle_:
        fr.spark(dx(10 + ex), -23, "gleam", 1 if sparkle_ == 1 else 2)
    return fr.done()


@obj("ObjBPortrait")
def build_portrait():
    osheet("ObjBPortrait", [("Idle", [portrait_cab(0)], [0.2]), ("EyesL", [portrait_cab(-1)], [0.2]), ("EyesR", [portrait_cab(1)], [0.2]),
                            ("Wink", [portrait_cab(0, 1), portrait_cab(0, 2), portrait_cab(0, 2, sparkle_=1), portrait_cab(0, 2, sparkle_=2), portrait_cab(0, 0)],
                             [0.08, 0.1, 0.1, 0.12, 0.14]),
                            ("Swing", [portrait_cab(0, 0, s) for s in (0.15, 0.3, 0.45, 0.6, 0.8, 0.95)], [0.07] * 6),
                            ("Spent", [portrait_cab(0, 0, 0.97)], [0.2]), ("Vault", [portrait_cab(1)], [0.2])])


# ================================================================== 15. GOLDEN DUCK
def duck(glint=0, sq=0, open_=False):
    """A tiny golden rubber duck that squeaks; a glint runs across it."""
    fr = Fr((0, 6, 1.2)); r = fr.r
    r.ell(-0.5, -3.8 + sq * 0.5, 6.0 + sq * 0.6, 3.7 - sq * 0.6, "ogold", 0.1)
    r.dot(-6.5, -6, "ogold", 3, 0.11); r.dot(-6.5, -5, "ogold", 2, 0.11); r.dot(-7, -7, "ogold", 4, 0.11)
    hy = -8.5 + sq
    r.ell(2, hy, 2.9, 2.7, "ogold", 0.2)
    r.dot(2.5, hy - 1, "tar", 0, 0.21); r.dot(2, hy - 1.5, "gleam", 3, 0.215)
    r.dot(5, hy + 0.5, "rune", 3, 0.22); r.dot(6, hy + 0.5, "rune", 2, 0.22); r.dot(5, hy - 0.4, "rune", 4, 0.22)
    if open_: r.dot(5, hy + 1.5, "rune", 2, 0.22); r.dot(6, hy + 1.5, "velvet", 2, 0.22)
    r.tube([(-4, -3.5), (0, -3)], [0.8, 0.6], "ogold", 0.15, bias=-0.3)            # the wing
    gx = [-4, -2, 0, 2][glint % 4]
    gl(fr, gx, -6, "gleam", 4, 220)
    if glint == 2: gl(fr, gx + 1, -7, "gleam", 4)
    if glint == 3: fr.spark(4, hy - 3, "gleam", 1)
    return fr.done()


@obj("ObjBGoldenDuck")
def build_duck():
    osheet("ObjBGoldenDuck", [("Idle", [duck(glint=g) for g in range(4)], [0.3, 0.12, 0.12, 0.4]),
                              ("Use", [duck(sq=1), duck(sq=2, open_=True), duck(sq=1, open_=True), duck()], [0.05, 0.08, 0.08, 0.1]),
                              ("Vault", [duck(glint=3)], [0.2])])


# ================================================================== FX
class Pc(dict):
    """A palette-character canvas for the particle effects: (x, y) -> char."""

    def put(self, x, y, ch):
        self[(int(round(x)), int(round(y)))] = ch


def sparkle(c, x, y, size=1, ch='Э', ch2='y'):
    c.put(x, y, ch)
    for i in range(1, size + 1):
        cc = ch2 if i == size else ch
        for dx, dy in ((i, 0), (-i, 0), (0, i), (0, -i)):
            c.put(x + dx, y + dy, cc)


CONF = "ЖЦYЛФЭO"


def conf_piece(c, x, y, k, col):
    """A confetti scrap: a 2 px strip or a dot as it tumbles."""
    c.put(x, y, col)
    if k % 3 == 0: c.put(x + 1, y, col)
    elif k % 3 == 1: c.put(x, y + 1, col)


def note(fr, x, y, mat, fade=False):
    """An eighth note: a 2 x 2 head lit on its top left, a stem and a flag (no outline)."""
    t = 2 if fade else 3
    gl(fr, x, y, mat, t + 1); gl(fr, x + 1, y, mat, t); gl(fr, x, y + 1, mat, t); gl(fr, x + 1, y + 1, mat, t - 1)
    for i in range(1, 5): gl(fr, x + 2, y + 1 - i, mat, t)
    gl(fr, x + 3, y - 3, mat, t); gl(fr, x + 3, y - 2, mat, t - 1)


def fx_notes(t, n=12):
    """Music notes drifting up and swaying from the jukebox horn (origin = the horn mouth)."""
    fr = Fr()
    for k in range(3):
        tt = t - k * 2
        if tt < 0 or tt >= n: continue
        x = -2 + k * 4 + int(round(2 * math.sin(tt * 0.9 + k)))
        note(fr, x, -tt * 2, LIGHTS[(k + tt // 3) % 4], fade=tt >= n - 2)
    return fr.done(floor=False)


def fx_confetti_burst(t, gold=False, n=24, spd=3.4):
    c = Pc()
    rnd = random.Random(5 if not gold else 9)
    for k in range(n):
        a = rnd.uniform(math.pi * 1.05, math.pi * 1.95); sp = rnd.uniform(0.6, 1.0) * spd
        x = math.cos(a) * sp * (t + 1) * 1.6
        y = math.sin(a) * sp * (t + 1) * 1.4 + 0.55 * (t + 1) ** 2
        col = ("YyOЭ" if gold else CONF)[k % (4 if gold else 7)]
        if t >= 6 and k % 2: continue
        conf_piece(c, x, y - 4, k + t, col)
    if t == 0:
        sparkle(c, 0, -4, 2, 'Э', 'y' if gold else 'Ж')
    return pal(c)


def fx_confetti_rain(t):
    """A 40 x 30 patch of confetti falling (loops)."""
    c = Pc()
    rnd = random.Random(21)
    for k in range(16):
        x0 = rnd.randint(-20, 20); y0 = rnd.randint(-30, 0)
        y = ((y0 + t * 4 + 30) % 32) - 30
        x = x0 + int(round(1.5 * math.sin((y + k) * 0.5)))
        conf_piece(c, x, y, k + t, CONF[k % 7])
    return pal(c)


def fx_blast(t):
    """Confetti cone from the cannon mouth (origin), to the right, 48 px."""
    c = Pc()
    rnd = random.Random(33)
    reach = [10, 22, 34, 44, 48, 48, 48][t]
    for k in range(60):
        d = rnd.uniform(0, 1) * reach
        a = rnd.uniform(-0.5, 0.5)
        x, y = d * math.cos(a), -6 + d * math.sin(a) * 0.8 + (t - 3) * 0.8 * (d / 48.0) * (t > 3)
        if t >= 5 and rnd.random() < 0.4 + 0.25 * (t - 5): continue
        conf_piece(c, x, y, k + t, CONF[k % 7])
    if t <= 1:
        for k in range(8):
            a = -0.6 + k * 0.17
            for rr in range(2, 5 + t * 3):
                c.put(rr * math.cos(a), -6 + rr * math.sin(a), 'Э' if rr < 4 else 'y')
    return pal(c)


def fx_rocket(t):
    """A small striped rocket flying right (the code rotates it): a red cone, a shaded body and a spark trail."""
    fr = Fr()
    for x in range(-3, 3):
        band = (x // 2) % 2
        gl(fr, x, -1, "ppink" if band else "cream", 4 if band else 4)
        gl(fr, x, 0, "ppink" if band else "cream", 2)
    gl(fr, 3, -1, "velvet", 4); gl(fr, 3, 0, "velvet", 2); gl(fr, 4, -1, "velvet", 3)
    gl(fr, -4, -2, "pcyan", 3); gl(fr, -4, 1, "pcyan", 2)
    for k in range(5):
        x = -5 - k * 2 - (t % 2)
        y = int(round(math.sin(k + t) * (k * 0.4)))
        gl(fr, x, y, "gleam" if k == 0 else "rune", [4, 4, 3, 2, 1][k], [255, 255, 230, 190, 150][k])
    return fr.done(floor=False)


def fx_firework(t, col):
    """Firework burst: a ring of sparks expands, then droops and fades (7 frames)."""
    d, m, l = col
    c = Pc()
    if t == 0:
        sparkle(c, 0, -14, 2, 'Э', l)
        return pal(c)
    rr = [0, 5, 9, 12, 14, 15, 15][t]
    droop = [0, 0, 0, 1, 3, 5, 7][t]
    for k in range(16):
        a = k * math.pi / 8
        for j in range(3 if t < 5 else 1):
            rj = rr - j * 2
            if rj <= 0: continue
            x, y = rj * math.cos(a), -14 + rj * math.sin(a) * 0.85 + droop * (rj / 15.0)
            ch = (l if j == 0 else m) if t < 4 else (m if j == 0 else d)
            if t == 6 and k % 2: continue
            c.put(x, y, ch)
    if t < 3: c.put(0, -14, 'Э')
    if 1 <= t <= 3:
        for i in range(-6, 7):
            if abs(i) < 6 - t: c.put(i, 0, m)
    return pal(c)


def fx_spores(t):
    c = Pc()
    rnd = random.Random(8)
    for k in range(14):
        a = rnd.uniform(0, 2 * math.pi); sp = rnd.uniform(0.6, 1.0)
        rr = (t + 1) * 2.4 * sp
        x, y = rr * math.cos(a), -3 + rr * math.sin(a) * 0.5 - t * 0.6
        if t >= 4 and k % 2: continue
        c.put(x, y, 'F' if k % 3 else ('Р' if t < 3 else 'р'))
    return pal(c)


def coin(fr, x, y, flip):
    """A 3 x 2 gold coin, lit on its top-left; flip 1 shows it edge-on."""
    if flip == 1:
        gl(fr, x, y - 1, "lyel", 4); gl(fr, x, y, "lyel", 2)
    else:
        for dx in (-1, 0, 1):
            gl(fr, x + dx, y - 1, "lyel", 4 if dx < 1 else 3); gl(fr, x + dx, y, "lyel", 2 if dx < 1 else 1)
        gl(fr, x - 1, y - 1, "gleam", 4)


def fx_coins(t):
    """A fountain of gold coins (payout, pinata, reliquary) that bounce and settle."""
    fr = Fr()
    rnd = random.Random(4)
    for k in range(12):
        vx = rnd.uniform(-2.2, 2.2); vy = rnd.uniform(-5.5, -3.5)
        tt = t + 0.5
        x, y = vx * tt * 1.6, vy * tt * 1.6 + 0.9 * tt * tt * 1.6
        if y > 0: y = 0
        if t >= 6 and k % 2: continue
        coin(fr, x, y - 1, (k + t) % 3)
    if t < 2: fr.spark(0, -3, "gleam", 2 - t)
    return fr.done(floor=False)


def fx_well_spirit(t):
    """The Well Spirit rises from the water: a luminous water maiden with streaming hair who spreads her arms and
    bursts into spray (11 frames)."""
    fr = Fr()
    rise = min(1.0, t / 5.0)
    top = int(-6 - 22 * rise)
    if t < 8:
        for y in range(top, 1):
            w = 1 + int((y - top) * 0.2)
            for x in range(-w, w + 1):
                u = x / float(w + 0.5)
                gl(fr, x, y, "lcyan", 4 if u < -0.3 else 3 if u < 0.35 else 2, 235)
            if (y + t) % 4 == 0: gl(fr, -w + 1, y, "gleam", 4, 200)
        if rise > 0.6:
            for y in range(top - 5, top + 1):
                for x in range(-3, 4):
                    if (x / 2.6) ** 2 + ((y - top + 2.5) / 2.8) ** 2 <= 1.0:
                        gl(fr, x, y, "lcyan", 4 if x < 0 and y < top - 2 else 3)
            gl(fr, -1, top - 2, "water", 1); gl(fr, 1, top - 2, "water", 1)
            for k in range(6):
                sw = int(round(math.sin(t * 0.8 + k * 0.6)))
                gl(fr, -3 - k // 2 + sw, top - 3 + k, "lcyan", 2); gl(fr, 3 + k // 2 + sw, top - 3 + k, "lcyan", 2)
        if t >= 5:
            arm = min(7, (t - 4) * 3)
            for i in range(arm):
                gl(fr, -2 - i, top + 5 - i // 2, "lcyan", 3); gl(fr, 2 + i, top + 5 - i // 2, "lcyan", 3)
    rnd = random.Random(t)
    for k in range(4 + t):
        gl(fr, rnd.randint(-10, 10), rnd.randint(max(-34, top - 6), 0), "gleam" if k % 2 else "lcyan", 4)
    if t >= 8:
        for k in range(18):
            a = k * math.pi / 9; rr = 6 + (t - 8) * 6
            gl(fr, rr * math.cos(a), max(-34, -16 + rr * math.sin(a) * 0.7), "lcyan" if k % 2 else "gleam", 4 if t < 10 else 3)
    return fr.done(floor=False)


def fx_card(t):
    """A fortune card flicks up out of the slot, turns over, glows and fades."""
    fr = Fr()
    y = -2 - [0, 5, 10, 13, 15, 16][t]
    w = [2, 1, 0, 1, 2, 2][t]
    for yy in range(y - 6, y + 1):
        for xx in range(-w, w + 1):
            edge = abs(xx) == w or yy in (y - 6, y)
            if t < 2 or w == 0: gl(fr, xx, yy, "pviol", 3 if xx <= 0 else 2)            # the back
            else: gl(fr, xx, yy, "paper", 3 if edge else 4)
    if w >= 1 and t >= 2:
        gl(fr, 0, y - 3, "lviol", 4); gl(fr, 0, y - 2, "lviol", 3); gl(fr, -1, y - 3, "lviol", 3); gl(fr, 1, y - 3, "lviol", 3)
    if t >= 3: fr.spark(3, y - 6, "gleam", 1)
    return fr.done(floor=False)


def fx_sparkle(t):
    """Secret found: a violet and gold twinkle (5 frames)."""
    c = Pc()
    s = [1, 2, 3, 2, 1][t]
    sparkle(c, 0, -8, s, 'Э', 'F' if t % 2 else 'y')
    for k in range(4):
        a = k * math.pi / 2 + t * 0.4
        rr = 4 + t * 2
        c.put(rr * math.cos(a), -8 + rr * math.sin(a), 'Ф' if k % 2 else 'Y')
    return pal(c)


def fx_dust(t):
    c = Pc()
    rnd = random.Random(2)
    for k in range(12):
        a = rnd.uniform(math.pi, 2 * math.pi); sp = rnd.uniform(0.5, 1.0)
        rr = (t + 1) * 2.0 * sp + 1
        x, y = rr * math.cos(a) * 1.4, rr * math.sin(a) * 0.6 - t * 0.5
        if t >= 4 and k % 2: continue
        c.put(x, y, 'Д' if k % 3 else ('S' if t < 3 else 's'))
        if t < 2 and k % 4 == 0: c.put(x + 1, y, 'S')
    return pal(c)


CROWN = ["3.4.3", "3.3.3", "34332", "3p3c2", "22221"]


def fx_jackpot(t):
    """Jackpot: a big gold crown pops up over the machine and spins coins out (8 frames). Origin = the crest."""
    fr = Fr()
    lift = [0, 4, 7, 9, 10, 10, 10, 10][t]
    cy = -6 - lift
    if t < 7:
        for yy, row in enumerate(CROWN):
            for xx, c in enumerate(row):
                if c == ".": continue
                for (ox, oy) in ((0, 0), (1, 0), (0, 1), (1, 1)):
                    X, Y = (xx - 2) * 2 + ox, cy + yy * 2 + oy
                    if c == "p": gl(fr, X, Y, "lpink", 4 - oy)
                    elif c == "c": gl(fr, X, Y, "lcyan", 4 - oy)
                    else: gl(fr, X, Y, "lyel", max(1, int(c) - (1 if ox + oy == 2 else 0)))
        gl(fr, -4, cy, "gleam", 4)
    for k in range(8):
        a = k * math.pi / 4 + t * 0.3
        rr = 6 + t * 3
        x, y = rr * math.cos(a), cy + 4 + rr * math.sin(a) * 0.6
        if k % 2: coin(fr, x, y, (k + t) % 3)
        else: gl(fr, x, y, "gleam", 4)
    return fr.done(floor=False)


def fx_statue_form(t):
    """Stone dust swirls up into a column over the altar plinth (origin = plinth top centre)."""
    c = Pc()
    h = [4, 8, 12, 16, 20, 22, 18, 10][t]
    for k in range(18):
        yy = -int(k * h / 18.0)
        a = k * 0.9 + t * 1.3
        rr = 5 - k * 0.15 + (2 if t >= 6 else 0)
        c.put(rr * math.cos(a), yy, 'д' if math.sin(a) > 0 else 'S')
    if t >= 4:
        sparkle(c, 0, -h - 1, 1 if t < 6 else 2, 'Э', 'Ф')
    return pal(c)


def ind_notes(n, ph):
    """Groove indicator: n little notes in a row over the head, bobbing (origin = bottom centre)."""
    fr = Fr()
    for i in range(n):
        x = int(round((i - (n - 1) / 2.0) * 4)) - 1
        y = -1 - ((i + ph) % 2)
        mat = LIGHTS[i]
        gl(fr, x, y, mat, 4); gl(fr, x + 1, y, mat, 3); gl(fr, x, y + 1, mat, 3); gl(fr, x + 1, y + 1, mat, 2)
        for k in range(1, 4): gl(fr, x + 2, y + 1 - k, mat, 3)
        gl(fr, x + 3, y - 2, mat, 2)
    return fr.done(floor=False)


def ind_fever(ph):
    """Disco Fever: coloured light specks circling the feet (body overlay, origin = feet)."""
    c = Pc()
    for k in range(6):
        a = k * math.pi / 3 + ph * 0.5
        x, y = 8 * math.cos(a), -1 + 3 * math.sin(a)
        c.put(x, y, "ЖЦYЛФЭ"[(k + ph) % 6])
        if k % 2 == 0: c.put(x, y - 1, 'Э')
    return pal(c)


def ind_hat(ph):
    """Party Time: a tiny striped party hat with a pom-pom (head overlay, origin = bottom centre)."""
    fr = Fr(); r = fr.r
    hp = r.part(False, 0.1)
    for y in range(0, 7):
        w = (6 - y) / 2.0
        for x in range(int(math.floor(-w)), int(math.ceil(w)) + 1):
            if abs(x) > w + 0.3: continue
            m = "ppink" if (y + x) % 3 else "pyel"
            r.put(x, -y, 0.1, m, lam(x / 3.5 - 0.3, -0.3, 0.8), hp)
    r.ell(ph * 2 - 1 if ph else 0, -7.5, 1.3, 1.2, "pcyan", 0.2)
    gl(fr, 3 + ph, -2, "llime", 4); gl(fr, 4 + ph, -1, "lviol", 4)
    return fr.done(floor=False)


@obj("FxObjB")
def build_fx():
    fxsheet("FxObjBNotes", [("Float", [fx_notes(t) for t in range(12)], [0.08] * 12)])
    fxsheet("FxObjBConfetti", [("Burst", [fx_confetti_burst(t) for t in range(8)], [0.05, 0.05, 0.06, 0.06, 0.07, 0.08, 0.1, 0.12]),
                               ("Rain", [fx_confetti_rain(t) for t in range(8)], [0.08] * 8),
                               ("Gold", [fx_confetti_burst(t, gold=True) for t in range(8)], [0.05, 0.05, 0.06, 0.06, 0.07, 0.08, 0.1, 0.12])])
    fxsheet("FxObjBConfettiBlast", [("Blast", [fx_blast(t) for t in range(7)], [0.04, 0.04, 0.05, 0.06, 0.08, 0.1, 0.12])])
    fxsheet("FxObjBRocket", [("Fly", [fx_rocket(t) for t in range(4)], [0.06] * 4)])
    fxsheet("FxObjBFirework", [(n, [fx_firework(t, c) for t in range(7)], [0.05, 0.05, 0.06, 0.08, 0.1, 0.12, 0.14])
                               for n, c in (("Pink", ("ж", "Ж", "F")), ("Gold", ("O", "Y", "y")), ("Cyan", ("ц", "Ц", "c")), ("Lime", ("л", "Л", "G")))])
    fxsheet("FxObjBSpores", [("Puff", [fx_spores(t) for t in range(6)], [0.05, 0.05, 0.06, 0.07, 0.08, 0.1])])
    fxsheet("FxObjBCoins", [("Burst", [fx_coins(t) for t in range(8)], [0.05, 0.05, 0.06, 0.06, 0.07, 0.08, 0.1, 0.12])])
    fxsheet("FxObjBWellSpirit", [("Rise", [fx_well_spirit(t) for t in range(11)], [0.1] * 5 + [0.12, 0.14, 0.2, 0.08, 0.08, 0.1])])
    fxsheet("FxObjBCard", [("Pop", [fx_card(t) for t in range(6)], [0.05, 0.06, 0.08, 0.1, 0.14, 0.2])])
    fxsheet("FxObjBSparkle", [("Twinkle", [fx_sparkle(t) for t in range(5)], [0.06, 0.07, 0.08, 0.09, 0.1])])
    fxsheet("FxObjBDust", [("Puff", [fx_dust(t) for t in range(6)], [0.05, 0.05, 0.06, 0.07, 0.08, 0.1])])
    fxsheet("FxObjBJackpot", [("Flash", [fx_jackpot(t) for t in range(8)], [0.06, 0.06, 0.08, 0.1, 0.12, 0.14, 0.14, 0.1])])
    fxsheet("FxObjBStatueForm", [("Form", [fx_statue_form(t) for t in range(8)], [0.08] * 8)])
    fxsheet("FxObjBInd", [("Groove1", [ind_notes(1, p) for p in (0, 1)], [0.25, 0.25]),
                          ("Groove2", [ind_notes(2, p) for p in (0, 1)], [0.25, 0.25]),
                          ("Groove3", [ind_notes(3, p) for p in (0, 1)], [0.25, 0.25]),
                          ("Groove4", [ind_notes(4, p) for p in (0, 1)], [0.25, 0.25]),
                          ("Hat", [ind_hat(p) for p in (0, 1)], [0.3, 0.3])])
    fxsheet("FxObjBIndFever", [("Fever", [ind_fever(p).shift(0, -2) for p in range(6)], [0.08] * 6)])


# ================================================================== anchor points the C# uses (pixels from the floor point, y up NEGATIVE)
ANCHORS = [
    ("ObjBJukebox", "horn mouth (FxObjBNotes)", HORN),
    ("ObjBDiscoBall", "ball centre", (int(BALL[0]), int(BALL[1]))),
    ("ObjBDiscoBall", "dance tiles: 3 x 3 grid centred on the floor point", "spacing 14 x 10"),
    ("ObjBConfettiCannon", "muzzle (FxObjBConfettiBlast origin; its art runs 6 px above the origin)", MUZZLE),
    ("ObjBSlotMachine", "reel centres (FxObjBSlotSymbols)", ", ".join("(%d, %d)" % (x, REEL_Y) for x in REEL_X)),
    ("ObjBSlotMachine", "crest (FxObjBJackpot)", CREST),
    ("ObjBFortuneTeller", "card slot (FxObjBCard)", CARD_SLOT),
    ("ObjBBounceShroom", "cap top (FxObjBSpores)", CAP_TOP),
    ("ObjBFireworkCrate", "rocket launch point", LAUNCH),
    ("ObjBLeverTrio", "lever pivots (FxObjBLever)", ", ".join("(%d, %d)" % (x, LEVER_Y) for x in LEVER_X)),
    ("ObjBLeverTrio", "plaque centres (FxObjBGlyphs Sun/Moon/Star)", ", ".join("(%d, %d)" % (x, PLAQUE_Y) for x in LEVER_X)),
    ("ObjBLeverTrio", "floor scratches (FxObjBGlyphs Scratch*), the order clue", ", ".join("(%d, 8)" % x for x in LEVER_X)),
    ("ObjBLeverTrio", "hatch (ObjBHatch floor point)", (0, 24)),
    ("ObjBCrackedWall", "niche shelf (key drop)", NICHE),
    ("ObjBKeyhole", "keyhole", KEYHOLE),
    ("ObjBSculptorAltar", "statue spawn + FxObjBStatueForm, in front of the altar", STATUE_AT),
    ("ObjBWishingWell", "water centre (FxObjBWellSpirit)", WATER),
    ("ObjBPortrait", "niche gold (FxObjBCoins)", NICHE_GOLD),
]


def write_timing(outdir):
    L = ["# Objects (part two): sprite timing", "",
         "Generated by `tools/sprites/objects2_rigs.py`. Frame indices are 0-based; durations in seconds.",
         "Object sheets: floor point = (cellW//2, cellH-2) (ObjectKit). FX sheets: the origin pixel ObjectPack2.cs pins.", "",
         "| Sheet | Cell (w x h) | Anims (frames: durations) |", "|---|---|---|"]
    for name, kind in SHEETS:
        b = BUILT[name]
        cw, ch = b["cell"]
        L.append("| %s | %d x %d | %s |" % (name, cw, ch, "; ".join("%s %d: %s" % (a, n, ", ".join("%.2f" % x for x in d)) for a, n, d in b["anims"])))
    L += ["", "## Anchor points (pixels from the floor point, x right, y up NEGATIVE; the C# uses x, -y)", "",
          "| Sheet | Point | Pixels |", "|---|---|---|"]
    for sh, what, pt in ANCHORS:
        L.append("| %s | %s | %s |" % (sh, what, pt if isinstance(pt, str) else "(%d, %d)" % pt))
    L += ["", "## Sync moments", "",
          "- ObjBSlotMachine Use (8 frames, 0.70 s): lever bottoms out on frame 2; reels blur 2-7; the code reveals the",
          "  three symbols at 0.75 / 0.95 / 1.15 s and plays Win on a paying line.",
          "- ObjBConfettiCannon Use: the blast leaves on frame 2 (0.24 s).",
          "- ObjBFireworkCrate: Lit loops for the 2.0 s fuse, Launch frames 0-2 release two rockets each.",
          "- ObjBPinata Hit 0.28 s, Burst 0.48 s (confetti + coins on frame 1).",
          "- ObjBCrackedWall Crumble 0.65 s (the key drops at its end).",
          "- ObjBKeyhole Unlock 0.92 s, then ObjBReliquary Rise 0.40 s at the same floor point.",
          "- ObjBSculptorAltar Use 0.74 s (strikes on frames 2 and 5), the statue appears at its end.",
          "- ObjBWishingWell Use 0.41 s (the coin lands on frame 3); Wish 0.72 s.",
          "- ObjBPortrait Wink 0.54 s then Swing 0.42 s."]
    open(os.path.join(outdir, "TIMING.md"), "w").write("\n".join(L) + "\n")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
        args = [a for a in args if a != sys.argv[sys.argv.index("--only") + 1]]
    out = args[0] if args else DEFAULT_OUT
    os.makedirs(out, exist_ok=True)
    K.OUT = out
    for name, fn in REGISTRY.items():
        if only and name not in only: continue
        fn()
    if not only: write_timing(out)


if __name__ == "__main__":
    main()
