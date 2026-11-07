"""The gods' own spells and artifacts: their 16x16 icons, drawn with the same pen as items_v2_icons.py.

    python3 tools/sprites/god_item_icons.py [--out DIR]

Each icon stays in its god's art folder (the sheet ids and folders the code and the other rigs expect): Ossivar,
Sylvene and Umbrael's six get their bubbles and HUD icons from item_icons.py (art/out_items); Zhekra, Kaurn and
Ysveld's six get theirs here, next to the icon. --out writes everything into one folder instead (for boards).
Anim `Idle`, 2 frames, feet (8, 15), like every item icon.
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
from PIL import Image  # noqa: E402
from anim import pack, preview  # noqa: E402
import items_v2_icons as V2  # noqa: E402
import jinx_v2_rigs as J  # noqa: E402
from items_v2_icons import accent, ring_pts, rot_pts  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
ART = os.path.join(ROOT, "art")

for _k, _v in {
    "amber":  ["3a1a06", "7a3c0c", "b8661a", "e6a03a", "ffd884"],
    "copper": ["2a1208", "5e2c14", "94502a", "c47c46", "eeb27a"],
    "crown":  ["120e1a", "241c2e", "3a3046", "564a62", "7c708a"],
    "apple":  ["2a0810", "5c1018", "98202a", "cc3a36", "f07a62"],
    "rot":    ["1e140a", "3a2a12", "5a4420", "7a6030", "9a7c44"],
    "mirror": ["1a2a3a", "34546e", "5e86a6", "a2c6dc", "e8f6ff"],
    "lace":   ["2a3a54", "5a7298", "94aed0", "c8dcf0", "f2f8ff"],
    "acid":   ["16300c", "2e5e14", "5a9a22", "8ed23a", "d4f878"],
}.items():
    J.RAMPS[_k] = [J._h(c) for c in _v]
J.EMISSIVE |= {"bolt"}
J.RAMPS["bolt"] = [J._h(c) for c in ("2a4a8a", "4a7ad0", "8ab8ff", "d0e8ff", "ffffff")]
J.SHINY |= {"amber", "copper", "apple", "mirror"}


# ================================================================== spells (laid on the parchment card)
def grave_call(g, ph):
    # a skeletal hand claws up out of a grave mound, a bone spear rising past it
    g.ell(8, 13.8, 7.0, 1.8, "dirt", 0.5, bias=0.2)
    g.tube([(13.0, 14.0), (13.8, 1.6)], [0.8, 0.55], "ivory", 0.8, bias=0.2)
    g.poly([(12.8, 2.6), (15.0, 2.6), (13.9, -0.4)], "ivory", 0.82, flat=3)
    k = 0.6 if ph else 0.0
    g.tube([(7.0, 14.2), (7.0, 10.4)], [1.0, 0.9], "ivory", 1.0, bias=0.15)
    g.ell(7.0, 9.0, 3.6, 2.0, "ivory", 1.05, bias=0.25)
    for i, (x, top) in enumerate(((4.0, 3.6 + k), (6.0, 2.0), (8.0, 2.4 + k), (10.0, 4.0))):
        g.tube([(x, 7.6), (x, top)], [0.45, 0.4], "ivory", 1.1 + 0.01 * i, bias=0.3)
    g.tube([(3.6, 9.4), (2.0, 7.6), (1.8, 6.0)], [0.55, 0.5, 0.4], "ivory", 1.1, bias=0.3)
    g.line(4.4, 13.4, 9.0, 13.0, "dirt", 0.6, tone=0)
    for (x, y) in ((2.6, 12.8), (10.4, 12.8)):
        g.ell(x, y, 0.9, 0.7, "dirt", 0.7, bias=0.2)
    if ph:
        g.glint(13.8, 1.2)


@accent("pink")
def thornwall(g, ph):
    # a hedge of thorned stems pushing up from a furrow, one pink bloom
    g.ell(8, 14.2, 7.4, 1.4, "dirt", 0.4, bias=0.2)
    for i, (x0, top, bend, th) in enumerate(((2.2, 6.0, 0.8, 0.6), (5.0, 3.4, -0.6, 0.55), (8.2, 3.6, 0.6, 0.45),
                                              (11.2, 3.8, -0.8, 0.5), (13.8, 6.6, 0.4, 0.62))):
        g.tube([(x0, 14.4), (x0 + bend, (14.4 + top) / 2), (x0 - bend * 0.4, top)], [1.2, 1.0, 0.6], "leaf", 1.0 + 0.01 * i,
               bias=0.35)
        side = 1 if i % 2 else -1
        y = 14.4 + (top - 14.4) * th
        x = x0 + bend * 0.7
        g.line(x + 0.9 * side, y, x + 2.2 * side, y - 1.0, "ivory", 1.05 + 0.01 * i, tone=3)
    b = 0.4 if ph else 0.0
    g.ell(8.2, 2.6, 2.0 + b, 1.7 + b, "pink", 1.2, bias=0.2)
    g.dot(8.2, 2.6, "gold", 3, 1.25)


def mirror_step(g, ph):
    # an oval hand mirror on a little stand; a dashing silhouette in the glass, the glass cracking where it left
    g.tube([(8, 12.4), (8, 14.4)], [0.8], "steel", 0.8)
    g.ell(8, 14.6, 3.2, 0.9, "steel", 0.8, bias=0.1)
    g.ell(8, 7.0, 5.2, 6.2, "steel", 0.9, bias=0.2)
    g.ell(8, 7.0, 4.0, 5.0, "mirror", 1.0, flat=2)
    g.ell(7.0, 5.6, 2.0, 2.8, "mirror", 1.01, flat=3)
    # the silhouette mid-dash, with a smear behind it
    g.ell(8.6, 4.6, 1.1, 1.1, "shadow", 1.1, flat=1)
    g.poly([(7.6, 5.8), (9.8, 5.8), (10.4, 9.8), (7.0, 9.8)], "shadow", 1.1, flat=1)
    g.line(5.4, 7.0, 7.0, 7.0, "shadow", 1.1, tone=2)
    g.line(5.0, 8.6, 6.8, 8.6, "shadow", 1.1, tone=2)
    g.polyline([(4.6, 10.2), (6.0, 9.4), (6.4, 11.0)], "white", 1.2, tone=3)
    if ph:
        g.glint(5.6, 3.4)


@accent("tox")
def acid_spit(g, ph):
    # a glob of acid in flight, droplets trailing back, a hissing pool where the last one landed
    g.ell(4.6, 13.6, 4.0, 1.3, "acid", 0.6, bias=0.2)
    for (x, y) in (((3.0, 11.6), (6.4, 11.8)) if not ph else ((2.4, 10.8), (6.8, 11.0))):
        g.dot(x, y, "tox", 3, 0.7)
    s = 0.4 if ph else 0.0
    for i, (x, y, r_) in enumerate(((3.4, 8.4, 0.8), (5.0, 6.0, 1.0), (7.2, 4.2, 1.2))):
        g.ell(x, y, r_, r_, "acid", 0.9 + 0.01 * i, bias=0.2)
    g.ell(11.0, 4.6, 3.6 + s, 3.2 - s * 0.5, "acid", 1.0, bias=0.2)
    g.poly([(13.4, 6.6), (14.6, 9.6), (12.2, 7.4)], "acid", 1.0, bias=0.2)
    g.ell(10.2, 3.6, 1.2, 0.9, "tox", 1.01, flat=4)


@accent("bolt")
def chain_spark(g, ph):
    # a spark jumping monster to monster: three struck points joined by forked bolts
    nodes = ((2.4, 12.6), (7.2, 4.0), (10.6, 11.4), (14.0, 3.2))
    for (a, b) in zip(nodes, nodes[1:]):
        mx, my = (a[0] + b[0]) / 2 + (1.2 if ph else -1.2), (a[1] + b[1]) / 2
        g.polyline([a, (mx, my), b], "bolt", 1.0, tone=3)
        g.polyline([(a[0] + 0.6, a[1]), (mx + 0.6, my), (b[0] + 0.6, b[1])], "ice", 0.95, tone=1)
    for i, (x, y) in enumerate(nodes):
        g.ell(x, y, 1.6, 1.6, "steel", 1.1, flat=1)
        g.ell(x, y, 0.8, 0.8, "bolt", 1.11, flat=3)
        g.dot(x, y, "white", 4, 1.12)
    if ph:
        for (x, y) in ((5.0, 9.6), (12.4, 7.2)):
            g.dot(x, y, "bolt", 4, 1.2)


@accent("white")
def icicle_requiem(g, ph):
    # icicles dropping in a ring: big ones in front, small ones behind, frost dust where they hit
    k = 0.8 if ph else 0.0
    g.ell(8, 14.0, 6.6, 1.4, "ice", 0.4, flat=1)
    for i, (x, top, ln, w, z) in enumerate(((4.4, 1.0, 8.6, 1.6, 0.6), (11.6, 1.6, 8.0, 1.5, 0.6), (8.0, 3.2, 10.6, 2.2, 1.0),
                                             (2.0, 4.6, 6.4, 1.2, 0.8), (14.0, 5.0, 6.2, 1.2, 0.8))):
        y0 = top + k * (1 if i % 2 else 0.6)
        g.poly([(x - w, y0), (x + w, y0), (x, y0 + ln)], "ice", z + 0.01 * i, curve=0.9, bias=0.2)
        g.ell(x, y0, w, 0.6, "ice", z + 0.01 * i + 0.001, flat=3)
        g.line(x - w * 0.4, y0 + 1, x - 0.1, y0 + ln - 1.6, "ice", z + 0.01 * i + 0.002, tone=4)
    for (x, y) in ((5.6, 13.2), (10.4, 13.4), (3.0, 12.8)):
        g.dot(x, y, "white", 3, 1.2)


# ================================================================== artifacts
def marrow_flask(g, ph):
    # a round flask of dark marrow, a knuckle-bone stopper, a little bone plate hung from the neck
    g.ell(8, 10.4, 4.8, 4.4, "glass", 0.9, flat=1)
    g.ell(8, 11.0, 4.2, 3.6, "apple", 1.0, bias=0.1)
    g.ell(7.2, 10.2, 1.8, 1.6, "apple", 1.01, flat=3)
    g.line(3.8, 9.0, 12.2, 9.0, "apple", 1.02, tone=4)
    g.poly([(6.6, 3.4), (9.4, 3.4), (9.4, 6.6), (6.6, 6.6)], "glass", 1.05, curve=0.8)
    g.ell(8, 2.4, 2.0, 1.4, "ivory", 1.1, bias=0.2)
    g.ell(6.4, 2.0, 0.8, 0.8, "ivory", 1.11, bias=0.2)
    g.ell(9.6, 2.0, 0.8, 0.8, "ivory", 1.11, bias=0.2)
    g.line(9.4, 4.4, 11.6, 6.0, "lthr", 1.12, tone=2)
    g.poly([(10.6, 6.0), (13.0, 6.0), (13.0, 8.0), (10.6, 8.0)], "ivory", 1.13, flat=2)
    g.line(10.6, 6.0, 12.6, 6.0, "ivory", 1.14, tone=3)
    g.line(4.6, 8.8, 5.0, 12.0, "white", 1.2, tone=3)
    if ph:
        g.glint(5.4, 8.0)


def rotting_apple(g, ph):
    # an apple gone soft on one side, a bite out of it, a maggot leaning out of the rot
    g.ell(7.6, 9.0, 5.6, 5.2, "apple", 1.0, bias=0.15)
    g.ell(11.6, 9.0, 1.8, 2.6, "shadow", 1.01, flat=1)
    g.ell(12.6, 9.0, 1.6, 2.4, "shadow", 1.02, flat=0)
    g.ell(9.0, 11.6, 2.4, 1.8, "rot", 1.02, bias=0.1)
    for (x, y) in ((8.0, 11.4), (10.0, 12.2)):
        g.dot(x, y, "rot", 0, 1.03)
    g.tube([(7.6, 4.0), (8.0, 2.0)], [0.45], "wood", 1.1)
    g.poly([(8.2, 2.6), (11.2, 1.2), (10.2, 3.4)], "leaf", 1.1, bias=0.3)
    w = 0.6 if ph else 0.0
    g.tube([(10.8, 11.2), (12.4, 10.2 - w), (13.8, 10.8 - w)], [0.7, 0.65, 0.55], "ivory", 1.2, bias=0.25)
    g.dot(13.8, 10.6 - w, "blk", 0, 1.21)
    g.dot(4.8, 6.4, "apple", 4, 1.05); g.dot(5.4, 5.8, "apple", 4, 1.05)
    if ph:
        g.dot(2.6, 2.8, "shadow", 2, 1.3); g.dot(3.6, 2.2, "shadow", 2, 1.3)


@accent("glow")
def hollow_crown(g, ph):
    # a black iron crown with violet stones, its own shadow rising off it
    s = 0.6 if ph else 0.0
    g.poly([(1.6, 8.0 - s), (3.6, 3.6 - s), (5.0, 7.0 - s), (8.0, 1.4 - s), (11.0, 7.0 - s), (12.4, 3.6 - s), (14.4, 8.0 - s)],
           "shadow", 0.5, flat=2)
    for i, (x, top) in enumerate(((2.4, 4.6), (8.0, 2.8), (13.6, 4.6))):
        g.poly([(x - 2.0, 10.0), (x + 2.0, 10.0), (x, top)], "crown", 1.0 + 0.01 * i, curve=0.8, bias=0.3)
        g.ell(x, top - 0.4, 0.9, 0.9, "glow", 1.05, flat=3)
    g.poly([(1.4, 9.0), (14.6, 9.0), (14.0, 13.8), (2.0, 13.8)], "crown", 1.1, curve=0.6, bias=0.3)
    g.line(1.6, 10.4, 14.4, 10.4, "crown", 1.11, tone=4)
    for x in (4.4, 8.0, 11.6):
        g.ell(x, 12.0, 1.0, 0.9, "glow", 1.12, flat=3 if x == 8.0 else 2)
    g.dot(7.6, 11.6, "white", 4, 1.13)


def hive_amber(g, ph):
    # a chunk of amber cut into a hexagon, a little drone trapped inside, comb cells showing in its face
    pts = [(8.0, 1.4), (13.8, 4.6), (13.8, 11.4), (8.0, 14.6), (2.2, 11.4), (2.2, 4.6)]
    g.poly(pts, "amber", 1.0, flat=2)
    g.poly([pts[0], pts[1], (8.0, 8.0), pts[5]], "amber", 1.01, flat=3)
    g.poly([pts[2], pts[3], (8.0, 8.0)], "amber", 1.01, flat=1)
    g.poly([pts[3], pts[4], (8.0, 8.0)], "amber", 1.01, flat=1)
    g.ell(8.0, 8.4, 1.4, 2.2, "rot", 1.05, flat=1)
    g.ell(8.0, 6.2, 1.0, 0.9, "rot", 1.06, flat=0)
    g.ell(6.4, 7.6, 1.4, 0.7, "amber", 1.07, flat=4, ang=-30)
    g.ell(9.6, 7.6, 1.4, 0.7, "amber", 1.07, flat=4, ang=30)
    g.line(3.4, 5.4, 7.2, 3.0, "amber", 1.08, tone=4)
    if ph:
        g.glint(4.8, 4.2)
    else:
        g.dot(12.0, 12.0, "amber", 4, 1.1)


@accent("bolt")
def lightning_rod(g, ph):
    # an iron rod wound with copper wire, a spark jumping at its forked tip
    g.tube([(8.0, 14.6), (8.0, 3.6)], [0.75, 0.6], "iron", 1.0, bias=0.35)
    for y in (6.4, 8.6, 10.8):
        g.tube([(6.6, y + 0.8), (9.4, y - 0.8)], [0.5], "copper", 1.1, bias=0.3)
        g.tube([(9.4, y - 0.8), (9.6, y + 0.2)], [0.4], "copper", 0.9, bias=-0.2)
    g.tube([(8.0, 4.0), (6.2, 1.6)], [0.45], "iron", 1.05, bias=0.35)
    g.tube([(8.0, 4.0), (9.8, 1.6)], [0.45], "iron", 1.05, bias=0.35)
    g.ell(8.0, 14.4, 2.6, 0.9, "iron", 1.06, bias=0.3)
    if ph:
        g.polyline([(6.2, 1.2), (4.4, 2.6), (5.2, 3.4), (3.0, 5.6)], "bolt", 1.2, tone=3)
        g.polyline([(9.8, 1.2), (11.8, 2.4), (11.0, 3.6), (13.4, 5.2)], "bolt", 1.2, tone=3)
        g.dot(8.0, 0.6, "white", 4, 1.2)
    else:
        g.polyline([(6.2, 1.2), (8.0, 0.2), (9.8, 1.2)], "bolt", 1.2, tone=3)
        g.dot(8.0, 0.4, "bolt", 4, 1.2)


def widows_shawl(g, ph):
    # a triangle of frost lace, its holes in a diamond pattern and a fringe of icicle tassels along the bottom
    edge = [(1.0, 3.0), (15.0, 3.0), (8.0, 13.0)]
    hole = lambda x, y: None if ((int(x) + int(y)) % 3 == 0 and (int(x) - int(y)) % 3 == 0) else "lace"
    g.poly(edge, hole, 1.0, curve=0.5, bias=0.2)
    g.tube([(1.0, 3.0), (15.0, 3.0)], [0.7], "lace", 1.05, bias=0.3)
    sw = 0.4 if ph else 0.0
    for i in range(6):
        t = (i + 0.5) / 6.0
        for (ax, ay, bx, by) in ((1.0, 3.0, 8.0, 13.0), (15.0, 3.0, 8.0, 13.0)):
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t
            g.line(x, y + 0.6, x + sw, y + 1.8, "ice", 1.1, tone=3)
    g.dot(8.0, 14.4, "ice", 4, 1.1)
    if ph:
        g.glint(4.4, 4.4)


ICONS = [  # sheet, folder, kind, drawing
    ("IconGraveCall", "out_ossivar", "spell", grave_call),
    ("IconMarrowFlask", "out_ossivar", "artifact", marrow_flask),
    ("IconThornwall", "out_sylvene", "spell", thornwall),
    ("IconRottingApple", "out_sylvene", "artifact", rotting_apple),
    ("IconMirrorStep", "out_umbrael", "spell", mirror_step),
    ("IconHollowCrown", "out_umbrael", "artifact", hollow_crown),
    ("IconZhkAcidSpit", "out_zhekra", "spell", acid_spit),
    ("IconZhkHiveAmber", "out_zhekra", "artifact", hive_amber),
    ("IconKrnChainSpark", "out_kaurn", "spell", chain_spark),
    ("IconKrnLightningRod", "out_kaurn", "artifact", lightning_rod),
    ("IconYsvRequiem", "out_ysveld", "spell", icicle_requiem),
    ("IconYsvShawl", "out_ysveld", "artifact", widows_shawl),
]
DRAW = {s: fn for s, _, _, fn in ICONS}
# their bubble and HUD sheets live here, next to the icon (the other six are made by item_icons.py)
OWN_BUBBLES = {"IconZhkAcidSpit", "IconZhkHiveAmber", "IconKrnChainSpark", "IconKrnLightningRod", "IconYsvRequiem", "IconYsvShawl"}
HUD = {
    "IconZhkHiveAmber": (["....aAa....",
                          "..aAAWAaa..",
                          "..aAkkAaa..",
                          "..aaAkAad..",
                          "..aaaAadd..",
                          "....add....",
                          "..........."], {"a": "b8661a", "A": "e6a03a", "W": "ffd884", "k": "3a2a12", "d": "7a3c0c"}),
    "IconKrnLightningRod": (["...b.y.b...",
                             "....bib....",
                             ".....i.....",
                             "....cic....",
                             ".....i.....",
                             "....cic....",
                             "....iii...."], {"b": "8ab8ff", "y": "ffffff", "i": "65636e", "c": "c47c46"}),
    "IconYsvShawl": (["lLLLLLLLLLl",
                      ".lL.lLl.Ll.",
                      "..lLl.lLl..",
                      "...lL.Ll...",
                      "....lLl....",
                      ".i...l...i.",
                      "..i..i..i.."], {"l": "94aed0", "L": "f2f8ff", "i": "8cc0e8"}),
}


def to_spr(im):
    return V2.to_spr(im)


def save_strip(path_noext, frames, w, h, anim, durs):
    img = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        img.alpha_composite(f, (i * w, 0))
    img.save(path_noext + ".png")
    json.dump({"cellW": w, "cellH": h, "cols": len(frames),
               "anims": [{"name": anim, "frames": list(range(len(frames))), "durations": durs}]}, open(path_noext + ".json", "w"))


def build(out=None):
    import item_icons
    card = item_icons.blank_card()
    for sheet, folder, kind, fn in ICONS:
        outdir = out or os.path.join(ART, folder)
        os.makedirs(outdir, exist_ok=True)
        ims = []
        for ph in (0, 1):
            im, lost = V2.render(fn, ph, sep=V2.PARCH if kind == "spell" else None)
            if lost: print("WARNING %s frame %d: %d px outside the cell" % (sheet, ph, lost))
            ims.append(im)
        img, man = pack(sheet, [("Idle", [to_spr(i) for i in ims], [0.9, 0.25])], 16, 16, V2.FEET, outdir, cols=2)
        preview(img, man, os.path.join(outdir, sheet + "_preview.png"), scale=10)
        if sheet in OWN_BUBBLES:
            bubbles = []
            for ph in (0, 1):
                if kind == "spell":
                    b = card.copy(); bb = card.getbbox()
                    b.alpha_composite(ims[ph], ((bb[0] + bb[2]) // 2 - 8, (bb[1] + bb[3]) // 2 - 8))
                else:
                    pic, _ = V2.render(fn, ph, S=V2.BUBBLE_SCALE)
                    b = Image.new("RGBA", (34, 41), (0, 0, 0, 0))
                    b.alpha_composite(pic, ((34 - pic.width) // 2, 41 - pic.height - 6))
                bubbles.append(b)
            save_strip(os.path.join(outdir, sheet + "Bubble"), bubbles, 34, 41, "Bubble", [0.9, 0.25])
            if kind == "artifact":
                grid, pal = HUD[sheet]
                hud = Image.new("RGBA", (11, 7), (0, 0, 0, 0))
                p = hud.load()
                for y, row in enumerate(grid):
                    assert len(row) == 11, (sheet, row)
                    for x, ch in enumerate(row):
                        if ch != ".": p[x, y] = item_icons.hx(pal[ch]) + (255,)
                save_strip(os.path.join(outdir, sheet + "Hud"), [V2.crawl_image(hud)], 11, 7, "Hud", [0.5])
        print("built", sheet)


if __name__ == "__main__":
    a = sys.argv[1:]
    build(a[a.index("--out") + 1] if "--out" in a else None)
