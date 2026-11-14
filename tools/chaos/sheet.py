"""Contact sheet of room_stretch previews (after only), 2x."""
import sys, os
from PIL import Image
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "build", "chaos_rooms")
names = sys.argv[2:]
out = sys.argv[1]
ims = []
for n in names:
    im = Image.open(os.path.join(D, n + ".png"))
    w, h = im.size
    # the after view is the lower part: find the 6px grey separator by scanning
    px = im.load()
    sep = next(y for y in range(h) if px[w - 1, y][:3] == (40, 40, 40) and px[0, y][:3] == (40, 40, 40))
    a = im.crop((0, sep + 18, w, h))
    ims.append(a.resize((a.size[0] * 2 // 3, a.size[1] * 2 // 3), Image.NEAREST))
cols = 3
W = max(i.size[0] for i in ims) + 10
rows = [ims[i:i + cols] for i in range(0, len(ims), cols)]
Hs = [max(i.size[1] for i in r) + 10 for r in rows]
sheet = Image.new("RGBA", (W * cols, sum(Hs)), (30, 30, 30, 255))
y = 0
for r, hh in zip(rows, Hs):
    for k, im in enumerate(r):
        sheet.paste(im, (k * W, y))
    y += hh
sheet.save(out)
print(sheet.size)
