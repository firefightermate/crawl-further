"""Collision check for the chaos concept rooms.

1. Probe sheet: every prop the rooms use, game's or ours, with the hero put where his own collider (an 8 x 3 capsule
   at the feet) can really stand: touching its front, the closest spot directly behind it, a few pixels further back,
   and beside it. Each is drawn the way the room draws them (sorted by feet), next to the footprint itself, so a
   wrong depth shows at once (the hero on a table top, inside a cart, on a coffin lid).
2. Room sweep: every concept room checked for overlapping footprints, footprints off the floor or in water, actors
   standing in props, and the floor the hero can reach.

    python3 tools/concepts/collision_check.py <outdir>
"""
import os
import sys

from PIL import Image, ImageDraw

import ingame as G
import ingame_biomes as B
import props as Q

HERO_W, HERO_D = 4.0, 1.5        # half-width and half-depth of the hero's capsule (game: r 1.5, h 8 along x)
BG = (96, 90, 82, 255)


def hero_fits(x, y, solids):
    r = (x - HERO_W, y - HERO_D, x + HERO_W, y + HERO_D)
    return all(not (r[0] < s[2] and s[0] < r[2] and r[1] < s[3] and s[1] < r[3]) for s in solids)


def probes(solids, sprite):
    """Hero foot points: front (touching), behind (closest free spot straight back from the front), further back,
    and beside."""
    x0, y0, x1, y1 = sprite
    cx = (x0 + x1) / 2
    fy0 = min(s[1] for s in solids) if solids else y0
    fy1 = max(s[3] for s in solids) if solids else y0
    out = {}
    out["front"] = (cx, fy0 - HERO_D - 0.5)
    y = fy0
    while not hero_fits(cx, y, solids):
        y += 0.5
    out["behind"] = (cx, y)
    out["further"] = (cx, y + 5)
    fx1 = max(s[2] for s in solids) if solids else x1
    out["beside"] = (fx1 + HERO_W + 0.5, (fy0 + fy1) / 2)
    return out


def panel(draws, solids, hero_at, hero, box, overlay=False, label=""):
    bx0, by0, bx1, by1 = box
    W, H = int(bx1 - bx0), int(by1 - by0)
    c = Image.new("RGBA", (W, H), BG)
    def put(d):
        c.alpha_composite(d.im, (int(round(d.left - bx0)), int(round(by1 - d.bottom - d.im.height))))
    for d in draws:
        if d.kind == "shadow":
            put(d)
    items = [d for d in draws if d.kind == "object"]
    if hero_at:
        hx, hy = hero_at
        items.append(G.Draw(hero, hx - hero.width / 2, hy, "object", hy, "hero"))
    for d in sorted(items, key=lambda d: -d.depth):
        put(d)
    if overlay:
        ov = Image.new("RGBA", c.size, (0, 0, 0, 0))
        dr = ImageDraw.Draw(ov)
        for s in solids:
            dr.rectangle((s[0] - bx0, by1 - s[3], s[2] - bx0 - 1, by1 - s[1] - 1), fill=(255, 70, 60, 110), outline=(255, 70, 60, 255))
        if hero_at:
            hx, hy = hero_at
            dr.rectangle((hx - HERO_W - bx0, by1 - hy - HERO_D, hx + HERO_W - bx0 - 1, by1 - hy + HERO_D - 1), outline=(90, 230, 255, 255))
        c.alpha_composite(ov)
    return c


def game_prop(name):
    g = G.BYNAME[name][0]
    ds = [d for d in G.collect(g) if d.kind in ("object", "shadow")]
    return ds, G.solid_footprints(g), G.footprints(g)


def own_prop(made):
    im, em, foot, sh = made
    fw, fd = foot
    ds = [G.Draw(sh, -sh.width / 2, -sh.height / 2 + 1, "shadow", 0, "s"), G.Draw(im, -im.width / 2, 0, "object", 0, "p")]
    return ds, [(-fw, -0.5, fw, fd)], []


