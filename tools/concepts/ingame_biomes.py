"""Crawl Chaos biome mock-ups as they would look in the game (v5).

Built on the game's own rooms, props, hero and light sprites (recoloured the way the mod could recolour them at
runtime), plus new props of ours painted to match (props.py), floor and wall detail layers (detail.py), and a
darkness layer lit by the room's flames and glowing things. Every standing thing has a solid footprint at its base
only, taken from the game's own colliders for its props, so the hero walks behind tall things and is hidden by them.

    python3 tools/concepts/ingame_biomes.py <outdir>

Needs the asset dump (see ingame.py). Concepts only: nothing here ships.
"""
import colorsys
import math
import os
import random
import sys

from PIL import Image

import detail as D
import ingame as G
import paint as P
import props as Q

SCALE = 3


# ------------------------------------------------------------------ colour helpers
def hsv_fn(h=None, sk=1.0, vk=1.0, hmix=1.0, sadd=0.0):
    def f(r, g, b):
        hh, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if h is not None:
            d = ((h - hh + 0.5) % 1.0) - 0.5
            hh = (hh + d * hmix) % 1.0
        s = max(0.0, min(1.0, s * sk + sadd))
        v = max(0.0, min(1.0, v * vk))
        return tuple(int(round(c * 255)) for c in colorsys.hsv_to_rgb(hh, s, v))
    return f


def hsv_set(**kw):
    """Recolour keeping the art's shading: hue moved to h (by hmix), saturation and value scaled."""
    return G.remap(hsv_fn(**kw))


def kinds(*ks, name=None, not_name=None):
    def p(d):
        if d.kind not in ks or d.name in ("hero", "monster", "mod", "light", "shaft"):
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


Noise = P.Noise


# ------------------------------------------------------------------ liquids
def liquid(mask, deep, shallow, foam, n, ripple=0.0, keep=0.25, glow=None, sheen=(255, 255, 255)):
    """A pool or flood on the floor: inside mask (mask(x, y) > 0 = depth in px from the edge) the floor turns to
    liquid. The floor's texture shows through a little (keep); a lip of foam at the edge, a wet dark rim outside it,
    the far bank's shade across the top of the pool, a few lit ripple lines and glints."""
    def fx(x, y, c):
        d = mask(x, y)
        if d <= 0:
            if d > -2.2:
                return mix(c, (0, 0, 0), 0.38 * (1 + d / 2.2))      # wet, dark rim round the pool
            return None
        if d < 1.1:
            return foam
        t = min(1.0, d / 10.0)
        base = mix(shallow, deep, t)
        l = lum(c) - 0.45
        base = tuple(v + l * 255 * keep for v in base)
        # the far bank shades the water below it
        if mask(x, y + 3) <= 0:
            base = mix(base, deep, 0.5)
        if ripple:
            r = n.v(x * 0.45, y * 2.6, 3.0)
            if r > 1 - ripple:
                base = mix(base, sheen, 0.22)
            elif r < ripple * 0.6:
                base = mix(base, deep, 0.3)
        if n.v(x * 2.3, y * 2.3, 1.0) > 0.93 and d > 2:
            base = mix(base, sheen, 0.45)
        if glow:
            k = n.v(x, y, 6.0)
            base = mix(base, glow, max(0.0, (k - 0.55) * 1.4))
        return base
    return fx


def liquid_glow(mask, colours, n, alpha=255, edge=None):
    """The glowing part of a liquid (lava, glowing slime) for the room's floor_glow: drawn over the darkness."""
    def g(x, y):
        d = mask(x, y)
        if d <= 0:
            return None
        if d < 1.1 and edge:
            return edge + (alpha,)
        k = 0.65 * n.v(x, y, 7) + 0.35 * n.v(x * 2, y * 2, 3)
        i = max(0, min(len(colours) - 1, int(k * len(colours) + min(1.0, d / 6) - 0.5)))
        crust = n.v(x + 50, y, 5) > 0.66 and d > 2.5
        if crust:
            return None
        return colours[i] + (alpha,)
    return g


def wavy_band(y_edge, amp=6, freq=0.05, below=True, n=None):
    def m(x, y):
        e = y_edge + amp * math.sin(x * freq) + ((n.v(x, 0, 9) - 0.5) * amp if n else 0)
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


# ------------------------------------------------------------------ placing our own things
def spot(R, near=None, spread=20, tries=60, ok=None):
    """A random open floor point (near a point if given)."""
    for _ in range(tries):
        if near:
            x, y = near[0] + R.rnd.uniform(-spread, spread), near[1] + R.rnd.uniform(-spread * 0.6, spread * 0.6)
        else:
            x, y = R.rnd.uniform(R.fx0 + 4, R.fx1 - 4), R.rnd.uniform(R.fy0 + 3, R.fy1 - 3)
        if R.walkable(x, y) and (ok is None or ok(x, y)):
            return x, y
    return None


def stand(R, made, x, y, lamp=None, tries=0, spread=10, ok=None, force=False):
    """Stand one of our props (sprite, glow, foot, shadow) at x, y, or nearby if tries."""
    im, em, foot, sh = made
    for i in range(tries + 1):
        px, py = (x, y) if i == 0 else (x + R.rnd.uniform(-spread, spread), y + R.rnd.uniform(-spread * 0.6, spread * 0.6))
        if ok and not ok(px, py):
            continue
        d = R.stand(im, px, py, foot, emit=em, shadow=sh, force=force)
        if d:
            if lamp:
                c, rad, inten = lamp
                R.lamp(px, py + im.height * 0.6, c, rad, inten)
            return d
    return None


def scatter_own(R, maker, count, lamp=None, ok=None, near=None, spread=30):
    placed = 0
    for i in range(count * 5):
        if placed >= count:
            break
        p = spot(R, near, spread, ok=ok)
        if not p:
            continue
        if stand(R, maker(i), p[0], p[1], lamp):
            placed += 1
    return placed


def decals(R, maker, count, ok=None, emit_too=True, near=None, spread=30):
    """Flat things on the floor (no footprint): kept off footprints so they are not hidden."""
    for i in range(count):
        r = maker(i)
        im, em = r if isinstance(r, tuple) else (r, None)
        for _ in range(30):
            p = spot(R, near, spread, ok=ok)
            if not p:
                continue
            x, y = p
            if R.free((x - im.width / 2, y - 1, x + im.width / 2, y + im.height * 0.6), R.rects):
                R.add_image(im, x, y - im.height / 2, kind="decal", emit=em if emit_too else None)
                break


def hang(R, maker, step=24, start=10, jitter=6, depth_off=40):
    """Hang things down the back wall from its top (roots, chains, banners)."""
    x = R.fx0 + start
    i = 0
    while x < R.fx1 - 6:
        xx = x + R.rnd.uniform(-jitter, jitter)
        sp = R.wall_span(xx)
        if sp:
            im, em = maker(i, sp[1] - sp[0])
            R.add_image(im, xx, sp[1] - im.height, emit=em, depth=R.fy1 + depth_off)
        x += step
        i += 1


def motes(R, x, y, w, h, colour, count, seed=0):
    m = Q.motes(int(w), int(h), colour, count, seed=seed)
    R.add_image(Image.new("RGBA", m.size), x, y, emit=m, depth=-1e6, name="motes")


def hero(R, x, y, flip=False, clip="1HSwordIdle", lamp=True):
    d = R.actor(G.hero(clip, 0, flip), x, y, "hero")
    if lamp:
        R.light(x, y + 10, (255, 236, 170), 0.55)
        R.lamp(x, y + 8, (255, 228, 180), 30, 0.55)
    return d


def hero_behind(R, x, flip=False):
    """Put the hero at the closest spot straight behind whatever stands at x: step back from its footprint until his
    own collider (8 x 3 at the feet) is clear."""
    near = [r for (r, lab, _) in R.solids if r[0] <= x <= r[2]]
    y = min(r[1] for r in near) if near else R.fy0
    while y < R.fy1:
        rect = (x - 4, y - 1.5, x + 4, y + 1.5)
        if R.free(rect, R.rects) and R.walkable(x, y):
            return hero(R, x, y, flip)
        y += 0.5
    return None


def monster(R, sheet, x, y, flip=False, frame=0):
    return R.actor(G.mod_sprite(sheet, frame, flip, prefer=()), x, y, "monster")


def floor_detail(R, n, crack=(14, 8, 18), stain=(16, 10, 20), cracks=8, grit=0.006, stains=0.2, seed=0, edge=0.42):
    R.floor_fx += [D.stains(n, 13, stains, stain), D.cracks(R, cracks, seed=seed, dark=crack, k=0.5),
                   D.grit(R, grit, seed=seed + 1), D.edge_shade(R, k=edge), D.contact_shade(R)]


