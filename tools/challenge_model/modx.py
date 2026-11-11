"""Mod monsters' combat numbers, read from the code the same way vanilla.py reads the dump: health, speed, attacks
(damage per use, windup, clip length, cooldown, reach, projectile speed), special (damage, charge)."""
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA = os.path.join(ROOT, "build", "chal")
os.makedirs(DATA, exist_ok=True)
import re, os, sys, json, glob, collections
sys.argv = ["validate.py"]; sys.path.insert(0, ROOT + "/tools")
import validate as V
NUM = r"(-?\d+(?:\.\d+)?)f?"

def split_args(s):
    out, depth, cur, q = [], 0, "", False
    for ch in s:
        if ch == '"': q = not q
        if not q:
            if ch in "([{": depth += 1
            if ch in ")]}":
                if depth == 0: break
                depth -= 1
            if ch == "," and depth == 0: out.append(cur.strip()); cur = ""; continue
        cur += ch
    if cur.strip(): out.append(cur.strip())
    return out

def fnum(a):
    if a is None: return None
    a = a.split(":")[-1].strip() if re.match(r"^\w+\s*:", a or "") else a
    m = re.fullmatch(r"\s*" + NUM + r"\s*", a or "")
    return float(m.group(1)) if m else None

def body_of(text, start):
    i = text.index("{", start); d = 0
    for j in range(i, len(text)):
        if text[j] == "{": d += 1
        elif text[j] == "}":
            d -= 1
            if d == 0: return text[i:j + 1]
    return text[i:]

def strip_comments(t):
    t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
    return re.sub(r"//[^\n]*", "", t)

# ---------------------------------------------------------------- effects
CORE_SIG = {
    "FxKit.Projectile": ["name", "vanilla", "art", "anim", "speed", "life", "damage", "knock"],
    "FxKit.Swipe": ["name", "vanilla", "damage", "knock"],
    "FxKit.BodyHit": ["name", "damage", "rate", "knock", "life"],
    "FxKit.TimedHit": ["name", "vanilla", "art", "anim", "onFrame", "offFrame", "damage", "knock", "status", "statusChance", "rate"],
    "FxKit.Cloud": ["name", "art", "anim", "speed", "damage", "rate"],
}
ROLE = {"damage": "dmg", "dmg": "dmg", "d": "dmg", "dm": "dmg", "speed": "speed", "rate": "rate", "count": "count",
        "w": "w", "h": "h", "life": "life"}

def helper_sigs(text):
    sig = {}
    for m in re.finditer(r"static GameObject (\w+)\(([^)]*)\)", text):
        names = []
        for p in m.group(2).split(","):
            p = p.split("=")[0].strip()
            names.append(p.split()[-1] if p else "")
        sig.setdefault(m.group(1), names)
    return sig

def effects_of(text):
    """name -> {dmg, rate, speed, count, w, h}: every GameObject the god's Fx code builds."""
    sigs = dict(CORE_SIG); sigs.update(helper_sigs(text))
    eff = {}
    assigns = list(re.finditer(r"(?<![\w.])(\w+)\s*=\s*([^;]+);", text))
    for _ in range(3):  # templates may be defined after use
        for m in assigns:
            name, expr = m.group(1), m.group(2).strip()
            if name in ("go", "o", "c", "d", "e", "s", "i", "r"): continue
            hm = re.match(r"(?:\w+Fx\.)?(FxKit\.\w+|\w+)\(", expr)
            if not hm: 
                hm2 = re.fullmatch(r"(?:\w+Fx\.)?(\w+)", expr)
                if hm2 and hm2.group(1) in eff: eff[name] = dict(eff[hm2.group(1)])
                continue
            fn = hm.group(1); args = split_args(expr[hm.end():])
            if fn in ("FxKit.Weakened",) and len(args) >= 3:
                t = re.sub(r"^\w+Fx\.", "", args[0])
                if t in eff: e = dict(eff[t]); e["dmg"] = (e.get("dmg") or 0) * (fnum(args[2]) or 1); eff[name] = e
                continue
            if fn == "FxKit.EchoOf" and args:
                t = re.sub(r"^\w+Fx\.", "", args[0])
                if t in eff: e = dict(eff[t]); e["dmg"] = (e.get("dmg") or 0) * (fnum(args[1]) if len(args) > 1 else 0.5); eff[name] = e
                continue
            if fn in ("FxKit.Emitter", "Ring") and len(args) >= 3:
                t = re.sub(r"^\w+Fx\.", "", args[1])
                if t in eff: e = dict(eff[t]); e["count"] = fnum(args[2]) or 1; eff[name] = e
                continue
            if fn in ("At", "Ground", "Flame") and args:
                t = re.sub(r"^\w+Fx\.", "", args[0])
                if t in eff: eff[name] = dict(eff[t])
                continue
            sig = sigs.get(fn) or sigs.get(fn.split(".")[-1])
            if not sig: continue
            e = {}
            for i, a in enumerate(args):
                key = sig[i] if i < len(sig) else None
                if re.match(r"^\w+\s*:", a): key, a = a.split(":", 1)[0].strip(), a.split(":", 1)[1]
                role = ROLE.get(key)
                if role:
                    v = fnum(a)
                    if v is not None: e[role] = v
            if "dmg" in e or "speed" in e: eff[name] = e
    for m in re.finditer(r"FxFactory\.SetDamage\(\s*(\w+)\s*,\s*" + NUM, text):
        eff.setdefault(m.group(1), {})["dmg"] = float(m.group(2))
    return eff

