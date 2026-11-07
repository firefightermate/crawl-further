"""Crawl: Further branding art -> art/out_branding/

  BrandFurther     the "Further" wordmark that sits at the bottom right of the CRAWL logo (title screen, credits).
                   Hand-lettered bold italic in ember gold with a maroon bevel and outline (CRAWL's own colours), tilted
                   up to the right like a splash note. Anims: Idle (glint sweep + ember flicker), Glitch (torn slices,
                   played on the CRAWL logo's glitch frames), In (burns in left to right), Out.
  BrandSpark       tiny ember that drifts up off the wordmark now and then (Rise).
  BrandMote        title backdrop dust/ember motes that drift slowly (Drift, 3 sizes).
  BrandPip         the main-menu highlight: a small flame pip shown either side of the selected item (Burn).
  VaultStampFurther  the vault's FURTHER category stamp (same 59x48 size and ink as the vanilla category stamps).
  VaultStampSecrets  the vault's SECRETS category stamp (same size and ink).

python3 tools/sprites/branding.py   (writes the sheets and art/out_branding/*_preview.png)
"""
import json, math, os, random
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "art", "out_branding")

def hx(s, a=255):
    s = s.lstrip("#"); return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)

# CRAWL's own logo colours (sampled from title_CRAWL_high_idle_01) for the outline/bevel, ember golds for the fill
OUTLINE = hx("1d0710")
BEVEL = hx("7a0f2c")      # the logo's deep crimson underside
SHADOW = hx("3b0a1c")
GOLD = [hx("fff2b8"), hx("ffd970"), hx("fbb03b"), hx("f07f1f"), hx("d4511a")]   # top -> bottom
GLINT = hx("ffffff")
HOT = hx("fffbe6")

# ------------------------------------------------------------------------------------------------- the lettering
# bold, angular, hand-cut letters ('#' ink). Cap height 11, x-height 7, baseline at row 10. Corners are clipped
# on the diagonal like the CRAWL letters.
G = {
 "F": [
  "..#######",
  ".########",
  "###......",
  "##.......",
  "##.......",
  "######...",
  "#####....",
  "##.......",
  "##.......",
  "##.......",
  "##.......",
  "#........",
 ],
 "u": [
  "", "", "", "",
  "##...##",
  "##...##",
  "##...##",
  "##...##",
  "##...##",
  "##..###",
  "#######",
  ".###.##",
 ],
 "r": [
  "", "", "", "",
  "##.###",
  "######",
  "###...",
  "##....",
  "##....",
  "##....",
  "##....",
  "#.....",
 ],
 "t": [
  "",
  ".##...",
  ".##...",
  ".##...",
  "######",
  ".##...",
  ".##...",
  ".##...",
  ".##...",
  ".##...",
  ".####.",
  "..###.",
 ],
 "h": [
  "##.....",
  "##.....",
  "##.....",
  "##.....",
  "##.###.",
  "#######",
  "###..##",
  "##...##",
  "##...##",
  "##...##",
  "##...##",
  "#....##",
 ],
 "e": [
  "", "", "", "",
  ".#####.",
  "##...##",
  "##...##",
  "#######",
  "##.....",
  "##.....",
  "##...##",
  ".#####.",
 ],
}
WORD = "Further"
KERN = 2            # px between letters
SHEAR = 8           # columns per 1px rise (the tilt up to the right)


def word_mask():
    """2D list of ink (True) for the word, upright, rows 0..10."""
    cols = []
    for k, ch in enumerate(WORD):
        g = G[ch]
        w = max(len(r) for r in g if r)
        for x in range(w):
            col = [False] * 12
            for y in range(12):
                r = g[y] if y < len(g) else ""
                col[y] = x < len(r) and r[x] == "#"
            cols.append(col)
        if k < len(WORD) - 1:
            for _ in range(KERN): cols.append([False] * 12)
    return cols


def italic(cols):
    """Slant 1px right every 3 rows from the baseline up (letters lean forward)."""
    return cols   # upright: the whole word is tilted instead (tilt)


