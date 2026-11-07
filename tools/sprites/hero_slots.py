"""Player-slot colour sets for the hero origins: four colour sets per origin, one per player slot.

Run from the repo root:  python3 tools/sprites/hero_slots.py [--boards DIR]

Writes
    art/out_heroes/Hero<Origin>_P1..P4.png/.json/_preview.png   the origin portrait in each slot's colours
    art/out_herogear/Gear<Origin>_P1..P4.png/.json/_preview.png the in-game gear in each slot's colours
and with --boards: slot_portraits.png (every origin x 4 slots, menu portrait) and slot_ingame.png (every origin x
4 slots, in-game frames with the gear on, recoloured exactly like the ramp shader does).

The design never changes between slots: only each origin's team parts (hero_looks.TEAM for the body,
origin_portraits.TEAM for the portrait, GEAR_TEAM below for the gear) turn to the player's colour family (P1 blue,
P2 red, P3 green, P4 amber), with hero_looks.slot_col, so the portrait, the gear and the in-game body always agree.
The slot that already holds the origin's canonical colour keeps the original art exactly.
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PIL import Image, ImageDraw
import hero_looks as HL
import hero_gear as HG
import origin_portraits as OP

ROOT = os.getcwd()
OUT_P = os.path.join(ROOT, "art", "out_heroes")
OUT_G = os.path.join(ROOT, "art", "out_herogear")

# ------------------------------------------------------------------------------------------------ team parts
# gear sheet origin -> (palette keys of the team part, canonical slot); others are steel/hair and never change.
# Must match hero_looks.TEAM and origin_portraits.TEAM in meaning.
GEAR_TEAM = {
    "Huntress": ("k-=+#", 2),
    "Hexblade": ("kCnNI%", 0),
    "Pilgrim": ("rR", 3),
    "Gambler": ("rR", 1),
    "Reaver": ("bB", 0),
    "Cutpurse": ("Tt", 0),
}


# ------------------------------------------------------------------------------------------------ portraits
def build_portraits():
    out = {}
    for name in OP.ORDER:
        for slot in range(4):
            ims = OP.frames(name, slot)
            OP.pack("Hero%s_P%d" % (name, slot + 1), ims, OUT_P)
            out[(name, slot)] = ims
    print("portraits: %d origins x 4 slots" % len(OP.ORDER))
    return out


# ------------------------------------------------------------------------------------------------ gear
def gear_cells(origin, slot, ramps):
    g = HG.GEAR[origin]
    keys, canon = GEAR_TEAM.get(origin, ("", -1))
    saved = g["pal"]
    pal = dict(saved)
    for k in keys:
        pal[k] = "%02x%02x%02x" % HL.slot_col(HG.hexrgb(pal[k]), slot, canon)
    g["pal"] = pal
    try:
        pix = HG.gear_pixels(origin, ramps)
    finally:
        g["pal"] = saved
    return [HG.gear_cell(pix, t) for t in range(HG.NPOSE)]


def write_gear_sheet(sid, imgs):
    C = HG.CELL
    sheet = Image.new("RGBA", (128, 32), (0, 0, 0, 0))
    for t, im in enumerate(imgs): sheet.paste(im, ((t % 8) * C, (t // 8) * C))
    sheet.save(os.path.join(OUT_G, sid + ".png"))
    man = {"cellW": C, "cellH": C, "cols": 8,
           "anims": [{"name": "Pose%d" % t, "frames": [t], "durations": [1.0]} for t in range(HG.NPOSE)]}
    with open(os.path.join(OUT_G, sid + ".json"), "w") as fh: json.dump(man, fh)
    prev = Image.new("RGBA", (8 * (C + 1) + 1, 2 * (C + 1) + 1), (52, 50, 60, 255))
    for t, im in enumerate(imgs): prev.alpha_composite(im, (1 + (t % 8) * (C + 1), 1 + (t // 8) * (C + 1)))
    prev.resize((prev.width * 8, prev.height * 8), Image.NEAREST).save(os.path.join(OUT_G, sid + "_preview.png"))


def build_gear():
    ramps = HG.load_ramps()
    cells = {}
    for o in HG.ORIGINS:
        for slot in range(4):
            imgs = gear_cells(o, slot, ramps)
            write_gear_sheet("Gear%s_P%d" % (o, slot + 1), imgs)
            cells[(o, slot)] = imgs
    print("gear: %d origins x 4 slots" % len(HG.ORIGINS))
    return cells


# ------------------------------------------------------------------------------------------------ boards
def label(d, xy, text, fill=(232, 228, 216)):
    d.text(xy, text, fill=fill)


def board_portraits(portraits, path, S=5):
    pad = 4
    W, H = OP.W, OP.H
    lab = 70
    img = Image.new("RGBA", (lab + 4 * (W + pad) * S + pad * S, (len(OP.ORDER) * (H + pad) + pad) * S + 18), (34, 32, 40, 255))
    d = ImageDraw.Draw(img)
    for s in range(4):
        label(d, (lab + (pad + s * (W + pad)) * S + 4, 2), HL.SLOT_NAMES[s] + " " + ["blue", "red", "green", "amber"][s])
    for r, name in enumerate(OP.ORDER):
        y = 18 + (pad + r * (H + pad)) * S
        label(d, (4, y + H * S // 2 - 6), name)
        for s in range(4):
            cell = portraits[(name, s)][0].resize((W * S, H * S), Image.NEAREST)
            img.alpha_composite(cell, (lab + (pad + s * (W + pad)) * S, y))
    img.convert("RGB").save(path)
    print("board ->", path)


INGAME_CLIPS = {None: ("RustySwordIdle", "RustySwordRun", "RustySwordCombo1"), "Huntress": ("BowIdle", "BowRun", "BowCombo1"),
                "Hexblade": ("StaffIdleVariantMagic", "StaffRunVariantMagic", "StaffCombo1"),
                "Flagellant": ("ClubIdle", "ClubRun", "ClubCombo1"), "Gambler": ("SlingIdle", "SlingRun", "SlingCombo2"),
                "Reaver": ("AxeIdle", "AxeRun", "AxeAttack"), "Cutpurse": ("DaggerIdle", "DaggerRun", "DaggerCombo2"),
                "Arbalist": ("CrossbowIdle", "CrossbowRun", "CrossbowCombo1")}


def ingame_frame(ha, van, cols, used, oid, slot, idx, gear, extra_swaps=None, look=None):
    """One hero frame as the game draws it for (origin, slot): the player's vanilla ramp + the origin plan, gear on top."""
    base = HL.load_ramp_cached(HL.RAMPS[HL.SLOT_NAMES[slot]])
    ramp = dict(base)
    lk = look if look is not None else (HL.look_for(oid, slot) if oid in HL.LOOKS else {})
    sw = HL.swaps_for(lk, cols) + (extra_swaps or [])
    if sw: ramp.update(HL.plan(sw, base, used))
    f = HL.simulate(ha.frame(idx), ramp)
    e = van[idx]
    if e[0] >= 0:
        for g in gear:
            if g is not None: HG._comp(f, g[e[0]], e[1], e[2])
    return f


