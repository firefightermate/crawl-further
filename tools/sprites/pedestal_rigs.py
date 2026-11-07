"""Shop pedestal sprites for every mod purchasable (the small item lying on the shop counter).

    python3 tools/sprites/pedestal_rigs.py [outdir]        (default art/out_pedestals)

Vanilla reference: the AtlasPurchasable elements the shop prop (PropPurchasable, exSprite anchor BotCenter, offset 0,
useTextureOffset on) shows. Each one is a 35x33 canvas whose bottom-centre sits on the prop's origin; the item is tiny
and lies or stands at the bottom of the canvas:
  * opaque item bottom on row 30-32 (rows counted from the canvas top), horizontal centre on x 16.5-17
  * no outline, 2-4 flat muted tones, one highlight pixel
  * a soft shadow (0x371a12 at alpha 59) one pixel below / below-right of the item
  * spells are closed tomes (Spell1-10: lying 7x4, standing 5x8 / 6x8 with page edge + red ribbon)
  * artifacts are the object itself (4-7 px wide), weapons lie diagonally, point to the lower left
Mod sheets load untrimmed (trimRect = whole cell), so drawing at the same canvas position gives the same placement.

Output: ShopPedestals.png/.json (cell 35x33, one 1-frame anim per purchasable) + ShopPedestals_preview.png.
Anim names: ItemDef id (= prefab "Mod"+id without "Mod"), and "Wpn"+id for WeaponDefs (prefab "ModWeapon"+id).
The item and weapon ids are read from the content mod's C# packs (src/CrawlFurther); the script fails if any of them has no drawing.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srcfiles import src_file, pack_files  # noqa: E402

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "art", "out_pedestals")
NAME = "ShopPedestals"
CW, CH = 35, 33
COLS = 14
SHADOW = (0x37, 0x1a, 0x12, 59)


def hx(s):
    s = s.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def shade(c, k):
    return tuple(max(0, min(255, int(round(v * k)))) for v in c)


def mute(c, amt=0.18, k=0.94):
    """Pull a bubble-icon accent toward grey and a touch darker so it sits with vanilla's flat counter items."""
    l = 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
    return tuple(max(0, min(255, int(round((v + (l - v) * amt) * k)))) for v in c)


# ------------------------------------------------------------------ shared colours (sampled from AtlasPurchasable)
PAGES = hx("a07c59")       # page edge of the vanilla tomes
RIBBON = hx("973641")
RIBBON_D = hx("793236")


# ------------------------------------------------------------------ spells: standing tomes (vanilla Spell7/8 layout)
TOME = [".AAAAA",
        "BCAAAA",
        "BAAAAA",
        "BAAAAA",
        "BAAAAA",
        "BAAAAA",
        "BDEDDF",
        ".FGFFF"]


def tome(cover, emblem, epal):
    """6x8 standing tome. emblem: up to 5 rows of 3 chars placed on the cover at cols 2-4, rows 1-5."""
    c = hx(cover)
    pal = {"A": c, "B": shade(c, 0.8), "C": shade(c, 1.22), "F": shade(c, 0.66), "D": PAGES, "E": RIBBON, "G": RIBBON_D}
    rows = [list(r) for r in TOME]
    for j, er in enumerate(emblem):
        for i, ch in enumerate(er):
            if ch != ".":
                rows[1 + j][2 + i] = ch
    for k, v in epal.items():
        pal[k] = mute(hx(v))
    return ["".join(r) for r in rows], pal


