using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Art;
    using CrawlFurther.Gods;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;
    using CrawlFurther.Content.Gods.Vhorrul;

    /// <summary>
    /// Ossivar, the Marrow King: bones that come apart and come home. The god's resource is the bone pile; the Rattlebones
    /// line builds things out of bone, the hound line hunts by blood, the crow line moves bones and bodies around.
    /// Spawn points and sync frames: art/out_ossivar/TIMING.md (x right, y up; Kit.AddEffect offsetY = height).
    /// </summary>
    public static class OssivarPack
    {
        static exSpriteAnimClip Loop(SpriteSheet sh, string anim, string name) { return sh.Has(anim) ? new ClipBuilder(sh, anim, name).Loop().Build() : null; }

        static exSpriteAnimClip Once(SpriteSheet sh, string anim, string name)
        {
            if (!sh.Has(anim)) return null;
            var c = new ClipBuilder(sh, anim, name).Once().Build();
            c.stopAction = exSpriteAnimClip.StopAction.DoNothing;
            return c;
        }

        // ================================================================== tier 1
        // Rattlebones: Skull Lob (the skull stays where it lands), a headless swipe that calls it home, and Collapse.
        static void RattlebonesKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int lob = Kit.AddEffect(p, OssivarFx.SkullLob, offsetX: 10f, offsetY: 1f);
            int swipe = Kit.AddEffect(p, OssivarFx.RattleSwipe, attach: true, destroyOnAnimEnd: true, offsetX: 7f, offsetY: 5f);
            var lb = Kit.Shot(sh, "Lob", "ModOssRattleLob", 3, v, 0f, lob).Ev(1, "OssSkullOff").Build();
            var sw = Kit.Melee(sh, "Swipe", "ModOssRattleSwipe", v, 2, swipe, 60f).Ev(3, "OssCallSkull").Build();
            var col = new ClipBuilder(sh, "Collapse", "ModOssRattleCollapse").Once()
                .Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop").Ev(0, "OssSkullSnap").Ev(1, "AnimStartInvincibility")
                .Ev(4, "ModCollapseHeal").EvO(4, "AnimSound", v)
                .Ev(6, "ModDropBones").Ev(7, "AnimStopInvincibility").Ev(-1, "AnimRun").Build();
            RattleSkull.BareIdle = Loop(sh, "IdleBare", "ModOssRattleIdleBare");
            RattleSkull.BareRun = Loop(sh, "RunBare", "ModOssRattleRunBare");
            atk.Clear();
            atk.Add(Kit.Attack(a0, lb, 1.6f, rangeInner: 24f, rangeOuter: 62f, rangeRetreat: 18f));   // 170 px/s for 0.38 s
            atk.Add(Kit.Attack(a0, sw, 0.9f, rangeInner: 6f, rangeOuter: 16f, rangeRetreat: 0f));
            Kit.SetSpecial(p, Kit.Attack(sp, col, 0f, rangeInner: 0f, rangeOuter: 40f, rangeRetreat: 0f), 5.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 9f);
        }

        // Marrow Hound: two snaps (may bleed); Howl rings bleed round it, then it sprints. Blood Scent: faster at a bleeding hero.
        static void HoundKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            var like = Kit.Effects(p)[0];
            int n0 = Strike.Mark(p);
            int bite = Kit.AddEffect(p, OssivarFx.HoundBite, attach: true, destroyOnAnimEnd: true, offsetX: 12f, offsetY: 6f, like: like);
            int howl = Kit.AddEffect(p, OssivarFx.HoundHowl, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            var bt = Kit.Melee(sh, "Bite", "ModOssHoundBite", v, 2, bite, 70f, 4, bite, 50f).Build();
            var hw = new ClipBuilder(sh, "Howl", "ModOssHoundHowl").Once().Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop")
                .Ev(3, "AnimAttack", howl).EvO(3, "AnimSound", v).EvF(-1, "ModSprint", 2.5f).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, bt, 1.1f, rangeInner: 10f, rangeOuter: 22f));
            Kit.SetSpecial(p, Kit.Attack(sp, hw, 0f, rangeInner: 0f, rangeOuter: 34f, rangeRetreat: 0f), 5.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 6f);
        }

        // Cairn Crow: a diving peck that pulls a splinter out of a bleeding hero; Caw herds nearby piles toward kin.
        static void CrowKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int peck = Kit.AddEffect(p, OssivarFx.CrowPeck, attach: true, destroyOnAnimEnd: true, offsetX: 12f, offsetY: 6f);
            var pk = new ClipBuilder(sh, "Peck", "ModOssCrowPeck").Once().AimLock(1)
                .EvF(2, "AnimMove", 170f).Ev(2, "AnimAttack", peck).EvO(2, "AnimSound", v).Ev(3, "AnimMoveStop").Ev(-1, "AnimRun").Build();
            var caw = new ClipBuilder(sh, "Caw", "ModOssCrowCaw").Once().Channel(v, 3, "OssCaw").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, pk, 1.2f, rangeInner: 10f, rangeOuter: 24f));
            // the bot caws when piles are about: the special is cheap, and a caw with no piles costs it nothing but time
            Kit.SetSpecial(p, Kit.Attack(sp, caw, 0f, rangeInner: 0f, rangeOuter: 90f, rangeRetreat: 30f), 5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 9f);
        }

        // ================================================================== tier 2
        // Bone Lancer: a 32 px thrust (may bleed); Spear Volley throws three spears in a fan that stand where they miss.
        static void LancerKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int thrust = Kit.AddEffect(p, OssivarFx.LancerThrust, attach: true, destroyOnAnimEnd: true, offsetX: 24f, offsetY: 12f);
            int s1 = Kit.AddEffect(p, OssivarFx.BoneSpear, offsetX: 14f, offsetY: 12f, angle: -14f);
            int s2 = Kit.AddEffect(p, OssivarFx.BoneSpear, offsetX: 14f, offsetY: 12f, angle: 0.01f);
            int s3 = Kit.AddEffect(p, OssivarFx.BoneSpear, offsetX: 14f, offsetY: 12f, angle: 14f);
            var th = Kit.Melee(sh, "Thrust", "ModOssLancerThrust", v, 2, thrust, 90f).Build();
            // Combo: two thrusts, then the Charge: a long run behind the spear that skewers twice
            var th2 = Kit.Melee(sh, "Thrust", "ModOssLancerThrust2", null, 2, thrust, 100f).Speed(1.15f).Build();
            var th3 = Kit.Melee(sh, "Thrust", "ModOssLancerCharge", v, 2, thrust, 170f, 4, thrust, 60f).Speed(0.9f).Build();
            var vo = Kit.Shot(sh, "Volley", "ModOssLancerVolley", 3, v, 0f, s1, s2, s3).Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, th, 0.35f, rangeInner: 18f, rangeOuter: 38f));
            atk.Add(Kit.Attack(a0, th2, 0.35f, rangeInner: 18f, rangeOuter: 40f));
            atk.Add(Kit.Attack(a0, th3, 1.5f, rangeInner: 18f, rangeOuter: 64f));
            Kit.SetSpecial(p, Kit.Attack(sp, vo, 0f, rangeInner: 40f, rangeOuter: 110f, rangeRetreat: 28f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.55f);
            Strike.Feet(p, n0, 12f);
        }

        // Gravedigger: a spade swing (two within 2 s bury the hero to the knees); Unearth digs up two bone piles.
        static void GravediggerKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int spade = Kit.AddEffect(p, OssivarFx.DigSpade, attach: true, destroyOnAnimEnd: true, offsetX: 12f, offsetY: 5f);
            var sd = Kit.Melee(sh, "Spade", "ModOssDigSpade", v, 2, spade, 50f).Build();
            // Combo: two spade swings, then the Backfill: it digs in and flings the spade twice, stepping in
            var sd2 = Kit.Melee(sh, "Spade", "ModOssDigSpade2", null, 2, spade, 60f).Speed(1.15f).Build();
            var sd3 = Kit.Melee(sh, "Spade", "ModOssDigBackfill", v, 2, spade, 90f, 4, spade, 40f).Speed(0.9f).Build();
            var un = new ClipBuilder(sh, "Unearth", "ModOssUnearth").Once().Channel(v, 5, "OssUnearth").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sd, 0.35f, rangeInner: 10f, rangeOuter: 24f));
            atk.Add(Kit.Attack(a0, sd2, 0.35f, rangeInner: 10f, rangeOuter: 26f));
            atk.Add(Kit.Attack(a0, sd3, 1.5f, rangeInner: 10f, rangeOuter: 38f));
            Kit.SetSpecial(p, Kit.Attack(sp, un, 0f, rangeInner: 0f, rangeOuter: 120f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.55f);
            Strike.Feet(p, n0, 10f);
        }

        // Gravetusk: a tusk toss; a 70 px charge that bends after a bleeding hero and bursts trampled piles into shards.
        static void GravetuskKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int gore = Kit.AddEffect(p, OssivarFx.TuskGore, attach: true, destroyOnAnimEnd: true, offsetX: 12f, offsetY: 11f);
            int rush = Kit.AddEffect(p, OssivarFx.TuskRush, attach: true, destroyOnAnimEnd: true, offsetX: 12f, offsetY: 8f);
            var gr = Kit.Melee(sh, "Gore", "ModOssTuskGore", v, 2, gore, 60f).Build();
            // Combo: two gores, then the Toss: a lunging gore that tosses him with a second
            var gr2 = Kit.Melee(sh, "Gore", "ModOssTuskGore2", null, 2, gore, 70f).Speed(1.1f).Build();
            var gr3 = Kit.Melee(sh, "Gore", "ModOssTuskToss", v, 2, rush, 130f, 4, gore, 40f).Speed(0.9f).Build();
            var ch = new ClipBuilder(sh, "Charge", "ModOssTuskCharge").Once().AimLock(1).Ev(1, "OssChargeOn")
                .EvF(2, "AnimMove", 230f).Ev(2, "AnimAttack", rush).EvO(2, "AnimSound", v)
                .Ev(7, "AnimMoveStop").Ev(7, "OssChargeOff").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, gr, 0.4f, rangeInner: 10f, rangeOuter: 26f));
            atk.Add(Kit.Attack(a0, gr2, 0.4f, rangeInner: 10f, rangeOuter: 28f));
            atk.Add(Kit.Attack(a0, gr3, 1.8f, rangeInner: 10f, rangeOuter: 48f));
            Kit.SetSpecial(p, Kit.Attack(sp, ch, 0f, rangeInner: 30f, rangeOuter: 90f, rangeRetreat: 0f), 6f);   // 230 px/s x 0.3 s
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 13f);
        }

        // Barghest: two rending bites (+50 % and a slow from behind); Pounce lands 20 px past the hero, facing him.
        static void BarghestKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            var like = Kit.Effects(p)[0];
            int n0 = Strike.Mark(p);
            int bite = Kit.AddEffect(p, OssivarFx.BarghestBite, attach: true, destroyOnAnimEnd: true, offsetX: 13f, offsetY: 12f, like: like);
            int land = Kit.AddEffect(p, OssivarFx.PounceBite, attach: true, destroyOnAnimEnd: true, offsetX: 12f, offsetY: 9f);
            int dust = Kit.AddEffect(p, OssivarFx.PounceDust, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            var bt = Kit.Melee(sh, "Bite", "ModOssBarghestBite", v, 2, bite, 60f, 4, bite, 30f).Build();
            // Combo: two pairs of rending bites, then the Maul: a lunge and three bites
            var bt2 = Kit.Melee(sh, "Bite", "ModOssBarghestBite2", null, 2, bite, 70f, 4, bite, 30f).Speed(1.1f).Build();
            var bt3 = Kit.Melee(sh, "Bite", "ModOssBarghestMaul", v, 2, land, 120f, 4, bite, 30f, 5, bite, 20f).Speed(0.9f).Build();
            var pc = new ClipBuilder(sh, "Pounce", "ModOssBarghestPounce").Once().AimLock(1)
                .Ev(2, "AnimStartInvincibility").Ev(2, "OssPounce").EvO(2, "AnimSound", v)
                .Ev(6, "AnimStopInvincibility").Ev(6, "AnimAttack", land).Ev(6, "AnimAttack", dust).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, bt, 0.35f, rangeInner: 10f, rangeOuter: 26f));
            atk.Add(Kit.Attack(a0, bt2, 0.35f, rangeInner: 10f, rangeOuter: 28f));
            atk.Add(Kit.Attack(a0, bt3, 1.6f, rangeInner: 10f, rangeOuter: 46f));
            Kit.SetSpecial(p, Kit.Attack(sp, pc, 0f, rangeInner: 30f, rangeOuter: 88f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.55f);
            Strike.Feet(p, n0, 9f);
        }

        // Ossuary Priest: a slow homing marrow bolt; Raise stands nearby piles up as Bone Rats. Shepherd: piles come to it.
        static void PriestKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int bolt = Kit.AddEffect(p, OssivarFx.MarrowBolt, offsetX: 12f, offsetY: 12f);
            var b = Kit.Shot(sh, "Bolt", "ModOssPriestBolt", 3, v, 0f, bolt).Build();
            int bl = Kit.AddEffect(p, OssivarFx.MarrowBolt, offsetX: 12f, offsetY: 12f, angle: -30f);
            int br = Kit.AddEffect(p, OssivarFx.MarrowBolt, offsetX: 12f, offsetY: 12f, angle: 30f);
            // Combo: two homing bolts, then the Litany: three that spread wide and close in on him
            var b2 = Kit.Shot(sh, "Bolt", "ModOssPriestBolt2", 3, null, 0f, bolt).Speed(1.15f).Build();
            var b3 = Kit.Shot(sh, "Bolt", "ModOssPriestLitany", 3, v, 0.06f, bl, bolt, br).Speed(0.85f).Build();
            var rs = new ClipBuilder(sh, "Raise", "ModOssPriestRaise").Once().Channel(v, 5, "OssRaise").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, b, 0.45f, rangeInner: 60f, rangeOuter: 120f, rangeRetreat: 45f));
            atk.Add(Kit.Attack(a0, b2, 0.45f, rangeInner: 60f, rangeOuter: 120f, rangeRetreat: 45f));
            atk.Add(Kit.Attack(a0, b3, 2.1f, rangeInner: 50f, rangeOuter: 120f, rangeRetreat: 45f));
            Kit.SetSpecial(p, Kit.Attack(sp, rs, 0f, rangeInner: 40f, rangeOuter: 200f, rangeRetreat: 40f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 12f);
        }

        // Carrion Vulture: a raking swoop (always bleeds on a hero below half health); Plummet drops onto his marked spot.
        static void VultureKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int rake = Kit.AddEffect(p, OssivarFx.VultureRake, attach: true, destroyOnAnimEnd: true, offsetX: 7f, offsetY: 5f);
            int dive = Kit.AddEffect(p, OssivarFx.DiveHit, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            var rk = new ClipBuilder(sh, "Rake", "ModOssVultureRake").Once().AimLock(1)
                .EvF(2, "AnimMove", 170f).Ev(2, "AnimAttack", rake).EvO(2, "AnimSound", v).Ev(4, "AnimMoveStop").Ev(-1, "AnimRun").Build();
            // Combo: two swoops, then the Double Swoop: it rakes through him and back again
            var rk2 = new ClipBuilder(sh, "Rake", "ModOssVultureRake2").Once().Speed(1.1f).AimLock(1)
                .EvF(2, "AnimMove", 190f).Ev(2, "AnimAttack", rake).Ev(4, "AnimMoveStop").Ev(-1, "AnimRun").Build();
            var rk3 = new ClipBuilder(sh, "Rake", "ModOssVultureDouble").Once().Repeat(2).Speed(1.2f).AimLock(1)
                .EvF(2, "AnimMove", 220f).Ev(2, "AnimAttack", rake).EvO(2, "AnimSound", v).EvF(5, "AnimInputMultiplyFreeFace", 0f)
                .Ev(7, "AnimInputMultiplyStop").EvF(8, "AnimMove", 220f).Ev(8, "AnimAttack", rake).Ev(10, "AnimMoveStop").Ev(-1, "AnimRun").Build();
            var pl = new ClipBuilder(sh, "Plummet", "ModOssVulturePlummet").Once().Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop")
                .Ev(2, "OssPlummetUp").Ev(4, "OssPlummetDown").Ev(6, "AnimAttack", dive).Ev(6, "OssPlummetLand").EvO(6, "AnimSound", v)
                .Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, rk, 0.4f, rangeInner: 12f, rangeOuter: 36f));
            atk.Add(Kit.Attack(a0, rk2, 0.4f, rangeInner: 12f, rangeOuter: 38f));
            atk.Add(Kit.Attack(a0, rk3, 1.8f, rangeInner: 12f, rangeOuter: 50f));
            Kit.SetSpecial(p, Kit.Attack(sp, pl, 0f, rangeInner: 30f, rangeOuter: 150f, rangeRetreat: 30f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 10f);
        }

        // ================================================================== tier 3
        // Charnel Rider: a wide lance sweep; Joust gallops until a wall or 110 px. Unhorsed at 5 health: a lance throw and a
        // short running thrust on foot.
        static void RiderKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int sweep = Kit.AddEffect(p, OssivarFx.LanceSweep, attach: true, destroyOnAnimEnd: true, offsetX: 20f, offsetY: 15f);
            int tip = Kit.AddEffect(p, OssivarFx.JoustTip, attach: true, destroyOnAnimEnd: true, offsetX: 34f, offsetY: 17f);
            int trample = Kit.AddEffect(p, OssivarFx.JoustTrample, attach: true, destroyOnAnimEnd: true, offsetX: 10f, offsetY: 6f);
            int thrown = Kit.AddEffect(p, OssivarFx.LanceThrow, offsetX: 12f, offsetY: 15f);
            int ftip = Kit.AddEffect(p, OssivarFx.FootThrustTip, attach: true, destroyOnAnimEnd: true, offsetX: 27f, offsetY: 14f);
            var sw = Kit.Melee(sh, "Sweep", "ModOssRiderSweep", v, 2, sweep, 40f).Build();
            var js = new ClipBuilder(sh, "Joust", "ModOssRiderJoust").Once().AimLock(2)
                .EvF(3, "AnimMove", 230f).Ev(3, "OssJoustOn").Ev(3, "AnimAttack", tip).Ev(3, "AnimAttack", trample).EvO(3, "AnimSound", v)
                .Ev(9, "AnimMoveStop").Ev(9, "OssJoustOff").Ev(-1, "AnimRun").Build();
            var th = Kit.Shot(sh, "FootThrow", "ModOssRiderThrow", 2, v, 0f, thrown).Build();
            RiderUnhorse.FootThrust = new ClipBuilder(sh, "FootThrust", "ModOssRiderThrust").Once().AimLock(1)
                .EvF(2, "AnimMove", 200f).Ev(2, "AnimAttack", ftip).EvO(2, "AnimSound", v).Ev(6, "AnimMoveStop").Ev(-1, "AnimRun").Build();
            RiderUnhorse.CrackIdle = Loop(sh, "IdleCracked", "ModOssRiderIdleCracked");
            RiderUnhorse.CrackRun = Loop(sh, "RunCracked", "ModOssRiderRunCracked");
            RiderUnhorse.UnhorseClip = Once(sh, "Unhorse", "ModOssRiderUnhorse");
            RiderUnhorse.FootIdle = Loop(sh, "FootIdle", "ModOssRiderFootIdle");
            RiderUnhorse.FootRun = Loop(sh, "FootRun", "ModOssRiderFootRun");
            RiderUnhorse.FootDeath = Once(sh, "FootDeath", "ModOssRiderFootDeath");
            atk.Clear();
            atk.Add(Kit.Attack(a0, sw, 1.6f, rangeInner: 14f, rangeOuter: 38f));
            atk.Add(Kit.Attack(a0, th, 1.8f, rangeInner: 30f, rangeOuter: 100f, rangeRetreat: 20f));
            Kit.SetSpecial(p, Kit.Attack(sp, js, 0f, rangeInner: 40f, rangeOuter: 130f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 15f);
        }

        // Spinehook: a hook rake (may bleed); a harpoon that bites the hero or a bone pile and reels the pile in through him.
        static void SpinehookKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int rake = Kit.AddEffect(p, OssivarFx.HookRake, attach: true, destroyOnAnimEnd: true, offsetX: 18f, offsetY: 13f);
            int harp = Kit.AddEffect(p, OssivarFx.Harpoon, offsetX: 23f, offsetY: 16f);
            var rk = Kit.Melee(sh, "Rake", "ModOssHookRake", v, 2, rake, 40f).Build();
            // Combo: two hook rakes, then the Reel: a lunge and two rakes that drag back across him
            var rk2 = Kit.Melee(sh, "Rake", "ModOssHookRake2", null, 2, rake, 50f).Speed(1.1f).Build();
            var rk3 = Kit.Melee(sh, "Rake", "ModOssHookReel", v, 2, rake, 110f, 4, rake, 0f).Speed(0.9f).Build();
            var hp = Kit.Shot(sh, "Harpoon", "ModOssHookHarpoon", 3, v, 0f, harp).Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, rk, 0.4f, rangeInner: 10f, rangeOuter: 28f));
            atk.Add(Kit.Attack(a0, rk2, 0.4f, rangeInner: 10f, rangeOuter: 30f));
            atk.Add(Kit.Attack(a0, rk3, 1.8f, rangeInner: 10f, rangeOuter: 46f));
            Kit.SetSpecial(p, Kit.Attack(sp, hp, 0f, rangeInner: 30f, rangeOuter: 100f, rangeRetreat: 24f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 16f);
        }

        // Tombwright: a mallet smash that also knocks over the headstone it hits; Raise Stones puts three in a line at the hero.
        static void TombwrightKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int mal = Kit.AddEffect(p, OssivarFx.MalletSmash, attach: true, destroyOnAnimEnd: true, offsetX: 19f, offsetY: 5f);
            var ml = Kit.Melee(sh, "Mallet", "ModOssTombMallet", v, 3, mal, 30f).Ev(3, "OssMalletKnock").Build();
            // Combo: two mallet smashes, then the Chisel: two smashes in a row, stepping in
            var ml2 = Kit.Melee(sh, "Mallet", "ModOssTombMallet2", null, 3, mal, 40f).Speed(1.1f).Ev(3, "OssMalletKnock").Build();
            var ml3 = Kit.Melee(sh, "Mallet", "ModOssTombChisel", v, 3, mal, 40f, 10, mal, 70f).Repeat(2).Speed(1.2f).Ev(3, "OssMalletKnock").Ev(10, "OssMalletKnock").Build();
            var rs = new ClipBuilder(sh, "Raise", "ModOssTombRaise").Once().AimLock(3).Ev(4, "OssRaiseStones").EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, ml, 0.45f, rangeInner: 10f, rangeOuter: 26f));
            atk.Add(Kit.Attack(a0, ml2, 0.45f, rangeInner: 10f, rangeOuter: 28f));
            atk.Add(Kit.Attack(a0, ml3, 2.0f, rangeInner: 10f, rangeOuter: 40f));
            Kit.SetSpecial(p, Kit.Attack(sp, rs, 0f, rangeInner: 20f, rangeOuter: 100f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 18f);
        }

        // Coffin Bearer: a coffin slam ahead; Whirl spins it (radius 14 -> 34 px, three hits) and leaves it dizzy, unless it
        // lets go mid-whirl and the coffin flies 60 px on its chain.
        static void CoffinBearerKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int slam = Kit.AddEffect(p, OssivarFx.CoffinSlam, attach: true, destroyOnAnimEnd: true, offsetX: 30f, offsetY: 5f);
            var sl = Kit.Melee(sh, "Slam", "ModOssCoffinSlam", v, 3, slam, 30f).Build();
            // Combo: two coffin slams, then the Pallbearer: two slams running, the second carried forward
            var sl2 = Kit.Melee(sh, "Slam", "ModOssCoffinSlam2", null, 3, slam, 40f).Speed(1.1f).Build();
            var sl3 = Kit.Melee(sh, "Slam", "ModOssCoffinPall", v, 3, slam, 40f, 10, slam, 80f).Repeat(2).Speed(1.2f).Build();
            var wh = new ClipBuilder(sh, "Whirl", "ModOssCoffinWhirl").Once().Repeat(5)
                .Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop").Ev(0, "OssWhirlOn").EvO(0, "AnimSound", v)
                .Ev(-1, "AnimRun").Ev(-1, "OssWhirlEnd").Build();
            BearerWhirl.FlingClip = new ClipBuilder(sh, "Fling", "ModOssCoffinFling").Once().Ev(3, "OssFlingHit").EvO(3, "AnimSound", v)
                .Ev(-1, "AnimRun").Build();
            BearerWhirl.DizzyClip = Loop(sh, "Dizzy", "ModOssCoffinDizzy");
            atk.Clear();
            atk.Add(Kit.Attack(a0, sl, 0.45f, rangeInner: 14f, rangeOuter: 34f));
            atk.Add(Kit.Attack(a0, sl2, 0.45f, rangeInner: 14f, rangeOuter: 36f));
            atk.Add(Kit.Attack(a0, sl3, 2.1f, rangeInner: 14f, rangeOuter: 48f));
            Kit.SetSpecial(p, Kit.Attack(sp, wh, 0f, rangeInner: 0f, rangeOuter: 60f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 15f);
        }

        // Bone Mammoth: a tusk sweep with knockback; Cross Quake splits the floor in a cross. Every footfall jolts the floor.
        static void MammothKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int tusk = Kit.AddEffect(p, OssivarFx.MammothTusk, attach: true, destroyOnAnimEnd: true, offsetX: 20f, offsetY: 15f);
            var tk = Kit.Melee(sh, "Tusk", "ModOssMammothTusk", v, 2, tusk, 30f).Build();
            // Combo: two tusk sweeps, then the Stampede: a lunging sweep, and its feet throw up bone spikes
            var tk2 = Kit.Melee(sh, "Tusk", "ModOssMammothTusk2", null, 2, tusk, 40f).Speed(1.1f).Build();
            var tk3 = Kit.Melee(sh, "Tusk", "ModOssMammothStampede", v, 2, tusk, 90f).Speed(0.85f).Ev(2, "OssFootfall").Ev(4, "OssFootfall").Build();
            var qk = new ClipBuilder(sh, "Quake", "ModOssMammothQuake").Once().Channel(v, 4, "OssCrossQuake").Build();
            var run = new ClipBuilder(sh, "Run", "ModOssMammothRun").Loop().Ev(0, "OssFootfall").Ev(3, "OssFootfall").Build();
            R.Set(p, "m_animationRun", run);
            atk.Clear();
            atk.Add(Kit.Attack(a0, tk, 0.45f, rangeInner: 12f, rangeOuter: 30f));
            atk.Add(Kit.Attack(a0, tk2, 0.45f, rangeInner: 12f, rangeOuter: 32f));
            atk.Add(Kit.Attack(a0, tk3, 2.0f, rangeInner: 12f, rangeOuter: 44f));
            Kit.SetSpecial(p, Kit.Attack(sp, qk, 0f, rangeInner: 0f, rangeOuter: 60f, rangeRetreat: 0f), 7.5f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 18f);
        }

        // Razorback: a tusk slash (may bleed); Skid fires every quill it raised while running, in a fan ahead.
        static void RazorbackKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int slash = Kit.AddEffect(p, OssivarFx.RazorSlash, attach: true, destroyOnAnimEnd: true, offsetX: 15f, offsetY: 16f);
            var sl = Kit.Melee(sh, "Slash", "ModOssRazorSlash", v, 2, slash, 50f).Build();
            // Combo: two tusk slashes, then the Gash: a long lunge that slashes twice
            var sl2 = Kit.Melee(sh, "Slash", "ModOssRazorSlash2", null, 2, slash, 60f).Speed(1.1f).Build();
            var sl3 = Kit.Melee(sh, "Slash", "ModOssRazorGash", v, 2, slash, 120f, 4, slash, 40f).Speed(0.9f).Build();
            var sk = new ClipBuilder(sh, "Skid", "ModOssRazorSkid").Once().AimLock(0).EvF(0, "AnimMove", 220f).Ev(3, "AnimMoveStop")
                .Ev(4, "OssQuillFire").EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            var idles = new exSpriteAnimClip[RazorQuills.Max + 1];
            var runs = new exSpriteAnimClip[RazorQuills.Max + 1];
            for (int q = 0; q <= RazorQuills.Max; q++)
            {
                idles[q] = Loop(sh, q == 0 ? "Idle" : "Idle" + q, "ModOssRazorIdle" + q);
                runs[q] = Loop(sh, q == 0 ? "Run" : "Run" + q, "ModOssRazorRun" + q);
            }
            RazorQuills.Idles = idles; RazorQuills.Runs = runs;
            atk.Clear();
            atk.Add(Kit.Attack(a0, sl, 0.35f, rangeInner: 10f, rangeOuter: 26f));
            atk.Add(Kit.Attack(a0, sl2, 0.35f, rangeInner: 10f, rangeOuter: 28f));
            atk.Add(Kit.Attack(a0, sl3, 1.7f, rangeInner: 10f, rangeOuter: 46f));
            Kit.SetSpecial(p, Kit.Attack(sp, sk, 0f, rangeInner: 30f, rangeOuter: 100f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.55f);
            Strike.Feet(p, n0, 16f);
        }

        // Cerberus: three heads bite on one frame (one hit); Converging Breath sweeps three gas cones in from the sides.
        static void CerberusKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int bite = Kit.AddEffect(p, OssivarFx.CerberusBite, attach: true, destroyOnAnimEnd: true, offsetX: 21f, offsetY: 17f);
            var bt = Kit.Melee(sh, "Bite", "ModOssCerberusBite", v, 3, bite, 30f).Build();
            // Combo: two three-headed bites, then the Frenzy: a lunge and each head bites in turn
            var bt2 = Kit.Melee(sh, "Bite", "ModOssCerberusBite2", null, 3, bite, 40f).Speed(1.1f).Build();
            var bt3 = Kit.Melee(sh, "Bite", "ModOssCerberusFrenzy", v, 2, bite, 90f, 3, bite, 20f, 4, bite, 20f).Speed(0.85f).Build();
            var br = new ClipBuilder(sh, "Breath", "ModOssCerberusBreath").Once().AimLock(1).Ev(2, "OssBreathOuter").EvO(2, "AnimSound", v)
                .Ev(3, "OssBreathMiddle").Ev(9, "OssBreathEnd").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, bt, 0.4f, rangeInner: 10f, rangeOuter: 28f));
            atk.Add(Kit.Attack(a0, bt2, 0.4f, rangeInner: 10f, rangeOuter: 30f));
            atk.Add(Kit.Attack(a0, bt3, 1.9f, rangeInner: 10f, rangeOuter: 42f));
            Kit.SetSpecial(p, Kit.Attack(sp, br, 0f, rangeInner: 16f, rangeOuter: 52f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 17f);
        }

        // Church Grim: a lunging bite; Graveward Lunge runs 60 px through the hero. Undying: once, it rises from its bones.
        static void GrimKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int bite = Kit.AddEffect(p, OssivarFx.GrimBite, attach: true, destroyOnAnimEnd: true, offsetX: 24f, offsetY: 17f);
            int lunge = Kit.AddEffect(p, OssivarFx.GrimLunge, attach: true, destroyOnAnimEnd: true, offsetX: 19f, offsetY: 12f);
            var bt = Kit.Melee(sh, "Bite", "ModOssGrimBite", v, 2, bite, 80f).Build();
            // Combo: two lunging bites, then the Hunt: it runs through him, the lunge and the bite both landing
            var bt2 = Kit.Melee(sh, "Bite", "ModOssGrimBite2", null, 2, bite, 90f).Speed(1.1f).Build();
            var bt3 = Kit.Melee(sh, "Bite", "ModOssGrimHunt", v, 2, lunge, 150f, 4, bite, 40f).Speed(0.9f).Build();
            var ln = new ClipBuilder(sh, "Lunge", "ModOssGrimLunge").Once().AimLock(1).EvF(2, "AnimMove", 250f).Ev(2, "AnimAttack", lunge).EvO(2, "AnimSound", v)
                .Ev(6, "AnimMoveStop").Ev(-1, "AnimRun").Build();
            GrimUndying.FallClip = Once(sh, "Fall", "ModOssGrimFall");
            GrimUndying.HeapClip = Loop(sh, "Heap", "ModOssGrimHeap");
            GrimUndying.RiseClip = Once(sh, "Rise", "ModOssGrimRise");
            atk.Clear();
            atk.Add(Kit.Attack(a0, bt, 0.4f, rangeInner: 12f, rangeOuter: 32f));
            atk.Add(Kit.Attack(a0, bt2, 0.4f, rangeInner: 12f, rangeOuter: 34f));
            atk.Add(Kit.Attack(a0, bt3, 1.8f, rangeInner: 12f, rangeOuter: 56f));
            Kit.SetSpecial(p, Kit.Attack(sp, ln, 0f, rangeInner: 20f, rangeOuter: 66f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 13f);
        }

        // Carrion Saint: sends its perched crows one at a time, or all at once as a wall; bones bring more crows.
        static void SaintKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            var send = new ClipBuilder(sh, "Send", "ModOssSaintSend").Once().AimLock(2).Ev(2, "OssSendCrow").EvO(2, "AnimSound", v).Ev(-1, "AnimRun").Build();
            // Combo: two crows, then a pair sent together
            var send2 = new ClipBuilder(sh, "Send", "ModOssSaintSend2").Once().Speed(1.15f).AimLock(2).Ev(2, "OssSendCrow").Ev(-1, "AnimRun").Build();
            var send3 = new ClipBuilder(sh, "Send", "ModOssSaintSendPair").Once().Speed(0.85f).AimLock(2).Ev(2, "OssSendCrow").Ev(3, "OssSendCrow").EvO(2, "AnimSound", v).Ev(-1, "AnimRun").Build();
            var mur = new ClipBuilder(sh, "Murder", "ModOssSaintMurder").Once().AimLock(3).Ev(3, "OssMurder").EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            var idles = new exSpriteAnimClip[SaintFlock.MaxCrows + 1];
            var runs = new exSpriteAnimClip[SaintFlock.MaxCrows + 1];
            for (int c = 0; c <= SaintFlock.MaxCrows; c++)
            {
                idles[c] = Loop(sh, c == SaintFlock.MaxCrows ? "Idle" : "Idle" + c, "ModOssSaintIdle" + c);
                runs[c] = Loop(sh, c == SaintFlock.MaxCrows ? "Run" : "Run" + c, "ModOssSaintRun" + c);
            }
            SaintFlock.Idles = idles; SaintFlock.Runs = runs;
            atk.Clear();
            atk.Add(Kit.Attack(a0, send, 0.45f, rangeInner: 40f, rangeOuter: 120f, rangeRetreat: 36f));
            atk.Add(Kit.Attack(a0, send2, 0.45f, rangeInner: 40f, rangeOuter: 120f, rangeRetreat: 36f));
            atk.Add(Kit.Attack(a0, send3, 2.0f, rangeInner: 40f, rangeOuter: 120f, rangeRetreat: 36f));
            Kit.SetSpecial(p, Kit.Attack(sp, mur, 0f, rangeInner: 20f, rangeOuter: 80f, rangeRetreat: 20f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
        }

        // The Ossuary: fists slam a ring of spikes; Ribcage shuts the hero in six ribs. It holds up to 3 plates.
        static void OssuaryKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int slam = Kit.AddEffect(p, OssivarFx.OssuarySlam, offsetX: 29f, offsetY: 0.01f);
            Kit.AimReach(p, slam, 8f, 8f);
            var sl = new ClipBuilder(sh, "Slam", "ModOssuarySlam").Once().AimLock(2).Ev(3, "AnimAttack", slam).EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            int slam2 = Kit.AddEffect(p, OssivarFx.OssuarySlam, offsetX: 56f, offsetY: 0.01f);
            // Combo: two spike rings, then the Procession: the spikes run on and ring up again further ahead
            var sl2 = new ClipBuilder(sh, "Slam", "ModOssuarySlam2").Once().Speed(1.1f).AimLock(2).Ev(3, "AnimAttack", slam).Ev(-1, "AnimRun").Build();
            var sl3 = new ClipBuilder(sh, "Slam", "ModOssuaryProcession").Once().Speed(0.85f).AimLock(2).Ev(3, "AnimAttack", slam)
                .Ev(3, "AnimAttack", slam2, 0.18f).EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            var rb = new ClipBuilder(sh, "Rib", "ModOssuaryRib").Once().Channel(v, 2, "OssRibCrack").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sl, 0.45f, rangeInner: 18f, rangeOuter: 44f));
            atk.Add(Kit.Attack(a0, sl2, 0.45f, rangeInner: 18f, rangeOuter: 46f));
            atk.Add(Kit.Attack(a0, sl3, 2.2f, rangeInner: 18f, rangeOuter: 80f));
            Kit.SetSpecial(p, Kit.Attack(sp, rb, 0f, rangeInner: 0f, rangeOuter: 120f, rangeRetreat: 0f), 7.5f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 10f);
        }

        // Marrow Wyrm: a long-necked lunge (may bleed); Neck Lash cocks back, then sweeps the half-circle in front.
        static void WyrmKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int bite = Kit.AddEffect(p, OssivarFx.WyrmBite, attach: true, destroyOnAnimEnd: true, offsetX: 29f, offsetY: 15f);
            int lash = Kit.AddEffect(p, OssivarFx.WyrmLash, attach: true, destroyOnAnimEnd: true, offsetX: 17f, offsetY: 13f);
            var lg = Kit.Melee(sh, "Lunge", "ModOssWyrmLunge", v, 2, bite, 30f).Build();
            // Combo: two long-necked lunges, then the Coil: a lunge whose neck sweeps round after the bite
            var lg2 = Kit.Melee(sh, "Lunge", "ModOssWyrmLunge2", null, 2, bite, 40f).Speed(1.1f).Build();
            var lg3 = Kit.Melee(sh, "Lunge", "ModOssWyrmCoil", v, 2, bite, 60f, 4, lash, 0f).Speed(0.85f).Build();
            var la = new ClipBuilder(sh, "Lash", "ModOssWyrmLash").Once().AimLock(4).Ev(5, "AnimAttack", lash).EvO(5, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, lg, 0.45f, rangeInner: 16f, rangeOuter: 36f));
            atk.Add(Kit.Attack(a0, lg2, 0.45f, rangeInner: 16f, rangeOuter: 38f));
            atk.Add(Kit.Attack(a0, lg3, 2.0f, rangeInner: 16f, rangeOuter: 44f));
            Kit.SetSpecial(p, Kit.Attack(sp, la, 0f, rangeInner: 0f, rangeOuter: 34f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 14f);
        }

        // Carrion Roc: a diving beak stab (may bleed); Airlift flies a friend (or a pile) at the hero and drops it on him.
        static void RocKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int stab = Kit.AddEffect(p, OssivarFx.RocStab, attach: true, destroyOnAnimEnd: true, offsetX: 18f, offsetY: 11f);
            var st = new ClipBuilder(sh, "Stab", "ModOssRocStab").Once().AimLock(1)
                .EvF(2, "AnimMove", 170f).Ev(2, "AnimAttack", stab).EvO(2, "AnimSound", v).Ev(4, "AnimMoveStop").Ev(-1, "AnimRun").Build();
            // Combo: two diving stabs, then the Strafe: it dives through, turns and stabs again
            var st2 = new ClipBuilder(sh, "Stab", "ModOssRocStab2").Once().Speed(1.1f).AimLock(1)
                .EvF(2, "AnimMove", 190f).Ev(2, "AnimAttack", stab).Ev(4, "AnimMoveStop").Ev(-1, "AnimRun").Build();
            var st3 = new ClipBuilder(sh, "Stab", "ModOssRocStrafe").Once().Repeat(2).Speed(1.2f).AimLock(1)
                .EvF(2, "AnimMove", 220f).Ev(2, "AnimAttack", stab).EvO(2, "AnimSound", v).EvF(5, "AnimInputMultiplyFreeFace", 0f)
                .Ev(7, "AnimInputMultiplyStop").EvF(8, "AnimMove", 220f).Ev(8, "AnimAttack", stab).Ev(10, "AnimMoveStop").Ev(-1, "AnimRun").Build();
            var gr = new ClipBuilder(sh, "Grab", "ModOssRocGrab").Once().Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop")
                .Ev(2, "OssGrab").EvO(2, "AnimSound", v).Ev(-1, "OssCarry").HandOff().Build();
            RocAirlift.CarryClip = Loop(sh, "Carry", "ModOssRocCarry");
            RocAirlift.DropClip = new ClipBuilder(sh, "Drop", "ModOssRocDrop").Once().Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, st, 0.4f, rangeInner: 12f, rangeOuter: 38f));
            atk.Add(Kit.Attack(a0, st2, 0.4f, rangeInner: 12f, rangeOuter: 40f));
            atk.Add(Kit.Attack(a0, st3, 1.9f, rangeInner: 12f, rangeOuter: 52f));
            Kit.SetSpecial(p, Kit.Attack(sp, gr, 0f, rangeInner: 30f, rangeOuter: 140f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 12f);
        }

        // Bone Rat (the Priest's minion)
        static void RatKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0];
            int n0 = Strike.Mark(p);
            int bite = Kit.AddEffect(p, OssivarFx.RatBite, attach: true, destroyOnAnimEnd: true, offsetX: 7f, offsetY: 4f);
            var b = Kit.Melee(sh, "Bite", "ModBoneRatBite", null, 2, bite, 60f).Build();
            atk.Clear();
            // the fodder base wanted to bite from 30-80 px; the jaws reach 11
            atk.Add(Kit.Attack(a0, b, a0.m_cooldown, rangeInner: 8f, rangeOuter: 16f, rangeRetreat: 0f));
            Strike.Feet(p, n0, 4f);
            MinionAI.Tune(p, 120f, 10f, 15f, 1.2f, 2f, 1.5f);
            GodArt.UseHitSplat(p, OssivarFx.HitSplat);
        }

        static void LeaveBones(GameObject go, Player p) { Kit.AddDeathSpawn(p, OssivarFx.BonePile); Strike.DeathAtFeet(p); GodArt.UseHitSplat(p, OssivarFx.HitSplat); }

        public static readonly MonsterDef Rat = new MonsterDef
        {
            id = "BoneRat", art = "OssBoneRat", basePrefab = "EnemyTinyRatFodder", health = 1.2f, kit = RatKit
        };

        // Rattlebones -> BoneLancer, OssGravedigger        MarrowHound -> OssGravetusk, OssBarghest
        // CairnCrow -> OssuaryPriest, OssCarrionVulture    BoneLancer -> OssCharnelRider, OssSpinehook
        // OssGravedigger -> OssTombwright, OssCoffinBearer OssGravetusk -> OssBoneMammoth, OssRazorback
        // OssBarghest -> OssCerberus, OssChurchGrim        OssuaryPriest -> OssCarrionSaint, Ossuary
        // OssCarrionVulture -> OssMarrowWyrm, OssCarrionRoc
        public static readonly List<MonsterDef> Monsters = new List<MonsterDef>
        {
            new MonsterDef { id = "Rattlebones", art = "OssRattlebones", basePrefab = "EnemySkeleton", health = 3.5f, evolveCost = 0f,
                             evolveTo = new[] { "BoneLancer", "OssGravedigger" }, kit = RattlebonesKit, customize = LeaveBones },
            new MonsterDef { id = "MarrowHound", art = "OssMarrowHound", basePrefab = "EnemyGiantRat_Fireball", health = 3.5f, speedMult = 1.1f, evolveCost = 0f,
                             evolveTo = new[] { "OssGravetusk", "OssBarghest" }, kit = HoundKit, customize = LeaveBones },
            new MonsterDef { id = "CairnCrow", art = "OssCairnCrow", basePrefab = "EnemyFlyingEye_Dodge", health = 3f, evolveCost = 0f,
                             evolveTo = new[] { "OssuaryPriest", "OssCarrionVulture" }, kit = CrowKit, customize = LeaveBones },
            new MonsterDef { id = "BoneLancer", art = "OssBoneLancer", basePrefab = "EnemyOrc", health = 7f, evolveCost = 2.5f,
                             evolveTo = new[] { "OssCharnelRider", "OssSpinehook" }, kit = LancerKit, customize = LeaveBones },
            new MonsterDef { id = "OssGravedigger", art = "OssGravedigger", basePrefab = "EnemyOrc", health = 6.5f, evolveCost = 2.5f, damageMult = 1.1f,
                             evolveTo = new[] { "OssTombwright", "OssCoffinBearer" }, kit = GravediggerKit, customize = LeaveBones },
            new MonsterDef { id = "OssGravetusk", art = "OssGravetusk", basePrefab = "EnemyScorpion", health = 6.5f, evolveCost = 2.5f, damageMult = 1.2f,
                             evolveTo = new[] { "OssBoneMammoth", "OssRazorback" }, kit = GravetuskKit, customize = LeaveBones },
            new MonsterDef { id = "OssBarghest", art = "OssBarghest", basePrefab = "EnemyGiantRat_Fireball", health = 6f, speedMult = 1.1f, evolveCost = 2.5f, damageMult = 0.9f,
                             evolveTo = new[] { "OssCerberus", "OssChurchGrim" }, kit = BarghestKit, customize = LeaveBones },
            new MonsterDef { id = "OssuaryPriest", art = "OssOssuaryPriest", basePrefab = "EnemyFacelessShaman", health = 6f, evolveCost = 2.5f, damageMult = 1.4f,
                             evolveTo = new[] { "OssCarrionSaint", "Ossuary" }, kit = PriestKit, customize = LeaveBones },
            new MonsterDef { id = "OssCarrionVulture", art = "OssCarrionVulture", basePrefab = "EnemyFlyingEye_Rapidfire", health = 5.5f, evolveCost = 2.5f, damageMult = 1.3f,
                             evolveTo = new[] { "OssMarrowWyrm", "OssCarrionRoc" }, kit = VultureKit, customize = LeaveBones },
            new MonsterDef { id = "OssCharnelRider", art = "OssCharnelRider", basePrefab = "EnemyMinotaur", health = 13.5f, speedMult = 1.05f, evolveCost = 4.5f, damageMult = 1.1f,
                             kit = RiderKit, customize = LeaveBones },
            new MonsterDef { id = "OssSpinehook", art = "OssSpinehook", basePrefab = "EnemyCapraDemon", health = 13f, evolveCost = 4.5f,
                             kit = SpinehookKit, customize = LeaveBones },
            new MonsterDef { id = "OssTombwright", art = "OssTombwright", basePrefab = "EnemyTroll", health = 13.5f, speedMult = 0.95f, evolveCost = 4.5f, damageMult = 1.2f,
                             kit = TombwrightKit, customize = LeaveBones },
            new MonsterDef { id = "OssCoffinBearer", art = "OssCoffinBearer", basePrefab = "EnemyGhoul", health = 14f, speedMult = 0.95f, evolveCost = 4.5f,
                             kit = CoffinBearerKit, customize = LeaveBones },
            new MonsterDef { id = "OssBoneMammoth", art = "OssBoneMammoth", basePrefab = "EnemyMinotaur", health = 14f, speedMult = 0.9f, evolveCost = 4.5f, damageMult = 1.1f,
                             kit = MammothKit, customize = LeaveBones },
            new MonsterDef { id = "OssRazorback", art = "OssRazorback", basePrefab = "EnemyScorpion", health = 12.5f, speedMult = 1.1f, evolveCost = 4.5f,
                             kit = RazorbackKit, customize = LeaveBones },
            new MonsterDef { id = "OssCerberus", art = "OssCerberus", basePrefab = "EnemySmallDragon", health = 13.5f, evolveCost = 4.5f, damageMult = 1.2f,
                             kit = CerberusKit, customize = LeaveBones },
            new MonsterDef { id = "OssChurchGrim", art = "OssChurchGrim", basePrefab = "EnemyGiantRat_Fireball", health = 12.5f, speedMult = 1.15f, evolveCost = 4.5f, damageMult = 0.9f,
                             kit = GrimKit, customize = LeaveBones },
            new MonsterDef { id = "OssCarrionSaint", art = "OssCarrionSaint", basePrefab = "EnemySkeletonPope", health = 12.5f, evolveCost = 4.5f, damageMult = 1.2f,
                             kit = SaintKit, customize = LeaveBones },
            new MonsterDef { id = "Ossuary", art = "OssOssuary", basePrefab = "EnemyTroll", health = 14f, evolveCost = 4.5f,
                             kit = OssuaryKit, customize = LeaveBones },
            new MonsterDef { id = "OssMarrowWyrm", art = "OssMarrowWyrm", basePrefab = "EnemySmallDragon", health = 13f, evolveCost = 4.5f,
                             kit = WyrmKit, customize = LeaveBones },
            new MonsterDef { id = "OssCarrionRoc", art = "OssCarrionRoc", basePrefab = "EnemyBeholder", health = 13f, evolveCost = 4.5f,
                             kit = RocKit, customize = LeaveBones },
        };

        public static readonly GodDef God = new GodDef
        {
            name = "Ossivar",
            text = "Bones crawl home: block a hit",
            flavour = "Every bone is his.\nThey crawl back to him.",
            winText = "THE OSSUARY IS SEALED",
            portraitArt = "DeityOssivar",
            startingMonsters = new[] { "Rattlebones", "MarrowHound", "CairnCrow" },
        };

        /// <summary>Each monster's own mechanic (an <see cref="OssBehaviour"/>) and its pile rules.</summary>
        static OssivarTraits TraitsFor(string id)
        {
            var t = new OssivarTraits();
            switch (id)
            {
                case "Rattlebones": t.Add<RattleSkull>(); break;
                case "MarrowHound": t.healOnBones = true; t.Add<HoundScent>(); break;
                case "CairnCrow": t.Add<CrowPicker>(); break;
                case "OssGravedigger": t.Add<DiggerGrave>(); break;
                case "OssGravetusk": t.Add<TuskCharge>(); break;
                case "OssBarghest": t.Add<BarghestHamstring>(); break;
                case "OssuaryPriest": t.shepherd = true; t.Add<PriestRaise>(); break;
                case "OssCarrionVulture": t.Add<VultureWatch>(); break;
                case "OssCharnelRider": t.Add<RiderUnhorse>(); break;
                case "OssSpinehook": t.Add<SpinehookReel>(); break;
                case "OssTombwright": t.Add<TombStones>(); break;
                case "OssCoffinBearer": t.Add<BearerWhirl>(); break;
                case "OssBoneMammoth": t.Add<MammothQuake>(); break;
                case "OssRazorback": t.Add<RazorQuills>(); break;
                case "OssCerberus": t.Add<CerberusBreath>(); break;
                case "OssChurchGrim": t.Add<GrimUndying>(); break;
                case "OssCarrionSaint": t.pilesToCrows = true; t.Add<SaintFlock>(); break;
                case "Ossuary": t.maxPlates = 3; t.Add<OssuaryRibs>(); break;
                case "OssMarrowWyrm": t.Add<WyrmMarrow>(); break;
                case "OssCarrionRoc": t.Add<RocAirlift>(); break;
            }
            return t;
        }

        static void OnAttackSpawned(Player owner, GameObject fx, GameObject template)
        {
            if (owner == null) return;
            var b = owner.GetComponent<OssBehaviour>();
            if (b != null) b.OnAttackSpawned(fx, template);
        }

        public static void Register()
        {
            OssivarFx.Build();
            foreach (var m in Monsters) MonsterTraits.Register(m.PrefabName, TraitsFor(m.id));
            // the bone plate is also what any monster without plate art of its own wears
            MonsterTraits.DefaultPlateFx = OssivarFx.PlateOrbit;
            MonsterTraits.DefaultPlateBreakFx = OssivarFx.PlateShatter;
            MonsterEvents.AttackSpawned += OnAttackSpawned;

            var rat = MonsterFactory.Build(Rat);
            if (rat != null) OssivarFx.RatSpawner = FxKit.MinionSpawner("ModBoneRatSpawner", rat.gameObject, "FxBonePile", "Rise");
            foreach (var m in Monsters) MonsterFactory.Build(m);
            MonsterFactory.LinkEvolutions(Monsters);
            DeityFactory.Register(God);
            // the gold idol carved in the Marrow King's likeness
            var prev = SlotGods.PortraitFor;
            SlotGods.PortraitFor = (tier, perk) =>
                tier == SlotTier.Gold && perk != null && perk.GetName() == God.name ? SlotArt.Clip("DeityOssIdol", "Idle") : (prev != null ? prev(tier, perk) : null);
            Strike.KeepAllScales();
        }
    }
}
