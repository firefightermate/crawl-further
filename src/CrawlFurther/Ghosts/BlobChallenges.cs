using System;
using HarmonyLib;

namespace CrawlFurther.Content.Ghosts
{
    using CrawlFurther.Gods;
    using CrawlFurther.UI;
    using CrawlFurther.Util;

    /// <summary>
    /// The challenges that open the Mote, Spitter and Gel blobs for every ghost form (GhostBlobs). Each is played as the
    /// form whose own blob it is, so it opens after a few games of that form: a Gleaner spawns 30 to 40 Motes a game, a
    /// Poltergeist's Spitters land 15 to 30 spits, a Binder fuses 1 to 3 Titans. Only human players count, and play that
    /// UnlockHooks.Excluded names (test mode, the tutorial, challenge mode) never does. The King needs no challenge: it is
    /// the silver and gold ghosts' own, open as soon as those forms are.
    /// </summary>
    public static class BlobChallenges
    {
        /// <summary>Challenge ids (GhostBlobDef.unlock).</summary>
        public const string Mote = "PickMote", Spitter = "PickSpitter", Gel = "PickGel";
        /// <summary>Their counters in CrawlFurther.Unlocks.cfg.</summary>
        public const string StatMotes = "MotesSpawned", StatSpits = "SpitHits", StatTitans = "TitansFused";

        public static void Register()
        {
            Add(Mote, "SWARM", "Spawn 100 Motes as the Gleaner", StatMotes, 100, "MOTE BLOB");
            Add(Spitter, "SPATTER", "Hit the hero with Spitter goo 60 times", StatSpits, 60, "SPITTER BLOB");
            Add(Gel, "FUSION", "Fuse 3 Titans as the Binder", StatTitans, 3, "GEL BLOB");
        }

        static void Add(string id, string title, string text, string stat, int target, string slot)
        {
            Unlocks.Add(new UnlockDef { id = id, title = title, text = text, stat = stat, target = target, slot = slot, tier = SlotTier.Silver });
        }

        static bool Counts(PlayerData pd) { return pd != null && pd.IsHuman && !UnlockHooks.Excluded(); }

        /// <summary>A Gleaner's Mote came out of Back (the pair counts twice).</summary>
        public static void MoteSpawned(PlayerData pd)
        {
            if (Counts(pd) && GhostPack.FormOf(pd) == GhostForm.Gleaner) Unlocks.Count(StatMotes);
        }

        /// <summary>A Binder fused three Gels.</summary>
        public static void TitanFused(PlayerData pd)
        {
            if (Counts(pd) && GhostPack.FormOf(pd) == GhostForm.Binder) Unlocks.Count(StatTitans);
        }

        /// <summary>A Spitter's goo glob hit the hero: counts for the player behind that Spitter.</summary>
        public static void SpitLanded(PlayerData pd)
        {
            if (Counts(pd) && !pd.IsHero) Unlocks.Count(StatSpits);
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

    /// <summary>Counts Spitter goo that hits the hero (BlobChallenges.Spitter).</summary>
    [HarmonyPatch(typeof(Health), "Damage", new[] { typeof(DamageInfo), typeof(bool) })]
    static class Patch_BlobSpitHits
    {
        static void Postfix(Health __instance, DamageInfo damage, bool __result)
        {
            if (!__result || damage == null || damage.m_source == null || damage.m_source.m_source == null) return;
            try
            {
                var hero = SystemPlayers.GetHeroPlayerData();
                if (hero == null || hero.GameObject != __instance.gameObject) return;
                if (GhostPack.GooGlob == null || ModUtil.PrefabName(damage.m_source.m_source) != GhostPack.GooGlob.name) return;
                var pd = damage.m_source.m_sourcePlayer;
                if (pd == null && damage.m_source.m_sourceOwner != null)
                {
                    var p = damage.m_source.m_sourceOwner.GetComponent<Player>();
                    if (p != null) pd = R.Get<PlayerData>(p, "m_spawner");
                }
                BlobChallenges.SpitLanded(pd);
            }
            catch (Exception e) { UnlockHooks.Warn("spit hits", e); }
        }
    }
}
