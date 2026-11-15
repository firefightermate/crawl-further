"""Preview of Rot Gardens as the mod builds it at runtime (src/CrawlFurther.Core/Game/Biomes.cs and
src/CrawlFurther/Chaos/RotGardens.cs), drawn from the asset dump so it can be looked at without the game.

What it copies from the mod:
  - the rooms are the Caves' own, normal size and big (tools/chaos/room_stretch.py, the same growth as ChaosRooms);
  - the floor is recoloured with the floor colours (Recolour.Hsv 0.86 / 0.42 / 0.84 / 0.55) and then moss is laid
    over it (RotGardens.MossOver, same counts, sizes, ragged edge and glow specks);
  - every other sprite of the room goes through the wall colours (0.82 / 0.45 / 0.70 / 0.60), lights and flames left;
  - props: the room's own prop counts, each slot 30% a game prop of the Caves (recoloured the way RotGardens.gameProp
    does: stalagmites, plants, the rest) and 70% one of the biome's, by the same weights, from art/out_biomes.

Concept and checking tool: nothing it makes ships. Needs the dump (build/dump/all).
    python3 tools/chaos/rot_preview.py   -> build/rot_preview/*.png, *.gif
"""
import colorsys
import json
import os
import random
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "concepts"))
sys.path.insert(0, HERE)
import ingame as G  # noqa: E402
import room_stretch as RS  # noqa: E402

OUT = os.path.join(G.ROOT, "build", "rot_preview")
ART = os.path.join(G.ROOT, "art", "out_biomes")


def hsv(h, sk, vk, hmix, sadd=0.0):
    """Recolour.Hsv: shading kept, hue turned toward h by hmix, saturation and value scaled."""
    def f(r, g, b):
        hh, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        d = ((h - hh + 1.5) % 1.0) - 0.5
        hh = (hh + d * hmix + 1.0) % 1.0
        s = max(0.0, min(1.0, s * sk + sadd))
        v = max(0.0, min(1.0, v * vk))
        return tuple(int(round(c * 255)) for c in colorsys.hsv_to_rgb(hh, s, v))
    return f


FLOOR = hsv(0.86, 0.42, 0.84, 0.55)
WALL = hsv(0.82, 0.45, 0.70, 0.60)
STALAG = hsv(0.80, 0.30, 1.05, 0.60)
PLANT = hsv(0.47, 1.20, 1.15, 1.00)
OTHER = hsv(0.82, 0.45, 0.80, 0.60)
MOSS, MOSS_LIGHT, GLOW = (62, 94, 74), (88, 128, 92), (110, 255, 220)

# RotGardens.Register: (sheet, weight, foot half-width, foot depth); foot None = decal
DECALS = [("BiomeRotMoss1", 3), ("BiomeRotMoss2", 3), ("BiomeRotMycelium1", 2), ("BiomeRotMycelium2", 2),
          ("BiomeRotPins1", 1.5), ("BiomeRotPins2", 1.5), ("BiomeRotPins3", 1.5)]
SMALL = [("BiomeRotInkCaps1", 2, (4, 4)), ("BiomeRotInkCaps2", 2, (3, 4)), ("BiomeRotPuffball1", 3, (6, 6)),
         ("BiomeRotPuffball2", 2, (4, 4)), ("BiomeRotEggSacs1", 1.5, None), ("BiomeRotEggSacs2", 1.5, None)]
LARGE = [("BiomeRotCapParasol", 2, (5, 6)), ("BiomeRotCapParasolSmall", 2.5, (4, 5)), ("BiomeRotCapBell", 2.5, (7, 7)),
         ("BiomeRotCapShelf", 1.5, (9, 6)), ("BiomeRotLog1", 1.5, (21, 8)), ("BiomeRotLog2", 1.5, (15, 8)),
         ("BiomeRotRoots1", 1, (6, 6)), ("BiomeRotRoots2", 1, (6, 6))]
FEATURE = [("BiomeRotCapParasol", 3, (5, 6)), ("BiomeRotCapBell", 2, (7, 7))]
GAME_SHARE = 0.3

_sheets = {}


def sheet(name):
    if name not in _sheets:
        m = json.load(open(os.path.join(ART, name + ".json")))
        _sheets[name] = (m, Image.open(os.path.join(ART, name + ".png")).convert("RGBA"))
    return _sheets[name]


