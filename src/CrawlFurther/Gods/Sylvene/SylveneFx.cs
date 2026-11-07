using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    using CrawlFurther.Art;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Sylvene's effect templates: seeds and pods, and every monster's attacks, ground effects and tells. Art origins are
    /// the sheets' (art/out_sylvene/TIMING.md); damage is before the tier multiplier.
    /// </summary>
    public static class SylveneFx
    {
        public const float GrowTime = 2.5f, FastGrowTime = 1.5f, TriggerRadius = 20f;

        // seeds and pods (PodBurst, RootSpike, RootRunner, ThornPatch and Maggots are also copied by the hero's items)
        public static GameObject Seed, SeedFast, PodBurst, PodBurstBig, RootSpike, RootRunner, ThornPatch, Maggots;
        // tier 1
        public static GameObject SporePuff, SproutPuff, TendMote, ThornLash, TaprootRunner, SpitGlob, DivePuff;
        // tier 2
        public static GameObject HuskClub, ShakeRing, BelchCloud, PollenLance, ThornSwipeA, ThornSwipeB, SweepPatch, OvergrowPatch,
                                 StranglerBite, LassoLash, PodSling, SeedSling, GallNeedle, WaspDash, BileDrop, BileHit, BilePuddle;
        // tier 3
        public static GameObject BehemothGore, BehemothRam, Bush, BushSwing, BushSwingBig, LanceTrim, PuffRing, PuffLand, PuffWall,
                                 Spine, ShamblerBurst, RootEruption, SproutRise, Wisp, Berry, BerrySmall, BerrySplit, BerryPop, Shimmer,
                                 PollenDart, PollenCloud, SeedShot, StrafeNeedle, FurrowVine, LilyBite, RotCloud, WyrmFront, WyrmBack,
                                 Thorn, Bladder, GasPuff, GasTile, BladderBurst, QueenStab, QueenDive, DroneRing;
        /// <summary>The Briar Champion's lance thrust and lunge hitboxes, one per lance length.</summary>
        public static readonly GameObject[] Lance = new GameObject[4], Lunge = new GameObject[4];
        public static GameObject SproutSpawner, ShamblerSpawner;
        public static exSpriteAnimClip BushDrag, BushTaut;
        public static StatusOverlayDef GraftInd, StalkInd, DustInd, SpoiledInd;

        /// <summary>True for the two seed templates (they become pods; anything else a projectile leaves is just spawned).</summary>
        public static bool IsSeed(GameObject t) { return t != null && (t == Seed || t == SeedFast); }

        public static void Build()
        {
            var poison = FxFactory.GetStatus("StatusPoisoned");
            var bleed = FxFactory.GetStatus("StatusBleeding");
            var stuck = FxFactory.GetStatus("StatusStuckToFloor");

            // ---- seeds and pods: the god's perk, and half the pack's moves
            PodBurst = FxKit.TimedHit("ModPodBurst", "skydropExplode", "FxSeed", "Burst", 1, 4, 0.75f, 0.6f, poison, 1f, colliderScale: 0.8f, canFlip: false);
            Strike.Ground(PodBurst, "FxSeed", 10, 16, 26f, 12f);
            PodBurstBig = FxKit.TimedHit("ModSylPodBurst", "skydropExplode", "FxSylPodBurst", "Play", 2, 5, 0.75f, 0.6f, poison, 1f, canFlip: false);
            Strike.Ground(PodBurstBig, "FxSylPodBurst", 21, 16, 34f, 16f);
            Seed = MakeSeed("ModSeed", "FxSeed", GrowTime);
            SeedFast = MakeSeed("ModSylSeedFast", "FxSylSeedFast", FastGrowTime);
            RootSpike = FxKit.TimedHit("ModRootSpike", "skydropExplode", "FxRootLine", "Play", 3, 5, 0.5f, 0.2f, stuck, 1f, colliderScale: 0.45f);
            Strike.Ground(RootSpike, "FxRootLine", 15, 11, 20f, 8f);
            RootRunner = Runner("ModRootRunner");
            ThornPatch = FxKit.TimedHit("ModThornPatch", "SkMageSlimeEffect", "FxThornPatch", "Life", 3, 21, 0.5f, 0.05f, bleed, 0.3f, rate: 0.6f, canFlip: false);
            Strike.Ground(ThornPatch, "FxThornPatch", 13, 5, 18f, 7f);
            Maggots = FxKit.Projectile("ModMaggotSwarm", "DFX_PriestessRune", "FxMaggots", "Fly", 40f, 3.5f, 0.5f, 0.15f, poison, 0.3f,
                                       accel: 40f, speedMax: 100f, rotate: false, destroyOnHit: false);
            if (Maggots != null) FxFactory.SetDamage(Maggots, 0.5f, rate: 0.45f, knockback: 0.1f, status: poison, statusChance: 0.3f, collisionAtStart: true);

            // ---- Sporeling
            SporePuff = FxKit.Cloud("ModSporePuff", "FxSporeCloud", "Play", 70f, 0.6f, 0.5f, poison, 0.6f, 0.08f, 0.1f, 0.11f, 0.11f, 0.12f, 0.12f);
            Strike.Collider(SporePuff, 16f, 14f);
            SproutPuff = FxKit.Cloud("ModSproutPuff", "FxSylSproutPuff", "Play", 50f, 0.35f, 0.5f, poison, 0.35f);
            Strike.Collider(SproutPuff, 11f, 10f);
            TendMote = FxKit.Visual("ModSylTendMote", "FxSylTendMote", "Play");

            // ---- Thornbiter: a vine whip; roots that race along the floor, pin the hero and leave a seed where they stop
            ThornLash = AimedMelee.Rotating(FxKit.BodyHit("ModThornLash", 0.7f, 0f, 0.5f, 0.2f, bleed, 0.25f));
            Strike.HitBox(ThornLash, 22f, 14f);   // the bud at full reach: x 4..26
            TaprootRunner = Runner("ModSylTaproot");
            Plants(TaprootRunner, Seed, false);

            // ---- Rotfly: a spit that seeds the floor when it misses; a dive that bursts a puff on the hero
            SpitGlob = FxKit.Projectile("ModSylSpit", "DFX_skelMageNewProjectile", "FxPoisonGlob", "Fly", 170f, 0.55f, 0.6f, 0.3f, poison, 0.5f);
            Strike.Collider(SpitGlob, 7f, 7f);
            Plants(SpitGlob, Seed, true);
            DivePuff = FxKit.TimedHit("ModSylDivePuff", "skydropExplode", "FxSporeCloud", "Play", 0, 3, 0.8f, 0.3f, poison, 1f, canFlip: false);
            Strike.Ground(DivePuff, "FxSporeCloud", 10, 8, 18f, 12f);

            // ---- Spore Husk: a club that rings the floor; a wide cone of spores
            HuskClub = AimedMelee.Rotating(FxKit.BodyHit("ModHuskClub", 1.1f, 0f, 0.9f, 0.15f, poison, 0.3f));
            Strike.HitBox(HuskClub, 14f, 12f);
            ShakeRing = FxKit.Visual("ModSylShakeRing", "FxSylShakeRing", "Play");
            Strike.ArtAt(ShakeRing, "FxSylShakeRing", 20, 8);
            BelchCloud = FxKit.Cloud("ModSylBelchCloud", "FxSporeCloud", "Play", 90f, 0.9f, 0.8f, poison, 1f, 0.08f, 0.1f, 0.12f, 0.14f, 0.16f, 0.16f);
            Strike.Collider(BelchCloud, 16f, 14f);

            // ---- Bloom Witch
            PollenLance = FxKit.Projectile("ModPollenLance", "DFX_skelMageNewProjectile", "FxPollen", "Fly", 280f, 0.8f, 0.9f, 0.4f, poison, 0.25f,
                                           destroyOnHit: false);
            if (PollenLance != null) FxFactory.SetDamage(PollenLance, 0.9f, rate: 0.3f, knockback: 0.4f, status: poison, statusChance: 0.25f, collisionAtStart: true);
            GraftInd = ModStatus.Indicator("ModSylGraftInd", "FxSylGraftPod", "Loop", 1f, OverlayAt.Head);

            // ---- Bramble Knight: two sweeps, the second plants a thorn patch at its tip; Overgrow bursts four patches
            ThornSwipeA = AimedMelee.Rotating(GodsBArc.Swipe("ModThornSwipeA", "OrcSwipe", "FxSylThornSweep", "Slash", 9, 21, 0.9f, 0.6f, bleed, 0.25f));
            ThornSwipeB = AimedMelee.Rotating(GodsBArc.Swipe("ModThornSwipeB", "OrcSwipe2", "FxSylThornSweep", "Upslash", 9, 21, 1.0f, 0.8f, bleed, 0.25f));
            Strike.Collider(ThornSwipeB, 18.82f, 13.51f, 9f, 0f);
            SweepPatch = Lingering("ModSylSweepPatch", "SkMageSlimeEffect", "FxSylThornPatch", "Rise", "Life", 4, "Wither",
                                   0.3f, 0.05f, bleed, 0.6f, 0.6f, 11, 10, 16f, 7f);
            OvergrowPatch = Lingering("ModSylOvergrowPatch", "SkMageSlimeEffect", "FxSylThornPatch", "Rise", "Life", 4, "Wither",
                                      0.8f, 0.3f, bleed, 0.4f, 0.8f, 11, 10, 16f, 7f);

            // ---- Strangler Vine: a bite; a lasso that slings a pod (or a seed) at the hero, or lashes him
            StranglerBite = AimedMelee.Rotating(FxKit.BodyHit("ModSylStranglerBite", 1.0f, 0f, 0.5f, 0.12f, poison, 0.25f));
            Strike.HitBox(StranglerBite, 14f, 12f);
            LassoLash = FxKit.Projectile("ModSylLasso", "DFX_skelMageNewProjectile", "FxSylLasso", "Fly", 220f, 0.28f, 1.0f, 0.5f);
            Strike.Collider(LassoLash, 10f, 8f);
            PodSling = FxKit.Projectile("ModSylPodSling", "DFX_skelMageNewProjectile", "FxSylPodSling", "Fly", 190f, 0.6f, 0.4f, 0.2f, rotate: false);
            Strike.Collider(PodSling, 8f, 8f);
            Plants(PodSling, PodBurstBig, false);
            SeedSling = FxKit.Projectile("ModSylSeedSling", "DFX_skelMageNewProjectile", "FxSylSeedShot", "Fly", 190f, 0.6f, 0.01f, 0f);
            if (SeedSling != null) { FxFactory.SetContacts(SeedSling, destroyOnHit: false); Strike.Collider(SeedSling, 4f, 4f); }
            Plants(SeedSling, Seed, false);

            // ---- Gall Wasp: needles that plant fast seeds, a dart that drops two
            GallNeedle = FxKit.Projectile("ModGallNeedle", "DFX_skelMageNewProjectile", "FxGallNeedle", "Fly", 230f, 0.5f, 0.8f, 0.3f, poison, 0.3f);
            Strike.Collider(GallNeedle, 10f, 6f);
            Plants(GallNeedle, SeedFast, false);
            WaspDash = AimedMelee.Rotating(FxKit.BodyHit("ModWaspDash", 0.9f, 0.3f, 0.6f, 0.4f, poison, 0.25f));
            Strike.HitBox(WaspDash, 16f, 12f);

            // ---- Bloatfly: a cone of bile gobs; a stream straight down that leaves spoiling puddles
            BileDrop = FxKit.Projectile("ModSylBileDrop", "DFX_skelMageNewProjectile", "FxSylBileDrop", "Fly", 190f, 0.32f, 0.8f, 0.2f, poison, 0.4f);
            Strike.Collider(BileDrop, 7f, 7f);
            BileHit = FxKit.TimedHit("ModSylBileHit", "skydropExplode", "FxSylBileSplash", "Play", 0, 3, 0.35f, 0.1f, poison, 0.6f, canFlip: false);
            Strike.Ground(BileHit, "FxSylBileSplash", 13, 10, 14f, 8f);
            BilePuddle = FxKit.Visual("ModSylBilePuddle", "FxSylBilePuddle", "Life", loop: true, lifetime: BilePuddleFx.Life);
            if (BilePuddle != null)
            {
                Strike.ArtAt(BilePuddle, "FxSylBilePuddle", 12, 7);
                FxFactory.OnSpawn[BilePuddle] = i => { var p = i.GetComponent<BilePuddleFx>() ?? i.AddComponent<BilePuddleFx>(); p.enabled = true; };
            }
            SpoiledInd = ModStatus.Indicator("ModSylSpoiledInd", "FxSylSpoiled", "Loop", -2f, OverlayAt.Feet);

            BuildFinals(poison, bleed, stuck);
            Plugin.Log.LogInfo("Sylvene FX templates built");
        }

        static void BuildFinals(Status poison, Status bleed, Status stuck)
        {
            // ---- Briar Behemoth: a tusk hook, a charge, and the bush it drags
            BehemothGore = AimedMelee.Rotating(GodsBArc.Swipe("ModBehemothGore", "OrcSwipe", "FxSylTuskHook", "Play", 9, 19, 1.4f, 1.2f, bleed, 0.3f));
            BehemothRam = AimedMelee.Rotating(FxKit.BodyHit("ModBehemothRam", 1.2f, 0.4f, 1.6f, 0.45f, bleed, 0.3f));
            Strike.HitBox(BehemothRam, 30f, 16f);
            var bush = SpriteSheets.Get("FxSylBush");
            if (bush != null)
            {
                BushDrag = new ClipBuilder(bush, "Drag", "ModSylBushDrag").Loop().Build();
                BushTaut = new ClipBuilder(bush, "Taut", "ModSylBushTaut").Loop().Build();
                Bush = FxFactory.Visual("ModSylBush", bush, BushDrag, true);
                FxFactory.SetEffect(Bush, destroyOnAnimEnd: false, canFlip: false, freeRotate: false);
                Strike.ArtAt(Bush, "FxSylBush", 13, 22);
            }
            BushSwing = FxKit.TimedHit("ModSylBushSwing", "skydropExplode", "FxSylBushSwing", "Play", 1, 4, 1.0f, 1.0f, bleed, 0.4f);
            Strike.Ground(BushSwing, "FxSylBushSwing", 28, 22, 44f, 22f);
            BushSwingBig = FxKit.TimedHit("ModSylBushSwingBig", "skydropExplode", "FxSylBushSwing", "Play", 1, 4, 1.2f, 1.2f, bleed, 0.5f);
            Strike.Ground(BushSwingBig, "FxSylBushSwing", 28, 22, 44f, 22f);

            // ---- Briar Champion: the lance at each length (20, 26, 32, 38 px past the hand) and the lunge 6 px further
            for (int k = 0; k < 4; k++)
            {
                float len = ChampionLance.LanceLength(k);
                Lance[k] = AimedMelee.Rotating(FxKit.BodyHit("ModSylLance" + k, 1.2f, 0f, 0.8f, 0.12f, bleed, 0.3f));
                Strike.HitBox(Lance[k], len, 10f);
                Lunge[k] = AimedMelee.Rotating(FxKit.BodyHit("ModSylLunge" + k, 1.5f, 0f, 1.2f, 0.14f, bleed, 0.4f));
                Strike.HitBox(Lunge[k], len + 6f, 12f);
            }
            LanceTrim = FxKit.Visual("ModSylLanceTrim", "FxSylLanceTrim", "Play");

            // ---- Puffball Brute: a ring of spores round the fists, the landing ring, the wall rebound
            PuffRing = FxKit.TimedHit("ModSylPuffRing", "skydropExplode", "FxSylPuffRing", "Play", 1, 4, 1.3f, 1.1f, poison, 0.3f, canFlip: false);
            Strike.Ground(PuffRing, "FxSylPuffRing", 18, 12, 32f, 12f);
            PuffLand = FxKit.TimedHit("ModSylPuffLand", "skydropExplode", "FxSylPuffRing", "Play", 1, 4, 1.3f, 1.2f, poison, 1f, canFlip: false);
            Strike.Ground(PuffLand, "FxSylPuffRing", 18, 12, 34f, 14f);
            PuffWall = FxKit.BodyHit("ModSylPuffWall", 1.0f, 0f, 1.2f, 0.3f);
            Strike.HitBox(PuffWall, 26f, 20f, 0f, 12f);

            // ---- Cordyceps Saint: a spine; the shambler's burst into three seeds
            Spine = FxKit.Projectile("ModSylSpine", "DFX_skelMageNewProjectile", "FxSylSpine", "Fly", 240f, 0.55f, 1.1f, 0.3f, poison, 0.3f);
            Strike.Collider(Spine, 10f, 5f);
            StalkInd = ModStatus.Indicator("ModSylStalkInd", "FxSylStalk", "Loop", 1f, OverlayAt.Head);
            ShamblerBurst = FxKit.Inert("ModSylShamblerBurst", "FxSylPodBurst", "Play");
            if (ShamblerBurst != null)
                FxFactory.OnSpawn[ShamblerBurst] = i => { var s = i.GetComponent<ScatterSeeds>() ?? i.AddComponent<ScatterSeeds>(); s.count = 3; s.enabled = true; };

            // ---- Rot Mother: roots erupt under the hero; Sprouts burst up round him; the orchard's wisps
            RootEruption = FxKit.TimedHit("ModRootEruption", "skydropExplode", "FxSylRootErupt", "Play", 3, 5, 1.0f, 1.0f, stuck, 0.6f,
                                          durations: new[] { 0.3f, 0.25f, 0.2f, 0.08f, 0.1f, 0.15f, 0.2f });
            Strike.Ground(RootEruption, "FxSylRootErupt", 18, 13, 29f, 13f);
            SproutRise = FxKit.TimedHit("ModSylSproutRise", "skydropExplode", "FxSylSproutBurst", "Play", 1, 3, 0.6f, 0.5f, canFlip: false);
            Strike.Ground(SproutRise, "FxSylSproutBurst", 11, 12, 16f, 10f);
            Wisp = FxKit.Visual("ModSylWisp", "FxSylHuskWisp", "Fly", loop: true, lifetime: 2f);
            if (Wisp != null) FxFactory.OnSpawn[Wisp] = i => { var w = i.GetComponent<WispFx>() ?? i.AddComponent<WispFx>(); w.enabled = true; };

            // ---- Nightshade: a berry that splits in three; the shimmer of a hidden pod
            BerryPop = FxKit.Visual("ModSylBerryPop", "FxSylBerryPop", "Play");
            Strike.ArtAt(BerryPop, "FxSylBerryPop", 10, 12);
            BerrySmall = FxKit.Projectile("ModSylBerrySmall", "DFX_skelMageNewProjectile", "FxSylBerrySmall", "Fly", 150f, 0.35f, 1.0f, 0.2f, poison, 0.3f);
            Strike.Collider(BerrySmall, 6f, 6f);
            BerrySplit = FxKit.Emitter("ModSylBerrySplit", BerrySmall, 3);
            if (BerrySplit != null) FxFactory.SetEffect(BerrySplit, destroyOnAnimEnd: false, destroyAfter: 0.3f, alsoSpawn: BerryPop, freeRotate: false);
            Berry = FxKit.Projectile("ModSylBerry", "DFX_skelMageNewProjectile", "FxSylBerry", "Fly", 170f, 0.6f, 1.0f, 0.3f, poison, 0.35f);
            if (Berry != null)
            {
                FxFactory.SetEffect(Berry, destroyOnAnimEnd: false, destroyAfter: 0.6f, spawnOnDestroy: BerrySplit, freeRotate: true);
                FxFactory.SetContacts(Berry, destroyOnHit: true, spawnOnHit: BerrySplit);
                Strike.Collider(Berry, 8f, 8f);
            }
            Shimmer = FxKit.Visual("ModSylShimmer", "FxSylShimmer", "Loop", loop: true);

            // ---- Pollen Monarch: a fan of darts; the pollen storm that dusts the hero
            PollenDart = FxKit.Projectile("ModPollenDart", "DFX_skelMageNewProjectile", "FxPollenDart", "Fly", 170f, 0.7f, 1.0f, 0.4f, poison, 0.25f);
            Strike.Collider(PollenDart, 8f, 8f);
            PollenCloud = FxKit.TimedHit("ModSylPollenCloud", "skydropExplode", "FxSylPollenCloud", "Play", 1, 6, 0.3f, 0.1f, poison, 0.3f, rate: 0.5f);
            Strike.Ground(PollenCloud, "FxSylPollenCloud", 28, 18, 46f, 14f);
            DustInd = ModStatus.Indicator("ModSylDustInd", "FxSylDust", "Loop", -2f, OverlayAt.Feet);

            // ---- The Sower: a seed shot; the needles of a strafe and the vine of their furrow
            SeedShot = FxKit.Projectile("ModSylSeedShot", "DFX_skelMageNewProjectile", "FxSylSeedShot", "Fly", 240f, 0.45f, 1.0f, 0.3f);
            Strike.Collider(SeedShot, 6f, 6f);
            Plants(SeedShot, Seed, false);
            StrafeNeedle = FxKit.Projectile("ModSylStrafeNeedle", "DFX_skelMageNewProjectile", "FxGallNeedle", "Fly", 220f, 0.5f, 0.6f, 0.2f);
            Strike.Collider(StrafeNeedle, 10f, 6f);
            Plants(StrafeNeedle, Seed, false);
            var vine = SpriteSheets.Get("FxSylFurrowVine");
            if (vine != null)
            {
                // 18 s: about as long as the pods it joins stay ripe
                FurrowVine = FxFactory.Visual("ModSylFurrowVine", vine, new ClipBuilder(vine, "Grow", "ModSylFurrowVineClip").Once().Then("Loop", 60).Build(), false);
                FxFactory.SetEffect(FurrowVine, destroyOnAnimEnd: true, canFlip: false, freeRotate: true);
                Strike.ArtAt(FurrowVine, "FxSylFurrowVine", 7, 3);
            }

            // ---- Carrion Lily: a bite at the end of its stalk; a cone of rot
            LilyBite = AimedMelee.Rotating(FxKit.BodyHit("ModLilyBite", 1.3f, 0f, 0.8f, 0.12f, poison, 0.5f));
            Strike.HitBox(LilyBite, 16f, 14f);
            RotCloud = FxKit.Cloud("ModSylRotCloud", "FxSylRotCloud", "Play", 110f, 1.2f, 1.0f, poison, 1f, 0.08f, 0.1f, 0.12f, 0.14f, 0.16f, 0.16f);
            Strike.Collider(RotCloud, 14f, 12f);

            // ---- Briar Wyrm: the mace in front and behind; the spiral's thorns
            WyrmFront = AimedMelee.Rotating(FxKit.BodyHit("ModSylWyrmFront", 1.2f, 0f, 1.4f, 0.12f, bleed, 0.25f));
            Strike.HitBox(WyrmFront, 16f, 14f);
            WyrmBack = AimedMelee.Rotating(FxKit.BodyHit("ModSylWyrmBack", 1.2f, 0f, 1.4f, 0.12f, bleed, 0.25f));
            Strike.HitBox(WyrmBack, 16f, 14f);
            Thorn = FxKit.Projectile("ModSylThorn", "DFX_skelMageNewProjectile", "FxSylThorn", "Fly", 130f, 0.9f, 0.6f, 0.2f, bleed, 0.2f);
            Strike.Collider(Thorn, 8f, 8f);

            // ---- Blight Bellows: the bouncing bladder, its puffs and burst, and the lanes (all twice as long-lived: Stale Air)
            Bladder = FxKit.Visual("ModSylBladder", "FxSylBladder", "Hop", loop: true, lifetime: 3f);
            if (Bladder != null) FxFactory.OnSpawn[Bladder] = i => { var b = i.GetComponent<BladderFx>() ?? i.AddComponent<BladderFx>(); b.enabled = true; };
            GasPuff = Lingering("ModSylGasPuff", "SkMageSlimeEffect", "FxSylGasPuff", "Play", "Life", 5, null, 0.3f, 0.05f, poison, 0.5f, 0.6f, 12, 12, 16f, 9f);
            GasTile = Lingering("ModSylGasTile", "SkMageSlimeEffect", "FxSylGasTile", "Rise", "Life", 5, null, 0.3f, 0.05f, poison, 0.5f, 0.6f, 8, 9, 12f, 8f);
            BladderBurst = FxKit.TimedHit("ModSylBladderBurst", "skydropExplode", "FxSylBladderBurst", "Play", 1, 4, 1.1f, 0.6f, poison, 1f, canFlip: false);
            Strike.Ground(BladderBurst, "FxSylBladderBurst", 18, 16, 26f, 12f);

            // ---- Carrion Queen: the stab, the steered dive, the drone ring (dazes through code: see QueenDrone)
            QueenStab = AimedMelee.Rotating(FxKit.BodyHit("ModSylQueenStab", 1.2f, 0f, 0.5f, 0.12f, poison, 0.4f));
            Strike.HitBox(QueenStab, 16f, 12f);
            QueenDive = AimedMelee.Rotating(FxKit.BodyHit("ModSylQueenDive", 1.4f, 0.5f, 0.8f, 0.4f, poison, 0.6f));
            Strike.HitBox(QueenDive, 18f, 14f);
            DroneRing = FxKit.Visual("ModSylDroneRing", "FxSylDroneRing", "Play");
            Strike.ArtAt(DroneRing, "FxSylDroneRing", 54, 28);
        }

        static GameObject MakeSeed(string name, string art, float grow)
        {
            var seed = FxKit.Inert(name, art, "Life", destroyOnAnimEnd: true, thenAnim: "Ripe", thenRepeat: 30);
            if (seed != null)
                FxFactory.OnSpawn[seed] = i =>
                {
                    var s = i.GetComponent<SeedFx>() ?? i.AddComponent<SeedFx>();
                    s.enabled = true;
                    s.growTime = grow;
                    s.triggerRadius = TriggerRadius;
                };
            return seed;
        }

        // roots that race along the floor (a clone of the vanilla web dropper) leaving root spikes behind them
        static GameObject Runner(string name)
        {
            var go = FxFactory.Clone("WebDropper", name);
            if (go == null) return null;
            FxFactory.SetEffect(go, destroyOnAnimEnd: false, destroyAfter: 0.6f, freeRotate: true);
            FxFactory.SetMotion(go, 170f, trail: RootSpike, trailDist: 13f, collide: true);
            return go;
        }

        static void Plants(GameObject tmpl, GameObject what, bool skipOnHero)
        {
            if (tmpl == null || what == null) return;
            FxFactory.OnSpawn[tmpl] = i =>
            {
                var p = i.GetComponent<PlantOnEnd>() ?? i.AddComponent<PlantOnEnd>();
                p.spawn = what; p.skipOnHero = skipOnHero; p.enabled = true;
            };
        }

        /// <summary>A ground effect that rises (<paramref name="rise"/>), lingers (<paramref name="life"/> x
        /// <paramref name="loops"/>) and withers, hurting whoever stands in it every <paramref name="rate"/> s.</summary>
        static GameObject Lingering(string name, string vanilla, string art, string rise, string life, int loops, string wither,
                                    float damage, float knock, Status status, float chance, float rate, int gx, int gy, float w, float h)
        {
            var sh = SpriteSheets.Get(art);
            var go = FxFactory.Clone(vanilla, name);
            if (go == null || sh == null) return go;
            FxFactory.StripChildren(go);
            var cb = new ClipBuilder(sh, rise, name + "Clip").Once().Then(life, loops);
            if (wither != null) cb.Then(wither);
            int off = cb.FrameCount - (wither != null ? sh.Anim(wither).frames.Length : 1);
            cb.Ev(0, "AnimDamageOn").Ev(off, "AnimDamageOff");
            FxFactory.Reskin(go, cb.Build(), sh);
            var spr = go.GetComponent<exSprite>();
            if (spr != null) { spr.anchor = exPlane.Anchor.BotCenter; spr.offset = Vector2.zero; }
            FxFactory.SetEffect(go, destroyOnAnimEnd: true, canFlip: false, freeRotate: false);
            foreach (var m in go.GetComponents<ParticleMotion>()) { R.Set(m, "m_trailObject", null); m.enabled = false; }
            FxFactory.SetDamage(go, damage, rate: rate, knockback: knock, status: status, statusChance: chance, collisionAtStart: false);
            ImpactFx.Theme(go, art);
            Strike.Ground(go, art, gx, gy, w, h);
            FxKit.NoTint(go);
            return go;
        }
    }
}
