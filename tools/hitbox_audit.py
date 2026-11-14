"""Hitbox audit: how much floor every monster's attacks cover, mod against vanilla, tier by tier.

For each attack and special it finds the damage effects the clip fires, where each lands (spawn node or feet plus the
slot's offset) and the collider it carries, then turns that into the patch of floor where the hero's feet get hit:
- Damage-layer effects (13) touch the hero's hurtbox, 8 wide and 18 tall above his feet;
- DamageBase-layer effects (19) touch only his feet capsule (8 x 3).
It reports forward reach, lane depth (how far up or down the floor the hit still lands) and area, and flags mod
melee and ground hits that come out small against the game's own monsters of the same tier, plus capsule colliders
(a capsule's round cross-section also limits depth, unlike the game's 230-deep boxes).

    python3 tools/hitbox_audit.py [--all] [--id SylPuffball]
"""
import os, re, sys, json, glob, statistics
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "challenge_model"))
argv = sys.argv[1:]
import vanilla as VA
import modx as MX
sys.argv = [sys.argv[0]] + argv

DB = VA.DB
COL = {int(k): v for k, v in json.load(open(f"{DB}/_colliders.json")).items()}
H = VA.H
PARENT = {c: pid for pid, h in H.items() for c in (h.get("c") or [])}
ROOTS = {}
for pid, h in sorted(H.items()):
    if pid not in PARENT and h["n"] not in ROOTS:
        ROOTS[h["n"]] = pid
HURT_W, HURT_H, FEET_W, FEET_D = 4.0, 18.0, 4.0, 1.5


def shapes(pid, children=True, ox=0.0, oy=0.0, sx=1.0, sy=1.0, top=True):
    """Collider rectangles (x0, x1, y0, y1, kind, layer) of a GameObject in its parent's space."""
    h = H.get(pid)
    if not h:
        return []
    if not top:
        ox, oy = ox + h["p"][0] * sx, oy + h["p"][1] * sy
    sx, sy = sx * abs(h["s"][0]), sy * abs(h["s"][1])
    out = []
    for c in COL.get(pid, []):
        if c["layer"] not in (13, 19) or not c.get("en", True):
            continue
        cx, cy = ox + c["c"][0] * sx, oy + c["c"][1] * sy
        if c["t"] == "BoxCollider":
            hw, hh = c["size"][0] / 2, c["size"][1] / 2
        elif c["t"] == "CapsuleCollider":
            hw, hh = (c["h"] / 2, c["r"]) if c["dir"] == 0 else (c["r"], c["h"] / 2)
            hw, hh = max(hw, c["r"]), max(hh, c["r"])
        else:
            hw = hh = c.get("r", 0)
        out.append([cx - hw * sx, cx + hw * sx, cy - hh * sy, cy + hh * sy, c["t"][0], c["layer"]])
    if children:
        for ch in h.get("c") or []:
            out += shapes(ch, True, ox, oy, sx, sy, top=False)
    return out


def zone(rects, bx, by):
    """Floor patch (relative to the attacker's feet) where the hero's feet get hit."""
    z = []
    for x0, x1, y0, y1, k, layer, *_ in rects:
        x0, x1, y0, y1 = x0 + bx, x1 + bx, y0 + by, y1 + by
        if layer == 19:
            z.append((x0 - FEET_W, x1 + FEET_W, y0 - FEET_D, y1 + FEET_D, k, layer))
        else:
            z.append((x0 - HURT_W, x1 + HURT_W, y0 - HURT_H, y1, k, layer))
    return z


def summary(zs):
    if not zs:
        return None
    x1 = max(z[1] for z in zs)
    x0 = min(z[0] for z in zs)
    y0 = min(z[2] for z in zs)
    y1 = max(z[3] for z in zs)
    area = sum((z[1] - z[0]) * (z[3] - z[2]) for z in zs)
    return {"reach": round(x1, 1), "back": round(x0, 1), "depth": round(y1 - y0, 1), "area": round(area),
            "caps": any(z[4] == "C" for z in zs), "layers": sorted(set(z[5] for z in zs))}


