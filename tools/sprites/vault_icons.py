"""Vault grid icons the game has no picture for -> art/out_branding/VaultIcons.png/.json (12 x 12 cells, the size
of a vault grid cell's box).

  Undiscovered  a dim sealed rune with a question mark: shown in a grid cell for an entry not found yet
                (the items/weapons/objects lists used to print "Undiscovered" instead).
  NoArt         a little scroll with a question mark: an entry whose prefab has no picture at all (safety net).
  Locked        a padlock: a silver/gold slot whose unlock challenge is not done yet (FURTHER category).
  Further       the FURTHER category's own cell marker (a tiny door), used for anything a mod registered
                without a picture.

Palette: the vault's own browns (cell text colours) so the icons sit in the grid like ink on the page.

python3 tools/sprites/vault_icons.py
"""
import json, os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "art", "core")

PAL = {
    "K": (30, 24, 22, 255),     # ink: carved marks and the lower/right rim
    "d": (69, 65, 53, 255),     # vault dark ink (cell disabled text colour)
    "m": (110, 101, 87, 255),   # mid
    "l": (162, 149, 129, 255),  # light (selected text colour)
    "h": (214, 203, 176, 255),  # highlight
    "g": (201, 161, 72, 255),   # gold
    "G": (240, 214, 120, 255),  # gold light
    "s": (140, 146, 158, 255),  # steel
    "S": (196, 202, 212, 255),  # steel light
}

ICONS = {
 "Undiscovered": [
  "............",
  "...KKKKKK...",
  "..KddddddK..",
  ".KdddlldddK.",
  ".KddlddlddK.",
  ".KdddddlddK.",
  ".KddddldddK.",
  ".KddddddddK.",
  ".KddddldddK.",
  "..KddddddK..",
  "...KKKKKK...",
  "............",
 ],
 "NoArt": [
  "............",
  "..KKKKKKKK..",
  ".KhllllllhK.",
  "..KllKKllK..",
  "..KlKllKlK..",
  "..KllllKlK..",
  "..KlllKllK..",
  "..KllllllK..",
  "..KlllKllK..",
  ".KhllllllhK.",
  "..KKKKKKKK..",
  "............",
 ],
 "Locked": [
  "............",
  "....KKKK....",
  "...KsKKsK...",
  "...Ks..sK...",
  "...Ks..sK...",
  "..KKKKKKKK..",
  "..KGGGGGgK..",
  "..KGgKKggK..",
  "..KGgKKggK..",
  "..KgggKggK..",
  "..KKKKKKKK..",
  "............",
 ],
 "Further": [
  "............",
  "....KKKK....",
  "...KmllmK...",
  "..KmlKKlmK..",
  "..KlKddKlK..",
  "..KlKdmKlK..",
  "..KlKmmKlK..",
  "..KlKmlKlK..",
  "..KlKllKlK..",
  ".KKKKKKKKKK.",
  ".KhhhhhhhhK.",
  ".KKKKKKKKKK.",
 ],
}


LIGHTER = {"d": "m", "m": "l", "l": "h", "h": "h", "g": "G", "G": "G", "s": "S", "S": "S"}


def lit_edge(rows, x, y):
    """No black ring: an outline pixel on the silhouette's upper or left side (open above or to the left, closed
    below and to the right) takes the lit tone of the shape just inside it; the lower and right rim stays dark, so
    the icon sits in the cell lit from the top left like the game's own art."""
    c = rows[y][x]
    if c != "K": return c
    at = lambda xx, yy: rows[yy][xx] if 0 <= yy < 12 and 0 <= xx < 12 else "."
    open_ul = at(x, y - 1) == "." or at(x - 1, y) == "."
    open_dr = at(x, y + 1) == "." or at(x + 1, y) == "."
    if not open_ul or open_dr: return c
    inner = at(x, y + 1) if at(x, y + 1) not in ".K" else at(x + 1, y)
    return LIGHTER.get(inner, c) if inner not in ".K" else c


def build():
    os.makedirs(OUT, exist_ok=True)
    names = list(ICONS)
    img = Image.new("RGBA", (12 * len(names), 12), (0, 0, 0, 0))
    px = img.load()
    for k, n in enumerate(names):
        rows = ICONS[n]
        assert len(rows) == 12 and all(len(r) == 12 for r in rows), n
        for y, r in enumerate(rows):
            for x, c in enumerate(r):
                if c in PAL: px[k * 12 + x, y] = PAL[lit_edge(rows, x, y)]
    img.save(os.path.join(OUT, "VaultIcons.png"))
    json.dump({"cellW": 12, "cellH": 12, "cols": len(names),
               "anims": [{"name": n, "frames": [k], "durations": [1.0]} for k, n in enumerate(names)]},
              open(os.path.join(OUT, "VaultIcons.json"), "w"), indent=1)
    pv = Image.new("RGBA", img.size, (69, 65, 53, 255))
    pv.alpha_composite(img)
    pv.resize((img.width * 8, img.height * 8), Image.NEAREST).save(os.path.join(OUT, "VaultIcons_preview.png"))
    print("VaultIcons", len(names), "icons")


if __name__ == "__main__":
    build()
