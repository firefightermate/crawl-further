#!/usr/bin/env python3
"""SILVER VARIANTS: the silver ghost's Ascension turns a tier-3 body into its moonlit silver self.

Every tier-3 final gets a silver variant of its OWN sheet, every frame of every anim, re-rendered (not tinted) by the
rules below, and the runtime (src/CrawlFurther/Secrets/SilverVariants.cs) swaps an ascended body's frames onto it:

  * mod finals: the 9 gods' 12 finals each, the 4 gold-secret finals and the 5 secret statue monsters
      art/out_<god>/<Sheet>.png  ->  art/out_silvervar/SilverVar_<Sheet>.png/.json (same grid, same anims, same timing)
  * vanilla finals: every vanilla monster at level 3 or 4 of a vanilla god's tree (what Ascension can meet: 33 bodies),
      cut from the game's AtlasEnemies (from the game dump, build/dump) element by element, re-rendered, packed into
      art/out_silvervar/SilverVar_AtlasEnemies.png + .json (BossFactory's element format: [vanilla element index, x, y,
      w, h, trimX, trimY]); the runtime builds a parallel atlas whose re-rendered elements point into that png.
    (The vanilla Statue clips live on AtlasProps and stay stone: an ascended body never plays them.)

The silver re-render, per pixel (frame geometry, alpha and timing never change):
  1. outline: an opaque pixel touching transparency that is dark, or any near-black line pixel -> navy ink;
  2. glow: bright, saturated pixels (eyes, flames, runes, gems) -> the god's moonlit accent ramp (a cooled, paled
     version of the god's signature colour, white at the core), so each god stays recognisable in silver;
  3. body: luminance, normalised to the sheet's own Idle range (5th / 50th / 95th percentile), drives a 9-step
     silver ramp (navy shadow -> slate -> steel -> silver -> moonlight white), so dark monsters and pale monsters both
     land on a bright, readable metal; the original hue nudges each tone a little (warm -> platinum, cool -> blue
     steel, green -> mint pewter, violet -> lilac) so materials stay told apart; where two materials of different hue
     met at the same lightness a one-step seam is kept;
  4. moonlight rim: body pixels under the top or left edge of the silhouette step up one tone (light from the top-left);
  5. sparkles: 1-3 white pin-glints per frame on the brightest body pixels (re-rolled every frame, so the metal
     twinkles as it animates), and on bigger bodies a 4-point star glint on about a third of the frames.
  The Statue anim is left as stone (the statue rooms' carvings stay carvings).

Each variant json keeps the source's cellW/cellH/cols/anims plus "source" (sheet id) and "sourceSha1" (of the
source png): `--check` reports any variant whose source changed since it was baked (re-run this script then).

    python3 tools/sprites/silver_variants.py            # bake everything (mod finals + vanilla), boards in build/boards
    python3 tools/sprites/silver_variants.py --only GoldWyrm,YsvEmpress
    python3 tools/sprites/silver_variants.py --mod      # mod finals only (no vanilla dump needed)
    python3 tools/sprites/silver_variants.py --check    # exit 1 if a variant is missing or stale
"""
import colorsys, glob, hashlib, json, os, re, sys, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srcfiles import src_file, pack_files  # noqa: E402

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from check_trees import defs_of, GODS, EXTRA  # noqa: E402

DUMP = os.environ.get("CRAWL_DUMP", os.path.join(ROOT, "build", "dump"))
BOARDS = os.path.join(ROOT, "build", "boards")
OUT = os.path.join(ROOT, "art", "out_silvervar")
PREFIX = "SilverVar_"
VANILLA_SHEET = PREFIX + "AtlasEnemies"
VANILLA_ATLAS = ("AtlasEnemies", "AtlasEnemies_7.png")

