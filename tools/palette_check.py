"""Does the mod's item art sit in Crawl's own palette? Compares each icon sheet's colours with the vanilla item and prop
atlases (dumped from the game, not shipped with the mod).

    python3 tools/palette_check.py --vanilla DIR [sheet-id ...]      (default: every item icon sheet)

DIR holds the vanilla textures AtlasProps_6.png and AtlasPurchasable_108.png (or set CRAWL_VANILLA_TEX).
For every icon (frame 0 of its first anim, opaque pixels only) it measures saturation (HSV S), chroma (max - min) and
value at the 90th percentile, after setting aside the icon's accent: its most saturated colour family (one hue band,
at most 15% of the pixels). An icon fails if what is left is more saturated or brighter than the vanilla art's 90th
percentile, or if it has a second bright colour family besides the accent.
"""
import colorsys, glob, json, os, sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VANILLA = ("AtlasProps_6.png", "AtlasPurchasable_108.png")
ICON_DIRS = ("out_icons_v2", "out_items3", "out_items", "out_ossivar", "out_sylvene", "out_umbrael", "out_zhekra", "out_kaurn",
             "out_ysveld")
ACCENT_SHARE = 0.15


def measures(px):
    a = np.asarray(px, dtype=float) / 255.0
    mx, mn = a.max(1), a.min(1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0.0)
    hue = np.array([colorsys.rgb_to_hsv(*c)[0] for c in a]) * 360.0
    return sat, mx - mn, mx, hue


def opaque_pixels(im):
    a = np.asarray(im.convert("RGBA"))
    return a[a[..., 3] > 128][:, :3]


def vanilla_limits(tex_dir):
    px = np.concatenate([opaque_pixels(Image.open(os.path.join(tex_dir, n))) for n in VANILLA])
    sat, chroma, val, _ = measures(px)
    return {"sat": np.percentile(sat, 90), "chroma": np.percentile(chroma, 90), "val": np.percentile(val, 90)}


def split_accent(px, lim):
    """(rest, accent count, other bright families): bright = more chromatic than vanilla's 90th percentile."""
    sat, chroma, val, hue = measures(px)
    bright = chroma > lim["chroma"]
    fams = {}
    for i in np.nonzero(bright)[0]:
        fams.setdefault(int(hue[i] // 40), []).append(i)
    keep = np.ones(len(px), bool)
    acc, others = 0, 0
    if fams:
        order = sorted(fams.values(), key=len, reverse=True)
        main = order[0]
        if len(main) <= ACCENT_SHARE * len(px):
            keep[main] = False
            acc = len(main)
            others = sum(len(f) for f in order[1:])
        else:
            others = sum(len(f) for f in order)
    return px[keep], acc, others


def frame0(path):
    m = json.load(open(path[:-4] + ".json"))
    a = m["anims"][0]
    f = a["frames"][0]
    x, y = (f % m["cols"]) * m["cellW"], (f // m["cols"]) * m["cellH"]
    return Image.open(path).convert("RGBA").crop((x, y, x + m["cellW"], y + m["cellH"]))


def icon_sheets():
    out = []
    for d in ICON_DIRS:
        for p in sorted(glob.glob(os.path.join(ROOT, "art", d, "Icon*.png"))):
            n = os.path.basename(p)[:-4]
            if n.endswith("_preview") or not os.path.exists(p[:-4] + ".json"): continue
            out.append(p)
    return out


def check(paths, lim):
    rows = []
    for p in paths:
        px = opaque_pixels(frame0(p))
        if len(px) < 8: continue
        rest, acc, others = split_accent(px, lim)
        sat, chroma, val, _ = measures(rest)
        r = {"id": os.path.basename(p)[:-4], "sat": np.percentile(sat, 90), "chroma": np.percentile(chroma, 90),
             "val": np.percentile(val, 90), "accent": acc, "others": others, "n": len(px)}
        r["ok"] = (r["sat"] <= lim["sat"] and r["chroma"] <= lim["chroma"] and r["val"] <= lim["val"]
                   and others <= max(2, 0.03 * len(px)))
        rows.append(r)
    return rows


def main():
    args = sys.argv[1:]
    tex = os.environ.get("CRAWL_VANILLA_TEX")
    if "--vanilla" in args:
        i = args.index("--vanilla"); tex = args[i + 1]; del args[i:i + 2]
    if not tex:
        sys.exit("palette_check: give --vanilla DIR (the dumped AtlasProps_6.png and AtlasPurchasable_108.png)")
    lim = vanilla_limits(tex)
    paths = [p for p in icon_sheets() if not args or os.path.basename(p)[:-4] in args]
    rows = check(paths, lim)
    print("vanilla 90th percentile: sat %.2f  chroma %.2f  value %.2f" % (lim["sat"], lim["chroma"], lim["val"]))
    bad = 0
    for r in rows:
        bad += not r["ok"]
        print("%-4s %-28s sat %.2f chroma %.2f value %.2f  accent %3d px  other bright %2d px" %
              ("OK" if r["ok"] else "FAIL", r["id"], r["sat"], r["chroma"], r["val"], r["accent"], r["others"]))
    print("%d of %d icons outside Crawl's palette" % (bad, len(rows)))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
