#!/usr/bin/env python3
"""Evolution-tree rule (v0.9): per god 3 T1 -> 6 T2 -> 12 T3, every T1/T2 offers exactly two evolutions that no other
monster offers (each evolved monster has exactly one parent), finals evolve no further, costs 0 / 2.5 / 4.5, every
monster has its own art sheet, a tip in data/tips/tips_<god>.json, and no two monsters in a god share a sheet.
Usage: python3 tools/check_trees.py [God ...]   (exit 1 on any problem)"""
import re, os, sys, json, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GODS = {'Vhorrul': 'vhorrul', 'Ossivar': 'ossivar', 'Sylvene': 'sylvene', 'Umbrael': 'umbrael', 'BelMora': 'belmora',
        'Jinx': 'jinx', 'Zhekra': 'zhekra', 'Kaurn': 'kaurn', 'Ysveld': 'ysveld'}
# lines with no god of their own: pack -> (tips file, monsters per tier); the starter is the pack's `Starter = "..."`
EXTRA = {'GoldSecret': ('goldsecret', (1, 2, 4))}
GODS.update({k: v[0] for k, v in EXTRA.items()})
CONTENT = os.path.join(ROOT, 'src', 'CrawlFurther')
TIPS = os.path.join(ROOT, 'data', 'tips')


def pack_path(name):
    """src/CrawlFurther/<area>/.../<name>Pack.cs (gods live under Gods/<God>/, the secret lines under Secrets/)."""
    hits = glob.glob(os.path.join(CONTENT, '**', name + 'Pack.cs'), recursive=True)
    if len(hits) != 1: raise SystemExit('check_trees: %d files named %sPack.cs under %s' % (len(hits), name, CONTENT))
    return hits[0]


def sheet_ids():
    return {os.path.basename(p)[:-5] for p in glob.glob(ROOT + '/art/out*/*.json') + glob.glob(ROOT + '/art/core/*.json')
            if not p.endswith('_preview.json')}


def defs_of(src):
    out = {}
    for m in re.finditer(r'new MonsterDef\s*\{', src):
        k = m.end(); dep = 1
        while dep:
            dep += {'{': 1, '}': -1}.get(src[k], 0); k += 1
        b = src[m.end():k]
        i = re.search(r'\bid = "(\w+)"', b)
        if not i: continue
        a = re.search(r'\bart = "(\w+)"', b)
        c = re.search(r'evolveCost = ([\d.]+)f', b)
        e = re.search(r'evolveTo = new\[\]\s*\{([^}]*)\}', b)
        out[i.group(1)] = dict(art=a.group(1) if a else i.group(1), cost=float(c.group(1)) if c else None,
                               to=[x.strip().strip('"') for x in e.group(1).split(',') if x.strip()] if e else [])
    return out


# packs of "unique finals": tier-3 monsters with NO parent that evolve no further (pack file stem -> tips stem).
# Silver uniques are reached only by the silver ghost's tier-3 orb upgrade (SilverUniques.RollTier3).
# the secret statue monsters (StatuePack.cs) are offered only by secret statues (StatuePlacement).
UNIQUE_FINALS = {'Silver': 'silver', 'Statue': 'statuemon'}


def check_unique_finals(name, all_parents):
    """Every MonsterDef in <name>Pack.cs: cost 4.5, no evolveTo, offered by no monster anywhere, own sheet, tip."""
    sheets = sheet_ids()
    d = defs_of(open(pack_path(name)).read())
    tp = f'{TIPS}/tips_{UNIQUE_FINALS[name]}.json'
    tips = json.load(open(tp)) if os.path.exists(tp) else {}
    probs, arts = [], {}
    for m, v in d.items():
        if v['cost'] is None or abs(v['cost'] - 4.5) > 0.01: probs.append(f'{m} costs {v["cost"]}, a unique final must cost 4.5')
        if v['to']: probs.append(f'unique final {m} evolves {v["to"]}')
        if m in all_parents: probs.append(f'unique final {m} is offered by {all_parents[m]} (must have no parent)')
        if v['art'] not in sheets: probs.append(f'{m}: art sheet {v["art"]} missing')
        if v['art'] in arts: probs.append(f'{m} and {arts[v["art"]]} share the art sheet {v["art"]}')
        arts[v['art']] = m
        if ('Mod' + m) not in tips: probs.append(f'{m}: no tip in {os.path.basename(tp)}')
    print(f'{"OK  " if not probs else "FAIL"} {name:8s} unique finals {len(d)}')
    for p in probs: print('       - ' + p)
    return len(probs)


