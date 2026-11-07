#!/usr/bin/env python3
"""Make the Example God's sheets by recolouring Crawl: Further sheets (orange wax and fire -> teal glimmer).

    python3 examples/ExampleGod/tools/make_art.py

Reads art/out*/ from the repo and writes examples/ExampleGod/art/<Sheet>.png and .json. The JSON keeps the source's
grid and only the animations the example's code uses. Run it again after the source sheets change.
"""
import colorsys, glob, json, os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLE = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(EXAMPLE))
OUT = os.path.join(EXAMPLE, "art")

HUE_SHIFT = 140 / 360.0   # orange (about 30 degrees) lands on teal (about 170)

# new sheet id: (source sheet id, animations to keep; None keeps them all)
SHEETS = {
    "GlimmerRat": ("Wickling", ["Idle", "Run", "Bite", "Dash", "Death", "Dead", "Statue", "Knockback", "Portrait"]),
    "GlimmerGrub": ("TallowGrub", ["Idle", "Run", "Spit", "Rise", "Death", "Dead", "Statue", "Knockback", "Portrait"]),
    "GlimmerMoth": ("AshMoth", ["Idle", "Run", "Puff", "Dive", "Death", "Dead", "Statue", "Knockback", "Portrait"]),
    "DeityGlimmer": ("DeityVhorrul", None),
    "FxGlimmerBolt": ("FxCandleBolt", None),
    "FxGlimmerWisp": ("FxVhFlare", None),
    "IconGlimmerVolleyBubble": ("IconEmberVolleyBubble", None),
}

# one-cell sheets cut from another sheet: new id -> (source sheet, source anim, new anim name)
CUTS = {
    "GlimmerPedestals": ("ShopPedestals", "SpellEmberVolley", "SpellGlimmerVolley"),
}


def find(sheet):
    hits = glob.glob(os.path.join(ROOT, "art", "*", sheet + ".json"))
    if len(hits) != 1:
        raise SystemExit("expected one %s.json under art/, found %d" % (sheet, len(hits)))
    return hits[0][:-5]


def recolour(img):
    img = img.convert("RGBA")
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            r2, g2, b2 = colorsys.hsv_to_rgb((h + HUE_SHIFT) % 1.0, s, v)
            px[x, y] = (round(r2 * 255), round(g2 * 255), round(b2 * 255), a)
    return img


def save(sheet, img, manifest):
    img.save(os.path.join(OUT, sheet + ".png"))
    with open(os.path.join(OUT, sheet + ".json"), "w") as f:
        json.dump(manifest, f, indent=1)
    print("%-26s %dx%d, %d anims" % (sheet, img.width, img.height, len(manifest["anims"])))


def main():
    os.makedirs(OUT, exist_ok=True)
    for sheet, (src, keep) in SHEETS.items():
        base = find(src)
        manifest = json.load(open(base + ".json"))
        anims = manifest.get("anims", [])
        if keep is not None:
            missing = set(keep) - set(a["name"] for a in anims)
            if missing:
                raise SystemExit("%s has no %s" % (src, ", ".join(sorted(missing))))
            anims = [a for a in anims if a["name"] in keep]
        out = {"cellW": manifest["cellW"], "cellH": manifest["cellH"], "cols": manifest["cols"], "anims": anims}
        save(sheet, recolour(Image.open(base + ".png")), out)

    for sheet, (src, anim, name) in CUTS.items():
        base = find(src)
        manifest = json.load(open(base + ".json"))
        a = next(a for a in manifest["anims"] if a["name"] == anim)
        w, h, cols = manifest["cellW"], manifest["cellH"], manifest["cols"]
        cell = a["frames"][0]
        x, y = (cell % cols) * w, (cell // cols) * h
        img = Image.open(base + ".png").convert("RGBA").crop((x, y, x + w, y + h))
        save(sheet, recolour(img), {"cellW": w, "cellH": h, "cols": 1, "anims": [{"name": name, "frames": [0]}]})


if __name__ == "__main__":
    main()