SPELLS = {
    # id: (cover, emblem rows, emblem palette)          emblem = the bubble icon's motif in 3x5 px
    "SpellWickwalk": ("7d4135", ["1.1", "2.2", ".1.", ".2."], {"1": "f28a26", "2": "c8551a"}),
    "SpellGraveCall": ("5e5f58", ["1.1", "111", "111", ".1.", "222"], {"1": "dcc998", "2": "3b2f2c"}),
    "SpellThornwall": ("4e5a34", [".3.", "1.1", "121", "121"], {"1": "7fd36a", "2": "3f7a3a", "3": "c03a2a"}),
    "SpellMirrorStep": ("3a3044", [".2.", "212", "232", "212", ".2."], {"1": "5e9cc8", "2": "8a93a8", "3": "1a1620"}),
    "SpellEmberVolley": ("6a4a3a", ["..1", "2..", "321", "2..", "..1"], {"1": "f28a26", "2": "c8551a", "3": "ffd85e"}),
    "SpellWaxSlick": ("5a3a4e", [".1.", ".1.", "...", "111", "222"], {"1": "f4eac6", "2": "b8a276"}),
    "SpellMarrowSpikes": ("6e4a40", [".3.", "313", "111", "111", "222"], {"1": "dcc998", "2": "7a6553", "3": "c0302a"}),
    "SpellBoneBoomerang": ("625e4a", ["111", "111", "313", "111", ".2."], {"1": "e8dcb4", "2": "b8a276", "3": "a81e1a"}),
    "SpellSporeBomb": ("8a7a5a", [".3.", "111", "121", "111", ".1."], {"1": "7a3fa0", "2": "e58fb0", "3": "5aa44a"}),
    "SpellRootSnare": ("3e4a2c", ["111", "1..", "1.3", "111"], {"1": "b08a5e", "3": "7fd36a"}),
    "SpellShardNova": ("3e4a66", [".1.", "1.1", ".2.", "1.1", ".1."], {"1": "8cc8ff", "2": "f0f9ff"}),
    "SpellShadowSwap": ("6c513c", ["1.2", "132", "1.2", "1.2"], {"1": "9a5cbf", "2": "c9d2e6", "3": "d9a6ff"}),
    "SpellSoulLantern": ("2e3238", [".2.", "222", "212", "212", "222"], {"1": "8cc8ff", "2": "9a96a0"}),
    "SpellBellToll": ("3a5a58", [".2.", ".1.", "111", "111", ".2."], {"1": "e6ae4a", "2": "9a6426"}),
    "SpellUndertow": ("2e3e4e", ["11.", "1.2", "1.2", ".22"], {"1": "338e8c", "2": "78d6c6"}),
    "SpellRiptide": ("4a5a50", [".22", "2.2", "2..", "111"], {"1": "338e8c", "2": "a8f0e4"}),
    "SpellWildCard": ("6a2f3a", ["111", "131", "111", "111"], {"1": "f4eac6", "3": "c0302a"}),
    "SpellLoadedDice": ("2f2a3a", ["11.", "13.", ".11", ".31"], {"1": "e8dcb4", "3": "c0302a"}),
    "SpellPuppetStrings": ("4a3a52", ["111", ".1.", "2.2", "2.2", "2.2"], {"1": "b08a5e", "2": "d9a6ff"}),
    "SpellZhkAcidSpit": ("6b5a2a", [".1.", "121", "111", ".3.", ".3."], {"1": "88d622", "2": "ccff66", "3": "488414"}),
    "SpellKrnChainSpark": ("44464e", ["..1", ".1.", "121", ".1.", "1.."], {"1": "9edaff", "2": "f4fcff"}),
    "SpellYsvRequiem": ("7a8aa0", ["222", "121", "1.1", "1.1", "..1"], {"1": "2e5a96", "2": "f0f9ff"}),
}

