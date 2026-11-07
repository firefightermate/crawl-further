"""Origin gear worn on the in-game hero: head detection over every hero frame, gear sheets, the anchor table
in src/CrawlFurther.Core/Heroes/HeroGearData.cs and a contact image.

Run from the repo root:  python3 tools/sprites/hero_gear.py [--contact out.png] [--check]

Deterministic and re-runnable: it reads the vanilla hero atlas (the game dump, build/dump) and the mod weapon hero sheets
art/out_weapons/WpnHand_*.json (only to check them), and rewrites
    art/out_herogear/Gear<Origin>.png/.json/_preview.png      16 cells of 15x15: the gear in each head pose
    src/CrawlFurther.Core/Heroes/HeroGearData.cs                                per AtlasHero element: pose + gear cell position
--check only verifies that the table on disk matches what the tool would write (used by validate.py).

How a frame is read (ex2D, verified in exSprite.UpdateMesh): an element is an originalWidth x originalHeight
canvas, trimRect.x from the left and trimRect.y from the TOP; the hero sprite (anchor BotCenter, offset (0,-1))
puts the canvas bottom-centre on the pivot. So canvas pixel (px, py) has its top-left corner at
    local x = (px - W/2) * scale.x + offset.x,   local y = (H - py) * scale.y + offset.y.

Head detection: the vanilla hero head is a tiny 4x5 block of one hair colour over three rows of skin. Every
frame is matched against head templates (side view, bowed head, short hair) in the 8 pixel-exact poses
(4 quarter turns x mirror); the best match gives the pose and the head reference point R = the back-of-head
pixel on the forehead row (canonical upright, facing right):

        . H H H          y = -1   hair crown
        R s s .          y =  0   forehead row (R = back hair)
        s s s .          y =  1   eye row (the eye is x = 2)
        s s s .          y =  2
        s s . .          y =  3   chin

Gear is drawn once in that canonical frame (15x15 cell, R at (7,7)) and turned with the same 8 transforms, so
it sits on the head pixel-exactly in every pose. Frames with no head (smears, transformations, beams) get no
gear. The mod weapon frames (WpnHand_*, tools/sprites/weapon_hands.py) keep their AtlasHero source frame's canvas and
body pixels, so they use the source's entry (the runtime reads the source index from the element name).
"""
import os, sys, json
from collections import Counter, defaultdict
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srcfiles import src_file, pack_files  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DUMP = os.environ.get("CRAWL_DUMP", os.path.join(ROOT, "build", "dump"))
OUT = os.path.join(ROOT, "art", "out_herogear")
CS = src_file("HeroGearData.cs")
WEAPON_DIR = os.path.join(ROOT, "art", "out_weapons")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERO_ATLAS = ("AtlasHero", 39931, DUMP + "/tex/AtlasHero_3.png")
# AtlasHeroBattle (pid 39932) holds only intro props and FX (no clip draws the hero from it): nothing to anchor.

CELL = 15           # gear cell (square so quarter turns stay inside), R at (C0, C0)
C0 = 7
NPOSE = 16          # 8 transforms (4 quarter turns x mirror), then the same 8 without the face pieces
ORIGINS = ["Sellsword", "Huntress", "Hexblade", "Flagellant", "Pilgrim", "Gambler",
           "Reaver", "Cutpurse", "Arbalist", "Scholar"]

# ------------------------------------------------------------------------------------------------ colours
HAIR = {(115, 91, 56)}
SKIN = {(199, 156, 110), (218, 193, 132), (182, 116, 80), (188, 142, 97), (191, 136, 95), (190, 136, 95),
        (187, 128, 89), (170, 124, 83)}


def _jsonl(cls):
    return [json.loads(l) for l in open(DUMP + "/db/" + cls + ".jsonl")]


