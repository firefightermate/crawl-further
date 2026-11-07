#!/usr/bin/env python3
"""Monster statues for every mod god's final (T3) in Crawl's vanilla statue style.

Fully data-driven: re-run any time finals are added or their art changes.
    python3 tools/sprites/statue_rigs.py            # from the repo root

1. Finals = every `new MonsterDef { ... evolveCost = 4.5f ... }` in src/CrawlFurther/**/*Pack.cs; art sheet = art ?? id.
2. Pose = the sheet's Idle frame 0 (Portrait as fallback), loose sparks/particles dropped.
3. Carving: shrunk to fit MAX_FIG_W x MAX_FIG_H, re-shaded in the olive mossy stone ramp sampled from the vanilla
   statues in AtlasProps (troll_statue, ghoul_statue, ...): source brightness ranked into 6 stone tones, silhouette
   edges re-lit (top/left light lip, bottom/right shadow) exactly like vanilla (they have no black outline),
   moss creeping over upward faces and the lower body, a few chipped edge pixels and hairline cracks.
   Hovering monsters (fliers) get a short carved stem like the vanilla beholder statue.
4. Plinth: vanilla's 8-row chamfered stone block (back lip, 4-row top face, lit front lip, 2-row front, inset base).

Placement (matches PropMonsterStatue: exSprite anchor BotCenter, useTextureOffset on, so the bottom-centre of the
element's ORIGINAL canvas sits on the prop's transform = the floor point). Mod elements are untrimmed cells, so:
the plinth's bottom row is the cell's last row (vanilla troll/demon/ghoul/priestess: same) and the plinth is centred
on the cell centre (vanilla plinths sit -1..+1.5 px from the canvas centre).

Output: art/out_statues/ModStatues.png/.json (one 1-frame anim per final, "Statue_<artSheetId>"), _preview.png,
and the vanilla-vs-mod comparison build/boards/statues_check.png (4x, on a floor strip, pivots marked).
"""
import glob, json, os, random, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srcfiles import src_file, pack_files  # noqa: E402

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "art", "out_statues")
DUMP = os.environ.get("CRAWL_DUMP", os.path.join(ROOT, "build", "dump"))
BOARDS = os.path.join(ROOT, "build", "boards")
SHEET = "ModStatues"

CELL_W, CELL_H = 40, 40          # even width: plinth centre lands exactly on the pivot
PLINTH_H = 8
MAX_FIG_W, MAX_FIG_H = 28, 28    # carving incl. the 2 rows it overlaps the plinth top -> <= 34 px visible in all
FEET_ROW = CELL_H - 6            # carving's lowest row sits on the plinth top face (row r2)

# ---------------------------------------------------------------- palette (sampled from vanilla AtlasProps statues)
STONE = [  # tone ramp dark -> light, each with a few vanilla variants for the slight per-pixel grain
    [(64, 65, 55), (63, 64, 54), (62, 63, 54)],          # 0 D  deep shadow / grooves
    [(72, 72, 61), (68, 68, 57), (68, 65, 56), (73, 73, 60)],   # 1 d
    [(81, 77, 67), (76, 75, 61), (79, 77, 63), (81, 79, 64)],   # 2 m  body
    [(98, 92, 72), (99, 93, 72), (100, 93, 73), (95, 90, 71)],  # 3 M
    [(120, 106, 79), (113, 102, 76), (120, 106, 79)],    # 4 L  lit faces / edges
    [(124, 110, 83), (127, 114, 89)],                    # 5 highlight
]
MOSS = [  # moss by underlying tone
    [(73, 85, 58)], [(73, 85, 58), (83, 94, 64)], [(93, 100, 70), (88, 95, 60)],
    [(113, 120, 76), (110, 118, 75)], [(138, 138, 83), (113, 121, 76)], [(138, 138, 83)],
]
TONE_SHARE = [0.13, 0.10, 0.31, 0.24, 0.17, 0.05]   # vanilla pixel shares (m most common, lots of light stone)
MOSS_SHARE = 0.13


