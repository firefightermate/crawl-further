using System.Collections.Generic;

namespace CrawlFurther.Content
{
    using CrawlFurther.Ghosts;
    using CrawlFurther.Gods;
    using CrawlFurther.Heroes;
    using CrawlFurther.Items;
    using CrawlFurther.Monsters;
    using CrawlFurther.UI;
    using CrawlFurther.Util;
    using CrawlFurther.Content.Bosses;
    using CrawlFurther.Content.Ghosts;
    using CrawlFurther.Content.Gods;
    using CrawlFurther.Content.Gods.BelMora;
    using CrawlFurther.Content.Gods.Jinx;
    using CrawlFurther.Content.Gods.Kaurn;
    using CrawlFurther.Content.Gods.Ossivar;
    using CrawlFurther.Content.Gods.Sylvene;
    using CrawlFurther.Content.Gods.Umbrael;
    using CrawlFurther.Content.Gods.Vhorrul;
    using CrawlFurther.Content.Gods.Ysveld;
    using CrawlFurther.Content.Gods.Zhekra;
    using CrawlFurther.Content.Heroes;
    using CrawlFurther.Content.Library;
    using CrawlFurther.Content.Items;
    using CrawlFurther.Content.Objects;
    using CrawlFurther.Content.Secrets;
    using CrawlFurther.Content.Tips;
    using CrawlFurther.Content.Weapons;

    /// <summary>
    /// Connects Crawl: Further to Core once the game has booted: registers the content tables and hooks Core reads,
    /// queues the content packs (in the order 0.10.0 registered them) and adds the self-test sections.
    /// </summary>
    public static class ContentSetup
    {
        /// <summary>The sheet of every item's and weapon's shop pedestal picture (art/out_pedestals).</summary>
        public const string PedestalSheet = "ShopPedestals";
        /// <summary>The tips group and pause topic of the mod bosses (data/tips/tips_bosses.json, the "bosses" page).</summary>
        public const string BossTopic = "bosses";

        public static void Install()
        {
            Branding.Set(new BrandingDef
            {
                name = Plugin.NAME, version = Plugin.VERSION,
                wordmark = "BrandFurther", spark = "BrandSpark", menuPip = "BrandPip", menuMote = "BrandMote",
            });
            ModMusic.AddFolder(System.IO.Path.Combine(Plugin.ModDir, "music"));
            // tools/challenge_sim.py: each tier's median monster is a little stronger than the game's own of that tier
            // (about x1.08); a monster is the same in a vault challenge as in a normal game
            TierRules.StarterMinHealth = 4f;
            TierRules.StarterDamage = 1.62f;     // with the floor: each tier a little stronger than the game's own (about x1.08)
            TierRules.T2Health = 1.14f;
            TierRules.T2Damage = 1.13f;
            Game.ContinueGame.Enabled = Plugin.I.Config.Bind("Game", "ContinueAfterWin", true,
                "When the hero beats the boss, offer to keep playing with two more tries at the boss.").Value;
            Game.ChaosMode.Enabled = Plugin.I.Config.Bind("Game", "Chaos", true,
                "Chaos: a Chaos entry on the main menu, and continued games play as chaos games (the hero holds two spells).").Value;
            ShopPedestal.AddSheet(PedestalSheet);
            // the vanilla choices in the mod's picker lists are drawn as mod sheets: no gem on them
            foreach (var id in new[] { "HeroWanderer", "HeroWanderer_P1", "HeroWanderer_P2", "HeroWanderer_P3", "HeroWanderer_P4", "GhostWisp" })
                ModGem.Exclude(id);
            foreach (var f in GhostPack.Forms) GhostForms.Register(f);
            GhostForms.FormOf = GhostPack.DefOf;
            OriginList.Register();
            OriginColours.Register();
            Statues.Sheets.Add("ModStatues");
            AddTips();
            FurtherVault.Register();
            SlotChallenges.Register();
            BlobChallenges.Register();
            // each monster's own challenge goal (tools/challenge_goals.py); a def's own challenge still wins
            foreach (var kv in Monsters.ChallengeGoalsGenerated.Goals)
                if (Challenges.Of("Mod" + kv.Key) == null) Challenges.Register("Mod" + kv.Key, new ChallengeDef { goal = kv.Value });

            // monsters and heroes in play
            MonsterEvents.PlayerAwake += HeroItemHooks.PlayerAwake;
            ItemRegistry.AddDamageHook(HeroItemHooks.Damage);
            MonsterEvents.AttackSpawned += HeroItemHooks.EffectSpawned;
            ImpactThemes.Register();
            Unlocks.EctoRefunding = () => GhostV11.Refunding;
            HeroClasses.CustomHeroes = new CustomHeroSlots();

            // gods and idols
            SlotGods.AddEntries = GodSlots.AddItems;
            SlotGods.HideExtras = GodSlots.HideExtras;
            SlotGods.Redraw = GodSlots.Invalidate;
            SlotGods.TierOf = d => { var r = CustomGod.Of(d); return r != null ? r.tier : SlotTier.Normal; };
            SlotGods.PageGodsOf = IdolGodNames;
            SlotGods.PerkGodOf = d => { var r = CustomGod.Of(d); return r != null ? r.PerkGod : null; };
            Statues.Exclude = id => SilverUniques.Ids.Contains(id) || GoldSecret.TreeIds.Contains(id) || SecretStatues.Is(id);

            Further.AddPack("Vhorrul", VhorrulPack.Register);
            Further.AddPack("Ossivar", OssivarPack.Register);
            Further.AddPack("Sylvene", SylvenePack.Register);
            Further.AddPack("Umbrael", UmbraelPack.Register);
            Further.AddPack("Bel'Mora", BelMoraPack.Register);
            Further.AddPack("Jinx", JinxPack.Register);
            Further.AddPack("Zhekra", ZhekraPack.Register);
            Further.AddPack("Kaurn", KaurnPack.Register);
            Further.AddPack("Ysveld", YsveldPack.Register);
            Further.AddPack("Silver", SilverPack.Register);
            Further.AddPack("Gold Secret", GoldSecretPack.Register);
            Further.AddPack("Secret Statues", StatuePack.Register);
            Further.AddPack("Ghosts", GhostPack.Register);
            Further.AddPack("Bosses", BossPack.Register);
            Further.AddPack("Items", ItemPack.Register);
            Further.AddPack("Items2", ItemPack2.Register);
            Further.AddPack("Items3", ItemPack3.Register);
            Further.AddPack("Weapons", WeaponPack.Register);
            Further.AddPack("Objects", ObjectPack.Register);
            Further.AddPack("Objects B", ObjectPack2.Register);
            Further.AddPack("Monster secrets", MonsterSecrets.Register);   // last: needs the silver and gold monsters built

            ContentChecks.AddSections();
        }

