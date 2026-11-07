import sys, collections
from PIL import Image
CH = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789#$%&*+=?@"
def d(a, b): return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5
def spritify(path, H, ncol=14, bgtol=34, out=None, crop=None):
    im = Image.open(path).convert("RGB")
    if crop: im = im.crop(crop)
    W0, H0 = im.size; p = im.load()
    cs = [p[2, 2], p[W0 - 3, 2], p[2, H0 - 3], p[W0 - 3, H0 - 3]]
    bg = tuple(sorted(c[i] for c in cs)[1] for i in range(3))
    a = Image.new("L", im.size)
    ap = a.load()
    for y in range(H0):
        for x in range(W0):
            ap[x, y] = 255 if d(p[x, y], bg) > bgtol else 0
    bb = a.getbbox()
    im = im.crop(bb); a = a.crop(bb)
    w = max(1, round(im.width * H / im.height))
    # premultiplied area resample
    rgba = im.convert("RGBA"); rgba.putalpha(a)
    pm = Image.new("RGBA", rgba.size)
    pm.paste(rgba, (0, 0), rgba)
    sm = rgba.resize((w, H), Image.BOX)
    sa = a.resize((w, H), Image.BOX)
    # colour from mode of opaque source pixels per cell for crispness
    sx = im.width / w; sy = im.height / H
    src = im.load(); srca = a.load()
    res = Image.new("RGBA", (w, H), (0, 0, 0, 0)); rp = res.load()
    for y in range(H):
        for x in range(w):
            if sa.getpixel((x, y)) < 110: continue
            votes = collections.Counter()
            for yy in range(int(y * sy), max(int(y * sy) + 1, int((y + 1) * sy))):
                for xx in range(int(x * sx), max(int(x * sx) + 1, int((x + 1) * sx))):
                    if srca[xx, yy]:
                        c = src[xx, yy]; votes[(c[0] // 8 * 8, c[1] // 8 * 8, c[2] // 8 * 8)] += 1
            if votes: rp[x, y] = votes.most_common(1)[0][0] + (255,)
    # quantize opaque pixels
    rgb = res.convert("RGB")
    q = rgb.quantize(ncol, method=Image.Quantize.MEDIANCUT)
    qp = q.getpalette()[:ncol * 3]; qq = q.load()
    pal = [tuple(qp[i * 3:i * 3 + 3]) for i in range(ncol)]
    for y in range(H):
        for x in range(w):
            if rp[x, y][3]: rp[x, y] = pal[qq[x, y]] + (255,)
    # remove orphans
    for y in range(H):
        for x in range(w):
            if rp[x, y][3] and not any(0 <= x + dx < w and 0 <= y + dy < H and rp[x + dx, y + dy][3]
                                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                rp[x, y] = (0, 0, 0, 0)
    if out:
        res.save(out)
        big = Image.new("RGBA", (w * 10, H * 10), (28, 26, 32, 255))
        big.alpha_composite(res.resize((w * 10, H * 10), Image.NEAREST))
        big.convert("RGB").save(out.replace(".png", "_x10.png"))
    return res

def to_text(res):
    pal = []; lines = []
    px = res.load()
    for y in range(res.height):
        s = ""
        for x in range(res.width):
            c = px[x, y]
            if not c[3]: s += "."; continue
            c = c[:3]
            if c not in pal: pal.append(c)
            s += CH[pal.index(c)]
        lines.append(s)
    return "PAL " + " ".join("%s%02x%02x%02x" % (CH[i], *c) for i, c in enumerate(pal)) + "\n" + "\n".join(lines)

if __name__ == "__main__":
    path, H = sys.argv[1], int(sys.argv[2])
    out = sys.argv[3]
    r = spritify(path, H, out=out)
    print(r.size)
    print(to_text(r))
