using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Art;
    using CrawlFurther.Gods;
    using CrawlFurther.Items;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;
    using CrawlFurther.Content.Items;

    /// <summary>
    /// Kaurn, the Storm Forge. Kaurn monsters build a circuit across the room (the perk's arcs, <see cref="KaurnConduction"/>)
    /// and make it dangerous: they heat it, pulse it, ride it, aim through it. Every basic attack stores a spark that the
    /// special fires (<see cref="KaurnUnit"/>), and every monster has a mechanic of its own (a <see cref="KaurnBehaviour"/>)
    /// with a tell the hero can read. Offsets below are the art's sync points (art/out_kaurn/TIMING.md), x forward, y up.
    /// </summary>
    public static class KaurnPack
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
        // Rivet Imp: a hammer bonk; Rivet Bat sends three hot rivets that stick in the floor as arc posts. Spark Plug: a bonk
        // that lands stores 2 sparks (KrnBonkFx).
        static void ImpKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int first = Strike.Mark(p);
            int bonk = Kit.AddEffect(p, KaurnFx.ImpBonk, attach: true, destroyOnAnimEnd: true, offsetX: 12f, offsetY: 4f);
            int flash = Kit.AddEffect(p, KaurnFx.HitFx, offsetX: 12f, offsetY: 2f);
            var r = new List<int>();
            foreach (var a in new[] { -18f, 0.01f, 18f }) r.Add(Kit.AddEffect(p, KaurnFx.Rivet, offsetX: 10f, offsetY: 12f, angle: a));
            var bk = Kit.Melee(sh, "Bonk", "ModKrnImpBonk", v, 3, bonk, 30f).Ev(3, "AnimAttack", flash).Ev(3, "KrnCharge").Build();
            var rv = Kit.Shot(sh, "Rivets", "ModKrnImpRivets", 3, v, 0.03f, r.ToArray()).Ev(3, "KrnDischarge").Build();
            atk.Clear();
            // hammer box x 6..18 (+ a 30 px/s lunge); rivets fly 160 px/s x 0.42 s from x 10 (~77 px)
            atk.Add(Kit.Attack(a0, bk, 1.3f, rangeInner: 6f, rangeOuter: 22f));
            Kit.SetSpecial(p, Kit.Attack(sp, rv, 0f, rangeInner: 24f, rangeOuter: 72f, rangeRetreat: 0f), 5.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, first, 10f);
        }

        // Spark Beetle: an antenna zap; Ball Lightning rolls it through the hero. Overcharge: with 3 sparks the roll is the big
        // ball (RushBig) that spends them and surely stuns (BeetleOvercharge).
        static void BeetleKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int first = Strike.Mark(p);
            int zap = Kit.AddEffect(p, KaurnFx.Zap, offsetX: 12f, offsetY: 10f);
            int rush = Kit.AddEffect(p, KaurnFx.RushHit, attach: true, destroyOnAnimEnd: true, offsetY: 5f);
            int big = Kit.AddEffect(p, KaurnFx.RushBig, attach: true, destroyOnAnimEnd: true, offsetY: 7f);
            var zp = Kit.Shot(sh, "Zap", "ModKrnBeetleZap", 3, v, 0f, zap).Ev(3, "KrnCharge").Build();
            Func<string, int, string, exSpriteAnimClip> roll = (anim, hit, spend) => new ClipBuilder(sh, anim, "ModKrnBeetle" + anim).Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(1, "AnimInputMultiplyStop").Ev(1, "AnimInputOff")
                .EvF(1, "AnimMove", 170f).Ev(1, "AnimAttack", hit).Ev(1, spend).EvO(1, "AnimSound", v)
                .Ev(6, "AnimMoveStop").Ev(-1, "AnimRun").Build();
            atk.Clear();
            // zap: 220 px/s x 0.3 s from x 12 (~78 px); the roll: 170 px/s for 0.3 s (~51 px) + the ball
            atk.Add(Kit.Attack(a0, zp, 1.4f, rangeInner: 28f, rangeOuter: 70f, rangeRetreat: 22f));
            Kit.SetSpecial(p, Kit.Attack(sp, roll("Rush", rush, "KrnDischarge"), 0f, rangeInner: 12f, rangeOuter: 58f, rangeRetreat: 0f), 5.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, first, 9f);
            BeetleOvercharge.RushBig = roll("RushBig", big, "KrnSpendSparks");
            BeetleOvercharge.ChargedIdle = Looped(sh, "IdleCharged", "ModKrnBeetleIdleCharged");
            BeetleOvercharge.ChargedRun = Looped(sh, "RunCharged", "ModKrnBeetleRunCharged");
        }

        // Coil Wisp: lightning motes; Shock Ring under itself. Relay: its arcs reach 110 px (WispRelay).
        static void WispKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int first = Strike.Mark(p);
            int mote = Kit.AddEffect(p, KaurnFx.Mote, offsetX: 7f, offsetY: 9f);
            int ring = Kit.AddEffect(p, KaurnFx.Ring, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            var sk = Kit.Shot(sh, "Spark", "ModKrnWispSpark", 3, v, 0f, mote).Ev(3, "KrnCharge").Build();
            var pl = Special(sh, "Pulse", "ModKrnWispPulse").Ev(3, "AnimAttack", ring).Ev(3, "KrnDischarge").EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            // mote: 160 px/s x 0.9 s (~150 px); the ring covers 42 x 16 round it
            atk.Add(Kit.Attack(a0, sk, 1.5f, rangeInner: 45f, rangeOuter: 110f, rangeRetreat: 35f));
            Kit.SetSpecial(p, Kit.Attack(sp, pl, 0f, rangeInner: 0f, rangeOuter: 20f, rangeRetreat: 0f), 5.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, first, 9f);
            WispRelay.LinkedIdle = Looped(sh, "IdleLinked", "ModKrnWispIdleLinked");
            WispRelay.LinkedRun = Looped(sh, "RunLinked", "ModKrnWispRunLinked");
        }

        // ---------------------------------------------------------------------------------------------- tier 2
        // Anvil Smith: a hammer smash with a floor surge; Plant Rod drives in a red-hot rod and gains an iron plate.
        static void SmithKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int first = Strike.Mark(p);
            int smash = Kit.AddEffect(p, KaurnFx.SmithSmash, attach: true, destroyOnAnimEnd: true, offsetX: 18f, offsetY: 4f);
            int surge = Kit.AddEffect(p, KaurnFx.Surge, offsetX: 20f, offsetY: 3f);
            int flash = Kit.AddEffect(p, KaurnFx.HitFx, offsetX: 18f, offsetY: 2f);
            int rod = Kit.AddEffect(p, KaurnFx.RodHot, offsetX: 11f, offsetY: 0f, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            int spark = Kit.AddEffect(p, KaurnFx.HitFx, offsetX: 11f, offsetY: 12f, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            // Combo: two hammer smashes, each sending a surge along the floor, then the Double: two smashes in a row, the second red-hot (sets him alight)
            var hm = Kit.Melee(sh, "Hammer", "ModKrnSmithHammer", v, 3, smash, 25f)
                .Ev(3, "AnimAttack", surge).Ev(3, "AnimAttack", flash).Ev(3, "KrnCharge").Build();
            var hm2 = Kit.Melee(sh, "Hammer", "ModKrnSmithHammer2", null, 3, smash, 35f).Speed(1.15f)
                .Ev(3, "AnimAttack", surge).Ev(3, "AnimAttack", flash).Ev(3, "KrnCharge").Build();
            int hot = Kit.AddEffect(p, FxKit.Finisher(KaurnFx.SmithSmash, "ModKrnSmashHot", damageMult: 1.1f, status: FxFactory.GetStatus("StatusOnFire")),
                                    attach: true, destroyOnAnimEnd: true, offsetX: 18f, offsetY: 4f);
            var hm3 = Kit.Melee(sh, "Hammer", "ModKrnSmithDouble", v, 3, smash, 40f, 10, hot, 50f).Repeat(2).Speed(1.2f)
                .Ev(3, "AnimAttack", surge).Ev(3, "AnimAttack", flash).Ev(10, "AnimAttack", surge).Ev(10, "AnimAttack", flash).Ev(10, "KrnCharge").Build();
            var pt = Special(sh, "Plant", "ModKrnSmithPlant").Ev(3, "AnimAttack", rod).Ev(3, "AnimAttack", spark).EvO(3, "AnimSound", v)
                .Ev(4, "ModGainPlates", 1).Ev(4, "KrnDischarge").Ev(-1, "AnimRun").Build();
            atk.Clear();
            // hammer box x 11..25 (+ 25 px/s lunge); the surge runs on 150 px/s x 0.45 s from x 20 (~88 px)
            atk.Add(Kit.Attack(a0, hm, 0.4f, rangeInner: 8f, rangeOuter: 30f));
            atk.Add(Kit.Attack(a0, hm2, 0.4f, rangeInner: 8f, rangeOuter: 32f));
            atk.Add(Kit.Attack(a0, hm3, 1.9f, rangeInner: 8f, rangeOuter: 40f));
            Kit.SetSpecial(p, Kit.Attack(sp, pt, 0f, rangeInner: 0f, rangeOuter: 80f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, first, 10f);
        }

        // Wire Gremlin: rooting hot staples; Wire Up flicks a hooked wire that wires the hero for 3 s (Conductor).
        static void GremlinKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p) ?? a0; var v = Kit.Voice(p);
            int first = Strike.Mark(p);
            int st = Kit.AddEffect(p, KaurnFx.Staple, offsetX: 12f, offsetY: 14f);
            int hk = Kit.AddEffect(p, KaurnFx.WireHook, offsetX: 10f, offsetY: 15f);
            int stL = Kit.AddEffect(p, KaurnFx.Staple, offsetX: 12f, offsetY: 14f, angle: -14f);
            int stR = Kit.AddEffect(p, KaurnFx.Staple, offsetX: 12f, offsetY: 14f, angle: 14f);
            // Combo: two staples, then the Live Wire: a staple whose wire lays a line of slowing static
            var s = Kit.Shot(sh, "Staple", "ModKrnGremlinStaple", 3, v, 0f, st).Ev(3, "KrnCharge").Build();
            var s2 = Kit.Shot(sh, "Staple", "ModKrnGremlinStaple2", 3, null, 0f, st).Speed(1.15f).Ev(3, "KrnCharge").Build();
            // Live Wire: one staple trailing its wire, the wire laying a line of slowing static behind it
            int live = Kit.AddEffect(p, FxKit.Finisher(KaurnFx.Staple, "ModKrnLiveWire", scale: 1.25f, trail: KaurnFx.Field, trailDist: 26f),
                                     offsetX: 12f, offsetY: 14f);
            var s3 = Kit.Shot(sh, "Staple", "ModKrnGremlinLiveWire", 3, v, 0f, live).Speed(0.85f).Ev(3, "KrnCharge").Build();
            var h = Kit.Shot(sh, "WireUp", "ModKrnGremlinWireUp", 3, v, 0f, hk).Ev(3, "KrnDischarge").Build();
            atk.Clear();
            // staple 200 px/s x 0.45 s (~90 px); hook 190 px/s x 0.5 s (~95 px)
            atk.Add(Kit.Attack(a0, s, 0.4f, rangeInner: 30f, rangeOuter: 90f, rangeRetreat: 26f));
            atk.Add(Kit.Attack(a0, s2, 0.4f, rangeInner: 30f, rangeOuter: 90f, rangeRetreat: 26f));
            atk.Add(Kit.Attack(a0, s3, 1.8f, rangeInner: 30f, rangeOuter: 85f, rangeRetreat: 26f));
            Kit.EnableSpecial(p, Kit.Attack(sp, h, 0f, rangeInner: 25f, rangeOuter: 92f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, first, 14f);
        }

        // Lodestone Hound: a leaping bite; Magnet Howl pulls (red collar) or pushes (blue) the hero, and the collar flips
        // (HoundPolarity). Basic 0 wears the red collar, basic 1 the blue.
        static void HoundKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int first = Strike.Mark(p);
            int bite = Kit.AddEffect(p, KaurnFx.HoundBite, attach: true, destroyOnAnimEnd: true, offsetX: 18f, offsetY: 13f);
            int pull = Kit.AddEffect(p, KaurnFx.MagPull, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            int push = Kit.AddEffect(p, KaurnFx.MagPush, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            Func<ClipBuilder, exSpriteAnimClip> leap = cb => cb.Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(1, "AnimInputMultiplyStop").Ev(1, "AnimInputOff")
                .EvF(2, "AnimMove", 190f).Ev(3, "AnimAttack", bite).Ev(3, "KrnCharge").EvO(3, "AnimSound", v)
                .Ev(4, "AnimMoveStop").Ev(-1, "AnimRun").Build();
            Func<string, int, exSpriteAnimClip> howl = (anim, field) =>
            {
                var c = Special(sh, anim, "ModKrnHound" + anim).Ev(2, "AnimAttack", field).Ev(2, "KrnDischarge").EvO(2, "AnimSound", v);
                for (int f = 2; f <= 5; f++) c.EvF(f, "KrnMagField", 45f);
                return c.Ev(7, "KrnFlipCollar").Ev(-1, "AnimRun").Build();
            };
            atk.Clear();
            // the leap covers ~27 px (190 px/s for 0.14 s) and the jaws reach 24 px ahead
            atk.Add(Kit.Attack(a0, leap(new ClipBuilder(sh, "Leap", "ModKrnHoundLeap")), 1.3f, rangeInner: 10f, rangeOuter: 46f));
            atk.Add(Kit.Attack(a0, leap(new ClipBuilder(sh, "LeapBlue", "ModKrnHoundLeapBlue")), 1.3f, rangeInner: 10f, rangeOuter: 46f));
            Kit.SetSpecial(p, Kit.Attack(sp, howl("Howl", pull), 0f, rangeInner: 30f, rangeOuter: 110f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, first, 11f);
            HoundPolarity.BlueIdle = Looped(sh, "IdleBlue", "ModKrnHoundIdleBlue");
            HoundPolarity.BlueRun = Looped(sh, "RunBlue", "ModKrnHoundRunBlue");
            HoundPolarity.BlueHowl = howl("HowlBlue", push);
        }

        // Stormcaller: ball lightning that speeds up; Static Build calls a bolt down on the hero, which a rod takes for him.
        static void CallerKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int first = Strike.Mark(p);
            int ball = Kit.AddEffect(p, KaurnFx.Ball, offsetX: 11f, offsetY: 14f);
            int bL = Kit.AddEffect(p, KaurnFx.Ball, offsetX: 11f, offsetY: 14f, angle: -14f);
            int bR = Kit.AddEffect(p, KaurnFx.Ball, offsetX: 11f, offsetY: 14f, angle: 14f);
            // Combo: two balls of lightning, then the Thunderhead: a swollen ball that ends in a lightning strike
            var ob = Kit.Shot(sh, "Orb", "ModKrnCallerOrb", 3, v, 0f, ball).Ev(3, "KrnCharge").Build();
            var ob2 = Kit.Shot(sh, "Orb", "ModKrnCallerOrb2", 3, null, 0f, ball).Speed(1.15f).Ev(3, "KrnCharge").Build();
            // Thunderhead: one swollen ball, slower, that ends in a lightning strike where it stops
            int head = Kit.AddEffect(p, FxKit.Finisher(KaurnFx.Ball, "ModKrnThunderhead", scale: 1.5f, damageMult: 1.2f, speedMult: 0.8f,
                                                       leaves: KaurnFx.StaticBolt), offsetX: 11f, offsetY: 14f);
            var ob3 = Kit.Shot(sh, "Orb", "ModKrnCallerThunderhead", 3, v, 0f, head).Speed(0.85f).Ev(3, "KrnCharge").Build();
            var bd = Special(sh, "Build", "ModKrnCallerBuild").Ev(2, "KrnStaticBuild").Ev(2, "KrnDischarge").EvO(2, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            // the ball accelerates 60 -> 150 px/s over its 1.7 s (~175 px); the bolt finds the hero wherever he is
            atk.Add(Kit.Attack(a0, ob, 0.45f, rangeInner: 50f, rangeOuter: 130f, rangeRetreat: 40f));
            atk.Add(Kit.Attack(a0, ob2, 0.45f, rangeInner: 50f, rangeOuter: 130f, rangeRetreat: 40f));
            atk.Add(Kit.Attack(a0, ob3, 2.0f, rangeInner: 45f, rangeOuter: 120f, rangeRetreat: 40f));
            Kit.SetSpecial(p, Kit.Attack(sp, bd, 0f, rangeInner: 30f, rangeOuter: 150f, rangeRetreat: 30f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, first, 13f);
        }

        // Leyden Golem: twin jolts; Shock Ring fires its stored sparks (up to 6, LeydenJar) and fills its allies.
        static void LeydenKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int first = Strike.Mark(p);
            int j0 = Kit.AddEffect(p, KaurnFx.Jolt, offsetX: 13f, offsetY: 15f, angle: -8f);
            int j1 = Kit.AddEffect(p, KaurnFx.Jolt, offsetX: 13f, offsetY: 15f, angle: 8f);
            int ring = Kit.AddEffect(p, KaurnFx.Ring, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            // Combo: two pairs of jolts, then the Discharge: jolts and a shock ring bursts round the golem
            var jo = Kit.Shot(sh, "Jolts", "ModKrnLeydenJolts", 3, v, 0.04f, j0, j1).Ev(3, "KrnCharge").Build();
            var jo2 = Kit.Shot(sh, "Jolts", "ModKrnLeydenJolts2", 3, null, 0.04f, j0, j1).Speed(1.15f).Ev(3, "KrnCharge").Build();
            var jo3 = Kit.Shot(sh, "Jolts", "ModKrnLeydenDischarge", 3, v, 0.04f, j0, j1).Speed(0.85f).Ev(4, "AnimAttack", ring).Ev(3, "KrnCharge").Build();
            var rg = Special(sh, "Ring", "ModKrnLeydenRing").Ev(4, "AnimAttack", ring).Ev(4, "KrnDischarge").Ev(4, "KrnFillAllies")
                .EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            // jolts fly 230 px/s for 0.45 s from 13 px ahead (~116 px)
            atk.Add(Kit.Attack(a0, jo, 0.45f, rangeInner: 45f, rangeOuter: 110f, rangeRetreat: 35f));
            atk.Add(Kit.Attack(a0, jo2, 0.45f, rangeInner: 45f, rangeOuter: 110f, rangeRetreat: 35f));
            atk.Add(Kit.Attack(a0, jo3, 2.0f, rangeInner: 0f, rangeOuter: 80f, rangeRetreat: 20f));
            Kit.SetSpecial(p, Kit.Attack(sp, rg, 0f, rangeInner: 0f, rangeOuter: 70f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, first, 14f);
            for (int k = 1; k <= LeydenJar.Jar; k++)
            {
                LeydenJar.JarIdle[k] = Looped(sh, "IdleJ" + k, "ModKrnLeydenIdleJ" + k);
                LeydenJar.JarRun[k] = Looped(sh, "RunJ" + k, "ModKrnLeydenRunJ" + k);
            }
        }

        // Arc Lantern: a seeking wisp (one that misses hangs as an arc post, KrnSeekerFx); Static Field under the hero.
        static void LanternKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p) ?? a0; var v = Kit.Voice(p);
            int first = Strike.Mark(p);
            int sk = Kit.AddEffect(p, KaurnFx.Seeker, offsetX: 9f, offsetY: 12f);
            int fd = Kit.AddEffect(p, KaurnFx.Field, spawnPoint: DamageEffectData.eSpawnPoint.ClosestEnemy);
            int skL = Kit.AddEffect(p, KaurnFx.Seeker, offsetX: 9f, offsetY: 12f, angle: -40f);
            int skR = Kit.AddEffect(p, KaurnFx.Seeker, offsetX: 9f, offsetY: 12f, angle: 40f);
            // Combo: two seeking wisps, then three that fan out wide and turn in after the hero
            var s = Kit.Shot(sh, "Seek", "ModKrnLanternSeek", 3, v, 0f, sk).Ev(3, "KrnCharge").Build();
            var s2 = Kit.Shot(sh, "Seek", "ModKrnLanternSeek2", 3, null, 0f, sk).Speed(1.15f).Ev(3, "KrnCharge").Build();
            var s3 = Kit.Shot(sh, "Seek", "ModKrnLanternFlock", 3, v, 0.06f, skL, sk, skR).Speed(0.85f).Ev(3, "KrnCharge").Build();
            var f = Special(sh, "Field", "ModKrnLanternField").Ev(4, "AnimAttack", fd).Ev(4, "KrnDischarge").EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            // the wisp flies 110 px/s, homing for 1.1 s, and hangs where it stops (~170 px)
            atk.Add(Kit.Attack(a0, s, 0.45f, rangeInner: 45f, rangeOuter: 140f, rangeRetreat: 40f));
            atk.Add(Kit.Attack(a0, s2, 0.45f, rangeInner: 45f, rangeOuter: 140f, rangeRetreat: 40f));
            atk.Add(Kit.Attack(a0, s3, 2.1f, rangeInner: 45f, rangeOuter: 130f, rangeRetreat: 40f));
            Kit.EnableSpecial(p, Kit.Attack(sp, f, 0f, rangeInner: 30f, rangeOuter: 140f, rangeRetreat: 30f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, first, 12f);
        }

        // ---------------------------------------------------------------------------------------------- tier 3
        // Forge Colossus: a two-fisted slam; Rod Fence bursts 4 rods up round it. Both heat its furnace (ColossusOverheat).
        static void ColossusKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int first = Strike.Mark(p);
            int quake = Kit.AddEffect(p, KaurnFx.Quake, offsetX: 17f, offsetY: 0f, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            int quake0 = Kit.AddEffect(p, KaurnFx.Quake, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            var rods = new List<int>();
            foreach (var o in new[] { new Vector2(30f, 14f), new Vector2(30f, -14f), new Vector2(-30f, 14f), new Vector2(-30f, -14f) })
                rods.Add(Kit.AddEffect(p, KaurnFx.RodFence, offsetX: o.x, offsetY: o.y, spawnPoint: DamageEffectData.eSpawnPoint.Position));
            var sl = new ClipBuilder(sh, "Slam", "ModKrnColossusSlam").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(3, "AnimInputMultiplyStop").Ev(3, "AnimInputOff")
                .Ev(4, "AnimAttack", quake).Ev(4, "KrnCharge").Ev(4, "KrnHeat").EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            int quake2 = Kit.AddEffect(p, KaurnFx.Quake, offsetX: 42f, offsetY: 0f, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            // Combo: two slams, then the Aftershock: the quake rolls on and bursts up again further ahead
            var sl2 = new ClipBuilder(sh, "Slam", "ModKrnColossusSlam2").Once().Speed(1.1f)
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(3, "AnimInputMultiplyStop").Ev(3, "AnimInputOff")
                .Ev(4, "AnimAttack", quake).Ev(4, "KrnCharge").Ev(4, "KrnHeat").Ev(-1, "AnimRun").Build();
            var sl3 = new ClipBuilder(sh, "Slam", "ModKrnColossusAftershock").Once().Speed(0.85f)
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(3, "AnimInputMultiplyStop").Ev(3, "AnimInputOff")
                .Ev(4, "AnimAttack", quake).Ev(4, "AnimAttack", quake2, 0.18f).Ev(4, "KrnCharge").Ev(4, "KrnHeat").EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            var fe = Special(sh, "Fence", "ModKrnColossusFence").Ev(5, "AnimAttack", quake0);
            for (int i = 0; i < rods.Count; i++) fe.Ev(5, "AnimAttack", rods[i], 0.02f * (i + 1));
            fe.Ev(5, "KrnDischarge").Ev(5, "KrnHeat").EvO(5, "AnimSound", v).Ev(-1, "AnimRun");
            atk.Clear();
            // slam quake: 48 x 18 centred 17 px ahead; the fence rods stand 33 px out on the diagonals
            atk.Add(Kit.Attack(a0, sl, 0.5f, rangeInner: 0f, rangeOuter: 38f));
            atk.Add(Kit.Attack(a0, sl2, 0.5f, rangeInner: 0f, rangeOuter: 40f));
            atk.Add(Kit.Attack(a0, sl3, 2.3f, rangeInner: 0f, rangeOuter: 66f));
            Kit.SetSpecial(p, Kit.Attack(sp, fe.Build(), 0f, rangeInner: 0f, rangeOuter: 40f, rangeRetreat: 0f), 7.5f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.65f);
            Strike.Feet(p, first, 18f);
            ColossusOverheat.HotIdle = Looped(sh, "IdleH1", "ModKrnColossusIdleH1");
            ColossusOverheat.HotRun = Looped(sh, "RunH1", "ModKrnColossusRunH1");
            ColossusOverheat.HotterIdle = Looped(sh, "IdleH2", "ModKrnColossusIdleH2");
            ColossusOverheat.HotterRun = Looped(sh, "RunH2", "ModKrnColossusRunH2");
            ColossusOverheat.ColdIdle = Looped(sh, "IdleCold", "ModKrnColossusIdleCold");
            ColossusOverheat.ColdRun = Looped(sh, "RunCold", "ModKrnColossusRunCold");
            ColossusOverheat.VentClip = Once(sh, "Vent", "ModKrnColossusVent");
        }

        // Forgemaster: a sledge swing (harder per rod carried); Rod Volley throws his rods round the hero (ForgemasterCollector).
        static void MasterKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p) ?? a0; var v = Kit.Voice(p);
            int first = Strike.Mark(p);
            int smash = Kit.AddEffect(p, KaurnFx.MasterSmash, attach: true, destroyOnAnimEnd: true, offsetX: 22f, offsetY: 4f);
            int flash = Kit.AddEffect(p, KaurnFx.HitFx, offsetX: 23f, offsetY: 2f);
            // Combo: two sledge swings, then the Overhand: two swings running, the second stepping in and cracking the floor into a quake
            var sw = Kit.Melee(sh, "Swing", "ModKrnMasterSwing", v, 3, smash, 30f).Ev(3, "AnimAttack", flash).Ev(3, "KrnCharge").Build();
            var sw2 = Kit.Melee(sh, "Swing", "ModKrnMasterSwing2", null, 3, smash, 40f).Speed(1.1f).Ev(3, "AnimAttack", flash).Ev(3, "KrnCharge").Build();
            int crack = Kit.AddEffect(p, KaurnFx.Quake, offsetX: 30f, offsetY: 0.01f);
            var sw3 = Kit.Melee(sh, "Swing", "ModKrnMasterOverhand", v, 3, smash, 40f, 10, smash, 70f).Repeat(2).Speed(1.15f)
                .Ev(3, "AnimAttack", flash).Ev(10, "AnimAttack", flash).Ev(10, "AnimAttack", crack).Ev(10, "KrnCharge").Build();
            var vo = Special(sh, "Volley", "ModKrnMasterVolley").Ev(4, "KrnVolley").Ev(4, "KrnDischarge").EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            // sledge box x 14..30 plus a 30 px/s step; the rods land round the hero wherever he is (max 130 px)
            atk.Add(Kit.Attack(a0, sw, 0.5f, rangeInner: 8f, rangeOuter: 32f));
            atk.Add(Kit.Attack(a0, sw2, 0.5f, rangeInner: 8f, rangeOuter: 34f));
            atk.Add(Kit.Attack(a0, sw3, 2.2f, rangeInner: 8f, rangeOuter: 44f));
            Kit.EnableSpecial(p, Kit.Attack(sp, vo, 0f, rangeInner: 20f, rangeOuter: 120f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, first, 20f);
            // the sheet's own Idle and Run carry the rods he starts with
            for (int n = 0; n <= ForgemasterCollector.MaxRods; n++)
            {
                bool own = n == ForgemasterCollector.StartRods;
                ForgemasterCollector.RodIdle[n] = own ? null : Looped(sh, "IdleR" + n, "ModKrnMasterIdleR" + n);
                ForgemasterCollector.RodRun[n] = own ? null : Looped(sh, "RunR" + n, "ModKrnMasterRunR" + n);
            }
        }

        // Wire Wyvern: a lightning breath beam; Ride the Arc races along the arcs and bursts out by the hero (WyvernRide).
        static void WyvernKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p) ?? a0; var v = Kit.Voice(p);
            int first = Strike.Mark(p);
            int br = Kit.AddEffect(p, KaurnFx.Breath, offsetX: 20f, offsetY: 23f);
            int bL = Kit.AddEffect(p, KaurnFx.Breath, offsetX: 20f, offsetY: 23f, angle: -16f);
            int bR = Kit.AddEffect(p, KaurnFx.Breath, offsetX: 20f, offsetY: 23f, angle: 16f);
            // Combo: two beams, then the Sweep: the beam swings across from one side to the other
            var b = Kit.Shot(sh, "Breath", "ModKrnWyvernBreath", 3, v, 0f, br).Ev(3, "KrnCharge").Build();
            var b2 = Kit.Shot(sh, "Breath", "ModKrnWyvernBreath2", 3, null, 0f, br).Speed(1.15f).Ev(3, "KrnCharge").Build();
            var b3 = Kit.Shot(sh, "Breath", "ModKrnWyvernSweep", 3, v, 0.1f, bL, br, bR).Speed(0.85f).Ev(3, "KrnCharge").Build();
            var r = Special(sh, "Dive", "ModKrnWyvernDive").Ev(0, "AnimStartInvincibility").Ev(0, "KrnRidePlan").Ev(0, "KrnDischarge")
                .EvO(0, "AnimSound", v).Ev(5, "KrnRideGo").Ev(5, "AnimStopInvincibility").HandOff().Build();
            atk.Clear();
            // the beam reaches 2..60 px past the mouth (20 px ahead): x 22..80
            atk.Add(Kit.Attack(a0, b, 0.5f, rangeInner: 20f, rangeOuter: 72f, rangeRetreat: 18f));
            atk.Add(Kit.Attack(a0, b2, 0.5f, rangeInner: 20f, rangeOuter: 72f, rangeRetreat: 18f));
            atk.Add(Kit.Attack(a0, b3, 2.2f, rangeInner: 20f, rangeOuter: 70f, rangeRetreat: 18f));
            // it rides to wherever the arcs reach the hero: any range works, it wants the hero away from it
            Kit.EnableSpecial(p, Kit.Attack(sp, r, 0f, rangeInner: 40f, rangeOuter: 170f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, first, 20f);
            WyvernRide.BurstClip = Once(sh, "Burst", "ModKrnWyvernBurst");
        }

        // Fuse Sapper: a lobbed canister; Lay Charges lobs three charges round the hero (Live Charges, KrnChargeFx).
        static void SapperKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p) ?? a0; var v = Kit.Voice(p);
            int first = Strike.Mark(p);
            int can = Kit.AddEffect(p, KaurnFx.Canister, offsetX: 12f, offsetY: 22f, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            int cL = Kit.AddEffect(p, KaurnFx.Canister, offsetX: 12f, offsetY: 22f, angle: -16f, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            int cR = Kit.AddEffect(p, KaurnFx.Canister, offsetX: 12f, offsetY: 22f, angle: 16f, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            // Combo: two canisters, then the Pressure Bomb: a fat canister that bursts and vents scalding steam
            var l = Kit.Shot(sh, "Lob", "ModKrnSapperLob", 3, v, 0f, can).Ev(3, "KrnCharge").Build();
            var l2 = Kit.Shot(sh, "Lob", "ModKrnSapperLob2", 3, null, 0f, can).Speed(1.1f).Ev(3, "KrnCharge").Build();
            // Pressure Bomb: one fat canister that bursts and then vents scalding steam
            var bomb = FxKit.Finisher(KaurnFx.Canister, "ModKrnPressureBomb", scale: 1.35f);
            FxFactory.OnSpawn[bomb] = i => { var lb = i.GetComponent<KrnLobFx>() ?? i.AddComponent<KrnLobFx>(); lb.Reset(); lb.land = KaurnFx.CanBurst; lb.land2 = KaurnFx.Steam; lb.time = 0.7f; };
            int pb = Kit.AddEffect(p, bomb, offsetX: 12f, offsetY: 22f, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            var l3 = Kit.Shot(sh, "Lob", "ModKrnSapperPressure", 3, v, 0f, pb).Speed(0.85f).Ev(3, "KrnCharge").Build();
            var m = Special(sh, "Lay", "ModKrnSapperLay").Ev(4, "KrnLayCharges").Ev(4, "KrnDischarge").EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            // the canister lands where the hero stood (max 130 px) after 0.6 s
            atk.Add(Kit.Attack(a0, l, 0.5f, rangeInner: 40f, rangeOuter: 125f, rangeRetreat: 36f));
            atk.Add(Kit.Attack(a0, l2, 0.5f, rangeInner: 40f, rangeOuter: 125f, rangeRetreat: 36f));
            atk.Add(Kit.Attack(a0, l3, 2.2f, rangeInner: 40f, rangeOuter: 120f, rangeRetreat: 36f));
            // lay them from out of reach, then walk in to set them off
            Kit.EnableSpecial(p, Kit.Attack(sp, m, 0f, rangeInner: 60f, rangeOuter: 125f, rangeRetreat: 50f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.65f);
            Strike.Feet(p, first, 16f);
        }

        // Thunder Bull: a horn hook that throws the hero; Stampede paws three times and charges (BullMomentum).
        static void BullKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int first = Strike.Mark(p);
            int gore = Kit.AddEffect(p, KaurnFx.BullGore, attach: true, destroyOnAnimEnd: true, offsetX: 20f, offsetY: 16f);
            int flash = Kit.AddEffect(p, KaurnFx.HitFx, offsetX: 22f, offsetY: 22f);
            int stud = Kit.AddEffect(p, KaurnFx.Stud, offsetX: 16f, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            // Combo: two horn hooks, then the Toss: a lunging hook and a second one that throws him back
            var gr = Kit.Melee(sh, "Hook", "ModKrnBullHook", v, 2, gore, 35f).Ev(2, "AnimAttack", flash).Ev(2, "KrnCharge").Build();
            var gr2 = Kit.Melee(sh, "Hook", "ModKrnBullHook2", null, 2, gore, 45f).Speed(1.1f).Ev(2, "AnimAttack", flash).Ev(2, "KrnCharge").Build();
            var gr3 = Kit.Melee(sh, "Hook", "ModKrnBullToss", v, 2, gore, 110f, 4, gore, 40f).Speed(0.9f).Ev(2, "AnimAttack", flash).Ev(4, "AnimAttack", flash).Ev(4, "KrnCharge").Build();
            var st = new ClipBuilder(sh, "Paw", "ModKrnBullPaw").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(0, "AnimMoveStop").Ev(7, "AnimInputMultiplyStop").Ev(7, "AnimInputOff")
                .Ev(1, "AnimAttack", stud).Ev(4, "AnimAttack", stud).Ev(7, "AnimAttack", stud).Ev(7, "KrnDischarge").EvO(7, "AnimSound", v)
                .Ev(8, "KrnStampede").HandOff().Build();
            atk.Clear();
            // horn box x 11..29 plus a 35 px/s step
            atk.Add(Kit.Attack(a0, gr, 0.45f, rangeInner: 6f, rangeOuter: 34f));
            atk.Add(Kit.Attack(a0, gr2, 0.45f, rangeInner: 6f, rangeOuter: 36f));
            atk.Add(Kit.Attack(a0, gr3, 2.0f, rangeInner: 6f, rangeOuter: 54f));
            // the charge runs up to 160 px at 230 px/s
            Kit.SetSpecial(p, Kit.Attack(sp, st, 0f, rangeInner: 30f, rangeOuter: 140f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, first, 14f);
            BullMomentum.ChargeClip = Looped(sh, "Charge", "ModKrnBullCharge");
            BullMomentum.StuckClip = Looped(sh, "Stuck", "ModKrnBullStuck");
        }

        // Polarity Warg: twin bites, the second lunging; Magnetize drags the hero to Kaurn iron (Iron Grip, KrnMagnet).
        static void WargKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p) ?? a0; var v = Kit.Voice(p);
            int first = Strike.Mark(p);
            int b1 = Kit.AddEffect(p, KaurnFx.WargBite, attach: true, destroyOnAnimEnd: true, offsetX: 22f, offsetY: 14f);
            int b2 = Kit.AddEffect(p, KaurnFx.WargBite, attach: true, destroyOnAnimEnd: true, offsetX: 26f, offsetY: 14f);
            int ring = Kit.AddEffect(p, KaurnFx.PolarRing, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            // Combo: two pairs of bites, then the Hunt: a long lunge with three snaps, the last one charged (dazes)
            var s = Kit.Melee(sh, "Bites", "ModKrnWargBites", v, 2, b1, 40f, 5, b2, 70f).Ev(5, "KrnCharge").Build();
            var s2 = Kit.Melee(sh, "Bites", "ModKrnWargBites2", null, 2, b1, 50f, 5, b2, 80f).Speed(1.1f).Ev(5, "KrnCharge").Build();
            int shock = Kit.AddEffect(p, FxKit.Finisher(KaurnFx.WargBite, "ModKrnWargShock", damageMult: 1.1f, status: FxFactory.GetStatus("StatusDizzy")),
                                      attach: true, destroyOnAnimEnd: true, offsetX: 26f, offsetY: 14f);
            int shockFx = Kit.AddEffect(p, KaurnFx.CrackleWhite, offsetX: 26f, offsetY: 14f);
            var s3 = Kit.Melee(sh, "Bites", "ModKrnWargHunt", v, 2, b1, 110f, 4, b2, 60f, 6, shock, 60f).Speed(0.9f)
                .Ev(6, "AnimAttack", shockFx).Ev(5, "KrnCharge").Build();
            var mz = Special(sh, "Magnetize", "ModKrnWargMagnetize").Ev(3, "AnimAttack", ring).Ev(3, "KrnMagnetize").Ev(3, "KrnDischarge")
                .EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            // jaws reach 29 / 33 px ahead plus the lunges
            atk.Add(Kit.Attack(a0, s, 0.45f, rangeInner: 8f, rangeOuter: 40f));
            atk.Add(Kit.Attack(a0, s2, 0.45f, rangeInner: 8f, rangeOuter: 42f));
            atk.Add(Kit.Attack(a0, s3, 2.0f, rangeInner: 8f, rangeOuter: 56f));
            Kit.EnableSpecial(p, Kit.Attack(sp, mz, 0f, rangeInner: 20f, rangeOuter: 110f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, first, 14f);
        }

        // Storm Herald: a piercing lance of lightning; Eye of the Storm strikes the ring round it (HeraldStorm).
        static void HeraldKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int first = Strike.Mark(p);
            int lance = Kit.AddEffect(p, KaurnFx.Lance, offsetX: 26f, offsetY: 18f);
            int lL = Kit.AddEffect(p, KaurnFx.Lance, offsetX: 26f, offsetY: 18f, angle: -9f);
            int lR = Kit.AddEffect(p, KaurnFx.Lance, offsetX: 26f, offsetY: 18f, angle: 9f);
            // Combo: two lances, then the Thunderlance: a heavier lance that bursts into a quake where it stops
            var ln = Kit.Shot(sh, "Lance", "ModKrnHeraldLance", 3, v, 0f, lance).Ev(3, "KrnCharge").Build();
            var ln2 = Kit.Shot(sh, "Lance", "ModKrnHeraldLance2", 3, null, 0f, lance).Speed(1.15f).Ev(3, "KrnCharge").Build();
            // Thunderlance: a heavier lance that bursts into a quake where it stops
            int tl = Kit.AddEffect(p, FxKit.Finisher(KaurnFx.Lance, "ModKrnThunderlance", scale: 1.3f, damageMult: 1.2f, leaves: KaurnFx.Quake),
                                   offsetX: 26f, offsetY: 18f);
            var ln3 = Kit.Shot(sh, "Lance", "ModKrnHeraldThunderlance", 3, v, 0f, tl).Speed(0.85f).Ev(3, "KrnCharge").Build();
            var hn = Special(sh, "Horn", "ModKrnHeraldHorn").Ev(4, "KrnStorm").Ev(4, "KrnDischarge").EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            // the lance is born 26 px ahead and flies 260 px/s x 0.65 s (~195 px)
            atk.Add(Kit.Attack(a0, ln, 0.45f, rangeInner: 36f, rangeOuter: 150f, rangeRetreat: 34f));
            atk.Add(Kit.Attack(a0, ln2, 0.45f, rangeInner: 36f, rangeOuter: 150f, rangeRetreat: 34f));
            atk.Add(Kit.Attack(a0, ln3, 2.1f, rangeInner: 36f, rangeOuter: 140f, rangeRetreat: 34f));
            // the storm hits 60-110 px out: it blows the horn when the hero is in that band
            Kit.SetSpecial(p, Kit.Attack(sp, hn, 0f, rangeInner: 50f, rangeOuter: 105f, rangeRetreat: 0f), 7.5f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, first, 18f);
        }

        // Scarab Magus: an orb that splits into 3 shards; Kindle lets go two drifting balls that drag arcs (MagusKindle).
        static void MagusKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p) ?? a0; var v = Kit.Voice(p);
            int first = Strike.Mark(p);
            int orb = Kit.AddEffect(p, KaurnFx.SplitOrb, offsetX: 14f, offsetY: 17f);
            int oL = Kit.AddEffect(p, KaurnFx.SplitOrb, offsetX: 14f, offsetY: 17f, angle: -18f);
            int oR = Kit.AddEffect(p, KaurnFx.SplitOrb, offsetX: 14f, offsetY: 17f, angle: 18f);
            // Combo: two splitting orbs, then the Sunburst: a bigger orb that splits into a full ring
            var o = Kit.Shot(sh, "Orb", "ModKrnMagusOrb", 3, v, 0f, orb).Ev(3, "KrnCharge").Build();
            var o2 = Kit.Shot(sh, "Orb", "ModKrnMagusOrb2", 3, null, 0f, orb).Speed(1.15f).Ev(3, "KrnCharge").Build();
            // Sunburst: a bigger orb that splits into a full ring of shards
            var sun = FxKit.Finisher(KaurnFx.SplitOrb, "ModKrnSunburst", scale: 1.4f, speedMult: 0.85f);
            FxFactory.OnSpawn[sun] = i => { var sf = i.GetComponent<KrnSplitFx>() ?? i.AddComponent<KrnSplitFx>(); sf.Reset(); sf.count = 8; sf.fan = 45f; };
            int sb = Kit.AddEffect(p, sun, offsetX: 14f, offsetY: 17f);
            var o3 = Kit.Shot(sh, "Orb", "ModKrnMagusSunburst", 3, v, 0f, sb).Speed(0.85f).Ev(3, "KrnCharge").Build();
            var kd = Special(sh, "Kindle", "ModKrnMagusKindle").Ev(5, "KrnKindle").Ev(5, "KrnDischarge").EvO(5, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            // the orb flies 0.38 s (~57 px) then splits; shards go 220 px/s x 0.5 s
            atk.Add(Kit.Attack(a0, o, 0.5f, rangeInner: 45f, rangeOuter: 150f, rangeRetreat: 40f));
            atk.Add(Kit.Attack(a0, o2, 0.5f, rangeInner: 45f, rangeOuter: 150f, rangeRetreat: 40f));
            atk.Add(Kit.Attack(a0, o3, 2.2f, rangeInner: 45f, rangeOuter: 140f, rangeRetreat: 40f));
            Kit.EnableSpecial(p, Kit.Attack(sp, kd, 0f, rangeInner: 40f, rangeOuter: 130f, rangeRetreat: 20f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.65f);
            Strike.Feet(p, first, 17f);
        }

        // Storm Orrery: a ringed orb; Alignment lines its planets up on the hero and fires along the line (OrreryAlignment).
        static void OrreryKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int first = Strike.Mark(p);
            int orb = Kit.AddEffect(p, KaurnFx.Orb, offsetX: 16f, offsetY: 22f);
            // Combo: two orbs, then the Transit: three orbs down one line, a beat apart
            var fl = Kit.Shot(sh, "Fling", "ModKrnOrreryFling", 3, v, 0f, orb).Ev(3, "KrnCharge").Build();
            var fl2 = Kit.Shot(sh, "Fling", "ModKrnOrreryFling2", 3, null, 0f, orb).Speed(1.15f).Ev(3, "KrnCharge").Build();
            var fl3 = Kit.Shot(sh, "Fling", "ModKrnOrreryTransit", 3, v, 0.12f, orb, orb, orb).Speed(0.85f).Ev(3, "KrnCharge").Build();
            var al = Special(sh, "Align", "ModKrnOrreryAlign").Ev(1, "KrnAlign").Ev(1, "KrnDischarge").EvO(8, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            // the orb flies 150 px/s for 1.2 s from 16 px ahead
            atk.Add(Kit.Attack(a0, fl, 0.45f, rangeInner: 45f, rangeOuter: 140f, rangeRetreat: 40f));
            atk.Add(Kit.Attack(a0, fl2, 0.45f, rangeInner: 45f, rangeOuter: 140f, rangeRetreat: 40f));
            atk.Add(Kit.Attack(a0, fl3, 2.1f, rangeInner: 45f, rangeOuter: 140f, rangeRetreat: 40f));
            // the beam reaches 160 px
            Kit.SetSpecial(p, Kit.Attack(sp, al, 0f, rangeInner: 30f, rangeOuter: 150f, rangeRetreat: 20f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, first, 22f);
        }

        // Voltaic Pile: a 40 px lightning lash; Surge flashes every arc joined to it. Pulse: beads run along them (PilePulse).
        static void PileKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p) ?? a0; var v = Kit.Voice(p);
            int first = Strike.Mark(p);
            int hit = Kit.AddEffect(p, KaurnFx.WhipHit, attach: true, destroyOnAnimEnd: true, offsetX: 32f, offsetY: 20f);
            int vis = Kit.AddEffect(p, KaurnFx.WhipVis, offsetX: 12f, offsetY: 22f);
            int hL = Kit.AddEffect(p, KaurnFx.WhipHit, attach: true, destroyOnAnimEnd: true, offsetX: 32f, offsetY: 20f, angle: -22f);
            int hR = Kit.AddEffect(p, KaurnFx.WhipHit, attach: true, destroyOnAnimEnd: true, offsetX: 32f, offsetY: 20f, angle: 22f);
            // Combo: two whip lashes, then the Arc: the whip cracks across from one side to the other
            var w = Kit.Melee(sh, "Whip", "ModKrnPileWhip", v, 3, hit, 20f).Ev(3, "AnimAttack", vis).Ev(3, "KrnCharge").Build();
            var w2 = Kit.Melee(sh, "Whip", "ModKrnPileWhip2", null, 3, hit, 30f).Speed(1.15f).Ev(3, "AnimAttack", vis).Ev(3, "KrnCharge").Build();
            var w3 = Kit.Melee(sh, "Whip", "ModKrnPileArc", v, 3, hL, 20f).Speed(0.85f).Ev(3, "AnimAttack", vis).Ev(4, "AnimAttack", hit).Ev(5, "AnimAttack", hR).Ev(3, "KrnCharge").Build();
            var n = Special(sh, "Surge", "ModKrnPileSurge").Ev(7, "KrnSurge").Ev(7, "KrnDischarge").EvO(7, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            // the lash box spans x 12..52, y 15..25 above the feet
            atk.Add(Kit.Attack(a0, w, 0.45f, rangeInner: 10f, rangeOuter: 50f));
            atk.Add(Kit.Attack(a0, w2, 0.45f, rangeInner: 10f, rangeOuter: 52f));
            atk.Add(Kit.Attack(a0, w3, 2.0f, rangeInner: 10f, rangeOuter: 50f));
            // its arcs reach 70 px from it: surge when the hero is among them
            Kit.EnableSpecial(p, Kit.Attack(sp, n, 0f, rangeInner: 0f, rangeOuter: 80f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, first, 20f);
        }

        // Tesla Spire: Remote Bolt from the rod nearest the hero; Every Rod Answers (SpireRemote).
        static void SpireKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p) ?? a0; var v = Kit.Voice(p);
            int first = Strike.Mark(p);
            var r = new ClipBuilder(sh, "Relay", "ModKrnSpireRelay").Once().EvF(0, "AnimInputMultiplyFreeFace", 0f)
                .Ev(1, "AnimInputMultiplyStop").Ev(1, "AnimInputOff").Ev(1, "KrnRemoteAim").Ev(4, "KrnRemoteFire").Ev(4, "KrnCharge")
                .EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            // Combo: two relayed bolts, then the Chorus: the relay fires twice
            var r2 = new ClipBuilder(sh, "Relay", "ModKrnSpireRelay2").Once().Speed(1.15f).EvF(0, "AnimInputMultiplyFreeFace", 0f)
                .Ev(1, "AnimInputMultiplyStop").Ev(1, "AnimInputOff").Ev(1, "KrnRemoteAim").Ev(4, "KrnRemoteFire").Ev(4, "KrnCharge").Ev(-1, "AnimRun").Build();
            var r3 = new ClipBuilder(sh, "Relay", "ModKrnSpireChorus").Once().Speed(0.85f).EvF(0, "AnimInputMultiplyFreeFace", 0f)
                .Ev(1, "AnimInputMultiplyStop").Ev(1, "AnimInputOff").Ev(1, "KrnRemoteAim").Ev(4, "KrnRemoteFire").Ev(4, "KrnCharge")
                .EvO(4, "AnimSound", v).Ev(-1, "KrnRemoteAim").Ev(-1, "KrnRemoteFire").Ev(-1, "AnimRun").Build();
            var an = Special(sh, "Answer", "ModKrnSpireAnswer").Ev(4, "KrnAnswer").Ev(4, "KrnDischarge").EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            // the bolt flies 240 px/s for 0.6 s from a rod within 100 px of the hero, or from its own crown
            atk.Add(Kit.Attack(a0, r, 0.5f, rangeInner: 45f, rangeOuter: 145f, rangeRetreat: 40f));
            atk.Add(Kit.Attack(a0, r2, 0.5f, rangeInner: 45f, rangeOuter: 145f, rangeRetreat: 40f));
            atk.Add(Kit.Attack(a0, r3, 2.2f, rangeInner: 45f, rangeOuter: 145f, rangeRetreat: 40f));
            Kit.EnableSpecial(p, Kit.Attack(sp, an, 0f, rangeInner: 20f, rangeOuter: 130f, rangeRetreat: 20f), 7.5f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.65f);
            Strike.Feet(p, first, 30f);
            SpireRemote.RootedClip = Looped(sh, "Rooted", "ModKrnSpireRooted");
        }

        // Static Moth: two weaving darts; Drink the Rods (heal, store sparks). Spark Fall at 3 sparks (MothSparkFall).
        static void MothKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p) ?? a0; var v = Kit.Voice(p);
            int first = Strike.Mark(p);
            int d0 = Kit.AddEffect(p, KaurnFx.Dart, offsetX: 12f, offsetY: 19f, angle: -6f);
            int d1 = Kit.AddEffect(p, KaurnFx.Dart, offsetX: 12f, offsetY: 19f, angle: 6f);
            int d2 = Kit.AddEffect(p, KaurnFx.Dart, offsetX: 12f, offsetY: 19f, angle: -20f);
            int d3 = Kit.AddEffect(p, KaurnFx.Dart, offsetX: 12f, offsetY: 19f, angle: 20f);
            // Combo: two pairs of weaving darts, then a swarm of four
            var dt = Kit.Shot(sh, "Darts", "ModKrnMothDarts", 3, v, 0.06f, d0, d1).Ev(3, "KrnCharge").Build();
            var dt2 = Kit.Shot(sh, "Darts", "ModKrnMothDarts2", 3, null, 0.06f, d0, d1).Speed(1.15f).Ev(3, "KrnCharge").Build();
            var dt3 = Kit.Shot(sh, "Darts", "ModKrnMothSwarm", 3, v, 0.05f, d2, d0, d1, d3).Speed(0.85f).Ev(3, "KrnCharge").Build();
            var dr = Special(sh, "Drink", "ModKrnMothDrink").Ev(3, "KrnDischarge").Ev(3, "KrnDrink").EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            // darts fly 150 px/s for 0.9 s (~135 px)
            atk.Add(Kit.Attack(a0, dt, 0.45f, rangeInner: 40f, rangeOuter: 130f, rangeRetreat: 36f));
            atk.Add(Kit.Attack(a0, dt2, 0.45f, rangeInner: 40f, rangeOuter: 130f, rangeRetreat: 36f));
            atk.Add(Kit.Attack(a0, dt3, 2.0f, rangeInner: 40f, rangeOuter: 120f, rangeRetreat: 36f));
            Kit.EnableSpecial(p, Kit.Attack(sp, dr, 0f, rangeInner: 0f, rangeOuter: 150f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, first, 19f);
            MothSparkFall.FullIdle = Looped(sh, "IdleFull", "ModKrnMothIdleFull");
            MothSparkFall.FullRun = Looped(sh, "RunFull", "ModKrnMothRunFull");
        }

        static void LeaveRod(GameObject go, Player p) { Kit.AddDeathSpawn(p, KaurnFx.SlagRod); Strike.DeathAtFeet(p); }

        // Evolution tree: every evolution has exactly one parent.
        //   RivetImp    -> AnvilSmith, WireGremlin       AnvilSmith    -> ForgeColossus, Forgemaster
        //                                                WireGremlin   -> WireWyvern, FuseSapper
        //   SparkBeetle -> LodeHound, Stormcaller        LodeHound     -> ThunderBull, PolarityWarg
        //                                                Stormcaller   -> StormHerald, ScarabMagus
        //   CoilWisp    -> LeydenGolem, ArcLantern       LeydenGolem   -> StormOrrery, VoltaicPile
        //                                                ArcLantern    -> TeslaSpire, StaticMoth
        public static readonly List<MonsterDef> Monsters = new List<MonsterDef>
        {
            new MonsterDef { id = "KrnRivetImp", art = "KrnRivetImp", basePrefab = "EnemyGnome", health = 4f, evolveCost = 0f,
                             evolveTo = new[] { "KrnAnvilSmith", "KrnWireGremlin" }, kit = ImpKit, customize = LeaveRod },
            new MonsterDef { id = "KrnSparkBeetle", art = "KrnSparkBeetle", basePrefab = "EnemyGiantRat_Fireball", health = 3.5f, evolveCost = 0f,
                             evolveTo = new[] { "KrnLodeHound", "KrnStormcaller" }, kit = BeetleKit, customize = LeaveRod },
            new MonsterDef { id = "KrnCoilWisp", art = "KrnCoilWisp", basePrefab = "EnemyFlyingEye_Dodge", health = 3f, evolveCost = 0f,
                             evolveTo = new[] { "KrnLeydenGolem", "KrnArcLantern" }, kit = WispKit, customize = LeaveRod },
            new MonsterDef { id = "KrnAnvilSmith", art = "KrnAnvilSmith", basePrefab = "EnemyOrc", health = 7f, speedMult = 0.9f, evolveCost = 2.5f,
                             evolveTo = new[] { "KrnForgeColossus", "KrnForgemaster" }, kit = SmithKit, customize = LeaveRod },
            new MonsterDef { id = "KrnStormcaller", art = "KrnStormcaller", basePrefab = "EnemyWitch", health = 6f, evolveCost = 2.5f, damageMult = 1.4f,
                             evolveTo = new[] { "KrnStormHerald", "KrnScarabMagus" }, kit = CallerKit, customize = LeaveRod },
            new MonsterDef { id = "KrnLodeHound", art = "KrnLodeHound", basePrefab = "EnemyRatman", health = 6f, evolveCost = 2.5f, damageMult = 1.4f,
                             evolveTo = new[] { "KrnThunderBull", "KrnPolarityWarg" }, kit = HoundKit, customize = LeaveRod },
            new MonsterDef { id = "KrnLeydenGolem", art = "KrnLeydenGolem", basePrefab = "EnemyWildShaman", health = 6.5f, speedMult = 0.85f,
                             evolveCost = 2.5f, damageMult = 1.3f, evolveTo = new[] { "KrnStormOrrery", "KrnVoltaicPile" }, kit = LeydenKit, customize = LeaveRod },
            new MonsterDef { id = "KrnWireGremlin", art = "KrnWireGremlin", basePrefab = "EnemyFlyingEyeBomber", health = 6.5f, evolveCost = 2.5f, damageMult = 1.4f,
                             evolveTo = new[] { "KrnWireWyvern", "KrnFuseSapper" }, kit = GremlinKit, customize = LeaveRod },
            new MonsterDef { id = "KrnArcLantern", art = "KrnArcLantern", basePrefab = "EnemyFlyingEye_Rapidfire", health = 5.5f, evolveCost = 2.5f, damageMult = 1.4f,
                             evolveTo = new[] { "KrnTeslaSpire", "KrnStaticMoth" }, kit = LanternKit, customize = LeaveRod },
            new MonsterDef { id = "KrnForgeColossus", art = "KrnForgeColossus", basePrefab = "EnemyTroll", health = 14f, evolveCost = 4.5f, damageMult = 1.2f,
                             kit = ColossusKit, customize = LeaveRod },
            new MonsterDef { id = "KrnStormHerald", art = "KrnStormHerald", basePrefab = "EnemyPriestess", health = 12.5f, evolveCost = 4.5f, damageMult = 1.2f,
                             kit = HeraldKit, customize = LeaveRod },
            new MonsterDef { id = "KrnThunderBull", art = "KrnThunderBull", basePrefab = "EnemyMinotaur", health = 13.5f, evolveCost = 4.5f, damageMult = 0.9f,
                             kit = BullKit, customize = LeaveRod },
            new MonsterDef { id = "KrnStormOrrery", art = "KrnStormOrrery", basePrefab = "EnemyFlyingEye_Red", health = 12.5f, evolveCost = 4.5f, damageMult = 1.2f,
                             kit = OrreryKit, customize = LeaveRod },
            new MonsterDef { id = "KrnForgemaster", art = "KrnForgemaster", basePrefab = "EnemyCapraDemon", health = 14f, speedMult = 0.9f, evolveCost = 4.5f,
                             kit = MasterKit, customize = LeaveRod },
            new MonsterDef { id = "KrnWireWyvern", art = "KrnWireWyvern", basePrefab = "EnemySmallDragon", health = 13f, evolveCost = 4.5f, damageMult = 1.1f,
                             kit = WyvernKit, customize = LeaveRod },
            new MonsterDef { id = "KrnFuseSapper", art = "KrnFuseSapper", basePrefab = "EnemyGhoul", health = 12.5f, evolveCost = 4.5f, damageMult = 1.3f,
                             kit = SapperKit, customize = LeaveRod },
            new MonsterDef { id = "KrnPolarityWarg", art = "KrnPolarityWarg", basePrefab = "EnemyEyelessBeast", health = 13f, evolveCost = 4.5f, damageMult = 0.9f,
                             kit = WargKit, customize = LeaveRod },
            new MonsterDef { id = "KrnScarabMagus", art = "KrnScarabMagus", basePrefab = "EnemySkeletonPope", health = 12.5f, evolveCost = 4.5f, damageMult = 1.3f,
                             kit = MagusKit, customize = LeaveRod },
            new MonsterDef { id = "KrnVoltaicPile", art = "KrnVoltaicPile", basePrefab = "EnemyDarkGuardian", health = 14f, speedMult = 0.85f, evolveCost = 4.5f,
                             kit = PileKit, customize = LeaveRod },
            new MonsterDef { id = "KrnTeslaSpire", art = "KrnTeslaSpire", basePrefab = "EnemyBeholder", health = 12.5f, speedMult = 0.9f, evolveCost = 4.5f, damageMult = 1.3f,
                             kit = SpireKit, customize = LeaveRod },
            new MonsterDef { id = "KrnStaticMoth", art = "KrnStaticMoth", basePrefab = "EnemyFlyingEyeBomber", health = 12.5f, evolveCost = 4.5f, damageMult = 1.2f,
                             kit = MothKit, customize = LeaveRod },
        };

        /// <summary>Each monster's own mechanic (the Rivet Imp's and the Wire Gremlin's live on their attacks' hitboxes).</summary>
        static readonly Dictionary<string, Type> Quirks = new Dictionary<string, Type>
        {
            { "KrnSparkBeetle", typeof(BeetleOvercharge) }, { "KrnCoilWisp", typeof(WispRelay) }, { "KrnLodeHound", typeof(HoundPolarity) },
            { "KrnStormcaller", typeof(CallerStaticBuild) }, { "KrnLeydenGolem", typeof(LeydenJar) }, { "KrnForgeColossus", typeof(ColossusOverheat) },
            { "KrnForgemaster", typeof(ForgemasterCollector) }, { "KrnWireWyvern", typeof(WyvernRide) }, { "KrnFuseSapper", typeof(SapperCharges) },
            { "KrnThunderBull", typeof(BullMomentum) }, { "KrnPolarityWarg", typeof(WargMagnetize) }, { "KrnStormHerald", typeof(HeraldStorm) },
            { "KrnScarabMagus", typeof(MagusKindle) }, { "KrnStormOrrery", typeof(OrreryAlignment) }, { "KrnVoltaicPile", typeof(PilePulse) },
            { "KrnTeslaSpire", typeof(SpireRemote) }, { "KrnStaticMoth", typeof(MothSparkFall) },
        };

        public static readonly GodDef God = new GodDef
        {
            name = "Kaurn",
            text = "Arcs between allies zap hero",
            flavour = "The forge is lit by lightning.\nMind the rods.",
            winText = "THE FORGE GOES COLD",
            portraitArt = "DeityKaurn",
            startingMonsters = new[] { "KrnRivetImp", "KrnSparkBeetle", "KrnCoilWisp" },
        };

        static List<DamageEffectData> SpecialEffects(Powerup pu) { return R.Get<List<DamageEffectData>>(pu, "m_specialAttackDamageEffects"); }

        public static readonly List<ItemDef> Items = new List<ItemDef>
        {
            new ItemDef { id = "SpellKrnChainSpark", cloneFrom = "SpellCycloneSummon", cost = 40, group = "GroupSpellsPurchasable",
                name = "Chain Spark", description = "Throw a spark that jumps from monster to monster",
                bubbleArt = "IconKrnChainSparkBubble",
                customize = (go, pu) =>
                {
                    var sp = SpecialEffects(pu);
                    // the item's own spark (art/out_itemfx) on the hero-only template, its jumps flash ItemPack2.ChainJumpFlash
                    ItemArt.Wear(KaurnFx.HeroChainSpark, "FxItemChainSpark", "Fly", loop: true);
                    ItemArt.Puffs(KaurnFx.HeroChainSpark, ItemPack2.ChainJumpFlash ?? ItemArt.Visual("ModItemChainJump", "FxItemChainSpark", "Hit"));
                    if (sp.Count > 0 && KaurnFx.HeroChainSpark != null) sp[0].m_object = KaurnFx.HeroChainSpark;
                } },
            new ItemDef { id = "ArtifactKrnLightningRod", cloneFrom = "ArtifactSpellbookTears", cost = 40, group = "GroupArtifactsPurchasable",
                name = "Lightning Rod", description = "A floating rod throws ball lightning at your foes",
                bubbleArt = "IconKrnLightningRodBubble", hudArt = "IconKrnLightningRodHud",
                customize = (go, pu) =>
                {
                    // the rod's own copy of the hero ball, launched at the nearest monster
                    var ball = ItemFixes.HeroCopy(KaurnFx.HeroBall, "ModKrnHeroRodBall");
                    ItemArt.Wear(ball, "FxItemRodBall", "Fly", loop: true);
                    ItemArt.Puffs(ball, ItemArt.Visual("ModItemRodBallPop", "FxItemRodBall", "Pop"));
                    ItemFixes.AimAtMonsters(ball, 220f);
                    ItemFixes.Follower(go, pu, "FxItemTokenRod", 8f, ball);
                } },
        };

        public static void Register()
        {
            KaurnFx.Build();
            foreach (var m in Monsters)
            {
                var t = new MonsterTraits();
                if (m.id == "KrnAnvilSmith") { t.maxPlates = 1; t.plateFx = KaurnFx.Plates; t.plateBreakFx = KaurnFx.Shatter; }
                Type q;
                if (Quirks.TryGetValue(m.id, out q)) t.behaviours.Add(q);
                MonsterTraits.Register(m.PrefabName, t);
            }
            foreach (var m in Monsters) MonsterFactory.Build(m);
            MonsterFactory.LinkEvolutions(Monsters);
            MonsterEvents.AttackSpawned += OnAttackSpawned;
            DeityFactory.Register(God);
            // the gold idol carved in the Storm Forge's likeness
            var prev = SlotGods.PortraitFor;
            SlotGods.PortraitFor = (tier, perk) =>
                tier == SlotTier.Gold && perk != null && perk.GetName() == God.name ? SlotArt.Clip("DeityGoldIdolKaurn", "Idle") : (prev != null ? prev(tier, perk) : null);
            // Kaurn registers before ItemPack: ItemPack.Register builds everything in ItemPack.Items, so only build here
            // ourselves if the shop pack already ran (never twice).
            bool shopBuilt = ItemPack.Built.ContainsKey("SpellWickwalk");
            if (shopBuilt)
                foreach (var def in Items)
                {
                    try { ItemRegistry.Register(def); }
                    catch (Exception e) { Plugin.Log.LogError("Item " + def.id + " failed: " + e); }
                }
            ItemPack.Items.AddRange(Items);
            Strike.KeepAllScales();
        }

        static void OnAttackSpawned(Player owner, GameObject fx, GameObject template)
        {
            var q = owner != null && fx != null ? owner.GetComponent<KaurnBehaviour>() : null;
            if (q != null) q.OnAttackSpawned(fx, template);
        }
    }
}
