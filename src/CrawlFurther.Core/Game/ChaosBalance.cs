using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Game
{
    /// <summary>
    /// How a chaos game paces itself: monster players start on tier 2 monsters, the hero levels faster, monster players
    /// earn wrath (the game's Vitae) faster, and gold comes in a little quicker. A normal game is untouched.
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

        /// <summary>Move each starting monster one step up its tree. An unlocked evolution is picked first; with none
        /// unlocked any of them will do, since a chaos game has everything present.</summary>
        internal static void EvolveStarters(PlayerGameData gd)
        {
            var data = gd != null ? gd.GetMonsterData() : null;
            if (data == null) return;
            int moved = 0;
            foreach (var m in data)
            {
                var next = m != null ? m.GetEvolvedPrefabs() : null;
                if (next == null || next.Length == 0) continue;
                var open = new List<Player>();
                foreach (var p in next) if (p != null && SystemUnlocks.GetUnlocked(p.gameObject)) open.Add(p);
                if (open.Count == 0) foreach (var p in next) if (p != null) open.Add(p);
                if (open.Count == 0) continue;
                m.Evolve(open[Random.Range(0, open.Count)]);
                moved++;
            }
            if (moved > 0) FurtherCore.Log.LogInfo("Chaos: " + moved + " starting monsters begin at tier 2");
        }
    }

    [HarmonyPatch(typeof(PlayerGameData), "SetStartingMonsters")]
    static class Patch_ChaosStarters
    {
        static void Postfix(PlayerGameData __instance)
        {
            if (ChaosBalance.StartEvolved && ChaosMode.Active) ChaosBalance.EvolveStarters(__instance);
        }
    }

    [HarmonyPatch(typeof(PlayerGameData), "OnCollectXP")]
    static class Patch_ChaosXP
    {
        static void Prefix(ref float xp) { if (xp > 0f && ChaosMode.Active) xp *= ChaosBalance.XPScale; }
    }

    [HarmonyPatch(typeof(PlayerGameData), "OnVitaeCollected")]
    static class Patch_ChaosWrath
    {
        static void Prefix(ref float amount) { if (amount > 0f && ChaosMode.Active) amount *= ChaosBalance.WrathScale; }
    }

    [HarmonyPatch(typeof(PlayerGameData), "OnGoldCollected")]
    static class Patch_ChaosGold
    {
        static void Prefix(ref float amount) { if (amount > 0f && ChaosMode.Active) amount *= ChaosBalance.GoldScale; }
    }

    /// <summary>Monster players' favour turns into gold here (a hero kill); the gold it pays out is scaled the same.</summary>
    [HarmonyPatch(typeof(PlayerGameData), "ConvertFavourToGold")]
    static class Patch_ChaosFavourGold
    {
        static void Postfix(ref int __result) { if (__result > 0 && ChaosMode.Active) __result = Mathf.RoundToInt(__result * ChaosBalance.GoldScale); }
    }
}
