using System.Collections.Generic;
using UnityEngine;
using CrawlFurther.Art;
using CrawlFurther.Gods;
using CrawlFurther.Items;
using CrawlFurther.Monsters;
using CrawlFurther.UI;
using CrawlFurther.Util;

namespace ExampleGod
{
    /// <summary>
    /// Glimmer, a small god with three starting monsters and one shop spell. Each monster is a vanilla monster's body
    /// (physics, AI, sounds) wearing a sheet from art/ and fighting with the moves its kit builds.
    /// </summary>
    public static class GlimmerPack
    {
        /// <summary>The sheet with the shop pedestal picture of every item this mod sells.</summary>
        public const string PedestalSheet = "GlimmerPedestals";

        /// <summary>Things to set up before any content pack runs. Called from the plugin's start callback.</summary>
        public static void Setup()
        {
            ShopPedestal.AddSheet(PedestalSheet);
        }

        // ---------------------------------------------------------------------------------------------- the monsters

        // Glimmer Rat: Bite (lunges in); Dash (a 60 px charge that hits everything on the way)
        static void RatKit(Player p, SpriteSheet sh)
        {
            var attacks = Kit.Attacks(p);
            var basic = attacks[0];
            var special = Kit.Special(p);
            var voice = Kit.Voice(p);
            int first = Strike.Mark(p);
            int bite = Kit.AddEffect(p, GlimmerFx.Bite, attach: true, destroyOnAnimEnd: true, offsetX: 10f, offsetY: 6f);
            int dash = Kit.AddEffect(p, GlimmerFx.DashHit, attach: true, destroyOnAnimEnd: true, offsetX: 4f, offsetY: 6f);

            var biteClip = Kit.Melee(sh, "Bite", "ModGlimmerRatBite", voice, 3, bite, 85f).Build();
            // 330 px/s over the four 0.045 s sprint frames: about 60 px
            var dashClip = new ClipBuilder(sh, "Dash", "ModGlimmerRatDash").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f)
                .Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff").EvF(2, "AnimMove", 330f).Ev(2, "AnimCollideOff")
                .Ev(2, "AnimAttack", dash).EvO(2, "AnimSound", voice)
                .Ev(6, "AnimMoveStop").Ev(6, "AnimCollideOn")
                .Ev(-1, "AnimRun")
                .Build();

            attacks.Clear();
            attacks.Add(Kit.Attack(basic, biteClip, cooldown: 1.2f, rangeInner: 14f, rangeOuter: 30f));
            Kit.SetSpecial(p, Kit.Attack(special, dashClip, 0f, rangeInner: 25f, rangeOuter: 66f, rangeRetreat: 0f), charge: 5.5f);
            Strike.Feet(p, first, 6f);
        }

        // Glimmer Grub: Spit (a bolt); Rise (bursts up, hurting what stands close, and heals itself 0.5)
        static void GrubKit(Player p, SpriteSheet sh)
        {
            var attacks = Kit.Attacks(p);
            var basic = attacks[0];
            var special = Kit.Special(p);
            var voice = Kit.Voice(p);
            int first = Strike.Mark(p);
            int bolt = Kit.AddEffect(p, GlimmerFx.Bolt, offsetX: 12f, offsetY: 6f);
            int burst = Kit.AddEffect(p, GlimmerFx.Burst, offsetX: 0.01f, offsetY: 4f);

            var spit = Kit.Shot(sh, "Spit", "ModGlimmerGrubSpit", 3, voice, 0f, bolt).Build();
            var rise = new ClipBuilder(sh, "Rise", "ModGlimmerGrubRise").Once()
                .Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop")
                .Ev(2, "AnimAttack", burst).EvO(2, "AnimSound", voice)
                .EvF(2, "GlimmerHeal", 0.5f)            // received by GlimmerGlow
                .Ev(-1, "AnimRun")
                .Build();

            attacks.Clear();
            attacks.Add(Kit.Attack(basic, spit, 1.6f, rangeInner: 45f, rangeOuter: 70f, retreatWhileAttacking: true));
            Kit.SetSpecial(p, Kit.Attack(special, rise, 0f, rangeInner: 0f, rangeOuter: 20f, rangeRetreat: 0f), 6f);
            Strike.Feet(p, first, 6f);
        }

        // Glimmer Moth: Puff (a slow spark that may daze); Dive (swoops through the hero)
        static void MothKit(Player p, SpriteSheet sh)
        {
            var attacks = Kit.Attacks(p);
            var basic = attacks[0];
            var special = Kit.Special(p);
            var voice = Kit.Voice(p);
            int first = Strike.Mark(p);
            int spark = Kit.AddEffect(p, GlimmerFx.Spark, offsetX: 7f, offsetY: 9f);
            int dive = Kit.AddEffect(p, GlimmerFx.DiveHit, attach: true, destroyOnAnimEnd: true, offsetX: 3f, offsetY: 7f);

            var puff = Kit.Shot(sh, "Puff", "ModGlimmerMothPuff", 3, voice, 0f, spark).Build();
            var diveClip = new ClipBuilder(sh, "Dive", "ModGlimmerMothDive").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f)
                .Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff").EvF(2, "AnimMove", 230f)
                .Ev(2, "AnimAttack", dive).EvO(2, "AnimSound", voice)
                .Ev(5, "AnimMoveStop")
                .Ev(-1, "AnimRun")
                .Build();

