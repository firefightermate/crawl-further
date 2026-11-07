"""Merge the monster tip text (data/tips/tips_*.json) and the pause-menu tip pages into C#.

Each data/tips/tips_<group>.json is {"ModPrefabName": {"name": ..., "attack": ..., "special": ..., "passive": ...,
"vault": ...}} ("passive" is optional and may be one string or a list of up to two lines; boss parts are keyed
"BossPrefab/PartName"). Lines are written for the PLAYER who is the monster ("Pull the hero to you"), never from the
hero's side.

"vault" (optional) is the monster's library line in the vanilla prop tone ("Spits motes of ball lightning and
discharges a static ring"), shown under the tip's name. The vault uses it for any monster without a hand-written line
(src/CrawlFurther/Library/VaultLines.cs), listed right after the hand-written block of the same god (file). It may also be {"name": ..., "text": ...},
and then the name must match the tip's name.

data/tips/tips_pages.json is different: the topics of the mod's pages in Pause > Tips (gods, status effects, ghost
forms). Each topic has header (tab text, max 8 capitals), subtitle and paragraphs; *word* is drawn in the highlight
colour and a paragraph starting with "- " is a bullet. The script wraps them exactly like the game will (the
CrawlTextBodyThin glyph widths below, PauseTips.BodyWidth px per line, PauseTips.LinesPerPage lines per page) and
prints how many pages each topic takes.

Writes src/CrawlFurther/Tips/MonsterTipsGenerated.cs, which MonsterTipsData loads after its hand-written (vanilla) rows, so a
JSON entry replaces a hand-written one for the same key. Names must carry no mod tag (since 0.9.1 nothing shows
one; mod names are marked in violet instead, and any tag found is stripped). Trailing full stops are dropped from tip lines.

Checks (any problem makes the script exit 1):
  - every tip line fits the tip box: "Attack: " / "Special: " / "Passive: " + text <= 60 characters, and the
    second passive line <= 60
  - only characters every HUD font has (CrawlSmall lacks % { | } ~, CrawlTextBodyThin lacks #; GUIText eats "[word]")
  - every MonsterDef id in src/CrawlFurther/**/*.cs has a tip (no generic fallback is ever shown)
  - every MonsterDef id has a vault line: hand-written in src/CrawlFurther/Library/VaultLines.cs, or a "vault" field
  - vault lines: one line, <= VAULT_MAX characters, the HUD-font character rules, no "[word]"
  - pause pages: headers fit the tab, no word wider than a line

Run from anywhere:  python3 tools/merge_tips.py
"""
import glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "src", "CrawlFurther", "Tips", "MonsterTipsGenerated.cs")
TIPS = os.path.join(ROOT, "data", "tips")
PAGES = "tips_pages.json"
MAX_LINE = 60
BAD_CHARS = set("%{|}~[]#")
TAG = re.compile(r"\s*[\[(]MOD[\])]\s*")
HIGHLIGHT = "#d4be9c"

# CrawlTextBodyThin advance widths (font px = world units at the tips' font size), chars 32..126. Same table as
# PauseTips.Thin in C#.
THIN = [3,2,4,0,4,4,5,2,3,3,2,4,2,4,2,4,4,3,4,4,4,4,4,4,4,4,2,2,4,4,4,4,6,4,4,3,4,3,3,4,4,2,4,4,3,5,4,4,4,4,4,4,4,4,
        4,5,4,4,4,3,4,3,4,4,2,4,4,3,4,4,3,4,4,2,2,4,2,5,4,4,4,4,3,4,3,4,4,5,4,4,4,3,2,3,4]
# CrawlSmall (tab headers)
SMALL = [5,3,4,6,7,0,7,2,4,4,6,6,2,5,2,4,6,4,6,6,6,6,6,6,6,6,2,2,5,4,5,7,7,6,6,5,6,5,5,6,6,3,6,6,5,8,6,6,6,6,6,6,5,6,
         6,8,6,6,6,4,4,4,4,6,2,6,6,5,6,5,5,6,6,3,6,6,5,8,6,6,6,6,6,6,5,6,6,8,6,6,6,0,0,0,0]
