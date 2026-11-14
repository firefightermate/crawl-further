"""Basic attacks of every tier 2 and 3 mod monster: what each clip fires, whether it moves, and the custom events its
quirk runs. A basic that fires one plain projectile or one plain hitbox, with no movement and no event of its own, is
flagged PLAIN.

    python3 tools/primary_audit.py [god]
"""
import os, re, sys, json
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
want = sys.argv[1:] 
sys.argv = [sys.argv[0]]
import hitbox_audit as A
MX = A.MX

out = []
for god, files in sorted(MX.god_groups().items()):
    raw = "\n".join(open(f).read() for f in files)
    text = MX.strip_comments(raw)
    rects, proj = A.mod_shapes(text)
    for f in MX.defs(raw):
        if not f["kit"] or (f["evolveCost"] or 0) < 2:
            continue
        km = re.search(r"static void " + re.escape(f["kit"]) + r"\s*\(", text)
        if not km:
            continue
        body = MX.body_of(text, km.start())
        slots = A.slot_info(body)
        clips = {}
        for cm in re.finditer(r"(?:var|exSpriteAnimClip)\s+(\w+)\s*=\s*([^;]*\(\s*sh\w*\s*,\s*\"\w+\"[^;]*);", body, re.S):
            clips[cm.group(1)] = cm.group(2)
        basics = []
        for am in re.finditer(r"Kit\.Attack\(", body):
            args = MX.split_args(body[am.end():])
            pre = body[max(0, am.start() - 40):am.start()]
            if re.search(r"(SetSpecial|EnableSpecial)\(\s*\w+\s*,\s*$", pre) or len(args) < 2:
                continue
            cexpr = clips.get(args[1].strip(), args[1])
            fired = A.fired_slots(body, cexpr, slots)
            kinds = []
            for sv in fired:
                en = slots[sv][0]
                kinds.append(en + ("(p)" if en in proj else ""))
            custom = sorted(set(c for c in re.findall(r'\.Ev[A-Z]?\(\s*-?\d+\s*,\s*"(\w+)"', cexpr) if not c.startswith("Anim")))
            move = bool(re.search(r"AnimMoveStick|Kit\.Melee\([^;]*,\s*[1-9]\d*f\s*\)", cexpr))
            n = len(set(kinds))
            plain = n <= 1 and not custom and not move
            basics.append({"fx": sorted(set(kinds)), "custom": custom, "move": move, "plain": plain})
        out.append({"god": god, "id": f["id"], "tier": 3 if f["evolveCost"] >= 4 else 2, "basics": basics})
for m in out:
    if want and m["god"] not in want:
        continue
    for b in m["basics"] or [{"fx": ["?"], "custom": [], "move": False, "plain": True}]:
        print("%-8s t%d %-20s %-6s %-60s %s%s" % (m["god"], m["tier"], m["id"], "PLAIN" if b["plain"] else "", ", ".join(b["fx"])[:60],
              ("events " + ",".join(b["custom"])) if b["custom"] else "", " move" if b["move"] else ""))
plain = sum(1 for m in out if all(b["plain"] for b in m["basics"]))
print("%d tier 2/3 monsters, %d with only plain basics" % (len(out), plain))
