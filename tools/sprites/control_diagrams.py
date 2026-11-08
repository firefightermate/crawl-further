"""The join screen's controls pictures, redrawn with the ghost button.

The game's pictures (AtlasMenuConnect, controller_diagrams_01 to _09) name A (attack) and B (special) with a coloured
button on the device, a line and a row. This adds the ghost button the same way: the device's ghost control picked
out in blue (the pad's X, the keyboard's C, the mouse's middle button; a pink square on the PlayStation picture), a
line, and a fourth row "X' Ghost" under Special.

The game's art is never copied into the mod. This script writes a list of paint steps (art/core/ControlDiagrams.json)
that ControlDiagrams.cs runs at run time on the game's own pictures: copy a block of the picture with a palette swap
(red to blue), recolour pixels, draw lines and letters. Letters and lines are ours.

    python3 tools/sprites/control_diagrams.py            # writes the JSON and, with the dump, a preview board
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT_JSON = os.path.join(ROOT, "art", "core", "ControlDiagrams.json")
DUMP = os.environ.get("CRAWL_DUMP", os.path.join(ROOT, "build", "dump"))

# ---- colours (RGB) ----
PLATE = (108, 91, 77)
TEXT = (170, 152, 131)
RED = [(242, 57, 64), (241, 58, 64)]
RED_DARK = (180, 36, 41)
RED_LIGHT = (255, 188, 171)
RED_HI = (255, 227, 220)
BLUE = (86, 138, 204)
BLUE_DARK = (46, 82, 138)
BLUE_LIGHT = (176, 210, 240)
BLUE_HI = (228, 242, 255)
PS_RED = (236, 83, 67)
PS_ICON = (64, 64, 64)
PINK = (214, 122, 180)
PINK_LIGHT = (240, 190, 222)
KEY_DARK = (66, 53, 42)

RED2BLUE = [[list(c), list(BLUE)] for c in RED] + [[list(RED_DARK), list(BLUE_DARK)], [list(RED_LIGHT), list(BLUE_LIGHT)],
                                                    [list(RED_HI), list(BLUE_HI)]]
PS2PINK = [[list(PS_RED), list(PINK)]] + [[list(c), list(PINK)] for c in RED]

# ---- our letters: 1 = ink ----
FONT = {
    "G": ["011", "100", "101", "101", "011"],
    "h": ["100", "100", "111", "101", "101"],
    "o": ["000", "111", "101", "101", "111"],
    "s": ["000", "011", "100", "001", "110"],
    "t": ["10", "11", "10", "10", "01"],
}
ICON_X = ["1001", "1001", "0110", "1001", "1001"]
KEY_C = ["111", "100", "100", "100", "111"]
PS_SQUARE = ["1111", "1001", "1001", "1111"]


def text_steps(word, x, y, color):
    steps = []
    for ch in word:
        g = FONT[ch]
        pts = [[x + i, y + j] for j, row in enumerate(g) for i, c in enumerate(row) if c == "1"]
        steps.append({"op": "pixels", "color": list(color), "pts": pts})
        x += len(g[0]) + 1
    return steps


def bitmap(rows, x, y, color):
    return {"op": "pixels", "color": list(color), "pts": [[x + i, y + j] for j, r in enumerate(rows) for i, c in enumerate(r) if c == "1"]}


def line(path, color=BLUE):
    """Straight and 45-degree segments through the points, one pixel wide."""
    pts = []
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        dx = (x1 > x0) - (x1 < x0)
        dy = (y1 > y0) - (y1 < y0)
        x, y = x0, y0
        while True:
            if [x, y] not in pts: pts.append([x, y])
            if (x, y) == (x1, y1): break
            if x != x1: x += dx
            if y != y1: y += dy
    return {"op": "pixels", "color": list(color), "pts": pts}


def ghost_row(b, ps=False, dx=0):
    """A fourth row 18 below the B row (top b): the B row copied with red made blue (or the PlayStation circle made
    pink), its plate and right edge moved 4 out, its words cleared, and X' / Ghost written in. dx: where this picture's
    button icon sits against the pad pictures' (the keyboard's is 2 further left)."""
    ny = b + 18
    steps = [
        {"op": "copy", "src": [0, b, 42, 10], "dst": [0, ny], "map": PS2PINK if ps else RED2BLUE},
        {"op": "recolor", "rect": [12, ny, 30, 10], "map": [[list(TEXT), list(PLATE)]]},
        {"op": "copy", "src": [37, ny, 5, 10], "dst": [41, ny]},
    ]
    for x in range(37, 41):
        steps.append({"op": "copy", "src": [36, ny, 1, 10], "dst": [x, ny]})
    if ps:
        # the circle symbol becomes a square
        steps.append({"op": "recolor", "rect": [3, ny, 10, 10], "map": [[list(PINK), list(PS_ICON)]]})
        steps.append(bitmap(PS_SQUARE, 6, ny + 3, PINK))
    else:
        steps.append({"op": "recolor", "rect": [5 + dx, ny + 1, 5, 7], "map": [[list(BLUE_LIGHT), list(BLUE)]]})
        steps.append(bitmap(ICON_X, 6 + dx, ny + 2, BLUE_LIGHT))
    steps += text_steps("Ghost", 15 + dx, ny + 2, TEXT)
    return steps, ny


def pad_steps(button, top_y, ny, color=BLUE, light=BLUE_LIGHT, from_col=(99, 84, 67)):
    """The pad's ghost button picked out (its pixels recoloured, a light corner) and a line from its top up over the
    pad, right, and down the outside to the new row."""
    x0, y0, x1, y1 = button
    steps = [{"op": "recolor", "rect": [x0, y0, x1 - x0 + 1, y1 - y0 + 1], "map": [[list(from_col), list(color)]]},
             {"op": "pixels", "color": list(light), "pts": [[x0 + 1, y0]] if x1 - x0 >= 2 else [[x0, y0]]}]
    cx = x0 + (x1 - x0) // 2
    steps.append(line([(cx, y0 - 1), (cx, top_y), (43, top_y), (45, top_y + 2), (45, ny - 1)], color))
    return steps


KEY_EDGE = (79, 66, 51)
KEY_RIGHT = (158, 137, 118)
GREEN = (134, 152, 54)
GLYPH_Z = ["111", "001", "010", "100", "111"]
GLYPH_X = ["101", "101", "010", "101", "101"]
GLYPH_C = ["111", "100", "100", "100", "111"]


def key(x, face, glyph, top=29):
    """A key 7 wide and 9 tall in the picture's own style: face colour on top, edges left and right, a dark base two
    rows deep, and the letter in the middle of the face."""
    face_pts = [[x + i, top + j] for j in range(7) for i in range(1, 6)]
    left = [[x, top + j] for j in range(2, 9)]
    right = [[x + 6, top + j] for j in range(2, 8)]
    base = [[x + i, top + j] for j in (7, 8) for i in range(1, 6)] + [[x + 6, top + 8]]
    return [{"op": "pixels", "color": list(face), "pts": face_pts},
            {"op": "pixels", "color": list(KEY_EDGE), "pts": left + base},
            {"op": "pixels", "color": list(KEY_RIGHT), "pts": right},
            bitmap(glyph, x + 2, top + 1, KEY_DARK)]


ARROWS = [(97, 84, 71), (59, 49, 37), (49, 40, 31), (117, 101, 88)]


def keyboard_steps(ny):
    """The keyboard picture (Esc over Z and X, the arrows to the right) with C added beside X. Its 9-wide keys leave
    no room for a third, so the arrows move 4 right and Z, X and C are drawn 7 wide in the same style (red Z, green X,
    blue C) with Z's and X's lines as before. C's line goes up past Esc, along the top, and down the right side to the
    new row, clear of the other two."""
    keys = [list(c) for c in (KEY_EDGE, GREEN, KEY_DARK, KEY_RIGHT, RED[0], RED[1])]
    return [{"op": "copy", "src": [24, 24, 19, 13], "dst": [28, 24], "move": True},
            {"op": "clear", "rect": [4, 29, 24, 16], "colors": keys}] + \
        key(4, RED[0], GLYPH_Z) + key(12, GREEN, GLYPH_X) + key(20, BLUE, GLYPH_C) + [
        {"op": "pixels", "color": list(BLUE_LIGHT), "pts": [[21, 29], [21, 30]]},
        {"op": "pixels", "color": list(RED[0]), "pts": [[4, 33]]},
        line([(16, 36), (24, 44), (26, 44)], GREEN),
        line([(23, 28), (23, 19), (45, 19), (47, 21), (47, ny - 3), (45, ny - 1)]),
    ]


def mouse_steps(ny, wheel_rect, top_y):
    """The middle button (the wheel) picked out in blue and a line from it straight up over the mouse, right, and down
    the outside to the new row."""
    x, y, w, h = wheel_rect
    return [
        {"op": "recolor", "rect": [x, y, w, h], "map": [[[155, 135, 115], list(BLUE)], [[79, 66, 51], list(BLUE)]]},
        {"op": "pixels", "color": list(BLUE_LIGHT), "pts": [[x, y], [x, y + 1]]},
        line([(x + w - 1, y - 1), (x + w - 1, top_y), (43, top_y), (45, top_y + 2), (45, ny - 1)]),
    ]


def spec():
    """The pictures the join screen shows (clips InputDiagramController, Keyboard, Mouse, ControllerXbone and
    ControllerPS4 play elements 15, 16, 17, 19 and 20: _04, _05, _06, _08, _09). _01 to _03 (with a Menu row) are not
    used by any clip; _07 is the arcade cabinet's, which has no ghost button."""
    d = {}
    s, ny = ghost_row(63)
    d["controller_diagrams_04"] = s + pad_steps((26, 27, 29, 30), 19, ny)
    s, ny = ghost_row(63, dx=-2)
    d["controller_diagrams_05"] = s + keyboard_steps(ny)
    s, ny = ghost_row(62)
    d["controller_diagrams_06"] = s + mouse_steps(ny, (23, 23, 2, 6), 15)
    # Xbox: X is the left face button
    s, ny = ghost_row(63)
    d["controller_diagrams_08"] = s + pad_steps((28, 25, 29, 26), 16, ny)
    # PlayStation: the square, in pink
    s, ny = ghost_row(63, ps=True)
    d["controller_diagrams_09"] = s + pad_steps((29, 25, 30, 26), 18, ny, PINK, PINK_LIGHT)
    return d