# ------------------------------------------------------------------ artifacts: the object itself, 3-7 px wide
ARTIFACTS = {
    # Votive Candle: candle stub in a little iron pot
    "ArtifactVotiveCandle": ([
        "..Y..",
        "..O..",
        ".wWw.",
        "IiiiI",
        "kkikk",
        ".k.k."], {"Y": "ffd85e", "O": "f28a26", "w": "c8b484", "W": "e8dcb4", "I": "8c8c98", "i": "666672", "k": "3a3a44"}),
    # Marrow Flask: blue glass flask of red marrow (vanilla potion shape)
    "ArtifactMarrowFlask": ([
        ".tt.",
        ".cg.",
        ".cg.",
        "ccXg",
        "RRrr",
        "Rrrq"], {"t": "6b5238", "c": "8cc8ff", "g": "3d6fb0", "X": "d8f2ff", "R": "ff462a", "r": "a81e1a", "q": "5e2426"}),
    # Rotting Apple: red apple with a bite, green stem, rot spot
    "ArtifactRottingApple": ([
        "..v.",
        ".Rr.",
        "Rrr.",
        "rrp.",
        ".pp."], {"v": "5aa44a", "R": "ff462a", "r": "a81e1a", "p": "5e2426"}),
    # Hollow Crown: dark violet crown with silver points and a gem
    "ArtifactHollowCrown": ([
        "u..u..u",
        "uU.u.Uu",
        "nnnNnnn",
        "qqqqqqq"], {"u": "c9d2e6", "U": "8a93a8", "n": "5b2f6e", "N": "8cc8ff", "q": "2b1a36"}),
    # Ember Heart: charred heart with an ember core
    "ArtifactEmberHeart": ([
        "kk.kk",
        "kOYok",
        ".kok.",
        "..k.."], {"k": "4a3c38", "O": "f28a26", "Y": "ffd85e", "o": "c8551a"}),
    # Venom Gland: fleshy sac with a green venom core
    "ArtifactVenomGland": ([
        ".EEE.",
        "EEgEE",
        "fEEEf",
        ".fvf."], {"E": "a85e6c", "f": "6e3a48", "g": "c4f552", "v": "3f7a3a"}),
    # Rime Ring: silver band with an ice gem
    "ArtifactRimeRing": ([
        ".cB.",
        "U..U",
        ".UU."], {"c": "d8f2ff", "B": "8cc8ff", "U": "8a93a8"}),
    # Leech Seed: red seed sprouting pale roots
    "ArtifactLeechSeed": ([
        ".R.",
        "RrR",
        "rrr",
        ".p.",
        "w.w"], {"R": "ff462a", "r": "a81e1a", "p": "5e2426", "w": "b8a276"}),
    # Thorn Mail: chainmail shirt laced with green thorns
    "ArtifactThornMail": ([
        "SS..SS",
        "SsSSsS",
        ".SvVS.",
        ".sSvs.",
        ".SSSS."], {"S": "8a93a8", "s": "5e5a64", "v": "3f7a3a", "V": "7fd36a"}),
    # Saint's Wick: tall candle on a brass dish with a gold halo glint
    "ArtifactSaintsWick": ([
        ".Y.",
        ".O.",
        ".W.",
        ".w.",
        ".w.",
        "TtT"], {"Y": "ffe28c", "O": "f28a26", "W": "f4eac6", "w": "dcc998", "T": "9a6426", "t": "d69e3e"}),
    # Lucky Die: bone die with green pips
    "ArtifactLuckyDie": ([
        "XXXW",
        "WgWw",
        "WWgw",
        "wwwc"], {"X": "f4eac6", "W": "dcc998", "w": "b8a276", "c": "7a6553", "g": "3f7a3a"}),
    # Hourglass of Ash: wooden frame, grey ash
    "ArtifactAshHourglass": ([
        "TTT",
        "cZc",
        ".z.",
        "cZc",
        "TTT"], {"T": "6b5238", "c": "c9d2e6", "Z": "beb9b0", "z": "8c8884"}),
    # Glass Mask: pale blue face, dark eye holes, a blue crack
    "ArtifactGlassMask": ([
        ".ccc.",
        "cKcKc",
        "ccBcc",
        ".cBc."], {"c": "d8f2ff", "K": "3d6fb0", "B": "5e9cc8"}),
    # Barnacle Shell: ribbed scallop
    "ArtifactBarnacleShell": ([
        ".WwWw.",
        "wWwWwW",
        ".gggg."], {"W": "d6d0c4", "w": "7a6553", "g": "4e403a"}),
    # Tidecaller Conch: cream spiral with a pink mouth
    "ArtifactTidecaller": ([
        "..WW.",
        ".WcWF",
        "WWcF.",
        ".cc.."], {"W": "e8dcb4", "c": "9a8468", "F": "e58fb0"}),
    # Brine Flask: green bottle with cork
    "ArtifactBrineFlask": ([
        ".t.",
        ".u.",
        "QCQ",
        "CIC",
        "CCC",
        "QQQ"], {"t": "6b5238", "u": "c9d2e6", "Q": "1f4e3c", "C": "358c5e", "I": "8adc96"}),
    # Jester's Bell: gold bell with a red cap tail
    "ArtifactJestersBell": ([
        "r...",
        ".rr.",
        ".YY.",
        "YyYY",
        "OKOO"], {"r": "c0302a", "Y": "d69e3e", "y": "ffe28c", "O": "9a6426", "K": "5c3a1a"}),
    # Joker's Wild: fanned cards with red pips
    "ArtifactJokersWild": ([
        ".XW.",
        "XrWW",
        "WWrW",
        "wWWw"], {"X": "f4eac6", "W": "dcc998", "w": "b8a276", "r": "c0302a"}),
    # Marionette Cross: crossed sticks, gold knot, lilac strings
    "ArtifactMarionetteCross": ([
        "T...T",
        ".TYT.",
        "T.L.T",
        "L.L.L"], {"T": "8a6a44", "Y": "d69e3e", "L": "d9a6ff"}),
    # Hive Amber: lump of amber resin
    "ArtifactZhkHiveAmber": ([
        ".YY.",
        "YyOO",
        "OOOo",
        ".oo."], {"Y": "f4c452", "y": "ffeca4", "O": "d68e22", "o": "a45812"}),
    # Lightning Rod: dark iron rod, copper band, blue spark tip
    "ArtifactKrnLightningRod": ([
        ".B.",
        ".s.",
        "BsB",
        ".s.",
        ".o.",
        ".s.",
        ".k."], {"B": "9edaff", "s": "787d8c", "o": "c2763e", "k": "45414c"}),
    # Widow's Shawl: dark folded shawl with frost-silk threads
    "ArtifactYsvShawl": ([
        "qBqqBq",
        ".qcBq.",
        "..qq.."], {"q": "453363", "B": "588cc2", "c": "c2e4f7"}),
}

