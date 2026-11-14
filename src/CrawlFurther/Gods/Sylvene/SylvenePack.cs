using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    using CrawlFurther.Art;
    using CrawlFurther.Gods;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;
    using CrawlFurther.Content.Gods.Ossivar;

    /// <summary>
    /// Sylvene, the Rot Orchard: things that grow, ripen and rot. A dying Sylvene monster drops a seed that ripens into a
    /// pod (the god's perk, <see cref="SeedFx"/>), and every monster works the orchard its own way through its signature
    /// (a <see cref="SylveneBehaviour"/>). Offsets below are the sprites' sync points (art/out_sylvene/TIMING.md), x forward,
    /// y up.
    /// </summary>
    public static class SylvenePack
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
        // Sporeling: a short spore puff; Scatter shakes two seeds out of its cap. Signature: SporelingTend.
        static void SporelingKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int puff = Kit.AddEffect(p, SylveneFx.SporePuff, offsetX: 9f, offsetY: 7f);   // spores burst from the gills at (9, -7)
            var pf = Kit.Shot(sh, "Puff", "ModSporelingPuff", 2, v, 0f, puff).Build();
            var sc = Special(sh, "Scatter", "ModSporelingScatter").Ev(3, "ModSowSeeds").EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            // the cloud drifts ~13 px and is 16 wide: it reaches about 30 px
            atk.Add(Kit.Attack(a0, pf, 1.3f, rangeInner: 10f, rangeOuter: 28f));
            Kit.SetSpecial(p, Kit.Attack(sp, sc, 0f, rangeInner: 0f, rangeOuter: 120f, rangeRetreat: 20f), 5.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 7f);
        }

        // Thornbiter: a vine whip reaching 26 px; Root Run sends roots racing at the hero that leave a seed where they stop.
        static void ThornbiterKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int lash = Kit.AddEffect(p, SylveneFx.ThornLash, attach: true, destroyOnAnimEnd: true, offsetX: 15f, offsetY: 9f);   // bud at (25, -7)
            int run = Kit.AddEffect(p, SylveneFx.TaprootRunner, offsetX: 10f, offsetY: 0.01f);   // roots break out at (10, 0)
            var wh = Kit.Melee(sh, "Whip", "ModThornbiterWhip", v, 3, lash, 20f).Build();
            var rr = Kit.Shot(sh, "RootRun", "ModThornbiterRootRun", 2, v, 0f, run).Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, wh, 1.2f, rangeInner: 8f, rangeOuter: 24f));
            // 170 px/s for 0.6 s: about 100 px of roots
            Kit.SetSpecial(p, Kit.Attack(sp, rr, 0f, rangeInner: 30f, rangeOuter: 95f, rangeRetreat: 0f), 5.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 9f);
        }

        // Rotfly: a spit that seeds the floor when it misses; Buzz Bomb dives at the hero, bursts a puff on him and climbs back.
        static void RotflyKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int glob = Kit.AddEffect(p, SylveneFx.SpitGlob, offsetX: 9f, offsetY: 10f);   // mouth (9, -10)
            int burst = Kit.AddEffect(p, SylveneFx.DivePuff, offsetX: 6f, offsetY: 0.01f, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            var spit = Kit.Shot(sh, "Spit", "ModRotflySpit", 2, v, 0f, glob).Build();
            var dive = new ClipBuilder(sh, "Dive", "ModRotflyDive").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff")
                .EvF(2, "AnimMoveStick", 240f).EvO(2, "AnimSound", v).Ev(4, "AnimMoveStop").Ev(4, "AnimAttack", burst)
                .EvF(5, "ModSylRecoil", 150f).Ev(-1, "AnimRun").Build();
            atk.Clear();
            // the glob flies 170 px/s for 0.55 s: about 90 px
            atk.Add(Kit.Attack(a0, spit, 1.3f, rangeInner: 40f, rangeOuter: 80f, rangeRetreat: 30f));
            // 240 px/s for 0.12 s, then the puff: a dive of about 30 px
            Kit.SetSpecial(p, Kit.Attack(sp, dive, 0f, rangeInner: 10f, rangeOuter: 38f, rangeRetreat: 0f), 5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 10f);
        }

        // ---------------------------------------------------------------------------------------------- tier 2
        // Spore Husk: a club smash that rings the floor (and shakes ripe pods loose: HuskShake); Spore Belch, a wide cone.
        static void SporeHuskKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int club = Kit.AddEffect(p, SylveneFx.HuskClub, attach: true, destroyOnAnimEnd: true, offsetX: 15f, offsetY: 4f);   // club head (17, -1)
            int puff = Kit.AddEffect(p, SylveneFx.SporePuff, offsetX: 17f, offsetY: 3f);
            int ring = Kit.AddEffect(p, SylveneFx.ShakeRing, offsetX: 17f, offsetY: 0.01f, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            var belch = new List<int>();
            foreach (var a in new[] { -24f, 0.01f, 24f }) belch.Add(Kit.AddEffect(p, SylveneFx.BelchCloud, offsetX: 9f, offsetY: 14f, angle: a));
            // Combo: two club smashes that each burst a spore puff, then the Groundbreaker: the floor rings, ripe pods
            // shake loose and two seeds jump out of the cracks ahead
            var sm1 = Kit.Melee(sh, "Smash", "ModHuskSmash", v, 3, club, 30f).Ev(3, "AnimAttack", puff).Build();
            var sm2 = Kit.Melee(sh, "Smash", "ModHuskSmash2", null, 3, club, 40f).Ev(3, "AnimAttack", puff).Build();
            var sm3 = Kit.Melee(sh, "Smash", "ModHuskGroundbreaker", v, 3, club, 50f).Speed(0.85f).Ev(3, "AnimAttack", puff).Ev(3, "AnimAttack", ring)
                .Ev(3, "ModSylShake").Ev(4, "ModSylHuskSow").Build();
            var bl = Kit.Shot(sh, "Belch", "ModHuskBelch", 3, v, 0.03f, belch.ToArray()).Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sm1, 0.35f, rangeInner: 10f, rangeOuter: 26f));
            atk.Add(Kit.Attack(a0, sm2, 0.35f, rangeInner: 10f, rangeOuter: 28f));
            atk.Add(Kit.Attack(a0, sm3, 1.6f, rangeInner: 10f, rangeOuter: 30f));
            Kit.SetSpecial(p, Kit.Attack(sp, bl, 0f, rangeInner: 10f, rangeOuter: 45f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.55f);
            Strike.Feet(p, n0, 12f);
        }

        // Bloom Witch: a piercing pollen lance; Graft grows pods onto her kin's heads and her own. Signature: WitchGraft.
        static void BloomWitchKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int lance = Kit.AddEffect(p, SylveneFx.PollenLance, offsetX: 9f, offsetY: 15f);   // palm (9, -15)
            var bouquet = new List<int>();
            foreach (var a in new[] { -13f, 0.01f, 13f }) bouquet.Add(Kit.AddEffect(p, SylveneFx.LanceBloom, offsetX: 9f, offsetY: 15f, angle: a));
            // Combo: two lances, then the Bouquet: three lances in a fan that each bloom into a spore puff where they end
            var ln = Kit.Shot(sh, "Lance", "ModBloomLance", 2, v, 0f, lance).Build();
            var ln2 = Kit.Shot(sh, "Lance", "ModBloomLance2", 2, null, 0f, lance).Speed(1.15f).Build();
            var bq = Kit.Shot(sh, "Lance", "ModBloomBouquet", 2, v, 0.04f, bouquet.ToArray()).Speed(0.85f).Build();
            var gr = Special(sh, "Graft", "ModBloomGraft").Ev(4, "ModSylGraft").EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, ln, 0.4f, rangeInner: 50f, rangeOuter: 120f, rangeRetreat: 40f));
            atk.Add(Kit.Attack(a0, ln2, 0.4f, rangeInner: 50f, rangeOuter: 120f, rangeRetreat: 40f));
            atk.Add(Kit.Attack(a0, bq, 1.8f, rangeInner: 40f, rangeOuter: 110f, rangeRetreat: 40f));
            Kit.SetSpecial(p, Kit.Attack(sp, gr, 0f, rangeInner: 0f, rangeOuter: 160f, rangeRetreat: 30f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 15f);
        }

        // Bramble Knight: two sweeps, the second planting a thorn patch at its tip; Overgrow bursts four patches round it.
        static void BrambleKnightKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            var like = Kit.Effects(p)[0];
            int n0 = Strike.Mark(p);
            int s1 = Kit.AddEffect(p, SylveneFx.ThornSwipeA, attach: true, offsetX: 2f, offsetY: 10f, like: like);   // tip (21, -9)
            int s2 = Kit.AddEffect(p, SylveneFx.ThornSwipeB, attach: true, offsetX: 4f, offsetY: 6f, like: like);    // up from the floor, tip (20, -2)
            int tip = Kit.AddEffect(p, SylveneFx.SweepPatch, offsetX: 22f, offsetY: 0.01f);
            var patches = new List<int>();
            foreach (var o in new[] { new Vector2(-16f, 6f), new Vector2(-16f, -8f), new Vector2(17f, 6f), new Vector2(17f, -8f) })
                patches.Add(Kit.AddEffect(p, SylveneFx.OvergrowPatch, offsetX: o.x, offsetY: o.y, spawnPoint: DamageEffectData.eSpawnPoint.Position));
            int l1 = Kit.AddEffect(p, SylveneFx.SweepPatch, offsetX: 34f, offsetY: 0.01f);
            int l2 = Kit.AddEffect(p, SylveneFx.SweepPatch, offsetX: 48f, offsetY: 0.01f);
            // Combo: the two-cut sweep, then the Briar Drive: a long lunge through both cuts that drives a line of three
            // thorn patches into the floor ahead
            var sw = Kit.Melee(sh, "Sweep", "ModBrambleSweep", v, 2, s1, 50f, 4, s2, 30f).Build();
            var dr = Kit.Melee(sh, "Sweep", "ModBrambleDrive", v, 2, s1, 110f, 4, s2, 60f).Speed(0.9f)
                .Ev(4, "AnimAttack", tip).Ev(4, "AnimAttack", l1, 0.07f).Ev(4, "AnimAttack", l2, 0.14f).Build();
            var og = Special(sh, "Overgrow", "ModBrambleOvergrow").EvO(3, "AnimSound", v);
            for (int i = 0; i < patches.Count; i++) og.Ev(4, "AnimAttack", patches[i], i * 0.05f);
            og.Ev(-1, "AnimRun");
            atk.Clear();
            atk.Add(Kit.Attack(a0, sw, 0.4f, rangeInner: 10f, rangeOuter: 26f));
            atk.Add(Kit.Attack(a0, dr, 1.6f, rangeInner: 14f, rangeOuter: 40f));
            Kit.SetSpecial(p, Kit.Attack(sp, og.Build(), 0f, rangeInner: 0f, rangeOuter: 30f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.55f);
            Strike.Feet(p, n0, 10f);
        }

        // Strangler Vine: a lunging bite; Lasso slings a pod or seed at the hero (Lash with none near). Signature: StranglerSling.
        static void StranglerKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int bite = Kit.AddEffect(p, SylveneFx.StranglerBite, attach: true, destroyOnAnimEnd: true, offsetX: 20f, offsetY: 6f);   // jaws (24, -6)
            int coil = Kit.AddEffect(p, SylveneFx.Constrict, attach: true, destroyOnAnimEnd: true, offsetX: 20f, offsetY: 6f);
            // Combo: two bites, then the Constrict: a long lunge whose coils hold the hero where he stands
            var bt = Kit.Melee(sh, "Bite", "ModSylStranglerBite", v, 3, bite, 30f).Build();
            var bt2 = Kit.Melee(sh, "Bite", "ModSylStranglerBite2", null, 3, bite, 40f).Speed(1.15f).Build();
            var cn = Kit.Melee(sh, "Bite", "ModSylStranglerConstrict", v, 3, coil, 75f).Speed(0.85f).Build();
            var la = Special(sh, "Lasso", "ModSylStranglerLasso").EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(3, "ModSylCatch")
                .EvO(7, "AnimSound", v).Ev(7, "ModSylSling").Ev(-1, "AnimInputMultiplyStop").Ev(-1, "AnimRun").Build();
            var ls = Special(sh, "Lash", "ModSylStranglerLash").EvF(0, "AnimInputMultiplyFreeFace", 0f)
                .EvO(3, "AnimSound", v).Ev(3, "ModSylLash").Ev(-1, "AnimInputMultiplyStop").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, bt, 0.35f, rangeInner: 10f, rangeOuter: 28f));
            atk.Add(Kit.Attack(a0, bt2, 0.35f, rangeInner: 10f, rangeOuter: 30f));
            atk.Add(Kit.Attack(a0, cn, 1.6f, rangeInner: 12f, rangeOuter: 42f));
            // a pod slung at 190 px/s: up to 110 px; the lash reaches about 60
            Kit.SetSpecial(p, Kit.Attack(sp, ls, 0f, rangeInner: 20f, rangeOuter: 60f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.55f);
            Strike.Feet(p, n0, 12f);
            StranglerSling.LassoClip = la;
            StranglerSling.LashClip = ls;
        }

        // Gall Wasp: needles that plant fast seeds where they land; Dart darts through the hero dropping two.
        static void GallWaspKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int needle = Kit.AddEffect(p, SylveneFx.GallNeedle, offsetX: 9f, offsetY: 5f);   // the needle's tip (9, -5)
            int nl = Kit.AddEffect(p, SylveneFx.NeedlePlain, offsetX: 9f, offsetY: 5f, angle: -9f);
            int nr = Kit.AddEffect(p, SylveneFx.NeedlePlain, offsetX: 9f, offsetY: 5f, angle: 9f);
            int dash = Kit.AddEffect(p, SylveneFx.WaspDash, attach: true, destroyOnAnimEnd: true, offsetX: 2f, offsetY: 10f);
            int s1 = Kit.AddEffect(p, SylveneFx.SeedFast, offsetX: -4f, offsetY: 0.01f, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            int s2 = Kit.AddEffect(p, SylveneFx.SeedFast, offsetX: -4f, offsetY: 0.01f, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            // a volley: three needles a beat apart, the middle one sowing a fast seed where it lands
            var nd = Kit.Shot(sh, "Needle", "ModWaspNeedle", 2, v, 0.07f, nl, needle, nr).Build();
            var dt = new ClipBuilder(sh, "Dart", "ModWaspDart").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(1, "AnimInputMultiplyStop").Ev(1, "AnimInputOff")
                .EvF(2, "AnimMoveStick", 220f).Ev(2, "AnimAttack", dash).Ev(2, "AnimAttack", s1).EvO(2, "AnimSound", v)
                .Ev(4, "AnimAttack", s2).Ev(5, "AnimMoveStop").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, nd, 1.4f, rangeInner: 40f, rangeOuter: 90f, rangeRetreat: 35f));
            // 220 px/s for 0.18 s: about 40 px of dart, through a hero up to 45 px away
            Kit.SetSpecial(p, Kit.Attack(sp, dt, 0f, rangeInner: 12f, rangeOuter: 45f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 6f);
        }

        // Bloatfly: three bile gobs in a short cone; Bile Rain flies over the hero and retches straight down. Signature: BloatflyRain.
        static void BloatflyKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            var gobs = new List<int>();
            foreach (var a in new[] { -16f, 0.01f, 16f }) gobs.Add(Kit.AddEffect(p, SylveneFx.BileDrop, offsetX: 10f, offsetY: 14f, angle: a));
            int heave = Kit.AddEffect(p, SylveneFx.BileLob, offsetX: 10f, offsetY: 14f);
            // Combo: two retches, then the Heave: one fat glob that bursts into five gobs where it lands
            var rt = Kit.Shot(sh, "Retch", "ModSylBloatRetch", 2, v, 0f, gobs.ToArray()).Build();
            var rt2 = Kit.Shot(sh, "Retch", "ModSylBloatRetch2", 2, null, 0f, gobs.ToArray()).Speed(1.15f).Build();
            var hv = Kit.Shot(sh, "Retch", "ModSylBloatHeave", 3, v, 0f, heave).Speed(0.8f).Build();
            var rain = Special(sh, "Rain", "ModSylBloatRain").Ev(0, "ModSylRainRise").EvO(2, "AnimSound", v)
                .Ev(2, "AnimInputOn").EvF(2, "AnimInputMultiply", 0.5f);
            for (int f = 2; f <= 7; f++) rain.Ev(f, "ModSylRain");
            rain.Ev(8, "AnimInputMultiplyStop").Ev(8, "AnimInputOff").Ev(-1, "AnimRun");
            atk.Clear();
            // 190 px/s for 0.32 s: about 60 px
            atk.Add(Kit.Attack(a0, rt, 0.45f, rangeInner: 18f, rangeOuter: 55f, rangeRetreat: 15f));
            atk.Add(Kit.Attack(a0, rt2, 0.45f, rangeInner: 18f, rangeOuter: 55f, rangeRetreat: 15f));
            atk.Add(Kit.Attack(a0, hv, 1.8f, rangeInner: 30f, rangeOuter: 75f, rangeRetreat: 20f));
            Kit.SetSpecial(p, Kit.Attack(sp, rain.Build(), 0f, rangeInner: 0f, rangeOuter: 50f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 14f);
        }

        // ---------------------------------------------------------------------------------------------- tier 3
        // Briar Behemoth: a tusk hook; a 70 px charge that ends with its bush swinging in. Signature: BehemothBush.
        static void BriarBehemothKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int gore = Kit.AddEffect(p, SylveneFx.BehemothGore, attach: true, offsetX: 10f, offsetY: 12f);   // tusks sweep x 18..26
            int ram = Kit.AddEffect(p, SylveneFx.BehemothRam, attach: true, destroyOnAnimEnd: true, offsetX: 12f, offsetY: 9f);
            // Combo: two tusk hooks, then the Bush Whip: a third hook and the bush it drags swings round after it
            var hk = Kit.Melee(sh, "Hook", "ModBehemothHook", v, 2, gore, 40f).Build();
            var hk2 = Kit.Melee(sh, "Hook", "ModBehemothHook2", null, 2, gore, 50f).Speed(1.1f).Build();
            var hk3 = Kit.Melee(sh, "Hook", "ModBehemothBushWhip", v, 2, gore, 60f).Ev(4, "ModSylBushWhip").Build();
            var ch = new ClipBuilder(sh, "Charge", "ModBehemothCharge").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff")
                .EvF(3, "AnimMoveStick", 240f).Ev(3, "AnimAttack", ram).EvO(3, "AnimSound", v)
                .Ev(8, "AnimMoveStop").Ev(8, "ModSylBushSlam").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, hk, 0.4f, rangeInner: 12f, rangeOuter: 32f));
            atk.Add(Kit.Attack(a0, hk2, 0.4f, rangeInner: 12f, rangeOuter: 34f));
            atk.Add(Kit.Attack(a0, hk3, 1.9f, rangeInner: 12f, rangeOuter: 36f));
            // 240 px/s with drag over 0.3 s: about 70 px
            Kit.SetSpecial(p, Kit.Attack(sp, ch, 0f, rangeInner: 25f, rangeOuter: 75f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.55f);
            Strike.Feet(p, n0, 12f);
        }

        // Briar Champion: a lance thrust and a planted lunge, one pair of clips per lance length. Signature: ChampionLance.
        static void BriarChampionKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            var thrusts = new List<AttackData>();
            AttackData lunge0 = null;
            for (int k = 0; k < 4; k++)
            {
                string sfx = k == 0 ? "" : k.ToString();
                float len = ChampionLance.LanceLength(k);
                int th = Kit.AddEffect(p, SylveneFx.Lance[k], attach: true, destroyOnAnimEnd: true, offsetX: 12f + len * 0.5f, offsetY: 15f);
                int lu = Kit.AddEffect(p, SylveneFx.Lunge[k], attach: true, destroyOnAnimEnd: true, offsetX: 14f + (len + 6f) * 0.5f, offsetY: 14f);
                var tc = Kit.Melee(sh, "Thrust" + sfx, "ModSylChampThrust" + sfx, v, 2, th, 25f).Build();
                var lc = Special(sh, "Lunge" + sfx, "ModSylChampLunge" + sfx).EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(3, "AnimInputMultiplyStop")
                    .EvF(4, "AnimMoveStick", 200f).Ev(4, "AnimAttack", lu).EvO(4, "AnimSound", v).Ev(5, "AnimMoveStop").Ev(-1, "AnimRun").Build();
                thrusts.Add(Kit.Attack(a0, tc, 1.5f, rangeInner: 10f, rangeOuter: 14f + len));
                if (k == 0) lunge0 = Kit.Attack(sp, lc, 0f, rangeInner: 20f, rangeOuter: 34f + len, rangeRetreat: 0f);
                ChampionLance.Lunge[k] = lc;
                ChampionLance.Idle[k] = k == 0 ? null : Looped(sh, "Idle" + sfx, "ModSylChampIdle" + sfx);
                ChampionLance.Run[k] = k == 0 ? null : Looped(sh, "Run" + sfx, "ModSylChampRun" + sfx);
            }
            atk.Clear();
            atk.AddRange(thrusts);
            Kit.SetSpecial(p, lunge0, 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 15f);
        }

        // Puffball Brute: a fist slam in a spore ring; Bounce flattens, bounces at the hero and lands in a ring. Signature: PuffballRebound.
        static void PuffballKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int ring = Kit.AddEffect(p, SylveneFx.PuffRing, offsetX: 16f, offsetY: 0.01f, spawnPoint: DamageEffectData.eSpawnPoint.Position);   // fists land at (13, -1)
            int land = Kit.AddEffect(p, SylveneFx.PuffLand, offsetX: 0.01f, offsetY: 0.01f, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            int roll = Kit.AddEffect(p, SylveneFx.PuffRoll, attach: true, destroyOnAnimEnd: true, offsetX: 0.01f, offsetY: 0.01f, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            int ring2 = Kit.AddEffect(p, SylveneFx.PuffRing, offsetX: 48f, offsetY: 0.01f, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            // Combo: two slams, then the Aftershock: the slam's ring rolls on and a second ring bursts up further ahead
            var sl = Kit.Melee(sh, "Slam", "ModSylPuffSlam", v, 2, ring, 15f).Build();
            var sl2 = Kit.Melee(sh, "Slam", "ModSylPuffSlam2", null, 2, ring, 25f).Speed(1.1f).Build();
            var sl3 = Kit.Melee(sh, "Slam", "ModSylPuffAftershock", v, 2, ring, 30f).Speed(0.85f).Ev(2, "AnimAttack", ring2, 0.18f).Build();
            var bn = new ClipBuilder(sh, "Bounce", "ModSylPuffBounce").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(0, "AnimMoveStop").Ev(2, "AnimInputMultiplyStop")
                .Ev(2, "AnimStartInvincibility").EvF(2, "AnimMoveStick", 230f).EvO(2, "AnimSound", v).Ev(2, "AnimAttack", roll)
                .Ev(6, "AnimMoveStop").Ev(6, "AnimStopInvincibility").Ev(6, "AnimAttack", land).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sl, 0.45f, rangeInner: 8f, rangeOuter: 40f));
            atk.Add(Kit.Attack(a0, sl2, 0.45f, rangeInner: 8f, rangeOuter: 40f));
            atk.Add(Kit.Attack(a0, sl3, 1.9f, rangeInner: 8f, rangeOuter: 70f));
            // 230 px/s through the 0.3 s in the air: about 50 px
            Kit.SetSpecial(p, Kit.Attack(sp, bn, 0f, rangeInner: 20f, rangeOuter: 55f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 12f);
            PuffballRebound.SquashClip = Once(sh, "WallSquash", "ModSylPuffSquash");
        }

        // Cordyceps Saint: a long spine flick; Infect stalks its kin (or itself) so they fight on after death. Signature: CordycepsInfect.
        static void CordycepsKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int spine = Kit.AddEffect(p, SylveneFx.Spine, offsetX: 11f, offsetY: 22f);   // fingers (11, -22)
            // Infest: three spore spines fanned at the hero from the stalks on its back (-6, -30)
            int s0 = Kit.AddEffect(p, SylveneFx.SporeSpine, offsetX: -2f, offsetY: 30f, angle: -16f);
            int s1 = Kit.AddEffect(p, SylveneFx.SporeSpine, offsetX: -2f, offsetY: 30f);
            int s2 = Kit.AddEffect(p, SylveneFx.SporeSpine, offsetX: -2f, offsetY: 30f, angle: 16f);
            int vl = Kit.AddEffect(p, SylveneFx.Spine, offsetX: 11f, offsetY: 22f, angle: -10f);
            int vr = Kit.AddEffect(p, SylveneFx.Spine, offsetX: 11f, offsetY: 22f, angle: 10f);
            // Combo: two flicks, then a volley of three spines a beat apart
            var fl = Kit.Shot(sh, "Flick", "ModSylCordFlick", 2, v, 0f, spine).Build();
            var fl2 = Kit.Shot(sh, "Flick", "ModSylCordFlick2", 2, null, 0f, spine).Speed(1.15f).Build();
            var vo = Kit.Shot(sh, "Flick", "ModSylCordVolley", 2, v, 0.08f, vl, spine, vr).Speed(0.85f).Build();
            var inf = new ClipBuilder(sh, "Infect", "ModSylCordInfect").Once().Ev(0, "AnimMoveStop").EvF(0, "AnimInputMultiplyFreeFace", 0f)
                .Ev(3, "AnimInputMultiplyStop").Ev(3, "AnimInputOff")
                .Ev(4, "AnimAttack", s0).Ev(4, "AnimAttack", s1).Ev(4, "AnimAttack", s2)
                .Ev(4, "ModSylInfect").EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, fl, 0.4f, rangeInner: 45f, rangeOuter: 120f, rangeRetreat: 40f));
            atk.Add(Kit.Attack(a0, fl2, 0.4f, rangeInner: 45f, rangeOuter: 120f, rangeRetreat: 40f));
            atk.Add(Kit.Attack(a0, vo, 1.9f, rangeInner: 40f, rangeOuter: 110f, rangeRetreat: 40f));
            Kit.SetSpecial(p, Kit.Attack(sp, inf, 0f, rangeInner: 30f, rangeOuter: 110f, rangeRetreat: 20f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 22f);
        }

        // Rot Mother: roots erupt under the hero twice; Sprouting bursts three Sprouts up round him. Signature: MotherFeed.
        static void RotMotherKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int e1 = Kit.AddEffect(p, SylveneFx.RootEruption, spawnPoint: DamageEffectData.eSpawnPoint.ClosestEnemy, offsetY: -2f);
            int e2 = Kit.AddEffect(p, SylveneFx.RootEruption, spawnPoint: DamageEffectData.eSpawnPoint.ClosestEnemy, offsetY: 2f);
            Kit.Effects(p)[e2].m_offsetX = new MinMaxRange(-8f, 8f);
            var rise = new List<int>();
            foreach (var o in new[] { new Vector2(-20f, 6f), new Vector2(20f, 6f), new Vector2(0.01f, -16f) })
            {
                rise.Add(Kit.AddEffect(p, SylveneFx.SproutRise, offsetX: o.x, offsetY: o.y, spawnPoint: DamageEffectData.eSpawnPoint.ClosestEnemy));
                rise.Add(Kit.AddEffect(p, SylveneFx.SproutSpawner, offsetX: o.x, offsetY: o.y, spawnPoint: DamageEffectData.eSpawnPoint.ClosestEnemy));
            }
            // the second eruption follows the first by 0.4 s (Erupt frames 2 and 4)
            var er = new ClipBuilder(sh, "Erupt", "ModRotMotherErupt").Once().Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop").Ev(2, "AnimAttack", e1).EvO(2, "AnimSound", v).Ev(4, "AnimAttack", e2).Ev(-1, "AnimRun").Build();
            // Combo: two eruptions under the hero, then the Root Run: roots race from her to him, leaving a seed where they
            // stop, and erupt under him twice more as they arrive
            int run = Kit.AddEffect(p, SylveneFx.TaprootRunner, offsetX: 10f, offsetY: 0.01f);
            var er2 = new ClipBuilder(sh, "Erupt", "ModRotMotherErupt2").Once().Speed(1.15f).Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop").Ev(2, "AnimAttack", e1).Ev(4, "AnimAttack", e2).Ev(-1, "AnimRun").Build();
            var rr = new ClipBuilder(sh, "Erupt", "ModRotMotherRootRun").Once().Ev(0, "AnimMoveStop").EvF(0, "AnimInputMultiplyFreeFace", 0f)
                .Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff").Ev(2, "AnimAttack", run).EvO(2, "AnimSound", v)
                .Ev(4, "AnimAttack", e1, 0.25f).Ev(4, "AnimAttack", e2, 0.45f).Ev(-1, "AnimRun").Build();
            var so = Special(sh, "Sprouting", "ModRotMotherSprouting").EvO(4, "AnimSound", v);
            for (int i = 0; i < rise.Count; i++) so.Ev(4, "AnimAttack", rise[i], (i / 2) * 0.06f);
            so.Ev(-1, "AnimRun");
            atk.Clear();
            atk.Add(Kit.Attack(a0, er, 0.5f, rangeInner: 40f, rangeOuter: 150f, rangeRetreat: 30f));
            atk.Add(Kit.Attack(a0, er2, 0.5f, rangeInner: 40f, rangeOuter: 150f, rangeRetreat: 30f));
            atk.Add(Kit.Attack(a0, rr, 2.4f, rangeInner: 30f, rangeOuter: 100f, rangeRetreat: 30f));
            Kit.SetSpecial(p, Kit.Attack(sp, so.Build(), 0f, rangeInner: 0f, rangeOuter: 160f, rangeRetreat: 30f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.65f);
            Strike.Feet(p, n0, 16f);   // eruptions and sprouts spawn on the hero (ClosestEnemy): unaffected
            MotherFeed.FeedClip = Once(sh, "Feed", "ModRotMotherFeed");
        }

        // Nightshade: a berry that splits into three; Shade Garden hides her pods and plants two more. Signature: NightshadeGarden.
        static void NightshadeKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int berry = Kit.AddEffect(p, SylveneFx.Berry, offsetX: 11f, offsetY: 25f);   // fingers (11, -25)
            int bl = Kit.AddEffect(p, SylveneFx.Berry, offsetX: 11f, offsetY: 25f, angle: -16f);
            int br = Kit.AddEffect(p, SylveneFx.Berry, offsetX: 11f, offsetY: 25f, angle: 16f);
            // Combo: two berries, then a Handful: three in a fan, nine seeds of poison when they split
            var ts = Kit.Shot(sh, "Toss", "ModSylShadeToss", 3, v, 0f, berry).Build();
            var ts2 = Kit.Shot(sh, "Toss", "ModSylShadeToss2", 3, null, 0f, berry).Speed(1.15f).Build();
            var hf = Kit.Shot(sh, "Toss", "ModSylShadeHandful", 3, v, 0.05f, bl, berry, br).Speed(0.85f).Build();
            var gd = Special(sh, "Garden", "ModSylShadeGarden").Ev(4, "ModSylShade").EvO(4, "AnimSound", v).Ev(5, "ModSylPlantTwo").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, ts, 0.45f, rangeInner: 45f, rangeOuter: 110f, rangeRetreat: 40f));
            atk.Add(Kit.Attack(a0, ts2, 0.45f, rangeInner: 45f, rangeOuter: 110f, rangeRetreat: 40f));
            atk.Add(Kit.Attack(a0, hf, 2.0f, rangeInner: 40f, rangeOuter: 100f, rangeRetreat: 40f));
            Kit.SetSpecial(p, Kit.Attack(sp, gd, 0f, rangeInner: 0f, rangeOuter: 120f, rangeRetreat: 30f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 24f);
        }

        // Pollen Monarch: a fan of three darts; Pollen Storm, a wide cloud ahead that dusts the hero. Signature: MonarchDust.
        static void PollenMonarchKit(Player p, SpriteSheet sh)
        {
            // the Beholder base's voice is its beam roar, far too loud for a moth that claps every couple of seconds
            var flap = Kit.SoundGO("SoundEyelessWingFlapHard");
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p);
            UnityEngine.Object v = flap != null ? flap : Kit.Voice(p);
            int n0 = Strike.Mark(p);
            var darts = new List<int>();
            foreach (var a in new[] { -14f, 0.01f, 14f }) darts.Add(Kit.AddEffect(p, SylveneFx.PollenDart, offsetX: 12f, offsetY: 24f, angle: a));
            int cloud = Kit.AddEffect(p, SylveneFx.PollenCloud, offsetX: 30f, offsetY: 0.01f);
            var wide = new List<int>();
            foreach (var a in new[] { -28f, -14f, 0.01f, 14f, 28f }) wide.Add(Kit.AddEffect(p, SylveneFx.PollenDart, offsetX: 12f, offsetY: 24f, angle: a));
            int gust = Kit.AddEffect(p, SylveneFx.PollenCloud, offsetX: 30f, offsetY: 0.01f);
            // Combo: a clap of three darts, a wider clap of five, then the Gust: three darts and a pollen cloud ahead
            var cl = Kit.Shot(sh, "Clap", "ModMonarchClap", 2, v, 0f, darts.ToArray()).Build();
            var cl2 = Kit.Shot(sh, "Clap", "ModMonarchClap2", 2, v, 0f, wide.ToArray()).Build();
            var cl3 = Kit.Shot(sh, "Clap", "ModMonarchGust", 2, v, 0f, darts.ToArray()).Speed(0.85f).Ev(3, "AnimAttack", gust).Build();
            var st = Special(sh, "Storm", "ModMonarchStorm").EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(3, "AnimInputMultiplyStop")
                .Ev(3, "AnimAttack", cloud).EvO(3, "AnimSound", v).Ev(4, "ModSylStormSeeds").Ev(-1, "AnimRun").Build();
            atk.Clear();
            var clap = Kit.Attack(a0, cl, 0.45f, rangeInner: 45f, rangeOuter: 110f, rangeRetreat: 40f);
            var clap2 = Kit.Attack(a0, cl2, 0.45f, rangeInner: 40f, rangeOuter: 100f, rangeRetreat: 40f);
            var clap3 = Kit.Attack(a0, cl3, 2.2f, rangeInner: 20f, rangeOuter: 70f, rangeRetreat: 30f);
            var storm = Kit.Attack(sp, st, 0f, rangeInner: 0f, rangeOuter: 52f, rangeRetreat: 0f);
            var soft = flap != null ? flap.GetComponent<AudioCue>() : null;
            clap.m_sound = soft; clap2.m_sound = soft; clap3.m_sound = soft;
            storm.m_sound = soft;
            atk.Add(clap); atk.Add(clap2); atk.Add(clap3);
            Kit.SetSpecial(p, storm, 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.65f);
            Strike.Feet(p, n0, 24f);
        }

        // The Sower: a seed shot that plants where it lands; Strafe flies across the hero's front sowing a furrow. Signature: SowerFurrow.
        static void SowerKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int shot = Kit.AddEffect(p, SylveneFx.SeedShot, offsetX: 14f, offsetY: 14f);   // jaws (14, -14)
            // Combo: two seed shots, then the Harvest: one more seed, and every ripe pod near the hero shakes loose
            var sh1 = Kit.Shot(sh, "Shot", "ModSylSowerShot", 2, v, 0f, shot).Build();
            var sh2 = Kit.Shot(sh, "Shot", "ModSylSowerShot2", 2, null, 0f, shot).Speed(1.15f).Build();
            var hv = Kit.Shot(sh, "Shot", "ModSylSowerHarvest", 2, v, 0f, shot).Speed(0.85f).Ev(3, "ModSylHarvest").Build();
            var sf = new ClipBuilder(sh, "Strafe", "ModSylSowerStrafe").Once().Ev(0, "AnimMoveStop").EvF(0, "AnimInputMultiply", 0.4f)
                .Ev(0, "ModSylStrafe").EvO(1, "AnimSound", v).Ev(-1, "AnimInputMultiplyStop").Ev(-1, "AnimRun").Build();
            atk.Clear();
            // 240 px/s for 0.45 s: about 110 px
            atk.Add(Kit.Attack(a0, sh1, 0.4f, rangeInner: 40f, rangeOuter: 100f, rangeRetreat: 35f));
            atk.Add(Kit.Attack(a0, sh2, 0.4f, rangeInner: 40f, rangeOuter: 100f, rangeRetreat: 35f));
            atk.Add(Kit.Attack(a0, hv, 1.9f, rangeInner: 40f, rangeOuter: 100f, rangeRetreat: 35f));
            Kit.SetSpecial(p, Kit.Attack(sp, sf, 0f, rangeInner: 30f, rangeOuter: 90f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 14f);
        }

        // Carrion Lily: a bite at the end of its stalk (24 px, or 40 px planted); Corpse Bloom, a 120 degree cone of rot.
        // Signature: LilyPlanted.
        static void CarrionLilyKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int near = Kit.AddEffect(p, SylveneFx.LilyBite, attach: true, destroyOnAnimEnd: true, offsetX: 20f, offsetY: 11f);   // bite (24, -11)
            int far = Kit.AddEffect(p, SylveneFx.LilyBite, attach: true, destroyOnAnimEnd: true, offsetX: 34f, offsetY: 10f);    // bite (38, -10)
            var rot = new List<int>();
            foreach (var a in new[] { -60f, -30f, 0.01f, 30f, 60f }) rot.Add(Kit.AddEffect(p, SylveneFx.RotCloud, offsetX: 12f, offsetY: 24f, angle: a));
            int breath = Kit.AddEffect(p, SylveneFx.RotCloud, offsetX: 22f, offsetY: 12f);
            var fan = new List<int>();
            foreach (var a in new[] { -22f, 22f }) fan.Add(Kit.AddEffect(p, SylveneFx.RotCloud, offsetX: 34f, offsetY: 12f, angle: a));
            // Combo: a near bite and a far bite that each breathe out a puff of rot, then the Rot Kiss: the far bite with
            // three puffs fanned from it
            var ln = Kit.Melee(sh, "Lunge", "ModLilyLunge", v, 3, near, 0f).Ev(3, "AnimAttack", breath).Build();
            var lf = Kit.Melee(sh, "LungeFar", "ModLilyLungeFar", v, 3, far, 0f).Ev(3, "AnimAttack", breath).Build();
            var lk = Kit.Melee(sh, "LungeFar", "ModLilyRotKiss", v, 3, far, 0f).Speed(0.85f).Ev(3, "AnimAttack", breath)
                .Ev(3, "AnimAttack", fan[0], 0.05f).Ev(3, "AnimAttack", fan[1], 0.05f).Build();
            var bl = Kit.Shot(sh, "Bloom", "ModLilyBloom", 4, v, 0.02f, rot.ToArray()).Ev(0, "AnimMoveStop").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, ln, 0.45f, rangeInner: 12f, rangeOuter: 30f));
            atk.Add(Kit.Attack(a0, lf, 0.45f, rangeInner: 12f, rangeOuter: 46f));
            atk.Add(Kit.Attack(a0, lk, 2.0f, rangeInner: 12f, rangeOuter: 50f));
            Kit.SetSpecial(p, Kit.Attack(sp, bl, 0f, rangeInner: 0f, rangeOuter: 50f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 24f);
            LilyPlanted.PlantedIdle = Looped(sh, "IdlePlanted", "ModLilyIdlePlanted");
            LilyPlanted.PlantClip = Once(sh, "Plant", "ModLilyPlant");
        }

        // Briar Wyrm: the mace cracks down in front, then swings behind it; Thorn Spiral spins thorns out in two arms.
        static void BriarWyrmKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int front = Kit.AddEffect(p, SylveneFx.WyrmFront, attach: true, destroyOnAnimEnd: true, offsetX: 19f, offsetY: 6f);   // mace (21, -6)
            int back = Kit.AddEffect(p, SylveneFx.WyrmBack, attach: true, destroyOnAnimEnd: true, offsetX: -21f, offsetY: 6f);   // mace (-23, -6)
            var flail = new List<int>();
            foreach (var a in new[] { 155f, 180f, 205f }) flail.Add(Kit.AddEffect(p, SylveneFx.Thorn, offsetX: -21f, offsetY: 8f, angle: a));
            // Combo: the mace in front and behind, twice, then the Flail: the back swing flings three thorns behind it
            var mc = Kit.Melee(sh, "Mace", "ModSylWyrmMace", v, 3, front, 10f, 6, back, 0f).Build();
            var mc2 = Kit.Melee(sh, "Mace", "ModSylWyrmMace2", null, 3, front, 20f, 6, back, 0f).Speed(1.1f).Build();
            var fl = Kit.Melee(sh, "Mace", "ModSylWyrmFlail", v, 3, front, 20f, 6, back, 0f).Speed(0.9f)
                .Ev(6, "AnimAttack", flail[0]).Ev(6, "AnimAttack", flail[1]).Ev(6, "AnimAttack", flail[2]).Build();
            var sp1 = Special(sh, "Spiral", "ModSylWyrmSpiral").Ev(2, "ModSylSpiral").EvO(2, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, mc, 0.45f, rangeInner: 8f, rangeOuter: 30f));
            atk.Add(Kit.Attack(a0, mc2, 0.45f, rangeInner: 8f, rangeOuter: 30f));
            atk.Add(Kit.Attack(a0, fl, 2.0f, rangeInner: 8f, rangeOuter: 30f));
            // thorns fly 130 px/s for 0.9 s
            Kit.SetSpecial(p, Kit.Attack(sp, sp1, 0f, rangeInner: 0f, rangeOuter: 80f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.6f);
            Strike.Feet(p, n0, 10f);
        }

        // Blight Bellows: a bouncing gas bladder; Gas Lanes, three pumps of gas along its facing. Signature: BellowsGas.
        static void BlightBellowsKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            var lb = new ClipBuilder(sh, "Lob", "ModSylBellowsLob").Once().EvF(0, "AnimInputMultiplyFreeFace", 0f)
                .Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff").Ev(2, "ModSylLob").EvO(2, "AnimSound", v).Ev(-1, "AnimRun").Build();
            // Combo: two bladders, then a pair at once that straddle the hero's spot
            var lb2 = new ClipBuilder(sh, "Lob", "ModSylBellowsLob2").Once().Speed(1.1f).EvF(0, "AnimInputMultiplyFreeFace", 0f)
                .Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff").Ev(2, "ModSylLob").Ev(-1, "AnimRun").Build();
            var lp = new ClipBuilder(sh, "Lob", "ModSylBellowsLobPair").Once().Speed(0.85f).EvF(0, "AnimInputMultiplyFreeFace", 0f)
                .Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff").Ev(2, "ModSylLobPair").EvO(2, "AnimSound", v).Ev(-1, "AnimRun").Build();
            var pm = new ClipBuilder(sh, "Pump", "ModSylBellowsPump").Once().Ev(0, "AnimMoveStop").EvF(0, "AnimInputMultiplyFreeFace", 0f);
            foreach (int f in new[] { 0, 3, 6 }) pm.Ev(f, "ModSylLane");
            pm.EvO(0, "AnimSound", v).Ev(-1, "AnimInputMultiplyStop").Ev(-1, "AnimRun");
            atk.Clear();
            // four hops of up to 22 px
            atk.Add(Kit.Attack(a0, lb, 0.5f, rangeInner: 40f, rangeOuter: 90f, rangeRetreat: 35f));
            atk.Add(Kit.Attack(a0, lb2, 0.5f, rangeInner: 40f, rangeOuter: 90f, rangeRetreat: 35f));
            atk.Add(Kit.Attack(a0, lp, 2.2f, rangeInner: 40f, rangeOuter: 90f, rangeRetreat: 35f));
            Kit.SetSpecial(p, Kit.Attack(sp, pm.Build(), 0f, rangeInner: 0f, rangeOuter: 65f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.65f);
            Strike.Feet(p, n0, 18f);
        }

        // Carrion Queen: a proboscis stab; Proboscis Dive, a long dive she steers. Signature: QueenDrone.
        static void CarrionQueenKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int stab = Kit.AddEffect(p, SylveneFx.QueenStab, attach: true, destroyOnAnimEnd: true, offsetX: 15f, offsetY: 24f);   // tip (22, -26)
            int dive = Kit.AddEffect(p, SylveneFx.QueenDive, attach: true, destroyOnAnimEnd: true, offsetX: 14f, offsetY: 14f);
            int siphon = Kit.AddEffect(p, SylveneFx.QueenSiphon, attach: true, destroyOnAnimEnd: true, offsetX: 15f, offsetY: 24f);
            // Combo: two stabs, then the Siphon: a long lunging stab that drinks from the hero (she heals on a hit)
            var sb = Kit.Melee(sh, "Stab", "ModSylQueenStab", v, 2, stab, 20f).Build();
            var sb2 = Kit.Melee(sh, "Stab", "ModSylQueenStab2", null, 2, stab, 30f).Speed(1.15f).Build();
            var si = Kit.Melee(sh, "Stab", "ModSylQueenSiphonStab", v, 2, siphon, 70f).Speed(0.85f).Build();
            var dv = Special(sh, "Dive", "ModSylQueenDive").Ev(1, "AnimInputOn").EvF(2, "AnimMoveStick", 260f).Ev(2, "AnimAttack", dive)
                .EvO(2, "AnimSound", v).Ev(6, "AnimMoveStop").Ev(6, "AnimInputOff").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sb, 0.35f, rangeInner: 10f, rangeOuter: 28f));
            atk.Add(Kit.Attack(a0, sb2, 0.35f, rangeInner: 10f, rangeOuter: 30f));
            atk.Add(Kit.Attack(a0, si, 1.8f, rangeInner: 12f, rangeOuter: 44f));
            // 260 px/s through four 0.08 s frames, steered: about 70 px
            Kit.SetSpecial(p, Kit.Attack(sp, dv, 0f, rangeInner: 20f, rangeOuter: 75f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.Combo, 0.55f);
            Strike.Feet(p, n0, 20f);
            QueenDrone.BlurIdle = Looped(sh, "IdleBlur", "ModSylQueenIdleBlur");
            QueenDrone.BlurRun = Looped(sh, "RunBlur", "ModSylQueenRunBlur");
        }

        // ---------------------------------------------------------------------------------------------- minions
        // Sprout (Rot Mother): a tiny spore puff.
        static void SproutKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0];
            int n0 = Strike.Mark(p);
            int puff = Kit.AddEffect(p, SylveneFx.SproutPuff, offsetX: 7f, offsetY: 5f);   // the husk splits at (7, -5)
            var pf = Kit.Shot(sh, "Puff", "ModSproutPuff", 2, null, 0f, puff).Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, pf, a0.m_cooldown, rangeInner: 8f, rangeOuter: 22f, rangeRetreat: 0f));
            Strike.Feet(p, n0, 5f);
            MinionAI.Tune(p, 120f, 16f, 24f, 1.2f, 2f, 1.5f);
        }

        // Shambler (Cordyceps Saint): what rises from an infected corpse; its basic is a spore puff.
        static void ShamblerKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0];
            int n0 = Strike.Mark(p);
            int puff = Kit.AddEffect(p, SylveneFx.SporePuff, offsetX: 6f, offsetY: 8f);
            var pf = Kit.Shot(sh, "Puff", "ModSylShamblerPuff", 2, null, 0f, puff).Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, pf, 1.0f, rangeInner: 8f, rangeOuter: 26f, rangeRetreat: 0f));
            R.Set(p, "m_hasSpecialAttack", false);
            Strike.Feet(p, n0, 8f);
            MinionAI.Tune(p, 140f, 14f, 24f, 0.9f, 1.4f, 1.3f);
        }

        // The god's perk: every Sylvene monster drops a seed where it dies.
        static void FallowGround(GameObject go, Player p) { Kit.AddDeathSpawn(p, SylveneFx.Seed); Strike.DeathAtFeet(p); }

        static void ShamblerBursts(GameObject go, Player p) { Kit.AddDeathSpawn(p, SylveneFx.ShamblerBurst); Strike.DeathAtFeet(p); }

        public static readonly MonsterDef Sprout = new MonsterDef
        {
            id = "Sprout", art = "SylSprout", basePrefab = "EnemyTinyRatFodder", health = 1.2f, kit = SproutKit
        };

        public static readonly MonsterDef Shambler = new MonsterDef
        {
            id = "SylShambler", art = "SylShambler", basePrefab = "EnemyTinyRatFodder", health = 1f, kit = ShamblerKit, customize = ShamblerBursts
        };

        // Evolution tree: every evolution has exactly one parent.
        //   Sporeling  -> SporeHusk, BloomWitch       SporeHusk -> Puffball, Cordyceps       BloomWitch -> RotMother, Nightshade
        //   Thornbiter -> BrambleKnight, Strangler    BrambleKnight -> BriarBehemoth, BriarChampion   Strangler -> CarrionLily, BriarWyrm
        //   Rotfly     -> GallWasp, Bloatfly          GallWasp -> PollenMonarch, Sower       Bloatfly -> BlightBellows, CarrionQueen
        public static readonly List<MonsterDef> Monsters = new List<MonsterDef>
        {
            new MonsterDef { id = "Sporeling", art = "SylSporeling", basePrefab = "EnemyMushroom", health = 4f, evolveCost = 0f,
                             evolveTo = new[] { "SylSporeHusk", "BloomWitch" }, kit = SporelingKit, customize = FallowGround },
            new MonsterDef { id = "Thornbiter", art = "SylThornbiter", basePrefab = "EnemyGnome", health = 4f, evolveCost = 0f,
                             evolveTo = new[] { "BrambleKnight", "SylStrangler" }, kit = ThornbiterKit, customize = FallowGround },
            new MonsterDef { id = "Rotfly", art = "SylRotfly", basePrefab = "EnemyFlyingEye_Dodge", health = 3f, evolveCost = 0f,
                             evolveTo = new[] { "SylGallWasp", "SylBloatfly" }, kit = RotflyKit, customize = FallowGround },
            new MonsterDef { id = "SylSporeHusk", art = "SylSporeHusk", basePrefab = "EnemyMinotaur", health = 6.5f, speedMult = 0.85f, evolveCost = 2.5f, damageMult = 1.4f,
                             evolveTo = new[] { "SylPuffball", "SylCordyceps" }, kit = SporeHuskKit, customize = FallowGround },
            new MonsterDef { id = "BloomWitch", art = "SylBloomWitch", basePrefab = "EnemyWitch", health = 5.5f, evolveCost = 2.5f, damageMult = 1.3f,
                             evolveTo = new[] { "RotMother", "SylNightshade" }, kit = BloomWitchKit, customize = FallowGround },
            new MonsterDef { id = "BrambleKnight", art = "SylBrambleKnight", basePrefab = "EnemyOrc", health = 7f, evolveCost = 2.5f, damageMult = 1.4f,
                             evolveTo = new[] { "SylBriarBehemoth", "SylBriarChampion" }, kit = BrambleKnightKit, customize = FallowGround },
            new MonsterDef { id = "SylStrangler", art = "SylStrangler", basePrefab = "EnemyDemonSnake", health = 6f, evolveCost = 2.5f, damageMult = 1.3f,
                             evolveTo = new[] { "SylCarrionLily", "SylBriarWyrm" }, kit = StranglerKit, customize = FallowGround },
            new MonsterDef { id = "SylGallWasp", art = "SylGallWasp", basePrefab = "EnemyFlyingEyeBomber", health = 5.5f, evolveCost = 2.5f, damageMult = 1.4f,
                             evolveTo = new[] { "SylPollenMonarch", "SylSower" }, kit = GallWaspKit, customize = FallowGround },
            new MonsterDef { id = "SylBloatfly", art = "SylBloatfly", basePrefab = "EnemyFlyingEye_Red", health = 6.5f, speedMult = 0.9f, evolveCost = 2.5f, damageMult = 1.2f,
                             evolveTo = new[] { "SylBlightBellows", "SylCarrionQueen" }, kit = BloatflyKit, customize = FallowGround },
            new MonsterDef { id = "SylBriarBehemoth", art = "SylBriarBehemoth", basePrefab = "EnemyCapraDemon", health = 14f, speedMult = 0.9f, evolveCost = 4.5f,
                             kit = BriarBehemothKit, customize = FallowGround },
            new MonsterDef { id = "SylBriarChampion", art = "SylBriarChampion", basePrefab = "EnemyDarkGuardian", health = 13.5f, evolveCost = 4.5f, damageMult = 1.2f,
                             kit = BriarChampionKit, customize = FallowGround },
            new MonsterDef { id = "SylPuffball", art = "SylPuffball", basePrefab = "EnemyGhoul", health = 14f, speedMult = 0.85f, evolveCost = 4.5f, damageMult = 1.1f,
                             kit = PuffballKit, customize = FallowGround },
            new MonsterDef { id = "SylCordyceps", art = "SylCordyceps", basePrefab = "EnemySkeletonPope", health = 12.5f, evolveCost = 4.5f, damageMult = 1.2f,
                             kit = CordycepsKit, customize = FallowGround },
            new MonsterDef { id = "RotMother", art = "SylRotMother", basePrefab = "EnemyPriestess", health = 13.5f, speedMult = 0.85f, evolveCost = 4.5f,
                             kit = RotMotherKit, customize = FallowGround },
            new MonsterDef { id = "SylNightshade", art = "SylNightshade", basePrefab = "EnemyPrincess", health = 12.5f, speedMult = 0.9f, evolveCost = 4.5f, damageMult = 1.2f,
                             kit = NightshadeKit, customize = FallowGround },
            new MonsterDef { id = "SylPollenMonarch", art = "SylPollenMonarch", basePrefab = "EnemyBeholder", health = 12.5f, evolveCost = 4.5f, damageMult = 1.1f,
                             kit = PollenMonarchKit, customize = FallowGround },
            new MonsterDef { id = "SylSower", art = "SylSower", basePrefab = "EnemyFlyingEye_Rapidfire", health = 12.5f, evolveCost = 4.5f, damageMult = 1.3f,
                             kit = SowerKit, customize = FallowGround },
            new MonsterDef { id = "SylCarrionLily", art = "SylCarrionLily", basePrefab = "EnemyTroll", health = 13f, speedMult = 0.75f, evolveCost = 4.5f, damageMult = 1.3f,
                             kit = CarrionLilyKit, customize = FallowGround },
            new MonsterDef { id = "SylBriarWyrm", art = "SylBriarWyrm", basePrefab = "EnemySmallDragon", health = 14f, speedMult = 0.85f, evolveCost = 4.5f, damageMult = 0.9f,
                             kit = BriarWyrmKit, customize = FallowGround },
            new MonsterDef { id = "SylBlightBellows", art = "SylBlightBellows", basePrefab = "EnemyFlyingEyeBomber", health = 13.5f, speedMult = 0.8f, evolveCost = 4.5f, damageMult = 1.3f,
                             kit = BlightBellowsKit, customize = FallowGround },
            new MonsterDef { id = "SylCarrionQueen", art = "SylCarrionQueen", basePrefab = "EnemyDarkHaunt", health = 13f, evolveCost = 4.5f, damageMult = 1.1f,
                             kit = CarrionQueenKit, customize = FallowGround },
        };

        /// <summary>Each monster's signature.</summary>
        static readonly Dictionary<string, Type> Signatures = new Dictionary<string, Type>
        {
            { "Sporeling", typeof(SporelingTend) }, { "SylSporeHusk", typeof(HuskShake) }, { "BloomWitch", typeof(WitchGraft) },
            { "SylStrangler", typeof(StranglerSling) }, { "SylBloatfly", typeof(BloatflyRain) }, { "SylBriarBehemoth", typeof(BehemothBush) },
            { "SylBriarChampion", typeof(ChampionLance) }, { "SylPuffball", typeof(PuffballRebound) }, { "SylCordyceps", typeof(CordycepsInfect) },
            { "RotMother", typeof(MotherFeed) }, { "SylNightshade", typeof(NightshadeGarden) }, { "SylPollenMonarch", typeof(MonarchDust) },
            { "SylSower", typeof(SowerFurrow) }, { "SylCarrionLily", typeof(LilyPlanted) }, { "SylBriarWyrm", typeof(WyrmSpiral) },
            { "SylBlightBellows", typeof(BellowsGas) }, { "SylCarrionQueen", typeof(QueenDrone) },
        };

        public static readonly GodDef God = new GodDef
        {
            name = "Sylvene",
            text = "Dead drop seeds: poison pods",
            flavour = "Every corpse in the orchard\nbecomes a seed.",
            winText = "THE ORCHARD WITHERS",
            portraitArt = "DeitySylvene",
            startingMonsters = new[] { "Sporeling", "Thornbiter", "Rotfly" },
        };

        static Deity s_deity;
        static exSpriteAnimClip s_idol;

        public static void Register()
        {
            SylveneFx.Build();
            foreach (var m in Monsters)
            {
                var t = new MonsterTraits().Add<SylveneMonster>();
                Type q;
                if (Signatures.TryGetValue(m.id, out q)) t.behaviours.Add(q);
                MonsterTraits.Register(m.PrefabName, t);
            }
            var sprout = MonsterFactory.Build(Sprout);
            if (sprout != null) SylveneFx.SproutSpawner = FxKit.MinionSpawner("ModSproutSpawner", sprout.gameObject, "FxSylSproutBurst", "Play");
            MonsterTraits.Register(Shambler.PrefabName, new MonsterTraits { lifetime = 4f, expireFx = SylveneFx.ShamblerBurst });
            var shambler = MonsterFactory.Build(Shambler);
            if (shambler != null) SylveneFx.ShamblerSpawner = FxKit.MinionSpawner("ModSylShamblerSpawner", shambler.gameObject, "FxSylSproutBurst", "Play");
            foreach (var m in Monsters) MonsterFactory.Build(m);
            MonsterFactory.LinkEvolutions(Monsters);
            s_deity = DeityFactory.Register(God);
            RegisterIdol();
            Strike.KeepAllScales();
        }

        // the gold idol carved for Sylvene's perk: an orchard mother whose pod opens and closes
        static void RegisterIdol()
        {
            s_idol = SlotArt.Clip("DeityGoldIdolSylvene", "Idle");
            if (s_idol == null) return;
            var prev = SlotGods.PortraitFor;
            SlotGods.PortraitFor = (tier, perk) =>
                tier == SlotTier.Gold && perk != null && (perk == s_deity || R.Get<string>(perk, "m_name") == God.name)
                    ? s_idol : (prev != null ? prev(tier, perk) : null);
        }
    }
}