def main(names):
    sheets = sheet_ids()
    bad = 0
    for g in [n for n in names if n in GODS]:
        src = open(pack_path(g)).read()
        d = defs_of(src)
        st = re.search(r'startingMonsters = new\[\]\s*\{([^}]*)\}', src)
        t1 = [x.strip().strip('"') for x in st.group(1).split(',')] if st else []
        if g in EXTRA:
            st = re.search(r'\bStarter = "(\w+)"', src)
            t1 = [st.group(1)] if st else []
        tips = {}
        tp = f'{TIPS}/tips_{GODS[g]}.json'
        if os.path.exists(tp): tips = json.load(open(tp))
        probs = []
        tiers = [t1]; parent = {}
        for t in range(2):
            nxt = []
            for m in tiers[t]:
                if m not in d: probs.append(f'{m} has no MonsterDef'); continue
                to = d[m]['to']
                if len(to) != 2 or len(set(to)) != 2: probs.append(f'{m} (T{t+1}) offers {to}, must be exactly 2 different')
                for x in to:
                    if x in parent: probs.append(f'{x} is offered by both {parent[x]} and {m} (shared evolution)')
                    else: parent[x] = m
                    if x not in nxt: nxt.append(x)
            tiers.append(nxt)
        shape = EXTRA[g][1] if g in EXTRA else (3, 6, 12)
        for t, want, cost in ((0, shape[0], 0.0), (1, shape[1], 2.5), (2, shape[2], 4.5)):
            if len(tiers[t]) != want: probs.append(f'T{t+1} has {len(tiers[t])} monsters, want {want}')
            for m in tiers[t]:
                if m not in d: probs.append(f'{m} has no MonsterDef'); continue
                if d[m]['cost'] is not None and abs(d[m]['cost'] - cost) > 0.01: probs.append(f'{m} (T{t+1}) costs {d[m]["cost"]}, want {cost}')
                if t == 2 and d[m]['to']: probs.append(f'final {m} still evolves {d[m]["to"]}')
        tree = set(tiers[0]) | set(tiers[1]) | set(tiers[2])
        arts = {}
        for m in tree:
            if m not in d: continue
            a = d[m]['art']
            if a not in sheets: probs.append(f'{m}: art sheet {a} missing')
            if a in arts: probs.append(f'{m} and {arts[a]} share the art sheet {a}')
            arts[a] = m
            if ('Mod' + m) not in tips: probs.append(f'{m}: no tip in data/tips/tips_{GODS[g]}.json')
        for m, v in d.items():
            if v['cost'] is not None and v['cost'] > 0 and m not in tree: probs.append(f'{m} is an evolved tier but not in the tree')
        print(f'{"OK  " if not probs else "FAIL"} {g:8s} T1 {len(tiers[0])} T2 {len(tiers[1])} T3 {len(tiers[2])}')
        for p in probs: print('       - ' + p)
        bad += len(probs)
    if any(n in UNIQUE_FINALS for n in names) or set(names) == set(GODS):
        parents = {}
        for f in glob.glob(CONTENT + '/**/*Pack.cs', recursive=True):
            for m, v in defs_of(open(f).read()).items():
                for x in v['to']: parents[x] = m
        for u in UNIQUE_FINALS:
            if u in names or set(names) == set(GODS): bad += check_unique_finals(u, parents)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:] or list(GODS)))