# ------------------------------------------------------------------ vanilla
def vanilla_moves():
    P = {d["m_GameObject"]["m_PathID"]: d for d in VA.rows("Player")}
    L = json.loads(open(f"{DB}/sharedassets0__SystemLibrary.jsonl").readline())
    out = []
    for e in L["m_monsters"]:
        p = P.get(e["m_prefab"]["m_PathID"])
        if not p:
            continue
        node = p.get("m_attackSpawnNode") or {"x": 1, "y": 0}
        eff = p["m_attackDamageEffects"]
        moves = []
        lst = [("atk%d" % i, a) for i, a in enumerate(p["m_attacks"])]
        if p["m_hasSpecialAttack"]:
            lst.append(("special", p["m_specialAttack"]))
        for tag, a in lst:
            c = VA.CLIP.get(a["m_animationFront"]["m_PathID"])
            if not c:
                continue
            zs, proj = [], False
            for ev in c["eventInfos"]:
                if ev["methodName"] != "AnimAttack" or not (0 <= ev["intParam"] < len(eff)):
                    continue
                d = eff[ev["intParam"]]
                g = d["m_object"]["m_PathID"]
                hit, lin, spd = VA.effect_damage(g)
                if not (hit or lin):
                    continue
                if spd:
                    proj = True
                    continue
                ox = d["m_offsetX"]["m_min"]; oy = d["m_offsetY"]["m_min"]
                sp = d["m_spawnPoint"]
                if sp == 0:
                    bx, by = node["x"] + ox, node["y"] + oy
                elif sp == 4:
                    bx, by = ox, oy
                else:
                    continue   # on the hero or the room: always lands
                zs += zone(shapes(g), bx, by)
            s = summary(zs)
            if s:
                s.update(tag=tag, proj=proj)
                moves.append(s)
        out.append({"name": p["_go"][5:], "cost": p["m_evolveCost"], "moves": moves})
    return out


# ------------------------------------------------------------------ mod
FX_CTORS = {"FxKit.TimedHit": (1, True), "FxKit.Swipe": (1, False), "FxKit.Projectile": (1, False),
            "FxFactory.Clone": (0, False), "Swipe": (1, False)}
SAFE = re.compile(r"^[\d\s.+\-*/()]+$")


def num(expr, env):
    """A number from a C# float expression, with helper parameters substituted."""
    if expr is None:
        return None
    e = expr.strip()
    if re.match(r"^\w+\s*:", e):
        e = e.split(":", 1)[1].strip()
    e = re.sub(r"\b([A-Za-z_]\w*)\b", lambda m: str(env[m.group(1)]) if isinstance(env.get(m.group(1)), (int, float)) else m.group(0), e)
    e = re.sub(r"(\d)f\b", r"\1", e)
    if SAFE.match(e):
        try:
            return float(eval(e, {"__builtins__": {}}))
        except Exception:
            return None
    return None


def helpers(text):
    """name -> (param names, defaults, body) for every static GameObject helper."""
    out = {}
    for m in re.finditer(r"static GameObject (\w+)\(([^)]*)\)\s*(?:\{|=>)", text):
        names, defs = [], {}
        for prm in MX.split_args(m.group(2)):
            left, _, dflt = prm.partition("=")
            n = left.split()[-1] if left.split() else ""
            names.append(n)
            if dflt.strip():
                defs[n] = dflt.strip()
        try:
            body = MX.body_of(text, m.start())
        except ValueError:
            continue
        out.setdefault(m.group(1), (names, defs, body))
    return out


def bind(names, defs, args, outer):
    env = {}
    for n, d in defs.items():
        env[n] = num(d, {}) if num(d, {}) is not None else d
    for i, a in enumerate(args):
        if re.match(r"^\w+\s*:", a):
            k, v = a.split(":", 1); k = k.strip(); v = v.strip()
        elif i < len(names):
            k, v = names[i], a
        else:
            continue
        val = num(v, outer)
        env[k] = val if val is not None else v.strip()
    return env


def apply_strike(rects, kind, args, env):
    if kind == "Ground":
        if len(args) < 5:
            return rects
        w, h, cx, cy = num(args[3], env), num(args[4], env), 0.0, 0.0
    else:
        vals = [num(a, env) for a in args]
        if len(vals) < 2 or vals[0] is None or vals[1] is None:
            return rects
        w, h = vals[0], vals[1]
        cx = vals[2] if len(vals) > 2 and vals[2] is not None else 0.0
        cy = vals[3] if len(vals) > 3 and vals[3] is not None else 0.0
    if w is None or h is None:
        return rects
    layer = rects[0][5] if rects else 13
    kindc = "C" if any(r[4] == "C" for r in rects) else "B"
    src = rects[0][6] if rects and len(rects[0]) > 6 else "?"
    if kind == "Ground" and src.startswith("van"):
        src = "art"
    return [[cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2, kindc, layer, src]]


