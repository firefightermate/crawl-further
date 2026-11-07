"""Silver and gold slot art: pick-list pips, the custom-god idol portraits, the lock overlay,
the slot-editor kit (arrows, row marker, grid cell frames, panel corners, confirm tick), the evolve-screen header and
side brackets for custom gods, and the unlock banner.

Run from the repo root:  python3 tools/sprites/ui_slots.py
Writes PNG + JSON sheets (and *_preview.png) into art/out_ui_slots/, plus board.png (8x, every sheet and anim).

Sheets (cell, anims):
  SlotPipSilver        3 x 4   Idle 7      silver pip: a white shimmer sweeps across the facets, then rests
  SlotPipGold          5 x 4   Idle 10     gold pip (3 x 4 core, centred): a glint sweep, then a twinkle in the free right-hand column
  SlotPipSilverLocked  3 x 4   Idle 1      dull pewter pip (challenge not done)
  SlotPipGoldLocked    5 x 4   Idle 1      tarnished brass pip (challenge not done)
  ModSpellPip          3 x 4   Idle 1      azure pip: an origin that grants a spell
  ModBothPip           3 x 4   Idle 4      rose-cyan prism pip: an origin that grants a weapon AND a spell; its
                                           cyan highlight walks round the facets
  DeitySilverIdol      29 x 24 Idle 6, Locked 1   the silver custom god: a silver mask before a blue moon, on a plinth
                                                  with 3 sockets
  DeityGoldIdol        29 x 24 Idle 8, Locked 1   the gold custom god: a crowned sun mask in a ring of rays, 4 sockets
  SlotLockOverlay      29 x 24 Idle 4, Shake 4    two iron chains crossed over a brass padlock, drawn over a locked
                                                  slot's portrait
  EdArrow              5 x 7   Silver 2, Gold 2, Off 1, Lit 1   editor value arrows (point right; flip for left)
  EdMark               4 x 5   Silver 4, Gold 4                 editor row marker (pulses)
  EdCell               12 x 15 Silver 4, Gold 4, Taken 1, Slot 2, Find 5   editor grid cell frames (selected / used / edited slot / secret)
  EdCorner             7 x 7   Silver 4, Gold 4                 editor panel corner filigree (top-left; flip for others)
  EdCheck              7 x 6   Silver 2, Gold 2, Off 1          editor confirm tick
  EvoBracket           5 x 18  Silver 4, Gold 4                 evolve menu: side bracket for each monster button
  EvoHeader            55 x 11 Silver 6, Gold 6                 evolve menu: ribbon tails either side of the player's name
  UnlockBanner         128 x 24 Silver 8, Gold 8                unlock announcement banner (text drawn over it)

Light from the top-left. The idols and the lock use the god art's material renderer (jinx_v2_rigs.py); the small
menu pieces keep a dark outline (#1e1a1c, the vanilla outline) so they stand off the menu backgrounds.
"""
import json, math, os, sys
from PIL import Image

OUT = "art/out_ui_slots"
CORE_OUT = "art/core"      # every sheet but the two idols is loaded by Core


def out_dir(name):
    return OUT if name.startswith("Deity") else CORE_OUT
K = (0x1e, 0x1a, 0x1c, 255)          # vanilla outline
T = (0, 0, 0, 0)

# ------------------------------------------------------------------ palettes
SIL = {"o": K, "0": (0x2c, 0x30, 0x3a, 255), "1": (0x4a, 0x50, 0x5e, 255), "2": (0x74, 0x7c, 0x8e, 255),
       "3": (0x9e, 0xa7, 0xb8, 255), "4": (0xc8, 0xd0, 0xdc, 255), "5": (0xea, 0xef, 0xf6, 255), "W": (0xff, 0xff, 0xff, 255),
       "b": (0x8c, 0xc8, 0xff, 255), "B": (0xd8, 0xf2, 0xff, 255)}
GLD = {"o": K, "0": (0x3a, 0x22, 0x0c, 255), "1": (0x6b, 0x3f, 0x12, 255), "2": (0xa0, 0x62, 0x1a, 255),
       "3": (0xd4, 0x96, 0x28, 255), "4": (0xf2, 0xc4, 0x4a, 255), "5": (0xff, 0xe8, 0x8c, 255), "W": (0xff, 0xfa, 0xe0, 255),
       "b": (0xe0, 0x30, 0x3c, 255), "B": (0xff, 0x9a, 0x86, 255)}


def new(w, h, c=T):
    return Image.new("RGBA", (w, h), c)


def put(im, x, y, c):
    if 0 <= x < im.width and 0 <= y < im.height and c is not None:
        im.putpixel((x, y), c)


def grid(im, x0, y0, rows, pal):
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch in ".  ":
                continue
            put(im, x0 + i, y0 + j, pal[ch] if isinstance(pal, dict) else pal)


