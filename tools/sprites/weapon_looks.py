"""In-hand colours for the mod weapons: the hero's weapon pixels are baked into the hero atlas, so each mod weapon
recolours its base weapon's pixels through the hero ramp (the same paletted shader HeroLooks uses for origins).

    python3 tools/sprites/weapon_looks.py [preview.png]

Writes the generated table block in src/CrawlFurther/Weapons/WeaponPack.cs (WeaponLooks.s_raw) and a preview that recolours
each mod weapon's real hero frames (idle, run, every attack clip it uses) exactly like the ramp does, next to the
vanilla frames. Only weapon slots are touched: every source colour below is used by weapon pixels alone
(checked against all non-weapon hero clips: only the base weapon's own magic-variant clips share them).
"""
import json, os, re, sys, warnings
from collections import Counter
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srcfiles import src_file, pack_files  # noqa: E402

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from hero_looks import Clips, slot, load_ramp, atlas_colours, RAMPS, DUMP, BOARDS, PINK  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
CS = src_file("WeaponPack.cs")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BOARDS, "weapon_inhand.png")
H = lambda s: tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))

# ------------------------------------------------------------------ weapon pixel roles per base (atlas colours)
BLADE, HILT, BLADE2, BLADE3 = (203, 203, 203), (68, 85, 116), (130, 127, 126), (187, 189, 193)
SHAFT, WOODL, SHAFT2 = (101, 60, 42), (137, 102, 59), (119, 81, 51)
AXE_HAFT, AXE_HEAD, AXE_SHADE = (99, 68, 48), (190, 185, 182), (162, 151, 143)
BOW_WOOD, BOW_STRING = (111, 69, 41), (181, 161, 139)
CLUB_D, CLUB_M, CLUB_L, CLUB_E = (111, 72, 47), (126, 89, 54), (154, 124, 64), (112, 74, 49)
XB_STOCK, XB_WOOD, XB_LIMB, XB_LIMBL = (96, 69, 37), (132, 96, 53), (193, 177, 134), (208, 190, 160)
SLING, SLING_STONE = (114, 78, 54), (199, 178, 153)
GEM = (239, 50, 109)                     # the staff's glow (only staffs and magic variants draw it)

ROLES = {
    "Weapon1HandedSword": {"blade": BLADE, "hilt": HILT},
    "Weapon2HandedSword": {"blade": BLADE, "hilt": HILT, "blade2": BLADE2},
    "WeaponDagger": {"blade": BLADE, "hilt": HILT},
    "WeaponThrowingKnives": {"blade": BLADE, "hilt": HILT, "blade3": BLADE3},
    "WeaponSpear": {"shaft": SHAFT, "woodL": WOODL, "tip": BLADE, "shaft2": SHAFT2},
    "WeaponBattleAxe": {"haft": AXE_HAFT, "head": AXE_HEAD, "shade": AXE_SHADE},
    "WeaponBow": {"wood": BOW_WOOD, "woodL": WOODL, "string": BOW_STRING},
    "WeaponClub": {"dark": CLUB_D, "mid": CLUB_M, "light": CLUB_L, "edge": CLUB_E, "studs": BLADE},
    "WeaponCrossbow": {"stock": XB_STOCK, "wood": XB_WOOD, "limb": XB_LIMB, "limbL": XB_LIMBL},
    "WeaponMagicStaff": {"shaft": SHAFT, "woodL": WOODL, "gem": GEM},
    "WeaponSling": {"leather": SLING, "stone": SLING_STONE},
}