class FxEval:
    def __init__(self, text):
        self.text = text
        self.helpers = helpers(text)
        self.known, self.proj = {}, set()

    def expr(self, e, env, depth=0):
        """(rects, is_projectile) for a C# expression building an effect."""
        e = e.strip()
        if depth > 6 or not e:
            return None, False
        m = re.match(r"^(?:\w+Fx\.)?(\w+)$", e)
        if m:
            if m.group(1) in env and isinstance(env[m.group(1)], tuple):
                return env[m.group(1)]
            if m.group(1) in self.known:
                return self.known[m.group(1)], m.group(1) in self.proj
            return None, False
        m = re.match(r"^(?:\w+Fx\.|GodsBArc\.)?((?:FxKit|FxFactory|AimedMelee|Strike)\.\w+|\w+)\s*\(", e)
        if not m:
            return None, False
        fn = m.group(1)
        args = MX.split_args(e[m.end():])
        if fn == "FxKit.BodyHit":
            return [r + ["inv"] for r in shapes(ROOTS["DamageGiantRatAttack"], False)], False
        if fn in ("AimedMelee.Rotating", "FxKit.Weakened", "FxKit.EchoOf", "FxKit.NoTint") and args:
            return self.expr(args[0], env, depth + 1)
        if fn in FX_CTORS and fn != "Swipe" or (fn == "Swipe" and fn not in self.helpers):
            i, strip = FX_CTORS.get(fn, (1, False))
            if len(args) <= i:
                return None, False
            van = args[i].strip()
            van = env.get(van, van) if not van.startswith('"') else van
            van = str(van).strip('"')
            if van not in ROOTS:
                return None, False
            rects = [r + ["art" if fn == "FxKit.TimedHit" else "van:" + van] for r in shapes(ROOTS[van], children=not strip)]
            if fn == "FxKit.TimedHit":
                k = None
                for j, a in enumerate(args):
                    if a.startswith("colliderScale:"):
                        k = num(a, env)
                    elif j == 11 and ":" not in a:
                        k = num(a, env)
                if k:
                    rects = [[r[0] * k, r[1] * k, r[2] * k, r[3] * k, r[4], r[5], r[6]] for r in rects]
            return rects, fn == "FxKit.Projectile"
        if fn in self.helpers:
            names, defs, body = self.helpers[fn]
            benv = bind(names, defs, args, env)
            for n in names:
                if n in benv and isinstance(benv[n], str) and re.match(r"^(?:\w+Fx\.)?\w+\s*\(|^(?:\w+Fx\.)?\w+$", benv[n]):
                    r = self.expr(benv[n], env, depth + 1)
                    if r[0] is not None:
                        benv[n] = r
            local = {}
            cur = (None, False)
            for st in re.finditer(r"(?:var\s+|GameObject\s+)?(\w+)\s*=\s*([^;]+);|Strike\.(HitBox|Ground|Collider)\(\s*(\w+)\s*,", body):
                if st.group(1):
                    r = self.expr(st.group(2), dict(benv, **local), depth + 1)
                    if r[0] is not None:
                        local[st.group(1)] = r
                        cur = r
                else:
                    tgt = st.group(4)
                    src = local.get(tgt) or (benv.get(tgt) if isinstance(benv.get(tgt), tuple) else None)
                    if src:
                        sargs = MX.split_args(body[st.end():])
                        r = (apply_strike(src[0], st.group(3), sargs, benv), src[1])
                        if tgt in local:
                            local[tgt] = r
                        else:
                            benv[tgt] = r
                        cur = r
            ret = re.search(r"return\s+(\w+)\s*;", body)
            if ret and ret.group(1) in local:
                return local[ret.group(1)]
            if ret and isinstance(benv.get(ret.group(1)), tuple):
                return benv[ret.group(1)]
            return cur
        return None, False