# ------------------------------------------------------------------ weapons: same bounding box as the vanilla base pedestal
# (left, top) of the vanilla element's opaque bounds; grids are drawn at exactly that spot.
WEAPON_BASE = {
    "WeaponSpear": ("Weapon_Spear", 7, 29), "WeaponThrowingKnives": ("Weapon_ThrowingKnives", 12, 29),
    "Weapon1HandedSword": ("Weapon_1hSword", 12, 28), "WeaponClub": ("Weapon_Club", 12, 28),
    "Weapon2HandedSword": ("Weapon_2hSword", 8, 28), "WeaponDagger": ("Weapon_Dagger", 15, 29),
    "WeaponBow": ("Weapon_Bow", 7, 25), "WeaponBattleAxe": ("Weapon_BattleAxe", 11, 27),
    "WeaponMagicStaff": ("Weapon_MagicStaff", 10, 28), "WeaponCrossbow": ("Weapon_Crossbow", 12, 28),
    "WeaponSling": ("Weapon_Sling", 14, 28),
}

WEAPONS = {
    # Gravehook (spear): barbed hook head, dark shaft
    "Gravehook": ([
        "..............hhhhhh",
        ".s......hhhhhh......",
        "s..mhhhh............",
        "SSS................."], {"h": "6a4228", "s": "6c6874", "m": "aab0bc", "S": "c9c6cc"}),
    # Moonglaive (throwing knives): ice ring glaive with a grip across it
    "Moonglaive": ([
        "..BcXcB..",
        "Bc.www.cB",
        "..BcccB.."], {"B": "6688aa", "c": "9ec4dc", "X": "e6f6fc", "w": "7e5230"}),
    # Riftblade (1h sword): violet blade, silver guard, dark grip
    "Riftblade": ([
        ".......uqq",
        ".....LLLu.",
        "..LLL.....",
        "XL........"], {"u": "aab0bc", "q": "3e1a5c", "L": "c070e8", "X": "f0c8ff"}),
    # Snake-Eyes (club): bone die head with red pips on a handle
    "SnakeEyes": ([
        "........ww",
        "XXX...ww..",
        "crcWWW....",
        "Ccr......."], {"w": "6f4529", "W": "89663b", "X": "e8dfc4", "c": "c8bc9c", "C": "9c8e72", "r": "c0302a"}),
    # Tidebreaker (2h sword): wavy teal blade, gold guard
    "Tidebreaker": ([
        "............o....",
        "..........xTTohho",
        "......TTTTttto...",
        "...TTxTTt........",
        "xxT.............."], {"o": "b08a40", "h": "5e3a22", "T": "5fb3a8", "t": "2f7a7a", "x": "dafff4"}),
    # Leechfang (dagger): pale blade with a blood edge, dark red grip
    "Leechfang": ([
        "kgg...",
        ".gSr..",
        "....rS"], {"k": "6e1018", "g": "7c8292", "S": "d6dae0", "r": "c83a34"}),
    # Briarbow (bow): vine-green limbs, leaves, cream string
    "Briarbow": ([
        "..................v",
        ".................v.",
        ".................V.",
        ".......XX.......v..",
        "vV.......XX.vVvv...",
        "..vv.G....vXX......",
        "....vVvvvv...XX....",
        "...............X..."], {"v": "4a6a2a", "V": "2e4a1e", "G": "7fb04a", "X": "d0c8a8"}),
    # Dirge Maul (battle axe): bronze bell head on a haft, mouth facing out
    "DirgeMaul": ([
        "..........OY",
        ".........OYY",
        ".......wOYYy",
        "...wwww..OYY",
        "www.......OO"], {"w": "7e5230", "O": "8a6428", "Y": "c89a48", "y": "e8d090"}),
    # Wickstaff (magic staff): staff with a hanging green-glow lantern
    "Wickstaff": ([
        "..........wwwww",
        ".....WwWww.....",
        ".k.WW..........",
        "kGk............",
        "kGk............"], {"w": "6f4529", "W": "9c6c40", "k": "45414c", "G": "5ac08a"}),
    # Arcbolt (crossbow): dark iron stock, storm-blue limbs and string
    "Arcbolt": ([
        "...b...ikk",
        "..b..ikkkk",
        "..iikkkk..",
        "cikbb.....",
        "....bcc..."], {"k": "45414c", "i": "6c6874", "b": "8ab8e0", "c": "c8e8ff"}),
    # ---- v0.7.2 set (each grid fits its vanilla base's box: 1h/club 10x4, 2h 17x5, axe 12x5, bow 19x8,
    #      crossbow 10x5, dagger 6x3, staff 15x5, sling 7x3, spear 20x4, knives 9x3)
    # Frostbrand (1h sword): ice-blue blade, white guard
    "Frostbrand": ([
        ".......wkk",
        ".....IiIw.",
        "..IiI.....",
        "Xi........"], {"w": "e8fbff", "k": "6e4428", "I": "5c9cc8", "i": "a6dcf2", "X": "e8fbff"}),
    # Mercyblade (1h sword): slim steel blade, gold guard, red grip
    "Mercyblade": ([
        ".......grr",
        ".....SSg..",
        "..SSs.....",
        "Ss........"], {"g": "d8b040", "r": "9a1a2c", "S": "d6dae0", "s": "7c8292"}),
    # Reaper (2h sword): long snath with a pale crescent blade
    "Reaper": ([
        "..PPp............",
        ".P...ppp.......hh",
        "P.......hhhhhhh..",
        "...hhhhh.........",
        "hhh.............."], {"P": "b8ccbe", "p": "7e9488", "h": "5e3a22"}),
    # Starfall Maul (battle axe): black iron head with a gold star
    "Starfall": ([
        ".........NNN",
        "........NNYN",
        ".......wNNNN",
        "...wwww..NN.",
        "www........."], {"N": "3c2e66", "Y": "fbe48a", "w": "7e5230"}),
    # Hydra Bow (bow): sea-green recurve, three arrows
    "HydraBow": ([
        "..................s",
        ".................s.",
        ".......XX.......S..",
        "...........xx..s...",
        "sS.......XX.sSss...",
        "..ss......xXX......",
        "....sSssss...XX....",
        "...............X..."], {"s": "2f7a5a", "S": "1e4a3a", "X": "d0c8a8", "x": "5ab48a"}),
    # Bulwark Mace (club): flanged head and a little blue shield
    "Bulwark": ([
        "........II",
        ".bbb..ww..",
        "bBBbww....",
        ".bbb......"], {"I": "9a96a0", "w": "6e4428", "b": "2a4a7a", "B": "6a96d0"}),
    # Heartseeker (crossbow): crimson stock, pale limbs, red heart head
    "Heartseeker": ([
        "...b...rkk",
        "..b..rrrrk",
        "..rrrrkk..",
        "hrrbb.....",
        "....b....."], {"r": "9a1a2c", "k": "5c0e1a", "b": "c8bc9c", "h": "d8344a"}),
    # Shadow Kris (dagger): wavy violet-black blade, gold guard
    "Kris": ([
        "sgdd..",
        ".S.gd.",
        "S...dd"], {"s": "5a4682", "S": "34264a", "g": "d8a02a", "d": "241a3c"}),
    # Blightstaff (magic staff): crooked staff, green plague gourd
    "Blightstaff": ([
        "..........wwwww",
        "......wWww.....",
        ".gG.WW.........",
        "gGgg...........",
        ".gg............"], {"w": "5e3a22", "W": "7e5230", "g": "6a8a1a", "G": "aed23a"}),
    # Orrery Staff (magic staff): night-violet staff with rings and a white star
    "Orrery": ([
        "..........bbbbb",
        ".....BbBbb.....",
        "BYB.BB.........",
        "bYYb...........",
        ".bb............"], {"b": "3c2e66", "B": "6a5aa8", "Y": "f4f8ff"}),
    # Grudgestone (sling): cords and a dark red stone
    "Grudgestone": ([
        "....ll.",
        "rRll...",
        "rr....."], {"l": "6e4428", "r": "5e2424", "R": "d8344a"}),
    # Midas Sling (sling): cords and a gold coin
    "Midas": ([
        "....ll.",
        "gGll...",
        "gg....."], {"l": "6e4428", "g": "d8a02a", "G": "fff4b8"}),
    # Charger Lance (spear): long steel lance, cone guard, red pennant
    "Lance": ([
        ".............rr.....",
        "...........SSrhhhhhh",
        "....SSSSSSS.........",
        "Sss................."], {"S": "aab0bc", "s": "d6dae0", "r": "9a1a2c", "h": "6a4228"}),
    # Viper Lash (throwing knives): coiled green whip with a handle
    "Lash": ([
        ".vvv...hh",
        "v...vvh..",
        ".vVv....."], {"v": "2e6e22", "V": "5aa83a", "h": "6e4428"}),
    # Hunter's Kunai (throwing knives): two black kunai with red grips
    "Kunai": ([
        "Ss.rrr...",
        "...Ss.rro",
        "......o.."], {"S": "6c6874", "s": "34264a", "r": "9a1a2c", "o": "9a96a0"}),
}


