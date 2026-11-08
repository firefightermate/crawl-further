"""Custom silver / gold hero: every appearance part, drawn as layers the game composites and recolours.

Run from the repo root:  python3 tools/sprites/hero_custom.py [--boards DIR]

Writes
    art/out_heroes/HcPortrait.png/.json        portrait layers (29x24, 4 Idle frames each; one anim per layer)
    art/out_heroes/HcIcons.png/.json           20x20 editor icon per appearance option (one anim each)
    art/out_heroes/HeroCustomSilver/Gold.*     the silver / gold slot portraits (a hooded stranger in a tier frame)
    art/out_herogear/HcHead_<id>.*, HcFace_<id>.*  in-game head / face pieces (16 pose cells of 15x15, like hero_gear)
    src/CrawlFurther/Heroes/HeroCustomData.cs               option lists, colour shades, marker colours, in-game role sources
and with --boards: hc_parts.png (every option of every part on a mannequin), hc_combos.png (sample heroes in all
four slots, portrait + in-game frames) and hc_icons.png.

Marker colours: layers and gear are drawn with reserved colours (254, group, k). The game swaps each for the
player's choice: group 1 = main colour (4 shades L M S D), 2 = trim colour, 3 = skin (L l j J lips blush),
4 = hair (H d D), 5 = player slot colour (L M S D), 6 = background (frame edge mid centre, in the slot hue),
7 = tier frame (silver or gold: dark mid light glint). Everything else is drawn as is.
The player-slot colour is always on the in-game belt and boots (the "trim" ramp role), the portrait collar hem and
the portrait background, so two players with the same custom look are still told apart (and "Player colour",
the default main colour, makes the whole outfit follow the slot).
"""
import os, sys, json, colorsys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srcfiles import src_file, pack_files  # noqa: E402
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
os.chdir(os.path.dirname(os.path.dirname(HERE)))

from PIL import Image, ImageDraw
import anim
from anim import Spr
import hero_portraits as HP
import hero_looks as HL
import hero_gear as HG

ROOT = os.getcwd()
OUT_P = os.path.join(ROOT, "art", "out_heroes")
OUT_G = os.path.join(ROOT, "art", "out_herogear")
CS = src_file("HeroCustomData.cs")
W, H = HP.W, HP.H
DURS = HP.DURS

# ------------------------------------------------------------------------------------------------ markers
MK = {}   # char -> (254, group, k)
def _mk(chars, group):
    for i, c in enumerate(chars):
        MK[c] = (254, group, i + 1)
_mk("αβγδ", 1)          # main  L M S D       (alpha beta gamma delta)
_mk("εζηθ", 2)          # trim  L M S D       (epsilon zeta eta theta)
_mk("ικλμνξ", 3)   # skin  L l j J lips blush
_mk("οπρ", 4)                 # hair  H d D
_mk("στυφ", 5)          # slot  L M S D
_mk("χψωϊ", 6)          # bg    frame edge mid centre
_mk("ϋόύώ", 7)          # tier  dark mid light glint
A1, A2, A3, A4 = "αβγδ"
T1, T2, T3, T4 = "εζηθ"
SK = dict(zip("Llj J M *".replace(" ", ""), "ικλμνξ"))
SK = {"L": "ι", "l": "κ", "j": "λ", "J": "μ", "M": "ν", "*": "ξ"}
HR = {"H": "ο", "d": "π", "D": "ρ"}
S1, S2, S3, S4 = "στυφ"
BGM = dict(zip("09@$", "χψωϊ"))
TI = "ϋόύώ"
MAIN = (A1, A2, A3, A4)
TRIM = (T1, T2, T3, T4)
anim.PALETTE.update(MK)


def rgb(h, l, s):
    return tuple(max(0, min(255, int(round(v * 255)))) for v in colorsys.hls_to_rgb(h % 1.0, max(0, min(1, l)), max(0, min(1, s))))


def hls(c):
    return colorsys.rgb_to_hls(*[v / 255.0 for v in c[:3]])


def H6(s):
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def shades(base):
    """L M S D shades of a cloth colour (M = base), light from the upper left."""
    h, l, s = hls(base)
    return [rgb(h, l + 0.11, s * 0.95), base, rgb(h, l - 0.09, s * 1.0), rgb(h, max(0.07, l - 0.19), s * 0.9)]


# ------------------------------------------------------------------------------------------------ options
# colours shared by the MAIN and TRIM parts: id, display name, base (mid) colour. "Player" = the slot colour.
COLOURS = [
    ("Player", "PLAYER COLOUR", None),
    ("Crimson", "CRIMSON", H6("a8282e")), ("Rust", "RUST", H6("b4502a")), ("Ochre", "OCHRE", H6("b8902e")),
    ("Gold", "GOLD", H6("d0a63a")), ("Moss", "MOSS", H6("6a7a34")), ("Forest", "FOREST", H6("2e6a3a")),
    ("Teal", "TEAL", H6("2a7a72")), ("Sky", "SKY", H6("4c8cc4")), ("Midnight", "MIDNIGHT", H6("2c3a72")),
    ("Plum", "PLUM", H6("6e3070")), ("Rose", "ROSE", H6("c0607a")), ("Umber", "UMBER", H6("80523a")),
    ("Ash", "ASH", H6("8a8a90")), ("Coal", "COAL", H6("3a363c")), ("Bone", "BONE", H6("d2c8ae")),
    ("Silver", "SILVER", H6("b4b8c4")),
]
# player slot base colours (vanilla PlayerSetup colour families, lit for cloth)
SLOT_BASE = [H6("3a64b0"), H6("b0302c"), H6("4a8c3c"), H6("cc9634")]
SKINS = [  # id, name, base (the portrait 'l' tone)
    ("Tan", "TAN", H6("c79c6e")), ("Pale", "PALE", H6("e2c4a8")), ("Fair", "FAIR", H6("d8ae8c")),
    ("Olive", "OLIVE", H6("b0925e")), ("Bronze", "BRONZE", H6("a87048")), ("Brown", "BROWN", H6("8a5838")),
    ("Deep", "DEEP", H6("5e3a28")), ("Ashen", "ASHEN", H6("a4a8a0")),
]
HAIRS = [  # id, name, base (the portrait 'H' tone)
    ("Brown", "BROWN", H6("8e6e3e")), ("Black", "BLACK", H6("3a3234")), ("Blond", "BLOND", H6("d8b864")),
    ("Auburn", "AUBURN", H6("8e3e26")), ("Ginger", "GINGER", H6("d87a3a")), ("White", "WHITE", H6("e4e0d8")),
    ("Grey", "GREY", H6("8c8a88")), ("Raven", "RAVEN", H6("2c3450")),
]
OUTFITS = [
    ("Tunic", "TUNIC", "Main colour clothes, a trim colour vest"),
    ("Robe", "ROBE", "One long robe in the main colour"),
    ("Jerkin", "JERKIN", "Leather sleeves, a main colour jerkin"),
    ("Tabard", "TABARD", "Mail sleeves under a main colour tabard"),
    ("Leathers", "LEATHERS", "Leather armour over a trim colour shirt"),
    ("Cloak", "CLOAK", "A main colour cloak over dark clothes"),
    ("Mail", "MAIL", "A mail shirt with main colour sleeves"),
]
HEADS = [
    ("Bare", "SHORT HAIR"), ("Long", "LONG HAIR"), ("Topknot", "TOPKNOT"), ("Mohawk", "MOHAWK"),
    ("Shaved", "SHAVED"), ("Hood", "HOOD"), ("Helm", "IRON HELM"), ("Horned", "HORNED HELM"),
    ("WideHat", "WIDE HAT"), ("Cap", "FEATHER CAP"), ("Wizard", "POINTED HAT"), ("Bandana", "BANDANA"),
    ("Circlet", "CIRCLET"),
]
FACES = [
    ("Plain", "PLAIN"), ("Soft", "SOFT"), ("Beard", "BEARD"), ("Moustache", "MOUSTACHE"), ("Scar", "SCARRED"),
    ("Eyepatch", "EYEPATCH"), ("Paint", "WAR PAINT"), ("Specs", "SPECTACLES"), ("Mask", "MASKED"),
]
# weapon families drawn on the portrait (vanilla prefab prefix -> family); mod weapons use their base weapon
FAMILIES = ["Sword", "Greatsword", "Axe", "Club", "Dagger", "Spear", "Staff", "Bow", "Crossbow", "Sling", "Knives"]
TIER_COLS = {"Silver": [H6("4a4c58"), H6("9ea2b2"), H6("dfe3ee"), H6("ffffff")],
             "Gold": [H6("5e4618"), H6("a8843a"), H6("d8bc6e"), H6("fff4d8")]}


