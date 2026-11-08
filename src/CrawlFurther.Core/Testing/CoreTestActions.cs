using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Testing
{
    using CrawlFurther.Gods;
    using CrawlFurther.Heroes;
    using CrawlFurther.Items;
    using CrawlFurther.Monsters;
    using CrawlFurther.Objects;

    /// <summary>Core's own test panel pages, built with the same public calls any mod uses.</summary>
    static class CoreTestActions
    {
        const string Become = "Become", Spawn = "Spawn", Items = "Items", Run = "Run", Players = "Player", View = "View",
                     Unlocks = "Progress";
        const string Vanilla = "Crawl", Modded = "Mods";

        static Boss s_boss;
        static bool s_challengePad;

        internal static void Register()
        {
            AddBecome();
            AddSpawn();
            AddItems();
            AddRun();
            AddPlayers();
            AddView();
            AddUnlocks();
        }

        /// <summary>An online match started: the boss pick stops steering the run's boss fights.</summary>
        internal static void Reset()
        {
            if (s_boss != null && BossFactory.Forced == s_boss) BossFactory.Forced = null;
            s_boss = null;
        }

        static PlayerData Target()
        {
            var pd = TestMode.Player;
            if (pd == null) throw new TestModeException("No player to act for: start a run with a monster player, or pick one at the top");
            return pd;
        }

        static string Who(PlayerData pd) { return "P" + (pd.Id + 1); }

        // ------------------------------------------------------------------ pages

        static void AddBecome()
        {
            TestMode.AddAction(Become, "Become a ghost", () =>
            {
                var pd = Target();
                TestGame.BecomeGhost(pd);
                TestMode.Say(Who(pd) + " is a ghost");
            });
            TestMode.AddAction(Become, "Become the hero (kills the hero)", () =>
            {
                var pd = Target();
                TestGame.BecomeHero(pd);
                TestMode.Say(Who(pd) + " killed the hero: the crown passes in a moment");
            });
            var gods = TestMode.AddList(Become, "God", GodList, item => TestMode.Say("Showing the monsters of " + item.Label));
            TestMode.AddList(Become, "Monster (by tier)", () => Tree(gods.SelectedValue as Deity), item =>
            {
                var pd = Target();
                TestGame.Become(pd, (GameObject)item.Value);
                TestMode.Say(Who(pd) + " is now " + item.Label);
            });
            TestMode.AddList(Become, "Hero origin", Origins, item =>
            {
                var pd = Target();
                TestGame.SetOrigin(pd, (int)item.Value);
                TestMode.Say(Who(pd) + "'s origin is " + item.Label + (pd.IsHero ? " (stats and weapon apply on the next hero)" : ""));
            });
        }

        static void AddSpawn()
        {
            TestMode.AddAction(Spawn, "Remove the test bots", () => TestMode.Say(TestGame.RemoveTestBots() + " test bots removed"));
            TestMode.AddList(Spawn, "Hostile monster", Monsters, item =>
            {
                TestGame.SpawnHostile((GameObject)item.Value);
                TestMode.Say(item.Label + " spawned beside the hero");
            });
            TestMode.AddList(Spawn, "Room object", Objects, item =>
            {
                TestGame.PlaceObject((string)item.Value);
                TestMode.Say(item.Label + " placed beside the hero");
            });
        }

        static void AddItems()
        {
            TestMode.AddList(Items, "Item or spell (to the hero)", ItemList, item =>
            {
                TestGame.GiveItem((Powerup)item.Value);
                TestMode.Say("The hero has " + item.Label);
            });
            TestMode.AddList(Items, "Weapon (to the hero)", WeaponList, item =>
            {
                var w = (KeyValuePair<Weapon, string>)item.Value;
                TestGame.GiveWeapon(w.Key, w.Value);
                TestMode.Say("The hero holds " + item.Label);
            });
        }

        static void AddRun()
        {
            TestMode.AddNumber(Run, "Go to floor (through the evolve screen)", 1, 99, 5, n => { TestGame.GoToFloor(n); TestMode.Say("Next floor: " + n); });
            TestMode.AddAction(Run, "Next floor", () => TestGame.NextFloor());
            TestMode.AddAction(Run, "Go to the boss now", () =>
            {
                TestGame.GoToBoss(s_boss);
                TestMode.Say("Boss portal: " + (s_boss != null ? BossName(s_boss) : "the game's pick"));
            });
            TestMode.AddAction(Run, "Beat the boss now (game end, continue prompt)", () =>
            {
                TestGame.BeatBoss();
                TestMode.Say("The boss falls: " + SystemPlayers.GetTotalBossAttempts() + " of " + SystemMenu.GetBossAttemptsAllowed() + " boss tries used");
            });
            TestMode.AddAction(Run, "Open the doors", () => TestGame.OpenDoors());
            TestMode.AddAction(Run, "Next room", () => TestGame.NextRoom());
            TestMode.AddAction(Run, "Go to the shop", () => TestGame.GoToStore());
            TestMode.AddAction(Run, "Go to the portal room", () => TestGame.GoToPortal());
            TestMode.AddAction(Run, "Reload this floor", () => TestGame.ReloadLevel());
            TestMode.AddChoice(Run, "Challenge controls", new[] { "Keyboard", "Pad 1" }, () => s_challengePad ? 1 : 0, i => s_challengePad = i == 1);
            TestMode.AddList(Run, "Monster challenge (from the menus)", ChallengeList, item =>
            {
                TestGame.StartChallenge((GameObject)item.Value, s_challengePad);
                TestMode.Say("Challenge: " + item.Label + " (the score is not saved in test mode)");
            });
            TestMode.AddList(Run, "God of the player acting", GodList, item =>
            {
                var pd = Target();
                TestGame.SetGod(pd, (Deity)item.Value);
                TestMode.Say(Who(pd) + "'s god is " + item.Label);
            });
            TestMode.AddList(Run, "Boss", Bosses, item =>
            {
                s_boss = item.Value as Boss;
                // with mod bosses built, the run's own boss fights take the pick too (BossFactory's boss roll)
                BossFactory.Forced = s_boss;
                TestMode.Say("Boss: " + item.Label + (BossFactory.Built.Count > 0 ? " (for Go to the boss now and the next boss fight)" : " (for Go to the boss now)"));
            });
        }

        static void AddPlayers()
        {
            TestMode.AddAction(Players, "Everyone: +1 level and evolve", () => { TestGame.LevelUpAll(); TestMode.Say("Everyone gained a level"); });
            TestMode.AddAction(Players, "Everyone: skip to level 10", () => { TestGame.SkipToLevel10(); TestMode.Say("Everyone is level 10 or more"); });
            TestMode.AddNumber(Players, "Hero level", 2, 30, 10, n => { TestGame.SetHeroLevel(n); TestMode.Say("The hero is level " + n); });
            TestMode.AddNumber(Players, "Gold for the player acting", 1, 99999, 100, n =>
            {
                var pd = Target();
                TestGame.AddGold(pd, n);
                TestMode.Say(Who(pd) + " +" + n + " gold");
            });
            TestMode.AddAction(Players, "Full heal: everyone", () =>
            {
                int n = 0;
                foreach (var p in SystemPlayers.GetPlayers()) if (p != null && p.IsActive && TestGame.FullHeal(p)) n++;
                TestMode.Say(n + " bodies healed");
            });
            TestMode.AddToggle(Players, "Invulnerable hero", () => TestCheats.InvulnerableHero, v => TestCheats.InvulnerableHero = v);
            TestMode.AddToggle(Players, "Invulnerable monster players", () => TestCheats.InvulnerableMonsters, v => TestCheats.InvulnerableMonsters = v);
            TestMode.AddToggle(Players, "Endless ectoplasm for ghosts", () => TestCheats.EndlessEcto, v => TestCheats.EndlessEcto = v);
        }

        static void AddView()
        {
            var speeds = new string[TestCheats.Speeds.Length];
            for (int i = 0; i < speeds.Length; i++) speeds[i] = "x" + TestCheats.Speeds[i];
            TestMode.AddChoice(View, "Game speed", speeds, () => System.Array.IndexOf(TestCheats.Speeds, TestCheats.Speed),
                i => { TestCheats.Speed = TestCheats.Speeds[i]; TestMode.Say("Game speed x" + TestCheats.Speed); });
            TestMode.AddToggle(View, "Hitboxes (red) and hurtboxes (green)", () => TestCheats.Hitboxes, v => TestCheats.Hitboxes = v);
            TestMode.AddToggle(View, "Freeze monster AI and bots", () => TestCheats.FreezeAI, v => TestCheats.FreezeAI = v);
            TestMode.AddToggle(View, "Hide the HUD", () => TestCheats.HideHud, v => TestCheats.HideHud = v);
        }

        static void AddUnlocks()
        {
            TestMode.AddToggle(Unlocks, "Open everything for this session (nothing is saved)", () => TestCheats.UnlockAll, v =>
            {
                TestCheats.UnlockAll = v;
                TestMode.Say(v ? "Everything is open until the game closes or this is switched off" : "Back to your real unlocks");
            });
            TestMode.AddAction(Unlocks, "The game's open-everything item (writes your save)", () =>
            {
                Singleton<SystemUnlocks>.Get.DebugUnlockAll();
                TestMode.Say("Every vanilla unlock is now in your save");
            });
        }

        // ------------------------------------------------------------------ list sources

        static IEnumerable<TestItem> GodList()
        {
            var list = SystemDeity.GetDeities();
            if (list == null) yield break;
            foreach (var d in list) if (d != null) yield return new TestItem(d.GetName(), d);
        }

        static IEnumerable<TestItem> Tree(Deity god)
        {
            if (god == null) yield break;
            foreach (var kv in TestGame.Tree(god)) yield return new TestItem(TestNames.Of(kv.Key), kv.Key, "Tier " + kv.Value);
        }

        static IEnumerable<TestItem> Origins()
        {
            for (int i = 0; i < HeroClasses.All.Count; i++)
            {
                var o = HeroClasses.All[i];
                yield return new TestItem(string.IsNullOrEmpty(o.name) ? o.id : o.name, i, o.tier == SlotTier.Normal ? null : o.tier.ToString());
            }
        }

        static IEnumerable<TestItem> Monsters()
        {
            var vanilla = new List<TestItem>();
            var mods = new List<TestItem>();
            var built = new HashSet<GameObject>();
            foreach (var p in MonsterFactory.Built.Values) if (p != null) built.Add(p.gameObject);
            foreach (var go in TestGame.AllMonsters())
            {
                bool mod = built.Contains(go);
                (mod ? mods : vanilla).Add(new TestItem(TestNames.Of(go), go, mod ? Modded : Vanilla));
            }
            return Sorted(vanilla, mods);
        }

        static IEnumerable<TestItem> ChallengeList()
        {
            var vanilla = new List<TestItem>();
            var mods = new List<TestItem>();
            var built = new HashSet<GameObject>();
            foreach (var p in MonsterFactory.Built.Values) if (p != null) built.Add(p.gameObject);
            foreach (var go in TestGame.ChallengeMonsters())
            {
                bool mod = built.Contains(go);
                (mod ? mods : vanilla).Add(new TestItem(TestNames.Of(go), go, mod ? Modded : Vanilla));
            }
            return Sorted(vanilla, mods);
        }

        static IEnumerable<TestItem> Objects()
        {
            var list = new List<TestItem>();
            foreach (var kv in ObjectKit.Defs)
                if (ObjectKit.Built.ContainsKey(kv.Key)) list.Add(new TestItem(string.IsNullOrEmpty(kv.Value.name) ? kv.Key : kv.Value.name, kv.Key, kv.Value.kind.ToString()));
            list.Sort((a, b) => a.Group == b.Group ? string.CompareOrdinal(a.Label, b.Label) : string.CompareOrdinal(a.Group, b.Group));
            return list;
        }

        static IEnumerable<TestItem> ItemList()
        {
            var vanilla = new List<TestItem>();
            var mods = new List<TestItem>();
            var seen = new HashSet<Powerup>();
            var modItems = new HashSet<Powerup>(ItemRegistry.Items.Values);
            if (Singleton<SystemLibrary>.HasInstance())
                foreach (var e in SystemLibrary.GetItems())
                {
                    var p = e != null && e.m_prefab != null ? e.m_prefab.GetComponent<Powerup>() : null;
                    if (p == null || !seen.Add(p)) continue;
                    (modItems.Contains(p) ? mods : vanilla).Add(new TestItem(Name(e.m_name, p.gameObject), p, modItems.Contains(p) ? Modded : Vanilla));
                }
            foreach (var p in ItemRegistry.Items.Values)
                if (p != null && seen.Add(p)) mods.Add(new TestItem(TestNames.Of(p.gameObject), p, Modded));
            return Sorted(vanilla, mods);
        }

        static IEnumerable<TestItem> WeaponList()
        {
            var vanilla = new List<TestItem>();
            var mods = new List<TestItem>();
            var seen = new HashSet<string>();
            var modWeapons = new HashSet<Weapon>(ItemRegistry.Weapons.Values);
            if (Singleton<SystemLibrary>.HasInstance())
                foreach (var e in SystemLibrary.GetWeapons())
                {
                    var w = e != null && e.m_prefab != null ? e.m_prefab.GetComponent<Weapon>() : null;
                    if (w == null || !seen.Add(w.name + "|" + e.m_type)) continue;
                    bool mod = modWeapons.Contains(w);
                    (mod ? mods : vanilla).Add(new TestItem(Name(e.m_name, w.gameObject), new KeyValuePair<Weapon, string>(w, e.m_type), mod ? Modded : Vanilla));
                }
            foreach (var w in ItemRegistry.Weapons.Values)
                if (w != null && seen.Add(w.name + "|")) mods.Add(new TestItem(TestNames.Of(w.gameObject), new KeyValuePair<Weapon, string>(w, null), Modded));
            return Sorted(vanilla, mods);
        }

        static IEnumerable<TestItem> Bosses()
        {
            var list = new List<TestItem> { new TestItem("The game's pick", null) };
            var seen = new HashSet<Boss>();
            var vanilla = Singleton<Constants>.HasInstance() ? Singleton<Constants>.Get.m_bosses : null;
            if (vanilla != null)
                foreach (var b in vanilla) if (b != null && seen.Add(b)) list.Add(new TestItem(BossName(b), b, Vanilla));
            foreach (var b in BossFactory.Built) if (b != null && seen.Add(b)) list.Add(new TestItem(BossName(b), b, Modded));
            return list;
        }

        // ------------------------------------------------------------------ helpers

        static string BossName(Boss b)
        {
            string n = null;
            try { n = b.GetDisplayName(); } catch { }
            n = string.IsNullOrEmpty(n) ? TestNames.Plain(b.name) : n.Trim(' ', '-');
            return n;
        }

        static string Name(string vaultName, GameObject prefab)
        {
            return string.IsNullOrEmpty(vaultName) ? TestNames.Of(prefab) : vaultName;
        }

        static List<TestItem> Sorted(List<TestItem> vanilla, List<TestItem> mods)
        {
            vanilla.Sort((a, b) => string.Compare(a.Label, b.Label, System.StringComparison.OrdinalIgnoreCase));
            mods.Sort((a, b) => string.Compare(a.Label, b.Label, System.StringComparison.OrdinalIgnoreCase));
            vanilla.AddRange(mods);
            return vanilla;
        }
    }
}
