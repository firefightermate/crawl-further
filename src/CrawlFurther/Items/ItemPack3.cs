using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Content.Items
{
    using CrawlFurther.Art;
    using CrawlFurther.Items;
    using CrawlFurther.Monsters;
    using CrawlFurther.UI;
    using CrawlFurther.Util;
    using CrawlFurther.Content.Weapons;

    /// <summary>
    /// The two secret items, for the room objects that use them (ObjectPack2's Cracked Wall drops the Skeleton Key; its Mysterious Keyhole
    /// checks and consumes it, and may hand out the Gilded Heart as its reward). Everything is null-safe: before the
    /// content has registered (or if an item failed to build) the getters return null and the actions return false/null.
    /// Neither item is ever in a shop pool; both are in the vault's ITEMS grid and the SECRETS group "Items".
    /// </summary>
    public static class SecretItems
    {
        /// <summary>ItemDef id of the Skeleton Key (its Powerup prefab is "Mod" + this).</summary>
        public const string SkeletonKeyId = "ArtifactSkeletonKey";
        public const string SkeletonKeyPrefab = "ModArtifactSkeletonKey";
        /// <summary>ItemDef id of the Gilded Heart (a reward for whatever the key opens).</summary>
        public const string GildedHeartId = "ArtifactGildedHeart";
        public const string GildedHeartPrefab = "ModArtifactGildedHeart";

        public static Powerup SkeletonKey { get { return ItemPack3.Get(SkeletonKeyId); } }
        public static Powerup GildedHeart { get { return ItemPack3.Get(GildedHeartId); } }

        /// <summary>Spawn the Skeleton Key as a free pickup at <paramref name="pos"/> (it hops out and lands, the hero walks
        /// onto it after 0.5 s; hero only, no cost). Returns the pickup instance, or null.</summary>
        public static GameObject DropSkeletonKey(Vector3 pos) { return ItemPack3.DropPickup(SkeletonKeyId, pos); }
        /// <summary>Spawn the Gilded Heart as a free pickup at <paramref name="pos"/>.</summary>
        public static GameObject DropGildedHeart(Vector3 pos) { return ItemPack3.DropPickup(GildedHeartId, pos); }
        /// <summary>Spawn any ItemPack3 item as a free pickup (ids are the ItemDef ids in ItemPack3.Items).</summary>
        public static GameObject Drop(string itemId, Vector3 pos) { return ItemPack3.DropPickup(itemId, pos); }

        public static bool HasSkeletonKey(PlayerData hero) { return Has(hero, SkeletonKeyId); }
        /// <summary>Remove the key from the hero (the keyhole takes it). True if the hero had it.</summary>
        public static bool ConsumeSkeletonKey(PlayerData hero) { return Take(hero, SkeletonKeyId); }

        public static bool Has(PlayerData pd, string itemId)
        {
            var pu = ItemPack3.Get(itemId);
            return pu != null && pd != null && pd.GameData != null && pd.GameData.HasPowerup(pu);
        }

        /// <summary>Give an item straight to a player (no pickup), as if bought.</summary>
        public static bool Give(PlayerData pd, string itemId)
        {
            var pu = ItemPack3.Get(itemId);
            if (pu == null || pd == null) return false;
            Powerup.Collect(pu, pd);
            return true;
        }

        public static bool Take(PlayerData pd, string itemId)
        {
            if (!Has(pd, itemId)) return false;
            var pu = ItemPack3.Get(itemId);
            pd.GameData.RemovePowerupPrefab(pu);
            var go = pd.GameObject;
            var perks = go != null ? go.GetComponent<HeroPerks3>() : null;
            if (perks != null) perks.Refresh();
            return true;
        }
    }

    /// <summary>
    /// The third wave of shop items: 7 stat potions, 7 fun trinkets, 9 game-changing little trinkets and 2 secret
    /// items. Art: tools/sprites/items3_icons.py (icons, shop pictures, HUD icons, pedestal drawings) and
    /// tools/sprites/items3_fx.py (world effects and indicators), both into art/out_items3.
    /// </summary>
    public static class ItemPack3
    {
        static readonly Dictionary<string, Powerup> s_built = new Dictionary<string, Powerup>();
        public static Powerup Get(string id) { Powerup p; return id != null && s_built.TryGetValue(id, out p) ? p : null; }

        // potions
        public static Powerup TrollMarrow, WyrmBlood, HaresDew, BerserkerGrog, Stoneskin, Quicksilver, ChaosBrew;
        // fun
        public static Powerup PartyHat, BardLute, PetFerret, BubblePipe, RubberDuck, FireflyJar, DancingShoes;
        // trinkets
        public static Powerup Whetstone, PhoenixFeather, SiphonGem, GluttonsFork, TallyStick, GamblersCoin, Bandage, WantedPoster, IronBoots;
        // secrets
        public static Powerup SkeletonKey, GildedHeart;

        // world art
        public static GameObject Confetti, LuteNote, Bubble, DuckSquawk, FireflyZapHit, FireflyZap, DanceStep, WhetSpark, PhoenixBurst,
                                 SiphonWisp, ForkHeal, CoinHeads, CoinTails, BandageAbsorb, BootsClank, KeyCollect, HeartCollect, HeartGlow;
        public static GameObject[] Quaff = new GameObject[8], TallyPops = new GameObject[5], ChaosRolls = new GameObject[6];
        public static GameObject FerretTmpl, FireflyTmpl;
        public static exSpriteAnimClip FerretIdle, FerretRun, FireflyGlow, FireflyDim;
        static readonly Dictionary<string, GameObject> s_pickups = new Dictionary<string, GameObject>();
        // indicators
        public static StatusOverlayDef IndSluggish, IndBurn, IndShaky, IndHat, IndKey, IndBandage, IndWanted, IndHeart;

        // quaff burst order (FxItem3Quaff anims)
        public static readonly string[] QuaffAnims = { "Marrow", "Wyrm", "Hare", "Grog", "Stone", "Quick", "Chaos", "Heart" };
        // chaos roll pops: up stat then down stat (V = vitality, S = strength, D = dexterity)
        public static readonly string[] ChaosAnims = { "VS", "VD", "SV", "SD", "DV", "DS" };

        static PlayerModifier Mul(PlayerModifier.eType t, float v)
        {
            return new PlayerModifier { m_modify = t, m_type = ValueModifier.eModifierType.Multiply, m_value = v, m_priority = 0f };
        }

        static Action<GameObject, Powerup> Passive(Action<Powerup> keep, params PlayerModifier[] mods)
        {
            return (go, pu) =>
            {
                R.Set(pu, "m_modifiers", new List<PlayerModifier>(mods));
                R.Set(pu, "m_heroStatModifiers", new List<HeroStatModifier>());
                if (keep != null) keep(pu);
            };
        }

        static Action<GameObject, Powerup> Potion(Action<Powerup> keep, params int[] stats)
        {
            return (go, pu) =>
            {
                var list = new List<HeroStatModifier>();
                for (int i = 0; i + 1 < stats.Length; i += 2) list.Add(new HeroStatModifier { m_type = (eHeroStatTypes)stats[i], m_amount = stats[i + 1] });
                R.Set(pu, "m_heroStatModifiers", list);
                R.Set(pu, "m_modifiers", new List<PlayerModifier>());
                if (keep != null) keep(pu);
            };
        }

        const int VIT = (int)eHeroStatTypes.Vitality, STR = (int)eHeroStatTypes.Strength, DEX = (int)eHeroStatTypes.Dexterity;
        const string Potions = "GroupPotionsPurchasable", Artifacts = "GroupArtifactsPurchasable";

        public static readonly List<ItemDef> Items = new List<ItemDef>
        {
            // ================================================================= stat potions (vanilla: 15, +1 or +2/-1)
            new ItemDef { id = "PotionTrollMarrow", cloneFrom = "StatUpHp", cost = 25, group = Potions,
                name = "Troll Marrow", description = "Raises VIT, but the thick brew slows you for a while",
                bubbleArt = "IconTrollMarrowBubble", customize = Potion(pu => TrollMarrow = pu, VIT, 2) },
            new ItemDef { id = "PotionWyrmBlood", cloneFrom = "StatUpDmg", cost = 25, group = Potions,
                name = "Wyrm Blood", description = "Raises STR, but burns going down",
                bubbleArt = "IconWyrmBloodBubble", customize = Potion(pu => WyrmBlood = pu, STR, 2) },
            new ItemDef { id = "PotionHaresDew", cloneFrom = "StatUpSpd", cost = 25, group = Potions,
                name = "Hare's Dew", description = "Raises DEX, but your hands shake for a while",
                bubbleArt = "IconHaresDewBubble", customize = Potion(pu => HaresDew = pu, DEX, 2) },
            new ItemDef { id = "PotionBerserkerGrog", cloneFrom = "PotionDmgUpHpDown", cost = 20, group = Potions,
                name = "Berserker's Grog", description = "More STR, less VIT",
                bubbleArt = "IconBerserkerGrogBubble", customize = Potion(pu => BerserkerGrog = pu, STR, 3, VIT, -2) },
            new ItemDef { id = "PotionStoneskin", cloneFrom = "PotionHpUpSpdDown", cost = 20, group = Potions,
                name = "Stoneskin Draught", description = "More VIT, less DEX",
                bubbleArt = "IconStoneskinBubble", customize = Potion(pu => Stoneskin = pu, VIT, 3, DEX, -2) },
            new ItemDef { id = "PotionQuicksilver", cloneFrom = "PotionSpdUpDmgDown", cost = 20, group = Potions,
                name = "Quicksilver", description = "More DEX, less STR",
                bubbleArt = "IconQuicksilverBubble", customize = Potion(pu => Quicksilver = pu, DEX, 3, STR, -2) },
            new ItemDef { id = "PotionChaosBrew", cloneFrom = "StatUpHp", cost = 10, group = Potions,
                name = "Chaos Brew", description = "Raises one random stat and lowers another",
                bubbleArt = "IconChaosBrewBubble", customize = Potion(pu => ChaosBrew = pu) },

            // ================================================================= fun trinkets
            new ItemDef { id = "ArtifactPartyHat", cloneFrom = "ArtifactThornOfWrath", cost = 30, group = Artifacts,
                name = "Party Hat", description = "Kills pop confetti, and sometimes gold",
                bubbleArt = "IconPartyHatBubble", hudArt = "IconPartyHatHud", customize = Passive(pu => PartyHat = pu) },
            new ItemDef { id = "ArtifactBardLute", cloneFrom = "ArtifactSpellbookTears", cost = 40, group = Artifacts,
                name = "Bard's Lute", description = "A floating lute strums stunning notes",
                bubbleArt = "IconBardLuteBubble", hudArt = "IconBardLuteHud",
                customize = (go, pu) =>
                {
                    BardLute = pu;
                    ItemFixes.AimAtMonsters(LuteNote, 220f);
                    ItemFixes.Follower(go, pu, "FxItem3TokenLute", 7f, LuteNote);
                } },
            new ItemDef { id = "ArtifactPetFerret", cloneFrom = "ArtifactThornOfWrath", cost = 25, group = Artifacts,
                name = "Pet Ferret", description = "A ferret that fetches gold for you",
                bubbleArt = "IconPetFerretBubble", hudArt = "IconPetFerretHud", customize = Passive(pu => PetFerret = pu) },
            new ItemDef { id = "ArtifactBubblePipe", cloneFrom = "ArtifactThornOfWrath", cost = 30, group = Artifacts,
                name = "Bubble Pipe", description = "Blow slowing bubbles as you walk",
                bubbleArt = "IconBubblePipeBubble", hudArt = "IconBubblePipeHud", customize = Passive(pu => BubblePipe = pu) },
            new ItemDef { id = "ArtifactRubberDuck", cloneFrom = "ArtifactThornOfWrath", cost = 25, group = Artifacts,
                name = "Rubber Duck", description = "Squeaks when you are hit, shoving monsters away",
                bubbleArt = "IconRubberDuckBubble", hudArt = "IconRubberDuckHud", customize = Passive(pu => RubberDuck = pu) },
            new ItemDef { id = "ArtifactFireflyJar", cloneFrom = "ArtifactThornOfWrath", cost = 35, group = Artifacts,
                name = "Firefly Jar", description = "Fireflies circle you and zap your foes",
                bubbleArt = "IconFireflyJarBubble", hudArt = "IconFireflyJarHud", customize = Passive(pu => FireflyJar = pu) },
            new ItemDef { id = "ArtifactDancingShoes", cloneFrom = "ArtifactThornOfWrath", cost = 30, group = Artifacts,
                name = "Dancing Shoes", description = "Dance off faster after casting a spell",
                bubbleArt = "IconDancingShoesBubble", hudArt = "IconDancingShoesHud", customize = Passive(pu => DancingShoes = pu) },

            // ================================================================= game-changing little trinkets
            new ItemDef { id = "ArtifactWhetstone", cloneFrom = "ArtifactThornOfWrath", cost = 40, group = Artifacts,
                name = "Whetstone", description = "Your first hit on each monster deals extra damage",
                bubbleArt = "IconWhetstoneBubble", hudArt = "IconWhetstoneHud", customize = Passive(pu => Whetstone = pu) },
            new ItemDef { id = "ArtifactPhoenixFeather", cloneFrom = "ArtifactThornOfWrath", cost = 60, group = Artifacts,
                name = "Phoenix Feather", description = "Saves you from death, once",
                bubbleArt = "IconPhoenixFeatherBubble", hudArt = "IconPhoenixFeatherHud", customize = Passive(pu => PhoenixFeather = pu) },
            new ItemDef { id = "ArtifactSiphonGem", cloneFrom = "ArtifactThornOfWrath", cost = 40, group = Artifacts,
                name = "Siphon Gem", description = "Each monster you kill charges your spell a little",
                bubbleArt = "IconSiphonGemBubble", hudArt = "IconSiphonGemHud", customize = Passive(pu => SiphonGem = pu) },
            new ItemDef { id = "ArtifactGluttonsFork", cloneFrom = "ArtifactThornOfWrath", cost = 30, group = Artifacts,
                name = "Glutton's Fork", description = "Health pickups heal you more",
                bubbleArt = "IconGluttonsForkBubble", hudArt = "IconGluttonsForkHud", customize = Passive(pu => GluttonsFork = pu) },
            new ItemDef { id = "ArtifactTallyStick", cloneFrom = "ArtifactThornOfWrath", cost = 35, group = Artifacts,
                name = "Tally Stick", description = "Kills carve notches that add to your damage",
                bubbleArt = "IconTallyStickBubble", hudArt = "IconTallyStickHud", customize = Passive(pu => TallyStick = pu) },
            new ItemDef { id = "ArtifactGamblersCoin", cloneFrom = "ArtifactThornOfWrath", cost = 35, group = Artifacts,
                name = "Gambler's Coin", description = "Flip a coin each fight: heads for damage, tails for speed",
                bubbleArt = "IconGamblersCoinBubble", hudArt = "IconGamblersCoinHud", customize = Passive(pu => GamblersCoin = pu) },
            new ItemDef { id = "ArtifactBandage", cloneFrom = "ArtifactThornOfWrath", cost = 35, group = Artifacts,
                name = "Patchwork Bandage", description = "Softens the first hit you take each fight",
                bubbleArt = "IconBandageBubble", hudArt = "IconBandageHud", customize = Passive(pu => Bandage = pu) },
            new ItemDef { id = "ArtifactWantedPoster", cloneFrom = "ArtifactThornOfWrath", cost = 40, group = Artifacts,
                name = "Wanted Poster", description = "The toughest monster in a fight takes extra damage from you",
                bubbleArt = "IconWantedPosterBubble", hudArt = "IconWantedPosterHud", customize = Passive(pu => WantedPoster = pu) },
            new ItemDef { id = "ArtifactIronBoots", cloneFrom = "ArtifactThornOfWrath", cost = 30, group = Artifacts,
                name = "Iron Boots", description = "No more knockback, but you move slower",
                bubbleArt = "IconIronBootsBubble", hudArt = "IconIronBootsHud",
                                // the no-knockback part is added by HeroPerks3 only while its holder is the live hero: Knockback is not a
                // hero-only modifier type, and powerup modifiers stay on a player's data while they play a monster
                customize = Passive(pu => IronBoots = pu, Mul(PlayerModifier.eType.HeroSpeed, 0.92f)) },

            // ================================================================= secret items (never in a shop: group left empty)
            new ItemDef { id = "ArtifactSkeletonKey", cloneFrom = "ArtifactThornOfWrath", cost = 0, group = "",
                name = "Skeleton Key", description = "A key that fits no door you have seen. Deal more damage",
                bubbleArt = "IconSkeletonKeyBubble", hudArt = "IconSkeletonKeyHud",
                customize = Passive(pu => SkeletonKey = pu, Mul(PlayerModifier.eType.HeroDamage, 1.1f), Mul(PlayerModifier.eType.PowerupDamage, 1.1f)) },
            new ItemDef { id = "ArtifactGildedHeart", cloneFrom = "ArtifactThornOfWrath", cost = 0, group = "",
                name = "Gilded Heart", description = "Raises every stat and heals you as each fight starts",
                bubbleArt = "IconGildedHeartBubble", hudArt = "IconGildedHeartHud",
                customize = (go, pu) =>
                {
                    Passive(p => GildedHeart = p)(go, pu);
                    R.Set(pu, "m_heroStatModifiers", new List<HeroStatModifier>
                    {
                        new HeroStatModifier { m_type = eHeroStatTypes.Vitality, m_amount = 1 },
                        new HeroStatModifier { m_type = eHeroStatTypes.Strength, m_amount = 1 },
                        new HeroStatModifier { m_type = eHeroStatTypes.Dexterity, m_amount = 1 },
                    });
                } },
        };

        // ------------------------------------------------------------------------------------------------ build
        static GameObject Pop(string name, string sheet, string anim) { return ItemArt.Visual(name, sheet, anim); }

        static void BuildFx()
        {
            for (int i = 0; i < QuaffAnims.Length; i++) Quaff[i] = Pop("ModItem3Quaff" + QuaffAnims[i], "FxItem3Quaff", QuaffAnims[i]);
            for (int i = 0; i < ChaosAnims.Length; i++) ChaosRolls[i] = Pop("ModItem3Chaos" + ChaosAnims[i], "FxItem3ChaosRoll", ChaosAnims[i]);
            string[] n = { "One", "Two", "Three", "Four", "Five" };
            for (int i = 0; i < 5; i++) TallyPops[i] = Pop("ModItem3Tally" + n[i], "FxItem3Tally", n[i]);
            Confetti = Pop("ModItem3Confetti", "FxItem3Confetti", "Burst");
            DanceStep = Pop("ModItem3DanceStep", "FxItem3Dance", "Step");
            WhetSpark = Pop("ModItem3WhetSpark", "FxItem3Whet", "Spark");
            PhoenixBurst = Pop("ModItem3PhoenixBurst", "FxItem3Phoenix", "Burst");
            SiphonWisp = Pop("ModItem3SiphonWisp", "FxItem3Siphon", "Wisp");
            ForkHeal = Pop("ModItem3ForkHeal", "FxItem3Fork", "Heal");
            CoinHeads = Pop("ModItem3CoinHeads", "FxItem3Coin", "Heads");
            CoinTails = Pop("ModItem3CoinTails", "FxItem3Coin", "Tails");
            BandageAbsorb = Pop("ModItem3BandageAbsorb", "FxItem3Bandage", "Absorb");
            BootsClank = Pop("ModItem3BootsClank", "FxItem3Boots", "Clank");
            KeyCollect = Pop("ModItem3KeyCollect", "FxItem3Key", "Collect");
            HeartCollect = Pop("ModItem3HeartCollect", "FxItem3Heart", "Collect");
            HeartGlow = Pop("ModItem3HeartGlow", "FxItem3Heart", "Beat");
            FireflyZap = Pop("ModItem3FireflyZap", "FxItem3Firefly", "Zap");

            // Bard's Lute: a seeking note (hero copy of a monster bolt, its own art and pop)
            var daze = FxFactory.GetStatus("StatusDizzy");
            var goo = FxFactory.GetStatus("StatusLavaSteveGoo");
            LuteNote = FxKit.Projectile("ModItem3LuteNote", "DFX_skelMageNewProjectile", "FxItem3Note", "Fly", 80f, 2.2f, 0.35f, 0.3f, daze, 0.3f,
                                        accel: 260f, speedMax: 120f, rotate: false);
            if (LuteNote != null)
            {
                ItemArt.Place(LuteNote, "FxItem3Note");
                ItemArt.Puffs(LuteNote, Pop("ModItem3NotePop", "FxItem3Note", "Pop"));
                ItemFixes.SeekMonsters(LuteNote, 220f);
            }
            // Bubble Pipe: a slow drifting bubble that pops on the first monster (0.3, slow)
            Bubble = FxKit.Projectile("ModItem3Bubble", "DFX_skelMageNewProjectile", "FxItem3Bubble", "Fly", 45f, 2.6f, 0.3f, 0.1f, goo, 1f, rotate: false);
            if (Bubble != null)
            {
                ItemArt.Place(Bubble, "FxItem3Bubble");
                var pop = Pop("ModItem3BubblePop", "FxItem3Bubble", "Pop");
                ItemArt.Puffs(Bubble, pop);
                FxFactory.SetEffect(Bubble, destroyOnAnimEnd: false, destroyAfter: 2.6f, spawnOnDestroy: pop, freeRotate: false);
                var a = Bubble.GetComponent<AudioCueSource>(); if (a != null) R.Set(a, "m_playOnSpawn", null);
            }
            // Rubber Duck: a squeak ring that shoves monsters (80 x 34 on the feet, like the Tidecaller ring)
            DuckSquawk = FxKit.TimedHit("ModItem3DuckSquawk", "TrollGroundPoundBigShockwave", "FxItem3Duck", "Squeak", 0, 3, 0.1f, 3.2f, canFlip: false);
            if (DuckSquawk != null) { Strike.Collider(DuckSquawk, 80f, 34f); ItemArt.Place(DuckSquawk, "FxItem3Duck"); }
            // Firefly zap: a short invisible hit on the monster's body
            FireflyZapHit = FxKit.BodyHit("ModItem3FireflyHit", 0.2f, 1f, 0.3f, 0.12f);
            if (FireflyZapHit != null)
            {
                var spr = FireflyZapHit.GetComponent<exSprite>(); if (spr != null) spr.enabled = false;
                Strike.HitBox(FireflyZapHit, 10f, 10f);
                ItemArt.Puffs(FireflyZapHit, null);
            }

            // followers drawn by code: the pet ferret and the fireflies
            FerretTmpl = FxKit.Visual("ModItem3Ferret", "FxItem3Ferret", "Idle", loop: true);
            ItemArt.Place(FerretTmpl, "FxItem3Ferret");
            FerretIdle = ItemArt.Clip("FxItem3Ferret", "Idle", true);
            FerretRun = ItemArt.Clip("FxItem3Ferret", "Run", true);
            FireflyTmpl = FxKit.Visual("ModItem3Firefly", "FxItem3Firefly", "Glow", loop: true);
            ItemArt.Place(FireflyTmpl, "FxItem3Firefly");
            FireflyGlow = ItemArt.Clip("FxItem3Firefly", "Glow", true);
            FireflyDim = ItemArt.Clip("FxItem3Firefly", "Dim", true);

            IndSluggish = ModStatus.Indicator("ModItem3IndSluggish", "FxItem3IndSluggish", "Loop", -2f, OverlayAt.Feet);
            IndBurn = ModStatus.Indicator("ModItem3IndBurn", "FxItem3IndBurn", "Loop", -2f, OverlayAt.Feet);
            IndShaky = ModStatus.Indicator("ModItem3IndShaky", "FxItem3IndShaky", "Loop", 1f, OverlayAt.Head);
            IndHat = ModStatus.Indicator("ModItem3IndHat", "FxItem3PartyHat", "Hat", -3f, OverlayAt.Head);
            IndKey = ModStatus.Indicator("ModItem3IndKey", "FxItem3IndKey", "Loop", -2f, OverlayAt.Feet);
            IndBandage = ModStatus.Indicator("ModItem3IndBandage", "FxItem3IndBandage", "Loop", 1f, OverlayAt.Head);
            IndWanted = ModStatus.Indicator("ModItem3IndWanted", "FxItem3Wanted", "Mark", 1f, OverlayAt.Head);
            IndHeart = ModStatus.Indicator("ModItem3IndHeart", "FxItem3IndHeart", "Loop", -2f, OverlayAt.Feet);
        }

        /// <summary>A free pickup that hops out (cloned from the vanilla potion that comes flying out of things) and gives
        /// the item on contact through the game's own MsgCollectPowerup.</summary>
        static GameObject BuildPickup(string id, Powerup pu, string sheet, GameObject collectFx, string anim = "Lie")
        {
            var go = FxFactory.Clone("HealthPickupPotion_ComeFlyingOut", "ModItem3Pickup" + id);
            if (go == null || pu == null) return null;
            var sh = SpriteSheets.Get(sheet);
            if (sh != null && sh.Has(anim))
            {
                FxFactory.Reskin(go, new ClipBuilder(sh, anim, go.name + "Clip").Loop().Build(), sh);
                int ox, oy;
                if (ItemArt.Origin(sheet, out ox, out oy)) ItemArt.Place(go, sheet);
                else { var spr = go.GetComponent<exSprite>(); if (spr != null) { spr.anchor = exPlane.Anchor.BotCenter; spr.offset = new Vector2(0f, -3f); } }
            }
            // lives until collected or its room is cleaned up (no timed fade, never despawned off screen)
            FxFactory.SetEffect(go, destroyOnAnimEnd: false, destroyAfter: 0f);
            foreach (var m in go.GetComponents<ParticleMotion>())
            {
                R.Set(m, "m_trailObject", null);
                R.Set(m, "m_destroyWhenOffScreen", false);
            }
            foreach (var b in go.GetComponents<BoxCollider>()) { b.size = new Vector3(11f, 9f, b.size.z); b.center = new Vector3(0f, 2f, b.center.z); }
            var pk = go.GetComponent<Pickup>();
            if (pk != null)
            {
                R.Set(pk, "m_message", "MsgCollectPowerup");
                R.Set(pk, "m_messageParams", new MsgParams { m_object = pu.gameObject, m_float = 0f });
                R.Set(pk, "m_spawnOnCollect", collectFx);
                R.Set(pk, "m_canHeroCollect", true);
                R.Set(pk, "m_canMonsterCollect", false);
                R.Set(pk, "m_canGhostCollect", false);
            }
            var t = go.GetComponent<ColorTinter>(); if (t != null) t.enabled = false;
            return go;
        }

        public static GameObject DropPickup(string id, Vector3 pos)
        {
            GameObject tmpl;
            if (id == null || !s_pickups.TryGetValue(id, out tmpl) || tmpl == null)
            {
                // any other ItemPack3 item drops as its own 16x16 icon (Idle), picked up with the key's sparkle
                var pu = Get(id);
                var def = Items.Find(d => d.id == id);
                if (pu == null || def == null) { Plugin.Log.LogWarning("ItemPack3: no item " + id + " to drop"); return null; }
                string icon = def.bubbleArt != null && def.bubbleArt.EndsWith("Bubble") ? def.bubbleArt.Substring(0, def.bubbleArt.Length - 6) : def.bubbleArt;
                tmpl = BuildPickup(id, pu, icon, KeyCollect, "Idle");
                if (tmpl == null) return null;
                s_pickups[id] = tmpl;
            }
            // hops out in a random direction like the vanilla potion drops, then settles where it lands
            try { return SystemPool.Spawn(tmpl, new Vector3(pos.x, pos.y, 0f), Quaternion.Euler(0f, 0f, UnityEngine.Random.Range(0f, 360f))); }
            catch (Exception e) { Plugin.Log.LogWarning("ItemPack3 drop " + id + ": " + e.Message); return null; }
        }

        static SpawnGroup FindGroup(string name)
        {
            foreach (var g in Resources.FindObjectsOfTypeAll<SpawnGroup>())
                if (g.gameObject.name == name && !g.gameObject.scene.IsValid()) return g;
            return null;
        }

        static exSpriteAnimClip Icon(string art, string anim)
        {
            var sh = art != null ? SpriteSheets.Get(art) : null;
            if (sh == null || !sh.Has(anim)) return null;
            return new ClipBuilder(sh, anim, "Mod" + art + anim).Loop().Build();
        }

        /// <summary>Same as ItemPack.Build, but a secret item (empty group) is never put in a shop pool.</summary>
        static void Build(ItemDef def)
        {
            var src = FxFactory.Vanilla(def.cloneFrom);
            if (src == null) return;
            var go = MonsterFactory.ClonePrefab(src, "Mod" + def.id);
            var pu = go.GetComponent<Powerup>();
            pu.m_displayName = def.name;
            pu.m_description = def.description;
            pu.m_cost = def.cost;
            var bubble = Icon(def.bubbleArt, "Bubble");
            if (bubble != null) R.Set(pu, "m_animPurchasableBubble", bubble);
            var hud = Icon(def.hudArt, "Hud");
            if (hud != null) R.Set(pu, "m_guiIcon", hud);
            if (def.customize != null) def.customize(go, pu);
            s_built[def.id] = pu;
            ItemPack.Built[def.id] = pu;                 // vault ITEMS grid + self-test
            if (!string.IsNullOrEmpty(def.group))
            {
                var group = FindGroup(def.group);
                if (group != null)
                {
                    var items = R.Get<List<SpawnItem>>(group, "m_items");
                    var like = items.Count > 0 ? items[0] : null;
                    var it = like != null ? R.Clone(like) : new SpawnItem();
                    it.m_object = go;
                    it.m_chance = 100f;
                    items.Add(it);
                }
                else Plugin.Log.LogWarning("Shop group not found: " + def.group);
            }
            else R.Set(pu, "m_shouldBotPurchase", false);
            Plugin.Log.LogInfo("Item built: " + def.name + " (" + def.cloneFrom + ")");
        }

        public static void Register()
        {
            try { BuildFx(); } catch (Exception e) { Plugin.Log.LogError("Items3 FX failed: " + e); }
            foreach (var def in Items)
            {
                try { Build(def); }
                catch (Exception e) { Plugin.Log.LogError("Item " + def.id + " failed: " + e); }
            }
            ItemPack.Items.AddRange(Items);   // so the self-test counts them
            try
            {
                if (SkeletonKey != null) s_pickups[SecretItems.SkeletonKeyId] = BuildPickup(SecretItems.SkeletonKeyId, SkeletonKey, "FxItem3Key", KeyCollect);
                if (GildedHeart != null) s_pickups[SecretItems.GildedHeartId] = BuildPickup(SecretItems.GildedHeartId, GildedHeart, "FxItem3Heart", HeartCollect);
            }
            catch (Exception e) { Plugin.Log.LogError("Items3 pickups failed: " + e); }
            RegisterSecrets();
        }

        // ------------------------------------------------------------------------------------------------ secrets
        static void RegisterSecrets()
        {
            Secrets.Add(new SecretDef
            {
                id = SecretItems.SkeletonKeyId, group = "Items", iconSheet = "IconSkeletonKey",
                name = "Skeleton Key",
                riddle = "Look for a cracked wall. The key behind it is made of bone.",
                rarity = "Rare: hidden in a wall",
                text = "Found behind a cracked wall. It opens the keyhole with no door.",
            });
            Secrets.Add(new SecretDef
            {
                id = SecretItems.GildedHeartId, group = "Items", iconSheet = "IconGildedHeart",
                name = "Gilded Heart",
                riddle = "Take the bone key to the keyhole that has no door.",
                rarity = "Very rare: behind a lock",
                text = "Guarded by the keyhole with no door. Raises every stat and heals you as fights start.",
            });
        }

        /// <summary>A player just collected (bought, picked up or was given) an item.</summary>
        internal static void OnCollect(Powerup prefab, PlayerData pd)
        {
            if (prefab == null || pd == null) return;
            if (prefab == SkeletonKey) Secrets.Found(SecretItems.SkeletonKeyId);
            if (prefab == GildedHeart) Secrets.Found(SecretItems.GildedHeartId);
            var go = pd.GameObject;
            var perks = go != null ? go.GetComponent<HeroPerks3>() : null;
            if (prefab == TallyStick) HeroPerks3.ResetTally(pd);
            if (perks != null) perks.OnCollect(prefab);
        }

        public static void SelfCheck(Action<string> bad)
        {
            foreach (var def in Items)
                if (Get(def.id) == null) bad("items3: " + def.id + " failed to build");
            foreach (var kv in new Dictionary<string, object>
            {
                { "Lute note", LuteNote }, { "bubble", Bubble }, { "duck squeak", DuckSquawk }, { "firefly hit", FireflyZapHit },
                { "ferret", FerretTmpl }, { "firefly", FireflyTmpl }, { "confetti", Confetti }, { "phoenix burst", PhoenixBurst },
                { "sluggish indicator", IndSluggish }, { "burn indicator", IndBurn }, { "shaky indicator", IndShaky }, { "party hat", IndHat },
                { "key indicator", IndKey }, { "bandage indicator", IndBandage }, { "wanted mark", IndWanted }, { "heart indicator", IndHeart },
            })
                if (kv.Value == null) bad("items3: " + kv.Key + " missing");
            foreach (var q in Quaff) if (q == null) bad("items3: a potion burst is missing");
            foreach (var q in ChaosRolls) if (q == null) bad("items3: a chaos roll pop is missing");
            foreach (var q in TallyPops) if (q == null) bad("items3: a tally pop is missing");
            GameObject p;
            if (!s_pickups.TryGetValue(SecretItems.SkeletonKeyId, out p) || p == null) bad("items3: Skeleton Key pickup missing");
            if (!s_pickups.TryGetValue(SecretItems.GildedHeartId, out p) || p == null) bad("items3: Gilded Heart pickup missing");
            foreach (var g in new[] { Potions, Artifacts })
            {
                var grp = FindGroup(g);
                var items = grp != null ? R.Get<List<SpawnItem>>(grp, "m_items") : null;
                if (items == null) { bad("items3: shop group " + g + " missing"); continue; }
                foreach (var s in new[] { SkeletonKey, GildedHeart })
                    if (s != null && items.Exists(i => i != null && i.m_object == s.gameObject)) bad("items3: secret " + s.m_displayName + " is in a shop pool");
            }
            if (Secrets.All.Find(e => e.id == SecretItems.SkeletonKeyId) == null) bad("items3: Skeleton Key secret not registered");
        }
    }

    /// <summary>Marks a monster the hero has already hit (Whetstone); dropped when the body is pooled.</summary>
    public class WhetMark : MonoBehaviour
    {
        void OnDisable() { Destroy(this); }
    }

    /// <summary>Hero-side logic of the third-wave items.</summary>
    public class HeroPerks3 : MonoBehaviour
    {
        // every timed modifier source this component adds (the Tally Stick's lives under its prefab name: it goes with the item)
        const string CoinSrc = "moditem3coin", PotionSrc = "moditem3potion", DanceSrc = "moditem3dance", BootsSrc = "moditem3boots";
        static readonly string[] TimedSources = { CoinSrc, PotionSrc, DanceSrc, BootsSrc };

        /// <summary>Take every timed item buff/debuff off a player's game data (hero death, hero change, level end).</summary>
        public static void StripTimed(PlayerGameData gd)
        {
            if (gd == null) return;
            foreach (var src in TimedSources) gd.RemoveModifiers(src);
        }
        static readonly AccessTools.FieldRef<Player, float> s_charge = AccessTools.FieldRefAccess<Player, float>("m_specialCharge");
        static readonly AccessTools.FieldRef<Player, Player.ePlayerState> s_state = AccessTools.FieldRefAccess<Player, Player.ePlayerState>("m_state");
        static readonly Dictionary<int, int> s_tally = new Dictionary<int, int>();

        Player m_player;
        Health m_health;
        bool m_inFight, m_bandage, m_wasSpecial, m_hatShown, m_keyShown, m_heartShown;
        int m_coin = -1, m_partyKills;
        float m_fightT, m_coinAt, m_pipe, m_duckCd, m_clankCd, m_danceT, m_danceStep, m_scan, m_markScan, m_orbit, m_potionT, m_burnT, m_burnTick;
        Vector3 m_lastPos;
        GameObject m_marked, m_ferret;
        exSpriteAnimation m_ferretAnim;
        bool m_ferretRunning;
        Vector2 m_ferretAt;
        readonly GameObject[] m_flies = new GameObject[3];
        readonly float[] m_flyRest = new float[3];
        readonly List<Pickup> m_gold = new List<Pickup>();

        // the game data of the player this hero body belongs to, cached while it is the live hero: when the hero dies
        // PlayerData.OnPlayerDied clears IsHero and Player.ResetPlayerData then nulls the player's data, so without the
        // cache nothing could take the timed modifiers back off and they would carry over to that player's next hero.
        PlayerGameData m_gd;
        bool m_clean = true, m_bootsOn;
        int m_pid = -1;                 // the player whose HUD shows this hero's potion countdowns
        Powerup m_potion;               // the potion whose catch is running (Troll Marrow or Hare's Dew)

        // potion catches count down only while a fight is on, so waiting in a shop or an empty room never uses them up
        const string PotionTimer = "item3.potion", BurnTimer = "item3.burn";
        public const float PotionTime = 15f, BurnTime = 3f;

        void Awake() { m_player = GetComponent<Player>(); m_health = GetComponent<Health>(); }
        void OnEnable() { ResetState(); m_lastPos = transform.position; }
        void OnDisable() { Cleanup(); m_hatShown = m_keyShown = m_heartShown = false; }

        void ResetState()
        {
            m_inFight = false; m_coin = -1; m_coinAt = 0f; m_bandage = false; m_marked = null;
            m_potionT = 0f; m_burnT = 0f; m_danceT = 0f; m_fightT = 0f;
        }

        /// <summary>No longer the live hero (death, hero change, level unload): every timed effect ends, its modifiers
        /// come off the cached game data, its markers and followers go.</summary>
        public void Cleanup()
        {
            var pd = Data;
            StripTimed(pd != null && pd.GameData != null ? pd.GameData : m_gd);
            if (m_gd != null && pd != null && pd.GameData != m_gd) StripTimed(m_gd);
            if (m_coin == 0) ModInd.Might(gameObject, false);
            if (m_coin == 1) ModInd.Haste(gameObject, false);
            if (m_danceT > 0f) ModInd.Haste(gameObject, false);
            ModInd.Set(gameObject, ItemPack3.IndSluggish, false);
            ModInd.Set(gameObject, ItemPack3.IndShaky, false);
            ModInd.Set(gameObject, ItemPack3.IndBurn, false);
            ModInd.Set(gameObject, ItemPack3.IndBandage, false);
            Unmark();
            Followers(false, false);
            ClearTimers();
            ResetState();
            m_bootsOn = false;
            m_clean = true;
        }

        PlayerData Data { get { return m_player != null ? m_player.GetPlayerData() : null; } }
        /// <summary>The live player's game data, else the one cached while this body was the hero.</summary>
        PlayerGameData GD { get { var pd = Data; return pd != null && pd.GameData != null ? pd.GameData : m_gd; } }
        bool Has(Powerup pu) { return HeroPerks.Has(Data, pu); }
        bool IsHero { get { var pd = Data; return pd != null && pd.IsHero && m_health != null && m_health.IsAlive(); } }

        public void Refresh() { m_scan = 0f; }

        static void Pop(GameObject fx, Vector2 at) { ItemArt.Pop(fx, at); }

        // ------------------------------------------------------------------------------------------------ collect
        public void OnCollect(Powerup pu)
        {
            Vector2 at = transform.position;
            int q = -1;
            if (pu == ItemPack3.TrollMarrow) q = 0;
            else if (pu == ItemPack3.WyrmBlood) q = 1;
            else if (pu == ItemPack3.HaresDew) q = 2;
            else if (pu == ItemPack3.BerserkerGrog) q = 3;
            else if (pu == ItemPack3.Stoneskin) q = 4;
            else if (pu == ItemPack3.Quicksilver) q = 5;
            else if (pu == ItemPack3.ChaosBrew) q = 6;
            else if (pu == ItemPack3.GildedHeart) q = 7;
            if (q >= 0) Pop(ItemPack3.Quaff[q], at);
            var gd = Data != null ? Data.GameData : null;
            if (gd == null) return;
            if (pu == ItemPack3.TrollMarrow)
            {
                EndPotion();
                gd.AddBaseModifier(PotionSrc, new PlayerModifier { m_modify = PlayerModifier.eType.HeroSpeed, m_type = ValueModifier.eModifierType.Multiply, m_value = 0.8f });
                m_potionT = PotionTime;
                m_potion = pu;
                ModInd.Set(gameObject, ItemPack3.IndSluggish, true);
            }
            else if (pu == ItemPack3.HaresDew)
            {
                EndPotion();
                gd.AddBaseModifier(PotionSrc, new PlayerModifier { m_modify = PlayerModifier.eType.HeroDamage, m_type = ValueModifier.eModifierType.Multiply, m_value = 0.8f });
                gd.AddBaseModifier(PotionSrc, new PlayerModifier { m_modify = PlayerModifier.eType.PowerupDamage, m_type = ValueModifier.eModifierType.Multiply, m_value = 0.8f });
                m_potionT = PotionTime;
                m_potion = pu;
                ModInd.Set(gameObject, ItemPack3.IndShaky, true);
            }
            else if (pu == ItemPack3.WyrmBlood)
            {
                m_burnT = BurnTime; m_burnTick = 1f;
                ModInd.Set(gameObject, ItemPack3.IndBurn, true);
            }
            else if (pu == ItemPack3.ChaosBrew)
            {
                int up = UnityEngine.Random.Range(0, 3);
                int down = (up + UnityEngine.Random.Range(1, 3)) % 3;
                gd.IncrementHeroStat((eHeroStatTypes)up, 2);
                gd.IncrementHeroStat((eHeroStatTypes)down, -1);
                // pop order: VS VD SV SD DV DS
                int k = up * 2 + (down > up ? down - 1 : down);
                StartCoroutine(Later(0.35f, () => Pop(ItemPack3.ChaosRolls[k], (Vector2)transform.position)));
            }
            Refresh();
        }

        System.Collections.IEnumerator Later(float s, Action a) { yield return new WaitForSeconds(s); if (a != null) a(); }

        void EndPotion()
        {
            var gd = GD;
            if (gd != null) gd.RemoveModifiers(PotionSrc);
            m_potionT = 0f;
            m_potion = null;
            ModInd.Set(gameObject, ItemPack3.IndSluggish, false);
            ModInd.Set(gameObject, ItemPack3.IndShaky, false);
            if (m_burnT > 0f) { m_burnT = 0f; ModInd.Set(gameObject, ItemPack3.IndBurn, false); }
            ClearTimers();
        }

        void ClearTimers()
        {
            if (m_pid < 0) return;
            HudTimers.Clear(m_pid, PotionTimer);
            HudTimers.Clear(m_pid, BurnTimer);
        }

        /// <summary>The potion catches tick in fights only; their countdowns sit by this player's HUD panel, dimmed while
        /// they wait for the next fight.</summary>
        void TickPotions(float dt)
        {
            float fightDt = m_inFight ? dt : 0f;
            if (m_potionT > 0f)
            {
                m_potionT -= fightDt;
                if (m_potionT <= 0f) EndPotion();
                else HudTimers.Set(m_pid, PotionTimer, m_potionT, Icon(m_potion), !m_inFight);
            }
            if (m_burnT > 0f)
            {
                m_burnT -= fightDt; m_burnTick -= fightDt;
                if (m_burnTick <= 0f)
                {
                    m_burnTick = 1f;
                    float cur = m_health.GetHealthCurrent();
                    if (cur > 0.65f) m_health.DamageNoSource(Mathf.Min(0.15f, cur - 0.5f));
                }
                if (m_burnT <= 0f) { ModInd.Set(gameObject, ItemPack3.IndBurn, false); HudTimers.Clear(m_pid, BurnTimer); }
                else HudTimers.Set(m_pid, BurnTimer, m_burnT, Icon(ItemPack3.WyrmBlood), !m_inFight);
            }
        }

        static SpriteSheet Icon(Powerup pu)
        {
            string id = pu == ItemPack3.TrollMarrow ? "IconTrollMarrow" : pu == ItemPack3.HaresDew ? "IconHaresDew" : pu == ItemPack3.WyrmBlood ? "IconWyrmBlood" : null;
            return id != null ? SpriteSheets.Get(id) : null;
        }

        // ------------------------------------------------------------------------------------------------ update
        void Update()
        {
            var pd = Data;
            if (pd == null || !pd.IsHero || m_health == null || !m_health.IsAlive())
            {
                if (!m_clean) Cleanup();
                return;
            }
            // the hero body is handed straight to the killer (SystemLevel: InitAsPlayer on the same object), so a new
            // player's data on this body means the old hero's timed effects end here, on the old hero's data
            if (m_gd != null && pd.GameData != m_gd) { StripTimed(m_gd); Cleanup(); }
            m_gd = pd.GameData;
            if (m_pid != pd.Id) { ClearTimers(); m_pid = pd.Id; }
            m_clean = false;
            float dt = Time.deltaTime;
            Vector2 me = transform.position;
            bool moving = (transform.position - m_lastPos).sqrMagnitude > 0.04f;
            m_lastPos = transform.position;

            TickPotions(dt);

            // Iron Boots: no knockback, only while this player is the live hero
            bool boots = Has(ItemPack3.IronBoots);
            if (boots != m_bootsOn)
            {
                m_bootsOn = boots;
                pd.GameData.RemoveModifiers(BootsSrc);
                if (boots) pd.GameData.AddBaseModifier(BootsSrc, new PlayerModifier { m_modify = PlayerModifier.eType.Knockback, m_type = ValueModifier.eModifierType.Multiply, m_value = 0f });
            }

            // carried looks
            Show(ref m_hatShown, ItemPack3.IndHat, Has(ItemPack3.PartyHat));
            Show(ref m_keyShown, ItemPack3.IndKey, Has(ItemPack3.SkeletonKey));
            Show(ref m_heartShown, ItemPack3.IndHeart, Has(ItemPack3.GildedHeart));

            // fights
            bool locked = ModUtil.DoorsLocked();
            if (locked && !m_inFight) StartFight();
            else if (!locked && m_inFight) EndFight();
            if (m_inFight)
            {
                m_fightT += dt;
                if (m_coin < 0 && m_coinAt > 0f && m_fightT >= m_coinAt) FlipCoin();
                if (Has(ItemPack3.WantedPoster)) Mark(dt);
            }

            // spell use: Dancing Shoes
            bool special = s_state(m_player) == Player.ePlayerState.AttackSpecial;
            if (special && !m_wasSpecial && Has(ItemPack3.DancingShoes))
            {
                var gd = pd.GameData;
                gd.RemoveModifiers(DanceSrc);
                gd.AddBaseModifier(DanceSrc, new PlayerModifier { m_modify = PlayerModifier.eType.HeroSpeed, m_type = ValueModifier.eModifierType.Multiply, m_value = 1.25f });
                m_danceT = 2f; m_danceStep = 0f;
                ModInd.Haste(gameObject, true, 2f);
            }
            m_wasSpecial = special;
            if (m_danceT > 0f)
            {
                m_danceT -= dt; m_danceStep -= dt;
                if (moving && m_danceStep <= 0f) { m_danceStep = 0.16f; Pop(ItemPack3.DanceStep, me); }
                if (m_danceT <= 0f) pd.GameData.RemoveModifiers(DanceSrc);
            }

            // Bubble Pipe
            if (Has(ItemPack3.BubblePipe) && moving)
            {
                m_pipe += dt;
                if (m_pipe >= 2.5f && ItemPack3.Bubble != null)
                {
                    m_pipe = 0f;
                    float ang = transform.lossyScale.x < 0f ? 180f : 0f;
                    var mv = m_player.GetComponent<Rigidbody>();
                    if (mv != null && mv.velocity.sqrMagnitude > 4f) ang = Mathf.Atan2(mv.velocity.y, mv.velocity.x) * Mathf.Rad2Deg;
                    float dir = Mathf.Cos(ang * Mathf.Deg2Rad) < 0f ? -1f : 1f;
                    FxFactory.SpawnOwned(ItemPack3.Bubble, me + new Vector2(5f * dir, 9f), ModUtil.HeroSource(), ang);
                }
            }
            if (m_duckCd > 0f) m_duckCd -= dt;
            if (m_clankCd > 0f) m_clankCd -= dt;

            // pets
            Followers(Has(ItemPack3.PetFerret), Has(ItemPack3.FireflyJar));
            if (m_ferret != null) Ferret(dt, me);
            if (m_flies[0] != null) Fireflies(dt, me);
        }

        /// <summary>Keep a carried-item look on while the item is held (re-shown if a death / pooling cleared it).</summary>
        void Show(ref bool shown, StatusOverlayDef d, bool want)
        {
            if (d == null) return;
            if (want)
            {
                var t = GetComponent<StatusOverlays>();
                if (shown && t != null && t.Showing(d)) return;
                shown = true;
                ModInd.Set(gameObject, d, true);
            }
            else if (shown)
            {
                shown = false;
                ModInd.Set(gameObject, d, false);
            }
        }

        // ------------------------------------------------------------------------------------------------ fights
        void StartFight()
        {
            m_inFight = true; m_fightT = 0f; m_coin = -1; m_marked = null; m_markScan = 1f;
            m_coinAt = Has(ItemPack3.GamblersCoin) ? 0.6f : 0f;
            m_bandage = Has(ItemPack3.Bandage);
            if (m_bandage) ModInd.Set(gameObject, ItemPack3.IndBandage, true);
            if (Has(ItemPack3.GildedHeart) && m_health != null)
            {
                m_health.Heal(0.5f);
                Pop(ItemPack3.HeartGlow, transform.position);
                ModInd.Heal(gameObject);
            }
        }

        void EndFight()
        {
            m_inFight = false;
            var gd = GD;
            if (gd != null) gd.RemoveModifiers(CoinSrc);
            if (m_coin == 0) ModInd.Might(gameObject, false);
            if (m_coin == 1) ModInd.Haste(gameObject, false);
            m_coin = -1;
            if (m_bandage) ModInd.Set(gameObject, ItemPack3.IndBandage, false);
            m_bandage = false;
            Unmark();
        }

        void FlipCoin()
        {
            var gd = Data != null ? Data.GameData : null;
            if (gd == null) return;
            gd.RemoveModifiers(CoinSrc);                    // never stacks with an earlier flip
            m_coin = UnityEngine.Random.value < 0.5f ? 0 : 1;
            Pop(m_coin == 0 ? ItemPack3.CoinHeads : ItemPack3.CoinTails, transform.position);
            if (m_coin == 0)
            {
                gd.AddBaseModifier(CoinSrc, new PlayerModifier { m_modify = PlayerModifier.eType.HeroDamage, m_type = ValueModifier.eModifierType.Multiply, m_value = 1.2f });
                gd.AddBaseModifier(CoinSrc, new PlayerModifier { m_modify = PlayerModifier.eType.PowerupDamage, m_type = ValueModifier.eModifierType.Multiply, m_value = 1.2f });
                ModInd.Might(gameObject, true);
            }
            else
            {
                gd.AddBaseModifier(CoinSrc, new PlayerModifier { m_modify = PlayerModifier.eType.HeroSpeed, m_type = ValueModifier.eModifierType.Multiply, m_value = 1.2f });
                ModInd.Haste(gameObject, true);
            }
        }

        void Mark(float dt)
        {
            if (m_marked != null)
            {
                var h = m_marked.GetComponent<Health>();
                if (m_marked.activeInHierarchy && h != null && h.IsAlive()) return;
                Unmark();
                m_markScan = 1f;
            }
            m_markScan -= dt;
            if (m_markScan > 0f) return;
            m_markScan = 0.5f;
            GameObject best = null; float bh = 0f;
            var hero = gameObject;
            foreach (var p in FindObjectsOfType<Player>())
            {
                if (!ItemFixes.LiveMonster(p, hero)) continue;
                if (((Vector2)p.transform.position - (Vector2)transform.position).sqrMagnitude > 320f * 320f) continue;
                var h = p.GetComponent<Health>();
                float mh = h != null ? h.GetHealthMax() : 0f;
                if (mh > bh) { bh = mh; best = p.gameObject; }
            }
            if (best == null) return;
            m_marked = best;
            ModInd.Set(best, ItemPack3.IndWanted, true);
        }

        void Unmark()
        {
            if (m_marked != null) ModInd.Set(m_marked, ItemPack3.IndWanted, false);
            m_marked = null;
        }

        // ------------------------------------------------------------------------------------------------ damage
        /// <summary>A hit on the hero (after the other items' patches). False blocks it.</summary>
        public bool OnIncoming(Health h, DamageInfo damage, float predicted)
        {
            bool status = damage.m_isDamageFromStatus;
            var attacker = damage.m_source != null ? damage.m_source.m_sourceOwnerPlayer : null;
            // a hit the weapon guard (WeaponPack Patch_WeaponHeroHit, Priority.Last: it runs after this) will block never
            // lands: no one-shot item (Phoenix, Bandage, Duck) is spent on it. Invincibility, Lucky Die and the plates
            // stop the hit before this runs (the prefix checks the invincibility list and __runOriginal).
            if (!status && attacker != null)
            {
                var rt = GetComponent<WeaponRuntime>();
                if (rt != null && rt.GuardUp) return true;
            }
            if (!status && attacker != null)
            {
                if (m_bandage && m_inFight)
                {
                    m_bandage = false;
                    damage.m_amount *= 0.5f; predicted *= 0.5f;
                    ModInd.Set(gameObject, ItemPack3.IndBandage, false);
                    Pop(ItemPack3.BandageAbsorb, transform.position);
                }
                if (Has(ItemPack3.RubberDuck) && m_duckCd <= 0f && ItemPack3.DuckSquawk != null)
                {
                    m_duckCd = 3f;
                    FxFactory.SpawnOwned(ItemPack3.DuckSquawk, transform.position, ModUtil.HeroSource());
                }
                if (Has(ItemPack3.IronBoots) && m_clankCd <= 0f)
                {
                    m_clankCd = 0.5f;
                    Pop(ItemPack3.BootsClank, transform.position);
                }
            }
            if (Has(ItemPack3.PhoenixFeather) && predicted >= h.GetHealthCurrent() - 0.001f)
            {
                // the feather burns instead of you
                var pd = Data;
                if (pd != null) pd.GameData.RemovePowerupPrefab(ItemPack3.PhoenixFeather);
                if (h.GetHealthCurrent() > 0.5f) h.ChangeHealth(0.5f);
                h.StartInvincibility("moditem3phoenix", 1.5f);
                Pop(ItemPack3.PhoenixBurst, transform.position);
                ModInd.Heal(gameObject);
                return false;
            }
            return true;
        }

        /// <summary>A hit from the hero on a monster.</summary>
        public float OnOutgoing(GameObject victim, float amount)
        {
            if (victim == null) return amount;
            if (Has(ItemPack3.Whetstone) && victim.GetComponent<WhetMark>() == null && victim.GetComponent<Player>() != null)
            {
                victim.AddComponent<WhetMark>();
                amount *= 1.5f;
                Pop(ItemPack3.WhetSpark, ItemFixes.AimPoint(victim));
            }
            if (m_marked != null && victim == m_marked && Has(ItemPack3.WantedPoster)) amount *= 1.4f;
            return amount;
        }

        public void OnHealthPickup(float healed)
        {
            if (!Has(ItemPack3.GluttonsFork) || m_health == null || healed <= 0f) return;
            m_health.Heal(healed * 0.5f);
            Pop(ItemPack3.ForkHeal, transform.position);
        }

        // ------------------------------------------------------------------------------------------------ kills
        public static void ResetTally(PlayerData pd)
        {
            if (pd == null) return;
            s_tally[pd.Id] = 0;
            if (ItemPack3.TallyStick != null) pd.GameData.RemoveModifiers(ItemPack3.TallyStick.name);
        }

        public void OnKill(PlayerData victim)
        {
            var pd = Data;
            if (pd == null) return;
            Vector2 at = victim != null && victim.GameObject != null ? ItemFixes.AimPoint(victim.GameObject) : (Vector2)transform.position;
            if (Has(ItemPack3.PartyHat))
            {
                Pop(ItemPack3.Confetti, at);
                if (++m_partyKills % 8 == 0)
                {
                    var gold = FxFactory.Vanilla("GoldPickup5");
                    if (gold != null) SystemPool.Spawn(gold, new Vector3(at.x, at.y - 6f, 0f));
                }
            }
            if (Has(ItemPack3.SiphonGem) && m_player != null)
            {
                float max = m_player.GetSpecialChargeTime();
                s_charge(m_player) = Mathf.Min(s_charge(m_player) + 1f, Mathf.Max(max, 0f) + 0.01f);
                Pop(ItemPack3.SiphonWisp, transform.position);
            }
            if (Has(ItemPack3.TallyStick))
            {
                int k;
                s_tally.TryGetValue(pd.Id, out k);
                k++;
                s_tally[pd.Id] = k;
                if (k % 8 == 0 && k / 8 <= 5)
                {
                    int notches = k / 8;
                    var src = ItemPack3.TallyStick.name;
                    pd.GameData.RemoveModifiers(src);
                    float m = 1f + 0.04f * notches;
                    pd.GameData.AddSpecialModifier(src, new PlayerModifier { m_modify = PlayerModifier.eType.HeroDamage, m_type = ValueModifier.eModifierType.Multiply, m_value = m });
                    pd.GameData.AddSpecialModifier(src, new PlayerModifier { m_modify = PlayerModifier.eType.PowerupDamage, m_type = ValueModifier.eModifierType.Multiply, m_value = m });
                    Pop(ItemPack3.TallyPops[notches - 1], transform.position);
                }
            }
        }

        // ------------------------------------------------------------------------------------------------ followers
        void Followers(bool ferret, bool flies)
        {
            if (ferret && m_ferret == null && ItemPack3.FerretTmpl != null)
            {
                m_ferretAt = (Vector2)transform.position + new Vector2(-12f, 0f);
                m_ferret = SystemPool.Spawn(ItemPack3.FerretTmpl, new Vector3(m_ferretAt.x, m_ferretAt.y, 0f));
                m_ferretAnim = m_ferret != null ? m_ferret.GetComponent<exSpriteAnimation>() : null;
                m_ferretRunning = true;
                SetFerretRun(false);
            }
            else if (!ferret && m_ferret != null)
            {
                if (m_ferret.activeInHierarchy) SystemPool.Despawn(m_ferret);
                m_ferret = null; m_ferretAnim = null;
            }
            if (flies && m_flies[0] == null && ItemPack3.FireflyTmpl != null)
            {
                for (int i = 0; i < 3; i++)
                {
                    m_flies[i] = SystemPool.Spawn(ItemPack3.FireflyTmpl, transform.position);
                    m_flyRest[i] = 0f;
                    var an = m_flies[i] != null ? m_flies[i].GetComponent<exSpriteAnimation>() : null;
                    ItemArt.Ensure(an, ItemPack3.FireflyGlow, true);
                }
            }
            else if (!flies && m_flies[0] != null)
            {
                for (int i = 0; i < 3; i++)
                {
                    if (m_flies[i] != null && m_flies[i].activeInHierarchy) SystemPool.Despawn(m_flies[i]);
                    m_flies[i] = null;
                }
            }
        }

        void SetFerretRun(bool run)
        {
            if (m_ferretAnim == null || run == m_ferretRunning) return;
            m_ferretRunning = run;
            ItemArt.Ensure(m_ferretAnim, run ? ItemPack3.FerretRun : ItemPack3.FerretIdle, true);
        }

        void Ferret(float dt, Vector2 me)
        {
            if (!m_ferret.activeInHierarchy) { m_ferret = null; return; }
            // trot to a spot behind the hero's back
            float back = transform.lossyScale.x < 0f ? 13f : -13f;
            var want = me + new Vector2(back, -1f);
            var d = want - m_ferretAt;
            float dist = d.magnitude;
            bool run = dist > 3f;
            if (dist > 120f) m_ferretAt = want;           // left behind (teleport, door): catch up at once
            else if (run) m_ferretAt += d / dist * Mathf.Min(dist, Mathf.Max(70f, dist * 4f) * dt);
            SetFerretRun(run);
            m_ferret.transform.position = new Vector3(Mathf.Round(m_ferretAt.x), Mathf.Round(m_ferretAt.y), m_ferret.transform.position.z);
            var s = m_ferret.transform.localScale;
            float face = run ? Mathf.Sign(d.x == 0f ? 1f : d.x) : Mathf.Sign(me.x - m_ferretAt.x == 0f ? 1f : me.x - m_ferretAt.x);
            m_ferret.transform.localScale = new Vector3(Mathf.Abs(s.x) * face, s.y, s.z);
            // fetch gold
            m_scan -= dt;
            if (m_scan <= 0f)
            {
                m_scan = 0.3f;
                m_gold.Clear();
                foreach (var p in FindObjectsOfType<Pickup>())
                    if (p != null && p.gameObject.activeInHierarchy && p.GetMessage() == "MsgCollectGold") m_gold.Add(p);
            }
            foreach (var p in m_gold)
            {
                if (p == null || !p.gameObject.activeInHierarchy) continue;
                var g = me - (Vector2)p.transform.position;
                float gd = g.magnitude;
                if (gd > 70f || gd < 1f) continue;
                p.transform.Translate((Vector3)(g / gd * Mathf.Min(gd, 110f * dt)), Space.World);
            }
        }

        void Fireflies(float dt, Vector2 me)
        {
            m_orbit += dt * 2.2f;
            for (int i = 0; i < 3; i++)
            {
                var f = m_flies[i];
                if (f == null || !f.activeInHierarchy) { m_flies[0] = null; return; }
                float a = m_orbit + i * 2.094f;
                Vector2 at = me + new Vector2(Mathf.Cos(a) * 17f, 8f + Mathf.Sin(a) * 7f);
                f.transform.position = new Vector3(Mathf.Round(at.x), Mathf.Round(at.y), f.transform.position.z);   // DepthHandler sorts by y
                if (m_flyRest[i] > 0f)
                {
                    m_flyRest[i] -= dt;
                    if (m_flyRest[i] <= 0f) ItemArt.Ensure(f.GetComponent<exSpriteAnimation>(), ItemPack3.FireflyGlow, true);
                    continue;
                }
                var t = ItemFixes.NearestMonster(at, 30f);
                if (t == null) continue;
                var aim = ItemFixes.AimPoint(t);
                if ((aim - at).sqrMagnitude > 11f * 11f) continue;
                m_flyRest[i] = 2f;
                ItemArt.Ensure(f.GetComponent<exSpriteAnimation>(), ItemPack3.FireflyDim, true);
                Pop(ItemPack3.FireflyZap, aim);
                if (ItemPack3.FireflyZapHit != null) FxFactory.SpawnOwned(ItemPack3.FireflyZapHit, aim, ModUtil.HeroSource());
            }
        }
    }

    // ---------------------------------------------------------------------------------------------------- patches
    [HarmonyPatch(typeof(Player), "Awake")]
    static class Patch_Items3PlayerAwake
    {
        static void Postfix(Player __instance)
        {
            if (__instance != null && R.Get<bool>(__instance, "m_isHero") && __instance.GetComponent<HeroPerks3>() == null)
                __instance.gameObject.AddComponent<HeroPerks3>();
        }
    }

    /// <summary>Safety net for the timed item modifiers: whenever the hero changes (SystemPlayers.OnHeroChange runs this for
    /// every active player, after the dead hero's data was reset), take them off every player and end the hero body's
    /// timers (the body is reused for the new hero). The new hero has not drunk or flipped anything yet at that point.</summary>
    [HarmonyPatch(typeof(PlayerData), "OnHeroChange")]
    static class Patch_Items3HeroChange
    {
        static void Postfix(PlayerData __instance)
        {
            try
            {
                if (__instance == null) return;
                HeroPerks3.StripTimed(__instance.GameData);
                var go = __instance.GameObject;
                var perks = go != null ? go.GetComponent<HeroPerks3>() : null;
                if (perks != null) perks.Cleanup();          // also the reused hero body: its timers belonged to the old hero
            }
            catch (Exception e) { Plugin.Log.LogWarning("Items3 hero change: " + e.Message); }
        }
    }

    [HarmonyPatch(typeof(Powerup), "Collect", new[] { typeof(Powerup), typeof(PlayerData), typeof(bool), typeof(bool) })]
    static class Patch_Items3Collect
    {
        static void Postfix(Powerup powerupPrefab, PlayerData player)
        {
            try { ItemPack3.OnCollect(powerupPrefab, player); }
            catch (Exception e) { Plugin.Log.LogWarning("Items3 collect: " + e.Message); }
        }
    }

    [HarmonyPatch(typeof(PlayerData), "OnKilledPlayer", new[] { typeof(PlayerData), typeof(bool) })]
    static class Patch_Items3Kill
    {
        static void Postfix(PlayerData __instance, PlayerData other)
        {
            try
            {
                if (__instance == null || !__instance.IsHero || other == null || other.IsHero) return;
                var go = __instance.GameObject;
                var perks = go != null ? go.GetComponent<HeroPerks3>() : null;
                if (perks != null) perks.OnKill(other);
            }
            catch (Exception e) { Plugin.Log.LogWarning("Items3 kill: " + e.Message); }
        }
    }

    [HarmonyPatch(typeof(Player), "MsgCollectHealth")]
    static class Patch_Items3HealthPickup
    {
        static void Postfix(Player __instance, MsgParams msgParams)
        {
            try
            {
                if (__instance == null || msgParams == null) return;
                var perks = __instance.GetComponent<HeroPerks3>();
                if (perks != null && R.Get<bool>(__instance, "m_isHero")) perks.OnHealthPickup(msgParams.m_float);
            }
            catch (Exception e) { Plugin.Log.LogWarning("Items3 health pickup: " + e.Message); }
        }
    }

    /// <summary>Runs after the other damage prefixes (plates, dodges, tier scaling) so it sees the hit as it will land.</summary>
    [HarmonyPatch(typeof(Health), "Damage", new[] { typeof(DamageInfo), typeof(bool) })]
    [HarmonyPriority(Priority.Low)]
    static class Patch_Items3Damage
    {
        static readonly AccessTools.FieldRef<Health, float> s_resist = AccessTools.FieldRefAccess<Health, float>("m_damageResistanceFinal");
        static readonly AccessTools.FieldRef<Health, bool> s_vuln = AccessTools.FieldRefAccess<Health, bool>("m_vulnerable");
        static readonly AccessTools.FieldRef<Health, float> s_vulnMult = AccessTools.FieldRefAccess<Health, float>("m_vulnerableDamageMult");
        static readonly AccessTools.FieldRef<Health, float> s_maxHit = AccessTools.FieldRefAccess<Health, float>("m_maxDamagePerHit");
        static readonly AccessTools.FieldRef<Health, TimedList<string>> s_inv = AccessTools.FieldRefAccess<Health, TimedList<string>>("m_invincibilityList");

        /// <summary>What Health.Damage will take off for this hit (same steps, in the same order).</summary>
        static float Predict(Health h, DamageInfo d)
        {
            float a = d.m_amount;
            if (d.m_source.m_damageMod != null) a = d.m_source.m_damageMod.Modify(a);
            float r = s_resist(h);
            if (r > 0f) a /= r;
            if (s_vuln(h)) a *= s_vulnMult(h);
            float mx = s_maxHit(h);
            if (mx > 0f) a = Mathf.Min(a, mx);
            return a;
        }

        static bool Prefix(Health __instance, DamageInfo damage, bool hitFriendly, ref bool __result, bool __runOriginal)
        {
            if (!__runOriginal) return false;
            try
            {
                if (damage == null || damage.m_source == null || damage.m_amount <= 0f) return true;
                var inv = s_inv(__instance);
                if (inv != null && !inv.Empty()) return true;
                if (!__instance.CanDamage(damage.m_source, hitFriendly)) return true;
                var hero = ModUtil.Hero();
                if (hero == null) return true;
                var attacker = damage.m_source.m_sourceOwnerPlayer;
                if (__instance.gameObject == hero)
                {
                    if (attacker == hero) return true;
                    var p = hero.GetComponent<HeroPerks3>();
                    if (p != null && !p.OnIncoming(__instance, damage, Predict(__instance, damage))) { __result = false; return false; }
                }
                else if (attacker == hero && !damage.m_isDamageFromStatus)
                {
                    var p = hero.GetComponent<HeroPerks3>();
                    if (p != null) damage.m_amount = p.OnOutgoing(__instance.gameObject, damage.m_amount);
                }
            }
            catch (Exception e) { Plugin.Log.LogWarning("Items3 damage: " + e.Message); }
            return true;
        }
    }
}