def mod_shapes(text):
    """effect name -> list of collider rects, as the Fx code leaves them."""
    ev = FxEval(text)
    body = re.sub(r"static GameObject \w+\([^)]*\)\s*\{", "", text)
    for _ in range(2):
        for m in re.finditer(r"(?<![\w.])(\w+)\s*=\s*([^;]+);|Strike\.(HitBox|Ground|Collider)\(\s*(?:\w+Fx\.)?(\w+)\s*,", text):
            if m.group(1):
                if m.group(1) in ("go", "o", "c", "d", "e", "s", "i", "r", "sh", "cb", "spr"):
                    continue
                r, pj = ev.expr(m.group(2), {})
                if r is not None:
                    ev.known[m.group(1)] = r
                    if pj:
                        ev.proj.add(m.group(1))
            else:
                nm = m.group(4)
                if nm in ev.known and nm not in ("go",):
                    ev.known[nm] = apply_strike(ev.known[nm], m.group(3), MX.split_args(text[m.end():]), {})
    return ev.known, ev.proj


class Spy(dict):
    def __init__(self, base):
        super().__init__(base); self.seen = []
    def get(self, k, d=None):
        self.seen.append(k); return super().get(k, d)


def slot_info(body):
    """slot var -> (effect, offsetX, offsetY, spawnPoint)."""
    names = ["p", "prefab", "attach", "destroyOnAnimEnd", "offsetX", "offsetY", "angle", "angleMax", "spawnPoint", "like"]
    out = {}
    for m in re.finditer(r"(?:int|var)\s+(\w+)\s*=\s*Kit\.AddEffect\(", body):
        args = MX.split_args(body[m.end():])
        kv = {}
        for i, a in enumerate(args):
            if re.match(r"^\w+\s*:", a):
                k, v = a.split(":", 1); kv[k.strip()] = v.strip()
            elif i < len(names):
                kv[names[i]] = a
        eff = re.sub(r"^\w+Fx\.", "", kv.get("prefab", "")).strip()
        sp = kv.get("spawnPoint", "Node")
        out[m.group(1)] = (eff, MX.fnum(kv.get("offsetX", "0")) or 0.0, MX.fnum(kv.get("offsetY", "0")) or 0.0,
                           "Position" if "Position" in sp else ("Enemy" if "Closest" in sp or "Room" in sp else "Node"))
    # slots kept in lists: xs.Add(Kit.AddEffect(...)) -> xs[0..]
    for m in re.finditer(r"(\w+)\.Add\(\s*Kit\.AddEffect\(", body):
        args = MX.split_args(body[m.end():])
        kv = {}
        for i, a in enumerate(args):
            if re.match(r"^\w+\s*:", a):
                k, v = a.split(":", 1); kv[k.strip()] = v.strip()
            elif i < len(names):
                kv[names[i]] = a
        eff = re.sub(r"^\w+Fx\.", "", kv.get("prefab", "")).strip()
        sp = kv.get("spawnPoint", "Node")
        k = 0
        while "%s#%d" % (m.group(1), k) in out:
            k += 1
        out["%s#%d" % (m.group(1), k)] = (eff, MX.fnum(kv.get("offsetX", "0")) or 0.0, MX.fnum(kv.get("offsetY", "0")) or 0.0,
                                          "Position" if "Position" in sp else ("Enemy" if "Closest" in sp or "Room" in sp else "Node"))
    return out


def fired_slots(body, cexpr, slots):
    """Slot vars an attack's clip fires: every slot named in the statements that build that clip (its variable, the
    local function it calls, the lists it spreads)."""
    names = set(re.findall(r"\b([A-Za-z_]\w*)\b", cexpr))
    text = cexpr
    stmts = re.split(r";", body)
    for _ in range(2):
        for st in stmts:
            if any(re.search(r"\b%s\b" % re.escape(n), st) for n in names if n not in ("sh", "p", "new", "ClipBuilder", "Kit", "Build", "Melee", "Shot", "Ev")):
                text += ";" + st
        for n in list(names):
            fm = re.search(r"(?:\w+(?:<[^>]*>)?\s+%s\s*\(|\b%s\s*=\s*(?:\([^)]*\)|\w+)\s*=>)" % (re.escape(n), re.escape(n)), body)
            if fm:
                try:
                    text += MX.body_of(body, fm.start())
                except ValueError:
                    pass
    out = []
    for sv in slots:
        base = sv.split("#")[0]
        if re.search(r"\b%s\b" % re.escape(base), text):
            out.append(sv)
    return out