            attacks.Clear();
            attacks.Add(Kit.Attack(basic, puff, 1.4f, rangeInner: 26f, rangeOuter: 44f, rangeRetreat: 18f));
            Kit.SetSpecial(p, Kit.Attack(special, diveClip, 0f, rangeInner: 15f, rangeOuter: 46f, rangeRetreat: 0f), 5f);
            Strike.Feet(p, first, 8f);
        }

        /// <summary>The god's three monsters. Each id is also its sheet's name (art/GlimmerRat.png and .json).</summary>
        public static readonly List<MonsterDef> Monsters = new List<MonsterDef>
        {
            new MonsterDef { id = "GlimmerRat", basePrefab = "EnemyGiantRat_Fireball", health = 3.5f, speedMult = 1.05f,
                             evolveCost = 0f, kit = RatKit },
            new MonsterDef { id = "GlimmerGrub", basePrefab = "EnemyMushroom", health = 4.5f, speedMult = 0.9f,
                             evolveCost = 0f, kit = GrubKit, traits = new MonsterTraits().Add<GlimmerGlow>() },
            // every monster a player can become gets the game's vault challenge, its goal by tier (4 for a starter);
            // the moth hides between dives, so its goal is one hero level higher
            new MonsterDef { id = "GlimmerMoth", basePrefab = "EnemyFlyingEye_Dodge", health = 3f, speedMult = 1.1f,
                             evolveCost = 0f, kit = MothKit, traits = new MonsterTraits { stealth = true },
                             challenge = new ChallengeDef { goal = 5 } },
        };

        // ---------------------------------------------------------------------------------------------- the god

        /// <summary>Runs on every Glimmer monster after its kit: it leaves a Wisp cloud where it dies.</summary>
        static void DeathWisp(GameObject go, Player p)
        {
            Kit.AddDeathSpawn(p, GlimmerFx.Wisp);
            Strike.DeathAtFeet(p);
        }

        static GodDef God()
        {
            return new GodDef
            {
                name = "Glimmer",
                text = "Dead monsters leave a stinging wisp",
                flavour = "A lamp that never goes out,\nand the things that gather to it.",
                portraitArt = "DeityGlimmer",
                startingMonsters = new[] { "GlimmerRat", "GlimmerGrub", "GlimmerMoth" },
                monsters = Monsters.ToArray(),
                perk = DeathWisp,
                tips = new Dictionary<string, MonsterTip>
                {
                    { "ModGlimmerRat", new MonsterTip("Glimmer Rat", "Lunging bite", "Dash through the hero") },
                    { "ModGlimmerGrub", new MonsterTip("Glimmer Grub", "Spit a bolt", "Burst up and heal 0.5",
                                                       "Heals a little with every burst") },
                    { "ModGlimmerMoth", new MonsterTip("Glimmer Moth", "Puff a spark that may daze", "Dive through the hero",
                                                       "Fades from sight while it keeps still") },
                },
                pausePage = new PauseTopic("glimmer", "Glimmer", "GLIMMER", "lamps and moths", new[]
                {
                    "When a " + PauseTips.Hi("Glimmer") + " monster dies it leaves a wisp that stings the hero for a second.",
                    "- The Grub heals 0.5 each time it bursts up.",
                    "- The Moth fades from sight while it keeps still.",
                }),
            };
        }

        /// <summary>The content pack: runs once the game's prefabs are loaded.</summary>
        public static void Register()
        {
            GlimmerFx.Build();
            DeityFactory.Register(God());
            Vault.AddMonsterLine("GlimmerRat", "Glimmer Rat", "A rat with a lamp for a tail. It bites, then charges.");
            Vault.AddMonsterLine("GlimmerGrub", "Glimmer Grub", "Spits bolts of cold light and heals as it bursts up.");
            Vault.AddMonsterLine("GlimmerMoth", "Glimmer Moth", "Puffs sparks that daze and fades from sight when still.");
            GlimmerItems.Register();
        }

        /// <summary>True for a body of one of the Glimmer monsters (prefab or pooled instance).</summary>
        public static bool IsGlimmer(GameObject body)
        {
            if (body == null) return false;
            string prefab = ModUtil.PrefabName(body);
            foreach (var m in Monsters) if (m.PrefabName == prefab) return true;
            return false;
        }
    }
}