def frames(name, anim):
    m, im = sheet(name)
    cw, ch, cols = m["cellW"], m["cellH"], m["cols"]
    a = next(a for a in m["anims"] if a["name"] == anim)
    fr = a["frames"] if isinstance(a["frames"], list) else list(range(a["frames"]))
    out = []
    for i in fr:
        x, y = (i % cols) * cw, (i // cols) * ch
        out.append(im.crop((x, y, x + cw, y + ch)))
    return out


def idle(name):
    """The prop's picture, cropped to its pixels but keeping its feet at the bottom centre."""
    im = frames(name, "Idle")[0]
    bb = im.getbbox()
    if not bb:
        return im
    w = im.width
    half = max(w / 2 - bb[0], bb[2] - w / 2)
    x0, x1 = int(w / 2 - half), int(w / 2 + half + 0.5)
    return im.crop((max(0, x0), bb[1], min(w, x1), im.height))


def is_light(name):
    n = name.lower()
    return any(k in n for k in ("light", "flicker", "flame", "candle"))


def moss_over(im, rnd):
    """RotGardens.MossOver on a floor image."""
    px = im.load()
    w, h = im.size
    patches = max(3, min(40, w * h // 2400))

    def mix(a, b, k):
        return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3)) + (a[3],)

    for p in range(patches):
        cx, cy = rnd.randrange(w), rnd.randrange(h)
        rx = 6 + rnd.randrange(18)
        ry = rx * (0.45 + rnd.random() * 0.3)
        col = MOSS_LIGHT if rnd.randrange(3) == 0 else MOSS
        for y in range(max(0, int(cy - ry - 2)), min(h, int(cy + ry + 3))):
            for x in range(max(0, int(cx - rx - 2)), min(w, int(cx + rx + 3))):
                c = px[x, y]
                if c[3] < 200:
                    continue
                dx, dy = (x - cx) / rx, (y - cy) / ry
                e = dx * dx + dy * dy
                n = ((x * 73856093 ^ y * 19349663 ^ p * 83492791) & 1023) / 1023.0
                if e > 0.75 + n * 0.5:
                    continue
                px[x, y] = mix(c, col, 0.8 if e < 0.5 else 0.55)
        if rnd.randrange(3) == 0:
            gx = min(w - 1, max(0, cx + rnd.randint(-4, 4)))
            gy = min(h - 1, max(0, cy + rnd.randint(-2, 2)))
            if px[gx, gy][3] >= 200:
                px[gx, gy] = mix(px[gx, gy], GLOW, 0.7)
    return im


def weighted(rnd, items):
    t = sum(i[1] for i in items)
    r = rnd.random() * t
    for i in items:
        r -= i[1]
        if r <= 0:
            return i
    return items[-1]


def big_room(name, seed):
    """A G.Room whose draws are the big copy's (room_stretch: the same growth as ChaosRooms)."""
    R = G.Room(name, seed=seed)
    P, sx, sy, draws, floor, strips, others = RS.stretch(name, seed)
    if sx is None and sy is None:
        return None
    R.draws = draws
    for d in R.draws:
        if d.kind == "room":
            d.kind = "floor" if d is floor else "wall"
            if "BackWallArt" in d.name or "wall" in d.name.split(":")[-1].lower():
                d.kind = "wall"
    floor.kind = "floor"
    R.floor = floor
    R._fpx = floor.im.load()
    R.fx0, R.fy0 = floor.left, floor.bottom
    R.fx1, R.fy1 = floor.left + floor.im.size[0], floor.bottom + floor.im.size[1]
    cb = R.r["m_cameraBounds"]
    R.cam = (cb["x"], cb["y"], cb["x"] + cb["width"] + P.dx, cb["y"] + cb["height"] + P.dy)
    R.big = (P.dx, P.dy)
    return R


def rot(R, seed, hero_at=None, scale=1.0, clouds=()):
    rnd = random.Random(seed)
    # floor: the floor colours, then moss
    R.floor.im = moss_over(G.remap(FLOOR)(R.floor.im), random.Random(hash(R.name) & 0xffff))
    R._fpx = R.floor.im.load()
    wall = G.remap(WALL)
    R.recolours.append((lambda d: d.kind == "wall" and not is_light(d.name), wall))
    # props: the room's own counts
    r = R.r
    n = lambda key: int(round(rnd.uniform(*G.rng(r[key])) * scale))
    plan = [("Decals", DECALS, n("m_maxDecalProps"), "decal"),
            ("Feature", FEATURE, max(1, int(rnd.uniform(*G.rng(r["m_maxFeatureProps"])))), "object"),
            ("Large", LARGE, n("m_maxLargeProps"), "object"), ("Small", SMALL, n("m_maxSmallProps"), "object")]
    game = set()
    for part, mine, count, kind in plan:
        for _ in range(count):
            if rnd.random() < GAME_SHARE:
                name, gid = G.pick(rnd, "GroupProps%sCaves" % part)
                if "Ghost" in name or "Actionable" in name:
                    continue
                ds = R.place(gid, kind)
                if ds:
                    for d in ds:
                        game.add(id(d))
                continue
            it = weighted(rnd, mine)
            im = idle(it[0])
            foot = it[2] if len(it) > 2 else None
            for _ in range(40):
                x = rnd.uniform(R.fx0 + 10, R.fx1 - 10)
                y = rnd.uniform(R.fy0 + 6, R.fy1 - 10)
                if not (R.on_floor(x, y) and R.on_floor(x - 6, y) and R.on_floor(x + 6, y)):
                    continue
                if kind == "decal" or foot is None:
                    rect = (x - im.width / 2, y, x + im.width / 2, y + im.height)
                    if not R.free(rect, R.drects, -2):
                        continue
                    R.drects.append(rect)
                    R.add_image(im, x, y, kind="decal", name=it[0])
                    break
                if R.stand(im, x, y, foot, name=it[0]):
                    break

    def game_prop(d):
        return id(d) in game and d.kind in ("object", "decal") and not is_light(d.name)

    def colour_game(im, d):
        nm = d.name.lower()
        fn = STALAG if "stalag" in nm else PLANT if ("plant" in nm or "grass" in nm) else OTHER
        return G.remap(fn)(im)
    colour_game.wants_draw = True
    R.recolours.append((game_prop, colour_game))
    if hero_at:
        R.actor(G.hero(), hero_at[0], hero_at[1], "hero")
    for (cx, cy, sheet_name, fr) in clouds:
        R.add_image(frames(sheet_name, "Loop")[fr], cx, cy, name="spores", depth=cy - 1)
    return R


def hazard_gif(path):
    """A puffball bursting into its spore cloud, and a drift crossing, on a patch of Rot Gardens floor."""
    R = G.Room("RoomCavesLarge1", seed=3)
    floor = moss_over(G.remap(FLOOR)(R.floor.im), random.Random(7))
    W, H = 150, 70
    fx = int(floor.width / 2 - W / 2)
    fy = int(floor.height / 2 - H / 2)
    base = floor.crop((fx, fy, fx + W, fy + H))
    puff = idle("BiomeRotPuffball1")
    burst = frames("BiomeRotBurst", "Burst")
    cloud = frames("BiomeRotCloud", "Loop")
    drift = frames("BiomeRotDrift", "Loop")
    hero = G.hero()
    seq = []
    feet = (50, 52)

    def put(cv, im, x, y):
        cv.alpha_composite(im, (int(x - im.width / 2), int(y - im.height)))

    for t in range(46):
        cv = base.copy()
        put(cv, hero, 78, 56)
        if t < 8:
            put(cv, puff, *feet)
        elif t < 15:
            put(cv, burst[t - 8], *feet)
        else:
            put(cv, cloud[(t // 2) % len(cloud)], feet[0], feet[1] + 2)
        dx = 160 - t * 4
        put(cv, drift[(t // 2) % len(drift)], dx, 40)
        seq.append(cv.resize((W * 4, H * 4), Image.NEAREST))
    seq[0].save(path, save_all=True, append_images=seq[1:], duration=90, loop=0, disposal=2)


def main():
    os.makedirs(OUT, exist_ok=True)
    made = []
    # normal size: the Caves' round chamber and two rooms of its set
    for name, seed, hero_at in (("RoomCavesLarge1", 11, (10, -10)), ("RoomLarge1", 12, (0, -6)), ("RoomMed1", 13, (0, -4))):
        if name not in G.ROOMS:
            continue
        before = G.Room(name, seed=seed)
        before.fill("Caves")
        R = rot(G.Room(name, seed=seed), seed, hero_at=hero_at)
        a, b = before.render(scale=3), R.render(scale=3)
        a.save(os.path.join(OUT, name + "_caves.png"))
        b.save(os.path.join(OUT, name + "_rot.png"))
        made.append(name)
    # big rooms
    for name, seed in (("RoomLarge1", 21), ("RoomLarge2", 22), ("RoomMed2", 23)):
        if name not in G.ROOMS:
            continue
        R = big_room(name, seed)
        if R is None:
            continue
        rot(R, seed, hero_at=(0, -6), scale=(R.big[0] + 1) and 1.6,
            clouds=((R.fx0 + 60, R.fy0 + 40, "BiomeRotDrift", 2),))
        R.render(scale=3).save(os.path.join(OUT, name + "_rot_big.png"))
        made.append(name + " big")
    hazard_gif(os.path.join(OUT, "spores.gif"))
    print("made:", ", ".join(made), "->", OUT)


if __name__ == "__main__":
    main()