def _muted(c, cap=0.30, s_cap=0.66):
    """Crawl's palette: option colours sit in the muted range of the game's own art (weapon_bubbles.tame)."""
    import weapon_bubbles
    return weapon_bubbles.tame(c, cap, s_cap)


COLOURS = [(i, n, None if b is None else _muted(b)) for i, n, b in COLOURS]
HAIRS = [(i, n, _muted(b, 0.34)) for i, n, b in HAIRS]
SLOT_BASE = [_muted(c, 0.38, 0.72) for c in SLOT_BASE]

# fixed materials
LEATHER = [H6("8a603e"), H6("6e4a30"), H6("543826"), H6("3a281e")]
STEEL = [H6("b0b2bc"), H6("7c7e8a"), H6("5c5e68"), H6("3c3c46")]
DARK = [H6("4a4248"), H6("3a3438"), H6("2c282c"), H6("201c20")]

# in-game body roles per outfit: role -> (source, shade index). source: main / trim / leather / steel / dark
L_, M_, S_, D_ = 0, 1, 2, 3
OUTFIT_ROLES = {
    "Tunic":    dict(clothL=("main", L_), clothM=("main", M_), clothS=("main", S_), shadow=("main", D_),
                     vestM=("trim", M_), vestL=("trim", L_)),
    "Robe":     dict(clothL=("main", L_), clothM=("main", M_), clothS=("main", S_), shadow=("main", D_),
                     vestM=("main", M_), vestL=("main", L_)),
    "Jerkin":   dict(clothL=("leather", L_), clothM=("leather", M_), clothS=("leather", S_), shadow=("leather", D_),
                     vestM=("main", M_), vestL=("main", L_)),
    "Tabard":   dict(clothL=("steel", L_), clothM=("steel", M_), clothS=("steel", S_), shadow=("steel", D_),
                     vestM=("main", M_), vestL=("main", L_)),
    "Leathers": dict(clothL=("leather", L_), clothM=("leather", M_), clothS=("leather", S_), shadow=("leather", D_),
                     vestM=("trim", M_), vestL=("trim", L_)),
    "Cloak":    dict(clothL=("dark", L_), clothM=("dark", M_), clothS=("main", S_), shadow=("main", D_),
                     vestM=("main", M_), vestL=("main", L_)),
    "Mail":     dict(clothL=("main", L_), clothM=("main", M_), clothS=("main", S_), shadow=("main", D_),
                     vestM=("steel", M_), vestL=("steel", L_)),
}
# in-game skin: the two hero skin colours that are only ever skin (face + hands); their portrait-tone equivalents
GAME_SKIN = [((199, 156, 110), 1), ((182, 116, 80), 2)]     # (atlas colour, portrait shade index l / j)
GAME_HAIR = (115, 91, 56)


# ------------------------------------------------------------------------------------------------ shade tables
VAN_SKIN = [H6("dab284"), H6("c79c6e"), H6("a2724c"), H6("6a4430"), H6("9e5646"), H6("e2a890")]   # L l j J M *
VAN_HAIR = [H6("8e6e3e"), H6("735b38"), H6("483624")]


def tone_shades(van, base, ref):
    """Shades of `van` (reference tone ref) re-toned to `base`: hue and saturation of base, lightness scaled."""
    hb, lb, sb = hls(base); hr, lr, sr = hls(ref)
    out = []
    for c in van:
        h, l, s = hls(c)
        dh = h - hr
        out.append(rgb(hb + dh * 0.5, l * (lb / lr) if lb < lr else l + (lb - lr) * (1 - l) / max(0.01, 1 - lr),
                       s * (sb / max(0.01, sr))))
    return out


def skin_shades(base):
    return tone_shades(VAN_SKIN, base, VAN_SKIN[1])


def hair_shades(base):
    return tone_shades(VAN_HAIR, base, VAN_HAIR[0])


def colour_shades(cid, slot):
    for i, n, b in COLOURS:
        if i == cid: return shades(SLOT_BASE[slot] if b is None else b)
    raise KeyError(cid)


def bg_tones(slot):
    """frame, edge, fill, fill: the origin portraits' backdrop in the slot hue."""
    import origin_portraits as OP
    base = [H6(c) for c in OP.BG["Wanderer"]]
    base = base + [base[-1]]
    return [rgb(HL.SLOT_HUE[slot] / 360.0, hls(c)[1], 0.22) for c in base]


# ------------------------------------------------------------------------------------------------ canvas helpers
class Cv(HP.Canvas):
    def tr(self, m):
        for k, c in list(self.px.items()):
            if c in m: self.px[k] = m[c]
        return self


def layer(fn, frames=4):
    return [fn(f) for f in range(frames)]


BREATH = [0, 0, 1, 0]