def windows(R):
    """x of each lit window slit in the back wall art (bright columns in its middle rows)."""
    out = []
    for d in R.draws:
        if d.kind != "wall" or "BackWallArt" not in d.name or d.im.height < 25:
            continue
        im = d.im.convert("RGB")
        rows = range(int(im.height * 0.3), int(im.height * 0.75))
        col = [sum(lum(im.getpixel((x, y))) for y in rows) / len(rows) for x in range(im.width)]
        avg = sum(col) / len(col)
        for x in range(2, im.width - 2):
            if col[x] > avg * 1.22 and col[x] >= max(col[x - 2:x + 3]):
                wx = d.left + x
                if not out or wx - out[-1] > 8:
                    out.append(wx)
    # one shaft per window bay
    keep = []
    for x in out:
        if not keep or x - keep[-1] > 34:
            keep.append(x)
    return keep


# ------------------------------------------------------------------ biomes
BIOMES = []


def biome(**info):
    def deco(fn):
        BIOMES.append((fn, info))
        return fn
    return deco


STONE_GREEN = dict(h=0.40, sk=0.55, vk=0.98, hmix=0.85)
BRINE = dict(deep=(10, 36, 46), shallow=(40, 92, 96), foam=(170, 210, 196), sheen=(190, 236, 226))
SEA = (150, 210, 220)


def drowned(R, n):
    R.recolours.append((kinds("floor", "decal"), hsv_set(**STONE_GREEN)))
    R.recolours.append((kinds("wall"), hsv_set(h=0.44, sk=0.6, vk=0.86, hmix=0.8)))
    R.recolours.append((kinds("object", name=("Column", "Vase", "Fountain", "Carcophegus", "Well")), hsv_set(h=0.42, sk=0.35, vk=0.9, hmix=0.7)))
    R.recolours.append((kinds("object", name=("Bench", "Chair", "Table", "Cabinet", "Barrel")), hsv_set(h=0.08, sk=0.7, vk=0.72, hmix=0.3)))
    R.recolours.append((kinds("decal", "object", name=("Plant",)), hsv_set(h=0.36, sk=1.1, vk=0.9, hmix=1.0)))
    R.wall_fx.append(D.creep(n, (52, 92, 76), 7, 0.6, None, 0.55, speck=(120, 170, 150)))
    R.wall_fx.append(D.stains(n, 6, 0.3, (10, 30, 30), 0.55))
    R.floor_fx.append(D.creep(n, (64, 104, 84), 10, 0.64, D.near_top(R), 0.5, speck=(150, 190, 160)))
    floor_detail(R, n, crack=(10, 24, 22), stain=(10, 26, 24), cracks=10, seed=3)
    R.dark = (0.6, 0.68, 0.72)
    R.auto_lamps = ((255, 190, 120), 34, 0.8)


def shore(R, water, n, count=14):
    """Shells, starfish, weed and barnacles along a waterline."""
    near = lambda x, y: -9 < water(x, y) < -2
    decals(R, lambda i: [Q.shell(seed=i), Q.starfish(seed=i), Q.barnacles(10, seed=i)][i % 3], count, ok=near)
    R.scatter([("FloorPlantDebris", 2), ("FloorPlantSprout", 1)], 6, kind="decal")


@biome(name="Drowned Nave", tag="A cathedral the sea took back", monsters="Bel'Mora, the Drowned Bell, big swimmers",
       look="The Crypt's gothic rooms in grey-green, brine over the low side of every room, cold light falling "
            "through the windows onto pews and columns crusted with barnacles.",
       hazard="The tide floods across the room and drains back on a slow cycle. Brine slows the hero; Bel'Mora's monsters "
              "heal in it.",
       made="Crypt rooms and props recoloured. New: the brine floor, kelp, barnacles, shells, light shafts, darkness.")
def drowned_nave():
    out = []
    n = Noise(1)
    # 1. the flooded nave
    R = G.Room("RoomCryptMedium2", seed=11)
    drowned(R, n)
    water = wavy_band(-15, amp=4, freq=0.07, n=n)
    R.floor_fx.insert(0, liquid(water, ripple=0.08, n=n, **BRINE))
    R.block(lambda x, y: water(x, y) > -3)
    monster(R, "BelDrownedBell", 70, -30, flip=True)
    hero(R, -24, -6)
    for x in (-84, -42, 0, 42, 84):
        R.put("ColumnCrypt", x, 23)
        R.add_image(Q.barnacles(12, seed=int(x)), x + 1, 20, kind="decal")
    for x in (-62, -22, 22, 62):
        R.put("PropGhostTrap_ShortBenchHoriz", x - 7, 6)
        R.put("PropGhostTrap_ShortBenchHoriz", x + 8, 6)
    R.put("PropGhostTrap_ShortBenchAngleA", 100, 4)
    R.put("PropActionableGhost_Fire_CandelabraCrypt", -104, 24)
    R.put("PropActionableGhost_Fire_CandelabraCryptFlipped", 104, 24)
    for x in (-100, -50, 30, 96):
        stand(R, Q.kelp(R.rnd.randint(10, 16), seed=x), x, -22, tries=8, spread=6,
              ok=lambda x, y: water(x, y) > 1, force="wet")
    R.scatter([("PropGhostTrap_Vase1", 2), ("PropGhostTrap_Vase3", 2), ("PropCandles2", 2), ("PropCandles4", 1)], 8)
    R.scatter([("FloorRot", 2), ("FloorBricks", 2), ("FloorSplotchSmall", 1)], 10, kind="decal")
    shore(R, water, n)
    for wx in windows(R):
        R.shaft(wx, R.fy1 + 18, 8, 50, SEA, 0.34, slant=0.35)
        R.lamp(wx + 10, R.fy1 - 22, SEA, 26, 0.35)
    out.append(("The Flooded Nave", "The Crypt's long gothic hall, its lower half under brine. Pews in rows, a colonnade crusted "
                "with barnacles, cold light slanting through the windows.", R))

    # 2. the font: a round pool, the fountain at its heart, columns round it
    R = G.Room("RoomCryptLarge2c", seed=12)
    drowned(R, n)
    pool = ellipse(0, -6, 44, 22, n, 0.12)
    R.floor_fx.insert(0, liquid(pool, ripple=0.07, n=n, **BRINE))
    def ring(x, y, c):
        d = math.hypot(x / 52, (y + 6) / 28)
        if 0.88 < d < 1.02 and pool(x, y) <= 0:
            a = math.atan2((y + 6) / 28, x / 52)
            k = int((a + 4) * 5) % 2
            return mix(c, (120, 140, 128) if k else (90, 106, 98), 0.55 if d > 0.9 else 0.3)
        return None
    R.floor_fx.insert(1, ring)
    R.block(lambda x, y: math.hypot(x / 50, (y + 6) / 27) < 1.0)
    hero(R, 70, -30, flip=True)
    R.actor(G.mod_sprite("BelKraken", 0, False, prefer=()), -12, -16, "monster")
    R.put("PropActionable_Fountain", 0, -8, force=True)
    R.wet_ok = ("PropActionable_Fountain",)     # the font's fountain stands in its pool on purpose
    for i in range(6):
        a = i / 6 * math.tau + 0.3
        x, y = 74 * math.cos(a), -6 + 38 * math.sin(a)
        if R.put("ColumnCrypt", x, y):
            R.add_image(Q.barnacles(12, seed=i), x + 1, y - 3, kind="decal")
    for x in (-92, 92):
        R.put("PropActionableGhost_Fire_CandelabraCrypt", x, 30)
    R.scatter([("PropGhostTrap_Vase1", 2), ("PropCandles3", 3), ("PropCandles1", 2), ("PropGhostTrap_ShortBenchVert", 1)], 10)
    R.scatter([("FloorRot", 2), ("FloorSplotchSmall", 2)], 10, kind="decal")
    shore(R, pool, n, 16)
    for (x, y) in ((-30, -14), (26, -2), (10, -22)):
        stand(R, Q.kelp(12, seed=x), x, y, ok=lambda x, y: pool(x, y) > 2, tries=8, spread=6, force="wet")
    for wx in windows(R):
        R.shaft(wx, R.fy1 + 20, 8, 56, SEA, 0.32, slant=0.3)
    R.lamp(0, -6, (110, 200, 200), 50, 0.4)
    out.append(("The Font", "A round pool where the floor should be, the fountain at its heart, a ring of columns, kelp "
                "standing in the shallows.", R))

    # 3. the bell chapel: the floor gone through to the sea
    R = G.Room("RoomCryptSmall2", seed=13)
    drowned(R, n)
    hole = union(ellipse(30, -16, 26, 13, n, 0.35), ellipse(56, -24, 14, 8, n, 0.4))
    R.floor_fx.insert(0, liquid(hole, ripple=0.07, n=n, **BRINE))
    R.block(lambda x, y: hole(x, y) > -3)
    monster(R, "BelSlimeHag", 30, -20)
    hero(R, -44, -14)
    R.put("PropActionable_Feature_Carcophegus", -40, 21)
    R.put("PropActionableGhost_Fire_CandelabraCrypt", -64, 22)
    R.put("PropActionableGhost_Fire_CandelabraCryptFlipped", -16, 22)
    R.put("Carpet2", -40, 2, kind="decal")
    R.scatter([("PropGhostTrap_Vase1TopWall", 2), ("PropCandles1", 2), ("PropCandles5", 1),
               ("PropGhostTrap_ShortBenchVert", 1), ("PropGhostTrap_Stool", 1)], 10)
    R.scatter([("FloorRotB", 2), ("FloorBricks", 1)], 6, kind="decal")
    shore(R, hole, n, 12)
    for (x, y) in ((18, -12), (44, -20)):
        stand(R, Q.kelp(14, seed=x), x, y, ok=lambda x, y: hole(x, y) > 2, tries=8, spread=5, force="wet")
    for wx in windows(R):
        R.shaft(wx, R.fy1 + 18, 8, 48, SEA, 0.34, slant=0.3)
    out.append(("The Bell Chapel", "A small chapel whose floor has given way to the sea, a runner leading to the sarcophagus, "
                "shells washed up round the hole.", R))
    return out


