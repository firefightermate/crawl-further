"""Turn an upscaled 'pixel art' AI image into a true low-res sprite.
Usage: python3 pixelize.py in.png [--pitch N] [--bgtol 28]
Prints: PITCH, palette, and a char grid (one char per pixel, '.' = transparent).
Designed to run anywhere with Pillow (no numpy needed)."""
import sys, collections
from PIL import Image

CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789#$%&*+=?@"

def dist(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5

def detect_pitch(im, mask_fn):
    W, H = im.size
    px = im.load()
    changes_x, changes_y = [], []
    for y in range(0, H, 3):
        for x in range(1, W):
            if dist(px[x, y], px[x - 1, y]) > 30:
                changes_x.append(x)
    for x in range(0, W, 3):
        for y in range(1, H):
            if dist(px[x, y], px[x, y - 1]) > 30:
                changes_y.append(y)
    best = None
    for p10 in range(60, 400):  # pitch 6.0 .. 40.0 in 0.1 steps
        p = p10 / 10.0
        for ch in (changes_x,):
            # circular mean of phase
            import math
            s = c = 0.0
            for v in ch:
                a = 2 * math.pi * (v % p) / p
                s += math.sin(a); c += math.cos(a)
            score = (s * s + c * c) ** 0.5 / max(1, len(ch))
            off = (math.atan2(s, c) / (2 * math.pi)) * p % p
            if best is None or score > best[0] + 1e-9:
                best = (score, p, off)
    return best

def main():
    path = sys.argv[1]
    pitch = None; bgtol = 28
    if "--pitch" in sys.argv: pitch = float(sys.argv[sys.argv.index("--pitch") + 1])
    if "--bgtol" in sys.argv: bgtol = float(sys.argv[sys.argv.index("--bgtol") + 1])
    im = Image.open(path).convert("RGB")
    W, H = im.size
    px = im.load()
    corners = [px[2, 2], px[W - 3, 2], px[2, H - 3], px[W - 3, H - 3]]
    bg = tuple(sorted(c[i] for c in corners)[1] for i in range(3))
    if pitch is None:
        score, pitch, off = detect_pitch(im, None)
        # prefer the fundamental: if half pitch scores nearly as well, take it
    else:
        off = 0.0
        import math
        s = c = 0.0
        for y in range(0, H, 3):
            for x in range(1, W):
                if dist(px[x, y], px[x - 1, y]) > 30:
                    a = 2 * math.pi * (x % pitch) / pitch; s += math.sin(a); c += math.cos(a)
        off = (math.atan2(s, c) / (2 * math.pi)) * pitch % pitch
    # y offset
    import math
    s = c = 0.0
    for x in range(0, W, 3):
        for y in range(1, H):
            if dist(px[x, y], px[x, y - 1]) > 30:
                a = 2 * math.pi * (y % pitch) / pitch; s += math.sin(a); c += math.cos(a)
    offy = (math.atan2(s, c) / (2 * math.pi)) * pitch % pitch
    cols = int((W - off) // pitch); rows = int((H - offy) // pitch)
    grid = []
    for r in range(rows):
        row = []
        for q in range(cols):
            x0 = off + q * pitch; y0 = offy + r * pitch
            votes = collections.Counter()
            for dy in (0.3, 0.5, 0.7):
                for dx in (0.3, 0.5, 0.7):
                    x = int(x0 + dx * pitch); y = int(y0 + dy * pitch)
                    if 0 <= x < W and 0 <= y < H:
                        c3 = px[x, y]
                        votes[(c3[0] // 4 * 4, c3[1] // 4 * 4, c3[2] // 4 * 4)] += 1
            col = votes.most_common(1)[0][0] if votes else bg
            row.append(None if dist(col, bg) < bgtol else col)
        grid.append(row)
    # crop
    ys = [i for i, r in enumerate(grid) if any(r)]
    xs = [j for j in range(cols) if any(grid[i][j] for i in range(rows))]
    grid = [r[min(xs):max(xs) + 1] for r in grid[min(ys):max(ys) + 1]]
    # palette merge (cluster colours within 18)
    pal = []
    def idx(c):
        for i, p in enumerate(pal):
            if dist(p, c) < 18: return i
        pal.append(c); return len(pal) - 1
    out = []
    for r in grid:
        out.append("".join("." if c is None else CHARS[idx(c)] for c in r))
    print("PITCH %.2f off %.1f,%.1f size %dx%d bg %s" % (pitch, off, offy, len(grid[0]), len(grid), bg))
    print("PAL " + " ".join("%s=%02x%02x%02x" % (CHARS[i], *p) for i, p in enumerate(pal)))
    print("\n".join(out))

if __name__ == "__main__":
    main()