def render_word(glint=None, heat=0.0, reveal=None, slices=None):
    """Full styled word as an RGBA image (not yet tilted).
    glint: x of a diagonal glint band (or None); heat 0..1 brightens the fill (flicker);
    reveal: only columns < reveal are inked, with a hot edge; slices: list of (y0, y1, dx) torn rows."""
    ink = italic(word_mask())
    W, H = len(ink), 12
    PAD = 2
    img = Image.new("RGBA", (W + PAD * 2 + 1, H + PAD * 2 + 5), (0, 0, 0, 0))
    px = img.load()
    swoosh = set()
    for x in range(5, W):
        # a hand-drawn underline under "urther": starts thin under the F, dips, then flicks up at the end
        t = (x - 5) / max(1, W - 6)
        y = H + 1 - int(round(2.2 * math.sin(math.pi * min(1.0, t * 1.15)) * 0 + (2 if t > 0.86 else 0) + (1 if t > 0.94 else 0)))
        swoosh.add((x, y))
        if 0.15 < t < 0.8: swoosh.add((x, y + 1)) if t < 0.5 else None
    swoosh = {(x, y) for (x, y) in swoosh}

    def isink(x, y):
        if (x, y) in swoosh: return reveal is None or x < reveal
        return 0 <= x < W and 0 <= y < H and ink[x][y] and (reveal is None or x < reveal)
    # bevel (2px straight down, deep crimson) then the dark outline around ink + bevel
    solid = set()
    for x in range(W):
        for y in range(H + 3):
            if isink(x, y):
                solid.add((x, y)); solid.add((x, y + 1))
    for (x, y) in solid:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                p = (x + dx, y + dy)
                if p not in solid:
                    xx, yy = p[0] + PAD, p[1] + PAD
                    if 0 <= xx < img.width and 0 <= yy < img.height: px[xx, yy] = OUTLINE
    for (x, y) in solid:
        if not isink(x, y): px[x + PAD, y + PAD] = BEVEL
    # fill: vertical gold gradient, lit top edges, darker right edges
    for x in range(W):
        for y in range(H + 3):
            if not isink(x, y): continue
            t = min(1.0, y / (H - 1))
            i = min(len(GOLD) - 1, int(t * (len(GOLD) - 0.01)))
            c = GOLD[i]
            if not isink(x, y - 1): c = GOLD[0] if i > 0 else HOT
            elif not isink(x + 1, y) and i < len(GOLD) - 1: c = GOLD[i + 1]
            if heat:
                c = tuple(min(255, int(v + (255 - v) * heat * 0.5)) for v in c[:3]) + (255,)
            if glint is not None:
                d = (x + (H - y) * 0.6) - glint
                if -1.0 <= d < 1.0: c = GLINT
                elif -2.2 <= d < 2.2: c = HOT
            if reveal is not None and reveal - 2 <= x < reveal: c = HOT
            px[x + PAD, y + PAD] = c
    if slices:
        src = img.copy()
        for (y0, y1, dx) in slices:
            band = src.crop((0, y0, src.width, y1))
            img.paste((0, 0, 0, 0), (0, y0, img.width, y1))
            img.alpha_composite(band, (max(0, dx), y0)) if dx >= 0 else img.alpha_composite(band.crop((-dx, 0, band.width, band.height)), (0, y0))
    return img