def ashen(R, n):
    R.recolours.append((kinds("floor", "decal"), hsv_set(h=0.08, sk=0.3, vk=0.8, hmix=0.6)))
    R.recolours.append((kinds("wall"), hsv_set(h=0.06, sk=0.4, vk=0.66, hmix=0.5)))
    R.recolours.append((kinds("object", name=("Tree",)), hsv_set(h=0.11, sk=0.16, vk=1.4, hmix=1.0)))
    R.recolours.append((kinds("object", name=("Tombstone", "Headstone")), hsv_set(h=0.6, sk=0.2, vk=0.9, hmix=0.4)))
    R.recolours.append((kinds("object", "decal", name=("BonePile", "FloorBones")), hsv_set(h=0.11, sk=0.32, vk=1.15, hmix=0.8)))
    R.floor_fx.append(D.creep(n, (70, 64, 56), 8, 0.6, None, 0.5))
    R.wall_fx.append(D.stains(n, 7, 0.3, (10, 6, 8), 0.5))
    floor_detail(R, n, crack=(20, 14, 12), stain=(14, 10, 10), cracks=10, seed=5, stains=0.25)
    mist = Noise(77)
    R.floor_fx.append(lambda x, y, c: mix(c, (150, 146, 160), 0.22 * min(1, (mist.fbm(x, y * 1.6, 16) - 0.5) * 4))
                      if mist.fbm(x, y * 1.6, 16) > 0.5 else None)
    R.dark = (0.42, 0.4, 0.46)
    R.auto_lamps = ((255, 150, 90), 36, 0.9)


LANT = (255, 184, 104)


def tree_lanterns(R, ds, k=2, seed=0):
    """Hang lanterns from a tree's branch tips: opaque pixels in its upper half with open air below them."""
    rnd = random.Random(seed)
    obj = [d for d in (ds or []) if d.kind == "object"]
    if not obj:
        return
    d = max(obj, key=lambda d: d.im.width * d.im.height)
    im = d.im
    a = im.split()[3].load()
    cands = []
    for y in range(int(im.height * 0.25), int(im.height * 0.62)):
        for x in range(2, im.width - 2):
            if a[x, y] and all(not a[x, yy] for yy in range(y + 1, min(im.height, y + 12))):
                cands.append((x, y))
    rnd.shuffle(cands)
    used = []
    for (x, y) in cands:
        if len(used) >= k:
            break
        if any(abs(x - u) < 10 for u, _ in used):
            continue
        used.append((x, y))
        wx, wy = d.left + x + 0.5, d.bottom + im.height - y
        li, le = Q.lantern(LANT, seed=x, chain=rnd.randint(2, 5))
        R.add_image(li, wx, wy - li.height, emit=le, depth=d.depth - 0.5)
        R.lamp(wx, wy - li.height + 3, LANT, 40, 0.75)
        R.light(wx, wy - li.height + 4, LANT, 0.6, 0.3)


@biome(name="Bone Orchard", tag="A grove grown from the dead", monsters="Ossivar, the Carrion Saint, anything that eats bones",
       look="The Dungeon's rooms gone ash-grey and dark, the game's dead trees bleached to bone with lanterns in their "
            "branches, graves and bone piles between them, mist along the ground.",
       hazard="Dark outside the lantern light. A tree hit hard drops its lanterns and the room goes darker. Bone piles "
              "mean Ossivar's monsters start every fight armed.",
       made="Dungeon, Crypt and Caves rooms and props recoloured. New: lanterns, graves, skulls, mist, darkness.")
def bone_orchard():
    out = []
    n = Noise(2)
    # 1. the grove
    R = G.Room("RoomLarge5", seed=21)
    ashen(R, n)
    monster(R, "OssTombwright", 38, -22)
    hero(R, -30, -22)
    trees = [("PropActionable_Tree5", -60, -4), ("PropActionable_Tree2", 62, 4), ("PropActionable_Tree1", 6, -34),
             ("PropActionable_Tree3", -18, 24), ("PropActionable_Tree6", 76, -34), ("PropActionable_Tree1", -78, 28)]
    for i, (t, x, y) in enumerate(trees):
        tree_lanterns(R, R.put(t, x, y), 1 + i % 2, seed=i)
    for i in range(5):
        stand(R, Q.grave(R.rnd.randint(12, 16), seed=i), *(spot(R) or (0, 0)), tries=10, spread=40)
    R.scatter([("PropActionable_Tombstone1", 3), ("PropActionable_Tombstone3", 3), ("PropActionable_Tombstone5", 2),
               ("PropActionable_Headstone1", 1)], 10)
    scatter_own(R, lambda i: Q.bone_pile(R.rnd.randint(12, 18), seed=i), 4)
    R.scatter([("FloorBones1", 2), ("FloorBones3", 2), ("FloorBones5", 2), ("FloorBones6", 1)], 18, kind="decal")
    decals(R, lambda i: Q.skull(seed=i), 8)
    R.floor_fx.append(D.cracks(R, 10, seed=8, dark=(40, 26, 18), k=0.5, length=(14, 30)))   # roots under the dust
    out.append(("The Grove", "Bone-white trees as pillars to fight round, lanterns in their branches, fresh graves and "
                "headstones between them.", R))

    # 2. the ossuary gate
    R = G.Room("RoomCryptCorridor1", seed=22)
    ashen(R, n)
    R.recolours.append((kinds("wall"), hsv_set(h=0.08, sk=0.3, vk=0.72, hmix=0.6)))
    monster(R, "OssCoffinBearer", 66, R.fy0 + 4, flip=True)
    hero(R, -54, R.fy0 + 6)
    for xx in (-80, -10, 60):
        R.put("PropActionable_Feature_Altar_Skull", xx, R.fy1 - 9)
    x = R.fx0 + 10
    while x < R.fx1 - 8:
        stand(R, Q.bone_pile(R.rnd.randint(14, 20), seed=int(x)), x, R.fy1 - 6)
        x += R.rnd.randint(14, 20)
    R.scatter([("FloorBones1", 2), ("FloorBones5", 2), ("PropActionable_Body1", 1)], 14, kind="decal")
    decals(R, lambda i: Q.skull(seed=i + 20), 10)
    hang(R, lambda i, h: (Q.chain(int(h * R.rnd.uniform(0.4, 0.8)), seed=i), None), step=30, start=20)
    for x in (-110, -30, 40, 110):
        im, em = Q.lantern((255, 120, 80), seed=int(x), chain=4)
        sp = R.wall_span(x)
        if sp:
            R.add_image(im, x, sp[1] - im.height - 2, emit=em, depth=R.fy1 + 30)
            R.lamp(x, R.fy1 + 2, (255, 120, 80), 34, 0.9)
    out.append(("The Ossuary Gate", "A long corridor walled in bone piles, chains down the wall, skull altars burning red "
                "along it.", R))

    # 3. the root shrine
    R = G.Room("RoomCavesLarge1", seed=23)
    ashen(R, n)
    monster(R, "OssOssuary", -62, -26)
    hero(R, 60, -24, flip=True)
    tree_lanterns(R, R.put("PropActionable_Tree5", 0, 8, force=True), 4, seed=9)
    for i in range(10):
        a = i / 10 * math.tau
        R.put("PropActionable_Headstone%d" % (1 + i % 2), 54 * math.cos(a), 6 + 28 * math.sin(a))
    R.scatter([("PropActionable_Tombstone2", 2), ("PropActionable_Tombstone4", 2), ("StalagmiteMedium3", 2)], 8)
    scatter_own(R, lambda i: Q.bone_pile(R.rnd.randint(12, 16), seed=i + 50), 3)
    R.scatter([("FloorBones3", 3), ("FloorBones2", 2)], 12, kind="decal")
    decals(R, lambda i: Q.skull(seed=i + 40), 8)
    R.floor_fx.append(D.cracks(R, 14, seed=12, dark=(46, 30, 20), k=0.55, length=(16, 34)))
    hang(R, lambda i, h: Q.wall_roots(12, int(h * 0.6), colour=(120, 104, 92), seed=i), step=46)
    out.append(("The Root Shrine", "The Caves' round chamber, one great bone tree hung with lanterns in a ring of headstones, "
                "its roots under the floor.", R))
    return out


