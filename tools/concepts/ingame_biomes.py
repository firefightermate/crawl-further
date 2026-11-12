"""Crawl Chaos biome mock-ups as they would look in the game: the game's own rooms, props, hero and light sprites,
recoloured the way the mod could recolour them at runtime, with a few new pieces of ours (water, lava, mushrooms,
the Seam's void) and our monsters at their real size.

    python3 tools/concepts/ingame_biomes.py <outdir>

Needs the asset dump (see ingame.py). Concepts only: nothing here ships.
"""
import colorsys
import math
import os
import random
import sys

from PIL import Image

import ingame as G

SCALE = 3


# ------------------------------------------------------------------ colour helpers
def hsv_set(h=None, sk=1.0, vk=1.0, hmix=1.0, sadd=0.0):
    """Recolour keeping the art's shading: hue moved to h (by hmix), saturation and value scaled."""
    def f(r, g, b):
        hh, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if h is not None:
            d = ((h - hh + 0.5) % 1.0) - 0.5
            hh = (hh + d * hmix) % 1.0
        s = max(0.0, min(1.0, s * sk + sadd))
        v = max(0.0, min(1.0, v * vk))
        return tuple(int(round(c * 255)) for c in colorsys.hsv_to_rgb(hh, s, v))
    return G.remap(f)


def kinds(*ks, name=None, not_name=None):
    def p(d):
        if d.kind not in ks or d.name in ("hero", "monster", "mod", "light"):
            return False
        if name and not any(n in d.name for n in name):
            return False
        if not_name and any(n in d.name for n in not_name):
            return False
        return True
    return p


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def lum(c):
    return (0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]) / 255


class Noise:
    def __init__(self, seed):
        self.seed, self.g = seed, {}

    def v(self, x, y, s):
        fx, fy = x / s, y / s
        ix, iy = math.floor(fx), math.floor(fy)
        tx, ty = fx - ix, fy - iy
        tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
        def r(a, b):
            k = (a, b, s)
            if k not in self.g:
                self.g[k] = random.Random(hash((a, b, s, self.seed))).random()
            return self.g[k]
        return (r(ix, iy) * (1 - tx) + r(ix + 1, iy) * tx) * (1 - ty) + (r(ix, iy + 1) * (1 - tx) + r(ix + 1, iy + 1) * tx) * ty


def liquid(mask, deep, shallow, foam, n, ripple=0.0, keep=0.25, glow=None):
    """A floor effect: inside mask (mask(x, y) > 0 = depth in px from the edge) the floor turns to liquid. The floor's
    own texture shows through a little (keep), the edge gets a lip of foam, ripples are faint streaks."""
    def fx(x, y, c):
        d = mask(x, y)
        if d <= 0:
            if d > -1.6:
                return mix(c, (0, 0, 0), 0.35)      # wet dark rim round the pool
            return None
        if d < 1.2:
            return foam
        t = min(1.0, d / 9.0)
        base = mix(shallow, deep, t)
        l = lum(c) - 0.45
        base = tuple(v + l * 255 * keep for v in base)
        if ripple and n.v(x * 0.6, y * 3.0, 3.0) > 1 - ripple:
            base = mix(base, foam, 0.35)
        if glow:
            k = n.v(x, y, 6.0)
            base = mix(base, glow, max(0.0, (k - 0.55) * 1.6))
        return base
    return fx


def wavy_band(y_edge, amp=6, freq=0.05, below=True, n=None):
    """Depth into a liquid whose edge is a wavy horizontal line."""
    def m(x, y):
        e = y_edge + amp * math.sin(x * freq) + (n.v(x, 0, 9) - 0.5) * amp if n else y_edge + amp * math.sin(x * freq)
        return (e - y) if below else (y - e)
    return m


def ellipse(cx, cy, rx, ry, n=None, rough=0.0):
    def m(x, y):
        d = math.hypot((x - cx) / rx, (y - cy) / ry)
        if n and rough:
            d += (n.v(x, y, 4) - 0.5) * rough
        return (1 - d) * min(rx, ry)
    return m


def union(*ms):
    return lambda x, y: max(m(x, y) for m in ms)


