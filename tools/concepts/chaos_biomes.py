"""Concept art for Crawl Chaos's bigger floors: one room mock-up per new biome, drawn at the game's own pixel scale
(a 256 x 144 screen; vanilla rooms are up to about 242 x 129, chaos arenas run past one screen) in its muted palette,
plus a floor-plan sketch comparing a vanilla floor with a chaos floor.

    python3 tools/concepts/chaos_biomes.py <outdir>

Concepts only: nothing here ships with the mod.
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 256, 144
SCALE = 4


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


class Canvas:
    def __init__(self, w=W, h=H, bg=(14, 12, 16)):
        self.im = Image.new("RGB", (w, h), bg)
        self.px = self.im.load()
        self.w, self.h = w, h

    def put(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[x, y] = c

    def get(self, x, y):
        return self.px[int(x), int(y)]

    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1)):
            for x in range(int(x0), int(x1)):
                self.put(x, y, c)

    def ell(self, cx, cy, rx, ry, c, edge=None):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                d = ((x - cx) / max(rx, 0.1)) ** 2 + ((y - cy) / max(ry, 0.1)) ** 2
                if d <= 1.0:
                    self.put(x, y, edge if edge and d > 0.72 else c)

    def line(self, x0, y0, x1, y1, c):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / max(1, n)
            self.put(round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), c)

    def glow(self, cx, cy, r, c, strength=0.5):
        for y in range(int(cy - r), int(cy + r) + 1):
            for x in range(int(cx - r), int(cx + r) + 1):
                if not (0 <= x < self.w and 0 <= y < self.h): continue
                d = math.hypot(x - cx, (y - cy) * 1.6) / r
                if d < 1:
                    self.px[x, y] = mix(self.px[x, y], c, strength * (1 - d) ** 2)

    def vignette(self, k=0.55):
        for y in range(self.h):
            for x in range(self.w):
                d = math.hypot((x - self.w / 2) / (self.w / 2), (y - self.h / 2) / (self.h / 2))
                f = 1 - k * max(0, d - 0.45) ** 1.5
                self.px[x, y] = shade(self.px[x, y], f)


# ------------------------------------------------------------------ shared room pieces (Crawl's 3/4 view)
def floor_slabs(cv, x0, y0, x1, y1, base, seed, slab=(38, 22), crack=0.25, edge_k=0.78):
    rnd = random.Random(seed)
    for y in range(y0, y1):
        row = (y - y0) // slab[1]
        off = (row % 2) * slab[0] // 2
        for x in range(x0, x1):
            sx = (x - x0 + off) % slab[0]; sy = (y - y0) % slab[1]
            n = rnd.uniform(-0.05, 0.05) + 0.05 * math.sin(x * 0.21 + y * 0.13) * math.sin(y * 0.3)
            c = shade(base, 1 + n)
            if sx == 0 or sy == 0: c = shade(base, edge_k)
            elif sy == 1 or sx == 1: c = shade(base, 1.07)
            cv.put(x, y, c)
    for _ in range(int((x1 - x0) * (y1 - y0) / 900 * crack)):
        x, y = rnd.randrange(x0, x1), rnd.randrange(y0, y1)
        for i in range(rnd.randint(3, 9)):
            cv.put(x, y, shade(base, 0.7)); x += rnd.choice((-1, 0, 1)); y += rnd.choice((0, 1))


def walls(cv, x0, y0, x1, y1, face, top, rim, face_h=26, motif=None):
    """Back wall face along the top, rims down the sides and along the bottom (the game's look)."""
    cv.rect(x0 - 6, y0 - face_h - 6, x1 + 6, y0 - face_h, rim)
    for y in range(y0 - face_h, y0):
        t = (y - (y0 - face_h)) / face_h
        cv.rect(x0, y, x1, y + 1, shade(face, 0.75 + 0.35 * (1 - t)))
    cv.rect(x0, y0 - face_h, x1, y0 - face_h + 2, top)
    cv.rect(x0, y0 - 1, x1, y0, shade(face, 0.45))
    if motif: motif(cv, x0, y0 - face_h, x1, y0)
    cv.rect(x0 - 6, y0 - face_h, x0, y1 + 6, rim); cv.rect(x1, y0 - face_h, x1 + 6, y1 + 6, rim)
    cv.rect(x0, y1, x1, y1 + 6, rim)
    cv.rect(x0 - 1, y0, x0, y1, top); cv.rect(x1, y0, x1 + 1, y1, top); cv.rect(x0, y1 - 1, x1, y1, shade(top, 0.8))


def door(cv, x, y, w, c):
    cv.rect(x - w // 2, y - 1, x + w // 2, y + 7, c)


def figure(cv, x, y, body, head=(200, 180, 150), big=1.0):
    """A small hero-sized figure for scale: cloak, head, a sword line."""
    h = int(14 * big)
    cv.ell(x, y, 5 * big, 1.6 * big, (10, 8, 10))
    cv.rect(x - 3 * big, y - h + 4, x + 3 * big, y, body)
    cv.rect(x - 2 * big, y - h + 4, x - big, y, shade(body, 1.25))
    cv.ell(x, y - h + 2, 2.5 * big, 2.5 * big, head)
    cv.line(x + 4, y - 6, x + 9, y - 13, (210, 210, 220))


def monster(cv, x, y, c, w, h, eye=(240, 220, 120), seed=0):
    """A big tier 4 silhouette for scale."""
    rnd = random.Random(seed)
    cv.ell(x, y, w * 0.6, 3, (8, 6, 8))
    cv.ell(x, y - h * 0.45, w * 0.5, h * 0.5, c, edge=shade(c, 0.6))
    for i in range(5):
        a = -math.pi * (0.15 + 0.7 * i / 4)
        cv.line(x + math.cos(a) * w * 0.4, y - h * 0.5 + math.sin(a) * h * 0.4,
                x + math.cos(a) * w * 0.65, y - h * 0.5 + math.sin(a) * h * 0.75 + rnd.randint(-2, 2), shade(c, 0.7))
    cv.put(x - 4, y - h * 0.6, eye); cv.put(x + 4, y - h * 0.6, eye); cv.put(x - 3, y - h * 0.6, eye); cv.put(x + 5, y - h * 0.6, eye)


# ------------------------------------------------------------------ the biomes
BIOMES = []


def biome(fn):
    BIOMES.append(fn)
    return fn


@biome
def drowned_nave():
    """Drowned Nave: a sunken cathedral. Brine floods in and out through the room; stained glass throws coloured light."""
    cv = Canvas()
    stone, brine = (92, 98, 96), (34, 78, 88)
    x0, y0, x1, y1 = 10, 34, 246, 138
    floor_slabs(cv, x0, y0, x1, y1, stone, 1, slab=(30, 18))

    def windows(c, a, b, e, f):
        for i, x in enumerate(range(a + 18, e - 10, 44)):
            c.rect(x, b + 4, x + 14, f - 2, (24, 28, 34))
            c.ell(x + 7, b + 5, 7, 5, (24, 28, 34))
            glass = [(120, 60, 70), (60, 90, 110), (110, 100, 60)][i % 3]
            for y in range(b + 6, f - 3, 3): c.rect(x + 2, y, x + 12, y + 2, shade(glass, 0.8))
            c.line(x + 7, b + 2, x + 7, f - 2, (40, 44, 48))
    walls(cv, x0, y0, x1, y1, (70, 76, 78), (120, 128, 124), (16, 20, 24), face_h=28, motif=windows)
    # the tide: a pool reaching in from the left, foam lip
    for y in range(y0, y1):
        reach = 70 + 25 * math.sin(y * 0.09) + 10 * math.sin(y * 0.31)
        for x in range(x0, int(x0 + reach)):
            c = cv.get(x, y)
            cv.put(x, y, mix(c, brine, 0.72 if x < x0 + reach - 3 else 0.35))
        cv.put(x0 + reach, y, (190, 214, 210))
    # light shafts
    for i, x in enumerate(range(x0 + 25, x1 - 10, 44)):
        for y in range(y0, y0 + 60):
            for dx in range(-3, 4):
                xx = x + 4 + dx + (y - y0) * 0.35
                if x0 < xx < x1:
                    glass = [(160, 90, 100), (90, 130, 160), (170, 150, 90)][i % 3]
                    cv.put(xx, y, mix(cv.get(xx, y), glass, 0.12))
    # broken pews
    for j, (px, py) in enumerate([(120, 70), (160, 70), (130, 100), (190, 102), (60, 118)]):
        cv.rect(px, py, px + 26, py + 4, (70, 52, 40)); cv.rect(px, py + 4, px + 26, py + 6, (40, 30, 24))
        if j % 2: cv.rect(px + 10, py - 1, px + 14, py + 6, (24, 32, 34))
    door(cv, 128, y1, 18, (6, 6, 8))
    figure(cv, 150, 92, (90, 60, 50))
    monster(cv, 70, 92, (60, 96, 104), 44, 38, eye=(140, 240, 240), seed=1)
    cv.vignette()
    return cv, dict(
        name="Drowned Nave", tag="A cathedral the sea took back",
        palette=[stone, brine, (190, 214, 210), (120, 60, 70), (60, 90, 110), (70, 52, 40)],
        look="Grey-green nave stone, tall arched windows of dim stained glass, broken pews. Brine stands in the low side "
             "of every room and the coloured light from the windows lies across the floor in slanted shafts.",
        hazard="The tide: brine floods across the room and drains back on a slow cycle. Standing in it slows the hero, and "
               "water monsters (Bel'Mora's) heal in it, as in their brine pools. Some rooms flood fully, then the floor is "
               "an island fight.",
        props="Pews to break (cover that monsters smash through), fallen bells, reliquaries that hold gold.",
        rooms="Long naves (two screens wide) with side chapels, and a font room that is all water but a ring of stone.",
        fits="Bel'Mora, the Drowned Bell, big swimmers.")


@biome
def bone_orchard():
    """Bone Orchard: a grove grown from the dead. Bone trees, lanterns, ash soil."""
    cv = Canvas()
    soil = (86, 82, 70)
    x0, y0, x1, y1 = 10, 34, 246, 138
    floor_slabs(cv, x0, y0, x1, y1, soil, 2, slab=(60, 34), crack=1.4, edge_k=0.93)
    rnd = random.Random(5)
    # root veins
    for _ in range(18):
        x, y = rnd.randrange(x0, x1), rnd.randrange(y0, y1)
        for i in range(30):
            cv.put(x, y, (170, 162, 140)); x += rnd.choice((-1, 1, 1)); y += rnd.choice((0, 0, 1, -1))

    def ribs(c, a, b, e, f):
        for x in range(a + 6, e - 6, 16):
            for t in range(18):
                yy = b + 4 + t
                xx = x + int(5 * math.sin(t / 18 * math.pi))
                c.put(xx, yy, (200, 192, 168)); c.put(xx + 1, yy, (150, 142, 120))
    walls(cv, x0, y0, x1, y1, (60, 56, 52), (150, 142, 124), (14, 12, 14), face_h=26, motif=ribs)

    def tree(x, y, s):
        bone, dark = (210, 202, 178), (120, 112, 96)
        cv.ell(x, y, 10 * s, 3, (30, 26, 24))
        cv.rect(x - 2, y - 26 * s, x + 2, y, bone); cv.rect(x + 1, y - 26 * s, x + 2, y, dark)
        for k, (dx, dy) in enumerate([(-12, -32), (10, -36), (-4, -42), (14, -24), (-15, -22)]):
            cv.line(x, y - 18 * s, x + dx * s, y + dy * s, bone)
            cv.line(x + 1, y - 18 * s, x + dx * s + 1, y + dy * s, dark)
            if k % 2 == 0:
                lx, ly = x + dx * s, y + dy * s + 3
                cv.line(lx, ly - 3, lx, ly, (60, 50, 40)); cv.rect(lx - 1, ly, lx + 2, ly + 3, (240, 190, 90))
                cv.glow(lx, ly + 1, 14, (240, 180, 80), 0.45)
        cv.ell(x - 5, y - 1, 3, 1.5, (190, 182, 160)); cv.ell(x + 6, y, 2, 1.2, (180, 172, 150))
    for (x, y, s) in [(60, 80, 1.0), (205, 74, 1.1), (140, 128, 0.9), (30, 126, 0.8)]:
        tree(x, y, s)
    # bone piles (Ossivar)
    for (x, y) in [(110, 60), (175, 112), (88, 108)]:
        for i in range(6): cv.ell(x + i % 3 * 3 - 3, y - i // 3 * 2, 2.5, 1.3, (196, 188, 164), edge=(130, 122, 104))
    door(cv, 128, y1, 18, (6, 6, 8))
    figure(cv, 120, 90, (70, 70, 90))
    monster(cv, 175, 86, (150, 140, 120), 46, 40, eye=(240, 120, 60), seed=2)
    cv.vignette()
    return cv, dict(
        name="Bone Orchard", tag="A grove grown from the dead",
        palette=[soil, (210, 202, 178), (120, 112, 96), (240, 190, 90), (60, 56, 52)],
        look="Ash-grey soil veined with pale roots, trees of fused bone hung with candle lanterns that throw warm pools "
             "of light, rib arches along the back wall. The only warm colour on the floor is lantern light.",
        hazard="Lanterns: rooms are dark outside the lantern pools (the game's darkness, as in Lights Out). A tree hit "
               "hard enough drops its lanterns and the room goes darker. Bone piles litter the floor, so Ossivar monsters "
               "start every fight armed.",
        props="Bone trees (solid, break into piles), grave mounds that cough up a minion when walked over, ossuary shrines.",
        rooms="Wide groves with trees as pillars to fight around, with narrow root tunnels between them.",
        fits="Ossivar, the Carrion Saint, anything that eats bones.")


@biome
def ember_works():
    """Ember Works: a foundry under the mines. Molten channels pulse; cranes and chains overhead."""
    cv = Canvas()
    iron = (70, 60, 54)
    x0, y0, x1, y1 = 10, 34, 246, 138
    floor_slabs(cv, x0, y0, x1, y1, iron, 3, slab=(24, 16), crack=0.4, edge_k=0.6)

    def furnaces(c, a, b, e, f):
        for x in range(a + 10, e - 20, 52):
            c.rect(x, b + 6, x + 24, f, (46, 38, 34))
            c.ell(x + 12, f - 6, 8, 5, (30, 14, 8))
            c.ell(x + 12, f - 5, 6, 3, (250, 140, 40)); c.glow(x + 12, f - 2, 18, (255, 120, 30), 0.5)
            c.rect(x + 9, b, x + 15, b + 6, (36, 30, 28))
        for x in range(a, e, 4): c.put(x, b + 3, (90, 76, 64))
    walls(cv, x0, y0, x1, y1, (58, 50, 46), (110, 92, 78), (12, 9, 8), face_h=26, motif=furnaces)
    # molten channels: a grid of glowing lines with grates
    for cy in (64, 108):
        for x in range(x0, x1):
            for dy in range(-2, 3):
                hot = (255, 170, 60) if abs(dy) < 1 else (220, 90, 30)
                cv.put(x, cy + dy, hot)
            if x % 10 == 0:
                for dy in range(-3, 4): cv.put(x, cy + dy, (40, 34, 30))
        for x in range(x0, x1, 3): cv.glow(x, cy, 6, (255, 110, 30), 0.05)
    for cx in (80, 176):
        for y in range(y0, y1):
            for dx in range(-2, 3): cv.put(cx + dx, y, (255, 160, 50) if abs(dx) < 1 else (210, 90, 30))
            if y % 10 == 0:
                for dx in range(-3, 4): cv.put(cx + dx, y, (40, 34, 30))
    # chains from above, a crucible
    for x in (40, 130, 220):
        for y in range(y0 - 2, y0 + 24, 3): cv.ell(x, y, 1.2, 1.5, (110, 100, 96))
    cv.ell(130, y0 + 30, 9, 6, (50, 44, 42), edge=(30, 26, 24)); cv.ell(130, y0 + 27, 7, 2, (255, 160, 60))
    door(cv, 128, y1, 18, (6, 6, 8))
    figure(cv, 120, 92, (80, 80, 110))
    monster(cv, 200, 92, (110, 70, 50), 48, 42, eye=(255, 230, 120), seed=3)
    cv.vignette(0.45)
    return cv, dict(
        name="Ember Works", tag="The foundry below the mines",
        palette=[iron, (110, 92, 78), (255, 170, 60), (220, 90, 30), (46, 38, 34)],
        look="Soot-black iron plate split by channels of molten metal under grates, furnace mouths along the back wall, "
             "chains and crucibles hanging from the dark. Most of the light in the room is the metal itself.",
        hazard="The pour: every few seconds a pulse of heat runs down the channels (a bright tell first), burning anything "
               "standing on a grate. Crucibles hang on chains. Hit one and it tips, pouring a short-lived pool.",
        props="Anvils (cover), coal carts that roll when struck, slag heaps.",
        rooms="Grid rooms cut into islands by the channels, and long casting halls with a pour that sweeps end to end.",
        fits="Vhorrul's fire monsters, anything heavy and armoured.")


@biome
def rot_gardens():
    """Rot Gardens: caves gone soft with fungus. Glowing caps, spore drifts."""
    cv = Canvas()
    moss = (74, 62, 72)
    x0, y0, x1, y1 = 10, 34, 246, 138
    floor_slabs(cv, x0, y0, x1, y1, moss, 4, slab=(50, 30), crack=0.2, edge_k=0.92)
    rnd = random.Random(9)
    for _ in range(900):
        x, y = rnd.randrange(x0, x1), rnd.randrange(y0, y1)
        cv.put(x, y, mix(cv.get(x, y), (110, 92, 104), 0.5))

    def shelves(c, a, b, e, f):
        for x in range(a + 4, e - 4, 22):
            for k in range(3):
                c.ell(x + k * 5, b + 8 + k * 6, 7 - k, 2, (150, 120, 120), edge=(90, 70, 76))
    walls(cv, x0, y0, x1, y1, (56, 46, 54), (120, 100, 110), (12, 9, 12), face_h=26, motif=shelves)

    def cap(x, y, s, col):
        cv.ell(x, y, 5 * s, 1.5 * s, (16, 12, 16))
        cv.rect(x - 1.5 * s, y - 10 * s, x + 1.5 * s, y, (190, 180, 170))
        cv.ell(x, y - 11 * s, 9 * s, 4.5 * s, col, edge=shade(col, 0.6))
        for i in range(-2, 3): cv.put(x + i * 3 * s, y - 12 * s, shade(col, 1.5))
        cv.glow(x, y - 8 * s, 26 * s, col, 0.4)
    for (x, y, s, c) in [(40, 70, 1.3, (60, 190, 180)), (215, 80, 1.5, (60, 190, 180)), (120, 128, 1.0, (170, 220, 90)),
                         (180, 126, 0.8, (60, 190, 180)), (95, 60, 0.7, (170, 220, 90))]:
        cap(x, y, s, c)
    # spore drift
    for _ in range(140):
        x, y = rnd.gauss(150, 30), rnd.gauss(80, 14)
        cv.put(x, y, mix(cv.get(int(min(255, max(0, x))), int(min(143, max(0, y)))) if 0 <= x < 256 and 0 <= y < 144 else (0, 0, 0), (200, 230, 160), 0.6))
    door(cv, 128, y1, 18, (6, 6, 8))
    figure(cv, 150, 100, (90, 50, 50))
    monster(cv, 70, 112, (110, 80, 100), 50, 40, eye=(200, 255, 140), seed=4)
    cv.vignette()
    return cv, dict(
        name="Rot Gardens", tag="Caves gone soft with fungus",
        palette=[moss, (60, 190, 180), (170, 220, 90), (150, 120, 120), (56, 46, 54)],
        look="Spongy plum-brown floor, shelf fungus up the walls, giant caps glowing teal and acid green. The caps are "
             "the room's lights, so the colour of a room tells you what grows there.",
        hazard="Spore drifts: clouds that hang in the air and slowly drift. Walking through dazes the hero briefly. A cap "
               "that is hit bursts into a fresh cloud, so a careless swing can blind your own escape.",
        props="Caps (light and burst), puffballs that roll, mycelium mats that slow everything on them.",
        rooms="Round caverns joined by low tunnels, and a hollow trunk room you fight inside.",
        fits="Spore and slime monsters, and the Tallow Grub's kin.")


@biome
def ledger_vaults():
    """Ledger Vaults: an endless archive. Shelves as walls, candles, ink."""
    cv = Canvas()
    wood = (96, 72, 52)
    x0, y0, x1, y1 = 10, 34, 246, 138
    floor_slabs(cv, x0, y0, x1, y1, wood, 6, slab=(64, 6), crack=0.1, edge_k=0.84)

    def cases(c, a, b, e, f):
        for x in range(a + 2, e - 2, 18):
            c.rect(x, b + 3, x + 16, f, (54, 38, 28))
            for yy in range(b + 6, f - 2, 6):
                for k in range(14):
                    col = [(120, 40, 40), (40, 70, 90), (130, 110, 60), (70, 90, 50)][(k * 7 + yy + x) % 4]
                    if (k + yy) % 5: c.put(x + 1 + k, yy, shade(col, 0.8)); c.put(x + 1 + k, yy + 1, shade(col, 0.6)); c.put(x + 1 + k, yy + 2, shade(col, 0.5))
    walls(cv, x0, y0, x1, y1, (60, 44, 34), (130, 104, 76), (12, 9, 8), face_h=28, motif=cases)
    # free-standing shelves forming a maze
    for (x, y, w) in [(40, 66, 60), (150, 66, 70), (90, 100, 50), (180, 104, 50)]:
        cv.rect(x, y - 16, x + w, y, (60, 42, 30))
        for yy in range(y - 14, y - 2, 4):
            for k in range(w - 2):
                if (k + yy) % 6: cv.put(x + 1 + k, yy, [(120, 40, 40), (40, 70, 90), (130, 110, 60)][(k + yy) % 3])
        cv.rect(x, y, x + w, y + 3, (30, 22, 16))
    # ink pool and floating candles
    cv.ell(60, 118, 20, 6, (20, 22, 34), edge=(40, 44, 60))
    for (x, y) in [(30, 50), (120, 46), (210, 52), (140, 84), (36, 92)]:
        cv.rect(x, y, x + 2, y + 4, (220, 210, 180)); cv.put(x, y - 1, (255, 220, 120)); cv.glow(x, y, 16, (255, 200, 110), 0.35)
    for _ in range(25):
        rnd = random.Random(_)
        x, y = rnd.randrange(20, 240), rnd.randrange(40, 130)
        cv.rect(x, y, x + 3, y + 2, (210, 200, 170))
    door(cv, 128, y1, 18, (6, 6, 8))
    figure(cv, 140, 92, (50, 80, 70))
    monster(cv, 205, 128, (70, 60, 90), 44, 40, eye=(255, 230, 160), seed=6)
    cv.vignette()
    return cv, dict(
        name="Ledger Vaults", tag="An archive that never ends",
        palette=[wood, (130, 104, 76), (120, 40, 40), (40, 70, 90), (255, 220, 120), (20, 22, 34)],
        look="Walnut boards, bookcases for walls, free-standing shelves that make a maze of the room, floating candles, "
             "loose pages everywhere. Dusty and warm, with ink-black pools as the cold accent.",
        hazard="Shelves fall: a big monster that charges into a shelf topples it, crushing whatever is behind and opening "
               "a new path. Ink pools hide anything standing in them (a monster's tell disappears).",
        props="Shelves (walls that fall), reading desks (cover), page drifts that rustle when walked through.",
        rooms="Shelf mazes that open up as the fight goes on, and a reading-room arena with a domed ceiling.",
        fits="Jinx's tricksters and gamblers, the Steward, anything that hides.")


@biome
def the_seam():
    """The Seam: chaos's own biome. Pieces of the other floors stitched together over a violet void."""
    cv = Canvas()
    void = (34, 18, 48)
    x0, y0, x1, y1 = 10, 34, 246, 138
    cv.rect(x0, y0, x1, y1, void)
    rnd = random.Random(12)
    for _ in range(500):
        x, y = rnd.randrange(x0, x1), rnd.randrange(y0, y1)
        cv.put(x, y, (110, 70, 160) if rnd.random() < 0.8 else (230, 200, 255))
    # islands of other biomes' floors
    bases = [(130, 118, 80), (92, 98, 96), (86, 82, 70), (70, 60, 54), (96, 72, 52), (124, 112, 80)]
    islands = [(20, 40, 90, 80), (100, 44, 170, 92), (180, 40, 244, 86), (40, 88, 120, 134), (130, 96, 214, 136)]
    for i, (a, b, e, f) in enumerate(islands):
        floor_slabs(cv, a, b, e, f, bases[i % len(bases)], 20 + i, slab=(26, 16))
        cv.rect(a, f, e, f + 4, shade(bases[i % len(bases)], 0.4))
        for x in range(a, e):
            if rnd.random() < 0.35: cv.put(x, f + 4 + rnd.randint(0, 3), shade(bases[i % len(bases)], 0.3))
        # violet rim light
        cv.rect(a, b, e, b + 1, (170, 120, 220))

    def torn(c, a, b, e, f):
        for x in range(a, e):
            seg = (x - a) // 40
            col = [(70, 76, 78), (60, 56, 52), (58, 50, 46), (60, 44, 34), (84, 70, 50)][seg % 5]
            for y in range(b, f): c.put(x, y, shade(col, 0.8 + 0.3 * (1 - (y - b) / (f - b))))
            if (x - a) % 40 == 0:
                for y in range(b, f): c.put(x + rnd.randint(-1, 1), y, (200, 150, 255))
    walls(cv, x0, y0, x1, y1, (50, 40, 60), (150, 110, 200), (10, 6, 14), face_h=26, motif=torn)
    # a rift crack
    x, y = 100, 60
    for i in range(70):
        for d in range(-1, 2): cv.put(x + d, y, (230, 200, 255) if d == 0 else (150, 90, 220))
        x += rnd.choice((0, 1, 1)); y += rnd.choice((0, 1, 1, -1))
    cv.glow(130, 90, 60, (160, 90, 230), 0.25)
    door(cv, 128, y1, 18, (6, 6, 8))
    figure(cv, 60, 70, (90, 60, 50))
    monster(cv, 175, 80, (90, 50, 120), 52, 46, eye=(240, 220, 255), seed=7)
    cv.vignette(0.5)
    return cv, dict(
        name="The Seam", tag="Chaos's own floor: the other floors, torn and stitched",
        palette=[void, (110, 70, 160), (230, 200, 255), (130, 118, 80), (92, 98, 96), (70, 60, 54)],
        look="Islands of every other floor's stone, crypt, mine and orchard, stitched over a violet void lit from below. "
             "The back wall changes material every few steps. The violet seams are the only bright colour.",
        hazard="Shifts: when a room is cleared its islands drift into a new layout before the next wave. Rifts open "
               "between islands, and anything knocked into one comes out of another.",
        props="Fragments of every biome's props; rift stones that teleport whoever strikes them.",
        rooms="Chaos-only. Arenas of several islands; the floor where tier 4 and 5 monsters live.",
        fits="Everything. The late chaos floors.")


# ------------------------------------------------------------------ the floor-plan sketch
def floor_plans():
    cv = Canvas(256, 144, (18, 16, 20))
    d = ImageDraw.Draw(cv.im)

    def room(x, y, w, h, c, label=None):
        d.rectangle([x, y, x + w, y + h], fill=c, outline=(200, 190, 160))

    def link(a, b):
        d.line([a, b], fill=(160, 150, 120), width=1)
    # vanilla: about nine one-screen rooms in a branching chain
    vx, vy = 10, 30
    cells = [(0, 1), (1, 1), (2, 1), (2, 0), (3, 1), (4, 1), (4, 2), (5, 1), (6, 1)]
    S = 12
    for i, (cx, cy) in enumerate(cells):
        c = (130, 118, 80)
        if i == 0: c = (90, 130, 90)
        if i == 5: c = (150, 110, 60)
        if i == 8: c = (130, 80, 150)
        room(vx + cx * (S + 4), vy + cy * (S + 4), S, S - 3, c)
    for a, b in zip(cells, cells[1:]):
        link((vx + a[0] * (S + 4) + S // 2, vy + a[1] * (S + 4) + 4), (vx + b[0] * (S + 4) + S // 2, vy + b[1] * (S + 4) + 4))
    # chaos: bigger rooms, loops, an arena
    cx0, cy0 = 10, 82
    rooms = [(0, 1, 1, 1, (90, 130, 90)), (1, 0, 2, 1, (92, 98, 96)), (1, 1, 1, 2, (86, 82, 70)), (2, 1, 2, 2, (130, 80, 60)),
             (3, 0, 1, 1, (150, 110, 60)), (4, 0, 2, 1, (96, 72, 52)), (4, 1, 1, 1, (74, 62, 72)), (5, 1, 2, 2, (90, 50, 120)),
             (7, 1, 1, 1, (130, 80, 150))]
    U = 14
    for (gx, gy, gw, gh, c) in rooms:
        room(cx0 + gx * (U + 2), cy0 + gy * (U - 2), gw * (U + 2) - 2, gh * (U - 2) - 2, c)
    return cv


def label_board(entries, plans, outdir):
    """A board of every biome with its palette, for the artifact and the vault."""
    font = ImageFont.load_default()
    tiles = []
    for cv, info in entries:
        im = cv.im.resize((W * SCALE, H * SCALE), Image.NEAREST)
        board = Image.new("RGB", (W * SCALE, H * SCALE + 70), (18, 16, 20))
        board.paste(im, (0, 0))
        dd = ImageDraw.Draw(board)
        dd.text((12, H * SCALE + 10), info["name"].upper(), fill=(230, 220, 200), font=font)
        dd.text((12, H * SCALE + 28), info["tag"], fill=(170, 160, 140), font=font)
        for i, c in enumerate(info["palette"]):
            dd.rectangle([W * SCALE - 30 - i * 34, H * SCALE + 14, W * SCALE - 6 - i * 34, H * SCALE + 50], fill=c)
        tiles.append(board)
    return tiles


def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    entries = [fn() for fn in BIOMES]
    tiles = label_board(entries, None, outdir)
    for (cv, info), tile in zip(entries, tiles):
        slug = info["name"].lower().replace(" ", "_")
        tile.save(os.path.join(outdir, "biome_%s.png" % slug))
    plans = floor_plans().im.resize((W * SCALE, H * SCALE), Image.NEAREST)
    plans.save(os.path.join(outdir, "floor_plans.png"))
    return entries


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "build/concepts/chaos")
