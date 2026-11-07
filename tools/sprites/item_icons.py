"""Shop bubbles (34x41, like vanilla) and HUD icons (11x7) for the god items and the v2 items.

    python3 tools/sprites/item_icons.py [outdir]      -> art/out_items/Icon*Bubble|Hud.png|json (+ board.png)

Spells are laid on a blank parchment card taken from the Wickwalk card (art/out_heroes), so every spell matches
vanilla's scroll look. Artifacts stand in the lower middle of the bubble, redrawn there at BUBBLE_SCALE by
items_v2_icons.py / god_item_icons.py (22 px, so the shop and the vault show them bigger than the 16 px icon). The HUD icons are drawn by hand at 11x7: a shrunk icon turns to mush at that size.
"""
import json, os, sys
from collections import Counter
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import items_v2_icons as V2  # noqa: E402
import god_item_icons as GI  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
ART = os.path.join(ROOT, "art")
DEFAULT_OUT = os.path.join(ART, "out_items")

ITEMS = {  # icon sheet -> (folder, kind)
    "IconGraveCall": ("out_ossivar", "spell"),
    "IconMarrowFlask": ("out_ossivar", "artifact"),
    "IconThornwall": ("out_sylvene", "spell"),
    "IconRottingApple": ("out_sylvene", "artifact"),
    "IconMirrorStep": ("out_umbrael", "spell"),
    "IconHollowCrown": ("out_umbrael", "artifact"),
}
for _sheet, _nice, _fn, _kind in V2.ICONS:
    ITEMS[_sheet] = ("out_icons_v2", _kind)