# ------------------------------------------------------------------ our new pieces, drawn to sit with the game's props
def outline(im, c):
    src = im.copy(); sp = src.load(); px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            if sp[x, y][3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < im.width and 0 <= yy < im.height and sp[xx, yy][3]:
                    px[x, y] = tuple(c) + (255,)
                    break
    return im


def mushroom(h, cap, stem=(196, 186, 168), seed=0):
    """A giant cap: about the height of the game's stalagmites, shaded in four tones lit from the upper left, outlined
    in a dark shade of its own colour like the game's props."""
    rnd = random.Random(seed)
    w = int(h * 0.95) | 1
    im = Image.new("RGBA", (w + 2, h + 2), (0, 0, 0, 0)); px = im.load()
    cx = (w + 2) / 2
    capy, caprx, capry = h * 0.32, w / 2 - 0.5, h * 0.22
    def tone(t, pal):
        return pal[max(0, min(len(pal) - 1, int(round(t))))]
    sp = [mix(stem, (40, 30, 30), 0.45), mix(stem, (40, 30, 30), 0.22), stem, mix(stem, (255, 255, 255), 0.25)]
    cap = mix(cap, (120, 110, 100), 0.25)          # as muted as the game's own props
    cp = [mix(cap, (20, 14, 26), 0.6), mix(cap, (20, 14, 26), 0.35), cap, mix(cap, (240, 236, 210), 0.25), mix(cap, (250, 248, 230), 0.5)]
    for y in range(int(capy), h + 1):
        half = max(1.2, h * 0.08 + (y - capy) * 0.04)
        for x in range(int(cx - half - 1), int(cx + half + 1)):
            if abs(x + 0.5 - cx) <= half:
                t = 2.2 - (x + 0.5 - cx) / half * 1.2 - (1 if y < capy + 3 else 0)
                px[x, y] = tone(t, sp) + (255,)
    for y in range(h + 1):
        for x in range(w + 2):
            dx, dy = (x + 0.5 - cx) / caprx, (y + 0.5 - capy) / capry
            if dx * dx + dy * dy <= 1 and y < capy + capry * 0.55:
                t = 2.3 - dx * 1.1 - dy * 1.4
                if y >= capy + capry * 0.3:
                    t = 0.6
                px[x, y] = tone(t, cp) + (255,)
    for _ in range(max(2, w // 5)):
        x, y = int(cx + rnd.uniform(-caprx * 0.6, caprx * 0.5)), int(capy + rnd.uniform(-capry * 0.7, 0))
        if px[x, y][3]:
            px[x, y] = cp[4] + (255,)
    return outline(im, mix(cap, (0, 0, 0), 0.7))


def shard(h, pal):
    w = max(5, h // 3)
    im = Image.new("RGBA", (w + 2, h + 2), (0, 0, 0, 0)); px = im.load()
    for y in range(h):
        half = (w / 2) * (1 - abs(y - h * 0.4) / (h * 0.6))
        for x in range(w + 2):
            if abs(x + 0.5 - (w + 2) / 2) <= half:
                t = 3 - (x - (w + 2) / 2) / max(1, half) * 1.2 - y / h
                px[x, y + 1] = pal[max(0, min(len(pal) - 1, int(round(t))))] + (255,)
    return outline(im, pal[0])


def monster(R, sheet, x, y, flip=False, frame=0):
    im = G.mod_sprite(sheet, frame, flip, prefer=())
    d = R.add_image(im, x, y, name="monster")
    return d


def hero(R, x, y, flip=False, clip="1HSwordIdle"):
    d = R.add_image(G.hero(clip, 0, flip), x, y, name="hero")
    # the game's hero casts its own faint light
    R.light(x, y + 12, (255, 236, 170), 0.8)
    return d


# ------------------------------------------------------------------ biomes
BIOMES = []


def biome(**info):
    def deco(fn):
        BIOMES.append((fn, info))
        return fn
    return deco


STONE_GREEN = dict(h=0.40, sk=0.55, vk=0.98, hmix=0.85)
BRINE = dict(deep=(14, 46, 56), shallow=(44, 96, 98), foam=(156, 196, 182))


def drowned(R, props_too=True):
    R.recolours.append((kinds("floor", "decal"), hsv_set(**STONE_GREEN)))
    R.recolours.append((kinds("wall"), hsv_set(h=0.42, sk=0.6, vk=0.92, hmix=0.8)))
    if props_too:
        R.recolours.append((kinds("object", name=("Column", "Vase", "Fountain", "Carcophegus", "Well")), hsv_set(h=0.42, sk=0.35, vk=0.9, hmix=0.7)))
        R.recolours.append((kinds("object", name=("Bench", "Chair", "Table", "Cabinet", "Barrel")), hsv_set(sk=0.85, vk=0.75)))


@biome(name="Drowned Nave", tag="A cathedral the sea took back", monsters="Bel'Mora, the Drowned Bell, big swimmers",
       look="The Crypt's own gothic rooms in grey-green, brine standing over the low side of every room, pews and columns "
            "left where the water found them.",
       hazard="The tide floods across the room and drains back on a slow cycle. Brine slows the hero; Bel'Mora's monsters "
              "heal in it.",
       made="Crypt rooms and props recoloured. New: the brine floor layer.")
def drowned_nave():
    out = []
    n = Noise(1)
    # 1. the flooded nave
    R = G.Room("RoomCryptMedium2", seed=11)
    drowned(R)
    water = wavy_band(-14, amp=5, freq=0.07, n=n)
    R.floor_fx.append(liquid(water, ripple=0.06, n=n, **BRINE))
    R.block(lambda x, y: water(x, y) > -3)
    for x in (-80, -40, 0, 40, 80):
        R.put("ColumnCrypt", x, 22)
    for x in (-60, -20, 20, 60):
        R.put("PropGhostTrap_ShortBenchHoriz", x - 6, 4); R.put("PropGhostTrap_ShortBenchHoriz", x + 6, 4)
    R.put("ColumnCryptFlipped", -70, -32); R.put("PropGhostTrap_ShortBenchAngleA", 30, -30)
    R.scatter([("PropActionableGhost_Fire_CandelabraCrypt", 3), ("PropGhostTrap_Vase1TopWall", 2), ("PropGhostTrap_Vase3", 2), ("PropCandles2", 3), ("FloorRot", 2), ("FloorBricks", 3)], 30)
    R.scatter([("FloorWater", 3), ("FloorPlantDebris", 1)], 10, kind="decal")
    monster(R, "BelDrownedBell", 66, -32, flip=True)
    hero(R, -30, -4)
    for x in (-62, 62):
        R.light(x, 44, (150, 220, 210), 1.2)
    out.append(("The Flooded Nave", "The Crypt's tall gothic room, its lower half under brine. Rows of pews, a line of columns down the nave.", R))

    # 2. the font: a round pool, the game's fountain at its heart, columns round it
    R = G.Room("RoomCryptLarge2c", seed=12)
    drowned(R)
    pool = ellipse(0, -6, 46, 24, n, 0.15)
    R.floor_fx.append(liquid(pool, ripple=0.05, n=n, **BRINE))
    def ring(x, y):
        d = math.hypot(x / 54, (y + 6) / 30)
        if 0.86 < d < 1.0 and pool(x, y) <= 0:
            a = math.atan2((y + 6) / 30, x / 54)
            return (92, 104, 96) if int((a + 4) * 4) % 2 else (76, 88, 82)
        return None
    R.floor_fx.append(lambda x, y, c: mix(c, ring(x, y), 0.6) if ring(x, y) else None)
    R.block(lambda x, y: math.hypot(x / 56, (y + 6) / 32) < 1.0)
    R.put("PropActionable_Fountain", 0, -8)
    for i in range(6):
        a = i / 6 * math.tau
        R.put("ColumnCrypt", 72 * math.cos(a), -6 + 40 * math.sin(a))
    R.scatter([("PropActionableGhost_Fire_CandelabraCrypt", 3), ("PropGhostTrap_Vase1", 2), ("PropCandles3", 3), ("FloorSplotchSmall", 2)], 14)
    monster(R, "BelKraken", -14, -16)
    hero(R, 64, -34, flip=True)
    R.light(0, 0, (140, 220, 210), 2.0, 0.8)
    out.append(("The Font", "A round pool where the floor should be, the game's fountain at its heart, columns in a ring round it.", R))

    # 3. the bell chapel: the floor gone through to the sea, a runner to the altar
    R = G.Room("RoomCryptSmall2", seed=13)
    drowned(R)
    hole = ellipse(30, -18, 24, 14, n, 0.4)
    R.floor_fx.append(liquid(hole, ripple=0.05, n=n, **BRINE))
    R.block(lambda x, y: hole(x, y) > -4)
    R.put("PropActionable_Feature_Carcophegus", -40, 20)
    R.put("PropActionableGhost_Fire_CandelabraCrypt", -62, 20); R.put("PropActionableGhost_Fire_CandelabraCryptFlipped", -18, 20)
    R.scatter([("PropGhostTrap_Vase1TopWall", 2), ("PropActionable_BonePile2", 1), ("PropCandles1", 2), ("FloorRotB", 2)], 10)
    monster(R, "BelSlimeHag", 30, -22)
    hero(R, -40, -14)
    out.append(("The Bell Chapel", "A small gothic chapel whose floor has given way to the sea, a runner leading to the sarcophagus.", R))
    return out


def ashen(R, dark=True):
    R.recolours.append((kinds("floor", "decal"), hsv_set(h=0.08, sk=0.35, vk=0.78, hmix=0.6)))
    R.recolours.append((kinds("wall"), hsv_set(h=0.06, sk=0.5, vk=0.62, hmix=0.5)))
    R.recolours.append((kinds("object", name=("Tree",)), hsv_set(h=0.12, sk=0.18, vk=1.7, hmix=1.0)))     # bone-white trees
    R.recolours.append((kinds("object", name=("Tombstone", "Headstone")), hsv_set(sk=0.4, vk=0.85)))
    R.recolours.append((kinds("object", "decal", name=("BonePile", "FloorBones")), hsv_set(h=0.12, sk=0.3, vk=0.78, hmix=0.6)))


@biome(name="Bone Orchard", tag="A grove grown from the dead", monsters="Ossivar, the Carrion Saint, anything that eats bones",
       look="The Dungeon's rooms gone ash-grey and dark, the game's dead trees bleached to bone, bone piles and graves "
            "between them. Light only round the lanterns.",
       hazard="Dark outside the lantern light. A tree hit hard drops its lanterns and the room goes darker. Bone piles "
              "mean Ossivar's monsters start every fight armed.",
       made="Dungeon and Caves rooms and props recoloured, darkened, with the game's light sprites as lanterns.")
def bone_orchard():
    out = []
    AMB = (0.62, 0.6, 0.62)
    LANT = (255, 190, 110)
    # 1. the grove
    R = G.Room("RoomLarge5", seed=21)
    ashen(R)
    trees = [("PropActionable_Tree5", -58, -6), ("PropActionable_Tree2", 62, 2), ("PropActionable_Tree1", 8, -34),
             ("PropActionable_Tree3", -20, 26), ("PropActionable_Tree6", 80, -36), ("PropActionable_Tree1", -82, 30)]
    for t, x, y in trees:
        R.put(t, x, y)
        R.light(x + 4, y + 26, LANT, 3.0, 0.55)
    R.scatter([("PropActionable_BonePile1", 2), ("PropActionable_BonePile3", 2), ("PropActionable_Tombstone1", 3), ("PropActionable_Tombstone3", 3),
               ("PropActionable_Headstone1", 1), ("PropActionable_Body4", 1)], 16)
    R.scatter([("FloorBones1", 2), ("FloorBones3", 2), ("FloorBones5", 2), ("FloorSplotchSmall", 1)], 22, kind="decal")
    monster(R, "OssTombwright", 34, -20)
    hero(R, -28, -22)
    out.append(("The Grove", "Bone-white trees as pillars to fight round, lanterns in their branches and graves between them.", (R, AMB)))

    # 2. the ossuary gate: a long corridor lined with bones
    R = G.Room("RoomCryptCorridor1", seed=22)
    ashen(R)
    R.recolours.append((kinds("wall"), hsv_set(h=0.08, sk=0.3, vk=0.7, hmix=0.6)))
    x = R.fx0 + 12
    while x < R.fx1 - 10:
        R.put("PropActionable_BonePile%d" % R.rnd.randint(1, 4), x, R.fy1 - 6)
        x += R.rnd.randint(20, 30)
    for xx in (-60, 0, 60):
        R.put("PropActionable_Feature_Altar_Skull", xx, R.fy1 - 4)
        R.light(xx, R.fy1 + 6, (255, 120, 80), 3.0, 0.5)
    R.scatter([("FloorBones1", 2), ("FloorBones5", 2), ("PropActionable_Body1", 1)], 14, kind="decal")
    monster(R, "OssCoffinBearer", 60, R.fy0 + 2, flip=True)
    hero(R, -50, R.fy0 + 4)
    out.append(("The Ossuary Gate", "A long corridor walled in bone piles, skull altars burning red along it.", (R, AMB)))

    # 3. the root shrine: the cave's round chamber, one tree in a ring of headstones
    R = G.Room("RoomCavesLarge1", seed=23)
    ashen(R)
    R.put("PropActionable_Tree5", 0, 6)
    R.light(4, 34, LANT, 4.0, 0.7)
    for i in range(8):
        a = i / 8 * math.tau
        R.put("PropActionable_Headstone%d" % (1 + i % 2), 52 * math.cos(a), 4 + 26 * math.sin(a))
    R.scatter([("PropActionable_BonePile2", 2), ("FloorBones3", 3), ("PropActionable_Tombstone2", 2)], 12)
    monster(R, "OssOssuary", -60, -30)
    hero(R, 56, -26, flip=True)
    out.append(("The Root Shrine", "The Caves' round chamber, one great bone tree in a ring of headstones, the orchard's brightest room.", (R, AMB)))
    return out


def sooty(R):
    R.recolours.append((kinds("floor", "decal"), hsv_set(h=0.03, sk=0.45, vk=0.55, hmix=0.5)))
    R.recolours.append((kinds("wall"), hsv_set(h=0.02, sk=0.7, vk=0.6, hmix=0.4)))
    R.recolours.append((kinds("object", name=("Tracks", "MineCart", "Minacart")), hsv_set(h=0.6, sk=0.25, vk=0.7, hmix=0.6)))


LAVA = dict(deep=(250, 150, 40), shallow=(200, 70, 20), foam=(255, 230, 140))
MOLTEN = [(70, 16, 6), (140, 40, 10), (205, 86, 22), (240, 140, 44), (252, 196, 90), (255, 236, 170)]


def molten(n, edge=None):
    """Fill a sprite's opaque pixels with molten metal (crust rafts on a glowing pool)."""
    def go(im):
        im = im.copy(); px = im.load()
        for y in range(im.height):
            for x in range(im.width):
                a = px[x, y][3]
                if not a:
                    continue
                crust = 0.7 * n.v(x, y, 10) + 0.3 * n.v(x, y, 3.5)
                if crust > 0.62:
                    c = mix((38, 30, 30), (70, 56, 50), (crust - 0.62) * 3)
                elif crust > 0.57:
                    c = MOLTEN[5]
                else:
                    c = MOLTEN[max(1, min(5, int(round(2.2 + (n.v(x + 40, y, 6) - 0.5) * 3 + (crust - 0.3) * 3))))]
                px[x, y] = c + (a,)
        return im
    return go


@biome(name="Ember Works", tag="The foundry below the mines", monsters="Vhorrul's fire monsters, anything heavy and armoured",
       look="The Mines gone soot-black and iron-grey, the tracks and carts still there, the mines' chasms and pits now "
            "full of molten slag that lights the room from below.",
       hazard="The pour: every few seconds a pulse of heat runs down the channels (a bright tell first), burning anything "
              "on them. Crucibles tip when hit.",
       made="Mines rooms and props recoloured; the rooms' own chasms and pits become slag. New: the molten floor layer.")
def ember_works():
    out = []
    n = Noise(3)
    AMB = (0.78, 0.72, 0.7)
    # 1. the casting hall: the cross of tracks, a channel of metal along each
    R = G.Room("RoomMinesLarge1dTracks", seed=31)
    sooty(R)
    chan = lambda x, y: max(2.6 - abs(y - (-38) - 1.5 * math.sin(x * 0.1)), (2.6 - abs(x - (-84))) if -38 < y < 40 else -9)
    R.floor_fx.append(liquid(chan, n=n, keep=0.1, glow=(255, 250, 200), **LAVA))
    R.block(lambda x, y: chan(x, y) > -4)
    for x in range(-96, 100, 20):
        R.light(x, -38, (255, 120, 40), 1.2, 0.3)
    for y in range(-30, 40, 20):
        R.light(-84, y, (255, 120, 40), 1.2, 0.3)
    R.put("PropActionable_FireplaceDungeon", -50, 34); R.light(-50, 44, (255, 140, 60), 3, 0.6)
    R.scatter([("PropGhostTrap_MineCart1", 2), ("PropGhostTrap_MineCart5", 2), ("PropsMinesCoalPile1", 3), ("PropsMinesCoalPile2", 2),
               ("PropActionable_CookingPot1", 1), ("PropGhostTrap_MinesCrate1", 1), ("PropsMinesWallLampTopL", 2)], 16)
    R.scatter([("FloorCoalDebris", 3), ("FloorCoalDebrisLarge", 2)], 14, kind="decal")
    monster(R, "VhPyreWarden", 60, -26, flip=True)
    hero(R, -40, -24)
    out.append(("The Casting Hall", "The mines' crossing tracks, a channel of molten metal running beside each, a furnace on the back wall.", (R, AMB)))

    # 2. the slag pit: the room's own chasm, full of slag
    R = G.Room("RoomMinesLarge3", seed=32)
    sooty(R)
    R.recolours.insert(0, (lambda d: d.name.endswith(":mines_room_2blackout"), molten(n)))
    R.recolours.insert(0, (lambda d: "blackoutEdge" in d.name, hsv_set(h=0.06, sk=1.0, vk=1.0, sadd=0.6)))
    R.block(lambda x, y: -14 < x < 14)
    for y in range(-46, 48, 16):
        R.light(4, y, (255, 120, 40), 1.4, 0.4)
    R.scatter([("PropsMinesCoalPile1", 3), ("PropGhostTrap_MineCart5", 2), ("PropActionable_CookingPot2", 1), ("PropGhostTrap_LargeCrate", 1), ("PropsMinesRock2", 2)], 14)
    R.scatter([("FloorCoalDebris", 3)], 10, kind="decal")
    monster(R, "VhAshSeraph", -50, -20)
    hero(R, 50, -24, flip=True)
    out.append(("The Slag Pit", "The mines room with a chasm down its middle, the chasm now a river of slag, the light all from below.", (R, AMB)))

    # 3. the bellows room: the room's two pits are crucibles
    R = G.Room("RoomMinesLarge2", seed=33)
    sooty(R)
    R.recolours.insert(0, (lambda d: d.name.endswith(":mines_room_5blackout"), molten(n)))
    R.recolours.insert(0, (lambda d: "blackoutEdge" in d.name, hsv_set(h=0.06, sk=1.0, vk=1.0, sadd=0.6)))
    R.block(lambda x, y: -52 < x < 52 and -24 < y < 32)
    for x in (-36, -12, 12, 36):
        R.light(x, 16, (255, 120, 40), 1.6, 0.45)
    R.put("PropActionable_FireplaceDungeon", 0, 34); R.light(0, 44, (255, 140, 60), 3, 0.6)
    R.scatter([("PropsMinesCoalPile1", 2), ("PropGhostTrap_MineCart1", 2), ("PropGhostTrap_Barrel", 2), ("PropsMinesWallLampTopR", 2)], 12)
    monster(R, "VhRenderer", 0, -40)
    hero(R, 70, 0, flip=True)
    out.append(("The Bellows Room", "The mines room with two pits, each a crucible of molten metal, the furnace between them.", (R, AMB)))
    return out


PLUM = dict(h=0.88, sk=0.5, vk=0.62, hmix=0.85)
TEAL, ACID = (54, 170, 160), (150, 190, 60)


def rotten(R):
    R.recolours.append((kinds("floor", "decal"), hsv_set(**PLUM)))
    R.recolours.append((kinds("wall"), hsv_set(h=0.9, sk=0.4, vk=0.55, hmix=0.8)))
    R.recolours.append((kinds("object", name=("Stalagmite",)), hsv_set(h=0.9, sk=0.4, vk=0.7, hmix=0.8)))
    R.recolours.append((kinds("decal", "object", name=("Plant", "FloorWater")), hsv_set(h=0.45, sk=1.4, vk=1.2, hmix=1.0)))


def caps(R, spots, rnd):
    for (x, y, h, c) in spots:
        R.add_image(mushroom(h, c, seed=rnd.randint(0, 999)), x, y, name="mod")
        R.rects.append((x - h / 2, y, x + h / 2, y + 6))
        R.light(x, y + h * 0.7, c, 2.6, 0.25 + h / 90)


@biome(name="Rot Gardens", tag="Caves gone soft with fungus", monsters="Spore and slime monsters, the Tallow Grub's kin",
       look="The Caves and the swamp room in plum and bruise tones, slime where the water stood, giant caps glowing teal "
            "and acid green. The caps are the rooms' lights.",
       hazard="Spore drifts hang in the air and slowly move; walking through dazes the hero. A cap that is hit bursts "
              "into a fresh cloud.",
       made="Caves, swamp and corridor rooms and props recoloured. New: the giant caps.")
def rot_gardens():
    out = []
    n = Noise(4)
    AMB = (0.8, 0.76, 0.84)
    # 1. the cap cavern
    R = G.Room("RoomCavesLarge1", seed=41)
    rotten(R)
    caps(R, [(-70, 10, 30, TEAL), (64, 18, 34, TEAL), (-20, -40, 20, ACID), (84, -36, 16, ACID), (20, 30, 14, TEAL), (-90, -20, 12, ACID)], R.rnd)
    R.scatter([("StalagmiteMedium3", 3), ("StalagmiteSmall2", 2), ("StalagmiteLarge2", 1), ("PropActionable_CookingPot1_Poisoned", 1)], 12)
    R.scatter([("FloorPlantSprout", 3), ("FloorPlantDebris", 3), ("FloorWater", 2)], 22, kind="decal")
    monster(R, "TallowColossus", -20, -4)
    hero(R, 40, -20, flip=True)
    out.append(("The Cap Cavern", "The Caves' round chamber, lit by giant caps, with slime underfoot.", (R, AMB)))

    # 2. the mire: the game's swamp room gone sour
    R = G.Room("RoomMed1cSwampRoom", seed=42)
    rotten(R)
    R.recolours.append((kinds("floor"), hsv_set(h=0.3, sk=0.9, vk=0.8, hmix=0.25)))
    slime = ellipse(-30, -20, 30, 12, n, 0.5)
    R.floor_fx.append(liquid(slime, deep=(70, 110, 40), shallow=(110, 150, 60), foam=(190, 220, 120), n=n, ripple=0.05))
    R.block(lambda x, y: slime(x, y) > -3)
    caps(R, [(50, 20, 26, ACID), (-60, 24, 18, TEAL), (60, -30, 14, TEAL)], R.rnd)
    R.scatter([("PropActionable_CookingPot2_Poisoned", 1), ("StalagmiteMedium1", 2), ("PropActionable_Tree6", 1)], 6)
    R.scatter([("FloorPlantSprout", 3), ("FloorPlantDebris", 3)], 16, kind="decal")
    monster(R, "SylCarrionLily", -30, -18)
    hero(R, 20, -10)
    out.append(("The Mire", "The game's swamp room gone sour, a pool of slime in it, caps round the edge.", (R, AMB)))

    # 3. the mycelium tunnel: the bendy corridor
    R = G.Room("RoomCorridorBendy", seed=43)
    rotten(R)
    def mat(x, y, c):
        k = n.v(x, y, 9)
        if k > 0.58 and R.on_floor(x, y):
            thread = abs(n.v(x + 30, y, 4) - 0.5) < 0.04
            return mix(c, (190, 182, 168), 0.4 if thread else 0.16 + (k - 0.58) * 0.5)
        return None
    R.floor_fx.append(mat)
    caps(R, [(R.fx0 + 14, R.fy1 - 30, 20, TEAL), (R.fx1 - 18, R.fy1 - 24, 22, ACID), (8, R.fy0 + 8, 14, TEAL)], R.rnd)
    R.scatter([("StalagmiteSmall1", 2), ("FloorPlantSprout", 3)], 10)
    monster(R, "SylBriarChampion", 30, R.fy0 + 10, flip=True)
    hero(R, -40, R.fy1 - 34)
    out.append(("The Mycelium Tunnel", "The bending corridor, a mat of mycelium across it that slows everything on it.", (R, AMB)))
    return out


def walnut(R):
    R.recolours.append((kinds("floor", "decal"), hsv_set(h=0.07, sk=1.15, vk=0.72, hmix=0.6)))
    R.recolours.append((kinds("wall"), hsv_set(h=0.05, sk=1.1, vk=0.72, hmix=0.6)))
    R.recolours.append((kinds("decal", "object", name=("Carpet",)), hsv_set(h=0.99, sk=1.4, vk=1.05, hmix=1.0)))


@biome(name="Ledger Vaults", tag="An archive that never ends", monsters="Jinx's tricksters and gamblers, the Steward",
       look="The Crypt's rooms in warm walnut, the game's bookshelves and cabinets set out in rows, red rugs, candelabras, "
            "reading tables.",
       hazard="Shelves fall: a big monster that charges a shelf topples it, crushing what is behind and opening a new "
              "path. Ink pools hide anything standing in them.",
       made="Crypt rooms and the game's own library props, recoloured. New: ink pools.")
def ledger_vaults():
    out = []
    n = Noise(5)
    INK = dict(deep=(10, 12, 20), shallow=(24, 28, 44), foam=(60, 66, 96))
    # 1. the stacks
    R = G.Room("RoomCryptLarge3", seed=51)
    walnut(R)
    for row, y in enumerate((26, 4, -18)):
        x = R.fx0 + 20 + (row % 2) * 10
        while x < R.fx1 - 20:
            if abs(x) > 18:
                R.put(R.rnd.choice(["BookshelfCrypt2", "BookshelfCrypt3", "BookshelfCrypt4", "BookshelfCrypt5", "Bookshelf2", "Bookshelf4"]), x, y)
            x += 13
    R.put("Carpet2", 0, -30)
    ink = ellipse(-70, -38, 14, 6, n, 0.4)
    R.floor_fx.append(liquid(ink, n=n, keep=0.05, **INK))
    R.scatter([("PropActionableGhost_Fire_CandelabraCrypt", 3), ("PropGhostTrap_Chair2", 2), ("TableCryptHoriz1", 1), ("PropCandles1", 2)], 10)
    monster(R, "JinxCardKing", 40, -38)
    hero(R, -20, -36)
    out.append(("The Stacks", "The game's bookshelves set out in rows as a maze, a red runner along the front, ink spilt in the corner.", R))

    # 2. the reading room
    R = G.Room("RoomCryptLarge2c", seed=52)
    walnut(R)
    R.put("Carpet1", -50, -12); R.put("Carpet1", 50, -12)
    for x in (-56, 0, 56):
        for y in (14, -18):
            R.put("TableCryptHoriz%d" % R.rnd.randint(1, 3), x, y)
            R.put("PropGhostTrap_Chair2", x - 14, y); R.put("PropGhostTrap_Chair2Flipped", x + 14, y)
    R.put("PropActionable_BookPodium_Flame", 0, 34)
    R.scatter([("PropActionableGhost_Fire_CandelabraCrypt", 3), ("BookshelfCrypt3", 2), ("PropActionable_CryptCabinet2", 2)], 10)
    monster(R, "JinxHouseOfCards", 70, -30, flip=True)
    hero(R, -76, -30)
    out.append(("The Reading Room", "Reading tables in two rows, red rugs, a lectern under the gothic arch.", R))

    # 3. the index hall
    R = G.Room("RoomCryptCorridor1", seed=53)
    walnut(R)
    x = R.fx0 + 10
    while x < R.fx1 - 8:
        R.put("PropActionable_CryptCabinet%d" % R.rnd.randint(1, 6), x, R.fy1 - 8)
        x += 15
    R.put("Carpet2", -40, R.fy0 + 12); R.put("Carpet2", 70, R.fy0 + 12)
    R.scatter([("PropActionableGhost_Fire_CandelabraCrypt", 2), ("PropCandles2", 2)], 6)
    monster(R, "JinxRingmaster", 60, R.fy0 + 4, flip=True)
    hero(R, -50, R.fy0 + 6)
    out.append(("The Index Hall", "A long corridor walled in the game's cabinets, red runners down the middle.", R))
    return out


VOIDC = [(8, 5, 14), (18, 10, 30), (34, 18, 56), (60, 34, 100), (110, 70, 180), (200, 160, 250)]


def seam_floor(R, sources, islands, n):
    """Replace parts of the floor with islands cut from other rooms' floors, over a violet void."""
    srcs = []
    for room, fn in sources:
        S = G.Room(room)
        f = max([d for d in S.draws if d.kind == "floor"], key=lambda d: d.im.width * d.im.height)
        im = fn(f.im) if fn else f.im
        srcs.append((f, im.load()))
    def fx(x, y, c):
        best = None
        for (i, m) in islands:
            d = m(x, y)
            if d > 0:
                best = (i, d); break
        if best is None:
            # cliff faces under the islands, then the void
            for (i, m) in islands:
                if m(x, y + 5) > 0:
                    k = 1 - (m(x, y + 5) / 5.0)
                    return mix((40, 30, 50), (14, 10, 22), 0.5)
            t = 1.0 + n.v(x, y, 7) * 2.2 + (2.5 if n.v(x * 3.3, y * 3.3, 1.0) > 0.93 else 0)
            return VOIDC[max(0, min(5, int(round(t))))]
        f, px = srcs[best[0]]
        u, v = int(x - f.left) % f.im.width, int(f.bottom + f.im.height - y) % f.im.height
        p = px[u, v]
        if best[1] < 1.2:
            return mix(p[:3], VOIDC[5], 0.7)
        return p[:3]
    return fx


@biome(name="The Seam", tag="Chaos's own floor: the other floors, torn and stitched", monsters="Everything. The late chaos floors",
       look="Islands cut from the Crypt, the Mines and the Dungeon, side by side over a violet void, each keeping its own "
            "props. The seams glow.",
       hazard="Shifts: when a room is cleared its islands drift into a new layout. Rifts open between islands; anything "
              "knocked into one comes out of another.",
       made="Floors and props of the other rooms, cut and stitched. New: the void and the rift shards.")
def the_seam():
    out = []
    n = Noise(6)
    SH = [(30, 14, 50), (70, 40, 120), (120, 80, 190), (180, 140, 240), (235, 220, 255)]
    # 1. the island arena
    R = G.Room("RoomLarge5", seed=61)
    sources = [("RoomCryptLarge1", hsv_set(**STONE_GREEN)), ("RoomMinesLarge1", hsv_set(h=0.03, sk=0.45, vk=0.55, hmix=0.5)),
               ("RoomLarge1", hsv_set(h=0.08, sk=0.35, vk=0.78, hmix=0.6)), ("RoomMed1cSwampRoom", hsv_set(**PLUM))]
    def blob(x0, y0, x1, y1):
        return lambda x, y: min(x - x0, x1 - x, y - y0, y1 - y) + (n.v(x, y, 5) - 0.5) * 8
    islands = [(0, blob(-100, 10, -16, 48)), (1, blob(-2, 14, 100, 48)), (2, blob(-100, -48, -24, 0)), (3, blob(-8, -48, 100, -4))]
    R.floor_fx.append(seam_floor(R, sources, islands, n))
    R.block(lambda x, y: all(m(x, y) < 3 for _, m in islands))
    R.recolours.append((kinds("object", name=("ColumnCrypt", "Candelabra")), hsv_set(**STONE_GREEN)))
    R.recolours.append((kinds("object", name=("MineCart", "CoalPile")), hsv_set(h=0.03, sk=0.45, vk=0.6, hmix=0.5)))
    R.recolours.append((kinds("object", name=("Tree6", "BonePile")), hsv_set(h=0.12, sk=0.25, vk=0.85, hmix=1.0)))
    R.recolours.append((kinds("wall"), hsv_set(h=0.78, sk=0.5, vk=0.7, hmix=0.5)))
    R.put("ColumnCrypt", -60, 22); R.put("PropActionableGhost_Fire_CandelabraCrypt", -30, 26)
    R.put("PropGhostTrap_MineCart1", 40, 22); R.put("PropsMinesCoalPile1", 76, 30)
    R.put("PropActionable_Tree6", 64, -30); R.put("PropActionable_BonePile2", -70, -30); R.put("PropActionable_BonePile4", -40, -36)
    for (x, y) in ((-8, 0), (-4, -40), (102, 4)):
        R.add_image(shard(16, SH), x, y, name="mod"); R.light(x, y + 8, (190, 130, 255), 2.4, 0.4)
    monster(R, "UmbHollowKing", 40, -40)
    hero(R, -60, 14)
    out.append(("The Island Arena", "Four floors torn from the Crypt, the Mines, the Dungeon and the swamp, side by side over the void.", R))

    # 2. the rift bridge
    R = G.Room("RoomCryptCorridor1", seed=62)
    xs = list(range(int(R.fx0) + 2, int(R.fx1), 40))
    islands = [(i % 4, (lambda a, i: (lambda x, y: min(x - a, a + 28 - x, y - (R.fy0 + 3 + (i % 2) * 3), (R.fy1 - 5 - (i % 3) * 2) - y) + (n.v(x, y, 4) - 0.5) * 4))(a, i)) for i, a in enumerate(xs)]
    R.floor_fx.append(seam_floor(R, sources, islands, n))
    R.recolours.append((kinds("wall"), hsv_set(h=0.78, sk=0.5, vk=0.7, hmix=0.5)))
    for a in xs[1:]:
        R.add_image(shard(10, SH), a - 6, R.fy0 + 6, name="mod"); R.light(a - 6, R.fy0 + 14, (190, 130, 255), 2.0, 0.3)
    monster(R, "UmbGlitterswarm", 60, R.fy0 + 6, flip=True)
    hero(R, -60, R.fy0 + 8)
    out.append(("The Rift Bridge", "A corridor of mismatched slabs over the void, each from a different floor.", R))

    # 3. the shard gate
    R = G.Room("RoomCryptMedium1", seed=63)
    def rift(x, y, c):
        d = math.hypot(x / 26, (y + 4) / 14)
        if d < 1:
            t = 5 - d * 4 + math.sin(d * 14) * 0.8
            return VOIDC[max(0, min(5, int(round(t))))]
        if d < 1.12:
            return mix(c, VOIDC[5], 0.6)
        return None
    R.floor_fx.append(rift)
    R.recolours.append((kinds("floor", "decal", "wall"), hsv_set(h=0.75, sk=0.4, vk=0.85, hmix=0.35)))
    R.block(lambda x, y: math.hypot(x / 30, (y + 4) / 17) < 1)
    for i in range(7):
        a = i / 7 * math.tau
        x, y = 52 * math.cos(a), -4 + 30 * math.sin(a)
        R.add_image(shard(18, SH), x, y, name="mod"); R.light(x, y + 10, (190, 130, 255), 2.2, 0.35)
        R.rects.append((x - 4, y, x + 4, y + 6))
    R.light(0, -4, (190, 130, 255), 4.0, 0.9)
    R.scatter([("ColumnCrypt", 2), ("PropGhostTrap_Vase1TopWall", 2), ("FloorRot", 2)], 8)
    monster(R, "UmbHollowKing", 64, -40, flip=True)
    hero(R, -64, -34)
    out.append(("The Shard Gate", "A Crypt room around a standing rift, a ring of shards round it: the way down to the next chaos floor.", R))
    return out


def render_all(outdir):
    os.makedirs(outdir, exist_ok=True)
    result = []
    for fn, info in BIOMES:
        rooms = []
        slug = info["name"].lower().replace(" ", "_").replace("'", "")
        for i, (title, blurb, r) in enumerate(fn()):
            R, amb = r if isinstance(r, tuple) else (r, None)
            im = R.render(scale=SCALE, ambient=amb, light=1.0)
            f = "%s_%d.png" % (slug, i + 1)
            im.save(os.path.join(outdir, f))
            rooms.append((title, blurb, f))
        result.append((info, rooms))
    return result


def vanilla(outdir):
    """The game's own rooms, filled the same way, for comparison."""
    out = []
    for room, env, title in (("RoomCryptLarge1", "Crypt", "Crypt"), ("RoomMinesLarge1bTracks", "Mines", "Mines"), ("RoomLarge1", "Caves", "Caves")):
        R = G.Room(room, seed=5)
        R.fill(env)
        hero(R, 0, -10)
        f = "vanilla_%s.png" % title.lower()
        R.render(scale=SCALE).save(os.path.join(outdir, f))
        out.append((title, f))
    return out


if __name__ == "__main__":
    o = sys.argv[1] if len(sys.argv) > 1 else "build/concepts/ingame"
    render_all(o)
    vanilla(o)
