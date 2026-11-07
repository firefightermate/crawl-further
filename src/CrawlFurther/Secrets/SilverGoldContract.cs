using System.Collections.Generic;

namespace CrawlFurther.Content.Secrets
{
    // Shared hooks for the secret monster lines. SilverPack and GoldSecretPack fill them in once their monsters are built;
    // GhostSlots, CustomGod and the checks only read them, so they never reference the packs directly.

    /// <summary>The three unique silver tier-3 monsters, reachable ONLY through the silver ghost's tier-3 orb upgrade.</summary>
    public static class SilverUniques
    {
        /// <summary>Prefab ids (e.g. "ModSilverX") of the three uniques, in order: common A, common B, legendary.</summary>
        public static readonly List<string> Ids = new List<string>();

        /// <summary>
        /// Called by GhostSlots when a silver ghost with 8 orbs takes a TIER-3 body. Returns the prefab id of a silver
        /// unique to become instead, or null to become the body's own Silver Ascended form. Odds are owned here.
        /// </summary>
        public static System.Func<string, string> RollTier3 = current => null;
    }

    /// <summary>The secret gold monster: a 7-monster tree (1 / 2 / 4) offered ONLY in the gold idol's 4th starter slot.</summary>
    public static class GoldSecret
    {
        /// <summary>Starter prefab id (e.g. "ModGoldX"); null until GoldSecretPack registers it.</summary>
        public static string StarterId;
        /// <summary>Every prefab id of the tree (starter, 2 tier-2, 4 tier-3).</summary>
        public static readonly List<string> TreeIds = new List<string>();
    }
}