# ---- reference runner (the same steps ControlDiagrams.cs runs), for previews ----
def run(img, steps, pad_left, pad_top, canvas_w, canvas_h):
    from PIL import Image
    cv = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    cv.paste(img, (pad_left, pad_top))
    px = cv.load()

    def at(x, y): return (x + pad_left, y + pad_top)

    def inside(x, y): return 0 <= x + pad_left < canvas_w and 0 <= y + pad_top < canvas_h
    for st in steps:
        op = st["op"]
        if op == "copy":
            sx, sy, w, h = st["src"]; dx, dy = st["dst"]
            m = {tuple(a): tuple(b) for a, b in st.get("map", [])}
            snap = {(i, j): px[at(sx + i, sy + j)] for j in range(h) for i in range(w) if inside(sx + i, sy + j)}
            if st.get("move"):
                for (i, j) in snap: px[at(sx + i, sy + j)] = (0, 0, 0, 0)
            for (i, j), p in snap.items():
                if p[3] == 0 or not inside(dx + i, dy + j): continue
                px[at(dx + i, dy + j)] = m.get(p[:3], p[:3]) + (255,)
        elif op == "recolor":
            x, y, w, h = st["rect"]; m = {tuple(a): tuple(b) for a, b in st["map"]}
            for j in range(h):
                for i in range(w):
                    if not inside(x + i, y + j): continue
                    p = px[at(x + i, y + j)]
                    if p[3] and p[:3] in m: px[at(x + i, y + j)] = m[p[:3]] + (255,)
        elif op == "clear":
            x, y, w, h = st["rect"]; only = {tuple(c) for c in st.get("colors", [])}
            for j in range(h):
                for i in range(w):
                    if not inside(x + i, y + j): continue
                    p = px[at(x + i, y + j)]
                    if p[3] and (not only or p[:3] in only): px[at(x + i, y + j)] = (0, 0, 0, 0)
        elif op == "pixels":
            c = tuple(st["color"]) + (255,)
            for x, y in st["pts"]:
                if inside(x, y): px[at(x, y)] = c
    return cv