# ------------------------------------------------------------------------------------------------ palette
OUTLINE = (20, 23, 52)          # navy ink
OUTLINE_SOFT = (34, 40, 78)     # inner line / outline on a lit edge
# 9-step moonlit silver ramp, t = 0 .. 1
RAMP = np.array([
    (30, 34, 66),     # deep navy shadow
    (46, 53, 90),
    (66, 76, 114),    # slate
    (90, 102, 140),
    (116, 128, 164),  # steel
    (146, 157, 190),  # silver
    (176, 186, 214),
    (206, 214, 234),  # bright silver
    (234, 239, 250),  # moonlight
], float)
WHITE = (255, 255, 255)
GLINT_ARM = (196, 222, 255)

# per group: the moonlit accent (glow pixels: dim, lit, core): a paled, cooled version of the god's signature colour
ACCENT = {
    "Vhorrul":    ((112, 86, 214), (172, 150, 255), (238, 230, 255)),   # candle fire -> violet moonfire
    "Ossivar":    ((52, 168, 178), (120, 230, 232), (226, 255, 252)),   # soul light -> pale cyan
    "Sylvene":    ((60, 166, 120), (140, 232, 182), (226, 255, 238)),   # spores / blooms -> mint
    "Umbrael":    ((128, 80, 214), (196, 160, 255), (240, 228, 255)),   # shadow / glass -> violet
    "BelMora":    ((36, 142, 186), (110, 214, 240), (220, 250, 255)),   # the deep -> aqua
    "Jinx":       ((186, 72, 170), (244, 150, 222), (255, 230, 248)),   # cards / dice -> rose
    "Zhekra":     ((126, 170, 52), (200, 240, 120), (244, 255, 214)),   # acid / chitin -> chartreuse
    "Kaurn":      ((52, 120, 230), (130, 196, 255), (230, 244, 255)),   # lightning -> electric blue
    "Ysveld":     ((70, 150, 220), (160, 226, 255), (240, 252, 255)),   # frost -> ice
    "GoldSecret": ((196, 150, 52), (250, 214, 120), (255, 246, 214)),   # gold -> white gold
    "Statue":     ((84, 120, 210), (170, 204, 255), (238, 246, 255)),   # the secret statues -> moonlight
    "Vanilla":    ((70, 128, 214), (156, 206, 255), (234, 246, 255)),   # vanilla finals -> moon blue
}
# second-material ramp (cloth, flesh, hide of another hue than the main metal): deep "moonlit enamel", navy leaning to
# the god's accent hue, so a red tabard / green leaf / gold trim stays a different material in silver
ENAMEL_BASE = np.array([(22, 24, 58), (32, 38, 84), (46, 56, 112), (64, 78, 142), (88, 106, 172), (120, 140, 204),
                        (160, 178, 228)], float)


def enamel_for(group):
    lo = np.array(ACCENT[group][0], float)
    return ENAMEL_BASE * 0.72 + (lo * (ENAMEL_BASE.mean(1, keepdims=True) / max(1.0, lo.mean()))) * 0.28


# per-group hue nudge strength (Ysveld is already navy/ice: push its metal a little warmer/brighter so it still changes)
HUE_K = {"Ysveld": 0.5, "Umbrael": 0.6}
STATUE_ANIMS = {"Statue"}
GLOW_MAX = 0.06


def lum(rgb):
    return rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114


def ramp(t):
    """t (array, 0..1) -> RGB float array, quantised to the 9 ramp steps (crisp pixel-art tones)."""
    i = np.clip(np.rint(t * (len(RAMP) - 1)), 0, len(RAMP) - 1).astype(int)
    return RAMP[i], i


def hsv_arr(rgb):
    r, g, b = [rgb[..., k] / 255.0 for k in range(3)]
    mx = np.maximum(np.maximum(r, g), b); mn = np.minimum(np.minimum(r, g), b)
    d = mx - mn
    s = np.where(mx > 0, d / np.maximum(mx, 1e-6), 0)
    h = np.zeros_like(mx)
    m = d > 1e-6
    rc = np.where(m, (mx - r) / np.maximum(d, 1e-6), 0)
    gc = np.where(m, (mx - g) / np.maximum(d, 1e-6), 0)
    bc = np.where(m, (mx - b) / np.maximum(d, 1e-6), 0)
    h = np.where(r == mx, bc - gc, np.where(g == mx, 2.0 + rc - bc, 4.0 + gc - rc))
    h = (h / 6.0) % 1.0
    return np.where(m, h, 0), s, mx