# ------------------------------------------------------------------------------------------------ frames
class HeroAtlas:
    """The vanilla hero atlas as canvases (exactly as ex2D lays them out) + the clips that use it."""

    def __init__(self):
        name, pid, png = HERO_ATLAS
        self.name = name
        a = [x for x in _jsonl("exAtlas") if x["_pid"] == pid][0]
        self.elements = a["elements"]
        self.img = Image.open(png).convert("RGBA")
        self.clips = {}
        for c in _jsonl("exSpriteAnimClip"):
            if c["frameInfos"] and all(f["atlas"]["m_PathID"] == pid for f in c["frameInfos"]):
                self.clips.setdefault(c["m_Name"], [f["index"] for f in c["frameInfos"]])
        self._cache = {}

    def frame(self, idx):
        if idx in self._cache: return self._cache[idx]
        W, H = self.img.size
        e = self.elements[idx]; c = e["coords"]
        x0 = round(c["x"] * W); y1 = H - round(c["y"] * H)
        w = round(c["width"] * W); h = round(c["height"] * H)
        crop = self.img.crop((x0, y1 - h, x0 + w, y1))
        if e["rotated"]: crop = crop.rotate(90, expand=True)     # ex2D rotated = stored a quarter turn clockwise
        t = e["trimRect"]
        cv = Image.new("RGBA", (e["originalWidth"], e["originalHeight"]), (0, 0, 0, 0))
        cv.paste(crop, (int(t["x"]), int(t["y"])))                # trimRect.y counts from the top
        self._cache[idx] = cv
        return cv


# ------------------------------------------------------------------------------------------------ matching
def classes(f):
    px = f.load(); W, H = f.size; m = {}
    for y in range(H):
        for x in range(W):
            p = px[x, y]
            if p[3] < 128: continue
            q = p[:3]
            m[(x, y)] = 'H' if q in HAIR else 's' if q in SKIN else 'o'
    return m


# canonical templates (facing right, upright): rows, forehead row (R = (0, that row)), face visible
TEMPLATES = {
    "side":  ([".HHH", "Hss.", "sss.", "sss."], 1, True),
    "bowed": ([".HH.", "HHHH", "Hss.", "sss."], 2, True),
    "short": ([".HH.", "Hss.", "sss.", "sss."], 1, True),
    "wide":  ([".HHHH", "Hssss", "sssss"], 1, True),        # squashed head (hit, lunges)
    "droop": ([".HH.", "HHHH", "sHHH", ".s.."], 2, False),  # head hung forward: crown and nape only
}
# weights: template cell vs frame pixel class. Arms and weapons over the head ('o') cost little, empty space a lot.
W_H = {'H': 3, 's': -1, 'o': -0.5, None: -2}
W_S = {'s': 2, 'H': -1, 'o': -0.5, None: -2}
W_E = {'H': -1, 's': -1, 'o': 0, None: 0}
UPRIGHT_BONUS = 2.0     # pose 0 (upright, facing right) wins unless the pixels clearly say otherwise


def A(t, x, y):
    """Pose transform t of a canonical offset: mirror (t >= 4) then t % 4 quarter turns clockwise."""
    if t >= 4: x = -x
    for _ in range(t % 4): x, y = -y, x
    return x, y


def _tpl_points():
    out = []
    for key, (rows, fy, face) in sorted(TEMPLATES.items()):
        pts = [(x, y - fy, ch) for y, r in enumerate(rows) for x, ch in enumerate(r)]   # relative to R
        for t in range(8):
            out.append((key, t, face, [A(t, x, y) + (ch,) for x, y, ch in pts]))
    return out


TPL = _tpl_points()
MAXSC = {key: sum(3 if ch == 'H' else 2 if ch == 's' else 0 for r in rows for ch in r)
         for key, (rows, _, _) in TEMPLATES.items()}
MIN_QUALITY = 0.5
# a frame whose head is mostly hidden (weapon or arm across it, smear) between frames of the same clip that matched:
# the best placement in the neighbour's pose within NEAR_R px of its head is kept if it still finds some head
NEAR_R, NEAR_QUALITY, NEAR_FRAMES = 2, 0.1, 2
FLIP_QUALITY = 0.3
LOOSE_QUALITY = 0.25
# hero frames that show hair but get no gear, checked by eye (validate.py requires every other hero frame with a
# head to have an anchor): the head is stretched into a teleport/portal beam or crushed in the demon's grab
NO_HEAD = {"demon_grab_hero_12", "demon_grab_hero_25", "demon_grab_hero_26", "hero_portal_beamup_05",
           "hero_teleport_to_store_12", "kicked_outof_portal_02"}


def hair_near(m, n):
    """At least two hair pixels inside the head box of neighbour entry n (its pose, R)."""
    rx, ry = n[1] + C0, n[2] + C0
    box = set(A(n[0] % 8, x, y) for x in range(0, 4) for y in range(-2, 4))
    return sum(1 for (x, y) in box if m.get((rx + x, ry + y)) == 'H') >= 2


