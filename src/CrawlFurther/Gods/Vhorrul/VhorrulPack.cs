using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    using CrawlFurther.Art;
    using CrawlFurther.Gods;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Vhorrul, the Tallow Saint: wax and fire. The dead burn as pyres that cool to tallow, wax slows the hero and heals
    /// the tallow monsters, and fire lights wax. Each monster's kit is below; their quirks are the
    /// <see cref="VhorrulBehaviour"/> classes in this folder. Art: tools/sprites/vhorrul_v2_*.py (art/out/TIMING.md).
    /// </summary>
    public static class VhorrulPack
    {
        /// <summary>The holy-fire indicator over an anointed monster.</summary>
        public static StatusOverlayDef AnointInd;
        static Deity s_deity;
        static exSpriteAnimClip s_idol;

        /// <summary>True while the hero is burning (Moth Matron's moths hunt him then).</summary>
        public static bool HeroBurning()
        {
            var h = ModUtil.Hero();
            var p = h != null ? h.GetComponent<Player>() : null;
            var sm = p != null ? p.GetStatusManager() : null;
            return sm != null && VhorrulFx.OnFire != null && sm.GetHasStatusWithClass(VhorrulFx.OnFire.m_class);
        }

        // ================================================================================================ tier 1
        // Wickling: Flare Bite; Gutter Dash (a 60 px sprint leaving 3 burning pools, ending in a stumble; the tail goes out)
        static void WicklingKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            var slot = Kit.Effects(p)[0];
            int n0 = Strike.Mark(p);
            int bite = Kit.AddEffect(p, VhorrulFx.WickBite, attach: true, destroyOnAnimEnd: true, offsetX: 10f, offsetY: 6f, like: slot);
            int dash = Kit.AddEffect(p, VhorrulFx.WickDashHit, attach: true, destroyOnAnimEnd: true, offsetX: 4f, offsetY: 6f, like: slot);
            int trail = Kit.AddEffect(p, VhorrulFx.WickDashTrail, attach: true, destroyOnAnimEnd: true);
            var b = new ClipBuilder(sh, "Bite", "ModWicklingBite").Once().Ev(0, "AnimInputOff").EvF(1, "AnimMoveStick", 85f)
                .Ev(3, "AnimAttack", bite).EvO(3, "AnimSound", v).Ev(4, "AnimMoveStop").Ev(5, "AnimRun").Build();
            // 330 px/s over the four 0.045 s sprint frames: about 60 px
            var d = new ClipBuilder(sh, "Dash", "ModWicklingDash").Once().EvF(0, "AnimInputMultiplyFreeFace", 0f)
                .Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff").EvF(2, "AnimMove", 330f).Ev(2, "AnimCollideOff")
                .Ev(2, "AnimAttack", dash).Ev(2, "AnimAttack", trail).EvO(2, "AnimSound", v)
                .Ev(6, "AnimMoveStop").Ev(6, "AnimCollideOn").Ev(7, "VhGutter").Ev(-1, "AnimRun").Build();
            WicklingRelight.IdleOut = new ClipBuilder(sh, "IdleOut", "ModWicklingIdleOut").Loop().Build(); WicklingRelight.RunOut = new ClipBuilder(sh, "RunOut", "ModWicklingRunOut").Loop().Build();
            WicklingRelight.IdleHot = new ClipBuilder(sh, "IdleHot", "ModWicklingIdleHot").Loop().Build(); WicklingRelight.RunHot = new ClipBuilder(sh, "RunHot", "ModWicklingRunHot").Loop().Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, b, 1.2f, rangeInner: 14f, rangeOuter: 30f));
            Kit.SetSpecial(p, Kit.Attack(sp, d, 0f, rangeInner: 25f, rangeOuter: 66f, rangeRetreat: 0f), 5.5f);
            Strike.Feet(p, n0, 6f);
        }

        // Tallow Grub: Wax Spit (skids along the floor and pools); Melt (glide as a puddle, then rise through it)
        static void GrubKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int glob = Kit.AddEffect(p, VhorrulFx.WaxGlob, offsetX: 12f, offsetY: 1f);
            int up = Kit.AddEffect(p, VhorrulFx.Upwell, offsetX: 0.01f, offsetY: 4f);
            var spit = Kit.Shot(sh, "Spit", "ModGrubSpit", 3, v, 0f, glob).EvF(3, "AddImpulseForwards", -40f).Build();
            var melt = new ClipBuilder(sh, "Melt", "ModGrubMelt").Once().Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop").Ev(0, "AnimStartInvincibility")
                .Ev(2, "AnimCollideOff").EvF(3, "AnimShadowAlpha", 0f).Ev(4, "AnimInputOn").Ev(4, "VhGlide").Ev(-1, "AnimRun").Build();
            GrubGlide.Puddle = new ClipBuilder(sh, "Puddle", "ModGrubPuddle").Loop().Build();
            GrubGlide.Glide = new ClipBuilder(sh, "Glide", "ModGrubGlide").Loop().Build();
            GrubGlide.Rise = new ClipBuilder(sh, "Rise", "ModGrubRise").Once().EvF(2, "AnimShadowAlpha", 1f).Ev(2, "AnimCollideOn")
                .Ev(2, "AnimAttack", up).EvO(2, "AnimSound", v).Build();
            GrubGlide.Pop = new ClipBuilder(sh, "Rise", "ModGrubPop").Once().Durations(0.05f, 0.05f, 0.06f, 0.08f, 0.1f, 0.1f)
                .EvF(0, "AnimShadowAlpha", 1f).Ev(0, "AnimCollideOn").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, spit, 1.3f, rangeInner: 45f, rangeOuter: 80f, retreatWhileAttacking: true));
            Kit.SetSpecial(p, Kit.Attack(sp, melt, 0f, rangeInner: 0f, rangeOuter: 110f, rangeRetreat: 0f), 4.5f);
            Strike.Feet(p, n0, 6f);
        }

        // Ash Moth: Ash Puff (dazes; carries embers near fire); Flame Dive (bends toward the nearest flame)
        static void AshMothKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int puff = Kit.AddEffect(p, VhorrulFx.AshPuff, offsetX: 7f, offsetY: 9f);
            int ember = Kit.AddEffect(p, VhorrulFx.EmberPuff, offsetX: 7f, offsetY: 9f);
            int dive = Kit.AddEffect(p, VhorrulFx.MothDive, attach: true, destroyOnAnimEnd: true, offsetX: 3f, offsetY: 7f);
            int burst = Kit.AddEffect(p, VhorrulFx.AshPuff, offsetX: 4f, offsetY: 6f);
            Func<int, string, exSpriteAnimClip> puffClip = (slot, name) => Kit.Shot(sh, "Puff", name, 3, v, 0f, slot)
                .EvF(3, "AddImpulseForwards", -30f).Build();
            var d = new ClipBuilder(sh, "Dive", "ModAshMothDive").Once().EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(1, "VhAimAtFlame")
                .Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff").EvF(2, "AnimMove", 230f).Ev(2, "AnimAttack", dive).EvO(2, "AnimSound", v)
                .Ev(3, "VhAimAtFlame").Ev(5, "AnimMoveStop").Ev(5, "AnimAttack", burst).Ev(-1, "AnimRun").Build();
            MothDrawn.IdleGlow = new ClipBuilder(sh, "IdleGlow", "ModAshMothIdleGlow").Loop().Build(); MothDrawn.RunGlow = new ClipBuilder(sh, "RunGlow", "ModAshMothRunGlow").Loop().Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, puffClip(puff, "ModAshMothPuff"), 1.4f, rangeInner: 26f, rangeOuter: 44f, rangeRetreat: 18f));
            atk.Add(Kit.Attack(a0, puffClip(ember, "ModAshMothEmberPuff"), 1.4f, rangeInner: 26f, rangeOuter: 44f, rangeRetreat: 18f));
            Kit.SetSpecial(p, Kit.Attack(sp, d, 0f, rangeInner: 15f, rangeOuter: 46f, rangeRetreat: 0f), 5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 8f);
        }

        // ================================================================================================ tier 2
        // Waxen Knight: Guttering Combo (3 cuts, the overhead spills wax); Seal (wax shell, cracked off as a slowing ring)
        static void WaxenKnightKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int c1 = Kit.AddEffect(p, VhorrulFx.KnightCut, attach: true, destroyOnAnimEnd: true, offsetX: 10f, offsetY: 11f);
            int c3 = Kit.AddEffect(p, VhorrulFx.KnightCut3, attach: true, destroyOnAnimEnd: true, offsetX: 11f, offsetY: 9f);
            KnightKindle.SpillSlot = Kit.AddEffect(p, VhorrulFx.WaxPuddle, offsetX: 18f, offsetY: 0.01f);
            KnightKindle.BurnSpillSlot = Kit.AddEffect(p, VhorrulFx.KindledSpill, offsetX: 18f, offsetY: 0.01f);
            KnightKindle.RingSlot = Kit.AddEffect(p, VhorrulFx.SealRing, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            KnightKindle.LitRingSlot = Kit.AddEffect(p, VhorrulFx.LitRing, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            var k1 = Kit.Melee(sh, "Combo1", "ModKnightCombo1", v, 2, c1, 70f).Build();
            var k2 = Kit.Melee(sh, "Combo2", "ModKnightCombo2", null, 2, c1, 70f).Build();
            var k3 = Kit.Melee(sh, "Combo3", "ModKnightCombo3", v, 3, c3, 95f).Ev(3, "VhKnightSpill").Build();
            var seal = new ClipBuilder(sh, "Seal", "ModKnightSeal").Once().Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop").Ev(1, "AnimStartInvincibility")
                .Ev(4, "AnimStopInvincibility").Ev(4, "VhKnightRing").EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, k1, 0.3f, rangeInner: 12f, rangeOuter: 26f));
            atk.Add(Kit.Attack(a0, k2, 0.3f, rangeInner: 12f, rangeOuter: 26f));
            atk.Add(Kit.Attack(a0, k3, 1.5f, rangeInner: 12f, rangeOuter: 28f));
            Kit.SetSpecial(p, Kit.Attack(sp, seal, 0f, rangeInner: 0f, rangeOuter: 30f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.5f);
            Strike.Feet(p, n0, 9f);
        }

        // Chandler: Molten Glob (lands as a burning pool); Pour (a 50 px line of touch-paper wax, lit later by any fire)
        static void ChandlerKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int glob = Kit.AddEffect(p, VhorrulFx.MoltenGlob, offsetX: 15.7f, offsetY: 1.1f);
            var seg = new List<int>();
            for (int i = 0; i < 5; i++) seg.Add(Kit.AddEffect(p, VhorrulFx.WaxLine, offsetX: 15.7f + i * 10f, offsetY: 0.01f));
            var toss = Kit.Shot(sh, "Toss", "ModChandlerToss", 3, v, 0f, glob).Build();
            var pour = new ClipBuilder(sh, "Pour", "ModChandlerPour").Once().EvF(0, "AnimInputMultiplyFreeFace", 0f)
                .Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff").Ev(2, "VhNewLine").EvO(2, "AnimSound", v);
            for (int i = 0; i < seg.Count; i++) pour.Ev(2, "AnimAttack", seg[i], i * 0.06f);
            pour.Ev(-1, "AnimRun");
            atk.Clear();
            atk.Add(Kit.Attack(a0, toss, 1.4f, rangeInner: 40f, rangeOuter: 66f, rangeRetreat: 32f));
            Kit.SetSpecial(p, Kit.Attack(sp, pour.Build(), 0f, rangeInner: 25f, rangeOuter: 66f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 10.1f);
        }

        // Wickworm: Rearing Bite; Drip Road (slithers fast for 2 s laying a road of wax); swims in wax
        static void WickwormKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p) ?? a0; var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int bite = Kit.AddEffect(p, VhorrulFx.WormBite, attach: true, destroyOnAnimEnd: true, offsetX: 13f, offsetY: 4f);
            int road = Kit.AddEffect(p, VhorrulFx.WaxRoad, attach: true);
            var b = Kit.Melee(sh, "Bite", "ModVhWormBite", v, 3, bite, 80f).Build();
            var r = new ClipBuilder(sh, "Road", "ModVhWormRoad").Once().EvF(0, "ModSprint", 2f).Ev(0, "AnimAttack", road).EvO(0, "AnimSound", v)
                .Ev(-1, "AnimRun").Build();
            WaxSwimmer.SwimIdle = new ClipBuilder(sh, "Swim", "ModVhWormSwim").Loop().Build(); WaxSwimmer.SwimRun = new ClipBuilder(sh, "SwimRun", "ModVhWormSwimRun").Loop().Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, b, 1.1f, rangeInner: 10f, rangeOuter: 28f, rangeRetreat: 0f));
            Kit.EnableSpecial(p, Kit.Attack(sp, r, 0f, rangeInner: 20f, rangeOuter: 140f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 6f);
        }

        // Tallow Sow: Fat Spray (3 drops, may slow); Lay (3 wax eggs: 2 s later each spits at the hero, then pools)
        static void SowKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p) ?? a0; var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            var drops = new List<int>();
            foreach (var a in new[] { -14f, 0.01f, 14f }) drops.Add(Kit.AddEffect(p, VhorrulFx.SowDrop, offsetX: 13f, offsetY: 7f, angle: a));
            var eggs = new List<int>();
            foreach (var o in new[] { new Vector2(-10f, 0.01f), new Vector2(-13f, 6f), new Vector2(-13f, -6f) })
                eggs.Add(Kit.AddEffect(p, VhorrulFx.WaxEgg, offsetX: o.x, offsetY: o.y));
            var spray = Kit.Shot(sh, "Spray", "ModVhSowSpray", 3, v, 0.02f, drops.ToArray()).Build();
            var lay = new ClipBuilder(sh, "Lay", "ModVhSowLay").Once().Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop");
            for (int i = 0; i < eggs.Count; i++) lay.Ev(4, "AnimAttack", eggs[i], i * 0.08f);
            lay.EvO(4, "AnimSound", v).Ev(-1, "AnimRun");
            SowGreased.IdleCoat = new ClipBuilder(sh, "IdleCoat", "ModVhSowIdleCoat").Loop().Build(); SowGreased.RunCoat = new ClipBuilder(sh, "RunCoat", "ModVhSowRunCoat").Loop().Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, spray, 1.5f, rangeInner: 30f, rangeOuter: 72f, rangeRetreat: 26f));
            Kit.EnableSpecial(p, Kit.Attack(sp, lay.Build(), 0f, rangeInner: 25f, rangeOuter: 120f, rangeRetreat: 20f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 6f);
        }

        // Moth Matron: Ember Rake (leaves an ash puff); Moth Lamp (3 ember moths that hunt a burning hero)
        static void MatronKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int rake = Kit.AddEffect(p, VhorrulFx.MatronRake, attach: true, destroyOnAnimEnd: true, offsetX: 10.8f, offsetY: 9.7f);
            int puff = Kit.AddEffect(p, VhorrulFx.AshPuff, offsetX: 13f, offsetY: 7.6f);
            var moths = new List<int>();
            foreach (var a in new[] { -40f, 0.01f, 40f }) moths.Add(Kit.AddEffect(p, VhorrulFx.EmberMoth, offsetX: 6.5f, offsetY: 20.5f, angle: a));
            var r = Kit.Melee(sh, "Rake", "ModMatronRake", v, 2, rake, 80f).Ev(3, "AnimAttack", puff).Build();
            var lamp = new ClipBuilder(sh, "Lamp", "ModMatronLamp").Once().Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop").Ev(2, "VhFaceHero");
            for (int i = 0; i < moths.Count; i++) lamp.Ev(3, "AnimAttack", moths[i], i * 0.06f);
            lamp.EvO(3, "AnimSound", v).Ev(-1, "AnimRun");
            atk.Clear();
            atk.Add(Kit.Attack(a0, r, 1.1f, rangeInner: 14f, rangeOuter: 30f, rangeRetreat: 0f));
            Kit.SetSpecial(p, Kit.Attack(sp, lamp.Build(), 0f, rangeInner: 30f, rangeOuter: 110f, rangeRetreat: 25f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 13f);
        }

        // Candelabra: Five Flames (they fork over wax); Vigil (plants 1.5 s, lights wax within 40 px, 3 flames at the hero)
        static void CandelabraKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            var fan = new List<int>();
            foreach (var a in new[] { -30f, -15f, 0.01f, 15f, 30f }) fan.Add(Kit.AddEffect(p, VhorrulFx.CandelabraFlame, offsetX: 7f, offsetY: 17f, angle: a));
            int single = Kit.AddEffect(p, VhorrulFx.CandelabraFlame, offsetX: 7f, offsetY: 17f, angle: -5f, angleMax: 5f);
            var f = Kit.Shot(sh, "Fan", "ModCandelabraFan", 3, v, 0f, fan.ToArray()).Build();
            var vigil = new ClipBuilder(sh, "Vigil", "ModCandelabraVigil").Once().Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop")
                .EvF(1, "VhLightWax", 40f).EvO(1, "AnimSound", v);
            foreach (int k in new[] { 3, 5, 7 }) vigil.Ev(k - 1, "VhFaceHero").Ev(k, "AnimAttack", single);
            vigil.Ev(-1, "AnimRun");
            atk.Clear();
            atk.Add(Kit.Attack(a0, f, 1.8f, rangeInner: 45f, rangeOuter: 105f, rangeRetreat: 38f));
            Kit.SetSpecial(p, Kit.Attack(sp, vigil.Build(), 0f, rangeInner: 30f, rangeOuter: 120f, rangeRetreat: 30f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 15f);
        }

        // ================================================================================================ tier 3
        // Tallow Colossus: Fist One-Two; Topple (rears over its shadow, falls flat, lies 1 s, leaves a slick); Accrete
        static void ColossusKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int fist = Kit.AddEffect(p, VhorrulFx.ColossusFist, attach: true, destroyOnAnimEnd: true, offsetX: 13.2f, offsetY: 13.2f);
            var slots = new int[VhorrulFx.ToppleHit.Length];
            for (int i = 0; i < slots.Length; i++)
                slots[i] = Kit.AddEffect(p, VhorrulFx.ToppleHit[i], offsetX: (4f + (28f + 10f * i) * 0.5f) * 1.1f, offsetY: 6.6f);
            ColossusAccrete.ToppleSlots = slots;
            ColossusAccrete.Idles = new[] { null, new ClipBuilder(sh, "Idle1", "ModColossusIdle1").Loop().Build(),
                new ClipBuilder(sh, "Idle2", "ModColossusIdle2").Loop().Build(), new ClipBuilder(sh, "Idle3", "ModColossusIdle3").Loop().Build() };
            ColossusAccrete.Runs = new[] { null, new ClipBuilder(sh, "Run1", "ModColossusRun1").Loop().Build(),
                new ClipBuilder(sh, "Run2", "ModColossusRun2").Loop().Build(), new ClipBuilder(sh, "Run3", "ModColossusRun3").Loop().Build() };
            var fists = Kit.Melee(sh, "Fists", "ModColossusFists", v, 2, fist, 45f, 4, fist, 45f).Build();
            // Rear 4 (0.8 s) + Fall 3 + Prone 2 x2 (1 s) + GetUp 4
            var topple = new ClipBuilder(sh, "Rear", "ModColossusTopple").Once().Then("Fall").Then("Prone", 2).Then("GetUp")
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(0, "VhToppleShadow").EvO(0, "AnimSound", v)
                .Ev(3, "AnimInputMultiplyStop").Ev(3, "AnimInputOff").Ev(5, "VhToppleLand").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, fists, 1.0f, rangeInner: 14f, rangeOuter: 30f));
            Kit.SetSpecial(p, Kit.Attack(sp, topple, 0f, rangeInner: 12f, rangeOuter: 34f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 11f);
        }

        // Pyre Warden: Censer Smash (an ember ring that lights wax); Stoke (the fire nearest the hero spreads in rings)
        static void PyreWardenKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p) ?? a0; var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int smash = Kit.AddEffect(p, VhorrulFx.CenserSmash, offsetX: 23.9f, offsetY: 0.01f);
            Kit.AimReach(p, smash, 5f, 5f);
            var s = new ClipBuilder(sh, "Smash", "ModVhWardenSmash").Once().EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(2, "AnimInputMultiplyStop")
                .Ev(2, "AnimInputOff").Ev(4, "AnimAttack", smash).EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            var stoke = new ClipBuilder(sh, "Stoke", "ModVhWardenStoke").Once().Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop")
                .Ev(4, "VhStoke").EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, s, 1.6f, rangeInner: 10f, rangeOuter: 30f, rangeRetreat: 0f));
            Kit.EnableSpecial(p, Kit.Attack(sp, stoke, 0f, rangeInner: 0f, rangeOuter: 80f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 17.6f);
        }

        // Tallow Renderer: Ladle Fling (boiling tallow, slows); Boil Over (rides its own wave 70 px, swings the ladle)
        static void RendererKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p) ?? a0; var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int fan = Kit.AddEffect(p, VhorrulFx.LadleFan, attach: true, destroyOnAnimEnd: true, offsetX: 29f, offsetY: 14.5f);
            int wave = Kit.AddEffect(p, VhorrulFx.BoilWave, offsetX: 17.4f, offsetY: 11.6f);
            int swing = Kit.AddEffect(p, VhorrulFx.LadleSwing, attach: true, destroyOnAnimEnd: true, offsetX: 20.3f, offsetY: 14.5f);
            var l = Kit.Melee(sh, "Ladle", "ModVhRendererLadle", v, 3, fan, 0f).Build();
            // Tip 4 (wave out on f3) + Ride 4 x2 (0.64 s at the wave's 115 px/s: about 70 px) + Swing 5 (hit on f2)
            var boil = new ClipBuilder(sh, "Tip", "ModVhRendererBoil").Once().Then("Ride", 2).Then("Swing")
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff")
                .Ev(3, "AnimAttack", wave).EvO(3, "AnimSound", v).Ev(3, "VhRide").EvF(3, "AnimMove", 112f)
                .Ev(12, "AnimMoveStop").Ev(12, "VhRideEnd").Ev(14, "AnimAttack", swing).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, l, 1.4f, rangeInner: 14f, rangeOuter: 34f, rangeRetreat: 0f));
            Kit.EnableSpecial(p, Kit.Attack(sp, boil, 0f, rangeInner: 20f, rangeOuter: 80f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 14.5f);
        }

        // Wick Hag: Hex Flame (may burn, lights wax); Poppet (a wax poppet of the hero: he feels its burns)
        static void WickHagKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p) ?? a0; var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int hex = Kit.AddEffect(p, VhorrulFx.HexFlame, offsetX: 13.9f, offsetY: 11.6f);
            var h = Kit.Shot(sh, "Hex", "ModVhHagHex", 3, v, 0f, hex).Build();
            var pop = new ClipBuilder(sh, "Poppet", "ModVhHagPoppet").Once().Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop").Ev(4, "VhPoppet")
                .EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, h, 1.3f, rangeInner: 40f, rangeOuter: 100f, rangeRetreat: 30f));
            Kit.EnableSpecial(p, Kit.Attack(sp, pop, 0f, rangeInner: 30f, rangeOuter: 120f, rangeRetreat: 25f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 11.6f);
        }

        // Candle Wyrm: Rear Strike (30 px ahead, may burn); Wick Coil (a lit ring round the hero that tightens); swims
        static void CandleWyrmKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p) ?? a0; var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int strike = Kit.AddEffect(p, VhorrulFx.WyrmStrike, attach: true, destroyOnAnimEnd: true, offsetX: 25.1f, offsetY: 6.8f);
            var s = new ClipBuilder(sh, "Strike", "ModVhWyrmStrike").Once().EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(2, "AnimInputMultiplyStop")
                .Ev(2, "AnimInputOff").Ev(3, "AnimAttack", strike).EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            var c = new ClipBuilder(sh, "Coil", "ModVhWyrmCoil").Once().Ev(0, "AnimInputOff").Ev(0, "VhCoil").EvO(0, "AnimSound", v).Ev(-1, "AnimRun").Build();
            WyrmCoil.CoilLoop = new ClipBuilder(sh, "Coil", "ModVhWyrmCoilLoop").Loop().Build();
            WyrmCoil.WyrmSwim = new ClipBuilder(sh, "Swim", "ModVhWyrmSwim").Loop().Build(); WyrmCoil.WyrmSwimRun = new ClipBuilder(sh, "SwimRun", "ModVhWyrmSwimRun").Loop().Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, s, 1.2f, rangeInner: 16f, rangeOuter: 34f, rangeRetreat: 0f));
            Kit.EnableSpecial(p, Kit.Attack(sp, c, 0f, rangeInner: 10f, rangeOuter: 70f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 11.4f);
        }

        // Fuse Scorpion: Twin Snap; Light the Fuse (a spark that runs the hero's own footsteps)
        static void FuseScorpionKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p) ?? a0; var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int snap = Kit.AddEffect(p, VhorrulFx.ScorpSnap, attach: true, destroyOnAnimEnd: true, offsetX: 21.6f, offsetY: 6.8f);
            var s = Kit.Melee(sh, "Snap", "ModVhScorpSnap", v, 3, snap, 70f).Build();
            var f = new ClipBuilder(sh, "Sting", "ModVhScorpSting").Once().EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(2, "AnimInputMultiplyStop")
                .Ev(2, "AnimInputOff").Ev(3, "VhLightFuse").EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, s, 1.0f, rangeInner: 12f, rangeOuter: 30f, rangeRetreat: 0f));
            // the spark wants room to chase: sting from mid range
            Kit.EnableSpecial(p, Kit.Attack(sp, f, 0f, rangeInner: 30f, rangeOuter: 110f, rangeRetreat: 20f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 8.1f);
        }

        // Grub Mother: Head Slam (leaves a wax pool); Brood Spit (3 grublings by the hero; lit ones burst as fire)
        static void BroodMotherKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p) ?? a0; var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int slam = Kit.AddEffect(p, VhorrulFx.MotherSlam, attach: true, destroyOnAnimEnd: true, offsetX: 16f, offsetY: 4f);
            int pool = Kit.AddEffect(p, VhorrulFx.WaxPuddle, offsetX: 18f, offsetY: 0.01f);
            var grubs = new List<int>();
            foreach (var o in new[] { new Vector2(14f, 8f), new Vector2(-14f, 8f), new Vector2(0.01f, -14f) })
                grubs.Add(Kit.AddEffect(p, VhorrulFx.Grubling, offsetX: o.x, offsetY: o.y, spawnPoint: DamageEffectData.eSpawnPoint.ClosestEnemy));
            var s = Kit.Melee(sh, "Slam", "ModVhBroodSlam", v, 3, slam, 0f).Ev(3, "AnimAttack", pool).Build();
            var spit = new ClipBuilder(sh, "Spit", "ModVhBroodSpit").Once().Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop");
            for (int i = 0; i < grubs.Count; i++) spit.Ev(4, "AnimAttack", grubs[i], i * 0.08f);
            spit.EvO(4, "AnimSound", v).Ev(-1, "AnimRun");
            atk.Clear();
            atk.Add(Kit.Attack(a0, s, 1.4f, rangeInner: 12f, rangeOuter: 30f, rangeRetreat: 0f));
            Kit.EnableSpecial(p, Kit.Attack(sp, spit.Build(), 0f, rangeInner: 20f, rangeOuter: 130f, rangeRetreat: 25f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 8f);
        }

        // Pyre Tick: Barbed Bite (gives the hero a fever); Ember Spray (5 drops of burning blood that land as fire)
        static void PyreTickKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p) ?? a0; var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int bite = Kit.AddEffect(p, VhorrulFx.TickBite, attach: true, destroyOnAnimEnd: true, offsetX: 19.6f, offsetY: 12.6f);
            var drops = new List<int>();
            foreach (var a in new[] { -30f, -15f, 0.01f, 15f, 30f }) drops.Add(Kit.AddEffect(p, VhorrulFx.TickDrop, offsetX: 19.6f, offsetY: 1.4f, angle: a));
            var b = Kit.Melee(sh, "Bite", "ModVhTickBite", v, 3, bite, 75f).Build();
            var s = Kit.Shot(sh, "Spray", "ModVhTickSpray", 4, v, 0.03f, drops.ToArray()).Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, b, 1.1f, rangeInner: 12f, rangeOuter: 28f, rangeRetreat: 0f));
            Kit.EnableSpecial(p, Kit.Attack(sp, s, 0f, rangeInner: 15f, rangeOuter: 60f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 11.2f);
        }

        // Ashen Seraph: Lance Thrust (reach 34); Ash to Ash (fires within 50 px go out and chase the hero as ash)
        static void SeraphKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int lance = Kit.AddEffect(p, VhorrulFx.SeraphLance, attach: true, destroyOnAnimEnd: true, offsetX: 20.2f, offsetY: 16.7f);
            var l = Kit.Melee(sh, "Lance", "ModSeraphLance", v, 3, lance, 120f).Build();
            var beat = new ClipBuilder(sh, "Beat", "ModSeraphBeat").Once().Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop").Ev(2, "VhSmother")
                .EvO(2, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, l, 1.3f, rangeInner: 18f, rangeOuter: 40f, rangeRetreat: 0f));
            Kit.SetSpecial(p, Kit.Attack(sp, beat, 0f, rangeInner: 0f, rangeOuter: 70f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 16.7f);
        }

        // Lantern Wraith: Soul Orb (bursts); Take the Light (a 50 px cone that takes the hero's soul flame)
        static void WraithKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int orb = Kit.AddEffect(p, VhorrulFx.LanternOrb, offsetX: 23.2f, offsetY: 26.1f);
            var s = Kit.Shot(sh, "Swing", "ModWraithSwing", 3, v, 0f, orb).Build();
            var take = new ClipBuilder(sh, "Take", "ModWraithTake").Once().EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(2, "AnimInputMultiplyStop")
                .Ev(2, "AnimInputOff").Ev(3, "VhTakeLight").EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            WraithLantern.IdleFull = new ClipBuilder(sh, "IdleFull", "ModWraithIdleFull").Loop().Build(); WraithLantern.RunFull = new ClipBuilder(sh, "RunFull", "ModWraithRunFull").Loop().Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, s, 1.6f, rangeInner: 45f, rangeOuter: 82f, rangeRetreat: 38f));
            Kit.SetSpecial(p, Kit.Attack(sp, take, 0f, rangeInner: 10f, rangeOuter: 46f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 23.2f);
        }

        // Grand Chandelier: Wheel of Flames (burns all round, flings 4 wax globs); Drip and Flare (a ring of wax, then lit)
        static void ChandelierKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int wheel = Kit.AddEffect(p, VhorrulFx.WheelFire, attach: true, destroyOnAnimEnd: true, offsetX: 0.01f, offsetY: 15f);
            var globs = new List<int>();
            foreach (var a in new[] { 35f, 145f, -35f, -145f }) globs.Add(Kit.AddEffect(p, VhorrulFx.ChandelierGlob, offsetX: 0.01f, offsetY: 1f, angle: a));
            var w = new ClipBuilder(sh, "Wheel", "ModChandelierWheel").Once().Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop").Ev(2, "AnimAttack", wheel)
                .EvO(2, "AnimSound", v);
            for (int i = 0; i < globs.Count; i++) w.Ev(5, "AnimAttack", globs[i], i * 0.01f);
            w.Ev(-1, "AnimRun");
            var df = new ClipBuilder(sh, "Drip", "ModChandelierDripFlare").Once().Then("Flare")
                .Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop").Ev(0, "VhDrip").Ev(7, "VhFlare").EvO(7, "AnimSound", v).Ev(-1, "AnimRun").Build();
            ChandelierHang.IdleHigh = new ClipBuilder(sh, "IdleHigh", "ModChandelierIdleHigh").Loop().Build();
            ChandelierHang.RunHigh = new ClipBuilder(sh, "RunHigh", "ModChandelierRunHigh").Loop().Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, w.Build(), 1.6f, rangeInner: 0f, rangeOuter: 20f, rangeRetreat: 0f));
            // the ring is 30 px out: stand the hero on it
            Kit.SetSpecial(p, Kit.Attack(sp, df, 0f, rangeInner: 18f, rangeOuter: 38f, rangeRetreat: 0f), 7.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 14f);
        }

        // Votive Reliquary: Votive Fan (3 flames, 5 when anointed); Anoint (its kin's next 2 hits burn and light wax)
        static void ReliquaryKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            var three = new List<int>();
            foreach (var a in new[] { -12f, 0.01f, 12f }) three.Add(Kit.AddEffect(p, VhorrulFx.VotiveFlame, offsetX: 6.7f, offsetY: 17.9f, angle: a));
            var five = new List<int>();
            foreach (var a in new[] { -24f, -12f, 0.01f, 12f, 24f }) five.Add(Kit.AddEffect(p, VhorrulFx.VotiveFlame, offsetX: 6.7f, offsetY: 17.9f, angle: a));
            var f3 = Kit.Shot(sh, "Fan", "ModVhReliquaryFan", 2, v, 0.04f, three.ToArray()).Build();
            var f5 = Kit.Shot(sh, "Fan", "ModVhReliquaryFan5", 2, v, 0.03f, five.ToArray()).Build();
            var an = new ClipBuilder(sh, "Anoint", "ModVhReliquaryAnoint").Once().Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop").Ev(3, "VhAnoint")
                .EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, f3, 1.5f, rangeInner: 40f, rangeOuter: 100f, rangeRetreat: 32f));
            atk.Add(Kit.Attack(a0, f5, 1.5f, rangeInner: 40f, rangeOuter: 100f, rangeRetreat: 32f));
            Kit.SetSpecial(p, Kit.Attack(sp, an, 0f, rangeInner: 0f, rangeOuter: 140f, rangeRetreat: 30f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 17.9f);
        }

        // ================================================================================================ the god
        public static readonly List<MonsterDef> Monsters = new List<MonsterDef>
        {
            // ---- tier 1 (starters) ----
            new MonsterDef { id = "Wickling", basePrefab = "EnemyGiantRat_Fireball", health = 3.5f, speedMult = 1.05f, evolveCost = 0f,
                             evolveTo = new[] { "WaxenKnight", "Chandler" }, kit = WicklingKit, customize = PyreOnDeath },
            new MonsterDef { id = "TallowGrub", basePrefab = "EnemyMushroom", health = 4.5f, evolveCost = 0f,
                             evolveTo = new[] { "VhWickworm", "VhTallowSow" }, kit = GrubKit, customize = PyreOnDeath },
            new MonsterDef { id = "AshMoth", basePrefab = "EnemyFlyingEye_Dodge", health = 3f, speedMult = 1.1f, evolveCost = 0f,
                             evolveTo = new[] { "MothMatron", "Candelabra" }, kit = AshMothKit, customize = PyreOnDeath },
            // ---- tier 2 ----
            new MonsterDef { id = "WaxenKnight", basePrefab = "EnemyOrc", health = 7f, evolveCost = 2.5f,
                             evolveTo = new[] { "TallowColossus", "VhPyreWarden" }, kit = WaxenKnightKit, customize = PyreOnDeath },
            new MonsterDef { id = "Chandler", basePrefab = "EnemySkeletonMage", health = 5.5f, evolveCost = 2.5f, damageMult = 1.4f,
                             evolveTo = new[] { "VhRenderer", "VhWickHag" }, kit = ChandlerKit, customize = PyreOnDeath },
            new MonsterDef { id = "VhWickworm", basePrefab = "EnemyDemonSnake", health = 6f, speedMult = 1.05f, evolveCost = 2.5f, damageMult = 1.2f,
                             evolveTo = new[] { "VhCandleWyrm", "VhFuseScorpion" }, kit = WickwormKit, customize = PyreOnDeath },
            new MonsterDef { id = "VhTallowSow", basePrefab = "EnemyBlobfish", health = 6.5f, evolveCost = 2.5f, damageMult = 1.4f,
                             evolveTo = new[] { "VhBroodMother", "VhPyreTick" }, kit = SowKit, customize = PyreOnDeath },
            new MonsterDef { id = "MothMatron", basePrefab = "EnemyWildShaman", health = 5.5f, evolveCost = 2.5f, damageMult = 1.3f,
                             evolveTo = new[] { "VhAshSeraph", "LanternWraith" }, kit = MatronKit, customize = PyreOnDeath },
            new MonsterDef { id = "Candelabra", basePrefab = "EnemySkeletonPope", health = 7f, speedMult = 0.85f, evolveCost = 2.5f, damageMult = 1.1f,
                             evolveTo = new[] { "VhChandelier", "VhReliquary" }, kit = CandelabraKit, customize = PyreOnDeath },
            // ---- tier 3 ----
            new MonsterDef { id = "TallowColossus", basePrefab = "EnemyTroll", health = 14f, evolveCost = 4.5f, damageMult = 0.9f, kit = ColossusKit, customize = PyreOnDeath },
            new MonsterDef { id = "VhPyreWarden", basePrefab = "EnemySkeletonGiantShield", health = 14f, speedMult = 0.85f, evolveCost = 4.5f, damageMult = 1.1f,
                             kit = PyreWardenKit, customize = PyreOnDeath },
            new MonsterDef { id = "VhRenderer", basePrefab = "EnemyGhoul", health = 13.5f, speedMult = 0.9f, evolveCost = 4.5f, damageMult = 1.1f,
                             kit = RendererKit, customize = PyreOnDeath },
            new MonsterDef { id = "VhWickHag", basePrefab = "EnemyWitch", health = 12.5f, evolveCost = 4.5f, damageMult = 1.2f, kit = WickHagKit, customize = PyreOnDeath },
            new MonsterDef { id = "VhCandleWyrm", basePrefab = "EnemySmallDragon", health = 13.5f, speedMult = 0.9f, evolveCost = 4.5f,
                             kit = CandleWyrmKit, customize = PyreOnDeath },
            new MonsterDef { id = "VhFuseScorpion", basePrefab = "EnemyScorpion", health = 13f, evolveCost = 4.5f, kit = FuseScorpionKit, customize = PyreOnDeath },
            new MonsterDef { id = "VhBroodMother", basePrefab = "EnemyGiantBlobfish", health = 14f, evolveCost = 4.5f, damageMult = 1.1f, kit = BroodMotherKit,
                             customize = BroodOnDeath },
            new MonsterDef { id = "VhPyreTick", basePrefab = "EnemyGiantSpider_SpitWebs", health = 13f, evolveCost = 4.5f, damageMult = 1.1f, kit = PyreTickKit, customize = PyreOnDeath },
            new MonsterDef { id = "VhAshSeraph", art = "VhAshSeraph", basePrefab = "EnemyCapraDemon", health = 12.5f, evolveCost = 4.5f, damageMult = 1.1f,
                             kit = SeraphKit, customize = PyreOnDeath },
            new MonsterDef { id = "LanternWraith", basePrefab = "EnemyPriestess", health = 12.5f, evolveCost = 4.5f, damageMult = 1.2f, kit = WraithKit, customize = PyreOnDeath },
            new MonsterDef { id = "VhChandelier", art = "VhChandelier", basePrefab = "EnemyDarkGuardian", health = 14f, speedMult = 0.9f, evolveCost = 4.5f, damageMult = 1.2f,
                             kit = ChandelierKit, customize = PyreOnDeath },
            new MonsterDef { id = "VhReliquary", basePrefab = "EnemyFacelessShaman", health = 13f, speedMult = 0.9f, evolveCost = 4.5f, damageMult = 0.9f,
                             kit = ReliquaryKit, customize = PyreOnDeath },
        };

        /// <summary>Each monster's quirk (every Vhorrul monster has exactly one <see cref="VhorrulBehaviour"/>).</summary>
        static readonly Dictionary<string, Func<MonsterTraits, MonsterTraits>> Quirks = new Dictionary<string, Func<MonsterTraits, MonsterTraits>>
        {
            { "Wickling", t => t.Add<WicklingRelight>() }, { "TallowGrub", t => t.Add<GrubGlide>() }, { "AshMoth", t => t.Add<MothDrawn>() },
            { "WaxenKnight", t => t.Add<KnightKindle>() }, { "VhWickworm", t => t.Add<WaxSwimmer>() }, { "VhTallowSow", t => t.Add<SowGreased>() },
            { "TallowColossus", t => t.Add<ColossusAccrete>() }, { "VhPyreWarden", t => t.Add<WardenKeeper>() },
            { "VhRenderer", t => t.Add<RendererRide>() }, { "VhWickHag", t => t.Add<HagSympathy>() }, { "VhCandleWyrm", t => t.Add<WyrmCoil>() },
            { "VhFuseScorpion", t => t.Add<ScorpionFuse>() }, { "VhAshSeraph", t => t.Add<SeraphSmother>() },
            { "LanternWraith", t => t.Add<WraithLantern>() }, { "VhChandelier", t => t.Add<ChandelierHang>() },
            { "VhReliquary", t => t.Add<ReliquaryAnoint>() },
        };

        /// <summary>The tallow monsters: they heal standing in unlit wax.</summary>
        static readonly string[] Tallow = { "TallowGrub", "Chandler", "TallowColossus", "VhTallowSow", "VhBroodMother", "VhRenderer" };

        public static readonly GodDef God = new GodDef
        {
            name = "Vhorrul",
            text = "Dead burn as pyres, then wax",
            flavour = "The Tallow Saint burns\nthe dead and keeps the wax.",
            winText = "THE CANDLES GUTTER OUT",
            portraitArt = "DeityVhorrul",
            startingMonsters = new[] { "Wickling", "TallowGrub", "AshMoth" },
        };

        /// <summary>The god's perk: a Vhorrul monster burns as a pyre where it falls, which cools into a tallow slick.</summary>
        static void PyreOnDeath(GameObject go, Player p)
        {
            Kit.AddDeathSpawn(p, VhorrulFx.Pyre ?? VhorrulFx.BurningPool);
            Strike.DeathAtFeet(p);
            GodArt.UseHitSplat(p, VhorrulFx.HitSplat);
        }

        static void BroodOnDeath(GameObject go, Player p)
        {
            Kit.AddDeathSpawn(p, VhorrulFx.GrubBrood);
            PyreOnDeath(go, p);
        }

        public static void Register()
        {
            VhorrulFx.Build();
            AnointInd = ModStatus.Indicator("ModIndVhAnoint", "FxVhAnoint", "Loop", 1f, OverlayAt.Head);
            foreach (var m in Monsters)
            {
                var t = new MonsterTraits();
                Func<MonsterTraits, MonsterTraits> q;
                if (Quirks.TryGetValue(m.id, out q)) q(t); else t.Add<VhorrulMonster>();
                if (Array.IndexOf(Tallow, m.id) >= 0) t.regenAt = WaxPuddleFx.HealsAt;
                MonsterTraits.Register(m.PrefabName, t);
            }
            foreach (var m in Monsters) MonsterFactory.Build(m);
            MonsterFactory.LinkEvolutions(Monsters);
            s_deity = DeityFactory.Register(God);
            Strike.KeepAllScales();
            MonsterEvents.AttackSpawned += OnAttackSpawned;
            var prev = SlotGods.PortraitFor;
            SlotGods.PortraitFor = (tier, perk) => tier == SlotTier.Gold && perk != null && perk == s_deity ? Idol() : (prev != null ? prev(tier, perk) : null);
        }

        static exSpriteAnimClip Idol()
        {
            if (s_idol == null) s_idol = SlotArt.Clip("DeityGoldIdolVhorrul", "Idle");
            return s_idol;
        }

        static void OnAttackSpawned(Player owner, GameObject fx, GameObject template)
        {
            if (owner == null || fx == null) return;
            if (owner.gameObject == ModUtil.Hero()) { VhPoppetFx.HeroStruck(fx.transform.position); return; }
            var q = owner.GetComponent<VhorrulBehaviour>();
            if (q != null) q.OnAttackSpawned(fx, template);
        }
    }
}