def hue_shift(h, s):
    """(dr, dg, db) per pixel from the original hue: warm -> platinum, cool -> blue steel, green -> mint, violet -> lilac."""
    out = np.zeros(h.shape + (3,))
    warm = (h < 0.15) | (h >= 0.93)
    green = (h >= 0.15) & (h < 0.42)
    cool = (h >= 0.42) & (h < 0.72)
    viol = (h >= 0.72) & (h < 0.93)
    for m, v in ((warm, (5, 1, -3)), (green, (-6, 8, -4)), (cool, (-9, 2, 12)), (viol, (8, -4, 10))):
        out[m] = v
    return out * np.clip(s, 0, 1)[..., None] * 1.2


def accent_ramp(acc, t):
    """Glow tone: t 0..1 -> dim / lit / core of the group's accent."""
    c = np.array(acc, float)
    i = np.where(t < 0.34, 0, np.where(t < 0.8, 1, 2))
    return c[i]


# ------------------------------------------------------------------------------------------------ the re-render
class Stats:
    """A sheet's body anchors from its Idle frames: luminance 5th / 50th / 95th percentile, and its main material hue
    (the hue most of its saturated body pixels share; None for a mostly grey sheet)."""

    def __init__(self, cells):
        Ls, Hs, Ss = [], [], []
        for c in cells:
            a = c[..., 3] > 0
            if not a.any(): continue
            rgb = c[..., :3].astype(float)
            L = lum(rgb)
            h, s, v = hsv_arr(rgb)
            body = a & ~edge_mask(a) & (L > 24)
            Ls.append(L[body]); Hs.append(h[body]); Ss.append(s[body])
        L = np.concatenate(Ls) if Ls else np.array([60.0, 100.0, 160.0])
        H = np.concatenate(Hs) if Hs else np.zeros(1)
        S = np.concatenate(Ss) if Ss else np.zeros(1)
        if L.size < 8: L = np.array([60.0, 100.0, 160.0])
        self.p5, self.p50, self.p95 = [float(np.percentile(L, q)) for q in (5, 50, 95)]
        if self.p95 - self.p5 < 30:            # flat sheet: spread it artificially
            self.p5 -= 15; self.p95 += 15
        self.p50 = min(max(self.p50, self.p5 + 5), self.p95 - 5)
        satd = S > 0.3
        self.hue = None
        if satd.mean() > 0.35 if S.size else False:
            hist = np.zeros(24)
            for hh in H[satd]: hist[int(hh * 24) % 24] += 1
            sm = hist + np.roll(hist, 1) + np.roll(hist, -1)
            self.hue = (int(np.argmax(sm)) + 0.5) / 24.0

    def t(self, L):
        # p5 -> 0.1, p50 -> 0.52, p95 -> 0.9 (piecewise linear, clamped 0..1)
        lo = 0.10 + (L - self.p5) / max(1e-3, self.p50 - self.p5) * (0.52 - 0.10)
        hi = 0.52 + (L - self.p50) / max(1e-3, self.p95 - self.p50) * (0.90 - 0.52)
        return np.clip(np.where(L < self.p50, lo, hi) + self.off, 0, 1)

    off = 0.0

    def calibrate(self, cells, group):
        """Shift the ramp so the silver Idle frames are at least as bright as the originals and land on a bright,
        readable metal (body mean luminance ~120-150; vanilla enemies average ~100, silver should shine above that)."""
        def mean_l(cs, fn):
            tot, n = 0.0, 0
            for c in cs:
                a = c[..., 3] > 0
                if not a.any(): continue
                o = fn(c)
                tot += lum(o[..., :3].astype(float))[a].sum(); n += int(a.sum())
            return tot / max(1, n)
        orig = mean_l(cells, lambda c: c)
        target = min(150.0, max(116.0, orig + 16.0))
        best = (1e9, 0.0)
        for k in range(-6, 9):
            self.off = k * 0.025
            m = mean_l(cells, lambda c: silverize(c, self, group, 0, sparkle=False))
            best = min(best, (abs(m - target), self.off))
        self.off = best[1]
        self.orig_mean, self.target = orig, target

    def second(self, h, s):
        """Pixels of a second material: saturated and off the sheet's main hue (any saturated pixel on a grey sheet)."""
        if self.hue is None: return s > 0.32
        d = np.abs(h - self.hue); d = np.minimum(d, 1 - d)
        return (s > 0.32) & (d > 0.09)