def sooty(R, n):
    R.recolours.append((kinds("floor", "decal"), hsv_set(h=0.04, sk=0.5, vk=0.6, hmix=0.5)))
    R.recolours.append((kinds("wall"), hsv_set(h=0.03, sk=0.65, vk=0.62, hmix=0.4)))
    R.recolours.append((kinds("object", "wall", name=("Tracks", "MineCart", "Minacart", "CartEnd")), hsv_set(h=0.6, sk=0.25, vk=0.75, hmix=0.6)))
    R.recolours.append((kinds("object", name=("CoalPile", "Rock")), hsv_set(h=0.05, sk=0.45, vk=1.25, hmix=0.4)))
    R.wall_fx.append(D.stains(n, 6, 0.4, (6, 4, 4), 0.5))
    floor_detail(R, n, crack=(10, 6, 6), stain=(6, 4, 4), cracks=8, seed=7, stains=0.3)
    R.dark = (0.56, 0.5, 0.5)
    R.auto_lamps = ((255, 140, 70), 38, 0.9)


LAVA = dict(deep=(250, 150, 40), shallow=(200, 70, 20), foam=(255, 230, 140))
MOLTEN = [(150, 40, 12), (210, 86, 22), (244, 140, 44), (252, 196, 90), (255, 236, 170)]
HEAT = (255, 120, 50)


def molten(n):
    """Fill a sprite's opaque pixels with molten metal (crust rafts on a glowing pool)."""
    def go(im):
        im = im.copy(); px = im.load()
        for y in range(im.height):
            for x in range(im.width):
                a = px[x, y][3]
                if not a:
                    continue
                crust = 0.7 * n.v(x, y, 10) + 0.3 * n.v(x, y, 3.5)
                if crust > 0.64:
                    c = mix((38, 30, 30), (70, 56, 50), (crust - 0.64) * 3)
                elif crust > 0.59:
                    c = MOLTEN[4]
                else:
                    c = MOLTEN[max(0, min(4, int(round(1.4 + (n.v(x + 40, y, 6) - 0.5) * 3 + (crust - 0.3) * 3))))]
                px[x, y] = c + (a,)
        return im
    return go


def molten_below(n, top):
    """molten(), but only up to the floor's top edge: above it the pit is dark rock going back under the wall."""
    go = molten(n)
    def f(im, d):
        im = go(im)
        px = im.load()
        for y in range(im.height):
            wy = d.bottom + im.height - y
            if wy > top:
                for x in range(im.width):
                    if px[x, y][3]:
                        k = min(1.0, (wy - top) / 6)
                        px[x, y] = mix(px[x, y][:3], (16, 10, 10), 0.6 + 0.4 * k) + (px[x, y][3],)
        return im
    f.wants_draw = True
    return f


def hot_cracks(R, mask, n, count=10, seed=0):
    """Glowing cracks running out from molten metal into the floor."""
    rnd = random.Random(seed)
    pts = {}
    for _ in range(count):
        for _t in range(40):
            x, y = rnd.uniform(R.fx0, R.fx1), rnd.uniform(R.fy0, R.fy1)
            if -3 < mask(x, y) < 0:
                break
        if not (-3 < mask(x, y) < 0):
            continue
        # head away from the metal
        a = math.atan2(-(mask(x, y + 1) - mask(x, y - 1)), -(mask(x + 1, y) - mask(x - 1, y)))
        for i in range(rnd.randint(4, 10)):
            a += rnd.uniform(-0.5, 0.5)
            x += math.cos(a); y += math.sin(a) * 0.6
            if mask(x, y) > 0:
                break
            pts[(int(x), int(y))] = max(pts.get((int(x), int(y)), 0), 1 - i / 10)
    def g(x, y):
        v = pts.get((int(x), int(y)))
        if v:
            return mix(MOLTEN[0], MOLTEN[3], v) + (int(255 * (0.25 + 0.7 * v)),)
        return None
    return g


@biome(name="Ember Works", tag="The foundry below the mines", monsters="Vhorrul's fire monsters, anything heavy and armoured",
       look="The Mines gone soot-black, its tracks and carts still in place. The chasms and pits are full of molten "
            "slag that lights the room from below, and anvils and crucibles stand where the miners worked.",
       hazard="The pour: every few seconds a pulse of heat runs down the channels (a bright tell first), burning anything "
              "on them. Crucibles tip when hit.",
       made="Mines rooms and props recoloured; the rooms' own chasms and pits become slag. New: molten floor, anvils, "
            "crucibles, slag, chains, sparks, darkness.")
def ember_works():
    out = []
    n = Noise(3)
    # 1. the casting hall: a channel of metal along the bottom, a pool in the corner, away from the tracks
    R = G.Room("RoomMinesLarge1dTracks", seed=31)
    sooty(R, n)
    chan = union(lambda x, y: 3.2 - abs(y + 42 - 1.6 * math.sin(x * 0.09)) if x > -60 else -9,
                 ellipse(-78, -38, 20, 9, n, 0.3))
    R.floor_fx.insert(0, liquid(chan, n=n, keep=0.05, **LAVA))
    R.floor_glow.append(liquid_glow(chan, MOLTEN, n, edge=MOLTEN[4]))
    R.floor_glow.append(hot_cracks(R, chan, n, 16, seed=1))
    R.block(lambda x, y: chan(x, y) > -4)
    for x in range(-96, 100, 16):
        if chan(x, -42) > 0 or chan(x, -38) > 0:
            R.lamp(x, -38, HEAT, 30, 0.8)
    monster(R, "VhPyreWarden", 60, -22, flip=True)
    hero(R, -36, -16)
    stand(R, Q.furnace(1), -50, 38, lamp=(HEAT, 46, 1.0), force=True)
    stand(R, Q.anvil(1), 20, 26, tries=6)
    stand(R, Q.anvil(2), 74, 16, tries=6)
    stand(R, Q.crucible(seed=1), -10, 30, lamp=(HEAT, 30, 0.8), tries=6)
    stand(R, Q.crucible(seed=2), -90, 6, lamp=(HEAT, 30, 0.8), tries=6)
    scatter_own(R, lambda i: Q.slag(R.rnd.randint(3, 6), seed=i), 6, lamp=(HEAT, 16, 0.6),
                ok=lambda x, y: -12 < chan(x, y) < -4)
    R.scatter([("PropGhostTrap_MineCart1", 2), ("PropGhostTrap_MineCart5", 2), ("PropsMinesCoalPile1", 2), ("PropsMinesCoalPile2", 2),
               ("PropGhostTrap_MinesCrate1", 2), ("PropsMinesRock2", 2), ("PropGhostTrap_Barrel", 1)], 12)
    R.scatter([("FloorCoalDebris", 3), ("FloorCoalDebrisLarge", 2), ("FloorStrayBoards", 1)], 14, kind="decal")
    hang(R, lambda i, h: (Q.chain(int(h * R.rnd.uniform(0.5, 0.9)), seed=i), None), step=34, start=24)
    motes(R, -100, -48, 200, 60, (255, 170, 80), 40, seed=1)
    out.append(("The Casting Hall", "The mines' crossing tracks, molten metal along the low side and pooled in the corner, "
                "anvils and crucibles where the carts stop.", R))

    # 2. the slag pit
    R = G.Room("RoomMinesLarge3", seed=32)
    sooty(R, n)
    R.recolours.insert(0, (lambda d: d.name.endswith(":mines_room_2blackout"), molten_below(n, R.fy1 - 4)))
    R.recolours.insert(0, (lambda d: "blackoutEdge" in d.name, hsv_set(h=0.06, sk=1.0, vk=1.0, sadd=0.6)))
    R.block(lambda x, y: -14 < x < 14)
    for y in range(-46, 40, 12):
        R.lamp(3, y, HEAT, 40, 1.0)
        R.light(3, y, HEAT, 0.9, 0.4)
    pit = lambda x, y: 6 - abs(x - 3)
    R.floor_glow.append(hot_cracks(R, pit, n, 14, seed=3))
    monster(R, "VhAshSeraph", -50, -18)
    hero(R, 50, -24, flip=True)
    stand(R, Q.crucible(seed=3), -60, 30, lamp=(HEAT, 30, 0.8), tries=8)
    stand(R, Q.anvil(3), 60, 30, tries=8)
    scatter_own(R, lambda i: Q.slag(R.rnd.randint(3, 6), seed=i + 10), 8, lamp=(HEAT, 16, 0.6),
                ok=lambda x, y: 14 < abs(x - 3) < 26)
    R.scatter([("PropsMinesCoalPile1", 2), ("PropGhostTrap_MineCart5", 2), ("PropActionable_CookingPot2", 1), ("PropGhostTrap_LargeCrate", 1),
               ("PropsMinesRock2", 2), ("PropsMinesRock3", 2), ("PropGhostTrap_MinesCrate2", 1)], 14)
    R.scatter([("FloorCoalDebris", 3), ("FloorCoalDebrisLarge", 1)], 12, kind="decal")
    motes(R, -14, -48, 34, 96, (255, 190, 90), 45, seed=2)
    out.append(("The Slag Pit", "The mines room with a chasm down its middle, the chasm a river of slag, the light all "
                "from below.", R))

    # 3. the bellows room
    R = G.Room("RoomMinesLarge2", seed=33)
    sooty(R, n)
    R.recolours.insert(0, (lambda d: d.name.endswith(":mines_room_5blackout"), molten(n)))
    R.recolours.insert(0, (lambda d: "blackoutEdge" in d.name, hsv_set(h=0.06, sk=1.0, vk=1.0, sadd=0.6)))
    R.block(lambda x, y: -52 < x < 52 and -24 < y < 32)
    for x in (-40, -20, 0, 20, 40):
        R.lamp(x, 16, HEAT, 40, 0.95)
        R.light(x, 16, HEAT, 0.9, 0.4)
    monster(R, "VhRenderer", 0, -38)
    hero(R, 72, 0, flip=True)
    stand(R, Q.furnace(2), 0, 37, lamp=(HEAT, 46, 1.0), force=True)
    stand(R, Q.anvil(4), -70, 26, tries=6)
    stand(R, Q.crucible(seed=4), 64, 28, lamp=(HEAT, 30, 0.8), tries=6)
    R.scatter([("PropsMinesCoalPile1", 2), ("PropGhostTrap_MineCart1", 2), ("PropGhostTrap_Barrel", 2), ("PropGhostTrap_MinesCrate3", 2),
               ("PropsMinesRock1", 2)], 12)
    scatter_own(R, lambda i: Q.slag(R.rnd.randint(3, 5), seed=i + 20), 5, lamp=(HEAT, 16, 0.6))
    R.scatter([("FloorCoalDebris", 3)], 10, kind="decal")
    hang(R, lambda i, h: (Q.chain(int(h * R.rnd.uniform(0.5, 0.9)), seed=i + 5), None), step=30, start=16)
    motes(R, -52, -24, 104, 70, (255, 180, 80), 40, seed=3)
    out.append(("The Bellows Room", "The mines room with two pits, each a crucible of molten metal, the furnace between "
                "them on the back wall.", R))
    return out


