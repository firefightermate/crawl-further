using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.BelMora
{
    using CrawlFurther.Art;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Bel'Mora's effect templates and on-body indicators: brine and tides, hooks and chains, bells and peals, and the
    /// tells of every monster's quirk. Built once by <see cref="BelMoraPack.Register"/>; the boss and items reuse
    /// <see cref="Brine"/>, <see cref="Hook"/>, <see cref="Wave"/> and <see cref="BellToll"/>. Ground effects sit on their
    /// sheet's origin pixel (art/out_belmora/TIMING.md).
    /// </summary>
    public static class BelMoraFx
    {
        // shared
        public static GameObject Brine, Splash, BrineGlob, HitSplat, TidePool, TideCrest, Hook, Wave, BellToll, Peal, Lane;
        // tier 1
        public static GameObject UrchinRoll, Spine, LureBite, CrabPinch, BarnaclePlate, BarnacleBreak;
        // tier 2
        public static GameObject AnchorSlam, AnchorQuake, AnchorShoulder, AnchorBite, ChainLink, StiltStab, SpineEgg, EggBurst,
                                 WaterBolt, SongNote, LampreyBite, LampreyLunge, LampreyRasp, HermitCrush, BoxerJab, BoxerSting,
                                 BoxerStingFx;
        // tier 3
        public static GameObject CastBellFly, BellShadow, CastBellLand, BellStand, BellPunch, LiftToll, CaptainGaff, GrappleKick,
                                 GrappleHook, RopeLink, KelpHand, CrownLash, ThornShot, ThornPatch, CrownArm, ArmDie, ArmGrow,
                                 BroodSpine, EggSpine, BroodEgg, EggMark, EggPop, TridentThrust, CoralShard, JellyLash, TrailSeg, TrailSting,
                                 JetRing, GulperScoop, GulperChew, HagRasp, HagTear, HagGlob, SlimeSplash, KrakenSlam, Tentacle,
                                 KrakenSwat, BelltowerCrush, BelltowerRing, PoolRing, ColossusSlam, GardenPulse, Bud, ChampionUpper,
                                 Haymaker;
        // indicators
        public static StatusOverlayDef SlimeCoat, RoundBell;

        public static void Build()
        {
            var goo = FxFactory.GetStatus("StatusLavaSteveGoo");
            var stun = FxFactory.GetStatus("StatusDizzy");
            var root = FxFactory.GetStatus("StatusStuckToFloor");
            var bleed = FxFactory.GetStatus("StatusBleeding");
            var poison = FxFactory.GetStatus("StatusPoisoned");
            BuildShared(goo, stun);
            BuildStarters(bleed);
            BuildSeconds(goo, bleed, poison);
            BuildFinals(goo, stun, root, bleed, poison);
            SlimeCoat = ModStatus.Indicator("ModBelSlimeCoat", "FxBelSlimeCoat", "Loop", -2f, OverlayAt.Feet);
            RoundBell = ModStatus.Indicator("ModBelRoundBell", "FxBelRoundBell", "Ring", 1f, OverlayAt.Head);
            Plugin.Log.LogInfo("Bel'Mora FX templates built");
        }

        // ------------------------------------------------------------------------------------------- helpers
        static GameObject Melee(string name, float damage, float knock, float w, float h, Status status = null, float chance = 1f,
                                float life = 0.12f, float rate = 0f)
        {
            var go = AimedMelee.Rotating(FxKit.BodyHit(name, damage, rate, knock, life, status, chance));
            Strike.HitBox(go, w, h);
            return go;
        }

        static GameObject Loop(string name, string art, string anim, float life = 0f)
        {
            var go = FxKit.Visual(name, art, anim, loop: true);
            if (go != null) FxFactory.SetEffect(go, destroyOnAnimEnd: false, destroyAfter: life, canFlip: false, freeRotate: false);
            return go;
        }

        static GameObject At(GameObject go, string art, int gx, int gy) { Strike.ArtAt(go, art, gx, gy); return go; }

        /// <summary>A hitbox in mod art that plays <paramref name="first"/>, then <paramref name="loop"/> x reps, then
        /// <paramref name="last"/>, hurting every <paramref name="rate"/> s from frame <paramref name="on"/> until
        /// <paramref name="offFromEnd"/> frames before the end.</summary>
        static GameObject LongHit(string name, string art, string first, string loop, int reps, string last, float damage, float knock,
                                  Status status, float chance, float rate, int on, int offFromEnd, int gx, int gy, float w, float h)
        {
            var sh = SpriteSheets.Get(art);
            var go = FxFactory.Clone("TrollGroundPoundBigShockwave", name);
            if (go == null || sh == null) return go;
            FxFactory.StripChildren(go);
            var cb = new ClipBuilder(sh, first, name + "Clip").Once().Then(loop, reps);
            if (last != null) cb.Then(last);
            FxFactory.Reskin(go, cb.Ev(on, "AnimDamageOn").Ev(-offFromEnd, "AnimDamageOff").Build(), sh);
            var spr = go.GetComponent<exSprite>();
            if (spr != null) { spr.anchor = exPlane.Anchor.BotCenter; spr.offset = Vector2.zero; }
            FxFactory.SetEffect(go, destroyOnAnimEnd: true, canFlip: false, freeRotate: false);
            foreach (var m in go.GetComponents<ParticleMotion>()) { R.Set(m, "m_trailObject", null); m.enabled = false; }
            FxFactory.SetDamage(go, damage, rate: rate, knockback: knock, status: status, statusChance: chance, collisionAtStart: false);
            ImpactFx.Theme(go, art);
            FxKit.NoTint(go);
            Strike.Ground(go, art, gx, gy, w, h);
            return go;
        }

        static void OnSpawn<T>(GameObject t, System.Action<T> arm) where T : Component
        {
            if (t == null) return;
            FxFactory.OnSpawn[t] = i => { var c = i.GetComponent<T>() ?? i.AddComponent<T>(); arm(c); };
        }

        /// <summary>Mod art on a vanilla melee swipe: only the picture and its clip change (damage live on frame 0).</summary>
        static void Swipe(GameObject go, string sheet, string anim, int gx, int gy)
        {
            var art = SpriteSheets.Get(sheet);
            if (go == null || art == null || !art.Has(anim)) return;
            FxFactory.StripChildren(go);
            FxFactory.Reskin(go, new ClipBuilder(art, anim, go.name + "Clip").Once().Ev(0, "AnimDamageOn").Ev(1, "AnimDamageOff").Build(), art);
            go.transform.localScale = Vector3.one;
            foreach (var s in go.GetComponentsInChildren<exSprite>(true)) s.color = Color.white;
            FxKit.NoTint(go);
            Strike.ArtAt(go, sheet, gx, gy);
        }

        // ------------------------------------------------------------------------------------------- shared
        static void BuildShared(Status goo, Status stun)
        {
            Brine = FxFactory.Clone("LavaEffectLongerReworkZone", "ModBrine");
            var sh = SpriteSheets.Get("FxBrine");
            if (Brine != null && sh != null)
            {
                FxFactory.Reskin(Brine, new ClipBuilder(sh, "Life", "ModBrineLife").Once().Ev(1, "AnimDamageOn").Ev(-3, "AnimDamageOff").Build(), sh);
                FxFactory.SetEffect(Brine, destroyOnAnimEnd: true, snap: 1f);
                FxFactory.SetStatusZone(Brine, goo, hitsHero: true, hitsMonster: false);
                FxKit.NoTint(Brine);
                OnSpawn<BrineFx>(Brine, b => { });
                Strike.Ground(Brine, "FxBrine", 13, 4, 23f, 8f);
            }
            Splash = At(FxKit.Visual("ModSplash", "FxSplash", "Play"), "FxSplash", 20, 16);
            HitSplat = BelArt.HitSplat("ModBelHitSplat", "FxBelBrineSplat", 17, 7);
            BrineGlob = FxKit.Projectile("ModBrineGlob", "webBall", "FxBelBrineGlob", "Fly", 150f, 0.8f, 0.5f, 0.3f, accel: 20f, speedMax: 8f);
            if (BrineGlob != null)
            {
                FxFactory.SetEffect(BrineGlob, destroyOnAnimEnd: false, destroyAfter: 0.8f, spawnOnDestroy: Brine, freeRotate: true);
                FxFactory.SetContacts(BrineGlob, destroyOnHit: true, spawnOnHit: Brine);
            }
            // the tide: a lava-zone clone wearing FxBelTide: the crest washes in (0.32 s), the water lies there (1.2 s x 9),
            // then drains (0.54 s): 11.7 s in all, the zone live from frame 2 to the last 4
            TidePool = FxFactory.Clone("LavaEffectLongerReworkZone", "ModBelTidePool");
            var tsh = SpriteSheets.Get("FxBelTide");
            if (TidePool != null && tsh != null)
            {
                FxFactory.Reskin(TidePool, new ClipBuilder(tsh, "Spread", "ModBelTidePoolClip").Once().Then("Idle", 9).Then("Fade", 1)
                    .Ev(2, "AnimDamageOn").Ev(-4, "AnimDamageOff").Build(), tsh);
                FxFactory.SetEffect(TidePool, destroyOnAnimEnd: true, snap: 1f, canFlip: false, freeRotate: false);
                FxFactory.SetStatusZone(TidePool, goo, hitsHero: true, hitsMonster: false);
                FxKit.NoTint(TidePool);
                Strike.Ground(TidePool, "FxBelTide", 33, 12, BelTidePool.ZoneW, BelTidePool.ZoneH);
                OnSpawn<BelTidePool>(TidePool, t => t.Arm());
            }
            TideCrest = At(FxKit.Visual("ModBelTideCrest", "FxBelTideCrest", "Play"), "FxBelTideCrest", 20, 10);
            Hook = FxKit.Projectile("ModAnchorHook", "DFX_skelMageNewProjectile", "FxHook", "Fly", 230f, 0.42f, 0.5f, 0f, destroyOnHit: false);
            OnSpawn<HookFx>(Hook, h => h.strength = 240f);
            Wave = FxKit.Projectile("ModRiptideWave", "DFX_skelMageNewProjectile", "FxWave", "Fly", 120f, 1.6f, 1f, 2f, goo, 0.5f, destroyOnHit: false);
            if (Wave != null)
            {
                FxFactory.SetDamage(Wave, 1f, rate: 0.5f, knockback: 2f, status: goo, statusChance: 0.5f, collisionAtStart: true);
                FxFactory.SetMotion(Wave, 120f, trail: Brine, trailDist: 26f);
                foreach (var c in Wave.GetComponents<BoxCollider>()) c.size = new Vector3(c.size.x * 1.6f, c.size.y * 2.2f, c.size.z);
            }
            BellToll = FxKit.TimedHit("ModBellToll", "TrollGroundPoundBigShockwave", "FxBellRing", "Play", 0, 3, 1.4f, 1.5f, stun, 0.6f,
                                      colliderScale: 0.7f, canFlip: false);
            Strike.Ground(BellToll, "FxBellRing", 29, 19, 50f, 20f);
            Peal = FxKit.TimedHit("ModHermitPeal", "TrollGroundPoundBigShockwave", "FxPeal", "Play", 0, 3, 0.4f, 1.6f, canFlip: false);
            Strike.Ground(Peal, "FxPeal", 17, 14, 30f, 12f);
            Lane = Loop("ModBelLane", "FxBelLane", "Flow");
            if (Lane != null) { FxFactory.SetEffect(Lane, destroyOnAnimEnd: false, canFlip: false, freeRotate: true); Strike.ArtAt(Lane, "FxBelLane", 10, 5); }
        }

        // ------------------------------------------------------------------------------------------- tier 1
        static void BuildStarters(Status bleed)
        {
            UrchinRoll = FxKit.BodyHit("ModUrchinRoll", 0.7f, 0.4f, 0.8f, 0.6f, bleed, 0.25f);
            Strike.HitBox(UrchinRoll, 16f, 14f);
            Spine = FxKit.Projectile("ModUrchinSpine", "DFX_skelMageNewProjectile", "FxSpine", "Fly", 190f, 0.55f, 0.6f, 0.3f);
            LureBite = Melee("ModLureBite", 0.8f, 0.6f, 12f, 10f);
            CrabPinch = FxKit.Swipe("ModCrabPinch", "OrcSwipe", 1.0f, 0.7f);
            Swipe(CrabPinch, "FxBelPinch", "Pinch", 9, 9);
            Strike.Collider(CrabPinch, 12f, 10f, 6f, 0f);
            BarnaclePlate = FxKit.Visual("ModBarnaclePlateOrbit", "FxBelBarnacle", "Orbit", loop: true);
            if (BarnaclePlate != null)
            {
                FxFactory.SetEffect(BarnaclePlate, destroyOnAnimEnd: false, canFlip: true, freeRotate: false);
                Strike.ArtAt(BarnaclePlate, "FxBelBarnacle", 15, 15);
            }
            BarnacleBreak = At(FxKit.Visual("ModBarnaclePlateBreak", "FxBelBarnacle", "Break"), "FxBelBarnacle", 15, 15);
        }

        // ------------------------------------------------------------------------------------------- tier 2
        static void BuildSeconds(Status goo, Status bleed, Status poison)
        {
            AnchorSlam = Melee("ModAnchorSlam", 1.2f, 1.4f, 14f, 12f);
            AnchorQuake = FxKit.TimedHit("ModAnchorQuake", "TrollGroundPoundBigShockwave", "FxBelAnchorQuake", "Ring", 0, 3, 0.5f, 0.9f,
                                         durations: new[] { 0.0667f, 0.0667f, 0.0667f, 0.0667f }, canFlip: false);
            Strike.Ground(AnchorQuake, "FxBelAnchorQuake", 23, 9, 42f, 16f);
            AnchorShoulder = FxKit.BodyHit("ModAnchorShoulder", 0.9f, 0.6f, 1.0f, 0.3f);
            Strike.HitBox(AnchorShoulder, 14f, 14f, 0f, 8f);
            AnchorBite = FxKit.Inert("ModAnchorBite", "FxBelAnchorBite", "Bite", destroyOnAnimEnd: false, life: DiverAnchor.Stay, thenAnim: "Hold", thenRepeat: 8);
            Strike.ArtAt(AnchorBite, "FxBelAnchorBite", 11, 12);
            ChainLink = Loop("ModBelChainLink", "FxBelChain", "Link");
            StiltStab = Melee("ModSpinewalkerStab", 1.0f, 0.6f, 12f, 10f);
            EggBurst = FxKit.TimedHit("ModBelEggBurst", "TrollGroundPoundBigShockwave", "FxBelSpineEgg", "Burst", 1, 3, 0.8f, 0.8f, bleed, 0.3f,
                                      canFlip: false);
            Strike.Ground(EggBurst, "FxBelSpineEgg", 18, 14, 32f, 12f);
            SpineEgg = FxKit.Inert("ModBelSpineEgg", "FxBelSpineEgg", "Lay", destroyOnAnimEnd: false, life: SpineEggFx.Fuse + 1f, thenAnim: "Idle", thenRepeat: 14);
            Strike.ArtAt(SpineEgg, "FxBelSpineEgg", 18, 14);
            OnSpawn<SpineEggFx>(SpineEgg, e => e.Arm());
            WaterBolt = FxKit.Projectile("ModWaterBolt", "DFX_fishFireball", "FxWaterBolt", "Fly", 170f, 1.2f, 0.9f, 0.5f, goo, 0.35f, accel: 60f, speedMax: 70f);
            if (WaterBolt != null) FxFactory.SetContacts(WaterBolt, destroyOnHit: true, spawnOnHit: Splash);
            SongNote = At(FxKit.Visual("ModSongNote", "FxSongNote", "Play"), "FxSongNote", 8, 22);
            LampreyBite = Melee("ModLampreyBite", 1.0f, 0.4f, 12f, 12f, bleed, 0.35f);
            LampreyLunge = FxKit.BodyHit("ModLampreyLunge", 0.9f, 0.3f, 0.5f, 0.2f);
            Strike.HitBox(LampreyLunge, 14f, 12f);
            LampreyRasp = FxKit.BodyHit("ModLampreyRasp", 0.5f, 0f, 0.1f, 0.1f, bleed, 0.5f);
            Strike.HitBox(LampreyRasp, 12f, 12f);
            HermitCrush = Melee("ModHermitCrush", 1.1f, 1.2f, 16f, 12f);
            BoxerJab = Melee("ModBoxerJab", 0.8f, 0.5f, 12f, 12f, poison, 0.25f, 0.1f);
            BoxerSting = Melee("ModBoxerSting", 0.6f, 0.3f, 12f, 12f, poison, 0.6f, 0.1f);
            BoxerStingFx = At(FxKit.Visual("ModBoxerStingFx", "FxBelSting", "Play"), "FxBelSting", 11, 13);
        }

        // ------------------------------------------------------------------------------------------- tier 3
        static void BuildFinals(Status goo, Status stun, Status root, Status bleed, Status poison)
        {
            // ---- The Drowned Bell: the cast bell flies (drawn over its landing spot), lands as a hit, then stands
            CastBellFly = At(FxKit.Visual("ModBelCastBellFly", "FxBelCastBell", "Fly"), "FxBelCastBell", 26, 49);
            BellShadow = At(FxKit.Visual("ModBelBellShadow", "FxBelBellShadow", "Grow"), "FxBelBellShadow", 18, 6);
            CastBellLand = FxKit.TimedHit("ModBelCastBellLand", "TrollGroundPoundBigShockwave", "FxBelCastBell", "Land", 0, 2, 1.4f, 1.4f,
                                          canFlip: false);
            Strike.Ground(CastBellLand, "FxBelCastBell", 26, 49, 30f, 14f);
            BellStand = FxKit.Inert("ModBelBellStand", "FxBelCastBell", "Stand", destroyOnAnimEnd: false, life: BellCast.MaxBare + 2f,
                                    thenAnim: "Stand", thenRepeat: 60);
            Strike.ArtAt(BellStand, "FxBelCastBell", 26, 49);
            BellPunch = Melee("ModBelBellPunch", 1.0f, 0.6f, 12f, 12f);
            LiftToll = FxKit.TimedHit("ModBelLiftToll", "TrollGroundPoundBigShockwave", "FxBellRing", "Play", 0, 3, 1.2f, 1.5f, stun, 0.6f,
                                      colliderScale: 0.7f, canFlip: false);
            Strike.Ground(LiftToll, "FxBellRing", 29, 19, 48f, 20f);
            // ---- Drowned Captain: the gaff, the grapple's hook and rope, the landing kick, the kelp hand
            CaptainGaff = Melee("ModCaptainGaff", 1.3f, 0.3f, 16f, 16f, bleed, 0.3f);
            GrappleKick = FxKit.BodyHit("ModCaptainKick", 1.2f, 0f, 1.6f, 0.12f);
            Strike.HitBox(GrappleKick, 16f, 14f);
            GrappleHook = FxKit.Inert("ModBelGrappleHook", "FxBelGrapple", "Bite", destroyOnAnimEnd: false, life: 1.2f, thenAnim: "Hold", thenRepeat: 6);
            Strike.ArtAt(GrappleHook, "FxBelGrapple", 8, 8);
            RopeLink = Loop("ModBelRopeLink", "FxBelRope", "Link");
            KelpHand = At(FxKit.Visual("ModBelKelpHand", "FxBelKelpHand", "Grab"), "FxBelKelpHand", 12, 25);
            // ---- Crown of Thorns: the lash, the thorns that stick, the arms that crawl to brine
            CrownLash = Melee("ModCrownLash", 1.3f, 1.0f, 18f, 14f, bleed, 0.3f);
            ThornPatch = FxKit.TimedHit("ModThornPatch", "TrollGroundPoundBigShockwave", "FxBelThornPatch", "Life", 1, 6, 0.4f, 0.1f, bleed, 0.25f,
                                        rate: 0.5f, canFlip: false);
            Strike.Ground(ThornPatch, "FxBelThornPatch", 11, 5, 20f, 8f);
            ThornShot = FxKit.Projectile("ModThornShot", "webBall", "FxBelThorn", "Fly", 170f, 0.55f, 0.6f, 0.3f, bleed, 0.3f);
            if (ThornShot != null)
            {
                FxFactory.SetEffect(ThornShot, destroyOnAnimEnd: false, destroyAfter: 0.55f, spawnOnDestroy: ThornPatch, freeRotate: true);
                FxFactory.SetContacts(ThornShot, destroyOnHit: true, spawnOnHit: ThornPatch);
            }
            CrownArm = FxKit.Inert("ModBelCrownArm", "FxBelArm", "Crawl", destroyOnAnimEnd: false, life: CrownArmFx.Life + 1f, thenAnim: "Crawl", thenRepeat: 40);
            Strike.ArtAt(CrownArm, "FxBelArm", 15, 11);
            OnSpawn<CrownArmFx>(CrownArm, a => a.Arm());
            ArmDie = At(FxKit.Visual("ModBelArmDie", "FxBelArm", "Die"), "FxBelArm", 15, 11);
            ArmGrow = At(FxKit.Visual("ModBelArmGrow", "FxBelArm", "Grow"), "FxBelArm", 15, 11);
            // ---- Brood Urchin: the spine fan, the tide eggs and their marks
            BroodSpine = FxKit.Projectile("ModBroodSpine", "DFX_skelMageNewProjectile", "FxBelBroodSpine", "Fly", 185f, 0.6f, 1.0f, 0.3f);
            EggSpine = FxKit.Projectile("ModBroodEggSpine", "DFX_skelMageNewProjectile", "FxBelBroodSpine", "Fly", 160f, 0.45f, 0.9f, 0.3f);
            BroodEgg = FxKit.Inert("ModBelBroodEgg", "FxBelBroodEgg", "Fall", destroyOnAnimEnd: false, life: BroodEggFx.Fuse + 2f, thenAnim: "Sit", thenRepeat: 30);
            Strike.ArtAt(BroodEgg, "FxBelBroodEgg", 8, 37);
            OnSpawn<BroodEggFx>(BroodEgg, e => e.Arm());
            EggMark = At(FxKit.Visual("ModBelEggMark", "FxBelEggMark", "Mark"), "FxBelEggMark", 8, 4);
            EggPop = At(FxKit.Visual("ModBelEggPop", "FxBelBroodEgg", "Pop"), "FxBelBroodEgg", 8, 37);
            // ---- Tide Matriarch: the trident thrust and the coral shard it throws
            TridentThrust = FxKit.Swipe("ModTridentThrust", "OrcSwipe", 1.3f, 0.9f);
            Swipe(TridentThrust, "FxBelTrident", "Thrust", 22, 7);
            Strike.Collider(TridentThrust, 22f, 10f, 4f, 0f);
            CoralShard = FxKit.Projectile("ModCoralShard", "DFX_skelMageNewProjectile", "FxCoralShard", "Fly", 200f, 0.7f, 0.8f, 0.3f,
                                          bleed, 0.2f, rotate: false);
            if (CoralShard != null) FxFactory.SetContacts(CoralShard, destroyOnHit: true, spawnOnHit: Splash);
            // ---- Jelly Siren: the lash, her trailing tentacles and the sting rings of her jets
            JellyLash = Melee("ModJellyLash", 1.2f, 0.5f, 18f, 12f, goo, 0.5f, 0.14f);
            TrailSeg = Loop("ModBelTrailSeg", "FxBelTentacleTrail", "Glow");
            if (TrailSeg != null) { FxFactory.SetEffect(TrailSeg, destroyOnAnimEnd: false, canFlip: false, freeRotate: true); Strike.ArtAt(TrailSeg, "FxBelTentacleTrail", 7, 4); }
            TrailSting = FxKit.BodyHit("ModJellyTrailSting", 0.5f, 0f, 0.2f, 0.1f, goo, 1f);
            Strike.HitBox(TrailSting, 10f, 10f);
            JetRing = FxKit.TimedHit("ModJellyJetRing", "TrollGroundPoundBigShockwave", "FxBelJetRing", "Play", 0, 3, 0.7f, 0.4f, goo, 1f, canFlip: false);
            Strike.Ground(JetRing, "FxBelJetRing", 20, 9, 34f, 12f);
            // ---- Gulper Eel: the wide scoop and the chewing inside
            GulperScoop = Melee("ModGulperScoop", 1.3f, 0.8f, 22f, 12f);
            GulperChew = FxKit.BodyHit("ModGulperChew", 0.4f, 0f, 0f, 0.08f);
            Strike.HitBox(GulperChew, 10f, 10f);
            // ---- Slime Hag: the rasp, the tear and the slime spew
            HagRasp = Melee("ModHagRasp", 1.3f, 0.6f, 16f, 12f, bleed, 0.4f);
            HagTear = FxKit.BodyHit("ModHagTear", 0.7f, 0f, 0.3f, 0.1f, bleed, 1f);
            Strike.HitBox(HagTear, 12f, 12f);
            SlimeSplash = At(FxKit.Visual("ModBelSlimeSplash", "FxBelSting", "Play"), "FxBelSting", 11, 13);
            HagGlob = FxKit.Projectile("ModHagGlob", "webBall", "FxBelSlimeGlob", "Fly", 150f, 0.7f, 0.8f, 0.2f);
            if (HagGlob != null) FxFactory.SetContacts(HagGlob, destroyOnHit: true);
            // ---- Abyss Kraken: the slam, the arms out of the floor and their swats
            KrakenSlam = Melee("ModKrakenSlam", 1.3f, 1.0f, 20f, 12f, goo, 0.5f);
            Tentacle = FxKit.TimedHit("ModKrakenTentacle", "TrollGroundPoundBigShockwave", "FxTentacle", "Rise", 1, 4, 1.0f, 0.6f, root, 1f,
                                      canFlip: false);
            if (Tentacle != null)
            {
                FxFactory.SetEffect(Tentacle, destroyOnAnimEnd: false, destroyAfter: KrakenArmFx.Stay + 0.4f, canFlip: false, freeRotate: false);
                Strike.Ground(Tentacle, "FxTentacle", 19, 30, 18f, 10f);
                OnSpawn<KrakenArmFx>(Tentacle, a => a.Arm());
            }
            KrakenSwat = FxKit.BodyHit("ModKrakenSwat", 0.8f, 0f, 0.6f, 0.1f);
            Strike.HitBox(KrakenSwat, 12f, 12f);
            // ---- Belltower Hermit: the crusher claw, one step of its march, a peal ringing through a pool
            BelltowerCrush = Melee("ModBelltowerCrush", 1.4f, 1.4f, 18f, 12f);
            BelltowerRing = FxKit.TimedHit("ModBelltowerRing", "TrollGroundPoundBigShockwave", "FxBelMarchRing", "Play", 0, 2, 0.9f, 1.0f, stun, 0.25f,
                                           canFlip: false);
            Strike.Ground(BelltowerRing, "FxBelMarchRing", 14, 12, 24f, 10f);
            PoolRing = At(FxKit.Visual("ModBelPoolRing", "FxBelPoolRing", "Play"), "FxBelPoolRing", 33, 12);
            // ---- Anemone Colossus: the hammer, its garden's sting field, the buds it flicks
            ColossusSlam = Melee("ModColossusSlam", 1.4f, 1.4f, 22f, 14f);
            GardenPulse = FxKit.TimedHit("ModColossusGarden", "TrollGroundPoundBigShockwave", "FxBelStingAura", "Play", 1, 3, 0.4f, 0.1f, poison, 0.5f,
                                         canFlip: false);
            Strike.Ground(GardenPulse, "FxBelStingAura", 30, 13, 48f, 18f);
            Bud = LongHit("ModColossusBud", "FxBelBud", "Root", "Sting", 8, "Wilt", 0.5f, 0.1f, poison, 0.6f, 0.6f, 3, 3, 12, 14, 30f, 12f);
            // ---- Reef Champion: the uppercut and the haymaker
            ChampionUpper = Melee("ModChampionUpper", 1.3f, 1.4f, 14f, 22f);
            Haymaker = Melee("ModChampionHaymaker", 1.6f, 2.0f, 18f, 14f);
        }
    }

    /// <summary>Bel'Mora's hit splat: brine instead of the vanilla red blood.</summary>
    public static class BelArt
    {
        /// <summary>A clone of the vanilla BloodSplashGenericRandom (keeps its hit sound and layer) playing one of the sheet's
        /// two variants ("Play" / "Play2") at random, without the red tint or the vanilla spark.</summary>
        public static GameObject HitSplat(string name, string sheet, int gx, int gy)
        {
            var art = SpriteSheets.Get(sheet);
            var go = FxFactory.Clone("BloodSplashGenericRandom", name);
            if (go == null || art == null || !art.Has("Play")) return null;
            FxFactory.StripChildren(go);
            var a = new ClipBuilder(art, "Play", name + "A").Once().Build();
            var b = art.Has("Play2") ? new ClipBuilder(art, "Play2", name + "B").Once().Build() : null;
            FxFactory.Reskin(go, a, art);
            FxFactory.SetEffect(go, destroyOnAnimEnd: true, freeRotate: false);
            var anim = go.GetComponent<exSpriteAnimation>();
            var eff = go.GetComponent<Effect>();
            if (anim != null && b != null && eff != null)
            {
                anim.animations = new List<exSpriteAnimClip> { a, b };
                R.Set(eff, "m_randomAnimation", true);
                R.Set(eff, "m_animationDefault", null);
            }
            FxKit.NoTint(go);
            foreach (var s in go.GetComponentsInChildren<exSprite>(true)) s.color = Color.white;
            Strike.ArtAt(go, sheet, gx, gy);
            return go;
        }

        /// <summary>Swap the vanilla red blood in a monster's m_spawnOnHit for <paramref name="splat"/>.</summary>
        public static void UseHitSplat(Player p, GameObject splat)
        {
            if (p == null || splat == null) return;
            var arr = R.Get<DamageEffectData[]>(p, "m_spawnOnHit");
            if (arr == null) return;
            foreach (var d in arr)
                if (d != null && d.m_object != null && d.m_object.name.StartsWith("BloodSplash")) d.m_object = splat;
        }
    }
}