# ------------------------------------------------------------------ items wave 3 drawings live with their icons
sys.path.insert(0, HERE)
from items3_icons import PEDESTALS as ITEMS3  # noqa: E402


# ------------------------------------------------------------------ ids from the C# packs (read only)
def mod_ids():
    items, weapons = [], []
    for f in ["ItemPack", "ItemPack2", "ItemPack3", "ZhekraPack", "KaurnPack", "YsveldPack"]:
        s = open(src_file(f + ".cs")).read()
        items += re.findall(r'new ItemDef \{ id = "(\w+)"', s)
    s = open(src_file("WeaponPack.cs")).read()
    weapons = re.findall(r'new WeaponDef \{ id = "(\w+)"[^\n]*?baseWeapon = "(\w+)"', s)
    return items, weapons


# ------------------------------------------------------------------ render
def draw(grid, pal, left, top):
    """One 35x33 cell: grid drawn with its top-left at (left, top), shadow one px below / below-right."""
    cell = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    px = cell.load()
    obj = {}
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch == ".":
                continue
            c = pal[ch]
            if isinstance(c, str):
                c = mute(hx(c))
            obj[(left + x, top + y)] = c
    for (x, y) in obj:
        for dx, dy in ((0, 1), (1, 1)):
            q = (x + dx, y + dy)
            if q not in obj and 0 <= q[0] < CW and 0 <= q[1] < CH:
                px[q] = SHADOW
    for (x, y), c in obj.items():
        assert 0 <= x < CW and 0 <= y < CH, (x, y)
        px[x, y] = tuple(c) + (255,)
    return cell