MAG, TEALG = (150, 62, 128), (110, 255, 220)
OCH, AMBG = (176, 104, 60), (255, 196, 96)
PALE, BLUEG = (214, 210, 222), (150, 200, 255)
SLIME = dict(deep=(26, 48, 30), shallow=(70, 104, 44), foam=(150, 196, 96), sheen=(200, 240, 140))


def rotten(R, n):
    R.recolours.append((kinds("floor", "decal"), hsv_set(h=0.86, sk=0.42, vk=0.84, hmix=0.55)))
    R.recolours.append((kinds("wall"), hsv_set(h=0.82, sk=0.45, vk=0.7, hmix=0.6)))
    R.recolours.append((kinds("object", name=("Stalagmite",)), hsv_set(h=0.8, sk=0.3, vk=1.05, hmix=0.6)))
    R.recolours.append((kinds("decal", "object", name=("Plant",)), hsv_set(h=0.47, sk=1.2, vk=1.15, hmix=1.0)))
    R.wall_fx.append(D.creep(n, (58, 96, 80), 6, 0.58, None, 0.6))
    R.floor_fx.append(D.creep(n, (62, 94, 74), 9, 0.63, D.near_top(R), 0.5, speck=(120, 200, 160)))
    floor_detail(R, n, crack=(16, 8, 20), stain=(20, 10, 24), cracks=7, seed=9, stains=0.22)
    R.dark = (0.48, 0.44, 0.58)
    R.auto_lamps = ((200, 255, 210), 30, 0.6)


def cap_lamp(R, x, y, h, glow):
    R.lamp(x, y + h * 0.7, glow, h * 1.5, 0.5)
    R.light(x, y + h * 0.75, glow, 0.7, 0.15 + h / 170)


def caps(R, spots):
    """Giant caps: (x, y, height, kind, cap colour, glow colour)."""
    for i, (x, y, h, k, c, g) in enumerate(spots):
        if k == "ink":
            made = Q.ink_cap(h, c, g, seed=i)
        else:
            made = Q.giant_cap(h, c, g, seed=i * 7 + 1 + int(x), kind=k, stem=(160, 146, 144))
        if stand(R, made, x, y, tries=6, spread=5):
            cap_lamp(R, x, y, h, g)
            motes(R, x - h * 0.8, y + h * 0.2, h * 1.6, h * 1.2, g, max(1, int(h / 8)), seed=int(x))


def rot_floor(R, n, pins=10, threads=5):
    for s in range(pins):
        decals(R, lambda i, s=s: Q.pins(MAG if s % 3 else OCH, TEALG if s % 3 else AMBG, seed=s), 1)
    if threads:
        th = Noise(91)
        R.floor_fx.append(lambda x, y, c: mix(c, (196, 186, 196), 0.16) if th.v(x, y, 11) > 0.6 and abs(th.v(x + 30, y, 5) - 0.5) < 0.03 else None)


@biome(name="Rot Gardens", tag="Caves gone soft with fungus", monsters="Sylvene's spore and rot monsters, slimes",
       look="The Caves and the swamp room in bruise and moss tones, gone dark. Giant caps tower over the floor and light "
            "it, magenta with teal gills, ochre with amber spots, pale ink caps dripping blue. Roots hang down the walls, "
            "slime stands in the hollows, spores drift.",
       hazard="Spore drifts hang in the air and slowly move; walking through dazes the hero. A cap that is hit bursts "
              "into a fresh cloud.",
       made="Caves, swamp and corridor rooms and props recoloured. New: the giant caps, logs, egg sacs, roots, pins, "
            "mycelium, slime, spores, darkness.")
