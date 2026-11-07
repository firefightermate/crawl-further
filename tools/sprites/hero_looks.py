"""Hero-origin colour looks: palette roles of the vanilla hero, per-origin colour schemes, the C# tables
(content OriginColours.cs, Core HeroLooks.cs), and a preview that recolours real hero frames exactly like the ramp shader does.

Run from the repo root:  python3 tools/sprites/hero_looks.py [preview.png]

How the game recolours the hero (verified in the decompiled code + the SpritePaletted shader):
  slot x = min(15, floor(r*16)) + 16*min(15, floor(g*16)),  slot y = min(63, floor(b*64))   (256x64 ramp)
  ramp pixel == pink (1,0,1)  -> the atlas colour is drawn unchanged, otherwise the ramp colour is drawn.
Each player has their own ramp (PlayerSetup.m_heroMaterial._ColorRamp: PaletteBlue/Red/Green/Yellow), which
already maps the tunic, vest and shadow slots to the player's colour. An origin writes its colours over those
slots (exact slot always; the 8 neighbours only where the ramp is pink and no hero-atlas colour lives there,
which is ColorSwapper's own neighbour rule made safe). HeroLooks.cs does exactly what simulate() does.
Needs the game dump (build/dump, or CRAWL_DUMP): atlas, ramps, clips.
"""
import os, sys, json, re
from collections import Counter, defaultdict
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srcfiles import src_file, pack_files  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DUMP = os.environ.get("CRAWL_DUMP", os.path.join(ROOT, "build", "dump"))
BOARDS = os.path.join(ROOT, "build", "boards")
CS = src_file("HeroLooks.cs")              # Core: the ramp slots the hero atlas uses
CS_ORIGINS = src_file("OriginColours.cs")  # content: each origin's colours per player slot
PINK = (255, 0, 255)

# ------------------------------------------------------------------ vanilla data
ATLAS_PNG = DUMP + "/tex/AtlasHero_3.png"
RAMPS = {"P1": "PaletteBlue_161", "P2": "PaletteRed_152", "P3": "PaletteGreen_134", "P4": "PaletteYellow_141"}
HERO_ATLAS_PID = 39931