EFFECTS = {}
FLOOR_BODY = {2: (24, 18), 3: (30, 22)}
FLOOR_THRUST = {2: 14, 3: 16}
FLOOR_GROUND = {2: (44, 18), 3: (56, 24)}
ART_GROWTH = 1.15


def floored(rects, tier, lingering):
    """The same rule as Core's HitFloor: capsules become boxes, strikes rise to the tier's least size."""
    out = []
    for r in rects:
        r = list(r) + ["?"] * (7 - len(r))
        x0, x1, y0, y1, k, layer, src = r[:7]
        w, h = x1 - x0, y1 - y0
        if tier >= 2 and not lingering:
            ground = layer == 19
            mw, mh = (FLOOR_GROUND if ground else FLOOR_BODY)[tier]
            if not ground and w >= 2 * h:
                mh = FLOOR_THRUST[tier]
            if src != "inv" and not str(src).startswith("van:DamageGiantRat"):
                mw, mh = min(mw, w * ART_GROWTH), min(mh, h * ART_GROWTH)
            nw, nh = max(w, mw), max(h, mh)
            shift = 0 if ground else (nw - w) * 0.25
            cx, cy = (x0 + x1) / 2 + shift, (y0 + y1) / 2
            x0, x1, y0, y1 = cx - nw / 2, cx + nw / 2, cy - nh / 2, cy + nh / 2
        out.append([x0, x1, y0, y1, "B", layer, src])
    return out


def mod_moves(vnode):
    out = []
    for god, files in sorted(MX.god_groups().items()):
        raw = "\n".join(open(f).read() for f in files)
        text = MX.strip_comments(raw)
        eff = MX.effects_of(text)
        rects, proj = mod_shapes(text)
        for f in MX.defs(raw):
            if not f["kit"]:
                continue
            km = re.search(r"static void " + re.escape(f["kit"]) + r"\s*\(", text)
            if not km:
                continue
            body = MX.body_of(text, km.start())
            slots = slot_info(body)
            feet = re.search(r"Strike\.Feet\(", body) is not None
            node = vnode.get(f["basePrefab"], {"x": 1, "y": 0})
            mon = next((x for x in MX.V.MONSTERS if x["id"] == f["id"]), None)
            sheets = set()
            for key, ss in MX.V.KIT_ART.items():
                if key[1] == f["kit"]:
                    sheets |= ss
            if mon and mon.get("art"):
                sheets.add(mon["art"])
            clips = {}
            for cm in re.finditer(r"(?:var|exSpriteAnimClip)\s+(\w+)\s*=\s*([^;]*\(\s*sh\w*\s*,\s*\"\w+\"[^;]*);", body, re.S):
                clips[cm.group(1)] = cm.group(2)
            moves, missing, whys = [], [], []
            for am in re.finditer(r"Kit\.Attack\(", body):
                args = MX.split_args(body[am.end():])
                if len(args) < 2:
                    continue
                pre = body[max(0, am.start() - 40):am.start()]
                tag = "special" if re.search(r"(SetSpecial|EnableSpecial)\(\s*\w+\s*,\s*$", pre) else "atk%d" % len([x for x in moves if x["tag"] != "special"])
                cexpr = clips.get(args[1].strip(), args[1])
                spy = Spy({s: s for s in slots})
                fired = fired_slots(body, cexpr, slots)
                zs, isproj, unk = [], False, []
                why = []
                for sv in fired:
                    if sv not in slots:
                        continue
                    en, ox, oy, sp = slots[sv]
                    d = MX.effect_damage(eff.get(en))
                    if en not in rects and not (d[0] or d[1]):
                        why.append(en + ":nodmg"); continue
                    if en in proj or d[2]:
                        isproj = True; why.append(en + ":proj"); continue
                    if sp == "Enemy":
                        why.append(en + ":onhero"); continue
                    r = rects.get(en)
                    if not r:
                        unk.append(en); continue
                    if "--floor" in argv:
                        tier = 3 if (f["evolveCost"] or 0) >= 4 else 2 if (f["evolveCost"] or 0) >= 2 else 1
                        r = floored(r, tier, (eff.get(en) or {}).get("rate", 0) > 0)
                    if feet or sp == "Position":
                        bx, by = ox, oy
                    else:
                        bx, by = node["x"] + ox, node["y"] + oy
                    zs += zone(r, bx, by)
                    for rr in r:
                        EFFECTS.setdefault(en, {"users": set(), "rect": rr, "god": god})["users"].add((f["id"], f["evolveCost"], tag, round(bx), round(by)))
                s = summary(zs)
                if s:
                    s.update(tag=tag, proj=isproj, unk=unk)
                    moves.append(s)
                elif unk:
                    missing += unk
                if not s:
                    whys.append("%s:%s" % (tag, ",".join(why) or "nofire:" + args[1].strip()[:30]))
            out.append({"name": f["id"], "cost": f["evolveCost"], "god": god, "moves": moves, "missing": missing, "why": whys})
    return out