def edge_mask(a):
    """Opaque pixels touching transparency (4-neighbour) or the cell border."""
    p = np.pad(a, 1, constant_values=False)
    n = p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
    return a & ~n


def top_left_rim(a, ink):
    """Body pixels whose upper or left neighbour is transparent or ink: the moonlit rim."""
    p = np.pad(a & ~ink, 1, constant_values=False)
    up, left = p[:-2, 1:-1], p[1:-1, :-2]
    return (a & ~ink) & (~up | ~left)


def silverize(cell, st, group, seed, sparkle=True):
    """One frame (H, W, 4 uint8) -> its silver re-render (same alpha)."""
    out = cell.copy()
    a = cell[..., 3] > 0
    if not a.any(): return out
    rgb = cell[..., :3].astype(float)
    L = lum(rgb)
    h, s, v = hsv_arr(rgb)
    e = edge_mask(a)
    # 1. ink: dark silhouette edge, or near-black anywhere (inner linework)
    ink = a & ((e & (L < max(70.0, st.p5 + 8))) | (L < min(26.0, st.p5 * 0.6 + 6)))
    # 2. glow: bright saturated (eyes, flames, runes) or near-white hot spots well above the body range
    glow = a & ~ink & (((s > 0.55) & (v > 0.8) & (L > 100)) | (L > max(232.0, st.p95 + 40)))
    # keep glow an accent (eyes, flames, runes), never a whole material: at most GLOW_MAX of the frame, the brightest
    if glow.sum() > GLOW_MAX * a.sum():
        thr = np.percentile(L[glow], 100 - 100 * GLOW_MAX * a.sum() / glow.sum())
        glow &= L > thr
    body = a & ~ink & ~glow
    enam = body & st.second(h, s)
    metal = body & ~enam
    # 3. body tones: the main material on the silver ramp, a second material on the enamel ramp (one tone darker)
    t = st.t(L)
    n = len(RAMP)
    idx = np.clip(np.rint(t * (n - 1)), 0, n - 1).astype(int)
    EN = enamel_for(group)
    eidx = np.clip(np.rint(t * (len(EN) - 1) - 0.2), 0, len(EN) - 1).astype(int)
    # 4. moonlit rim (top-left), one step up
    rim = top_left_rim(a, ink) & body
    idx = np.where(rim, np.minimum(idx + 1, n - 1), idx)
    eidx = np.where(rim, np.minimum(eidx + 1, len(EN) - 1), eidx)
    hs = hue_shift(h, s) * HUE_K.get(group, 1.0)
    res = np.zeros_like(rgb)
    res[metal] = (RAMP[idx] + hs)[metal]
    res[enam] = (EN[eidx] + hs * 0.5)[enam]
    res[ink] = OUTLINE
    gt = np.clip((L - 85) / 150.0, 0, 1)
    gc = accent_ramp(ACCENT[group], gt)
    res[glow] = gc[glow]
    idx2 = np.where(metal, idx, -1)
    # 5. sparkles
    if sparkle:
        rng = np.random.RandomState(seed & 0x7fffffff)
        cand = body & (idx2 >= len(RAMP) - 3) & ~e
        ys, xs = np.nonzero(cand)
        area = int(a.sum())
        n = 1 + (area > 180) + (area > 520)
        if len(ys):
            order = rng.permutation(len(ys))
            taken = []
            for k in order:
                y, x = ys[k], xs[k]
                if any(abs(y - ty) + abs(x - tx) < 6 for ty, tx in taken): continue
                taken.append((y, x))
                if len(taken) >= n: break
            star = area > 360 and rng.rand() < 0.34 and taken
            for j, (y, x) in enumerate(taken):
                res[y, x] = WHITE
                if star and j == 0:
                    for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                        yy, xx = y + dy, x + dx
                        if 0 <= yy < a.shape[0] and 0 <= xx < a.shape[1] and a[yy, xx] and not ink[yy, xx]:
                            res[yy, xx] = GLINT_ARM
    out[..., :3] = np.where(a[..., None], np.clip(np.rint(res), 0, 255), cell[..., :3]).astype(np.uint8)
    out[..., 3] = cell[..., 3]
    return out


