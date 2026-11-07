using System;
using HarmonyLib;

namespace CrawlFurther.Content.Ghosts
{
    using CrawlFurther.Gods;
    using CrawlFurther.UI;
    using CrawlFurther.Util;

    /// <summary>
    /// The challenges that earn the Gleaner, Poltergeist and Binder their own blobs (Mote, Spitter, Gel; GhostBlobs). Each
    /// is played as that form with what it has before its blob: the Gleaner gathers ectoplasm, the Poltergeist throws hex
    /// bolts, the Binder spawns regular blobs. Pace: a Gleaner banks 80 to 130 ectoplasm a game, a Poltergeist lands 10 to
    /// 20 bolts, a ghost spawns 12 to 20 blobs, so each takes about three games of that form. Only human players count,
    /// and play that UnlockHooks.Excluded names (test mode, the tutorial, challenge mode) never does. The King needs no
    /// challenge: it is the silver and gold ghosts' own, open as soon as those forms are.
    /// Counters of the 1.1.0 test builds (MotesSpawned, SpitHits, TitansFused) are no longer read; they stay in the file.
    /// </summary>
    public static class BlobChallenges
    {
        /// <summary>Challenge ids (GhostBlobDef.unlock).</summary>
        public const string Mote = "PickMote", Spitter = "PickSpitter", Gel = "PickGel";
        /// <summary>Their counters in CrawlFurther.Unlocks.cfg.</summary>
        public const string StatGleaned = "GleanerEcto", StatBolts = "HexBoltHits", StatBinderBlobs = "BinderBlobs";

        public static void Register()
        {
            Add(Mote, "HARVEST", "Gather 250 ectoplasm as the Gleaner", StatGleaned, 250, "MOTE BLOB");
            Add(Spitter, "CUTLERY", "Hit the hero with 40 hex bolts", StatBolts, 40, "SPITTER BLOB");
            Add(Gel, "BINDING", "Spawn 40 blobs as the Binder", StatBinderBlobs, 40, "GEL BLOB");
        }

        static void Add(string id, string title, string text, string stat, int target, string slot)
        {
            Unlocks.Add(new UnlockDef { id = id, title = title, text = text, stat = stat, target = target, slot = slot, tier = SlotTier.Silver });
        }

        static bool Counts(PlayerData pd, GhostForm form)
        {
            return pd != null && pd.IsHuman && !UnlockHooks.Excluded() && GhostPack.FormOf(pd) == form;
        }

        /// <summary>A ghost's Back spawned a blob (the Binder's count).</summary>
        public static void BlobSpawned(PlayerData pd)
        {
            if (Counts(pd, GhostForm.Binder)) Unlocks.Count(StatBinderBlobs);
        }

        /// <summary>Ectoplasm a Gleaner banked (after its lower worth and the cap).</summary>
        public static void Gleaned(PlayerData pd, float amount)
        {
            if (amount > 0f && Counts(pd, GhostForm.Gleaner)) Unlocks.CountFraction(StatGleaned, amount);
        }

        /// <summary>A Poltergeist's hex bolt hit the hero.</summary>
        public static void BoltLanded(PlayerData pd)
        {
            if (Counts(pd, GhostForm.Poltergeist) && !pd.IsHero) Unlocks.Count(StatBolts);
        }

        /// <summary>Every blob challenge is registered and a blob opens with it.</summary>
        public static void SelfCheck(Action<string> bad)
        {
            foreach (var id in new[] { Mote, Spitter, Gel })
            {
                if (Unlocks.Find(id) == null) bad("Unlocks: no blob challenge " + id);
                bool used = false;
                foreach (var b in CrawlFurther.Ghosts.GhostBlobs.All) if (b.unlock == id) used = true;
                if (!used) bad("Unlocks: blob challenge " + id + " opens no blob");
            }
        }
    }

    /// <summary>Counts the Poltergeist's hex bolts that hit the hero (BlobChallenges.Spitter).</summary>
    [HarmonyPatch(typeof(Health), "Damage", new[] { typeof(DamageInfo), typeof(bool) })]
    static class Patch_HexBoltHits
    {
        static void Postfix(Health __instance, DamageInfo damage, bool __result)
        {
            if (!__result || damage == null || damage.m_source == null || damage.m_source.m_source == null) return;
            try
            {
                var hero = SystemPlayers.GetHeroPlayerData();
                if (hero == null || hero.GameObject != __instance.gameObject) return;
                if (GhostPack.HexBolt == null || ModUtil.PrefabName(damage.m_source.m_source) != GhostPack.HexBolt.name) return;
                BlobChallenges.BoltLanded(damage.m_source.m_sourcePlayer);
            }
            catch (Exception e) { UnlockHooks.Warn("hex bolt hits", e); }
        }
    }

    /// <summary>Counts the ectoplasm a Gleaner banks (BlobChallenges.Mote), the way Core counts a ghost's: what the game
    /// recorded as earned, after the cap, refunds left out.</summary>
    [HarmonyPatch(typeof(PlayerGameData), "OnEctoplasmCollected")]
    static class Patch_GleanerGathered
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
            if (__state < 0f || GhostV11.Refunding) return;
            try
            {
                var pd = SystemPlayers.GetPlayer(R.Get<int>(__instance, "m_ownerPlayerId"));
                BlobChallenges.Gleaned(pd, Earned(__instance) - __state);
            }
            catch (Exception e) { UnlockHooks.Warn("gleaned ectoplasm", e); }
        }
    }
}
