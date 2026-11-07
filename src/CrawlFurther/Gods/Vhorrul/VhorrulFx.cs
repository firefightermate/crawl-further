using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    using CrawlFurther.Art;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Vhorrul's effect templates. The floor has three states the monsters play with: wax (<see cref="WaxPuddle"/>, slows
    /// the hero, heals the tallow monsters), lit wax (<see cref="BurningPool"/>) and flames (anything with an
    /// <see cref="IgniterFx"/>: pools, pyres, bolts, moths). Fire that touches wax lights it. Sheets and origins:
    /// tools/sprites/vhorrul_v2_fx.py and art/out/TIMING.md.
    /// </summary>
    public static class VhorrulFx
    {
        /// <summary>The floor: unlit wax, lit wax, a line of touch-paper wax, the flame racing along it.</summary>
        public static GameObject WaxPuddle, BurningPool, WaxLine, LineFlare;
        /// <summary>The god perk: a dead monster's pyre and the tallow slick it cools into.</summary>
        public static GameObject Pyre, PyreWax;
        /// <summary>Kept for the shop items built on them (Tallow Trail, Ember Volley, Soul Lantern).</summary>
        public static GameObject WickTrail, CandleBolt, LanternOrb, LanternBlast;
        /// <summary>Wax chips instead of red blood when a Vhorrul monster is hit.</summary>
        public static GameObject HitSplat;

        public static GameObject WaxGlob, MoltenGlob, WickBite, WickDashHit, WickDashTrail, Flare, Upwell, AshPuff, EmberPuff, MothDive,
                                 KnightCut, KnightCut3, SealRing, LitRing, KindledSpill, WormBite, WaxRoad, SowDrop, EggGlob, WaxEgg,
                                 EggHatch, Glance, MatronRake, EmberMoth, CandelabraFlame, Fork, ColossusFist, ToppleShadow, CenserSmash,
                                 SigilFlame, LadleFan, BoilWave, LadleSwing, HexFlame, Poppet, Thread, WyrmStrike, CoilFlame, CoilClose,
                                 ScorpSnap, FuseSpark, FuseSmoke, FuseBlast, MotherSlam, Grubling, GrubPop, GrubPopLit, GrubBrood,
                                 TickBite, TickDrop, SeraphLance, Smother, AshCloud, SoulCone, WheelFire, Drip, RingFlare, VotiveFlame;
        /// <summary>Tallow Colossus Topple, one hitbox per wax layer (0-3): the body lands further out with each.</summary>
        public static GameObject[] ToppleHit = new GameObject[0];
        /// <summary>Pyre Warden Stoke: the three rings of fire spreading out (radius 12, 24, 36).</summary>
        public static GameObject[] StokeRing = new GameObject[0];
        /// <summary>Clips the effects switch between at run time.</summary>
        public static exSpriteAnimClip MothHunt, CoilWhite, PoppetFlinch, PoppetMelt, GrubLit;
        public static exSpriteAnimClip[] ShadowLengths = new exSpriteAnimClip[0];

        /// <summary>Kindled (the Waxen Knight wears fire), Prone (the toppled Colossus), Fever and Soulless (on the hero).</summary>
        public static Status Kindled, Prone, Fever, Soulless;
        public static Status OnFire, Slow, Daze;

        public const float PyreFlameRadius = 15f, PyreWaxRadius = 13f;

        public static void Build()
        {
            OnFire = FxFactory.GetStatus("StatusOnFire");
            Slow = FxFactory.GetStatus("StatusLavaSteveGoo");
            Daze = FxFactory.GetStatus("StatusDizzy");
            BuildStatuses();
            BuildFloor();
            BuildTier1();
            BuildTier2();
            BuildTier3a();
            BuildTier3b();
            HitSplat = GodArt.HitSplat("ModVhHitSplat", "FxVhWaxSplat", 13, 6);
            Plugin.Log.LogInfo("Vhorrul FX templates built");
        }

        // ------------------------------------------------------------------------------------------------ helpers
        static void Hook(GameObject tmpl, Action<GameObject> act)
        {
            if (tmpl == null) return;
            Action<GameObject> prev;
            FxFactory.OnSpawn.TryGetValue(tmpl, out prev);
            FxFactory.OnSpawn[tmpl] = i => { if (prev != null) prev(i); act(i); };
        }

        static T Add<T>(GameObject i) where T : Component { return i.GetComponent<T>() ?? i.AddComponent<T>(); }

        /// <summary>An invisible melee hitbox, turned with the aim when <paramref name="aimed"/>.</summary>
        static GameObject Hit(string name, float dmg, float knock, float w, float h, float life = 0.15f, Status st = null, float chance = 0f,
                              bool aimed = true, float rate = 0.3f)
        {
            var go = FxKit.BodyHit(name, dmg, rate, knock, life, st, chance);
            if (aimed) go = AimedMelee.Rotating(go);
            Strike.HitBox(go, w, h);
            return go;
        }

        /// <summary>A wax-like floor zone: slows the hero and catches fire (its <see cref="WaxPuddleFx"/>).</summary>
        static GameObject WaxZone(string name, string sheet, string anim, int gx, int gy, float w, float h, float radius, bool line)
        {
            var sh = SpriteSheets.Get(sheet);
            var go = FxFactory.Clone("LavaEffectLongerReworkZone", name);
            if (go == null || sh == null) return go;
            var clip = new ClipBuilder(sh, anim, name + "Life").Once().Ev(1, "AnimDamageOn").Ev(-2, "AnimDamageOff").Build();
            FxFactory.Reskin(go, clip, sh);
            FxFactory.SetEffect(go, destroyOnAnimEnd: true, offsetX: 0f, snap: 1f);
            FxFactory.SetStatusZone(go, Slow, hitsHero: true, hitsMonster: false);
            FxKit.NoTint(go);
            Hook(go, i => { var wp = Add<WaxPuddleFx>(i); wp.radius = radius; wp.line = line; });
            Strike.Ground(go, sheet, gx, gy, w, h);
            return go;
        }

        static GameObject Flame(GameObject go, float radius = 10f)
        {
            if (go != null) Hook(go, i => { var f = Add<IgniterFx>(i); f.radius = radius; });
            return go;
        }

        static Status MakeStatus(string name, string cls, float duration, Color tint, params PlayerModifier[] mods)
        {
            var src = ModStatus.Slow;
            if (src == null) return null;
            var go = MonsterFactory.ClonePrefab(src.gameObject, name);
            var s = go.GetComponent<Status>();
            s.m_class = cls;
            s.m_duration = duration;
            s.m_stacks = true;
            s.m_damage = 0f;
            s.m_preventAttack = false;
            s.m_preventMove = false;
            s.m_modifiers = new List<PlayerModifier>(mods);
            s.m_tintColour = tint;
            s.m_tintFlashTime = 0f;
            s.m_effects = new DamageEffectData[0];
            return s;
        }

        static PlayerModifier Mul(PlayerModifier.eType t, float v)
        {
            return new PlayerModifier { m_modify = t, m_type = ValueModifier.eModifierType.Multiply, m_value = v, m_priority = 500f };
        }

        // ------------------------------------------------------------------------------------------------ statuses
        static void BuildStatuses()
        {
            // resistance 0.8: 25 % more damage taken
            Kindled = MakeStatus("ModStatusVhKindled", "ModVhKindled", 5f, new Color(1f, 0.55f, 0.15f, 0.12f),
                                 Mul(PlayerModifier.eType.MonsterDamageResistance, 0.8f));
            Prone = MakeStatus("ModStatusVhProne", "ModVhProne", 1.1f, new Color(0f, 0f, 0f, 0f),
                               Mul(PlayerModifier.eType.MonsterDamageResistance, 0.8f));
            Fever = MakeStatus("ModStatusVhFever", "ModVhFever", 4f, new Color(1f, 0.25f, 0.2f, 0.18f));
            Soulless = MakeStatus("ModStatusVhSoulless", "ModVhSoulless", 4f, new Color(0f, 0f, 0f, 0.15f),
                                  Mul(PlayerModifier.eType.HeroDamage, 0.75f));
            ModStatus.RegisterOverlay("ModStatusVhKindled", "FxVhKindled", "Loop", -2f, OverlayAt.Feet);
            ModStatus.RegisterOverlay("ModStatusVhFever", "FxVhFever", "Loop", -2f, OverlayAt.Feet);
            ModStatus.RegisterOverlay("ModStatusVhSoulless", "FxVhSoulless", "Loop", 1f, OverlayAt.Head);
        }

        // ------------------------------------------------------------------------------------------------ the floor and the perk
        static void BuildFloor()
        {
            WaxPuddle = WaxZone("ModWaxPuddle", "FxWaxPuddle", "Life", 13, 6, 22f, 8f, 11f, false);
            {
                var sh = SpriteSheets.Get("FxEmberPatch");
                var go = FxFactory.Clone("SkMageSlimeEffect", "ModBurningPool");
                var clip = new ClipBuilder(sh, "Loop", "ModBurningPoolLife").Repeat(7).Once()
                    .Ev(0, "AnimDamageOn").Ev(-3, "AnimDamageOff").Build();   // 2.8 s of lit wax
                FxFactory.Reskin(go, clip, sh);
                FxFactory.SetEffect(go, destroyOnAnimEnd: true, offsetX: 0f, snap: 1f);
                FxFactory.SetDamage(go, 0.5f, rate: 0.6f, knockback: 0.03f, status: OnFire, statusChance: 0.15f, collisionAtStart: false);
                FxKit.NoTint(go);
                Flame(go);
                Strike.Ground(go, "FxEmberPatch", 12, 12, 20f, 7f);
                BurningPool = go;
            }
            WaxLine = WaxZone("ModVhWaxLine", "FxVhWaxLine", "Life", 8, 4, 12f, 5f, 6f, true);
            LineFlare = FxKit.TimedHit("ModVhLineFlare", "TrollGroundPoundBigShockwave", "FxVhLineFlare", "Play", 1, 3, 0.8f, 0.4f, OnFire, 0.3f,
                                       canFlip: false);
            if (LineFlare != null)
            {
                FxFactory.SetEffect(LineFlare, destroyOnAnimEnd: true, spawnOnDestroy: BurningPool, canFlip: false, freeRotate: false);
                Strike.Ground(LineFlare, "FxVhLineFlare", 8, 16, 12f, 6f);
            }
            // the shop's Tallow Trail copies this dropper: it keeps its own spacing and life
            WickTrail = FxFactory.Clone("WebDropper", "ModWickTrail");
            FxFactory.SetEffect(WickTrail, destroyOnAnimEnd: false, destroyAfter: 1.2f);
            FxFactory.SetMotion(WickTrail, speed: 0f, trail: BurningPool, trailDist: 9f);
            {
                var sh = SpriteSheets.Get("FxVhPyreWax");
                var go = FxFactory.Clone("LavaEffectLongerReworkZone", "ModVhPyreWax");
                if (go != null && sh != null)
                {
                    var clip = new ClipBuilder(sh, "Set", "ModVhPyreWaxLife").Once().Then("Idle", 9).Then("Fade")
                        .Ev(1, "AnimDamageOn").Ev(-2, "AnimDamageOff").Build();   // a slow zone for about 7.5 s
                    FxFactory.Reskin(go, clip, sh);
                    FxFactory.SetEffect(go, destroyOnAnimEnd: true, offsetX: 0f, snap: 1f);
                    FxFactory.SetStatusZone(go, Slow, hitsHero: true, hitsMonster: false);
                    FxKit.NoTint(go);
                    Hook(go, i => { Add<WaxPuddleFx>(i).radius = PyreWaxRadius; });
                    Strike.Ground(go, "FxVhPyreWax", 15, 6, 26f, 8f);
                    PyreWax = go;
                }
            }
            {
                var sh = SpriteSheets.Get("FxVhPyre");
                var go = FxFactory.Clone("SkMageSlimeEffect", "ModVhPyre");
                if (go != null && sh != null)
                {
                    // Ignite 0.24 + Burn 0.54 x 9 + Gutter 0.46 = 5.6 s. It burns from the first Burn frame, so a killer
                    // standing on the body has the flare-up to step off; a Pyre Warden nearby keeps it in the Burn loop.
                    var clip = new ClipBuilder(sh, "Ignite", "ModVhPyreLife").Once().Then("Burn", 9).Then("Gutter")
                        .Ev(2, "AnimDamageOn").Ev(-3, "AnimDamageOff").Build();
                    FxFactory.Reskin(go, clip, sh);
                    FxFactory.SetEffect(go, destroyOnAnimEnd: true, offsetX: 0f, snap: 1f, spawnOnDestroy: PyreWax);
                    FxFactory.SetDamage(go, 0.5f, rate: 0.6f, knockback: 0.03f, status: OnFire, statusChance: 0.15f, collisionAtStart: false);
                    FxKit.NoTint(go);
                    Flame(go, PyreFlameRadius);
                    Hook(go, i => Add<VhPyreFx>(i).Restart());
                    Strike.Ground(go, "FxVhPyre", 17, 22, 28f, 9f);
                    Pyre = go;
                }
            }
            SigilFlame = FxKit.Visual("ModVhSigilFlame", "FxVhSigilFlame", "Loop", loop: true);
            if (SigilFlame != null)
            {
                FxFactory.SetEffect(SigilFlame, destroyOnAnimEnd: false, canFlip: false, freeRotate: false);
                Strike.ArtAt(SigilFlame, "FxVhSigilFlame", 5, 13);
            }
        }

        // ------------------------------------------------------------------------------------------------ tier 1
        static void BuildTier1()
        {
            // Wax Spit and the floor glob: the kit launches it along the floor, the art rides 8 px up
            WaxGlob = FxFactory.Clone("webBall", "ModWaxGlob");
            {
                var sh = SpriteSheets.Get("FxWaxGlob");
                FxFactory.Reskin(WaxGlob, new ClipBuilder(sh, "Fly", "ModWaxGlobFly").Repeat(3).Once().Build(), sh);
                FxFactory.SetEffect(WaxGlob, destroyOnAnimEnd: true, spawnOnDestroy: WaxPuddle);
                FxFactory.SetMotion(WaxGlob, speed: 175f, accel: 20f, speedMax: 8f, collide: true, bounce: 0.2f);
                FxFactory.SetDamage(WaxGlob, 0.6f, knockback: 0.2f, collisionAtStart: true);
                FxFactory.SetContacts(WaxGlob, destroyOnHit: true, spawnOnHit: WaxPuddle);
                Strike.ArtAt(WaxGlob, "FxWaxGlob", 6, 12);
            }
            // Wickling
            WickBite = Hit("ModVhWickBite", 0.8f, 0.5f, 12f, 11f, 0.15f, OnFire, 0.35f);
            WickDashHit = Hit("ModWickDashHit", 0.7f, 0.8f, 13f, 11f, 0.5f, OnFire, 0.2f, rate: 0.4f);
            WickDashTrail = FxFactory.Clone("WebDropper", "ModVhWickDashTrail");
            FxFactory.SetEffect(WickDashTrail, destroyOnAnimEnd: false, destroyAfter: 0.22f);
            FxFactory.SetMotion(WickDashTrail, speed: 0f, trail: BurningPool, trailDist: 19f);
            Flare = FxKit.Visual("ModVhFlare", "FxVhFlare", "Play");
            if (Flare != null) Strike.ArtAt(Flare, "FxVhFlare", 10, 14);
            // Tallow Grub: bursting up through its own puddle
            Upwell = Hit("ModVhUpwell", 0.8f, 0.9f, 24f, 12f, 0.12f, aimed: false);
            // Ash Moth: the ash puff (dazes), the same puff carrying embers (lights wax) near fire, the dive
            AshPuff = FxFactory.Clone("DFX_skelMageNewProjectile", "ModAshPuff");
            EmberPuff = FxFactory.Clone("DFX_skelMageNewProjectile", "ModVhEmberPuff");
            foreach (var go in new[] { AshPuff, EmberPuff })
            {
                var sh = SpriteSheets.Get("FxAshCloud");
                FxFactory.Reskin(go, new ClipBuilder(sh, "Puff", go.name + "Drift").Once().Build(), sh);
                FxFactory.SetEffect(go, destroyOnAnimEnd: true, freeRotate: false);
                foreach (var m in go.GetComponents<ParticleMotion>()) R.Set(m, "m_trailObject", null);
                FxFactory.SetMotion(go, 160f, accel: 150f, speedMax: 18f);
                Strike.Collider(go, 14f, 12f);
                FxFactory.SetDamage(go, 0.5f, rate: 0.5f, knockback: 0.1f, status: Daze, statusChance: 0.5f, collisionAtStart: true);
                FxFactory.SetContacts(go, destroyOnHit: false, clearSpawnOnHit: true);
                FxKit.NoTint(go);
            }
            Flame(EmberPuff, 9f);
            MothDive = Hit("ModMothDiveHit", 1f, 0.6f, 13f, 10f, 0.45f, OnFire, 0.4f, rate: 0.45f);
        }

        // ------------------------------------------------------------------------------------------------ tier 2
        static void BuildTier2()
        {
            // Waxen Knight: three cuts (they burn while it is Kindled), the spill, the Seal ring (lit when Kindled)
            KnightCut = Hit("ModVhKnightCut", 0.9f, 0.6f, 18f, 14f);
            KnightCut3 = Hit("ModVhKnightCut3", 1.1f, 1.2f, 20f, 16f);
            KindledSpill = BurningPool;
            SealRing = FxKit.TimedHit("ModWaxShockwave", "TrollGroundPoundBigShockwave", "FxWaxShockwave", "Ring", 0, 3, 0.75f, 1.2f, Slow, 1f,
                                      canFlip: false);
            Strike.Ground(SealRing, "FxWaxShockwave", 28, 13, 56f, 22f);
            LitRing = FxKit.TimedHit("ModVhLitRing", "TrollGroundPoundBigShockwave", "FxWaxShockwave", "Lit", 0, 3, 0.9f, 1.2f, OnFire, 1f,
                                     canFlip: false);
            Strike.Ground(LitRing, "FxWaxShockwave", 28, 13, 56f, 22f);
            Flame(LitRing, 26f);
            // Chandler: the burning glob (lands as lit wax); the line uses WaxLine / LineFlare
            MoltenGlob = FxFactory.Clone("webBall", "ModMoltenGlob");
            {
                var sh = SpriteSheets.Get("FxVhMoltenGlob");
                FxFactory.Reskin(MoltenGlob, new ClipBuilder(sh, "Fly", "ModMoltenGlobFly").Repeat(3).Once().Build(), sh);
                FxFactory.SetEffect(MoltenGlob, destroyOnAnimEnd: true, spawnOnDestroy: BurningPool);
                FxFactory.SetMotion(MoltenGlob, speed: 160f, accel: 20f, speedMax: 8f, collide: true, bounce: 0.2f);
                FxFactory.SetDamage(MoltenGlob, 0.9f, knockback: 0.3f, status: OnFire, statusChance: 0.3f, collisionAtStart: true);
                FxFactory.SetContacts(MoltenGlob, destroyOnHit: true, spawnOnHit: BurningPool);
                FxKit.NoTint(MoltenGlob);
                Strike.ArtAt(MoltenGlob, "FxVhMoltenGlob", 7, 19);
                Flame(MoltenGlob, 6f);
            }
            // Wickworm: the snap, the dropper that lays its wax road
            WormBite = Hit("ModVhWormBite", 1.0f, 0.5f, 14f, 12f);
            WaxRoad = FxFactory.Clone("WebDropper", "ModVhWaxRoad");
            FxFactory.SetEffect(WaxRoad, destroyOnAnimEnd: false, destroyAfter: 2f);
            FxFactory.SetMotion(WaxRoad, speed: 0f, trail: WaxPuddle, trailDist: 14f);
            // Tallow Sow: drops of hot fat (slow), eggs that hatch a glob at the hero and crack into wax, the glance spark
            SowDrop = FxKit.Projectile("ModVhSowDrop", "DFX_skelMageNewProjectile", "FxVhSowDrop", "Fly", 150f, 0.55f, 0.8f, 0.3f, Slow, 0.4f);
            Strike.ArtAt(SowDrop, "FxVhSowDrop", 5, 4);
            EggGlob = FxKit.Projectile("ModVhEggGlob", "DFX_skelMageNewProjectile", "FxVhSowDrop", "Fly", 160f, 0.8f, 0.8f, 0.3f);
            Strike.ArtAt(EggGlob, "FxVhSowDrop", 5, 4);
            EggHatch = FxKit.Inert("ModVhEggHatch", null, null, destroyOnAnimEnd: false, life: 0.3f);
            Hook(EggHatch, i => { var a = Add<VhAimShotFx>(i); a.projectile = EggGlob; a.lift = 4f; a.leave = WaxPuddle; a.Restart(); });
            WaxEgg = FxKit.Inert("ModVhWaxEgg", "FxVhWaxEgg", "Life", destroyOnAnimEnd: true, spawnOnDestroy: EggHatch);
            Strike.ArtAt(WaxEgg, "FxVhWaxEgg", 5, 10);
            Glance = FxKit.Visual("ModVhGlance", "FxVhGlance", "Play");
            // Moth Matron: the rake, and ember moths that hunt a burning hero (else drift and light wax)
            MatronRake = Hit("ModVhMatronRake", 0.9f, 0.6f, 16f, 14f);
            EmberMoth = FxKit.Projectile("ModVhEmberMoth", "DFX_PriestessRune", "FxVhEmberMoth", "Drift", 0f, 3.2f, 0.75f, 0.3f, OnFire, 0.3f,
                                         rotate: false);
            if (EmberMoth != null)
            {
                Strike.ArtAt(EmberMoth, "FxVhEmberMoth", 5, 4);
                var sh = SpriteSheets.Get("FxVhEmberMoth");
                MothHunt = new ClipBuilder(sh, "Hunt", "ModVhEmberMothHunt").Loop().Build();
                Flame(EmberMoth, 6f);
                Hook(EmberMoth, i => Add<VhMothFx>(i).Restart());
            }
            // Candelabra: candle flames that fork in two over wax
            CandleBolt = FxKit.Projectile("ModCandleBolt", "DFX_skelMageNewProjectile", "FxCandleBolt", "Fly", 150f, 1.5f, 0.8f, 0.5f, OnFire, 0.2f);
            Strike.ArtAt(CandleBolt, "FxCandleBolt", 12, 5);
            Flame(CandleBolt, 6f);
            CandelabraFlame = FxKit.Projectile("ModVhCandelabraFlame", "DFX_skelMageNewProjectile", "FxCandleBolt", "Fly", 150f, 1.5f, 0.8f, 0.5f,
                                               OnFire, 0.2f);
            Strike.ArtAt(CandelabraFlame, "FxCandleBolt", 12, 5);
            Flame(CandelabraFlame, 6f);
            Hook(CandelabraFlame, i => Add<VhForkFx>(i).Restart());
            Fork = FxKit.Visual("ModVhFork", "FxVhFork", "Play");
            if (Fork != null) { FxFactory.SetEffect(Fork, destroyOnAnimEnd: true, freeRotate: true); Strike.ArtAt(Fork, "FxVhFork", 4, 7); }
        }

        // ------------------------------------------------------------------------------------------------ tier 3, first half
        static void BuildTier3a()
        {
            // Tallow Colossus: the fists, the Topple shadow (one length per layer) and its landing
            ColossusFist = Hit("ModVhColossusFist", 1.3f, 1.4f, 22f, 20f);
            ToppleShadow = FxKit.Visual("ModVhToppleShadow", "FxVhToppleShadow", "S0", lifetime: 0.85f);
            if (ToppleShadow != null)
            {
                FxFactory.SetEffect(ToppleShadow, destroyOnAnimEnd: false, destroyAfter: 0.85f, canFlip: true, freeRotate: true);
                Strike.ArtAt(ToppleShadow, "FxVhToppleShadow", 2, 5);
                var sh = SpriteSheets.Get("FxVhToppleShadow");
                var names = new[] { "S0", "S1", "S2", "S3" };
                ShadowLengths = new exSpriteAnimClip[names.Length];
                for (int i = 0; i < names.Length; i++) ShadowLengths[i] = new ClipBuilder(sh, names[i], "ModVhTopple" + names[i]).Loop().Build();
            }
            ToppleHit = new GameObject[4];
            for (int i = 0; i < 4; i++)
                ToppleHit[i] = Hit("ModVhTopple" + i, 1.6f, 2.4f, 28f + 10f * i, 16f, 0.12f);
            // Pyre Warden: the censer's ember ring (lights wax), Stoke's three spreading rings
            CenserSmash = FxKit.TimedHit("ModVhCenserSmash", "TrollGroundPoundBigShockwave", "FxVhStokeRing", "R1", 0, 2, 1.2f, 1.0f, OnFire, 0.3f,
                                         canFlip: false);
            Strike.Ground(CenserSmash, "FxVhStokeRing", 40, 20, 26f, 10f);
            Flame(CenserSmash, 14f);
            StokeRing = new GameObject[3];
            for (int i = 0; i < 3; i++)
            {
                float r = 12f * (i + 1);
                var go = FxKit.TimedHit("ModVhStokeRing" + (i + 1), "TrollGroundPoundBigShockwave", "FxVhStokeRing", "R" + (i + 1), 0, 2, 1.0f, 0.8f,
                                        OnFire, 0.4f, canFlip: false);
                Strike.Ground(go, "FxVhStokeRing", 40, 20, r * 2f, r * 0.8f);
                StokeRing[i] = Flame(go, r);
            }
            // Tallow Renderer: the ladle's fan of boiling tallow, the wave it rides (pushes, leaves a wax sheet), the swing
            LadleFan = Hit("ModVhLadleFan", 1.1f, 0.8f, 28f, 22f, 0.15f, Slow, 0.6f);
            LadleSwing = Hit("ModVhLadleSwing", 1.0f, 1.0f, 30f, 22f);
            BoilWave = FxKit.Projectile("ModVhBoilWave", "DFX_skelMageNewProjectile", "FxVhBoilWave", "Roll", 115f, 0.62f, 1.3f, 2.2f,
                                        destroyOnHit: false);
            if (BoilWave != null)
            {
                FxFactory.SetDamage(BoilWave, 1.3f, rate: 1f, knockback: 2.2f, collisionAtStart: true);
                FxFactory.SetMotion(BoilWave, 115f, trail: WaxPuddle, trailDist: 16f, collide: false);
                Strike.Collider(BoilWave, 12f, 40f);
                Strike.ArtAt(BoilWave, "FxVhBoilWave", 10, 24);
            }
            // Wick Hag: the hex flame (lights wax), the poppet and the red thread to the hero
            HexFlame = FxKit.Projectile("ModVhHexFlame", "DFX_skelMageNewProjectile", "FxVhHexFlame", "Fly", 170f, 0.9f, 1.0f, 0.4f, OnFire, 0.3f);
            Strike.ArtAt(HexFlame, "FxVhHexFlame", 12, 5);
            Flame(HexFlame, 6f);
            Poppet = FxKit.Inert("ModVhPoppet", "FxVhPoppet", "Sit", destroyOnAnimEnd: false, life: 0f, thenAnim: "Sit", thenRepeat: 60);
            if (Poppet != null)
            {
                Strike.ArtAt(Poppet, "FxVhPoppet", 5, 12);
                var sh = SpriteSheets.Get("FxVhPoppet");
                PoppetFlinch = new ClipBuilder(sh, "Flinch", "ModVhPoppetFlinch").Once().Then("Sit", 40).Build();
                PoppetMelt = new ClipBuilder(sh, "Melt", "ModVhPoppetMelt").Once().Build();
                Hook(Poppet, i => Add<VhPoppetFx>(i).Restart());
            }
            Thread = FxKit.Visual("ModVhThread", "FxVhThread", "Loop", loop: true);
            if (Thread != null) { FxFactory.SetEffect(Thread, destroyOnAnimEnd: false, canFlip: false, freeRotate: false); Strike.ArtAt(Thread, "FxVhThread", 1, 2); }
            // Candle Wyrm: the strike, the lit coil it lays, and the same flames closing in
            WyrmStrike = Hit("ModVhWyrmStrike", 1.3f, 0.8f, 18f, 16f, 0.15f, OnFire, 0.2f);
            CoilFlame = FxKit.TimedHit("ModVhCoilFlame", "SkMageSlimeEffect", "FxVhCoil", "Burn", 0, 3, 0.5f, 0.05f, OnFire, 0.15f, rate: 0.6f,
                                       canFlip: false);
            if (CoilFlame != null)
            {
                var sh = SpriteSheets.Get("FxVhCoil");
                FxFactory.Reskin(CoilFlame, new ClipBuilder(sh, "Burn", "ModVhCoilBurn").Loop().Ev(0, "AnimDamageOn").Build(), sh);
                FxFactory.SetEffect(CoilFlame, destroyOnAnimEnd: false, destroyAfter: 3.2f, canFlip: false, freeRotate: false);
                Strike.Ground(CoilFlame, "FxVhCoil", 5, 11, 8f, 6f);
                CoilWhite = new ClipBuilder(sh, "White", "ModVhCoilWhite").Loop().Build();
                Flame(CoilFlame, 6f);
                Hook(CoilFlame, i => Add<VhCoilFx>(i).Restart());
            }
            CoilClose = Hit("ModVhCoilClose", 1.5f, 1.0f, 12f, 10f, 0.65f, OnFire, 0.5f, aimed: false, rate: 2f);
            // Fuse Scorpion: the snap, the spark that runs the hero's footsteps, its smoke and the blast
            ScorpSnap = Hit("ModVhScorpSnap", 1.2f, 0.8f, 22f, 18f);
            FuseSpark = FxKit.Inert("ModVhFuseSpark", "FxVhFuseSpark", "Fizz", destroyOnAnimEnd: false, life: 0f, thenAnim: "Fizz", thenRepeat: 40);
            if (FuseSpark != null)
            {
                Strike.ArtAt(FuseSpark, "FxVhFuseSpark", 6, 9);
                Hook(FuseSpark, i => Add<VhFuseSparkFx>(i).Restart());
            }
            FuseSmoke = FxKit.Visual("ModVhFuseSmoke", "FxVhFuseSmoke", "Puff");
            if (FuseSmoke != null) Strike.ArtAt(FuseSmoke, "FxVhFuseSmoke", 3, 8);
            FuseBlast = FxKit.TimedHit("ModVhFuseBlast", "TrollGroundPoundBigShockwave", "FxVhFuseBlast", "Blast", 1, 4, 1.5f, 1.6f, OnFire, 0.5f,
                                       canFlip: false);
            Strike.Ground(FuseBlast, "FxVhFuseBlast", 15, 16, 24f, 12f);
            Flame(FuseBlast, 12f);
        }

        // ------------------------------------------------------------------------------------------------ tier 3, second half
        static void BuildTier3b()
        {
            // Grub Mother: the head slam, grublings that crawl at the hero (lit by fire they crawl through)
            MotherSlam = Hit("ModVhBroodSlam", 1.3f, 1.4f, 22f, 16f);
            GrubPop = FxKit.TimedHit("ModVhGrubPop", "TrollGroundPoundBigShockwave", "FxVhGrubPop", "Pop", 0, 2, 0.6f, 0.5f, Slow, 0.6f, canFlip: false);
            if (GrubPop != null)
            {
                FxFactory.SetEffect(GrubPop, destroyOnAnimEnd: true, spawnOnDestroy: WaxPuddle, canFlip: false, freeRotate: false);
                Strike.Ground(GrubPop, "FxVhGrubPop", 13, 4, 16f, 8f);
            }
            GrubPopLit = FxKit.TimedHit("ModVhGrubPopLit", "TrollGroundPoundBigShockwave", "FxVhLineFlare", "Play", 1, 3, 0.9f, 0.5f, OnFire, 0.6f,
                                        canFlip: false);
            if (GrubPopLit != null)
            {
                FxFactory.SetEffect(GrubPopLit, destroyOnAnimEnd: true, spawnOnDestroy: BurningPool, canFlip: false, freeRotate: false);
                Strike.Ground(GrubPopLit, "FxVhLineFlare", 8, 16, 16f, 8f);
            }
            Grubling = FxKit.Inert("ModVhGrubling", "FxVhGrubling", "Crawl", destroyOnAnimEnd: false, life: 0f, thenAnim: "Crawl", thenRepeat: 40);
            if (Grubling != null)
            {
                Strike.ArtAt(Grubling, "FxVhGrubling", 6, 7);
                GrubLit = new ClipBuilder(SpriteSheets.Get("FxVhGrubling"), "CrawlLit", "ModVhGrublingLit").Loop().Build();
                Hook(Grubling, i => Add<VhCrawlFx>(i).Restart());
            }
            GrubBrood = FxKit.Inert("ModVhGrubBrood", null, null, destroyOnAnimEnd: false, life: 0.2f);
            Hook(GrubBrood, i => Add<VhBroodFx>(i).Restart());
            // Pyre Tick: the bite (gives the hero a fever), drops of burning blood that land as fire
            TickBite = Hit("ModVhTickBite", 1.1f, 0.6f, 20f, 18f, 0.15f, Fever, 1f);
            TickDrop = FxKit.Projectile("ModVhTickDrop", "webBall", "FxVhSowDrop", "Fly", 140f, 0.45f, 0.6f, 0.3f, OnFire, 0.3f);
            if (TickDrop != null)
            {
                FxFactory.SetEffect(TickDrop, destroyOnAnimEnd: false, destroyAfter: 0.45f, spawnOnDestroy: BurningPool, freeRotate: true);
                FxFactory.SetContacts(TickDrop, destroyOnHit: true, spawnOnHit: BurningPool);
                Strike.ArtAt(TickDrop, "FxVhSowDrop", 5, 4 + 13);   // flies along the floor, drawn at the jaws
            }
            // Ashen Seraph: the lance, the smoke off a fire it beats out, the ash cloud that chases the hero
            SeraphLance = Hit("ModSeraphLance", 1.3f, 1.0f, 38f, 12f, 0.2f);
            Smother = FxKit.Visual("ModVhSmother", "FxVhSmother", "Rise");
            if (Smother != null) Strike.ArtAt(Smother, "FxVhSmother", 10, 38);
            AshCloud = FxKit.Cloud("ModVhAshCloud", "FxVhAshCloud", "Drift", 0f, 0.6f, 1f, Daze, 1f);
            if (AshCloud != null)
            {
                var sh = SpriteSheets.Get("FxVhAshCloud");
                FxFactory.Reskin(AshCloud, new ClipBuilder(sh, "Drift", "ModVhAshCloudDrift").Loop().Build(), sh);
                FxFactory.SetEffect(AshCloud, destroyOnAnimEnd: false, destroyAfter: 3f, freeRotate: false);
                Strike.Collider(AshCloud, 14f, 10f);
                Strike.ArtAt(AshCloud, "FxVhAshCloud", 11, 14);
                Hook(AshCloud, i => Add<VhCrawlFx>(i).Restart(VhCrawlFx.Kind.Cloud));
            }
            // Lantern Wraith: soul orbs (burst), the cone that takes the hero's soul flame
            LanternBlast = FxFactory.Clone("skydropExplode", "ModLanternBlast");
            {
                var sh = SpriteSheets.Get("FxVhSoulBurst");
                if (LanternBlast != null && sh != null)
                {
                    FxFactory.StripChildren(LanternBlast);
                    var clip = new ClipBuilder(sh, "Play", "ModSoulBurstPlay").Once()
                        .Ev(1, "AnimSound", 0).Ev(2, "AnimDamageOn").Ev(4, "AnimDamageOff").Build();
                    FxFactory.Reskin(LanternBlast, clip, sh);
                    FxFactory.SetEffect(LanternBlast, destroyOnAnimEnd: true, freeRotate: false);
                    FxKit.NoTint(LanternBlast);
                    Strike.ArtAt(LanternBlast, "FxVhSoulBurst", 21, 23);
                    FxFactory.SetDamage(LanternBlast, 1.1f, knockback: 1f, status: OnFire, statusChance: 0.3f, stun: 0.2f);
                }
            }
            LanternOrb = FxKit.Projectile("ModLanternOrb", "DFX_fishFireball", "FxLanternOrb", "Fly", 175f, 1.3f, 1.1f, 0.6f, null, 1f,
                                          accel: 110f, speedMax: 30f);
            if (LanternOrb != null)
            {
                FxFactory.SetEffect(LanternOrb, destroyOnAnimEnd: false, destroyAfter: 1.3f, spawnOnDestroy: LanternBlast, freeRotate: true);
                FxFactory.SetContacts(LanternOrb, destroyOnHit: true, spawnOnHit: LanternBlast);
                Strike.ArtAt(LanternOrb, "FxLanternOrb", 6, 6);
            }
            SoulCone = FxKit.Visual("ModVhSoulCone", "FxVhSoulCone", "Play");
            if (SoulCone != null) { FxFactory.SetEffect(SoulCone, destroyOnAnimEnd: true, freeRotate: true); Strike.ArtAt(SoulCone, "FxVhSoulCone", 2, 22); }
            // Grand Chandelier: the wheel of flame, the drips round the ring, the ring flaring
            WheelFire = Hit("ModVhWheelFire", 1.2f, 1.0f, 40f, 24f, 0.3f, OnFire, 0.3f, aimed: false, rate: 0.5f);
            Drip = FxKit.TimedHit("ModVhDrip", "TrollGroundPoundBigShockwave", "FxVhDrip", "Fall", 2, 3, 0.3f, 0.1f, canFlip: false);
            if (Drip != null)
            {
                FxFactory.SetEffect(Drip, destroyOnAnimEnd: true, spawnOnDestroy: WaxPuddle, canFlip: false, freeRotate: false);
                Strike.Ground(Drip, "FxVhDrip", 5, 17, 8f, 5f);
            }
            RingFlare = FxKit.TimedHit("ModVhRingFlare", "TrollGroundPoundBigShockwave", "FxVhRingFlare", "Play", 1, 3, 1.3f, 0.6f, OnFire, 0.5f,
                                       canFlip: false);
            Strike.Ground(RingFlare, "FxVhRingFlare", 6, 16, 14f, 8f);
            Flame(RingFlare, 12f);
            // Votive Reliquary: votive flames (light wax)
            VotiveFlame = FxKit.Projectile("ModVhVotiveFlame", "DFX_skelMageNewProjectile", "FxVhVotiveFlame", "Fly", 150f, 1.0f, 1.0f, 0.4f, OnFire, 0.25f);
            Strike.ArtAt(VotiveFlame, "FxVhVotiveFlame", 12, 5);
            Flame(VotiveFlame, 6f);
        }
    }
}
