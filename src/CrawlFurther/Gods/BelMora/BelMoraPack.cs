using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.BelMora
{
    using CrawlFurther.Art;
    using CrawlFurther.Gods;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Bel'Mora, the Drowned Bell: the tide always returns. Rising Tide (<see cref="BelTide"/>) is the god's perk, and
    /// every monster has a quirk of its own (a <see cref="BelBehaviour"/>) built on the tide, hooks and currents, with a
    /// tell the hero can read. Offsets below are the sprite's sync points (art/out_belmora/TIMING.md), x forward, y up.
    /// </summary>
    public static class BelMoraPack
    {
        static exSpriteAnimClip Looped(SpriteSheet sh, string anim, string clip)
        {
            return sh.Has(anim) ? new ClipBuilder(sh, anim, clip).Loop().Build() : null;
        }

        static ClipBuilder Still(SpriteSheet sh, string anim, string clip)
        {
            return new ClipBuilder(sh, anim, clip).Once().Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop");
        }

        // ---------------------------------------------------------------------------------------------- tier 1
        // Bell Urchin: curls up and rolls into the hero; Spine Ring fires eight spines all round. Quirk: UrchinGrip.
        static void UrchinKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int roll = Kit.AddEffect(p, BelMoraFx.UrchinRoll, attach: true, destroyOnAnimEnd: true, offsetX: 1f, offsetY: 6f);
            var ring = new List<int>();
            for (int i = 0; i < 8; i++)
                ring.Add(Kit.AddEffect(p, BelMoraFx.Spine, offsetY: 6f, angle: i == 0 ? 0.01f : i * 45f, spawnPoint: DamageEffectData.eSpawnPoint.Position));
            var rl = new ClipBuilder(sh, "Roll", "ModUrchinRoll").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff")
                .EvF(2, "AnimMove", 160f).Ev(2, "AnimAttack", roll).EvO(2, "AnimSound", v).Ev(6, "AnimMoveStop").Ev(-1, "AnimRun").Build();
            var br = Still(sh, "Bristle", "ModUrchinBristle");
            foreach (var r in ring) br.Ev(3, "AnimAttack", r);
            br.EvO(3, "AnimSound", v).Ev(-1, "AnimRun");
            atk.Clear();
            // the roll lasts 0.24 s at 160 px/s: about 40 px
            atk.Add(Kit.Attack(a0, rl, 1.5f, rangeInner: 16f, rangeOuter: 44f));
            Kit.SetSpecial(p, Kit.Attack(sp, br.Build(), 0f, rangeInner: 0f, rangeOuter: 50f, rangeRetreat: 0f), 5.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 6f);
            UrchinGrip.GripIdle = Looped(sh, "IdleGrip", "ModUrchinIdleGrip");
        }

        // Lurefish: a snapping lunge; Lure casts the light, tugs the hero in and bites. Quirk: LureBait.
        static void LurefishKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int bite = Kit.AddEffect(p, BelMoraFx.LureBite, attach: true, destroyOnAnimEnd: true, offsetX: 10f, offsetY: 6f);
            var ch = Kit.Melee(sh, "Chomp", "ModLureChomp", v, 3, bite, 70f).Build();
            var lure = Still(sh, "Lure", "ModLureLure").Ev(2, "BelLureTug").Ev(6, "AnimAttack", bite).EvO(6, "AnimSound", v).Ev(-1, "AnimRun");
            atk.Clear();
            atk.Add(Kit.Attack(a0, ch, 1.2f, rangeInner: 10f, rangeOuter: 24f));
            // the tug reaches 40 px, 85 with a fully lit lure
            Kit.SetSpecial(p, Kit.Attack(sp, lure.Build(), 0f, rangeInner: 20f, rangeOuter: 70f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 7f);
            LureBait.LitIdle = new exSpriteAnimClip[3]; LureBait.LitRun = new exSpriteAnimClip[3];
            for (int k = 0; k < 3; k++)
            {
                LureBait.LitIdle[k] = Looped(sh, "IdleLit" + (k + 1), "ModLureIdleLit" + (k + 1));
                LureBait.LitRun[k] = Looped(sh, "RunLit" + (k + 1), "ModLureRunLit" + (k + 1));
            }
        }

        // Barnacle Crab: a heavy pinch; Shell hunkers down (can't be hit) and grows a barnacle plate. Quirk: CrabSidle.
        static void CrabKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int pinch = Kit.AddEffect(p, BelMoraFx.CrabPinch, attach: true, offsetX: 5f, offsetY: 6f);   // claw shuts at (13, -6)
            var pn = Kit.Melee(sh, "Pinch", "ModCrabPinch", v, 3, pinch, 50f).Build();
            var shell = Still(sh, "Shell", "ModCrabShell").Ev(2, "AnimStartInvincibility")
                .Ev(3, "ModGainPlates", 1).EvO(3, "AnimSound", v).Ev(6, "AnimStopInvincibility").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, pn, 1.2f, rangeInner: 10f, rangeOuter: 22f));
            Kit.SetSpecial(p, Kit.Attack(sp, shell, 0f, rangeInner: 0f, rangeOuter: 40f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 5f);
            CrabSidle.SidleRun = Looped(sh, "Sidle", "ModCrabSidle");
        }

        // ---------------------------------------------------------------------------------------------- tier 2
        // Bell Diver: an anchor slam with a quake ring; Chain Hook reels the hero in. Quirk: DiverAnchor.
        static void DiverKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int slam = Kit.AddEffect(p, BelMoraFx.AnchorSlam, attach: true, destroyOnAnimEnd: true, offsetX: 11f, offsetY: 5f);
            int quake = Kit.AddEffect(p, BelMoraFx.AnchorQuake, offsetX: 13f, offsetY: 0.01f);
            int hook = Kit.AddEffect(p, BelMoraFx.Hook, offsetX: 12f, offsetY: 16f);
            int brine = Kit.AddEffect(p, BelMoraFx.Brine, offsetX: 16f, offsetY: 0.01f);
            // Combo: two anchor slams, then the Anchor Drop: a long lunge, the quake, and a pool of brine where it lands
            var an = Kit.Melee(sh, "Anchor", "ModDiverAnchor", v, 3, slam, 40f).Ev(4, "AnimAttack", quake);
            var an2 = Kit.Melee(sh, "Anchor", "ModDiverAnchor2", null, 3, slam, 50f).Speed(1.1f).Ev(4, "AnimAttack", quake).Build();
            var drop = Kit.Melee(sh, "Anchor", "ModDiverAnchorDrop", v, 3, slam, 100f).Speed(0.85f).Ev(4, "AnimAttack", quake).Ev(4, "AnimAttack", brine, 0.1f).Build();
            var hk = Kit.Shot(sh, "Hook", "ModDiverHook", 2, v, 0f, hook).Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, an.Build(), 0.4f, rangeInner: 12f, rangeOuter: 32f));
            atk.Add(Kit.Attack(a0, an2, 0.4f, rangeInner: 12f, rangeOuter: 34f));
            atk.Add(Kit.Attack(a0, drop, 1.9f, rangeInner: 14f, rangeOuter: 46f));
            // the hook flies about 95 px
            Kit.SetSpecial(p, Kit.Attack(sp, hk, 0f, rangeInner: 40f, rangeOuter: 95f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 12f);
            DiverAnchor.HaulClip = Looped(sh, "Haul", "ModDiverHaul");
        }

        // Spinewalker: spears the floor with a stilt; Spined Eggs drops three eggs. Quirk: the eggs drift in brine (SpineEggFx).
        static void SpinewalkerKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int stab = Kit.AddEffect(p, BelMoraFx.StiltStab, attach: true, destroyOnAnimEnd: true, offsetX: 12f, offsetY: 3f);
            var eggs = new List<int>();
            foreach (var o in new[] { new Vector2(14f, 0.01f), new Vector2(-12f, 4f), new Vector2(2f, -9f) })
                eggs.Add(Kit.AddEffect(p, BelMoraFx.SpineEgg, offsetX: o.x, offsetY: o.y, spawnPoint: DamageEffectData.eSpawnPoint.Position));
            int w1 = Kit.AddEffect(p, BelMoraFx.StiltStab, offsetX: 26f, offsetY: 3f);
            int w2 = Kit.AddEffect(p, BelMoraFx.StiltStab, offsetX: 40f, offsetY: 3f);
            // Combo: two stabs, then the Stilt Walk: it strides in, spearing the floor three times further and further ahead
            var st = Kit.Melee(sh, "Stab", "ModSpinewalkerStab", v, 2, stab, 40f).Build();
            var st2 = Kit.Melee(sh, "Stab", "ModSpinewalkerStab2", null, 2, stab, 50f).Speed(1.15f).Build();
            var walk = Kit.Melee(sh, "Stab", "ModSpinewalkerWalk", v, 2, stab, 70f).Speed(0.85f).Ev(2, "AnimAttack", w1, 0.1f).Ev(2, "AnimAttack", w2, 0.2f).Build();
            var sw = Still(sh, "Sow", "ModSpinewalkerSow");
            for (int i = 0; i < eggs.Count; i++) sw.Ev(4, "AnimAttack", eggs[i], i * 0.05f);
            sw.EvO(4, "AnimSound", v).Ev(-1, "AnimRun");
            atk.Clear();
            atk.Add(Kit.Attack(a0, st, 0.35f, rangeInner: 10f, rangeOuter: 24f));
            atk.Add(Kit.Attack(a0, st2, 0.35f, rangeInner: 10f, rangeOuter: 26f));
            atk.Add(Kit.Attack(a0, walk, 1.7f, rangeInner: 12f, rangeOuter: 46f));
            Kit.SetSpecial(p, Kit.Attack(sp, sw.Build(), 0f, rangeInner: 0f, rangeOuter: 60f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.55f);
            Strike.Feet(p, n0, 8f);
            var esh = SpriteSheets.Get("FxBelSpineEgg");
            if (esh != null) { SpineEggFx.DriftClip = Looped(esh, "Drift", "ModBelSpineEggDrift"); SpineEggFx.IdleClip = Looped(esh, "Idle", "ModBelSpineEggIdle"); }
        }

        // Salt Siren: a slowing water bolt; Song tugs the hero in and wells brine under him. Quirk: SirenTidesong.
        static void SirenKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int bolt = Kit.AddEffect(p, BelMoraFx.WaterBolt, offsetX: 11f, offsetY: 15f);
            int note = Kit.AddEffect(p, BelMoraFx.SongNote, offsetX: 1f, offsetY: 19f, attach: true);
            int brine = Kit.AddEffect(p, BelMoraFx.Brine, spawnPoint: DamageEffectData.eSpawnPoint.ClosestEnemy);
            int wave = Kit.AddEffect(p, BelMoraFx.Wave, offsetX: 11f, offsetY: 4f);
            // Combo: two water bolts, then a breaking wave that rolls at the hero, leaving brine behind it
            var bl = Kit.Shot(sh, "Bolt", "ModSirenBolt", 3, v, 0f, bolt).Build();
            var bl2 = Kit.Shot(sh, "Bolt", "ModSirenBolt2", 3, null, 0f, bolt).Speed(1.15f).Build();
            var wv = Kit.Shot(sh, "Bolt", "ModSirenWave", 3, v, 0f, wave).Speed(0.85f).Build();
            var song = Still(sh, "Song", "ModSirenSong").Ev(1, "BelSong").Ev(1, "AnimAttack", note).EvO(1, "AnimSound", v)
                .Ev(3, "AnimAttack", brine).Ev(4, "AnimAttack", note).Ev(-1, "AnimRun");
            atk.Clear();
            atk.Add(Kit.Attack(a0, bl, 0.4f, rangeInner: 50f, rangeOuter: 110f, rangeRetreat: 40f));
            atk.Add(Kit.Attack(a0, bl2, 0.4f, rangeInner: 50f, rangeOuter: 110f, rangeRetreat: 40f));
            atk.Add(Kit.Attack(a0, wv, 2.2f, rangeInner: 30f, rangeOuter: 110f, rangeRetreat: 30f));
            Kit.SetSpecial(p, Kit.Attack(sp, song.Build(), 0f, rangeInner: 30f, rangeOuter: 110f, rangeRetreat: 20f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 15f);
        }

        // Brine Lamprey: a rasping bite; Undercurrent Lunge slides 70 px along the floor. Quirk: LampreyLatch.
        static void LampreyKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int bite = Kit.AddEffect(p, BelMoraFx.LampreyBite, attach: true, destroyOnAnimEnd: true, offsetX: 12f, offsetY: 7f);
            int lunge = Kit.AddEffect(p, BelMoraFx.LampreyLunge, attach: true, destroyOnAnimEnd: true, offsetX: 12f, offsetY: 6f);
            // Combo: two rasps, then a long darting rasp that bites twice as it goes, the second always opening a bleed
            var rs = Kit.Melee(sh, "Rasp", "ModLampreyRasp", v, 3, bite, 60f).Build();
            var rs2 = Kit.Melee(sh, "Rasp", "ModLampreyRasp2", null, 3, bite, 70f).Speed(1.15f).Build();
            int drain = Kit.AddEffect(p, FxKit.Finisher(BelMoraFx.LampreyBite, "ModLampreyBiteDrain", damageMult: 1.2f, status: FxFactory.GetStatus("StatusBleeding")),
                                      attach: true, destroyOnAnimEnd: true, offsetX: 12f, offsetY: 7f);
            var dart = Kit.Melee(sh, "Rasp", "ModLampreyDart", v, 2, lunge, 140f, 4, drain, 40f).Speed(0.9f).Build();
            // 0.16 s at 440 px/s: the 70 px lunge
            var ln = new ClipBuilder(sh, "Lunge", "ModLampreyLunge").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(1, "AnimInputMultiplyStop").Ev(1, "AnimInputOff")
                .Ev(2, "BelLungeOn").EvF(2, "AnimMove", 440f).Ev(2, "AnimAttack", lunge).EvO(2, "AnimSound", v)
                .Ev(5, "AnimMoveStop").Ev(5, "BelLungeOff").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, rs, 0.35f, rangeInner: 10f, rangeOuter: 26f));
            atk.Add(Kit.Attack(a0, rs2, 0.35f, rangeInner: 10f, rangeOuter: 28f));
            atk.Add(Kit.Attack(a0, dart, 1.6f, rangeInner: 12f, rangeOuter: 50f));
            Kit.SetSpecial(p, Kit.Attack(sp, ln, 0f, rangeInner: 30f, rangeOuter: 80f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.55f);
            Strike.Feet(p, n0, 7f);
            LampreyLatch.LatchedClip = Looped(sh, "Latched", "ModLampreyLatched");
        }

        // Bell Hermit: a lunging claw crush; Bell Down sets its bell down over itself. Quirk: HermitBell.
        static void HermitKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int crush = Kit.AddEffect(p, BelMoraFx.HermitCrush, attach: true, destroyOnAnimEnd: true, offsetX: 15f, offsetY: 4f);
            int peal = Kit.AddEffect(p, BelMoraFx.Peal, offsetX: 20f, offsetY: 0.01f);
            // Combo: two claw crushes, then the Pealing Crush: the claw rings its shell and a peal rolls out from it
            var cr = Kit.Melee(sh, "Crush", "ModHermitCrush", v, 3, crush, 40f).Build();
            var cr2 = Kit.Melee(sh, "Crush", "ModHermitCrush2", null, 3, crush, 50f).Speed(1.1f).Build();
            var pc = Kit.Melee(sh, "Crush", "ModHermitPealCrush", v, 3, crush, 60f).Speed(0.85f).Ev(3, "AnimAttack", peal).Build();
            var shell = Still(sh, "Shell", "ModHermitShell").Ev(2, "BelShellOn").EvO(2, "AnimSound", v).Ev(7, "BelShellOff").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, cr, 0.4f, rangeInner: 12f, rangeOuter: 30f));
            atk.Add(Kit.Attack(a0, cr2, 0.4f, rangeInner: 12f, rangeOuter: 32f));
            atk.Add(Kit.Attack(a0, pc, 1.8f, rangeInner: 12f, rangeOuter: 40f));
            Kit.SetSpecial(p, Kit.Attack(sp, shell, 0f, rangeInner: 0f, rangeOuter: 40f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 6f);
            HermitBell.FullIdle = Looped(sh, "IdleFull", "ModHermitIdleFull");
            HermitBell.FullRun = Looped(sh, "RunFull", "ModHermitRunFull");
        }

        // Anemone Boxer: a one-two with its anemone gloves; Hop In hops 30 px in and throws three stinging jabs. Quirk:
        // BoxerFootwork (it hops back after each punch).
        static void BoxerKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int jab = Kit.AddEffect(p, BelMoraFx.BoxerJab, attach: true, destroyOnAnimEnd: true, offsetX: 12f, offsetY: 9f);
            int sting = Kit.AddEffect(p, BelMoraFx.BoxerSting, attach: true, destroyOnAnimEnd: true, offsetX: 12f, offsetY: 9f);
            int fx = Kit.AddEffect(p, BelMoraFx.BoxerStingFx, attach: true, offsetX: 13f, offsetY: 9f);
            var jb = Kit.Melee(sh, "Jab", "ModBoxerJab", v, 2, jab, 40f, 4, jab, 20f);
            jb.Ev(2, "AnimAttack", fx).Ev(4, "AnimAttack", fx).Ev(-1, "BelHopBack");
            // Combo: the one-two twice, then the Flurry: three jabs and a stinging hook, stepping in, before it hops back
            var jb2 = Kit.Melee(sh, "Jab", "ModBoxerJab2", null, 2, jab, 40f, 4, jab, 20f).Speed(1.15f);
            jb2.Ev(2, "AnimAttack", fx).Ev(4, "AnimAttack", fx).Ev(-1, "BelHopBack");
            var fl = Kit.Melee(sh, "Jab", "ModBoxerFlurry", v, 2, jab, 40f, 4, jab, 20f, 9, jab, 40f, 11, sting, 70f).Repeat(2);
            fl.Ev(2, "AnimAttack", fx).Ev(4, "AnimAttack", fx).Ev(9, "AnimAttack", fx).Ev(11, "AnimAttack", fx).Ev(-1, "BelHopBack");
            var hop = new ClipBuilder(sh, "HopIn", "ModBoxerHopIn").Once().EvF(0, "AnimInputMultiplyFreeFace", 0f)
                .Ev(1, "AnimInputMultiplyStop").Ev(1, "AnimInputOff").EvF(1, "AnimMove", 300f).Ev(2, "AnimMoveStop").EvO(1, "AnimSound", v);
            foreach (var f in new[] { 3, 5, 7 }) hop.Ev(f, "AnimAttack", sting).Ev(f, "AnimAttack", fx);
            hop.Ev(-1, "BelHopBack").Ev(-1, "AnimRun");
            atk.Clear();
            atk.Add(Kit.Attack(a0, jb.Build(), 0.35f, rangeInner: 8f, rangeOuter: 26f));
            atk.Add(Kit.Attack(a0, jb2.Build(), 0.35f, rangeInner: 8f, rangeOuter: 26f));
            atk.Add(Kit.Attack(a0, fl.Build(), 1.7f, rangeInner: 8f, rangeOuter: 34f));
            Kit.SetSpecial(p, Kit.Attack(sp, hop.Build(), 0f, rangeInner: 20f, rangeOuter: 50f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.55f);
            Strike.Feet(p, n0, 10f);
            BoxerFootwork.HopBackClip = new ClipBuilder(sh, "HopBack", "ModBoxerHopBack").Once().Build();
        }

        // ---------------------------------------------------------------------------------------------- tier 3
        // The Drowned Bell: Toll swings the bell down in a ring; Cast the Bell hurls it at the hero. Bare, he punches.
        // Quirk: BellCast.
        static void BellKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int toll = Kit.AddEffect(p, BelMoraFx.BellToll, offsetX: 19f, offsetY: 0.01f);
            Kit.AimReach(p, toll, 8f, 8f);
            int punch = Kit.AddEffect(p, BelMoraFx.BellPunch, attach: true, destroyOnAnimEnd: true, offsetX: 15f, offsetY: 9f);
            var tl = new ClipBuilder(sh, "Toll", "ModBellToll").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(3, "AnimInputMultiplyStop").Ev(3, "AnimInputOff")
                .Ev(4, "AnimAttack", toll).EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            var pu = Kit.Melee(sh, "Punch", "ModBellPunch", v, 2, punch, 60f).Build();
            var cast = new ClipBuilder(sh, "Cast", "ModBellCast").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(3, "AnimInputMultiplyStop").Ev(3, "AnimInputOff")
                .Ev(4, "BelCastBell").EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, tl, 1.8f, rangeInner: 18f, rangeOuter: 44f));
            atk.Add(Kit.Attack(a0, pu, 0.8f, rangeInner: 8f, rangeOuter: 22f));
            Kit.SetSpecial(p, Kit.Attack(sp, cast, 0f, rangeInner: 40f, rangeOuter: 140f, rangeRetreat: 0f), 7.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 10f);
            BellCast.BareIdle = Looped(sh, "IdleBare", "ModBellIdleBare");
            BellCast.BareRun = Looped(sh, "RunBare", "ModBellRunBare");
            BellCast.BareSpecial = Kit.Melee(sh, "Punch", "ModBellPunchSpecial", v, 2, punch, 60f).Build();
            BellCast.LiftClip = new ClipBuilder(sh, "Lift", "ModBellLift").Once().Ev(7, "BelLiftToll").Build();
        }

        // Drowned Captain: the gaff rakes and hauls; Grapple Swing swings across the room and lands with a boot. Quirk:
        // CaptainGrapple (and Man Overboard).
        static void CaptainKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int gaff = Kit.AddEffect(p, BelMoraFx.CaptainGaff, attach: true, destroyOnAnimEnd: true, offsetX: 16f, offsetY: 9f);
            int kick = Kit.AddEffect(p, BelMoraFx.GrappleKick, attach: true, destroyOnAnimEnd: true, offsetX: 12f, offsetY: 6f);
            // Combo: two gaff slashes, then the Keelhaul: a lunging gaff that drags him close for the boot
            var gf = Kit.Melee(sh, "Gaff", "ModCaptainGaff", v, 3, gaff, 50f).Build();
            var gf2 = Kit.Melee(sh, "Gaff", "ModCaptainGaff2", null, 3, gaff, 60f).Speed(1.1f).Build();
            var kh = Kit.Melee(sh, "Gaff", "ModCaptainKeelhaul", v, 3, gaff, 100f, 5, kick, 30f).Speed(0.9f).Build();
            var gr = Still(sh, "Grapple", "ModCaptainGrapple").Ev(2, "BelGrappleFire").EvO(2, "AnimSound", v)
                .Ev(3, "AnimStartInvincibility").Ev(3, "AnimCollideOff").Ev(3, "BelSwing")
                .Ev(8, "AnimCollideOn").Ev(8, "AnimStopInvincibility").Ev(8, "AnimAttack", kick).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, gf, 0.4f, rangeInner: 12f, rangeOuter: 30f));
            atk.Add(Kit.Attack(a0, gf2, 0.4f, rangeInner: 12f, rangeOuter: 32f));
            atk.Add(Kit.Attack(a0, kh, 1.9f, rangeInner: 14f, rangeOuter: 46f));
            Kit.SetSpecial(p, Kit.Attack(sp, gr, 0f, rangeInner: 40f, rangeOuter: 150f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 10f);
        }

        // Crown of Thorns: an arm lash; Thorn Fling throws one thorn per arm it still has. Quirk: CrownRegrowth.
        static void CrownKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int lash = Kit.AddEffect(p, BelMoraFx.CrownLash, attach: true, destroyOnAnimEnd: true, offsetX: 13f, offsetY: 6f);
            atk.Clear();
            CrownRegrowth.ArmIdle = new exSpriteAnimClip[6]; CrownRegrowth.ArmRun = new exSpriteAnimClip[6]; CrownRegrowth.ArmFling = new exSpriteAnimClip[6];
            exSpriteAnimClip fling5 = null;
            for (int n = 5; n >= 2; n--)
            {
                string sfx = n == 5 ? "" : n.ToString();
                var thorns = new List<int>();
                for (int i = 0; i < n; i++)
                {
                    float a = n == 1 ? 0.01f : -24f + 48f * i / (n - 1);
                    thorns.Add(Kit.AddEffect(p, BelMoraFx.ThornShot, offsetX: 10f, offsetY: 1f, angle: Mathf.Abs(a) < 0.01f ? 0.01f : a));
                }
                var ls = Kit.Melee(sh, "Lash" + sfx, "ModCrownLash" + n, v, 2, lash, 30f).Build();
                atk.Add(Kit.Attack(a0, ls, 1.5f, rangeInner: 10f, rangeOuter: 26f));
                var fl = new ClipBuilder(sh, "Fling" + sfx, "ModCrownFling" + n).Once()
                    .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff");
                for (int i = 0; i < thorns.Count; i++) fl.Ev(3, "AnimAttack", thorns[i], i * 0.02f);
                var flc = fl.EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
                if (n == 5) fling5 = flc;
                CrownRegrowth.ArmFling[n] = flc;
                if (n < 5)
                {
                    CrownRegrowth.ArmIdle[n] = Looped(sh, "Idle" + sfx, "ModCrownIdle" + n);
                    CrownRegrowth.ArmRun[n] = Looped(sh, "Run" + sfx, "ModCrownRun" + n);
                }
            }
            // a thorn rolls about 90 px before it sticks
            Kit.SetSpecial(p, Kit.Attack(sp, fling5, 0f, rangeInner: 30f, rangeOuter: 90f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 10f);
        }

        // Brood Urchin: a fan of three spines; Clutch lobs three tide eggs by the hero. Quirk: BroodClutch / BroodEggFx.
        static void BroodKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            var spines = new List<int>();
            foreach (var a in new[] { -16f, 0.01f, 16f }) spines.Add(Kit.AddEffect(p, BelMoraFx.BroodSpine, offsetX: 13f, offsetY: 12f, angle: a));
            var wide = new List<int>();
            foreach (var a in new[] { -34f, -17f, 0.01f, 17f, 34f }) wide.Add(Kit.AddEffect(p, BelMoraFx.BroodSpine, offsetX: 13f, offsetY: 12f, angle: a));
            // Combo: two sprays of three spines, then the Brood Bomb: a fat spine that bursts into a full ring of spines
            var sy = Kit.Shot(sh, "Spray", "ModBroodSpray", 3, v, 0.02f, spines.ToArray()).Build();
            var sy2 = Kit.Shot(sh, "Spray", "ModBroodSpray2", 3, null, 0.02f, spines.ToArray()).Speed(1.15f).Build();
            // the Brood Bomb: one fat spine, slow, that bursts into a full ring of spines where it stops
            int bomb = Kit.AddEffect(p, FxKit.Finisher(BelMoraFx.BroodSpine, "ModBroodSpineBomb", scale: 1.6f, damageMult: 1.2f, speedMult: 0.7f,
                                                       leaves: FxKit.Emitter("ModBroodSpineRing", BelMoraFx.BroodSpine, 8)), offsetX: 13f, offsetY: 12f);
            var sy3 = Kit.Shot(sh, "Spray", "ModBroodBomb", 3, v, 0f, bomb).Speed(0.85f).Build();
            var cl = Still(sh, "Clutch", "ModBroodClutch").Ev(4, "BelClutch").EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sy, 0.45f, rangeInner: 40f, rangeOuter: 100f, rangeRetreat: 30f));
            atk.Add(Kit.Attack(a0, sy2, 0.45f, rangeInner: 40f, rangeOuter: 100f, rangeRetreat: 30f));
            atk.Add(Kit.Attack(a0, sy3, 2.0f, rangeInner: 35f, rangeOuter: 95f, rangeRetreat: 30f));
            Kit.SetSpecial(p, Kit.Attack(sp, cl, 0f, rangeInner: 30f, rangeOuter: 150f, rangeRetreat: 30f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 12f);
            var esh = SpriteSheets.Get("FxBelBroodEgg");
            if (esh != null) { BroodEggFx.SlowClip = Looped(esh, "PulseSlow", "ModBelEggSlow"); BroodEggFx.FastClip = Looped(esh, "PulseFast", "ModBelEggFast"); }
        }

        // Tide Matriarch: a trident thrust that also flings a coral shard; Riptide Lanes plants the trident. Quirk:
        // MatriarchLanes.
        static void MatriarchKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int thrust = Kit.AddEffect(p, BelMoraFx.TridentThrust, attach: true, destroyOnAnimEnd: true, offsetX: 15f, offsetY: 10f);
            Kit.Scale(p, thrust, 1.3f);   // a tier 3 trident: the thrust's art and hit at the size of the game's own tier 4 swipes
            int shard = Kit.AddEffect(p, BelMoraFx.CoralShard, offsetX: 22f, offsetY: 12f);
            int wave = Kit.AddEffect(p, BelMoraFx.Wave, offsetX: 18f, offsetY: 4f);
            // Combo: two thrusts that fling a coral shard, then the trident calls a wave that rolls on at the hero
            var tr = Kit.Melee(sh, "Thrust", "ModMatriarchThrust", v, 3, thrust, 30f).Ev(3, "AnimAttack", shard).Build();
            var tr2 = Kit.Melee(sh, "Thrust", "ModMatriarchThrust2", null, 3, thrust, 40f).Speed(1.1f).Ev(3, "AnimAttack", shard).Build();
            var tw = Kit.Melee(sh, "Thrust", "ModMatriarchWave", v, 3, thrust, 50f).Speed(0.85f).Ev(3, "AnimAttack", wave).Build();
            var pl = Still(sh, "Plant", "ModMatriarchPlant").Ev(3, "BelLanes").EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, tr, 0.45f, rangeInner: 18f, rangeOuter: 42f));
            atk.Add(Kit.Attack(a0, tr2, 0.45f, rangeInner: 18f, rangeOuter: 42f));
            atk.Add(Kit.Attack(a0, tw, 2.2f, rangeInner: 18f, rangeOuter: 100f));
            Kit.SetSpecial(p, Kit.Attack(sp, pl, 0f, rangeInner: 20f, rangeOuter: 140f, rangeRetreat: 0f), 7.5f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 12f);
            MatriarchLanes.PlantLoop = Looped(sh, "PlantLoop", "ModMatriarchPlantLoop");
        }

        // Jelly Siren: her tentacles lash ahead (may slow); Jet Pulse jets her round the hero three times. Quirk: JellyTrail.
        static void JellyKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int lash = Kit.AddEffect(p, BelMoraFx.JellyLash, attach: true, destroyOnAnimEnd: true, offsetX: 13f, offsetY: 7f);
            int lashL = Kit.AddEffect(p, BelMoraFx.JellyLash, attach: true, destroyOnAnimEnd: true, offsetX: 13f, offsetY: 7f, angle: -28f);
            int lashR = Kit.AddEffect(p, BelMoraFx.JellyLash, attach: true, destroyOnAnimEnd: true, offsetX: 13f, offsetY: 7f, angle: 28f);
            // Combo: two lashes, then the Bloom: three tentacles lash out together in a fan
            var ls = Kit.Melee(sh, "Lash", "ModJellyLash", v, 3, lash, 30f).Ev(3, "BelLashOut").Build();
            var ls2 = Kit.Melee(sh, "Lash", "ModJellyLash2", null, 3, lash, 40f).Speed(1.1f).Ev(3, "BelLashOut").Build();
            var bloom = Kit.Melee(sh, "Lash", "ModJellyBloom", v, 3, lash, 30f).Speed(0.85f).Ev(3, "AnimAttack", lashL).Ev(3, "AnimAttack", lashR).Ev(3, "BelLashOut").Build();
            var jt = Still(sh, "Jet", "ModJellyJet").Ev(1, "BelJet").Ev(5, "BelJet").Ev(9, "BelJet").EvO(1, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, ls, 0.45f, rangeInner: 14f, rangeOuter: 70f));
            atk.Add(Kit.Attack(a0, ls2, 0.45f, rangeInner: 14f, rangeOuter: 70f));
            atk.Add(Kit.Attack(a0, bloom, 2.0f, rangeInner: 14f, rangeOuter: 66f));
            Kit.SetSpecial(p, Kit.Attack(sp, jt, 0f, rangeInner: 10f, rangeOuter: 60f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 12f);
        }

        // Gulper Eel: a wide jaw scoop; Swallow Whole unhinges and gulps. Quirk: GulperSwallow (and Full Pouch).
        static void GulperKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int scoop = Kit.AddEffect(p, BelMoraFx.GulperScoop, attach: true, destroyOnAnimEnd: true, offsetX: 14f, offsetY: 5f);
            // Combo: two scoops, then the Lunge: it hurls its whole length forward, jaws wide, scoops twice and spills a pool of brine
            var sc = Kit.Melee(sh, "Scoop", "ModGulperScoop", v, 3, scoop, 40f).Build();
            var sc2 = Kit.Melee(sh, "Scoop", "ModGulperScoop2", null, 3, scoop, 50f).Speed(1.1f).Build();
            int spill = Kit.AddEffect(p, BelMoraFx.Brine, offsetX: 22f, offsetY: 0.01f);
            var lg = Kit.Melee(sh, "Scoop", "ModGulperLunge", v, 2, scoop, 130f, 4, scoop, 40f).Speed(0.9f).Ev(4, "AnimAttack", spill, 0.05f).Build();
            var un = new ClipBuilder(sh, "Unhinge", "ModGulperUnhinge").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(3, "AnimInputMultiplyStop").Ev(3, "AnimInputOff")
                .Ev(4, "BelGulp").EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sc, 0.4f, rangeInner: 10f, rangeOuter: 28f));
            atk.Add(Kit.Attack(a0, sc2, 0.4f, rangeInner: 10f, rangeOuter: 30f));
            atk.Add(Kit.Attack(a0, lg, 1.9f, rangeInner: 12f, rangeOuter: 52f));
            // the gulp lunges 30 px and its mouth reaches 30 px past that
            Kit.SetSpecial(p, Kit.Attack(sp, un, 0f, rangeInner: 14f, rangeOuter: 52f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 10f);
            GulperSwallow.FullIdle = Looped(sh, "IdleFull", "ModGulperIdleFull");
            GulperSwallow.FullRun = Looped(sh, "RunFull", "ModGulperRunFull");
            GulperSwallow.GagClip = Looped(sh, "Gag", "ModGulperGag");
        }

        // Slime Hag: a rasping bite (bleed); Slime Spew spews three globs that coat the hero. Quirk: HagKnot.
        static void HagKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int rasp = Kit.AddEffect(p, BelMoraFx.HagRasp, attach: true, destroyOnAnimEnd: true, offsetX: 16f, offsetY: 6f);
            var globs = new List<int>();
            foreach (var a in new[] { -18f, 0.01f, 18f }) globs.Add(Kit.AddEffect(p, BelMoraFx.HagGlob, offsetX: 17f, offsetY: 1f, angle: a));
            // Combo: two rasping bites, then a lunge that bites and spits a slime glob after him
            var rs = Kit.Melee(sh, "Bite", "ModHagBite", v, 3, rasp, 60f).Build();
            var rs2 = Kit.Melee(sh, "Bite", "ModHagBite2", null, 3, rasp, 70f).Speed(1.1f).Build();
            var sl = Kit.Melee(sh, "Bite", "ModHagSlimeLunge", v, 3, rasp, 120f).Speed(0.9f).Ev(4, "AnimAttack", globs[1]).Build();
            var sw = Kit.Shot(sh, "Spew", "ModHagSpew", 4, v, 0.04f, globs.ToArray()).Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, rs, 0.4f, rangeInner: 12f, rangeOuter: 32f));
            atk.Add(Kit.Attack(a0, rs2, 0.4f, rangeInner: 12f, rangeOuter: 34f));
            atk.Add(Kit.Attack(a0, sl, 1.8f, rangeInner: 14f, rangeOuter: 50f));
            Kit.SetSpecial(p, Kit.Attack(sp, sw, 0f, rangeInner: 30f, rangeOuter: 100f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 8f);
            HagKnot.KnotClip = new ClipBuilder(sh, "Knot", "ModHagKnot").Once().Build();
        }

        // Abyss Kraken: two arms slam the floor ahead; Erupt drives them under the hero and out of the brine. Quirk: KrakenArms.
        static void KrakenKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int slam = Kit.AddEffect(p, BelMoraFx.KrakenSlam, attach: true, destroyOnAnimEnd: true, offsetX: 15f, offsetY: 3f);
            int armL = Kit.AddEffect(p, BelMoraFx.KrakenSlam, attach: true, destroyOnAnimEnd: true, offsetX: 15f, offsetY: 3f, angle: -40f);
            int armR = Kit.AddEffect(p, BelMoraFx.KrakenSlam, attach: true, destroyOnAnimEnd: true, offsetX: 15f, offsetY: 3f, angle: 40f);
            // Combo: two slams, then All Arms: arms crash down ahead and to both sides, one after another
            var sl = Kit.Melee(sh, "Slam", "ModKrakenSlam", v, 3, slam, 20f).Build();
            var sl2 = Kit.Melee(sh, "Slam", "ModKrakenSlam2", null, 3, slam, 30f).Speed(1.1f).Build();
            var all = Kit.Melee(sh, "Slam", "ModKrakenAllArms", v, 3, slam, 30f).Speed(0.85f).Ev(3, "AnimAttack", armL, 0.08f).Ev(3, "AnimAttack", armR, 0.16f).Build();
            var er = Still(sh, "Erupt", "ModKrakenErupt").Ev(3, "BelKrakenErupt").EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sl, 0.45f, rangeInner: 12f, rangeOuter: 30f));
            atk.Add(Kit.Attack(a0, sl2, 0.45f, rangeInner: 12f, rangeOuter: 32f));
            atk.Add(Kit.Attack(a0, all, 2.0f, rangeInner: 12f, rangeOuter: 34f));
            Kit.SetSpecial(p, Kit.Attack(sp, er, 0f, rangeInner: 0f, rangeOuter: 130f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 10f);
            KrakenArms.OpenIdle = Looped(sh, "IdleOpen", "ModKrakenIdleOpen");
            KrakenArms.OpenRun = Looped(sh, "RunOpen", "ModKrakenRunOpen");
            var tsh = SpriteSheets.Get("FxTentacle");
            if (tsh != null)
            {
                KrakenArmFx.SwayClip = Looped(tsh, "Sway", "ModKrakenArmSway");
                KrakenArmFx.SwatClip = new ClipBuilder(tsh, "Swat", "ModKrakenArmSwat").Once().Build();
                KrakenArmFx.SinkClip = new ClipBuilder(tsh, "Sink", "ModKrakenArmSink").Once().Build();
            }
        }

        // Belltower Hermit: crusher claw; Five Peals march out to the hero. Quirk: BelltowerPeals (Carried by Water).
        static void BelltowerKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int crush = Kit.AddEffect(p, BelMoraFx.BelltowerCrush, attach: true, destroyOnAnimEnd: true, offsetX: 19f, offsetY: 5f);
            int peal = Kit.AddEffect(p, BelMoraFx.Peal, offsetX: 24f, offsetY: 0.01f);
            int peal2 = Kit.AddEffect(p, BelMoraFx.Peal, offsetX: 44f, offsetY: 0.01f);
            // Combo: two claw snaps, then the Toll: the claw strikes its bell tower and two peals roll out ahead
            var cr = Kit.Melee(sh, "Crush", "ModBelltowerCrush", v, 3, crush, 40f).Build();
            var cr2 = Kit.Melee(sh, "Crush", "ModBelltowerCrush2", null, 3, crush, 50f).Speed(1.1f).Build();
            var tl = Kit.Melee(sh, "Crush", "ModBelltowerToll", v, 3, crush, 50f).Speed(0.85f).Ev(3, "AnimAttack", peal).Ev(3, "AnimAttack", peal2, 0.15f).Build();
            var pe = new ClipBuilder(sh, "Peals", "ModBelltowerPeals").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff")
                .Ev(3, "BelMarch").EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, cr, 0.4f, rangeInner: 12f, rangeOuter: 32f));
            atk.Add(Kit.Attack(a0, cr2, 0.4f, rangeInner: 12f, rangeOuter: 34f));
            atk.Add(Kit.Attack(a0, tl, 1.9f, rangeInner: 12f, rangeOuter: 56f));
            // five peals reach 16 + 4 x 14 = 72 px
            Kit.SetSpecial(p, Kit.Attack(sp, pe, 0f, rangeInner: 20f, rangeOuter: 80f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 8f);
        }

        // Anemone Colossus: both pincers hammer the floor; Budding flicks two stinging buds by the hero. Quirk: ColossusGarden.
        static void ColossusKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int slam = Kit.AddEffect(p, BelMoraFx.ColossusSlam, attach: true, destroyOnAnimEnd: true, offsetX: 17f, offsetY: 4f);
            int budA = Kit.AddEffect(p, BelMoraFx.Bud, offsetX: -18f, offsetY: 4f, spawnPoint: DamageEffectData.eSpawnPoint.ClosestEnemy);
            int budB = Kit.AddEffect(p, BelMoraFx.Bud, offsetX: 18f, offsetY: -4f, spawnPoint: DamageEffectData.eSpawnPoint.ClosestEnemy);
            int seed = Kit.AddEffect(p, BelMoraFx.Bud, offsetX: 26f, offsetY: 0.01f);
            // Combo: two pincer hammers, then the Seeding: the hammer plants an anemone bud where the pincers fall
            var hm = Kit.Melee(sh, "Hammer", "ModColossusHammer", v, 3, slam, 20f).Build();
            var hm2 = Kit.Melee(sh, "Hammer", "ModColossusHammer2", null, 3, slam, 30f).Speed(1.1f).Build();
            var hs = Kit.Melee(sh, "Hammer", "ModColossusSeeding", v, 3, slam, 40f).Speed(0.85f).Ev(3, "AnimAttack", seed).Build();
            var bd = Still(sh, "Budding", "ModColossusBudding").Ev(4, "AnimAttack", budA).Ev(4, "AnimAttack", budB, 0.08f)
                .EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, hm, 0.45f, rangeInner: 12f, rangeOuter: 32f));
            atk.Add(Kit.Attack(a0, hm2, 0.45f, rangeInner: 12f, rangeOuter: 34f));
            atk.Add(Kit.Attack(a0, hs, 2.0f, rangeInner: 12f, rangeOuter: 40f));
            Kit.SetSpecial(p, Kit.Attack(sp, bd, 0f, rangeInner: 20f, rangeOuter: 120f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 10f);
            ColossusGarden.OpenIdle = Looped(sh, "IdleOpen", "ModColossusIdleOpen");
            ColossusGarden.OpenRun = Looped(sh, "RunOpen", "ModColossusRunOpen");
        }

        // Reef Champion: a rising uppercut; Haymaker plants its tail, winds up and throws one huge punch. Quirk: ChampionRounds.
        static void ChampionKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int up = Kit.AddEffect(p, BelMoraFx.ChampionUpper, attach: true, destroyOnAnimEnd: true, offsetX: 12f, offsetY: 10f);
            int hay = Kit.AddEffect(p, BelMoraFx.Haymaker, attach: true, destroyOnAnimEnd: true, offsetX: 16f, offsetY: 8f);
            // Combo: two uppercuts, then the Rush: it steps in with two quick uppercuts and a lunging third that leaves him dizzy
            var uc = Kit.Melee(sh, "Uppercut", "ModChampionUppercut", v, 3, up, 40f).Build();
            var uc2 = Kit.Melee(sh, "Uppercut", "ModChampionUppercut2", null, 3, up, 50f).Speed(1.15f).Build();
            int ko = Kit.AddEffect(p, FxKit.Finisher(BelMoraFx.ChampionUpper, "ModChampionUpperKO", damageMult: 1.1f, status: FxFactory.GetStatus("StatusDizzy")),
                                   attach: true, destroyOnAnimEnd: true, offsetX: 12f, offsetY: 10f);
            var rush = Kit.Melee(sh, "Uppercut", "ModChampionRush", v, 3, up, 50f, 10, ko, 90f).Repeat(2).Speed(1.2f).Build();
            var hm = Still(sh, "Haymaker", "ModChampionHaymaker").EvF(5, "AnimMove", 120f).Ev(5, "AnimAttack", hay).EvO(5, "AnimSound", v)
                .Ev(6, "AnimMoveStop").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, uc, 0.35f, rangeInner: 8f, rangeOuter: 26f));
            atk.Add(Kit.Attack(a0, uc2, 0.35f, rangeInner: 8f, rangeOuter: 28f));
            atk.Add(Kit.Attack(a0, rush, 1.7f, rangeInner: 10f, rangeOuter: 40f));
            Kit.SetSpecial(p, Kit.Attack(sp, hm, 0f, rangeInner: 8f, rangeOuter: 30f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.55f);
            Strike.Feet(p, n0, 14f);
            ChampionRounds.RestClip = Looped(sh, "Rest", "ModChampionRest");
        }

        // ---------------------------------------------------------------------------------------------- the god
        static void LeaveBrine(GameObject go, Player p)
        {
            Kit.AddDeathSpawn(p, BelMoraFx.Brine);
            Strike.DeathAtFeet(p);
            BelArt.UseHitSplat(p, BelMoraFx.HitSplat);
        }

        // Evolution tree: every evolution has exactly one parent.
        //   BellUrchin   -> BellDiver, Spinewalker        BellDiver    -> DrownedBell, DrownedCaptain
        //                                                 Spinewalker  -> CrownOfThorns, BroodUrchin
        //   Lurefish     -> SaltSiren, BrineLamprey       SaltSiren    -> TideMatriarch, JellySiren
        //                                                 BrineLamprey -> GulperEel, SlimeHag
        //   BarnacleCrab -> BellHermit, AnemoneBoxer      BellHermit   -> AbyssKraken, BelltowerHermit
        //                                                 AnemoneBoxer -> AnemoneColossus, ReefChampion
        public static readonly List<MonsterDef> Monsters = new List<MonsterDef>
        {
            new MonsterDef { id = "BellUrchin", art = "BelUrchin", basePrefab = "EnemyMushroom", health = 4f, evolveCost = 0f,
                             evolveTo = new[] { "BellDiver", "Spinewalker" }, kit = UrchinKit, customize = LeaveBrine },
            new MonsterDef { id = "Lurefish", art = "BelLurefish", basePrefab = "EnemyGiantRat_Fireball", health = 3.5f, evolveCost = 0f,
                             evolveTo = new[] { "SaltSiren", "BrineLamprey" }, kit = LurefishKit, customize = LeaveBrine },
            new MonsterDef { id = "BarnacleCrab", art = "BelCrab", basePrefab = "EnemyGnome", health = 4.5f, speedMult = 0.9f, evolveCost = 0f,
                             evolveTo = new[] { "BellHermit", "AnemoneBoxer" }, kit = CrabKit, customize = LeaveBrine },
            new MonsterDef { id = "BellDiver", art = "BelDiver", basePrefab = "EnemyOrc", health = 7f, speedMult = 0.9f, evolveCost = 2.5f, damageMult = 1.1f,
                             evolveTo = new[] { "DrownedBell", "DrownedCaptain" }, kit = DiverKit, customize = LeaveBrine },
            new MonsterDef { id = "Spinewalker", art = "BelSpinewalker", basePrefab = "EnemyGiantSpider_Standard", health = 6f, evolveCost = 2.5f, damageMult = 1.4f,
                             evolveTo = new[] { "CrownOfThorns", "BroodUrchin" }, kit = SpinewalkerKit, customize = LeaveBrine },
            new MonsterDef { id = "SaltSiren", art = "BelSiren", basePrefab = "EnemyWitch", health = 5.5f, evolveCost = 2.5f, damageMult = 1.4f,
                             evolveTo = new[] { "TideMatriarch", "JellySiren" }, kit = SirenKit, customize = LeaveBrine },
            new MonsterDef { id = "BrineLamprey", art = "BelLamprey", basePrefab = "EnemyTentacleGlutton", health = 5.5f, evolveCost = 2.5f, damageMult = 1.3f,
                             evolveTo = new[] { "GulperEel", "SlimeHag" }, kit = LampreyKit, customize = LeaveBrine },
            new MonsterDef { id = "BellHermit", art = "BelHermit", basePrefab = "EnemyBlobfish", health = 6.5f, speedMult = 1.35f, evolveCost = 2.5f, damageMult = 1.3f,
                             evolveTo = new[] { "AbyssKraken", "BelltowerHermit" }, kit = HermitKit, customize = LeaveBrine },
            new MonsterDef { id = "AnemoneBoxer", art = "BelBoxer", basePrefab = "EnemyScorpion", health = 6.5f, evolveCost = 2.5f,
                             evolveTo = new[] { "AnemoneColossus", "ReefChampion" }, kit = BoxerKit, customize = LeaveBrine },
            new MonsterDef { id = "DrownedBell", art = "BelDrownedBell", basePrefab = "EnemyTroll", health = 14f, evolveCost = 4.5f, damageMult = 1.1f,
                             kit = BellKit, customize = LeaveBrine },
            new MonsterDef { id = "DrownedCaptain", art = "BelCaptain", basePrefab = "EnemyMinotaur", health = 13f, evolveCost = 4.5f, damageMult = 1.1f,
                             kit = CaptainKit, customize = LeaveBrine },
            new MonsterDef { id = "CrownOfThorns", art = "BelCrownThorns", basePrefab = "EnemyCapraDemon", health = 13f, speedMult = 0.85f, evolveCost = 4.5f, damageMult = 1.1f,
                             kit = CrownKit, customize = LeaveBrine },
            new MonsterDef { id = "BroodUrchin", art = "BelBrood", basePrefab = "EnemyGhoul", health = 13.5f, speedMult = 0.8f, evolveCost = 4.5f, damageMult = 1.1f,
                             kit = BroodKit, customize = LeaveBrine },
            new MonsterDef { id = "TideMatriarch", art = "BelMatriarch", basePrefab = "EnemyPriestess", health = 13f, evolveCost = 4.5f, damageMult = 1.1f,
                             kit = MatriarchKit, customize = LeaveBrine },
            new MonsterDef { id = "JellySiren", art = "BelJellySiren", basePrefab = "EnemyFacelessShaman", health = 12.5f, evolveCost = 4.5f, damageMult = 1.1f,
                             kit = JellyKit, customize = LeaveBrine },
            new MonsterDef { id = "GulperEel", art = "BelGulperEel", basePrefab = "EnemyDemonSnake", health = 12.5f, evolveCost = 4.5f,
                             kit = GulperKit, customize = LeaveBrine },
            new MonsterDef { id = "SlimeHag", art = "BelSlimeHag", basePrefab = "EnemyStingerTadpole_Giant", health = 13f, speedMult = 0.9f, evolveCost = 4.5f,
                             kit = HagKit, customize = LeaveBrine },
            new MonsterDef { id = "AbyssKraken", art = "BelKraken", basePrefab = "EnemyOctopusHead", health = 13.5f, speedMult = 0.8f, evolveCost = 4.5f, damageMult = 1.1f,
                             kit = KrakenKit, customize = LeaveBrine },
            new MonsterDef { id = "BelltowerHermit", art = "BelBelltower", basePrefab = "EnemyDarkGuardian", health = 14f, speedMult = 0.85f, evolveCost = 4.5f, damageMult = 1.1f,
                             kit = BelltowerKit, customize = LeaveBrine },
            new MonsterDef { id = "AnemoneColossus", art = "BelColossus", basePrefab = "EnemySkeletonGiantShield", health = 14f, speedMult = 0.8f, evolveCost = 4.5f, damageMult = 1.1f,
                             kit = ColossusKit, customize = LeaveBrine },
            new MonsterDef { id = "ReefChampion", art = "BelChampion", basePrefab = "EnemyEyelessBeast", health = 13f, evolveCost = 4.5f, damageMult = 1.1f,
                             kit = ChampionKit, customize = LeaveBrine },
        };

        /// <summary>Each monster's quirk.</summary>
        static readonly Dictionary<string, Type> Quirks = new Dictionary<string, Type>
        {
            { "BellUrchin", typeof(UrchinGrip) }, { "Lurefish", typeof(LureBait) }, { "BarnacleCrab", typeof(CrabSidle) },
            { "BellDiver", typeof(DiverAnchor) }, { "SaltSiren", typeof(SirenTidesong) }, { "BrineLamprey", typeof(LampreyLatch) },
            { "BellHermit", typeof(HermitBell) }, { "AnemoneBoxer", typeof(BoxerFootwork) }, { "DrownedBell", typeof(BellCast) },
            { "DrownedCaptain", typeof(CaptainGrapple) }, { "CrownOfThorns", typeof(CrownRegrowth) }, { "BroodUrchin", typeof(BroodClutch) },
            { "TideMatriarch", typeof(MatriarchLanes) }, { "JellySiren", typeof(JellyTrail) }, { "GulperEel", typeof(GulperSwallow) },
            { "SlimeHag", typeof(HagKnot) }, { "AbyssKraken", typeof(KrakenArms) }, { "BelltowerHermit", typeof(BelltowerPeals) },
            { "AnemoneColossus", typeof(ColossusGarden) }, { "ReefChampion", typeof(ChampionRounds) },
        };

        public static readonly GodDef God = new GodDef
        {
            name = "Bel'Mora",
            text = "Tides leave brine: slows hero",
            flavour = "The bell sank with the town.\nIt rings at high tide.",
            winText = "THE BELL FALLS SILENT",
            portraitArt = "DeityBelMora",
            startingMonsters = new[] { "BellUrchin", "Lurefish", "BarnacleCrab" },
        };

        static Deity s_deity;

        public static void Register()
        {
            BelMoraFx.Build();
            foreach (var m in Monsters)
            {
                var t = new BelMoraTraits();
                Type q;
                if (Quirks.TryGetValue(m.id, out q)) t.behaviours.Add(q);
                if (m.id == "BarnacleCrab") { t.maxPlates = 1; t.plateFx = BelMoraFx.BarnaclePlate; t.plateBreakFx = BelMoraFx.BarnacleBreak; }
                MonsterTraits.Register(m.PrefabName, t);
            }
            foreach (var m in Monsters) MonsterFactory.Build(m);
            MonsterFactory.LinkEvolutions(Monsters);
            MonsterEvents.AttackSpawned += OnAttackSpawned;
            s_deity = DeityFactory.Register(God);
            Strike.KeepAllScales();
            BelTide.Ensure();
            HeroStrikes.Install();
            // the gold idol carved in the Drowned Bell's likeness (other gods chain their own the same way)
            var prev = SlotGods.PortraitFor;
            SlotGods.PortraitFor = (tier, god) =>
                tier == SlotTier.Gold && IsBelMora(god) ? SlotArt.Clip("DeityGoldIdolBelMora", "Idle") : (prev != null ? prev(tier, god) : null);
        }

        static bool IsBelMora(Deity d) { return d != null && s_deity != null && (d == s_deity || d.GetName() == s_deity.GetName()); }

        static void OnAttackSpawned(Player owner, GameObject fx, GameObject template)
        {
            var q = owner != null && fx != null ? owner.GetComponent<BelBehaviour>() : null;
            if (q != null) q.OnAttackSpawned(fx, template);
        }
    }
}
