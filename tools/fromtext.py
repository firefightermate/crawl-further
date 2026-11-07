"""Decode spritify text (PAL line + char grid) into an RGBA PNG."""
import sys
from PIL import Image
CH = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789#$%&*+=?@"
def decode(txt):
    lines = [l for l in txt.strip().splitlines() if l.strip()]
    pal = {}
    for tok in lines[0].split()[1:]:
        pal[tok[0]] = tuple(int(tok[1 + i * 2:3 + i * 2], 16) for i in range(3))
    rows = lines[1:]
    w = max(len(r) for r in rows); im = Image.new("RGBA", (w, len(rows)), (0, 0, 0, 0)); p = im.load()
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c != ".": p[x, y] = pal[c] + (255,)
    return im
if __name__ == "__main__":
    decode(open(sys.argv[1]).read()).save(sys.argv[2])