# ---------------------------------------------------------------- data
def find_finals():
    """[(monster id, art sheet id, pack file)] for every MonsterDef with evolveCost 4.5 (T3)."""
    out = []
    for f in pack_files():
        s = open(f).read()
        for m in re.finditer(r"new\s+MonsterDef\s*\{", s):
            i, d = m.end(), 1
            while d and i < len(s):
                if s[i] == "{": d += 1
                elif s[i] == "}": d -= 1
                i += 1
            body = s[m.end():i - 1]
            ec = re.search(r"\bevolveCost\s*=\s*([0-9.]+)f?", body)
            if not ec or float(ec.group(1)) < 4.0: continue
            mid = re.search(r'\bid\s*=\s*"([^"]+)"', body)
            if not mid: continue
            art = re.search(r'\bart\s*=\s*"([^"]+)"', body)
            out.append((mid.group(1), art.group(1) if art else mid.group(1), os.path.basename(f)))
    return out


def find_sheet(art):
    hits = [p for p in glob.glob(os.path.join(ROOT, "art", "out*", art + ".json")) if os.sep + "out_statues" + os.sep not in p]
    return hits[0] if hits else None


def source_frame(json_path):
    m = json.load(open(json_path))
    img = Image.open(json_path[:-5] + ".png").convert("RGBA")
    anims = {a["name"]: a for a in m["anims"]}
    a = anims.get("Idle") or anims.get("Portrait")
    if not a: return None
    fi = a["frames"][0]
    cw, ch, cols = m["cellW"], m["cellH"], m["cols"]
    x0, y0 = (fi % cols) * cw, (fi // cols) * ch
    return img.crop((x0, y0, x0 + cw, y0 + ch)), (cw // 2, ch - 2)


# ---------------------------------------------------------------- image helpers (dict/grids of pixels)
def components(mask, W, H):
    seen, comps = set(), []
    for y in range(H):
        for x in range(W):
            if not mask[y][x] or (x, y) in seen: continue
            st, comp = [(x, y)], []
            seen.add((x, y))
            while st:
                cx, cy = st.pop()
                comp.append((cx, cy))
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < W and 0 <= ny < H and mask[ny][nx] and (nx, ny) not in seen:
                            seen.add((nx, ny)); st.append((nx, ny))
            comps.append(comp)
    return comps


def lum(c):
    return 0.30 * c[0] + 0.59 * c[1] + 0.11 * c[2]


def extract(cell, feet):
    """Opaque body pixels -> (lum grid, mask grid, bbox, hover px, base-centre x) without detached sparks."""
    W, H = cell.size
    px = cell.load()
    mask = [[px[x, y][3] >= 128 for x in range(W)] for y in range(H)]
    # Strip the sprite's own dark outline (stone statues have none): find the sheet's outline colour (most common
    # silhouette-edge colour, if dark) and flood it from the outside, which also opens the gaps between limbs that
    # the outline fills. Outline lines enclosed by the body stay and become carved grooves.
    edge = {}
    for y in range(H):
        for x in range(W):
            if mask[y][x] and any(not (0 <= x + dx < W and 0 <= y + dy < H) or not mask[y + dy][x + dx]
                                  for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                edge[px[x, y][:3]] = edge.get(px[x, y][:3], 0) + 1
    if edge:
        oc = max(edge, key=edge.get)
        if lum(oc) < 45 and edge[oc] >= 0.4 * sum(edge.values()):
            is_ol = lambda c: lum(c) < 50 and abs(c[0] - oc[0]) + abs(c[1] - oc[1]) + abs(c[2] - oc[2]) < 36
            st = [(x, y) for y in range(H) for x in range(W) if not mask[y][x]]
            seen = set(st)
            while st:
                x, y = st.pop()
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and (nx, ny) not in seen and mask[ny][nx] and is_ol(px[nx, ny]):
                        seen.add((nx, ny)); mask[ny][nx] = False; st.append((nx, ny))
    comps = components(mask, W, H)
    if not comps: return None
    big = max(len(c) for c in comps)
    keep = set()
    for c in comps:
        if len(c) >= max(6, 0.08 * big): keep.update(c)
    xs = [p[0] for p in keep]; ys = [p[1] for p in keep]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    w, h = x1 - x0 + 1, y1 - y0 + 1
    # relief value: brightness + local contrast (unsharp) - grooves where the art changes colour (part boundaries
    # drawn by hue rather than by a dark line would otherwise vanish once everything is one stone colour)
    raw = {(x, y): lum(px[x, y]) for (x, y) in keep}
    L = [[None] * w for _ in range(h)]
    for (x, y) in keep:
        nb = [raw[(x + dx, y + dy)] for dx in range(-2, 3) for dy in range(-2, 3) if (x + dx, y + dy) in raw]
        v = raw[(x, y)] + 0.8 * (raw[(x, y)] - sum(nb) / len(nb))
        c = px[x, y]
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in raw: continue
            d = px[q[0], q[1]]
            cd = abs(c[0] - d[0]) + abs(c[1] - d[1]) + abs(c[2] - d[2])
            if cd > 90 and raw[(x, y)] <= raw[q]: v -= 22; break
        L[y - y0][x - x0] = v
    base = [x for (x, y) in keep if y >= y1 - 2]
    base_cx = (min(base) + max(base) + 1) / 2.0 - x0
    return L, w, h, feet[1] - y1, base_cx


def shrink(L, w, h, s):
    """Area-average downscale of a luminance+coverage grid by factor s (<=1)."""
    if s >= 0.999: return L, w, h
    tw, th = max(1, round(w * s)), max(1, round(h * s))
    sx, sy = w / tw, h / th
    out = [[None] * tw for _ in range(th)]
    for ty in range(th):
        for tx in range(tw):
            a0, a1, b0, b1 = tx * sx, (tx + 1) * sx, ty * sy, (ty + 1) * sy
            cov = acc = area = 0.0
            for y in range(int(b0), min(h, int(b1 + 0.9999))):
                fy = min(b1, y + 1) - max(b0, y)
                if fy <= 0: continue
                for x in range(int(a0), min(w, int(a1 + 0.9999))):
                    fx = min(a1, x + 1) - max(a0, x)
                    if fx <= 0: continue
                    k = fx * fy
                    area += k
                    if L[y][x] is not None:
                        cov += k; acc += k * L[y][x]
            if area and cov / area >= 0.42:
                nx, ny = min(w - 1, int((a0 + a1) / 2)), min(h - 1, int((b0 + b1) / 2))
                avg = acc / cov
                # nearest source pixel keeps the art's crisp interior lines; average only where it falls outside
                out[ty][tx] = avg if L[ny][nx] is None else 0.65 * L[ny][nx] + 0.35 * min(avg, L[ny][nx] + 20)
    return out, tw, th


def value_noise(w, h, rng, cell=3):
    gw, gh = w // cell + 3, h // cell + 3
    g = [[rng.random() for _ in range(gw)] for _ in range(gh)]
    out = [[0.0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            fx, fy = x / cell, y / cell
            ix, iy = int(fx), int(fy)
            tx, ty = fx - ix, fy - iy
            a = g[iy][ix] * (1 - tx) + g[iy][ix + 1] * tx
            b = g[iy + 1][ix] * (1 - tx) + g[iy + 1][ix + 1] * tx
            out[y][x] = a * (1 - ty) + b * ty
    return out


# ---------------------------------------------------------------- carving
def ray(on, x, y, dx, dy, cap=6):
    n = 0
    while n < cap and (x + dx * (n + 1), y + dy * (n + 1)) in on: n += 1
    return n


def carve(L, w, h, rng):
    """Luminance grid -> {(x,y): (tone, mossy)} in figure space (0,0 = top-left of the carving)."""
    pts = [(x, y) for y in range(h) for x in range(w) if L[y][x] is not None]
    on = set(pts)
    # enclosed holes (shrink pinholes, visor slits, furnace mouths) become deep recesses in the stone
    outside, st = set(), [(-1, -1)]
    while st:
        q = st.pop()
        if q in outside or q in on or not (-1 <= q[0] <= w and -1 <= q[1] <= h): continue
        outside.add(q)
        st.extend(((q[0] + 1, q[1]), (q[0] - 1, q[1]), (q[0], q[1] + 1), (q[0], q[1] - 1)))
    lo = min(L[y][x] for (x, y) in on)
    holes = [(x, y) for y in range(h) for x in range(w) if (x, y) not in on and (x, y) not in outside]
    hmask = [[(x, y) in holes for x in range(w)] for y in range(h)]
    for comp in components(hmask, w, h):
        if len(comp) <= 6:   # big openings (rings, arches, between legs) stay open
            for (x, y) in comp:
                on.add((x, y)); L[y][x] = lo
    pts = sorted(on, key=lambda p: (p[1], p[0]))
    # 1) rank source brightness (keeps the monster's own grooves, eyes and lit planes as relief)
    order = sorted(pts, key=lambda p: (L[p[1]][p[0]], -p[0] - p[1]))
    rank = {p: (i + 0.5) / len(order) for i, p in enumerate(order)}
    # 2) volume light from the top-left: depth to the lit and to the shadowed silhouette
    vol = {}
    for (x, y) in pts:
        tl = min(ray(on, x, y, -1, 0), ray(on, x, y, 0, -1), ray(on, x, y, -1, -1))
        br = min(ray(on, x, y, 1, 0), ray(on, x, y, 0, 1), ray(on, x, y, 1, 1))
        vol[(x, y)] = (br - tl) / float(br + tl + 1)          # -1 shadow side .. +1 lit side
    cum, bounds = 0.0, []
    for s_ in TONE_SHARE:
        cum += s_; bounds.append(cum)
    def to_tone(r):
        k = 0
        while k < len(bounds) - 1 and r > bounds[k]: k += 1
        return k
    tone = {}
    for p in pts:
        r = min(0.999, max(0.0, 0.6 * rank[p] + 0.4 * (0.5 + 0.5 * vol[p])))
        tone[p] = to_tone(r)
    # 3) despeckle: a pixel unlike all 8 neighbours takes their most common tone (source grooves kept)
    sm = {}
    for (x, y) in pts:
        if rank[(x, y)] < 0.10: sm[(x, y)] = 0; continue
        c = {}
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (x + dx, y + dy)
                if q in tone and q != (x, y): c[tone[q]] = c.get(tone[q], 0) + 1
        t = tone[(x, y)]
        sm[(x, y)] = t if (not c or c.get(t, 0) or min(abs(t - k) for k in c) <= 1 and len(c) > 1) else max(c, key=c.get)
    tone = sm
    # 4) silhouette (vanilla edges: light lip on top/left, dark stone bottom/right, no black outline)
    for (x, y) in pts:
        lit = (x - 1, y) not in on or (x, y - 1) not in on
        shade = (x + 1, y) not in on or (x, y + 1) not in on
        if lit and not shade:
            tone[(x, y)] = max(tone[(x, y)], 4 if (x - 1, y) not in on else 3)
        elif shade and not lit:
            tone[(x, y)] = min(tone[(x, y)], 0 if (x + 1, y) not in on else 1)
        elif lit and shade:   # 1-px features (spear shafts, horns): mid stone so they still read
            tone[(x, y)] = 3 if (x - 1, y) not in on else 2
    # 5) chips: knock a few corner pixels off the top/right silhouette
    cands = [p for p in pts if ((p[0] + 1, p[1]) not in on or (p[0], p[1] - 1) not in on)
             and sum((p[0] + dx, p[1] + dy) in on for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) == 2
             and sum((p[0] + dx, p[1] + dy) in on for dx in (-1, 0, 1) for dy in (-1, 0, 1)) >= 4]
    rng.shuffle(cands)
    for p in cands[:max(1, len(pts) // 150)]:
        on.discard(p); tone.pop(p)
        for q in ((p[0] - 1, p[1]), (p[0], p[1] + 1)):
            if q in tone: tone[q] = min(tone[q], 1)
    # 6) hairline cracks on bigger bodies
    inner = sorted(p for p in on if all((p[0] + dx, p[1] + dy) in on for dx in (-1, 0, 1) for dy in (-1, 0, 1)))
    for _ in range(min(2, len(inner) // 90)):
        x, y = rng.choice(inner)
        dx = rng.choice((-1, 1))
        for i in range(rng.randint(2, 3)):
            q = (x + dx * (i // 2), y + i)
            if q in inner: tone[q] = 0
    # 7) moss: coherent noise patches on upward faces (drip) and the lower body (creeps up from the plinth)
    nz = value_noise(w, h, rng)
    score = {}
    for (x, y) in on:
        up = 0.3 if (x, y - 1) not in on or (x, y - 2) not in on else 0.0
        low = 0.4 * max(0.0, (y / max(1, h - 1)) - 0.45)
        score[(x, y)] = nz[y][x] + up + low
    cut = sorted(score.values(), reverse=True)[max(0, int(len(score) * MOSS_SHARE) - 1)] if score else 9
    return {p: (tone[p], score[p] >= cut) for p in on}


def colour(t, mossy, rng):
    ramp = (MOSS if mossy else STONE)[t]
    return (ramp[0] if rng.random() < 0.75 else rng.choice(ramp)) + (255,)


# ---------------------------------------------------------------- plinth
def draw_plinth(px, ox, pw, fig_cols, rng):
    """Vanilla plinth: 8 rows ending on the cell's last row; ox = left column; fig_cols = columns the feet cover."""
    top = CELL_H - PLINTH_H
    S = lambda t: rng.choice(STONE[t]) + (255,)
    Mo = lambda t: rng.choice(MOSS[t]) + (255,)
    moss_x = set(x for x in range(pw) if rng.random() < 0.22)
    for r in range(PLINTH_H):
        y = top + r
        x_lo, x_hi = (1, pw - 2) if r in (0, PLINTH_H - 1) else (0, pw - 1)
        for i in range(x_lo, x_hi + 1):
            right = i >= pw - 3
            if r == 0:                                 # back lip of the top face
                c = S(3) if i <= 2 or i >= pw - 3 else S(2 if rng.random() < 0.6 else 0)
                if i in moss_x and 2 < i < pw - 3: c = Mo(3)
            elif r <= 3:                               # top face, figure shadow in the middle
                if i == 0: c = S(4)
                elif i <= 2 or i >= pw - 3: c = S(3)
                elif i in fig_cols: c = S(0 if r <= 2 else 1)
                else: c = S(2)
                if i in moss_x and r == 3 and 2 < i < pw - 3 and i not in fig_cols: c = Mo(2)
            elif r == 4:                               # front edge of the top face
                c = S(4) if i == 0 else (S(3) if i <= 3 or right else S(2 if i < pw * 0.6 else 1))
            elif r == 5:                               # lit front lip, moss on the right
                c = S(2) if i in (0, pw - 1) else (Mo(4) if i > pw * 0.55 and rng.random() < 0.6 else S(4))
            elif r == 6:                               # front face
                c = S(1) if right else S(2)
                if i in moss_x and rng.random() < 0.5: c = Mo(2)
            else:                                      # inset base
                c = S(1) if i >= pw * 0.6 else S(2)
            px[ox + i, y] = c


# ---------------------------------------------------------------- one statue
def build(art, cell, feet, rng):
    ex = extract(cell, feet)
    if not ex: return None, "empty frame"
    L, w, h, hover, base_cx = ex
    stem_h = 3 if hover >= 3 else 0
    s = min(1.0, MAX_FIG_W / w, (MAX_FIG_H - stem_h) / h)
    L, w2, h2 = shrink(L, w, h, s)
    base_cx *= w2 / w
    fig = carve(L, w2, h2, rng)
    img = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
    px = img.load()
    # figure anchor: halfway between its feet and its bbox centre, so long bodies don't hang off the plinth
    anchor = 0.5 * base_cx + 0.5 * (w2 / 2.0)
    fx0 = int(round(CELL_W / 2.0 - anchor))
    fx0 = max(1, min(CELL_W - 1 - w2, fx0))
    fy0 = FEET_ROW - stem_h - (h2 - 1)
    bottom = [x for (x, y) in fig if y == h2 - 1] or [w2 // 2]
    foot_cols = set(range(min(bottom) + fx0 - 1, max(bottom) + fx0 + 2))
    # plinth width follows the footprint (vanilla 15-23 for figures 13-27 wide)
    foot_w = max(bottom) - min(bottom) + 1
    pw = max(16, min(22, int(max(foot_w + 6, w2 * 0.62) + 1) // 2 * 2))
    ox = CELL_W // 2 - pw // 2
    stem_cols = set()
    if stem_h:
        sw = max(4, min(8, (foot_w * 2 // 5) // 2 * 2))
        sx0 = CELL_W // 2 - sw // 2
        stem_cols = set(range(sx0, sx0 + sw))
    draw_plinth(px, ox, pw, set(c - ox for c in (stem_cols or foot_cols)), rng)
    if stem_h:   # carved stem + a 1px cup lip under the figure, lit from the left like the beholder statue
        sx0 = min(stem_cols)
        for r in range(stem_h):
            y = FEET_ROW - r
            for x in stem_cols:
                t = 4 if x == sx0 else (0 if x == sx0 + len(stem_cols) - 1 else (2 if r else 1))
                px[x, y] = colour(t, r == 0 and rng.random() < 0.3, rng)
        y = FEET_ROW - stem_h + 1
        for x in range(sx0 - 1, sx0 + len(stem_cols) + 1):
            px[x, y] = colour(4 if x < sx0 + 1 else 3, False, rng)
    for (x, y), (t, mossy) in fig.items():
        X, Y = fx0 + x, fy0 + y
        if 0 <= X < CELL_W and 0 <= Y < CELL_H:
            px[X, Y] = colour(t, mossy, rng)
    return img, "src %dx%d -> carving %dx%d (x%.2f)%s, plinth %d" % (w, h, w2, h2, s, ", stem" if stem_h else "", pw)


# ---------------------------------------------------------------- vanilla reference (for the comparison only)
VANILLA = ["troll_statue", "beholder", "demon_statue", "skelpope_statue", "ghoul_statue", "capra_statue",
           "priestess_statue", "minotaur_statue"]


def vanilla_statues():
    try:
        atlas = None
        for l in open(os.path.join(DUMP, "db", "exAtlas.jsonl")):
            if '"AtlasProps"' in l:
                o = json.loads(l)
                if o.get("m_Name") == "AtlasProps": atlas = o; break
        tex = Image.open(os.path.join(DUMP, "tex", "AtlasProps_6.png")).convert("RGBA")
    except Exception as e:
        print("(vanilla reference unavailable: %s)" % e); return []
    W, H = tex.size
    els = {e["name"]: e for e in atlas["elements"]}
    out = []
    for n in VANILLA:
        e = els.get(n)
        if not e: continue
        c, t = e["coords"], e["trimRect"]
        x0, w, h = round(c["x"] * W), round(c["width"] * W), round(c["height"] * H)
        y0 = H - round(c["y"] * H) - h
        can = Image.new("RGBA", (e["originalWidth"], e["originalHeight"]), (0, 0, 0, 0))
        can.paste(tex.crop((x0, y0, x0 + w, y0 + h)), (int(t["x"]), int(t["y"])))
        out.append((n, can))
    return out


def comparison(vanilla, mods, path, scale=4):
    """Every canvas placed exactly as the prop draws it: canvas bottom-centre on the floor point (BotCenter anchor)."""
    items = [(n, c, True) for n, c in vanilla] + [(n, c, False) for n, c in mods]
    gap = 6
    per_row = 12
    rows = [items[i:i + per_row] for i in range(0, len(items), per_row)]
    rowH = max(c.height for _, c, _ in items) + 14
    width = max(sum(c.width + gap for _, c, _ in r) for r in rows) + gap
    bg = Image.new("RGBA", (width, rowH * len(rows)), (24, 21, 26, 255))
    d = ImageDraw.Draw(bg)
    for ri, r in enumerate(rows):
        floor_y = ri * rowH + rowH - 8           # world y = 0 for every statue in this row
        d.rectangle((0, floor_y, width, floor_y + 7), fill=(52, 45, 43, 255))
        d.line((0, floor_y + 3, width, floor_y + 3), fill=(46, 40, 38, 255))
        x = gap
        for n, c, van in r:
            cx = x + c.width / 2.0
            bg.alpha_composite(c, (x, floor_y - c.height))
            # pivot tick (floor point) and the prop's Body collider footprint (15 x 6 at y 2.57)
            d.point((int(cx), floor_y + 1), fill=(220, 60, 60, 255) if van else (80, 160, 230, 255))
            d.point((int(cx - 0.5), floor_y + 1), fill=(220, 60, 60, 255) if van else (80, 160, 230, 255))
            x += c.width + gap
    bg = bg.resize((bg.width * scale, bg.height * scale), Image.NEAREST)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bg.convert("RGB").save(path)


# ---------------------------------------------------------------- main
def main():
    finals = find_finals()
    os.makedirs(OUT, exist_ok=True)
    frames, anims, mods, log = [], [], [], []
    seen = set()
    for mid, art, pack in finals:
        if art in seen: continue
        seen.add(art)
        jp = find_sheet(art)
        if not jp:
            log.append("SKIP %s (%s): no art sheet %s" % (mid, pack, art)); continue
        src = source_frame(jp)
        if not src:
            log.append("SKIP %s: %s has no Idle/Portrait" % (mid, art)); continue
        rng = random.Random("statue:" + art)
        img, info = build(art, src[0], src[1], rng)
        if img is None:
            log.append("SKIP %s: %s" % (mid, info)); continue
        anims.append({"name": "Statue_" + art, "frames": [len(frames)], "durations": [1.0]})
        frames.append(img)
        mods.append((art, img))
        bb = img.getbbox()
        log.append("%-18s %-18s %-16s %s, visible %dx%d" % (mid, art, pack, info, bb[2] - bb[0], bb[3] - bb[1]))
    cols = 8
    rows = max(1, (len(frames) + cols - 1) // cols)
    pw = 1
    while pw < cols * CELL_W: pw *= 2
    ph = 1
    while ph < rows * CELL_H: ph *= 2
    sheet = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.paste(f, ((i % cols) * CELL_W, (i // cols) * CELL_H))
    man = {"cellW": CELL_W, "cellH": CELL_H, "cols": cols, "anims": anims}
    sheet.save(os.path.join(OUT, SHEET + ".png"))
    json.dump(man, open(os.path.join(OUT, SHEET + ".json"), "w"))
    # preview: all statues side by side at 6x
    pv = Image.new("RGBA", (max(1, len(frames)) * (CELL_W + 2) * 6, (CELL_H + 2) * 6), (28, 26, 32, 255))
    for i, f in enumerate(frames):
        pv.alpha_composite(f.resize((CELL_W * 6, CELL_H * 6), Image.NEAREST), (i * (CELL_W + 2) * 6, 0))
    pv.convert("RGB").save(os.path.join(OUT, SHEET + "_preview.png"))
    comparison(vanilla_statues(), mods, os.path.join(BOARDS, "statues_check.png"))
    print("\n".join(log))
    print("%d statues -> %s (%dx%d cells, pivot = cell bottom-centre)" % (len(frames), os.path.join(OUT, SHEET + ".png"), CELL_W, CELL_H))


if __name__ == "__main__":
    main()
