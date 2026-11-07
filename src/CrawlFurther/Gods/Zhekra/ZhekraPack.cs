using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Zhekra
{
    using CrawlFurther.Art;
    using CrawlFurther.Gods;
    using CrawlFurther.Items;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;
    using CrawlFurther.Content.Gods.Ossivar;
    using CrawlFurther.Content.Items;

    /// <summary>
    /// Zhekra, the Brood Queen: the swarm. Insects that are weak alone and dangerous together, a hive that feeds itself.
    /// The perk (<see cref="ZhkBrain"/>): the dead hatch a biting larva, and a Zhekra monster near any other monster swarms.
    /// Every monster has a signature of its own (a <see cref="ZhkBehaviour"/>) with a tell the hero can read, and most of
    /// them do something to or for their kin. Offsets below are the sprite's sync points (art/out_zhekra/TIMING.md),
    /// x forward, y up.
    /// </summary>
    public static class ZhekraPack
    {
        static exSpriteAnimClip Looped(SpriteSheet sh, string anim, string clip)
        {
            return sh.Has(anim) ? new ClipBuilder(sh, anim, clip).Loop().Build() : null;
        }

        static exSpriteAnimClip Once(SpriteSheet sh, string anim, string clip)
        {
            return sh.Has(anim) ? new ClipBuilder(sh, anim, clip).Once().Build() : null;
        }

        static exSpriteAnimClip[] Stances(SpriteSheet sh, string anim, string clip, params string[] suffixes)
        {
            var a = new exSpriteAnimClip[suffixes.Length];
            for (int i = 0; i < suffixes.Length; i++) a[i] = Looped(sh, anim + suffixes[i], clip + anim + suffixes[i]);
            return a;
        }

        /// <summary>A special that stops the body: no aiming, no moving, then the events.</summary>
        static ClipBuilder Still(SpriteSheet sh, string anim, string clip)
        {
            return new ClipBuilder(sh, anim, clip).Once().Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop");
        }

        // ---------------------------------------------------------------------------------------------- tier 1
        // Acid Grub: a lunging bite (35% Corroded); Spit throws a glob of acid. Signature: GrubGorge (it grows on bites).
        static void GrubKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            var sfx = new[] { "", "1", "2", "3" };
            var bites = new List<AttackData>();
            var spits = new exSpriteAnimClip[4];
            for (int k = 0; k < 4; k++)
            {
                // each feed puts the mouth 1.25 px further forward
                int bite = Kit.AddEffect(p, ZhekraFx.GrubBite, attach: true, destroyOnAnimEnd: true, offsetX: 14f + 1.3f * k, offsetY: 4f);
                int spit = Kit.AddEffect(p, ZhekraFx.AcidSpit, offsetX: 12f + 1.3f * k, offsetY: 6f);
                bites.Add(Kit.Attack(a0, Kit.Melee(sh, "Bite" + sfx[k], "ModZhkGrubBite" + sfx[k], v, 2, bite, 70f).Build(), 1.3f,
                                     rangeInner: 12f, rangeOuter: 27f + k));
                spits[k] = Kit.Shot(sh, "Spit" + sfx[k], "ModZhkGrubSpit" + sfx[k], 3, v, 0f, spit).Build();
            }
            atk.Clear();
            atk.AddRange(bites);
            Kit.SetSpecial(p, Kit.Attack(sp, spits[0], 0f, rangeInner: 30f, rangeOuter: 90f, rangeRetreat: 20f), 5.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 5f);
            GrubGorge.Idles = Stances(sh, "Idle", "ModZhkGrub", sfx);
            GrubGorge.Runs = Stances(sh, "Run", "ModZhkGrub", sfx);
            GrubGorge.Spits = spits;
        }

        // Brood Drone: a stinger dart; Dive folds its wings and dashes through the hero, sting first. Signature:
        // DroneLastSting (below 1 health the dive hits twice as hard and kills it).
        static void DroneKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int dart = Kit.AddEffect(p, ZhekraFx.Stinger, offsetX: 6f, offsetY: 12f);
            int dive = Kit.AddEffect(p, ZhekraFx.DroneDive, attach: true, destroyOnAnimEnd: true, offsetX: 6f, offsetY: 7f);
            int last = Kit.AddEffect(p, ZhekraFx.DroneDiveLast, attach: true, destroyOnAnimEnd: true, offsetX: 6f, offsetY: 7f);
            var st = Kit.Shot(sh, "Sting", "ModZhkDroneSting", 3, v, 0f, dart).Build();
            Func<string, int, bool, exSpriteAnimClip> diveClip = (anim, fx, fatal) =>
            {
                var c = new ClipBuilder(sh, anim, "ModZhkDrone" + anim).Once()
                    .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(1, "AnimInputMultiplyStop").Ev(1, "AnimInputOff")
                    .EvF(2, "AnimMove", 200f).Ev(2, "AnimAttack", fx).EvO(2, "AnimSound", v).Ev(5, "AnimMoveStop");
                if (fatal) c.Ev(-1, "ModZhkLastSting");
                return c.Ev(-1, "AnimRun").Build();
            };
            atk.Clear();
            atk.Add(Kit.Attack(a0, st, 1.2f, rangeInner: 45f, rangeOuter: 100f, rangeRetreat: 35f));
            Kit.SetSpecial(p, Kit.Attack(sp, diveClip("Dive", dive, false), 0f, rangeInner: 25f, rangeOuter: 80f, rangeRetreat: 0f), 5.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 12f);
            DroneLastSting.IdleLast = Looped(sh, "IdleLast", "ModZhkDroneIdleLast");
            DroneLastSting.RunLast = Looped(sh, "RunLast", "ModZhkDroneRunLast");
            DroneLastSting.DiveLast = sh.Has("DiveLast") ? diveClip("DiveLast", last, true) : null;
        }

        // Resin Beetle: a mandible snap that shoves; Resin spits a glob that roots and leaves a sticky puddle.
        // Signature: BeetleShove (shoved onto resin, the hero sticks).
        static void BeetleKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int snap = Kit.AddEffect(p, ZhekraFx.BeetleSnap, attach: true, destroyOnAnimEnd: true, offsetX: 11f, offsetY: 3f);
            int glob = Kit.AddEffect(p, ZhekraFx.ResinGlob, offsetX: 10f, offsetY: 1f);   // runs along the floor, drawn at the jaws
            var sn = Kit.Melee(sh, "Snap", "ModZhkBeetleSnap", v, 2, snap, 60f).Build();
            var rs = Kit.Shot(sh, "Resin", "ModZhkBeetleResin", 3, v, 0f, glob).Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sn, 1.2f, rangeInner: 12f, rangeOuter: 26f));
            Kit.SetSpecial(p, Kit.Attack(sp, rs, 0f, rangeInner: 30f, rangeOuter: 90f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 5f);
        }

        // ---------------------------------------------------------------------------------------------- tier 2
        // Acid Spitter: a glob that slides along the floor and bursts into an acid pool; Egg lays an egg that hatches a
        // larva. Signature: SpitterSac (a full sac makes a pool twice as wide; a hit on a full sac bursts it).
        static void SpitterKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int lob = Kit.AddEffect(p, ZhekraFx.AcidGlob, offsetX: 12f, offsetY: 1f);
            int wide = Kit.AddEffect(p, ZhekraFx.AcidGlobWide, offsetX: 12f, offsetY: 1f);
            int egg = Kit.AddEffect(p, ZhekraFx.LarvaEgg, offsetX: -9f, offsetY: 2f);
            var lb = Kit.Shot(sh, "Lob", "ModZhkSpitterLob", 3, v, 0f, lob).Build();
            var full = Kit.Shot(sh, "LobFull", "ModZhkSpitterLobFull", 3, v, 0f, wide).Ev(3, "ModZhkSacEmpty").Build();
            var eg = Still(sh, "Egg", "ModZhkSpitterEgg").Ev(4, "AnimAttack", egg).EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, lb, 1.6f, rangeInner: 50f, rangeOuter: 120f, rangeRetreat: 40f));
            atk.Add(Kit.Attack(a0, full, 1.6f, rangeInner: 50f, rangeOuter: 120f, rangeRetreat: 40f));
            Kit.SetSpecial(p, Kit.Attack(sp, eg, 0f, rangeInner: 0f, rangeOuter: 140f, rangeRetreat: 30f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 10f);
            SpitterSac.Idles = Stances(sh, "Idle", "ModZhkSpitter", "", "1", "2", "3");
            SpitterSac.Runs = Stances(sh, "Run", "ModZhkSpitter", "", "1", "2", "3");
        }

        // Hive Soldier: two scythe sweeps; Scythe Guard raises the scythes for 2 s and strikes whatever steps in.
        // Signature: SoldierGuard (Hair Trigger: the strike lands 0.1 s after the hero steps in; a quiet guard speeds the
        // next sweep).
        static void SoldierKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int cut = Kit.AddEffect(p, ZhekraFx.Scythe, attach: true, destroyOnAnimEnd: true, offsetX: 13f, offsetY: 9f);
            var sc = Kit.Melee(sh, "Scythe", "ModZhkSoldierScythe", v, 2, cut, 40f, 4, cut, 30f).Build();
            var fast = Kit.Melee(sh, "Scythe", "ModZhkSoldierScytheFast", v, 2, cut, 50f, 4, cut, 40f).Speed(1.5f).Ev(-1, "ModZhkSweepDone").Build();
            var gd = Still(sh, "Guard", "ModZhkSoldierGuard").Then("GuardHold", 5).EvO(1, "AnimSound", v)
                .Ev(3, "ModZhkGuardOn").Ev(-1, "ModZhkGuardOff").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sc, 1.3f, rangeInner: 14f, rangeOuter: 30f));
            atk.Add(Kit.Attack(a0, fast, 1.3f, rangeInner: 14f, rangeOuter: 30f));
            Kit.SetSpecial(p, Kit.Attack(sp, gd, 0f, rangeInner: 0f, rangeOuter: 48f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 9f);
            SoldierGuard.StrikeClip = Once(sh, "Strike", "ModZhkSoldierStrike");
        }

        // Hive Hornet: a fan of three stingers; Mark flicks a pheromone dart (4 s). Signature (the Scent Trail): a Marked
        // hero leaves amber prints that speed up any Zhekra on them (ZhkHero, ZhkBrain).
        static void HornetKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            var fan = new List<int>();
            foreach (var a in new[] { -14f, 0.01f, 14f }) fan.Add(Kit.AddEffect(p, ZhekraFx.HornetStinger, offsetX: 14f, offsetY: 8f, angle: a));
            int dart = Kit.AddEffect(p, ZhekraFx.MarkDart, offsetX: 14f, offsetY: 8f);
            var vl = Kit.Shot(sh, "Volley", "ModZhkHornetVolley", 3, v, 0.04f, fan.ToArray()).Build();
            var mk = Kit.Shot(sh, "Mark", "ModZhkHornetMark", 4, v, 0f, dart).Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, vl, 1.4f, rangeInner: 45f, rangeOuter: 105f, rangeRetreat: 35f));
            Kit.SetSpecial(p, Kit.Attack(sp, mk, 0f, rangeInner: 40f, rangeOuter: 130f, rangeRetreat: 30f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 8f);
        }

        // Blood Siphon: a needle stab; Feed dives onto the hero and stabs three times. Signature: SiphonEngorge (each stab
        // fills the belly; killed full, it bursts as a heal for its kin).
        static void SiphonKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int stab = Kit.AddEffect(p, ZhekraFx.Stab, attach: true, destroyOnAnimEnd: true, offsetX: 16f, offsetY: 7f);
            int feed = Kit.AddEffect(p, ZhekraFx.FeedStab, attach: true, offsetX: 12f, offsetY: 6f);
            var st = Kit.Melee(sh, "Stab", "ModZhkSiphonStab", v, 2, stab, 40f).Build();
            var fd = new ClipBuilder(sh, "Feed", "ModZhkSiphonFeed").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(1, "AnimInputMultiplyStop").Ev(1, "AnimInputOff")
                .EvF(1, "AnimMove", 220f).EvO(1, "AnimSound", v).Ev(2, "AnimMoveStop")
                .Ev(2, "AnimAttack", feed).Ev(4, "AnimAttack", feed).Ev(6, "AnimAttack", feed).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, st, 1.3f, rangeInner: 12f, rangeOuter: 26f));
            Kit.SetSpecial(p, Kit.Attack(sp, fd, 0f, rangeInner: 15f, rangeOuter: 55f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 7f);
            SiphonEngorge.Idles = Stances(sh, "Idle", "ModZhkSiphon", "", "1", "2", "3");
            SiphonEngorge.Runs = Stances(sh, "Run", "ModZhkSiphon", "", "1", "2", "3");
        }

        // Nasute: three glue specks (each may root); Shore Up gives it and its kin a resin plate. Signature:
        // NasuteBodyguard (hit its kin and it squirts you).
        static void NasuteKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int speck = Kit.AddEffect(p, ZhekraFx.GlueSpeck, offsetX: 16f, offsetY: 13f);
            var sq = Kit.Shot(sh, "Specks", "ModZhkNasuteSpecks", 2, v, 0.06f, speck, speck, speck).Build();
            var su = Still(sh, "ShoreUp", "ModZhkNasuteShoreUp").Ev(4, "ModZhkShoreUp").EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sq, 1.3f, rangeInner: 20f, rangeOuter: 65f, rangeRetreat: 15f));
            Kit.SetSpecial(p, Kit.Attack(sp, su, 0f, rangeInner: 0f, rangeOuter: 120f, rangeRetreat: 20f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 13f);
            NasuteBodyguard.PuffClip = Once(sh, "Puff", "ModZhkNasutePuff");
        }

        // Amber Scarab: bowls its resin ball (0.8 / 1.0 / 1.2 by size, the biggest roots) or hurls it onto the hero's spot.
        // Signature: ScarabStock (no ball, no threat: basic 0 is a weak headbutt).
        static void ScarabKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int butt = Kit.AddEffect(p, ZhekraFx.Butt, attach: true, destroyOnAnimEnd: true, offsetX: 9f, offsetY: 4f);
            atk.Clear();
            atk.Add(Kit.Attack(a0, Kit.Melee(sh, "Butt", "ModZhkScarabButt", v, 2, butt, 40f).Build(), 1.4f, rangeInner: 8f, rangeOuter: 20f));
            var hurls = new exSpriteAnimClip[4];
            hurls[0] = Kit.Melee(sh, "Butt", "ModZhkScarabButtSpecial", v, 2, butt, 40f).Build();
            for (int s = 1; s <= 3; s++)
            {
                string sfx = s == 3 ? "" : s.ToString();
                int ball = Kit.AddEffect(p, ZhekraFx.RollBall[s], offsetX: 14f, offsetY: 1f);
                var bw = Kit.Shot(sh, "Bowl" + sfx, "ModZhkScarabBowl" + sfx, 2, v, 0f, ball).Ev(3, "ModZhkBallUsed").Build();
                atk.Add(Kit.Attack(a0, bw, 1.6f, rangeInner: 30f, rangeOuter: 110f, rangeRetreat: 20f));
                hurls[s] = Still(sh, "Hurl" + sfx, "ModZhkScarabHurl" + sfx).EvO(3, "AnimSound", v).Ev(3, "ModZhkHurl")
                    .Ev(3, "ModZhkBallUsed").Ev(-1, "AnimRun").Build();
            }
            Kit.SetSpecial(p, Kit.Attack(sp, hurls[3], 0f, rangeInner: 30f, rangeOuter: 150f, rangeRetreat: 20f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 5f);
            ScarabStock.Idles = Stances(sh, "Idle", "ModZhkScarab", "0", "1", "2", "");
            ScarabStock.Runs = Stances(sh, "Run", "ModZhkScarab", "0", "1", "2", "");
            ScarabStock.Hurls = hurls;
        }

        // ---------------------------------------------------------------------------------------------- tier 3
        // Brood Mother: Acid Rain drops three splats on and by the hero; Frenzy Call frenzies everything within 110 px and
        // lays two eggs. Signature: MotherJelly (larvae near her don't wither; she feeds one into an Acid Grub).
        static void MotherKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int pher = Kit.AddEffect(p, ZhekraFx.Pheromone, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            int e1 = Kit.AddEffect(p, ZhekraFx.LarvaEgg, offsetX: -24f, offsetY: 1f);
            int e2 = Kit.AddEffect(p, ZhekraFx.LarvaEgg, offsetX: -19f, offsetY: 1f);
            var rn = new ClipBuilder(sh, "Rain", "ModZhkMotherRain").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff")
                .Ev(3, "ZhkAcidRain").EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            var cl = Still(sh, "Call", "ModZhkMotherCall").Ev(2, "AnimAttack", pher).Ev(2, "ZhkFrenzyCall").EvO(2, "AnimSound", v)
                .Ev(4, "AnimAttack", e1).Ev(5, "AnimAttack", e2).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, rn, 2f, rangeInner: 40f, rangeOuter: 150f, rangeRetreat: 30f));
            Kit.SetSpecial(p, Kit.Attack(sp, cl, 0f, rangeInner: 0f, rangeOuter: 200f, rangeRetreat: 20f), 7.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 20f);
        }

        // Acid Bloater: a slow bubble that pops into drops; Deflate whistles and zips round the room. Signature:
        // BloaterDeflate (it hangs limp after, then refills; its bubble drops 6 / 4 / 2 by size).
        static void BloaterKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            atk.Clear();
            var sfx = new[] { "", "Mid", "Low" };
            for (int s = 0; s < 3; s++)
            {
                int bub = Kit.AddEffect(p, ZhekraFx.Bubble[2 - s], offsetX: 18f - 3f * s, offsetY: 15f - 3f * s);
                atk.Add(Kit.Attack(a0, Kit.Shot(sh, "Blow" + sfx[s], "ModZhkBloaterBlow" + sfx[s], 4, v, 0f, bub).Build(), 2f,
                                   rangeInner: 40f, rangeOuter: 120f, rangeRetreat: 30f));
            }
            var df = Still(sh, "Whistle", "ModZhkBloaterDeflate").Then("Zip", 6).EvO(0, "AnimSound", v).Ev(4, "ModZhkDeflate").Ev(-1, "AnimRun").Build();
            Kit.SetSpecial(p, Kit.Attack(sp, df, 0f, rangeInner: 20f, rangeOuter: 110f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 15f);
            BloaterDeflate.Idles = Stances(sh, "Idle", "ModZhkBloater", sfx);
            BloaterDeflate.Runs = Stances(sh, "Run", "ModZhkBloater", sfx);
            BloaterDeflate.LimpClip = Looped(sh, "Limp", "ModZhkBloaterLimp");
        }

        // Acid Mantis: Twin Blades (1.4x on a Corroded hero); Scissor Catch opens both blades wide for 0.5 s and snaps them
        // shut in an X ahead (a hero at the crossing takes both). Signature: MantisReflex (it cuts a shot a second).
        static void MantisKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int cut = Kit.AddEffect(p, ZhekraFx.Reap, attach: true, destroyOnAnimEnd: true, offsetX: 13f, offsetY: 14f);
            int x1 = Kit.AddEffect(p, ZhekraFx.ScissorHit, attach: true, destroyOnAnimEnd: true, offsetX: 14f, offsetY: 16f);
            int x2 = Kit.AddEffect(p, ZhekraFx.ScissorHit, attach: true, destroyOnAnimEnd: true, offsetX: 16f, offsetY: 13f);
            var bl = Kit.Melee(sh, "Blades", "ModZhkMantisBlades", v, 2, cut, 40f, 4, cut, 30f).Build();
            var sc = new ClipBuilder(sh, "Scissor", "ModZhkMantisScissor").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff")
                .EvF(3, "AnimMoveStick", 40f).Ev(3, "AnimAttack", x1).Ev(3, "AnimAttack", x2).EvO(3, "AnimSound", v)
                .Ev(4, "AnimMoveStop").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, bl, 1.4f, rangeInner: 14f, rangeOuter: 28f));
            Kit.SetSpecial(p, Kit.Attack(sp, sc, 0f, rangeInner: 12f, rangeOuter: 34f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 14f);
            MantisReflex.ReflexClip = Once(sh, "Reflex", "ModZhkMantisReflex");
        }

        // Pit Antlion: Jaw Clamp (may bleed); Sand Pit digs in and opens a pit round it for 5 s. Signature: AntlionPit
        // (the slope and the sand flicks).
        static void AntlionKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int bite = Kit.AddEffect(p, ZhekraFx.Clamp, attach: true, destroyOnAnimEnd: true, offsetX: 20f, offsetY: 6f);
            int dirt = Kit.AddEffect(p, ZhekraFx.Dirt, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            var cl = Kit.Melee(sh, "Clamp", "ModZhkAntlionClamp", v, 2, bite, 40f).Build();
            var dg = Still(sh, "Dig", "ModZhkAntlionDig").Ev(0, "AnimAttack", dirt).EvO(0, "AnimSound", v).Ev(3, "AnimAttack", dirt)
                .Ev(-1, "ModZhkPit").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, cl, 1.5f, rangeInner: 14f, rangeOuter: 30f));
            Kit.SetSpecial(p, Kit.Attack(sp, dg, 0f, rangeInner: 0f, rangeOuter: 45f, rangeRetreat: 0f), 7.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 7f);
            AntlionPit.PitIdle = Looped(sh, "PitIdle", "ModZhkAntlionPitIdle");
            AntlionPit.FlickClip = Once(sh, "Flick", "ModZhkAntlionFlick");
            AntlionPit.EmergeClip = Once(sh, "Emerge", "ModZhkAntlionEmerge");
        }

        // Amber Hive: Comb Slam drops its weight forward; Swarm Out sends two slow hornet swarms that sting and Mark.
        // Signature: HiveComb (each hero hit spills amber it mends in).
        static void HiveKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int slam = Kit.AddEffect(p, ZhekraFx.Slam, attach: true, destroyOnAnimEnd: true, offsetX: 16f, offsetY: 8f);
            int c1 = Kit.AddEffect(p, ZhekraFx.SwarmCloud, offsetX: 14f, offsetY: 14f, angle: -16f);
            int c2 = Kit.AddEffect(p, ZhekraFx.SwarmCloud, offsetX: 14f, offsetY: 14f, angle: 16f);
            var sl = Kit.Melee(sh, "Slam", "ModZhkHiveSlam", v, 2, slam, 30f).Build();
            var sw = Kit.Shot(sh, "Swarm", "ModZhkHiveSwarm", 3, v, 0.1f, c1, c2).Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sl, 1.6f, rangeInner: 14f, rangeOuter: 30f));
            Kit.SetSpecial(p, Kit.Attack(sp, sw, 0f, rangeInner: 40f, rangeOuter: 140f, rangeRetreat: 20f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 14f);
            HiveComb.IdleCrack = Looped(sh, "IdleCrack", "ModZhkHiveIdleCrack");
            HiveComb.RunCrack = Looped(sh, "RunCrack", "ModZhkHiveRunCrack");
        }

        // Hunting Wasp: Lance Sting (may daze); Hunter's Mark rises, circles once and Marks the hero from range. Signature:
        // HunterCarry (a lance on a Marked hero carries him into the swarm).
        static void HunterKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int lance = Kit.AddEffect(p, ZhekraFx.Lance, attach: true, destroyOnAnimEnd: true, offsetX: 20f, offsetY: 16f);
            var ln = Kit.Melee(sh, "Lance", "ModZhkHunterLance", v, 3, lance, 50f).Build();
            var rs = Still(sh, "Rise", "ModZhkHunterRise").EvO(1, "AnimSound", v).Ev(6, "ModZhkHunterMark").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, ln, 1.4f, rangeInner: 14f, rangeOuter: 32f));
            Kit.SetSpecial(p, Kit.Attack(sp, rs, 0f, rangeInner: 40f, rangeOuter: 160f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 16f);
            HunterCarry.CarryClip = Looped(sh, "Carry", "ModZhkHunterCarry");
        }

        // Blood Gorger: Drill (may bleed); Transfuse pumps its stored blood into the nearest kin. Signature: GorgerBank.
        static void GorgerKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int drill = Kit.AddEffect(p, ZhekraFx.Drill, attach: true, destroyOnAnimEnd: true, offsetX: 16f, offsetY: 12f);
            var dr = Kit.Melee(sh, "Drill", "ModZhkGorgerDrill", v, 2, drill, 35f).Build();
            var pm = Still(sh, "Pump", "ModZhkGorgerPump").Ev(2, "ModZhkTransfuse").EvO(2, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, dr, 1.5f, rangeInner: 14f, rangeOuter: 30f));
            Kit.SetSpecial(p, Kit.Attack(sp, pm, 0f, rangeInner: 0f, rangeOuter: 140f, rangeRetreat: 20f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 12f);
            GorgerBank.Idles = Stances(sh, "Idle", "ModZhkGorger", "", "1", "2", "3");
            GorgerBank.Runs = Stances(sh, "Run", "ModZhkGorger", "", "1", "2", "3");
        }

        // Botfly Matron: Head Ram; Egg Dart implants the hero for 4 s. Signature (Hatchery, on the hero: ZhkHero): while
        // the egg is in him, every hit he takes pops a larva out of him (up to three).
        static void BotflyKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int ram = Kit.AddEffect(p, ZhekraFx.Ram, attach: true, destroyOnAnimEnd: true, offsetX: 13f, offsetY: 16f);
            int dart = Kit.AddEffect(p, ZhekraFx.EggDart, offsetX: 10f, offsetY: 18f);
            var rm = Kit.Melee(sh, "Ram", "ModZhkBotflyRam", v, 2, ram, 70f).Build();
            var ed = Kit.Shot(sh, "EggDart", "ModZhkBotflyEggDart", 4, v, 0f, dart).Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, rm, 1.4f, rangeInner: 14f, rangeOuter: 31f));
            Kit.SetSpecial(p, Kit.Attack(sp, ed, 0f, rangeInner: 35f, rangeOuter: 110f, rangeRetreat: 30f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 16f);
        }

        // Chitin Colossus: Horn Gore throws the hero back; Bulldozer charges 80 px, shoving the hero ahead and leaving
        // resin. Signature: ColossusPlate (its front is armour, it turns slowly).
        static void ColossusKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int gore = Kit.AddEffect(p, ZhekraFx.Gore, attach: true, destroyOnAnimEnd: true, offsetX: 18f, offsetY: 12f);
            int end = Kit.AddEffect(p, ZhekraFx.BullHit, attach: true, destroyOnAnimEnd: true, offsetX: 18f, offsetY: 8f);
            int trail = Kit.AddEffect(p, ZhekraFx.Resin, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            var gr = Kit.Melee(sh, "Gore", "ModZhkColossusGore", v, 2, gore, 30f).Build();
            var bd = new ClipBuilder(sh, "Bulldoze", "ModZhkColossusBulldoze").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(1, "AnimInputMultiplyStop").Ev(1, "AnimInputOff")
                .EvF(2, "AnimMove", 280f).EvF(2, "ModZhkBulldoze", 0.28f).EvO(2, "AnimSound", v).Ev(3, "AnimAttack", trail)
                .Ev(5, "AnimAttack", trail).Ev(6, "AnimMoveStop").Ev(6, "AnimAttack", end).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, gr, 1.6f, rangeInner: 16f, rangeOuter: 32f));
            Kit.SetSpecial(p, Kit.Attack(sp, bd, 0f, rangeInner: 20f, rangeOuter: 100f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 10f);
        }

        // Glue Mortar: lobs a glue shell on the hero (slows, leaves glue); Bombard drops three, one on the hero and one on
        // each of the two Zhekra nearest him. Signature: MortarSpotters (it aims through its kin).
        static void MortarKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            var lb = new ClipBuilder(sh, "Shell", "ModZhkMortarShell").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff")
                .Ev(3, "ModZhkShell", 0).EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            var bb = Still(sh, "Bombard", "ModZhkMortarBombard").Ev(2, "ModZhkShell", 0).EvO(2, "AnimSound", v)
                .Ev(4, "ModZhkShell", 1).EvO(4, "AnimSound", v).Ev(6, "ModZhkShell", 2).EvO(6, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, lb, 2.2f, rangeInner: 50f, rangeOuter: 150f, rangeRetreat: 40f));
            atk.Add(Kit.Attack(a0, lb, 3.6f, rangeInner: 50f, rangeOuter: 150f, rangeRetreat: 40f));
            Kit.SetSpecial(p, Kit.Attack(sp, bb, 0f, rangeInner: 40f, rangeOuter: 160f, rangeRetreat: 30f), 7.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 14f);
        }

        // Stag Titan: Mandible Pinch hits only at the jaw tips; Uproot hooks the hero and tosses him up. Signature:
        // StagJaws (inside 18 px it can only headbutt).
        static void StagKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int tips = Kit.AddEffect(p, ZhekraFx.Pinch, attach: true, destroyOnAnimEnd: true, offsetX: 30f, offsetY: 6f);
            int butt = Kit.AddEffect(p, ZhekraFx.StagButt, attach: true, destroyOnAnimEnd: true, offsetX: 12f, offsetY: 6f);
            var pn = Kit.Melee(sh, "Pinch", "ModZhkStagPinch", v, 2, tips, 0f).Build();
            var bt = Kit.Melee(sh, "Butt", "ModZhkStagButt", v, 2, butt, 30f).Build();
            var up = new ClipBuilder(sh, "Uproot", "ModZhkStagUproot").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(1, "AnimInputMultiplyStop").Ev(1, "AnimInputOff")
                .Ev(2, "ModZhkUproot").EvO(2, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, pn, 1.5f, rangeInner: 24f, rangeOuter: 34f));
            atk.Add(Kit.Attack(a0, bt, 1.3f, rangeInner: 0f, rangeOuter: 18f));
            Kit.SetSpecial(p, Kit.Attack(sp, up, 0f, rangeInner: 20f, rangeOuter: 38f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 6f);
        }

        // Sun Scarab: Shove pushes its ball into the hero (big knockback); Release sends the ball rolling at him. Signature:
        // SunScarabFossil (the ball picks up larvae and lets them out on impact).
        static void SunScarabKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int shove = Kit.AddEffect(p, ZhekraFx.Shove, attach: true, destroyOnAnimEnd: true, offsetX: 22f, offsetY: 8f);
            var sv = Kit.Melee(sh, "Shove", "ModZhkSunScarabShove", v, 2, shove, 45f).Build();
            var rl = new ClipBuilder(sh, "Release", "ModZhkSunScarabRelease").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(1, "AnimInputMultiplyStop").Ev(1, "AnimInputOff")
                .Ev(2, "ModZhkRelease").EvO(2, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sv, 1.6f, rangeInner: 16f, rangeOuter: 34f));
            Kit.SetSpecial(p, Kit.Attack(sp, rl, 0f, rangeInner: 35f, rangeOuter: 150f, rangeRetreat: 20f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 8f);
            SunScarabFossil.Idles = Stances(sh, "Idle", "ModZhkSunScarab", "", "1", "2", "3");
            SunScarabFossil.Runs = Stances(sh, "Run", "ModZhkSunScarab", "", "1", "2", "3");
            SunScarabFossil.IdleEmpty = Looped(sh, "IdleEmpty", "ModZhkSunScarabIdleEmpty");
            SunScarabFossil.RunEmpty = Looped(sh, "RunEmpty", "ModZhkSunScarabRunEmpty");
        }

        // ---------------------------------------------------------------------------------------------- minions
        // The larva the perk, the eggs, implants and amber hatch (fodder base: it has an AI brain). 1 health, lives 8 s.
        static void LarvaKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0];
            int n0 = Strike.Mark(p);
            int bite = Kit.AddEffect(p, ZhekraFx.LarvaBite, attach: true, destroyOnAnimEnd: true, offsetX: 7f, offsetY: 2f);
            atk.Clear();
            atk.Add(Kit.Attack(a0, Kit.Melee(sh, "Bite", "ModZhkLarvaBite", Kit.Voice(p), 2, bite, 40f).Build(), 1f, rangeInner: 6f, rangeOuter: 18f));
            R.Set(p, "m_hasSpecialAttack", false);
            Strike.Feet(p, n0, 3f);
            MinionAI.Tune(p, 140f, 8f, 13f, 1.0f, 1.5f);
        }

        // The Acid Grub a Brood Mother raises from a larva (Royal Jelly): an AI-driven grub that bites and coats in acid.
        static void GrublingKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0];
            int n0 = Strike.Mark(p);
            int bite = Kit.AddEffect(p, ZhekraFx.GrubBite, attach: true, destroyOnAnimEnd: true, offsetX: 14f, offsetY: 4f);
            atk.Clear();
            atk.Add(Kit.Attack(a0, Kit.Melee(sh, "Bite", "ModZhkGrublingBite", Kit.Voice(p), 2, bite, 60f).Build(), 1.3f, rangeInner: 10f, rangeOuter: 24f));
            R.Set(p, "m_hasSpecialAttack", false);
            Strike.Feet(p, n0, 5f);
            MinionAI.Tune(p, 160f, 12f, 20f, 1.2f, 1.8f);
        }

        static void Hatchling(GameObject go, Player p) { Kit.AddDeathSpawn(p, ZhekraFx.LarvaHatch); Strike.DeathAtFeet(p); }

        public static readonly MonsterDef Larva = new MonsterDef
        {
            id = "ZhkLarva", art = "ZhkLarva", basePrefab = "EnemyFodderMushroom", health = 1f, speedMult = 1.3f, kit = LarvaKit
        };

        public static readonly MonsterDef Grubling = new MonsterDef
        {
            id = "ZhkGrubling", art = "ZhkGrub", basePrefab = "EnemyFodderMushroom", health = 4f, speedMult = 0.9f, kit = GrublingKit
        };

        // Evolution tree: every evolution has exactly one parent.
        //   Grub   -> Spitter, Soldier        Spitter -> Mother, Bloater        Soldier -> Mantis, Antlion
        //   Drone  -> Hornet, Siphon          Hornet  -> Hive, Hunter           Siphon  -> Gorger, Botfly
        //   Beetle -> Nasute, Scarab          Nasute  -> Colossus, Mortar       Scarab  -> Stag, SunScarab
        public static readonly List<MonsterDef> Monsters = new List<MonsterDef>
        {
            new MonsterDef { id = "ZhkGrub", art = "ZhkGrub", basePrefab = "EnemyGiantRat_Fireball", health = 4f, speedMult = 0.85f, evolveCost = 0f,
                             evolveTo = new[] { "ZhkSpitter", "ZhkSoldier" }, kit = GrubKit, customize = Hatchling },
            new MonsterDef { id = "ZhkDrone", art = "ZhkDrone", basePrefab = "EnemyFlyingEye_Dodge", health = 3f, evolveCost = 0f,
                             evolveTo = new[] { "ZhkHornet", "ZhkSiphon" }, kit = DroneKit, customize = Hatchling },
            new MonsterDef { id = "ZhkBeetle", art = "ZhkBeetle", basePrefab = "EnemyGiantSpider_Standard", health = 4.5f, speedMult = 0.9f, evolveCost = 0f,
                             evolveTo = new[] { "ZhkNasute", "ZhkScarab" }, kit = BeetleKit, customize = Hatchling },
            new MonsterDef { id = "ZhkSpitter", art = "ZhkSpitter", basePrefab = "EnemyWitch", health = 5.5f, evolveCost = 2.5f,
                             evolveTo = new[] { "ZhkMother", "ZhkBloater" }, kit = SpitterKit, customize = Hatchling },
            new MonsterDef { id = "ZhkSoldier", art = "ZhkSoldier", basePrefab = "EnemyScorpion", health = 7f, speedMult = 0.9f, evolveCost = 2.5f,
                             evolveTo = new[] { "ZhkMantis", "ZhkAntlion" }, kit = SoldierKit, customize = Hatchling },
            new MonsterDef { id = "ZhkHornet", art = "ZhkHornet", basePrefab = "EnemyFlyingEye_Red", health = 5.5f, evolveCost = 2.5f,
                             evolveTo = new[] { "ZhkHive", "ZhkHunter" }, kit = HornetKit, customize = Hatchling },
            new MonsterDef { id = "ZhkSiphon", art = "ZhkSiphon", basePrefab = "EnemyFlyingEye_Rapidfire", health = 6f, evolveCost = 2.5f,
                             evolveTo = new[] { "ZhkGorger", "ZhkBotfly" }, kit = SiphonKit, customize = Hatchling },
            new MonsterDef { id = "ZhkNasute", art = "ZhkNasute", basePrefab = "EnemyRatman", health = 6.5f, speedMult = 0.9f, evolveCost = 2.5f,
                             evolveTo = new[] { "ZhkColossus", "ZhkMortar" }, kit = NasuteKit, customize = Hatchling },
            new MonsterDef { id = "ZhkScarab", art = "ZhkScarab", basePrefab = "EnemyOrc", health = 6.5f, speedMult = 0.9f, evolveCost = 2.5f,
                             evolveTo = new[] { "ZhkStag", "ZhkSunScarab" }, kit = ScarabKit, customize = Hatchling },
            new MonsterDef { id = "ZhkMother", art = "ZhkMother", basePrefab = "EnemyPriestess", health = 11f, speedMult = 0.85f, evolveCost = 4.5f,
                             kit = MotherKit, customize = Hatchling },
            new MonsterDef { id = "ZhkBloater", art = "ZhkBloater", basePrefab = "EnemyBeholder", health = 12f, speedMult = 0.8f, evolveCost = 4.5f,
                             kit = BloaterKit, customize = Hatchling },
            new MonsterDef { id = "ZhkMantis", art = "ZhkMantis", basePrefab = "EnemyCapraDemon", health = 10.5f, evolveCost = 4.5f,
                             kit = MantisKit, customize = Hatchling },
            new MonsterDef { id = "ZhkAntlion", art = "ZhkAntlion", basePrefab = "EnemyMinotaur", health = 11.5f, speedMult = 0.9f, evolveCost = 4.5f,
                             kit = AntlionKit, customize = Hatchling },
            new MonsterDef { id = "ZhkHive", art = "ZhkHive", basePrefab = "EnemyGhoul", health = 12f, speedMult = 0.75f, evolveCost = 4.5f,
                             kit = HiveKit, customize = Hatchling },
            new MonsterDef { id = "ZhkHunter", art = "ZhkHunter", basePrefab = "EnemyFlyingEye_Red", health = 10.5f, speedMult = 1.1f, evolveCost = 4.5f,
                             kit = HunterKit, customize = Hatchling },
            new MonsterDef { id = "ZhkGorger", art = "ZhkGorger", basePrefab = "EnemyEyelessBeast", health = 12f, speedMult = 0.85f, evolveCost = 4.5f,
                             kit = GorgerKit, customize = Hatchling },
            new MonsterDef { id = "ZhkBotfly", art = "ZhkBotfly", basePrefab = "EnemyFlyingEyeBomber", health = 10.5f, evolveCost = 4.5f,
                             kit = BotflyKit, customize = Hatchling },
            new MonsterDef { id = "ZhkColossus", art = "ZhkColossus", basePrefab = "EnemyTroll", health = 12f, speedMult = 0.9f, evolveCost = 4.5f,
                             kit = ColossusKit, customize = Hatchling },
            new MonsterDef { id = "ZhkMortar", art = "ZhkMortar", basePrefab = "EnemyDarkExecutioner_Boomerang", health = 11f, speedMult = 0.8f, evolveCost = 4.5f,
                             kit = MortarKit, customize = Hatchling },
            new MonsterDef { id = "ZhkStag", art = "ZhkStag", basePrefab = "EnemyDarkGuardian", health = 12f, speedMult = 0.9f, evolveCost = 4.5f,
                             kit = StagKit, customize = Hatchling },
            new MonsterDef { id = "ZhkSunScarab", art = "ZhkSunScarab", basePrefab = "EnemySkeletonPope", health = 11f, speedMult = 0.85f, evolveCost = 4.5f,
                             kit = SunScarabKit, customize = Hatchling },
        };

        /// <summary>Each monster's signature.</summary>
        static readonly Dictionary<string, Type> Signatures = new Dictionary<string, Type>
        {
            { "ZhkGrub", typeof(GrubGorge) }, { "ZhkDrone", typeof(DroneLastSting) }, { "ZhkBeetle", typeof(BeetleShove) },
            { "ZhkSpitter", typeof(SpitterSac) }, { "ZhkSoldier", typeof(SoldierGuard) }, { "ZhkSiphon", typeof(SiphonEngorge) },
            { "ZhkNasute", typeof(NasuteBodyguard) }, { "ZhkScarab", typeof(ScarabStock) }, { "ZhkMother", typeof(MotherJelly) },
            { "ZhkBloater", typeof(BloaterDeflate) }, { "ZhkMantis", typeof(MantisReflex) }, { "ZhkAntlion", typeof(AntlionPit) },
            { "ZhkHive", typeof(HiveComb) }, { "ZhkHunter", typeof(HunterCarry) }, { "ZhkGorger", typeof(GorgerBank) },
            { "ZhkColossus", typeof(ColossusPlate) }, { "ZhkMortar", typeof(MortarSpotters) }, { "ZhkStag", typeof(StagJaws) },
            { "ZhkSunScarab", typeof(SunScarabFossil) },
        };

        public static readonly GodDef God = new GodDef
        {
            name = "Zhekra",
            text = "Dead hatch a biting larva",
            flavour = "The hive feeds its young\non the fallen.",
            winText = "THE HIVE FALLS QUIET",
            portraitArt = "DeityZhekra",
            startingMonsters = new[] { "ZhkGrub", "ZhkDrone", "ZhkBeetle" },
        };

        // ------------------------------------------------------------------ shop items
        public static GameObject HeroAcidGlob, HeroAcidPool, HeroResinBurst;

        static List<DamageEffectData> Special(Powerup pu) { return R.Get<List<DamageEffectData>>(pu, "m_specialAttackDamageEffects"); }
        static System.Collections.IList Effects(Powerup pu) { return R.Get<System.Collections.IList>(pu, "m_effects"); }

        static void BuildItemFx()
        {
            // Acid Spit: a weaker copy of the Spitter's lob whose pool is a weaker copy too
            HeroAcidPool = FxKit.Weakened(ZhekraFx.AcidPool, "ModZhkHeroAcidPool", 0.6f);          // 0.15 per 0.6 s
            HeroAcidGlob = FxKit.Weakened(ZhekraFx.AcidGlob, "ModZhkHeroAcidGlob", 0.7f);          // 0.7 on contact
            if (HeroAcidGlob != null && HeroAcidPool != null)
            {
                FxFactory.SetEffect(HeroAcidGlob, destroyOnAnimEnd: false, destroyAfter: 0.85f, spawnOnDestroy: HeroAcidPool, freeRotate: false);
                Strike.ArtAt(HeroAcidGlob, "FxZhkAcidGlob", 14, 14);   // drawn at the hero's hand height
                FxFactory.SetContacts(HeroAcidGlob, destroyOnHit: true, spawnOnHit: HeroAcidPool);
                FxFactory.SetMotion(HeroAcidGlob, 190f, accel: 20f, speedMax: 8f);
            }
            // Hive Amber: a ring of resin that roots the monsters it catches
            HeroResinBurst = FxKit.TimedHit("ModZhkHeroResinBurst", "skydropExplode", "FxZhkResinBurst", "Play", 1, 3, 0.3f, 0.8f,
                                            FxFactory.GetStatus("StatusStuckToFloor"), 1f, canFlip: false);
            Strike.Ground(HeroResinBurst, "FxZhkResinBurst", 16, 8, 32f, 14f);   // the ring reaches r 15
        }

        public static readonly List<ItemDef> Items = new List<ItemDef>
        {
            new ItemDef { id = "SpellZhkAcidSpit", cloneFrom = "SpellCycloneSummon", cost = 40, group = "GroupSpellsPurchasable",
                name = "Acid Spit", description = "Spit acid that makes monsters more vulnerable",
                bubbleArt = "IconZhkAcidSpitBubble",
                customize = (go, pu) =>
                {
                    var sp = Special(pu);
                    // the item's own art (art/out_itemfx) on its hero-only templates: same damage, colliders and timing
                    ItemArt.Wear(HeroAcidGlob, "FxItemAcidSpit", "Fly", loop: true);
                    ItemArt.Wear(HeroAcidPool, "FxItemAcidPool", "Life");
                    if (sp.Count > 0 && HeroAcidGlob != null) sp[0].m_object = HeroAcidGlob;
                } },
            new ItemDef { id = "ArtifactZhkHiveAmber", cloneFrom = "PowerupAcidBlood", cost = 40, group = "GroupArtifactsPurchasable",
                name = "Hive Amber", description = "Resin bursts out when you are hit, rooting monsters",
                bubbleArt = "IconZhkHiveAmberBubble", hudArt = "IconZhkHiveAmberHud",
                customize = (go, pu) =>
                {
                    var e = Effects(pu);
                    ItemArt.Wear(HeroResinBurst, "FxItemHiveAmber", "Burst");                       // the item's own amber ring
                    var pop = ItemArt.Visual("ModItemHiveAmberPop", "FxItemHiveAmber", "Pop");      // and honeycomb pop at the hero
                    for (int i = 0; i < e.Count && i < 2; i++)
                    {
                        var d = e[i] as DamageEffectData;
                        if (d == null) continue;
                        d.m_object = i == 0 ? HeroResinBurst : (pop ?? ZhekraFx.ResinPop);
                        d.m_attach = false;
                    }
                } },
        };

        static void RegisterItems()
        {
            try { BuildItemFx(); } catch (Exception e) { Plugin.Log.LogError("Zhekra item FX failed: " + e); }
            // ItemPack.Register builds everything in ItemPack.Items. If it has already run, build ours here;
            // otherwise it will build them itself (building twice would list each item twice in the shop).
            bool itemPackDone = ItemPack.Built.ContainsKey("SpellWickwalk");
            if (itemPackDone)
                foreach (var def in Items)
                {
                    try { ItemRegistry.Register(def); }
                    catch (Exception e) { Plugin.Log.LogError("Item " + def.id + " failed: " + e); }
                }
            ItemPack.Items.AddRange(Items);   // so the self-test counts them
        }

        public static void Register()
        {
            ZhekraFx.Build();
            foreach (var m in Monsters)
            {
                var t = new MonsterTraits { plateFx = ZhekraFx.Plate, plateBreakFx = ZhekraFx.ResinPop };
                Type q;
                if (Signatures.TryGetValue(m.id, out q)) t.behaviours.Add(q);
                MonsterTraits.Register(m.PrefabName, t);
            }
            var hive = MonsterTraits.Of("ModZhkHive");
            if (hive != null) { hive.regenAt = HiveComb.InResin; hive.regenPerSecond = HiveComb.Mend; }
            MonsterTraits.Register(Larva.PrefabName, new MonsterTraits { lifetime = 8f, expireFx = ZhekraFx.Splash }.Add<ZhkLarvaLife>());

            var larva = MonsterFactory.Build(Larva);
            var grubling = MonsterFactory.Build(Grubling);
            ZhekraFx.BuildLarva(larva != null ? larva.gameObject : null, grubling != null ? grubling.gameObject : null);
            foreach (var m in Monsters) MonsterFactory.Build(m);
            MonsterFactory.LinkEvolutions(Monsters);
            s_deity = DeityFactory.Register(God);
            RegisterItems();
            MonsterEvents.AttackSpawned += OnAttackSpawned;
            // the gold idol carved in the Brood Queen's likeness
            var prev = SlotGods.PortraitFor;
            SlotGods.PortraitFor = (tier, perk) =>
                tier == SlotTier.Gold && perk != null && perk == s_deity ? Idol() : (prev != null ? prev(tier, perk) : null);
            Strike.KeepAllScales();
        }

        static Deity s_deity;
        static exSpriteAnimClip s_idol;

        static exSpriteAnimClip Idol()
        {
            if (s_idol == null) s_idol = SlotArt.Clip("DeityGoldIdolZhekra", "Idle");
            return s_idol;
        }

        // the hero's shots, so the Acid Mantis can cut them out of the air
        static void OnAttackSpawned(Player owner, GameObject fx, GameObject template)
        {
            if (owner == null || fx == null || owner.gameObject != ModUtil.Hero()) return;
            if (fx.GetComponent<ParticleMotion>() != null && fx.GetComponent<ZhkHeroShot>() == null) fx.AddComponent<ZhkHeroShot>();
        }
    }

    /// <summary>Acid Mantis: its hits deal 40% more to a Corroded target.</summary>
    [HarmonyPatch(typeof(Health), "Damage", new[] { typeof(DamageInfo), typeof(bool) })]
    static class Patch_ZhekraMantisExecute
    {
        static void Prefix(Health __instance, DamageInfo damage)
        {
            try
            {
                if (damage == null || damage.m_isDamageFromStatus || damage.m_amount <= 0f || damage.m_source == null) return;
                var attacker = damage.m_source.m_sourceOwnerPlayer;
                if (attacker == null || attacker == __instance.gameObject || ModUtil.PrefabName(attacker) != "ModZhkMantis") return;
                var victim = __instance.GetComponent<Player>();
                var sm = victim != null ? victim.GetStatusManager() : null;
                if (sm != null && sm.GetHasStatusWithClass("ModZhkAcid")) damage.m_amount *= 1.4f;
            }
            catch { }
        }
    }

    /// <summary>Give every Zhekra body (the monsters, the larva, the grubling) the brood's perk.</summary>
    [HarmonyPatch(typeof(Player), "Awake")]
    static class Patch_ZhekraAwake
    {
        static void Postfix(Player __instance)
        {
            if (__instance == null) return;
            if (__instance.gameObject.name.StartsWith("ModZhk") && __instance.GetComponent<ZhkBrain>() == null)
                __instance.gameObject.AddComponent<ZhkBrain>();
        }
    }
}