def effect_damage(e):
    if not e: return 0.0, 0.0, 0.0
    d = e.get("dmg") or 0.0; n = e.get("count") or 1.0
    life = e.get("life") or 0.0; rate = e.get("rate") or 0.0
    if rate > 0 and life > rate * 1.5:   # a lingering zone: hits every rate seconds
        return 0.0, d / rate * n, e.get("speed") or 0.0
    # a spread of n projectiles: about half of them find a single target
    return d * (1 + 0.5 * (n - 1)), 0.0, e.get("speed") or 0.0

# ---------------------------------------------------------------- clips
def anim_frames(sheets, anim):
    for s in sheets:
        m = V.SHEETS.get(s)
        if not m: continue
        for a in m["anims"]:
            if a["name"] == anim:
                return a.get("durations") or [0.1] * len(a["frames"])
    return None

def clip_from(expr, sheets, slots, eff):
    """A clip expression -> {len, dmg, linger, windup, proj, custom[]}."""
    m = re.search(r'(new ClipBuilder|Kit\.Melee|Kit\.Shot|\w+)\(\s*sh\w*\s*,\s*"(\w+)"', expr)
    if not m: return None
    kind, anim = m.group(1), m.group(2)
    durs = anim_frames(sheets, anim)
    if durs is None: return None
    rep = re.search(r"\.Repeat\(\s*(\d+)\s*\)", expr)
    times = list(durs) * (int(rep.group(1)) if rep else 1)
    dd = re.search(r"\.Durations\(([^)]*)\)", expr)
    if dd:
        vals = [fnum(x) for x in dd.group(1).split(",")]
        for i, v in enumerate(vals):
            if v is not None and i < len(times): times[i] = v
    for t, rp in re.findall(r'\.Then\(\s*"(\w+)"\s*(?:,\s*(\d+))?\s*\)', expr):
        k = anim_frames(sheets, t)
        if k: times += list(k) * (int(rp) if rp else 1)
    sp = re.search(r"\.Speed\(\s*" + NUM + r"\s*\)", expr)
    spd = float(sp.group(1)) if sp else 1.0
    starts = [0.0]
    for t in times: starts.append(starts[-1] + t)
    n = len(times)
    def at(fr, off=0.0):
        fr = n + fr if fr < 0 else fr
        return starts[max(0, min(n, fr))] / spd + off
    events = []  # (time, slot or None, method)
    args = split_args(expr[expr.index("(", m.start()) + 1:])
    if kind == "Kit.Melee":
        nums = args[4:]
        for i in range(0, len(nums) - 2, 3):
            f = fnum(nums[i]); slot = nums[i + 1].strip()
            if f is not None: events.append((at(int(f)), slot, "AnimAttack"))
    if kind == "Kit.Shot" and len(args) >= 6:
        rel = fnum(args[3]); stag = fnum(args[5]) or 0.0
        for i, slot in enumerate(args[6:]):
            if rel is not None: events.append((at(int(rel), i * stag), slot.strip(), "AnimAttack"))
    for em in re.finditer(r'\.Ev\(\s*(-?\d+)\s*,\s*"AnimAttack"\s*,\s*([\w.]+)\s*(?:,\s*' + NUM + r')?\s*\)', expr):
        events.append((at(int(em.group(1)), float(em.group(3) or 0)), em.group(2), "AnimAttack"))
    custom = sorted(set(c for c in re.findall(r'\.Ev[A-Z]?\(\s*-?\d+\s*,\s*"(\w+)"', expr)
                        if not c.startswith("Anim")))
    hit = lin = proj = 0.0; first = None
    for t, slot, _ in sorted(events):
        e = eff.get(slots.get(slot, slot))
        h, l, s = effect_damage(e)
        if h or l:
            hit += h; lin += l; proj = max(proj, s)
            if first is None: first = t
    return {"anim": anim, "len": round(starts[-1] / spd, 3), "dmg": round(hit, 3), "linger": round(lin, 3),
            "windup": first, "proj": proj, "custom": custom}

