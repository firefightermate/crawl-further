using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.UI
{
    using CrawlFurther.Art;
    using CrawlFurther.Gods;
    using CrawlFurther.Items;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// The vault (main menu library) entries for mod content: monsters, shop items, weapons, objects, the pages of the
    /// mod categories (<see cref="Vault.AddCategory"/>) and the secrets.
    ///
    /// How it fits Crawl's SystemLibrary (traced from the decompiled code):
    ///  - Entries are appended to the serialized lists (m_monsters / m_weapons / m_items / m_props), the flat m_entryList
    ///    and the m_entries name dictionary. Vanilla entries keep their positions, so nothing vanilla is renumbered.
    ///  - The save is keyed by entry NAME (prefab name + combo/type), not by index: "lib.i.nm" holds the name and the
    ///    loader looks it up. Mod names all start with "Mod", so without the mod those records are simply skipped.
    ///  - Mod content registers late. If a user's save was read before that, the loader skipped the mod records; the
    ///    Sync postfix keeps them aside and they are applied when the entries are added (then saved normally).
    ///  - Completion ratios (vault / weapon vault / challenge achievements) are computed over vanilla entries only.
    ///  - Mod monsters a player can become have the game's own hero challenge (<see cref="Challenges"/>): their
    ///    m_targetScore is their goal, and the game's level, HUD, scoring and save run unchanged. Minions and blobs
    ///    have none (goal <see cref="Challenges.NoGoal"/>), and their Challenge action and label are disabled.
    /// </summary>
    public static class LibraryEntries
    {
        /// <summary>The " (MOD)" tag 0.9.0 put on entry names. Names carry no tag now; it is kept only so that 0.9.0
        /// weapon records ("prefab + combo name (MOD)") still find their entry.</summary>
        public const string OldTag = " (MOD)";

        class Info
        {
            public string name, desc;
            public Info(string n, string d) { name = n; desc = d; }
        }

        // ------------------------------------------------------------------ state
        static SystemLibrary s_registeredInto;
        static readonly HashSet<SystemLibrary.LibraryEntry> s_mod = new HashSet<SystemLibrary.LibraryEntry>();
        /// <summary>Every dictionary key this mod added (entry names + aliases) -> entry.</summary>
        static readonly Dictionary<string, SystemLibrary.LibraryEntry> s_keys = new Dictionary<string, SystemLibrary.LibraryEntry>();
        /// <summary>Monster prefabs that no god's roster or evolution reaches (minions, ghost blobs).</summary>
        static readonly HashSet<GameObject> s_summoned = new HashSet<GameObject>();
        /// <summary>Mod monster entries with a challenge.</summary>
        static readonly HashSet<SystemLibrary.LibraryEntry> s_challenge = new HashSet<SystemLibrary.LibraryEntry>();

        struct SavedRec { public bool found, isNew; public int high, last; }
        /// <summary>uid -> entry name -> record read from a save before the mod entries existed.</summary>
        static readonly Dictionary<string, Dictionary<string, SavedRec>> s_pending = new Dictionary<string, Dictionary<string, SavedRec>>();

        static List<SystemLibrary.LibraryEntry> s_lists;
        static Dictionary<string, SystemLibrary.LibraryEntry> s_dict;
        static List<string> s_users;
        static SystemLibrary s_lib;
        static GameObject s_vaultHolder;

        public static bool IsMod(SystemLibrary.LibraryEntry e) { return e != null && s_mod.Contains(e); }
        public static bool HasModEntries { get { return s_mod.Count > 0; } }
        public static bool IsSummoned(GameObject prefab) { return prefab != null && s_summoned.Contains(prefab); }
        /// <summary>A mod monster entry with a vault challenge.</summary>
        public static bool HasChallenge(SystemLibrary.LibraryEntry e) { return e != null && s_challenge.Contains(e); }
        /// <summary>A mod monster entry the game would offer a challenge for, but which has none (minions, blobs).</summary>
        public static bool NoChallenge(SystemLibrary.LibraryEntry e) { return IsMod(e) && e is SystemLibrary.LibraryEntryMonster && !s_challenge.Contains(e); }

        /// <summary>Called once from ContentManager after every pack has registered.</summary>
        public static void Register()
        {
            if (!Singleton<SystemLibrary>.HasInstance())
            {
                FurtherCore.Log.LogWarning("Library: SystemLibrary not up yet; entries will be added when the vault opens");
                return;
            }
            EnsureRegistered();
        }

        /// <summary>Adds the entries to the current SystemLibrary instance if they are not in it yet (idempotent).</summary>
        public static void EnsureRegistered()
        {
            if (!ContentManager.Registered || !Singleton<SystemLibrary>.HasInstance()) return;
            var lib = Singleton<SystemLibrary>.Instance;
            if (lib == null || lib == s_registeredInto) return;
            s_registeredInto = lib;
            s_mod.Clear(); s_keys.Clear(); s_summoned.Clear(); s_challenge.Clear(); s_pages.Clear(); s_pageInfo.Clear();
            SecretList.Clear(); s_secretOf.Clear(); s_pageOf.Clear();
            try { AddAll(lib); }
            catch (Exception e) { FurtherCore.Log.LogError("Library entries failed: " + e); }
        }

        static void AddAll(SystemLibrary lib)
        {
            var entryList = R.Get<List<SystemLibrary.LibraryEntry>>(lib, "m_entryList");
            var entries = R.Get<Dictionary<string, SystemLibrary.LibraryEntry>>(lib, "m_entries");
            if (entryList == null || entries == null || lib.m_monsters == null || lib.m_items == null || lib.m_weapons == null)
            {
                FurtherCore.Log.LogError("Library: SystemLibrary has not built its lists; no mod entries added");
                return;
            }
            var users = KnownUsers(lib);
            int nm = 0, ni = 0, nw = 0;

            // ---- monsters
            var reach = Reachable();
            foreach (var id in MonsterOrder())
            {
                var p = MonsterFactory.Built[id];
                if (p == null) continue;
                Info info = Lookup(id);
                var e = new SystemLibrary.LibraryEntryMonster
                {
                    m_prefab = p.gameObject,
                    m_type = string.Empty,
                    m_name = info.name,
                    m_description = info.name + "\n" + info.desc,
                    m_portraitOffset = PortraitOffset(p),
                    m_startFound = false,
                    m_targetScore = Challenges.NoGoal,   // set by RefreshChallenges below
                };
                if (!Add(entryList, entries, e, users)) continue;
                lib.m_monsters.Add(e);
                if (!reach.Contains(p.gameObject)) s_summoned.Add(p.gameObject);
                nm++;
            }

            // ---- shop items
            foreach (var kv in ItemRegistry.Items)
            {
                var pu = kv.Value;
                if (pu == null) continue;
                string name = Strip(pu.GetDisplayName());
                if (string.IsNullOrEmpty(name)) name = Words(kv.Key);
                var e = new SystemLibrary.LibraryEntry
                {
                    m_prefab = pu.gameObject,
                    m_type = string.Empty,
                    m_name = name,
                    m_description = Strip(pu.GetDescription()),
                    m_startFound = false,
                };
                if (!Add(entryList, entries, e, users)) continue;
                lib.m_items.Add(e);
                ni++;
            }

            // ---- weapons: keyed like vanilla, prefab name + combo name (Player.EquipWeapon reports both)
            foreach (var kv in ItemRegistry.Weapons)
            {
                var w = kv.Value;
                if (w == null) continue;
                string combo = w.m_combos != null && w.m_combos.Count > 0 ? w.m_combos[0].m_name : string.Empty;
                string name = Strip(!string.IsNullOrEmpty(combo) ? combo : w.m_weaponName);
                if (string.IsNullOrEmpty(name)) name = Words(kv.Key);
                var e = new SystemLibrary.LibraryEntry
                {
                    m_prefab = w.gameObject,
                    m_type = combo ?? string.Empty,
                    m_name = name,
                    m_description = string.Empty,   // vanilla shows the combo's description + "."
                    m_startFound = false,
                    // a weapon equipped without a combo reports the bare prefab name, and 0.9.0 saved the combo name
                    // with the old tag: both keys find this entry
                    m_otherPrefabs = string.IsNullOrEmpty(combo) ? null
                        : new[] { new SystemLibrary.LibraryEntryAdditional { m_prefab = w.gameObject, m_type = string.Empty },
                                  new SystemLibrary.LibraryEntryAdditional { m_prefab = w.gameObject, m_type = combo + OldTag } },
                };
                if (!Add(entryList, entries, e, users)) continue;
                lib.m_weapons.Add(e);
                nw++;
            }

            int np = 0;
            try { np = AddPages(entryList, entries, users); }
            catch (Exception ex) { FurtherCore.Log.LogError("Library category pages: " + ex); }
            s_lists = entryList; s_dict = entries; s_users = users; s_lib = lib;
            foreach (var x in s_extra) { try { AddExtra(lib, x); } catch (Exception ex) { FurtherCore.Log.LogError("Library extra page " + x.name + ": " + ex.Message); } }
            try { SyncSecrets(); }
            catch (Exception ex) { FurtherCore.Log.LogError("Library SECRETS entries: " + ex); }
            FurtherCore.Log.LogInfo("Library: " + SecretList.Count + " secret pages (" + Secrets.All.Count + " registered)");

            ApplyPending();
            try { RefreshChallenges(); } catch (Exception ex) { FurtherCore.Log.LogError("Library challenges: " + ex); }
            try { SystemLibrary.UpdateHasNewEntries(); } catch (Exception ex) { FurtherCore.Log.LogWarning("Library: UpdateHasNewEntries: " + ex.Message); }
            FurtherCore.Log.LogInfo("Library: added " + nm + " monsters (" + s_summoned.Count + " summoned-only), " + ni + " items, " + nw +
                               " weapons, " + np + " category pages for " + users.Count + " user(s). Vanilla: " + (lib.m_monsters.Count - nm) + "/" +
                               (lib.m_items.Count - ni) + "/" + (lib.m_weapons.Count - nw));
        }

        /// <summary>Same key rule as SystemLibrary.GetEntryName.</summary>
        public static string Key(GameObject obj, string type)
        {
            string n = obj != null ? obj.name : null;
            if (n != null && n.EndsWith(")") && n.Length >= 7) n = n.Substring(0, n.Length - 7);
            if (!string.IsNullOrEmpty(type)) return (n ?? string.Empty) + type;
            return n ?? string.Empty;
        }

        static bool Add(List<SystemLibrary.LibraryEntry> list, Dictionary<string, SystemLibrary.LibraryEntry> dict,
                        SystemLibrary.LibraryEntry e, List<string> users)
        {
            string key = Key(e.m_prefab, e.m_type);
            // a clash would make the save count (m_entries.Count) smaller than the list it writes: never add one
            if (string.IsNullOrEmpty(key) || dict.ContainsKey(key))
            {
                FurtherCore.Log.LogWarning("Library: skipped '" + key + "' (empty or already in the library)");
                return false;
            }
            foreach (var u in users) e.CreateSyncData(u);
            dict.Add(key, e);
            s_keys[key] = e;
            if (e.m_otherPrefabs != null)
                foreach (var o in e.m_otherPrefabs)
                {
                    string k = Key(o.m_prefab, o.m_type);
                    if (!string.IsNullOrEmpty(k) && !dict.ContainsKey(k)) { dict.Add(k, e); s_keys[k] = e; }
                }
            list.Add(e);
            s_mod.Add(e);
            return true;
        }

        /// <summary>Every user the library already knows (OnUserAdded only fires for users added after this).</summary>
        static List<string> KnownUsers(SystemLibrary lib)
        {
            var set = new List<string>();
            try
            {
                if (Singleton<SystemUsers>.HasInstance())
                    foreach (var u in Singleton<SystemUsers>.Get.GetUsers())
                        if (u != null && !string.IsNullOrEmpty(u.GetUid()) && !set.Contains(u.GetUid())) set.Add(u.GetUid());
                var stats = R.Get<object>(lib, "m_usersCompletionStats") as IDictionary;
                if (stats != null)
                    foreach (var k in stats.Keys) { var s = k as string; if (!string.IsNullOrEmpty(s) && !set.Contains(s)) set.Add(s); }
                foreach (var k in s_pending.Keys) if (!set.Contains(k)) set.Add(k);
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Library: user scan: " + e.Message); }
            return set;
        }

        /// <summary>Monster prefabs a player can become: every god's starters and everything they evolve into.</summary>
        static HashSet<GameObject> Reachable()
        {
            var set = new HashSet<GameObject>();
            var todo = new Stack<Player>();
            try
            {
                var gods = SystemDeity.GetDeities();
                if (gods != null)
                    foreach (var d in gods)
                    {
                        var starters = d != null ? d.GetStartingMonsters() : null;
                        if (starters == null) continue;
                        foreach (var go in starters) if (go != null) { var p = go.GetComponent<Player>(); if (p != null) todo.Push(p); }
                    }
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Library: roster scan: " + e.Message); }
            while (todo.Count > 0)
            {
                var p = todo.Pop();
                if (p == null || !set.Add(p.gameObject)) continue;
                var next = p.GetEvolveTo();
                if (next != null) foreach (var n in next) if (n != null && !set.Contains(n.gameObject)) todo.Push(n);
            }
            return set;
        }

        // ------------------------------------------------------------------ challenges
        /// <summary>Monster prefabs a player can become: <see cref="Reachable"/>, plus every secret monster and what it
        /// evolves into (no god's roster offers those).</summary>
        static HashSet<GameObject> Playable()
        {
            var set = Reachable();
            var todo = new Stack<Player>();
            foreach (var se in Secrets.All)
            {
                var p = SecretMonster(se);
                if (p != null) todo.Push(p);
            }
            while (todo.Count > 0)
            {
                var p = todo.Pop();
                if (p == null || !set.Add(p.gameObject)) continue;
                var next = p.GetEvolveTo();
                if (next != null) foreach (var n in next) if (n != null && !set.Contains(n.gameObject)) todo.Push(n);
            }
            return set;
        }

        /// <summary>The built mod monster a secret stands for, or null: a monster secret (<see cref="Secrets.AddMonster"/>)
        /// or any secret whose id is a mod monster's prefab name (the secret statues register theirs that way).</summary>
        public static Player SecretMonster(SecretDef se)
        {
            if (se == null || string.IsNullOrEmpty(se.id)) return null;
            bool prefabId = se.id.StartsWith("Mod", StringComparison.Ordinal);
            if (!se.monster && !prefabId) return null;
            Player p;
            return MonsterFactory.Built.TryGetValue(prefabId ? se.id.Substring(3) : se.id, out p) ? p : null;
        }

        /// <summary>Give every mod monster entry its challenge goal (<see cref="Challenges.GoalOf"/>) or none. Runs when
        /// the entries are added and whenever the vault opens (secrets and challenge defs may register late).</summary>
        public static void RefreshChallenges()
        {
            if (s_lib == null) return;
            var playable = Playable();
            s_challenge.Clear();
            foreach (var m in s_lib.m_monsters)
            {
                if (m == null || !s_mod.Contains(m) || m.m_prefab == null) continue;
                int goal = Challenges.GoalOf(m.m_prefab.GetComponent<Player>(), playable.Contains(m.m_prefab));
                m.m_targetScore = goal > 0 ? goal : Challenges.NoGoal;
                if (goal > 0) s_challenge.Add(m);
            }
        }

        /// <summary>Mod challenges passed (high score at or above the goal) by the primary user. The vault summary adds
        /// them to the game's own count. Achievements never see them.</summary>
        internal static int ModChallengesPassed()
        {
            int n = 0;
            foreach (var e in s_challenge)
            {
                var m = e as SystemLibrary.LibraryEntryMonster;
                if (m != null && m.GetHighScore(string.Empty) >= m.m_targetScore) n++;
            }
            return n;
        }

        /// <summary>
        /// The challenge lines of a mod monster's vault page, as the game words them for its own monsters, most important
        /// first, each with its place on the page: the score from the vault's own strings (best attempt first, then the
        /// last), the "-PASSED-" line once passed and the "CHALLENGE" heading, both read from the vault's own text
        /// objects so a translation shows. Empty for an entry without a challenge.
        /// </summary>
        internal static List<KeyValuePair<int, string>> ChallengeLines(MenuLibrary lib, SystemLibrary.LibraryEntryMonster e)
        {
            var list = new List<KeyValuePair<int, string>>();
            if (lib == null || !HasChallenge(e)) return list;
            int high = e.GetHighScore(string.Empty);
            bool hidePassed = Singleton<SystemDebug>.HasInstance() && Singleton<SystemDebug>.Get.m_challengeModeHidePassedFeature;
            bool passed = !hidePassed && high > 0 && high >= e.m_targetScore;
            string score;
            if (high == 0) score = R.Get<string>(lib, "m_stringHeroChallengeNotAttempted");
            else
            {
                string fmt = R.Get<string>(lib, "m_stringHeroChallenge") ?? string.Empty;
                try { score = string.Format(fmt, e.GetLastScore(), high); }
                catch (FormatException) { score = fmt; }
            }
            var rows = new List<string>();
            foreach (var r in (score ?? string.Empty).Replace("\r", string.Empty).Split('\n')) if (r.Trim().Length > 0) rows.Add(r.Trim());
            const int Heading = 0, Passed = 1, Score = 2;
            // the game's score text ends with the best attempt: that row first, then the rest
            if (rows.Count > 0) list.Add(new KeyValuePair<int, string>(Score + rows.Count - 1, rows[rows.Count - 1]));
            var normal = Headings(R.Get<GUIText>(lib, "m_textDescriptionMonster"));
            if (passed)
                foreach (var h in Headings(R.Get<GUIText>(lib, "m_textDescriptionMonsterPassed")))
                    if (!normal.Contains(h)) list.Add(new KeyValuePair<int, string>(Passed, h));
            for (int i = 0; i < rows.Count - 1; i++) list.Add(new KeyValuePair<int, string>(Score + i, rows[i]));
            if (normal.Count > 0) list.Add(new KeyValuePair<int, string>(Heading, normal[0]));
            return list;
        }

        /// <summary>The texts drawn above a vault challenge text, top to bottom, as they read now.</summary>
        static List<string> Headings(GUIText holder)
        {
            var found = new List<KeyValuePair<float, string>>();
            if (holder != null)
                foreach (var tm in holder.GetComponentsInChildren<TextMesh>(true))
                {
                    if (tm == null || tm.gameObject == holder.gameObject || string.IsNullOrEmpty(tm.text)) continue;
                    float y = holder.transform.InverseTransformPoint(tm.transform.position).y;
                    found.Add(new KeyValuePair<float, string>(y, tm.text.Replace("\r", string.Empty).Trim()));
                }
            found.Sort((a, b) => b.Key.CompareTo(a.Key));
            var list = new List<string>();
            foreach (var kv in found) if (kv.Value.Length > 0) list.Add(kv.Value);
            return list;
        }

        /// <summary>
        /// Self-test of the challenges: every built mod monster has its vault entry, found by the lookups the game's
        /// challenge uses (the prefab for the level, HUD and score, the name for the save), and has a goal exactly when
        /// a player can become it or its <see cref="ChallengeDef"/> says so.
        /// </summary>
        public static void ChallengeSelfCheck(Action<string> bad, Action<string> note)
        {
            foreach (var f in new[] { "m_stringHeroChallenge", "m_stringHeroChallengeNotAttempted", "m_stringMonstersCategorySummary",
                                      "m_textDescriptionMonster", "m_textDescriptionMonsterPassed", "m_selectedCategory", "m_menuItemsMonster" })
                if (AccessTools.Field(typeof(MenuLibrary), f) == null) bad("MenuLibrary." + f + " not found (mod monster challenge pages)");
            if (AccessTools.Method(typeof(MenuLibrary), "StartChallenge") == null) bad("MenuLibrary.StartChallenge not found");
            if (AccessTools.Method(typeof(AchievementBase), "Unlock") == null) bad("AchievementBase.Unlock not found (no achievements in mod challenges)");
            if (AccessTools.Field(typeof(Player), "m_evolveCost") == null) bad("Player.m_evolveCost not found (challenge goals by cost)");
            if (s_lib == null || !Singleton<SystemLibrary>.HasInstance())
            {
                note("the vault is not built yet: challenges are given when it is");
                return;
            }
            var playable = Playable();
            int with = 0, without = 0;
            var goals = new SortedDictionary<int, int>();
            foreach (var kv in MonsterFactory.Built)
            {
                var p = kv.Value;
                if (p == null) continue;
                string label = p.gameObject.name;
                if (!label.StartsWith("Mod", StringComparison.Ordinal)) bad(label + ": prefab name does not start with Mod (its save key would not be a mod key)");
                var e = SystemLibrary.GetMonsterEntry(p.gameObject);
                if (e == null) { bad(label + ": no vault entry, so no challenge"); continue; }
                if (!IsMod(e)) bad(label + ": its vault entry is not a mod entry");
                if (e.m_prefab == null || e.m_prefab.GetComponent<Player>() != p) bad(label + ": its vault entry does not resolve to its prefab");
                if (SystemLibrary.GetLibraryEntry(p.gameObject) != e) bad(label + ": its save key does not find its vault entry");
                bool want = Challenges.GoalOf(p, playable.Contains(p.gameObject)) > 0;
                if (want != HasChallenge(e)) bad(label + (want ? ": should have a challenge but has none" : ": has a challenge it should not have"));
                if (HasChallenge(e))
                {
                    with++;
                    if (e.m_targetScore < 1 || e.m_targetScore > Challenges.MaxGoal) bad(label + ": challenge goal " + e.m_targetScore + " is out of range");
                    int c; goals.TryGetValue(e.m_targetScore, out c); goals[e.m_targetScore] = c + 1;
                }
                else
                {
                    without++;
                    if (e.m_targetScore != Challenges.NoGoal) bad(label + ": no challenge, but its goal is " + e.m_targetScore);
                }
            }
            var by = new List<string>();
            foreach (var g in goals) by.Add("level " + g.Key + " x" + g.Value);
            note(with + " mod monsters have a challenge (" + string.Join(", ", by.ToArray()) + "), " + without + " have none (minions and blobs)");
        }

        /// <summary>
        /// The MONSTERS order: the monsters with a <see cref="Vault.AddMonsterLine"/> line in the order added; after each
        /// tip group's block, that group's monsters whose line comes from their tip (in tip order), so the grid stays
        /// grouped; then monsters of groups with no block of their own, then anything else.
        /// </summary>
        static List<string> MonsterOrder()
        {
            var order = new List<string>();
            var seen = new HashSet<string>();
            string block = null;
            foreach (var m in Vault.MonsterLines)
            {
                string g = GroupOf(m.id);
                if (g != block) { if (block != null) AddFromTips(order, seen, block); block = g; }
                if (MonsterFactory.Built.ContainsKey(m.id) && seen.Add(m.id)) order.Add(m.id);
            }
            if (block != null) AddFromTips(order, seen, block);
            AddFromTips(order, seen, null);
            foreach (var id in MonsterFactory.Built.Keys) if (seen.Add(id)) order.Add(id);
            return order;
        }

        /// <summary>The tip group of a monster id ("ysveld", "ghosts"...), null if none.</summary>
        static string GroupOf(string id)
        {
            string g;
            return TipRegistry.Group.TryGetValue("Mod" + id, out g) ? g : null;
        }

        /// <summary>Append the built monsters with a tip vault line from <paramref name="group"/> (null: every group) that
        /// are not listed yet, in tip order.</summary>
        static void AddFromTips(List<string> order, HashSet<string> seen, string group)
        {
            foreach (var key in TipRegistry.VaultOrder)
            {
                if (key == null || !key.StartsWith("Mod", StringComparison.Ordinal)) continue;
                string g;
                if (group != null && (!TipRegistry.Group.TryGetValue(key, out g) || g != group)) continue;
                string id = key.Substring(3);
                if (MonsterFactory.Built.ContainsKey(id) && seen.Add(id)) order.Add(id);
            }
        }

        /// <summary>The <see cref="Vault.AddMonsterLine"/> line, else a VaultRegistry monster entry, else the tip's vault
        /// line, else the tip's name and moves (never an id-derived name when a tip exists).</summary>
        static Info Lookup(string id)
        {
            foreach (var m in Vault.MonsterLines) if (m.id == id) return new Info(m.name, m.line);
            var reg = Registered("Monsters", id);
            if (reg != null && !string.IsNullOrEmpty(reg.name)) return new Info(reg.name, reg.text ?? string.Empty);
            KeyValuePair<string, string> v;
            if (TipRegistry.Vault.TryGetValue("Mod" + id, out v) && !string.IsNullOrEmpty(v.Key)) return new Info(v.Key, v.Value);
            MonsterTip t;
            if (TipRegistry.TryGet("Mod" + id, out t) && !string.IsNullOrEmpty(t.name))
            {
                FurtherCore.Log.LogWarning("Library: no vault text for " + id + ", using its monster tip");
                string desc = t.attack + (string.IsNullOrEmpty(t.special) || t.special.StartsWith("none") ? "" : ". " + t.special);
                return new Info(t.name, desc);
            }
            FurtherCore.Log.LogWarning("Library: no vault text for " + id);
            return new Info(Words(id), string.Empty);
        }

        /// <summary>The anim a vault page shows from a sheet: "Portrait", else "Vault" (the ObjectKit convention for
        /// objects), else "Idle" (frame 0 for silhouettes); null if the sheet has none of them.</summary>
        public static string PictureAnim(SpriteSheet sh)
        {
            if (sh == null) return null;
            foreach (var a in new[] { "Portrait", "Vault", "Idle" }) if (sh.Has(a)) return a;
            return null;
        }

        /// <summary>A built mod monster's vault name and line, by MonsterDef id.</summary>
        public static void MonsterInfo(string id, out string name, out string text)
        {
            var i = Lookup(id);
            name = i.name; text = i.desc;
        }

        /// <summary>A VaultRegistry entry for a monster id ("Wickling" or its prefab name "ModWickling"), or null.</summary>
        static VaultRegistry.Entry Registered(string category, string id)
        {
            foreach (var e in VaultRegistry.Entries)
                if (e != null && e.category == category && (e.id == id || e.id == "Mod" + id)) return e;
            return null;
        }

        // ------------------------------------------------------------------ mod categories
        class PageInfo { public VaultCategory cat; public VaultPage page; public string text; }
        static readonly Dictionary<VaultCategory, List<SystemLibrary.LibraryEntry>> s_pages = new Dictionary<VaultCategory, List<SystemLibrary.LibraryEntry>>();
        static readonly Dictionary<SystemLibrary.LibraryEntry, PageInfo> s_pageInfo = new Dictionary<SystemLibrary.LibraryEntry, PageInfo>();
        static readonly List<SystemLibrary.LibraryEntry> s_none = new List<SystemLibrary.LibraryEntry>();

        /// <summary>The entries of a mod category (the secret pages for a secrets category), in grid order.</summary>
        public static List<SystemLibrary.LibraryEntry> EntriesOf(VaultCategory c)
        {
            if (c == null) return s_none;
            if (c.secrets) return SecretList;
            List<SystemLibrary.LibraryEntry> l;
            return s_pages.TryGetValue(c, out l) ? l : s_none;
        }

        /// <summary>A mod category's pages and the entries made for them, for self-checks.</summary>
        public static List<KeyValuePair<VaultPage, SystemLibrary.LibraryEntry>> PagesOf(VaultCategory c)
        {
            var list = new List<KeyValuePair<VaultPage, SystemLibrary.LibraryEntry>>();
            foreach (var e in EntriesOf(c))
            {
                PageInfo pi;
                if (s_pageInfo.TryGetValue(e, out pi)) list.Add(new KeyValuePair<VaultPage, SystemLibrary.LibraryEntry>(pi.page, e));
            }
            return list;
        }

        static int AddPages(List<SystemLibrary.LibraryEntry> list, Dictionary<string, SystemLibrary.LibraryEntry> dict, List<string> users)
        {
            int n = 0;
            foreach (var c in Vault.Categories)
            {
                if (c.secrets || c.pages == null) continue;
                var mine = new List<SystemLibrary.LibraryEntry>();
                s_pages[c] = mine;
                var names = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
                IEnumerable<VaultPage> pages;
                try { pages = c.pages(); }
                catch (Exception e) { FurtherCore.Log.LogError("Vault " + c.label + " pages: " + e); continue; }
                if (pages == null) continue;
                foreach (var p in pages)
                {
                    var e = AddPage(list, dict, users, names, c, p);
                    if (e == null) continue;
                    mine.Add(e);
                    n++;
                }
            }
            return n;
        }

        /// <summary>One page, keyed by a small inactive holder object named "ModVault" + kind + id (saves are keyed by
        /// name, so a save without the mod skips it). Pages start found.</summary>
        static SystemLibrary.LibraryEntry AddPage(List<SystemLibrary.LibraryEntry> list, Dictionary<string, SystemLibrary.LibraryEntry> dict,
                                                  List<string> users, HashSet<string> names, VaultCategory cat, VaultPage p)
        {
            if (p == null || string.IsNullOrEmpty(p.id) || string.IsNullOrEmpty(p.name) || !names.Add(p.name)) return null;
            var go = Holder(KeyName("ModVault" + p.kind, p.id));
            var e = new SystemLibrary.LibraryEntry
            {
                m_prefab = go,
                m_type = string.Empty,
                m_name = p.name,
                m_description = p.text ?? string.Empty,
                m_portrait = PageClip(p.art, "ModVault_" + go.name),
                m_startFound = true,
            };
            if (!Add(list, dict, e, users)) return null;
            s_pageInfo[e] = new PageInfo { cat = cat, page = p, text = e.m_description };
            return e;
        }

        static string KeyName(string prefix, string id)
        {
            var key = new System.Text.StringBuilder(prefix);
            foreach (char c in id) if (char.IsLetterOrDigit(c)) key.Append(c);
            return key.ToString();
        }

        static GameObject Holder(string name)
        {
            if (s_vaultHolder == null)
            {
                s_vaultHolder = new GameObject("CrawlMod_VaultEntries");
                s_vaultHolder.SetActive(false);
                UnityEngine.Object.DontDestroyOnLoad(s_vaultHolder);
            }
            var go = new GameObject(name);
            go.transform.SetParent(s_vaultHolder.transform, false);
            return go;
        }

        static exSpriteAnimClip PageClip(string art, string clipName)
        {
            var sheet = string.IsNullOrEmpty(art) ? null : SpriteSheets.Get(art);
            if (sheet == null || sheet.atlas == null || sheet.atlas.texture == null) return null;
            string anim = PictureAnim(sheet);
            var clip = anim != null ? SpriteSheets.MakeClip(sheet, anim, null, clipName) : null;
            if (clip != null) clip.wrapMode = WrapMode.Loop;
            return clip;
        }

        /// <summary>Is this mod category page locked (its challenge not done yet)?</summary>
        public static bool IsLocked(SystemLibrary.LibraryEntry e)
        {
            PageInfo pi;
            if (e == null || !s_pageInfo.TryGetValue(e, out pi)) return false;
            if (pi.page.locked != null) { try { return pi.page.locked(); } catch { return false; } }
            return pi.page.unlock != null && !Unlocks.IsUnlocked(pi.page.unlock);
        }

        /// <summary>Before a category grid opens: rebuild any picture something destroyed (never show a dead clip), and
        /// give locked pages their challenge and progress.</summary>
        public static void RefreshPages(VaultCategory c)
        {
            foreach (var e in EntriesOf(c))
            {
                PageInfo pi;
                if (!s_pageInfo.TryGetValue(e, out pi)) continue;
                if (!VaultGrid.Alive(e.m_portrait)) e.m_portrait = PageClip(pi.page.art, "ModVault_" + pi.page.kind + pi.page.id);
                string d = pi.text;
                if (IsLocked(e) && pi.page.unlock != null)
                {
                    var u = Unlocks.Find(pi.page.unlock);
                    d = "LOCKED" + (u != null && !string.IsNullOrEmpty(u.title) ? ": " + u.title : "") + "\n" + Unlocks.ProgressText(pi.page.unlock) + "\n" + d;
                }
                e.m_description = d;
            }
        }

        public static bool HasNew(VaultCategory c)
        {
            if (c != null && c.secrets) return SecretsHaveNew();
            try { foreach (var e in EntriesOf(c)) if (e.IsNew(string.Empty)) return true; }
            catch { }
            return false;
        }

        /// <summary>
        /// Self-test of the mod category pages: no two pages share a name, key or picture, each has its text, and each
        /// picture's clip really is its sheet. Then each category's own <see cref="VaultCategory.selfCheck"/>.
        /// </summary>
        public static void SelfCheck(Action<string> bad)
        {
            foreach (var c in Vault.Categories)
            {
                if (c.secrets) continue;
                var seenName = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
                var seenKey = new HashSet<string>();
                var seenArt = new HashSet<string>();
                foreach (var kv in PagesOf(c))
                {
                    var p = kv.Key; var e = kv.Value;
                    string label = c.label + " " + p.kind + " " + p.id;
                    if (string.IsNullOrEmpty(e.m_name)) bad(label + ": no name");
                    if (!seenName.Add(e.m_name ?? "")) bad(label + ": name '" + e.m_name + "' used twice");
                    if (e.m_prefab == null || !seenKey.Add(e.m_prefab.name)) bad(label + ": missing or repeated key");
                    if (string.IsNullOrEmpty(p.text)) bad(label + ": no text");
                    if (string.IsNullOrEmpty(p.art)) continue;
                    if (!seenArt.Add(p.art)) bad(label + ": picture " + p.art + " also used by another page");
                    var sh = SpriteSheets.Get(p.art);
                    if (sh != null && (e.m_portrait == null || e.m_portrait.frameInfos.Count == 0 || e.m_portrait.frameInfos[0].atlas != sh.atlas))
                        bad(label + ": picture clip is not " + p.art);
                }
                if (c.selfCheck != null) c.selfCheck(bad);
            }
        }

        // ------------------------------------------------------------------ extra ITEMS / OBJECTS pages
        class Extra { public GameObject prefab; public string name, desc; public exSpriteAnimClip portrait; public Vector2 offset; public bool obj; }
        static readonly List<Extra> s_extra = new List<Extra>();

        internal static void AddExtra(GameObject prefab, string name, string description, exSpriteAnimClip portrait, Vector2 portraitOffset, bool isObject)
        {
            if (prefab == null) return;
            var x = new Extra { prefab = prefab, name = isObject ? name : Strip(name), desc = isObject ? description : Strip(description), portrait = portrait, offset = portraitOffset, obj = isObject };
            s_extra.Add(x);
            if (s_lib != null) AddExtra(s_lib, x);
        }

        static void AddExtra(SystemLibrary lib, Extra x)
        {
            if (s_lists == null || s_dict == null) return;
            var e = new SystemLibrary.LibraryEntry
            {
                m_prefab = x.prefab, m_type = string.Empty,
                m_name = string.IsNullOrEmpty(x.name) ? Words(x.prefab.name.StartsWith("Mod") ? x.prefab.name.Substring(3) : x.prefab.name) : x.name,
                m_description = x.desc ?? string.Empty, m_portrait = x.portrait, m_portraitOffset = x.offset, m_startFound = false,
            };
            if (!Add(s_lists, s_dict, e, s_users)) return;
            if (x.obj) lib.m_props.Add(e); else lib.m_items.Add(e);
            ApplyPending();
        }

        public static int ExtraObjects { get { int n = 0; foreach (var x in s_extra) if (x.obj) n++; return n; } }

        // ------------------------------------------------------------------ secrets
        /// <summary>The secret pages: one per <see cref="Secrets"/> entry, in <see cref="Secrets.Ordered"/> order. Library-wise
        /// every page is found (so the vault shows its text); unfound shows a silhouette of the picture, the group's hidden
        /// title and the riddle and rarity; found shows the picture, the real name and the text. Keyed "ModSecret" + id.</summary>
        public static readonly List<SystemLibrary.LibraryEntry> SecretList = new List<SystemLibrary.LibraryEntry>();
        static readonly Dictionary<SystemLibrary.LibraryEntry, string> s_secretOf = new Dictionary<SystemLibrary.LibraryEntry, string>();
        static readonly Dictionary<string, SystemLibrary.LibraryEntry> s_pageOf = new Dictionary<string, SystemLibrary.LibraryEntry>();
        static readonly Dictionary<string, exSpriteAnimClip> s_secretClip = new Dictionary<string, exSpriteAnimClip>();

        public static string SecretOf(SystemLibrary.LibraryEntry e) { string id; return e != null && s_secretOf.TryGetValue(e, out id) ? id : null; }

        /// <summary>Make a page for every registered secret that has none yet (secrets may register late), then put the
        /// pages in vault order. Called at registration and whenever a secrets grid opens.</summary>
        public static void SyncSecrets()
        {
            if (s_lists == null || s_dict == null) return;
            if (Secrets.OnFound == null) Secrets.OnFound = OnSecretFound;
            foreach (var se in Secrets.All)
            {
                if (se == null || string.IsNullOrEmpty(se.id) || s_pageOf.ContainsKey(se.id)) continue;
                var go = Holder(KeyName("ModSecret", se.id));
                var e = new SystemLibrary.LibraryEntry { m_prefab = go, m_type = string.Empty, m_name = se.name, m_description = se.text, m_startFound = true };
                if (!Add(s_lists, s_dict, e, s_users)) continue;
                s_secretOf[e] = se.id;
                s_pageOf[se.id] = e;
                // a secret that is still hidden has no red dot; one found before this page existed gets one
                foreach (var d in e.m_usersSyncData.Values) d.m_new = Secrets.IsFound(se.id);
            }
            SecretList.Clear();
            foreach (var se in Secrets.Ordered()) { SystemLibrary.LibraryEntry e; if (s_pageOf.TryGetValue(se.id, out e)) SecretList.Add(e); }
            RefreshSecrets();
        }

        /// <summary>Each page's name, text and picture for the secret's current state.</summary>
        public static void RefreshSecrets()
        {
            foreach (var e in SecretList)
            {
                var se = Secrets.Find(SecretOf(e));
                if (se == null) continue;
                bool found = Secrets.IsFound(se.id);
                foreach (var d in e.m_usersSyncData.Values) d.m_found = true;
                e.m_name = found ? se.name : Secrets.HiddenTitle(se.group);
                e.m_description = found ? se.text : se.riddle + "\n" + se.rarity;
                e.m_portrait = SecretClip(se, !found);
            }
        }

        static void OnSecretFound(string id)
        {
            SystemLibrary.LibraryEntry e;
            if (!s_pageOf.TryGetValue(id, out e)) { SyncSecrets(); if (!s_pageOf.TryGetValue(id, out e)) return; }
            foreach (var d in e.m_usersSyncData.Values) d.m_new = true;
            RefreshSecrets();
            try { SystemLibrary.UpdateHasNewEntries(); } catch { }
        }

        public static bool SecretsHaveNew()
        {
            try { foreach (var e in SecretList) if (Secrets.IsFound(SecretOf(e)) && e.IsNew(string.Empty)) return true; }
            catch { }
            return false;
        }

        /// <summary>The secret's picture (Portrait, else Vault, else Idle), or its silhouette. Built once per secret and kept.</summary>
        static exSpriteAnimClip SecretClip(SecretDef se, bool silhouette)
        {
            string k = se.id + (silhouette ? "#sil" : "");
            exSpriteAnimClip c;
            if (s_secretClip.TryGetValue(k, out c) && VaultGrid.Alive(c)) return c;
            c = null;
            var sh = string.IsNullOrEmpty(se.iconSheet) ? null : SpriteSheets.Get(se.iconSheet);
            if (sh != null && sh.atlas != null && sh.atlas.texture != null)
            {
                string anim = PictureAnim(sh);
                if (anim != null)
                {
                    if (!silhouette) { c = SpriteSheets.MakeClip(sh, anim, null, "ModSecret_" + se.id); if (c != null) c.wrapMode = WrapMode.Loop; }
                    else c = Silhouette.Clip(sh, sh.Anim(anim).frames[0], "ModSecretSil_" + se.id);
                }
            }
            if (c == null)
            {
                // no picture: the drawn sealed "?" (VaultIcons)
                var ic = SpriteSheets.Get("VaultIcons");
                if (ic != null && ic.Has("Undiscovered")) c = SpriteSheets.MakeClip(ic, silhouette ? "Undiscovered" : "NoArt", null, "ModSecretIcon_" + se.id);
            }
            s_secretClip[k] = c;
            return c;
        }

        static string Strip(string s) { return string.IsNullOrEmpty(s) ? s : s.Trim(); }

        /// <summary>"RivetImp" -> "Rivet Imp": a fallback name for content with none.</summary>
        static string Words(string id)
        {
            if (string.IsNullOrEmpty(id)) return id;
            var sb = new System.Text.StringBuilder();
            for (int i = 0; i < id.Length; i++)
            {
                if (i > 0 && char.IsUpper(id[i]) && !char.IsUpper(id[i - 1])) sb.Append(' ');
                sb.Append(id[i]);
            }
            return sb.ToString();
        }

        /// <summary>
        /// MenuLibrary draws a monster's Run frame 0 at the prefab sprite's offset/anchor, then (BotCenter anchor) lowers it
        /// by half the frame's trimmed height. Vanilla frames are trimmed to the body, so that centres the body. Mod cells
        /// are untrimmed (the whole cell), so the body would sit wherever it happens to be in its cell. Return the
        /// m_portraitOffset that puts the body's opaque bounds where vanilla puts a body: centred on (0, -1).
        /// </summary>
        static Vector2 PortraitOffset(Player p)
        {
            try
            {
                var spr = p.GetComponent<exSprite>();
                var run = R.Get<exSpriteAnimClip>(p, "m_animationRun");
                if (spr == null || run == null || run.frameInfos == null || run.frameInfos.Count == 0) return Vector2.zero;
                var f0 = run.frameInfos[0];
                var sheet = SpriteSheets.ByAtlas(f0.atlas);
                if (sheet == null || f0.atlas.elements == null || f0.index < 0 || f0.index >= f0.atlas.elements.Length) return Vector2.zero;
                int bx, by, bw, bh;
                if (!MonsterFactory.Bounds(sheet, f0.index, out bx, out by, out bw, out bh)) return Vector2.zero;
                var el = f0.atlas.elements[f0.index];
                float W = el.trimRect.width, H = el.trimRect.height;   // = the cell (SpriteSheets makes untrimmed elements)
                int a = (int)spr.anchor;
                float fx = new[] { 0f, 0.5f, 1f }[a % 3];               // left / centre / right
                float fy = new[] { 1f, 0.5f, 0f }[Mathf.Clamp(a / 3, 0, 2)];   // top / mid / bottom
                float shift = spr.anchor == exPlane.Anchor.BotCenter ? -H * 0.5f : 0f;
                // the quad's bottom-left lands at offset - (W fx, H fy); pick it so the body centre sits on (0, -1),
                // on whole pixels
                float left = Mathf.Round(0f - (bx + bw * 0.5f));
                float bottom = Mathf.Round(-1f - (by + bh * 0.5f));
                var want = new Vector2(left + W * fx, bottom + H * fy);
                return want - spr.offset - new Vector2(0f, shift);
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Library portrait " + p.name + ": " + e.Message); return Vector2.zero; }
        }

        // ------------------------------------------------------------------ saves
        /// <summary>Loader postfix: keep mod records the vanilla loader could not place (entries not added yet).</summary>
        internal static void OnLoaded(SystemLibrary lib, SaveHelper file)
        {
            // entries already in this library: the vanilla loader placed every record it knows; the rest name
            // content this version of the mod no longer has, and stay unread (as vanilla does with unknown names)
            if (s_registeredInto == lib && HasModEntries) return;
            var ud = file.GetUserData();
            if (ud == null) return;
            string uid = ud.GetUid();
            if (string.IsNullOrEmpty(uid)) return;
            var entries = R.Get<Dictionary<string, SystemLibrary.LibraryEntry>>(lib, "m_entries");
            int count = 0;
            file.Sync("lib.count", ref count);
            s_pending.Remove(uid);   // a newer load of this user replaces whatever was kept from an older one
            Dictionary<string, SavedRec> recs = null;
            for (int i = 0; i < count; i++)
            {
                string prefix = "lib." + i;
                string name = null;
                file.Sync(prefix + ".nm", ref name);
                if (string.IsNullOrEmpty(name) || !name.StartsWith("Mod")) continue;
                if (entries != null && entries.ContainsKey(name)) continue;   // vanilla loader already filled it in
                var r = new SavedRec { found = false, isNew = true };
                file.Sync(prefix + ".f", ref r.found);
                file.Sync(prefix + ".n", ref r.isNew);
                file.Sync(prefix + ".hs", ref r.high);
                file.Sync(prefix + ".ls", ref r.last);
                if (recs == null) { recs = new Dictionary<string, SavedRec>(); s_pending[uid] = recs; }
                recs[name] = r;
            }
            if (recs != null) FurtherCore.Log.LogInfo("Library: kept " + recs.Count + " mod records from " + uid + "'s save until the entries exist");
        }

        static void ApplyPending()
        {
            if (s_pending.Count == 0) return;
            int n = 0;
            foreach (var u in s_pending)
            {
                string uid = u.Key;
                var applied = new List<string>();
                foreach (var kv in u.Value)
                {
                    SystemLibrary.LibraryEntry e;
                    if (!s_keys.TryGetValue(kv.Key, out e)) continue;   // content no longer in the mod: leave it unread
                    if (!e.m_usersSyncData.ContainsKey(uid)) e.CreateSyncData(uid);
                    var d = e.m_usersSyncData[uid];
                    d.m_found = kv.Value.found;
                    d.m_new = kv.Value.isNew;
                    var m = e as SystemLibrary.LibraryEntryMonster;
                    if (m != null && m.m_usersMonsterSyncData.ContainsKey(uid))
                    {
                        m.m_usersMonsterSyncData[uid].m_highScore = kv.Value.high;
                        m.m_usersMonsterSyncData[uid].m_lastScore = kv.Value.last;
                    }
                    applied.Add(kv.Key);
                    n++;
                }
                foreach (var k in applied) u.Value.Remove(k);
            }
            if (n > 0) FurtherCore.Log.LogInfo("Library: restored " + n + " saved mod entry records");
        }

        // ------------------------------------------------------------------ completion (achievements)
        static MethodInfo s_getStats;
        static FieldInfo s_fRatio, s_fRatioW, s_fRatioC, s_fCountC;

        /// <summary>
        /// SystemLibrary.UpdateCompletionRatio over vanilla entries only, line for line otherwise. The vault, weapon vault
        /// and challenge achievements read these ratios, so mod entries can neither lower them nor count towards them.
        /// </summary>
        internal static bool UpdateCompletionVanillaOnly(SystemLibrary lib, string userUid)
        {
            if (s_getStats == null)
            {
                s_getStats = AccessTools.Method(typeof(SystemLibrary), "GetCompletionStats");
                var t = AccessTools.Inner(typeof(SystemLibrary), "CompletionStats");
                s_fRatio = AccessTools.Field(t, "m_completionRatio");
                s_fRatioW = AccessTools.Field(t, "m_completionRatioWeapons");
                s_fRatioC = AccessTools.Field(t, "m_completionRatioChallenges");
                s_fCountC = AccessTools.Field(t, "m_completionCountChallenges");
            }
            var stats = s_getStats.Invoke(lib, new object[] { userUid });
            if (stats == null)
            {
                Debug.LogError("Unable to update completion stats for user " + userUid);
                return true;
            }
            var list = R.Get<List<SystemLibrary.LibraryEntry>>(lib, "m_entryList");
            int found = 0, total = 0;
            foreach (var e in list)
            {
                if (s_mod.Contains(e)) continue;
                total++;
                if (e.IsFound(userUid)) found++;
            }
            s_fRatio.SetValue(stats, (float)found / (float)total);
            found = 0; total = 0;
            foreach (var e in lib.m_weapons)
            {
                if (s_mod.Contains(e)) continue;
                total++;
                if (e.IsFound(string.Empty)) found++;   // vanilla reads the primary user here too
            }
            s_fRatioW.SetValue(stats, (float)found / (float)total);
            int passed = 0; total = 0;
            foreach (var m in lib.m_monsters)
            {
                if (s_mod.Contains(m)) continue;
                total++;
                if (m.GetHighScore(string.Empty) >= m.m_targetScore) passed++;
            }
            s_fCountC.SetValue(stats, passed);
            s_fRatioC.SetValue(stats, (float)passed / (float)total);
            SystemAchievements.Check();
            return false;
        }
    }

    // ====================================================================================================== patches

    [HarmonyPatch(typeof(SystemLibrary), "Sync")]
    static class Patch_LibrarySync
    {
        static void Postfix(SystemLibrary __instance, SaveHelper file)
        {
            if (file == null || !file.GetLoading()) return;
            try { LibraryEntries.OnLoaded(__instance, file); }
            catch (Exception e) { FurtherCore.Log.LogError("Library load hook: " + e); }
        }
    }

    [HarmonyPatch(typeof(SystemLibrary), "UpdateCompletionRatio")]
    static class Patch_LibraryCompletion
    {
        static bool Prefix(SystemLibrary __instance, string userUid)
        {
            if (!LibraryEntries.HasModEntries) return true;
            try { return LibraryEntries.UpdateCompletionVanillaOnly(__instance, userUid); }
            catch (Exception e)
            {
                // vanilla then counts mod entries too: ratios can only come out lower, never unlock anything early
                FurtherCore.Log.LogError("Library completion: " + e);
                return true;
            }
        }
    }

    /// <summary>
    /// Minions and ghost blobs are never inhabited, so the vanilla rule (InitAsPlayer) can't find them. They are found
    /// when a human player's monster or ghost brings one into the world (InitAsAI(spawner) is how the game wires both
    /// fodder and effect-spawned minions). OnEntryFound itself ignores bots and inactive players.
    /// </summary>
    [HarmonyPatch(typeof(Player), "InitAsAI")]
    static class Patch_LibrarySummonFound
    {
        static void Postfix(Player __instance, GameObject spawner)
        {
            if (spawner == null || __instance == null || !LibraryEntries.HasModEntries) return;
            try
            {
                var entry = SystemLibrary.GetLibraryEntry(__instance.gameObject);
                if (entry == null || !LibraryEntries.IsMod(entry) || !LibraryEntries.IsSummoned(entry.m_prefab)) return;
                var owner = spawner.GetComponent<Player>();
                var pd = owner != null ? owner.GetPlayerData() : null;
                if (pd != null) SystemLibrary.OnEntryFound(pd, __instance.gameObject);
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Library summon find: " + e.Message); }
        }
    }

    // ---------------------------------------------------------------------------------------------- vault menu

    /// <summary>Late safety net: add the entries when the vault opens if Register ran before SystemLibrary existed.
    /// Then give the mod monsters their challenge goals again (a secret or challenge def may have registered since).</summary>
    [HarmonyPatch(typeof(MenuLibrary), "OnEnable")]
    static class Patch_LibraryMenuEnable
    {
        static void Prefix()
        {
            try { LibraryEntries.EnsureRegistered(); LibraryEntries.RefreshChallenges(); }
            catch (Exception e) { FurtherCore.Log.LogError("Library late register: " + e); }
        }
    }

    /// <summary>Mod monsters without a challenge (minions, blobs): never launch one from the vault. Every other entry,
    /// mod monsters with a challenge included, goes through the game's own StartChallenge.</summary>
    [HarmonyPatch(typeof(MenuLibrary), "StartChallenge")]
    static class Patch_LibraryChallengeStart
    {
        static bool Prefix(MenuTextMenu ___m_menuItemsMonster)
        {
            try
            {
                var list = SystemLibrary.GetMonsters();
                int i = ___m_menuItemsMonster != null ? ___m_menuItemsMonster.GetSelectedId() : -1;
                if (list != null && i >= 0 && i < list.Count && LibraryEntries.NoChallenge(list[i])) return false;
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Library challenge guard: " + e.Message); }
            return true;
        }
    }

    /// <summary>Remember which monster cells are mod entries without a challenge, so pressing them does nothing (like an
    /// undiscovered cell). Mark found mod monsters' cells with the gem. The passed tick is the game's own
    /// (SetMonster shows it from the entry's goal and high score, for mod monsters too).</summary>
    [HarmonyPatch(typeof(MenuItemLibraryMonster), "SetMonster", new[] { typeof(Player), typeof(SystemLibrary.LibraryEntryMonster) })]
    static class Patch_LibraryCellSet
    {
        internal static readonly HashSet<int> NoChallengeCells = new HashSet<int>();
        static void Postfix(MenuItemLibraryMonster __instance, SystemLibrary.LibraryEntryMonster libraryEntry)
        {
            if (__instance == null) return;
            int id = __instance.GetInstanceID();
            if (LibraryEntries.NoChallenge(libraryEntry)) NoChallengeCells.Add(id); else NoChallengeCells.Remove(id);
            try { VaultGrid.CellGem(__instance, LibraryEntries.IsMod(libraryEntry) && libraryEntry.IsFound(string.Empty), true); }
            catch (Exception e) { FurtherCore.Log.LogWarning("Vault gem: " + e.Message); }
        }
    }

    /// <summary>The cell's own action hides its art and sends MsgChallenge. Skip both for mod monsters without a
    /// challenge.</summary>
    [HarmonyPatch(typeof(MenuItemLibraryMonster), "OnAction")]
    static class Patch_LibraryCellAction
    {
        static bool Prefix(MenuItemLibraryMonster __instance)
        {
            return __instance == null || !Patch_LibraryCellSet.NoChallengeCells.Contains(__instance.GetInstanceID());
        }
    }

    /// <summary>
    /// When the selection lands on a found mod monster, the page uses the item layout: its name under the rule, then
    /// its line, laid out to fit. A monster with a challenge keeps the game's "Challenge" label and gets the game's
    /// challenge lines under its line (<see cref="LibraryEntries.ChallengeLines"/>, as many as fit above the button
    /// row). One without (minions, blobs) shows neither.
    /// </summary>
    [HarmonyPatch(typeof(MenuLibrary), "UpdateItem")]
    static class Patch_LibraryItemText
    {
        static FieldInfo s_category;

        static void Prefix(int ___m_selectedItem, out int __state) { __state = ___m_selectedItem; }

        static void Postfix(MenuLibrary __instance, int __state, int ___m_selectedItem, TextMesh ___m_textButtonA,
                            GUIText ___m_textDescriptionMonster, GUIText ___m_textDescriptionMonsterPassed)
        {
            if (!LibraryEntries.HasModEntries || ___m_selectedItem < 0) return;
            try
            {
                if (s_category == null) s_category = AccessTools.Field(typeof(MenuLibrary), "m_category");
                if (Convert.ToInt32(s_category.GetValue(__instance)) != 0) return;   // eCategory.Monsters
                var list = SystemLibrary.GetMonsters();
                if (___m_selectedItem >= list.Count) return;
                var e = list[___m_selectedItem];
                if (!LibraryEntries.IsMod(e)) return;
                bool challenge = LibraryEntries.HasChallenge(e);
                if (!challenge && ___m_textButtonA != null && ___m_textButtonA.gameObject.activeSelf) ___m_textButtonA.gameObject.SetActive(false);
                if (__state == ___m_selectedItem) return;   // only when the selection just changed
                if (___m_textDescriptionMonsterPassed != null) ___m_textDescriptionMonsterPassed.gameObject.SetActive(false);
                if (___m_textDescriptionMonster != null) ___m_textDescriptionMonster.gameObject.SetActive(false);
                // the entry's text is "Name\nline": the name becomes the page title
                string text = e.m_description ?? string.Empty;
                if (!string.IsNullOrEmpty(e.m_name) && text.StartsWith(e.m_name + "\n", StringComparison.Ordinal)) text = text.Substring(e.m_name.Length + 1);
                if (challenge) VaultGrid.ShowChallengePage(__instance, e.m_name, text, LibraryEntries.ChallengeLines(__instance, e));
                else VaultGrid.ShowPage(__instance, e.m_name, text);
            }
            catch (Exception ex) { FurtherCore.Log.LogWarning("Library item text: " + ex.Message); }
        }
    }

    /// <summary>
    /// The MONSTERS summary says how many challenges are passed ("{2} challenges passed", the game's own string). The
    /// game counts that from its completion stats, which leave mod entries out so achievements never see them. Here the
    /// mod challenges passed are added to the number shown, with the same live string.
    /// </summary>
    [HarmonyPatch(typeof(MenuLibrary), "UpdateCategory")]
    static class Patch_LibraryChallengeSummary
    {
        static FieldInfo s_selected;

        static void Prefix(MenuLibrary __instance, MenuTextMenu ___m_menuCategories, bool force, out bool __state)
        {
            __state = false;
            try
            {
                if (s_selected == null) s_selected = AccessTools.Field(typeof(MenuLibrary), "m_selectedCategory");
                int want = ___m_menuCategories != null ? Mathf.Max(0, ___m_menuCategories.GetSelectedId()) : -1;
                // vanilla rewrites the summary only when the highlighted category changed or it is forced
                __state = want == VaultGrid.Monsters && (force || Convert.ToInt32(s_selected.GetValue(__instance)) != want);
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Vault challenge summary: " + e.Message); }
        }

        static void Postfix(MenuLibrary __instance, bool __state, GUIText ___m_textCategorySummary, string ___m_stringMonstersCategorySummary)
        {
            if (!__state || !LibraryEntries.HasModEntries || ___m_textCategorySummary == null || !___m_textCategorySummary.gameObject.activeSelf) return;
            try
            {
                if (!Singleton<SystemDebug>.HasInstance() || Singleton<SystemDebug>.Get.m_challengeModeHidePassedFeature) return;
                int passed = LibraryEntries.ModChallengesPassed();
                if (passed == 0) return;   // the game's own number is already right
                var list = SystemLibrary.GetMonsters();
                int found = 0;
                foreach (var m in list) if (m != null && m.IsFound(string.Empty)) found++;
                int total = Mathf.RoundToInt(SystemLibrary.GetCompletionCountChallenges(string.Empty)) + passed;
                ___m_textCategorySummary.SetText(string.Format(___m_stringMonstersCategorySummary ?? string.Empty, found, list.Count, total));
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Vault challenge summary: " + e.Message); }
        }
    }

    /// <summary>
    /// The item list numbers rows "{i+1:D2} name(22)". Past row 99 the number takes a third digit, one character more
    /// than vanilla's widest row (25); trim those names by one so no row is wider than vanilla's.
    /// </summary>
    [HarmonyPatch(typeof(MenuLibrary), "SetCategory")]
    static class Patch_LibraryListWidth
    {
        const int VanillaRowChars = 25;   // "NN " + 22
        static void Postfix(MenuLibrary __instance, MenuTextMenu ___m_menuItems)
        {
            if (!LibraryEntries.HasModEntries || ___m_menuItems == null) return;
            try
            {
                var items = R.Get<List<MenuTextMenuItem>>(___m_menuItems, "m_itemsAll");
                for (int i = 99; i < items.Count; i++)
                {
                    if (items[i] == null) continue;
                    string t = items[i].GetText();
                    if (string.IsNullOrEmpty(t) || t.Length <= VanillaRowChars) continue;
                    int sp = t.IndexOf(' ');
                    if (sp < 0) continue;
                    string num = t.Substring(0, sp + 1), rest = t.Substring(sp + 1);
                    ___m_menuItems.SetItemString(i, num + rest.Truncate(VanillaRowChars - num.Length));
                }
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Library list width: " + e.Message); }
        }
    }
}
