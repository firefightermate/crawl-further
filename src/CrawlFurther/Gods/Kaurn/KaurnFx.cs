using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Art;
    using CrawlFurther.Monsters;

    /// <summary>
    /// Kaurn's effect templates: arcs, sparks, rods and the other iron posts the arcs join, and every move's projectile,
    /// hitbox and tell. Art origins follow art/out_kaurn/TIMING.md (the FX table).
    /// </summary>
    public static class KaurnFx
    {
        // the perk and every monster's shared pieces
        public static GameObject ArcSeg, ArcThin, ArcWhite, ArcHot, HitFx, Crackle, CrackleWhite, StaticSpark, DoubleClang, RodGlow, RodDark;
        // iron posts
        public static GameObject Stud, Rod, RodHot, RodFence, RodVolley, SlagRod, HangingWisp, Charge, KindleOrb;
        // tier 1
        public static GameObject ImpBonk, Rivet, Zap, RushHit, RushBig, Mote, Ring;
        // tier 2
        public static GameObject SmithSmash, Surge, Plates, Shatter, Staple, WireHook, HoundBite, MagPull, MagPush, Ball, StaticBolt, Jolt,
                                 Seeker, Field;
        // tier 3
        public static GameObject Quake, Steam, MasterSmash, ThrownRod, RodLand, Breath, WyvernBite, RideStreak, RideFlash, Canister, CanBurst,
                                 ChargeLob, ChargeBlast, BullGore, Ram, RamHard, RamFull, WargBite, PolarRing, Clamp, LodeSeg, Lance,
                                 StormBand, StormBolt, SplitOrb, Shard, Orb, PlanetDots, PlanetBeam, WhipHit, WhipVis, Bead, PileTick,
                                 Relay, RelayAnswer, RelayFlash, Dart, Drain, SparkFall, RodStrike;
        public static readonly GameObject[] Planets = new GameObject[3];
        // shop items
        public static GameObject HeroChainSpark, HeroBall;
        public static StatusOverlayDef MagnetInd, WiredInd, HairInd;

        static T Comp<T>(GameObject i) where T : Component { return i.GetComponent<T>() ?? i.AddComponent<T>(); }

        /// <summary>Run <paramref name="fn"/> on every spawned instance of <paramref name="tmpl"/>, after any hook it already has.</summary>
        public static void OnSpawn(GameObject tmpl, System.Action<GameObject> fn)
        {
            if (tmpl == null) return;
            System.Action<GameObject> prev;
            FxFactory.OnSpawn.TryGetValue(tmpl, out prev);
            FxFactory.OnSpawn[tmpl] = i => { if (prev != null) prev(i); fn(i); };
        }

        static void Node(GameObject tmpl, KrnNode.Kind kind, float height, float hot = 0f)
        {
            OnSpawn(tmpl, i => Comp<KrnNode>(i).Init(kind, height, hot));
        }

        static GameObject Seg(string name, string sheet, string anim, bool loop)
        {
            var go = FxKit.Visual(name, sheet, anim, loop);
            if (go == null) return null;
            var spr = go.GetComponent<exSprite>();
            if (spr != null) { spr.anchor = exPlane.Anchor.MidCenter; spr.offset = Vector2.zero; }
            FxFactory.SetEffect(go, destroyOnAnimEnd: !loop, destroyAfter: 0f, canFlip: false, freeRotate: true);
            return go;
        }

        static GameObject Proj(string name, string art, float speed, float life, float damage, float knock, Status status = null,
                               float chance = 1f, bool rotate = true, bool destroyOnHit = true)
        {
            var go = FxKit.Projectile(name, "DFX_skelMageNewProjectile", art, "Fly", speed, life, damage, knock, status, chance,
                                      rotate: rotate, destroyOnHit: destroyOnHit);
            if (go != null && destroyOnHit) FxFactory.SetContacts(go, destroyOnHit: true, spawnOnHit: HitFx);
            return go;
        }

        static GameObject Look(string name, string sheet, string anim, int gx, int gy, bool loop = false, float life = 0f)
        {
            var go = FxKit.Visual(name, sheet, anim, loop, life);
            Strike.ArtAt(go, sheet, gx, gy);
            return go;
        }

        static GameObject Hit(string name, string sheet, int on, int off, float damage, float knock, int gx, int gy, float w, float h,
                              Status status = null, float chance = 1f, float rate = 0f)
        {
            var go = FxKit.TimedHit(name, "TrollGroundPoundBigShockwave", sheet, "Play", on, off, damage, knock, status, chance, rate: rate, canFlip: false);
            Strike.Ground(go, sheet, gx, gy, w, h);
            return go;
        }

        static GameObject Body(string name, float damage, float knock, float life, float w, float h, Status status = null, float chance = 1f,
                               float rate = 0f, bool aimed = true)
        {
            var go = FxKit.BodyHit(name, damage, rate, knock, life, status, chance);
            if (aimed) go = AimedMelee.Rotating(go);
            Strike.HitBox(go, w, h);
            return go;
        }

        static GameObject Post(string name, string sheet, string rise, string then, int repeat, float life, int gx, int gy)
        {
            var go = FxKit.Inert(name, sheet, rise, destroyOnAnimEnd: false, life: life, thenAnim: then, thenRepeat: repeat);
            Strike.Ground(go, sheet, gx, gy, 6f, 4f);
            return go;
        }

        public static void Build()
        {
            var daze = ModStatus.Daze;
            var root = ModStatus.Root;
            var slow = ModStatus.Slow;

            // ---- the perk: arcs (12 px segments), hits, crackles, the discharged sparks
            ArcSeg = Seg("ModKrnArcSeg", "FxKrnArc", "Crackle", true);
            ArcThin = Seg("ModKrnArcThin", "FxKrnArc", "Thin", true);
            ArcWhite = Seg("ModKrnArcWhite", "FxKrnArc", "White", true);
            ArcHot = Seg("ModKrnArcHot", "FxKrnArc", "Hot", true);
            HitFx = Look("ModKrnHitFx", "FxKrnHit", "Play", 12, 9);
            Crackle = Look("ModKrnCrackle", "FxKrnCrackle", "Play", 6, 6);
            CrackleWhite = Look("ModKrnCrackleWhite", "FxKrnCrackle", "White", 6, 6);
            StaticSpark = Proj("ModKrnStaticSpark", "FxKrnStaticSpark", 200f, 0.5f, 0.4f, 0.2f);
            DoubleClang = Look("ModKrnDoubleClang", "FxKrnDoubleClang", "Play", 11, 12);
            RodGlow = Look("ModKrnRodGlow", "FxKrnRodGlow", "Play", 7, 23);
            RodDark = FxKit.Inert("ModKrnRodDark", "FxKrnRodDark", "Play", destroyOnAnimEnd: true);
            Strike.ArtAt(RodDark, "FxKrnRodDark", 7, 23);

            // ---- iron posts: every one of them is an arc end (KrnNode)
            Stud = Post("ModKrnStud", "FxKrnStud", "Land", "Idle", 8, 6f, 6, 8);
            Node(Stud, KrnNode.Kind.Stud, 3f);
            Rod = Post("ModKrnRod", "FxKrnRod", "Rise", "Idle", 9, 6f, 7, 23);
            Node(Rod, KrnNode.Kind.Rod, 13f);
            // the Anvil Smith's: red hot for 3 s (its arcs hurt twice as much), then grey
            RodHot = Post("ModKrnRodHot", "FxKrnRod", "Rise", "Hot", 1, 6f, 7, 23);
            Node(RodHot, KrnNode.Kind.Rod, 13f, KrnNode.HotTime);
            RodFence = Post("ModKrnRodFence", "FxKrnRod", "Rise", "Idle", 6, 4.5f, 7, 23);
            Node(RodFence, KrnNode.Kind.Rod, 13f);
            RodVolley = Post("ModKrnRodVolley", "FxKrnRod", "Rise", "Idle", 12, 9f, 7, 23);
            Node(RodVolley, KrnNode.Kind.Rod, 13f);
            // the rod a Kaurn monster leaves where it dies: its own crooked slag art
            SlagRod = Post("ModKrnSlagRod", "FxKrnSlagRod", "Rise", "Idle", 12, 9f, 7, 23);
            Node(SlagRod, KrnNode.Kind.Rod, 13f);
            // an Arc Lantern wisp that missed: it hangs where it stopped (drawn 14 px up) for 3 s
            HangingWisp = FxKit.Inert("ModKrnHangingWisp", "FxKrnHangingWisp", "Hang", destroyOnAnimEnd: false, life: 3f, thenAnim: "Hang", thenRepeat: 12);
            Strike.ArtAt(HangingWisp, "FxKrnHangingWisp", 7, 21);
            Node(HangingWisp, KrnNode.Kind.Wisp, 14f);
            // a Fuse Sapper charge: iron, but arcs don't join it; one that reaches it sets it off (KrnChargeFx)
            Charge = FxKit.Inert("ModKrnCharge", "FxKrnCharge", "Idle", destroyOnAnimEnd: false, life: KrnChargeFx.Life + 0.5f, thenAnim: "Idle", thenRepeat: 30);
            Strike.ArtAt(Charge, "FxKrnCharge", 7, 11);
            Node(Charge, KrnNode.Kind.Charge, 4f);
            OnSpawn(Charge, i => Comp<KrnChargeFx>(i).Reset());
            // a Scarab Magus ball: drifts in a straight line (30 px/s) for 5 s, an arc end the whole way
            KindleOrb = FxKit.Projectile("ModKrnKindleOrb", "DFX_skelMageNewProjectile", "FxKrnKindleOrb", "Fly", 30f, 5f, 0.5f, 0.3f,
                                         rotate: false, destroyOnHit: false);
            if (KindleOrb != null)
            {
                FxFactory.SetDamage(KindleOrb, 0.5f, rate: 0.6f, knockback: 0.3f, collisionAtStart: true);
                Strike.ArtAt(KindleOrb, "FxKrnKindleOrb", 8, 9);
                Strike.Collider(KindleOrb, 8f, 8f);
            }
            Node(KindleOrb, KrnNode.Kind.Orb, 0f);

            // ---- Rivet Imp: a hammer bonk (a landed bonk stores 2 sparks), hot rivets that stick as posts
            ImpBonk = Body("ModKrnBonk", 0.9f, 0.6f, 0.15f, 12f, 12f);         // hammer head lands at (12, -2)
            OnSpawn(ImpBonk, i => Comp<KrnBonkFx>(i).Reset());
            Rivet = Proj("ModKrnRivet", "FxKrnRivet", 160f, 0.42f, 0.6f, 0.3f);
            if (Rivet != null) FxFactory.SetEffect(Rivet, destroyOnAnimEnd: false, destroyAfter: 0.42f, spawnOnDestroy: Stud, freeRotate: true);

            // ---- Spark Beetle: an antenna zap; the rolling ball (bigger and sure to stun when overcharged)
            Zap = Proj("ModKrnZap", "FxKrnSpark", 220f, 0.3f, 0.7f, 0.3f);
            RushHit = Body("ModKrnRush", 0.8f, 0.8f, 0.45f, 11f, 11f, daze, 0.3f, 0.4f, aimed: false);
            RushBig = Body("ModKrnRushBig", 0.9f, 1.0f, 0.45f, 16f, 16f, daze, 1f, 0.4f, aimed: false);

            // ---- Coil Wisp: a lightning mote; a shock ring
            Mote = Proj("ModKrnMote", "FxKrnMote", 160f, 0.9f, 0.7f, 0.4f);
            Ring = Hit("ModKrnRing", "FxKrnRing", 1, 4, 0.8f, 0.6f, 26, 11, 42f, 16f, daze, 0.35f);

            // ---- Anvil Smith: a hammer smash and its floor surge; the iron plate
            SmithSmash = Body("ModKrnSmash", 1.1f, 0.9f, 0.15f, 14f, 12f);      // hammer head at (18, -1)
            Surge = Proj("ModKrnSurge", "FxKrnSurge", 150f, 0.45f, 0.8f, 0.6f, destroyOnHit: false);
            Plates = Look("ModKrnPlateOrbit", "FxKrnPlates", "Loop", 18, 22, true);
            Shatter = Look("ModKrnPlateShatter", "FxKrnShatter", "Play", 20, 24);

            // ---- Wire Gremlin: a rooting staple; the hooked wire that wires the hero (Conductor)
            Staple = Proj("ModKrnStaple", "FxKrnStaple", 200f, 0.45f, 0.8f, 0.3f, root, 1f);
            WireHook = Proj("ModKrnWireHook", "FxKrnHook", 190f, 0.5f, 0.3f, 0.1f);
            OnSpawn(WireHook, i => Comp<KrnWireHookFx>(i).Reset());
            WiredInd = ModStatus.Indicator("ModIndKrnWired", "FxKrnWired", "Loop", 0f, OverlayAt.Feet);

            // ---- Lodestone Hound: a leaping bite; the howl's field (red pulls, blue pushes)
            HoundBite = Body("ModKrnHoundBite", 1.0f, 0.7f, 0.2f, 12f, 12f);    // jaws at (19, -12)
            MagPull = Look("ModKrnMagPull", "FxKrnMagField", "Pull", 27, 17);
            MagPush = Look("ModKrnMagPush", "FxKrnMagField", "Push", 27, 17);

            // ---- Stormcaller: ball lightning; Static Build's bolt (rods take it)
            Ball = FxKit.Projectile("ModKrnBall", "DFX_skelMageNewProjectile", "FxKrnBall", "Fly", 60f, 1.7f, 0.9f, 0.6f, accel: 130f, speedMax: 150f);
            if (Ball != null) FxFactory.SetContacts(Ball, destroyOnHit: true, spawnOnHit: HitFx);
            StaticBolt = FxKit.TimedHit("ModKrnStaticBolt", "TrollGroundPoundBigShockwave", "FxKrnStrike", "Play", 6, 8, 1.2f, 0.5f, daze, 0.3f,
                                        canFlip: false, durations: new[] { 0.06f, 0.06f, 0.06f, 0.06f, 0.06f, 0.06f, 0.05f, 0.06f, 0.06f, 0.14f });
            Strike.Ground(StaticBolt, "FxKrnStrike", 20, 61, 24f, 10f);
            HairInd = ModStatus.Indicator("ModIndKrnHair", "FxKrnHair", "Loop", 1f, OverlayAt.Head);
            // the same bolt taken by a rod: no hitbox, just the strike
            RodStrike = FxKit.Visual("ModKrnRodStrike", "FxKrnStrike", "Play", false, 0f, 0.02f, 0.02f, 0.02f, 0.02f, 0.02f, 0.02f, 0.05f, 0.06f, 0.06f, 0.14f);
            Strike.ArtAt(RodStrike, "FxKrnStrike", 20, 61);

            // ---- Leyden Golem / Arc Lantern
            Jolt = Proj("ModKrnJolt", "FxKrnJolt", 230f, 0.45f, 0.9f, 0.4f);
            Seeker = Proj("ModKrnSeeker", "FxKrnSeeker", 110f, 1.6f, 0.9f, 0.4f);
            OnSpawn(Seeker, i => Comp<KrnSeekerFx>(i).Reset());
            Field = Hit("ModKrnField", "FxKrnField", 2, 10, 0.3f, 0.1f, 26, 11, 44f, 16f, slow, 0.5f, 0.5f);

            // ---- Forge Colossus: the quake; the vent's steam
            Quake = Hit("ModKrnQuake", "FxKrnQuake", 1, 4, 1.4f, 1.6f, 31, 15, 48f, 18f, daze, 0.3f);
            Steam = Hit("ModKrnSteam", "FxKrnSteam", 1, 4, 0.8f, 2.4f, 38, 26, 60f, 24f);

            // ---- Forgemaster: the sledge (damage set per swing by the rods carried); thrown rods
            MasterSmash = Body("ModKrnMasterSmash", 1.3f, 1.2f, 0.15f, 16f, 12f, daze, 0.3f);   // sledge head at (23, -1)
            RodLand = Hit("ModKrnRodLand", "FxKrnRodLand", 0, 2, 0.9f, 0.5f, 16, 12, 18f, 8f);
            ThrownRod = FxKit.Inert("ModKrnThrownRod", "FxKrnThrownRod", "Fly", destroyOnAnimEnd: false, life: 2f, thenAnim: "Fly", thenRepeat: 10);
            Strike.ArtAt(ThrownRod, "FxKrnThrownRod", 9, 9);
            OnSpawn(ThrownRod, i => Comp<KrnLobFx>(i).Reset());

            // ---- Wire Wyvern: the breath beam; the ride
            Breath = FxKit.Projectile("ModKrnBreath", "DFX_skelMageNewProjectile", "FxKrnBreath", "Play", 0f, 0.36f, 1.3f, 0.6f, destroyOnHit: false);
            if (Breath != null)
            {
                FxFactory.SetMotion(Breath, 0f, enabled: false);
                Strike.ArtAt(Breath, "FxKrnBreath", 2, 7);
                Strike.Collider(Breath, 58f, 6f, 30f, 0f);   // the beam: 2..60 px out of the mouth
            }
            WyvernBite = Body("ModKrnWyvernBite", 1.4f, 1.0f, 0.15f, 16f, 14f);
            RideStreak = FxKit.Visual("ModKrnRideStreak", "FxKrnRideStreak", "Fly", true);
            if (RideStreak != null)
            {
                var spr = RideStreak.GetComponent<exSprite>();
                if (spr != null) { spr.anchor = exPlane.Anchor.MidCenter; spr.offset = Vector2.zero; }
                FxFactory.SetEffect(RideStreak, destroyOnAnimEnd: false, destroyAfter: 2f, canFlip: false, freeRotate: true);
            }
            RideFlash = Look("ModKrnRideFlash", "FxKrnRideFlash", "Play", 20, 33);

            // ---- Fuse Sapper: the canister; the charges it lobs by the hero
            CanBurst = Hit("ModKrnCanBurst", "FxKrnCanBurst", 1, 4, 1.0f, 0.9f, 24, 19, 36f, 14f, daze, 0.3f);
            Canister = FxKit.Inert("ModKrnCanister", "FxKrnCanister", "Fly", destroyOnAnimEnd: false, life: 1.2f, thenAnim: "Fly", thenRepeat: 6);
            Strike.ArtAt(Canister, "FxKrnCanister", 6, 10);
            OnSpawn(Canister, i => { var l = Comp<KrnLobFx>(i); l.Reset(); l.land = CanBurst; });
            ChargeBlast = Hit("ModKrnChargeBlast", "FxKrnChargeBlast", 1, 4, 1.3f, 1.0f, 22, 20, 40f, 16f, daze, 0.4f);
            ChargeLob = FxKit.Inert("ModKrnChargeLob", "FxKrnCanister", "Fly", destroyOnAnimEnd: false, life: 1.2f, thenAnim: "Fly", thenRepeat: 6);
            Strike.ArtAt(ChargeLob, "FxKrnCanister", 6, 10);
            OnSpawn(ChargeLob, i => { var l = Comp<KrnLobFx>(i); l.Reset(); l.land = Charge; l.time = 0.45f; });

            // ---- Thunder Bull: the horn hook; the charge (its hit grows with the distance run)
            BullGore = Body("ModKrnGore", 1.4f, 1.6f, 0.18f, 18f, 18f);        // horn hook at (22, -20)
            Ram = Body("ModKrnRam", 0.8f, 1.2f, 2f, 18f, 16f, daze, 0.3f, aimed: false);
            RamHard = Body("ModKrnRamHard", 1.2f, 1.4f, 2f, 18f, 16f, daze, 0.4f, aimed: false);
            RamFull = Body("ModKrnRamFull", 1.6f, 1.8f, 2f, 18f, 16f, daze, 0.6f, aimed: false);
            foreach (var r in new[] { Ram, RamHard, RamFull }) OnSpawn(r, i => Comp<KrnRamFx>(i).Reset());

            // ---- Polarity Warg: twin bites; Magnetize's ring, field line and clamp
            WargBite = Body("ModKrnWargBite", 1.0f, 0.8f, 0.15f, 14f, 14f);
            PolarRing = Look("ModKrnPolarRing", "FxKrnPolarRing", "Play", 33, 17);
            Clamp = Look("ModKrnClamp", "FxKrnClamp", "Play", 13, 20);
            LodeSeg = Seg("ModKrnLodeSeg", "FxKrnLodeArc", "Crackle", true);
            MagnetInd = ModStatus.Indicator("ModIndKrnMagnet", "FxKrnIndMagnet", "Loop", 1f, OverlayAt.Head);

            // ---- Storm Herald: the lance; Eye of the Storm's band and strikes
            Lance = Proj("ModKrnLance", "FxKrnLance", 260f, 0.65f, 1.2f, 0.8f, destroyOnHit: false);
            if (Lance != null)
                foreach (var c in Lance.GetComponents<BoxCollider>()) c.size = new Vector3(c.size.x * 2f, c.size.y * 0.8f, c.size.z);
            StormBand = Look("ModKrnStormBand", "FxKrnStormBand", "Loop", 113, 58, true, HeraldStorm.Duration + 0.2f);
            StormBolt = FxKit.TimedHit("ModKrnStormBolt", "TrollGroundPoundBigShockwave", "FxKrnStormBolt", "Play", 3, 5, 1.0f, 0.5f, canFlip: false);
            Strike.Ground(StormBolt, "FxKrnStormBolt", 16, 55, 32f, 14f);

            // ---- Scarab Magus: the splitting orb
            SplitOrb = Proj("ModKrnSplitOrb", "FxKrnSplitOrb", 150f, 0.9f, 0.9f, 0.6f, rotate: false);
            OnSpawn(SplitOrb, i => Comp<KrnSplitFx>(i).Reset());
            Shard = Proj("ModKrnShard", "FxKrnShard", 220f, 0.5f, 0.9f, 0.3f);

            // ---- Storm Orrery: the ringed orb; the planet line and its beam
            Orb = Proj("ModKrnOrb", "FxKrnOrb", 150f, 1.2f, 1.1f, 0.8f, rotate: false);
            PlanetDots = Seg("ModKrnPlanetDots", "FxKrnPlanetLine", "Dots", true);
            PlanetBeam = Seg("ModKrnPlanetBeam", "FxKrnPlanetLine", "Beam", true);
            var names = new[] { "Red", "Green", "Violet" };
            for (int k = 0; k < 3; k++)
            {
                Planets[k] = FxKit.Visual("ModKrnPlanet" + names[k], "FxKrnPlanet", names[k], true);
                if (Planets[k] != null) FxFactory.SetEffect(Planets[k], destroyOnAnimEnd: false, destroyAfter: 2f, canFlip: false, freeRotate: false);
                Strike.ArtAt(Planets[k], "FxKrnPlanet", 5, 5);
            }

            // ---- Voltaic Pile: the lightning lash; the beads and the tick
            WhipHit = Body("ModKrnWhipHit", 1.3f, 0.8f, 0.15f, 40f, 10f);       // the 40 px lash from the hand
            WhipVis = AimedMelee.Rotating(FxKit.Visual("ModKrnWhip", "FxKrnWhip", "Play"));
            Strike.ArtAt(WhipVis, "FxKrnWhip", 2, 7);
            Bead = FxKit.Visual("ModKrnBead", "FxKrnBead", "Loop", true);
            if (Bead != null)
            {
                FxFactory.SetEffect(Bead, destroyOnAnimEnd: false, destroyAfter: 1f, canFlip: false, freeRotate: false);
                Strike.ArtAt(Bead, "FxKrnBead", 5, 5);
            }
            PileTick = Look("ModKrnPileTick", "FxKrnPileTick", "Play", 8, 9);

            // ---- Tesla Spire: the remote bolt and the flash of the rod that fires it
            Relay = Proj("ModKrnRelay", "FxKrnRelay", 240f, 0.6f, 1.1f, 0.5f);
            RelayAnswer = Proj("ModKrnRelayAnswer", "FxKrnRelay", 230f, 0.55f, 0.8f, 0.4f);
            RelayFlash = Look("ModKrnRelayFlash", "FxKrnRelayFlash", "Play", 11, 11);

            // ---- Static Moth: weaving darts; drinking a rod; Spark Fall
            Dart = Proj("ModKrnDart", "FxKrnDart", 150f, 0.9f, 0.9f, 0.3f);
            OnSpawn(Dart, i => Comp<KrnWeaveFx>(i).Reset());
            Drain = Look("ModKrnDrain", "FxKrnDrain", "Play", 6, 25);
            SparkFall = FxKit.TimedHit("ModKrnSparkFall", "TrollGroundPoundBigShockwave", "FxKrnSparkFall", "Play", 6, 7, 0.4f, 0.2f, canFlip: false);
            Strike.Ground(SparkFall, "FxKrnSparkFall", 8, 33, 12f, 6f);

            // ---- hero copies (shop items)
            HeroChainSpark = FxKit.Weakened(Zap, "ModKrnHeroChainSpark", 0.85f);
            if (HeroChainSpark != null)
            {
                FxFactory.SetEffect(HeroChainSpark, destroyOnAnimEnd: false, destroyAfter: 0.8f, freeRotate: true);
                FxFactory.SetMotion(HeroChainSpark, 260f);
                FxFactory.OnSpawn[HeroChainSpark] = i => Comp<ChainSparkFx>(i).Reset();
            }
            HeroBall = FxKit.Weakened(Ball, "ModKrnHeroBall", 0.7f);
            Plugin.Log.LogInfo("Kaurn FX templates built");
        }

        /// <summary>A clip from one of Kaurn's FX sheets (looping or once), for effects that change what they show.</summary>
        public static exSpriteAnimClip Clip(string sheet, string anim, bool loop)
        {
            var sh = SpriteSheets.Get(sheet);
            if (sh == null || !sh.Has(anim)) return null;
            var cb = new ClipBuilder(sh, anim, "ModKrn" + sheet + anim);
            if (loop) cb.Loop(); else cb.Once();
            return cb.Build();
        }

        /// <summary>Lay a chain of 12 px segment sprites from a to b, reusing <paramref name="segs"/>.</summary>
        public static void Chain(List<GameObject> segs, GameObject tmpl, Vector2 a, Vector2 b, int maxSegs = 12)
        {
            var d = b - a;
            float len = d.magnitude;
            int n = len < 1f || tmpl == null ? 0 : Mathf.Clamp(Mathf.CeilToInt(len / 12f), 1, maxSegs);
            float ang = Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg;
            for (int k = 0; k < n; k++)
            {
                while (segs.Count <= k) segs.Add(null);
                var s = segs[k];
                if (s == null || !s.activeInHierarchy) { s = SystemPool.Spawn(tmpl, (Vector3)a); segs[k] = s; }
                if (s == null) continue;
                var p = a + d * ((k + 0.5f) / n);
                s.transform.position = new Vector3(p.x, p.y, s.transform.position.z);
                s.transform.rotation = Quaternion.Euler(0f, 0f, ang);
                s.transform.localScale = new Vector3(len / n / 12f, (k % 2 == 0) ? 1f : -1f, 1f);
            }
            Clear(segs, n);
        }

        /// <summary>Despawn the segments from index <paramref name="from"/> on.</summary>
        public static void Clear(List<GameObject> segs, int from = 0)
        {
            for (int i = segs.Count - 1; i >= from; i--)
            {
                if (segs[i] != null && segs[i].activeInHierarchy) SystemPool.Despawn(segs[i]);
                segs.RemoveAt(i);
            }
        }

        public static Vector2 HeroChest(GameObject hero) { return (Vector2)hero.transform.position + new Vector2(0f, 8f); }
        public static float Angle(Vector2 from, Vector2 to) { var d = to - from; return Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg; }

        /// <summary>Distance from p to the segment a-b, and how far along it (0..1) the nearest point lies.</summary>
        public static float SegDist(Vector2 p, Vector2 a, Vector2 b, out float t)
        {
            var ab = b - a;
            t = Mathf.Clamp01(Vector2.Dot(p - a, ab) / Mathf.Max(ab.sqrMagnitude, 0.01f));
            return (a + ab * t - p).magnitude;
        }
    }
}