def tilt(img, shear=SHEAR):
    """Rise to the right: column x moves up by x // shear (pixel-clean vertical shear)."""
    rise = img.width // shear + 1
    out = Image.new("RGBA", (img.width, img.height + rise), (0, 0, 0, 0))
    for x in range(img.width):
        col = img.crop((x, 0, x + 1, img.height))
        out.alpha_composite(col, (x, rise - x // shear))
    return out


CW, CH = 76, 28   # wordmark cell


def cellify(img):
    c = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    c.alpha_composite(img, ((CW - img.width) // 2, (CH - img.height) // 2))
    return c


def wordmark_frames():
    frames, anims = [], []
    def add(im): frames.append(cellify(tilt(im))); return len(frames) - 1
    base = add(render_word())
    W = render_word().width
    # Idle: rest, then a glint sweeps across, then a soft ember flicker
    idle, dur = [], []
    idle.append(base); dur.append(2.4)
    for g in range(-4, W + 6, 4):
        idle.append(add(render_word(glint=g))); dur.append(0.05)
    idle.append(base); dur.append(1.6)
    for h in (0.35, 0.15, 0.45, 0.0):
        idle.append(add(render_word(heat=h)) if h else base); dur.append(0.08)
    idle.append(base); dur.append(1.2)
    anims.append({"name": "Idle", "frames": idle, "durations": dur})
    # Glitch: torn horizontal slices (played while the CRAWL logo glitches)
    rnd = random.Random(7)
    gl = []
    for k in range(4):
        sl = []
        y = 0
        while y < 16:
            h = rnd.randint(2, 4)
            sl.append((y, min(17, y + h), rnd.choice([-3, -2, 2, 3, 4]) if rnd.random() < 0.6 else 0))
            y += h
        gl.append(add(render_word(slices=sl, heat=0.3 if k % 2 else 0.0)))
    anims.append({"name": "Glitch", "frames": gl, "durations": [0.05] * len(gl)})
    # In: burns in left to right with a hot edge
    ins = [add(render_word(reveal=r)) for r in range(2, W + 3, 5)] + [base]
    anims.append({"name": "In", "frames": ins, "durations": [0.04] * (len(ins) - 1) + [0.1]})
    # Out: torn away quickly
    outs = gl[:2] + [add(render_word(reveal=r)) for r in range(W, 0, -10)]
    anims.append({"name": "Out", "frames": outs, "durations": [0.04] * len(outs)})
    return frames, anims


# ------------------------------------------------------------------------------------------------- small pieces
def spark_frames():
    S = 5
    fr = []
    for k, (core, glow) in enumerate([(HOT, GOLD[1]), (GOLD[1], GOLD[2]), (GOLD[2], GOLD[3]), (GOLD[3], BEVEL), (GOLD[4], None)]):
        im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); p = im.load()
        if glow:
            for (x, y) in ((1, 2), (3, 2), (2, 1), (2, 3)): p[x, y] = glow
        p[2, 2] = core
        fr.append(im)
    return fr, [{"name": "Rise", "frames": list(range(len(fr))), "durations": [0.25, 0.25, 0.3, 0.3, 0.3]}]


def mote_frames():
    """Backdrop motes: dust (grey-violet) and embers (gold), 3 sizes, each with a 2-frame twinkle."""
    S = 5
    fr, anims = [], []
    pal = {"dust": [hx("8e7f9a", 200), hx("5d5068", 160)], "ember": [hx("ffd970", 230), hx("d4511a", 190)]}
    for kind in ("dust", "ember"):
        for size in (1, 2, 3):
            ids = []
            for tw in (0, 1):
                im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); p = im.load()
                a, b = pal[kind]
                c = a if tw == 0 else b
                if size == 1: p[2, 2] = c
                elif size == 2:
                    p[2, 2] = c; p[3, 2] = b; p[2, 3] = b
                else:
                    for (x, y) in ((2, 1), (1, 2), (2, 2), (3, 2), (2, 3)): p[x, y] = b
                    p[2, 2] = c
                fr.append(im); ids.append(len(fr) - 1)
            anims.append({"name": "%s%d" % (kind.capitalize(), size), "frames": ids, "durations": [0.6, 0.4]})
    return fr, anims


def pip_frames():
    """Main-menu highlight pip: a little flame lozenge, 7x9, 4-frame burn loop."""
    W, H = 7, 9
    shapes = [
        ["...#...", "...#...", "..###..", "..#o#..", ".##o##.", ".#ooo#.", ".#ooo#.", "..###..", "...#..."],
        ["...#...", "..##...", "..###..", "..#o#..", ".##o##.", ".#ooo#.", ".#ooo#.", "..###..", "...#..."],
        ["....#..", "...#...", "..###..", "..#o#..", ".##o##.", ".#ooo#.", ".#ooo#.", "..###..", "...#..."],
        ["...#...", "...##..", "..###..", "..#o#..", ".#ooo#.", ".#ooo#.", ".#ooo#.", "..###..", "...#..."],
    ]
    fr = []
    for s in shapes:
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); p = im.load()
        for y, row in enumerate(s):
            for x, ch in enumerate(row):
                if ch == "#": p[x, y] = GOLD[3] if y > 3 else GOLD[2]
                elif ch == "o": p[x, y] = GOLD[0] if y in (3, 4) else GOLD[1]
        # outline
        q = im.copy().load()
        for y in range(H):
            for x in range(W):
                if q[x, y][3] == 0 and any(0 <= x + dx < W and 0 <= y + dy < H and q[x + dx, y + dy][3] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    p[x, y] = OUTLINE
        fr.append(im)
    return fr, [{"name": "Burn", "frames": [0, 1, 2, 3], "durations": [0.12, 0.12, 0.12, 0.12]}]


def stamp_frames():
    """FURTHER vault stamp, 59x48 like the vanilla category stamps, inked in the vanilla stamps' own colour
    (0.255, 0.247, 0.22 at 75% alpha; the vanilla stamps are white art tinted by the sprite, ours is drawn on its own sprite):
    a broken double ring like the others, around an arched crypt door with steps going down into it."""
    W, H = 59, 48
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); p = im.load()
    INK = (65, 63, 56, 191)
    cx, cy = 29.5, 24.0
    rnd = random.Random(11)
    def put(x, y):
        if 0 <= x < W and 0 <= y < H: p[int(x), int(y)] = INK
    # outer ring: 2px, broken in a few places
    gaps = [(35, 47), (150, 158), (262, 280)]
    for y in range(H):
        for x in range(W):
            d = math.hypot(x + 0.5 - cx, (y + 0.5 - cy) * 1.06)
            ang = (math.degrees(math.atan2(y - cy, x - cx)) + 360) % 360
            if 21.2 <= d <= 23.2 and not any(g0 <= ang <= g1 for g0, g1 in gaps): put(x, y)
            # inner chain of short runes
            if 17.6 <= d <= 18.8 and int(ang / 9) % 2 == 0 and rnd.random() < 0.85: put(x, y)
    # the door: an arch 15 wide, 22 tall, outlined 2px, dark inside
    dx0, dx1, top, bot = 22, 37, 13, 36
    for y in range(top, bot + 1):
        for x in range(dx0, dx1 + 1):
            ax = (dx0 + dx1) / 2.0
            r = (dx1 - dx0) / 2.0
            if y < top + r:      # round top
                d = math.hypot(x - ax, (y - (top + r)))
                if r - 2 <= d <= r: put(x, y)
            elif x - dx0 < 2 or dx1 - x < 2: put(x, y)
    # steps going down into the dark, narrowing (perspective)
    for k, (y, half) in enumerate(((34, 6), (31, 5), (28, 4), (25, 3), (22, 2))):
        for x in range(int(29.5 - half), int(29.5 + half) + 1): put(x, y)
    # a threshold slab and a little star above the door
    for x in range(18, 42): put(x, 37); put(x, 38) if 19 < x < 40 else None
    for (x, y) in ((29, 6), (29, 7), (29, 8), (28, 7), (30, 7), (29, 9)): put(x, y)
    # rough the ink like a rubber stamp
    for y in range(H):
        for x in range(W):
            if p[x, y][3] and rnd.random() < 0.08: p[x, y] = (0, 0, 0, 0)
    return [im], [{"name": "Stamp", "frames": [0], "durations": [1.0]}]


def stamp_secrets_frames():
    """SECRETS vault stamp (59x48, the vanilla stamps' ink): the same broken double ring around a keyhole, with three
    small stars, as if the page were sealed."""
    W, H = 59, 48
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); p = im.load()
    INK = (65, 63, 56, 191)
    cx, cy = 29.5, 24.0
    rnd = random.Random(23)
    def put(x, y):
        if 0 <= x < W and 0 <= y < H: p[int(x), int(y)] = INK
    gaps = [(60, 74), (192, 200), (300, 316)]
    for y in range(H):
        for x in range(W):
            d = math.hypot(x + 0.5 - cx, (y + 0.5 - cy) * 1.06)
            ang = (math.degrees(math.atan2(y - cy, x - cx)) + 360) % 360
            if 21.2 <= d <= 23.2 and not any(g0 <= ang <= g1 for g0, g1 in gaps): put(x, y)
            if 17.6 <= d <= 18.8 and int(ang / 9) % 2 == 1 and rnd.random() < 0.85: put(x, y)
    # keyhole: a round head and a flared slot, outlined 2 px, the inside left clear
    hx, hy, hr = 29.5, 19.0, 6.0
    for y in range(H):
        for x in range(W):
            dx, dy = x + 0.5 - hx, y + 0.5 - hy
            d = math.hypot(dx, dy)
            in_head = d <= hr
            # slot from the head down to y 34, widening from 4 to 8 px
            t = (y + 0.5 - 22) / 12.0
            half = 2.0 + 2.0 * max(0.0, min(1.0, t))
            in_slot = 22 <= y <= 34 and abs(dx) <= half
            inside = in_head or in_slot
            if not inside: continue
            # outline: inside pixels with an outside neighbour within 2 px
            edge = False
            for ox, oy in ((2, 0), (-2, 0), (0, 2), (0, -2), (1, 1), (-1, 1), (1, -1), (-1, -1), (1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + ox, y + oy
                ddx, ddy = xx + 0.5 - hx, yy + 0.5 - hy
                tt = (yy + 0.5 - 22) / 12.0
                hh = 2.0 + 2.0 * max(0.0, min(1.0, tt))
                if not (math.hypot(ddx, ddy) <= hr or (22 <= yy <= 34 and abs(ddx) <= hh)): edge = True; break
            if edge: put(x, y)
    for (sx, sy) in ((16, 12), (43, 13), (41, 35)):
        for (ox, oy) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)): put(sx + ox, sy + oy)
    for y in range(H):
        for x in range(W):
            if p[x, y][3] and rnd.random() < 0.08: p[x, y] = (0, 0, 0, 0)
    return [im], [{"name": "Stamp", "frames": [0], "durations": [1.0]}]