def preview(d):
    from PIL import Image
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    atlas = None
    for l in open(os.path.join(DUMP, "all", "db", "sharedassets0__exAtlas.jsonl")):
        a = json.loads(l)
        if a.get("m_Name") == "AtlasMenuConnect": atlas = a; break
    tex = Image.open(os.path.join(DUMP, "tex", "AtlasMenuConnect_165.png")).convert("RGBA")
    W, H = tex.size
    els = {e["name"]: e for e in atlas["elements"]}
    cells = []
    for name in sorted(els):
        if not name.startswith("controller_diagrams"): continue
        e = els[name]; c = e["coords"]; t = e["trimRect"]
        x = int(round(c["x"] * W)); w = int(round(c["width"] * W)); h = int(round(c["height"] * H))
        y = int(round((1 - c["y"] - c["height"]) * H))
        img = tex.crop((x, y, x + w, y + h))
        cv = run(img, d.get(name, []), int(t["x"]), int(t["y"]), e["originalWidth"], e["originalHeight"])
        cells.append((name, img, cv, int(t["x"]), int(t["y"])))
    sc = 5
    cw, ch = 51 * sc, 141 * sc
    board = Image.new("RGBA", (len(cells) * (cw + 10), ch * 2 + 10), (42, 36, 30, 255))
    for i, (name, img, cv, tx, ty) in enumerate(cells):
        before = Image.new("RGBA", (51, 141), (0, 0, 0, 0)); before.paste(img, (tx, ty))
        board.alpha_composite(before.resize((cw, ch), Image.NEAREST), (i * (cw + 10), 0))
        board.alpha_composite(cv.resize((cw, ch), Image.NEAREST), (i * (cw + 10), ch + 10))
    return board


if __name__ == "__main__":
    d = spec()
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump({"atlas": "AtlasMenuConnect", "frames": d}, f, separators=(",", ":"))
    print("wrote", OUT_JSON, sum(len(v) for v in d.values()), "steps for", len(d), "pictures")
    if os.path.isdir(os.path.join(DUMP, "tex")):
        out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "build", "control_diagrams_preview.png")
        preview(d).save(out)
        print("preview", out)