# ------------------------------------------------------------------------------------------------ mod finals
def mod_finals():
    """[(group, monster id, sheet id, png path)] for every mod tier-3 final."""
    sheets = {os.path.basename(p)[:-5]: p[:-5] + ".png" for p in glob.glob(ROOT + "/art/out*/*.json")
              if not p.endswith("_preview.json") and "/out_silvervar/" not in p}
    out = []
    for g in GODS:
        src = open(src_file(f"{g}Pack.cs")).read()
        d = defs_of(src)
        if g in EXTRA:
            m = re.search(r'\bStarter = "(\w+)"', src); t1 = [m.group(1)] if m else []
        else:
            m = re.search(r'startingMonsters = new\[\]\s*\{([^}]*)\}', src)
            t1 = [x.strip().strip('"') for x in m.group(1).split(",")] if m else []
        t2 = [x for m in t1 if m in d for x in d[m]["to"]]
        t3 = [x for m in t2 if m in d for x in d[m]["to"]]
        for m in t3:
            if m in d: out.append((g, m, d[m]["art"], sheets.get(d[m]["art"])))
    for m, v in defs_of(open(src_file("StatuePack.cs")).read()).items():
        out.append(("Statue", m, v["art"], sheets.get(v["art"])))
    return out


def sha1(path):
    return hashlib.sha1(open(path, "rb").read()).hexdigest()


def seed_of(*parts):
    return int(hashlib.md5("|".join(str(p) for p in parts).encode()).hexdigest()[:8], 16)


