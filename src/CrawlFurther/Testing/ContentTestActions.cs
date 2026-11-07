using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Testing
{
    using CrawlFurther.Ghosts;
    using CrawlFurther.Gods;
    using CrawlFurther.Monsters;
    using CrawlFurther.Testing;
    using CrawlFurther.Content.Ghosts;
    using CrawlFurther.Content.Secrets;

    /// <summary>
    /// Crawl: Further's own test panel entries: its ghost forms, the silver ascension of every final, the secret
    /// monsters and statues, and the mod bosses. Registered from the start callback, only while test mode is on.
    /// </summary>
    static class ContentTestActions
    {
        const string Become = "Become", Secrets = "Secrets";

        static float s_bossChance = -1f;

        internal static void Register()
        {
            TestMode.SwitchedOff += () => { if (s_bossChance >= 0f) BossFactory.Chance = s_bossChance; };

            TestMode.AddList(Become, "Ghost form", GhostForms, item =>
            {
                var pd = Player();
                if (pd.IsBot) throw new TestModeException("Bots always use the plain Wisp: pick a human player");
                var entry = GhostPack.Forms[(int)item.Value];
                int before;
                bool had = GhostPack.Chosen.TryGetValue(pd.Id, out before);
                GhostPack.Chosen[pd.Id] = (int)item.Value;
                if (GhostPack.DefOf(pd) != entry)
                {
                    if (had) GhostPack.Chosen[pd.Id] = before; else GhostPack.Chosen.Remove(pd.Id);
                    throw new TestModeException(item.Label + " is still locked: switch on Open everything on the Progress page");
                }
                TestGame.BecomeGhost(pd);
                TestMode.Say("P" + (pd.Id + 1) + " is a " + item.Label + " ghost");
            });
            TestMode.AddList(Become, "Ghost blob", GhostBlobList, item =>
            {
                var pd = Player();
                if (pd.IsBot) throw new TestModeException("Bots always spawn their form's default blob: pick a human player");
                var def = item.Value as GhostBlobDef;
                var form = GhostPack.DefOf(pd);
                if (def != null && !GhostBlobs.Fits(def, form))
                    throw new TestModeException("The " + form.name + " ghost cannot pick " + item.Label + ": the Gleaner, Poltergeist and Binder pick their own, silver and gold pick any");
                if (def != null && !GhostBlobs.IsOpen(def))
                    throw new TestModeException(item.Label + " is still locked: switch on Open everything on the Progress page");
                GhostBlobs.SetPick(pd.Id, form, def);
                TestGame.BecomeGhost(pd);
                TestMode.Say("P" + (pd.Id + 1) + "'s ghost spawns the " + GhostBlobs.ChoiceOf(pd).name);
            });
            TestMode.AddList(Become, "Silver ascended final", Finals, item =>
            {
                var pd = Player();
                var body = TestGame.Become(pd, (GameObject)item.Value);
                GhostSlots.Ascend(body);
                TestMode.Say("P" + (pd.Id + 1) + " is a silver ascended " + item.Label);
            });

            TestMode.AddToggle(Secrets, "Every boss fight is a mod boss", () => BossFactory.Built.Count > 0 && BossFactory.Chance >= 1f, on =>
            {
                if (BossFactory.Built.Count == 0) throw new TestModeException("The mod bosses are switched off: turn on Enabled in the Bosses part of the mod's config");
                if (s_bossChance < 0f) s_bossChance = BossFactory.Chance;
                BossFactory.Chance = on ? 1f : s_bossChance;
            });
            TestMode.AddList(Secrets, "Secret monster (become)", SecretMonsters, item =>
            {
                var pd = Player();
                TestGame.Become(pd, (GameObject)item.Value);
                TestMode.Say("P" + (pd.Id + 1) + " is now " + item.Label);
            });
            TestMode.AddList(Secrets, "Secret statue (place)", SecretStatueList, item =>
            {
                var room = SystemLevel.GetCurrentRoom();
                if (!TestGame.InLevel || room == null) throw new TestModeException("Start a run first");
                if (StatuePlacement.Spawn(TestGame.BesideHero(), room.transform, (string)item.Value) == null)
                    throw new TestModeException("The secret statues are not built");
                TestMode.Say(item.Label + " statue placed beside the hero");
            });
        }

        static PlayerData Player()
        {
            var pd = TestMode.Player;
            if (pd == null) throw new TestModeException("No player to act for: start a run with a monster player, or pick one at the top");
            return pd;
        }

        static IEnumerable<TestItem> GhostForms()
        {
            for (int i = 0; i < GhostPack.Forms.Count; i++)
            {
                var f = GhostPack.Forms[i];
                yield return new TestItem(f.name, i, f.tier == SlotTier.Normal ? null : "Custom slots");
            }
        }

        /// <summary>The form's own blob, then every blob a ghost can pick.</summary>
        static IEnumerable<TestItem> GhostBlobList()
        {
            yield return new TestItem("Form default", null);
            foreach (var b in GhostBlobs.All) yield return new TestItem(b.name, b, b.unlock == null ? null : "Unlocked by a challenge");
        }

        /// <summary>Every final of every god's tree (vanilla and mod, once each), under the first god that has it.</summary>
        static IEnumerable<TestItem> Finals()
        {
            var seen = new HashSet<GameObject>();
            var gods = SystemDeity.GetDeities();
            if (gods == null) yield break;
            foreach (var d in gods)
            {
                if (d == null) continue;
                foreach (var kv in TestGame.Tree(d))
                    if (GhostSlots.IsFinal(kv.Key, kv.Key.name) && seen.Add(kv.Key))
                        yield return new TestItem(Name(kv.Key), kv.Key, d.GetName());
            }
        }

        static IEnumerable<TestItem> SecretMonsters()
        {
            foreach (var id in SecretStatues.Ids) { var go = Prefab(id); if (go != null) yield return new TestItem(Name(go), go, "Secret statues"); }
            foreach (var id in SilverUniques.Ids) { var go = Prefab(id); if (go != null) yield return new TestItem(Name(go), go, "Silver uniques"); }
            foreach (var id in GoldSecret.TreeIds) { var go = Prefab(id); if (go != null) yield return new TestItem(Name(go), go, "Gold secret"); }
        }

        static IEnumerable<TestItem> SecretStatueList()
        {
            foreach (var id in SecretStatues.Ids)
            {
                var go = Prefab(id);
                yield return new TestItem(go != null ? Name(go) : id, id, id == SecretStatues.Lachrymosa ? "Legendary" : null);
            }
        }

        /// <summary>A mod monster by prefab id ("ModX") or registry id ("X").</summary>
        static GameObject Prefab(string id)
        {
            if (string.IsNullOrEmpty(id)) return null;
            Player p;
            if (MonsterFactory.Built.TryGetValue(id, out p) && p != null) return p.gameObject;
            if (id.StartsWith("Mod") && MonsterFactory.Built.TryGetValue(id.Substring(3), out p) && p != null) return p.gameObject;
            foreach (var kv in MonsterFactory.Built) if (kv.Value != null && kv.Value.gameObject.name == id) return kv.Value.gameObject;
            return null;
        }

        /// <summary>The vault's name for a monster, or its prefab name without "Mod".</summary>
        static string Name(GameObject prefab)
        {
            if (Singleton<SystemLibrary>.HasInstance())
            {
                var e = SystemLibrary.GetMonsterEntry(prefab);
                if (e != null && !string.IsNullOrEmpty(e.m_name)) return e.m_name;
            }
            var n = prefab.name;
            return n.StartsWith("Mod") ? n.Substring(3) : n;
        }
    }
}