def sheet(entries, out, cols=2, scale=3):
    hero = G.hero()
    tiles = []
    for name, (ds, solids, old) in entries:
        obj = [d for d in ds if d.kind == "object"]
        sp = (min(d.left for d in obj), min(d.bottom for d in obj), max(d.left + d.im.width for d in obj), max(d.bottom + d.im.height for d in obj))
        pr = probes(solids, sp)
        box = (min(sp[0], pr["front"][0] - 6) - 4, min(sp[1], pr["front"][1]) - 4,
               max(sp[2], pr["beside"][0] + HERO_W) + 4, max(sp[3], pr["further"][1] + hero.height) + 3)
        pans = [panel(ds, solids, None, hero, box, overlay=True)]
        if old:
            pans.insert(0, panel(ds, old, None, hero, box, overlay=True))
        for k in ("front", "behind", "further", "beside"):
            pans.append(panel(ds, solids, pr[k], hero, box))
        W = sum(p.width + 3 for p in pans)
        t = Image.new("RGBA", (W, pans[0].height + 9), (34, 32, 38, 255))
        x = 0
        for p in pans:
            t.paste(p, (x, 9)); x += p.width + 3
        ImageDraw.Draw(t).text((1, -1), name, fill=(235, 230, 220, 255))
        tiles.append((t, bool(old)))
    rows = [tiles[i:i + cols] for i in range(0, len(tiles), cols)]
    cw = max(t.width for t, _ in tiles) + 10
    H = sum(max(t.height for t, _ in r) + 6 for r in rows)
    s = Image.new("RGBA", (cw * cols, H), (34, 32, 38, 255))
    y = 0
    for r in rows:
        for i, (t, _) in enumerate(r):
            s.paste(t, (i * cw, y))
        y += max(t.height for t, _ in r) + 6
    s = s.resize((s.width * scale, s.height * scale), Image.NEAREST)
    s.save(out)
    return s.size


def room_sweep(rooms):
    """Problems per room: overlapping footprints, footprints off the floor or in water, actors in props."""
    report = []
    for title, R in rooms:
        probs = []
        sol = R.solids
        for i, (a, la, _) in enumerate(sol):
            for (b, lb, _) in sol[i + 1:]:
                if a[0] < b[2] - 0.01 and b[0] < a[2] - 0.01 and a[1] < b[3] - 0.01 and b[1] < a[3] - 0.01:
                    probs.append("overlap: %s / %s" % (la, lb))
        for (r, lab, _) in sol:
            if lab in ("monster",):
                continue
            pts = [(r[0], r[1]), (r[2], r[1]), (r[0], r[3]), (r[2], r[3])]
            if not all(R.on_floor(*p) for p in pts):
                probs.append("off the floor: %s" % lab)
            elif lab != "mod" and lab not in getattr(R, "wet_ok", ()) and any(any(bl(*p) for bl in R.blocked) for p in pts):
                probs.append("in water: %s" % lab)
        # how much open floor the hero can stand on
        free = tot = 0
        props = [r for (r, lab, _) in sol if lab not in ("hero", "monster")]
        for y in range(int(R.fy0), int(R.fy1)):
            for x in range(int(R.fx0), int(R.fx1)):
                if R.on_floor(x, y):
                    tot += 1
                    if R.walkable(x, y) and hero_fits(x, y, props):
                        free += 1
        report.append((title, probs, free / max(1, tot)))
    return report


def used_props(rooms):
    names = set()
    for title, R in rooms:
        for d in R.draws:
            if d.kind == "object" and d.name.startswith("/"):
                names.add(d.name[1:].split("/")[0].split(":")[0])
    return sorted(n for n in names if n in G.BYNAME)


def all_rooms():
    rooms = []
    for fn, info in B.BIOMES:
        for title, blurb, R in fn():
            rooms.append(("%s: %s" % (info["name"], title), R))
    return rooms


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "build/concepts/collision"
    os.makedirs(out, exist_ok=True)
    rooms = all_rooms()
    names = [n for n in used_props(rooms) if G.solid_footprints(G.BYNAME[n][0])]
    deep = [n for n in names if G.depth_of(n)]
    tall = [n for n in names if not G.depth_of(n)]
    print("deep", sheet([(n.replace("PropActionable_", "").replace("PropGhostTrap_", "").replace("PropDestructible", ""), game_prop(n)) for n in deep],
                        os.path.join(out, "check_game_deep.png")))
    print("tall", sheet([(n.replace("PropActionable_", "").replace("PropGhostTrap_", "").replace("PropDestructible", ""), game_prop(n)) for n in tall],
                        os.path.join(out, "check_game_tall.png"), cols=3))
    ours = [("giant cap", Q.giant_cap(38, B.MAG, B.TEALG, seed=1)), ("bell cap", Q.giant_cap(28, B.OCH, B.AMBG, seed=2, kind="bell")),
            ("ink caps", Q.ink_cap(22)), ("puffball", Q.puffball(7)), ("egg sacs", Q.pod_cluster()), ("log", Q.rotten_log(40, glow=1)),
            ("grave", Q.grave(14)), ("bone pile", Q.bone_pile(16)), ("anvil", Q.anvil()), ("crucible", Q.crucible()),
            ("slag", Q.slag(5)), ("furnace", Q.furnace()), ("book stack", Q.book_stack(1)), ("kelp", Q.kelp(14))]
    print("ours", sheet([(n, own_prop(m)) for n, m in ours], os.path.join(out, "check_ours.png")))
    rep = room_sweep(rooms)
    with open(os.path.join(out, "sweep.txt"), "w") as f:
        for title, probs, free in rep:
            line = "%-40s open floor %3d%%  %s" % (title, round(free * 100), "; ".join(probs) if probs else "ok")
            print(line)
            f.write(line + "\n")
