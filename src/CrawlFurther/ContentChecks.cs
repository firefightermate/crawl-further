using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content
{
    using CrawlFurther.Art;
    using CrawlFurther.Diagnostics;
    using CrawlFurther.Gods;
    using CrawlFurther.Heroes;
    using CrawlFurther.Items;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;
    using CrawlFurther.Content.Bosses;
    using CrawlFurther.Content.Ghosts;
    using CrawlFurther.Content.Gods;
    using CrawlFurther.Content.Heroes;
    using CrawlFurther.Content.Items;
    using CrawlFurther.Content.Objects;
    using CrawlFurther.Content.Secrets;
    using CrawlFurther.Content.Weapons;

    /// <summary>
    /// The Crawl: Further self-test sections: the 3 / 6 / 12 evolution trees, the nine gods, shop items, weapons, ghost
    /// forms, bosses and hero origins, plus every content area's own SelfCheck. Added to <see cref="SelfTest"/> by
    /// <see cref="ContentSetup"/> in the order the report lists them.
    /// </summary>
    public static class ContentChecks
    {
        public static readonly string[] GodNames = { "Vhorrul", "Ossivar", "Sylvene", "Umbrael", "Bel'Mora", "Jinx", "Zhekra", "Kaurn", "Ysveld" };

        static void Bad(string msg) { SelfTest.Bad(msg); }
        static void Note(string msg) { SelfTest.Note(msg); }

        /// <summary>Every section, in report order (Core's own sections slot in between by their order numbers).</summary>
        public static void AddSections()
        {
            SelfTest.AddSection(300, "evolution trees", CheckTrees);
            SelfTest.AddSection(400, "gods", CheckGods);
            SelfTest.AddSection(500, "shop items", CheckItems);
            SelfTest.AddSection(600, "weapons", CheckWeapons);
            SelfTest.AddSection(700, "ghost forms, bosses, origins", CheckOthers);
            SelfTest.AddSection(800, "slots, unlocks, custom gods", () => { FrameworkChecks.SelfCheck(Bad); SlotChallenges.SelfCheck(Bad); });
            SelfTest.AddSection(900, "custom heroes", () => HeroCustom.SelfCheck(Bad));
            SelfTest.AddSection(1000, "custom ghosts", () => GhostCustom.SelfCheck(Bad));
            SelfTest.AddSection(1100, "ghost forms", () => GhostV11.SelfCheck(Bad));
            SelfTest.AddSection(1500, "silver uniques", () => { SilverPack.SelfCheck(Bad); MonsterSecrets.SelfCheck(Bad); });
            SelfTest.AddSection(1600, "secret statues", () => StatuePack.SelfCheck(Bad));
            SelfTest.AddSection(1650, "monster challenges", () => Library.MonsterChallenges.SelfCheck(Bad, Note));
            SelfTest.AddSection(1700, "items wave 3", () => ItemPack3.SelfCheck(Bad));
            SelfTest.AddSection(1800, "room objects A (and ObjectKit)", () => ObjectPack.SelfCheck(Bad));
            SelfTest.AddSection(1900, "room objects B (fun and secret)", () => ObjectPack2.SelfCheck(Bad));
            SelfTest.AddSection(2200, "ghost slots (Ascension, Thralls)", () => GhostSlots.SelfCheck(Bad));
            SelfTest.AddSection(2300, "silver variants", () => SilverVariants.SelfCheck(Bad));
        }

        // ------------------------------------------------------------------------------------------ trees
        static SpawnGroup StatueGroup()
        {
            foreach (var g in Resources.FindObjectsOfTypeAll<SpawnGroup>())
                if (g.gameObject.name == "EnemyGroupStatue" && !g.gameObject.scene.IsValid()) return g;
            return null;
        }

        static string Name(Player p) { return p == null ? "null" : p.gameObject.name; }

        /// <summary>
        /// v0.9 rule (a true branching tree): 3 T1 -> 6 T2 -> 12 T3 per god; every T1 and T2 offers exactly two different
        /// evolutions that NO other monster offers (every evolved monster has exactly one parent), finals evolve no further, costs 0 / 2.5 / 4.5, every evolved mod monster
        /// is reachable from some god's starters, every final has its carved statue and sits in the statue group.
        /// </summary>
        public static void CheckTrees()
        {
            var built = new HashSet<Player>(MonsterFactory.Built.Values);
            var reached = new HashSet<Player>();
            var group = StatueGroup();
            var statueItems = group != null ? R.Get<List<SpawnItem>>(group, "m_items") : null;
            if (statueItems == null) Bad("statue group EnemyGroupStatue not found");

            foreach (var god in DeityFactory.BuiltNames)
            {
                // other mods' gods follow their own rules
                if (Array.IndexOf(GodNames, god) < 0) continue;
                var d = SystemDeity.GetDeity(god);
                if (d == null) { Bad("god " + god + " was built but is not in the god list"); continue; }
                var tiers = new List<List<Player>> { new List<Player>() };
                foreach (var go in d.GetStartingMonsters() ?? new GameObject[0])
                {
                    var p = go != null ? go.GetComponent<Player>() : null;
                    if (p == null) { Bad(god + ": a starting monster is missing"); continue; }
                    tiers[0].Add(p);
                }
                var pairs = new Dictionary<string, Player>();
                var parentOf = new Dictionary<Player, Player>();
                for (int t = 0; t < 2; t++)
                {
                    var next = new List<Player>();
                    foreach (var p in tiers[t])
                    {
                        var to = p.GetEvolveTo() ?? new Player[0];
                        var distinct = new List<Player>();
                        foreach (var x in to) if (x != null && !distinct.Contains(x)) distinct.Add(x);
                        if (to.Length != 2 || distinct.Count != 2)
                            Bad(god + ": " + Name(p) + " (T" + (t + 1) + ") offers " + to.Length + " evolutions (" + distinct.Count + " distinct), must be exactly 2");
                        foreach (var x in distinct)
                        {
                            if (!built.Contains(x)) Bad(god + ": " + Name(p) + " evolves into " + Name(x) + ", which is not a mod monster");
                            Player first;
                            if (parentOf.TryGetValue(x, out first)) Bad(god + ": " + Name(x) + " is offered by both " + Name(first) + " and " + Name(p) + " (evolutions must not be shared)");
                            else parentOf[x] = p;
                            if (!next.Contains(x)) next.Add(x);
                        }
                        if (distinct.Count == 2)
                        {
                            var a = Name(distinct[0]); var b = Name(distinct[1]);
                            string key = string.CompareOrdinal(a, b) < 0 ? a + "|" + b : b + "|" + a;
                            Player other;
                            if (pairs.TryGetValue(key, out other)) Bad(god + ": " + Name(p) + " and " + Name(other) + " offer the same pair (" + key + ")");
                            else pairs[key] = p;
                        }
                    }
                    tiers.Add(next);
                }
                int[] want = { 3, 6, 12 };
                float[] cost = { 0f, 2.5f, 4.5f };
                for (int t = 0; t < 3; t++)
                {
                    if (tiers[t].Count != want[t]) Bad(god + ": T" + (t + 1) + " has " + tiers[t].Count + " monsters, the tree rule wants " + want[t]);
                    foreach (var p in tiers[t])
                    {
                        reached.Add(p);
                        for (int u = 0; u < 3; u++) if (u != t && tiers[u].Contains(p)) Bad(god + ": " + Name(p) + " sits in two tiers");
                        float c = R.Get<float>(p, "m_evolveCost");
                        if (t > 0 && Mathf.Abs(c - cost[t]) > 0.01f) Bad(god + ": " + Name(p) + " (T" + (t + 1) + ") costs " + c + ", expected " + cost[t]);
                    }
                }
                foreach (var p in tiers[2])
                {
                    var to = p.GetEvolveTo();
                    if (to != null && to.Length > 0) Bad(god + ": final " + Name(p) + " still evolves (" + to.Length + ")");
                    var st = p.GetAnimationStatue();
                    if (st == null || !st.name.StartsWith("ModStatue_")) Bad(god + ": final " + Name(p) + " has no carved statue (" + (st == null ? "none" : st.name) + ")");
                    if (statueItems != null && !statueItems.Exists(i => i != null && i.m_object == p.gameObject)) Bad(god + ": final " + Name(p) + " is not in the statue group");
                }
                Note(god + ": T1 " + Names(tiers[0]) + " | T2 " + Names(tiers[1]) + " | T3 " + Names(tiers[2]));
            }
            // the Gilded Secret line (1 / 2 / 4, no god; gold idol slot 4 only) counts as reached through its own starter
            GoldSecretPack.CheckTree(Bad, Note, reached, statueItems);
            // evolved mod monsters nobody can reach (minions and blobs stay tier 1, so they're not listed)
            foreach (var kv in MonsterFactory.Tier)
            {
                if (kv.Value < 2) continue;
                Player p = null;
                foreach (var b in built) if (b != null && b.gameObject.name == kv.Key) { p = b; break; }
                if (SilverUniques.Ids.Contains(kv.Key)) continue;   // silver unique finals have no tree (silver ghost upgrade only)
                if (SecretStatues.Is(kv.Key)) continue;             // secret statue finals have no tree (secret statues only)
                if (p != null && !reached.Contains(p)) Bad(kv.Key + " is an evolved tier but no god's tree reaches it");
            }
        }

        static string Names(List<Player> l)
        {
            var n = new List<string>();
            foreach (var p in l) n.Add(Name(p));
            return string.Join(", ", n.ToArray());
        }

        // ------------------------------------------------------------------------------------------ gods
        public static void CheckGods()
        {
            var deities = SystemDeity.GetDeities();
            foreach (var name in GodNames)
            {
                bool found = false;
                if (deities != null) foreach (var d in deities) if (d != null && d.GetName() == name) found = true;
                if (!found) Bad("god " + name + " is not in the god list");
                else Note("god " + name + " ok");
            }
            int ours = 0;
            foreach (var name in DeityFactory.BuiltNames) if (Array.IndexOf(GodNames, name) >= 0) ours++;
            if (ours != GodNames.Length) Bad(ours + " Crawl: Further gods registered, expected " + GodNames.Length);
            int dup = 0;
            if (deities != null)
                foreach (var name in DeityFactory.BuiltNames)
                {
                    int n = 0;
                    foreach (var d in deities) if (d != null && d.GetName() == name) n++;
                    if (n > 1) dup++;
                }
            if (dup > 0) Bad(dup + " mod god(s) appear more than once in the god list");
        }

        // ------------------------------------------------------------------------------------------ shop
        static void CheckBubble(string who, exSpriteAnimClip bubble)
        {
            if (bubble == null || bubble.frameInfos == null || bubble.frameInfos.Count == 0) Bad(who + " has no shop bubble clip");
            else if (SpriteSheets.ByAtlas(bubble.frameInfos[0].atlas) == null) Bad(who + " shop bubble is vanilla art (" + bubble.name + ")");
        }

        static void CheckPedestal(string who, string key, SpriteSheet pedestals)
        {
            if (pedestals == null) return;
            if (key == null || !pedestals.Has(key)) Bad(who + " has no shop pedestal frame '" + key + "' in " + ContentSetup.PedestalSheet);
        }

        public static void CheckItems()
        {
            var pedestals = SpriteSheets.Get(ContentSetup.PedestalSheet);
            if (pedestals == null) Bad("art/" + ContentSetup.PedestalSheet + " missing: every mod item shows a stand-in on its pedestal");
            var seen = new HashSet<string>();
            foreach (var def in ItemPack.Items)
            {
                if (!seen.Add(def.id)) { Bad("item " + def.id + " is queued twice"); continue; }
                Powerup pu;
                if (!ItemPack.Built.TryGetValue(def.id, out pu) || pu == null) { Bad("item " + def.id + " failed to build"); continue; }
                Note("item " + pu.m_displayName + " cost " + pu.m_cost);
                CheckBubble("item " + def.id, R.Get<exSpriteAnimClip>(pu, "m_animPurchasableBubble"));
                CheckPedestal("item " + def.id, ShopPedestal.KeyFor(pu), pedestals);
            }
        }

        public static void CheckWeapons()
        {
            var pedestals = SpriteSheets.Get(ContentSetup.PedestalSheet);
            foreach (var def in WeaponPack.Defs)
            {
                Weapon w;
                if (!WeaponPack.Built.TryGetValue(def.id, out w) || w == null) { Bad("weapon " + def.id + " failed to build"); continue; }
                Note("weapon " + w.m_weaponName + " cost " + w.m_cost);
                CheckBubble("weapon " + def.id, w.m_animationPurchasableBubble);
                CheckPedestal("weapon " + def.id, "Wpn" + def.id, pedestals);
            }
            if (WeaponPack.Built.Count < WeaponPack.Defs.Count) Note((WeaponPack.Defs.Count - WeaponPack.Built.Count) + " weapon(s) missing");
        }

        // ------------------------------------------------------------------------------------------ the rest
        public static void CheckOthers()
        {
            foreach (var g in GhostPack.Forms)
            {
                var sh = SpriteSheets.Get(g.portraitArt);
                if (sh == null || !sh.Has("Idle")) Bad("ghost form " + g.name + " portrait missing");
            }
            foreach (var b in new[] { GhostPack.Mote, GhostPack.Spitter, GhostPack.Gel, GhostPack.Brute, GhostPack.Titan, GhostPack.King })
                if (b == null) Bad("a ghost-form blob monster failed to build");
            foreach (var fx in new[] { GhostPack.KingSlam, GhostPack.KingQuake, GhostPack.KingDrop, GhostPack.KingDropPool })
                if (fx == null) Bad("a King Blob effect failed to build");
            CrawlFurther.Ghosts.GhostBlobs.SelfCheck(Bad);
            BlobChallenges.SelfCheck(Bad);
            Note("bosses built: " + BossFactory.Built.Count + (BossPack.Enabled ? "" : " (switched off: Bosses.Enabled = false)"));
            foreach (var b in BossFactory.Built) Note("  " + b.GetDisplayName());
            if (BossPack.Enabled && BossFactory.Built.Count < 2) Bad("only " + BossFactory.Built.Count + " of 2 mod bosses built");
            if (!BossPack.Enabled && BossFactory.Built.Count > 0) Bad("bosses are switched off but " + BossFactory.Built.Count + " were built");
            foreach (var c in HeroClasses.All)
            {
                var sh = SpriteSheets.Get(c.portraitArt);
                if (sh == null || !sh.Has("Idle")) Bad("origin " + c.id + " portrait missing");
            }
        }
    }
}
