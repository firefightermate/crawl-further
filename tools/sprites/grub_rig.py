"""Tallow Grub: segmented wax maggot drawn as a chain of shaded segments along a spine.
Moves: Wax Spit (lobbed glob that becomes a puddle), Melt (sink into wax, resurface elsewhere)."""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import scalekit as SK
from anim import Spr, pack, preview
from rig import Part

FLAMES = [Part(".O\nOY\noY", (0, 3)), Part("O.\nOY\noY", (0, 3)), Part(".O\nYO\nYo", (0, 3)), Part("O\nY\no", (0, 3))]


def seg(px, cx, cy, rx, ry, dark=False):
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d > 1: continue
            if y > cy + ry * 0.45: c = 'h' if d > 0.5 else 'w'
            elif d > 0.72: c = 'w'
            elif y < cy - ry * 0.3 and x < cx + rx * 0.2: c = 'X'
            else: c = 'W'
            if dark and c in 'WX': c = 'w'
            px[(x, y)] = c


def grub(t=0.0, stretch=1.0, lift=0.0, head_up=0.0, mouth=0, flatten=1.0, flame_phase=0, sink=0.0, swell=0.0, fade=False):
    """t: wave phase (0..1); stretch: body length factor; lift: arch amount (inchworm);
    head_up: px to raise head; mouth: 0 closed, 1 open, 2 wide; flatten: vertical scale; sink: 0..1 into ground."""
    px = {}
    K = SK.cur()   # design scale (v0.7): segments / head / wicks are placed at K, then rasterised
    n = 5
    radii = [3.0, 3.4, 3.6, 3.4, 3.2]
    xs = []
    x = -9.0 * stretch
    for i in range(n):
        xs.append(x)
        x += 4.2 * stretch
    for i in range(n):
        arch = math.sin(math.pi * i / (n - 1)) * lift
        wave = math.sin(2 * math.pi * (t + i * 0.18)) * 0.6
        cy = -radii[i] * flatten - arch + wave * 0.5 - (head_up * i / (n - 1) if i > 2 else 0)
        rx = radii[i] * 0.95 + swell * (1 if i == n - 1 else 0.3)
        ry = radii[i] * flatten + swell * (0.8 if i == n - 1 else 0.2)
        seg(px, xs[i] * K, (cy + sink * ry * 2) * K, rx * K, ry * K, dark=(i % 2 == 1))
    # head: mouth ring + teeth + eyes on the last segment
    hx, hy = xs[-1] + radii[-1] * 0.9, -radii[-1] * flatten - head_up + sink * radii[-1] * 2
    hx, hy = hx * K, hy * K
    for dy in range(-1, 2):
        px[(int(hx), int(hy + dy))] = 'k'
    if mouth >= 1:
        px[(int(hx) + 1, int(hy))] = 'K'; px[(int(hx), int(hy))] = 'K'
        px[(int(hx) + 1, int(hy) - 1)] = 'X'; px[(int(hx) + 1, int(hy) + 1)] = 'X'
    if mouth == 2:
        px[(int(hx) + 2, int(hy) - 1)] = 'X'; px[(int(hx) + 2, int(hy) + 1)] = 'X'; px[(int(hx) + 1, int(hy))] = 'K'
    if not fade:
        px[(int(hx) - 1, int(hy) - 2)] = 'R'
        px[(int(hx) - 2, int(hy) - 2)] = 'r'
    # wicks with flames on segments 1..3
    for k, i in enumerate((1, 2, 3)):
        arch = math.sin(math.pi * i / (n - 1)) * lift
        top = (-radii[i] * flatten * 2 - arch + sink * radii[i] * 2) * K
        wx = int(round(xs[i] * K))
        if top + 1 > 0: continue
        px[(wx, int(top))] = 'k'
        if not fade:
            for (fx, fy), c in FLAMES[(flame_phase + k) % 4].px.items():
                px[(wx + fx, int(top) + fy)] = c
        else:
            px[(wx, int(top) - 1)] = 's'
    # clip anything below the ground line when sinking
    px = {k: v for k, v in px.items() if k[1] <= 0}
    return Spr(px)