def rot_gardens():
    out = []
    n = Noise(4)
    # 1. the cap cavern
    R = G.Room("RoomCavesLarge1", seed=41)
    rotten(R, n)
    pool = ellipse(-56, -26, 22, 9, n, 0.5)
    R.floor_fx.insert(0, liquid(pool, n=n, ripple=0.08, keep=0.12, **SLIME))
    R.floor_glow.append(lambda x, y: (150, 230, 90, 150) if pool(x, y) > 2 and n.v(x * 1.7, y * 1.7, 2) > 0.8 else None)
    R.block(lambda x, y: pool(x, y) > -2)
    monster(R, "SylPuffball", -4, -16)
    caps(R, [(-64, 14, 42, "parasol", MAG, TEALG), (58, 22, 38, "parasol", MAG, TEALG), (8, 34, 28, "bell", OCH, AMBG),
             (80, -26, 24, "bell", OCH, AMBG), (-24, -40, 18, "parasol", MAG, TEALG), (-90, -12, 24, "ink", PALE, BLUEG),
             (34, -12, 20, "ink", PALE, BLUEG), (92, 6, 16, "ink", PALE, BLUEG)])
    hero_behind(R, 56)     # as close behind the right-hand cap's stem as his collider allows
    for i, (x, y) in enumerate(((30, -36), (-2, 4), (72, 2))):
        stand(R, Q.pod_cluster(seed=i + 3), x, y, tries=6, lamp=((120, 255, 210), 14, 0.4))
    stand(R, Q.rotten_log(44, colour=(86, 66, 62), cap=MAG, glow=1, seed=9), -22, 28, tries=6)
    R.scatter([("StalagmiteMedium3", 3), ("StalagmiteSmall2", 2), ("StalagmiteLarge2", 2), ("StalagmiteMedium5", 2)], 7)
    R.scatter([("FloorPlantSprout", 2), ("FloorPlantDebris", 2)], 8, kind="decal")
    rot_floor(R, n)
    hang(R, lambda i, h: Q.wall_roots(18, int(h * 0.85), colour=(96, 74, 86), seed=i, tips=TEALG, moss=(60, 96, 74)), step=20)
    out.append(("The Cap Cavern", "The Caves' round chamber under a canopy of giant caps that are its only light. The hero "
                "stands behind a stem: footprints are at the base, so tall things hide whoever walks behind them.", R))

    # 2. the mire
    R = G.Room("RoomMed1cSwampRoom", seed=42)
    rotten(R, n)
    R.recolours.append((kinds("floor"), hsv_set(h=0.3, sk=0.85, vk=0.82, hmix=0.25)))
    slime = union(ellipse(-28, -18, 30, 12, n, 0.5), ellipse(10, -30, 18, 7, n, 0.5))
    R.floor_fx.insert(0, liquid(slime, n=n, ripple=0.08, keep=0.12, **SLIME))
    R.floor_glow.append(lambda x, y: (150, 230, 90, 140) if slime(x, y) > 2 and n.v(x * 1.7, y * 1.7, 2) > 0.8 else None)
    R.block(lambda x, y: slime(x, y) > -2)
    monster(R, "SylCarrionLily", -26, -16)
    hero(R, 30, -4)
    caps(R, [(50, 22, 30, "parasol", MAG, TEALG), (-58, 24, 22, "bell", OCH, AMBG), (60, -28, 16, "ink", PALE, BLUEG),
             (-62, -6, 18, "ink", PALE, BLUEG), (6, 28, 14, "parasol", MAG, TEALG)])
    stand(R, Q.rotten_log(36, colour=(80, 64, 58), cap=OCH, glow=1, seed=4), -14, 26, tries=8)
    for i, (x, y) in enumerate(((22, 12), (-40, 6))):
        stand(R, Q.pod_cluster(seed=i + 7), x, y, tries=6, lamp=((120, 255, 210), 14, 0.4))
    R.scatter([("PropActionable_CookingPot2_Poisoned", 1), ("StalagmiteMedium1", 2), ("StalagmiteSmall3", 2)], 5)
    for (x, y) in ((-34, -20), (-10, -14), (14, -30)):
        R.add_image(Q.pins(OCH, AMBG, seed=x, count=5, spread=5)[0], x, y, kind="decal")
    rot_floor(R, n, 8, 4)
    hang(R, lambda i, h: Q.wall_roots(18, int(h * 0.85), colour=(96, 74, 86), seed=i + 30, tips=TEALG, moss=(60, 96, 74)), step=20)
    out.append(("The Mire", "The game's swamp room gone sour: slime in the hollows, a log across the back, caps round "
                "the edge.", R))

    # 3. the mycelium tunnel
    R = G.Room("RoomCorridorBendy", seed=43)
    rotten(R, n)
    def mat(x, y, c):
        k = n.v(x, y, 9)
        if k > 0.56 and R.on_floor(x, y):
            thread = abs(n.v(x + 30, y, 4) - 0.5) < 0.05
            return mix(c, (200, 190, 196), 0.42 if thread else 0.12 + (k - 0.56) * 0.5)
        return None
    R.floor_fx.insert(0, mat)
    R.floor_glow.append(lambda x, y: (140, 255, 220, 170) if n.v(x, y, 9) > 0.6 and abs(n.v(x + 30, y, 4) - 0.5) < 0.012 else None)
    monster(R, "SylBriarChampion", 34, R.fy0 + 10, flip=True)
    hero(R, -44, 10)
    caps(R, [(R.fx0 + 16, 12, 30, "parasol", MAG, TEALG), (R.fx1 - 20, -2, 26, "bell", OCH, AMBG),
             (2, R.fy0 + 10, 18, "ink", PALE, BLUEG), (-60, -30, 14, "ink", PALE, BLUEG), (60, -34, 16, "parasol", MAG, TEALG)])
    for i in range(4):
        p = spot(R)
        if p:
            stand(R, Q.pod_cluster(seed=i + 11), p[0], p[1], tries=6, spread=20, lamp=((120, 255, 210), 14, 0.4))
    R.scatter([("StalagmiteSmall1", 2), ("StalagmiteMedium2", 2)], 6)
    rot_floor(R, n, 10, 6)
    hang(R, lambda i, h: Q.wall_roots(18, int(h * 0.85), colour=(96, 74, 86), seed=i + 60, tips=TEALG, moss=(60, 96, 74)), step=18)
    out.append(("The Mycelium Tunnel", "The bending corridor, a mat of mycelium across it with threads that glow, egg sacs "
                "in the corners.", R))
    return out


def walnut(R, n):
    R.recolours.append((kinds("floor", "decal"), hsv_set(h=0.07, sk=1.1, vk=0.72, hmix=0.6)))
    R.recolours.append((kinds("wall"), hsv_set(h=0.05, sk=1.05, vk=0.7, hmix=0.6)))
    R.recolours.append((kinds("decal", "object", name=("Carpet",)), hsv_set(h=0.99, sk=1.4, vk=1.0, hmix=1.0)))
    R.wall_fx.append(D.stains(n, 6, 0.25, (20, 10, 6), 0.55))
    floor_detail(R, n, crack=(20, 10, 6), stain=(24, 12, 6), cracks=6, seed=11, stains=0.2)
    R.dark = (0.5, 0.44, 0.42)
    R.auto_lamps = ((255, 186, 110), 40, 0.95)


INK = dict(deep=(8, 10, 18), shallow=(22, 26, 42), foam=(60, 66, 96), sheen=(120, 130, 180))


def shelf_row(R, y, x0, x1, names, gap=1):
    """A row of shelves side by side, each its own sprite's width apart."""
    x = x0
    while x < x1:
        nm = R.rnd.choice(names)
        g = G.BYNAME[nm][0]
        bx0, by0, bx1, by1 = G.prefab_size(g)
        if R.put(nm, x - bx0, y):
            pass
        x += (bx1 - bx0) + gap


@biome(name="Ledger Vaults", tag="An archive that never ends", monsters="Jinx's tricksters and gamblers, the Steward",
       look="The Crypt's rooms in warm walnut, the game's bookshelves and cabinets set out in rows with aisles between, "
            "red runners, candlelit reading tables, books stacked on the floor and pages and cards scattered everywhere.",
       hazard="Shelves fall: a big monster that charges a shelf topples it, crushing what is behind and opening a new "
              "path. Ink pools hide anything standing in them.",
       made="Crypt rooms and the game's own library props, recoloured. New: book stacks, pages, cards, ink, darkness.")
def ledger_vaults():
    out = []
    n = Noise(5)
    SHELVES = ["BookshelfCrypt2", "BookshelfCrypt3", "BookshelfCrypt4", "BookshelfCrypt5"]
    # 1. the stacks
    R = G.Room("RoomCryptLarge3", seed=51)
    walnut(R, n)
    ink = ellipse(-84, -30, 14, 6, n, 0.4)
    R.floor_fx.insert(0, liquid(ink, n=n, keep=0.05, ripple=0.04, **INK))
    R.block(lambda x, y: ink(x, y) > -2)
    monster(R, "JinxCardKing", 40, -34)
    hero(R, -22, -32)
    R.put("Carpet2", 0, -30, kind="decal")
    for y, off in ((30, 0), (6, 12)):
        shelf_row(R, y, R.fx0 + 8 + off, -16, SHELVES)
        shelf_row(R, y, 16 + off, R.fx1 - 8, SHELVES)
    for x in (-110, 110):
        R.put("PropActionableGhost_Fire_CandelabraCrypt", x, -10)
    R.put("PropActionableGhost_Fire_CandelabraCrypt", 0, 22)
    R.scatter([("PropGhostTrap_Chair2", 2), ("PropCandles1", 2), ("PropCandles3", 1), ("PropGhostTrap_SmallChestHorizontal", 1)], 6)
    scatter_own(R, lambda i: Q.book_stack(seed=i), 7)
    decals(R, lambda i: Q.papers(seed=i), 8)
    out.append(("The Stacks", "The game's bookshelves set out in rows with an aisle down the middle, a red runner along the "
                "front, books in piles and pages everywhere, ink spilt in the corner.", R))

    # 2. the reading room
    R = G.Room("RoomCryptLarge2c", seed=52)
    walnut(R, n)
    monster(R, "JinxHouseOfCards", 74, -28, flip=True)
    hero(R, -78, -28)
    R.put("Carpet1", -50, -10, kind="decal"); R.put("Carpet1", 50, -10, kind="decal")
    for x in (-56, 0, 56):
        for y in (12, -18):
            if R.put("TableCryptHoriz%d" % R.rnd.randint(1, 3), x, y):
                R.add_named("PropCandles%d" % R.rnd.randint(1, 3), x + R.rnd.randint(-4, 4), y + 5)
                R.put("PropGhostTrap_Chair2", x - 18, y + 1)
                R.put("PropGhostTrap_Chair2Flipped", x + 19, y + 1)
    R.put("PropActionable_BookPodium_Flame", 0, 34, force=True)
    shelf_row(R, 34, R.fx0 + 6, -20, SHELVES)
    shelf_row(R, 34, 20, R.fx1 - 6, SHELVES)
    R.scatter([("PropActionable_CryptCabinet2", 1), ("PropActionable_CryptCabinet4", 1)], 2)
    scatter_own(R, lambda i: Q.book_stack(seed=i + 10), 6)
    decals(R, lambda i: Q.papers(seed=i + 20), 7)
    out.append(("The Reading Room", "Candlelit reading tables in two rows on red rugs, shelves along the back wall, a lectern "
                "under the gothic arch.", R))

    # 3. the index hall
    R = G.Room("RoomCryptCorridor1", seed=53)
    walnut(R, n)
    monster(R, "JinxRingmaster", 64, R.fy0 + 4, flip=True)
    hero(R, -54, R.fy0 + 6)
    x = R.fx0 + 6
    while x < R.fx1 - 8:
        nm = "PropActionable_CryptCabinet%d" % R.rnd.randint(1, 6)
        bx0, by0, bx1, by1 = G.prefab_size(G.BYNAME[nm][0])
        R.put(nm, x - bx0, R.fy1 - 6)
        x += (bx1 - bx0) + (6 if R.rnd.random() < 0.3 else 1)
    R.put("Carpet2", -40, R.fy0 + 10, kind="decal"); R.put("Carpet2", 70, R.fy0 + 10, kind="decal")
    for x in (-100, -10, 90):
        R.put("PropActionableGhost_Fire_CandelabraCrypt", x, R.fy0 + 10)
    scatter_own(R, lambda i: Q.book_stack(seed=i + 30), 5)
    decals(R, lambda i: Q.papers(seed=i + 40), 6)
    out.append(("The Index Hall", "A long corridor walled in the game's cabinets, with red runners down the middle and "
                "index cards spilt between the candelabras.", R))
    return out