        /// <summary>The monster tips, vault lines and pause pages (data/tips, merged into MonsterTipsData by tools/merge_tips.py).</summary>
        static void AddTips()
        {
            // the bosses' tips (tips_bosses.json) and their pause page share one id; with the bosses off neither shows
            bool bosses = BossPack.Enabled;
            foreach (var kv in MonsterTipsData.Tips)
            {
                string group;
                MonsterTipsData.Group.TryGetValue(kv.Key, out group);
                if (!bosses && group == BossTopic) continue;
                TipRegistry.Add(kv.Key, kv.Value, group);
            }
            foreach (var kv in MonsterTipsData.Alias) TipRegistry.AddAlias(kv.Key, kv.Value);
            foreach (var key in MonsterTipsData.VaultOrder)
            {
                string group;
                if (!bosses && MonsterTipsData.Group.TryGetValue(key, out group) && group == BossTopic) continue;
                TipRegistry.AddVaultLine(key, MonsterTipsData.Vault[key].Key, MonsterTipsData.Vault[key].Value);
            }
            foreach (var t in PauseTipsData.Topics)
                if (bosses || t.id != BossTopic) TipRegistry.AddTopic(t);
            TipRegistry.TopicOrder.AddRange(new[] { "status", "icons", "ghosts", "slots", "unlocks" });
            if (bosses) TipRegistry.TopicOrder.Add(BossTopic);
            TipRegistry.GhostFormTopic = "ghosts";
            // every ghost form but the plain Wisp has its own tip, "ModGhost" + the form (tips_ghosts.json)
            MonsterTips.GhostKey = body =>
            {
                var def = GhostPack.DefOf(body.GetPlayerData());
                return def != null && !GhostForms.IsDefault(def) ? "ModGhost" + def.id : null;
            };
        }

        /// <summary>A silver / gold idol's pause pages: the perk god's, then the god of every starter.</summary>
        static List<string> IdolGodNames(Deity d)
        {
            var idol = CustomGod.Of(d);
            if (idol == null) return null;
            var names = new List<string> { idol.perk };
            foreach (var n0 in idol.starters)
                foreach (var s in CustomGod.Starters())
                    if (s.p.gameObject.name == n0) names.Add(s.god.GetName());
            return names;
        }
    }
}
