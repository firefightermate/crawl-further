"""The death-perk sheets for Vhorrul, Ossivar (in ossivar_rigs.py: FxBonePile Crawl) and Sylvene.

    python3 godsa_v15.py [--only Name,Name]

  Vhorrul   FxVhPyre      Ignite 4, Burn 6, Gutter 4   a dead monster's pyre: a 28 x 9 pool of burning tallow (5.4 s)
            FxVhPyreWax   Set 3, Idle 2, Fade 3        the pyre cools into a tallow slick (slows the hero, wax monsters
                                                       heal in it, any flame relights it), 8 s
  Sylvene   FxSylPodBurst Play 7                       a ripe pod bursting: a 34 x 14 cloud of spores (was the seed's
                                                       13 px Burst anim under a 26 x 12 box)

Drawn with godsa_fx.py's primitives in the gods' palettes. Origin = the floor point the effect is spawned on (Strike.Ground).
Coordinates: x right, y DOWN (negative = up), (0, 0) = the effect origin.
"""
import math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from rig import Canvas  # noqa: E402
from anim import Spr  # noqa: E402
import godsa_fx as G  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "art")
G.OUT["syl"] = os.path.join(ROOT, "out_sylvene")
if os.environ.get("FX_TMP"):
    G.OUT = {k: os.environ["FX_TMP"] for k in ("vh", "bel", "oss", "syl")}
    os.makedirs(os.environ["FX_TMP"], exist_ok=True)

PYRE_RX, PYRE_RY, PYRE_CY = 14.0, 4.3, -1.0   # the burning pool: 29 x 9 px around (0, -1)


def pool(c, rx, ry, cy, cols, seed, crack=None, crack_n=0):
    """A floor pool: cols = (rim, body, inner); `crack` lays glowing seams through the body."""
    rnd = random.Random(seed)
    rim, body, inner = cols
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(-rx - 1), int(rx + 2)):
            j = (rnd.random() - 0.5) * 0.18
            d = (x / max(rx, 0.5)) ** 2 + ((y - cy) / max(ry, 0.5)) ** 2 + j
            if d > 1.0: continue
            ch = rim if d > 0.66 else inner if d < 0.3 else body
            c.put(x, y, ch)
    if crack:
        for k in range(crack_n):
            a = rnd.uniform(0, 2 * math.pi)
            x0, y0 = rnd.uniform(-rx * 0.6, rx * 0.6), cy + rnd.uniform(-ry * 0.4, ry * 0.4)
            for t in range(rnd.randint(2, 4)):
                x, y = int(round(x0 + t * math.cos(a))), int(round(y0 + t * 0.4 * math.sin(a)))
                if (x / rx) ** 2 + ((y - cy) / ry) ** 2 < 0.7: c.put(x, y, crack[t % len(crack)])


def tongue(c, x, base, h, lean, ph):
    """One flame tongue rising from (x, base): hot core low, dark-orange tip, a 2 px body that tapers."""
    for t in range(h):
        k = t / max(1, h - 1)
        xx = x + int(round(lean * k * k + 0.6 * math.sin(ph + t * 0.9) * k))
        col = "y" if k < 0.22 else "Y" if k < 0.5 else "O" if k < 0.8 else "o"
        c.put(xx, base - t, col)
        if k < 0.75 and h > 3: c.put(xx + (1 if lean >= 0 else -1), base - t, "Y" if k < 0.25 else "O" if k < 0.5 else "o", over=False)