def slot(c):
    r, g, b = c[:3]
    return min(15, r * 16 // 255) + 16 * min(15, g * 16 // 255), min(63, b * 64 // 255)


def load_ramp(name):
    im = Image.open(DUMP + "/tex/" + name + ".png").convert("RGB")
    px = im.load()
    # PNG rows are top-down, Unity texture rows bottom-up
    return {(x, y): px[x, 63 - y] for x in range(256) for y in range(64)}


def _jsonl(cls):
    return [json.loads(l) for l in open(DUMP + "/db/" + cls + ".jsonl")]


class Clips:
    def __init__(self):
        a = [x for x in _jsonl("exAtlas") if x["_pid"] == HERO_ATLAS_PID][0]
        self.elements = a["elements"]
        self.img = Image.open(ATLAS_PNG).convert("RGBA")
        self.clips = {}
        for c in _jsonl("exSpriteAnimClip"):
            if c["frameInfos"] and c["frameInfos"][0]["atlas"]["m_PathID"] == HERO_ATLAS_PID:
                self.clips.setdefault(c["m_Name"], c)

    def frame(self, idx):
        W, H = self.img.size
        e = self.elements[idx]; c = e["coords"]
        x0 = round(c["x"] * W); y1 = H - round(c["y"] * H)
        w = round(c["width"] * W); h = round(c["height"] * H)
        crop = self.img.crop((x0, y1 - h, x0 + w, y1))
        if e["rotated"]: crop = crop.rotate(-90, expand=True)
        t = e["trimRect"]
        cv = Image.new("RGBA", (e["originalWidth"], e["originalHeight"]), (0, 0, 0, 0))
        cv.paste(crop, (int(t["x"]), e["originalHeight"] - int(t["y"]) - crop.size[1]))
        return cv

    def get(self, name):
        return [self.frame(f["index"]) for f in self.clips[name]["frameInfos"]]


def atlas_colours():
    """slot -> Counter(colour -> pixel count) over every opaque pixel of the hero atlas."""
    im = Image.open(ATLAS_PNG).convert("RGBA")
    out = defaultdict(Counter)
    for p in im.getdata():
        if p[3] > 0: out[slot(p)][p[:3]] += 1
    return out


# ------------------------------------------------------------------ palette roles
# Slots of the vanilla hero, grouped the way the player ramps group them (PaletteRed maps each group to one
# ramp step). Found by false-colouring every hero frame; weapons, blood, skin and hilt slots are left alone.
ROLES = {
    "clothL": [(76, 10), (76, 11), (76, 13)],                                   # front leg, sleeve/shoulder light
    "clothM": [(90, 11), (90, 13), (74, 9), (74, 10), (73, 12)],                # sleeves, back leg
    "clothS": [(72, 10), (72, 13), (72, 9), (56, 11), (56, 8), (71, 11)],       # collar/shoulder shade
    "trim":   [(56, 9), (55, 11), (55, 12), (54, 12), (57, 9), (57, 10)],       # belt line + boots
    "shadow": [(36, 11), (37, 11), (37, 10), (36, 13), (35, 10)],               # back arm / far side in shadow
    "vestM":  [(88, 14), (71, 14), (87, 16), (71, 16), (72, 16), (70, 13), (72, 12)],  # torso
    # (86,17) is left out: it is mostly the book in ChantingFromBook/ExpeditionNapoleon/GenericIdle4
    "vestL":  [(88, 18), (88, 17), (88, 19), (89, 18), (87, 19)],               # torso light
    "hair":   [(87, 14)],                                                       # hair
    # (88,13) is left out: vanilla folds it into hair, but it is the backpack in the HeavyPack* clips
}

# Origin schemes: role -> colour. Missing roles keep the player's own colour.
H = lambda s: tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
LOOKS = {
    "Wanderer": {},
    # rust tunic, steel mail, iron half-helm
    "Sellsword": dict(clothL=H("c4542e"), clothM=H("a6462a"), clothS=H("843a26"), trim=H("4a3428"),
                      shadow=H("4c2a28"), vestM=H("7c808c"), vestL=H("aeb2bc"), hair=H("6a6c78")),
    # green hood and cloak over a rust tunic
    "Huntress": dict(clothL=H("6a8a42"), clothM=H("587636"), clothS=H("44602c"), trim=H("5e4028"),
                     shadow=H("2c3a22"), vestM=H("a2442a"), vestL=H("bc5a38"), hair=H("769846")),
    # violet cowl and robe
    "Hexblade": dict(clothL=H("8a5cb4"), clothM=H("70489a"), clothS=H("56347e"), trim=H("2e1e3e"),
                     shadow=H("2a1a38"), vestM=H("422a5e"), vestL=H("5a3c7e"), hair=H("7e50a8")),
    # bare scarred torso, dark sackcloth breeches, rope belt, blood-dark shadows (hair stays as in the portrait)
    "Flagellant": dict(clothL=H("6e604c"), clothM=H("5c503e"), clothS=H("4a4032"), trim=H("b4985e"),
                       shadow=H("6a2a26"), vestM=H("b47c58"), vestL=H("c8966e")),
    # white tabard over a brown travelling robe, grey hat
    "Pilgrim": dict(clothL=H("9c6a48"), clothM=H("82583c"), clothS=H("684632"), trim=H("3e302a"),
                    shadow=H("3e2a28"), vestM=H("cec8b6"), vestL=H("e8e2d2"), hair=H("5c5e6e")),
    # wine-red coat, black waistcoat, black tricorn, brass belt and buckles
    "Gambler": dict(clothL=H("a03040"), clothM=H("862636"), clothS=H("6a1e2c"), trim=H("a8843a"),
                    shadow=H("3a1820"), vestM=H("2e282c"), vestL=H("4a4044"), hair=H("2a2226")),
    # --- v0.7 origins
    # dark leather breeches, tawny wolf pelt, ginger mane
    "Reaver": dict(clothL=H("7a5a40"), clothM=H("664a34"), clothS=H("52382a"), trim=H("33261e"),
                   shadow=H("30221c"), vestM=H("9a8c74"), vestL=H("bcae94"), hair=H("c8602a")),
    # charcoal hood and breeches, dark teal jerkin
    "Cutpurse": dict(clothL=H("66605c"), clothM=H("524c4a"), clothS=H("3e3a3a"), trim=H("262222"),
                     shadow=H("242228"), vestM=H("346660"), vestL=H("4e867e"), hair=H("4a4544")),
    # ochre livery breeches, oxblood padded jack, steel kettle hat
    "Arbalist": dict(clothL=H("c49a44"), clothM=H("a47e36"), clothS=H("82602a"), trim=H("4a3424"),
                     shadow=H("4a3422"), vestM=H("8a2e2a"), vestL=H("a6443a"), hair=H("8c8e9a")),
    # midnight-blue robe, gold-trimmed stole, white hair
    "Scholar": dict(clothL=H("46609e"), clothM=H("38508a"), clothS=H("2c3e6e"), trim=H("c0983e"),
                    shadow=H("1e2440"), vestM=H("b08c40"), vestL=H("d0ac58"), hair=H("d2cec4")),
}
# ------------------------------------------------------------------ player-slot colour sets
# Every origin has four colour sets, one per player slot, so P1-P4 heroes with the same origin can be told apart.
# The design stays the same: only the origin's "team" parts (its main cloth, hood, robe, jerkin...) change colour,
# into the family of the player's own colour (the vanilla PlayerSetup colours: P1 blue, P2 red, P3 green, P4 amber).
# Steel, skin, leather, pelts, white tabards and gold trim never change. The slot whose family already holds the
# origin's canonical colour keeps it exactly (that set is the original art).
SLOT_HUE = [214, 356, 112, 40]          # degrees: P1 blue, P2 red, P3 green, P4 amber
SLOT_NAMES = ["P1", "P2", "P3", "P4"]
SAT_MIN = 0.30                          # rotated team colours are at least this saturated (readable on dark floors)
SAT_MAX = [0.56, 0.68, 0.44, 0.72]      # ... and at most this (a saturated rust turned green would glow neon)
SLOT_L = [1.0, 1.0, 0.92, 1.24]         # greens read brighter, dark ambers turn mud-brown
# origin -> [(team roles, canonical slot)]: the roles that take the player's colour family
TEAM = {
    "Sellsword":  [(["clothL", "clothM", "clothS", "shadow"], 1)],
    "Huntress":   [(["clothL", "clothM", "clothS", "shadow", "hair"], 2)],
    "Hexblade":   [(["clothL", "clothM", "clothS", "trim", "shadow", "vestM", "vestL", "hair"], 0)],
    "Flagellant": [(["clothL", "clothM", "clothS", "trim"], 3)],
    "Pilgrim":    [(["clothL", "clothM", "clothS"], 3)],
    "Gambler":    [(["clothL", "clothM", "clothS", "shadow"], 1)],
    "Reaver":     [(["clothL", "clothM", "clothS", "shadow", "vestM", "vestL"], 3)],   # breeches + wolf-pelt mantle
    "Cutpurse":   [(["vestM", "vestL"], 0), (["clothL", "clothM"], -1)],   # jerkin; sleeves + breeches always tinted
    "Arbalist":   [(["vestM", "vestL"], 1)],
    "Scholar":    [(["clothL", "clothM", "clothS", "shadow"], 0)],
}


def slot_col(c, slot, canon, sat_min=SAT_MIN):
    """A team colour in player slot `slot` (0-3): the canonical colour in its own slot, otherwise the same lightness
    turned to the slot's hue (saturation at least sat_min)."""
    import colorsys
    if slot == canon: return tuple(c)
    h, l, s = colorsys.rgb_to_hls(*[v / 255.0 for v in c[:3]])
    s = min(max(s, sat_min), SAT_MAX[slot])
    r, g, b = colorsys.hls_to_rgb(SLOT_HUE[slot] / 360.0, l * SLOT_L[slot], s)
    return tuple(max(0, min(255, int(round(v * 255)))) for v in (r, g, b))


def look_for(oid, slot):
    """The origin's role -> colour scheme for player slot 0-3."""
    look = dict(LOOKS[oid])
    for roles, canon in TEAM.get(oid, []):
        for r in roles:
            if r in look: look[r] = slot_col(look[r], slot, canon)
    return look


ORDER = ["Wanderer", "Sellsword", "Huntress", "Hexblade", "Flagellant", "Pilgrim", "Gambler",
         "Reaver", "Cutpurse", "Arbalist", "Scholar"]
# preview animations per origin (its weapon; the rest use the god's starting sword)
ANIMS = {
    None: ("RustySwordIdle", "RustySwordRun", "DaggerCombo1"),
    "Huntress": ("BowIdle", "BowRun", "BowCombo1"),
    "Hexblade": ("StaffIdleVariantMagic", "StaffRunVariantMagic", "StaffCombo1"),
    "Flagellant": ("ClubIdle", "ClubRun", "ClubCombo1"),
    "Gambler": ("SlingIdle", "SlingRun", "SlingCombo2"),
    "Reaver": ("AxeIdle", "AxeRun", "AxeAttack"),
    "Cutpurse": ("DaggerIdle", "DaggerRun", "DaggerCombo2"),
    "Arbalist": ("CrossbowIdle", "CrossbowRun", "CrossbowCombo1"),
}


def lum(c):
    return 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]


