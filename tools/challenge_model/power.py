import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA = os.path.join(ROOT, "build", "chal")
os.makedirs(DATA, exist_ok=True)
import json, statistics as st
V = json.load(open(os.path.join(DATA, "vanilla.json")))
M = json.load(open(os.path.join(DATA, "mod.json")))

def vtier(c): return 1 if c < 0.5 else 2 if c < 2 else 3 if c < 4 else 4   # vanilla costs 0, 1, 2.5, 4
def mtier(c): return 1 if (c or 0) < 2 else 3 if c < 4 else 4               # mod costs 0, 2.5, 4.5 -> vanilla 0, 2.5, 4

def basic(m, mult=1.0):
    best, w, rng = 0.0, None, False
    for a in m["attacks"]:
        d = (a["dmg"] + 0.5 * a["linger"]) * mult
        cyc = max(a.get("busy", a["len"]), a["len"]) + a["cd"] * m.get("_cdm", 1.0)
        if cyc > 0 and d / cyc > best:
            best, w = d / cyc, a["windup"]
            rng = (a.get("proj") or 0) > 0 or (a.get("reach") or a.get("rangeOuter") or 0) >= 100
    return best, w, rng

def special(m, charge, mult=1.0):
    sp = m.get("special")
    if not sp or not charge: return 0.0
    return (sp["dmg"] + 0.5 * sp["linger"]) * mult / (charge + sp["len"])

def vanilla_rows():
    out = []
    for m in V:
        b, w, r = basic(m); s = special(m, m["charge"])
        out.append(dict(name=m["name"][5:], tier=vtier(m["cost"]), goal=m["goal"], hp=m["hp"], basic=b, sp=s, windup=w, ranged=r))
    return out

def mod_rows():
    out = []
    for m in M:
        t = mtier(m["evolveCost"])
        dm = m["damageMult"] or 1.0
        m["_cdm"] = m["attackCooldownMult"] or 1.0
        for a in m["attacks"]: a.setdefault("reach", a.get("rangeOuter") or 0)
        b, w, r = basic(m, dm)
        ch = m["specialChargeTime"] or m["charge"]
        if ch and t >= 3 and not m["specialChargeTime"]: ch *= 0.8
        s = special(m, ch, dm)
        out.append(dict(name=m["id"], god=m["god"], tier=t, hp=m["health"] or 0, basic=b, sp=s, windup=w, ranged=r,
                        basic_known=b > 0, sp_known=s > 0, has_sp=bool(m.get("special"))))
    # fill what the parse could not read with the tier's median (marked)
    for t in (1, 3, 4):
        R = [x for x in out if x["tier"] == t]
        mb = st.median([x["basic"] for x in R if x["basic_known"]]); ms = st.median([x["sp"] for x in R if x["sp_known"]])
        mw = st.median([x["windup"] for x in R if x["windup"] is not None])
        for x in R:
            if not x["basic_known"]: x["basic"] = mb
            if not x["sp_known"] and x["has_sp"]: x["sp"] = ms
            if x["windup"] is None: x["windup"] = mw
    return out

def power(x): return x["hp"] * (x["basic"] + x["sp"])