# ------------------------------------------------------------------ hand-drawn HUD icons ('.' = clear)
HUD = {
    "IconEmberHeart": ([".cCc...cCc.",
                        "cCCCc.cCCCc",
                        "cCCoCcCoCCc",
                        ".cCoyYyoCc.",
                        "..cCoyoCc..",
                        "...cCoCc...",
                        "....ccc...."], {"c": "40221c", "C": "6a3426", "o": "e8501a", "y": "ffa040", "Y": "fff0a0"}),
    "IconVenomGland": (["..pPPPp....",
                        ".pPPggPp...",
                        "pPPgGGgPpp.",
                        "pPgGWGgPpPp",
                        ".pPgggPp..G",
                        "..pPPPp....",
                        "....G......"], {"p": "6c283e", "P": "a24a5e", "g": "3e8a1e", "G": "7ccc2e", "W": "c4f552"}),
    "IconRimeRing": (["....bib....",
                      "....bBb....",
                      "..sSSsSSs..",
                      ".sS.....Ss.",
                      ".sd.....ds.",
                      "..sdddddd..",
                      "..........."], {"s": "9aa0ae", "S": "d4d8e0", "d": "3e4250", "b": "4a80b2", "B": "8cc0e8",
                                       "i": "e4f8ff"}),
    "IconLeechSeed": (["......gG...",
                       ".....rg....",
                       "...rRWrr...",
                       "...rRRrr...",
                       "...drrrd...",
                       "..w.ddw.w..",
                       ".w..w...w.."], {"r": "981c22", "R": "d03a30", "W": "f8806a", "d": "5c1018", "g": "325e28",
                                        "G": "52903c", "w": "553a26"}),
    "IconThornMail": (["...sSkSs...",
                       ".sSsSsSsSs.",
                       "sSsgSsSgsSs",
                       "s.sSgggSs.s",
                       "..sSsSsSs..",
                       "..gsSsSsg..",
                       "..ssssss..."], {"s": "686e7e", "S": "9aa0ae", "k": "1a1a24", "g": "52903c"}),
    "IconSaintsWick": (["...g.Y.g...",
                        "..g.oYo.g..",
                        "...g.o.g...",
                        "....wWw....",
                        "....wWd....",
                        "....wwd....",
                        "...bbbbb..."], {"g": "dcb04a", "Y": "fff0b0", "o": "f07a24", "w": "d4c098", "W": "f0e6c8",
                                         "d": "8c7458", "b": "9a6220"}),
    "IconLuckyDie": (["...IIIIIII.",
                      "..wWWWWWWd.",
                      "..wGwwwGwd.",
                      "..wGwwwGwd.",
                      "..wGwwwGwd.",
                      "..wwwwwwwd.",
                      "...ddddddd."], {"I": "e6dab8", "W": "fbf4dc", "w": "c4b294", "d": "8a7468", "G": "245a42"}),
    "IconAshHourglass": (["..WWWWWWW..",
                          "...gaaag...",
                          "....gag....",
                          ".....a.....",
                          "....g.g....",
                          "...gaeag...",
                          "..WWWWWWW.."], {"W": "96643c", "g": "6a94a4", "a": "868080", "e": "e8501a"}),
    "IconGlassMask": (["...iIIIi...",
                       "..iIIIIIi..",
                       "..IkkIkkb..",
                       "..iIIIIIb..",
                       "...iIkIb...",
                       "....ibb....",
                       "..........."], {"i": "8cc0e8", "I": "e4f8ff", "k": "1e1630", "b": "4a80b2"}),
    "IconBarnacleShell": (["...sSSSs...",
                           "..sSwSSSs..",
                           ".sSwkSsSSs.",
                           ".sSSsSsSss.",
                           "..ssSsSss.g",
                           "....sss...g",
                           "..........."], {"s": "766452", "S": "a48e72", "w": "e6dab8", "k": "1e1630", "g": "2e8a5a"}),
    "IconTidecaller": ([".......cCc.",
                        ".....cCCc..",
                        "...cCCCCc..",
                        "..pPCCCc...",
                        ".pPpcCc....",
                        ".tppc......",
                        "ttt........"], {"c": "b47e6c", "C": "f8e2c6", "p": "86205a", "P": "e884b6", "t": "2e9696"}),
    "IconBrineFlask": ([".....k.....",
                        ".....g.....",
                        "....gBg....",
                        "...gbBBg...",
                        "...bBbbb...",
                        "...gbbbg...",
                        "....ggg...."], {"k": "6e5034", "g": "6a94a4", "b": "2e8a5a", "B": "5cc27e"}),
    "IconJestersBell": (["......rr...",
                         ".....rk....",
                         "...yYYy....",
                         "..yYWYYy...",
                         "..yykkyy...",
                         "...yyyy....",
                         "..........."], {"r": "c4423a", "k": "3a3046", "y": "a8782a", "Y": "dcb04a", "W": "fbe796"}),
    "IconJokersWild": (["...rrwwww..",
                        "..rrwwwwwr.",
                        "..rrwwRwwr.",
                        ".rrwwRRRwr.",
                        ".rrwwwRwww.",
                        ".rrwwwwww..",
                        "..rwwwww..."], {"r": "962230", "w": "efeadc", "R": "c4423a"}),
    "IconMarionetteCross": (["W.........W",
                             ".W.......W.",
                             "..W.....W..",
                             "...WWgWW...",
                             "..W.l.l.W..",
                             ".W..l.l..W.",
                             "W...l.l...W"], {"W": "96643c", "g": "dcb04a", "l": "a476d8"}),
    "IconMarrowFlask": ([".....w.....",
                         ".....g.....",
                         "....gRg....",
                         "...gRRRg...",
                         "...rRWRr...",
                         "...rRRRr...",
                         "....rrr...."], {"w": "e6dab8", "g": "a8ccd4", "r": "962230", "R": "c4423a", "W": "ff8a7a"}),
    "IconRottingApple": (["......l....",
                          "....rlr....",
                          "...rRRrr...",
                          "...RWRbb...",
                          "...rRRrw...",
                          "....rrr....",
                          "..........."], {"l": "52903c", "r": "962230", "R": "c4423a", "W": "f8806a", "b": "1a120e",
                                           "w": "e6dab8"}),
    "IconHollowCrown": ([".v...v...v.",
                         ".k...k...k.",
                         ".kk.kkk.kk.",
                         ".kKkkKkkKk.",
                         ".kvkkvkkvk.",
                         ".kkkkkkkkk.",
                         "..........."], {"v": "b46ae0", "k": "3a3046", "K": "564a62"}),
}


