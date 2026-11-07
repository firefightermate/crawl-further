using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.UI
{
    using CrawlFurther.Util;

    // The game hooks that count the Unlocks.Stat... counters. Only human players count (bots never advance a challenge),
    // and play Excluded() names never does.

    /// <summary>The hero kills a monster or fodder (StatHeroKills); a monster kills the hero (StatHeroSlain).</summary>
    [HarmonyPatch(typeof(PlayerData), "OnKilledPlayer")]
    static class Patch_UnlockKills
    {
        // a prefix: who is the hero is read before anything this kill sets in motion
        static void Prefix(PlayerData __instance, PlayerData other)
        {
            try
            {
                if (__instance == null || other == null || !__instance.IsHuman || UnlockHooks.Excluded()) return;
                if (__instance.IsHero && !other.IsHero) Unlocks.Count(Unlocks.StatHeroKills);
                else if (!__instance.IsHero && other.IsHero) Unlocks.Count(Unlocks.StatHeroSlain);
            }
            catch (Exception e) { UnlockHooks.Warn("kills", e); }
        }
    }

    /// <summary>A human who is the hero when the final boss falls has won the game (StatWins).</summary>
    [HarmonyPatch(typeof(PlayerData), "OnGameComplete")]
    static class Patch_UnlockWins
    {
        static void Prefix(PlayerData __instance, bool won)
        {
            try
            {
                if (won && __instance != null && __instance.IsHuman && __instance.IsHero && !UnlockHooks.Excluded()) Unlocks.Count(Unlocks.StatWins);
                Unlocks.Save();
            }
            catch (Exception e) { UnlockHooks.Warn("wins", e); }
        }
    }

    /// <summary>Ectoplasm a ghost actually banked (after the cap), per human player (StatEcto).</summary>
    [HarmonyPatch(typeof(PlayerGameData), "OnEctoplasmCollected")]
    static class Patch_UnlockEcto
    {
        static float Earned(PlayerGameData gd)
        {
            var s = gd.StatsGame;
            return s.GetStat(PlayerStats.eStat.EctoplasmEarned) + s.GetStat(PlayerStats.eStat.EctoplasmEarnedBoss);
        }

        static void Prefix(PlayerGameData __instance, out float __state)
        {
            __state = -1f;
            try { __state = Earned(__instance); } catch { }
        }

        static void Postfix(PlayerGameData __instance, float __state)
        {
            try
            {
                if (__state < 0f || (Unlocks.EctoRefunding != null && Unlocks.EctoRefunding()) || UnlockHooks.Excluded()) return;
                var pd = SystemPlayers.GetPlayer(R.Get<int>(__instance, "m_ownerPlayerId"));
                if (pd == null || !pd.IsHuman) return;
                Unlocks.CountFraction(Unlocks.StatEcto, Earned(__instance) - __state);
            }
            catch (Exception e) { UnlockHooks.Warn("ectoplasm", e); }
        }
    }

    /// <summary>Every evolution a human makes (StatEvolutions), and each distinct final form reached (StatFinals).</summary>
    [HarmonyPatch(typeof(PlayerMonsterData), "Evolve", new[] { typeof(int) })]
    static class Patch_UnlockEvolve
    {
        static void Postfix(PlayerMonsterData __instance, bool __result)
        {
            try
            {
                if (!__result || UnlockHooks.Excluded()) return;
                var pd = UnlockHooks.OwnerOf(__instance);
                if (pd == null || !pd.IsHuman) return;
                Unlocks.Count(Unlocks.StatEvolutions);
                var prefab = __instance.GetPrefab();
                var p = prefab != null ? prefab.GetComponent<Player>() : null;
                if (p != null && UnlockHooks.IsFinal(p)) Unlocks.CountDistinct(Unlocks.StatFinals, prefab.name);
            }
            catch (Exception e) { UnlockHooks.Warn("evolve", e); }
        }
    }

    /// <summary>Helpers for the counting hooks.</summary>
    public static class UnlockHooks
    {
        /// <summary>Play that never counts: the tutorial, challenge mode and the hero-battle mini mode (the same games
        /// vanilla withholds its kill XP from, Player.OnKilled), and anything while test mode is on.</summary>
        public static bool Excluded()
        {
            try
            {
                if (Testing.TestMode.Active) return true;
                if (SystemTutorial.GetActive()) return true;
                if (Singleton<SystemMenu>.HasInstance() && SystemMenu.GetChallengeMode()) return true;
                if (Singleton<SystemLevel>.HasInstance() && SystemLevel.GetHeroBattleActive()) return true;
            }
            catch { }
            return false;
        }

        static readonly HashSet<string> s_warned = new HashSet<string>();
        public static void Warn(string what, Exception e)
        {
            if (s_warned.Add(what)) FurtherCore.Log.LogWarning("Unlock hook (" + what + "): " + e.Message);
        }

        /// <summary>The player whose monster list holds <paramref name="md"/>.</summary>
        public static PlayerData OwnerOf(PlayerMonsterData md)
        {
            var all = SystemPlayers.GetPlayers();
            if (all == null) return null;
            foreach (var pd in all)
            {
                if (pd == null || pd.GameData == null) continue;
                var arr = pd.GameData.GetMonsterData();
                if (arr == null) continue;
                foreach (var m in arr) if (m == md) return pd;
            }
            return null;
        }

        /// <summary>A final form: nothing further to evolve into (every vanilla and mod tree ends in these).</summary>
        public static bool IsFinal(Player p)
        {
            var to = p.GetEvolveTo();
            if (to == null || to.Length == 0) return true;
            foreach (var t in to) if (t != null && !t.GetIsEvolveCircular(p.gameObject)) return false;
            return true;
        }

        /// <summary>Every final form reachable from any god's starters (what StatFinals can count).</summary>
        public static List<Player> AllFinals()
        {
            var seen = new HashSet<Player>();
            var finals = new List<Player>();
            var stack = new Stack<Player>();
            foreach (var d in SystemDeity.GetDeities())
            {
                if (d == null || d.GetIsTrial()) continue;
                foreach (var go in d.GetStartingMonsters()) if (go != null && go.GetComponent<Player>() != null) stack.Push(go.GetComponent<Player>());
            }
            while (stack.Count > 0)
            {
                var p = stack.Pop();
                if (p == null || !seen.Add(p)) continue;
                if (IsFinal(p)) { finals.Add(p); continue; }
                foreach (var t in p.GetEvolveTo()) if (t != null) stack.Push(t);
            }
            return finals;
        }

        /// <summary>Self-test: the challenges, and enough final forms for any challenge that counts them.</summary>
        public static void SelfCheck(Action<string> bad)
        {
            Unlocks.SelfCheck(bad);
            int finals = -1;
            foreach (var c in Unlocks.All)
            {
                if (c.stat != Unlocks.StatFinals) continue;
                if (finals < 0) finals = AllFinals().Count;
                if (finals < c.target * 3 / 2) bad("Unlocks: only " + finals + " final forms exist for a " + c.target + "-form challenge");
            }
            UnlockToast.Ensure();
        }
    }
}
