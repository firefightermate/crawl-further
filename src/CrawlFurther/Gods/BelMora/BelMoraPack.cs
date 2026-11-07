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
            var an = Kit.Melee(sh, "Anchor", "ModDiverAnchor", v, 3, slam, 40f).Ev(4, "AnimAttack", quake);
            var hk = Kit.Shot(sh, "Hook", "ModDiverHook", 2, v, 0f, hook).Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, an.Build(), 1.4f, rangeInner: 12f, rangeOuter: 30f));
            // the hook flies about 95 px
            Kit.SetSpecial(p, Kit.Attack(sp, hk, 0f, rangeInner: 40f, rangeOuter: 95f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
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
            var st = Kit.Melee(sh, "Stab", "ModSpinewalkerStab", v, 2, stab, 40f).Build();
            var sw = Still(sh, "Sow", "ModSpinewalkerSow");
            for (int i = 0; i < eggs.Count; i++) sw.Ev(4, "AnimAttack", eggs[i], i * 0.05f);
            sw.EvO(4, "AnimSound", v).Ev(-1, "AnimRun");
            atk.Clear();
            atk.Add(Kit.Attack(a0, st, 1.3f, rangeInner: 10f, rangeOuter: 22f));
            Kit.SetSpecial(p, Kit.Attack(sp, sw.Build(), 0f, rangeInner: 0f, rangeOuter: 60f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
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
            var bl = Kit.Shot(sh, "Bolt", "ModSirenBolt", 3, v, 0f, bolt).Build();
            var song = Still(sh, "Song", "ModSirenSong").Ev(1, "BelSong").Ev(1, "AnimAttack", note).EvO(1, "AnimSound", v)
                .Ev(3, "AnimAttack", brine).Ev(4, "AnimAttack", note).Ev(-1, "AnimRun");
            atk.Clear();
            atk.Add(Kit.Attack(a0, bl, 1.4f, rangeInner: 50f, rangeOuter: 110f, rangeRetreat: 40f));
            Kit.SetSpecial(p, Kit.Attack(sp, song.Build(), 0f, rangeInner: 30f, rangeOuter: 110f, rangeRetreat: 20f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 15f);
        }

        // Brine Lamprey: a rasping bite; Undercurrent Lunge slides 70 px along the floor. Quirk: LampreyLatch.
        static void LampreyKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int bite = Kit.AddEffect(p, BelMoraFx.LampreyBite, attach: true, destroyOnAnimEnd: true, offsetX: 12f, offsetY: 7f);
            int lunge = Kit.AddEffect(p, BelMoraFx.LampreyLunge, attach: true, destroyOnAnimEnd: true, offsetX: 12f, offsetY: 6f);
            var rs = Kit.Melee(sh, "Rasp", "ModLampreyRasp", v, 3, bite, 60f).Build();
            // 0.16 s at 440 px/s: the 70 px lunge
            var ln = new ClipBuilder(sh, "Lunge", "ModLampreyLunge").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(1, "AnimInputMultiplyStop").Ev(1, "AnimInputOff")
                .Ev(2, "BelLungeOn").EvF(2, "AnimMove", 440f).Ev(2, "AnimAttack", lunge).EvO(2, "AnimSound", v)
                .Ev(5, "AnimMoveStop").Ev(5, "BelLungeOff").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, rs, 1.2f, rangeInner: 10f, rangeOuter: 24f));
            Kit.SetSpecial(p, Kit.Attack(sp, ln, 0f, rangeInner: 30f, rangeOuter: 80f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 7f);
            LampreyLatch.LatchedClip = Looped(sh, "Latched", "ModLampreyLatched");
        }

        // Bell Hermit: a lunging claw crush; Bell Down sets its bell down over itself. Quirk: HermitBell.
        static void HermitKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int crush = Kit.AddEffect(p, BelMoraFx.HermitCrush, attach: true, destroyOnAnimEnd: true, offsetX: 15f, offsetY: 4f);
            var cr = Kit.Melee(sh, "Crush", "ModHermitCrush", v, 3, crush, 40f).Build();
            var shell = Still(sh, "Shell", "ModHermitShell").Ev(2, "BelShellOn").EvO(2, "AnimSound", v).Ev(7, "BelShellOff").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, cr, 1.3f, rangeInner: 12f, rangeOuter: 28f));
            Kit.SetSpecial(p, Kit.Attack(sp, shell, 0f, rangeInner: 0f, rangeOuter: 40f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
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
            var hop = new ClipBuilder(sh, "HopIn", "ModBoxerHopIn").Once().EvF(0, "AnimInputMultiplyFreeFace", 0f)
                .Ev(1, "AnimInputMultiplyStop").Ev(1, "AnimInputOff").EvF(1, "AnimMove", 300f).Ev(2, "AnimMoveStop").EvO(1, "AnimSound", v);
            foreach (var f in new[] { 3, 5, 7 }) hop.Ev(f, "AnimAttack", sting).Ev(f, "AnimAttack", fx);
            hop.Ev(-1, "BelHopBack").Ev(-1, "AnimRun");
            atk.Clear();
            atk.Add(Kit.Attack(a0, jb.Build(), 1.2f, rangeInner: 8f, rangeOuter: 24f));
            Kit.SetSpecial(p, Kit.Attack(sp, hop.Build(), 0f, rangeInner: 20f, rangeOuter: 50f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
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
            var gf = Kit.Melee(sh, "Gaff", "ModCaptainGaff", v, 3, gaff, 50f).Build();
            var gr = Still(sh, "Grapple", "ModCaptainGrapple").Ev(2, "BelGrappleFire").EvO(2, "AnimSound", v)
                .Ev(3, "AnimStartInvincibility").Ev(3, "AnimCollideOff").Ev(3, "BelSwing")
                .Ev(8, "AnimCollideOn").Ev(8, "AnimStopInvincibility").Ev(8, "AnimAttack", kick).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, gf, 1.5f, rangeInner: 12f, rangeOuter: 28f));
            Kit.SetSpecial(p, Kit.Attack(sp, gr, 0f, rangeInner: 40f, rangeOuter: 150f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
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
            var sy = Kit.Shot(sh, "Spray", "ModBroodSpray", 3, v, 0.02f, spines.ToArray()).Build();
            var cl = Still(sh, "Clutch", "ModBroodClutch").Ev(4, "BelClutch").EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sy, 1.5f, rangeInner: 40f, rangeOuter: 100f, rangeRetreat: 30f));
            Kit.SetSpecial(p, Kit.Attack(sp, cl, 0f, rangeInner: 30f, rangeOuter: 150f, rangeRetreat: 30f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
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
            int shard = Kit.AddEffect(p, BelMoraFx.CoralShard, offsetX: 22f, offsetY: 12f);
            var tr = Kit.Melee(sh, "Thrust", "ModMatriarchThrust", v, 3, thrust, 30f).Ev(3, "AnimAttack", shard).Build();
            var pl = Still(sh, "Plant", "ModMatriarchPlant").Ev(3, "BelLanes").EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, tr, 1.6f, rangeInner: 18f, rangeOuter: 40f));
            Kit.SetSpecial(p, Kit.Attack(sp, pl, 0f, rangeInner: 20f, rangeOuter: 140f, rangeRetreat: 0f), 7.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 12f);
            MatriarchLanes.PlantLoop = Looped(sh, "PlantLoop", "ModMatriarchPlantLoop");
        }

        // Jelly Siren: her tentacles lash ahead (may slow); Jet Pulse jets her round the hero three times. Quirk: JellyTrail.
        static void JellyKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int lash = Kit.AddEffect(p, BelMoraFx.JellyLash, attach: true, destroyOnAnimEnd: true, offsetX: 13f, offsetY: 7f);
            var ls = Kit.Melee(sh, "Lash", "ModJellyLash", v, 3, lash, 30f).Build();
            var jt = Still(sh, "Jet", "ModJellyJet").Ev(1, "BelJet").Ev(5, "BelJet").Ev(9, "BelJet").EvO(1, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, ls, 1.4f, rangeInner: 10f, rangeOuter: 26f));
            Kit.SetSpecial(p, Kit.Attack(sp, jt, 0f, rangeInner: 10f, rangeOuter: 60f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 12f);
        }

        // Gulper Eel: a wide jaw scoop; Swallow Whole unhinges and gulps. Quirk: GulperSwallow (and Full Pouch).
        static void GulperKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int scoop = Kit.AddEffect(p, BelMoraFx.GulperScoop, attach: true, destroyOnAnimEnd: true, offsetX: 14f, offsetY: 5f);
            var sc = Kit.Melee(sh, "Scoop", "ModGulperScoop", v, 3, scoop, 40f).Build();
            var un = new ClipBuilder(sh, "Unhinge", "ModGulperUnhinge").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(3, "AnimInputMultiplyStop").Ev(3, "AnimInputOff")
                .Ev(4, "BelGulp").EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sc, 1.3f, rangeInner: 10f, rangeOuter: 26f));
            // the gulp lunges 30 px and its mouth reaches 30 px past that
            Kit.SetSpecial(p, Kit.Attack(sp, un, 0f, rangeInner: 14f, rangeOuter: 52f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
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
            var rs = Kit.Melee(sh, "Bite", "ModHagBite", v, 3, rasp, 60f).Build();
            var sw = Kit.Shot(sh, "Spew", "ModHagSpew", 4, v, 0.04f, globs.ToArray()).Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, rs, 1.3f, rangeInner: 12f, rangeOuter: 30f));
            Kit.SetSpecial(p, Kit.Attack(sp, sw, 0f, rangeInner: 30f, rangeOuter: 100f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 8f);
            HagKnot.KnotClip = new ClipBuilder(sh, "Knot", "ModHagKnot").Once().Build();
        }

        // Abyss Kraken: two arms slam the floor ahead; Erupt drives them under the hero and out of the brine. Quirk: KrakenArms.
        static void KrakenKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int slam = Kit.AddEffect(p, BelMoraFx.KrakenSlam, attach: true, destroyOnAnimEnd: true, offsetX: 15f, offsetY: 3f);
            var sl = Kit.Melee(sh, "Slam", "ModKrakenSlam", v, 3, slam, 20f).Build();
            var er = Still(sh, "Erupt", "ModKrakenErupt").Ev(3, "BelKrakenErupt").EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sl, 1.6f, rangeInner: 12f, rangeOuter: 28f));
            Kit.SetSpecial(p, Kit.Attack(sp, er, 0f, rangeInner: 0f, rangeOuter: 130f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
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
            var cr = Kit.Melee(sh, "Crush", "ModBelltowerCrush", v, 3, crush, 40f).Build();
            var pe = new ClipBuilder(sh, "Peals", "ModBelltowerPeals").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff")
                .Ev(3, "BelMarch").EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, cr, 1.4f, rangeInner: 12f, rangeOuter: 30f));
            // five peals reach 16 + 4 x 14 = 72 px
            Kit.SetSpecial(p, Kit.Attack(sp, pe, 0f, rangeInner: 20f, rangeOuter: 80f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
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
            var hm = Kit.Melee(sh, "Hammer", "ModColossusHammer", v, 3, slam, 20f).Build();
            var bd = Still(sh, "Budding", "ModColossusBudding").Ev(4, "AnimAttack", budA).Ev(4, "AnimAttack", budB, 0.08f)
                .EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, hm, 1.6f, rangeInner: 12f, rangeOuter: 30f));
            Kit.SetSpecial(p, Kit.Attack(sp, bd, 0f, rangeInner: 20f, rangeOuter: 120f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
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
            var uc = Kit.Melee(sh, "Uppercut", "ModChampionUppercut", v, 3, up, 40f).Build();
            var hm = Still(sh, "Haymaker", "ModChampionHaymaker").EvF(5, "AnimMove", 120f).Ev(5, "AnimAttack", hay).EvO(5, "AnimSound", v)
                .Ev(6, "AnimMoveStop").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, uc, 1.4f, rangeInner: 8f, rangeOuter: 24f));
            Kit.SetSpecial(p, Kit.Attack(sp, hm, 0f, rangeInner: 8f, rangeOuter: 30f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
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
            new MonsterDef { id = "BellDiver", art = "BelDiver", basePrefab = "EnemyOrc", health = 7f, speedMult = 0.9f, evolveCost = 2.5f,
                             evolveTo = new[] { "DrownedBell", "DrownedCaptain" }, kit = DiverKit, customize = LeaveBrine },
            new MonsterDef { id = "Spinewalker", art = "BelSpinewalker", basePrefab = "EnemyGiantSpider_Standard", health = 6f, evolveCost = 2.5f,
                             evolveTo = new[] { "CrownOfThorns", "BroodUrchin" }, kit = SpinewalkerKit, customize = LeaveBrine },
            new MonsterDef { id = "SaltSiren", art = "BelSiren", basePrefab = "EnemyWitch", health = 5.5f, evolveCost = 2.5f,
                             evolveTo = new[] { "TideMatriarch", "JellySiren" }, kit = SirenKit, customize = LeaveBrine },
            new MonsterDef { id = "BrineLamprey", art = "BelLamprey", basePrefab = "EnemyTentacleGlutton", health = 5.5f, evolveCost = 2.5f,
                             evolveTo = new[] { "GulperEel", "SlimeHag" }, kit = LampreyKit, customize = LeaveBrine },
            new MonsterDef { id = "BellHermit", art = "BelHermit", basePrefab = "EnemyBlobfish", health = 6.5f, speedMult = 1.35f, evolveCost = 2.5f,
                             evolveTo = new[] { "AbyssKraken", "BelltowerHermit" }, kit = HermitKit, customize = LeaveBrine },
            new MonsterDef { id = "AnemoneBoxer", art = "BelBoxer", basePrefab = "EnemyScorpion", health = 6.5f, evolveCost = 2.5f,
                             evolveTo = new[] { "AnemoneColossus", "ReefChampion" }, kit = BoxerKit, customize = LeaveBrine },
            new MonsterDef { id = "DrownedBell", art = "BelDrownedBell", basePrefab = "EnemyTroll", health = 12f, evolveCost = 4.5f,
                             kit = BellKit, customize = LeaveBrine },
            new MonsterDef { id = "DrownedCaptain", art = "BelCaptain", basePrefab = "EnemyMinotaur", health = 11f, evolveCost = 4.5f,
                             kit = CaptainKit, customize = LeaveBrine },
            new MonsterDef { id = "CrownOfThorns", art = "BelCrownThorns", basePrefab = "EnemyCapraDemon", health = 11f, speedMult = 0.85f, evolveCost = 4.5f,
                             kit = CrownKit, customize = LeaveBrine },
            new MonsterDef { id = "BroodUrchin", art = "BelBrood", basePrefab = "EnemyGhoul", health = 11.5f, speedMult = 0.8f, evolveCost = 4.5f,
                             kit = BroodKit, customize = LeaveBrine },
            new MonsterDef { id = "TideMatriarch", art = "BelMatriarch", basePrefab = "EnemyPriestess", health = 11f, evolveCost = 4.5f,
                             kit = MatriarchKit, customize = LeaveBrine },
            new MonsterDef { id = "JellySiren", art = "BelJellySiren", basePrefab = "EnemyFacelessShaman", health = 10.5f, evolveCost = 4.5f,
                             kit = JellyKit, customize = LeaveBrine },
            new MonsterDef { id = "GulperEel", art = "BelGulperEel", basePrefab = "EnemyDemonSnake", health = 10.5f, evolveCost = 4.5f,
                             kit = GulperKit, customize = LeaveBrine },
            new MonsterDef { id = "SlimeHag", art = "BelSlimeHag", basePrefab = "EnemyStingerTadpole_Giant", health = 11f, speedMult = 0.9f, evolveCost = 4.5f,
                             kit = HagKit, customize = LeaveBrine },
            new MonsterDef { id = "AbyssKraken", art = "BelKraken", basePrefab = "EnemyOctopusHead", health = 11.5f, speedMult = 0.8f, evolveCost = 4.5f,
                             kit = KrakenKit, customize = LeaveBrine },
            new MonsterDef { id = "BelltowerHermit", art = "BelBelltower", basePrefab = "EnemyDarkGuardian", health = 12f, speedMult = 0.85f, evolveCost = 4.5f,
                             kit = BelltowerKit, customize = LeaveBrine },
            new MonsterDef { id = "AnemoneColossus", art = "BelColossus", basePrefab = "EnemySkeletonGiantShield", health = 12f, speedMult = 0.8f, evolveCost = 4.5f,
                             kit = ColossusKit, customize = LeaveBrine },
            new MonsterDef { id = "ReefChampion", art = "BelChampion", basePrefab = "EnemyEyelessBeast", health = 11f, evolveCost = 4.5f,
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
            flavour = "The bell went down with the town.\nIt still rings at high tide.",
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