# ------------------------------------------------------------------ themes (role -> colour)
THEMES = {
    "Gravehook": dict(shaft=H("3c3a44"), woodL=H("6c6874"), tip=H("b4642e"), shaft2=H("54505c")),       # iron-chain haft, rusted hook
    "Moonglaive": dict(blade=H("c4e2f0"), hilt=H("5a7aa6"), blade3=H("9ec4dc")),                       # pale silver-blue
    "Riftblade": dict(blade=H("b45adc"), hilt=H("2a163e")),                                             # violet void steel
    "SnakeEyes": dict(dark=H("b8aa86"), mid=H("d8ccaa"), light=H("f4eedc"), edge=H("c8bc98"), studs=H("c0302a")),  # bone + red pips
    "Tidebreaker": dict(blade=H("5fb3a8"), hilt=H("b08a40"), blade2=H("2f7a7a")),                     # sea-green, bronze guard
    "Leechfang": dict(blade=H("c83434"), hilt=H("5c0e1a")),                                            # blood-red
    "Briarbow": dict(wood=H("2e4a1e"), woodL=H("7aae3e"), string=H("d0c8a8")),                         # thorny green wood
    "DirgeMaul": dict(haft=H("5a3a22"), head=H("dcac52"), shade=H("9a6a24")),                          # bell bronze
    "Wickstaff": dict(shaft=H("b8a276"), woodL=H("e8dcb4"), gem=H("ff9a3a")),                          # tallow + flame
    "Arcbolt": dict(stock=H("3a3844"), wood=H("5c5a6a"), limb=H("78b4f0"), limbL=H("d0ecff")),         # dark iron + electric blue
    "Frostbrand": dict(blade=H("a8e2f6"), hilt=H("e4f6ff")),                                            # ice
    "Mercyblade": dict(blade=H("f0dca8"), hilt=H("a81e2c")),                                            # pale gold blade, crimson guard
    "Reaper": dict(blade=H("c4dccc"), hilt=H("1c201e"), blade2=H("4a5e54")),                           # ghost-pale scythe (icon PALE), not Tidebreaker's teal
    "Starfall": dict(haft=H("c89a34"), head=H("4a3c7a"), shade=H("2c2250")),                           # night iron, gold haft
    "HydraBow": dict(wood=H("173a52"), woodL=H("46a8bc"), string=H("e8d8c0")),                         # deep-sea serpent blue (Briarbow is the green bow)
    "Bulwark": dict(dark=H("4e4e5c"), mid=H("767686"), light=H("aeaebe"), edge=H("62626e"), studs=H("4a7ac0")),  # iron, blue studs
    "Heartseeker": dict(stock=H("5c0e1a"), wood=H("9a1a2c"), limb=H("d0c09a"), limbL=H("ff8aa0")),    # crimson + bone
    "Kris": dict(blade=H("4a3a72"), hilt=H("d8a02a")),                                                  # shadow steel, gold
    "Blightstaff": dict(shaft=H("4a5a1a"), woodL=H("8aa632"), gem=H("b4e03a")),                        # sickly green
    "Orrery": dict(shaft=H("2e2458"), woodL=H("6a5aa8"), gem=H("f4f8ff")),                             # night-violet shaft, star-white head (Wickstaff is the gold one)
    "Grudgestone": dict(leather=H("5e2424"), stone=H("8a3a32")),                                       # grudge red
    "Midas": dict(leather=H("8a6422"), stone=H("f2c84a")),                                             # gold coin
    "Lance": dict(shaft=H("a82830"), woodL=H("e05a5a"), tip=H("e6eaf0"), shaft2=H("7a1a22")),         # red tourney lance
    "Lash": dict(blade=H("5aa83a"), hilt=H("6e4428"), blade3=H("2e6e22")),                            # venom green
    "Kunai": dict(blade=H("7a7690"), hilt=H("b01e30"), blade3=H("9a96aa")),                            # gunmetal, red grip
}


# ------------------------------------------------------------------ the mod weapons and their hero clips (read from C#)
def mod_weapons():
    s = open(CS).read()
    out = []
    for m in re.finditer(r'new WeaponDef \{ id = "(\w+)", name = "([^"]+)"[^\n]*?baseWeapon = "(\w+)"(?:, baseCombo = (-?\d+))?', s):
        start = m.end()
        nxt = s.find("new WeaponDef {", start)
        body = s[start:nxt if nxt > 0 else len(s)]
        srcs = [int(x) for x in re.findall(r"new (?:WpnAttack|WeaponAttack)\((\d+),", body)]
        out.append((m.group(1), m.group(2), m.group(3), int(m.group(4) or -1), srcs))
    return out


def clip_names(base, combo, srcs):
    pid = {}
    for l in open(DUMP + "/db/exSpriteAnimClip.jsonl"):
        c = json.loads(l); pid[c["_pid"]] = c["m_Name"]
    w = [json.loads(l) for l in open(DUMP + "/db/Weapon.jsonl") if json.loads(l)["_go"] == base][0]
    name = lambda ref: pid.get(ref["m_PathID"]) if ref["m_PathID"] else None
    idle, run = name(w["m_animationIdle"]), name(w["m_animationRun"])
    if 0 <= combo < len(w["m_combos"]):
        idle = name(w["m_combos"][combo]["m_animationIdle"]) or idle
        run = name(w["m_combos"][combo]["m_animationRun"]) or run
    atk = []
    for i in srcs:
        a = w["m_attacks"][i]
        atk.append(name(a["m_animationFront"]))
        atk += [name(x["m_animation"]) for x in a["m_animAngles"] if x["m_animation"]["m_PathID"]]
    return idle, run, list(dict.fromkeys(atk))


def swaps(wid, base):
    roles = ROLES[base]
    return [(roles[r], c) for r, c in THEMES[wid].items()]