def bake_sheet(group, sheet, png):
    man = json.load(open(png[:-4] + ".json"))
    im = np.array(Image.open(png).convert("RGBA"))
    cw, ch, cols = man["cellW"], man["cellH"], man["cols"]
    H, W = im.shape[:2]
    rows = H // ch
    def cell(i):
        x, y = (i % cols) * cw, (i // cols) * ch
        return im[y:y + ch, x:x + cw]
    idle = [cell(i) for a in man["anims"] if a["name"] == "Idle" for i in a["frames"]]
    st = Stats(idle or [cell(0)])
    st.calibrate(idle or [cell(0)], group)
    stone = {i for a in man["anims"] if a["name"] in STATUE_ANIMS for i in a["frames"]}
    out = im.copy()
    for i in range((W // cw) * rows):
        if i in stone: continue
        x, y = (i % cols) * cw, (i // cols) * ch
        out[y:y + ch, x:x + cw] = silverize(cell(i), st, group, seed_of(sheet, i))
    sid = PREFIX + sheet
    os.makedirs(OUT, exist_ok=True)
    Image.fromarray(out).save(os.path.join(OUT, sid + ".png"), optimize=True)
    m2 = {"cellW": cw, "cellH": ch, "cols": cols, "anims": man["anims"], "source": sheet, "sourceSha1": sha1(png),
          "group": group}
    with open(os.path.join(OUT, sid + ".json"), "w") as f:
        json.dump(m2, f, separators=(",", ":"))
    preview(Image.fromarray(out), m2, os.path.join(OUT, sid + "_preview.png"))
    return out, im, man, st


def preview(img, manifest, path, scale=3):
    cw, ch, cols = manifest["cellW"], manifest["cellH"], manifest["cols"]
    rows = manifest["anims"]
    Wd = max(len(a["frames"]) for a in rows) * (cw + 2) * scale
    Hd = len(rows) * (ch + 2) * scale
    bg = Image.new("RGBA", (Wd, Hd), (28, 26, 32, 255))
    for r, a in enumerate(rows):
        for j, fi in enumerate(a["frames"]):
            x0, y0 = (fi % cols) * cw, (fi // cols) * ch
            c = img.crop((x0, y0, x0 + cw, y0 + ch)).resize((cw * scale, ch * scale), Image.NEAREST)
            bg.alpha_composite(c, (j * (cw + 2) * scale, r * (ch + 2) * scale))
    bg.convert("RGB").save(path)


# ------------------------------------------------------------------------------------------------ vanilla finals
_V = {}


def vanilla_data():
    """Vanilla level-3/4 monsters -> their body clips' AtlasEnemies elements (from the game dump)."""
    if _V: return _V
    sys.path.insert(0, os.path.join(DUMP, "q"))
    bygo, bypid, gos = pickle.load(open(os.path.join(DUMP, "q", "idx.pkl"), "rb"))
    go, tr, native = pickle.load(open(os.path.join(DUMP, "q", "hier.pkl"), "rb"))
    deity = json.loads(open(os.path.join(DUMP, "db", "SystemDeity.jsonl")).readline())
    pl = {p["_go"]: p for p in bypid.values() if p["_cls"] == "Player"}

    def nm(ref):
        i = ref["m_PathID"]
        if i in go: return go[i]["name"]
        if i in bypid: return bypid[i]["_go"]

    def evo(n): return [nm(e) for e in pl[n]["m_evolveTo"]] if n in pl else []
    level = {}
    for d in deity["m_deities"]:
        fr = [nm(x) for x in d["m_startingMonsters"]]
        for L in range(1, 6):
            nx = []
            for m in fr:
                level[m] = max(level.get(m, 0), L); nx += evo(m)
            fr = nx
    atlas = None
    for l in open(os.path.join(DUMP, "db", "exAtlas.jsonl")):
        a = json.loads(l)
        if a.get("m_Name") == VANILLA_ATLAS[0]: atlas = a
    apid = atlas["_pid"]
    clips = {}
    for l in open(os.path.join(DUMP, "db", "exSpriteAnimClip.jsonl")):
        if '"m_PathID": %d' % apid not in l: continue
        c = json.loads(l); clips[c["_pid"]] = c

    def refs(v, out):
        if isinstance(v, dict):
            if set(v.keys()) == {"m_FileID", "m_PathID"}:
                if v["m_PathID"] in clips: out.add(v["m_PathID"])
            else:
                for x in v.values(): refs(x, out)
        elif isinstance(v, list):
            for x in v: refs(x, out)
    mons = {}
    for m, L in sorted(level.items()):
        if L < 3 or m not in pl: continue
        g = pl[m]["m_GameObject"]["m_PathID"]
        cs = set()
        for c in bygo.get(g, []):
            refs({k: v for k, v in c.items() if k not in ("m_GameObject", "m_Script")}, cs)
        els, names = [], []
        for c in sorted(cs, key=lambda p: clips[p]["m_Name"]):
            names.append(clips[c]["m_Name"])
            for f in clips[c]["frameInfos"]:
                if f["atlas"]["m_PathID"] == apid and f["index"] not in els: els.append(f["index"])
        mons[m] = dict(level=L, elements=els, clips=names)
    tex = np.array(Image.open(os.path.join(DUMP, "tex", VANILLA_ATLAS[1])).convert("RGBA"))
    _V.update(atlas=atlas, tex=tex, mons=mons, sha=sha1(os.path.join(DUMP, "tex", VANILLA_ATLAS[1])))
    return _V


def elem_rect(atlas, tex, i):
    """(x, y_top, w, h) of an element in the atlas png (origin top-left)."""
    H, W = tex.shape[:2]
    c = atlas["elements"][i]["coords"]
    x0 = round(c["x"] * W); w = round(c["width"] * W); h = round(c["height"] * H)
    y1 = H - round(c["y"] * H)
    return x0, y1 - h, w, h


def bake_vanilla(only=None):
    V = vanilla_data()
    atlas, tex = V["atlas"], V["tex"]
    done, pieces = set(), []      # (idx, array, trimX, trimY, monster)
    for m, info in V["mons"].items():
        els = []
        for i in info["elements"]:
            e = atlas["elements"][i]
            if e.get("rotated"):
                raise SystemExit("rotated vanilla element %d (%s) not handled" % (i, m))
            x, y, w, h = elem_rect(atlas, tex, i)
            if w <= 0 or h <= 0: continue
            els.append((i, tex[y:y + h, x:x + w].copy(), int(e["trimRect"]["x"]), int(e["trimRect"]["y"])))
        if not els: continue
        st = Stats([a for _, a, _, _ in els[:12]])
        st.calibrate([a for _, a, _, _ in els[:12]], "Vanilla")
        info["stats"] = (st.p5, st.p50, st.p95)
        for i, arr, tx, ty in els:
            if i in done: continue
            done.add(i)
            pieces.append((i, silverize(arr, st, "Vanilla", seed_of("vanilla", i)), tx, ty, m, arr))
    # shelf-pack (1 px gap), 1024 wide
    pieces.sort(key=lambda p: -p[1].shape[0])
    Wp, x, y, rowh, place = 1024, 1, 1, 0, []
    for p in pieces:
        h, w = p[1].shape[:2]
        if x + w + 1 > Wp: x, y, rowh = 1, y + rowh + 1, 0
        place.append((p, x, y)); x += w + 1; rowh = max(rowh, h)
    Hp = y + rowh + 1
    Hp = 1 << (Hp - 1).bit_length()
    sheet = np.zeros((Hp, Wp, 4), np.uint8)
    rows = []
    for (i, arr, tx, ty, m, orig), px, py in place:
        h, w = arr.shape[:2]
        sheet[py:py + h, px:px + w] = arr
        rows.append([i, px, py, w, h, tx, ty])
    rows.sort()
    os.makedirs(OUT, exist_ok=True)
    Image.fromarray(sheet).save(os.path.join(OUT, VANILLA_SHEET + ".png"), optimize=True)
    man = {"atlas": VANILLA_ATLAS[0], "width": Wp, "height": Hp, "elementCount": len(atlas["elements"]),
           "sourceSha1": V["sha"],
           "format": "elements: [vanilla element index, x, y (top-left in this png), w, h, trimX, trimY (the vanilla "
                     "trimRect, y from the top as ex2D stores it)]",
           "monsters": {m: info["elements"] for m, info in V["mons"].items()},
           "elements": rows}
    with open(os.path.join(OUT, VANILLA_SHEET + ".json"), "w") as f:
        json.dump(man, f, separators=(",", ":"))
    return place


# ------------------------------------------------------------------------------------------------ boards
def board(pairs, path, scale=2, cols=4, title_h=0):
    """pairs: [(label, orig RGBA array, silver RGBA array)] side by side on a dark floor."""
    cellw = max(o.shape[1] for _, o, _ in pairs) * 2 + 6
    cellh = max(o.shape[0] for _, o, _ in pairs) + 4
    rows = (len(pairs) + cols - 1) // cols
    bg = Image.new("RGBA", (cols * cellw * scale, rows * cellh * scale), (34, 31, 38, 255))
    for k, (lab, o, s) in enumerate(pairs):
        cx, cy = (k % cols) * cellw, (k // cols) * cellh
        for j, a in enumerate((o, s)):
            im = Image.fromarray(a).resize((a.shape[1] * scale, a.shape[0] * scale), Image.NEAREST)
            bg.alpha_composite(im, ((cx + 2 + j * (o.shape[1] + 2)) * scale, (cy + 2) * scale))
    bg.convert("RGB").save(path)


def frames_of(img, man, anim, k=None):
    a = [x for x in man["anims"] if x["name"] == anim]
    if not a: return []
    fr = a[0]["frames"] if k is None else a[0]["frames"][:k]
    cw, ch, cols = man["cellW"], man["cellH"], man["cols"]
    return [img[(i // cols) * ch:(i // cols + 1) * ch, (i % cols) * cw:(i % cols + 1) * cw] for i in fr]


def main(argv):
    only = None
    for a in argv:
        if a.startswith("--only"): only = set(argv[argv.index(a) + 1].split(",")) if a == "--only" else set(a.split("=", 1)[1].split(","))
    if "--check" in argv: return check()
    fins = mod_finals()
    missing = [(g, m, s) for g, m, s, p in fins if not p]
    for g, m, s in missing: print("MISSING SOURCE SHEET", g, m, s)
    idle_pairs, move_pairs = {}, {}
    n = 0
    for g, m, s, p in fins:
        if not p: continue
        if only and s not in only and m not in only: continue
        out, im, man, st = bake_sheet(g, s, p)
        n += 1
        o = frames_of(im, man, "Idle", 1)[0]; v = frames_of(out, man, "Idle", 1)[0]
        idle_pairs.setdefault(g, []).append((s, o, v))
        mv = [a["name"] for a in man["anims"] if a["name"] not in ("Idle", "Run", "Death", "Dead", "Statue", "Knockback", "Portrait", "Spawn")]
        if mv:
            fo = frames_of(im, man, mv[0]); fv = frames_of(out, man, mv[0])
            mid = len(fo) // 2
            move_pairs.setdefault(g, []).append((s, fo[mid], fv[mid]))
    print("baked %d mod silver variants -> %s" % (n, OUT))
    bd = os.path.join(BOARDS, "silvervar")
    os.makedirs(bd, exist_ok=True)
    for g in idle_pairs:
        board(idle_pairs[g], os.path.join(bd, "board_%s_idle.png" % g), scale=3, cols=4)
        board(move_pairs.get(g, []), os.path.join(bd, "board_%s_move.png" % g), scale=3, cols=4)
    if "--mod" not in argv and not only:
        if not os.path.exists(os.path.join(DUMP, "db", "exAtlas.jsonl")):
            print("vanilla dump missing: kept the existing", VANILLA_SHEET)
        else:
            place = bake_vanilla()
            V = vanilla_data()
            byel = {p[0][0]: p for p in place}
            pairs = []
            for m, info in V["mons"].items():
                els = [e for e in info["elements"] if e in byel][:3]
                for e in els[:2]:
                    (i, arr, tx, ty, mm, orig), px, py = byel[e]
                    pairs.append((m, orig, arr))
            # pad every pair to a common cell
            mh = max(o.shape[0] for _, o, _ in pairs); mw = max(o.shape[1] for _, o, _ in pairs)
            def padto(a):
                z = np.zeros((mh, mw, 4), np.uint8); z[mh - a.shape[0]:, (mw - a.shape[1]) // 2:(mw - a.shape[1]) // 2 + a.shape[1]] = a; return z
            pairs = [(l, padto(o), padto(s)) for l, o, s in pairs]
            half = (len(pairs) + 1) // 2
            board(pairs[:half], os.path.join(bd, "board_Vanilla_1.png"), scale=2, cols=6)
            board(pairs[half:], os.path.join(bd, "board_Vanilla_2.png"), scale=2, cols=6)
            print("baked vanilla silver: %d monsters, %d elements" % (len(V["mons"]), len(place)))
    return 0


def check():
    bad = 0
    for g, m, s, p in mod_finals():
        j = os.path.join(OUT, PREFIX + s + ".json")
        if not p: print("FAIL %s: source sheet %s missing" % (m, s)); bad += 1; continue
        if not os.path.exists(j): print("FAIL %s: no silver variant (run tools/sprites/silver_variants.py)" % s); bad += 1; continue
        v = json.load(open(j))
        if v.get("sourceSha1") != sha1(p): print("FAIL %s: silver variant is stale (source changed)" % s); bad += 1
    j = os.path.join(OUT, VANILLA_SHEET + ".json")
    if not os.path.exists(j): print("FAIL vanilla silver sheet missing"); bad += 1
    print("silver variants:", "OK" if not bad else "%d problems" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