def place_centered(grid, bottom):
    w = max(len(r) for r in grid)
    return 17 - w // 2, bottom - len(grid) + 1


def build():
    items, weapons = mod_ids()
    cells, names, missing = [], [], []
    for iid in items:
        if iid in SPELLS:
            cover, em, ep = SPELLS[iid]
            grid, pal = tome(cover, em, ep)
            left, top = place_centered(grid, 31)               # vanilla Spell7-9: x14-19, y24-31
        elif iid in ARTIFACTS:
            grid, pal = ARTIFACTS[iid]
            h = len(grid)
            left, top = place_centered(grid, 30 if h <= 3 else 31)   # flat trinkets sit on row 30 like rings/medals
        elif iid in ITEMS3:
            # items wave 3 (tools/sprites/items3_icons.py PEDESTALS): potions stand on row 32 like the vanilla bottles
            grid, pal = ITEMS3[iid]
            h = len(grid)
            left, top = place_centered(grid, 32 if iid.startswith("Potion") else (30 if h <= 3 else 31))
        else:
            missing.append(iid); continue
        cells.append(draw(grid, pal, left, top)); names.append(iid)
    for wid, base in weapons:
        if wid not in WEAPONS or base not in WEAPON_BASE:
            missing.append("Wpn" + wid); continue
        grid, pal = WEAPONS[wid]
        _, left, top = WEAPON_BASE[base]
        cells.append(draw(grid, pal, left, top)); names.append("Wpn" + wid)
    if missing:
        raise SystemExit("no pedestal drawing for: " + ", ".join(missing))

    rows = (len(cells) + COLS - 1) // COLS
    pw, ph = 1, 1
    while pw < COLS * CW: pw *= 2
    while ph < rows * CH: ph *= 2
    sheet = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    for i, c in enumerate(cells):
        sheet.paste(c, ((i % COLS) * CW, (i // COLS) * CH))
    os.makedirs(OUT, exist_ok=True)
    sheet.save(os.path.join(OUT, NAME + ".png"))
    man = {"cellW": CW, "cellH": CH, "cols": COLS,
           "anims": [{"name": n, "frames": [i], "durations": [1.0]} for i, n in enumerate(names)]}
    json.dump(man, open(os.path.join(OUT, NAME + ".json"), "w"))
    preview(cells, names)
    print("%s: %d pedestal sprites (%d items, %d weapons) -> %s" % (NAME, len(cells), len(items), len(weapons), OUT))
    return cells, names


FLOOR = (140, 132, 103, 255)     # shop counter (AtlasEnvironment 'rb16Cshop')


def preview(cells, names, sc=4):
    cols = 9
    cw, ch = 24, 12                  # crop of the canvas bottom where items live (x 5..28, y 21..32)
    lab = 12
    rows = (len(cells) + cols - 1) // cols
    img = Image.new("RGBA", (cols * cw * sc, rows * (ch * sc + lab)), (28, 26, 32, 255))
    d = ImageDraw.Draw(img)
    for i, (c, n) in enumerate(zip(cells, names)):
        x0, y0 = (i % cols) * cw * sc, (i // cols) * (ch * sc + lab)
        bg = Image.new("RGBA", (cw, ch), FLOOR)
        bg.alpha_composite(c.crop((5, 21, 5 + cw, 21 + ch)))
        img.paste(bg.resize((cw * sc, ch * sc), Image.NEAREST), (x0, y0))
        d.text((x0 + 2, y0 + ch * sc), n.replace("Spell", "S:").replace("Artifact", "A:")[:16], fill=(220, 210, 190, 255))
    img.convert("RGB").save(os.path.join(OUT, NAME + "_preview.png"))


if __name__ == "__main__":
    build()