# ------------------------------------------------------------------------------------------------ portrait layers
def L_tier(f):
    """The silver / gold frame: the 1px border in the tier colours, a bright glint running round it, and corner studs.
    Same layer for both tiers (the tier colours are the markers)."""
    cv = Cv()
    ring = [(x, 0) for x in range(W)] + [(W - 1, y) for y in range(1, H)] + [(x, H - 1) for x in range(W - 2, -1, -1)] \
        + [(0, y) for y in range(H - 2, 0, -1)]
    n = len(ring)
    head = (f * n) // 4 + 6
    for i, (x, y) in enumerate(ring):
        d = (head - i) % n
        cv.put(x, y, TI[3] if d == 0 else TI[2] if d in (1, 2) else TI[0] if i % 3 == 0 else TI[1])
    for (x, y) in [(0, 0), (W - 1, 0), (0, H - 1), (W - 1, H - 1)]:
        cv.put(x, y, TI[2])
    # inner corner ticks
    for (x, y) in [(1, 1), (W - 2, 1), (1, H - 2), (W - 2, H - 2)]:
        cv.put(x, y, TI[1])
    return cv.spr()


def L_tierplate(f):
    """Gold only: a small crest at the top centre that sparkles."""
    cv = Cv()
    cv.stamp(["." + TI[0] * 3 + ".", TI[0] + TI[2] + TI[1] + TI[2] + TI[0], "." + TI[0] + TI[1] + TI[0] + "."], 12, 0)
    sp = [(14, 1), (13, 0), (15, 0), (14, 1)][f]
    cv.put(sp[0], sp[1], TI[3])
    return cv.spr()


# ------------------------------------------------------------------------------------------------ portrait sheet
def portrait_layers():
    """[(anim name, [4 Spr])] in sheet order. The layers are painted by hero_bust_layers (the origin portraits'
    close-up style); the tier frame and crest stay as drawn here."""
    import hero_bust_layers as BL
    out = [("Bg", BL.bg_layer()), ("Tier", layer(L_tier)), ("TierCrest", layer(L_tierplate)),
           ("Glint", [BL.L_glint(f) for f in range(4)]), ("Spell", [BL.L_spell(f) for f in range(4)]),
           ("Unknown", [BL.L_unknown(f) for f in range(4)])]
    for oid, _, _ in OUTFITS:
        out.append(("Outfit_" + oid, BL.layer(BL.outfit_fn(oid))))
        out.append(("OutfitF_" + oid, BL.layer(BL.outfit_fn(oid, female=True))))
    for fid, _ in FACES:
        out.append(("Face_" + fid, BL.layer(BL.face_fn(fid))))
        out.append(("FacePiece_" + fid, BL.layer(BL.facepiece_fn(fid))))
    for hid, _ in HEADS:
        out.append(("Head_" + hid, BL.layer(BL.head_fn(hid))))
    for fam in FAMILIES:
        out.append(("Weapon_" + fam, BL.layer(BL.weapon_fn(fam))))
    return out


# portrait draw order (C# composes in this order; the weapon goes behind the body)
# (no "Gem": the violet mod gem is Core's, drawn over the portrait at run time, never baked in)
ORDER = ["Bg", "Weapon", "Outfit", "Face", "FacePiece", "Head", "Glint", "Spell", "Tier", "TierCrest"]


# ------------------------------------------------------------------------------------------------ colour resolution
def palette_for(choice, slot, tier="Silver"):
    """marker rgb -> colour for a choice dict (part -> option id)."""
    m = {}
    for i, c in enumerate(colour_shades(choice["Colour"], slot)): m[(254, 1, i + 1)] = c
    for i, c in enumerate(colour_shades(choice["Trim"], slot)): m[(254, 2, i + 1)] = c
    sk = dict((i, b) for i, n, b in SKINS)[choice["Skin"]]
    for i, c in enumerate(skin_shades(sk)): m[(254, 3, i + 1)] = c
    hr = dict((i, b) for i, n, b in HAIRS)[choice["Hair"]]
    for i, c in enumerate(hair_shades(hr)): m[(254, 4, i + 1)] = c
    for i, c in enumerate(shades(SLOT_BASE[slot])): m[(254, 5, i + 1)] = c
    for i, c in enumerate(bg_tones(slot)): m[(254, 6, i + 1)] = c
    for i, c in enumerate(TIER_COLS[tier]): m[(254, 7, i + 1)] = c
    return m


