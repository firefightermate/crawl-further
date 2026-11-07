"""CUSTOM GHOSTS (the silver and gold ghost slots): the parts a player builds their ghost from, plus the silver /
gold portrait frames, and src/CrawlFurther/Ghosts/GhostCustomData.cs (the choice tables the C# compositor and the editor read).

    python3 ghost_custom.py [--out dir]

Parts (composed per player at run time by GhostCustom.cs, exactly like compose() below):
  CustomGhostBody    54 x 50 cells (the vanilla ghost cell and anchor). For each SHAPE: <Shape>Spawn 10, <Shape>Idle 6,
                     <Shape>Run 6. Drawn in KEY colours, not final ones: shroud keys (10,0,1..4), skin keys (11,0,1..4),
                     glow keys (12,0,1..3); the chosen COLOUR replaces them (alpha kept). Two marker pixels per frame:
                     (14,0,0) = the eye anchor (between the eyes), (15,0,0) = the tail tip (trail anchor). The compositor
                     removes each marker (it takes the colour of the pixel to its left).
  CustomGhostEyes    11 x 7 cells, origin (5, 3) = the eye anchor. One anim per EYES style, 2 frames (frame = body frame
                     index mod 2): glow keys + literal darks.
  CustomGhostTrails  30 x 28 cells, origin (18, 12) = the tail tip. One anim per TRAIL style, 6 frames (body frame mod 6),
                     drawn behind the body: glow keys + shroud keys.
  CustomGhostFrames    29 x 24 portrait backgrounds, opaque: Silver 4, Gold 4 (a metal frame with its own shimmer / glint);
                     the custom ghost's Idle frames are pasted in a per-shape window (WinX / WinY in GhostCustomData.cs).
  GhostSilver, GhostGold   29 x 24 portraits (Idle 4) with the default look, for the vault and as a fallback.
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srcfiles import src_file, pack_files  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ghost_forms as GF  # noqa: E402
import ghost_v11kit as KT  # noqa: E402
from ghost_forms import Pose, _T, arm, ell, tube, line, P  # noqa: E402
from anim import pack, preview  # noqa: E402
from rig import Canvas  # noqa: E402
from ghosts_v2_kit import mute_rgb as KT_mute  # noqa: E402
from PIL import Image  # noqa: E402

OUT = [KT.OUT]
CS_OUT = src_file("GhostCustomData.cs")
CELL = GF.CELL
ORIGIN = GF.ORIGIN
SA = 158                 # body alpha (the vanilla ghost's)

# key colours (rgb); the alpha travels with the pixel
SH = [(10, 0, 1), (10, 0, 2), (10, 0, 3), (10, 0, 4)]
SK = [(11, 0, 1), (11, 0, 2), (11, 0, 3), (11, 0, 4)]
GL = [(12, 0, 1), (12, 0, 2), (12, 0, 3)]
EYE_MARK = (14, 0, 0)
TAIL_MARK = (15, 0, 0)
DARK = (22, 18, 24)
DARK2 = (52, 46, 58)

# ghost_forms chars -> key colour + alpha
CHARMAP = {'a': SH[0] + (SA,), 'b': SH[1] + (SA,), 'c': SH[2] + (SA,), 'd': SH[3] + (SA,),
           '1': SH[0] + (96,), '2': SH[1] + (120,), '3': SH[0] + (60,),
           'h': SK[0] + (SA,), 'i': SK[1] + (SA,), 'j': SK[2] + (SA,), 'k': SK[3] + (SA,),
           'M': DARK + (210,), 'O': DARK2 + (200,), 'e': SK[2] + (SA,)}

# ------------------------------------------------------------------ choices (names shown in the editor)
SHAPES = [("Hag", "HAG"), ("Hood", "HOODED"), ("Sheet", "SHEET"), ("Horned", "HORNED"), ("Skull", "SKULL WISP"), ("Serpent", "SERPENT")]
EYES = [("Glow", "GLOW"), ("Hollow", "HOLLOW"), ("Slits", "SLITS"), ("Cyclops", "CYCLOPS"), ("Stars", "STARS")]
TRAILS = [("None", "NONE"), ("Mist", "MIST"), ("Embers", "EMBERS"), ("Motes", "MOTES"), ("Chains", "CHAINS")]
# COLOUR: 4 shroud (dark -> light), 4 skin (dark -> light), 3 glow (dark -> light)
COLOURS = [
    ("Ash", "ASH", ["5e625a", "7a8074", "969c8c", "b2b8a4"], ["8e8e60", "aaac76", "c8c892", "e0e0b0"], ["a14a3a", "e0886a", "ffc8a8"]),
    ("Frost", "FROST", ["4a6a8a", "6a92b4", "92bad6", "c2e2f4"], ["8aa6c0", "aac4da", "cce2f2", "eef8ff"], ["2a7aa8", "6ad0ff", "e0fcff"]),
    ("Ember", "EMBER", ["6a2a1a", "963c20", "c45a28", "e88a3a"], ["a8784a", "c89a5e", "e2bc7a", "f8dca0"], ["c03010", "ff8a20", "fff0a0"]),
    ("Verdant", "VERDANT", ["2a5a34", "3e7e44", "5aa45a", "86cc78"], ["7a9a5a", "9cba70", "bed88c", "dcf0aa"], ["2a8a3a", "7fe060", "e8ffc0"]),
    ("Violet", "VIOLET", ["4a2a6a", "684090", "8a5cb4", "b48ad8"], ["9a7aaa", "b496c4", "d0b4dc", "ecd8f4"], ["7a2ab0", "d070ff", "f8d8ff"]),
    ("Abyss", "ABYSS", ["16141e", "24202e", "36304a", "4c4466"], ["4a4458", "62586e", "7c7088", "9a8ca6"], ["8a1a3a", "ff3a6a", "ffc0d0"]),
    ("Blood", "BLOOD", ["4a1218", "701c24", "962a30", "c04a48"], ["a87a6a", "c49a86", "dcb8a2", "f2d8c4"], ["a81010", "ff4030", "ffd0a0"]),
    ("Silver", "SILVER", ["6a7080", "8e96a6", "b6bcca", "e0e4ee"], ["9aa0aa", "b8bec8", "d6dce4", "f4f6fa"], ["6a8ab0", "c8e0ff", "ffffff"]),
    ("Gilded", "GILDED", ["7a5418", "a4741e", "d0a030", "f0cc5a"], ["b49a6a", "d0b884", "e8d4a4", "fcf0cc"], ["c08010", "ffd040", "fff8d0"]),
]
DEFAULT = {"Silver": (1, 7, 0, 1), "Gold": (3, 8, 0, 3)}   # (shape, colour, eyes, trail) per tier


def hx(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def recolor(c, col):
    _, _, shr, skn, glw = COLOURS[col]
    r, g, b = c[:3]
    if g == 0 and 1 <= b <= 4:
        if r == 10: return hx(shr[b - 1]) + c[3:]
        if r == 11: return hx(skn[b - 1]) + c[3:]
        if r == 12 and b <= 3: return hx(glw[b - 1]) + c[3:]
    return c


# ================================================================== body shapes
class KC(Canvas):
    """A Canvas taking ghost_forms chars, translated to key colours on the way out."""

    def keyed(self):
        out = {}
        for k, v in self.px.items():
            if isinstance(v, tuple): out[k] = v if len(v) == 4 else v + (255,)
            elif v in CHARMAP: out[k] = CHARMAP[v]
        return out


def face(c, p, cx, cy, mouth="hum"):
    """A plain hag face without eyes (the eyes layer is stamped on the anchor), marker at the anchor."""
    g = GF.HEADS[mouth]
    X0, Y0 = int(round(cx)) - 3, int(round(cy)) - 3
    for j, row in enumerate(g):
        for i, ch in enumerate(row):
            if ch == '.': continue
            if ch in 'eO' and j == 2: ch = 'j' if ch == 'e' else 'i'
            c.put(X0 + i, Y0 + j, ch)
    c.put(X0 + 2, Y0 + 2, EYE_MARK + (255,))


def tail_mark(c, p):
    tip = P(*_T(p, -12.6 * p.tail, -7.0 + p.sway * 1.4))
    c.put(tip[0], tip[1], TAIL_MARK + (255,))


def dark(c, x, y, a=230):
    c.put(*P(x, y), DARK + (a,))


def shape_hag(c, p, mouth="hum"):
    """The hunched crone: bent forward, long hair streaming down her back, both clawed hands reaching out low."""
    q = Pose(**dict(p.__dict__)); q.lean = p.lean + 2.0; q.bob = p.bob + 2.0
    q.back = (9.0 + (p.back[0] - 8.5) * 0.4, -12.5 + (p.back[1] + 21.0) * 0.3) if p.back else None
    q.front = (11.5 + (p.front[0] - 10.0) * 0.4, -10.5 + (p.front[1] + 18.0) * 0.3) if p.front else None
    if q.back: arm(c, q, (5.2, -12.5), _T(q, *q.back), claw=True, front=False, bend=1)
    # long hair: thick strands falling down her back to the tail
    hx_, hy_ = _T(q, 1.5, -17.5)
    for k, (dx, L) in enumerate(((-1.0, 11), (-2.5, 13), (0.5, 9), (-3.8, 10))):
        pts = [(hx_ + dx, hy_), (hx_ + dx - 4 - q.hair * 0.6, hy_ + L * 0.45), (hx_ + dx - 8 - q.hair, hy_ + L * 0.8 + q.sway)]
        tube(c, pts, [1.5, 1.1, 0.5], "abc" if k % 2 == 0 else "ab", bias=-0.05)
        c.put(*P(pts[-1][0] - 1, pts[-1][1] + 1), '1')
    GF.hair(c, q, wild=True)
    GF.shroud(c, q)
    face(c, q, *_T(q, 3.2, -16.0), mouth=mouth)
    if q.front: arm(c, q, (1.2, -12.0), _T(q, *q.front), claw=True, front=True, bend=1)
    tail_mark(c, q)


def shape_hood(c, p, mouth="hum"):
    """A tall robed wraith: an upright robe longer than the others, a deep pointed cowl, no arms (the sleeves are folded
    into the robe), a ragged hem that drifts back into a short tail."""
    sw = p.sway
    top = _T(p, 1.2, -27.5)
    pts = [_T(p, 1.2, -22.0), _T(p, 1.0, -16.0), _T(p, 0.4, -10.0), _T(p, -0.6, -5.5), _T(p, -3.5 * p.tail, -2.8 + sw * 0.4),
           _T(p, -7.5 * p.tail, -2.6 + sw * 0.8)]
    tube(c, pts, [3.6, 4.6, 5.3, 5.4, 3.0, 1.0], "abcd", bias=0.05)
    # robe folds and tatters along the hem
    for x in (-3.5, -1.0, 1.5, 3.5):
        X, Y = P(*_T(p, x + 0.3 * sw, -1.0))
        c.put(X, Y, 'a'); c.put(X, Y + 1, '1')
    for (x0, y0, x1, y1) in ((2.4, -19.0, 2.8, -7.0), (-1.4, -18.0, -2.0, -6.0)):
        line(c, *_T(p, x0, y0), *_T(p, x1, y1), 'a')
    # the cowl: a tall peak trailing back
    hx_, hy_ = _T(p, 1.8, -23.2)
    ell(c, hx_ - 0.4, hy_, 4.2, 4.4, "abcd", bias=0.12)
    tube(c, [(hx_ - 0.5, hy_ - 3.8), (top[0] - 2.5, top[1] - 0.5), (top[0] - 5.0 - p.hair, top[1] + 1.5)], [1.8, 1.2, 0.5], "bcd")
    for (dx, dy) in ((0, -2), (1, -2), (2, -2), (0, -1), (1, -1), (2, -1), (3, -1), (0, 0), (1, 0), (2, 0), (3, 0), (1, 1), (2, 1), (1, 2)):
        dark(c, hx_ + dx, hy_ + dy)
    # a clasp at the throat
    c.put(*P(hx_ + 1.0, hy_ + 4.0), 'k'); c.put(*P(hx_ + 2.0, hy_ + 4.0), 'i')
    c.put(*P(hx_ + 1.5, hy_ - 1), EYE_MARK + (255,))
    tip = P(*_T(p, -8.6 * p.tail, -3.0 + sw * 0.9))
    c.put(tip[0], tip[1], TAIL_MARK + (255,))


def shape_sheet(c, p, mouth="hum"):
    """The classic sheet ghost: a round dome of cloth with a wavy hem and two stub arms, no hair."""
    cx, cy = _T(p, 1.5, -13.0)
    ell(c, cx, cy, 6.0 * p.squash, 6.6, "abcd", bias=0.15)
    tube(c, [(cx, cy + 3), (cx - 2, cy + 7), (cx - 6 * p.tail, cy + 8 + p.sway), (cx - 10 * p.tail, cy + 6 + p.sway * 1.4)],
         [5.6, 4.6, 2.4, 0.8], "abcd", bias=0.05)
    for k, x in enumerate((-3, -1, 1, 3)):
        X, Y = P(cx + x, cy + 9.6 + (0.5 if (k + int(p.sway * 2)) % 2 else -0.5))
        c.put(X, Y, '1')
    for (dx, dy, ch) in ((6.0, 0.0, 'b'), (6.6, -1.0, 'c'), (-5.6, 1.0, 'a')):
        c.put(*P(cx + dx, cy + dy + (p.front[1] + 21.0) * 0.15 if p.front else cy + dy), ch)
    mx, my = P(cx + 2.4, cy + 2.2)
    c.put(mx, my, DARK + (210,)); c.put(mx + 1, my, DARK + (210,))
    if mouth == "wail": c.put(mx, my + 1, DARK + (210,)); c.put(mx + 1, my + 1, DARK + (210,))
    c.put(*P(cx + 2.0, cy - 1.4), EYE_MARK + (255,))
    tip = P(cx - 10 * p.tail - 1, cy + 5 + p.sway * 1.4)
    c.put(tip[0], tip[1], TAIL_MARK + (255,))


def shape_horned(c, p, mouth="grit"):
    """A broad-shouldered demon shade: a bulky chest and shoulders, a small head with big curling horns, heavy arms
    hanging to clenched fists, a short thick tail of smoke under the chest."""
    sw = p.sway
    # tail first (behind the chest)
    pts = [_T(p, 0.5, -8.0), _T(p, -2.0, -4.0), _T(p, -6.0 * p.tail, -2.6 + sw * 0.6), _T(p, -9.5 * p.tail, -3.6 + sw * 1.2)]
    tube(c, pts, [4.0, 3.0, 1.6, 0.6], "abc", bias=0.0)
    # far arm
    f = (p.front[1] + 18.0) * 0.3 if p.front else 0.0
    sh_b = _T(p, -4.0, -15.0); fist_b = _T(p, -6.5, -7.5 + f)
    tube(c, [sh_b, ((sh_b[0] + fist_b[0]) / 2 - 1.0, (sh_b[1] + fist_b[1]) / 2), fist_b], [2.0, 1.7, 1.6], "hij", bias=-0.1)
    # chest + shoulders
    ell(c, *_T(p, 0.5, -14.0), 7.4 * p.squash, 5.6, "abcd", bias=0.1)
    ell(c, *_T(p, -4.2, -16.5), 3.0, 2.6, "bcd", bias=0.2)
    ell(c, *_T(p, 5.0, -16.5), 3.2, 2.7, "bcd", bias=0.25)
    for (x, y) in ((0.5, -15.0), (1.0, -13.0), (0.5, -11.0)):   # a seam down the chest
        c.put(*P(*_T(p, x, y)), 'a')
    # head: small, low between the shoulders, jaw jutting
    hx_, hy_ = _T(p, 2.6, -21.0)
    ell(c, hx_, hy_, 2.9, 2.7, "hijk", bias=0.15)
    ell(c, hx_ + 1.0, hy_ + 2.0, 2.0, 1.2, "hij", bias=0.0)
    dark(c, hx_ + 0.5, hy_ + 2.0, 200); dark(c, hx_ + 1.5, hy_ + 2.0, 200)
    c.put(*P(hx_ + 0.0, hy_ + 3.0), 'k'); c.put(*P(hx_ + 2.0, hy_ + 3.0), 'k')    # tusks
    # big curling horns
    # big bull horns sweeping out and up, the tips curling in
    for (x0, d, k) in ((-1.6, -1, 0), (1.6, 1, 1)):
        hp = [(hx_ + x0, hy_ - 2.0), (hx_ + x0 + d * 3.2, hy_ - 3.6), (hx_ + x0 + d * 4.6, hy_ - 6.6), (hx_ + x0 + d * 3.6, hy_ - 9.2)]
        tube(c, hp, [1.5, 1.2, 0.85, 0.45], "ijk" if k else "hij", bias=0.25)
    c.put(*P(hx_ + 0.6, hy_ - 0.6), EYE_MARK + (255,))
    # near arm, a heavy fist
    sh_f = _T(p, 6.0, -15.0); fist_f = _T(p, 8.5, -7.0 - f)
    tube(c, [sh_f, ((sh_f[0] + fist_f[0]) / 2 + 1.0, (sh_f[1] + fist_f[1]) / 2), fist_f], [2.1, 1.8, 1.7], "hijk", bias=0.05)
    ell(c, fist_f[0], fist_f[1] + 0.5, 2.0, 1.8, "hijk", bias=0.2)
    tip = P(*_T(p, -10.2 * p.tail, -4.0 + sw * 1.2))
    c.put(tip[0], tip[1], TAIL_MARK + (255,))


def shape_skull(c, p, mouth="hum"):
    """A skull-headed wisp: a big bone skull wreathed in ghost-flame, no body but a flickering flame tail."""
    sw = p.sway
    hx_, hy_ = _T(p, 2.0, -17.0)
    # flame tail and tongues rising behind the skull
    pts = [(hx_ - 1.0, hy_ + 2.0), _T(p, -2.0, -11.0), _T(p, -5.5 * p.tail, -7.0 + sw), _T(p, -9.0 * p.tail, -6.5 + sw * 1.6),
           _T(p, -12.0 * p.tail, -8.0 + sw * 1.8)]
    tube(c, pts, [4.2, 3.4, 2.4, 1.2, 0.5], "abcd", bias=0.1)
    ph = int(round(p.hair * 2 + sw * 3))
    for k, (dx, h) in enumerate(((-3.5, 6), (-1.0, 8), (1.5, 6), (-5.5, 4))):
        x = hx_ + dx; w = [0, 1, 0, -1][(ph + k) % 4]
        tube(c, [(x, hy_ - 2.0), (x - 0.5 + w * 0.5, hy_ - 2.0 - h * 0.5), (x - 1.0 + w, hy_ - 2.0 - h)], [1.6, 1.0, 0.4], "bcd", bias=0.2)
    # the skull (bone = the skin keys)
    ell(c, hx_, hy_, 4.4, 4.0, "hijk", bias=0.2)
    ell(c, hx_ + 1.6, hy_ + 3.4, 2.6, 1.6, "hij", bias=0.05)     # jaw
    for (dx, dy) in ((-1, 0), (0, 0), (-1, 1), (0, 1), (2, 0), (3, 0), (2, 1), (3, 1)):
        dark(c, hx_ + dx, hy_ + dy, 240)                           # sockets
    dark(c, hx_ + 1.5, hy_ + 2.0, 220)                             # nose
    for k in range(4):
        c.put(*P(hx_ + k, hy_ + 3.6), 'k' if k % 2 else 'h')      # teeth
    if mouth == "wail": dark(c, hx_ + 1.5, hy_ + 4.5, 220); dark(c, hx_ + 2.5, hy_ + 4.5, 220)
    c.put(*P(hx_ - 2.4, hy_ - 2.0), 'k')                           # crown highlight
    c.put(*P(hx_ + 0.5, hy_ + 0.0), EYE_MARK + (255,))
    tip = P(*_T(p, -12.6 * p.tail, -8.6 + sw * 1.8))
    c.put(tip[0], tip[1], TAIL_MARK + (255,))


def shape_serpent(c, p, mouth="hum"):
    """A long-tailed serpent spirit: a snake's head with a spined frill, a long body coiling back in an S and tapering
    to a whip tail that sways with the drift."""
    sw = p.sway
    ph = p.hair * 0.5 + sw
    pts = []
    for k in range(9):
        t = k / 8.0
        x = 4.0 - 26.0 * t * p.tail
        y = -18.0 + 14.0 * t - 3.2 * math.sin(t * 2 * math.pi * 1.2 + ph) * t
        pts.append(_T(p, x, y))
    rad = [3.2, 3.4, 3.0, 2.6, 2.2, 1.8, 1.3, 0.8, 0.45]
    tube(c, pts, rad, "abcd", bias=0.05)
    # belly scales: a lighter stripe under the body
    for k in range(1, 7):
        x, y = pts[k]
        c.put(*P(x, y + rad[k] * 0.6), 'd')
    # a spined frill behind the head
    hx_, hy_ = _T(p, 6.5, -20.0)
    for k, a in enumerate((-150, -120, -95)):
        ex, ey = hx_ - 1.0 + 5.0 * math.cos(math.radians(a)), hy_ + 5.0 * math.sin(math.radians(a))
        tube(c, [(hx_ - 1.5, hy_), (ex, ey)], [1.0, 0.4], "bc", bias=0.2)
    # the head: long, pointed, slightly raised
    ell(c, hx_, hy_, 4.2, 2.6, "hijk", ang=-10, bias=0.15)
    ell(c, hx_ + 3.2, hy_ + 0.6, 2.0, 1.4, "hij", ang=-10, bias=0.1)
    line(c, hx_ + 1.0, hy_ + 1.6, hx_ + 5.0, hy_ + 1.2, 'h')       # jaw line
    if mouth == "wail":
        dark(c, hx_ + 3.0, hy_ + 1.6); dark(c, hx_ + 4.0, hy_ + 1.6)
        c.put(*P(hx_ + 5.6, hy_ + 2.2), 'k')                        # forked tongue
    c.put(*P(hx_ - 0.2, hy_ - 0.8), EYE_MARK + (255,))
    tx, ty = pts[-1]
    c.put(*P(tx - 1, ty), TAIL_MARK + (255,))


SHAPE_FN = {"Hag": shape_hag, "Hood": shape_hood, "Sheet": shape_sheet, "Horned": shape_horned, "Skull": shape_skull,
            "Serpent": shape_serpent}


def pose_idle(i):
    return Pose(bob=[0, -1, -1, 0, 1, 1][i], sway=[0, 0.6, 1, 0.6, 0, -0.6][i], hair=[0, 1, 1, 0, -1, -1][i],
                back=(8.5 + [0, 1, 2, 1, 0, -1][i] * 0.3, -21.0 + [0, 1, 2, 1, 0, -1][i] * 0.4),
                front=(10.0, -18.0 + [0, -1, -1, 0, 1, 1][i] * 0.5), claw=(True, True), lean=0.5)


def pose_run(i):
    return Pose(bob=[0, -1, -2, -1, 0, 1][i] - 1, lean=2.6, sway=[1.0, 1.4, 1.6, 1.4, 1.0, 0.8][i], tail=1.15, hair=1.6,
                back=(12.0, -17.0), front=(13.0, -15.0 + (i % 2)), claw=(True, True))


def body_frames(shape):
    fn = SHAPE_FN[shape]
    spawn = []
    for i, (w, h, b) in enumerate(((7, 0.6, 0), (6, 1.6, 2), (5, 3.0, 3))):
        c = KC(); GF.spawn_pool(c, w, h, b); spawn.append(c.keyed())
    c = KC(); GF.spawn_pool(c, 4, 1.0); GF.column(c, -15.0, 3.0, lean=0.5); spawn.append(c.keyed())
    for (st, bob, tl, sq) in ((1.35, -1.0, 0.45, 0.85), (1.18, -4.0, 0.7, 0.92), (1.08, -6.0, 0.85, 0.97),
                              (1.0, -6.5, 0.95, 1.0), (0.97, -4.5, 1.0, 1.0), (1.0, -1.0, 1.0, 1.0)):
        p = pose_idle(0); p.stretch = st; p.bob = bob; p.tail = tl; p.squash = sq
        p.front = (5.0 + (st - 1) * 10, -26.0 + (1.35 - st) * 20); p.back = (0.0, -27.0 + (1.35 - st) * 20)
        c = KC()
        if st > 1.3: GF.spawn_pool(c, 3, 0.5)
        fn(c, p, mouth="wail" if st > 1.1 else "hum"); spawn.append(c.keyed())
    idle = []
    for i in range(6):
        c = KC(); fn(c, pose_idle(i)); idle.append(c.keyed())
    run = []
    for i in range(6):
        c = KC(); fn(c, pose_run(i)); run.append(c.keyed())
    return spawn, idle, run


# ================================================================== eyes (stamped on the eye anchor)
def eyes_frames(style):
    out = []
    for f in range(2):
        px = {}
        g = lambda k: GL[k] + (255,)
        if style == "Glow":
            for x in (-1, 2):
                px[(x, 0)] = g(2 if f else 1); px[(x, -1)] = g(0) if f else g(1)
        elif style == "Hollow":
            for x in (-1, 2):
                for (dx, dy) in ((0, 0), (1, 0), (0, -1), (1, -1)): px[(x + dx - (1 if x < 0 else 0), dy)] = DARK + (255,)
                px[(x - (0 if x < 0 else 0), 0)] = g(2) if f else g(1)
        elif style == "Slits":
            for x in (-2, -1, 2, 3):
                px[(x, 0)] = g(2) if x in (-1, 2) else g(1)
            px[(-2, -1)] = DARK + (255,); px[(3, -1)] = DARK + (255,)
        elif style == "Cyclops":
            for (dx, dy) in ((0, -1), (1, -1), (-1, 0), (0, 0), (1, 0), (2, 0), (0, 1), (1, 1)):
                px[(dx, dy)] = DARK + (255,)
            px[(0, 0)] = g(2); px[(1, 0)] = g(1); px[(0, -1)] = g(1) if f else DARK + (255,)
        elif style == "Stars":
            for x in (-1, 2):
                px[(x, 0)] = g(2)
                for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)) if f == 0 else ((1, 1), (-1, -1), (1, -1), (-1, 1)):
                    px[(x + dx, dy)] = g(1)
        out.append(px)
    return out


# ================================================================== trails (stamped behind the body on the tail tip)
def trail_frames(style):
    out = []
    for f in range(6):
        px = {}
        if style == "None":
            pass
        elif style == "Mist":
            for k in range(4):
                x = -2 - k * 3 - (f % 3); y = (k % 2) + math.sin(f + k) * 1.2
                for (dx, dy, kk, a) in ((0, 0, 2, 170), (1, 0, 1, 150), (0, 1, 0, 120), (-1, 0, 1, 110)):
                    px[P(x + dx, y + dy)] = SH[kk + 1 if kk < 3 else 3] + (a - k * 25,)
        elif style == "Embers":
            for k in range(5):
                u = ((f + k * 1.3) % 6) / 6.0
                x = -2 - k * 2.5 - u * 3; y = 2 - u * 9 + (k % 2)
                px[P(x, y)] = GL[2 if u < 0.4 else 1] + (255,)
                if u < 0.5: px[P(x, y + 1)] = GL[0] + (220,)
        elif style == "Motes":
            for k in range(3):
                a = (f / 6.0 + k / 3.0) * 2 * math.pi
                x, y = 6 + 9 * math.cos(a) - 6, -4 + 4 * math.sin(a)
                px[P(x, y)] = GL[2] + (255,); px[P(x - 1, y)] = GL[1] + (200,)
        elif style == "Chains":
            # a broken shackle chain hanging off the tail tip and swinging
            sw = [0, 1, 2, 1, 0, -1][f]
            for k in range(7):
                x = -1 - k * 0.6 + sw * k * 0.15; y = 1 + k * 1.3
                px[P(x, y)] = (110, 114, 124, 255) if k % 2 == 0 else (60, 62, 70, 255)
            px[P(-5 + sw, 10)] = (150, 154, 164, 255); px[P(-4 + sw, 11)] = (90, 92, 100, 255)
        out.append(px)
    return out


# ================================================================== compositor (mirrors GhostCustom.Compose in C#)
def find_mark(px, mark):
    for k, v in px.items():
        if v[:3] == mark: return k
    return None


def compose(body, f, eyes, trails, col):
    px = dict(body)
    em = find_mark(px, EYE_MARK); tm = find_mark(px, TAIL_MARK)
    for m in (em, tm):
        if m is not None:
            left = px.get((m[0] - 1, m[1]))
            if left is not None and left[:3] not in (EYE_MARK, TAIL_MARK): px[m] = left
            else: del px[m]
    out = {}
    if tm is not None:
        for (x, y), v in trails[f % len(trails)].items(): out[(tm[0] + x, tm[1] + y)] = v
    out.update(px)
    if em is not None:
        for (x, y), v in eyes[f % len(eyes)].items(): out[(em[0] + x, em[1] + y)] = v
    return {k: recolor(v, col) for k, v in out.items()}


def img_of(px, w=CELL[0], h=CELL[1], org=ORIGIN):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for (x, y), v in px.items():
        X, Y = org[0] + x, org[1] + y
        if 0 <= X < w and 0 <= Y < h: im.putpixel((X, Y), v)
    return im


class PX:
    """A pack()-able frame holding RGBA pixels."""

    def __init__(self, px): self.px = px

    def to_rgba(self): return dict(self.px)

    def bbox(self):
        xs = [k[0] for k in self.px] or [0]; ys = [k[1] for k in self.px] or [0]
        return min(xs), min(ys), max(xs), max(ys)


# ================================================================== portrait frames


def slot_bg(tier, i):
    """A 29 x 24 opaque portrait background: a dark vault with a metal frame (silver: a soft shimmer sweeping across;
    gold: a brighter frame, a glint running round it, little sparkles)."""
    im = Image.new("RGBA", (29, 24), (0, 0, 0, 255))
    met = [(70, 74, 86), (120, 126, 140), (176, 182, 196), (230, 234, 242)] if tier == "Silver" else \
          [c[:3] for c in KT_mute([(110, 74, 20), (168, 120, 24), (224, 176, 42), (255, 232, 120)])]   # old gold, as the secret's
    base = (26, 26, 34) if tier == "Silver" else (30, 24, 20)
    glow = (40, 42, 54) if tier == "Silver" else (52, 40, 26)
    for y in range(24):
        for x in range(29):
            d = math.hypot((x - 14) / 13.0, (y - 12) / 11.5)
            c = glow if d + (0.06 if (x + y) % 2 else -0.06) < 0.6 else base
            im.putpixel((x, y), c + (255,))
    # frame: 1 px outer dark, 1 px metal
    for x in range(29):
        for y in (0, 23):
            im.putpixel((x, y), met[0] + (255,))
        im.putpixel((x, 1), met[2] + (255,)); im.putpixel((x, 22), met[1] + (255,))
    for y in range(24):
        for x in (0, 28):
            im.putpixel((x, y), met[0] + (255,))
        im.putpixel((1, y), met[2] + (255,)); im.putpixel((27, y), met[1] + (255,))
    for (x, y) in ((1, 1), (27, 1), (1, 22), (27, 22)):
        im.putpixel((x, y), met[3] + (255,))
    # running light
    per = 2 * (27 + 22)
    for k in range(3 if tier == "Gold" else 2):
        s = (i * per // 4 + k * (per // (3 if tier == "Gold" else 2))) % per
        for t in range(4):
            u = (s + t) % per
            if u < 27: xy = (1 + u, 1)
            elif u < 49: xy = (27, 1 + u - 27)
            elif u < 76: xy = (27 - (u - 49), 22)
            else: xy = (1, 22 - (u - 76))
            im.putpixel(xy, (met[3] if t < 2 else met[2]) + (255,))
    if tier == "Gold":
        for k, (x, y) in enumerate(((5, 5), (23, 6), (6, 18), (22, 17))):
            if (i + k) % 2 == 0:
                for (dx, dy) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                    im.putpixel((x + dx, y + dy), (met[3] if (dx, dy) == (0, 0) else met[2]) + (255,))
    return im


def window(shape):
    """Per-shape portrait window (cell pixel of the portrait's top-left): head and shoulders always in, centred across."""
    sp, idle, run = BODY[shape]
    xs = [k[0] for f in idle for k in f]; ys = [k[1] for f in idle for k in f]
    x0, x1, y0 = min(xs), max(xs), min(ys)
    left = int(round((x0 + x1) / 2.0)) - 14
    if x1 - x0 + 1 > 25: left = x1 + 2 - 28            # too wide: keep the head end (it faces right)
    top = min(y0 - 2, -24)
    return ORIGIN[0] + left, ORIGIN[1] + top


def portrait_frames(tier, look):
    shape, col, ey, tr = look
    sp, idle, run = BODY[SHAPES[shape][0]]
    WIN = window(SHAPES[shape][0])
    eyes = eyes_frames(EYES[ey][0]); trails = trail_frames(TRAILS[tr][0])
    frames = []
    for i in range(4):
        bg = slot_bg(tier, i)
        body = img_of(compose(idle[(i * 3) // 2], (i * 3) // 2, eyes, trails, col)).crop((WIN[0], WIN[1], WIN[0] + 29, WIN[1] + 24))
        bg.alpha_composite(body)
        # repaint the frame over anything that crossed it
        frm = slot_bg(tier, i)
        for x in range(29):
            for y in range(24):
                if x < 2 or x > 26 or y < 2 or y > 21: bg.putpixel((x, y), frm.getpixel((x, y)))
        frames.append(bg)
    return frames


def img_frame(im):
    px = {}
    for y in range(im.height):
        for x in range(im.width):
            v = im.getpixel((x, y))
            if v[3]: px[(x - 14, y - 23)] = v
    return PX(px)


# ================================================================== build
BODY = {}


def build():
    out = OUT[0]
    for s, _ in SHAPES:
        BODY[s] = body_frames(s)
    anims = []
    for s, _ in SHAPES:
        sp, idle, run = BODY[s]
        anims += [(s + "Spawn", [PX(x) for x in sp], GF.SPAWN_DURS), (s + "Idle", [PX(x) for x in idle], GF.IDLE_DURS),
                  (s + "Run", [PX(x) for x in run], GF.RUN_DURS)]
    img, man = pack("CustomGhostBody", anims, CELL[0], CELL[1], ORIGIN, out, cols=8)
    print("built CustomGhostBody", img.size, sum(len(a[1]) for a in anims), "frames")
    eanims = [(e, [PX(x) for x in eyes_frames(e)], [0.4, 0.4]) for e, _ in EYES]
    pack("CustomGhostEyes", eanims, 11, 7, (5, 3), out, cols=8)
    tanims = [(t, [PX(x) for x in trail_frames(t)] if t != "None" else [PX({}) for _ in range(6)], [0.1] * 6) for t, _ in TRAILS]
    pack("CustomGhostTrails", tanims, 30, 28, (18, 12), out, cols=8)
    # previews of the raw parts recoloured with the default silver look
    for name in ("CustomGhostBody",):
        prev = Image.open(os.path.join(out, name + ".png")).convert("RGBA")
        pp = prev.load()
        for y in range(prev.height):
            for x in range(prev.width):
                if pp[x, y][3]: pp[x, y] = recolor(pp[x, y], 7)
        preview(prev, man, os.path.join(out, name + "_preview.png"), scale=4)
    for name in ("CustomGhostEyes", "CustomGhostTrails"):
        im = Image.open(os.path.join(out, name + ".png")).convert("RGBA"); pp = im.load()
        for y in range(im.height):
            for x in range(im.width):
                if pp[x, y][3]: pp[x, y] = recolor(pp[x, y], 7)
        m = json.load(open(os.path.join(out, name + ".json")))
        preview(im, m, os.path.join(out, name + "_preview.png"), scale=8)
    # slot portrait frames + the default-look portraits
    fr = [("Silver", [img_frame(slot_bg("Silver", i)) for i in range(4)], [0.15] * 4),
          ("Gold", [img_frame(slot_bg("Gold", i)) for i in range(4)], [0.12] * 4)]
    img, man = pack("CustomGhostFrames", fr, 29, 24, (14, 23), out)
    preview(img, man, os.path.join(out, "CustomGhostFrames_preview.png"), scale=10)
    for tier in ("Silver", "Gold"):
        frames = [img_frame(f) for f in portrait_frames(tier, DEFAULT[tier])]
        img, man = pack("Ghost" + tier, [("Idle", frames, [0.25, 0.2, 0.25, 0.2])], 29, 24, (14, 23), out)
        preview(img, man, os.path.join(out, "Ghost" + tier + "_preview.png"), scale=10)
        crop = img.crop((0, 0, 29 * 4, 24)).load()
        assert all(crop[x, y][3] == 255 for x in range(29 * 4) for y in range(24)), tier + " portrait must be opaque"
    write_cs()


def write_cs():
    L = ["// GENERATED by tools/sprites/ghost_custom.py: do not edit by hand (run the script).",
         "namespace CrawlFurther.Content.Ghosts", "{", "    public static partial class GhostCustom", "    {"]
    L.append("        /// <summary>Body shapes: (anim prefix in CustomGhostBody, editor name).</summary>")
    L.append("        public static readonly string[,] ShapeTable = { " + ", ".join('{ "%s", "%s" }' % s for s in SHAPES) + " };")
    L.append("        public static readonly string[,] EyesTable = { " + ", ".join('{ "%s", "%s" }' % s for s in EYES) + " };")
    L.append("        public static readonly string[,] TrailTable = { " + ", ".join('{ "%s", "%s" }' % s for s in TRAILS) + " };")
    L.append("        public static readonly string[,] ColourNames = { " + ", ".join('{ "%s", "%s" }' % (c[0], c[1]) for c in COLOURS) + " };")
    L.append("        /// <summary>Per colour: 4 shroud, 4 skin, 3 glow, as 0xRRGGBB (dark to light in each group).</summary>")
    L.append("        public static readonly int[,] ColourTable =")
    L.append("        {")
    for c in COLOURS:
        L.append("            { " + ", ".join("0x" + h for h in c[2] + c[3] + c[4]) + " },   // " + c[0])
    L.append("        };")
    for t, d in DEFAULT.items():
        L.append("        public static readonly int[] Default%s = { %s };   // shape, colour, eyes, trail" % (t, ", ".join(str(v) for v in d)))
    wins = [window(sh) for sh, _ in SHAPES]
    L.append("        /// <summary>Per shape: the portrait window's top-left in the body cell (29 x 24).</summary>")
    L.append("        public static readonly int[] WinX = { %s };" % ", ".join(str(w[0]) for w in wins))
    L.append("        public static readonly int[] WinY = { %s };" % ", ".join(str(w[1]) for w in wins))
    L += ["    }", "}", ""]
    open(CS_OUT, "w").write("\n".join(L))
    print("wrote", CS_OUT)


def board(path):
    """Every option on one board: each shape x each colour (idle 0), then eyes and trails on the default look."""
    rows = []
    for si, (s, _) in enumerate(SHAPES):
        sp, idle, run = BODY[s]
        rows.append([img_of(compose(idle[0], 0, eyes_frames("Glow"), trail_frames("Mist"), ci)) for ci in range(len(COLOURS))])
    rows.append([img_of(compose(BODY["Hag"][1][1], 1, eyes_frames(e), trail_frames("None"), 0)) for e, _ in EYES])
    rows.append([img_of(compose(BODY[s][2][1], 1, eyes_frames("Stars"), trail_frames("Embers"), 4)) for s, _ in SHAPES])
    rows.append([img_of(compose(BODY[s][1][3], 3, eyes_frames("Cyclops"), trail_frames("Chains"), 0)) for s, _ in SHAPES])
    rows.append([img_of(compose(BODY[s][0][7], 7, eyes_frames("Slits"), trail_frames("Motes"), 6)) for s, _ in SHAPES])
    rows.append([img_of(compose(BODY["Hag"][2][i], i, eyes_frames("Glow"), trail_frames(t), 2)) for i, (t, _) in enumerate(TRAILS)])
    rows.append([img_of(compose(BODY["Hood"][2][i], i, eyes_frames("Stars"), trail_frames("Embers"), 4)) for i in range(6)])
    rows.append([img_of(compose(BODY["Sheet"][0][i], i, eyes_frames("Cyclops"), trail_frames("Chains"), 1)) for i in range(10)])
    sc = 4
    W = max(len(r) for r in rows) * (CELL[0] * sc + 4); H = len(rows) * (CELL[1] * sc + 4)
    bg = Image.new("RGB", (W, H), (58, 52, 50))
    for j, r in enumerate(rows):
        for i, im in enumerate(r):
            tile = Image.new("RGBA", im.size, (58, 52, 50, 255)); tile.alpha_composite(im)
            bg.paste(tile.resize((CELL[0] * sc, CELL[1] * sc), Image.NEAREST), (i * (CELL[0] * sc + 4), j * (CELL[1] * sc + 4)))
    bg.save(path)
    print(path, bg.size)


def main():
    args = sys.argv[1:]
    if "--out" in args:
        i = args.index("--out"); OUT[0] = args[i + 1]; del args[i:i + 2]; os.makedirs(OUT[0], exist_ok=True)
    build()
    os.makedirs(KT.BOARDS, exist_ok=True)
    board(os.path.join(KT.BOARDS, "ghost_custom_board.png"))


if __name__ == "__main__":
    main()
