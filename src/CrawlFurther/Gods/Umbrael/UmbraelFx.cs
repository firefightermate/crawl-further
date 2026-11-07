using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Art;
    using CrawlFurther.Monsters;
    using CrawlFurther.Content.Gods.Sylvene;

    /// <summary>
    /// Umbrael's effect templates (art/out_umbrael, origins in its TIMING.md). Every basic attack has a half-strength echo
    /// (<see cref="UmbraelEcho"/> fires it) and a full-strength one for echoes that land inside a Glassmoth's glitter.
    /// </summary>
    public static class UmbraelFx
    {
        // ---- shared by other packs (items, Jinx, custom gods)
        public static GameObject SwapFlash, DecoySpawner, DecoyBurst, RingShard, EchoSmear;

        // ---- echoes
        public static GameObject EchoMark, EchoQuick, EchoSparkle, EchoBite;

        // ---- tier 1
        public static GameObject ImpClaw, SmokeStep, MirrorShard, Darkness, LurkerBite, LurkerAmbush, LurkEyes;
        public static exSpriteAnimClip ShardHot;

        // ---- tier 2
        public static GameObject TwinCut, TwinSwapCut, Nail, Pin, Pinned, NailRake, ReflectBolt, Pane, PaneShatter, PaneFlash, CoilBite,
                                 CoilSlither, GloamPool, DuskEdge, MothScale, Glitter, SandShard, RewindMark, RewindSnap;
        /// <summary>The creeping edge of growing darkness, one loop per radius (16, 20, 24, 28, 32 px).</summary>
        public static exSpriteAnimClip[] DuskEdges;
        public static readonly int[] DuskRadii = { 16, 20, 24, 28, 32 };

        // ---- tier 3
        public static GameObject KingCleave, Crown, CrownShade, Scissor, PaleHalf, PaleCut, Crack, RejoinHit, RejoinCut, Feather, PrismFeather,
                                 LightThread, Quill, Caltrop, ShakeNail, GazeBeam, GazeEnd, Blackout, EyeFlash, WidowFang, GlazeWeb,
                                 GlazeCrack, WyrmBite, WyrmGlassBite, Corona, CoronaHit, EclipseBurst, VenomBite, InkUnder, ArgusScale,
                                 ArgusCatch, SwarmBite, SurgeBite, SwarmGlint, SwarmGhost, GhostBite, PendulumSpin, BladeHit,
                                 Tick, TimeRing, SandBall, SandGlass, SandShadow, SandColumn;
        public static exSpriteAnimClip ShadeRise, ShadeIdle, ShadeSwing, ShadeFade, PaleIdle, PaleRush, PaleDrift, PaleCutClip, InkLoop, InkFade, FeatherSplit;
        public static exSpriteAnimClip[] SandFill;
        public static StatusOverlayDef GlazeInd;
        public static StatusOverlayDef[] StuckInd;

        /// <summary>Attack template -> its full-strength echo (the half-strength one is <see cref="FxKit.FindEcho"/>).</summary>
        public static readonly Dictionary<GameObject, GameObject> FullEcho = new Dictionary<GameObject, GameObject>();

        /// <summary>Chain a spawn hook onto a template (keeps any hook already there).</summary>
        static void Hook(GameObject tmpl, System.Action<GameObject> a)
        {
            if (tmpl == null) return;
            System.Action<GameObject> prev;
            FxFactory.OnSpawn.TryGetValue(tmpl, out prev);
            FxFactory.OnSpawn[tmpl] = i => { if (prev != null) prev(i); a(i); };
        }

        /// <summary>Play <paramref name="clip"/> on an effect instance (added to its animation once).</summary>
        public static void Play(GameObject fx, exSpriteAnimClip clip)
        {
            var an = fx != null ? fx.GetComponent<exSpriteAnimation>() : null;
            if (an == null || clip == null) return;
            if (an.GetAnimation(clip.name) == null) an.AddAnimation(clip);
            an.Play(clip.name);
        }

        /// <summary>Stretch a 32 px line effect (origin at its left end) from <paramref name="a"/> to <paramref name="b"/>.</summary>
        public static void Span(GameObject line, Vector2 a, Vector2 b)
        {
            if (line == null) return;
            var d = b - a;
            line.transform.position = new Vector3(a.x, a.y, line.transform.position.z);
            line.transform.rotation = Quaternion.Euler(0f, 0f, Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg);
            line.transform.localScale = new Vector3(Mathf.Max(0.05f, d.magnitude / 32f), 1f, 1f);
        }

        static void Dark(GameObject tmpl, float radius)
        {
            Hook(tmpl, i => { var d = i.GetComponent<DarknessFx>() ?? i.AddComponent<DarknessFx>(); d.Reset(radius); });
        }

        static exSpriteAnimClip Clip(string sheet, string anim, string name, bool loop)
        {
            var sh = SpriteSheets.Get(sheet);
            if (sh == null || !sh.Has(anim)) return null;
            var b = new ClipBuilder(sh, anim, name);
            return (loop ? b.Loop() : b.Once()).Build();
        }

        /// <summary>A pure visual placed with its sheet origin on the spawn point.</summary>
        static GameObject Vis(string name, string sheet, string anim, int gx, int gy, bool loop = false, float life = 0f)
        {
            var go = FxKit.Visual(name, sheet, anim, loop, life);
            if (go != null) Strike.ArtAt(go, sheet, gx, gy);
            return go;
        }

        static GameObject Bite(string name, float damage, float knock, float w, float h, Status status = null, float chance = 1f)
        {
            var go = AimedMelee.Rotating(FxFactory.Clone("DamageGiantRatAttack", name));
            FxFactory.SetDamage(go, damage, knockback: knock, status: status, statusChance: chance);
            Strike.HitBox(go, w, h);
            return go;
        }

        static GameObject Missile(string name, string sheet, float speed, float life, float damage, float knock, float w, float h, bool bounce = false,
                               Status status = null, float chance = 1f)
        {
            var go = FxKit.Projectile(name, "DFX_skelMageNewProjectile", sheet, "Fly", speed, life, damage, knock, status, chance);
            if (go == null) return null;
            if (bounce) FxFactory.SetMotion(go, speed, collide: true, bounce: 1f);
            Strike.HitBox(go, w, h);
            return go;
        }

        public static void Build()
        {
            var daze = FxFactory.GetStatus("StatusDizzy");
            var root = FxFactory.GetStatus("StatusStuckToFloor");
            var slow = FxFactory.GetStatus("StatusLavaSteveGoo");
            var poison = FxFactory.GetStatus("StatusPoisoned");

            // ------------------------------------------------------------------------------------- shared and echoes
            SwapFlash = Vis("ModSwapFlash", "FxSwapFlash", "Play", 12, 24);
            EchoMark = Vis("ModUmbEchoMark", "FxUmbEchoMark", "Play", 12, 16);
            EchoQuick = Vis("ModUmbEchoQuick", "FxUmbEchoMark", "Quick", 12, 16);
            EchoSparkle = Vis("ModUmbEchoSparkle", "FxUmbEchoMark", "Sparkle", 12, 16);
            EchoSmear = Vis("ModEchoSmear", "FxUmbEchoSmear", "Play", 12, 20);
            EchoBite = Vis("ModUmbEchoBite", "FxUmbEchoBite", "Play", 9, 11);
            DecoyBurst = FxKit.TimedHit("ModDecoyBurst", "skydropExplode", "FxDecoyBurst", "Play", 1, 3, 0.75f, 0.6f, colliderScale: 0.6f, canFlip: false);
            Strike.Ground(DecoyBurst, "FxDecoyBurst", 26, 14, 22f, 12f);

            // ------------------------------------------------------------------------------------- Shade Imp
            ImpClaw = AimedMelee.Rotating(GodsBArc.Swipe("ModImpClaw", "OrcSwipe", "FxUmbImpClaw", "Play", 9, 12, 0.6f, 0.5f));
            Strike.Collider(ImpClaw, 16f, 14f, 5f, 0f);
            SmokeStep = Vis("ModUmbSmokeStep", "FxUmbSmokeStep", "Life", 19, 16);
            Dark(SmokeStep, 16f);

            // ------------------------------------------------------------------------------------- Glimmer
            MirrorShard = Missile("ModMirrorShard", "FxMirrorShard", 200f, 1.4f, 0.6f, 0.4f, 9f, 6f, bounce: true);
            ShardHot = Clip("FxMirrorShard", "Hot", "ModMirrorShardHot", true);
            Hook(MirrorShard, i => { var b = i.GetComponent<BankShotFx>() ?? i.AddComponent<BankShotFx>(); b.Arm(); });
            RingShard = Missile("ModRingShard", "FxUmbRingShard", 170f, 0.9f, 0.3f, 0.3f, 8f, 5f);

            // ------------------------------------------------------------------------------------- Gloom Lurker
            Darkness = Vis("ModDarkness", "FxDarkness", "Life", 30, 24);
            Dark(Darkness, 26f);
            LurkerBite = Bite("ModLurkerBite", 0.8f, 0.5f, 14f, 12f);
            LurkerAmbush = Bite("ModLurkerAmbush", 1.6f, 1.2f, 14f, 12f, daze, 0.5f);
            LurkEyes = Vis("ModUmbLurkEyes", "FxUmbLurkEyes", "Loop", 8, 8, loop: true);

            BuildTier2(daze, root, slow);
            BuildTier3(daze, root, slow, poison);
            BuildEchoes();
            Plugin.Log.LogInfo("Umbrael FX templates built");
        }

        static void BuildTier2(Status daze, Status root, Status slow)
        {
            // ---- The Twinned
            TwinCut = AimedMelee.Rotating(GodsBArc.Swipe("ModTwinCut", "OrcSwipe2", "FxUmbTwinCut", "Play", 10, 14, 1.0f, 0.7f));
            Strike.Collider(TwinCut, 18f, 16f, 6f, 0f);
            TwinSwapCut = AimedMelee.Rotating(GodsBArc.Swipe("ModTwinSwapCut", "OrcSwipe2", "FxUmbTwinCut", "Play", 10, 14, 1.1f, 0.8f));
            Strike.Collider(TwinSwapCut, 18f, 16f, 6f, 0f);

            // ---- Nailshade
            Nail = Missile("ModUmbNail", "FxUmbNail", 230f, 0.45f, 0.8f, 0.3f, 8f, 5f);
            Pinned = Vis("ModUmbPinned", "FxUmbPinned", "Play", 10, 13);
            Pin = Missile("ModNailshadePin", "FxUmbPin", 270f, 0.55f, 0.6f, 0.2f, 10f, 5f, status: root);
            if (Pin != null) FxFactory.SetContacts(Pin, destroyOnHit: true, spawnOnHit: Pinned);
            NailRake = AimedMelee.Rotating(GodsBArc.Swipe("ModNailshadeRake", "OrcSwipe2", "FxUmbNailRake", "Play", 10, 13, 1.0f, 0.8f, stun: 0.2f));
            Strike.Collider(NailRake, 18f, 16f, 6f, 0f);

            // ---- Mirror Witch: a long-lived bolt that banks off walls; the standing mirror
            ReflectBolt = Missile("ModReflectBolt", "FxReflectBolt", 185f, 2.6f, 0.9f, 0.5f, 9f, 7f, bounce: true);
            Hook(ReflectBolt, i => { if (i.GetComponent<WitchBoltFx>() == null) i.AddComponent<WitchBoltFx>(); });
            PaneShatter = Vis("ModUmbPaneShatter", "FxUmbMirrorPane", "Shatter", 12, 22);
            Pane = FxKit.Inert("ModUmbMirrorPane", "FxUmbMirrorPane", "Rise", destroyOnAnimEnd: true, spawnOnDestroy: PaneShatter,
                               thenAnim: "Idle", thenRepeat: 5);   // 0.22 s rise + 5 x 0.96 s standing
            if (Pane != null)
            {
                Strike.ArtAt(Pane, "FxUmbMirrorPane", 12, 22);
                Hook(Pane, i => { var f = i.GetComponent<MirrorPaneFx>() ?? i.AddComponent<MirrorPaneFx>(); f.Arm(); });
            }
            PaneFlash = Vis("ModUmbPaneFlash", "FxUmbMirrorPane", "Flash", 12, 22);

            // ---- Gloamcoil
            CoilBite = Bite("ModGloamcoilBite", 1.0f, 0.6f, 14f, 12f);
            CoilSlither = AimedMelee.Rotating(FxKit.BodyHit("ModGloamcoilSlither", 0.8f, 0.5f, 0.8f, 0.4f));
            Strike.HitBox(CoilSlither, 22f, 10f);
            GloamPool = Vis("ModGloamPool", "FxUmbGloamPool", "Life", 16, 12);
            Dark(GloamPool, 13f);
            DuskEdge = Vis("ModUmbDuskEdge", "FxUmbDuskEdge", "R16", 35, 29, loop: true);
            DuskEdges = new exSpriteAnimClip[DuskRadii.Length];
            for (int i = 0; i < DuskRadii.Length; i++) DuskEdges[i] = Clip("FxUmbDuskEdge", "R" + DuskRadii[i], "ModUmbDuskEdgeR" + DuskRadii[i], true);

            // ---- Glassmoth: scales in a V; a glitter cloud that drifts after the hero, slows, and makes echoes whole
            MothScale = Missile("ModMothScale", "FxUmbMothScale", 210f, 0.5f, 0.8f, 0.35f, 8f, 6f);
            Glitter = FxKit.Cloud("ModGlitterDust", "FxUmbGlitter", "Life", 70f, 0.15f, 0.5f, slow, 1f);
            if (Glitter != null)
            {
                Strike.HitBox(Glitter, 22f, 14f);
                Strike.ArtAt(Glitter, "FxUmbGlitter", 13, 13);
                Hook(Glitter, i => { if (i.GetComponent<GlitterFx>() == null) i.AddComponent<GlitterFx>(); });
            }

            // ---- Hourglass
            SandShard = Missile("ModSandShard", "FxUmbSandShard", 190f, 0.6f, 0.9f, 0.4f, 8f, 6f);
            RewindMark = Vis("ModRewindMark", "FxUmbRewind", "Mark", 13, 22);
            RewindSnap = Vis("ModRewindSnap", "FxUmbRewind", "Snap", 13, 22);
        }

        static void BuildTier3(Status daze, Status root, Status slow, Status poison)
        {
            // ---- The Hollow King: the eclipse cleave; the thrown crown and the shadow king that rises from it
            KingCleave = AimedMelee.Rotating(GodsBArc.Swipe("ModKingCleave", "OrcSwipe2", "FxUmbKingCleave", "Play", 16, 26, 1.5f, 1.3f,
                                                            stun: 0.25f, damageFrame: 1));
            Strike.Collider(KingCleave, 32f, 26f, 8f, 0f);
            Crown = Vis("ModUmbCrown", "FxUmbCrown", "Fly", 10, 7, loop: true);
            CrownShade = Vis("ModUmbCrownShade", "FxUmbCrownShade", "Rise", 22, 46);
            if (CrownShade != null) FxFactory.SetEffect(CrownShade, destroyOnAnimEnd: false, canFlip: true, freeRotate: false);
            ShadeRise = Clip("FxUmbCrownShade", "Rise", "ModUmbShadeRise", false);
            ShadeIdle = Clip("FxUmbCrownShade", "Idle", "ModUmbShadeIdle", true);
            ShadeSwing = Clip("FxUmbCrownShade", "Swing", "ModUmbShadeSwing", false);
            ShadeFade = Clip("FxUmbCrownShade", "Fade", "ModUmbShadeFade", false);

            // ---- The Sundered: the scissor cut; the pale half, the crack of light, the rejoin rush
            Scissor = AimedMelee.Rotating(GodsBArc.Swipe("ModSunderedCross", "OrcSwipe2", "FxUmbScissor", "Play", 10, 12, 1.2f, 0.9f, damageFrame: 2));
            Strike.Collider(Scissor, 22f, 18f, 8f, 0f);
            PaleHalf = Vis("ModUmbPaleHalf", "FxUmbPaleHalf", "Idle", 26, 35, loop: true);
            PaleIdle = Clip("FxUmbPaleHalf", "Idle", "ModUmbPaleIdle", true);
            PaleRush = Clip("FxUmbPaleHalf", "Rush", "ModUmbPaleRush", true);
            PaleDrift = Clip("FxUmbPaleHalf", "Drift", "ModUmbPaleDrift", true);
            PaleCutClip = Clip("FxUmbPaleHalf", "Cut", "ModUmbPaleCutAnim", false);
            // the pale half's own strike, a beat after the dark half's scissor (SunderedTorn spawns it toward the hero)
            PaleCut = AimedMelee.Rotating(GodsBArc.Swipe("ModSunderedPaleCut", "OrcSwipe2", "FxUmbPaleCut", "Play", 13, 13, 0.6f, 0.6f,
                                                         damageFrame: 1));
            Strike.Collider(PaleCut, 24f, 16f, 10f, 0f);
            Crack = Vis("ModUmbCrack", "FxUmbCrack", "Line", 0, 1, loop: true);
            LightThread = Vis("ModUmbLightThread", "FxUmbLightThread", "Line", 0, 1, life: 0.3f);
            if (Crack != null) FxFactory.SetEffect(Crack, destroyOnAnimEnd: false, canFlip: false, freeRotate: true);
            if (LightThread != null) FxFactory.SetEffect(LightThread, destroyOnAnimEnd: false, destroyAfter: 0.3f, canFlip: false, freeRotate: true);
            RejoinHit = FxKit.BodyHit("ModUmbRejoinHit", 1.4f, 1f, 1.0f, 0.3f);
            Strike.HitBox(RejoinHit, 14f, 14f, 0f, 8f);
            RejoinCut = Vis("ModUmbRejoinCut", "FxUmbRejoinCut", "Play", 12, 10);

            // ---- Glass Seraph: feathers that ricochet; Prism's split on the wall; threads of light to the echoes it bends
            Feather = Missile("ModSeraphFeather", "FxUmbFeather", 190f, 1.2f, 1.0f, 0.4f, 9f, 6f, bounce: true);
            PrismFeather = Missile("ModSeraphPrism", "FxUmbFeather", 190f, 1.2f, 1.0f, 0.4f, 9f, 6f, bounce: true);
            Hook(PrismFeather, i => { var s = i.GetComponent<FeatherSplitFx>() ?? i.AddComponent<FeatherSplitFx>(); s.Arm(); });
            FeatherSplit = Clip("FxUmbFeather", "Split", "ModUmbFeatherSplit", false);

            // ---- Bristleback: lobbed nails that land as caltrops; the shake; the hero's shots stuck in its back
            Caltrop = FxFactory.Clone("SkMageSlimeEffect", "ModBristleCaltrop");
            if (Caltrop != null)
            {
                var sh = SpriteSheets.Get("FxUmbCaltrop");
                FxFactory.Reskin(Caltrop, new ClipBuilder(sh, "Life", "ModBristleCaltropLife").Once()
                    .Ev(2, "AnimDamageOn").Ev(11, "AnimDamageOff").Build(), sh);
                FxFactory.SetEffect(Caltrop, destroyOnAnimEnd: true, snap: 1f);
                FxFactory.SetDamage(Caltrop, 0.4f, rate: 0.6f, knockback: 0.05f, collisionAtStart: false);
                FxKit.NoTint(Caltrop);
                Strike.Ground(Caltrop, "FxUmbCaltrop", 6, 7, 12f, 6f);
            }
            Quill = FxKit.Projectile("ModBristleQuill", "DFX_skelMageNewProjectile", "FxUmbQuill", "Fly", 150f, 0.42f, 1.0f, 0.4f, rotate: false);
            if (Quill != null)
            {
                Strike.HitBox(Quill, 7f, 7f);
                Strike.ArtAt(Quill, "FxUmbQuill", 4, 10);
                FxFactory.SetEffect(Quill, destroyOnAnimEnd: false, destroyAfter: 0.42f, spawnOnDestroy: Caltrop, freeRotate: false);
            }
            ShakeNail = Missile("ModBristleShakeNail", "FxUmbNail", 210f, 0.4f, 0.6f, 0.3f, 8f, 5f);
            StuckInd = new[] { ModStatus.Indicator("ModUmbStuck1", "FxUmbStuckShot", "One", 0f, OverlayAt.Feet),
                               ModStatus.Indicator("ModUmbStuck2", "FxUmbStuckShot", "Two", 0f, OverlayAt.Feet),
                               ModStatus.Indicator("ModUmbStuck3", "FxUmbStuckShot", "Three", 0f, OverlayAt.Feet) };

            // ---- The Unblinking: a short straight gaze; Lights Out's darkness and the flash when the eye opens
            GazeBeam = FxFactory.Clone("DamageBeholderBeam", "ModGazeBeam");
            if (GazeBeam != null)
            {
                var bsh = SpriteSheets.Get("FxUmbBeam");
                FxFactory.Reskin(GazeBeam, new ClipBuilder(bsh, "Play", "ModGazeBeamClip").Once().Build(), bsh);
                GazeEnd = FxKit.Visual("ModGazeBeamEnd", "FxUmbBeam", "End");
                if (GazeEnd != null)
                {
                    FxFactory.SetEffect(GazeEnd, destroyOnAnimEnd: true, canFlip: true, freeRotate: true);
                    var es = GazeEnd.GetComponent<exSprite>();
                    if (es != null) { es.anchor = exPlane.Anchor.MidLeft; es.offset = Vector2.zero; }
                }
                FxFactory.SetEffect(GazeBeam, destroyOnAnimEnd: true, spawnOnDestroy: GazeEnd, canFlip: true, freeRotate: true);
                // one hit per gaze: the tick rate outlasts the beam
                FxFactory.SetDamage(GazeBeam, 1.1f, rate: 1f, knockback: 0.4f, collisionAtStart: true);
                var spr = GazeBeam.GetComponent<exSprite>();
                if (spr != null) { spr.anchor = exPlane.Anchor.MidLeft; spr.offset = Vector2.zero; spr.color = Color.white; }
                Strike.Collider(GazeBeam, 50f, 8f, 25f, 0f);
                FxKit.NoTint(GazeBeam);
            }
            Blackout = Vis("ModUmbBlackout", "FxUmbBlackout", "Life", 102, 79);
            Dark(Blackout, 90f);
            EyeFlash = Vis("ModUmbEyeFlash", "FxUmbEyeFlash", "Play", 93, 78);

            // ---- Glass Widow: the stab; the glaze web; the glaze on the hero and its crack
            WidowFang = AimedMelee.Rotating(GodsBArc.Swipe("ModWidowFang", "OrcSwipe2", "FxUmbWidowFang", "Play", 8, 14, 1.2f, 0.8f));
            Strike.Collider(WidowFang, 16f, 18f, 6f, 0f);
            GlazeWeb = FxKit.TimedHit("ModUmbGlazeWeb", "TrollGroundPoundBigShockwave", "FxUmbGlazeWeb", "Play", 4, 6, 0.4f, 0.1f, root, 1f,
                                      canFlip: false);
            Strike.Ground(GlazeWeb, "FxUmbGlazeWeb", 15, 36, 24f, 12f);
            GlazeCrack = Vis("ModUmbGlazeCrack", "FxUmbGlazeCrack", "Play", 15, 24);
            GlazeInd = ModStatus.Indicator("ModUmbGlaze", "FxUmbGlaze", "Loop", 0f, OverlayAt.Feet);

            // ---- Eclipse Wyrm: two bites; the eclipse's corona and the glass head bursting out
            WyrmBite = Bite("ModWyrmBite", 1.1f, 0.8f, 16f, 14f);
            WyrmGlassBite = Bite("ModWyrmGlassBite", 1.1f, 0.6f, 16f, 14f, daze, 0.35f);
            Corona = Vis("ModUmbCorona", "FxUmbCorona", "Loop", 30, 29, loop: true);
            CoronaHit = FxKit.BodyHit("ModUmbCoronaHit", 0.4f, 1f, 0.2f, 0.1f);
            Strike.HitBox(CoronaHit, 52f, 28f, 0f, 8f);
            EclipseBurst = FxKit.TimedHit("ModUmbEclipseBurst", "TrollGroundPoundBigShockwave", "FxUmbEclipseBurst", "Play", 1, 3, 1.2f, 1.2f,
                                          canFlip: false);
            Strike.Ground(EclipseBurst, "FxUmbEclipseBurst", 28, 22, 44f, 22f);

            // ---- The Undertow: the bite; the ink it rides in under an ally
            VenomBite = AimedMelee.Rotating(GodsBArc.Swipe("ModUndertowVenom", "OrcSwipe", "FxUmbVenomBite", "Play", 9, 9, 1.2f, 0.6f, poison, 0.6f,
                                                           damageFrame: 2));
            Strike.Collider(VenomBite, 16f, 14f, 6f, 0f);
            InkUnder = FxKit.Inert("ModUmbInkUnder", "FxUmbInkUnder", "Spread", destroyOnAnimEnd: false);
            if (InkUnder != null)
            {
                Strike.ArtAt(InkUnder, "FxUmbInkUnder", 15, 8);
                Dark(InkUnder, 14f);
            }
            InkLoop = Clip("FxUmbInkUnder", "Loop", "ModUmbInkLoop", true);
            InkFade = Clip("FxUmbInkUnder", "Fade", "ModUmbInkFade", false);

            // ---- Argus Moth
            ArgusScale = Missile("ModArgusScale", "FxUmbArgusScale", 200f, 0.6f, 1.0f, 0.4f, 9f, 7f);
            ArgusCatch = Vis("ModUmbArgusCatch", "FxUmbArgusCatch", "Play", 12, 25);

            // ---- Glitterswarm: the bite; the surge's bites, its glinting path, the glass ghost that runs it again
            SwarmBite = AimedMelee.Rotating(GodsBArc.Swipe("ModSwarmBite", "OrcSwipe", "FxUmbSwarmBite", "Play", 8, 11, 1.1f, 0.6f, damageFrame: 1));
            Strike.Collider(SwarmBite, 24f, 22f, 10f, 0f);
            SurgeBite = FxKit.BodyHit("ModUmbSurgeBite", 0.5f, 1f, 0.5f, 0.1f);
            Strike.HitBox(SurgeBite, 24f, 18f, 0f, 10f);
            SwarmGlint = Vis("ModUmbSwarmGlint", "FxUmbSwarmGlint", "Play", 10, 16);
            SwarmGhost = Vis("ModUmbSwarmGhost", "FxUmbSwarmGhost", "Fly", 19, 17, loop: true);
            if (SwarmGhost != null) FxFactory.SetEffect(SwarmGhost, destroyOnAnimEnd: false, canFlip: true, freeRotate: false);
            GhostBite = FxKit.BodyHit("ModUmbGhostBite", 0.25f, 1f, 0.3f, 0.1f);
            Strike.HitBox(GhostBite, 24f, 18f, 0f, 10f);

            // ---- The Pendulum: the full swing round its pivot; the hit of the blade that swings by itself; the slowed ring of time
            PendulumSpin = FxKit.TimedHit("ModPendulumSpin", "TrollGroundPoundBigShockwave", "FxUmbPendulumSpin", "Play", 1, 4, 1.5f, 1.0f,
                                          canFlip: false);
            Strike.Ground(PendulumSpin, "FxUmbPendulumSpin", 16, 16, 30f, 24f);
            BladeHit = FxKit.BodyHit("ModUmbBladeHit", 1.0f, 1f, 0.6f, 0.12f);
            Strike.HitBox(BladeHit, 30f, 10f, 0f, 2f);
            Tick = Vis("ModUmbTick", "FxUmbTick", "Play", 5, 12);
            TimeRing = Vis("ModUmbTimeRing", "FxUmbTimeRing", "Loop", 42, 36, loop: true, life: 1.5f);

            // ---- Sand Wraith: the fist of sand; the hourglass over the hero; the column
            SandBall = Missile("ModSandBall", "FxUmbSandBall", 170f, 0.75f, 1.2f, 0.6f, 9f, 8f);
            SandGlass = Vis("ModUmbSandGlass", "FxUmbSandGlass", "Fill0", 8, 17, loop: true);
            SandFill = new exSpriteAnimClip[5];
            for (int i = 0; i < 5; i++) SandFill[i] = Clip("FxUmbSandGlass", "Fill" + i, "ModUmbSandFill" + i, true);
            SandShadow = Vis("ModUmbSandShadow", "FxUmbSandColumn", "Shadow", 14, 83);
            SandColumn = FxKit.TimedHit("ModUmbSandColumn", "TrollGroundPoundBigShockwave", "FxUmbSandColumn", "Fall", 2, 4, 0.2f, 1.0f,
                                        canFlip: false);
            Strike.Ground(SandColumn, "FxUmbSandColumn", 14, 83, 20f, 10f);
        }

        /// <summary>The god perk: the half echo of every basic attack, its full twin, and the shadow jaws a bite's echo snaps.</summary>
        static void BuildEchoes()
        {
            var basics = new[] { ImpClaw, MirrorShard, LurkerBite, LurkerAmbush, TwinCut, TwinSwapCut, Nail, ReflectBolt, CoilBite, MothScale,
                                 SandShard, KingCleave, Scissor, Feather, Quill, GazeBeam, WidowFang, WyrmBite, WyrmGlassBite, VenomBite,
                                 ArgusScale, SwarmBite, PendulumSpin, SandBall };
            foreach (var t in basics)
            {
                if (t == null) continue;
                // the full one first: EchoOf links the last copy made as the template's echo
                var full = FxKit.EchoOf(t, 1f);
                if (full != null)
                {
                    full.name = t.name + "EchoWhole";
                    FxFactory.Templates[full.name] = full;
                    FullEcho[t] = full;
                }
                FxKit.EchoOf(t, 0.5f);
            }
            foreach (var t in new[] { LurkerBite, LurkerAmbush, CoilBite, WyrmBite, WyrmGlassBite })
            {
                GameObject full;
                foreach (var e in new[] { FxKit.FindEcho(t), FullEcho.TryGetValue(t, out full) ? full : null })
                    if (e != null) Hook(e, i => { if (EchoBite != null) SystemPool.Spawn(EchoBite, i.transform.position); });
            }
            // the Undertow's echo is a shadow of its own jaws, drawn on the same cell (FxUmbVenomBite "Echo"), so it closes
            // exactly where the bite closed instead of a tinted copy of the bone jaws
            GameObject vbFull;
            EchoArt(FxKit.FindEcho(VenomBite), "FxUmbVenomBite", "Echo", 2);
            if (VenomBite != null && FullEcho.TryGetValue(VenomBite, out vbFull)) EchoArt(vbFull, "FxUmbVenomBite", "Echo", 2);
        }

        /// <summary>Give an echo template its own shadow art (same sheet and origin as the attack, damage on the same frame).</summary>
        static void EchoArt(GameObject echo, string sheet, string anim, int damageFrame)
        {
            var sh = SpriteSheets.Get(sheet);
            if (echo == null || sh == null || !sh.Has(anim)) return;
            var cb = new ClipBuilder(sh, anim, echo.name + "Clip").Once().Ev(damageFrame, "AnimDamageOn").Ev(damageFrame + 1, "AnimDamageOff");
            FxFactory.Reskin(echo, cb.Build(), sh);
            foreach (var spr in echo.GetComponentsInChildren<exSprite>(true)) spr.color = new Color(1f, 1f, 1f, 0.9f);
        }
    }
}
