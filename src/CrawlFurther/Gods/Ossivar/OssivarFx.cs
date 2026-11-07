using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Art;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;
    using CrawlFurther.Content.Gods.Vhorrul;

    /// <summary>Ossivar's effect templates (art: tools/sprites/ossivar_v2_fx.py; origins in art/out_ossivar/TIMING.md).</summary>
    public static class OssivarFx
    {
        /// <summary>The Carrion Vulture's rake bleeds this often (always while its Death Watch is on).</summary>
        public const float RakeBleedChance = 0.3f;

        // the god perk and things every line shares
        public static GameObject BonePile, MarrowVeins, PlateOrbit, PlateShatter, RatSpawner, RatBite, HitSplat;
        // kept for the hero items that clone them (ItemPack2): a boomerang skull and a spike burst
        public static GameObject Skull, SpikeBurst;
        // tier 1
        public static GameObject SkullLob, SkullFloor, RattleSwipe, HoundBite, HoundHowl, Scent, CrowPeck, Splinter, Caw;
        public static exSpriteAnimClip SkullChatter, SkullRoll;
        // tier 2
        public static GameObject LancerThrust, BoneSpear, SpearStand, DigSpade, DigHole, TuskGore, TuskRush, TuskShard, PileGlow,
                                 BarghestBite, PounceBite, PounceDust, MarrowBolt, VultureRake, DiveShadow, DiveHit, WatchRing;
        public static exSpriteAnimClip SpearCrumble;
        public static Status Buried;
        public static StatusOverlayDef EyeFlare;
        // tier 3
        public static GameObject LanceSweep, JoustTip, JoustTrample, LanceThrow, FootThrustTip, HookRake, Harpoon, RopeSeg,
                                 MalletSmash, StoneRise, Headstone, StoneFall, CoffinSlam, WhirlHit, FlingHit, MammothTusk, StepDust,
                                 Crack, CrossSpike, RazorSlash, Quill, CerberusBite, GasConeHit, GasConeArt, GrimBite, GrimLunge,
                                 GrimRing, CrowShot, CrowWall, OssuarySlam, RibCrack, Rib, WyrmBite, WyrmLash, MarrowLine, RocStab,
                                 RocDrop, DropShadow;
        public static exSpriteAnimClip StoneCrack, StoneFallSide, StoneFallFront, StoneFallBack, StoneCrumble,
                                       RibRise, RibRiseL, RibStand, RibStandL, RibBreak, RibBreakL;

        static exSpriteAnimClip Clip(string sheet, string anim, bool loop = false)
        {
            var sh = SpriteSheets.Get(sheet);
            if (sh == null || !sh.Has(anim)) { Plugin.Log.LogWarning("Ossivar: missing " + sheet + "/" + anim); return null; }
            var b = new ClipBuilder(sh, anim, "ModOss_" + sheet + "_" + anim);
            return (loop ? b.Loop() : b.Once()).Build();
        }

        /// <summary>A floor object that stays until its owner despawns it: <paramref name="first"/> once, then <paramref name="then"/>.</summary>
        static GameObject Standing(string name, string sheet, string first, string then, int gx, int gy)
        {
            var sh = SpriteSheets.Get(sheet);
            if (sh == null || !sh.Has(first) || !sh.Has(then)) { Plugin.Log.LogWarning("Ossivar: missing " + sheet + "/" + first); return null; }
            var clip = new ClipBuilder(sh, first, name + "Clip").Once().Then(then, 60).Build();
            var go = FxFactory.Visual(name, sh, clip, false, 60f);
            Strike.ArtAt(go, sheet, gx, gy);
            return go;
        }

        static GameObject Vis(string name, string sheet, string anim, int gx, int gy, bool loop = false)
        {
            var go = FxKit.Visual(name, sheet, anim, loop);
            Strike.ArtAt(go, sheet, gx, gy);
            return go;
        }

        static GameObject Thrown(string name, string sheet, int gx, int gy, float speed, float life, float damage, float knock,
                               Status status = null, float chance = 1f, bool rotate = true, bool destroyOnHit = true)
        {
            var go = FxKit.Projectile(name, "DFX_skelMageNewProjectile", sheet, "Fly", speed, life, damage, knock, status, chance,
                                      rotate: rotate, destroyOnHit: destroyOnHit);
            Strike.ArtAt(go, sheet, gx, gy);
            return go;
        }

        static GameObject Melee(string name, float damage, float knock, float w, float h, Status status = null, float chance = 1f,
                                float life = 0.15f, float rate = 0f)
        {
            var go = AimedMelee.Rotating(FxKit.BodyHit(name, damage, rate, knock, life, status, chance));
            Strike.HitBox(go, w, h);
            return go;
        }

        static void Add<T>(GameObject template) where T : Component
        {
            if (template != null) FxFactory.OnSpawn[template] = i => { if (i.GetComponent<T>() == null) i.AddComponent<T>(); };
        }

        public static void Build()
        {
            var bleed = FxFactory.GetStatus("StatusBleeding");
            var poison = FxFactory.GetStatus("StatusPoisoned");

            // ---- the perk: piles (about 20 s), plates and their break
            BonePile = FxKit.Visual("ModBonePile", "FxBonePile", "Life");
            if (BonePile != null)
            {
                Strike.ArtAt(BonePile, "FxBonePile", 10, 12);
                FxFactory.OnSpawn[BonePile] = i =>
                {
                    if (i.GetComponent<BonePileFx>() == null) i.AddComponent<BonePileFx>();
                    var c = i.GetComponent<OssBoneCrawlFx>() ?? i.AddComponent<OssBoneCrawlFx>();
                    c.Restart();
                };
            }
            MarrowVeins = Vis("ModOssMarrowVeins", "FxBonePile", "Veins", 10, 12, loop: true);
            PlateOrbit = FxKit.Visual("ModBonePlateOrbit", "FxBonePlate", "Play", loop: true);
            if (PlateOrbit != null) FxFactory.SetEffect(PlateOrbit, destroyOnAnimEnd: false, offsetY: 9f, canFlip: true, freeRotate: false);
            PlateShatter = Vis("ModBonePlateShatter", "FxOssBonePlateBreak", "Play", 17, 21);
            HitSplat = GodArt.HitSplat("ModOssHitSplat", "FxOssBoneChips", 16, 12);

            // ---- item templates (ItemPack2 reskins these two)
            Skull = FxKit.Projectile("ModSkullBoomerang", "AxeThrowProjectileBoomerang", "FxSkull", "Fly", 230f, 1.1f, 1f, 0.4f,
                                     rotate: false, destroyOnHit: false);
            if (Skull != null)
            {
                FxFactory.SetDamage(Skull, 1f, rate: 0.35f, knockback: 0.4f, collisionAtStart: true);
                FxFactory.SetMotion(Skull, 230f, accel: -420f);
            }
            SpikeBurst = FxKit.TimedHit("ModOssuarySpikeBurst", "TrollGroundPoundBigShockwave", "FxOssSpikeBurst", "Play", 0, 3,
                                        1.2f, 1.6f, bleed, 0.5f, canFlip: false);
            Strike.Ground(SpikeBurst, "FxOssSpikeBurst", 30, 14, 52f, 21f);

            // ---- Rattlebones: the skull that stays where it lands
            SkullLob = Thrown("ModOssSkullLob", "FxOssSkull", 12, 13, 170f, 0.38f, 0.8f, 0.4f, rotate: false);
            Add<OssSkullLobFx>(SkullLob);
            SkullFloor = Standing("ModOssSkullFloor", "FxOssSkull", "Land", "Chatter", 12, 13);
            SkullChatter = Clip("FxOssSkull", "Chatter", true);
            SkullRoll = Clip("FxOssSkull", "Roll", true);
            RattleSwipe = Melee("ModOssRattleSwipe", 0.6f, 0.4f, 12f, 10f);

            // ---- Marrow Hound
            HoundBite = AimedMelee.Rotating(FxFactory.Clone("DamageGiantRatAttack", "ModHoundBite"));
            FxFactory.SetDamage(HoundBite, 0.6f, knockback: 0.3f, status: bleed, statusChance: 0.25f);
            Strike.HitBox(HoundBite, 10f, 10f);
            HoundHowl = FxKit.TimedHit("ModHoundHowl", "TrollGroundPoundBigShockwave", "FxOssHowl", "Ring", 0, 3, 0.25f, 0.15f, bleed, 1f,
                                       durations: new[] { 0.0667f, 0.0667f, 0.0667f, 0.0667f }, canFlip: false);
            Strike.Ground(HoundHowl, "FxOssHowl", 25, 17, 48f, 22f);
            Scent = Vis("ModOssScent", "FxOssScent", "Drop", 4, 6);

            // ---- Cairn Crow
            CrowPeck = Melee("ModCrowPeck", 0.6f, 0.5f, 10f, 10f, life: 0.3f);
            Splinter = Vis("ModOssSplinter", "FxOssSplinter", "Play", 10, 16);
            Caw = Vis("ModOssCaw", "FxOssCaw", "Ring", 24, 10);

            // ---- Bone Lancer: a long thrust; spears that stand where they miss
            LancerThrust = Melee("ModLancerThrust", 1.1f, 0.8f, 32f, 10f, bleed, 0.3f, life: 0.2f);
            BoneSpear = Thrown("ModBoneSpear", "FxOssSpear", 16, 17, 230f, 0.45f, 0.9f, 0.5f, bleed, 0.3f);
            Add<OssSpearFlightFx>(BoneSpear);
            SpearStand = Vis("ModOssSpearStand", "FxOssSpear", "Stand", 16, 17, loop: true);
            SpearCrumble = Clip("FxOssSpear", "Crumble");

            // ---- Gravedigger: two spade hits bury the hero to the knees
            DigSpade = Melee("ModOssDigSpade", 1.0f, 0.6f, 17f, 11f);
            DigHole = Vis("ModOssDigHole", "FxOssDigHole", "Play", 14, 6);
            Buried = MakeStatus("ModStatusOssBuried", "ModOssBuried", 1.5f, new Color(0.45f, 0.32f, 0.2f, 0.15f),
                                Mul(PlayerModifier.eType.HeroSpeed, 0.6f), Mul(PlayerModifier.eType.MonsterSpeed, 0.6f));
            ModStatus.RegisterOverlay("ModStatusOssBuried", "FxOssDirtLegs", "Loop", -2f, OverlayAt.Feet);

            // ---- Gravetusk: a tusk toss; a charge that bends to a bleeding hero and bursts piles into shards
            TuskGore = Melee("ModOssTuskGore", 1.1f, 1.3f, 16f, 20f);
            TuskRush = Melee("ModOssTuskRush", 1.0f, 1.4f, 23f, 20f, life: 0.55f, rate: 0.4f);
            TuskShard = Thrown("ModOssTuskShard", "FxBoneShard", 5, 5, 170f, 0.35f, 0.5f, 0.3f);
            PileGlow = Vis("ModOssPileGlow", "FxOssPileGlow", "Play", 10, 10);

            // ---- Barghest: bites from behind, a pounce that lands past the hero
            BarghestBite = AimedMelee.Rotating(FxFactory.Clone("DamageGiantRatAttack", "ModOssBarghestBite"));
            FxFactory.SetDamage(BarghestBite, 0.9f, knockback: 0.4f, status: bleed, statusChance: 0.3f);
            Strike.HitBox(BarghestBite, 14f, 17f);
            PounceBite = Melee("ModOssPounceBite", 0.9f, 1.0f, 18f, 17f);
            PounceDust = Vis("ModOssPounceDust", "FxOssPounceDust", "Play", 22, 12);
            EyeFlare = ModStatus.Indicator("ModIndOssEyes", "FxOssEyeFlare", "Loop", 1f, OverlayAt.Head);

            // ---- Ossuary Priest
            MarrowBolt = FxKit.Projectile("ModMarrowBolt", "DFX_PriestessRune", "FxMarrowBolt", "Fly", 60f, 3.2f, 0.9f, 0.5f,
                                          accel: 40f, speedMax: 115f, rotate: true);
            Strike.ArtAt(MarrowBolt, "FxMarrowBolt", 12, 6);

            // ---- Carrion Vulture
            VultureRake = Melee("ModOssVultureRake", 1.0f, 0.6f, 20f, 12f, bleed, RakeBleedChance, life: 0.25f);
            DiveShadow = Vis("ModOssDiveShadow", "FxOssDiveShadow", "Play", 15, 6);
            DiveHit = FxKit.TimedHit("ModOssDiveHit", "TrollGroundPoundBigShockwave", "FxOssDiveImpact", "Play", 0, 2, 1.2f, 1.0f,
                                     durations: new[] { 0.05f, 0.06f, 0.07f, 0.08f, 0.1f }, canFlip: false);
            Strike.Ground(DiveHit, "FxOssDiveImpact", 26, 22, 20f, 10f);
            WatchRing = Vis("ModOssWatchRing", "FxOssWatchRing", "Loop", 17, 7, loop: true);

            // ---- Charnel Rider (mounted and on foot)
            LanceSweep = Melee("ModOssLanceSweep", 1.4f, 1.1f, 36f, 21f);
            JoustTip = Melee("ModOssJoustTip", 1.5f, 1.2f, 17f, 12f, life: 0.5f, rate: 0.5f);
            JoustTrample = Melee("ModOssJoustTrample", 1.0f, 0.8f, 18f, 12f, life: 0.5f, rate: 0.5f);
            LanceThrow = Thrown("ModOssLanceThrow", "FxOssSpear", 16, 17, 220f, 0.5f, 1.2f, 0.8f);
            FootThrustTip = Melee("ModOssFootThrust", 1.2f, 1.0f, 14f, 10f, life: 0.3f, rate: 0.3f);

            // ---- Spinehook: a hook rake; a harpoon that bites the hero or reels a pile in through him
            HookRake = Melee("ModOssHookRake", 1.2f, 0.9f, 28f, 18f, bleed, 0.3f);
            Harpoon = Thrown("ModOssHarpoon", "FxOssHarpoon", 11, 5, 240f, 0.42f, 1.3f, 0.3f, bleed, 1f);
            Add<OssHarpoonFx>(Harpoon);
            RopeSeg = Vis("ModOssRope", "FxOssRope", "Seg", 7, 2, loop: true);

            // ---- Tombwright: headstones that rise as walls and fall like dominoes
            MalletSmash = Melee("ModOssMalletSmash", 1.3f, 1.2f, 24f, 15f);
            StoneRise = FxKit.BodyHit("ModOssStoneRise", 0.8f, 0f, 0.8f, 0.2f);
            Strike.HitBox(StoneRise, 12f, 8f);
            Headstone = Standing("ModOssHeadstone", "FxOssHeadstone", "Rise", "Stand", 30, 28);
            StoneFall = FxKit.BodyHit("ModOssStoneFall", 1.4f, 0f, 1.2f, 0.2f);
            Strike.HitBox(StoneFall, 28f, 10f);
            StoneCrack = Clip("FxOssHeadstone", "Crack"); StoneFallSide = Clip("FxOssHeadstone", "FallSide");
            StoneFallFront = Clip("FxOssHeadstone", "FallFront"); StoneFallBack = Clip("FxOssHeadstone", "FallBack");
            StoneCrumble = Clip("FxOssHeadstone", "Crumble");

            // ---- Coffin Bearer
            CoffinSlam = Melee("ModOssCoffinSlam", 1.4f, 1.4f, 27f, 15f);
            WhirlHit = FxKit.BodyHit("ModOssCoffinWhirl", 1.1f, 0f, 1.1f, 0.15f);
            FlingHit = FxKit.BodyHit("ModOssCoffinFling", 1.5f, 0f, 1.6f, 0.15f);
            Strike.HitBox(FlingHit, 16f, 14f);

            // ---- Bone Mammoth
            MammothTusk = Melee("ModOssMammothTusk", 1.4f, 1.4f, 23f, 26f);
            StepDust = Vis("ModOssStepDust", "FxOssStepDust", "Ring", 20, 8);
            Crack = Vis("ModOssCrack", "FxOssCrack", "Crack", 8, 3);
            CrossSpike = FxKit.TimedHit("ModOssCrossSpike", "TrollGroundPoundBigShockwave", "FxOssCrossSpike", "Play", 1, 3, 1.3f, 0.9f,
                                        durations: new[] { 0.04f, 0.05f, 0.12f, 0.1f, 0.08f }, canFlip: false);
            Strike.Ground(CrossSpike, "FxOssCrossSpike", 9, 15, 12f, 10f);

            // ---- Razorback
            RazorSlash = Melee("ModOssRazorSlash", 1.1f, 0.9f, 20f, 22f, bleed, 0.3f);
            Quill = Thrown("ModOssQuill", "FxOssQuill", 8, 3, 200f, 0.5f, 0.6f, 0.3f);

            // ---- Cerberus: one fan bite; three cones of grave gas that sweep in
            CerberusBite = Melee("ModOssCerberusBite", 1.2f, 0.8f, 25f, 25f);
            GasConeHit = FxKit.BodyHit("ModOssGasCone", 0.4f, 0.3f, 0f, 1.4f, poison, 1f);
            Strike.HitBox(GasConeHit, 36f, 14f, 22f, 0f);
            GasConeArt = Vis("ModOssGasConeArt", "FxOssGasCone", "Loop", 2, 15, loop: true);
            if (GasConeArt != null) FxFactory.SetEffect(GasConeArt, destroyOnAnimEnd: false, destroyAfter: 1.6f, canFlip: false, freeRotate: true);

            // ---- Church Grim
            GrimBite = Melee("ModOssGrimBite", 1.3f, 0.8f, 19f, 18f);
            GrimLunge = Melee("ModOssGrimLunge", 1.4f, 0.6f, 22f, 13f, bleed, 0.4f, life: 0.3f, rate: 0.3f);
            GrimRing = Vis("ModOssGrimRing", "FxOssGrimRing", "Fill", 14, 6);

            // ---- Carrion Saint: its perched crows are its shots
            CrowShot = Thrown("ModOssCrowShot", "FxOssCrow", 8, 7, 140f, 1.2f, 0.9f, 0.4f);
            Add<OssCrowSeekFx>(CrowShot);
            CrowWall = Thrown("ModOssCrowWall", "FxOssCrow", 8, 7, 160f, 0.5f, 0.7f, 0.4f);

            // ---- The Ossuary
            OssuarySlam = FxKit.TimedHit("ModOssuarySlam", "TrollGroundPoundBigShockwave", "FxSpikeRing", "Play", 0, 3, 1.3f, 1.4f,
                                         colliderScale: 0.6f, canFlip: false);
            Strike.Ground(OssuarySlam, "FxSpikeRing", 26, 13, 40f, 16f);
            RibCrack = Vis("ModOssRibCrack", "FxOssRibCrack", "Play", 26, 18);
            Rib = Standing("ModOssRib", "FxOssRib", "Rise", "Stand", 11, 19);
            RibRise = Clip("FxOssRib", "Rise"); RibRiseL = Clip("FxOssRib", "RiseL");
            RibStand = Clip("FxOssRib", "Stand", true); RibStandL = Clip("FxOssRib", "StandL", true);
            RibBreak = Clip("FxOssRib", "Break"); RibBreakL = Clip("FxOssRib", "BreakL");

            // ---- Marrow Wyrm
            WyrmBite = Melee("ModOssWyrmBite", 1.3f, 0.9f, 14f, 14f, bleed, 0.4f);
            WyrmLash = Melee("ModOssWyrmLash", 1.5f, 1.3f, 35f, 60f, life: 0.12f);
            MarrowLine = Vis("ModOssMarrowLine", "FxOssMarrowLine", "Seg", 7, 2, loop: true);

            // ---- Carrion Roc
            RocStab = Melee("ModOssRocStab", 1.3f, 0.7f, 22f, 14f, bleed, 0.3f, life: 0.25f);
            RocDrop = FxKit.TimedHit("ModOssRocDrop", "TrollGroundPoundBigShockwave", "FxOssDiveImpact", "Play", 0, 2, 1.0f, 1.0f,
                                     durations: new[] { 0.05f, 0.06f, 0.07f, 0.08f, 0.1f }, canFlip: false);
            Strike.Ground(RocDrop, "FxOssDiveImpact", 26, 22, 18f, 10f);
            DropShadow = Vis("ModOssDropShadow", "FxOssDropShadow", "Loop", 11, 5, loop: true);

            RatBite = AimedMelee.Rotating(FxFactory.Clone("DamageGiantRatAttack", "ModBoneRatBite"));
            FxFactory.SetDamage(RatBite, 0.5f, knockback: 0.2f);
            Strike.HitBox(RatBite, 9f, 9f);
            Plugin.Log.LogInfo("Ossivar FX templates built");
        }

        static Status MakeStatus(string name, string cls, float duration, Color tint, params PlayerModifier[] mods)
        {
            var src = ModStatus.Slow;      // the mod's timed status: no anims, no damage, never blocks attacks
            if (src == null) return null;
            var go = MonsterFactory.ClonePrefab(src.gameObject, name);
            var s = go.GetComponent<Status>();
            s.m_class = cls;
            s.m_duration = duration;
            s.m_stacks = true;
            s.m_damage = 0f;
            s.m_preventAttack = false;
            s.m_preventMove = false;
            s.m_modifiers = new System.Collections.Generic.List<PlayerModifier>(mods);
            s.m_tintColour = tint;
            s.m_tintFlashTime = 0f;
            s.m_effects = new DamageEffectData[0];
            return s;
        }

        static PlayerModifier Mul(PlayerModifier.eType t, float v)
        {
            return new PlayerModifier { m_modify = t, m_type = ValueModifier.eModifierType.Multiply, m_value = v, m_priority = 500f };
        }
    }
}