def compose(sheet, choice, slot, tier, weapon=None, magic=False, spell=False, frame=True):
    """The 4 portrait frames exactly as HeroCustom.cs composes them (used for the boards)."""
    img, man = sheet
    anims = {a["name"]: a["frames"] for a in man["anims"]}
    pal = palette_for(choice, slot, tier)
    female = choice["Face"] == "Soft"
    names = []
    for part in ORDER:
        if part == "Bg": names.append("Bg")
        elif part == "Weapon":
            if weapon: names.append("Weapon_" + weapon)
        elif part == "Outfit": names.append(("OutfitF_" if female else "Outfit_") + choice["Outfit"])
        elif part == "Face": names.append("Face_" + choice["Face"])
        elif part == "FacePiece": names.append("FacePiece_" + choice["Face"])
        elif part == "Head": names.append("Head_" + choice["Head"])
        elif part == "Glint":
            if magic and weapon: names.append("Glint")
        elif part == "Spell":
            if spell: names.append("Spell")
        elif part == "TierCrest":
            if tier == "Gold" and frame: names.append("TierCrest")
        elif part == "Tier":
            if frame: names.append(part)
        else: names.append(part)
    frames = []
    cols = man["cols"]
    for k in range(4):
        out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        px = out.load()
        for n in names:
            fi = anims[n][k]
            x0, y0 = (fi % cols) * W, (fi // cols) * H
            cell = img.crop((x0, y0, x0 + W, y0 + H)).load()
            for y in range(H):
                for x in range(W):
                    p = cell[x, y]
                    if p[3] == 0: continue
                    c = pal.get(p[:3], p[:3])
                    px[x, y] = c + (255,)
        frames.append(out)
    return frames


# ------------------------------------------------------------------------------------------------ in-game gear
# canonical 15x15 cell, head reference R at (7,7); hair crown (8..10, 6); face x 8..9 rows 7..10, eye (9, 8).
# The vanilla head is 3-4 px across, so every piece stays at that scale, edged in its own darkest tone (no black ring).
# chars: H d D hair, a b c q main (L M S D), e f g h trim, S s skin, m n o slot, plus fixed colours
GEAR_HEAD = {
    "Long": dict(y0=6, rows=[
        ".......HHHd....",
        "......Hd.......",
        "......dD.......",
        "......dD.......",
        ".....dD........",
        ".....DD........",
        "......D........",
    ]),
    "Topknot": dict(y0=3, rows=[
        "........HD.....",
        "........dD.....",
        "........f......",
        ".......HHd.....",
    ]),
    "Mohawk": dict(y0=4, rows=[
        "........H.H....",
        ".......HdHd....",
        "........ddD....",
    ]),
    "Shaved": dict(y0=6, rows=[
        "........Sss....",
        ".......s.......",
    ]),
    "Hood": dict(y0=5, rows=[
        ".......qqq.....",
        "......qabbq....",
        ".....qab..bq...",
        ".....qbc.......",
        "....qbcq.......",
        "....qcc........",
        "...qcq.........",
    ]),
    "Helm": dict(y0=4, rows=[
        "........fe.....",
        ".......KK......",
        "......K432K....",
        "......K3221K...",
        "......K1111K...",
        "......M...2....",
        "......N........",
    ]),
    "Horned": dict(y0=3, rows=[
        ".....W.....W...",
        ".....XW...WX...",
        "......XKK.X....",
        "......K432K....",
        "......K3221K...",
        "......K1111K...",
    ]),
    "WideHat": dict(y0=3, rows=[
        ".......qqq.....",
        "......qabbq....",
        "......qmnoq....",
        "....qabbbbcq...",
        ".....qq...qq...",
    ]),
    "Cap": dict(y0=4, rows=[
        "...........e...",
        "......qabbcf...",
        ".....qabbbcq...",
        ".....qqqqqq....",
    ]),
    "Wizard": dict(y0=2, rows=[
        ".......q.......",
        "......qaq......",
        "......abcq.....",
        ".....qabYcq....",
        ".....qffggq....",
        "....qabbbccq...",
    ]),
    "Bandana": dict(y0=5, rows=[
        ".......effg....",
        "......efffgh...",
        ".....hg........",
        "....h..........",
    ]),
    "Circlet": dict(y0=6, rows=[
        "........HHd....",
        "......YYfY.....",
    ]),
}
# face pieces: every pixel is a face piece (hidden when the face is turned away)
GEAR_FACE = {
    "Beard": dict(y0=9, rows=[
        ".........d.....",
        ".......dHd.....",
        ".......dD......",
    ]),
    "Moustache": dict(y0=9, rows=[
        "........dH.....",
    ]),
    "Scar": dict(y0=7, rows=[
        "........r......",
        "........!......",
        "........r......",
    ]),
    "Eyepatch": dict(y0=7, rows=[
        "......KKKK.....",
        ".........K.....",
    ]),
    "Paint": dict(y0=8, rows=[
        "........ff.....",
    ]),
    "Specs": dict(y0=8, rows=[
        "........eYe....",
    ]),
    "Mask": dict(y0=9, rows=[
        "........fg.....",
        ".......effg....",
    ]),
}
GEAR_MARK = {"H": (254, 4, 1), "d": (254, 4, 2), "D": (254, 4, 3),
             "a": (254, 1, 1), "b": (254, 1, 2), "c": (254, 1, 3), "q": (254, 1, 4),
             "e": (254, 2, 1), "f": (254, 2, 2), "g": (254, 2, 3), "h": (254, 2, 4),
             "S": (254, 3, 1), "s": (254, 3, 2),
             "m": (254, 5, 1), "n": (254, 5, 2), "o": (254, 5, 3)}
GEAR_FIXED = {"K": H6("2a2c36"), "4": H6("e2e4ec"), "3": H6("a8aab6"), "2": H6("767884"), "1": H6("4c4e5a"),
              "M": H6("8c8c98"), "N": H6("4a4a56"), "W": H6("e8e0c8"), "X": H6("a89c80"), "Y": H6("ffd85e"),
              "r": H6("a81e1a"), "!": H6("963430")}
GEAR_D_MAIN = {}


def gear_pixels_custom(piece, face_piece, ramps):
    g = (GEAR_FACE if face_piece else GEAR_HEAD)[piece]
    out = {}
    for i, row in enumerate(g["rows"]):
        assert len(row) == HG.CELL, (piece, i, row, len(row))
        for x, ch in enumerate(row):
            if ch == '.': continue
            if ch == 'd' and GEAR_D_MAIN.get(piece): col = (254, 1, 4)
            elif ch in GEAR_MARK: col = GEAR_MARK[ch]
            else: col = HG.ramp_safe(GEAR_FIXED[ch], ramps)
            out[(x - HG.C0, g["y0"] + i - HG.C0)] = (col + (255,), face_piece)
    return out


def write_gear(ramps):
    cells = {}
    for kind, table in (("HcHead_", GEAR_HEAD), ("HcFace_", GEAR_FACE)):
        for piece in table:
            pix = gear_pixels_custom(piece, kind == "HcFace_", ramps)
            imgs = [HG.gear_cell(pix, t) for t in range(HG.NPOSE)]
            sid = kind + piece
            import hero_slots
            hero_slots.write_gear_sheet(sid, imgs)
            cells[sid] = imgs
    return cells


# ------------------------------------------------------------------------------------------------ icons
IC = 20
DEFAULT = dict(Outfit="Tunic", Colour="Player", Trim="Umber", Skin="Tan", Hair="Brown", Head="Bare", Face="Plain")


def icon_swatch(base):
    """A folded tunic swatch in a colour's four shades."""
    L, M, S, D = shades(base)
    im = Image.new("RGBA", (IC, IC), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    k = (30, 26, 28, 255)
    body = [(4, 5), (8, 3), (11, 3), (15, 5), (17, 9), (14, 10), (14, 17), (5, 17), (5, 10), (2, 9)]
    d.polygon(body, fill=M + (255,), outline=k)
    d.line([(6, 6), (6, 15)], fill=L + (255,))
    d.line([(7, 5), (9, 5)], fill=L + (255,))
    d.line([(13, 7), (13, 15)], fill=S + (255,))
    d.line([(6, 16), (13, 16)], fill=D + (255,))
    d.line([(9, 4), (10, 6)], fill=k); d.line([(10, 6), (11, 4)], fill=k)
    return im


def icon_crop(frame, box):
    x0, y0 = box
    return frame.crop((x0, y0, x0 + IC, y0 + IC))


def build_icons(sheet):
    """One 20x20 icon per option: colours as swatches (Player colour per slot), the rest as close crops of a
    mannequin wearing that option (skin/hair on a plain head, outfits at the shoulders)."""
    icons = []   # (anim name, image)
    for cid, n, b in COLOURS:
        if b is None:
            for s in range(4): icons.append(("Colour_Player_P%d" % (s + 1), icon_swatch(SLOT_BASE[s])))
        else:
            icons.append(("Colour_" + cid, icon_swatch(b)))
    for sid, n, b in SKINS:
        ch = dict(DEFAULT, Skin=sid, Head="Shaved")
        fr = compose(sheet, ch, 0, "Silver", frame=False)[0]
        icons.append(("Skin_" + sid, transparent_bg(icon_crop(fr, (4, 1)), fr)))
    for hid, n, b in HAIRS:
        ch = dict(DEFAULT, Hair=hid, Head="Long")
        fr = compose(sheet, ch, 0, "Silver", frame=False)[0]
        icons.append(("Hair_" + hid, transparent_bg(icon_crop(fr, (4, 0)), fr)))
    for hid, n in HEADS:
        ch = dict(DEFAULT, Head=hid)
        fr = compose(sheet, ch, 0, "Silver", frame=False)[0]
        icons.append(("Head_" + hid, transparent_bg(icon_crop(fr, (4, 0)), fr)))
    for fid, n in FACES:
        ch = dict(DEFAULT, Face=fid)
        fr = compose(sheet, ch, 0, "Silver", frame=False)[0]
        icons.append(("Face_" + fid, transparent_bg(icon_crop(fr, (4, 2)), fr)))
    for oid, n, t in OUTFITS:
        ch = dict(DEFAULT, Outfit=oid, Colour="Crimson", Trim="Gold")
        fr = compose(sheet, ch, 0, "Silver", frame=False)[0]
        icons.append(("Outfit_" + oid, transparent_bg(icon_crop(fr, (4, 4)), fr)))
    return icons


def transparent_bg(icon, frame):
    """Drop the background vignette pixels (keeps the figure only, with a 1px dark outline)."""
    bgcols = set()
    for s in range(4):
        bgcols |= set(bg_tones(s))
    im = icon.copy(); px = im.load()
    allbg = set(bg_tones(0))
    for y in range(IC):
        for x in range(IC):
            if px[x, y][:3] in allbg: px[x, y] = (0, 0, 0, 0)
    # outline
    add = []
    for y in range(IC):
        for x in range(IC):
            if px[x, y][3]: continue
            if any(0 <= x + dx < IC and 0 <= y + dy < IC and px[x + dx, y + dy][3] and px[x + dx, y + dy][:3] != (30, 26, 28)
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                add.append((x, y))
    for (x, y) in add: px[x, y] = (30, 26, 28, 255)
    return im


def write_icons(icons):
    cols = 8
    n = len(icons)
    rows = (n + cols - 1) // cols
    pw = 1
    while pw < cols * IC: pw *= 2
    ph = 1
    while ph < rows * IC: ph *= 2
    img = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    man = {"cellW": IC, "cellH": IC, "cols": cols, "anims": []}
    for i, (name, im) in enumerate(icons):
        img.alpha_composite(im, ((i % cols) * IC, (i // cols) * IC))
        man["anims"].append({"name": name, "frames": [i], "durations": [1.0]})
    img.save(os.path.join(OUT_P, "HcIcons.png"))
    json.dump(man, open(os.path.join(OUT_P, "HcIcons.json"), "w"))
    anim.preview(img, man, os.path.join(OUT_P, "HcIcons_preview.png"), scale=4)
    return img, man


# ------------------------------------------------------------------------------------------------ slot portraits
def slot_portrait(sheet, tier):
    """HeroCustomSilver / HeroCustomGold: a hooded stranger in shadow, a glowing question mark, the tier frame."""
    img, man = sheet
    anims = {a["name"]: a["frames"] for a in man["anims"]}
    ch = dict(DEFAULT, Outfit="Cloak", Colour="Coal", Trim="Silver" if tier == "Silver" else "Gold", Head="Hood",
              Face="Plain", Skin="Deep", Hair="Black")
    pal = palette_for(ch, 0, tier)
    for i, c in enumerate(TIER_COLS[tier]): pal[(254, 5, i + 1)] = c     # collar hem in the tier colour, no slot
    # neutral background in the tier tone instead of a slot hue
    tone = TIER_COLS[tier]
    import origin_portraits as OP
    for i, c in enumerate([H6(c) for c in OP.BG["Wanderer"]] + [H6(OP.BG["Wanderer"][-1])]):
        h, l, s = hls(tone[1])
        pal[(254, 6, i + 1)] = rgb(h, hls(c)[1], 0.10 if tier == "Silver" else 0.22)
    names = ["Bg", "Outfit_Cloak", "Face_Plain", "Head_Hood", "Unknown", "Tier"] + (["TierCrest"] if tier == "Gold" else [])
    frames = []
    cols = man["cols"]
    for k in range(4):
        out = Image.new("RGBA", (W, H), (0, 0, 0, 0)); px = out.load()
        for n in names:
            fi = anims[n][k]
            x0, y0 = (fi % cols) * W, (fi // cols) * H
            cell = img.crop((x0, y0, x0 + W, y0 + H)).load()
            for y in range(H):
                for x in range(W):
                    p = cell[x, y]
                    if p[3] == 0: continue
                    c = pal.get(p[:3], p[:3])
                    if n == "Face_Plain" and p[:3][0] == 254 and p[:3][1] == 3:   # the face stays in deep shadow
                        c = tuple(int(v * 0.32) for v in c)
                    px[x, y] = c + (255,)
        frames.append(out)
    sid = "HeroCustom" + tier
    W2 = 4 * W
    pw = 1
    while pw < W2 * 1: pw *= 2
    ph = 32
    sh = Image.new("RGBA", (128, 32), (0, 0, 0, 0))
    for k, fr in enumerate(frames): sh.alpha_composite(fr, (k * W, 0))
    sh.save(os.path.join(OUT_P, sid + ".png"))
    m = {"cellW": W, "cellH": H, "cols": 4, "anims": [{"name": "Idle", "frames": [0, 1, 2, 3], "durations": DURS}]}
    json.dump(m, open(os.path.join(OUT_P, sid + ".json"), "w"))
    anim.preview(sh, m, os.path.join(OUT_P, sid + "_preview.png"))
    return frames


# ------------------------------------------------------------------------------------------------ in-game simulation
def game_swaps(choice, slot, cols):
    """(from, to) pairs exactly as HeroCustom.BodySwaps builds them: outfit roles, trim = slot, skin, hair."""
    look = {}
    srcs = {"main": colour_shades(choice["Colour"], slot), "trim": colour_shades(choice["Trim"], slot),
            "leather": LEATHER, "steel": STEEL, "dark": DARK}
    for role, (src, k) in OUTFIT_ROLES[choice["Outfit"]].items():
        look[role] = srcs[src][k]
    look["trim"] = shades(SLOT_BASE[slot])[2]
    look["shadow"] = shades(SLOT_BASE[slot])[3]
    look["hair"] = hair_shades(dict((i, b) for i, n, b in HAIRS)[choice["Hair"]])[0]
    sw = HL.swaps_for(look, cols)
    sk = skin_shades(dict((i, b) for i, n, b in SKINS)[choice["Skin"]])
    for src, k in GAME_SKIN:
        sw.append((src, sk[k]))
    return sw


def role_sources(cols):
    """role -> [(atlas colour, k)] (HeroLooks.swaps_for's per-slot shading factor)."""
    out = {}
    for role, slots in HL.ROLES.items():
        base = HL.lum(cols[slots[0]].most_common(1)[0][0])
        lst = []
        for s in slots:
            src = cols[s].most_common(1)[0][0]
            k = max(0.88, min(1.12, HL.lum(src) / base))
            lst.append((src, k))
        out[role] = lst
    return out


# ------------------------------------------------------------------------------------------------ C# data
def cs_rgb(c):
    return "0x%02X%02X%02X" % tuple(c[:3])


def write_cs(cols, ramps):
    rs = role_sources(cols)
    safe = lambda c: HG.ramp_safe(tuple(c), ramps)
    L = ["// <auto-generated> by tools/sprites/hero_custom.py: do not edit by hand (re-run the tool).",
         "using System.Collections.Generic;", "", "namespace CrawlFurther.Content.Heroes", "{",
         "    public static partial class HeroCustom", "    {"]
    def arr(name, items):
        L.append("        static readonly %s;" % name.replace("{}", "{ " + ", ".join(items) + " }"))
    # colours: id, name, 4 shades (Player = 4 slots x 4 shades)
    L.append("        // colours (MAIN and TRIM): id, display name, L M S D; the Player colour has 4 slots x 4 shades")
    L.append("        static readonly string[] s_colourIds = { %s };" % ", ".join('"%s"' % c[0] for c in COLOURS))
    L.append("        static readonly string[] s_colourNames = { %s };" % ", ".join('"%s"' % c[1] for c in COLOURS))
    sh = []
    for cid, n, b in COLOURS:
        if b is None:
            for s in range(4): sh.extend(safe(c) for c in shades(SLOT_BASE[s]))
        else:
            sh.extend(safe(c) for c in shades(b))
    L.append("        static readonly int[] s_colourShades = { %s };" % ", ".join(cs_rgb(c) for c in sh))
    L.append("        static readonly int[] s_slotShades = { %s };" % ", ".join(cs_rgb(safe(c)) for s in range(4) for c in shades(SLOT_BASE[s])))
    L.append("        static readonly int[] s_slotBg = { %s };" % ", ".join(cs_rgb(safe(c)) for s in range(4) for c in bg_tones(s)))
    L.append("        static readonly int[] s_tierShades = { %s };" % ", ".join(cs_rgb(safe(c)) for t in ("Silver", "Gold") for c in TIER_COLS[t]))
    # skins: portrait shades (6) + in-game targets (2)
    L.append("        static readonly string[] s_skinIds = { %s };" % ", ".join('"%s"' % c[0] for c in SKINS))
    L.append("        static readonly string[] s_skinNames = { %s };" % ", ".join('"%s"' % c[1] for c in SKINS))
    L.append("        static readonly int[] s_skinShades = { %s };" % ", ".join(cs_rgb(safe(c)) for _, _, b in SKINS for c in skin_shades(b)))
    L.append("        static readonly int[] s_gameSkinFrom = { %s };" % ", ".join(cs_rgb(s) for s, _ in GAME_SKIN))
    L.append("        static readonly int[] s_gameSkinShade = { %s };" % ", ".join(str(k) for _, k in GAME_SKIN))
    L.append("        static readonly string[] s_hairIds = { %s };" % ", ".join('"%s"' % c[0] for c in HAIRS))
    L.append("        static readonly string[] s_hairNames = { %s };" % ", ".join('"%s"' % c[1] for c in HAIRS))
    L.append("        static readonly int[] s_hairShades = { %s };" % ", ".join(cs_rgb(safe(c)) for _, _, b in HAIRS for c in hair_shades(b)))
    L.append("        const int GameHairFrom = %s;" % cs_rgb(GAME_HAIR))
    L.append("        static readonly string[] s_outfitIds = { %s };" % ", ".join('"%s"' % o[0] for o in OUTFITS))
    L.append("        static readonly string[] s_outfitNames = { %s };" % ", ".join('"%s"' % o[1] for o in OUTFITS))
    L.append("        static readonly string[] s_outfitText = { %s };" % ", ".join('"%s"' % o[2] for o in OUTFITS))
    L.append("        static readonly string[] s_headIds = { %s };" % ", ".join('"%s"' % o[0] for o in HEADS))
    L.append("        static readonly string[] s_headNames = { %s };" % ", ".join('"%s"' % o[1] for o in HEADS))
    L.append("        static readonly string[] s_faceIds = { %s };" % ", ".join('"%s"' % o[0] for o in FACES))
    L.append("        static readonly string[] s_faceNames = { %s };" % ", ".join('"%s"' % o[1] for o in FACES))
    L.append("        /// <summary>Head / face options that wear an in-game gear piece (sheet \"HcHead_\" / \"HcFace_\" + id).</summary>")
    L.append("        static readonly string[] s_headGear = { %s };" % ", ".join('"%s"' % k for k in GEAR_HEAD))
    L.append("        static readonly string[] s_faceGear = { %s };" % ", ".join('"%s"' % k for k in GEAR_FACE))
    L.append("        static readonly string[] s_families = { %s };" % ", ".join('"%s"' % f for f in FAMILIES))
    L.append("        static readonly string[] s_layerOrder = { %s };" % ", ".join('"%s"' % o for o in ORDER))
    # fixed materials and outfit role sources
    L.append("        static readonly int[] s_leather = { %s }, s_steel = { %s }, s_dark = { %s };" % (
        ", ".join(cs_rgb(c) for c in LEATHER), ", ".join(cs_rgb(c) for c in STEEL), ", ".join(cs_rgb(c) for c in DARK)))
    L.append("        /// <summary>Per outfit: \"role:source:shade\" (source m = main, t = trim, l = leather, s = steel, d = dark).</summary>")
    L.append("        static readonly string[] s_outfitRoles = {")
    code = {"main": "m", "trim": "t", "leather": "l", "steel": "s", "dark": "d"}
    for oid, _, _ in OUTFITS:
        L.append('            "%s",' % " ".join("%s:%s:%d" % (r, code[s], k) for r, (s, k) in OUTFIT_ROLES[oid].items()))
    L.append("        };")
    L.append("        /// <summary>Per body role: atlas colours and the shading factor HeroLooks.swaps_for gives each.</summary>")
    L.append("        static readonly Dictionary<string, int[]> s_roleSrc = new Dictionary<string, int[]>")
    L.append("        {")
    for role, lst in rs.items():
        L.append('            { "%s", new[] { %s } },' % (role, ", ".join("%s, %d" % (cs_rgb(s), int(round(k * 1000))) for s, k in lst)))
    L.append("        };")
    L.append("    }")
    L.append("}")
    L.append("")
    open(CS, "w").write("\n".join(L))
    print("data ->", CS)


# ------------------------------------------------------------------------------------------------ boards
def scale(im, s):
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


def board_parts(sheet, path):
    S = 4
    parts = [("Outfit", [o[0] for o in OUTFITS]), ("Colour", [c[0] for c in COLOURS]), ("Trim", [c[0] for c in COLOURS]),
             ("Skin", [s[0] for s in SKINS]), ("Hair", [h[0] for h in HAIRS]), ("Head", [h[0] for h in HEADS]),
             ("Face", [f[0] for f in FACES])]
    ncol = max(len(v) for _, v in parts)
    lab = 60
    img = Image.new("RGBA", (lab + ncol * (W + 2) * S, len(parts) * (H + 10) * S), (34, 32, 40, 255))
    d = ImageDraw.Draw(img)
    for r, (part, ids) in enumerate(parts):
        d.text((4, r * (H + 10) * S + H * S // 2), part, fill=(232, 228, 216))
        for c, oid in enumerate(ids):
            ch = dict(DEFAULT, **{part: oid})
            if part == "Trim": ch["Outfit"] = "Tabard"
            fr = compose(sheet, ch, 0, "Silver", weapon="Sword")[0]
            img.alpha_composite(scale(fr, S), (lab + c * (W + 2) * S, r * (H + 10) * S))
            d.text((lab + c * (W + 2) * S, (r * (H + 10) + H) * S + 2), oid[:10], fill=(200, 196, 186))
    img.convert("RGB").save(path)
    print("board ->", path)


SAMPLES = [
    (dict(Outfit="Tabard", Colour="Player", Trim="Gold", Skin="Brown", Hair="Black", Head="Helm", Face="Beard"), "Gold", "Sword", True, True),
    (dict(Outfit="Robe", Colour="Plum", Trim="Gold", Skin="Pale", Hair="White", Head="Wizard", Face="Specs"), "Gold", "Staff", True, True),
    (dict(Outfit="Leathers", Colour="Moss", Trim="Teal", Skin="Olive", Hair="Ginger", Head="Long", Face="Soft"), "Silver", "Bow", False, False),
    (dict(Outfit="Cloak", Colour="Coal", Trim="Crimson", Skin="Fair", Hair="Raven", Head="Hood", Face="Mask"), "Silver", "Dagger", False, False),
    (dict(Outfit="Mail", Colour="Player", Trim="Silver", Skin="Deep", Hair="Grey", Head="Horned", Face="Paint"), "Gold", "Axe", False, True),
    (dict(Outfit="Jerkin", Colour="Rust", Trim="Bone", Skin="Bronze", Hair="Blond", Head="WideHat", Face="Moustache"), "Silver", "Crossbow", True, False),
    (dict(Outfit="Tunic", Colour="Sky", Trim="Umber", Skin="Ashen", Hair="Auburn", Head="Mohawk", Face="Eyepatch"), "Gold", "Knives", False, True),
    (dict(Outfit="Tunic", Colour="Player", Trim="Rose", Skin="Tan", Hair="Brown", Head="Bandana", Face="Scar"), "Silver", "Sling", False, False),
    (dict(Outfit="Robe", Colour="Midnight", Trim="Silver", Skin="Fair", Hair="Blond", Head="Circlet", Face="Soft"), "Gold", None, False, True),
    (dict(Outfit="Leathers", Colour="Forest", Trim="Ochre", Skin="Tan", Hair="Brown", Head="Cap", Face="Plain"), "Silver", "Spear", False, False),
    (dict(Outfit="Jerkin", Colour="Ash", Trim="Crimson", Skin="Olive", Hair="Black", Head="Topknot", Face="Plain"), "Silver", "Greatsword", False, False),
    (dict(Outfit="Mail", Colour="Crimson", Trim="Gold", Skin="Brown", Hair="Black", Head="Shaved", Face="Beard"), "Gold", "Club", True, False),
]
GAME_CLIP = {"Sword": "RustySwordIdle", "Greatsword": "2HSwordIdle", "Axe": "AxeIdle", "Club": "ClubIdle",
             "Dagger": "DaggerIdle", "Spear": "SpearIdle", "Staff": "StaffIdleVariantMagic", "Bow": "BowIdle",
             "Crossbow": "CrossbowIdle", "Sling": "SlingIdle", "Knives": "KnivesIdle", None: "RustySwordIdle"}


def board_combos(sheet, gear, path):
    import hero_slots as HS
    ha, van = HG.build()
    cols = HL.atlas_colours(); used = set(cols)
    S = 3
    CW, CH = 26, 26
    row_h = H + 4
    lab = 4
    img = Image.new("RGBA", (lab + 4 * (W + CW + 6) * S, len(SAMPLES) * row_h * S + 16), (34, 32, 40, 255))
    d = ImageDraw.Draw(img)
    for s in range(4):
        d.text((lab + s * (W + CW + 6) * S + 4, 2), "P%d" % (s + 1), fill=(232, 228, 216))
    for r, (ch, tier, wpn, magic, spell) in enumerate(SAMPLES):
        clip = GAME_CLIP.get(wpn, "RustySwordIdle")
        if clip not in ha.clips: clip = "RustySwordIdle"
        idx = ha.clips[clip][0]
        for s in range(4):
            fr = compose(sheet, ch, s, tier, weapon=wpn, magic=magic, spell=spell)[0]
            x = lab + s * (W + CW + 6) * S
            y = 16 + r * row_h * S
            img.alpha_composite(scale(fr, S), (x, y))
            # in game
            sw = game_swaps(ch, s, cols)
            base = HS._load_ramp_cached(HL.RAMPS[HL.SLOT_NAMES[s]])
            ramp = dict(base); ramp.update(HL.plan(sw, base, used))
            f = HL.simulate(ha.frame(idx), ramp)
            e = van[idx]
            pal = palette_for(ch, s, tier)
            for kind, pid in (("HcFace_", ch["Face"]), ("HcHead_", ch["Head"])):
                cells = gear.get(kind + pid)
                if cells and e[0] >= 0:
                    c = recolour(cells[e[0]], pal)
                    HG._comp(f, c, e[1], e[2])
            bb = f.getbbox() or (0, 0, 1, 1)
            cx = e[1] + 7 if e[0] >= 0 else (bb[0] + bb[2]) // 2
            win = HG._crop(f, cx - CW // 2, bb[3] - CH + 1, CW, CH)
            tile = Image.new("RGBA", (CW, CH), (64, 62, 74, 255))
            tile.alpha_composite(win)
            img.alpha_composite(scale(tile, S), (x + (W + 1) * S, y))
    img.convert("RGB").save(path)
    print("board ->", path)


def recolour(cell, pal):
    im = cell.copy(); px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            p = px[x, y]
            if p[3] and p[:3] in pal: px[x, y] = pal[p[:3]] + (255,)
    return im


def board_icons(icons, path):
    S = 4
    cols = 12
    rows = (len(icons) + cols - 1) // cols
    img = Image.new("RGBA", (cols * (IC + 4) * S, rows * (IC + 8) * S), (34, 32, 40, 255))
    d = ImageDraw.Draw(img)
    for i, (n, im) in enumerate(icons):
        x, y = (i % cols) * (IC + 4) * S, (i // cols) * (IC + 8) * S
        img.alpha_composite(scale(im, S), (x, y))
        d.text((x, y + IC * S + 2), n.split("_", 1)[1][:11], fill=(200, 196, 186))
    img.convert("RGB").save(path)
    print("board ->", path)


def board_slots(slotp, path):
    S = 6
    img = Image.new("RGBA", (2 * 4 * (W + 2) * S, (H + 2) * S), (34, 32, 40, 255))
    for t, frames in enumerate(slotp):
        for k, fr in enumerate(frames):
            img.alpha_composite(scale(fr, S), ((t * 4 + k) * (W + 2) * S, 0))
    img.convert("RGB").save(path)
    print("board ->", path)


# ------------------------------------------------------------------------------------------------ debuff doc
DOC = os.path.join(ROOT, "build", "boards", "hero_debuffs.md")


def write_debuff_doc():
    """build/boards/hero_debuffs.md from the tables in HeroCustom.cs and the origins in OriginList.cs."""
    import re
    hc = open(src_file("HeroCustom.cs")).read()
    cl = open(src_file("OriginList.cs")).read()
    wp = open(src_file("WeaponPack.cs")).read()
    items = ""
    for f in ("ItemPack.cs", "ItemPack2.cs", "YsveldPack.cs", "ZhekraPack.cs", "KaurnPack.cs"):
        items += open(src_file(f)).read()
    def fmt(v, s, d):
        out = []
        for n, x in (("VIT", v), ("STR", s), ("DEX", d)):
            if x: out.append("%+d %s" % (x, n))
        return ", ".join(out) or "none"
    L = ["# Hero debuffs (generated by tools/sprites/hero_custom.py from the C# tables: do not edit by hand)", "",
         "Stats start at the god's values; each point of VIT, STR or DEX is one step of the game's own hero stat.",
         "Rule of thumb: about one point per 20 gold of shop price, more for range, safety and magic; a custom hero pays",
         "about what an origin with the same weapon pays. A gold hero with a weapon AND a spell pays both; no single stat",
         "drops by more than 4 (the excess moves to the lightest stat, so the total cost never shrinks).", "",
         "## Base origins (1.0.0: slightly stronger debuffs)", "",
         "| Origin | 1.0.0 | 0.10 |", "|---|---|---|"]
    was = {"Wanderer": "The standard hero, no changes", "Sellsword": "Shield spell, +1 VIT, -1 STR",
           "Huntress": "Bow, -2 VIT, -1 STR", "Hexblade": "Staff, -2 VIT, -2 STR, spells charge 15 pct faster",
           "Flagellant": "Club, -2 VIT, bleeds, low HP 2x dmg", "Pilgrim": "+1 VIT, -1 STR, pentagrams heal",
           "Gambler": "Sling, -2 VIT, +25 gold, 20 pct off", "Reaver": "Battle axe, -2 VIT, -2 DEX",
           "Cutpurse": "Knife, +1 DEX, -1 VIT, -1 STR", "Arbalist": "Crossbow, -2 VIT, -2 STR", "Scholar": "Book of Flame, -1 VIT"}
    for m in re.finditer(r'new OriginDef \{ id = "(\w+)".*?summary = "([^"]*)"', cl, re.S):
        L.append("| %s | %s | %s |" % (m.group(1), m.group(2), was.get(m.group(1), "(new)")))
    L.append("")
    L.append("Hexblade now charges spells 10 pct faster (was 15). Gambler: 15 gold (was 25) and the Lucky Claw discount.")
    L += ["", "## Custom hero weapons (silver and gold)", "", "| Weapon | Prefab | Family | Cost |", "|---|---|---|---|",
          "| God's weapon | (keep) | | none |"]
    for m in re.finditer(r'new object\[\] \{ "(Weapon\w+)", "([^"]+)", "(\w+)", (true|false), (-?\d), (-?\d), (-?\d)', hc):
        L.append("| %s | %s | %s%s | %s |" % (m.group(2), m.group(1), m.group(3), " (magic)" if m.group(4) == "true" else "",
                                              fmt(int(m.group(5)), int(m.group(6)), int(m.group(7)))))
    names = dict(re.findall(r'new WeaponDef \{ id = "(\w+)", name = "([^"]+)"', wp))
    costs = dict(re.findall(r'new WeaponDef \{ id = "(\w+)".*?cost = ([0-9.]+)', wp))
    for m in re.finditer(r'\{ "(\w+)", new\[\] \{ (-?\d), (-?\d), (-?\d) \} \}', hc.split("s_modWeapons")[1].split("};")[0]):
        L.append("| %s (mod, %s gold) | ModWeapon%s | | %s |" % (names.get(m.group(1), m.group(1)), costs.get(m.group(1), "?"), m.group(1),
                                                         fmt(int(m.group(2)), int(m.group(3)), int(m.group(4)))))
    L += ["", "## Custom hero spells (gold only)", "", "| Spell | Prefab | Cost |", "|---|---|---|", "| No spell | (keep) | none |"]
    for m in re.finditer(r'new object\[\] \{ "((?:Spell|Artifact)\w+)", "([^"]+)", (-?\d), (-?\d), (-?\d)', hc):
        L.append("| %s | %s | %s |" % (m.group(2), m.group(1), fmt(int(m.group(3)), int(m.group(4)), int(m.group(5)))))
    snames = dict(re.findall(r'id = "(Spell\w+)".*?name = "([^"]+)"', items))
    scost = dict(re.findall(r'id = "(Spell\w+)", cloneFrom = "\w+", cost = (\d+)', items))
    for m in re.finditer(r'\{ "(\w+)", new\[\] \{ (-?\d), (-?\d), (-?\d) \} \}', hc.split("s_modSpells")[1].split("};")[0]):
        L.append("| %s (mod, %s gold) | Mod%s | %s |" % (snames.get(m.group(1), m.group(1)), scost.get(m.group(1), "?"), m.group(1),
                                                    fmt(int(m.group(2)), int(m.group(3)), int(m.group(4)))))
    L += ["", "Content added later without a table entry uses HeroCustom.CostDebuff: round(price / 20) points (1-5 for a",
          "weapon in the order VIT, STR, DEX, VIT, STR; 1-3 for a spell in the order VIT, STR, VIT). The self-test flags it.", ""]
    os.makedirs(os.path.dirname(DOC), exist_ok=True)
    open(DOC, "w").write("\n".join(L))
    print("doc ->", DOC)


# ------------------------------------------------------------------------------------------------ main
def main():
    if "--doc" in sys.argv:
        write_debuff_doc(); return
    layers = portrait_layers()
    img, man = anim.pack("HcPortrait", [(n, fr, DURS) for n, fr in layers], W, H, (0, 0), OUT_P)
    anim.preview(img, man, os.path.join(OUT_P, "HcPortrait_preview.png"), scale=3)
    sheet = (img, man)
    print("portrait layers: %d anims" % len(man["anims"]))
    ramps = HG.load_ramps()
    gear = write_gear(ramps)
    print("gear pieces: %d head, %d face" % (len(GEAR_HEAD), len(GEAR_FACE)))
    icons = build_icons(sheet)
    write_icons(icons)
    print("icons: %d" % len(icons))
    slotp = [slot_portrait(sheet, "Silver"), slot_portrait(sheet, "Gold")]
    cols = HL.atlas_colours()
    write_cs(cols, ramps)
    write_debuff_doc()
    if "--boards" in sys.argv:
        d = sys.argv[sys.argv.index("--boards") + 1]
        os.makedirs(d, exist_ok=True)
        board_parts(sheet, os.path.join(d, "hc_parts.png"))
        board_combos(sheet, gear, os.path.join(d, "hc_combos.png"))
        board_icons(icons, os.path.join(d, "hc_icons.png"))
        board_slots(slotp, os.path.join(d, "hc_slots.png"))


if __name__ == "__main__":
    main()