# ------------------------------------------------------------------ the Seam: other floors, joined by purple cracks
VIOLET = (150, 92, 230)
VIOLET_CORE = (206, 160, 255)
VIOLET_DARK = (34, 14, 52)

SOURCES = {
    "crypt": ("RoomCryptLarge1", hsv_fn(**STONE_GREEN), hsv_fn(h=0.44, sk=0.6, vk=0.86, hmix=0.8)),
    "mines": ("RoomMinesLarge1", hsv_fn(h=0.04, sk=0.5, vk=0.6, hmix=0.5), hsv_fn(h=0.03, sk=0.65, vk=0.62, hmix=0.4)),
    "orchard": ("RoomLarge1", hsv_fn(h=0.08, sk=0.3, vk=0.8, hmix=0.6), hsv_fn(h=0.06, sk=0.4, vk=0.66, hmix=0.5)),
    "rot": ("RoomCavesLarge1", hsv_fn(h=0.86, sk=0.42, vk=0.84, hmix=0.55), hsv_fn(h=0.82, sk=0.45, vk=0.7, hmix=0.6)),
    "vault": ("RoomCryptLarge3", hsv_fn(h=0.07, sk=1.1, vk=0.72, hmix=0.6), hsv_fn(h=0.05, sk=1.05, vk=0.7, hmix=0.6)),
}