def puddle(w=10, h=3.2):
    w, h = w * SK.cur(), h * SK.cur()
    px = {}
    for y in range(-4, 1):
        for x in range(-int(w) - 1, int(w) + 2):
            d = (x / w) ** 2 + ((y + 1.5) / h) ** 2
            if d <= 1: px[(x, y)] = 'h' if d > 0.6 else 'w' if y > -2 else 'W'
    return px


def build(outdir):
    idle = [grub(t=i / 4.0, swell=(0.3 if i in (1, 2) else 0), flame_phase=i) for i in range(4)]
    # v0.8: the inchworm never lies flat mid-stride (run f0 used to be Idle f0)
    run = [grub(t=i / 6.0, stretch=[1.08, 0.9, 0.8, 0.85, 0.95, 1.05][i], lift=[0.6, 1.5, 3, 2, 1, 0.4][i], flame_phase=i) for i in range(6)]
    spit = [
        grub(head_up=1, swell=0.4, flame_phase=0),
        grub(head_up=3, swell=0.9, stretch=0.9, flame_phase=1),
        grub(head_up=4, swell=1.2, stretch=0.85, mouth=1, flame_phase=2),
        grub(head_up=1, swell=0.2, stretch=1.1, mouth=2, flame_phase=3),
        grub(head_up=0, swell=0, stretch=1.05, mouth=1, flame_phase=0),
        grub(flame_phase=1),
    ]
    melt = []
    for i in range(6):
        k = (i + 1) / 6.0
        s = grub(sink=min(1.0, k * 1.1), flatten=1 - 0.4 * k, flame_phase=i, fade=(i > 3))
        px = dict(puddle(6 + 5 * k, 1.5 + 2 * k)); px.update(s.px)
        melt.append(Spr(px))
    rise = []
    for i in range(5):
        k = 1 - (i + 1) / 5.0
        s = grub(sink=k, flatten=1 - 0.4 * k, flame_phase=i, fade=(i == 0), head_up=(1.5 if i == 4 else 0), swell=(0.5 if i == 4 else 0))
        px = dict(puddle(6 + 5 * k, 1.5 + 2 * k)) if k > 0.1 else {}
        px.update(s.px)
        rise.append(Spr(px))
    # v0.8: the held frame under the floor is its own picture (the puddle bubbling), not a repeat of melt[-1]
    bub = dict(puddle(11, 3.5)); bub.update({(-3, -3): 'X', (-3, -4): 'W', (2, -2): 'X', (4, -3): 'W', (5, -2): 'h', (0, -1): 'h'})
    bubbling = Spr(bub)
    death = [grub(swell=0.6, mouth=2, flame_phase=0), grub(flatten=0.75, mouth=2, flame_phase=2),
             grub(flatten=0.5, fade=True), Spr(dict(puddle(11, 3.4)))]
    dead = [death[-1].over(Spr({(0, -2): 'r', (1, -2): 'R'}))]
    knock = [grub(head_up=-1, stretch=0.85, swell=0.5, mouth=2, flame_phase=3)]
    anims = [
        ("Idle", idle, [0.18] * 4), ("Run", run, [0.09] * 6), ("Dead", dead, [0.2]),
        ("Death", death, [0.08, 0.1, 0.14, 0.3]), ("Statue", [idle[0].stone()], [0.2]),
        ("Knockback", knock, [0.2]), ("Portrait", [idle[0]], [0.2]),
        ("Spit", spit, [0.1, 0.1, 0.12, 0.06, 0.1, 0.12]),
        ("Melt", melt, [0.07] * 6), ("Rise", rise, [0.07] * 5),
        ("MeltRise", melt + [bubbling] + rise, [0.07] * 5 + [0.12, 0.25] + [0.08] * 5),
    ]
    img, man = pack("TallowGrub", anims, cell_w=40, cell_h=24, feet=(20, 22), outdir=outdir)
    preview(img, man, os.path.join(outdir, "TallowGrub_preview.png"), scale=6)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "art/out"))