def match(m, near=None):
    """Best (quality, key, pose, Rx, Ry, face) or None; pose 0-7 = transform. Deterministic tie-breaks.
    near = (pose, Rx, Ry): only that pose, R within NEAR_R pixels (a neighbouring frame of the same clip)."""
    hs = sorted(p for p, v in m.items() if v == 'H')
    if not hs: return None
    cand = set()
    if near is None:
        for (x, y) in hs:
            for dx in range(-4, 5):
                for dy in range(-4, 5): cand.add((x + dx, y + dy))
    else:
        for dx in range(-NEAR_R, NEAR_R + 1):
            for dy in range(-NEAR_R, NEAR_R + 1): cand.add((near[1] + dx, near[2] + dy))
    cand = sorted(cand)
    best = None
    for key, t, face, pts in TPL:
        if near is not None and (t + (0 if face else 8)) != near[0]: continue
        for (rx, ry) in cand:
            sc = 0.0
            for x, y, ch in pts:
                v = m.get((rx + x, ry + y))
                sc += (W_H if ch == 'H' else W_S if ch == 's' else W_E)[v]
            q = sc / float(MAXSC[key])
            k = (q + (UPRIGHT_BONUS / MAXSC[key] if t == 0 else 0.0), -t, key == "side", -ry, -rx)
            if best is None or k > best[0]:
                best = (k, (q, key, t, rx, ry, face))
    return best[1] if best else None


