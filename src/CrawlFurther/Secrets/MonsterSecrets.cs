using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Content.Secrets
{
    using CrawlFurther.Gods;
    using CrawlFurther.UI;
    using CrawlFurther.Content.Gods;

    /// <summary>The Crawl: Further secrets that are monsters: the silver uniques and the gold secret line.</summary>
    public static class MonsterSecrets
    {
        /// <summary>The three silver uniques and the seven-monster gold line, found when a human player becomes one. A
        /// content pack queued after every other (SilverUniques.Ids and GoldSecret.TreeIds are filled by then).</summary>
        public static void Register()
        {
            const string silverOdds = "Rare";
            var silver = new Dictionary<string, string[]>
            {
                { "ModSilverMoonwarden", new[] { "Ascend a final form with eight silver orbs: a moon-faced knight may rise.", silverOdds } },
                { "ModSilverCometStag", new[] { "Ascend a final form with eight silver orbs and listen for hooves.", silverOdds } },
                { "ModSilverAstrarch", new[] { "Ascend a final form with eight orbs. Very rarely, you become a star.", "Legendary" } },
            };
            foreach (var id in SilverUniques.Ids)
            {
                string[] r;
                if (!silver.TryGetValue(id, out r)) r = new[] { "A silver ghost with eight orbs may become something rare.", "Rare" };
                Secrets.AddMonster(id, "Silver", r[0], r[1]);
            }
            var gold = new Dictionary<string, string[]>
            {
                { "ModGoldMimic", new[] { "Gold has four hands. In the last, past every face, a box breathes.", "Hidden: somewhere gilded" } },
                { "ModGoldWarden", new[] { "Evolve the coffer and it stands up, swinging a key on a chain.", "Hidden: the Coffer Mimic line" } },
                { "ModGoldRegent", new[] { "Evolve the coffer the other way and something crowned climbs out.", "Hidden: the Coffer Mimic line" } },
                { "ModGoldWyrm", new[] { "A warden that hoards long enough grows scales and molten breath.", "Hidden: the Vault Warden line" } },
                { "ModGoldVault", new[] { "Down the warden's other road, every blow is banked.", "Hidden: the Vault Warden line" } },
                { "ModGoldSovereign", new[] { "Crown the regent, and the hero will be told to kneel.", "Hidden: the Gilt Regent line" } },
                { "ModGoldTreasurer", new[] { "The regent's other heir carries a quill and a ledger.", "Hidden: the Gilt Regent line" } },
            };
            foreach (var id in GoldSecret.TreeIds)
            {
                string[] r;
                if (!gold.TryGetValue(id, out r)) r = new[] { "Somewhere in the gold idol's secret line.", "Hidden" };
                Secrets.AddMonster(id, "Gold", r[0], r[1]);
            }
        }

        /// <summary>Every silver unique and gold secret monster has its page.</summary>
        public static void SelfCheck(Action<string> bad)
        {
            if (SilverUniques.Ids.Count > 0 && !SilverUniques.Ids.TrueForAll(i => Secrets.Find(i) != null)) bad("secrets: a silver unique is not registered");
            if (GoldSecret.TreeIds.Count > 0 && !GoldSecret.TreeIds.TrueForAll(i => Secrets.Find(i) != null)) bad("secrets: a gold secret monster is not registered");
        }
    }

    /// <summary>The gold idol editor stores a pick that includes the secret starter: the Coffer Mimic is found.</summary>
    [HarmonyPatch(typeof(CustomGod), "Store")]
    static class Patch_SecretIdolPick
    {
        static void Postfix(CustomGod.Record r)
        {
            try
            {
                if (r != null && r.tier == SlotTier.Gold && !string.IsNullOrEmpty(GoldSecret.StarterId) && r.starters != null && r.starters.Contains(GoldSecret.StarterId))
                    Secrets.Found(GoldSecret.StarterId);
            }
            catch (Exception e) { Plugin.Log.LogWarning("Secret idol hook: " + e.Message); }
        }
    }
}
