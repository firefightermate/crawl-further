"""Static checks of the C# content against the art (run before every package).

    python3 tools/validate.py            # all checks, prints an OK/FAIL line per check, exit 1 on any FAIL
    python3 tools/validate.py -v         # also print warnings and per-check details

Checks (each prints OK or FAIL with the problems underneath):
  manifests     every sheet's json/png agree (frame indices in range, one duration per frame, sane durations)
  duplicates    a sheet id lives in exactly one art dir (the deploy folder is flat: a second copy would overwrite it)
  code-refs     every sheet the code names exists, and every (sheet, anim) the code builds a clip from exists:
                FxKit/WeaponFx helpers, "Sheet", "Anim" argument pairs, SpriteSheets.Get variables, kit bodies
                (ClipBuilder / Kit.Shot / Kit.Melee / Then), alias maps; event frames inside the clip
  vanilla       every vanilla prefab passed to Clone/Projectile/Swipe/... and every basePrefab/cloneFrom exists
  monsters      every MonsterDef sheet: Idle/Run/Death/Dead/Statue/Knockback/Portrait (+ every move its kit uses)
                with sensible frame counts; no empty frames; nothing touching a cell edge (clipped)
  sizes         visible Idle bounds within the tier limits (T1 20x16, T2 28x26, T3 42x40)
  feet          feet on the cell's centre column at cellH-2 (grounded) or above it (hover); never below
  statues       each sheet's Statue frame is grey stone; ModStatues has a Statue_<sheet> frame for every T3 final,
                plinth on the bottom row and centred
  fx            every FX sheet the code uses: no empty frames inside an anim (a trailing fade-out frame is ok)
  items         every shop item: 34x41 Bubble, 11x7 Hud for artifacts, a ShopPedestals frame; every weapon:
                IconWpn<id>Bubble and a Wpn<id> pedestal frame
  portraits     every god (Deity*), origin (Hero*) and ghost form (Ghost*): 29x24 Idle with a non-empty first frame
  badge         the ModBadgeGem sheet is the 5 x 5 gem tools/badge.py defines, pixel for pixel
  marks         one violet mark per entry: gems placed only through UI/ModMark.cs, one call site per context, no gem
                painted into any art
  vaultfit      every vault page text (monster lines, FURTHER pages, objects, items, weapons, secrets hidden and found,
                category summaries) fits its box without the "..." cut, laid out exactly like UI/TextFit.cs; a monster
                line leaves its page's last row above the buttons to the challenge line
  textfit       text the mod lays out in boxes it can't grow (modelled with the fonts' own pixel widths and the boxes'
                sizes from the code and the game's scenes): every HUD monster tip at full size in a two-player column and
                readable in a four-player one, the god-select panel's texts within the four lines the game's own take,
                the unlock banner's lines inside the banner, the pause pages' subtitles beside their tab and counter
  previews      every monster/fx sheet's _preview.png is at least as new as its png (previews are not committed:
                missing ones are a warning)
  package       the files tools/package.sh ships contain every sheet the code loads
  menulists     a pick list copied from a vanilla MenuTextMenu switches the copy's component on (else it ignores input)
"""
import collections, glob, json, os, re, shutil, sys, tempfile

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# A dump of the game's assets and decompiled code (db/, q/, src/), made outside this repo. Checks that need it are
# skipped with a warning when it is missing. Set CRAWL_DUMP to its folder; the default is build/dump.
SCR = os.environ.get("CRAWL_DUMP", os.path.join(ROOT, "build", "dump"))
VERBOSE = "-v" in sys.argv
sys.path.insert(0, os.path.join(ROOT, "tools"))

SKIP_JSON = ("_preview", "board", "contact_idle", "fx_all", "designs_board")
TIER_LIMIT = {1: (20, 16), 2: (28, 26), 3: (42, 40)}     # (max width, max height) of the visible Idle frame
# monsters outside a god's tree (no evolveCost): which tier's size limit applies
MINION_TIER = {"BlobMote": 1, "BlobSpitter": 1, "BlobGel": 1, "BlobBrute": 2, "BlobTitan": 2, "BlobKing": 3}
BASE_ANIMS = ["Idle", "Run", "Death", "Dead", "Statue", "Knockback", "Portrait"]
ONE_FRAME = ["Dead", "Statue", "Knockback", "Portrait"]
VIOLET = (154, 92, 191)
# names in string literals that look like sheet ids but are prefixes joined at run time
PREFIX_LITERALS = {"IconWpn", "Blob", "Ghost", "Ghosts", "Blobfish", "Hero"}
# silver / gold slots: unlock challenge ids / counter names and menu state names that look like sheet ids
PREFIX_LITERALS |= {"HeroSilver", "HeroGold", "GhostSilver", "GhostGold", "HeroKills", "HeroWins", "HeroesSlain", "DeitySelected"}

RESULTS = collections.OrderedDict()   # check -> (fails, warns, count)


def check(name):
    def deco(fn):
        def run():
            fails, warns = [], []
            try:
                n = fn(fails, warns)
            except Exception as e:     # a crash in a check is a failure of that check, not of the run
                import traceback
                fails.append("check crashed: %r\n%s" % (e, traceback.format_exc()))
                n = 0
            RESULTS[name] = (fails, warns, n)
        run.__name__ = fn.__name__
        CHECKS.append(run)
        return run
    return deco


CHECKS = []

# ----------------------------------------------------------------------------------------------------------- loading
SHEETS = {}          # id -> manifest (+ "_dir", "_png")
ALL_COPIES = collections.defaultdict(list)
# art/core holds Core's own sheets, art/out* the content mod's; package.sh flattens all of them into one art folder
ART_DIRS = [os.path.join(ROOT, "art", "core")] + sorted(glob.glob(os.path.join(ROOT, "art", "out*")))
CORE_SRC = os.path.join(ROOT, "src", "CrawlFurther.Core")
CONTENT_SRC = os.path.join(ROOT, "src", "CrawlFurther")
for f in [j for d in ART_DIRS for j in sorted(glob.glob(os.path.join(d, "*.json")))]:
    sid = os.path.basename(f)[:-5]
    if sid.endswith(SKIP_JSON) or sid in SKIP_JSON:
        continue
    try:
        m = json.load(open(f))
    except Exception:
        continue
    if "anims" not in m:
        continue
    png = f[:-5] + ".png"
    m["_dir"] = os.path.basename(os.path.dirname(f))
    m["_png"] = png
    m["_anims"] = {a["name"]: a for a in m["anims"]}
    ALL_COPIES[sid].append(m)
    SHEETS[sid] = m      # same order as package.sh's copy loop: the last dir wins

_IMG = {}


def img(sid):
    if sid not in _IMG:
        _IMG[sid] = Image.open(SHEETS[sid]["_png"]).convert("RGBA")
    return _IMG[sid]