BODY_WIDTH = 188      # PauseTips.BodyWidth
LINES_PER_PAGE = 7    # PauseTips.LinesPerPage
TAB_TEXT_MAX = 41     # the vanilla tab sprite is 43 px; wider headers get a doubled tab
VAULT_MAX = 90        # the vault wraps its description box, but every hand-written line is <= 84; keep them short
INDENT = "  "


def clean(text, is_name=False):
    text = (text or "").strip()
    text = TAG.sub(" ", text).strip()
    text = re.sub(r"\s+", " ", text)
    if not is_name:
        text = text.rstrip(".").rstrip()
    return text


def cs(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


NBSP = "~"   # a space that never breaks (number and unit); shown as a space, never reaches the font


def width(s, table=THIN):
    s = re.sub(r"<[^>]*>", "", s).replace(NBSP, " ")
    return sum(table[ord(c) - 32] if 32 <= ord(c) < 127 else 4 for c in s)


def wrap(para, maxw=BODY_WIDTH):
    """Same algorithm as PauseTips.Wrap: greedy words, rich-text tags take no width, bullets hang."""
    bullet = para.startswith("- ")
    words = para.split(" ")
    lines, cur = [], ""
    for w in words:
        trial = w if not cur else cur + " " + w
        if cur and width(trial) > maxw:
            lines.append(cur)
            cur = (INDENT if bullet else "") + w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return [l.replace(NBSP, " ") for l in lines]


def paginate(paras):
    """Same as PauseTips.Paginate: a paragraph that does not fit the rest of a page starts the next one, unless it is
    longer than a page anyway."""
    pages, cur = [], []
    for p in paras:
        lines = wrap(p)
        if cur and len(cur) + len(lines) > LINES_PER_PAGE and len(lines) <= LINES_PER_PAGE:
            pages.append(cur)
            cur = []
        for l in lines:
            if len(cur) == LINES_PER_PAGE:
                pages.append(cur)
                cur = []
            cur.append(l)
    if cur or not pages:
        pages.append(cur)
    return pages


def markup(text):
    text = re.sub(r"(\d) (s|px)\b", lambda m: m.group(1) + NBSP + m.group(2), text)
    return re.sub(r"\*([^*]+)\*", lambda m: "<color=%s>%s</color>" % (HIGHLIGHT, m.group(1)), text)


def library_ids():
    """Monster ids with a hand-written vault line in VaultLines.cs (M("Id", "Name", "Line"))."""
    src = open(os.path.join(ROOT, "src", "CrawlFurther", "Library", "VaultLines.cs"), encoding="utf-8").read()
    return {"Mod" + m.group(1) for m in re.finditer(r'\bM\("(\w+)",\s*"', src)}


def monster_ids():
    """Every MonsterDef id the packs build (prefab name = "Mod" + id)."""
    ids = set()
    for f in glob.glob(os.path.join(ROOT, "src", "CrawlFurther", "**", "*.cs"), recursive=True):
        src = open(f, encoding="utf-8").read()
        for m in re.finditer(r"MonsterDef\s*\{[^{}]*?\bid\s*=\s*\"(\w+)\"", src, re.S):
            ids.add("Mod" + m.group(1))
    return ids


def check_chars(where, line, problems):
    bad = sorted(set(line) & BAD_CHARS)
    if bad or any(ord(c) > 126 for c in line):
        problems.append("%s uses characters the HUD fonts lack: %r" % (where, line))


def load_pages(problems, notes):
    path = os.path.join(TIPS, PAGES)
    if not os.path.exists(path):
        return []
    try:
        data = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        problems.append("%s: unreadable (%s)" % (PAGES, e))
        return []
    topics = []
    for t in data.get("topics", []):
        tid, header = t.get("id"), (t.get("header") or "").upper()
        paras = [p.strip() for p in t.get("text", []) if p and p.strip()]
        if not tid or not header or not paras:
            problems.append("%s: topic %r needs id, header and text" % (PAGES, tid))
            continue
        if width(header, SMALL) > 2 * TAB_TEXT_MAX:
            problems.append("%s: header %r is too wide for the tab" % (PAGES, header))
        sub = t.get("subtitle") or ""
        for where, line in [("header", header), ("subtitle", sub)] + [("text", p) for p in paras]:
            check_chars("%s: %s %s" % (PAGES, tid, where), line.replace("*", ""), problems)
            if line.count("*") % 2:
                problems.append("%s: %s has an unclosed *highlight*: %r" % (PAGES, tid, line))
        rich = [markup(p) for p in paras]
        n = 0
        for p in rich:
            for w in p.split(" "):
                if width(w) > BODY_WIDTH:
                    problems.append("%s: %s word too wide for a line: %r" % (PAGES, tid, w))
            n += len(wrap(p))
        pages = len(paginate(rich))
        notes.append("page topic %-8s %2d lines -> %d page(s)" % (tid, n, pages))
        if width(sub) > 110:
            problems.append("%s: %s subtitle is too wide (keep it short): %r" % (PAGES, tid, sub))
        topics.append((tid, t.get("god") or "", header, sub, rich))
    return topics


def main():
    rows, notes, problems = {}, [], []
    vault = []   # (key, name, line) in file order
    files = sorted(f for f in glob.glob(os.path.join(TIPS, "tips_*.json")) if os.path.basename(f) != PAGES)
    for f in files:
        base = os.path.basename(f)
        group = base[len("tips_"):-len(".json")]
        try:
            data = json.load(open(f, encoding="utf-8"))
        except Exception as e:
            problems.append("%s: unreadable (%s)" % (base, e))
            continue
        for key, tip in data.items():
            if not isinstance(tip, dict):
                problems.append("%s: %s is not an object" % (base, key))
                continue
            name = clean(tip.get("name"), True)
            attack, special = clean(tip.get("attack")), clean(tip.get("special"))
            praw = tip.get("passive")
            plines = [clean(x) for x in (praw if isinstance(praw, list) else [praw]) if x and clean(x)]
            # a full stop between two passive lines stays (only the last one is dropped)
            raw = [re.sub(r"\s+", " ", x.strip()) for x in (praw if isinstance(praw, list) else [praw]) if x and clean(x)]
            for i in range(len(plines) - 1):
                if raw[i].endswith(".") and not plines[i].endswith("."):
                    plines[i] += "."
            if len(plines) > 2:
                problems.append("%s: %s passive has %d lines (max 2)" % (base, key, len(plines)))
                plines = plines[:2]
            if not name or not attack:
                problems.append("%s: %s needs a name and an attack" % (base, key))
                continue
            special = special or "none"
            if key in rows:
                notes.append("%s: %s also in %s (later file wins)" % (base, key, rows[key][0]))
            rows[key] = (base, name, attack, special, "\n".join(plines), group)
            v = tip.get("vault")
            if v:
                vname, vline = name, v
                if isinstance(v, dict):
                    vname, vline = clean(v.get("name"), True) or name, v.get("text") or ""
                    if vname != name:
                        problems.append("%s: %s vault name %r does not match the tip name %r" % (base, key, vname, name))
                vline = re.sub(r"\s+", " ", str(vline).strip()).rstrip(".").rstrip()
                if not vline or "\n" in str(v):
                    problems.append("%s: %s vault line must be one non-empty line" % (base, key))
                else:
                    check_chars("%s: %s vault" % (base, key), vline, problems)
                    if len(vline) > VAULT_MAX:
                        problems.append("%s: %s vault line is %d chars (max %d): %s" % (base, key, len(vline), VAULT_MAX, vline))
                    if not key.startswith("Mod") or "/" in key:
                        problems.append("%s: %s has a vault line but is not a mod monster" % (base, key))
                    vault = [x for x in vault if x[0] != key] + [(key, name, vline)]
            checks = [("Title", "", name), ("Attack", "Attack: ", attack), ("Special", "Special: ", special)]
            for i, pl in enumerate(plines):
                checks.append(("Passive" if i == 0 else "Passive line 2", "Passive: " if i == 0 else "", pl))
            for what, label, line in checks:
                check_chars("%s: %s %s" % (base, key, what), line, problems)
                if what != "Title" and len(label + line) > MAX_LINE:
                    problems.append("%s: %s %s is %d chars (max %d): %s" % (base, key, what, len(label + line), MAX_LINE, line))

    defs = monster_ids()
    for pid in sorted(defs - set(rows)):
        problems.append("no tip for mod monster %s" % pid)
    hand = library_ids()
    for pid in sorted(defs - hand - {k for k, _, _ in vault}):
        problems.append("no vault line for mod monster %s (add \"vault\" to its tip, or a line in VaultLines.cs)" % pid)

    topics = load_pages(problems, notes)

    out = [
        "// GENERATED by tools/merge_tips.py from data/tips/tips_*.json - do not edit by hand, re-run the script.",
        "using System.Collections.Generic;",
        "",
        "namespace CrawlFurther.Content.Tips",
        "{",
        "    using CrawlFurther.UI;",
        "",
        "    public static partial class MonsterTipsData",
        "    {",
        "        /// <summary>The tips file each generated key came from (\"ysveld\", \"ghosts\", ...): the pause pages link a",
        "        /// monster to its god's topic with it.</summary>",
        "        public static readonly Dictionary<string, string> Group = new Dictionary<string, string>();",
        "        /// <summary>Vault lines from the tips files' \"vault\" fields: prefab name -> (display name, line).</summary>",
        "        public static readonly Dictionary<string, KeyValuePair<string, string>> Vault = new Dictionary<string, KeyValuePair<string, string>>();",
        "        /// <summary>The <see cref=\"Vault\"/> keys in file order (the vault lists them in this order).</summary>",
        "        public static readonly List<string> VaultOrder = new List<string>();",
        "",
        "        static void V(string key, string name, string line)",
        "        {",
        "            if (!Vault.ContainsKey(key)) VaultOrder.Add(key);",
        "            Vault[key] = new KeyValuePair<string, string>(name, line);",
        "        }",
        "",
        "        /// <summary>Mod monster, minion, ghost and boss-part tips (%d entries from %d files). Loaded after the hand-written rows.</summary>" % (len(rows), len(files)),
        "        static void AddGenerated()",
        "        {",
    ]
    last = None
    for key in sorted(rows, key=lambda k: (rows[k][0], k)):
        src, name, attack, special, passive, group = rows[key]
        if src != last:
            out.append("            // %s" % src)
            last = src
        args = [cs(key), cs(name), cs(attack), cs(special)] + ([cs(passive)] if passive else [])
        out.append("            T(%s); Group[%s] = %s;" % (", ".join(args), cs(key), cs(group)))
    if vault:
        out.append("            // vault lines (%d), in file order" % len(vault))
    for key, name, line in vault:
        out.append("            V(%s, %s, %s);" % (cs(key), cs(name), cs(line)))
    out += ["        }", "    }", ""]
    out += [
        "    public static partial class PauseTipsData",
        "    {",
        "        /// <summary>Pause > Tips topics from data/tips/%s (%d topics). Text is rich text, unwrapped.</summary>" % (PAGES, len(topics)),
        "        public static readonly PauseTopic[] Topics =",
        "        {",
    ]
    for tid, god, header, sub, rich in topics:
        out.append("            new PauseTopic(%s, %s, %s, %s, new[]" % (cs(tid), cs(god), cs(header), cs(sub)))
        out.append("            {")
        for p in rich:
            out.append("                %s," % cs(p))
        out.append("            }),")
    out += ["        };", "    }", "}", ""]
    open(OUT, "w", encoding="utf-8").write("\n".join(out))
    print("merge_tips: %d tips from %d files, %d vault lines, %d pause topics -> %s"
          % (len(rows), len(files), len(vault), len(topics), os.path.relpath(OUT, ROOT)))
    for n in notes:
        print("  note: " + n)
    for p in problems:
        print("  PROBLEM: " + p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