TIER_OF_MOD = {0.0: 0.0, 2.5: 2.5, 4.5: 4.0}    # compare with the game's own tier at that place in a tree


def main():
    van = vanilla_moves()
    P = {d["m_GameObject"]["m_PathID"]: d for d in VA.rows("Player")}
    vnode = {p["_go"]: (p.get("m_attackSpawnNode") or {"x": 1, "y": 0}) for p in P.values()}
    mod = mod_moves(vnode)
    ref = {}
    for m in van:
        t = 4.0 if m["cost"] >= 4 else m["cost"]
        for mv in m["moves"]:
            if mv["proj"]:
                continue
            ref.setdefault((t, mv["tag"] == "special"), []).append(mv)
    def med(t, sp, key):
        xs = [x[key] for x in ref.get((t, sp), [])] or [x[key] for x in ref.get((t, False), [])]
        return statistics.median(xs) if xs else 0
    if "--effects" in argv:
        for en, e in sorted(EFFECTS.items(), key=lambda kv: kv[1]["god"]):
            r = e["rect"]
            tiers = sorted(set(u[1] for u in e["users"] if u[1] is not None))
            print("%-8s %-22s L%d %-4s %s w %5.1f h %5.1f c(%4.1f,%4.1f)  %s" % (e["god"], en, r[5], r[4], (r[6] if len(r) > 6 else "?")[:18].ljust(18),
                  r[1] - r[0], r[3] - r[2], (r[0] + r[1]) / 2, (r[2] + r[3]) / 2,
                  "; ".join("%s t%s %s @(%d,%d)" % u for u in sorted(e["users"], key=str))))
        return
    if "--vanilla" in argv:
        for m in van:
            for mv in m["moves"]:
                print("%-30s c%-4s %-8s reach %5.1f depth %5.1f area %6d %s%s" % (m["name"], m["cost"], mv["tag"], mv["reach"], mv["depth"], mv["area"], "caps " if mv["caps"] else "", "proj" if mv["proj"] else ""))
        for k in sorted(ref):
            print("tier", k, "reach", med(*k, "reach"), "depth", med(*k, "depth"), "area", med(*k, "area"))
        return
    want = None
    if "--id" in argv:
        want = argv[argv.index("--id") + 1]
    flags = []
    for m in mod:
        if want and m["name"] != want:
            continue
        t = TIER_OF_MOD.get(m["cost"])
        if t is None:
            continue
        for mv in m["moves"]:
            if mv["proj"] and mv["area"] == 0:
                continue
            sp = mv["tag"] == "special"
            r, d, a = med(t, sp, "reach"), med(t, sp, "depth"), med(t, sp, "area")
            small = mv["depth"] < 0.75 * d or mv["area"] < 0.6 * a
            line = "%-26s %-8s t%-3s %-8s reach %5.1f/%-5.1f depth %5.1f/%-5.1f area %6d/%-6d %s%s" % (
                m["name"], m["god"], m["cost"], mv["tag"], mv["reach"], r, mv["depth"], d, mv["area"], a,
                "CAPSULE " if mv["caps"] else "", "SMALL" if small else "")
            if small or mv["caps"] or "--all" in argv or want:
                flags.append(line)
        if "--why" in argv and m["why"] and m["cost"] in (2.5, 4.5):
            flags.append("%-26s why: %s" % (m["name"], " | ".join(m["why"])))
        if m["missing"] and (want or "--all" in argv):
            flags.append("%-26s unmeasured: %s" % (m["name"], ", ".join(sorted(set(m["missing"])))))
    print("\n".join(flags))
    print("%d lines; %d mod monsters measured" % (len(flags), len(mod)))


if __name__ == "__main__":
    main()