def kit_moves(text, kit, sheets, eff):
    m = re.search(r"static void " + re.escape(kit) + r"\s*\(", text)
    if not m: return None
    b = strip_comments(body_of(text, m.start()))
    slots = {}
    for sm in re.finditer(r"(?:int|var)\s+(\w+)\s*=\s*Kit\.AddEffect\(\s*\w+\s*,\s*(?:\w+Fx\.)?(\w+)", b):
        slots[sm.group(1)] = sm.group(2)
    clips = {}
    for cm in re.finditer(r"(?:var|exSpriteAnimClip)\s+(\w+)\s*=\s*([^;]*\(\s*sh\w*\s*,\s*\"\w+\"[^;]*);", b, re.S):
        clips[cm.group(1)] = cm.group(2)
    attacks, special, charge = [], None, None
    for am in re.finditer(r"Kit\.Attack\(", b):
        args = split_args(b[am.end():])
        if len(args) < 3: continue
        cexpr = clips.get(args[1].strip(), args[1])
        ci = clip_from(cexpr, sheets, slots, eff)
        if not ci: continue
        ci["cd"] = fnum(args[2]) or 0.0
        for a in args[3:]:
            if ":" in a:
                k, v = a.split(":", 1); ci[k.strip()] = fnum(v)
        pre = b[max(0, am.start() - 40):am.start()]
        if re.search(r"(SetSpecial|EnableSpecial)\(\s*\w+\s*,\s*$", pre):
            special = ci
            tail = b[am.start():]
            cm2 = re.match(r"Kit\.Attack\(", tail)
            # charge is the argument after the Kit.Attack(...) call
            depth = 0
            for j, ch in enumerate(tail):
                if ch == "(": depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        rest = tail[j + 1:]; mm = re.match(r"\s*,\s*" + NUM, rest)
                        charge = float(mm.group(1)) if mm else None; break
        else:
            attacks.append(ci)
    return {"attacks": attacks, "special": special, "charge": charge, "slots": slots}

def god_groups():
    g = {os.path.basename(d): sorted(glob.glob(d + "/*.cs")) for d in glob.glob(ROOT + "/src/CrawlFurther/Gods/*")}
    g["Secrets"] = sorted(glob.glob(ROOT + "/src/CrawlFurther/Secrets/*.cs"))
    return g

def defs(text):
    for m in re.finditer(r"new MonsterDef\s*\{", text):
        b = body_of(text, m.start()); f = {}
        for k in ("id", "art", "basePrefab"):
            mm = re.search(r"\b" + k + r"\s*=\s*\"([^\"]+)\"", b); f[k] = mm.group(1) if mm else None
        for k in ("health", "speedMult", "damageMult", "evolveCost", "specialChargeTime", "attackCooldownMult"):
            mm = re.search(r"\b" + k + r"\s*=\s*" + NUM, b); f[k] = float(mm.group(1)) if mm else None
        mm = re.search(r"\bkit\s*=\s*(\w+)", b); f["kit"] = mm.group(1) if mm else None
        yield f

if __name__ == "__main__":
    vb = {m["name"]: m for m in json.load(open(os.path.join(DATA, "vanilla_all.json")))}
    out = []
    for god, files in sorted(god_groups().items()):
        text = "\n".join(open(f).read() for f in files)
        eff = effects_of(strip_comments(text))
        for f in defs(text):
            if not f["kit"]: continue
            mon = next((x for x in V.MONSTERS if x["id"] == f["id"]), None)
            sheets = set()
            for key, ss in V.KIT_ART.items():
                if key[1] == f["kit"]: sheets |= ss
            if mon and mon.get("art"): sheets.add(mon["art"])
            km = kit_moves(text, f["kit"], sorted(sheets), eff) or {}
            base = vb.get(f["basePrefab"]) or {}
            f.update(god=god, sheets=sorted(sheets), attacks=km.get("attacks", []), special=km.get("special"),
                     charge=km.get("charge"), base_speed=base.get("speed"))
            out.append(f)
    json.dump(out, open(os.path.join(DATA, "mod.json"), "w"), indent=1)
    print(len(out))