def cell(sid, fi):
    m = SHEETS[sid]
    cw, ch, cols = m["cellW"], m["cellH"], m["cols"]
    x, y = (fi % cols) * cw, (fi // cols) * ch
    return img(sid).crop((x, y, x + cw, y + ch))


def bbox(im):
    return im.split()[3].point(lambda v: 255 if v > 0 else 0).getbbox()


def has(sid, anim):
    return sid in SHEETS and anim in SHEETS[sid]["_anims"]


def nframes(sid, anim):
    return len(SHEETS[sid]["_anims"][anim]["frames"]) if has(sid, anim) else 0


SRC = {}
for f in sorted(glob.glob(os.path.join(ROOT, "src", "**", "*.cs"), recursive=True)):
    SRC[f] = open(f).read()


def strip_comments(s):
    # keep line numbers: blank out // and /* */ comments but keep the newlines (strings with // are rare: keep "...")
    out, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c == '"':
            j = i + 1
            while j < n and s[j] != '"':
                j += 2 if s[j] == "\\" else 1
            out.append(s[i:j + 1]); i = j + 1
        elif s.startswith("//", i):
            j = s.find("\n", i); j = n if j < 0 else j
            out.append(" " * (j - i)); i = j
        elif s.startswith("/*", i):
            j = s.find("*/", i + 2); j = n if j < 0 else j + 2
            out.append(re.sub(r"[^\n]", " ", s[i:j])); i = j
        else:
            out.append(c); i += 1
    return "".join(out)


CODE = {f: strip_comments(s) for f, s in SRC.items()}


def where(f, pos):
    return "%s:%d" % (os.path.relpath(f, ROOT), CODE[f].count("\n", 0, pos) + 1)


def block(s, i):
    """The {...} block starting at the first '{' at or after i (string-aware)."""
    j = s.index("{", i)
    d, k, n = 0, j, len(s)
    while k < n:
        c = s[k]
        if c == '"':
            k += 1
            while k < n and s[k] != '"':
                k += 2 if s[k] == "\\" else 1
        elif c == "{":
            d += 1
        elif c == "}":
            d -= 1
            if d == 0:
                return j, k + 1
        k += 1
    return j, n


def field(body, key, quoted=True):
    m = re.search(r'\b%s\s*=\s*"([^"]*)"' % key, body) if quoted else re.search(r'\b%s\s*=\s*(-?[\d.]+)f?' % key, body)
    return m.group(1) if m else None


def objects(kind):
    """Every `new <kind> { ... }` initializer: (file, pos, body)."""
    for f, s in CODE.items():
        for m in re.finditer(r'new %s\s*\{' % kind, s):
            a, b = block(s, m.start())
            yield f, m.start(), s[a:b]


# ------------------------------------------------------------------------------------------------- content inventory
MONSTERS = []        # dicts: id, art, cost, tier, kit, aliases, file, pos
for f, pos, body in objects("MonsterDef"):
    mid = field(body, "id")
    cost = field(body, "evolveCost", quoted=False)
    cost = float(cost) if cost is not None else -1.0
    tier = 3 if cost >= 4 else 2 if cost >= 2 else 1 if cost >= 0 else 0
    kit = re.search(r'\bkit\s*=\s*(\w+)', body)
    aliases = dict(re.findall(r'\{\s*"(\w+)"\s*,\s*"(\w+)"\s*\}', body[body.find("aliases"):]) if "aliases" in body else [])
    MONSTERS.append(dict(id=mid, art=field(body, "art") or mid, cost=cost, tier=tier, kit=kit.group(1) if kit else None,
                         aliases=aliases, file=f, pos=pos, base=field(body, "basePrefab")))

ITEMS = []
for f, pos, body in objects("ItemDef"):
    ITEMS.append(dict(id=field(body, "id"), group=field(body, "group") or "", bubble=field(body, "bubbleArt"),
                      hud=field(body, "hudArt"), clone=field(body, "cloneFrom"), file=f, pos=pos))
WEAPONS = []
for f, pos, body in objects("WeaponDef"):
    WEAPONS.append(dict(id=field(body, "id"), base=field(body, "baseWeapon"), file=f, pos=pos))
PORTRAITS = []       # (kind, name, sheet, file, pos)
for kind, cls, key in [("god", "GodDef", "name"), ("origin", "OriginDef", "id"), ("ghost form", "GhostFormEntry", "name")]:
    for f, pos, body in objects(cls):
        PORTRAITS.append((kind, field(body, key), field(body, "portraitArt"), f, pos))


def kit_bodies():
    """kit function name -> (file, start, end, body) for every `static void X(Player p, Sheet sh)`."""
    out = {}
    for f, s in CODE.items():
        for m in re.finditer(r'static\s+void\s+(\w+)\s*\(\s*Player\s+\w+\s*,\s*SpriteSheet\s+(\w+)\s*\)', s):
            a, b = block(s, m.end())
            out[(f, m.group(1))] = (f, a, b, s[a:b], m.group(2))
    return out


KITS = kit_bodies()
KIT_ART = collections.defaultdict(set)
for mo in MONSTERS:
    if mo["kit"]:
        KIT_ART[(mo["file"], mo["kit"])].add(mo["art"])

# (sheet, anim) -> list of places; filled by code-refs and reused by package / fx checks
REFS = collections.defaultdict(list)
SHEET_REFS = collections.defaultdict(list)

# ------------------------------------------------------------------------------------------------------------ checks


@check("manifests")
def c_manifests(fails, warns):
    for sid, m in SHEETS.items():
        if not os.path.exists(m["_png"]):
            fails.append("%s/%s.png missing" % (m["_dir"], sid)); continue
        W, H = img(sid).size
        cw, ch, cols = m["cellW"], m["cellH"], m["cols"]
        count = (W // cw) * (H // ch)        # SpriteSheets's element count; element i sits at (i % cols, i // cols)
        if cols * cw > W:
            fails.append("%s: %d cols of %dpx do not fit the %dpx-wide png" % (sid, cols, cw, W))
        for a in m["anims"]:
            fr, du = a.get("frames", []), a.get("durations", [])
            if not fr:
                fails.append("%s/%s: no frames" % (sid, a["name"]))
            if any(i < 0 or i >= count or (i // cols + 1) * ch > H for i in fr):
                fails.append("%s/%s: frame index out of the png (%s, %d cells)" % (sid, a["name"], fr, count))
            if len(du) != len(fr):
                fails.append("%s/%s: %d frames but %d durations" % (sid, a["name"], len(fr), len(du)))
            if any(d <= 0 or d > 3.0 for d in du):
                fails.append("%s/%s: odd duration %s" % (sid, a["name"], du))
    return len(SHEETS)


@check("duplicates")
def c_duplicates(fails, warns):
    for sid, copies in ALL_COPIES.items():
        if len(copies) < 2:
            continue
        datas = set(open(c["_png"], "rb").read() for c in copies)
        dirs = ", ".join(c["_dir"] for c in copies)
        if len(datas) == 1:
            warns.append("%s is in %s (identical)" % (sid, dirs))
        else:
            fails.append("%s is in %s with different pixels: the flat deploy folder keeps only %s's" % (sid, dirs, copies[-1]["_dir"]))
    return len(ALL_COPIES)


def need(sid, anim, at, fails, optional=False):
    SHEET_REFS[sid].append(at)
    if sid not in SHEETS:
        if not optional: fails.append("%s: sheet %s missing" % (at, sid))
        return 0
    if anim is None:
        return 0
    REFS[(sid, anim)].append(at)
    if anim not in SHEETS[sid]["_anims"]:
        if not optional: fails.append("%s: %s has no anim '%s' (has %s)" % (at, sid, anim, ", ".join(sorted(SHEETS[sid]["_anims"]))))
        return 0
    return nframes(sid, anim)


def clip_statements(body):
    return re.split(r';\s*(?:\n|$)', body)


def event_frames(st):
    frames = [int(x) for x in re.findall(r'\.Ev[FSOB]?\(\s*(\d+)\s*,', st)]
    sm = re.search(r'Kit\.Shot\(\s*\w+\s*,\s*"[^"]+"\s*,\s*"[^"]+"\s*,\s*(\d+)', st)
    if sm: frames.append(int(sm.group(1)))
    mm = re.search(r'Kit\.Melee\(\s*\w+\s*,\s*"[^"]+"\s*,\s*"[^"]+"\s*,\s*[^,]+,\s*([^)]*)\)', st)
    if mm:
        nums = [x.strip().rstrip("f") for x in mm.group(1).split(",")]
        frames += [int(float(nums[i])) + 1 for i in range(0, len(nums), 3) if re.match(r'^\d+(\.\d+)?$', nums[i])]
    return frames


@check("code-refs")
def c_code_refs(fails, warns):
    n0 = 0
    monster_ids = set(m["id"] for m in MONSTERS)
    # 1. every literal that looks like one of our sheet ids names a real sheet
    for f, s in CODE.items():
        for m in re.finditer(r'"((?:Fx|Icon|Deity|Hero|Ghost|Blob)[A-Za-z0-9]*)"', s):
            lit = m.group(1)
            if lit in SHEETS or lit in PREFIX_LITERALS or lit in monster_ids:
                if lit in SHEETS: SHEET_REFS[lit].append(where(f, m.start()))
                continue
            after = s[m.end():m.end() + 3]
            before = s[max(0, m.start() - 3):m.start()]
            if "+" in after or "+" in before:
                continue
            # vanilla names (HeroSlimeDropper, ...) are checked by the vanilla check
            if lit in VANILLA:
                continue
            if not VANILLA:     # without the dump a vanilla name can't be told apart from a missing sheet
                warns.append("%s: \"%s\" is no mod sheet (a vanilla name? no dump to check)" % (where(f, m.start()), lit))
                continue
            fails.append("%s: \"%s\" looks like a mod sheet id but no art/out*/%s.json exists" % (where(f, m.start()), lit, lit))
    # 2. kit bodies: every clip anim, Then(), event frames in range
    masked = {f: list(s) for f, s in CODE.items()}
    for key, (f, a, b, body, shv) in KITS.items():
        kit = key[1]
        arts = KIT_ART.get(key)
        for k in range(a, b):
            if masked[f][k] != "\n": masked[f][k] = " "
        if not arts:
            continue    # a kit no MonsterDef uses (helper with the kit signature)
        for art in sorted(arts):
            at = "%s(%s)" % (kit, art)
            for st in clip_statements(body):
                cm = re.search(r'(?:new ClipBuilder\(\s*%s\s*,\s*|Kit\.(?:Shot|Melee)\(\s*%s\s*,\s*)"([^"]+)"' % (shv, shv), st)
                if not cm:
                    continue
                n0 += 1
                total = need(art, cm.group(1), at, fails)
                for t in re.finditer(r'\.Then\(\s*"([^"]+)"(?:\s*,\s*(\d+))?\)', st):
                    total += need(art, t.group(1), at, fails) * int(t.group(2) or 1)
                rep = re.search(r'\.Repeat\((\d+)\)', st)
                if rep: total *= int(rep.group(1))
                fr = event_frames(st)
                if total and fr and max(fr) >= total:
                    fails.append("%s: clip on %s puts an event on frame %d but has %d frames" % (at, cm.group(1), max(fr), total))
                du = re.search(r'\.Durations\(([^)]*)\)', st)
                if du and total and not re.search(r'\.Then\(|\.Repeat\(', st):
                    k = len([x for x in du.group(1).split(",") if x.strip()])
                    if k != nframes(art, cm.group(1)) and "new " not in du.group(1):
                        warns.append("%s: %s has %d frames but Durations() gives %d" % (at, cm.group(1), nframes(art, cm.group(1)), k))
            for m in re.finditer(r'\b%s\.(?:Has|Anim)\(\s*"([^"]+)"\s*\)' % shv, body):
                need(art, m.group(1), at, fails, optional=True)
    masked = {f: "".join(v) for f, v in masked.items()}
    # 3. SpriteSheets.Get variables outside kits: the nearest preceding `v = SpriteSheets.Get("S")`
    for f, s in masked.items():
        gets = [(m.start(), m.group(1), m.group(2)) for m in re.finditer(r'\b(\w+)\s*=\s*SpriteSheets\.Get\(\s*"(\w+)"\s*\)', s)]
        for m in re.finditer(r'(?:new ClipBuilder\(|SpriteSheets\.MakeClip\(|Kit\.(?:Shot|Melee)\()\s*(\w+)\s*,\s*"(\w+)"', s):
            v, anim = m.group(1), m.group(2)
            src = [g for g in gets if g[1] == v and g[0] < m.start()]
            if not src:
                continue
            n0 += 1
            need(src[-1][2], anim, where(f, m.start()), fails)
        for m in re.finditer(r'\b(\w+)\.Anim\(\s*"(\w+)"\s*\)', s):
            src = [g for g in gets if g[1] == m.group(1) and g[0] < m.start()]
            if src: n0 += 1; need(src[-1][2], m.group(2), where(f, m.start()), fails)
    # 4. "Sheet", "Anim" argument pairs anywhere (FxKit.*, WeaponFx.*, Vis(...), Strike.*)
    for f, s in masked.items():
        base = os.path.basename(f)
        if base.startswith(("LibraryEntries", "MonsterTips", "VaultLines")):
            continue
        for m in re.finditer(r'"(\w+)"\s*,\s*"(\w+)"(\s*\+)?', s):
            sid, anim, plus = m.groups()
            if sid not in SHEETS or anim in SHEETS or anim in monster_ids:
                continue
            n0 += 1
            if plus:
                if not any(a.startswith(anim) for a in SHEETS[sid]["_anims"]):
                    fails.append("%s: %s has no anim starting with '%s'" % (where(f, m.start()), sid, anim))
                continue
            need(sid, anim, where(f, m.start()), fails)
        # FxKit.MinionSpawner(name, prefab, "art", "anim")
        for m in re.finditer(r'MinionSpawner\(\s*"[^"]+"\s*,\s*[^,]+,\s*"(\w+)"\s*,\s*"(\w+)"', s):
            n0 += 1; need(m.group(1), m.group(2), where(f, m.start()), fails)
        # Strike.ArtAt / Ground name a sheet (the origin pixel may lie outside the cell: art drawn above a floor origin)
        for m in re.finditer(r'Strike\.(?:ArtAt|Ground)\(\s*\w+\s*,\s*"(\w+)"', s):
            need(m.group(1), None, where(f, m.start()), fails)
    # 5. alias maps (monsters without a kit animate their base kit's attacks from these)
    for mo in MONSTERS:
        for slot, anim in mo["aliases"].items():
            need(mo["art"], anim, "%s aliases[%s]" % (mo["id"], slot), fails)
    return n0


VANILLA = set()
try:
    gos = json.load(open(os.path.join(SCR, "db", "_gameobjects.json")))
    VANILLA = set(v["name"] if isinstance(v, dict) else v for v in (gos.values() if isinstance(gos, dict) else gos))
except Exception:
    pass
try:
    for l in open(os.path.join(SCR, "q", "prefabs.txt")):
        if l.strip(): VANILLA.add(l.split()[0].strip())
except Exception:
    pass


@check("vanilla")
def c_vanilla(fails, warns):
    if not VANILLA:
        warns.append("vanilla prefab dump not found (%s/db): skipped" % SCR); return 0
    n = 0
    for f, s in CODE.items():
        pats = [r'FxFactory\.(?:Clone|Vanilla)\(\s*"([^"]+)"', r'FxKit\.(?:Swipe|Projectile|TimedHit)\(\s*"[^"]+"\s*,\s*"([^"]+)"',
                r'\b(?:Swipe|Shot)\(\s*"[^"]+"\s*,\s*"([^"]+)"', r'cloneFrom\s*=\s*"([^"]+)"', r'basePrefab\s*=\s*"([^"]+)"',
                r'baseWeapon\s*=\s*"([^"]+)"']
        for p in pats:
            for m in re.finditer(p, s):
                n += 1
                if m.group(1) not in VANILLA:
                    fails.append("%s: vanilla prefab %s not found" % (where(f, m.start()), m.group(1)))
    return n


def kit_anims(mo):
    """Anims the monster's kit builds clips from."""
    out = []
    k = (mo["file"], mo["kit"])
    if k in KITS:
        body, shv = KITS[k][3], KITS[k][4]
        out += re.findall(r'(?:new ClipBuilder\(\s*%s\s*,\s*|Kit\.(?:Shot|Melee)\(\s*%s\s*,\s*)"([^"]+)"' % (shv, shv), body)
        out += re.findall(r'\.Then\(\s*"([^"]+)"', body)
    out += list(mo["aliases"].values())
    return sorted(set(out))


def is_t3_final(mo):
    return mo["tier"] == 3


@check("monsters")
def c_monsters(fails, warns):
    seen = set()
    for mo in MONSTERS:
        art, at = mo["art"], "%s (%s)" % (mo["id"], mo["art"])
        if art not in SHEETS:
            fails.append("%s: sheet missing" % at); continue
        if art in seen:
            continue
        seen.add(art)
        m = SHEETS[art]
        for a in BASE_ANIMS:
            if a not in m["_anims"]:
                fails.append("%s: no %s anim" % (at, a))
        for a in ONE_FRAME:
            if has(art, a) and nframes(art, a) != 1:
                warns.append("%s: %s has %d frames (expected 1)" % (at, a, nframes(art, a)))
        if nframes(art, "Idle") < 2: warns.append("%s: Idle has %d frames" % (at, nframes(art, "Idle")))
        if nframes(art, "Run") < 4: fails.append("%s: Run has %d frames" % (at, nframes(art, "Run")))
        if has(art, "Death") and nframes(art, "Death") < 3: warns.append("%s: Death has %d frames" % (at, nframes(art, "Death")))
        moves = [a for a in kit_anims(mo) if a not in BASE_ANIMS]
        if mo["kit"] and not moves:
            fails.append("%s: kit %s builds no clip from the sheet" % (at, mo["kit"]))
        for a in moves:
            k = nframes(art, a)
            if k and not (2 <= k <= 14):
                warns.append("%s: move %s has %d frames" % (at, a, k))
        cw, ch = m["cellW"], m["cellH"]
        for a in m["anims"]:
            for i, fi in enumerate(a["frames"]):
                c = cell(art, fi)
                bb = bbox(c)
                if not bb:
                    fails.append("%s: %s[%d] is empty" % (at, a["name"], i)); continue
                if bb[0] == 0 or bb[1] == 0 or bb[2] == cw or bb[3] == ch:
                    side = [n for n, v in (("left", bb[0] == 0), ("top", bb[1] == 0), ("right", bb[2] == cw), ("bottom", bb[3] == ch)) if v]
                    fails.append("%s: %s[%d] touches the cell's %s edge (clipped?)" % (at, a["name"], i, "/".join(side)))
                if a["name"] in ("Idle", "Run", "Portrait"):
                    # an outline: the outermost opaque pixels of each row should be dark
                    pass
        # durations: sensible per-frame timings
        for a in m["anims"]:
            if a["name"] in ("Dead", "Statue", "Portrait", "Knockback"):
                continue
            if any(d < 0.02 or d > 1.6 for d in a["durations"]):
                warns.append("%s: %s durations %s" % (at, a["name"], a["durations"]))
    return len(seen)


def idle_bounds(art):
    bbs = [bbox(cell(art, fi)) for fi in SHEETS[art]["_anims"]["Idle"]["frames"]]
    bbs = [b for b in bbs if b]
    return (min(b[0] for b in bbs), min(b[1] for b in bbs), max(b[2] for b in bbs), max(b[3] for b in bbs)) if bbs else None


@check("sizes")
def c_sizes(fails, warns):
    n = 0
    for mo in MONSTERS:
        art = mo["art"]
        if not has(art, "Idle"):
            continue
        tier = mo["tier"] or MINION_TIER.get(mo["id"], 1)
        bb = idle_bounds(art)
        if not bb:
            continue
        n += 1
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        mw, mh = TIER_LIMIT[tier]
        if w > mw or h > mh:
            fails.append("%s (%s, T%d%s): Idle is %dx%d, limit %dx%d" % (mo["id"], art, tier, "" if mo["tier"] else " minion", w, h, mw, mh))
    return n


@check("feet")
def c_feet(fails, warns):
    n = 0
    seen = set()
    for mo in MONSTERS:
        art = mo["art"]
        if not has(art, "Idle") or art in seen:
            continue
        seen.add(art)
        n += 1
        m = SHEETS[art]
        cw, ch = m["cellW"], m["cellH"]
        bb = idle_bounds(art)
        if not bb:
            continue
        bottom = bb[3] - 1
        if bottom > ch - 2:
            fails.append("%s: Idle reaches row %d, below the feet row %d (cellH-2)" % (art, bottom, ch - 2))
        if not (bb[0] <= cw // 2 < bb[2]):
            fails.append("%s: the feet column x=%d is outside the Idle body (x %d..%d)" % (art, cw // 2, bb[0], bb[2] - 1))
        # grounded walkers should stand on the feet row in their Run cycle too
        for anim in ("Run", "Death"):
            if not has(art, anim):
                continue
            for i, fi in enumerate(m["_anims"][anim]["frames"]):
                b = bbox(cell(art, fi))
                if b and b[3] - 1 > ch - 2:
                    fails.append("%s: %s[%d] reaches row %d, below the feet row %d" % (art, anim, i, b[3] - 1, ch - 2))
    return n


def stone(c):
    px = [p for p in list(c.getdata()) if p[3] > 0]
    if not px:
        return 0, 0
    sat = sum(max(p[:3]) - min(p[:3]) for p in px) / float(len(px))
    return sat, len(px)


@check("statues")
def c_statues(fails, warns):
    n = 0
    # every monster sheet's own Statue frame (the possessable prop pose) is grey stone
    for art in sorted(set(mo["art"] for mo in MONSTERS)):
        if not has(art, "Statue"):
            continue
        sat, k = stone(cell(art, SHEETS[art]["_anims"]["Statue"]["frames"][0]))
        if sat > 40:
            fails.append("%s: Statue frame is not grey stone (mean saturation %.0f)" % (art, sat))
    st = "ModStatues"
    if st not in SHEETS:
        fails.append("art/out_statues/ModStatues missing"); return 0
    m = SHEETS[st]
    finals = [mo for mo in MONSTERS if is_t3_final(mo)]
    for mo in finals:
        n += 1
        key = "Statue_" + mo["art"]
        if key not in m["_anims"]:
            fails.append("%s: no %s frame in ModStatues (re-run tools/sprites/statue_rigs.py)" % (mo["id"], key)); continue
        c = cell(st, m["_anims"][key]["frames"][0])
        bb = bbox(c)
        if not bb:
            fails.append("%s: %s is empty" % (mo["id"], key)); continue
        if bb[3] != m["cellH"]:
            fails.append("%s: %s plinth bottom on row %d, not the cell's last row %d" % (mo["id"], key, bb[3] - 1, m["cellH"] - 1))
        # plinth = the bottom 3 rows
        bot = c.crop((0, m["cellH"] - 3, m["cellW"], m["cellH"]))
        pb = bbox(bot)
        if pb and abs((pb[0] + pb[2]) / 2.0 - m["cellW"] / 2.0) > 1.0:
            fails.append("%s: %s plinth is off centre (x %d..%d in a %d cell)" % (mo["id"], key, pb[0], pb[2] - 1, m["cellW"]))
        sat, k = stone(c)
        if sat > 45:
            warns.append("%s: %s saturation %.0f" % (mo["id"], key, sat))
    extra = set(a[7:] for a in m["_anims"] if a.startswith("Statue_")) - set(mo["art"] for mo in finals)
    for e in sorted(extra):
        warns.append("ModStatues has Statue_%s but no T3 final uses that sheet" % e)
    return n


@check("fx")
def c_fx(fails, warns):
    n = 0
    monster_arts = set(mo["art"] for mo in MONSTERS)
    for (sid, anim), places in sorted(REFS.items()):
        if sid in monster_arts or sid not in SHEETS or anim not in SHEETS[sid]["_anims"]:
            continue
        n += 1
        fr = SHEETS[sid]["_anims"][anim]["frames"]
        empt = [i for i, fi in enumerate(fr) if not bbox(cell(sid, fi))]
        inner = [i for i in empt if i != len(fr) - 1]
        if len(empt) == len(fr):
            fails.append("%s/%s: every frame is empty (used at %s)" % (sid, anim, places[0]))
        elif inner:
            fails.append("%s/%s: empty frame(s) %s" % (sid, anim, inner))
        elif empt and VERBOSE:
            warns.append("%s/%s: last frame empty (fade-out)" % (sid, anim))
    unused = sorted(s for s in SHEETS if s.startswith("Fx") and s not in SHEET_REFS)
    if unused:
        warns.append("FX sheets no code loads: " + ", ".join(unused))
    return n


@check("items")
def c_items(fails, warns):
    ped = SHEETS.get("ShopPedestals")
    if not ped:
        fails.append("art/out_pedestals/ShopPedestals missing")
    bubbles = collections.defaultdict(list)
    for it in ITEMS:
        at = "item %s (%s)" % (it["id"], where(it["file"], it["pos"]))
        artifact = "Artifact" in it["group"]
        b = it["bubble"]
        if not b:
            fails.append("%s: no bubbleArt" % at)
        elif not has(b, "Bubble"):
            fails.append("%s: %s has no Bubble anim" % (at, b) if b in SHEETS else "%s: bubble sheet %s missing" % (at, b))
        else:
            m = SHEETS[b]
            if (m["cellW"], m["cellH"]) != (34, 41):
                fails.append("%s: %s is %dx%d, shop bubbles are 34x41" % (at, b, m["cellW"], m["cellH"]))
            for fi in m["_anims"]["Bubble"]["frames"]:
                if not bbox(cell(b, fi)): fails.append("%s: %s has an empty Bubble frame" % (at, b))
            bubbles[b].append(it["id"])
        h = it["hud"]
        if artifact and not h:
            fails.append("%s: artifact without hudArt (HUD shows nothing)" % at)
        if h:
            if not has(h, "Hud"):
                fails.append("%s: HUD sheet %s missing or has no Hud anim" % (at, h))
            else:
                m = SHEETS[h]
                if (m["cellW"], m["cellH"]) != (11, 7):
                    fails.append("%s: %s is %dx%d, HUD icons are 11x7" % (at, h, m["cellW"], m["cellH"]))
                if not bbox(cell(h, m["_anims"]["Hud"]["frames"][0])): fails.append("%s: %s Hud frame empty" % (at, h))
        if ped and it["id"]:
            if it["id"] not in ped["_anims"]:
                fails.append("%s: no ShopPedestals frame '%s' (owner: tools/sprites/pedestal_rigs.py)" % (at, it["id"]))
            elif not bbox(cell("ShopPedestals", ped["_anims"][it["id"]]["frames"][0])):
                fails.append("%s: ShopPedestals/%s is empty" % (at, it["id"]))
    for w in WEAPONS:
        at = "weapon %s (%s)" % (w["id"], where(w["file"], w["pos"]))
        b = "IconWpn%sBubble" % w["id"]
        if not has(b, "Bubble"):
            fails.append("%s: %s missing (shop bubble / library portrait)" % (at, b))
        elif (SHEETS[b]["cellW"], SHEETS[b]["cellH"]) != (34, 41):
            fails.append("%s: %s is %dx%d, not 34x41" % (at, b, SHEETS[b]["cellW"], SHEETS[b]["cellH"]))
        else:
            SHEET_REFS[b].append(at)
        if ped and "Wpn" + w["id"] not in ped["_anims"]:
            fails.append("%s: no ShopPedestals frame 'Wpn%s' (owner: tools/sprites/pedestal_rigs.py)" % (at, w["id"]))
    for b, ids in bubbles.items():
        if len(ids) > 1:
            warns.append("items %s share the bubble %s" % (", ".join(ids), b))
    if ped:
        known = set(i["id"] for i in ITEMS) | set("Wpn" + w["id"] for w in WEAPONS)
        stale = sorted(set(ped["_anims"]) - known)
        if stale:
            warns.append("ShopPedestals frames for no item: " + ", ".join(stale))
    return len(ITEMS) + len(WEAPONS)


@check("portraits")
def c_portraits(fails, warns):
    for kind, name, sid, f, pos in PORTRAITS:
        at = "%s %s (%s)" % (kind, name, where(f, pos))
        if not sid:
            fails.append("%s: no portraitArt" % at); continue
        SHEET_REFS[sid].append(at)
        if not has(sid, "Idle"):
            fails.append("%s: %s missing or has no Idle" % (at, sid)); continue
        m = SHEETS[sid]
        if (m["cellW"], m["cellH"]) != (29, 24):
            warns.append("%s: %s is %dx%d (vanilla portraits are 29x24)" % (at, sid, m["cellW"], m["cellH"]))
        for i, fi in enumerate(m["_anims"]["Idle"]["frames"]):
            if not bbox(cell(sid, fi)): fails.append("%s: %s Idle[%d] empty" % (at, sid, i))
    gods = [p for p in PORTRAITS if p[0] == "god"]
    if len(gods) < 9:
        warns.append("only %d gods have a GodDef" % len(gods))
    return len(PORTRAITS)


@check("badge")
def c_badge(fails, warns):
    import badge
    m = SHEETS.get("ModBadgeGem")
    if not m:
        fails.append("ModBadgeGem sheet missing (Core marks mod art with it)")
        return 0
    if (m["cellW"], m["cellH"]) != (5, 5):
        fails.append("ModBadgeGem is %dx%d, not 5x5" % (m["cellW"], m["cellH"]))
        return 1
    im = Image.open(m["_png"]).convert("RGBA")
    for y, row in enumerate(badge.GEM):
        for x, ch in enumerate(row):
            want = badge.COL.get(ch, (0, 0, 0, 0))
            got = im.getpixel((x, y))
            if (got[3] == 0 and want[3] == 0) or got == want:
                continue
            fails.append("ModBadgeGem pixel (%d, %d) is %s, badge.py has %s" % (x, y, got, want))
    return 1

def cs_attributes(t, at):
    """The [attributes] written right before the declaration starting at `at` (modifiers skipped)."""
    i = at
    while True:
        j = i
        while j > 0 and t[j - 1].isspace(): j -= 1
        w = re.search(r"\b(static|internal|public|private|protected|sealed|partial|abstract)$", t[:j])
        if w: i = w.start(); continue
        if j == 0 or t[j - 1] != "]": return t[i:at]
        depth, k = 0, j - 1
        while k >= 0:
            depth += {"]": 1, "[": -1}.get(t[k], 0)
            if depth == 0: break
            k -= 1
        i = max(k, 0)


@check("marks")
def c_marks(fails, warns):
    """One violet mod mark per entry:
    - gems are made only by UI/ModGem.cs and placed only through UI/ModMark.cs (no other ModGem.Attach / AttachAt);
    - no two ModMark.Follow / ModMark.Pin call sites decorate the same context (one Harmony target, or one method);
    - no art has the gem painted in (badge.py's 5 x 5 outline around a lit centre): ModGem draws it at run time, where
      it can be turned off, so a baked one would make two."""
    import numpy as np
    import badge
    n = 0
    owners = collections.defaultdict(list)       # context -> ["File.cs:line", ...]
    for f, raw in SRC.items():
        base = os.path.basename(f)
        t = strip_comments(raw)
        line = lambda pos: t.count("\n", 0, pos) + 1
        if base not in ("ModGem.cs", "ModMark.cs"):
            for m in re.finditer(r"\bModGem\.(Attach|AttachAt)\s*\(", t):
                fails.append("%s:%d: ModGem.%s called directly (place gems through ModMark)" % (base, line(m.start()), m.group(1)))
            for m in re.finditer(r'new\s+GameObject\s*\(\s*"ModGem"', t):
                fails.append("%s:%d: makes its own ModGem object" % (base, line(m.start())))
        if base == "ModMark.cs":
            continue
        for m in re.finditer(r"\bModMark\.(Follow|Pin)\s*\(", t):
            n += 1
            head = t[:m.start()]
            cls = list(re.finditer(r"\bclass\s+(\w+)", head))
            if not cls:
                continue
            c = cls[-1]
            hp = list(re.finditer(r'\[HarmonyPatch\(\s*typeof\((\w+)\)\s*,\s*"(\w+)"', cs_attributes(head, c.start())))
            if hp:
                ctx = "%s.%s (patch)" % (hp[-1].group(1), hp[-1].group(2))
            else:
                meth = list(re.finditer(r"\b(?:static\s+|internal\s+|public\s+|private\s+)*[\w<>\[\],]+\s+(\w+)\s*\([^;{}]*\)\s*\{", head[c.end():]))
                ctx = "%s.%s" % (c.group(1), meth[-1].group(1) if meth else "?")
            owners[ctx].append("%s:%d" % (base, line(m.start())))
    for ctx, sites in sorted(owners.items()):
        if len(sites) > 1:
            fails.append("%s is marked from %d places (%s): one owner per context" % (ctx, len(sites), ", ".join(sites)))
        elif VERBOSE:
            warns.append("mark owner: %s <- %s" % (ctx, sites[0]))
    # the gem's signature: the lit centre, the four facets around it (any colour) and the dark outline ring
    K = np.array(badge.COL["K"][:3]); X = np.array(badge.COL["X"][:3])
    ring = [(x - 2, y - 2) for y, row in enumerate(badge.GEM) for x, ch in enumerate(row) if ch == "K"]
    for sid, m in sorted(SHEETS.items()):
        if sid == "ModBadgeGem":
            continue
        a = np.asarray(Image.open(m["_png"]).convert("RGBA")).astype(int)
        h, w = a.shape[:2]
        if h < 5 or w < 5:
            continue
        rgb, op = a[..., :3], a[..., 3] > 0
        hit = (rgb[2:h - 2, 2:w - 2] == X).all(-1) & op[2:h - 2, 2:w - 2]
        for dx, dy in ring:
            hit &= (rgb[2 + dy:h - 2 + dy, 2 + dx:w - 2 + dx] == K).all(-1) & op[2 + dy:h - 2 + dy, 2 + dx:w - 2 + dx]
        ys, xs = np.nonzero(hit)
        if len(ys):
            fails.append("%s: the mod gem is painted into the art at (%d, %d)%s: ModGem marks it at run time"
                         % (sid, xs[0] + 2, ys[0] + 2, " and %d more" % (len(ys) - 1) if len(ys) > 1 else ""))
    return n


# ------------------------------------------------------------------------------------------------------- vault text fit
def cs_unescape(lit):
    return re.sub(r'\\(.)', lambda m: {"n": "\n", "t": "\t", "r": ""}.get(m.group(1), m.group(1)), lit)


def cs_expr(s, i, consts=None):
    """The value of the C# string expression starting at i: literals joined by +, other terms (counts, names) read as
    their constant when `consts` has them, else as "00". None for anything else (a ternary, a call on a literal)."""
    consts = consts or {}
    out, depth, n = [], 0, len(s)
    term = ""
    while i < n:
        c = s[i]
        if c == '"':
            j = i + 1
            while j < n and s[j] != '"':
                j += 2 if s[j] == "\\" else 1
            out.append(cs_unescape(s[i + 1:j])); i = j + 1; continue
        if c in "([{":
            depth += 1
        elif c in ")]}":
            if depth == 0:
                break
            depth -= 1
        elif depth == 0 and c in ",;":
            break
        elif depth == 0 and c == "?":
            return None
        if depth == 0 and c == "+":
            t = term.strip()
            if t: out.append(consts.get(t, "00"))
            term = ""
        elif not c.isspace() or term:
            term += c
        i += 1
    t = term.strip()
    if t: out.append(consts.get(t, "00"))
    return "".join(out) if out else None


def cs_field(body, key, consts=None):
    m = re.search(r'\b%s\s*=\s*(?=["\w(])' % key, body)
    return cs_expr(body, m.end(), consts) if m else None


def cs_consts(src):
    return {m.group(1): cs_unescape(m.group(2)) for m in re.finditer(r'\bconst string (\w+)\s*=\s*"((?:[^"\\]|\\.)*)"\s*;', src)}


def vault_texts():
    """(where, kind, name, text) for every vault page text the content defines, composed the way the vault composes it."""
    out = []
    def add(f, pos, kind, name, text):
        if text is not None: out.append((where(f, pos), kind, name, text))
    for f, s in CODE.items():
        consts = cs_consts(s)
        # monster lines: VaultLines M("Id", "Name", "line") and VaultRegistry monster entries
        for m in re.finditer(r'\bM\(\s*"(\w+)"\s*,\s*"((?:[^"\\]|\\.)*)"\s*,\s*', s):
            add(f, m.start(), "monster", cs_unescape(m.group(2)), cs_expr(s, m.end(), consts))
        for m in re.finditer(r'VaultRegistry\.Add\(\s*"(\w+)"\s*,\s*[^,]+,\s*("(?:[^"\\]|\\.)*")\s*,\s*', s):
            add(f, m.start(), m.group(1).lower(), cs_unescape(m.group(2)[1:-1]), cs_expr(s, m.end(), consts))
        # monster secrets: { "ModId", new[] { "riddle", rarity } } inside MonsterSecrets
        if f.endswith("MonsterSecrets.cs"):
            for m in re.finditer(r'\{\s*"(\w+)"\s*,\s*new\[\]\s*\{\s*', s):
                riddle = cs_expr(s, m.end(), consts)
                k = s.index(",", m.end() + len(riddle or "") + 1) if riddle is not None else -1
                rarity = cs_expr(s, k + 1, consts) if k > 0 else None
                if riddle is not None and rarity is not None:
                    add(f, m.start(), "secret (hidden)", None, riddle + "\n" + rarity)
        # category summaries (found / total filled in as three digits each)
        for m in re.finditer(r'\bsummary\s*=\s*\(\s*found\s*,\s*total\s*\)\s*=>\s*', s):
            add(f, m.start(), "summary", None, cs_expr(s, m.end(), dict(consts, found="000", total="000")))
        # the idol pages
        m = re.search(r'static string IdolText\([^)]*\)\s*\{\s*return\s+', s)
        if m:
            add(f, m.start(), "idol", "Silver Idol", cs_expr(s, m.end(), consts))
    for f, pos, body in objects("GodDef"):
        consts = cs_consts(SRC[f])
        text, flav = cs_field(body, "text", consts), cs_field(body, "flavour", consts)
        if text is not None:
            add(f, pos, "god", field(body, "name"), text.strip() + ("\n" + flav.replace("\n", " ") if flav else ""))
    for cls in ("OriginDef", "GhostFormEntry"):
        for f, pos, body in objects(cls):
            consts = cs_consts(SRC[f])
            summ, flav = cs_field(body, "summary", consts), cs_field(body, "flavour", consts)
            if summ is not None:
                add(f, pos, "origin" if cls == "OriginDef" else "ghost form", field(body, "name"),
                    summ + ("\n" + flav.replace("\n", " ") if flav else ""))
    for f, pos, body in objects("ObjectDef"):
        consts = cs_consts(SRC[f])
        vault, t1, t2 = cs_field(body, "vault", consts), cs_field(body, "tip1", consts), cs_field(body, "tip2", consts)
        if vault is not None:
            add(f, pos, "object", field(body, "name"), vault + ("\n" + t1 + (". " + t2 if t2 else "") if t1 else ""))
    for cls, kind in (("ItemDef", "item"), ("WeaponDef", "weapon")):
        for f, pos, body in objects(cls):
            d = cs_field(body, "description", cs_consts(SRC[f]))
            if d is not None:
                add(f, pos, kind, field(body, "name"), d.strip() + ("." if kind == "weapon" else ""))
    for f, pos, body in objects("SecretDef"):
        if f.startswith(CORE_SRC):
            continue   # Core builds monster secrets from the arguments MonsterSecrets passes (read above)
        consts = cs_consts(SRC[f])
        riddle, rarity, text = (cs_field(body, k, consts) for k in ("riddle", "rarity", "text"))
        name = cs_field(body, "name", consts)
        if riddle is not None and rarity is not None:
            add(f, pos, "secret (hidden)", None, riddle + "\n" + rarity)   # titled "A ... secret" until found
        if text is not None:
            add(f, pos, "secret (found)", name, text)
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "tips", "tips_*.json"))):
        if f.endswith("tips_pages.json"):
            continue
        for key, t in json.load(open(f)).items():
            v = t.get("vault") if isinstance(t, dict) else None
            if isinstance(v, dict):
                v = v.get("text")
            if v:
                out.append(("%s %s" % (os.path.relpath(f, ROOT), key), "monster", t.get("name"), v.rstrip(".").strip()))
    return out


def vault_layout():
    """The vault's text boxes from VaultGrid.cs (MenuLibrary local units, one font pixel each) and the library's
    TextMesh: CrawlTextBodyThin, fontSize 160 at characterSize 1 (so 1 unit per font pixel), lineSpacing 0.5."""
    src = SRC[os.path.join(CORE_SRC, "UI", "VaultGrid.cs")]
    num = lambda k: float(re.search(r'\b%s\s*=\s*(-?[\d.]+)f' % k, src).group(1))
    L = {k: num(k) for k in ("TextLeft", "DescTop", "RightOpen", "RightBesideBack", "BackRowTop", "ScreenBottom",
                             "SummaryLeft", "SummaryTop", "SummaryLowest", "ButtonRowTop")}
    L["lineH"] = 14.09375 * 0.5     # the font's lineHeight (ascent 682 + descent 128 + gap 92 of 1024, at 16 px) x 0.5
    return L


def fit_lines(text, left, top, L):
    """TextFit.Lines with VaultGrid's widths: (lines, max lines, width of line i)."""
    import merge_tips
    lh = L["lineH"]
    width = lambda i: (L["RightOpen"] if top - (i + 1) * lh >= L["BackRowTop"] else L["RightBesideBack"]) - left
    max_lines = max(1, int((top - L["ScreenBottom"]) // lh))
    adv = lambda w: merge_tips.width(w)
    space = adv(" ")
    lines = []
    for para in text.replace("\r", "").split("\n"):
        cur, w = [], 0
        for word in para.split(" "):
            ww = adv(word)
            if cur and w + space + ww > width(len(lines)):
                lines.append(" ".join(cur)); cur, w = [], 0
            if cur:
                w += space
            cur.append(word); w += ww
        lines.append(" ".join(cur))
    while lines and not lines[-1]:
        lines.pop()
    return lines, max_lines, width


TITLE_MIN_SCALE = 0.8    # the smallest a shrunk vault title or banner line may be drawn


@check("vaultfit")
def c_vaultfit(fails, warns):
    import merge_tips
    L = vault_layout()
    n = 0
    challenge_rows = int((L["DescTop"] - L["ButtonRowTop"]) // L["lineH"])
    # the game's own challenge lines (MenuLibrary's strings, English) take one full-width row each
    for t in ("Challenge not yet attempted", "Last attempt: LEVEL 30", "Best attempt: LEVEL 30", "-PASSED-", "CHALLENGE",
              "No challenge available"):
        if merge_tips.width(t) > L["RightOpen"] - L["TextLeft"]:
            fails.append("the game's challenge line %r is wider than a vault row" % t)
    for at, kind, name, text in vault_texts():
        n += 1
        summary = kind == "summary"
        # a summary may sit as low as SummaryLowest (a long category list pushes it down): check the worst case
        left, top = (L["SummaryLeft"], L["SummaryLowest"]) if summary else (L["TextLeft"], L["DescTop"])
        lines, max_lines, width = fit_lines(text, left, top, L)
        label = "%s: %s%s" % (at, kind, " " + name if name else "")
        if len(lines) > max_lines:
            fails.append("%s takes %d lines, the vault shows %d (cut with ...): %r" % (label, len(lines), max_lines, text))
        elif kind == "monster" and len(lines) > challenge_rows - 1:
            # a monster page shares the rows above the button row with at least one challenge line (or "No challenge
            # available" for a minion or blob)
            fails.append("%s takes %d lines; a monster page keeps %d of its %d rows for the line and one for the "
                         "challenge (VaultGrid.ShowChallengePage): %r" % (label, len(lines), challenge_rows - 1, challenge_rows, text))
        for i, l in enumerate(lines[:max_lines]):
            if merge_tips.width(l) > width(i):
                fails.append("%s: line %d is wider than the box (one long word?): %r" % (label, i + 1, l))
        # a title wider than the page is drawn smaller to end by RightOpen (VaultGrid.ShowPage); not too much smaller
        tw = merge_tips.width(name.upper(), merge_tips.SMALL) if name and not summary else 0
        if tw and (L["RightOpen"] - L["TextLeft"]) / tw < TITLE_MIN_SCALE:
            fails.append("%s: the title %s is %d px, drawn at %.2f of its size to fit the page (keep it above %.2f)"
                         % (label, name.upper(), tw, (L["RightOpen"] - L["TextLeft"]) / tw, TITLE_MIN_SCALE))
    if n < 200:
        fails.append("only %d vault texts found: the extraction no longer matches the code" % n)
    return n



# --------------------------------------------------------------------------------------------------------- text fit
import merge_tips   # the HUD fonts' width tables and the pause pages' layout (tools/merge_tips.py)

# CrawlMedium advance widths (font px), chars 32..126 (the unlock banner's title)
MEDIUM = [2, 3, 4, 6, 8, 7, 8, 2, 3, 3, 6, 7, 3, 4, 2, 4, 7, 4, 7, 7, 7, 7, 7, 7, 7, 6, 2, 2, 4, 5, 4, 7, 7, 7, 7, 5, 7, 5,
          5, 7, 7, 3, 6, 6, 5, 8, 7, 7, 7, 7, 7, 7, 7, 7, 7, 8, 6, 7, 6, 3, 4, 3, 4, 6, 2, 7, 7, 5, 7, 7, 6, 7, 7, 3, 4, 7,
          3, 8, 7, 7, 7, 7, 5, 7, 5, 7, 7, 8, 6, 7, 7, 0, 0, 0, 0]
FONT_LINE = 14.09375     # every Crawl pixel font: lineHeight (ascent + descent + gap) at its 16 px size
SMALL_GLYPH = 6.0        # CrawlSmall's capitals are 6 px tall: one line of HUD tip text is that high
GHOST_BUTTON = "middle click"   # the longest name one player's ghost button gets (GhostControls.Personalise)
TIP_MIN_COMPACT = 0.55   # a four-player tip is drawn smaller to fit its column (a 60-character line: about 0.6), never below this
PANEL_LINES = 4          # the god select's text and flavour: the game's own longest take four lines
PANEL_WRAP, PANEL_SCALE = 35.0, 0.8   # their GUIText wrap width (world units) and CrawlTextBodyThin's size there
BANNER_ROOM = 112.0      # UnlockToast.TextRoom


def personalise(s):
    i = s.lower().find("ghost button")
    if i < 0 or s[i + 12:].lstrip().startswith("("):
        return s
    return s[:i + 12] + " (" + GHOST_BUTTON + ")" + s[i + 12:]


def cs_args(s, i):
    """The raw argument texts of the call whose "(" is just before i, up to its ")" (strings and nesting respected)."""
    args, depth, start, n = [], 0, i, len(s)
    while i < n:
        c = s[i]
        if c == '"':
            i += 1
            while i < n and s[i] != '"':
                i += 2 if s[i] == "\\" else 1
        elif c in "([{":
            depth += 1
        elif c in ")]}":
            if depth == 0:
                args.append(s[start:i])
                return args
            depth -= 1
        elif c == "," and depth == 0:
            args.append(s[start:i])
            start = i + 1
        i += 1
    return args


def monster_tips():
    """(where, key, name, attack, special, passive) for every T(...) row of the tip tables (vanilla and generated)."""
    out = []
    for rel in ("MonsterTipsData.cs", "MonsterTipsGenerated.cs"):
        f = os.path.join(CONTENT_SRC, "Tips", rel)
        s = CODE.get(f, "")
        consts = dict(cs_consts(s))
        consts.setdefault("None", "none")
        for m in re.finditer(r'\bT\(', s):
            args = cs_args(s, m.end())
            vals = [cs_expr(a.strip(), 0, consts) for a in args]
            if len(vals) < 4 or any(v is None for v in vals):
                continue
            out.append((where(f, m.start()), vals[0], vals[1], vals[2], vals[3], vals[4] if len(vals) > 4 else None))
    return out


def tip_layout():
    """TipView's numbers: body line height (share of the screen height, normal / compact), the HUD columns' left edges
    and the panel width they assume."""
    src = SRC[os.path.join(CORE_SRC, "UI", "TipView.cs")]
    num = lambda k: float(re.search(r'\b%s\s*=\s*([\d.]+)f' % k, src).group(1))
    rows = [[float(x) for x in re.findall(r'([\d.]+)f', r)] for r in re.findall(r'new\[\]\s*\{([^}]*)\}', src.split("Offsets", 1)[1])[:4]]
    return num("LineHeight"), num("CompactLineHeight"), rows, num("PanelGuess")


def tip_scale(title, lines, col, line_share, aspect=16 / 9.0):
    """TipView.Place at fit 1: the share of its size a tip is drawn at in a column `col` wide (share of the screen
    width). TipView.Measure: the block is the widest line plus 0.35 of a title height each side, its line height the
    body's height over its lines."""
    w = lambda t: merge_tips.width(t.upper(), merge_tips.SMALL)
    n = len(lines)
    line_h = ((n - 1) * FONT_LINE + SMALL_GLYPH) / n
    block = max([w(title)] + [w(l) for l in lines]) + 2 * 0.35 * SMALL_GLYPH
    return min(1.0, col * 0.94 * aspect / (block / line_h * line_share))


def gui_wrap(text, width, scale):
    """The game's TextWrapper (GUIText.SetWrapWidth): a word goes on while the run's summed glyph bounds (advance - 1 px
    each, a space counts 4 px) stay within `width`; tags take no room."""
    def run(t):
        out, tag = 0.0, False
        for c in t:
            tag = tag or c == "<"
            if not tag:
                a = merge_tips.THIN[ord(c) - 32] if 32 <= ord(c) < 127 else 4
                out += 4 if c == " " else max(0, a - 1)
            if c == ">":
                tag = False
        return out * scale
    lines = []
    for para in text.replace("\r", "").split("\n"):
        words = para.split(" ")
        cur = ""
        for j, wd in enumerate(words):
            trial = wd if j == 0 else cur + " " + wd
            if run(trial) > width:
                lines.append(cur)
                cur = wd
            else:
                cur = trial
        lines.append(cur)
    return lines


def panel_texts():
    """(where, what, text, wrap width) for every text the mod puts in the god select's paragraphs, composed as shown."""
    out = []
    gods = []
    for f, pos, body in objects("GodDef"):
        c = cs_consts(SRC[f])
        name, text, flav = field(body, "name"), cs_field(body, "text", c), cs_field(body, "flavour", c)
        gods.append(name)
        out += [(where(f, pos), "god %s text" % name, text), (where(f, pos), "god %s flavour" % name, flav)]
        out.append((where(f, pos), "silver idol perk of %s" % name, "Perk of %s: %s" % (name, " ".join((text or "").split()))))
        out.append((where(f, pos), "gold idol with %s" % name, "Any 4 starters, only %s's perk" % name))
    for cls in ("OriginDef", "GhostFormEntry"):
        for f, pos, body in objects(cls):
            c = cs_consts(SRC[f])
            n = field(body, "name")
            out.append((where(f, pos), "%s %s summary" % (cls, n), cs_field(body, "summary", c)))
            out.append((where(f, pos), "%s %s flavour" % (cls, n), cs_field(body, "flavour", c)))
    for f, s in CODE.items():
        for m in re.finditer(r'\bBlob\(\s*"(\w+)"\s*,\s*"([^"]*)"\s*,\s*"([^"]*)"', s):
            out.append((where(f, m.start()), "blob %s" % m.group(2), m.group(3)))
        for m in re.finditer(r'GhostBlobDef\s*\{[^}]*?\bname\s*=\s*"([^"]*)"[^}]*?\bsummary\s*=\s*"([^"]*)"', s):
            out.append((where(f, m.start()), "blob %s" % m.group(1), m.group(2)))
    for at, title, text, target, slot in unlock_defs():
        out.append((at, "locked %s" % slot, "%s  %d / %d" % (text, target, target)))
    out = [(a, k, t, PANEL_WRAP) for a, k, t in out]
    # the silver / gold editors' paragraph rows (InfoRow, wrap 46): a weapon's or spell's description as a sentence
    for cls in ("ItemDef", "WeaponDef"):
        for f, pos, body in objects(cls):
            d, i = cs_field(body, "description", cs_consts(SRC[f])), field(body, "id") or ""
            if d and (cls == "WeaponDef" or i.startswith("Spell")):
                d = " ".join(d.split())
                out.append((where(f, pos), "hero editor pick %s" % field(body, "name"), d if d.endswith(".") else d + ".", 46.0))
    return [(a, k, personalise(t), w) for a, k, t, w in out if t]


def unlock_defs():
    """(where, title, text, target, slot) of the unlock challenges (SlotChallenges / BlobChallenges Add calls)."""
    out = []
    pat = re.compile(r'\bAdd\(\s*(?:"\w+"\s*,\s*SlotTier\.\w+|\w+)\s*,\s*"([A-Z ]+)"\s*,\s*"([^"]+)"\s*,\s*[\w.]+\s*,\s*(\d+)\s*,\s*"([^"]+)"\s*\)')
    for f, s in CODE.items():
        if f.endswith(("SlotChallenges.cs", "BlobChallenges.cs")):
            for m in pat.finditer(s):
                out.append((where(f, m.start()), m.group(1), m.group(2), int(m.group(3)), m.group(4)))
    return out


@check("textfit")
def c_textfit(fails, warns):
    n = 0
    # HUD monster tips (TipView): two players' columns at full size, four players' (compact, no passive) readable
    lh, lh_compact, rows, panel = tip_layout()
    col2 = (rows[1][0] + panel / 2 + rows[1][1] + panel / 2) / 2 - 0.01          # P1's column: to half way to P2
    centres4 = [x + panel / 2 for x in rows[3]]
    col4 = min((centres4[i + 1] - centres4[i - 1]) / 2 for i in (1, 2))           # the inner columns are the narrowest
    tips = monster_tips()
    if len(tips) < 300:
        fails.append("only %d monster tips found: the extraction no longer matches MonsterTipsData" % len(tips))
    for at, key, name, attack, special, passive in tips:
        n += 1
        body = ["Attack: " + attack, "Special: " + special] + (["Passive: " + passive.split("\n")[0]] + passive.split("\n")[1:] if passive else [])
        body = [personalise(l) for l in body]
        title = "P2 - " + name
        for l in body:
            if len(l) > merge_tips.MAX_LINE + (len(GHOST_BUTTON) + 3 if GHOST_BUTTON in l else 0):
                fails.append("%s: tip %s line is %d chars (max %d): %r" % (at, key, len(l), merge_tips.MAX_LINE, l))
        k = tip_scale(title, body, col2, lh)
        if k < 0.999:
            fails.append("%s: tip %s is too wide for a two-player column (drawn at %.2f of its size): %r"
                         % (at, key, k, max(body, key=len)))
        k = tip_scale(title, body[:2], col4, lh_compact)
        if k < TIP_MIN_COMPACT:
            fails.append("%s: tip %s is drawn at %.2f of its size in a four-player column (min %.2f): shorten %r"
                         % (at, key, k, TIP_MIN_COMPACT, max(body[:2], key=len)))
    # the god select's paragraphs (PanelText shrinks a longer one, but English never needs it)
    for at, what, text, wrap in panel_texts():
        n += 1
        lines = gui_wrap(text, wrap, PANEL_SCALE)
        if len(lines) > PANEL_LINES:
            fails.append("%s: %s takes %d lines on the god select (the game's own take %d): %r"
                         % (at, what, len(lines), PANEL_LINES, lines))
    # the unlock banner (UnlockToast): both lines inside the banner at the size the borrowed font style may have
    banner = [(at, slot + " UNLOCKED", MEDIUM) for at, _, _, _, slot in unlock_defs()]
    banner += [(at, text, merge_tips.THIN) for at, _, text, _, _ in unlock_defs()]
    banner.append((os.path.join(CORE_SRC, "UI", "Secrets.cs"), "VAULT SECRET UNLOCKED", MEDIUM))
    for f, pos, body in objects("SecretDef"):
        nm = cs_field(body, "name", cs_consts(SRC[f]))
        if nm:
            banner.append((where(f, pos), nm, merge_tips.THIN))
    for at, text, table in banner:
        n += 1
        w = merge_tips.width(text, table)
        if w and BANNER_ROOM / w < TITLE_MIN_SCALE:
            fails.append("%s: unlock banner line %r is %d px; the banner holds %d (it would be drawn at %.2f)"
                         % (at, text, w, BANNER_ROOM, BANNER_ROOM / w))
    # pause pages: a subtitle sits right of the tab and must end before the page counter (PauseTips.BuildPage)
    pages = json.load(open(os.path.join(ROOT, "data", "tips", "tips_pages.json")))
    left, tab_w, right = -96.0, 43.0, 94.0
    subs = [(t["header"].upper(), t.get("subtitle") or "", len(merge_tips.paginate([merge_tips.markup(p) for p in t["text"] if p.strip()])))
            for t in pages.get("topics", [])]
    gods = sorted({t.get("god") for t in pages.get("topics", []) if t.get("god")})
    subs += [(hdr, "the monster you are now (%s)" % g, 2) for g in gods for hdr in ("YOU", "P4")]
    for hdr, sub, npages in subs:
        n += 1
        start = left + max(tab_w, merge_tips.width(hdr, merge_tips.SMALL) + 8) + 4
        limit = right - (merge_tips.width("%d/%d" % (npages, npages)) + 3 if npages > 1 else 0)
        if start + merge_tips.width(sub) > limit:
            fails.append("pause page %s: the subtitle %r runs into the page counter" % (hdr, sub))
    return n


@check("previews")
def c_previews(fails, warns):
    n = missing = 0
    arts = set(mo["art"] for mo in MONSTERS)
    for sid, m in SHEETS.items():
        if not (sid in arts or sid.startswith(("Fx", "Deity", "Ghost", "Hero", "Mod", "Shop"))):
            continue
        prev = m["_png"][:-4] + "_preview.png"
        n += 1
        if not os.path.exists(prev):
            missing += 1
            continue
        if os.path.getmtime(prev) + 1 < os.path.getmtime(m["_png"]):
            fails.append("%s/%s_preview.png is older than the sheet (re-run its rig script)" % (m["_dir"], sid))
    if missing:
        warns.append("%d sheets have no _preview.png (previews are made by the rig scripts and not committed)" % missing)
    return n


@check("hands")
def c_hands(fails, warns):
    """Every hero frame a mod weapon's clips use (idle, run, attacks and their aim angles) has a redrawn frame in
    art/out_weapons/WpnHand_<id>.json: the weapon's clips are remapped by that table, and a missing entry would show the
    vanilla weapon. Also checks the table's cells against the sheet, and that the C# remaps every clip it builds."""
    import importlib
    sys.path.insert(0, os.path.join(ROOT, "tools", "sprites"))
    WL = importlib.import_module("weapon_looks")
    clips = os.path.join(SCR, "db", "exSpriteAnimClip.jsonl")
    if not os.path.exists(clips):
        warns.append("vanilla clip dump not found (%s): skipped" % clips); return 0
    clipf = {}
    for l in open(clips):
        c = json.loads(l)
        clipf.setdefault(c["m_Name"], [f["index"] for f in c["frameInfos"] if f["atlas"]["m_PathID"] == 39931])
    n = 0
    for wid, name, base, combo, srcs in WL.mod_weapons():
        n += 1
        sid = "WpnHand_" + wid
        if sid not in SHEETS:
            fails.append("%s: no in-hand sheet %s (run tools/sprites/weapon_hands.py)" % (wid, sid)); continue
        m = SHEETS[sid]
        table = m.get("hero") or []
        have = {r[0] for r in table}
        idle, run, atk = WL.clip_names(base, combo, srcs)
        need = set()
        for cn in [idle, run] + atk:
            need |= set(clipf.get(cn, []))
        miss = sorted(need - have)
        if miss:
            fails.append("%s: %d hero frame(s) still point at the vanilla AtlasHero weapon (e.g. %s)" % (wid, len(miss), miss[:5]))
        cells = len(m["anims"][0]["frames"]) if m.get("anims") else 0
        for r in table:
            if not (0 <= r[1] < cells) or r[6] > m["cellW"] or r[7] > m["cellH"]:
                fails.append("%s: frame table row %s outside the sheet grid" % (sid, r)); break
    # Core builds the clips (ItemRegistry.HeroClip, through WeaponDef.heroFrames); the content mod must point every
    # weapon's heroFrames at its in-hand table
    core = open(os.path.join(ROOT, "src", "CrawlFurther.Core", "Items", "ItemRegistry.cs")).read()
    calls = []
    for m in re.finditer(r"(?<![\w.])HeroClip\(", core):
        if re.search(r"exSpriteAnimClip\s*$", core[max(0, m.start() - 40):m.start()]): continue     # the definition
        i, depth = m.end(), 1
        while i < len(core) and depth:
            depth += {"(": 1, ")": -1}.get(core[i], 0); i += 1
        calls.append(core[m.end():i - 1])
    bad = [c for c in calls if not c.rstrip().endswith("heroFrames")]
    if not calls or bad:
        fails.append("ItemRegistry.cs: HeroClip call(s) without the weapon's heroFrames: %s" % (bad[:3] or "none found"))
    src = open(os.path.join(CONTENT_SRC, "Weapons", "WeaponPack.cs")).read()
    if not re.search(r"def\.heroFrames\s*=.*WeaponHands\.Remap\(", src):
        fails.append("WeaponPack.cs: weapons are built without their in-hand frames (def.heroFrames = ... WeaponHands.Remap)")
    return n


def package_files():
    """The art files tools/package.sh copies (same rules: every art/core and art/out*/<id>.json with a png, minus boards)."""
    out = {}
    for d in ART_DIRS:
        for f in sorted(glob.glob(os.path.join(d, "*.json"))):
            b = os.path.basename(f)[:-5]
            if b.endswith("_preview") or b in ("board", "contact_idle", "fx_all", "designs_board"):
                continue
            if os.path.exists(os.path.join(d, b + ".png")):
                out[b] = d
    return out


@check("bosses")
def c_bosses(fails, warns):
    """The two mod bosses wear redrawn art (tools/sprites/boss_art.py -> art/out_bosses/<sheet>.png/.json): both
    sheets exist, every row sits inside its png, is non-empty and keeps the vanilla original cell (trim within a
    small margin of it), the sheet BossPack.cs loads is shipped, and every vanilla frame the boss_art rules repaint
    (body, heads/eye/mouth/tentacles/orb, the boss FX) has a new-art counterpart, so none falls back to vanilla."""
    sys.path.insert(0, os.path.join(ROOT, "tools", "sprites"))
    n = 0
    src = open(os.path.join(CONTENT_SRC, "Bosses", "BossPack.cs")).read()
    pkg = package_files()
    try:
        import importlib
        BA = importlib.import_module("boss_art")
        BA.load_vanilla()
    except Exception as e:            # no vanilla dump: check the sheets on their own
        BA = None
        warns.append("boss_art vanilla data unavailable (%r): skipped the coverage check" % e)
    for sheet, atlas in (("BossLeviathanArt", "AtlasBossHydra"), ("BossPandemoniumArt", "AtlasBoss"),
                         ("BossLeviathanFx", "AtlasEffectsShared"), ("BossPandemoniumFx", "AtlasEffectsShared")):
        d = os.path.join(ROOT, "art", "out_bosses")
        pj, pp = os.path.join(d, sheet + ".json"), os.path.join(d, sheet + ".png")
        if '"%s"' % sheet not in src:
            fails.append("BossPack.cs no longer loads %s" % sheet)
        if not (os.path.exists(pj) and os.path.exists(pp)):
            fails.append("art/out_bosses/%s.png/.json missing (run tools/sprites/boss_art.py)" % sheet); continue
        if pkg.get(sheet) != d:
            fails.append("%s is not shipped by package.sh" % sheet)
        m = json.load(open(pj))
        im = Image.open(pp).convert("RGBA")
        if m.get("atlas") != atlas:
            fails.append("%s: manifest atlas %r, expected %s" % (sheet, m.get("atlas"), atlas))
        if (im.width, im.height) != (m.get("width"), m.get("height")):
            fails.append("%s: png %dx%d but manifest says %sx%s" % (sheet, im.width, im.height, m.get("width"), m.get("height")))
        have = set()
        alpha = im.getchannel("A")
        for r in m.get("elements", []):
            n += 1
            idx, x, y, w, h, tx, ty = r
            have.add(idx)
            if x < 0 or y < 0 or x + w > im.width or y + h > im.height or w <= 0 or h <= 0:
                fails.append("%s: element %d rect %s outside the png" % (sheet, idx, r[1:5])); continue
            if not alpha.crop((x, y, x + w, y + h)).getbbox():
                fails.append("%s: element %d is empty" % (sheet, idx))
            if BA is not None and atlas == "AtlasBossHydra":
                # the Hydra body's AnimNodes markers (head attachment points read from the texture at run time)
                import numpy as np
                v = BA.vframe(39921, idx)
                if BA.is_marker(v).any():
                    M = BA.MARGIN
                    nv = np.zeros_like(v)
                    nv[ty + M:ty + M + h, tx + M:tx + M + w] = np.array(im.crop((x, y, x + w, y + h)))
                    if not np.array_equal(BA.is_marker(v) & (v[..., 3] > 0), BA.is_marker(nv) & (nv[..., 3] > 0)):
                        fails.append("%s: element %d moved/lost an AnimNodes marker pixel" % (sheet, idx))
            if BA is not None:
                e = BA.elem(BA.ATLAS_PIDS[atlas][0], idx)
                M = BA.MARGIN
                if tx < -M or ty < -M or tx + w > e["originalWidth"] + M or ty + h > e["originalHeight"] + M:
                    fails.append("%s: element %d trim %s leaves the vanilla cell (+%d px)" % (sheet, idx, (tx, ty, w, h), M))
        if BA is not None:
            boss = [b for b in BA.BOSSES if b["sheet"] == sheet][0]
            try:
                best, parts = BA.plan(boss)
            except Exception as e:
                warns.append("%s: plan failed (%r)" % (sheet, e)); continue
            miss = sorted(set(best) - have)
            if miss:
                fails.append("%s: %d repainted vanilla frame(s) have no new art (e.g. %s): re-run boss_art.py"
                             % (sheet, len(miss), miss[:6]))
            if m.get("elementCount") != len(BA._ATL[boss["apid"]]["elements"]):
                fails.append("%s: elementCount %s does not match the vanilla atlas" % (sheet, m.get("elementCount")))
    return n


@check("herogear")
def c_herogear(fails, warns):
    """Origin gear on the in-game hero (tools/sprites/hero_gear.py -> art/out_herogear, src/CrawlFurther.Core/Heroes/HeroGearData.cs):
    every normal origin but the vanilla hero names a gearArt sheet (16 non-empty 15x15 pose cells);
    the anchor table has one entry per AtlasHero element; every hero frame a clip shows with the hero's head
    (2+ hair pixels) has an anchor (except hero_gear.NO_HEAD, checked by eye); every WpnHand frame resolves to
    an AtlasHero source entry."""
    sys.path.insert(0, os.path.join(ROOT, "tools", "sprites"))
    import importlib
    HG = importlib.import_module("hero_gear")
    data = os.path.join(CORE_SRC, "Heroes", "HeroGearData.cs")
    if not os.path.exists(data):
        fails.append("src/CrawlFurther.Core/Heroes/HeroGearData.cs missing (run tools/sprites/hero_gear.py)"); return 0
    txt = open(data).read()
    tm = re.search(r"AtlasHero\s*=\s*\{([^}]*)\}", txt)
    table = [int(v) for v in re.findall(r"-?\d+", tm.group(1))] if tm else []
    origins = []
    for f, pos, body in objects("OriginDef"):
        if field(body, "id") is None or re.search(r"\b(isVanilla|tier)\s*=", body): continue
        origins.append((field(body, "id"), field(body, "gearArt")))
    if not origins: fails.append("no origins found (new OriginDef { ... })")
    n = 0
    for o, sid in origins:
        n += 1
        if not sid: fails.append("%s: no gearArt (no gear in game)" % o); continue
        if sid not in SHEETS:
            fails.append("%s: gear sheet %s missing (art/out_herogear)" % (o, sid)); continue
        m = SHEETS[sid]
        if (m["cellW"], m["cellH"]) != (HG.CELL, HG.CELL):
            fails.append("%s: cell %dx%d, expected %dx%d" % (sid, m["cellW"], m["cellH"], HG.CELL, HG.CELL)); continue
        img = Image.open(m["_png"]).convert("RGBA")
        cols = img.width // HG.CELL
        for p in range(HG.NPOSE):
            x, y = (p % cols) * HG.CELL, (p // cols) * HG.CELL
            if img.crop((x, y, x + HG.CELL, y + HG.CELL)).getbbox() is None:
                fails.append("%s: pose cell %d is empty" % (sid, p)); break
    try:
        ha = HG.HeroAtlas()
    except Exception as e:
        warns.append("vanilla hero atlas dump unavailable, frame coverage not checked: %r" % e); return n
    if len(table) != len(ha.elements):
        fails.append("HeroGearData.AtlasHero has %d entries, AtlasHero %d elements (re-run hero_gear.py)" % (len(table), len(ha.elements)))
        return n
    used = sorted(set(i for v in ha.clips.values() for i in v))
    miss = []
    for i in used:
        n += 1
        if table[i] != 0 or ha.elements[i]["name"] in HG.NO_HEAD: continue
        if sum(1 for v in HG.classes(ha.frame(i)).values() if v == 'H') >= 2:
            miss.append("%d %s" % (i, ha.elements[i]["name"]))
    if miss:
        fails.append("%d hero frame(s) show a head but have no gear anchor (re-run hero_gear.py or add to NO_HEAD after "
                     "checking by eye): %s" % (len(miss), miss[:6]))
    for sid, rows in HG.hand_sheets():
        bad = [r[0] for r in rows if not 0 <= r[0] < len(table)]
        if bad: fails.append("%s: source element(s) %s outside AtlasHero" % (sid, bad[:5]))
    return n


@check("package")
def c_package(fails, warns):
    pkg = package_files()
    sh = open(os.path.join(ROOT, "tools", "package.sh")).read()
    if 'art/out*' not in sh or 'art/core' not in sh:
        fails.append("package.sh no longer copies art/core and every art/out* dir")
    for d in ART_DIRS:
        if not any(v == d for v in pkg.values()) and glob.glob(os.path.join(d, "*.json")):
            fails.append("package ships nothing from %s" % os.path.relpath(d, ROOT))
    loaded = set(SHEET_REFS) | set(mo["art"] for mo in MONSTERS) | {"ModStatues", "ShopPedestals"}
    loaded |= set(i["bubble"] for i in ITEMS if i["bubble"]) | set(i["hud"] for i in ITEMS if i["hud"])
    for sid in sorted(loaded):
        if sid not in pkg:
            fails.append("%s is loaded by the code but the package has no %s.png/.json" % (sid, sid))
    return len(loaded)


@check("branding")
def c_branding(fails, warns):
    """Crawl: Further branding and vault stamps (tools/sprites/branding.py -> art/out_branding, VaultIcons -> art/core): every
    anim Branding.cs / UiRefresh.cs / VaultGrid.cs plays exists with non-empty frames, at the sizes the code places."""
    need = {"BrandFurther": (["Idle", "Glitch", "In", "Out"], (76, 28)), "BrandSpark": (["Rise"], (5, 5)),
            "BrandPip": (["Burn"], (7, 9)), "BrandMote": (["Dust1", "Dust2", "Dust3", "Ember1", "Ember2", "Ember3"], (5, 5)),
            "VaultIcons": (["Undiscovered", "NoArt", "Locked", "Further"], (12, 12)), "VaultStampFurther": (["Stamp"], (59, 48)),
            "VaultStampSecrets": (["Stamp"], (59, 48))}
    for sid, (anims, size) in need.items():
        m = SHEETS.get(sid)
        if m is None:
            fails.append("%s missing (run tools/sprites/branding.py / vault_icons.py)" % sid); continue
        if (m["cellW"], m["cellH"]) != size:
            fails.append("%s cells are %dx%d, the code places %dx%d" % (sid, m["cellW"], m["cellH"], size[0], size[1]))
        for a in anims:
            if not has(sid, a):
                fails.append("%s has no %s anim" % (sid, a)); continue
            for f in [x for x in m["anims"] if x["name"] == a][0]["frames"]:
                if bbox(cell(sid, f)) is None and not (sid == "BrandFurther" and a == "Out"):
                    fails.append("%s %s frame %d is empty" % (sid, a, f))
    return len(need)


@check("music")
def c_music(fails, warns):
    """music/*.ogg|wav (src/CrawlFurther.Core/UI/ModMusic.cs): each file decodes, is 44.1 or 48 kHz, mono or stereo, and the real tracks
    (not placeholder*) run at least 60 s and loop cleanly enough not to clip at the seam (warned, not failed)."""
    import subprocess
    files = sorted(glob.glob(os.path.join(ROOT, "music", "*.ogg")) + glob.glob(os.path.join(ROOT, "music", "*.wav")))
    if not shutil.which("ffprobe"):
        warns.append("ffprobe missing: music files not decoded"); return len(files)
    for f in files:
        name = os.path.basename(f)
        try:
            out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_name,sample_rate,channels",
                                  "-of", "json", f], capture_output=True, text=True, timeout=30)
            info = json.loads(out.stdout or "{}")
            st = (info.get("streams") or [{}])[0]
            dur = float((info.get("format") or {}).get("duration") or 0)
        except Exception as e:
            fails.append("%s: ffprobe failed (%s)" % (name, e)); continue
        if st.get("codec_name") not in ("vorbis", "pcm_s16le", "pcm_s24le", "pcm_f32le", "pcm_u8"):
            fails.append("%s: codec %s (Unity 5.4 loads Ogg Vorbis or PCM wav)" % (name, st.get("codec_name")))
        if int(st.get("sample_rate") or 0) not in (44100, 48000):
            fails.append("%s: %s Hz (use 44100 or 48000)" % (name, st.get("sample_rate")))
        if int(st.get("channels") or 0) not in (1, 2):
            fails.append("%s: %s channels" % (name, st.get("channels")))
        if not name.startswith("placeholder") and dur < 60:
            warns.append("%s: only %.0f s long for a looping game track" % (name, dur))
    return len(files)


@check("text")
def c_text(fails, warns):
    """Player-facing name/description/subtitle strings in src: none of % { | } ~ (the in-game fonts drop or mangle them)
    and no "(MOD)" tag. Format strings and log lines are not matched (only name =, description =, subtitle = fields)."""
    n = 0
    pat = re.compile(r'\b(name|description|subtitle|desc|tip|text)\s*=\s*"((?:[^"\\\n]|\\.)*)"')
    for f in sorted(glob.glob(os.path.join(ROOT, "src", "**", "*.cs"), recursive=True)):
        if f.endswith("MonsterTipsGenerated.cs"): continue        # merge_tips.py checks those
        src = open(f, encoding="utf-8").read()
        for m in pat.finditer(src):
            n += 1
            v = m.group(2)
            bad = [c for c in "%{|}~" if c in v]
            if bad or "(MOD)" in v:
                fails.append("%s:%d: %s = \"%s\" has %s" % (os.path.basename(f), src.count("\n", 0, m.start()) + 1,
                                                           m.group(1), v[:60], "".join(bad) or "(MOD)"))
    # secrets: riddle, rarity and text limits (SecretDef; the self-test checks the same at run time)
    for f, pos, body in objects("SecretDef"):
        if f.startswith(CORE_SRC):
            continue
        consts = cs_consts(SRC[f])
        for key, most in (("riddle", 75), ("rarity", 30), ("text", 120)):
            v = cs_field(body, key, consts)
            n += 1
            if v is not None and len(v) > most:
                fails.append("%s: secret %s is %d characters (keep it to %d): %s" % (where(f, pos), key, len(v), most, v[:40]))
    return n


@check("patch-order")
def c_patch_order(fails, warns):
    """Every name in a plugin's PatchOrder list must be a patch class that exists: a renamed patch silently drops to
    the end of the order (and its ordering guarantee with it)."""
    n = 0
    for src_dir in (CORE_SRC, CONTENT_SRC):
        texts = [open(f, encoding="utf-8").read() for f in glob.glob(os.path.join(src_dir, "**", "*.cs"), recursive=True)]
        classes = set(re.findall(r"\bclass\s+(\w+)", "\n".join(texts)))
        for t in texts:
            m = re.search(r"PatchOrder\s*=\s*\{(.*?)\};", t, re.S)
            if not m:
                continue
            for name in re.findall(r'"(\w+)"', m.group(1)):
                n += 1
                if name not in classes:
                    fails.append("PatchOrder lists %s, but no class has that name" % name)
    return n


@check("menulists")
def c_menulists(fails, warns):
    """A pick list made by copying a vanilla menu list (Object.Instantiate of a MenuTextMenu's GameObject) must switch
    the copy's MenuTextMenu on. The copy takes the original's component state, and the origin picker switches the god
    list off before it copies it: a copy left off draws but never runs MenuTextMenu.Update, so it ignores every press
    (the 1.2.0 blob page)."""
    n = 0
    for f, raw in SRC.items():
        t = strip_comments(raw)
        for m in re.finditer(r"Instantiate\(\s*(\w+)\.gameObject\s*\)", t):
            body_end = t.find("return ", m.end())
            body = t[m.end():body_end if body_end > 0 else len(t)]
            if "GetComponent<MenuTextMenu>" not in body:
                continue
            n += 1
            if not re.search(r"\.enabled\s*=\s*true", body):
                fails.append("%s:%d: a copied MenuTextMenu is never switched on (set .enabled = true where it is made)"
                             % (os.path.basename(f), t.count("\n", 0, m.start()) + 1))
    if n == 0:
        warns.append("no copied menu lists found")
    return n


@check("reflection")
def c_reflection(fails, warns):
    """Reflection that only fails at run time in the game:
    - AccessTools.Method(typeof(T), "Name") / [HarmonyPatch(typeof(T), "Name")] with no parameter types, where the game's T
      declares Name more than once: AmbiguousMatchException (0.10.0 shipped one inside a Health.Damage prefix's static
      field: every hit threw and nobody could hurt anybody).
    - R.Set(obj, "m_field", literal) where the literal's type can't go into the game's field (a float into an enum:
      every Use/Touch room object failed to build)."""
    G = os.environ.get("CRAWL_DECOMP", os.path.join(SCR, "src"))
    if not os.path.isdir(G):
        warns.append("decompiled game source not found (set CRAWL_DECOMP): reflection check skipped")
        return 0
    files = {}
    for f in glob.glob(os.path.join(G, "**", "*.cs"), recursive=True):
        files.setdefault(os.path.basename(f)[:-3], []).append(f)
    texts = {}
    def text(f):
        if f not in texts: texts[f] = open(f, encoding="utf-8", errors="ignore").read()
        return texts[f]
    def decls(t, n):
        c = 0
        for f in files.get(t, []):
            src = text(f)
            # only the top-level class body: nested classes in the same file are separate types
            m = re.search(r"^(?:public |internal )?(?:abstract |sealed |static )*class\s+" + re.escape(t) + r"\b", src, re.M)
            body = src[m.start():] if m else src
            c += len(re.findall(r"^\t(?:public|private|protected|internal)[^=;(\n]*\b" + re.escape(n) + r"\s*\(", body, re.M))
        return c
    fieldtypes = {}
    for lst in files.values():
        for f in lst:
            for m in re.finditer(r"^\s*(?:public|private|protected|internal)?\s*(?:static\s+)?(?:readonly\s+)?([\w\.<>\[\],]+)\s+(m_\w+)\s*(?:=|;)",
                                 text(f), re.M):
                fieldtypes.setdefault(m.group(2), set()).add(m.group(1))
    lit_ok = {"float": {"float", "Single", "double"}, "bool": {"bool"}, "string": {"string"}}
    n = 0
    p_method = re.compile(r'AccessTools\.(?:Method|DeclaredMethod)\(\s*typeof\((\w+)\)\s*,\s*"(\w+)"\s*\)')
    p_patch = re.compile(r'\[(?:HarmonyLib\.)?HarmonyPatch\(typeof\((\w+)\)\s*,\s*"(\w+)"\s*\)\]')
    p_set = re.compile(r'R\.Set(?:<[^>]*>)?\(\s*[^,]+,\s*"(m_\w+)"\s*,\s*([^)]+?)\)\s*;')
    for f in sorted(glob.glob(os.path.join(ROOT, "src", "**", "*.cs"), recursive=True)):
        src = open(f, encoding="utf-8").read()
        where = lambda pos: "%s:%d" % (os.path.basename(f), src.count("\n", 0, pos) + 1)
        for m in list(p_method.finditer(src)) + list(p_patch.finditer(src)):
            t, name = m.group(1), m.group(2)
            if t not in files: continue                       # a mod type
            n += 1
            c = decls(t, name)
            if c > 1: fails.append("%s: %s.%s has %d overloads: pass the parameter types" % (where(m.start()), t, name, c))
        for m in p_set.finditer(src):
            fld, val = m.group(1), m.group(2).strip()
            kind = ("float" if re.fullmatch(r"-?\d+(\.\d+)?f", val) else "bool" if val in ("true", "false")
                    else "string" if val.startswith('"') else None)
            ts = fieldtypes.get(fld)
            if not kind or not ts: continue
            n += 1
            if not (ts & lit_ok[kind]):
                fails.append("%s: R.Set %s = %s, but the game declares %s as %s" % (where(m.start()), fld, val, fld, "/".join(sorted(ts))))
    return n


@check("silver")
def c_silver(fails, warns):
    """art/out_silvervar (src/CrawlFurther/Secrets/SilverVariants.cs): every tier-3 final has a silver variant baked from its CURRENT
    sheet. tools/sprites/silver_variants.py --check exits 1 for a missing or stale one (re-run the bake to fix)."""
    import subprocess
    tool = os.path.join(ROOT, "tools", "sprites", "silver_variants.py")
    out = subprocess.run([sys.executable, "-W", "ignore", tool, "--check"], capture_output=True, text=True, timeout=600)
    lines = [l for l in (out.stdout + out.stderr).splitlines() if l.strip()]
    if out.returncode != 0:
        fails.extend(lines[-20:] or ["silver_variants.py --check failed"])
        fails.append("fix: python3 tools/sprites/silver_variants.py")
    return len(glob.glob(os.path.join(ROOT, "art", "out_silvervar", "SilverVar_*.json")))


def main():
    for c in CHECKS:
        c()
    total_fail = 0
    print("sheets: %d   monsters: %d   items: %d   weapons: %d   portraits: %d   source files: %d"
          % (len(SHEETS), len(MONSTERS), len(ITEMS), len(WEAPONS), len(PORTRAITS), len(SRC)))
    for name, (fails, warns, n) in RESULTS.items():
        status = "OK  " if not fails else "FAIL"
        print("%s %-11s %4d checked%s%s" % (status, name, n, "" if not fails else "  %d problem(s)" % len(fails),
                                           "" if not warns else "  (%d warning%s)" % (len(warns), "s" * (len(warns) > 1))))
        for e in fails:
            print("       - " + e)
        if VERBOSE:
            for w in warns:
                print("       ~ " + w)
        total_fail += len(fails)
    print("OK" if not total_fail else "FAIL: %d problem(s)" % total_fail)
    return 1 if total_fail else 0


if __name__ == "__main__":
    sys.exit(main())
