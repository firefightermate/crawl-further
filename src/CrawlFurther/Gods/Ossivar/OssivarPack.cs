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
            var vo = Kit.Shot(sh, "Volley", "ModOssLancerVolley", 3, v, 0f, s1, s2, s3).Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, th, 1.0f, rangeInner: 18f, rangeOuter: 36f));
            Kit.SetSpecial(p, Kit.Attack(sp, vo, 0f, rangeInner: 40f, rangeOuter: 110f, rangeRetreat: 28f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 12f);
        }

        // Gravedigger: a spade swing (two within 2 s bury the hero to the knees); Unearth digs up two bone piles.
        static void GravediggerKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int spade = Kit.AddEffect(p, OssivarFx.DigSpade, attach: true, destroyOnAnimEnd: true, offsetX: 12f, offsetY: 5f);
            var sd = Kit.Melee(sh, "Spade", "ModOssDigSpade", v, 2, spade, 50f).Build();
            var un = new ClipBuilder(sh, "Unearth", "ModOssUnearth").Once().Channel(v, 5, "OssUnearth").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sd, 1.0f, rangeInner: 10f, rangeOuter: 22f));   // quick enough to land two inside 2 s
            Kit.SetSpecial(p, Kit.Attack(sp, un, 0f, rangeInner: 0f, rangeOuter: 120f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
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
            var ch = new ClipBuilder(sh, "Charge", "ModOssTuskCharge").Once().AimLock(1).Ev(1, "OssChargeOn")
                .EvF(2, "AnimMove", 230f).Ev(2, "AnimAttack", rush).EvO(2, "AnimSound", v)
                .Ev(7, "AnimMoveStop").Ev(7, "OssChargeOff").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, gr, 1.3f, rangeInner: 10f, rangeOuter: 24f));
            Kit.SetSpecial(p, Kit.Attack(sp, ch, 0f, rangeInner: 30f, rangeOuter: 90f, rangeRetreat: 0f), 6f);   // 230 px/s x 0.3 s
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
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
            var pc = new ClipBuilder(sh, "Pounce", "ModOssBarghestPounce").Once().AimLock(1)
                .Ev(2, "AnimStartInvincibility").Ev(2, "OssPounce").EvO(2, "AnimSound", v)
                .Ev(6, "AnimStopInvincibility").Ev(6, "AnimAttack", land).Ev(6, "AnimAttack", dust).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, bt, 1.1f, rangeInner: 10f, rangeOuter: 24f));
            Kit.SetSpecial(p, Kit.Attack(sp, pc, 0f, rangeInner: 30f, rangeOuter: 88f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 9f);
        }

        // Ossuary Priest: a slow homing marrow bolt; Raise stands nearby piles up as Bone Rats. Shepherd: piles come to it.
        static void PriestKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int bolt = Kit.AddEffect(p, OssivarFx.MarrowBolt, offsetX: 12f, offsetY: 12f);
            var b = Kit.Shot(sh, "Bolt", "ModOssPriestBolt", 3, v, 0f, bolt).Build();
            var rs = new ClipBuilder(sh, "Raise", "ModOssPriestRaise").Once().Channel(v, 5, "OssRaise").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, b, 1.6f, rangeInner: 60f, rangeOuter: 120f, rangeRetreat: 45f));
            Kit.SetSpecial(p, Kit.Attack(sp, rs, 0f, rangeInner: 40f, rangeOuter: 200f, rangeRetreat: 40f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
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
            var pl = new ClipBuilder(sh, "Plummet", "ModOssVulturePlummet").Once().Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop")
                .Ev(2, "OssPlummetUp").Ev(4, "OssPlummetDown").Ev(6, "AnimAttack", dive).Ev(6, "OssPlummetLand").EvO(6, "AnimSound", v)
                .Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, rk, 1.2f, rangeInner: 12f, rangeOuter: 34f));
            Kit.SetSpecial(p, Kit.Attack(sp, pl, 0f, rangeInner: 30f, rangeOuter: 150f, rangeRetreat: 30f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
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
            var hp = Kit.Shot(sh, "Harpoon", "ModOssHookHarpoon", 3, v, 0f, harp).Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, rk, 1.4f, rangeInner: 10f, rangeOuter: 26f));
            Kit.SetSpecial(p, Kit.Attack(sp, hp, 0f, rangeInner: 30f, rangeOuter: 100f, rangeRetreat: 24f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 16f);
        }

        // Tombwright: a mallet smash that also knocks over the headstone it hits; Raise Stones puts three in a line at the hero.
        static void TombwrightKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int mal = Kit.AddEffect(p, OssivarFx.MalletSmash, attach: true, destroyOnAnimEnd: true, offsetX: 19f, offsetY: 5f);
            var ml = Kit.Melee(sh, "Mallet", "ModOssTombMallet", v, 3, mal, 30f).Ev(3, "OssMalletKnock").Build();
            var rs = new ClipBuilder(sh, "Raise", "ModOssTombRaise").Once().AimLock(3).Ev(4, "OssRaiseStones").EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, ml, 1.6f, rangeInner: 10f, rangeOuter: 24f));
            Kit.SetSpecial(p, Kit.Attack(sp, rs, 0f, rangeInner: 20f, rangeOuter: 100f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
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
            var wh = new ClipBuilder(sh, "Whirl", "ModOssCoffinWhirl").Once().Repeat(5)
                .Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop").Ev(0, "OssWhirlOn").EvO(0, "AnimSound", v)
                .Ev(-1, "AnimRun").Ev(-1, "OssWhirlEnd").Build();
            BearerWhirl.FlingClip = new ClipBuilder(sh, "Fling", "ModOssCoffinFling").Once().Ev(3, "OssFlingHit").EvO(3, "AnimSound", v)
                .Ev(-1, "AnimRun").Build();
            BearerWhirl.DizzyClip = Loop(sh, "Dizzy", "ModOssCoffinDizzy");
            atk.Clear();
            atk.Add(Kit.Attack(a0, sl, 1.7f, rangeInner: 14f, rangeOuter: 32f));
            Kit.SetSpecial(p, Kit.Attack(sp, wh, 0f, rangeInner: 0f, rangeOuter: 60f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 15f);
        }

        // Bone Mammoth: a tusk sweep with knockback; Cross Quake splits the floor in a cross. Every footfall jolts the floor.
        static void MammothKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int tusk = Kit.AddEffect(p, OssivarFx.MammothTusk, attach: true, destroyOnAnimEnd: true, offsetX: 20f, offsetY: 15f);
            var tk = Kit.Melee(sh, "Tusk", "ModOssMammothTusk", v, 2, tusk, 30f).Build();
            var qk = new ClipBuilder(sh, "Quake", "ModOssMammothQuake").Once().Channel(v, 4, "OssCrossQuake").Build();
            var run = new ClipBuilder(sh, "Run", "ModOssMammothRun").Loop().Ev(0, "OssFootfall").Ev(3, "OssFootfall").Build();
            R.Set(p, "m_animationRun", run);
            atk.Clear();
            atk.Add(Kit.Attack(a0, tk, 1.5f, rangeInner: 12f, rangeOuter: 28f));
            Kit.SetSpecial(p, Kit.Attack(sp, qk, 0f, rangeInner: 0f, rangeOuter: 60f, rangeRetreat: 0f), 7.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 18f);
        }

        // Razorback: a tusk slash (may bleed); Skid fires every quill it raised while running, in a fan ahead.
        static void RazorbackKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int slash = Kit.AddEffect(p, OssivarFx.RazorSlash, attach: true, destroyOnAnimEnd: true, offsetX: 15f, offsetY: 16f);
            var sl = Kit.Melee(sh, "Slash", "ModOssRazorSlash", v, 2, slash, 50f).Build();
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
            atk.Add(Kit.Attack(a0, sl, 1.2f, rangeInner: 10f, rangeOuter: 24f));
            Kit.SetSpecial(p, Kit.Attack(sp, sk, 0f, rangeInner: 30f, rangeOuter: 100f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 16f);
        }

        // Cerberus: three heads bite on one frame (one hit); Converging Breath sweeps three gas cones in from the sides.
        static void CerberusKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int bite = Kit.AddEffect(p, OssivarFx.CerberusBite, attach: true, destroyOnAnimEnd: true, offsetX: 21f, offsetY: 17f);
            var bt = Kit.Melee(sh, "Bite", "ModOssCerberusBite", v, 3, bite, 30f).Build();
            var br = new ClipBuilder(sh, "Breath", "ModOssCerberusBreath").Once().AimLock(1).Ev(2, "OssBreathOuter").EvO(2, "AnimSound", v)
                .Ev(3, "OssBreathMiddle").Ev(9, "OssBreathEnd").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, bt, 1.4f, rangeInner: 10f, rangeOuter: 26f));
            Kit.SetSpecial(p, Kit.Attack(sp, br, 0f, rangeInner: 16f, rangeOuter: 52f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
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
            var ln = new ClipBuilder(sh, "Lunge", "ModOssGrimLunge").Once().AimLock(1).EvF(2, "AnimMove", 250f).Ev(2, "AnimAttack", lunge).EvO(2, "AnimSound", v)
                .Ev(6, "AnimMoveStop").Ev(-1, "AnimRun").Build();
            GrimUndying.FallClip = Once(sh, "Fall", "ModOssGrimFall");
            GrimUndying.HeapClip = Loop(sh, "Heap", "ModOssGrimHeap");
            GrimUndying.RiseClip = Once(sh, "Rise", "ModOssGrimRise");
            atk.Clear();
            atk.Add(Kit.Attack(a0, bt, 1.3f, rangeInner: 12f, rangeOuter: 30f));
            Kit.SetSpecial(p, Kit.Attack(sp, ln, 0f, rangeInner: 20f, rangeOuter: 66f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 13f);
        }

        // Carrion Saint: sends its perched crows one at a time, or all at once as a wall; bones bring more crows.
        static void SaintKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            var send = new ClipBuilder(sh, "Send", "ModOssSaintSend").Once().AimLock(2).Ev(2, "OssSendCrow").EvO(2, "AnimSound", v).Ev(-1, "AnimRun").Build();
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
            atk.Add(Kit.Attack(a0, send, 1.5f, rangeInner: 40f, rangeOuter: 120f, rangeRetreat: 36f));
            Kit.SetSpecial(p, Kit.Attack(sp, mur, 0f, rangeInner: 20f, rangeOuter: 80f, rangeRetreat: 20f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
        }

        // The Ossuary: fists slam a ring of spikes; Ribcage shuts the hero in six ribs. It holds up to 3 plates.
        static void OssuaryKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int slam = Kit.AddEffect(p, OssivarFx.OssuarySlam, offsetX: 29f, offsetY: 0.01f);
            Kit.AimReach(p, slam, 8f, 8f);
            var sl = new ClipBuilder(sh, "Slam", "ModOssuarySlam").Once().AimLock(2).Ev(3, "AnimAttack", slam).EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            var rb = new ClipBuilder(sh, "Rib", "ModOssuaryRib").Once().Channel(v, 2, "OssRibCrack").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sl, 1.6f, rangeInner: 18f, rangeOuter: 42f));
            Kit.SetSpecial(p, Kit.Attack(sp, rb, 0f, rangeInner: 0f, rangeOuter: 120f, rangeRetreat: 0f), 7.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
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
            var la = new ClipBuilder(sh, "Lash", "ModOssWyrmLash").Once().AimLock(4).Ev(5, "AnimAttack", lash).EvO(5, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, lg, 1.5f, rangeInner: 16f, rangeOuter: 34f));
            Kit.SetSpecial(p, Kit.Attack(sp, la, 0f, rangeInner: 0f, rangeOuter: 34f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
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
            var gr = new ClipBuilder(sh, "Grab", "ModOssRocGrab").Once().Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop")
                .Ev(2, "OssGrab").EvO(2, "AnimSound", v).Ev(-1, "OssCarry").HandOff().Build();
            RocAirlift.CarryClip = Loop(sh, "Carry", "ModOssRocCarry");
            RocAirlift.DropClip = new ClipBuilder(sh, "Drop", "ModOssRocDrop").Once().Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, st, 1.3f, rangeInner: 12f, rangeOuter: 36f));
            Kit.SetSpecial(p, Kit.Attack(sp, gr, 0f, rangeInner: 30f, rangeOuter: 140f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
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