def pyre_frame(i, grow=1.0, flame=1.0, glow=1.0, embers=0, smoke=0, seed=0):
    c = Canvas()
    rx, ry = PYRE_RX * grow, PYRE_RY * min(1.0, 0.45 + 0.55 * grow)
    hot = glow > 0.5
    pool(c, rx, ry, PYRE_CY, ("K", "k", "a" if hot else "g") if glow > 0 else ("g", "h", "w"), 11, crack="oO" if hot else ("ag" if glow > 0.2 else "gk"),
         crack_n=int(7 * grow * (0.4 + glow)))
    if glow > 0.2:   # molten tallow core
        G.ell(c, 0, PYRE_CY, max(1.0, rx * 0.42), max(0.8, ry * 0.42), "OoaK" if hot else "akKK")
    rnd = random.Random(300 + seed * 17 + i)
    xs = [-11, -7, -3, 1, 5, 9, 12]
    for n, x in enumerate(xs):
        if abs(x) > rx - 1: continue
        centre = 1.0 - abs(x) / (PYRE_RX + 2)
        h = int(round(flame * (4 + 9 * centre ** 1.3) * (0.75 + 0.5 * rnd.random())))
        if h < 1: continue
        base = int(round(PYRE_CY + ry * 0.25 * ((n % 3) - 1)))
        tongue(c, x + (i + n) % 2, base, h, rnd.choice((-1.5, -0.8, 0.8, 1.5)), i * 1.3 + n)
    for k in range(embers):   # sparks lifting off
        x = rnd.randint(int(-rx * 0.8), int(rx * 0.8)); y = int(PYRE_CY - 6 - rnd.randint(0, 9) * flame - k % 3)
        c.put(x, y, "Y" if k % 3 else "y")
    for k in range(smoke):    # guttering smoke curls
        x = rnd.randint(-8, 8); y0 = int(PYRE_CY - 3 - k * 2)
        for t in range(3):
            c.put(x + int(round(math.sin(t + k + i))), y0 - t, "S" if t < 2 else "s")
    return c.spr()


def pyre():
    ignite = [pyre_frame(0, grow=0.35, flame=0.35, embers=1, seed=1), pyre_frame(1, grow=0.6, flame=0.6, embers=2, seed=2),
              pyre_frame(2, grow=0.85, flame=0.85, embers=3, seed=3), pyre_frame(3, grow=1.0, flame=1.05, embers=4, seed=4)]
    burn = [pyre_frame(i, embers=3 + i % 2, seed=10 + i) for i in range(6)]
    gutter = [pyre_frame(0, flame=0.6, glow=0.8, embers=2, smoke=1, seed=30), pyre_frame(1, flame=0.35, glow=0.45, embers=1, smoke=2, seed=31),
              pyre_frame(2, flame=0.15, glow=0.25, smoke=3, seed=32), pyre_frame(3, flame=0.0, glow=0.0, smoke=2, seed=33)]
    return ignite, burn, gutter


def pyre_wax():
    """The cooled pyre: a tallow slick with a soot crust, a burnt-out wick and the glints of the fresh wax."""
    def slick(seed, crust=0.0, glints=()):
        c = Canvas()
        pool(c, PYRE_RX - 0.5, PYRE_RY - 0.2, PYRE_CY, ("h", "w", "W"), seed)
        rnd = random.Random(77)
        for k in range(9):    # soot specks and charred flecks left by the fire
            x, y = rnd.randint(-11, 11), int(PYRE_CY + rnd.randint(-2, 2))
            if (x / (PYRE_RX - 1)) ** 2 + ((y - PYRE_CY) / (PYRE_RY - 1)) ** 2 < 0.8: c.put(x, y, "g" if k % 3 else "k")
        if crust > 0:         # still-glowing crust round the edge while it sets
            for k in range(int(26 * crust)):
                a = 2 * math.pi * k / max(1, int(26 * crust)) + 0.2
                c.put(int(round((PYRE_RX - 1.5) * math.cos(a))), int(round(PYRE_CY + (PYRE_RY - 1) * math.sin(a))), "a" if k % 3 else "o")
        c.put(-1, int(PYRE_CY) - 1, "K"); c.put(-1, int(PYRE_CY) - 2, "k"); c.put(0, int(PYRE_CY) - 2, "g")   # the dead wick
        for (x, y) in glints: c.put(x, y, "X")
        return c.spr()
    sett = [slick(1, crust=1.0), slick(1, crust=0.6), slick(1, crust=0.25)]
    idle = [slick(1, glints=((-6, -3), (5, -2))), slick(1, glints=((-3, -3), (8, -2)))]
    base = slick(1)
    fade = []
    for i in range(3):
        keep = 1 - (i + 1) / 4
        fade.append(Spr({kk: ({"w": "h", "W": "w", "h": "g", "X": "W"}.get(v, v))
                         for kk, v in base.px.items() if random.Random(kk[0] * 31 + kk[1] * 7 + i).random() < keep + 0.15}))
    return sett, idle, fade