def _load_ramp_cached(name, _c={}):
    if name not in _c: _c[name] = HL.load_ramp(name)
    return _c[name]


HL.load_ramp_cached = _load_ramp_cached


def board_ingame(gear, path, S=4):
    ha, van = HG.build()
    cols = HL.atlas_colours(); used = set(cols)
    origins = ["Wanderer"] + HG.ORIGINS
    CW, CH = 30, 30
    lab = 70
    per = 3
    img = Image.new("RGBA", (lab + 4 * (per * (CW + 1) + 6) * S, (len(origins) * (CH + 2) + 6) * S), (44, 42, 52, 255))
    d = ImageDraw.Draw(img)
    for r, o in enumerate(origins):
        names = INGAME_CLIPS.get(o, INGAME_CLIPS[None])
        idxs = [ha.clips[names[0]][0], ha.clips[names[1]][2], ha.clips[names[2]][len(ha.clips[names[2]]) // 2]]
        for s in range(4):
            for k, i in enumerate(idxs):
                gl = [gear.get((o, s))] if o != "Wanderer" else []
                f = ingame_frame(ha, van, cols, used, o, s, i, gl)
                bb = f.getbbox() or (0, 0, 1, 1)
                e = van[i]
                cx = e[1] + 7 if e[0] >= 0 else (bb[0] + bb[2]) // 2
                win = HG._crop(f, cx - CW // 2, bb[3] - CH, CW, CH)
                tile = Image.new("RGBA", (CW, CH), (64, 62, 74, 255) if s % 2 == 0 else (56, 54, 66, 255))
                tile.alpha_composite(win)
                x = lab + (s * (per * (CW + 1) + 6) + k * (CW + 1)) * S
                img.paste(tile.resize((CW * S, CH * S), Image.NEAREST), (x, (6 + r * (CH + 2)) * S))
        label(d, (4, (6 + r * (CH + 2)) * S + CH * S // 2), o)
    for s in range(4):
        label(d, (lab + s * (per * (CW + 1) + 6) * S + 4, 4), HL.SLOT_NAMES[s])
    img.convert("RGB").save(path)
    print("board ->", path)


def main():
    portraits = build_portraits()
    gear = build_gear()
    if "--boards" in sys.argv:
        d = sys.argv[sys.argv.index("--boards") + 1]
        os.makedirs(d, exist_ok=True)
        board_portraits(portraits, os.path.join(d, "slot_portraits.png"))
        board_ingame(gear, os.path.join(d, "slot_ingame.png"))


if __name__ == "__main__":
    main()
