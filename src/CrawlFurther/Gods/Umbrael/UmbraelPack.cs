using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Art;
    using CrawlFurther.Gods;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Umbrael, the Hollow Mirror: echoes, mirrors and glass, shadows and darkness, and time running wrong. Every basic
    /// attack comes back as an echo 0.6 s later in the same spot for half damage (the god perk, <see cref="UmbraelEcho"/>),
    /// and every monster bends that rule or the dark in a way of its own (an <see cref="UmbraelBehaviour"/>) with a tell
    /// the hero can read. Offsets below are pixels from the feet (x forward, y up), from art/out_umbrael/TIMING.md and the
    /// rigs in tools/sprites/umbrael_v2_*.py.
    /// </summary>
    public static class UmbraelPack
    {
        static ClipBuilder Special(SpriteSheet sh, string anim, string clip)
        {
            return new ClipBuilder(sh, anim, clip).Once().Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop");
        }

        static exSpriteAnimClip Looped(SpriteSheet sh, string anim, string clip)
        {
            return sh.Has(anim) ? new ClipBuilder(sh, anim, clip).Loop().Build() : null;
        }

        static exSpriteAnimClip Once(SpriteSheet sh, string anim, string clip)
        {
            return sh.Has(anim) ? new ClipBuilder(sh, anim, clip).Once().Build() : null;
        }

        // ---------------------------------------------------------------------------------------------- tier 1
        // Shade Imp: two rakes; Smoke Step blinks 40 px toward the hero through darkness. Quirk: ImpQuickShadow.
        static void ImpKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int c1 = Kit.AddEffect(p, UmbraelFx.ImpClaw, attach: true, offsetX: 4f, offsetY: 7f);   // claws strike at (6..9, -4..-8)
            int c2 = Kit.AddEffect(p, UmbraelFx.ImpClaw, attach: true, offsetX: 4f, offsetY: 7f, angle: 14f);
            var rake = Kit.Melee(sh, "Rake", "ModImpRake", v, 2, c1, 60f, 4, c2, 40f).Build();
            var step = Special(sh, "Step", "ModImpStep").Ev(1, "AnimStartInvincibility")
                .Ev(2, "AnimCollideOff").EvF(2, "AnimShadowAlpha", 0f).Ev(4, "ModUmbSmokeStep").EvO(4, "AnimSound", v)
                .Ev(6, "AnimCollideOn").EvF(6, "AnimShadowAlpha", 1f).Ev(7, "AnimStopInvincibility").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, rake, 1.1f, rangeInner: 8f, rangeOuter: 22f));
            Kit.SetSpecial(p, Kit.Attack(sp, step, 0f, rangeInner: 35f, rangeOuter: 90f, rangeRetreat: 0f), 5.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 7f);
        }

        // Glimmer: a shard that ricochets (and hits harder once it has); Mirror Image makes two decoys. Bank shot: BankShotFx.
        static void GlimmerKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int shard = Kit.AddEffect(p, UmbraelFx.MirrorShard, offsetX: 4f, offsetY: 9f);   // off the tip of the pane
            var sd = Kit.Shot(sh, "Shard", "ModGlimmerShard", 2, v, 0f, shard).Build();
            var split = Special(sh, "Split", "ModGlimmerSplit").Ev(3, "ModMirrorImage").EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sd, 1.3f, rangeInner: 45f, rangeOuter: 100f, rangeRetreat: 40f));
            Kit.SetSpecial(p, Kit.Attack(sp, split, 0f, rangeInner: 30f, rangeOuter: 160f, rangeRetreat: 30f), 5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 9f);
        }

        static void DecoyKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0];
            int n0 = Strike.Mark(p);
            int shard = Kit.AddEffect(p, UmbraelFx.RingShard, offsetX: 4f, offsetY: 9f);
            var sd = Kit.Shot(sh, "Shard", "ModDecoyShard", 2, null, 0f, shard).Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sd, 1.6f, rangeInner: 40f, rangeOuter: 110f, rangeRetreat: 30f));
            Kit.AddDeathSpawn(p, UmbraelFx.DecoyBurst);
            Strike.Feet(p, n0, 9f);
            Strike.DeathAtFeet(p);
        }

        // Gloom Lurker: a lunging bite, twice as hard from hiding; Breathe Darkness hides its kin. Quirk: LurkerEyes.
        static void LurkerKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            var like = Kit.Effects(p)[0];
            int n0 = Strike.Mark(p);
            // the face plate lunges to (10..13, -4); the ambush bite must sit right after the plain one (ModAmbush picks +1)
            int bite = Kit.AddEffect(p, UmbraelFx.LurkerBite, attach: true, destroyOnAnimEnd: true, offsetX: 12f, offsetY: 5f, like: like);
            Kit.AddEffect(p, UmbraelFx.LurkerAmbush, attach: true, destroyOnAnimEnd: true, offsetX: 12f, offsetY: 5f, like: like);
            int dark = Kit.AddEffect(p, UmbraelFx.Darkness, offsetX: 10f, offsetY: 0.01f);
            var amb = new ClipBuilder(sh, "Ambush", "ModLurkerAmbush").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff")
                .EvF(3, "AnimMoveStick", 110f).Ev(3, "ModAmbush", bite).EvO(3, "AnimSound", v)
                .Ev(4, "AnimMoveStop").Ev(-1, "AnimRun").Build();
            var gl = Special(sh, "Gloom", "ModLurkerGloom").Ev(3, "AnimAttack", dark).EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, amb, 1.2f, rangeInner: 12f, rangeOuter: 30f));
            Kit.SetSpecial(p, Kit.Attack(sp, gl, 0f, rangeInner: 0f, rangeOuter: 80f, rangeRetreat: 0f), 5.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 5f);
        }

        // ---------------------------------------------------------------------------------------------- tier 2
        // The Twinned: the dark body cuts ahead, the pale one behind; Swap trades places with the hero and cuts.
        // Quirk: TwinnedCrossed.
        static void TwinnedKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            var like = Kit.Effects(p)[0];
            int n0 = Strike.Mark(p);
            // the extra 180 degrees turns the swipe but not its offset, so the back cut gets a negative offset
            int front = Kit.AddEffect(p, UmbraelFx.TwinCut, attach: true, offsetX: 8f, offsetY: 12f, like: like);
            int back = Kit.AddEffect(p, UmbraelFx.TwinCut, attach: true, offsetX: -8f, offsetY: 12f, like: like, angle: 180f);
            int swapCut = Kit.AddEffect(p, UmbraelFx.TwinSwapCut, attach: true, offsetX: 8f, offsetY: 12f, like: like);
            var cut = Kit.Melee(sh, "Cut", "ModTwinnedCut", v, 2, front, 60f, 4, back, 0f).Build();
            var swap = Special(sh, "Swap", "ModTwinnedSwap").Ev(3, "ModUmbTwinSwap").EvO(3, "AnimSound", v)
                .EvF(6, "AnimMoveStick", 50f).Ev(6, "AnimAttack", swapCut).Ev(7, "AnimMoveStop").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, cut, 1.2f, rangeInner: 10f, rangeOuter: 26f));
            Kit.SetSpecial(p, Kit.Attack(sp, swap, 0f, rangeInner: 40f, rangeOuter: 150f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 12f);
        }

        // Nailshade: a fan of three nails that tightens as it hits (basics 0-2: 30, 20, 10 degrees); Pin roots the hero and
        // it re-forms beside him to rake. Quirk: NailshadeNarrowing.
        static void NailshadeKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            var tags = new[] { "", "Mid", "Tight" };
            var spreads = new[] { 15f, 10f, 5f };
            var fans = new List<exSpriteAnimClip>();
            for (int k = 0; k < 3; k++)
            {
                // the hand releases at (10, -13)
                int na = Kit.AddEffect(p, UmbraelFx.Nail, offsetX: 10f, offsetY: 13f, angle: 0.01f);
                int nb = Kit.AddEffect(p, UmbraelFx.Nail, offsetX: 10f, offsetY: 13f, angle: spreads[k]);
                int nc = Kit.AddEffect(p, UmbraelFx.Nail, offsetX: 10f, offsetY: 13f, angle: -spreads[k]);
                fans.Add(Kit.Shot(sh, "Fling" + tags[k], "ModNailshadeFling" + tags[k], 2, v, 0f, na, nb, nc).Build());
            }
            int pin = Kit.AddEffect(p, UmbraelFx.Pin, offsetX: 10f, offsetY: 14f);
            int rake = Kit.AddEffect(p, UmbraelFx.NailRake, attach: true, offsetX: 9f, offsetY: 9f);
            var pn = new ClipBuilder(sh, "Pin", "ModNailshadePin").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f)
                .Ev(3, "AnimInputMultiplyStop").Ev(3, "AnimInputOff").Ev(3, "AnimAttack", pin).EvO(3, "AnimSound", v)
                .Ev(4, "AnimMoveStop").Ev(4, "AnimStartInvincibility").Ev(4, "AnimCollideOff").EvF(4, "AnimShadowAlpha", 0f)
                .Ev(6, "ModUmbPinPounce")   // 0.34 s after the throw: a pin that hit has landed
                .Ev(6, "AnimCollideOn").EvF(6, "AnimShadowAlpha", 1f).Ev(6, "AnimStopInvincibility")
                .EvF(7, "AnimMoveStick", 50f).Ev(7, "AnimAttack", rake).Ev(8, "AnimMoveStop").Ev(-1, "AnimRun").Build();
            atk.Clear();
            foreach (var f in fans) atk.Add(Kit.Attack(a0, f, 1.3f, rangeInner: 30f, rangeOuter: 90f, rangeRetreat: 25f));   // nails fly ~100 px
            Kit.SetSpecial(p, Kit.Attack(sp, pn, 0f, rangeInner: 30f, rangeOuter: 130f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 13f);
            NailshadeNarrowing.Idles = new[] { null, Looped(sh, "IdleMid", "ModNailshadeIdleMid"), Looped(sh, "IdleTight", "ModNailshadeIdleTight") };
            NailshadeNarrowing.Runs = new[] { null, Looped(sh, "RunMid", "ModNailshadeRunMid"), Looped(sh, "RunTight", "ModNailshadeRunTight") };
        }

        // Mirror Witch: a bolt that banks off walls; Standing Mirror sets a pane between her and the hero.
        // Quirk: WitchLookingGlass.
        static void WitchKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int bolt = Kit.AddEffect(p, UmbraelFx.ReflectBolt, offsetX: 11f, offsetY: 16f);   // out of the glass at (9..13, -16)
            var rf = Kit.Shot(sh, "Reflect", "ModWitchReflect", 3, v, 0f, bolt).Build();
            var mr = Special(sh, "Mirror", "ModWitchMirror").Ev(3, "ModUmbStandingMirror").EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, rf, 1.4f, rangeInner: 55f, rangeOuter: 120f, rangeRetreat: 40f));
            Kit.SetSpecial(p, Kit.Attack(sp, mr, 0f, rangeInner: 30f, rangeOuter: 120f, rangeRetreat: 20f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 16f);
        }

        // Gloamcoil: a rearing lunge; Dusk Trail dashes along the floor leaving three darkness pools. Quirk: GloamcoilDusk.
        static void GloamcoilKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int bite = Kit.AddEffect(p, UmbraelFx.CoilBite, attach: true, destroyOnAnimEnd: true, offsetX: 14f, offsetY: 10f);   // jaws at (13, -10)
            int body = Kit.AddEffect(p, UmbraelFx.CoilSlither, attach: true, destroyOnAnimEnd: true, offsetX: 4f, offsetY: 4f);
            int pool = Kit.AddEffect(p, UmbraelFx.GloamPool, offsetX: -6f, offsetY: 0.01f);
            var st = Kit.Melee(sh, "Strike", "ModGloamcoilStrike", v, 3, bite, 70f).Build();
            var sl = new ClipBuilder(sh, "Slither", "ModGloamcoilSlither").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(1, "AnimInputMultiplyStop").Ev(1, "AnimInputOff")
                .EvF(2, "AnimMove", 230f).Ev(2, "AnimAttack", body).Ev(2, "AnimAttack", pool).EvO(2, "AnimSound", v)
                .Ev(4, "AnimAttack", pool).Ev(6, "AnimMoveStop").Ev(6, "AnimAttack", pool).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, st, 1.2f, rangeInner: 12f, rangeOuter: 28f));
            // 230 px/s for the 0.32 s dash = ~74 px
            Kit.SetSpecial(p, Kit.Attack(sp, sl, 0f, rangeInner: 25f, rangeOuter: 85f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 9f);
        }

        // Glassmoth: two scales in a V; Glitter drifts at the hero and slows him. Echoes inside glitter hit whole (GlitterFx).
        static void GlassmothKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int sa = Kit.AddEffect(p, UmbraelFx.MothScale, offsetX: 8f, offsetY: 12f, angle: 9f);   // forewings at (8, -12)
            int sb = Kit.AddEffect(p, UmbraelFx.MothScale, offsetX: 8f, offsetY: 12f, angle: -9f);
            int dust = Kit.AddEffect(p, UmbraelFx.Glitter, offsetX: 10f, offsetY: 4f);
            var sc = Kit.Shot(sh, "Scales", "ModGlassmothScales", 2, v, 0f, sa, sb).Build();
            var du = Kit.Shot(sh, "Dust", "ModGlassmothDust", 3, v, 0f, dust).Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sc, 1.2f, rangeInner: 40f, rangeOuter: 95f, rangeRetreat: 35f));
            Kit.SetSpecial(p, Kit.Attack(sp, du, 0f, rangeInner: 20f, rangeOuter: 90f, rangeRetreat: 20f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 12f);
        }

        // Hourglass: a fused sand shard; Rewind marks its spot and health and snaps back to both. Quirk: HourglassRewind.
        static void HourglassKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int shard = Kit.AddEffect(p, UmbraelFx.SandShard, offsetX: 5f, offsetY: 16f);   // the eye in the waist
            var sd = Kit.Shot(sh, "Shard", "ModHourglassShard", 2, v, 0f, shard).Build();
            var rw = Special(sh, "Rewind", "ModHourglassRewind").Ev(1, "ModUmbRewindMark").EvO(1, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sd, 1.3f, rangeInner: 45f, rangeOuter: 100f, rangeRetreat: 35f));
            Kit.SetSpecial(p, Kit.Attack(sp, rw, 0f, rangeInner: 0f, rangeOuter: 140f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 16f);
            HourglassRewind.SnapClip = Once(sh, "Snap", "ModHourglassSnap");
        }

        // ---------------------------------------------------------------------------------------------- tier 3
        // The Hollow King: the eclipse cleave (basic 0 crowned, 1 bare); Hollow Crown throws the crown by the hero.
        // Quirk: KingCrown.
        static void KingKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int cleave = Kit.AddEffect(p, UmbraelFx.KingCleave, attach: true, offsetX: 10f, offsetY: 16f);
            var cl = Kit.Melee(sh, "Cleave", "ModKingCleave", v, 4, cleave, 70f).Build();
            var clb = Kit.Melee(sh, "CleaveBare", "ModKingCleaveBare", v, 4, cleave, 70f).Build();
            var th = Special(sh, "Throw", "ModKingThrow").Ev(4, "ModUmbThrowCrown").EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, cl, 1.5f, rangeInner: 16f, rangeOuter: 38f));
            atk.Add(Kit.Attack(a0, clb, 1.5f, rangeInner: 16f, rangeOuter: 38f));
            Kit.SetSpecial(p, Kit.Attack(sp, th, 0f, rangeInner: 30f, rangeOuter: 110f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 16f);
            KingCrown.BareIdle = Looped(sh, "IdleBare", "ModKingIdleBare");
            KingCrown.BareRun = Looped(sh, "RunBare", "ModKingRunBare");
        }

        // The Sundered: two sabres scissor shut; Rejoin rushes the pale half home through whatever lies between.
        // Quirk: SunderedTorn.
        static void SunderedKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int cut = Kit.AddEffect(p, UmbraelFx.Scissor, attach: true, offsetX: 8f, offsetY: 14f);   // the sabres meet at (12, -14)
            // the pale half steps up as the sabres close (2) and cuts a beat after the dark half's hit (3)
            var cr = Kit.Melee(sh, "Cross", "ModSunderedCross", v, 3, cut, 60f).Ev(2, "ModUmbPaleCut").Build();
            // Rejoin: the pale half swings out past the hero as it braces (0), then rushes home through him (2)
            var rj = Special(sh, "Rejoin", "ModSunderedRejoin").Ev(0, "ModUmbRejoinSet").Ev(2, "ModUmbRejoin").EvO(2, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, cr, 1.3f, rangeInner: 12f, rangeOuter: 30f));
            // the pale half trails a second behind: a dark half that has just run past the hero has him on the line
            Kit.SetSpecial(p, Kit.Attack(sp, rj, 0f, rangeInner: 0f, rangeOuter: 45f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 14f);
            // in play the body is the dark half alone (its hurtbox too); the pale half is its own effect that SunderedTorn
            // walks, strikes and rushes, and the sheet's Idle and Run, which show both halves, are for the portrait and the vault
            SunderedTorn.SoloIdle = Looped(sh, "IdleSolo", "ModSunderedIdleSolo");
            SunderedTorn.SoloRun = Looped(sh, "RunSolo", "ModSunderedRunSolo");
            if (SunderedTorn.SoloIdle != null) R.Set(p, "m_animationIdle", SunderedTorn.SoloIdle);
            if (SunderedTorn.SoloRun != null) R.Set(p, "m_animationRun", SunderedTorn.SoloRun);
        }

        // Glass Seraph: three feathers that ricochet; Prism sends five that split on the wall. Quirk: SeraphLight.
        static void SeraphKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            var fan = new List<int>();
            foreach (var a in new[] { -14f, 0.01f, 14f }) fan.Add(Kit.AddEffect(p, UmbraelFx.Feather, offsetX: 12f, offsetY: 20f, angle: a));
            var prism = new List<int>();
            foreach (var a in new[] { -30f, -15f, 0.01f, 15f, 30f }) prism.Add(Kit.AddEffect(p, UmbraelFx.PrismFeather, offsetX: 12f, offsetY: 20f, angle: a));
            var ft = Kit.Shot(sh, "Feathers", "ModSeraphFeathers", 3, v, 0f, fan.ToArray()).Build();
            var pr = Kit.Shot(sh, "Prism", "ModSeraphPrism", 5, v, 0.03f, prism.ToArray()).Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, ft, 1.5f, rangeInner: 50f, rangeOuter: 110f, rangeRetreat: 40f));
            Kit.SetSpecial(p, Kit.Attack(sp, pr, 0f, rangeInner: 30f, rangeOuter: 130f, rangeRetreat: 20f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 20f);
        }

        // Bristleback: three lobbed nails that stay as caltrops; Shake throws a horseshoe of six. Quirk: BristlePincushion.
        static void BristlebackKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            // the nails go up off its back and travel low over the floor (drawn 6 px up) so the caltrops land on the floor
            var lob = new List<int>();
            foreach (var a in new[] { -22f, 0.01f, 22f }) lob.Add(Kit.AddEffect(p, UmbraelFx.Quill, offsetX: 2f, offsetY: 3f, angle: a));
            var shake = new List<int>();
            foreach (var a in new[] { 70f, 110f, 150f, -70f, -110f, -150f }) shake.Add(Kit.AddEffect(p, UmbraelFx.ShakeNail, offsetX: 0f, offsetY: 10f, angle: a));
            var lb = Kit.Shot(sh, "Lob", "ModBristleLob", 3, v, 0.05f, lob.ToArray()).Build();
            var sk = Special(sh, "Shake", "ModBristleShake");
            for (int i = 0; i < shake.Count; i++) sk.Ev(3, "AnimAttack", shake[i], i * 0.03f);
            sk.EvO(3, "AnimSound", v).Ev(-1, "AnimRun");
            atk.Clear();
            atk.Add(Kit.Attack(a0, lb, 1.5f, rangeInner: 25f, rangeOuter: 70f, rangeRetreat: 15f));
            Kit.SetSpecial(p, Kit.Attack(sp, sk.Build(), 0f, rangeInner: 0f, rangeOuter: 45f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 10f);
        }

        // The Unblinking: a short straight gaze; Lights Out shuts its eye under a great darkness. Quirk: UnblinkingEye.
        static void EyeKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int beam = Kit.AddEffect(p, UmbraelFx.GazeBeam, attach: true, offsetX: 9f, offsetY: 18f);   // the iris at (9, -18), 50 px of beam
            var gz = Kit.Shot(sh, "Gaze", "ModEyeGaze", 3, v, 0f, beam).Build();
            var bo = Special(sh, "Blackout", "ModEyeBlackout").EvO(1, "AnimSound", v).Ev(4, "ModUmbLightsOut").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, gz, 1.5f, rangeInner: 20f, rangeOuter: 55f, rangeRetreat: 15f));
            Kit.SetSpecial(p, Kit.Attack(sp, bo, 0f, rangeInner: 0f, rangeOuter: 80f, rangeRetreat: 0f), 7.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 18f);
            UnblinkingEye.ShutClip = Looped(sh, "Shut", "ModEyeShut");
            UnblinkingEye.CrackClip = Once(sh, "Crack", "ModEyeCrack");
        }

        // Glass Widow: the front legs stab; Glaze Web drops on the hero's spot. Quirk: WidowBrittle.
        static void WidowKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int fang = Kit.AddEffect(p, UmbraelFx.WidowFang, attach: true, offsetX: 12f, offsetY: 7f);   // the legs stab to (18, -2)
            var fg = Kit.Melee(sh, "Fang", "ModWidowFang", v, 3, fang, 50f).Build();
            var wb = Special(sh, "Web", "ModWidowWeb").Ev(3, "ModUmbGlazeWeb").EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, fg, 1.3f, rangeInner: 12f, rangeOuter: 28f));
            Kit.SetSpecial(p, Kit.Attack(sp, wb, 0f, rangeInner: 20f, rangeOuter: 120f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 8f);
        }

        // Eclipse Wyrm: the void head bites, then the glass head (it may daze); Eclipse swallows the glass head.
        // Quirk: WyrmEclipse. Basic 1 is the disc's roll (no hit).
        static void WyrmKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int b1 = Kit.AddEffect(p, UmbraelFx.WyrmBite, attach: true, destroyOnAnimEnd: true, offsetX: 18f, offsetY: 16f);
            int b2 = Kit.AddEffect(p, UmbraelFx.WyrmGlassBite, attach: true, destroyOnAnimEnd: true, offsetX: 18f, offsetY: 20f);
            var fg = Kit.Melee(sh, "Fangs", "ModWyrmFangs", v, 3, b1, 60f, 5, b2, 30f).Build();
            var roll = Kit.Melee(sh, "Disc", "ModWyrmDiscRoll", null).Build();
            var sw = Special(sh, "Swallow", "ModWyrmSwallow").EvO(3, "AnimSound", v).Ev(7, "ModUmbEclipse").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, fg, 1.6f, rangeInner: 14f, rangeOuter: 32f));
            atk.Add(Kit.Attack(a0, roll, 0.6f, rangeInner: 0f, rangeOuter: 20f));
            Kit.SetSpecial(p, Kit.Attack(sp, sw, 0f, rangeInner: 0f, rangeOuter: 60f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 18f);
            WyrmEclipse.DiscClip = Looped(sh, "Disc", "ModWyrmDisc");
            WyrmEclipse.BurstClip = Once(sh, "Burst", "ModWyrmBurst");
        }

        // The Undertow: a rearing bite that may poison; Lurk Beneath rides in the ink under an ally. Quirk: UndertowLurk.
        static void UndertowKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int bite = Kit.AddEffect(p, UmbraelFx.VenomBite, attach: true, offsetX: 13f, offsetY: 13f);   // the jaws close at (19, -13)
            var vb = Kit.Melee(sh, "Venom", "ModUndertowVenom", v, 3, bite, 60f).Build();
            var dv = Special(sh, "Dive", "ModUndertowDive").EvO(2, "AnimSound", v).Ev(6, "ModUmbLurk").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, vb, 1.4f, rangeInner: 12f, rangeOuter: 30f));
            Kit.SetSpecial(p, Kit.Attack(sp, dv, 0f, rangeInner: 0f, rangeOuter: 120f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 13f);
            UndertowLurk.LurkClip = Looped(sh, "Lurk", "ModUndertowLurk");
            UndertowLurk.BiteClip = Once(sh, "LurkBite", "ModUndertowLurkBite");
            UndertowLurk.SurfaceClip = Once(sh, "Surface", "ModUndertowSurface");
        }

        // Argus Moth: a fan of three eye scales; Scale Storm sends three widening waves. Quirk: ArgusEyes.
        static void ArgusKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            var vol = new List<int>();
            foreach (var a in new[] { -14f, 0.01f, 14f }) vol.Add(Kit.AddEffect(p, UmbraelFx.ArgusScale, offsetX: 8f, offsetY: 18f, angle: a));
            var waves = new List<int[]>();
            foreach (var w in new[] { 10f, 20f, 30f })
                waves.Add(new[] { Kit.AddEffect(p, UmbraelFx.ArgusScale, offsetX: 8f, offsetY: 18f, angle: -w),
                                  Kit.AddEffect(p, UmbraelFx.ArgusScale, offsetX: 8f, offsetY: 18f, angle: 0.01f),
                                  Kit.AddEffect(p, UmbraelFx.ArgusScale, offsetX: 8f, offsetY: 18f, angle: w) });
            var vo = Kit.Shot(sh, "Volley", "ModArgusVolley", 2, v, 0f, vol.ToArray()).Build();
            // three down-strokes 0.3 s apart (frames 1, 4, 7)
            var st = new ClipBuilder(sh, "Storm", "ModArgusStorm").Once().EvF(0, "AnimInputMultiplyFreeFace", 0f)
                .Ev(1, "AnimInputMultiplyStop").Ev(1, "AnimInputOff").Ev(0, "AnimMoveStop");
            for (int w = 0; w < 3; w++)
                foreach (var e in waves[w]) st.Ev(1 + w * 3, "AnimAttack", e);
            st.EvO(1, "AnimSound", v).Ev(-1, "AnimRun");
            atk.Clear();
            atk.Add(Kit.Attack(a0, vo, 1.4f, rangeInner: 50f, rangeOuter: 110f, rangeRetreat: 40f));
            Kit.SetSpecial(p, Kit.Attack(sp, st.Build(), 0f, rangeInner: 30f, rangeOuter: 120f, rangeRetreat: 20f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 18f);
            ArgusEyes.CatchClip = Once(sh, "Catch", "ModArgusCatch");
        }

        // Glitterswarm: the swarm surges and bites; Surge rushes through the hero on a line it steers. Quirk: SwarmSurge.
        static void SwarmKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int bite = Kit.AddEffect(p, UmbraelFx.SwarmBite, attach: true, offsetX: 6f, offsetY: 16f);
            int sb = Kit.AddEffect(p, UmbraelFx.SurgeBite, attach: true, destroyOnAnimEnd: true, offsetX: 4f, offsetY: 6f);
            var bt = Kit.Melee(sh, "Bite", "ModSwarmBite", v, 2, bite, 60f).Build();
            // the rush steers with the stick (AnimMoveStick) through frames 2-5
            var sg = new ClipBuilder(sh, "Surge", "ModSwarmSurge").Once().EvF(0, "AnimInputMultiplyFreeFace", 0f)
                .Ev(2, "AnimInputMultiplyStop").Ev(2, "ModUmbSurgeStart").EvF(2, "AnimMoveStick", 260f).EvO(2, "AnimSound", v)
                .Ev(2, "AnimAttack", sb).Ev(3, "AnimAttack", sb).Ev(4, "AnimAttack", sb)
                .Ev(6, "AnimMoveStop").Ev(6, "ModUmbSurgeEnd").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, bt, 1.3f, rangeInner: 12f, rangeOuter: 32f));
            // 260 px/s for the 0.24 s rush = ~62 px
            Kit.SetSpecial(p, Kit.Attack(sp, sg, 0f, rangeInner: 10f, rangeOuter: 50f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 18f);
        }

        // The Pendulum: the heavy swing goes all the way round its pivot; Stop the Clock slows time round it.
        // Quirk: PendulumClock (the blade that swings by itself).
        static void PendulumKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int spin = Kit.AddEffect(p, UmbraelFx.PendulumSpin, offsetX: 0f, offsetY: 11f);   // round the pivot under the case
            var sw = Kit.Melee(sh, "Swing", "ModPendulumSwing", v, 2, spin, 0f).Build();
            var stp = Special(sh, "Stop", "ModPendulumStop").Ev(1, "ModUmbStopClock").EvO(1, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sw, 1.5f, rangeInner: 0f, rangeOuter: 20f));
            Kit.SetSpecial(p, Kit.Attack(sp, stp, 0f, rangeInner: 0f, rangeOuter: 36f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 14f);
        }

        // Sand Wraith: a fist of sand; Time Out hangs an hourglass over the hero. Quirk: WraithHeldTime.
        static void WraithKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int ball = Kit.AddEffect(p, UmbraelFx.SandBall, offsetX: 13f, offsetY: 18f);   // the hand at (12, -16)
            var fi = Kit.Shot(sh, "Fist", "ModWraithFist", 2, v, 0f, ball).Build();
            var to = Special(sh, "TimeOut", "ModWraithTimeOut").EvO(2, "AnimSound", v).Ev(4, "ModUmbTimeOut").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, fi, 1.4f, rangeInner: 35f, rangeOuter: 100f, rangeRetreat: 30f));
            Kit.SetSpecial(p, Kit.Attack(sp, to, 0f, rangeInner: 20f, rangeOuter: 120f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 18f);
        }

        public static readonly MonsterDef Decoy = new MonsterDef
        {
            id = "GlimmerDecoy", art = "UmbGlimmerDecoy", basePrefab = "EnemyTinyRatFodder", health = 0.6f, speedMult = 1.3f, kit = DecoyKit
        };

        // Evolution tree: every evolution has exactly one parent.
        //   ShadeImp    -> Twinned, Nailshade      Twinned     -> HollowKing, Sundered     Nailshade -> GlassSeraph, Bristleback
        //   Glimmer     -> Glassmoth, Hourglass    Glassmoth   -> ArgusMoth, Glitterswarm  Hourglass -> Pendulum, SandWraith
        //   GloomLurker -> MirrorWitch, Gloamcoil  MirrorWitch -> Unblinking, GlassWidow   Gloamcoil -> EclipseWyrm, Undertow
        public static readonly List<MonsterDef> Monsters = new List<MonsterDef>
        {
            new MonsterDef { id = "ShadeImp", art = "UmbShadeImp", basePrefab = "EnemyDarkServant", health = 3.5f, evolveCost = 0f,
                             evolveTo = new[] { "Twinned", "Nailshade" }, kit = ImpKit },
            new MonsterDef { id = "Glimmer", art = "UmbGlimmer", basePrefab = "EnemyFlyingEye_Dodge", health = 3f, evolveCost = 0f,
                             evolveTo = new[] { "Glassmoth", "Hourglass" }, kit = GlimmerKit },
            new MonsterDef { id = "GloomLurker", art = "UmbGloomLurker", basePrefab = "EnemyGiantSpider_Standard", health = 4f, evolveCost = 0f,
                             evolveTo = new[] { "MirrorWitch", "Gloamcoil" }, kit = LurkerKit },
            new MonsterDef { id = "Twinned", art = "UmbTwinned", basePrefab = "EnemyOrc", health = 7f, evolveCost = 2.5f,
                             evolveTo = new[] { "HollowKing", "Sundered" }, kit = TwinnedKit },
            new MonsterDef { id = "Nailshade", art = "UmbNailshade", basePrefab = "EnemyRatman", health = 6f, evolveCost = 2.5f,
                             evolveTo = new[] { "GlassSeraph", "Bristleback" }, kit = NailshadeKit },
            new MonsterDef { id = "MirrorWitch", art = "UmbMirrorWitch", basePrefab = "EnemyWitch", health = 5.5f, evolveCost = 2.5f,
                             evolveTo = new[] { "Unblinking", "GlassWidow" }, kit = WitchKit },
            new MonsterDef { id = "Gloamcoil", art = "UmbGloamcoil", basePrefab = "EnemyDemonSnake", health = 6.5f, evolveCost = 2.5f,
                             evolveTo = new[] { "EclipseWyrm", "Undertow" }, kit = GloamcoilKit },
            new MonsterDef { id = "Glassmoth", art = "UmbGlassmoth", basePrefab = "EnemyFlyingEye_Rapidfire", health = 5.5f, evolveCost = 2.5f,
                             evolveTo = new[] { "ArgusMoth", "Glitterswarm" }, kit = GlassmothKit },
            new MonsterDef { id = "Hourglass", art = "UmbHourglass", basePrefab = "EnemyFlyingEye_Dodge", health = 6f, speedMult = 0.9f, evolveCost = 2.5f,
                             evolveTo = new[] { "Pendulum", "SandWraith" }, kit = HourglassKit },
            new MonsterDef { id = "EclipseWyrm", art = "UmbEclipseWyrm", basePrefab = "EnemySmallDragon", health = 12f, speedMult = 0.85f,
                             evolveCost = 4.5f, kit = WyrmKit },
            new MonsterDef { id = "HollowKing", art = "UmbHollowKing", basePrefab = "EnemyPriestess", health = 11.5f, evolveCost = 4.5f,
                             kit = KingKit },
            new MonsterDef { id = "GlassSeraph", art = "UmbGlassSeraph", basePrefab = "EnemySkeletonPope", health = 10.5f, evolveCost = 4.5f,
                             kit = SeraphKit },
            new MonsterDef { id = "Unblinking", art = "UmbUnblinking", basePrefab = "EnemyBeholder", health = 11f, evolveCost = 4.5f,
                             kit = EyeKit },
            new MonsterDef { id = "Sundered", art = "UmbSundered", basePrefab = "EnemyMinotaur", health = 11f, evolveCost = 4.5f,
                             kit = SunderedKit },
            new MonsterDef { id = "Bristleback", art = "UmbBristleback", basePrefab = "EnemyCapraDemon", health = 12f, speedMult = 0.9f,
                             evolveCost = 4.5f, kit = BristlebackKit },
            new MonsterDef { id = "GlassWidow", art = "UmbGlassWidow", basePrefab = "EnemyGiantSpider_SpitWebs", health = 11.5f, evolveCost = 4.5f,
                             kit = WidowKit },
            new MonsterDef { id = "Undertow", art = "UmbUndertow", basePrefab = "EnemyDemonSnake", health = 11.5f, speedMult = 0.9f,
                             evolveCost = 4.5f, kit = UndertowKit },
            new MonsterDef { id = "ArgusMoth", art = "UmbArgusMoth", basePrefab = "EnemyFlyingEye_Red", health = 10.5f, speedMult = 0.9f,
                             evolveCost = 4.5f, kit = ArgusKit },
            new MonsterDef { id = "Glitterswarm", art = "UmbGlitterswarm", basePrefab = "EnemyFlyingEye_Red", health = 10.5f, evolveCost = 4.5f,
                             kit = SwarmKit },
            new MonsterDef { id = "Pendulum", art = "UmbPendulum", basePrefab = "EnemyBeholder", health = 11.5f, evolveCost = 4.5f,
                             kit = PendulumKit },
            new MonsterDef { id = "SandWraith", art = "UmbSandWraith", basePrefab = "EnemySkeletonPope", health = 11f, speedMult = 0.9f,
                             evolveCost = 4.5f, kit = WraithKit },
        };

        /// <summary>Each monster's quirk.</summary>
        static readonly Dictionary<string, Type> Quirks = new Dictionary<string, Type>
        {
            { "ShadeImp", typeof(ImpQuickShadow) }, { "GloomLurker", typeof(LurkerEyes) }, { "Twinned", typeof(TwinnedCrossed) },
            { "Nailshade", typeof(NailshadeNarrowing) }, { "MirrorWitch", typeof(WitchLookingGlass) }, { "Gloamcoil", typeof(GloamcoilDusk) },
            { "Hourglass", typeof(HourglassRewind) }, { "HollowKing", typeof(KingCrown) }, { "Sundered", typeof(SunderedTorn) },
            { "GlassSeraph", typeof(SeraphLight) }, { "Bristleback", typeof(BristlePincushion) }, { "Unblinking", typeof(UnblinkingEye) },
            { "GlassWidow", typeof(WidowBrittle) }, { "EclipseWyrm", typeof(WyrmEclipse) }, { "Undertow", typeof(UndertowLurk) },
            { "ArgusMoth", typeof(ArgusEyes) }, { "Glitterswarm", typeof(SwarmSurge) }, { "Pendulum", typeof(PendulumClock) },
            { "SandWraith", typeof(WraithHeldTime) },
        };

        public static readonly GodDef God = new GodDef
        {
            name = "Umbrael",
            text = "Basic hits echo a beat later",
            flavour = "Every blow in the mirror\nlands twice.",
            winText = "THE MIRROR CRACKS",
            portraitArt = "DeityUmbrael",
            startingMonsters = new[] { "ShadeImp", "Glimmer", "GloomLurker" },
        };

        static exSpriteAnimClip s_idol;

        public static void Register()
        {
            UmbraelFx.Build();
            UmbraelEcho.Index();
            foreach (var m in Monsters)
            {
                var t = new UmbraelTraits { echo = true, echoDelay = 0.6f, echoFx = UmbraelFx.EchoSmear };
                Type q;
                if (Quirks.TryGetValue(m.id, out q)) t.behaviours.Add(q);
                if (m.id == "GloomLurker") t.stealth = true;
                MonsterTraits.Register(m.PrefabName, t);
            }
            MonsterTraits.Register("ModGlimmerDecoy", new UmbraelTraits { lifetime = 4f, expireFx = UmbraelFx.DecoyBurst });
            var decoy = MonsterFactory.Build(Decoy);
            if (decoy != null) UmbraelFx.DecoySpawner = FxKit.MinionSpawner("ModDecoySpawner", decoy.gameObject, "FxShadowPuff", "Play");
            foreach (var m in Monsters) MonsterFactory.Build(m);
            MonsterFactory.LinkEvolutions(Monsters);
            MonsterEvents.AttackSpawned += OnAttackSpawned;
            MonsterEvents.AttackSpawned += HeroShots.OnAttackSpawned;
            DeityFactory.Register(God);
            // the gold idol carved in the Hollow Mirror's likeness
            var prev = SlotGods.PortraitFor;
            SlotGods.PortraitFor = (tier, perk) =>
                tier == SlotTier.Gold && perk != null && perk.GetName() == God.name ? Idol() : (prev != null ? prev(tier, perk) : null);
            Strike.KeepAllScales();
        }

        static exSpriteAnimClip Idol()
        {
            if (s_idol == null) s_idol = SlotArt.Clip("DeityGoldIdolUmbrael", "Idle");
            return s_idol;
        }

        static void OnAttackSpawned(Player owner, GameObject fx, GameObject template)
        {
            var q = owner != null && fx != null ? owner.GetComponent<UmbraelBehaviour>() : null;
            if (q != null) q.OnAttackSpawned(fx, template);
        }
    }
}
