"""Floating roll numbers: the digit sheet FloatNumber.cs (src/Core) builds its pop-up readouts from.

    python3 float_digits.py [outdir]          (default art/out_common)

Sheet FxCommonDigits, cell 9 x 13, one single-frame anim per glyph and tone: "<Tone><Glyph>", e.g. Normal6, Max6, Min1,
Flash3, MaxD. Glyphs 0-9 and the letters D O G E (for DODGE).
The letters are redrawn so they never read as each other or as digits: D has a straight left side (square corners) and a
chamfered right side, O is rounded on all four corners (the slashed 0 stays the font's), G has a full top bar running to
the right edge and an open notch before its inner bar (the 6 has a short top and a closed loop). Tones:
  Normal  cream white                   any roll between the extremes
  Max     gold, warm brown outline      the highest face (a 6 on a d6)
  Min     grey-red, dull                a 1
  Flash   white-hot                     the first 0.08 s of every pop, whatever the tone

The glyph shapes follow Crawl's bitmap font style (chunky strokes, chamfered top-left / bottom-right corners) at the size
of the game's in-world text: 5 x 7 bodies, 2 px strokes (v0.10 sweep; the first set was the 8 x 10 menu font and read far
too big over monsters). Each glyph gets a 1 px dark outline and a 1 px drop shadow under it (the bottom edge is 2 px dark,
which keeps it legible on light floors), and is shaded top-lit: the top row is the highlight, the bottom row the shade.

Layout inside a cell: body rows 2-8, outline rows 1-9, shadow row 10; body columns start at x 2. The C# side measures
each glyph's opaque width from the texture and overlaps neighbouring glyphs by 1 px, so their outlines merge into a
single dark pixel between letters.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from anim import Spr, pack, preview  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else \
    os.path.join(os.path.dirname(os.path.dirname(HERE)), "art", "core")

CELL_W, CELL_H = 9, 13
BODY_X, BODY_Y = 2, 2

# v0.10 sweep: redrawn at in-world text size. The first set copied CrawlBitmapLarge, the MENU font (8 x 10 glyphs, 13 px
# with outline and shadow), so a roll stood as tall as a goblin and DODGE ran 55 px wide; Crawl's own in-world text (the
# shop price, 04B_03 at 0.6) is about 6 px tall. Now 5 x 7 bodies with 2 px strokes in the same chunky style (chamfered
# top-left / bottom-right corners like the font), 10 px with outline and shadow. D, O and G stay distinct from 0 and 6.
GLYPHS = {
    "0": [".####", "##.##", "##.##", "##.##", "##.##", "##.##", "####."],
    "1": [".##", "###", ".##", ".##", ".##", ".##", ".##"],
    "2": [".####", "...##", "...##", ".###.", "##...", "##...", "#####"],
    "3": [".####", "...##", "...##", "..###", "...##", "...##", "####."],
    "4": ["##.##", "##.##", "##.##", "#####", "...##", "...##", "...##"],
    "5": ["#####", "##...", "##...", "####.", "...##", "...##", "####."],
    "6": [".###.", "##...", "####.", "##.##", "##.##", "##.##", ".###."],
    "7": ["#####", "...##", "...##", "..##.", "..##.", ".##..", ".##.."],
    "8": [".###.", "##.##", "##.##", ".###.", "##.##", "##.##", ".###."],
    "9": [".###.", "##.##", "##.##", "##.##", ".####", "...##", ".###."],
    "D": ["####.", "##.##", "##.##", "##.##", "##.##", "##.##", "####."],
    "O": [".###.", "##.##", "##.##", "##.##", "##.##", "##.##", ".###."],
    "G": [".####", "##...", "##...", "##.##", "##.##", "##.##", ".####"],
    "E": ["#####", "##...", "##...", "####.", "##...", "##...", "#####"],
}
ORDER = "0123456789DOGE"


def hx(s):
    s = s.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


# hi (top 2 rows), mid, lo (bottom 2 rows), rim (top-left edge light on the middle rows), outline, shadow
TONES = {
    "Normal": dict(hi="ffffff", mid="f4eac6", lo="c4b48c", rim="fffaea", out="1e1a1c", sh="1e1a1c"),
    "Max":    dict(hi="fff6c4", mid="ffd23c", lo="e8781c", rim="ffe88a", out="3a1c0c", sh="1e1a1c"),
    "Min":    dict(hi="d8b0a8", mid="a86e68", lo="70444a", rim="c4928a", out="1e1a1c", sh="1e1a1c"),
    "Flash":  dict(hi="ffffff", mid="ffffff", lo="fff3b8", rim="ffffff", out="2a2024", sh="1e1a1c"),
}
TONE_ORDER = ["Normal", "Max", "Min", "Flash"]


class SprA(Spr):
    def to_rgba(self):
        return {k: (c if len(c) == 4 else c + (255,)) for k, c in self.px.items()}


def glyph(ch, tone):
    rows = GLYPHS[ch]
    T = {k: hx(v) for k, v in TONES[tone].items()}
    body = {(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c == "#"}
    px = {}
    for (x, y) in body:
        if y <= 0:
            col = T["hi"]
        elif y >= 6:
            col = T["lo"]
        elif (x - 1, y) not in body or (x, y - 1) not in body:
            col = T["rim"]          # light catching the top-left edges of the strokes
        else:
            col = T["mid"]
        px[(x + BODY_X, y + BODY_Y)] = col
    ring = set()
    for (x, y) in body:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (x + dx, y + dy)
                if q not in body:
                    ring.add(q)
    for (x, y) in ring:
        px[(x + BODY_X, y + BODY_Y)] = T["out"]
    # drop shadow: the whole outlined shape one row lower, only where nothing is drawn yet
    for (x, y) in list(px.keys()):
        q = (x, y + 1)
        if q not in px:
            px[q] = T["sh"]
    return SprA(px)


def build(out):
    anims = []
    for tone in TONE_ORDER:
        for ch in ORDER:
            anims.append((tone + ch, [glyph(ch, tone)], [0.1]))
    img, man = pack("FxCommonDigits", anims, CELL_W, CELL_H, (0, 0), out, cols=len(ORDER))
    # preview: one row per tone (the default preview would put every single-frame anim on its own row)
    from PIL import Image
    S = 6
    pv = Image.new("RGBA", (len(ORDER) * (CELL_W + 1) * S, len(TONE_ORDER) * (CELL_H + 1) * S), (28, 26, 32, 255))
    for r, tone in enumerate(TONE_ORDER):
        for j, ch in enumerate(ORDER):
            fi = r * len(ORDER) + j
            x0, y0 = (fi % man["cols"]) * CELL_W, (fi // man["cols"]) * CELL_H
            c = img.crop((x0, y0, x0 + CELL_W, y0 + CELL_H)).resize((CELL_W * S, CELL_H * S), Image.NEAREST)
            pv.alpha_composite(c, (j * (CELL_W + 1) * S, r * (CELL_H + 1) * S))
    pv.convert("RGB").save(os.path.join(out, "FxCommonDigits_preview.png"))
    print("built FxCommonDigits: %d glyphs x %d tones, cell %dx%d, sheet %dx%d" % (len(ORDER), len(TONE_ORDER), CELL_W, CELL_H, img.width, img.height))
    return img, man


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    build(OUT)