def pod_burst():
    """A ripe Sylvene pod bursting into a broad spore cloud that hangs at hip height (frames 2-4 hurt)."""
    out = []
    # 0: the pod swells on its stalk
    c = Canvas()
    for y in range(-4, 1): c.put(0, y, "v")
    G.ell(c, 0, -8, 3.6, 3.9, "qnNF", bias=0.1)
    for (x, y) in ((-1, -10), (1, -7), (2, -9)): c.put(x, y, "F")
    out.append(c.spr())
    # 1: it splits, green light in the seams
    c = Canvas()
    for y in range(-4, 1): c.put(0, y, "v")
    G.ell(c, 0, -8, 4.4, 4.6, "qnNF", bias=0.1)
    for (x, y) in ((0, -12), (0, -11), (-1, -10), (1, -9), (0, -8), (-2, -6), (2, -7), (3, -10), (-3, -9)): c.put(x, y, "G")
    c.put(0, -9, "y")
    out.append(c.spr())
    # 2-6: the pop and the spreading cloud
    specs = [(8, 4.5, 0.15, 0.0, 6), (13, 6.5, 0.3, 0.05, 14), (16, 7.0, 0.35, 0.18, 18), (17, 7.2, 0.4, 0.45, 14), (17, 7.0, 0.45, 0.75, 8)]
    for k, (rx, ry, noise, holes, motes) in enumerate(specs):
        c = Canvas()
        cy = -7 + (k >= 3)
        cols = ["y", "G", "F", "N", "n"] if k == 0 else ["F", "F", "N", "N", "n"] if k < 3 else ["N", "N", "n", "q"]
        rnd = random.Random(90 + k)
        for lobe in range(5):   # a lumpy cloud from several overlapping puffs
            lx = (lobe - 2) * rx * 0.42 + rnd.uniform(-1, 1); ly = cy + rnd.uniform(-1.5, 1.5) - (2 if lobe == 2 else 0)
            G.blob(c, lx, ly, ry * (1.0 if lobe in (1, 2, 3) else 0.75), cols, noise=noise, seed=lobe * 7 + k, holes=holes, sy=0.85)
        if k == 0:
            for a in range(0, 360, 30):
                rr = math.radians(a)
                c.put(int(round(10 * math.cos(rr))), int(round(cy + 5 * math.sin(rr))), "G")
        for m in range(motes):
            a = rnd.uniform(0, 2 * math.pi); r = rnd.uniform(0.8, 1.25)
            c.put(int(round(rx * r * math.cos(a))), int(round(cy + ry * r * math.sin(a))), "G" if m % 3 == 0 else "F" if m % 3 == 1 else "V")
        if k < 3:
            for x in (-1, 0, 1): c.put(x, 0, "v")   # torn stalk at the floor
            c.put(0, -1, "v")
        out.append(c.spr())
    return out


BUILT = {}


def build(only=None):
    def want(n): return only is None or n in only
    if want("FxVhPyre"):
        ig, burn, gut = pyre()
        G.sheet("vh", "FxVhPyre", [("Ignite", ig, [0.06] * 4), ("Burn", burn, [0.09] * 6), ("Gutter", gut, [0.1, 0.1, 0.12, 0.14])])
    if want("FxVhPyreWax"):
        st, idle, fade = pyre_wax()
        G.sheet("vh", "FxVhPyreWax", [("Set", st, [0.12, 0.14, 0.16]), ("Idle", idle, [0.4, 0.4]), ("Fade", fade, [0.12] * 3)])
    if want("FxSylPodBurst"):
        G.sheet("syl", "FxSylPodBurst", [("Play", pod_burst(), [0.08, 0.07, 0.06, 0.08, 0.1, 0.12, 0.14])])
    for k, v in G.BUILT.items(): BUILT[k] = v


