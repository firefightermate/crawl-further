"""Vanilla vault monsters' combat numbers from the dump: health, speed, attacks (damage per use, windup, clip length,
cooldown, reach), special (damage, charge), and the game's own challenge goal."""
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA = os.path.join(ROOT, "build", "chal")
os.makedirs(DATA, exist_ok=True)
import json, glob, collections, os
DB = os.environ.get("CRAWL_DUMP", os.path.join(ROOT, "build", "dump")) + "/all/db"
def rows(c): return [json.loads(l) for l in open(f"{DB}/sharedassets0__{c}.jsonl")]
H = {int(k): v for k, v in json.load(open(f"{DB}/_hier.json")).items()}
comp = collections.defaultdict(dict)
for f in glob.glob(f"{DB}/sharedassets0__*.jsonl"):
    cls = f.split("__")[1][:-6]
    if cls == "Constants": continue
    for l in open(f):
        d = json.loads(l); g = (d.get("m_GameObject") or {}).get("m_PathID")
        if g: comp[g].setdefault(cls, []).append(d)
CLIP = {d["_pid"]: d for d in rows("exSpriteAnimClip")}

def refs(obj):
    """Every PathID an object's fields point to."""
    out = []
    if isinstance(obj, dict):
        if "m_PathID" in obj and obj.get("m_FileID") == 0 and obj["m_PathID"]: out.append(obj["m_PathID"])
        for k, v in obj.items():
            if k in ("m_GameObject", "m_Script", "m_trailObject"): continue
            out += refs(v)
    elif isinstance(obj, list):
        for v in obj: out += refs(v)
    return out

def effect_damage(g, depth=0, seen=None):
    """Damage an effect GameObject deals: its DamageEffects, its children's, and what it spawns. Returns
    (direct hit damage, lingering dps, projectile speed or 0)."""
    seen = seen if seen is not None else set()
    if g in seen or depth > 5 or g not in H: return 0.0, 0.0, 0.0
    seen.add(g)
    hit, dps, spd = 0.0, 0.0, 0.0
    for de in comp[g].get("DamageEffect", []):
        if de["m_damageRate"] > 0: dps += de["m_damage"] / max(de["m_damageRate"], 0.1)
        else: hit = max(hit, de["m_damage"])
    for pm in comp[g].get("ParticleMotion", []):
        s = pm["m_speed"]; spd = max(spd, s["m_max"] if s["m_hasMax"] else s["m_min"])
    subs = list(H[g].get("c", []))
    for cls in ("Effect", "EffectSpawner", "DamageEffect"):
        for d in comp[g].get(cls, []): subs += [r for r in refs(d) if r in H]
    for s in subs:
        h2, d2, s2 = effect_damage(s, depth + 1, seen)
        hit += h2; dps += d2; spd = max(spd, s2)
    return hit, dps, spd

def clip_info(pid, effects):
    c = CLIP.get(pid)
    if not c: return None
    length = sum(f["length"] for f in c["frameInfos"]) / max(c.get("speed", 1.0), 0.01)
    hits, first, lin, spd = 0.0, None, 0.0, 0.0
    off_time = on_time = None
    for e in c["eventInfos"]:
        m = e["methodName"]
        if m == "AnimAttack" and 0 <= e["intParam"] < len(effects):
            g = effects[e["intParam"]]["m_object"]["m_PathID"]
            h, d, s = effect_damage(g)
            if h or d:
                hits += h; lin += d; spd = max(spd, s)
                if first is None: first = e["time"]
        if m == "AnimInputOff" and off_time is None: off_time = e["time"]
        if m in ("AnimInputOn", "AnimRun") and on_time is None: on_time = e["time"]
    return {"name": c["m_Name"], "len": round(length, 3), "dmg": round(hits, 3), "linger": round(lin, 3),
            "windup": first, "proj": spd, "busy": on_time if on_time is not None else length}

def attack(a, effects):
    ci = clip_info(a["m_animationFront"]["m_PathID"], effects)
    if not ci: return None
    ci.update(cd=a["m_cooldown"], reach=a["m_botData"]["m_rangeOuter"], inner=a["m_botData"]["m_rangeInner"],
              retreat=a["m_botData"]["m_rangeRetreat"])
    return ci

def monster(p):
    g = p["m_GameObject"]["m_PathID"]
    hp = comp[g]["Health"][0]["m_healthMax"]
    mv = comp[g].get("PlayerMovement", [{}])[0]
    eff = p["m_attackDamageEffects"]
    atks = [x for x in (attack(a, eff) for a in p["m_attacks"]) if x]
    sp = attack(p["m_specialAttack"], eff) if p["m_hasSpecialAttack"] else None
    return {"name": p["_go"], "cost": p["m_evolveCost"], "hp": hp, "speed": mv.get("m_speedMax"),
            "attacks": atks, "special": sp, "charge": p["m_specialAttackChargeTime"], "order": p["m_attackOrderType"]}

if __name__ == "__main__":
    P = {d["m_GameObject"]["m_PathID"]: d for d in rows("Player")}
    L = json.loads(open(f"{DB}/sharedassets0__SystemLibrary.jsonl").readline())
    out = []
    for e in L["m_monsters"]:
        p = P.get(e["m_prefab"]["m_PathID"])
        if not p: continue
        m = monster(p); m["goal"] = e["m_targetScore"]; out.append(m)
    json.dump(out, open(os.path.join(DATA, "vanilla.json"), "w"), indent=1)
    for m in out:
        a = m["attacks"][0] if m["attacks"] else {}
        print(f'{m["name"][5:]:26} c{m["cost"]:3} g{m["goal"]:2} hp{m["hp"]:5} spd{m["speed"] or 0:6.1f} ' +
              " | ".join(f'{x["dmg"]}+{x["linger"]}/s w{x["windup"]} len{x["len"]} cd{x["cd"]:.2f} r{x["reach"]:.0f} p{x["proj"]:.0f}' for x in m["attacks"]) +
              (f' || SP {m["special"]["dmg"]}+{m["special"]["linger"]} ch{m["charge"]:.1f} len{m["special"]["len"]}' if m["special"] else ""))