def ramp_with(swaps_, base_ramp, used):
    """HeroLooks' plan for these swaps on a player ramp: exact slots, plus pink non-hero neighbours."""
    r = dict(base_ramp)
    exact = {slot(f): t for f, t in swaps_}
    r.update(exact)
    for f, t in swaps_:
        x, y = slot(f)
        for dx, dy in ((-1, 0), (1, 0), (-1, 1), (1, 1), (-1, -1), (1, -1), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if 0 <= n[0] < 256 and 0 <= n[1] < 64 and n not in exact and n not in used and base_ramp[n] == PINK:
                r[n] = t
    return r


def simulate(frame, ramp):
    im = frame.copy(); px = im.load()
    for yy in range(im.height):
        for xx in range(im.width):
            p = px[xx, yy]
            if p[3] == 0: continue
            t = ramp[slot(p)]
            if t != PINK: px[xx, yy] = t + (p[3],)
    return im


def write_cs(weapons):
    lines = ["        // <generated by tools/sprites/weapon_looks.py: do not edit by hand>",
             "        // per weapon id: (from, to) RGB pairs; from = a hero-atlas weapon colour, its ramp slot gets 'to'",
             "        static readonly Dictionary<string, int[]> s_raw = new Dictionary<string, int[]>",
             "        {"]
    for wid, _, base, _, _ in weapons:
        body = ", ".join("0x%02X%02X%02X, 0x%02X%02X%02X" % (f + t) for f, t in swaps(wid, base))
        lines.append('            { "%s", new[] { %s } },' % (wid, body))
    lines += ["        };", "        // </generated>"]
    src = open(CS).read()
    a = src.index("        // <generated by tools/sprites/weapon_looks.py")
    b = src.index("        // </generated>", a) + len("        // </generated>")
    open(CS, "w").write(src[:a] + "\n".join(lines) + src[b:])


def crop_all(frames):
    box = None
    for f in frames:
        b = f.getbbox()
        if b: box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    return box


def main():
    weapons = mod_weapons()
    missing = [w[0] for w in weapons if w[0] not in THEMES]
    if missing: raise SystemExit("no in-hand theme for: " + ", ".join(missing))
    write_cs(weapons)
    clips = Clips()
    cols = atlas_colours()
    used = set(cols.keys())
    base_ramp = load_ramp(RAMPS["P1"])
    rows, warn = [], []
    for wid, name, base, combo, srcs in weapons:
        idle, run, atk = clip_names(base, combo, srcs)
        frames = clips.get(idle)[:1] + clips.get(run)[:2]
        for a in atk[:4]:
            fs = clips.get(a)
            frames += [fs[i] for i in sorted(set([0, len(fs) // 3, len(fs) // 2, (2 * len(fs)) // 3]))][:4]
        ramp = ramp_with(swaps(wid, base), base_ramp, used)
        # every colour the weapon's own clips draw: anything that is not body/skin and not themed gets flagged
        seen = Counter(p[:3] for f in frames for p in f.getdata() if p[3])
        rows.append((wid, name, base, [simulate(f, base_ramp) for f in frames], [simulate(f, ramp) for f in frames]))
    sc, pad = 3, 2
    cw = max(f.width for r in rows for f in r[3]); ch = max(f.height for r in rows for f in r[3])
    ncol = max(len(r[3]) for r in rows)
    W = 120 + ncol * (cw * sc // 2 + pad)
    # each weapon: label column, then its frames (vanilla above, recoloured below, cropped to the action)
    out_rows = []
    for wid, name, base, van, mod in rows:
        box = crop_all(van)
        vv = [f.crop(box) for f in van]; mm = [f.crop(box) for f in mod]
        fw, fh = box[2] - box[0], box[3] - box[1]
        img = Image.new("RGBA", (120 + len(vv) * (fw * sc + pad), 2 * fh * sc + 6), (34, 32, 40, 255))
        d = ImageDraw.Draw(img)
        d.text((4, 4), name, fill=(235, 228, 210, 255))
        d.text((4, 18), base.replace("Weapon", ""), fill=(150, 144, 160, 255))
        d.text((4, fh * sc + 6), "mod", fill=(170, 200, 160, 255))
        for i, (a, b) in enumerate(zip(vv, mm)):
            x = 120 + i * (fw * sc + pad)
            img.alpha_composite(a.resize((fw * sc, fh * sc), Image.NEAREST), (x, 0))
            img.alpha_composite(b.resize((fw * sc, fh * sc), Image.NEAREST), (x, fh * sc + 6))
        out_rows.append(img)
    Wt = max(i.width for i in out_rows); Ht = sum(i.height + 6 for i in out_rows)
    sheet = Image.new("RGBA", (Wt, Ht), (22, 20, 26, 255))
    y = 0
    for i in out_rows:
        sheet.alpha_composite(i, (0, y)); y += i.height + 6
    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    sheet.convert("RGB").save(OUT)
    print("in-hand colours: %d weapons -> %s, preview %s (%dx%d)" % (len(rows), CS, OUT, Wt, Ht))


if __name__ == "__main__":
    main()