MARK0, MARK1 = "<!-- perk sheets (godsa_v15.py) -->", "<!-- /perk sheets -->"
NOTES = {
    "FxVhPyre": "perk: a dead Vhorrul monster's pyre. Clip Ignite + Burn x9 + Gutter (5.6 s); damage live from Ignite f2 to Gutter f1;"
                " 28 x 9 floor box on the origin; then FxVhPyreWax",
    "FxVhPyreWax": "perk: the cooled pyre. Clip Set + Idle x9 + Fade (8.0 s); slow zone live Set f1 to Fade f0; 26 x 8 floor box",
    "FxSylPodBurst": "perk: ripe pod burst (SylveneFx.PodBurst for monster seeds). Damage live f2-f4 (0.21-0.45 s); 34 x 14 box on the origin",
}


# perk sheets drawn in the gods' own rigs (listed here so each TIMING.md has one perk section)
EXTRA = {
    "oss": {"FxBonePile": ((9, 10), "perk: Crawl 4 x 0.09 s (loop) while the pile drags itself to an Ossivar monster (OssBoneCrawlFx);"
                                    " drawn in ossivar_rigs.py fx_bone_crawl, same cell as the pile"),
            "FxOssSpikeBurst": ((30, 14), "the Ossuary's Ossify burst drawn at its size (ossivar_rigs.py fx_spike_ring(1.3));"
                                         " was FxSpikeRing scaled x1.3. Damage f0-f2, 52 x 21 floor box")},
    "syl": {"FxSylRootErupt": ((18, 13), "Rot Mother / Carrion Lily root eruption drawn at its size (sylvene_rigs.py root_line_frames(1.3));"
                                        " was FxRootLine scaled x1.3. Damage f3-f4, 29 x 13 floor box"),
            "FxSylSproutPuff": ((8, 11), "the Sprout's puff drawn at its size (sylvene_rigs.py spore_cloud_frames(0.7)); was FxSporeCloud"
                                        " scaled x0.7. 11 x 10 box"),
            "FxSeed": ((10, 16), "perk: Life now 2.5 s (growth 6 x 0.3, ripe pulse 4 x 0.175); the pod is ripe at 2.5 s")},
}


def write_timing():
    import json
    G.OUT.setdefault("oss", os.path.join(ROOT, "out_ossivar"))
    for god, d in (("vh", G.OUT["vh"]), ("syl", G.OUT["syl"]), ("oss", G.OUT["oss"])):
        L = ["", MARK0, "## Perk sheets (tools/sprites/godsa_v15.py)", "",
             "| Sheet | Cell | Origin (cell px, y down) | Anims (frames: durations) | Use |", "|---|---|---|---|---|"]
        for name, note in NOTES.items():
            jp = os.path.join(d, name + ".json")
            if not os.path.exists(jp) or name not in BUILT or BUILT[name]["god"] != god: continue
            m = json.load(open(jp))
            o = BUILT[name]["origin"]
            an = "; ".join("%s %d: %s" % (a["name"], len(a["frames"]), ", ".join("%.3g" % x for x in a["durations"])) for a in m["anims"])
            L.append("| %s | %d x %d | (%d, %d) | %s | %s |" % (name, m["cellW"], m["cellH"], o[0], o[1], an, note))
        for name, (o, note) in EXTRA.get(god, {}).items():
            jp = os.path.join(d, name + ".json")
            if not os.path.exists(jp): continue
            m = json.load(open(jp))
            an = "; ".join("%s %d" % (a["name"], len(a["frames"])) for a in m["anims"])
            L.append("| %s | %d x %d | (%d, %d) | %s | %s |" % (name, m["cellW"], m["cellH"], o[0], o[1], an, note))
        L.append(MARK1)
        p = os.path.join(d, "TIMING.md")
        old = open(p).read() if os.path.exists(p) else ""
        if MARK0 in old:
            old = old[:old.index(MARK0)].rstrip("\n") + "\n" + old[old.index(MARK1) + len(MARK1):].lstrip("\n")
        open(p, "w").write(old.rstrip("\n") + "\n" + "\n".join(L) + "\n")
        print("timing ->", p)


if __name__ == "__main__":
    a = sys.argv[1:]
    only = set(a[a.index("--only") + 1].split(",")) if "--only" in a else None
    build(only)
    if not os.environ.get("FX_TMP") and only is None: write_timing()