# ------------------------------------------------------------------------------------------------- output
def save(name, frames, anims, cols=None):
    w, h = frames[0].size
    cols = cols or min(len(frames), 8)
    rows = (len(frames) + cols - 1) // cols
    img = Image.new("RGBA", (w * cols, h * rows), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        img.alpha_composite(f, ((i % cols) * w, (i // cols) * h))
    img.save(os.path.join(OUT, name + ".png"))
    json.dump({"cellW": w, "cellH": h, "cols": cols, "anims": anims}, open(os.path.join(OUT, name + ".json"), "w"), indent=1)
    # preview: every frame at 6x on the title's dark backdrop
    k = 6
    pv = Image.new("RGBA", (img.width * k, img.height * k), (36, 22, 34, 255))
    pv.alpha_composite(img.resize((img.width * k, img.height * k), Image.NEAREST))
    pv.save(os.path.join(OUT, name + "_preview.png"))
    print(name, len(frames), "frames", w, "x", h)


def build():
    os.makedirs(OUT, exist_ok=True)
    save("BrandFurther", *wordmark_frames())
    save("BrandSpark", *spark_frames())
    save("BrandMote", *mote_frames())
    save("BrandPip", *pip_frames())
    save("VaultStampFurther", *stamp_frames())
    save("VaultStampSecrets", *stamp_secrets_frames())


if __name__ == "__main__":
    build()