# ------------------------------------------------------------------------------------------------ gear art
# Canonical cell: 15x15, R at (7,7). Rows are written as 15-character strings starting at row y0
# (cell row = y0 + i). Head for reference: hair crown cells (8..10, 6); R (7,7); face cells x 7..9, rows 7..10,
# eye at (9, 8). '.' = transparent. Light from the top-left: each material has a highlight, light, base and shadow
# tone, and its own dark ink ('k' and friends) on the silhouette, where the gear meets the floor behind the hero.
#            0123456789ABCDE
GEAR = {
    # steel kettle helm: a lit dome, a riveted band, a flared brim, mail hanging at the nape
    "Sellsword": dict(y0=3, rows=[
        "......kkkk.....",
        ".....k4433k....",
        "....k443322k...",
        "....k3r22r1k...",
        "...kk111111kk..",
        ".....kMm..k....",
        ".....kmM.......",
        "......km.......",
        ".......k.......",
    ], pal={"k": "1c1e26", "4": "e2e2ea", "3": "a8a8b4", "2": "767682", "1": "4c4c58", "r": "f2f2f8",
            "m": "4a4a56", "M": "8c8c98"}),
    # green hood with its tail hanging down the back: the crown and nape covered, the face open in its shadow
    "Huntress": dict(y0=4, rows=[
        "......kkkk.....",
        ".....k-==-k....",
        "....k-====+k...",
        "...k-=+#..++k..",
        "...k=+##.......",
        "..k-=+#........",
        "..k=++#........",
        ".k=+kk.........",
        ".k+k...........",
        "..k............",
    ], pal={"k": "142014", "-": "7c9050", "=": "56683c", "+": "3a4a2a", "#": "232e1c"}),
    # violet cowl whose peak trails back, a cold glow where the eye is
    "Hexblade": dict(y0=1, rows=[
        "..kk...........",
        "..kIk..........",
        "...kIk.........",
        "...kINkkkk.....",
        "....kINNIIk....",
        "....kINNInnk...",
        "....kNnC..nk...",
        "....kNnC..%....",
        "....kNnC.......",
        "....knnC.......",
        ".....knk.......",
        "......k........",
    ], face="%", pal={"k": "100a18", "C": "24163a", "n": "45265c", "N": "6c408c", "I": "9a6cc0", "%": "ecc0ff"}),
    # wild spiky hair (the penitent goes bare-headed) and a streak of blood down the cheek
    "Flagellant": dict(y0=2, rows=[
        "....k..k..k....",
        "....kk.kk.kk.k.",
        "...kHkkHhkhHkk.",
        "..kHHhHHhhHhhk.",
        "...khHhhdhhdk..",
        "...kdhdk....k..",
        "....kdd........",
        "....kd...r.....",
        ".........r.....",
    ], face="r", pal={"k": "221416", "H": "a68654", "h": "86643a", "d": "5e4228", "r": "b02420"}),
    # pilgrim's hat: a tall felt crown, a coloured band with a scallop-shell badge, a broad brim drooping at the ends
    "Pilgrim": dict(y0=2, rows=[
        ".......kkk.....",
        "......k6664k...",
        ".....k666442k..",
        ".....krrwrRRk..",
        "..kk664444422kk",
        ".k442222222211k",
        "..kk........kk.",
    ], pal={"k": "1c1c24", "6": "8a8a9a", "4": "5a5a6a", "2": "3e3e4a", "1": "2a2a34", "r": "b02a20", "R": "6e1412",
            "w": "e8e0c8"}),
    # black tricorn: both brim points turned up and edged in gold, a red plume curling off the back
    "Gambler": dict(y0=0, rows=[
        "..rr...........",
        ".rRrr..........",
        "..kRrr.kkkk....",
        "...kRRk4332k...",
        "..kGgk333221kGk",
        "..kgGg222211gGk",
        "...kkGggggggkk.",
    ], pal={"k": "13110e", "4": "5c4e48", "3": "403430", "2": "2a2420", "1": "1e1a16", "g": "9c8a4a", "G": "e0c46a",
            "r": "ff4a2c", "R": "a8281a"}),
    # bristling ginger mane, a braided beard, a blue woad stripe across the eye
    "Reaver": dict(y0=2, rows=[
        ".....k..k.k....",
        "....kEk.EkEk...",
        "...kEEkEEOEEk..",
        "..kEEOEEOOEOEk.",
        "...kEOOOOOOOOk.",
        "..kOOOzz....k..",
        "...kOz.bBb.....",
        "...kOz.zO......",
        "....kzOOOk.....",
        ".....kOzOk.....",
        "......kzk......",
        ".......k.......",
    ], face="bBzO", pal={"k": "251b16", "E": "f09a4a", "O": "c06428", "z": "7c381c", "b": "3d6fb0", "B": "6a9ad8"}),
    # charcoal hood with a lit crown, a teal cloth mask over nose and mouth, its knot trailing at the back
    "Cutpurse": dict(y0=4, rows=[
        ".......kkkk....",
        "......k8664k...",
        ".....k86644kk..",
        "....k864#..4k..",
        "....k64#.......",
        "....k64#TTTk...",
        "...kT44tTttk...",
        "..kTk.kkkk.....",
    ], face="Tt", pal={"k": "161c1e", "8": "8a847e", "6": "66605c", "4": "4a4544", "#": "2c2a2a", "T": "4e867e",
                       "t": "2e5e58"}),
    # chapel-de-fer: a low steel dome on a broad brim that droops at both ends, rivets round the brim
    "Arbalist": dict(y0=3, rows=[
        "......kkkk.....",
        ".....k5543k....",
        "....k443322k...",
        "..kk44r322r21kk",
        ".k32222222111k.",
        "..kk.......kk..",
    ], pal={"k": "1c1a20", "5": "eeeef4", "4": "b0b0ba", "3": "84848e", "2": "62626e", "1": "3a3a44", "r": "f2f2f8"}),
    # white hair caught up in a bun with a gold pin, wisps at the nape, gold-rimmed spectacles
    "Scholar": dict(y0=2, rows=[
        "....kk.........",
        "...kWQk.kkk....",
        "...kQ:Pk4WWk...",
        "....k:kWWWQ:k..",
        "....kWWQQQ::k..",
        "....k:W:.......",
        ".....k:..gGg...",
        "......:........",
    ], face="gG", pal={"k": "4a4642", "W": "f2eee6", "4": "ffffff", "Q": "c6c2ba", ":": "8e8a84", "P": "d8b04a",
                       "g": "b0903c", "G": "fff0b0"}),
}


def hexrgb(s):
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def tame(rgb):
    """Keep gear colours in Crawl's muted range (the vanilla hero's own tunic is about as colourful as it gets)."""
    import weapon_bubbles
    return weapon_bubbles.tame(rgb, 0.42, 0.75)