class Seam:
    """A room's floor split into regions (warped Voronoi cells), each showing another floor's texture in its own
    colours, joined by thin glowing purple cracks. All of it is floor: the hero walks straight across a crack."""

    def __init__(self, R, cells, n, warp=9, crack=0.45):
        self.R, self.cells, self.n, self.warp, self.crack = R, cells, n, warp, crack
        self.src = {}
        for _, key in cells:
            if key in self.src:
                continue
            room, ffn, wfn = SOURCES[key]
            S = G.Room(room)
            f = S.floor
            im = G.remap(ffn)(f.im)
            w, h = im.size
            # the source floor's inner part, away from its own edges and wall shade
            box = (int(w * 0.18), int(h * 0.22), int(w * 0.82), int(h * 0.88))
            self.src[key] = (im.crop(box).load(), box[2] - box[0], box[3] - box[1])
        self.cache = {}

    def nearest(self, x, y):
        k = (int(x * 2), int(y * 2))
        if k in self.cache:
            return self.cache[k]
        wx = x + (self.n.v(x, y, 14) - 0.5) * self.warp * 2
        wy = y + (self.n.v(x + 99, y, 14) - 0.5) * self.warp * 2
        ds = sorted((math.hypot(wx - cx, (wy - cy) * 1.35), i) for i, ((cx, cy), _) in enumerate(self.cells))
        r = (ds[0][1], (ds[1][0] - ds[0][0]) / 2)
        self.cache[k] = r
        return r

    def region(self, x, y):
        return self.nearest(x, y)[0]

    def key(self, x, y):
        return self.cells[self.region(x, y)][1]

    def floor(self):
        """floor_fx: each region's texture, darkened toward the cracks, the crack's dark edge and a violet halo."""
        def fx(x, y, c):
            i, e = self.nearest(x, y)
            px, w, h = self.src[self.cells[i][1]]
            # mirrored tiling, so no seams show inside a region
            u, v = int(x + 400) % (2 * w), int(400 - y) % (2 * h)
            u = u if u < w else 2 * w - 1 - u
            v = v if v < h else 2 * h - 1 - v
            p = px[u, v][:3]
            if e < self.crack + 1.0:
                return mix(p, VIOLET_DARK, 0.85)
            if e < 2.2:
                # chipped lip: the broken edge catches the light on one side
                return mix(p, (255, 255, 255) if (self.nearest(x, y + 1)[1] < e) else (0, 0, 0), 0.18)
            if e < 5:
                return mix(p, VIOLET, 0.16 * (1 - e / 5) ** 1.5)
            return p
        return fx

    def glow(self):
        def g(x, y):
            i, e = self.nearest(x, y)
            if e < self.crack:
                # the light in the crack comes and goes along it
                k = self.n.v(x * 0.7, y * 0.7, 3)
                if k < 0.3:
                    return VIOLET + (150,)
                return (VIOLET_CORE if k > 0.62 else VIOLET) + (235,)
            return None
        return g

    def hairlines(self, count=40, seed=0):
        """Short dim cracks branching off the main ones into the regions."""
        R, rnd = self.R, random.Random(seed)
        pts = {}
        for _ in range(count):
            for _t in range(60):
                x, y = rnd.uniform(R.fx0, R.fx1), rnd.uniform(R.fy0, R.fy1)
                if self.nearest(x, y)[1] < 1.2:
                    break
            a = rnd.uniform(0, math.tau)
            for i in range(rnd.randint(4, 12)):
                a += rnd.uniform(-0.5, 0.5)
                x += math.cos(a); y += math.sin(a) * 0.6
                pts[(int(x), int(y))] = max(pts.get((int(x), int(y)), 0), 1 - i / 13)
        def g(x, y):
            v = pts.get((int(x), int(y)))
            return (VIOLET + (int(120 * v),)) if v else None
        return g

    def walls(self):
        """The back wall above each region takes that region's wall colours; a crack runs up the wall where two
        regions meet."""
        R = self.R
        top = R.fy1 - 1.5
        bounds = []
        prev = self.region(R.fx0, top)
        for x in range(int(R.fx0), int(R.fx1)):
            r = self.region(x + 0.5, top)
            if r != prev:
                bounds.append(x)
                prev = r
        wfns = {k: SOURCES[k][2] for k in SOURCES}
        n = self.n
        spans = {b: R.wall_span(b) for b in bounds}
        def wx(x, y, c):
            c2 = wfns[self.key(x, top)](*c)
            for b in bounds:
                sp_ = spans.get(b)
                if not sp_ or y > sp_[0] + (sp_[1] - sp_[0]) * 0.75:
                    continue
                jx = b + (n.v(b, y, 2.5) - 0.5) * 5
                if abs(x - jx) < 0.6:
                    return VIOLET
                if abs(x - jx) < 1.6:
                    return mix(c2, VIOLET_DARK, 0.75)
            return c2
        R.wall_fx.append(wx)
        for b in bounds:
            sp = spans.get(b)
            if sp:
                h = int((sp[1] - sp[0]) * 0.75)
                im = Image.new("RGBA", (7, h), (0, 0, 0, 0))
                px = im.load()
                for yy in range(h):
                    wy = sp[0] + h - yy
                    jx = (n.v(b, wy, 2.5) - 0.5) * 5
                    xx = int(round(3 + jx))
                    t = yy / h        # 0 at the top of the crack, 1 at the floor
                    if 0 <= xx < 7 and n.v(b, wy * 0.7, 3) > 0.3:
                        px[xx, yy] = VIOLET + (int(220 * t ** 0.7),)
                R.add_image(Image.new("RGBA", im.size), b + 0.5, sp[0], emit=im, depth=R.fy1 + 50, name="seamwall")
                R.lamp(b, sp[0] + 3, VIOLET, 18, 0.4)

    def lamps(self, step=16, k=0.24):
        """Light along the cracks."""
        R = self.R
        for y in range(int(R.fy0), int(R.fy1), step // 2):
            for x in range(int(R.fx0), int(R.fx1), step):
                if self.nearest(x, y)[1] < 1.2 and R.on_floor(x, y):
                    R.lamp(x, y, VIOLET, 20, k)

    def inside(self, i, margin=4):
        """For placing: the point is in region i, clear of its cracks."""
        return lambda x, y: self.nearest(x, y) [0] == i and self.nearest(x, y)[1] > margin

    def apply(self):
        R = self.R
        R.floor_fx.insert(0, self.floor())
        R.floor_glow.append(self.glow())
        R.floor_glow.append(self.hairlines(len(self.cells) * 10, seed=len(self.cells)))
        self.walls()
        self.lamps()
        R.dark = (0.5, 0.46, 0.58)


def dress_region(R, S, i, key, n):
    """Props of a region's own biome, kept inside the region."""
    ok = S.inside(i)
    R.block_ok = ok
    old = list(R.blocked)
    R.blocked.append(lambda x, y: not ok(x, y))
    if key == "crypt":
        R.scatter([("ColumnCrypt", 1), ("PropActionableGhost_Fire_CandelabraCrypt", 2), ("PropGhostTrap_Vase1", 2), ("PropCandles2", 2),
                   ("PropGhostTrap_ShortBenchHoriz", 1)], 5)
        decals(R, lambda j: Q.barnacles(10, seed=j), 2, ok=ok)
    elif key == "mines":
        R.scatter([("PropGhostTrap_MineCart1", 1), ("PropsMinesCoalPile1", 2), ("PropGhostTrap_MinesCrate1", 1), ("PropsMinesRock2", 2)], 4)
        scatter_own(R, lambda j: Q.slag(4, seed=j), 2, lamp=(HEAT, 14, 0.5), ok=ok)
        R.recolours.append((kinds("object", name=("MineCart", "Crate")), hsv_set(h=0.04, sk=0.5, vk=0.85, hmix=0.5)))
        R.recolours.append((kinds("object", name=("CoalPile", "Rock")), hsv_set(h=0.05, sk=0.45, vk=1.25, hmix=0.4)))
    elif key == "orchard":
        R.scatter([("PropActionable_Tombstone1", 2), ("PropActionable_Tombstone3", 2), ("PropActionable_Tree6", 1)], 4)
        scatter_own(R, lambda j: Q.bone_pile(12, seed=j), 1, ok=ok)
        decals(R, lambda j: Q.skull(seed=j), 3, ok=ok)
        R.recolours.append((kinds("object", name=("Tree6",)), hsv_set(h=0.11, sk=0.16, vk=1.75, hmix=1.0)))
        R.recolours.append((kinds("object", name=("Tombstone", "BonePile")), hsv_set(h=0.6, sk=0.2, vk=0.9, hmix=0.4)))
    elif key == "rot":
        for j in range(2):
            p = spot(R, ok=ok)
            if p:
                made = Q.giant_cap(R.rnd.randint(18, 26), MAG, TEALG, seed=j + 3) if j == 0 else Q.ink_cap(18, PALE, BLUEG, seed=j)
                if stand(R, made, *p, tries=10, spread=12, ok=ok):
                    cap_lamp(R, p[0], p[1], 22, TEALG if j == 0 else BLUEG)
        decals(R, lambda j: Q.pins(MAG, TEALG, seed=j), 3, ok=ok)
    elif key == "vault":
        R.scatter([("BookshelfCrypt3", 2), ("BookshelfCrypt5", 1), ("PropGhostTrap_Chair2", 1)], 3)
        scatter_own(R, lambda j: Q.book_stack(seed=j), 2, ok=ok)
        decals(R, lambda j: Q.papers(seed=j), 4, ok=ok)
    R.blocked[:] = old


@biome(name="The Seam", tag="Chaos's own floor: the other floors, stitched together", monsters="Everything. The late chaos floors",
       look="Pieces of the Crypt, the Mines, the Orchard, the Rot Gardens and the Vaults fitted edge to edge, each with "
            "its own floor, wall and props, joined by thin cracks of violet light. The cracks run up the walls too.",
       hazard="Shifts: when a room is cleared its pieces trade places for the next fight. A crack that flares is about to "
              "shift: whatever stands on it is thrown to the far side of the room.",
       made="The other biomes' floors, walls and props, cut along warped cells. New: the glowing cracks, darkness.")
def the_seam():
    out = []
    n = Noise(6)
    # 1. the patchwork hall
    R = G.Room("RoomLarge5", seed=61)
    cells = [((-60, 22), "crypt"), ((10, 26), "vault"), ((70, 18), "mines"), ((-58, -26), "orchard"), ((26, -24), "rot")]
    S = Seam(R, cells, n)
    S.apply()
    monster(R, "UmbHollowKing", 46, -14, flip=True)
    hero(R, -36, -4)
    for i, (_, key) in enumerate(cells):
        dress_region(R, S, i, key, n)
    R.floor_fx += [D.edge_shade(R), D.contact_shade(R), D.grit(R, 0.004, seed=2)]
    out.append(("The Patchwork Hall", "Five floors fitted together like broken tiles, each keeping its own props and wall, "
                "the joins glowing violet. The hero walks straight across them.", R))

    # 2. the stitched corridor
    R = G.Room("RoomCryptCorridor1", seed=62)
    keys = ["crypt", "mines", "rot", "orchard", "vault", "crypt", "mines"]
    cells = [((R.fx0 + 18 + i * 34, (i % 2) * 6 - 3), keys[i]) for i in range(7)]
    S = Seam(R, cells, n, warp=7)
    S.apply()
    monster(R, "UmbGlitterswarm", 70, R.fy0 + 6, flip=True)
    hero(R, -64, R.fy0 + 8)
    for i, (_, key) in enumerate(cells):
        dress_region(R, S, i, key, n)
    R.floor_fx += [D.edge_shade(R), D.contact_shade(R)]
    out.append(("The Stitched Corridor", "A corridor made of slabs from five different floors, end to end, each crack a "
                "line of light underfoot and up the wall.", R))

    # 3. the fault: cracks radiate from one point in the middle of a Crypt room
    R = G.Room("RoomCryptMedium1", seed=63)
    keys = ["crypt", "orchard", "mines", "rot", "vault", "crypt", "mines"]
    cells = [((math.cos(a) * 60, -4 + math.sin(a) * 34), keys[i]) for i, a in enumerate([k / 7 * math.tau + 0.2 for k in range(7)])]
    S = Seam(R, cells, n, warp=5, crack=0.6)
    S.apply()
    R.floor_glow.insert(0, lambda x, y: (VIOLET_CORE + (230,)) if math.hypot(x / 3.5, (y + 4) / 2.2) < 1 else
                        ((VIOLET + (140,)) if math.hypot(x / 6, (y + 4) / 3.8) < 1 else None))
    R.lamp(0, -4, VIOLET, 50, 0.8)
    R.light(0, -4, VIOLET, 0.8, 0.5)
    monster(R, "UmbHollowKing", 56, -30, flip=True)
    hero(R, -58, -24)
    for i, (_, key) in enumerate(cells):
        dress_region(R, S, i, key, n)
    R.floor_fx += [D.edge_shade(R), D.contact_shade(R)]
    out.append(("The Fault", "Seven floors meeting at a single point of light in the middle of a Crypt room: the way down "
                "to the next chaos floor.", R))
    return out


def render_all(outdir, collision=True):
    os.makedirs(outdir, exist_ok=True)
    result = []
    for fn, info in BIOMES:
        rooms = []
        slug = info["name"].lower().replace(" ", "_").replace("'", "")
        for i, (title, blurb, R) in enumerate(fn()):
            f = "%s_%d.png" % (slug, i + 1)
            R.render(scale=SCALE).save(os.path.join(outdir, f))
            fc = None
            if collision:
                fc = "%s_%d_col.png" % (slug, i + 1)
                R.render(scale=SCALE, collision=True).save(os.path.join(outdir, fc))
            rooms.append((title, blurb, f, fc))
        result.append((info, rooms))
    return result


def vanilla(outdir):
    """The game's own rooms, filled the same way, for comparison."""
    out = []
    for room, env, title in (("RoomCryptLarge1", "Crypt", "Crypt"), ("RoomMinesLarge1bTracks", "Mines", "Mines"), ("RoomLarge1", "Caves", "Caves")):
        R = G.Room(room, seed=5)
        R.auto_lamps = None
        R.actor(G.hero(), 0, -10, "hero")
        R.fill(env)
        f = "vanilla_%s.png" % title.lower()
        R.render(scale=SCALE).save(os.path.join(outdir, f))
        out.append((title, f))
    return out


if __name__ == "__main__":
    o = sys.argv[1] if len(sys.argv) > 1 else "build/concepts/ingame"
    only = sys.argv[2] if len(sys.argv) > 2 else None
    if only:
        BIOMES[:] = [b for b in BIOMES if only.lower() in b[1]["name"].lower()]
    render_all(o)
    if not only:
        vanilla(o)
