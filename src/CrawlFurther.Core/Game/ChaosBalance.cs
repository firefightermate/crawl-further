#if CHAOS_NEXT
// Next chaos update: compiled only with CHAOS_NEXT (build.sh sets it unless NO_CHAOS_NEXT=1).
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Game
{
    /// <summary>
    /// How a chaos game paces itself: every player starts with a head start (a hero at the level and purse of a normal
    /// game whose monsters have reached tier 2) and picks each starting monster's tier 2 evolution on the game's own
    /// evolve screen before the first floor; the hero levels faster, monster players earn wrath (the game's Vitae)
    /// faster, and gold comes in a little quicker. A normal game is untouched.
    /// </summary>
    public static class ChaosBalance
    {
        /// <summary>Hero XP from every source, times this.</summary>
        public static float XPScale = 1.5f;
        /// <summary>Monster players' wrath (Vitae) from every source, times this.</summary>
        public static float WrathScale = 1.5f;
        /// <summary>Gold from every source after the starting purse, times this.</summary>
        public static float GoldScale = 1.2f;
        /// <summary>Monster players start each line one evolution in (tier 2).</summary>
        public static bool StartEvolved = true;
        /// <summary>The tier 2 evolutions are picked on the evolve screen before the first floor (else random).</summary>
        public static bool PickStarters = true;
        /// <summary>
        /// The hero level every player starts a chaos game at. In a normal game a player's monsters reach tier 2 once
        /// the others have levelled enough to pay the evolution's wrath: about two levels each (with four players,
        /// five level-ups between the other three at the game's wrath per level; with two, the other's two).
        /// Level 3 also brings the game's first Vitality upgrade.
        /// </summary>
        public static int HeadStartLevel = 3;
        /// <summary>Starting gold per hero level: the figure the game itself uses to stage a game in progress (its
        /// attract mode gives each player 40 gold a level).</summary>
        public static float HeadStartGoldPerLevel = 40f;

        static bool s_applying;
        static bool s_done;
        /// <summary>The pre-game evolve screen is up: starting monsters evolve for free, one step each.</summary>
        internal static bool Picking;
        static readonly Dictionary<PlayerGameData, HashSet<GameObject>> s_starters = new Dictionary<PlayerGameData, HashSet<GameObject>>();
        static readonly HashSet<GameObject> s_starterEvos = new HashSet<GameObject>();

        /// <summary>Head-start level-ups and gold don't pay wrath or get the chaos scaling.</summary>
        internal static bool Applying { get { return s_applying; } }

        static bool NewGame()
        {
            if (!Singleton<SystemGame>.HasInstance()) return false;
            var sg = Singleton<SystemGame>.Instance;
            return !Util.R.Get<bool>(sg, "m_gameStarted") && Util.R.Get<int>(sg, "m_level") == 0;
        }

        /// <summary>A new chaos game is about to load its first floor: give the head start and, when picking, send the
        /// players to the evolve screen first. True when the scene to load was changed.</summary>
        internal static bool BeforeFirstFloor(ref string scene)
        {
            if (scene != "SceneGame")
            {
                // left the pre-game evolve screen some other way (quit to the menu): the next game starts clean
                if (Picking && scene != "SceneMenuEvolve") { Picking = false; s_done = false; }
                return false;
            }
            if (Picking)
            {
                // back from the evolve screen: any line left at tier 1 evolves at random
                Picking = false;
                FinishStarters();
                return false;
            }
            if (s_done || !ChaosMode.Active || !NewGame()) return false;
            HeadStart();
            if (!StartEvolved) return false;
            if (!PickStarters) { FinishStarters(); return false; }
            Picking = true;
            scene = "SceneMenuEvolve";
            FurtherCore.Log.LogInfo("Chaos: picking tier 2 monsters before the first floor");
            return true;
        }

        /// <summary>A game that started some other way (or a picker that never ran) still gets its head start.</summary>
        internal static void OnGameStart()
        {
            if (Picking) { Picking = false; FinishStarters(); }
            if (!ChaosMode.Active) { s_done = false; return; }
            if (!s_done)
            {
                HeadStart();
                if (StartEvolved) FinishStarters();
            }
            s_done = false;   // ready for the next game
        }

        static void HeadStart()
        {
            s_done = true;
            s_starters.Clear();
            s_starterEvos.Clear();
            s_applying = true;
            try
            {
                for (int i = 0; i < SystemPlayers.GetMaxPlayers(); i++)
                {
                    var pd = SystemPlayers.GetPlayer(i);
                    if (pd == null || !pd.IsActive || pd.GameData == null) continue;
                    var gd = pd.GameData;
                    int guard = 0;
                    while (gd.Level < HeadStartLevel && guard++ < 50) gd.OnCollectXP(Mathf.Max(gd.XPRequired - gd.XP, 0.01f));
                    float gold = HeadStartGoldPerLevel * HeadStartLevel - gd.Gold;
                    if (gold > 0f) gd.OnGoldCollected(gold);
                    gd.OnLevelStart();   // the evolve screen shows the levels as already had, not as this floor's
                    var set = new HashSet<GameObject>();
                    var data = gd.GetMonsterData();
                    if (data != null)
                        foreach (var m in data)
                        {
                            if (m == null || m.GetPrefab() == null) continue;
                            set.Add(m.GetPrefab());
                            var next = m.GetEvolvedPrefabs();
                            if (next != null) foreach (var p in next) if (p != null) s_starterEvos.Add(p.gameObject);
                        }
                    s_starters[gd] = set;
                }
            }
            finally { s_applying = false; }
            FurtherCore.Log.LogInfo("Chaos: head start, every hero at level " + HeadStartLevel + " with " + (HeadStartGoldPerLevel * HeadStartLevel) + " gold");
        }

        /// <summary>Evolve, at random, every starting monster still on its first tier.</summary>
        static void FinishStarters()
        {
            int moved = 0;
            foreach (var kv in s_starters)
            {
                var data = kv.Key.GetMonsterData();
                if (data == null) continue;
                foreach (var m in data)
                {
                    if (m == null || m.GetPrefab() == null || !kv.Value.Contains(m.GetPrefab())) continue;
                    var next = m.GetEvolvedPrefabs();
                    if (next == null || next.Length == 0) continue;
                    var open = new List<Player>();
                    foreach (var p in next) if (p != null && SystemUnlocks.GetUnlocked(p.gameObject)) open.Add(p);
                    if (open.Count == 0) foreach (var p in next) if (p != null) open.Add(p);
                    if (open.Count == 0) continue;
                    m.Evolve(open[Random.Range(0, open.Count)]);
                    moved++;
                }
            }
            if (moved > 0) FurtherCore.Log.LogInfo("Chaos: " + moved + " starting monsters left on tier 1 evolved at random");
        }

        /// <summary>On the pre-game evolve screen: a starting monster's evolution is free; anything else costs as usual
        /// (and nobody has wrath yet), so each line goes up one step.</summary>
        internal static bool FreeEvolve(PlayerGameData gd, GameObject from)
        {
            HashSet<GameObject> set;
            return Picking && gd != null && from != null && s_starters.TryGetValue(gd, out set) && set.Contains(from);
        }

        /// <summary>On the pre-game evolve screen every tier 2 evolution of a starting monster can be picked, locked in
        /// the vault or not: a chaos game has everything present.</summary>
        internal static bool OpenEvolution(GameObject go) { return Picking && go != null && s_starterEvos.Contains(go); }

        /// <summary>Self-test: the game members the head start reaches by name.</summary>
        public static void SelfCheck(System.Action<string> bad)
        {
            foreach (var f in new[] { "m_gameStarted", "m_level" })
                if (AccessTools.Field(typeof(SystemGame), f) == null) bad("chaos head start: SystemGame." + f + " missing");
            if (AccessTools.Field(typeof(MenuEvolve), "m_debugSkipResults") == null) bad("chaos head start: MenuEvolve.m_debugSkipResults missing");
            if (AccessTools.Method(typeof(PlayerGameData), "OnOtherPlayerLeveledUp") == null) bad("chaos head start: PlayerGameData.OnOtherPlayerLeveledUp missing");
            if (AccessTools.Method(typeof(Player), "GetEvolveCost") == null) bad("chaos head start: Player.GetEvolveCost missing");
        }
    }

    [HarmonyPatch(typeof(SystemMain), "LoadLevel", new[] { typeof(string) })]
    static class Patch_ChaosFirstFloor
    {
        static void Prefix(ref string levelName)
        {
            try { ChaosBalance.BeforeFirstFloor(ref levelName); }
            catch (System.Exception e) { FurtherCore.Log.LogError("Chaos head start: " + e); ChaosBalance.Picking = false; }
        }
    }

    [HarmonyPatch(typeof(MenuEvolve), "Start")]
    static class Patch_ChaosPickerSkipResults
    {
        // nothing to tally before the first floor: straight to the evolve menus (the game's own skip path)
        static void Prefix(MenuEvolve __instance) { if (ChaosBalance.Picking) Util.R.Set(__instance, "m_debugSkipResults", true); }
    }

    [HarmonyPatch(typeof(Player), "GetEvolveCost")]
    static class Patch_ChaosPickerCost
    {
        static void Postfix(PlayerGameData gameData, GameObject evolveFrom, ref float __result)
        {
            if (ChaosBalance.FreeEvolve(gameData, evolveFrom)) __result = 0f;
        }
    }

    [HarmonyPatch(typeof(SystemUnlocks), "GetUnlocked", new[] { typeof(GameObject) })]
    static class Patch_ChaosPickerUnlocked
    {
        static void Postfix(GameObject obj, ref bool __result) { if (!__result && ChaosBalance.OpenEvolution(obj)) __result = true; }
    }

    [HarmonyPatch(typeof(PlayerGameData), "OnOtherPlayerLeveledUp")]
    static class Patch_ChaosHeadStartWrath
    {
        // the head start's level-ups pay no wrath: the tier 2 monsters are the head start's wrath
        static bool Prefix() { return !ChaosBalance.Applying; }
    }

    [HarmonyPatch(typeof(PlayerGameData), "OnCollectXP")]
    static class Patch_ChaosXP
    {
        static void Prefix(ref float xp) { if (xp > 0f && ChaosMode.Active && !ChaosBalance.Applying) xp *= ChaosBalance.XPScale; }
    }

    [HarmonyPatch(typeof(PlayerGameData), "OnVitaeCollected")]
    static class Patch_ChaosWrath
    {
        static void Prefix(ref float amount) { if (amount > 0f && ChaosMode.Active) amount *= ChaosBalance.WrathScale; }
    }

    [HarmonyPatch(typeof(PlayerGameData), "OnGoldCollected")]
    static class Patch_ChaosGold
    {
        static void Prefix(ref float amount) { if (amount > 0f && ChaosMode.Active && !ChaosBalance.Applying) amount *= ChaosBalance.GoldScale; }
    }

    /// <summary>Monster players' favour turns into gold here (a hero kill); the gold it pays out is scaled the same.</summary>
    [HarmonyPatch(typeof(PlayerGameData), "ConvertFavourToGold")]
    static class Patch_ChaosFavourGold
    {
        static void Postfix(ref int __result) { if (__result > 0 && ChaosMode.Active) __result = Mathf.RoundToInt(__result * ChaosBalance.GoldScale); }
    }
}
#endif