def ramp_safe(rgb, ramps):
    """Nudge a colour until its _ColorRamp slot is pink (= draw as is) in every vanilla palette, so no
    palette material can ever recolour it. Deterministic: tries the smallest changes first."""
    def ok(c):
        x = min(15, c[0] * 16 // 255) + 16 * min(15, c[1] * 16 // 255); y = min(63, c[2] * 64 // 255)
        return all(r[x + 256 * y] for r in ramps)
    if ok(rgb): return rgb
    for d in range(1, 24):
        for dr, dg, db in sorted({(a, b, c) for a in (-d, 0, d) for b in (-d, 0, d) for c in (-d, 0, d)},
                                 key=lambda v: (abs(v[0]) + abs(v[1]) + abs(v[2]), v)):
            c = (min(255, max(0, rgb[0] + dr)), min(255, max(0, rgb[1] + dg)), min(255, max(0, rgb[2] + db)))
            if ok(c): return c
    return rgb


def load_ramps():
    """For every Palette*.png in the dump: a flat list, True where the slot is pink (no recolour)."""
    out = []
    for f in sorted(os.listdir(DUMP + "/tex")):
        if not f.startswith("Palette") or not f.endswith(".png"): continue
        im = Image.open(DUMP + "/tex/" + f).convert("RGB")
        if im.size != (256, 64): continue
        px = im.load()
        out.append([px[i % 256, 63 - i // 256] == (255, 0, 255) for i in range(256 * 64)])
    return out


def gear_pixels(origin, ramps):
    """{(dx, dy) relative to R: RGBA} of an origin's canonical gear."""
    g = GEAR[origin]
    pal = {k: ramp_safe(tame(hexrgb(v)), ramps) for k, v in g["pal"].items()}
    out = {}
    for i, row in enumerate(g["rows"]):
        assert len(row) == CELL, (origin, i, row)
        for x, ch in enumerate(row):
            if ch == '.': continue
            out[(x - C0, g["y0"] + i - C0)] = (pal[ch] + (255,), ch in g.get("face", ""))
    return out


def gear_cell(pix, pose):
    """Cell for pose 0-15: transform pose % 8; poses 8-15 leave out the face pieces (head hung, face unseen)."""
    im = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    p = im.load()
    for (x, y), (c, face) in pix.items():
        if face and pose >= 8: continue
        u, v = A(pose % 8, x, y)
        p[C0 + u, C0 + v] = c
    return im


def write_sheets(ramps):
    os.makedirs(OUT, exist_ok=True)
    cells = {}
    for o in ORIGINS:
        pix = gear_pixels(o, ramps)
        imgs = [gear_cell(pix, t) for t in range(NPOSE)]
        cells[o] = imgs
        sheet = Image.new("RGBA", (128, 32), (0, 0, 0, 0))
        for t, im in enumerate(imgs): sheet.paste(im, ((t % 8) * CELL, (t // 8) * CELL))
        sheet.save(os.path.join(OUT, "Gear%s.png" % o))
        man = {"cellW": CELL, "cellH": CELL, "cols": 8,
               "anims": [{"name": "Pose%d" % t, "frames": [t], "durations": [1.0]} for t in range(NPOSE)]}
        with open(os.path.join(OUT, "Gear%s.json" % o), "w") as fh: json.dump(man, fh)
        prev = Image.new("RGBA", (8 * (CELL + 1) + 1, 2 * (CELL + 1) + 1), (52, 50, 60, 255))
        for t, im in enumerate(imgs): prev.alpha_composite(im, (1 + (t % 8) * (CELL + 1), 1 + (t // 8) * (CELL + 1)))
        prev.resize((prev.width * 8, prev.height * 8), Image.NEAREST).save(os.path.join(OUT, "Gear%s_preview.png" % o))
    return cells


# ------------------------------------------------------------------------------------------------ anchors
def analyse_vanilla(ha):
    """{element index: (pose, gx, gy, quality, how)} for every element of the hero atlas (pose -1 = none).
    Pass 1 matches every frame alone; pass 2 fills mostly hidden heads from matched neighbours in a clip."""
    res = {}
    cls = {}
    for i in range(len(ha.elements)):
        cls[i] = classes(ha.frame(i))
        r = match(cls[i])
        if r is None or r[0] < MIN_QUALITY:
            res[i] = (-1, 0, 0, r[0] if r else 0.0, "none")
        else:
            q, key, t, rx, ry, face = r
            res[i] = (t + (0 if face else 8), rx - C0, ry - C0, q, key)
    for _ in range(3):              # a run of hidden frames fills from both ends inwards
        changed = False
        for name in sorted(ha.clips):
            fr = ha.clips[name]
            for k, i in enumerate(fr):
                if res[i][0] >= 0 or not any(v == 'H' for v in cls[i].values()): continue
                free = match(cls[i])
                best, how = None, None
                for d in range(1, NEAR_FRAMES + 1):
                    for j in (k - d, k + d):
                        if not 0 <= j < len(fr): continue
                        n = res[fr[j]]
                        if n[0] < 0 or n[4].startswith("hold"): continue
                        # 1. its own best reading, when it agrees with the neighbour's pose and place
                        if free is not None and free[0] >= LOOSE_QUALITY and free[2] + (0 if free[5] else 8) == n[0] \
                                and max(abs(free[3] - C0 - n[1]), abs(free[4] - C0 - n[2])) <= NEAR_R + 2:
                            if best is None or free[0] > best[0]: best, how = free, "near"
                            continue
                        # 2. the best reading in the neighbour's pose next to the neighbour's head
                        r = match(cls[i], near=(n[0], n[1] + C0, n[2] + C0))
                        if r is not None and r[0] >= NEAR_QUALITY and (best is None or r[0] > best[0]):
                            best, how = r, "near"
                        # 3. the head is behind a weapon/arm but its hair still shows there: keep the neighbour's place
                        elif best is None and hair_near(cls[i], n):
                            best, how = (0.0, "hold", n[0] % 8, n[1] + C0, n[2] + C0, n[0] < 8), "hold"
                    if best: break
                if best:
                    q, key, t, rx, ry, face = best
                    res[i] = (t + (0 if face else 8), rx - C0, ry - C0, q, how + ":" + name)
                    changed = True
        if not changed: break
    # pass 3: a lone pose flip (both clip neighbours agree on another pose) is an ambiguous head: re-read it in theirs
    for name in sorted(ha.clips):
        fr = ha.clips[name]
        for k in range(1, len(fr) - 1):
            i, a, b = fr[k], res[fr[k - 1]], res[fr[k + 1]]
            if res[i][0] < 0 or a[0] < 0 or a[0] != b[0] or a[0] == res[i][0]: continue
            r = match(cls[i], near=(a[0], (a[1] + b[1]) // 2 + C0, (a[2] + b[2]) // 2 + C0))
            if r is not None and r[0] >= FLIP_QUALITY:
                q, key, t, rx, ry, face = r
                res[i] = (t + (0 if face else 8), rx - C0, ry - C0, q, "flip:" + name)
    return res


def hand_sheets():
    """[(sheet id, [[src, cell, origW, origH, x, y, w, h], ...])] of the mod weapon hero sheets
    (art/out_weapons/WpnHand_*.json, tools/sprites/weapon_hands.py). At run time WeaponPack shows them as atlases
    "ModAtlas_WpnHand_<id>" whose element k is named "WpnHand_<id>_<src>" and keeps AtlasHero element src's canvas
    and body pixels, so HeroGear reads src from the element name and uses src's anchor."""
    out = []
    if not os.path.isdir(WEAPON_DIR): return out
    for f in sorted(os.listdir(WEAPON_DIR)):
        if not (f.startswith("WpnHand_") and f.endswith(".json")): continue
        try:
            m = json.load(open(os.path.join(WEAPON_DIR, f)))
        except Exception:
            continue
        if isinstance(m.get("hero"), list): out.append((f[:-5], m["hero"]))
    return out


def check_hands(ha, van):
    """Every WpnHand frame must keep its source frame's canvas and head pixels (else the src anchor is wrong)."""
    problems, n = [], 0
    for sid, rows in hand_sheets():
        png = os.path.join(WEAPON_DIR, sid + ".png")
        man = json.load(open(os.path.join(WEAPON_DIR, sid + ".json")))
        img = Image.open(png).convert("RGBA")
        cw, ch, cols = man["cellW"], man["cellH"], max(1, man.get("cols", 1))
        for src, cell, ow, oh, x, y, w, h in rows:
            n += 1
            e = ha.elements[src] if 0 <= src < len(ha.elements) else None
            if e is None:
                problems.append("%s: src %d is not an AtlasHero element" % (sid, src)); continue
            if (ow, oh) != (e["originalWidth"], e["originalHeight"]):
                problems.append("%s: src %d canvas %dx%d != %dx%d" % (sid, src, ow, oh, e["originalWidth"], e["originalHeight"]))
                continue
            if van[src][0] < 0: continue
            cv = Image.new("RGBA", (ow, oh), (0, 0, 0, 0))
            px0, py0 = (cell % cols) * cw, (cell // cols) * ch
            cv.paste(img.crop((px0, py0, px0 + w, py0 + h)), (x, y))
            a, b = classes(ha.frame(src)), classes(cv)
            head = [p for p, v in a.items() if v in ('H', 's') and abs(p[0] - van[src][1] - C0) <= 4 and abs(p[1] - van[src][2] - C0) <= 5]
            moved = [p for p in head if b.get(p) not in (a[p], 'o')]
            if moved: problems.append("%s: src %d (%s) head pixels changed at %s" % (sid, src, e["name"], moved[:3]))
    return n, problems


def encode(entries, n):
    """One int per frame: 0 = no gear, else (pose + 1) | (gx + 512) << 5 | (gy + 512) << 15."""
    vals = []
    for i in range(n):
        e = entries.get(i)
        if e is None or e[0] < 0: vals.append(0); continue
        t, gx, gy = e[0], e[1], e[2]
        vals.append((t + 1) | ((gx + 512) << 5) | ((gy + 512) << 15))
    return vals


def cs_text(van, n_van):
    L = ["// <auto-generated> by tools/sprites/hero_gear.py from the vanilla hero atlas (AtlasHero).",
         "// Do not edit by hand: re-run the tool (it is deterministic).",
         "namespace CrawlFurther.Heroes", "{",
         "    public static partial class HeroGearData", "    {",
         "        /// <summary>Gear cell size (pixels) and the head reference point inside a cell.</summary>",
         "        public const int Cell = %d, Ref = %d, Poses = %d;" % (CELL, C0, NPOSE),
         "        /// <summary>Per AtlasHero element: 0 = no gear; else gear cell = (v &amp; 31) - 1 (pose 0-7, +8 = face",
         "        /// hidden), its top-left in the frame canvas = ((v >> 5 &amp; 1023) - 512, (v >> 15 &amp; 1023) - 512).</summary>",
         "        public static readonly int[] AtlasHero =",
         "        {"]
    vals = encode(van, n_van)
    for i in range(0, len(vals), 12):
        L.append("            " + ", ".join(str(v) for v in vals[i:i + 12]) + ",")
    L += ["        };", "    }", "}", ""]
    return "\n".join(L)


# ------------------------------------------------------------------------------------------------ contact
CONTACT_CLIPS = [
    ("idle", ["Idle", "RustySwordIdle", "BowIdle", "StaffIdleVariantMagic", "GenericIdle3"]),
    ("run", ["RunEdit", "AxeRun", "CrossbowRun"]),
    ("attacks", ["RustySwordCombo1", "2HSwordCombo1", "AxeAttack", "AxeAttackAngle4Up", "SpearCombo1upfacing",
                 "DaggerCombo2", "ClubCombo3", "BowCombo1", "CrossbowCombo1", "SlingCombo2", "StaffCombo1",
                 "KnivesCombo2", "1HSwordSpecialSpin"]),
    ("hurt", ["Hit", "HitUpInAir", "DizzyStart", "HitSlamDown"]),
    ("roll", ["SpellsDodgeRoll", "SpellsTribalShield", "SpellsBullCharge"]),
    ("death", ["Dead", "FallenInjured2"]),
]


def contact(ha, van, cells, path, per_row=34):
    import hero_looks as hl
    cols = hl.atlas_colours(); used = set(cols)
    base = hl.load_ramp(hl.RAMPS["P1"])
    frames = []
    seen = set()
    for _, names in CONTACT_CLIPS:
        for n in names:
            if n not in ha.clips: print("contact: no clip", n); continue
            for i in ha.clips[n]:
                if i in seen: continue
                seen.add(i); frames.append((n, i))
    # each frame cropped to a fixed window around its head (or its body centre when it has none)
    WIN_W, WIN_H = 30, 30
    def window(i):
        f = ha.frame(i); e = van[i]
        bb = f.getbbox() or (0, 0, f.width, f.height)
        if e[0] >= 0: cx, cy = e[1] + C0, e[2] + C0 + 6
        else: cx, cy = (bb[0] + bb[2]) // 2, (bb[1] + bb[3]) // 2
        return (cx - WIN_W // 2, cy - WIN_H // 2)
    rows = []
    for o in ["Wanderer"] + ORIGINS:
        ramp = dict(base)
        ramp.update(hl.plan(hl.swaps_for(hl.LOOKS[o], cols), base, used))
        rows.append((o, ramp))
    ncell = len(frames)
    nr = (ncell + per_row - 1) // per_row
    S = 3
    lab = 64
    block_h = len(rows) * (WIN_H + 1) + 6
    img = Image.new("RGBA", (lab + per_row * (WIN_W + 1), nr * block_h), (44, 42, 52, 255))
    rc = {}
    for bi in range(nr):
        for ri, (o, ramp) in enumerate(rows):
            for k in range(per_row):
                j = bi * per_row + k
                if j >= ncell: break
                n, i = frames[j]
                if (o, i) not in rc:
                    f = hl.simulate(ha.frame(i), ramp)
                    e = van[i]
                    if o != "Wanderer" and e[0] >= 0:
                        _comp(f, cells[o][e[0]], e[1], e[2])
                    rc[(o, i)] = f
                f = rc[(o, i)]
                wx, wy = window(i)
                tile = Image.new("RGBA", (WIN_W, WIN_H), (64, 62, 74, 255) if ri % 2 == 0 else (58, 56, 68, 255))
                tile.alpha_composite(_crop(f, wx, wy, WIN_W, WIN_H))
                img.paste(tile, (lab + k * (WIN_W + 1), bi * block_h + ri * (WIN_H + 1)))
    img = img.resize((img.width * S, img.height * S), Image.NEAREST)
    d = ImageDraw.Draw(img)
    for bi in range(nr):
        for ri, (o, _) in enumerate(rows):
            d.text((4, (bi * block_h + ri * (WIN_H + 1)) * S + WIN_H * S // 2 - 6), o, fill=(230, 226, 214))
        for k in range(per_row):
            j = bi * per_row + k
            if j >= ncell: break
            n, i = frames[j]
            if k == 0 or frames[j - 1][0] != n:
                d.text(((lab + k * (WIN_W + 1)) * S + 2, (bi * block_h + len(rows) * (WIN_H + 1)) * S - 2), n[:16], fill=(255, 220, 120))
    img.convert("RGB").save(path)
    print("contact ->", path, img.size, "%d frames" % ncell)


def _crop(f, x, y, w, h):
    big = Image.new("RGBA", (f.width + 2 * max(w, h), f.height + 2 * max(w, h)), (0, 0, 0, 0))
    big.paste(f, (max(w, h), max(w, h)))
    return big.crop((x + max(w, h), y + max(w, h), x + max(w, h) + w, y + max(w, h) + h))


def _comp(f, cell, x, y):
    """alpha_composite that tolerates a cell hanging over the canvas edge (the runtime draws it anyway)."""
    pad = CELL
    big = Image.new("RGBA", (f.width + 2 * pad, f.height + 2 * pad), (0, 0, 0, 0))
    big.paste(f, (pad, pad))
    big.alpha_composite(cell, (x + pad, y + pad))
    f.paste(big.crop((pad, pad, pad + f.width, pad + f.height)), (0, 0))


# ------------------------------------------------------------------------------------------------ main
def build():
    ha = HeroAtlas()
    van = analyse_vanilla(ha)
    return ha, van


def stats(ha, van):
    used = sorted(set(i for v in ha.clips.values() for i in v))
    nu = sum(1 for i in used if van[i][0] >= 0)
    near = sum(1 for i in used if van[i][0] >= 0 and van[i][4].startswith("near"))
    poses = Counter(van[i][0] for i in used if van[i][0] >= 0)
    print("hero atlas: %d elements, %d used by clips: %d with gear (%d filled from clip neighbours), %d without (no head)" %
          (len(van), len(used), nu, near, len(used) - nu))
    print("poses:", dict(sorted(poses.items())))
    n, probs = check_hands(ha, van)
    print("weapon hand frames: %d (anchors from their AtlasHero source), %d problems" % (n, len(probs)))
    for p in probs[:20]: print("  ", p)


def main():
    args = sys.argv[1:]
    ha, van = build()
    text = cs_text(van, len(ha.elements))
    if "--check" in args:
        cur = open(CS).read() if os.path.exists(CS) else ""
        if cur != text:
            print("HeroGearData.cs is stale: re-run python3 tools/sprites/hero_gear.py"); sys.exit(1)
        print("HeroGearData.cs up to date"); return
    ramps = load_ramps()
    cells = write_sheets(ramps)
    with open(CS, "w") as fh: fh.write(text)
    print("table ->", CS)
    stats(ha, van)
    if "--contact" in args:
        contact(ha, van, cells, args[args.index("--contact") + 1])


if __name__ == "__main__":
    main()