def swaps_for(look, cols):
    """[(from, to)] per slot. The source colour is that slot's most common hero colour; the target keeps the
    vanilla per-slot shading by scaling the role colour with the source's brightness relative to the role."""
    out = []
    for role, target in look.items():
        slots = ROLES[role]
        base = lum(cols[slots[0]].most_common(1)[0][0])
        for s in slots:
            src = cols[s].most_common(1)[0][0]
            k = max(0.88, min(1.12, lum(src) / base))
            out.append((src, tuple(max(0, min(255, int(round(v * k)))) for v in target)))
    return out


def plan(swaps, base_ramp, used):
    """What HeroLooks.cs writes: {slot: colour}. Exact slots first, then safe neighbour fills."""
    exact = {}
    for f, t in swaps:
        exact[slot(f)] = t
    out = dict(exact)
    for f, t in swaps:
        x, y = slot(f)
        for dx, dy in ((-1, 0), (1, 0), (-1, 1), (1, 1), (-1, -1), (1, -1), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if not (0 <= n[0] < 256 and 0 <= n[1] < 64): continue
            if n in out or n in used or base_ramp[n] != PINK: continue
            out[n] = t
    return out


def simulate(frame, ramp):
    im = frame.copy(); px = im.load()
    for yy in range(im.height):
        for xx in range(im.width):
            p = px[xx, yy]
            if p[3] == 0: continue
            t = ramp[slot(p)]
            if t != PINK: px[xx, yy] = t + (p[3],)
    return im


# ------------------------------------------------------------------ C# tables
def hexc(c):
    return "0x%02X%02X%02X" % c


def _replace_generated(path, lines):
    src = open(path).read()
    a = src.index("        // <generated")
    b = src.index("        // </generated>") + len("        // </generated>")
    open(path, "w").write(src[:a] + "\n".join(lines) + src[b:])


def write_cs(cols, used):
    head = "        // <generated by tools/sprites/hero_looks.py: do not edit by hand>"
    lines = [head]
    lines.append("        // per origin id + \"#\" + player slot 0-3: (from, to) RGB pairs; from = a hero-atlas colour, its ramp slot gets 'to'")
    lines.append("        static readonly Dictionary<string, int[]> s_raw = new Dictionary<string, int[]>")
    lines.append("        {")
    for oid in ORDER:
        for sl in range(4):
            sw = swaps_for(look_for(oid, sl), cols)
            if not sw: continue
            body = ", ".join("%s, %s" % (hexc(f), hexc(t)) for f, t in sw)
            lines.append('            { "%s#%d", new[] { %s } },' % (oid, sl, body))
    lines.append("        };")
    lines.append("        // </generated>")
    _replace_generated(CS_ORIGINS, lines)
    idx = sorted(x + 256 * y for (x, y) in used)
    lines = [head]
    lines.append("        // every ramp slot used by a hero-atlas colour (x + 256*y): neighbour fills never land here")
    lines.append("        static readonly ushort[] s_heroSlots = {")
    for i in range(0, len(idx), 16):
        lines.append("            " + ", ".join(str(v) for v in idx[i:i + 16]) + ",")
    lines.append("        };")
    lines.append("        // </generated>")
    _replace_generated(CS, lines)


# ------------------------------------------------------------------ checks
def report(cols, used):
    """Collision check. For every slot a role writes: every hero colour that lands in it and the clips it is
    drawn in (a weapon/effect colour sharing a role slot would be recoloured too). Then the neighbour fills."""
    clips = Clips()
    inclip = defaultdict(set)
    for name in clips.clips:
        for f in clips.get(name):
            for p in set(f.getdata()):
                if p[3] > 0: inclip[p[:3]].add(name)
    print("slot        role    colour (atlas px, #clips, sample clips)")
    for r, ss in ROLES.items():
        for s in ss:
            for c, n in cols[s].most_common():
                cl = sorted(inclip[c])
                print("  %-10s %-7s %s px=%d clips=%d %s" % (s, r, c, n, len(cl), cl[:4] if len(cl) < 12 else ""))
    base = load_ramp(RAMPS["P1"])
    for oid in ORDER:
        sw = swaps_for(LOOKS[oid], cols)
        p = plan(sw, base, used)
        print("%-10s exact=%d neighbour fills=%d" % (oid, len(set(slot(f) for f, _ in sw)), len(p) - len(set(slot(f) for f, _ in sw))))


def portrait(oid):
    p = os.path.join(ROOT, "art", "out_heroes", "Hero%s.png" % oid)
    if not os.path.exists(p): return None
    m = json.load(open(p[:-4] + ".json"))
    img = Image.open(p).convert("RGBA")
    return img.crop((0, 0, m["cellW"], m["cellH"]))


def preview(cols, used, out_path, scale=4, player="P1"):
    clips = Clips()
    base = load_ramp(RAMPS[player])
    rows = []
    for oid in ORDER:
        ramp = dict(base)
        ramp.update(plan(swaps_for(look_for(oid, SLOT_NAMES.index(player)), cols), base, used))
        idle, run, atk = ANIMS.get(oid, ANIMS[None])
        fr = clips.get(idle)[:1] + clips.get(run)[0:6:2] + clips.get(atk)[1:4]
        rows.append((oid, portrait(oid), [simulate(f, ramp) for f in fr]))
    # layout: fixed cell per frame (trimmed union box per row)
    pad = 3
    cellw = max(max(f.getbbox()[2] - f.getbbox()[0] for f in r[2] if f.getbbox()) for r in rows) + 2
    cellh = max(max(f.getbbox()[3] - f.getbbox()[1] for f in r[2] if f.getbbox()) for r in rows) + 2
    cellh = max(cellh, 24)
    ncol = max(len(r[2]) for r in rows)
    W = pad + 29 + pad * 2 + ncol * (cellw + pad) + 70
    Hh = pad + len(rows) * (cellh + pad)
    img = Image.new("RGBA", (W, Hh), (34, 32, 40, 255))
    d = ImageDraw.Draw(img)
    y = pad
    for oid, por, frs in rows:
        if por: img.alpha_composite(por, (pad, y + (cellh - 24) // 2))
        x = pad + 29 + pad * 2
        for f in frs:
            bb = f.getbbox()
            if bb:
                t = f.crop(bb)
                img.alpha_composite(t, (x + (cellw - t.width) // 2, y + cellh - 1 - t.height))
            x += cellw + pad
        y += cellh + pad
    img = img.resize((W * scale, Hh * scale), Image.NEAREST)
    d = ImageDraw.Draw(img)
    for i, (oid, _, _) in enumerate(rows):
        d.text(((W - 68) * scale, (pad + i * (cellh + pad) + cellh // 2) * scale - 6), oid, fill=(230, 226, 214))
    img.convert("RGB").save(out_path)
    print("preview ->", out_path)


def main():
    cols = atlas_colours()
    used = set(cols)
    for oid in ORDER:
        for f, t in swaps_for(LOOKS[oid], cols):
            assert slot(f) in used
    write_cs(cols, used)
    print("tables ->", CS, "(%d hero slots)" % len(used))
    if "--report" in sys.argv:
        report(cols, used)
    out = [a for a in sys.argv[1:] if a.endswith(".png")]
    if out:
        for p in SLOT_NAMES:
            preview(cols, used, out[0][:-4] + "_" + p + ".png", player=p)


if __name__ == "__main__":
    main()