def hx(s):
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def hud_img(name):
    grid, pal = HUD[name]
    im = Image.new("RGBA", (11, 7), (0, 0, 0, 0))
    p = im.load()
    assert len(grid) == 7, name
    for y, row in enumerate(grid):
        assert len(row) == 11, (name, row)
        for x, ch in enumerate(row):
            if ch != ".": p[x, y] = hx(pal[ch]) + (255,)
    return V2.crawl_image(im)


def cell(folder, name, anim, i=0):
    m = json.load(open(os.path.join(ART, folder, name + ".json")))
    im = Image.open(os.path.join(ART, folder, name + ".png")).convert("RGBA")
    a = [x for x in m["anims"] if x["name"] == anim][0]
    f = a["frames"][i]
    x, y = (f % m["cols"]) * m["cellW"], (f // m["cols"]) * m["cellH"]
    return im.crop((x, y, x + m["cellW"], y + m["cellH"])), len(a["frames"])


def blank_card():
    card, _ = cell("out_heroes", "IconWickwalk", "Bubble")
    px = card.load()
    W, H = card.size
    cols = Counter(px[x, y][:3] for x in range(W) for y in range(H) if px[x, y][3] > 0)
    base = cols.most_common(1)[0][0]
    for x in range(W):
        for y in range(H):
            r, g, b, a = px[x, y]
            if a and (r > 170 and b < 110 and r - g > 40):      # flame glyph pixels
                px[x, y] = base + (255,)
    return card


def save(outdir, name, frames, w, h, anim, durs):
    img = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        img.alpha_composite(f, (i * w, 0))
    img.save(os.path.join(outdir, name + ".png"))
    json.dump({"cellW": w, "cellH": h, "cols": len(frames),
               "anims": [{"name": anim, "frames": list(range(len(frames))), "durations": durs}]},
              open(os.path.join(outdir, name + ".json"), "w"))


def bubble_frames(name, folder, kind, card):
    """The Bubble anim's frames: the spell glyph on the card, or the artifact standing in the bubble."""
    out = []
    draw = V2.DRAW.get(name) or GI.DRAW.get(name)
    if kind == "artifact" and draw:
        for ph in (0, 1):
            pic, _ = V2.render(draw, ph, S=V2.BUBBLE_SCALE)
            b = Image.new("RGBA", (34, 41), (0, 0, 0, 0))
            b.alpha_composite(pic, ((34 - pic.width) // 2, 41 - pic.height - 6))
            out.append(b)
        return out
    _, n = cell(folder, name, "Idle")
    for i in range(n):
        ic, _ = cell(folder, name, "Idle", i)
        if kind == "spell":
            b = card.copy()
            bb = card.getbbox()
            b.alpha_composite(ic, ((bb[0] + bb[2]) // 2 - 8, (bb[1] + bb[3]) // 2 - 8))
        else:
            b = Image.new("RGBA", (34, 41), (0, 0, 0, 0))
            b.alpha_composite(ic, (9, 41 - 16 - 6))
        out.append(b)
    return out


def build(outdir=DEFAULT_OUT):
    os.makedirs(outdir, exist_ok=True)
    card = blank_card()
    for name, (folder, kind) in ITEMS.items():
        bubbles = bubble_frames(name, folder, kind, card)
        durs = [0.9, 0.25] if len(bubbles) == 2 else [0.5] * len(bubbles)
        save(outdir, name + "Bubble", bubbles, 34, 41, "Bubble", durs)
        if kind == "artifact":
            save(outdir, name + "Hud", [hud_img(name)], 11, 7, "Hud", [0.5])
        print("built", name)
    board(outdir)


def board(outdir):
    names = list(ITEMS)
    cols = 12
    rows = (len(names) + cols - 1) // cols
    board = Image.new("RGBA", (cols * 46 + 4, rows * 62), (28, 26, 32, 255))
    for i, name in enumerate(names):
        x, y = (i % cols) * 46 + 4, (i // cols) * 62 + 2
        b = Image.open(os.path.join(outdir, name + "Bubble.png")).crop((0, 0, 34, 41))
        board.alpha_composite(b, (x, y))
        hp = os.path.join(outdir, name + "Hud.png")
        if os.path.exists(hp):
            board.alpha_composite(Image.open(hp), (x + 11, y + 46))
    board.resize((board.width * 5, board.height * 5), Image.NEAREST).save(os.path.join(outdir, "board.png"))


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT)
