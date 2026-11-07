"""The char-grid bust parts the custom hero is built from (hero_custom.py), the Vhorrul item icons, and the build
entry point for art/out_heroes.

    python3 tools/sprites/hero_portraits.py

Writes the icons here, the origin portraits through origin_portraits.py, and art/out_heroes/board.png (6x).
The bust parts are hand placed: char grids stamped at explicit offsets, plus explicit per-row spans for the
shoulders. Light comes from the upper left. (0,0) is the top-left of the cell, so sheets are packed with feet=(0, 0).
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from anim import Spr, PALETTE, pack, preview
from PIL import Image

OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'art', 'out_heroes')
W, H = 29, 24

# ---------------------------------------------------------------- palette additions (runtime only)
PALETTE.update({
    # skin (tan, from the vanilla hero)
    'L': (0xda, 0xb2, 0x84), 'l': (0xc7, 0x9c, 0x6e), 'j': (0xa2, 0x72, 0x4c), 'J': (0x6a, 0x44, 0x30),
    'Q': (0xe6, 0xdc, 0xc8), 'f': (0x24, 0x18, 0x16), 'M': (0x9e, 0x56, 0x46), '*': (0xe2, 0xa8, 0x90),
    # hair
    'H': (0x8e, 0x6e, 0x3e), 'd': (0x73, 0x5b, 0x38), 'D': (0x48, 0x36, 0x24),
    # rust tunic
    'E': (0xd8, 0x62, 0x36), 'Z': (0xb4, 0x48, 0x2a), 'z': (0x85, 0x35, 0x25), 'x': (0x4f, 0x28, 0x2d),
    # steel
    '5': (0x3a, 0x3a, 0x44), '6': (0x66, 0x66, 0x72), '7': (0xa0, 0xa0, 0xaa), '8': (0xdc, 0xdc, 0xe4),
    # olive / green-brown cloth
    '#': (0x24, 0x2a, 0x1c), '+': (0x3a, 0x46, 0x2a), '=': (0x54, 0x5e, 0x38), '-': (0x70, 0x7a, 0x48),
    # violet cowl + runes
    'C': (0x24, 0x16, 0x30), 'n': (0x45, 0x26, 0x5c), 'N': (0x6c, 0x40, 0x8c), 'I': (0x8e, 0x5c, 0xae),
    '%': (0xb8, 0x7c, 0xff), '&': (0xf0, 0xdc, 0xff),
    # welts / blood
    '!': (0x96, 0x34, 0x30), 'r': (0xa8, 0x1e, 0x1a),
    # off-white tabard
    '^': (0xd6, 0xd0, 0xc0), '~': (0xa8, 0xa2, 0x92), '_': (0x74, 0x70, 0x66),
    # rope
    ':': (0xb8, 0x9e, 0x6a), ';': (0x86, 0x6e, 0x46),
    # parchment card (vanilla Spell8 colours)
    '1': (0x93, 0x7c, 0x49), '2': (0x86, 0x71, 0x43), '3': (0xaf, 0x95, 0x5c), '4': (0x6e, 0x5c, 0x36),
    # gold
    'Y': (0xff, 0xd8, 0x5e), 'y': (0xff, 0xf3, 0xb8),
})

# background vignette tones (frame, edge, mid, centre): the custom hero tints these to the player slot
BG = {
    'HeroWanderer':   [(0x12, 0x10, 0x14), (0x22, 0x1c, 0x21), (0x2d, 0x25, 0x2a), (0x3a, 0x30, 0x34)],
}
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


# ---------------------------------------------------------------- drawing helpers
class Canvas:
    def __init__(self, w=W, h=H):
        self.w, self.h, self.px = w, h, {}

    def put(self, x, y, c):
        if c not in '. ':
            self.px[(x, y)] = c

    def get(self, x, y):
        return self.px.get((x, y))

    def stamp(self, rows, ox, oy, dy=0, only=None):
        for y, r in enumerate(rows):
            for x, c in enumerate(r):
                if c not in '. ' and (only is None or c in only):
                    self.px[(ox + x, oy + y + dy)] = c

    def recolor(self, mapping, region=None):
        for k, c in list(self.px.items()):
            if (region is None or region(*k)) and c in mapping:
                self.px[k] = mapping[c]

    def spr(self):
        return Spr({k: v for k, v in self.px.items() if 0 <= k[0] < self.w and 0 <= k[1] < self.h})


def background(cv, cx=14.0, cy=9.0):
    """Radial vignette with ordered dithering between 3 tones, plus a 1px dark frame."""
    for y in range(H):
        for x in range(W):
            if x in (0, W - 1) or y in (0, H - 1):
                cv.put(x, y, '0'); continue
            d = (((x - cx) / 15.0) ** 2 + ((y - cy) / 13.0) ** 2) ** 0.5  # 0 centre .. ~1.2 corners
            t = d * 2.6 + BAYER[y % 4][x % 4] / 16.0 - 0.5
            cv.put(x, y, '$' if t < 0.55 else '@' if t < 1.55 else '9')


def outline(cv, char='K', skip=''):
    """1px outline around all non-background pixels (for transparent icons)."""
    add = {}
    for (x, y), c in cv.px.items():
        if c in skip: continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            k = (x + dx, y + dy)
            if k not in cv.px: add[k] = char
    for k, c in add.items():
        cv.px.setdefault(k, c)


# ---------------------------------------------------------------- the hero: shared face + body
# head-local grid, stamped at (8, 3): face cols 1..10, ears at 0 and 11. Rows 0..10 -> canvas rows 3..13.
# The same hand-placed face as the origin portraits (origin_portraits.FACE_M / FACE_F), in the skin chars the custom
# hero recolours: L light, l base, j shadow, J ink, Q eye white, f pupil, D brow, M lips. Rows -> canvas rows 3..13.
FACE_M = [
    ".jlLLLLlljJ.",
    ".lLLLLLLllj.",
    ".lLLLLLLllj.",
    ".lLLLLLLllj.",
    ".lLDDLLDDlj.",
    "jlLQfLLQfljJ",
    "jlLLLLLLlljJ",
    ".lLLLLljllj.",
    ".llLLJJJllj.",
    "..llLLLlljj.",
    "...jjlljj...",
]
FACE_F = [
    "..jlLLLllj..",
    ".lLLLLLLllj.",
    ".lLLLLLLllj.",
    ".lLLLLLLllj.",
    ".lDLLLDLllj.",
    "jlLQfLLQfljJ",
    ".lLLLLLLlljJ",
    ".lLLLLljllj.",
    "..lLLMMLllj.",
    "...lLLLlj...",
    "....jllj....",
]
FX, FY = 8, 3
EYES = [(11, 8), (12, 8), (15, 8), (16, 8)]


def face(cv, female=False, blink=False, dy=0):
    cv.stamp(FACE_F if female else FACE_M, FX, FY, dy)
    if blink:
        for (x, y) in EYES:
            cv.put(x, y + dy, 'J' if x in (12, 15) or not female else 'f')
        for (x, y) in EYES:
            cv.put(x, y - 1 + dy, 'j' if cv.get(x, y - 1 + dy) in ('D',) else cv.get(x, y - 1 + dy))


def neck(cv, female=False, dy=0):
    x0, x1 = (12, 15) if female else (11, 16)
    for y in range(13, 22):
        for x in range(x0, x1 + 1):
            c = 'J' if x in (x0, x1) else ('j' if y <= 14 or x == x1 - 1 else 'l')
            cv.put(x, y, c)


def spans(female=False):
    if female:
        s = {15: (8, 19), 16: (6, 21), 17: (4, 23), 18: (3, 24), 19: (2, 25)}
        for y in range(20, 27): s[y] = (1, 26)
    else:
        s = {15: (7, 20), 16: (4, 23), 17: (2, 25), 18: (1, 26), 19: (0, 27)}
        for y in range(20, 27): s[y] = (-1, 28)
    return s


def body(cv, pal, female=False, dy=0, collar=True, seams=True):
    """Shoulders as explicit per-row spans, lit like the origin portraits' torso: the top of a wide dome under a light
    from the upper left, three tones, the right and bottom edges in the dark tone. pal = (light, mid, shadow, dark)."""
    Lc, Mc, Sc, Dc = pal
    sp = spans(female)
    cx, cy, rx, ry = 13.5, 25.5, 14.5, 10.0
    lx, ly, lz = -0.55, -0.68, 0.48
    seamL, seamR = (7, 20) if female else (6, 21)
    for y, (x0, x1) in sp.items():
        for x in range(x0, x1 + 1):
            nx, ny = (x - cx) / rx, (y - cy) / ry
            nz = max(0.0, 1.0 - min(1.0, nx * nx + ny * ny)) ** 0.5
            l = nx * lx + ny * ly + nz * lz + 0.05
            c = Sc if l < 0.12 else Mc if l < 0.62 else Lc
            if x == x1 or (x == x1 - 1 and l < 0.12):
                c = Dc
            if seams and y >= 18 and x in (seamL, seamR):
                c = Sc if x == seamL else Dc
            cv.put(x, y + dy, c)
    if collar:
        # open neckline: skin V under the jaw, darker hem around it
        V = {15: (11, 16), 16: (12, 15), 17: (13, 14)} if not female else {15: (12, 15), 16: (13, 14)}
        for y, (a, b) in V.items():
            for x in range(a, b + 1):
                cv.put(x, y + dy, 'J' if x in (a, b) else 'j' if y == 15 else 'l')
            cv.put(a - 1, y + dy, Dc)
            cv.put(b + 1, y + dy, Dc)
        ylast = max(V) + 1
        a, b = V[max(V)]
        for x in range(a, b + 1):
            cv.put(x, ylast + dy, Dc)


# ---------------------------------------------------------------- Vhorrul icons
BW, BH = 34, 41


def icon_votive():
    cv = Canvas(BW, BH)
    # flame
    cv.stamp([
        "....o....",
        "....O....",
        "...oOo...",
        "...OYO...",
        "..oOYOo..",
        "..OYyYO..",
        "..oYyYo..",
        "...OYO...",
        "....k....",
    ], 12, 7)
    # wax body (squat), lit from the left, drips over the rim
    cv.stamp([
        "....XXWWWWWw....",
        "..XXWWWWWWWWww..",
        ".XWWXWWWWWWWwwk.",
        ".XWWWWWWWWWWwwk.",
        ".XWWWWWWWWWwwwk.",
        ".XWWWWWWWWWWwwk.",
    ], 9, 16)
    # cracked iron cup
    cv.stamp([
        "56777777766666655",
        "6XW77666666665X55",
        "5X6K666666655XW5K",
        "W6766666666655wK5",
        "X67666K666665555K",
        "w57666K6666655555",
        ".5766666K66665555",
        ".57666666K6655555",
        ".55666666K665555.",
        "..55666666555555.",
        "...5555555555555.",
        "....55555555555..",
    ], 8, 22)
    # drips running down the outside
    for (x, y, c) in [(9, 23, 'X'), (9, 24, 'W'), (9, 25, 'X'), (9, 26, 'W'),
                      (21, 23, 'X'), (22, 24, 'W'), (22, 25, 'w'), (13, 22, 'W'), (13, 23, 'w'), (13, 24, 'w')]:
        cv.put(x, y, c)
    # jagged crack down the cup, glowing with heat inside
    for (x, y, c) in [(17, 22, 'K'), (17, 23, 'K'), (16, 24, 'K'), (16, 25, 'o'), (17, 26, 'O'), (17, 27, 'o'),
                      (16, 28, 'K'), (16, 29, 'K'), (15, 30, 'K'), (18, 27, 'K'), (19, 28, 'K')]:
        cv.put(x, y, c)
    for (x, y) in [(14, 26), (14, 27), (9, 28), (16, 29 - 0)]:
        if cv.get(x, y) == 'K': cv.put(x, y, '6')
    cv.put(14, 26, '6'); cv.put(16, 29, 'K')
    # base ring + feet
    cv.stamp(["K5555555555555K", ".K5K.......K5K."], 9, 34)
    outline(cv, 'K', skip='oOYy')
    return cv.spr()


def icon_votive_hud():
    cv = Canvas(11, 7)
    cv.stamp([
        ".....O.....",
        "....oYo....",
        "....XWw....",
        "...6XWw6...",
        "...67665...",
        "....555....",
    ], 0, 0)
    outline(cv, 'K', skip='oOYy')
    # keep inside the 11x7 cell
    return cv.spr()


def icon_wickwalk():
    cv = Canvas(BW, BH)
    card = [
        "..11211111..........",
        ".2221111111111112...",
        ".22211111111111222..",
        ".2221111111111112223",
        ".1211111111111111222",
        ".1111111111111111122",
        ".1111111111111111112",
        ".1111111111111111111",
        ".2111111111111111111",
        ".2111111111111111111",
        ".2111111111111111113",
        ".2111111111111111113",
        ".1111111111111111111",
        ".1111111111111111111",
        ".1111111111111111111",
        ".1111111111111111111",
        ".1111111111111111111",
        ".1111111111111111111",
        ".1211111111111111111",
        ".1211111111111111111",
        ".1211111111111111111",
        "21111111111111111111",
        "22111111111111111111",
        "2222111111111111111.",
        "111111111111111111..",
        ".................1..",
    ]
    cv.stamp(card, 7, 8)
    for (x, y) in [(8, 9), (24, 33)]:
        cv.put(x, y, '3')
    # glyph: flame footprints walking up a burning wick
    print_l = [  # a left footprint whose toes are flame tongues
        "o.o...",
        "o.o.o.",
        "oooOo.",
        "oOOOoo",
        "oOOOo.",
        ".oOo..",
        ".ooo..",
        ".oOoo.",
        ".oooo.",
        "..oo..",
    ]
    print_r = [r[::-1] for r in print_l]
    cv.stamp(print_l, 9, 22)
    cv.stamp(print_r, 17, 15)
    cv.stamp(print_l, 10, 9)
    # embers trailing between the steps
    for (x, y, c) in [(15, 20, 'o'), (16, 25, 'o'), (17, 12, 'o'), (14, 31, 'o')]:
        cv.put(x, y, c)
    return cv.spr()


# ---------------------------------------------------------------- build
DURS = [0.2, 0.18, 0.2, 0.16]


def main():
    os.makedirs(OUT, exist_ok=True)
    icons = []
    for name, sprs, cw, ch, an in [('IconVotiveCandle', [icon_votive()], BW, BH, 'Bubble'),
                                   ('IconVotiveCandleHud', [icon_votive_hud()], 11, 7, 'Hud'),
                                   ('IconWickwalk', [icon_wickwalk()], BW, BH, 'Bubble')]:
        img, man = pack(name, [(an, sprs, [1.0])], cw, ch, (0, 0), OUT)
        preview(img, man, os.path.join(OUT, name + '_preview.png'))
        icons.append((name, img, man))
        print('built', name)
    import origin_portraits
    portraits = origin_portraits.build()
    board(portraits, icons)


def board(portraits, icons, scale=6):
    """art/out_heroes/board.png: every origin's Idle frames, then the item icons drawn here."""
    pad = 3
    bw = (4 * (W + pad) + pad) * scale
    bh = (len(portraits) * (H + pad) + pad + BH + pad) * scale
    bg = Image.new('RGBA', (bw, bh), (40, 38, 46, 255))
    y = pad
    for ims in portraits:
        for j, im in enumerate(ims):
            bg.alpha_composite(im.resize((W * scale, H * scale), Image.NEAREST), ((pad + j * (W + pad)) * scale, y * scale))
        y += H + pad
    x = pad
    for name, img, man in icons:
        cw, ch = man['cellW'], man['cellH']
        cell = img.crop((0, 0, cw, ch)).resize((cw * scale, ch * scale), Image.NEAREST)
        bg.alpha_composite(cell, (x * scale, y * scale))
        x += cw + pad
    bg.convert('RGB').save(os.path.join(OUT, 'board.png'))


if __name__ == '__main__':
    main()
