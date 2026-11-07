using System;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Art;
    using CrawlFurther.Monsters;

    /// <summary>
    /// Ysveld's effect templates (art/out_ysveld, drawn by tools/sprites/ysveld_v2_rigs.py; offsets and origins are in its
    /// TIMING.md). Frost-tagged templates carry <see cref="YsvRimeFx"/>: a hit on the hero adds a frost pip.
    /// </summary>
    public static class YsveldFx
    {
        // the perk: floor ice, the blizzard's gusts, frost pips
        public static readonly GameObject[] FloeLay = new GameObject[YsvFloor.Variants], FloeMelt = new GameObject[YsvFloor.Variants];
        public static GameObject Ice, DeathIce, Gale, Puff, Bind;
        /// <summary>Frost pips on the hero: one or two of the three that pin (head meter); the ice skid at the feet.</summary>
        public static StatusOverlayDef[] IndRime;
        public static StatusOverlayDef IndIce;

        // tier 1
        public static GameObject Glob, Mote, Gust, Bite, Ram, IcicleMark, IcicleHit, SkidShard;
        public static exSpriteAnimClip GustClip, GustSleetClip, IcicleIceClip;
        // tier 2
        public static GameObject Fangs, Thread, Bead, Snap, StrumBead, StrumTwang, LurkBite, Snare, SnareSnap, SnareRing,
                                 Needle, Dive, Wake, WakeStreak, Shard, Crystal, CrystalBurst, CrystalRing, PipFlash, Cleave,
                                 EdgeIce, Plates, PlateBreak, Jab, HermitCrystal, HermitCrystalMelt, HermitCrystalFlash,
                                 TriangleLink, TriangleFrost, TrianglePulse;
        public static exSpriteAnimClip SnareIcedClip;
        // tier 3
        public static GameObject Impale, ImpaleDouble, EggSac, Wrap, Lash, LashPin, Spool, SpoolBead, SpoolSnap, TarBite, Hairs,
                                 BroodShake, ClawSnap, ClawGrab, GrabHold, GrabFling, CurlTrail, CurlSpin, CurlCrash, AuroraMote,
                                 Storm, AuroraRibbons, GlassSlash, GlassDouble, Cocoon, CocoonBurst, CocoonShatter, ShieldBlock,
                                 Breath, BlackBreath, TrainSweep, TrainSweepArt, BlackVeil, WraithClaw, Vortex, VortexBurst,
                                 ColdRing, Slam, SlamIce, Quake, Spike, GlacierRunner, BellyHit, BellySpray, Smash, RushHit,
                                 Sigil, Brand, ChallengeBang, GeodeSlam, HalfSlam, GeodeShard, GeodeCrack, PrismBolt, SlabFlash,
                                 BroodBite;
        public static readonly GameObject[] SpoolShow = new GameObject[3];
        public static exSpriteAnimClip AuroraLoopClip, AuroraFlareClip, PrismClip, LensClip;
        public static readonly exSpriteAnimClip[] CocoonCracks = new exSpriteAnimClip[3];
        // hero items
        public static GameObject BrideMark, BrideHit, HeroNova, HeroRequiem, HeroIcicleMark, HeroIcicleHit;

        /// <summary>Chain a spawn hook onto a template (keeps any hook already there).</summary>
        public static void Hook(GameObject tmpl, Action<GameObject> a)
        {
            if (tmpl == null) return;
            Action<GameObject> prev;
            FxFactory.OnSpawn.TryGetValue(tmpl, out prev);
            FxFactory.OnSpawn[tmpl] = i => { if (prev != null) prev(i); a(i); };
        }

        static void Frost(GameObject tmpl, bool coldSnap = false)
        {
            Hook(tmpl, i =>
            {
                var r = i.GetComponent<YsvRimeFx>() ?? i.AddComponent<YsvRimeFx>();
                r.coldSnap = coldSnap;
            });
        }

        static void Add<T>(GameObject tmpl, Action<T> arm = null) where T : Component
        {
            Hook(tmpl, i => { var c = i.GetComponent<T>() ?? i.AddComponent<T>(); if (arm != null) arm(c); });
        }

        /// <summary>Centred art: the cell centre sits on the effect origin.</summary>
        static void Center(GameObject go)
        {
            if (go == null) return;
            foreach (var s in go.GetComponents<exSprite>()) { s.anchor = exPlane.Anchor.MidCenter; s.offset = Vector2.zero; }
        }

        static GameObject Bolt(string name, string art, float speed, float life, float dmg, float knock, float w, float h,
                               Status st = null, float chance = 1f, bool destroyOnHit = true)
        {
            var go = FxKit.Projectile(name, "DFX_skelMageNewProjectile", art, "Fly", speed, life, dmg, knock, st, chance, destroyOnHit: destroyOnHit);
            if (go == null) return null;
            Center(go);
            Strike.Collider(go, w, h);
            if (destroyOnHit && Puff != null) FxFactory.SetContacts(go, destroyOnHit: true, spawnOnHit: Puff);
            return go;
        }

        static GameObject Melee(string name, float dmg, float knock, float w, float h, float life = 0.15f)
        {
            var go = AimedMelee.Rotating(FxKit.BodyHit(name, dmg, 0f, knock, life));
            Strike.HitBox(go, w, h);
            return go;
        }

        static exSpriteAnimClip Loop(string sheet, string anim, string clip)
        {
            var sh = SpriteSheets.Get(sheet);
            return sh != null && sh.Has(anim) ? new ClipBuilder(sh, anim, clip).Loop().Build() : null;
        }

        /// <summary>A clip of `first`, then `mid` x n, then `end` (snares, crystals, vortices).</summary>
        static void Life(GameObject go, string sheet, string first, string mid, int n, string end, string clipName)
        {
            if (go == null) return;
            var sh = SpriteSheets.Get(sheet);
            if (sh == null) return;
            var cb = new ClipBuilder(sh, first, clipName).Once().Then(mid, n);
            if (end != null) cb.Then(end);
            FxFactory.Reskin(go, cb.Build(), sh);
        }

        /// <summary>A visual drawn at floor depth (the code sets its z): its own depth sorting is removed.</summary>
        static GameObject FloorVisual(string name, string sheet, exSpriteAnimClip clip, bool loop)
        {
            var sh = SpriteSheets.Get(sheet);
            if (sh == null || clip == null) return null;
            var go = FxFactory.Visual(name, sh, clip, loop);
            if (go == null) return null;
            Center(go);
            var dh = go.GetComponent<DepthHandler>();
            if (dh != null) UnityEngine.Object.DestroyImmediate(dh);
            FxKit.NoTint(go);
            FxFactory.SetEffect(go, destroyOnAnimEnd: !loop, canFlip: false, freeRotate: false);
            return go;
        }

        /// <summary>A telegraphed icicle: the Fall art plays on the floor, then the Shatter hit lands on the same spot.</summary>
        static GameObject Icicle(string name, float dmg, out GameObject hit)
        {
            hit = FxKit.TimedHit(name + "Hit", "skydropExplode", "FxYsvIcicle", "Shatter", 0, 2, dmg, 0.6f, canFlip: false);
            if (hit != null)
            {
                FxFactory.SetDamage(hit, dmg, knockback: 0.6f, stun: 0f, collisionAtStart: false);
                Strike.Ground(hit, "FxYsvIcicle", 16, 60, 18f, 10f);      // DamageBase: the hero's feet inside an 18 x 10 oval
                Frost(hit);
            }
            var mark = FxKit.Inert(name, "FxYsvIcicle", "Fall", destroyOnAnimEnd: true, spawnOnDestroy: hit);
            Strike.ArtAt(mark, "FxYsvIcicle", 16, 60);
            return mark;
        }

        /// <summary>An invisible spawner that drops copies of a template in a ring (+ optionally one in the middle, later).</summary>
        static GameObject Ring(string name, GameObject tmpl, int count, float radius, float centreDelay, bool coldRead = false)
        {
            var go = FxKit.Inert(name, null, null, destroyOnAnimEnd: false, life: 1.2f);
            Add<YsvRingFx>(go, r => r.Setup(tmpl, count, radius, centreDelay, coldRead));
            return go;
        }

        static GameObject Spawner(string name, float life) { return FxKit.Inert(name, null, null, destroyOnAnimEnd: false, life: life); }

        public static void Build()
        {
            var slow = FxFactory.GetStatus("StatusLavaSteveGoo");
            IndRime = new[]
            {
                ModStatus.Indicator("ModIndRime1", "FxCommonIndRime", "One", 1f, OverlayAt.Head),
                ModStatus.Indicator("ModIndRime2", "FxCommonIndRime", "Two", 1f, OverlayAt.Head),
            };
            IndIce = ModStatus.Indicator("ModIndIce", "FxCommonIndIce", "Loop", -2f, OverlayAt.Feet);
            BuildFloor();
            Puff = FxKit.Visual("ModYsvPuff", "FxYsvPuff", "Play");
            Center(Puff);
            Bind = FxKit.Visual("ModYsvBind", "FxYsvBind", "Bind");
            Strike.ArtAt(Bind, "FxYsvBind", 14, 23);
            BuildT1(slow);
            BuildT2();
            BuildT3A();
            BuildT3B();
            BuildHeroItems(slow);
            Plugin.Log.LogInfo("Ysveld FX templates built");
        }

        // ---------------------------------------------------------------------------------------------- the perk
        static void BuildFloor()
        {
            // every slab is a FxYsvFloe variant drawn at floor depth, laid and thawed by YsvFloor
            var fsh = SpriteSheets.Get("FxYsvFloe");
            var forms = new[] { "Form0", "Form1", "Form2", "Form3" };
            var idles = new[] { "Idle0", "Idle1", "Idle2", "Idle3" };
            var melts = new[] { "Melt0", "Melt1", "Melt2", "Melt3" };
            for (int v = 0; v < YsvFloor.Variants; v++)
            {
                if (fsh == null || !fsh.Has(forms[v]) || !fsh.Has(idles[v]) || !fsh.Has(melts[v])) break;
                var lay = FxFactory.Visual("ModYsvFloe" + v, fsh, new ClipBuilder(fsh, forms[v], "ModYsvFloeLay" + v).Once()
                                           .Then(idles[v], 400).Build(), false);
                var melt = FxFactory.Visual("ModYsvFloeMelt" + v, fsh, new ClipBuilder(fsh, melts[v], "ModYsvFloeMelt" + v).Once().Build(), false);
                foreach (var t in new[] { lay, melt })
                {
                    if (t == null) continue;
                    Center(t);
                    var dh = t.GetComponent<DepthHandler>();
                    if (dh != null) UnityEngine.Object.DestroyImmediate(dh);   // YsvFloor sets the floor depth itself
                    FxKit.NoTint(t);
                }
                if (lay != null) FxFactory.SetEffect(lay, destroyOnAnimEnd: false, canFlip: false, freeRotate: false);
                if (melt != null) FxFactory.SetEffect(melt, destroyOnAnimEnd: true, canFlip: false, freeRotate: false);
                FloeLay[v] = lay; FloeMelt[v] = melt;
            }
            Ice = Spawner("ModYsvIce", 0.2f);
            Add<YsvIceSpawn>(Ice, z => z.Arm(1, YsvFloor.KitIceLife));
            DeathIce = Spawner("ModYsvDeathIce", 0.2f);
            Add<YsvIceSpawn>(DeathIce, z => z.Arm(3, YsvFloor.DeathIceLife));
            Gale = FxKit.Visual("ModYsvGale", "FxYsvGale", "Blow", loop: true, lifetime: YsvFloor.GaleTime);
            if (Gale != null)
            {
                Center(Gale);
                var dh = Gale.GetComponent<DepthHandler>();
                if (dh != null) UnityEngine.Object.DestroyImmediate(dh);      // snow in the air: in front of everyone
                FxFactory.SetEffect(Gale, destroyOnAnimEnd: false, destroyAfter: YsvFloor.GaleTime, canFlip: false, freeRotate: false);
                Add<YsvGaleFx>(Gale, g => g.Arm());
                FxKit.NoTint(Gale);
            }
        }

        // ---------------------------------------------------------------------------------------------- tier 1
        static void BuildT1(Status slow)
        {
            Glob = Bolt("ModYsvGlob", "FxYsvGlob", 150f, 0.7f, 0.7f, 0.3f, 9f, 9f, slow, 0.6f);
            Mote = Bolt("ModYsvMote", "FxYsvMote", 170f, 0.5f, 0.6f, 0.2f, 7f, 7f);
            Gust = Bolt("ModYsvGust", "FxYsvGust", 150f, 0.45f, 0.5f, 2.4f, 14f, 22f, destroyOnHit: false);
            GustClip = Loop("FxYsvGust", "Fly", "ModYsvGustFly");
            GustSleetClip = Loop("FxYsvGust", "Sleet", "ModYsvGustSleet");
            Add<YsvGustFx>(Gust);
            Bite = Melee("ModYsvBite", 0.8f, 0.5f, 12f, 12f);
            Frost(Bite, coldSnap: true);
            Ram = Melee("ModYsvRam", 0.9f, 1.1f, 12f, 14f);
            IcicleMark = Icicle("ModYsvIcicle", 0.9f, out IcicleHit);
            var ish = SpriteSheets.Get("FxYsvIcicle");
            if (ish != null && ish.Has("FallIce")) IcicleIceClip = new ClipBuilder(ish, "FallIce", "ModYsvIcicleFallIce").Once().Build();
            Add<YsvIcicleFx>(IcicleMark, f => f.mark = true);
            Add<YsvIcicleFx>(IcicleHit, f => f.mark = false);
            SkidShard = Bolt("ModYsvSkidShard", "FxYsvSkidShard", 130f, 0.6f, 0.4f, 0.3f, 8f, 5f);
            Add<YsvSkidFx>(SkidShard);
            foreach (var t in new[] { Glob, Mote, Gust, Ram, SkidShard }) Frost(t);
        }

        // ---------------------------------------------------------------------------------------------- tier 2
        static void BuildT2()
        {
            // Silk Weaver: frost fangs, the silk line and its Strum beads
            Fangs = Melee("ModYsvFangs", 1.0f, 0.6f, 16f, 14f);
            Thread = Bolt("ModYsvThread", "FxYsvThread", 230f, 0.6f, 0.3f, 0.1f, 10f, 8f);
            Add<YsvThreadFx>(Thread);
            Bead = FxKit.Visual("ModYsvSilkBead", "FxYsvThread", "Bead", loop: true);
            Center(Bead);
            Snap = FxKit.Visual("ModYsvSilkSnap", "FxYsvThread", "Snap");
            Center(Snap);
            StrumBead = FxKit.Visual("ModYsvStrumBead", "FxYsvStrumBead", "Run", loop: true);
            Center(StrumBead);
            StrumTwang = FxKit.Visual("ModYsvStrumTwang", "FxYsvStrumBead", "Twang");
            Center(StrumTwang);

            // Rime Lurker: the trapdoor bite and its snares (Set in Ice: the Iced loop)
            LurkBite = Melee("ModYsvLurkBite", 1.1f, 0.6f, 14f, 12f);
            Snare = FxKit.Inert("ModYsvSnare", "FxYsvSnare", "Land", destroyOnAnimEnd: true);
            Life(Snare, "FxYsvSnare", "Land", "Idle", 7, "Fade", "ModYsvSnareLife");      // 0.3 + 4.2 + 0.32 s off the ice
            Strike.ArtAt(Snare, "FxYsvSnare", 10, 15);
            Add<YsvSnareFx>(Snare, z => z.Arm());
            SnareIcedClip = Loop("FxYsvSnare", "Iced", "ModYsvSnareIced");
            SnareSnap = FxKit.Visual("ModYsvSnareSnap", "FxYsvSnare", "Snap");
            Strike.ArtAt(SnareSnap, "FxYsvSnare", 10, 15);
            SnareRing = Ring("ModYsvSnareRing", Snare, 2, 14f, -1f);

            // Silkmoth: silk needles and the dive that leaves a Frost Wake
            Needle = Bolt("ModYsvNeedle", "FxYsvNeedle", 220f, 0.55f, 0.8f, 0.2f, 10f, 5f);
            Dive = Melee("ModYsvDive", 0.9f, 0.9f, 20f, 14f, 0.3f);
            Wake = Spawner("ModYsvWake", 0.5f);
            Add<YsvWakeFx>(Wake);
            var wsh = SpriteSheets.Get("FxYsvFrostWake");
            WakeStreak = wsh != null ? FloorVisual("ModYsvWakeStreak", "FxYsvFrostWake", new ClipBuilder(wsh, "Streak", "ModYsvWakeStreak").Once().Build(), false) : null;

            // Veil Witch: the ice shard, and Cold Read's crystals (1 + the hero's pips, max 4) that shatter after 1 s
            Shard = Bolt("ModYsvShard", "FxYsvShard", 210f, 0.8f, 0.9f, 0.4f, 12f, 6f);
            CrystalBurst = FxKit.TimedHit("ModYsvCrystalBurst", "skydropExplode", "FxYsvCrystal", "Shatter", 0, 2, 1.0f, 0.6f, canFlip: false);
            if (CrystalBurst != null)
            {
                FxFactory.SetDamage(CrystalBurst, 1.0f, knockback: 0.6f, stun: 0f, collisionAtStart: false);
                Strike.Ground(CrystalBurst, "FxYsvCrystal", 18, 26, 18f, 10f);
            }
            Crystal = FxKit.Inert("ModYsvCrystal", "FxYsvCrystal", "Grow", destroyOnAnimEnd: true, spawnOnDestroy: CrystalBurst);
            Strike.ArtAt(Crystal, "FxYsvCrystal", 18, 26);
            CrystalRing = Ring("ModYsvCrystalRing", Crystal, 1, 20f, -1f, coldRead: true);
            PipFlash = FxKit.Visual("ModYsvPipFlash", "FxYsvPipFlash", "Flash");
            Strike.ArtAt(PipFlash, "FxYsvPipFlash", 8, 8);

            // Rime Knight: the cleave (its own ice crescent; OrcSwipe gives the layer and capsule) freezes the floor ahead
            Cleave = AimedMelee.Rotating(FxKit.TimedHit("ModYsvCleave", "OrcSwipe", "FxYsvCleave", "Slash", 0, 1, 1.2f, 0.9f));
            Strike.ArtAt(Cleave, "FxYsvCleave", 16, 24);
            EdgeIce = Spawner("ModYsvEdgeIce", 0.2f);
            Add<YsvIceSpawn>(EdgeIce, z => z.Arm(2, 6f));
            Plates = FxKit.Visual("ModYsvPlates", "FxYsvPlates", "Orbit", loop: true);
            Strike.ArtAt(Plates, "FxYsvPlates", 14, 21);
            PlateBreak = FxKit.Visual("ModYsvPlateBreak", "FxYsvPlateBreak", "Play");
            Strike.ArtAt(PlateBreak, "FxYsvPlateBreak", 15, 23);

            // Shard Hermit: the staff thrust, the planted crystals and the Triangle between them
            Jab = Melee("ModYsvJab", 0.9f, 0.6f, 16f, 10f);
            var hsh = SpriteSheets.Get("FxYsvHermitCrystal");
            if (hsh != null)
            {
                HermitCrystal = FxFactory.Visual("ModYsvHermitCrystal", hsh, new ClipBuilder(hsh, "Grow", "ModYsvHermitCrystalLife").Once()
                                                 .Then("Idle", 45).Build(), false);
                if (HermitCrystal != null) FxFactory.SetEffect(HermitCrystal, destroyOnAnimEnd: true, canFlip: false, freeRotate: false);
                Strike.ArtAt(HermitCrystal, "FxYsvHermitCrystal", 9, 22);
            }
            HermitCrystalMelt = FxKit.Visual("ModYsvHermitCrystalMelt", "FxYsvHermitCrystal", "Melt");
            Strike.ArtAt(HermitCrystalMelt, "FxYsvHermitCrystal", 9, 22);
            HermitCrystalFlash = FxKit.Visual("ModYsvHermitCrystalFlash", "FxYsvHermitCrystal", "Flash");
            Strike.ArtAt(HermitCrystalFlash, "FxYsvHermitCrystal", 9, 22);
            var tsh = SpriteSheets.Get("FxYsvTriangle");
            if (tsh != null)
            {
                TriangleLink = FloorVisual("ModYsvTriangleLink", "FxYsvTriangle", new ClipBuilder(tsh, "Link", "ModYsvTriangleLink").Loop().Build(), true);
                TriangleFrost = FloorVisual("ModYsvTriangleFrost", "FxYsvTriangle",
                                            new ClipBuilder(tsh, "Form", "ModYsvTriangleFrost").Once().Then("Frost", 200).Build(), false);
                TrianglePulse = FxKit.Visual("ModYsvTrianglePulse", "FxYsvTriangle", "Pulse");
                Center(TrianglePulse);
            }

            foreach (var t in new[] { Fangs, Thread, LurkBite, Needle, Dive, Shard, CrystalBurst, Cleave, Jab }) Frost(t);
        }

        // ---------------------------------------------------------------------------------------------- tier 3: Weaver and Lurker lines, Silkmoth line
        static void BuildT3A()
        {
            // Widow Matron: impale (doubled after a Wrap), egg sacs, the silk wrap on the hero
            Impale = Melee("ModYsvImpale", 1.4f, 1.0f, 22f, 14f, 0.18f);
            ImpaleDouble = Melee("ModYsvImpaleDouble", 2.8f, 1.4f, 22f, 14f, 0.18f);
            Wrap = FxKit.Visual("ModYsvWrap", "FxYsvWrap", "Loop", loop: true, lifetime: MatronWrap.PinTime);
            Strike.ArtAt(Wrap, "FxYsvWrap", 10, 16);

            // Loom Widow: the silk whip (and the whip that pins at a full spool), the spool line and its beads
            Lash = Melee("ModYsvLash", 1.2f, 0.8f, 24f, 12f);
            LashPin = Melee("ModYsvLashPin", 1.2f, 0.8f, 24f, 12f);
            Add<YsvPinFx>(LashPin);
            Spool = Bolt("ModYsvSpool", "FxYsvSpool", 210f, 0.7f, 0.3f, 0.1f, 10f, 8f);
            Add<YsvSpoolHookFx>(Spool);
            SpoolBead = FxKit.Visual("ModYsvSpoolBead", "FxYsvSpool", "Bead", loop: true);
            Center(SpoolBead);
            SpoolSnap = FxKit.Visual("ModYsvSpoolSnap", "FxYsvSpool", "Snap");
            Center(SpoolSnap);
            for (int i = 0; i < 3; i++)
            {
                SpoolShow[i] = FxKit.Visual("ModYsvSpoolS" + (i + 1), "FxYsvSpool", "S" + (i + 1), loop: true);
                Center(SpoolShow[i]);
            }

            // Hoarfrost Tarantula: the crushing bite and the frozen hairs it flicks (40 px)
            TarBite = Melee("ModYsvTarBite", 1.4f, 0.8f, 16f, 12f);
            Hairs = Bolt("ModYsvHairs", "FxYsvHairs", 200f, 0.22f, 0.9f, 0.3f, 9f, 6f);

            // Hoarclaw: pincer snap, the seize, and the Curling Stone slide
            ClawSnap = Melee("ModYsvClawSnap", 1.3f, 0.7f, 16f, 14f);
            ClawGrab = Melee("ModYsvClawGrab", 0.5f, 0f, 16f, 14f, 0.2f);
            Add<YsvGrabFx>(ClawGrab);
            GrabHold = FxKit.Visual("ModYsvGrabHold", "FxYsvGrab", "Hold", loop: true);
            Strike.ArtAt(GrabHold, "FxYsvGrab", 15, 19);
            GrabFling = FxKit.Visual("ModYsvGrabFling", "FxYsvGrab", "Fling");
            Strike.ArtAt(GrabFling, "FxYsvGrab", 15, 19);
            CurlTrail = FxKit.Visual("ModYsvCurlTrail", "FxYsvCurlTrail", "Trail");
            Strike.ArtAt(CurlTrail, "FxYsvCurlTrail", 14, 21);
            CurlSpin = FxKit.Visual("ModYsvCurlSpin", "FxYsvCurlTrail", "Spin", loop: true);
            Strike.ArtAt(CurlSpin, "FxYsvCurlTrail", 14, 21);
            CurlCrash = FxKit.Visual("ModYsvCurlCrash", "FxYsvCurlTrail", "Crash");
            Strike.ArtAt(CurlCrash, "FxYsvCurlTrail", 14, 21);

            // Pale Empress: aurora motes, the homing blizzard (~3.4 s), the Storm Queen ribbons
            AuroraMote = Bolt("ModYsvAuroraMote", "FxYsvAuroraMote", 180f, 0.6f, 1.0f, 0.3f, 8f, 8f);
            Storm = FxKit.Cloud("ModYsvStorm", "FxYsvStorm", "Loop", 0f, 0.35f, 0.5f, null, 0f);
            if (Storm != null)
            {
                var ssh = SpriteSheets.Get("FxYsvStorm");
                FxFactory.Reskin(Storm, new ClipBuilder(ssh, "Loop", "ModYsvStormLife").Once().Then("Loop", 6).Build(), ssh);
                FxFactory.SetMotion(Storm, 0f, enabled: false);
                Center(Storm);
                Strike.Collider(Storm, 24f, 16f);
                Add<YsvHomingFx>(Storm, h => h.Reset());
            }
            AuroraRibbons = FxKit.Visual("ModYsvAurora", "FxYsvAurora", "Loop", loop: true);
            Strike.ArtAt(AuroraRibbons, "FxYsvAurora", 13, 14);
            AuroraLoopClip = Loop("FxYsvAurora", "Loop", "ModYsvAuroraLoop");
            AuroraFlareClip = Loop("FxYsvAurora", "Flare", "ModYsvAuroraFlare");

            // Glasswing: the glass scythe (doubled after a hatch) and the Glass Cocoon
            GlassSlash = Melee("ModYsvGlassSlash", 1.3f, 0.6f, 16f, 14f);
            GlassDouble = Melee("ModYsvGlassDouble", 2.6f, 1.2f, 18f, 16f);
            var csh = SpriteSheets.Get("FxYsvCocoon");
            if (csh != null)
            {
                Cocoon = FxFactory.Visual("ModYsvCocoon", csh, new ClipBuilder(csh, "Grow", "ModYsvCocoonGrow").Once().Then("C0", 2).Build(), false);
                if (Cocoon != null) FxFactory.SetEffect(Cocoon, destroyOnAnimEnd: false, canFlip: false, freeRotate: false);
                Strike.ArtAt(Cocoon, "FxYsvCocoon", 18, 34);
                var cracks = new[] { "C1", "C2", "C3" };
                for (int i = 0; i < 3; i++)
                    if (csh.Has(cracks[i])) CocoonCracks[i] = new ClipBuilder(csh, cracks[i], "ModYsvCocoon" + cracks[i]).Loop().Build();
            }
            CocoonBurst = FxKit.Visual("ModYsvCocoonBurst", "FxYsvCocoon", "Burst");
            Strike.ArtAt(CocoonBurst, "FxYsvCocoon", 18, 34);
            CocoonShatter = FxKit.Visual("ModYsvCocoonShatter", "FxYsvCocoon", "Shatter");
            Strike.ArtAt(CocoonShatter, "FxYsvCocoon", 18, 34);
            ShieldBlock = FxKit.Visual("ModYsvShieldBlock", "FxYsvShieldBlock", "Play");
            Center(ShieldBlock);

            foreach (var t in new[] { Impale, ImpaleDouble, Lash, LashPin, TarBite, Hairs, ClawSnap, AuroraMote, Storm, GlassSlash, GlassDouble }) Frost(t);
        }

        // ---------------------------------------------------------------------------------------------- tier 3: Witch, Knight and Hermit lines
        static void BuildT3B()
        {
            // Winter Bride: frost breath (twice the reach in black when widowed), the Train Sweep, the black veil
            Breath = FxKit.Cloud("ModYsvBreath", "FxYsvBreath", "Puff", 110f, 0.45f, 0.35f, null, 0f);
            Center(Breath);
            Strike.Collider(Breath, 18f, 14f);
            BlackBreath = FxKit.Cloud("ModYsvBlackBreath", "FxYsvBreath", "Black", 110f, 0.45f, 0.35f, null, 0f);
            if (BlackBreath != null)
            {
                var bsh = SpriteSheets.Get("FxYsvBreath");
                FxFactory.Reskin(BlackBreath, new ClipBuilder(bsh, "Black", "ModYsvBlackBreathLife").Once().Repeat(2).Build(), bsh);
                Center(BlackBreath);
                Strike.Collider(BlackBreath, 18f, 14f);
            }
            TrainSweep = Spawner("ModYsvTrainSweep", 0.5f);
            Add<YsvSweepFx>(TrainSweep);
            TrainSweepArt = FxKit.Visual("ModYsvTrainSweepArt", "FxYsvTrainSweep", "Sweep");
            Strike.ArtAt(TrainSweepArt, "FxYsvTrainSweep", 41, 28);
            if (TrainSweepArt != null) FxFactory.SetEffect(TrainSweepArt, destroyOnAnimEnd: true, canFlip: false, freeRotate: false);
            BlackVeil = FxKit.Visual("ModYsvBlackVeil", "FxYsvBlackVeil", "Play");
            Strike.ArtAt(BlackVeil, "FxYsvBlackVeil", 20, 42);

            // Snow Wraith: the claw rake, the maelstrom, the Cold Presence ring
            WraithClaw = Melee("ModYsvWraithClaw", 1.2f, 0.7f, 16f, 16f);
            VortexBurst = FxKit.TimedHit("ModYsvVortexBurst", "skydropExplode", "FxYsvVortex", "Burst", 1, 4, 1.3f, 1.0f, canFlip: false);
            if (VortexBurst != null)
            {
                FxFactory.SetDamage(VortexBurst, 1.3f, knockback: 1.0f, stun: 0f, collisionAtStart: false);
                Strike.Ground(VortexBurst, "FxYsvVortex", 21, 24, 22f, 12f);
            }
            Vortex = FxKit.Inert("ModYsvVortex", "FxYsvVortex", "Open", destroyOnAnimEnd: true, spawnOnDestroy: VortexBurst);
            Life(Vortex, "FxYsvVortex", "Open", "Spin", 7, null, "ModYsvVortexLife");      // 0.24 + 1.96 s, then the burst
            Strike.ArtAt(Vortex, "FxYsvVortex", 21, 24);
            Add<YsvVortexFx>(Vortex, z => z.Arm());
            var rsh = SpriteSheets.Get("FxYsvColdRing");
            ColdRing = rsh != null ? FxFactory.Visual("ModYsvColdRing", rsh, new ClipBuilder(rsh, "Loop", "ModYsvColdRing").Loop().Build(), true) : null;
            Strike.ArtAt(ColdRing, "FxYsvColdRing", 34, 16);
            if (ColdRing != null) FxKit.NoTint(ColdRing);

            // Rime Colossus: the slam and its quake (+0.3 on ice), Glacier Run's spikes, road and belly slide
            Slam = Melee("ModYsvSlam", 1.4f, 1.4f, 20f, 16f, 0.2f);
            SlamIce = Melee("ModYsvSlamIce", 1.7f, 1.4f, 20f, 16f, 0.2f);
            Quake = FxKit.TimedHit("ModYsvQuake", "TrollGroundPoundBigShockwave", "FxYsvQuake", "Play", 0, 3, 0.6f, 1.0f, canFlip: false);
            Strike.Ground(Quake, "FxYsvQuake", 26, 12, 46f, 18f);
            Spike = FxKit.TimedHit("ModYsvSpike", "skydropExplode", "FxYsvSpike", "Play", 1, 4, 0.9f, 0.8f, canFlip: false);
            if (Spike != null)
            {
                FxFactory.SetDamage(Spike, 0.9f, knockback: 0.8f, stun: 0f, collisionAtStart: false);
                Strike.Ground(Spike, "FxYsvSpike", 9, 15, 16f, 9f);
                FxFactory.SetEffect(Spike, destroyOnAnimEnd: true, spawnOnDestroy: Ice, canFlip: false, freeRotate: false);   // paves the road
            }
            GlacierRunner = FxFactory.Clone("WebDropper", "ModYsvGlacierRunner");
            if (GlacierRunner != null)
            {
                FxFactory.SetEffect(GlacierRunner, destroyOnAnimEnd: false, destroyAfter: 0.5f, freeRotate: true);
                FxFactory.SetMotion(GlacierRunner, 210f, trail: Spike, trailDist: 19f, collide: true);
            }
            BellyHit = Melee("ModYsvBellyHit", 1.4f, 1.6f, 26f, 18f, 0.45f);
            BellySpray = FxKit.Visual("ModYsvBellySpray", "FxYsvBellySlide", "Spray", loop: true, lifetime: 0.45f);
            Strike.ArtAt(BellySpray, "FxYsvBellySlide", 22, 12);

            // Rime Warden: the mace smash, the Shield Rush, the Challenge sigil and brand
            Smash = Melee("ModYsvSmash", 1.4f, 1.2f, 18f, 14f, 0.18f);
            RushHit = Melee("ModYsvRushHit", 1.1f, 1.6f, 20f, 18f, 0.3f);
            Sigil = FxKit.Visual("ModYsvSigil", "FxYsvChallenge", "Sigil", loop: true);
            Strike.ArtAt(Sigil, "FxYsvChallenge", 8, 14);
            Brand = FxKit.Visual("ModYsvBrand", "FxYsvChallenge", "Brand", loop: true);
            Strike.ArtAt(Brand, "FxYsvChallenge", 8, 14);
            ChallengeBang = FxKit.Visual("ModYsvChallengeBang", "FxYsvChallenge", "Bang");
            Strike.ArtAt(ChallengeBang, "FxYsvChallenge", 8, 14);

            // The Geode: dome slam (a smaller one as a half), Geode Burst's crystals, the split
            GeodeSlam = Melee("ModYsvGeodeSlam", 1.4f, 1.3f, 22f, 14f, 0.18f);
            HalfSlam = Melee("ModYsvHalfSlam", 1.1f, 1.0f, 16f, 12f, 0.18f);
            GeodeShard = Bolt("ModYsvGeodeShard", "FxYsvGeodeShard", 200f, 0.7f, 0.9f, 0.4f, 9f, 6f);
            GeodeCrack = FxKit.Visual("ModYsvGeodeCrack", "FxYsvGeodeCrack", "Play");
            Strike.ArtAt(GeodeCrack, "FxYsvGeodeCrack", 26, 36);

            // Prism Oracle: the prism bolt (Ice Lens) and the Sunburst's slab flashes
            PrismBolt = Bolt("ModYsvPrismBolt", "FxYsvPrismBolt", 190f, 0.8f, 1.2f, 0.3f, 9f, 7f);
            PrismClip = Loop("FxYsvPrismBolt", "Fly", "ModYsvPrismFly");
            LensClip = Loop("FxYsvPrismBolt", "Lens", "ModYsvPrismLens");
            Add<YsvLensFx>(PrismBolt);
            var fsh = SpriteSheets.Get("FxYsvSlabFlash");
            SlabFlash = fsh != null ? FloorVisual("ModYsvSlabFlash", "FxYsvSlabFlash", new ClipBuilder(fsh, "Flash", "ModYsvSlabFlash").Once().Build(), false) : null;

            BroodBite = Melee("ModYsvBroodBite", 0.4f, 0.3f, 9f, 9f, 0.12f);

            foreach (var t in new[] { Breath, BlackBreath, WraithClaw, VortexBurst, Slam, SlamIce, Quake, Spike, BellyHit, Smash, RushHit,
                                      GeodeSlam, HalfSlam, GeodeShard, PrismBolt, BroodBite }) Frost(t);
        }

        // ---------------------------------------------------------------------------------------------- the god's items
        static void BuildHeroItems(Status slow)
        {
            BrideMark = Icicle("ModYsvRequiemIcicle", 1.2f, out BrideHit);
            HeroIcicleHit = FxKit.Weakened(BrideHit, "ModYsvHeroIcicleHit", 0.6f);              // 1.2 -> 0.72
            HeroIcicleMark = MonsterFactory.ClonePrefab(BrideMark, "ModYsvHeroIcicle");
            FxFactory.Templates["ModYsvHeroIcicle"] = HeroIcicleMark;
            FxFactory.SetEffect(HeroIcicleMark, destroyOnAnimEnd: true, spawnOnDestroy: HeroIcicleHit, freeRotate: false);
            HeroRequiem = Ring("ModYsvHeroRequiem", HeroIcicleMark, 6, 24f, -1f);
            HeroNova = FxKit.TimedHit("ModYsvHeroNova", "TrollGroundPoundBigShockwave", "FxYsvNova", "Play", 0, 4, 0f, 0.6f, slow, 1f, canFlip: false);
            if (HeroNova != null) Strike.Ground(HeroNova, "FxYsvNova", 26, 12, 48f, 20f);   // DamageBase: monsters' feet inside 48 x 20
        }
    }
}