def outline(im, col=K):
    """1 px outline around every opaque pixel (4-neighbour), drawn into transparent pixels only."""
    src = im.copy(); px = src.load(); w, h = im.size
    for y in range(h):
        for x in range(w):
            if px[x, y][3] != 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < w and 0 <= yy < h and px[xx, yy][3] != 0 and px[xx, yy][:3] != col[:3]:
                    im.putpixel((x, y), col); break
    return im


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3)) + (255,)


def bright(c, k):
    return tuple(max(0, min(255, int(round(v * k)))) for v in c[:3]) + (c[3],)


def mix_white(c, t):
    return lerp(c, (255, 255, 255), t)


def desat(c, k=0.75, dark=0.55):
    g = (c[0] * 0.3 + c[1] * 0.59 + c[2] * 0.11)
    return tuple(int(round((v * (1 - k) + g * k) * dark)) for v in c[:3]) + (c[3],)


BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def save(name, frames, anims, cell, cols=8):
    """frames: list of RGBA images (cell sized); anims: list of (name, [frame indices], [durations])."""
    cw, ch = cell
    n = len(frames)
    cols = min(cols, n)
    rows = (n + cols - 1) // cols
    sheet = new(cw * cols, ch * rows)
    for i, f in enumerate(frames):
        assert f.size == (cw, ch), (name, i, f.size)
        sheet.alpha_composite(f, ((i % cols) * cw, (i // cols) * ch))
    os.makedirs(out_dir(name), exist_ok=True)
    sheet.save(os.path.join(out_dir(name), name + ".png"))
    man = {"cellW": cw, "cellH": ch, "cols": cols,
           "anims": [{"name": a, "frames": fr, "durations": du} for a, fr, du in anims]}
    json.dump(man, open(os.path.join(out_dir(name), name + ".json"), "w"))
    preview_sheet(name, frames, anims, cell)
    SHEETS.append((name, frames, anims, cell))
    return sheet


def preview_sheet(name, frames, anims, cell, scale=None):
    cw, ch = cell
    scale = scale or max(2, min(12, 160 // max(cw, ch)))
    pad = 2
    rows = len(anims)
    width = max(len(fr) for _, fr, _ in anims) * (cw + pad) + pad
    bg = new(width, rows * (ch + pad) + pad, (0x1c, 0x18, 0x1e, 255))
    for r, (_, fr, _) in enumerate(anims):
        for i, fi in enumerate(fr):
            bg.alpha_composite(frames[fi], (pad + i * (cw + pad), pad + r * (ch + pad)))
    bg.resize((bg.width * scale, bg.height * scale), Image.NEAREST).convert("RGB").save(os.path.join(out_dir(name), name + "_preview.png"))


SHEETS = []


# ================================================================== pips
PIP = ["445",
       "432",
       "321",
       "211"]


def pip_frame(pal, core_x=0, w=3, sweep=None, sparkle=None):
    im = new(w, 4)
    for y, row in enumerate(PIP):
        for x, ch in enumerate(row):
            c = pal[ch]
            if sweep is not None:
                d = x + y
                if d == sweep: c = pal["W"]
                elif d == sweep - 1 or d == sweep + 1: c = mix_white(c, 0.55)
            put(im, core_x + x, y, c)
    if sparkle:
        for (x, y, c) in sparkle:
            put(im, x, y, c)
    return im


def build_pips():
    # silver: sweep over the 6 diagonals, then rest
    fr = [pip_frame(SIL, sweep=s) for s in range(0, 6)] + [pip_frame(SIL)]
    save("SlotPipSilver", fr, [("Idle", list(range(7)), [0.06] * 6 + [1.3])], (3, 4))
    # gold (5 wide: the 3 x 4 core in the middle; the twinkle lights the 1 px gaps beside it)
    W5, Y5 = GLD["W"], GLD["5"]
    fr = [pip_frame(GLD, 1, 5, sweep=s) for s in range(0, 6)]
    fr += [pip_frame(GLD, 1, 5)]
    # the twinkle only ever lights the right-hand column: gold is the last entry of its list, so nothing sits there
    fr += [pip_frame(GLD, 1, 5, sparkle=[(4, 2, Y5)]),
           pip_frame(GLD, 1, 5, sparkle=[(4, 1, W5), (4, 2, Y5)]),
           pip_frame(GLD, 1, 5, sparkle=[(4, 0, Y5), (4, 1, Y5)])]
    save("SlotPipGold", fr, [("Idle", list(range(10)), [0.05] * 6 + [0.6, 0.08, 0.1, 0.08])], (5, 4))
    # locked: dull pewter / tarnished brass, a dark notch where the lock would be
    lpal = {k: desat(v, 0.6, 0.62) for k, v in SIL.items()}
    im = pip_frame(lpal); put(im, 1, 2, SIL["0"])
    save("SlotPipSilverLocked", [im], [("Idle", [0], [1.0])], (3, 4))
    lpal = {k: desat(v, 0.55, 0.55) for k, v in GLD.items()}
    im = pip_frame(lpal, 1, 5); put(im, 2, 2, GLD["0"])
    save("SlotPipGoldLocked", [im], [("Idle", [0], [1.0])], (5, 4))
    # spell origins: azure
    az = {"5": (0xd2, 0xf6, 0xff, 255), "4": (0x8a, 0xe2, 0xff, 255), "3": (0x3c, 0xb0, 0xe8, 255),
          "2": (0x22, 0x78, 0xc0, 255), "1": (0x16, 0x4a, 0x86, 255), "W": (255, 255, 255, 255)}
    save("ModSpellPip", [pip_frame(az)], [("Idle", [0], [1.0])], (3, 4))
    # weapon AND spell: a rose / magenta prism whose cyan highlight walks round the top facets
    pr = {"5": (0xff, 0xb4, 0xd2, 255), "4": (0xff, 0x6e, 0xa8, 255), "3": (0xd0, 0x3c, 0x96, 255),
          "2": (0x9a, 0x26, 0x86, 255), "1": (0x5a, 0x16, 0x62, 255), "W": (255, 255, 255, 255)}
    cy = (0x8c, 0xf6, 0xff, 255); cyd = (0x46, 0xc8, 0xe6, 255)
    path = [(0, 0), (1, 0), (2, 0), (2, 1)]
    fr = []
    for i in range(4):
        im = pip_frame(pr)
        x, y = path[i]; put(im, x, y, cy)
        x, y = path[(i - 1) % 4]; put(im, x, y, cyd)
        fr.append(im)
    save("ModBothPip", fr, [("Idle", [0, 1, 2, 3], [0.16, 0.12, 0.16, 0.22])], (3, 4))


# ================================================================== portraits (29 x 24)
PW, PH = 29, 24


def background(warm):
    """Vanilla-style portrait backdrop: dark frame, a dithered radial glow toward the centre."""
    if warm:
        cols = [(0x14, 0x0c, 0x0c), (0x24, 0x15, 0x14), (0x33, 0x1d, 0x19), (0x45, 0x27, 0x1d)]
    else:
        cols = [(0x0e, 0x10, 0x16), (0x19, 0x1c, 0x26), (0x23, 0x28, 0x35), (0x30, 0x37, 0x47)]
    im = new(PW, PH)
    cx, cy = 14, 10
    for y in range(PH):
        for x in range(PW):
            if x in (0, PW - 1) or y in (0, PH - 1):
                put(im, x, y, cols[0] + (255,)); continue
            d = ((x - cx) ** 2 / 196.0 + (y - cy) ** 2 / 110.0) ** 0.5
            v = max(0.0, 1.0 - d) * 3.0
            v += (BAYER[y % 4][x % 4] / 16.0 - 0.47)
            i = max(0, min(3, int(v) + 1))
            put(im, x, y, cols[i] + (255,))
    return im


# The idols and the lock are drawn with the material renderer the god art uses (jinx_v2_rigs.py): 3 tones per material
# lit from the top left, the bottom edges in the material's darkest tone, no black ring.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jinx_v2_rigs as MR  # noqa: E402

MR.RAMPS.setdefault("silv", [MR._h(c) for c in ("262a36", "4a505e", "7c8496", "aab3c4", "e6ecf4")])
MR.RAMPS.setdefault("ruby", [MR._h(c) for c in ("2a0610", "6a0c1c", "b01e2c", "e8483e", "ffa08a")])
MR.RAMPS.setdefault("moon", [MR._h(c) for c in ("0c2a4a", "1c4e8a", "4a8ad8", "8cc8ff", "e0f4ff")])
MR.SHINY.update({"silv", "ruby"})
MR.EMISSIVE.add("moon")
IO = (14, 22)     # idol origin: the plinth's bottom centre


def to_im(spr, origin=IO, base=None):
    """A resolved sprite as a cell image, laid over base (a cell image) when given."""
    im = base.copy() if base is not None else new(PW, PH)
    for (x, y), c in spr.px.items():
        put(im, origin[0] + x, origin[1] + y, tuple(c[:3]) + (255,))
    return im


def sweep(spr, mat, at, width=1.2):
    """A diagonal glint across the lit metal (tone 2 and up) of one material."""
    for k, (m, t) in spr.tones.items():
        if m == mat and t >= 2 and abs((k[0] + k[1] * 0.6) - at) < width:
            spr.px[k] = MR.RAMPS[mat][4]
    return spr


def plinth(r, n, mat, gem, w):
    """The idol's plinth: a lit slab with n sockets set in its face, one per slot it fills."""
    MR.box3(r, -w / 2.0, 0.0, w, 4.0, 1.6, mat, 0.0)
    r.line(-w / 2.0, -4.0, w / 2.0 - 1, -4.0, mat, 0.05, tone=4)
    step = w / n
    for i in range(n):
        cx = int(round(-w / 2.0 + step * (i + 0.5)))
        r.dots([(cx - 1, -2), (cx, -2), (cx - 1, -1), (cx, -1)], mat, 0, 0.1)
        r.dot(cx - 1, -2, gem, 4, 0.2)
        r.dot(cx, -1, gem, 2, 0.2)


def silver_idol(sweep_at=None, eye=1.0, locked=False):
    """The silver custom god: a calm silver mask with a three-point crown before a blue moon, on a plinth with three
    sockets."""
    r = MR.Rig()
    r.ell(0.0, -12.5, 10.0, 9.0, "moon", -2.0, flat=1)                          # a blue moon behind the mask
    for i in range(13):                                                          # its lit rim, top left
        a = math.radians(150 + i * 10)
        r.dot(9.6 * math.cos(a), -12.5 + 8.6 * math.sin(a), "moon", 2, -1.9)
    for (x, y) in ((-7.0, -9.0), (6.0, -16.0), (7.5, -8.0)):                     # its seas
        r.ell(x, y, 1.2, 0.9, "moon", -1.95, flat=0)
    for x, h in ((-4.0, 3.0), (0.0, 4.6), (4.0, 3.0)):   # crown points
        r.poly([(x - 1.6, -17.4), (x + 1.6, -17.4), (x, -17.4 - h)], "silv", 0.4, normal=(-0.2, -0.4, 0.9))
        r.dot(x, -17.0 - h * 0.5, "moon", 3, 0.5)
    r.ell(0.0, -12.0, 6.2, 6.8, "silv", 1.0, bias=0.3)
    r.ell(0.0, -16.6, 6.0, 1.3, "silv", 1.1, bias=0.2)
    for sx in (-1, 1):
        r.poly([(sx * 1.0, -12.8), (sx * 4.4, -13.4), (sx * 3.6, -11.6), (sx * 1.6, -11.8)], "silv", 1.1, flat=0)
        r.dot(sx * 2.6, -12.4, "moon", 4 if eye > 0.8 else 2, 1.2)
    r.line(0.0, -12.0, 0.0, -9.0, "silv", 1.1, tone=1)
    r.polyline([(-2.0, -7.6), (0.0, -7.0), (2.0, -7.6)], "silv", 1.1, tone=1)
    r.tube([(-3.0, -5.4), (3.0, -5.4)], [0.9, 0.9], "silv", 0.6, bias=0.2)       # neck ring
    plinth(r, 3, "silv", "moon", 20.0)
    spr = r.resolve(floor=False, cast=False)
    if sweep_at is not None: sweep(spr, "silv", sweep_at)
    im = to_im(spr, base=background(False))
    return darken(im) if locked else im


def gold_idol(glint=None, phase=0, sparkles=(), locked=False):
    """The gold custom god: a sun mask with a crown of five points and rays round it, ruby eyes, on a plinth with four
    sockets."""
    r = MR.Rig()
    for i in range(12):                                   # rays: every other one long, the lit ones swap each frame
        a = math.radians(i * 30 - 90)
        ln = 10.5 if i % 2 == 0 else 8.6
        x0, y0 = 6.0 * math.cos(a), -12.0 + 5.6 * math.sin(a)
        x1, y1 = ln * math.cos(a), -12.0 + ln * 0.85 * math.sin(a)
        if y1 > -5.5: continue
        r.line(x0, y0, x1, y1, "gold", -1.0, tone=4 if (i + phase) % 2 == 0 else 2)
    for i, x in enumerate((-4.4, -2.2, 0.0, 2.2, 4.4)):
        h = 2.2 + (1.4 if i == 2 else 0.6 if i in (1, 3) else 0.0)
        r.poly([(x - 1.1, -16.8), (x + 1.1, -16.8), (x, -16.8 - h)], "gold", 0.4, normal=(-0.2, -0.4, 0.9))
    r.ell(0.0, -16.6, 5.6, 1.3, "gold", 1.1, bias=0.25)
    r.dot(0.0, -16.6, "ruby", 3, 1.15)
    r.ell(0.0, -11.6, 6.4, 6.0, "gold", 1.0, bias=0.45)
    for sx in (-1, 1):
        r.ell(sx * 2.6, -12.4, 1.5, 1.0, "gold", 1.1, flat=0)
        r.dot(sx * 2.6, -12.4, "ruby", 3, 1.2)
        r.ell(sx * 4.2, -9.6, 1.0, 0.7, "gold", 1.05, flat=4)                 # round cheeks catch the light
    r.polyline([(-2.4, -8.2), (-1.0, -7.4), (1.0, -7.4), (2.4, -8.2)], "gold", 1.1, tone=0)
    r.tube([(-3.0, -5.4), (3.0, -5.4)], [0.9, 0.9], "gold", 0.6, bias=0.2)
    plinth(r, 4, "gold", "ruby", 24.0)
    spr = r.resolve(floor=False, cast=False)
    if glint is not None: sweep(spr, "gold", glint)
    im = to_im(spr, base=background(True))
    for (x, y, big) in sparkles:
        star(im, x, y, big, GLD["W"], GLD["5"])
    return darken(im) if locked else im


def star(im, x, y, big, c, c2):
    put(im, x, y, c)
    if big:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            put(im, x + dx, y + dy, c2)


def darken(im):
    out = im.copy(); px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            c = px[x, y]
            if c[3]: px[x, y] = desat(c, 0.7, 0.5)
    return out


def build_portraits():
    # silver: shimmer sweep across the mask, eyes breathe
    fr = [silver_idol(sweep_at=g, eye=1.0) for g in (-20, -13, -6, 1, 8)] + [silver_idol(eye=0.6)]
    fr.append(silver_idol(locked=True))
    save("DeitySilverIdol", fr, [("Idle", [0, 1, 2, 3, 4, 5], [0.07, 0.07, 0.07, 0.07, 0.07, 0.9]),
                                 ("Locked", [6], [1.0])], (PW, PH))
    # gold: glint across the crown, rays twinkle, sparkles pop around the mask
    fr = [gold_idol(glint=g, phase=i % 2) for i, g in enumerate((-20, -13, -6, 1, 8))]
    fr += [gold_idol(phase=1, sparkles=[(4, 4, True)]), gold_idol(phase=0, sparkles=[(24, 13, True), (4, 4, False)]),
           gold_idol(phase=1, sparkles=[(24, 13, False)])]
    fr.append(gold_idol(locked=True))
    save("DeityGoldIdol", fr, [("Idle", list(range(8)), [0.06, 0.06, 0.06, 0.06, 0.06, 0.22, 0.2, 0.5]),
                               ("Locked", [8], [1.0])], (PW, PH))


# ------------------------------------------------------------------ lock overlay
MR.RAMPS.setdefault("lockb", [MR._h(c) for c in ("2a1a10", "5e3a18", "9a6424", "d29a3a", "f6d47a")])
MR.SHINY.add("lockb")


def lock_overlay(glint=None, dx=0, dy=0, tilt=0.0):
    """Two iron chains crossed over the slot and a brass padlock where they meet. glint: which link of each chain
    catches the light (0-3); dx/dy/tilt: the padlock shaking."""
    r = MR.Rig()
    for (x0, y0, x1, y1, k) in ((-13.0, -21.0, 13.0, 1.0, 0), (13.0, -21.0, -13.0, 1.0, 1)):
        n = 14
        for i in range(n + 1):
            t = i / float(n)
            x, y = MR.lerp(x0, x1, t), MR.lerp(y0, y1, t)
            lit = glint is not None and (i // 2 + k) % 4 == glint
            z = 0.5 + (0.1 if k else 0.0) + i * 0.001
            if i % 2 == 0:                     # a link seen flat: an oval ring
                r.ell(x, y, 1.6, 1.4, "steel", z, bias=0.45 if lit else 0.0)
                r.dot(x, y, "steel", 0, z + 0.01)
            else:                              # the next link edge-on: a short bar across the chain
                ang = math.atan2(y1 - y0, x1 - x0) + math.pi / 2
                r.line(x - math.cos(ang), y - math.sin(ang), x + math.cos(ang), y + math.sin(ang), "steel", z + 0.02,
                       tone=4 if lit else 2)
    cx, cy = dx, -10.0 + dy
    r.tube([(cx - 3.2, cy - 1.0), (cx - 3.2, cy - 4.6), (cx, cy - 7.0), (cx + 3.2, cy - 4.6), (cx + 3.2, cy - 1.0)],
           [1.1], "steel", 2.0, bias=0.1)                                   # the shackle
    MR.box3(r, cx - 5.2, cy + 7.0, 10.4, 7.6, 1.6, "lockb", 2.5, ang=tilt)
    r.line(cx - 4.8, cy - 0.4, cx + 4.6, cy - 0.4, "lockb", 2.55, tone=4)
    for rx_ in (-3.8, 3.8): r.dot(cx + rx_, cy + 5.4, "lockb", 4, 2.55)     # rivets
    r.ell(cx, cy + 2.6, 1.0, 1.0, "lockb", 2.6, flat=0)                    # keyhole
    r.dot(cx, cy + 3.8, "lockb", 0, 2.6); r.dot(cx, cy + 4.6, "lockb", 0, 2.6)
    if glint == 0:
        r.dot(cx - 4.0, cy + 0.4, "white", 4, 3.0)
    return to_im(r.resolve(floor=False, cast=False), origin=(14, 22))


def build_lock():
    fr = [lock_overlay(glint=g) for g in range(4)]
    fr += [lock_overlay(dx=-1, tilt=-8.0), lock_overlay(dx=1, tilt=8.0), lock_overlay(dx=-1, dy=-1, tilt=-4.0), lock_overlay()]
    save("SlotLockOverlay", fr, [("Idle", [0, 1, 2, 3], [0.5, 0.12, 0.12, 0.12]),
                                 ("Shake", [4, 5, 6, 7], [0.04, 0.04, 0.04, 0.06])], (PW, PH))


# ================================================================== editor kit
def tier_pals():
    return (("Silver", SIL), ("Gold", GLD))


ARROW = ["o....",
         "4o...",
         "45o..",
         "4553o",
         "432o.",
         "32o..",
         "oo..."]


def build_editor():
    frames, anims = [], []
    for nm, pal in tier_pals():
        a = new(5, 7); grid(a, 0, 0, ARROW, pal)
        b = new(5, 7); grid(b, 1, 0, [r[:4] for r in ARROW], pal)   # nudged 1 px right (bob)
        frames += [a, b]; anims.append((nm, [len(frames) - 2, len(frames) - 1], [0.4, 0.25]))
    off = {k: desat(v, 0.8, 0.6) for k, v in SIL.items()}; off["o"] = K
    a = new(5, 7); grid(a, 0, 0, ARROW, off); frames.append(a); anims.append(("Off", [len(frames) - 1], [1.0]))
    lit = {k: (mix_white(v, 0.6) if k != "o" else K) for k, v in SIL.items()}
    a = new(5, 7); grid(a, 0, 0, ARROW, lit); frames.append(a); anims.append(("Lit", [len(frames) - 1], [1.0]))
    save("EdArrow", frames, anims, (5, 7))

    # row marker: a small faceted diamond that pulses
    MARK = [".o..", "o5o.", "o43o", "o2o.", ".o.."]
    frames, anims = [], []
    for nm, pal in tier_pals():
        idx = []
        for k in (0.0, 0.35, 0.7, 0.35):
            p = {kk: (mix_white(v, k) if kk not in "o" else K) for kk, v in pal.items()}
            im = new(4, 5); grid(im, 0, 0, MARK, p); frames.append(im); idx.append(len(frames) - 1)
        anims.append((nm, idx, [0.16, 0.1, 0.16, 0.1]))
    save("EdMark", frames, anims, (4, 5))

    # grid cell frames (12 x 15: one px around the god-select's 10 x 12.8 monster box at its 0.9 scale, plus outline)
    frames, anims = [], []
    for nm, pal in tier_pals():
        idx = []
        for f in range(4):
            im = new(12, 15)
            for x in range(12):
                for y in (0, 14):
                    put(im, x, y, pal["2"])
            for y in range(15):
                for x in (0, 11):
                    put(im, x, y, pal["2"])
            # bright corners, a light that runs round the frame
            for (x, y) in ((0, 0), (11, 0), (0, 14), (11, 14)):
                put(im, x, y, pal["5"])
            per = [(x, 0) for x in range(12)] + [(11, y) for y in range(1, 15)] + \
                  [(x, 14) for x in range(10, -1, -1)] + [(0, y) for y in range(13, 0, -1)]
            n = len(per)
            for k in range(3):
                x, y = per[(f * n // 4 + k) % n]
                put(im, x, y, pal["W"] if k == 1 else pal["4"])
            frames.append(im); idx.append(len(frames) - 1)
        anims.append((nm, idx, [0.12] * 4))
    # taken: a dim frame with small corner ticks (the monster is already in another slot)
    im = new(12, 15)
    for (x, y) in ((0, 0), (1, 0), (0, 1), (11, 0), (10, 0), (11, 1), (0, 14), (1, 14), (0, 13), (11, 14), (10, 14), (11, 13)):
        put(im, x, y, (0x6e, 0x60, 0x58, 255))
    for i in range(4):
        put(im, 4 + i, 5 + i, (0x8e, 0x3a, 0x30, 255)); put(im, 7 - i, 5 + i, (0x8e, 0x3a, 0x30, 255))
    frames.append(im); anims.append(("Taken", [len(frames) - 1], [1.0]))
    # slot: the slot being edited in the slot strip (a dashed frame that crawls)
    idx = []
    for f in range(2):
        im = new(12, 15)
        per = [(x, 0) for x in range(12)] + [(11, y) for y in range(1, 15)] + \
              [(x, 14) for x in range(10, -1, -1)] + [(0, y) for y in range(13, 0, -1)]
        for i, (x, y) in enumerate(per):
            if (i + f) % 3 != 2:
                put(im, x, y, (0xea, 0xd8, 0xb4, 255))
        frames.append(im); idx.append(len(frames) - 1)
    anims.append(("Slot", idx, [0.18, 0.18]))
    # find: the gold idol's secret last cell. Small gold corner brackets and, now and then, a glint that blooms on the
    # top-right corner (a treasure catching the light); quiet most of the time, so it hides in plain sight
    idx = []
    BR = ((0, 0), (1, 0), (0, 1), (11, 0), (10, 0), (11, 1), (0, 14), (1, 14), (0, 13), (11, 14), (10, 14), (11, 13))
    for f in range(5):
        im = new(12, 15)
        for (x, y) in BR: put(im, x, y, GLD["4"])
        for (x, y) in ((0, 0), (11, 0), (0, 14), (11, 14)): put(im, x, y, GLD["5"])
        if f == 1: put(im, 10, 1, GLD["W"])
        if f == 2:
            for (x, y) in ((10, 1), (9, 1), (11, 1), (10, 0), (10, 2)): put(im, x, y, GLD["5"])
            put(im, 10, 1, GLD["W"])
        if f == 3: put(im, 10, 1, GLD["5"])
        frames.append(im); idx.append(len(frames) - 1)
    anims.append(("Find", idx, [1.4, 0.08, 0.12, 0.08, 0.6]))
    save("EdCell", frames, anims, (12, 15))

    # panel corners: an L of filigree with a gem at the bend
    CORNER = ["oooooo.",
              "o5443o.",
              "o4bo2o.",
              "o4oo...",
              "o3o....",
              "oo.....",
              "......."]
    frames, anims = [], []
    for nm, pal in tier_pals():
        idx = []
        for f in range(4):
            p = dict(pal)
            if f == 1: p["b"] = pal["B"]; p["5"] = pal["W"]
            if f == 2: p["4"] = pal["5"]
            im = new(7, 7); grid(im, 0, 0, CORNER, p)
            frames.append(im); idx.append(len(frames) - 1)
        anims.append((nm, idx, [0.9, 0.08, 0.08, 0.08]))
    save("EdCorner", frames, anims, (7, 7))

    # confirm tick
    TICK = ["......o",
            ".....o5",
            "o...o4o",
            "5o.o4o.",
            "o42o3o.".replace("o3o.", "3o.."),
            ".oo2o.."]
    TICK = [".....oo",
            "....o5o",
            "oo.o4o.",
            "o4o43o.",
            ".o432o.",
            "..ooo.."]
    frames, anims = [], []
    for nm, pal in tier_pals():
        a = new(7, 6); grid(a, 0, 0, TICK, pal)
        b = new(7, 6); grid(b, 0, 0, TICK, {k: (mix_white(v, 0.5) if k != "o" else K) for k, v in pal.items()})
        frames += [a, b]; anims.append((nm, [len(frames) - 2, len(frames) - 1], [0.5, 0.15]))
    off = {k: desat(v, 0.8, 0.55) for k, v in SIL.items()}; off["o"] = K
    a = new(7, 6); grid(a, 0, 0, TICK, off); frames.append(a); anims.append(("Off", [len(frames) - 1], [1.0]))
    save("EdCheck", frames, anims, (7, 6))


# ================================================================== evolve screen
def rig_im(r, cell, origin, mat=None, glint=None, slope=0.5, width=1.2):
    """Resolve a rig into a cell image (origin = where rig (0, 0) lands); an optional glint across one material."""
    spr = r.resolve(floor=False, cast=False)
    if glint is not None:
        for k, (m, t) in spr.tones.items():
            if m == mat and t >= 2 and abs(k[0] + k[1] * slope - glint) < width:
                spr.px[k] = MR.RAMPS[mat][4]
    im = new(*cell)
    for (x, y), c in spr.px.items():
        put(im, origin[0] + x, origin[1] + y, tuple(c[:3]) + (255,))
    return im


def tier_mats(nm):
    return ("silv", "moon") if nm == "Silver" else ("gold", "ruby")


def build_evolve():
    # side bracket for one 18 px monster button: a rolled rail with curled end caps and a gem in the middle
    frames, anims = [], []
    for nm, pal in tier_pals():
        mat, gem = tier_mats(nm)
        idx = []
        for f in range(4):
            r = MR.Rig()
            r.tube([(1.5, 1.5), (1.5, 15.5)], [1.0], mat, 1.0, bias=0.1)
            for y, d in ((0.6, 1), (16.4, -1)):
                r.tube([(1.5, y), (3.0, y), (3.6, y + d)], [0.9, 0.7, 0.5], mat, 1.1, bias=0.2)
            r.ell(2.0, 8.0, 1.6, 2.2, mat, 1.2, bias=0.1)
            r.ell(2.0, 8.0, 0.9, 1.3, gem, 1.3, bias=(0.5 if f == 1 else 0.25 if f == 2 else 0.0))
            frames.append(rig_im(r, (5, 18), (0, 0), mat, glint=(None, 2.0, 6.0, 10.0)[f] if f else None, slope=-0.3))
            idx.append(len(frames) - 1)
        anims.append((nm, idx, [0.8, 0.07, 0.07, 0.12]))
    save("EvoBracket", frames, anims, (5, 18))

    # header: two ribbon tails flanking the player's name (55 x 11, the panel's width). The middle 29 px stay empty so
    # the name (three letters in the evolve menu's large font) is never drawn over: full contrast for every player colour.
    W, GAP0, GAP1 = 55, 13, 42
    frames, anims = [], []
    for nm, pal in tier_pals():
        mat, gem = tier_mats(nm)
        idx = []
        for f in range(6):
            r = MR.Rig()
            for sx, inner, outer in ((-1, GAP0 - 2, 0.5), (1, GAP1 + 1, W - 1.5)):
                # the ribbon: a band with a swallow-tail notch at the outer end, folded under where it meets the cap
                r.poly([(inner, 1.0), (outer, 1.0), (outer - sx * 4.0, 5.0), (outer, 9.0), (inner, 9.0)], mat, 0.5,
                       normal=(0.0, -0.4, 1.0))
                r.line(inner, 1.0, outer, 1.0, mat, 0.55, tone=4)
                r.line(inner, 2.0, outer - sx * 1, 2.0, mat, 0.55, tone=3)
                r.line(inner, 9.0, outer - sx * 0.5, 9.0, mat, 0.55, tone=1)
                r.line(inner + sx * 2, 5.0, outer - sx * 5.0, 5.0, mat, 0.55, tone=1)          # a stitched seam
                r.ell(inner, 5.0, 1.7, 4.4, mat, 1.0, bias=0.15)                                # end cap
                r.ell(inner, 5.0, 0.9, 1.6, gem, 1.1, bias=0.2)
            frames.append(rig_im(r, (W, 11), (0, 0), mat, glint=(2 + f * 13) if f < 5 else None, slope=0.5, width=1.0))
            idx.append(len(frames) - 1)
        anims.append((nm, idx, [0.06] * 5 + [1.6]))
    save("EvoHeader", frames, anims, (W, 11), cols=6)


def banner_frame(nm, pal, f):
    """One frame of the unlock banner: a dark plate for the text inside a rolled metal rim, round end caps with the
    tier's gem, and studs at the corners. f 0-5: a glint runs along the rim; 6: the end gems flare; 7: rest."""
    W, H = 128, 24
    mat, gem = ("silv", "moon") if nm == "Silver" else ("gold", "ruby")
    r = MR.Rig()
    r.tube([(4.0, 2.5), (W - 5.0, 2.5)], [1.4], mat, 1.0, bias=0.1)           # the rim
    r.tube([(4.0, H - 3.5), (W - 5.0, H - 3.5)], [1.4], mat, 1.0, bias=-0.1)
    for x in (3.5, W - 4.5):
        r.tube([(x, 3.5), (x, H - 4.5)], [1.2], mat, 1.05)
    for x in (3.0, W - 4.0):                                                  # end caps with the gem
        r.ell(x, H / 2.0 - 0.5, 3.0, 5.2, mat, 1.2, bias=0.05)
        r.ell(x, H / 2.0 - 0.5, 1.4, 2.2, gem, 1.3, bias=0.4 if f == 6 else 0.1)
    for (x, y) in ((9.0, 2.5), (W - 10.0, 2.5), (9.0, H - 3.5), (W - 10.0, H - 3.5), (W / 2.0 - 0.5, 2.5)):
        r.ell(x, y, 1.3, 1.3, mat, 1.4, bias=0.3)                            # studs
    spr = r.resolve(floor=False, cast=False)
    if f < 6:
        g = 6 + f * 24
        for k, (m, t) in spr.tones.items():
            if m == mat and t >= 2 and abs(k[0] - g + k[1] * 0.5) < 2.0:
                spr.px[k] = MR.RAMPS[mat][4]
    im = new(W, H)
    plate = pal["0"]
    for y in range(4, H - 4):                                                 # the plate: flat, with a faint engraved hatch
        for x in range(5, W - 5):
            c = plate
            if (x + 2 * y) % 9 == 0 and 6 <= y <= H - 7: c = lerp(pal["0"], pal["1"], 0.45)
            if y == 4: c = lerp(pal["0"], pal["1"], 0.7)
            put(im, x, y, c)
    for (x, y), c in spr.px.items():
        put(im, x, y, tuple(c[:3]) + (255,))
    if f == 6:
        star(im, 3, 11, True, pal["W"], pal["5"]); star(im, W - 4, 11, True, pal["W"], pal["5"])
    return im


def build_banner():
    """128 x 24: room for the slot name (CrawlMedium) over the challenge line (thin font, up to ~38 characters)."""
    frames, anims = [], []
    for nm, pal in tier_pals():
        idx = []
        for f in range(8):
            frames.append(banner_frame(nm, pal, f)); idx.append(len(frames) - 1)
        anims.append((nm, idx, [0.05] * 6 + [0.12, 0.9]))
    save("UnlockBanner", frames, anims, (128, 24), cols=4)


# ================================================================== board
def board():
    scale = 8
    pad = 4
    tiles = []
    for name, frames, anims, cell in SHEETS:
        for an, fr, _ in anims:
            row = new((cell[0] + pad) * len(fr) + pad, cell[1] + 2 * pad, (0x1c, 0x18, 0x1e, 255))
            for i, fi in enumerate(fr):
                row.alpha_composite(frames[fi], (pad + i * (cell[0] + pad), pad))
            tiles.append((name + " " + an, row))
    W = max(t.width for _, t in tiles) * scale
    H = sum(t.height * scale + 14 for _, t in tiles)
    from PIL import ImageDraw
    b = Image.new("RGB", (W, H), (0x10, 0x0e, 0x12))
    d = ImageDraw.Draw(b)
    y = 0
    for label, t in tiles:
        d.text((4, y), label, fill=(220, 210, 190))
        y += 12
        b.paste(t.resize((t.width * scale, t.height * scale), Image.NEAREST), (0, y))
        y += t.height * scale + 2
    b.save(os.path.join(OUT, "board.png"))


def main():
    os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    build_pips()
    build_portraits()
    build_lock()
    build_editor()
    build_evolve()
    build_banner()
    board()
    print("ui_slots: %d sheets -> %s" % (len(SHEETS), OUT))


if __name__ == "__main__":
    main()
