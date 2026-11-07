using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Art;
    using CrawlFurther.Gods;
    using CrawlFurther.Items;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;
    using CrawlFurther.Content.Gods.Ossivar;
    using CrawlFurther.Content.Items;

    /// <summary>
    /// Ysveld, the Frost Widow: cold that creeps up on you and spiders that wait. The perk is the blizzard's floor ice
    /// (<see cref="YsvFloor"/>) and every frost hit fills a pip over the hero (<see cref="YsvRime"/>); each monster has a
    /// signature of its own (a <see cref="YsveldBehaviour"/>, or a rule on its effects) with a tell the hero can read.
    /// Offsets below are the sprite's sync points (art/out_ysveld/TIMING.md), x forward, y up.
    /// </summary>
    public static class YsveldPack
    {
        static Attacks.eAttackOrderType InOrder { get { return Attacks.eAttackOrderType.InOrder; } }

        static ClipBuilder Special(SpriteSheet sh, string anim, string clip)
        {
            return new ClipBuilder(sh, anim, clip).Once().Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop");
        }

        static exSpriteAnimClip Looped(SpriteSheet sh, string anim, string clip)
        {
            return sh.Has(anim) ? new ClipBuilder(sh, anim, clip).Loop().Build() : null;
        }

        // ---------------------------------------------------------------------------------------------- tier 1
        // Rimeling: a lunging frost bite (Cold Snap: on a hero with 2 pips it adds 2); Spit lobs a glob that may slow.
        static void RimelingKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int from = Strike.Mark(p);
            int bite = Kit.AddEffect(p, YsveldFx.Bite, attach: true, destroyOnAnimEnd: true, offsetX: 9f, offsetY: 3f);   // fangs (9, -2)
            int glob = Kit.AddEffect(p, YsveldFx.Glob, offsetX: 9f, offsetY: 5f);
            Strike.Feet(p, from, 5f);
            var bt = Kit.Melee(sh, "Bite", "ModYsvRimelingBite", v, 3, bite, 70f).Build();
            var spt = Kit.Shot(sh, "Spit", "ModYsvRimelingSpit", 3, v, 0f, glob).Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, bt, 1.3f, rangeInner: 10f, rangeOuter: 24f));
            Kit.SetSpecial(p, Kit.Attack(sp, spt, 0f, rangeInner: 30f, rangeOuter: 90f, rangeRetreat: 0f), 5.5f);
            Kit.Order(p, InOrder);
            RimelingSnap.SnapIdle = Looped(sh, "IdleSnap", "ModYsvRimelingIdleSnap");
            RimelingSnap.SnapRun = Looped(sh, "RunSnap", "ModYsvRimelingRunSnap");
        }

        // Hoarmoth: flings a fan of three frost motes; Gust knocks the hero far back (Sleet Gust: twice as far on ice).
        static void HoarmothKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var v = Kit.Voice(p);
            int from = Strike.Mark(p);
            var motes = new List<int>();
            foreach (var a in new[] { -16f, 0.01f, 16f }) motes.Add(Kit.AddEffect(p, YsveldFx.Mote, offsetX: 6f, offsetY: 8f, angle: a));
            int gust = Kit.AddEffect(p, YsveldFx.Gust, offsetX: 8f, offsetY: 7f);
            Strike.Feet(p, from, 8f);
            var ds = Kit.Shot(sh, "Dust", "ModYsvHoarmothDust", 3, v, 0.03f, motes.ToArray()).Build();
            var gs = Kit.Shot(sh, "Gust", "ModYsvHoarmothGust", 3, v, 0f, gust).Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, ds, 1.5f, rangeInner: 30f, rangeOuter: 80f, rangeRetreat: 25f));
            Kit.EnableSpecial(p, Kit.Attack(a0, gs, 0f, rangeInner: 0f, rangeOuter: 50f, rangeRetreat: 0f), 5.5f);
            Kit.Order(p, InOrder);
        }

        // Rime Shardling: a crystal head-butt; Icicle calls one icicle down on the hero 0.7 s later (Splinter on ice).
        static void ShardlingKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int from = Strike.Mark(p);
            int ram = Kit.AddEffect(p, YsveldFx.Ram, attach: true, destroyOnAnimEnd: true, offsetX: 8f, offsetY: 5f);
            int mark = Kit.AddEffect(p, YsveldFx.IcicleMark, spawnPoint: DamageEffectData.eSpawnPoint.ClosestEnemy);
            Strike.Feet(p, from, 6f);
            var rm = Kit.Melee(sh, "Ram", "ModYsvShardlingRam", v, 3, ram, 90f).Build();
            var ic = Special(sh, "Icicle", "ModYsvShardlingIcicle").Ev(4, "AnimAttack", mark).EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, rm, 1.4f, rangeInner: 12f, rangeOuter: 27f));
            Kit.SetSpecial(p, Kit.Attack(sp, ic, 0f, rangeInner: 20f, rangeOuter: 120f, rangeRetreat: 0f), 5.5f);
            Kit.Order(p, InOrder);
        }

        // ---------------------------------------------------------------------------------------------- tier 2
        // Silk Weaver: frost fangs; Silk Line ties the hero to her for 2.5 s (Strum: a frost bead down the line every 0.8 s).
        static void WeaverKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int from = Strike.Mark(p);
            int fangs = Kit.AddEffect(p, YsveldFx.Fangs, attach: true, destroyOnAnimEnd: true, offsetX: 11f, offsetY: 4f);
            int thread = Kit.AddEffect(p, YsveldFx.Thread, offsetX: 6f, offsetY: 12f);       // spinnerets (6, -19), flown at the node
            Strike.Feet(p, from, 12f);
            var fg = Kit.Melee(sh, "Fangs", "ModYsvWeaverFangs", v, 3, fangs, 60f).Build();
            var th = Kit.Shot(sh, "Tether", "ModYsvWeaverTether", 3, v, 0f, thread).Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, fg, 1.3f, rangeInner: 14f, rangeOuter: 30f));
            Kit.SetSpecial(p, Kit.Attack(sp, th, 0f, rangeInner: 40f, rangeOuter: 110f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, InOrder);
        }

        // Rime Lurker: a lunging trapdoor bite; Snares flicks two snares by the hero (Set in Ice: snares on ice stay, 2 pips).
        static void LurkerKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p) ?? a0; var v = Kit.Voice(p);
            int from = Strike.Mark(p);
            int bite = Kit.AddEffect(p, YsveldFx.LurkBite, attach: true, destroyOnAnimEnd: true, offsetX: 11f, offsetY: 4f);
            int ring = Kit.AddEffect(p, YsveldFx.SnareRing, spawnPoint: DamageEffectData.eSpawnPoint.ClosestEnemy);
            Strike.Feet(p, from, 5f);
            var bt = Kit.Melee(sh, "Bite", "ModYsvLurkerBite", v, 3, bite, 70f).Build();
            var sn = Special(sh, "Snare", "ModYsvLurkerSnare").Ev(4, "AnimAttack", ring).EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, bt, 1.3f, rangeInner: 14f, rangeOuter: 30f));
            Kit.EnableSpecial(p, Kit.Attack(sp, sn, 0f, rangeInner: 30f, rangeOuter: 110f, rangeRetreat: 0f), 6f);
            Kit.Order(p, InOrder);
        }

        // Silkmoth: three silk needles in a fan; Dive rushes through the hero (Frost Wake: a 50 px streak of ice behind it).
        static void SilkmothKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var v = Kit.Voice(p);
            int from = Strike.Mark(p);
            var needles = new List<int>();
            foreach (var a in new[] { -14f, 0.01f, 14f }) needles.Add(Kit.AddEffect(p, YsveldFx.Needle, offsetX: 8f, offsetY: 10f, angle: a));
            int dive = Kit.AddEffect(p, YsveldFx.Dive, attach: true, destroyOnAnimEnd: true, offsetX: 4f, offsetY: 8f);
            int wake = Kit.AddEffect(p, YsveldFx.Wake, attach: true, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            Strike.Feet(p, from, 10f);
            var vl = Kit.Shot(sh, "Volley", "ModYsvSilkmothVolley", 3, v, 0.03f, needles.ToArray()).Build();
            var dv = new ClipBuilder(sh, "Dive", "ModYsvSilkmothDive").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff")
                .EvF(3, "AnimMove", 210f).Ev(3, "AnimAttack", dive).Ev(3, "AnimAttack", wake).EvO(3, "AnimSound", v)
                .Ev(6, "AnimMoveStop").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, vl, 1.5f, rangeInner: 35f, rangeOuter: 95f, rangeRetreat: 30f));
            Kit.EnableSpecial(p, Kit.Attack(a0, dv, 0f, rangeInner: 25f, rangeOuter: 80f, rangeRetreat: 0f), 6f);
            Kit.Order(p, InOrder);
        }

        // Veil Witch: an ice shard from her wand; Crystals grow round the hero and shatter 1 s later (Cold Read: 1 + pips).
        static void WitchKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int from = Strike.Mark(p);
            int shard = Kit.AddEffect(p, YsveldFx.Shard, offsetX: 13f, offsetY: 12f);
            int ring = Kit.AddEffect(p, YsveldFx.CrystalRing, spawnPoint: DamageEffectData.eSpawnPoint.ClosestEnemy);
            Strike.Feet(p, from, 12f);
            var sd = Kit.Shot(sh, "Shard", "ModYsvWitchShard", 3, v, 0f, shard).Build();
            var cr = Special(sh, "Crystals", "ModYsvWitchCrystals").Ev(4, "AnimAttack", ring).EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sd, 1.4f, rangeInner: 50f, rangeOuter: 120f, rangeRetreat: 40f));
            Kit.SetSpecial(p, Kit.Attack(sp, cr, 0f, rangeInner: 40f, rangeOuter: 140f, rangeRetreat: 30f), 6.5f);
            Kit.Order(p, InOrder);
        }

        // Rime Knight: a two-handed cleave (Frozen Edge: it freezes 2 slabs of floor ahead); Ice Plates grows 2 plates.
        static void KnightKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int from = Strike.Mark(p);
            int cleave = Kit.AddEffect(p, YsveldFx.Cleave, attach: true, destroyOnAnimEnd: true, offsetX: 3f, offsetY: 8f);
            int edge = Kit.AddEffect(p, YsveldFx.EdgeIce, offsetX: 20f, offsetY: 0f);       // the blade tip meets the floor at (18, 0)
            int puff = Kit.AddEffect(p, YsveldFx.Puff, offsetX: 5f, offsetY: 12f);
            Strike.Feet(p, from, 12f);
            var cl = Kit.Melee(sh, "Cleave", "ModYsvKnightCleave", v, 4, cleave, 40f).Ev(4, "AnimAttack", edge).Build();
            var pl = Special(sh, "Plate", "ModYsvKnightPlate").Ev(4, "ModGainPlates", 2).Ev(4, "AnimAttack", puff).EvO(4, "AnimSound", v)
                .Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, cl, 1.4f, rangeInner: 14f, rangeOuter: 28f));
            Kit.SetSpecial(p, Kit.Attack(sp, pl, 0f, rangeInner: 0f, rangeOuter: 60f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, InOrder);
        }

        // Shard Hermit: a staff thrust; Plant Crystal plants a spike by the hero (Triangle: inside 3 of them he freezes).
        static void HermitKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p) ?? a0; var v = Kit.Voice(p);
            int from = Strike.Mark(p);
            int jab = Kit.AddEffect(p, YsveldFx.Jab, attach: true, destroyOnAnimEnd: true, offsetX: 16f, offsetY: 10f);    // staff tip (22, -10)
            Strike.Feet(p, from, 10f);
            var jb = Kit.Melee(sh, "Jab", "ModYsvHermitJab", v, 3, jab, 60f).Build();
            var pl = Special(sh, "Plant", "ModYsvHermitPlant").Ev(4, "YsvPlantCrystal").EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, jb, 1.4f, rangeInner: 12f, rangeOuter: 28f));
            Kit.EnableSpecial(p, Kit.Attack(sp, pl, 0f, rangeInner: 20f, rangeOuter: 130f, rangeRetreat: 20f), 6.5f);
            Kit.Order(p, InOrder);
        }

        // ---------------------------------------------------------------------------------------------- tier 3
        // Widow Matron: rears and impales the floor (doubled after a Wrap); Egg Sacs sets two sacs down by the hero.
        static void MatronKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int from = Strike.Mark(p);
            int impale = Kit.AddEffect(p, YsveldFx.Impale, attach: true, destroyOnAnimEnd: true, offsetX: 22f, offsetY: 4f);
            int dbl = Kit.AddEffect(p, YsveldFx.ImpaleDouble, attach: true, destroyOnAnimEnd: true, offsetX: 22f, offsetY: 4f);
            int egg0 = Kit.AddEffect(p, YsveldFx.EggSac, offsetX: -14f, offsetY: 0f, spawnPoint: DamageEffectData.eSpawnPoint.ClosestEnemy);
            int egg1 = Kit.AddEffect(p, YsveldFx.EggSac, offsetX: 14f, offsetY: 6f, spawnPoint: DamageEffectData.eSpawnPoint.ClosestEnemy);
            Strike.Feet(p, from, 8f);
            var im = Kit.Melee(sh, "Impale", "ModYsvMatronImpale", v, 4, impale, 50f).Build();
            var id = Kit.Melee(sh, "Impale", "ModYsvMatronImpaleWrapped", v, 4, dbl, 50f).Build();
            var br = Special(sh, "Brood", "ModYsvMatronBrood").Ev(5, "AnimAttack", egg0).Ev(5, "AnimAttack", egg1, 0.12f)
                .EvO(5, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, im, 1.6f, rangeInner: 16f, rangeOuter: 34f));
            atk.Add(Kit.Attack(a0, id, 1.6f, rangeInner: 16f, rangeOuter: 34f));
            Kit.SetSpecial(p, Kit.Attack(sp, br, 0f, rangeInner: 20f, rangeOuter: 120f, rangeRetreat: 0f), 7f);
            Kit.Order(p, InOrder);
            MatronWrap.WrapIdle = Looped(sh, "IdleWrap", "ModYsvMatronIdleWrap");
            MatronWrap.WrapRun = Looped(sh, "RunWrap", "ModYsvMatronRunWrap");
            MatronWrap.DoubleImpale = YsveldFx.ImpaleDouble;
        }

        // Loom Widow: a silk whip along the floor (it pins with a full spool); Spool casts a line that eats frost pips.
        static void LoomKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p) ?? a0; var v = Kit.Voice(p);
            int from = Strike.Mark(p);
            int lash = Kit.AddEffect(p, YsveldFx.Lash, attach: true, destroyOnAnimEnd: true, offsetX: 20f, offsetY: 6f);   // whip to (29, -2)
            int pin = Kit.AddEffect(p, YsveldFx.LashPin, attach: true, destroyOnAnimEnd: true, offsetX: 20f, offsetY: 6f);
            int line = Kit.AddEffect(p, YsveldFx.Spool, offsetX: 14f, offsetY: 14f);
            Strike.Feet(p, from, 14f);
            var ls = Kit.Melee(sh, "Lash", "ModYsvLoomLash", v, 3, lash, 30f).Build();
            var lp = Kit.Melee(sh, "Lash", "ModYsvLoomLashPin", v, 3, pin, 30f).Build();
            var sl = Kit.Shot(sh, "Spool", "ModYsvLoomSpool", 3, v, 0f, line).Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, ls, 1.6f, rangeInner: 16f, rangeOuter: 40f));
            atk.Add(Kit.Attack(a0, lp, 1.6f, rangeInner: 16f, rangeOuter: 40f));
            Kit.EnableSpecial(p, Kit.Attack(sp, sl, 0f, rangeInner: 40f, rangeOuter: 120f, rangeRetreat: 0f), 7f);
            Kit.Order(p, InOrder);
            LoomSpool.PinLash = YsveldFx.LashPin;
        }

        // Hoarfrost Tarantula: a crushing bite; Hair Flick sprays a cone of frozen hairs (Brood on Its Back sheds Broodlings).
        static void TarantulaKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p) ?? a0; var v = Kit.Voice(p);
            int from = Strike.Mark(p);
            int bite = Kit.AddEffect(p, YsveldFx.TarBite, attach: true, destroyOnAnimEnd: true, offsetX: 14f, offsetY: 5f);
            var hairs = new List<int>();
            foreach (var a in new[] { -24f, -12f, 0.01f, 12f, 24f }) hairs.Add(Kit.AddEffect(p, YsveldFx.Hairs, offsetX: 12f, offsetY: 9f, angle: a));
            Strike.Feet(p, from, 9f);
            var bt = Kit.Melee(sh, "Bite", "ModYsvTarantulaBite", v, 3, bite, 50f).Build();
            var fl = Kit.Shot(sh, "Flick", "ModYsvTarantulaFlick", 4, v, 0.02f, hairs.ToArray()).Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, bt, 1.7f, rangeInner: 16f, rangeOuter: 32f));
            Kit.EnableSpecial(p, Kit.Attack(sp, fl, 0f, rangeInner: 10f, rangeOuter: 46f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, InOrder);
            var idle = new[] { "Idle0", "Idle1", "Idle2" }; var run = new[] { "Run0", "Run1", "Run2" };
            TarantulaBrood.BroodIdle = new exSpriteAnimClip[3]; TarantulaBrood.BroodRun = new exSpriteAnimClip[3];
            for (int i = 0; i < 3; i++)
            {
                TarantulaBrood.BroodIdle[i] = Looped(sh, idle[i], "ModYsvTarantula" + idle[i]);
                TarantulaBrood.BroodRun[i] = Looped(sh, run[i], "ModYsvTarantula" + run[i]);
            }
        }

        // Hoarclaw: a pincer snap; Seize grabs the hero, then hurls him (Curling Stone: across ice he slides into the wall).
        static void HoarclawKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p) ?? a0; var v = Kit.Voice(p);
            int from = Strike.Mark(p);
            int snap = Kit.AddEffect(p, YsveldFx.ClawSnap, attach: true, destroyOnAnimEnd: true, offsetX: 20f, offsetY: 8f);
            int grab = Kit.AddEffect(p, YsveldFx.ClawGrab, attach: true, destroyOnAnimEnd: true, offsetX: 21f, offsetY: 8f);
            Strike.Feet(p, from, 8f);
            var sn = Kit.Melee(sh, "Snap", "ModYsvHoarclawSnap", v, 3, snap, 40f).Build();
            var sz = new ClipBuilder(sh, "Seize", "ModYsvHoarclawSeize").Once().EvF(0, "AnimInputMultiplyFreeFace", 0f)
                .Ev(1, "AnimInputMultiplyStop").Ev(1, "AnimInputOff").EvF(2, "AnimMoveStick", 140f).Ev(2, "AnimAttack", grab)
                .EvO(2, "AnimSound", v).Ev(3, "AnimMoveStop").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sn, 1.5f, rangeInner: 14f, rangeOuter: 34f));
            Kit.EnableSpecial(p, Kit.Attack(sp, sz, 0f, rangeInner: 10f, rangeOuter: 46f, rangeRetreat: 0f), 7f);
            Kit.Order(p, InOrder);
        }

        // Pale Empress: a wide fan of five aurora motes; Blizzard drifts after the hero for 3.4 s (Storm Queen: 8 s blizzards).
        static void EmpressKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var v = Kit.Voice(p);
            int from = Strike.Mark(p);
            var motes = new List<int>();
            foreach (var a in new[] { -28f, -14f, 0.01f, 14f, 28f }) motes.Add(Kit.AddEffect(p, YsveldFx.AuroraMote, offsetX: 10f, offsetY: 16f, angle: a));
            int storm = Kit.AddEffect(p, YsveldFx.Storm, offsetX: 14f, offsetY: 14f);
            Strike.Feet(p, from, 16f);
            var au = Kit.Shot(sh, "Aurora", "ModYsvEmpressAurora", 3, v, 0.02f, motes.ToArray()).Build();
            var bz = Special(sh, "Blizzard", "ModYsvEmpressBlizzard").Ev(4, "AnimAttack", storm).EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, au, 1.6f, rangeInner: 40f, rangeOuter: 110f, rangeRetreat: 35f));
            Kit.EnableSpecial(p, Kit.Attack(a0, bz, 0f, rangeInner: 20f, rangeOuter: 150f, rangeRetreat: 0f), 7f);
            Kit.Order(p, InOrder);
        }

        // Glasswing: a glass scythe (doubled after a hatch); Glass Cocoon shuts her in glass for 2 s: crack it 3 times.
        static void GlasswingKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var v = Kit.Voice(p);
            int from = Strike.Mark(p);
            int slash = Kit.AddEffect(p, YsveldFx.GlassSlash, attach: true, destroyOnAnimEnd: true, offsetX: 16f, offsetY: 9f);
            int dbl = Kit.AddEffect(p, YsveldFx.GlassDouble, attach: true, destroyOnAnimEnd: true, offsetX: 16f, offsetY: 9f);
            Strike.Feet(p, from, 10f);
            var sl = Kit.Melee(sh, "Slash", "ModYsvGlasswingSlash", v, 3, slash, 80f).Build();
            var sd = Kit.Melee(sh, "Slash", "ModYsvGlasswingSlashKeen", v, 3, dbl, 80f).Build();
            var co = Special(sh, "Cocoon", "ModYsvGlasswingCocoon").EvO(1, "AnimSound", v).Ev(4, "YsvCocoon").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sl, 1.4f, rangeInner: 14f, rangeOuter: 34f));
            atk.Add(Kit.Attack(a0, sd, 1.4f, rangeInner: 14f, rangeOuter: 34f));
            // a cornered moth: the bot cocoons when the hero is close
            Kit.EnableSpecial(p, Kit.Attack(a0, co, 0f, rangeInner: 0f, rangeOuter: 50f, rangeRetreat: 0f), 7f);
            Kit.Order(p, InOrder);
            GlasswingCocoon.CurledClip = Looped(sh, "Curled", "ModYsvGlasswingCurled");
            GlasswingCocoon.StunnedClip = Looped(sh, "Stunned", "ModYsvGlasswingStunned");
            GlasswingCocoon.KeenIdle = Looped(sh, "IdleKeen", "ModYsvGlasswingIdleKeen");
            GlasswingCocoon.KeenRun = Looped(sh, "RunKeen", "ModYsvGlasswingRunKeen");
            GlasswingCocoon.DoubleSlash = YsveldFx.GlassDouble;
        }

        // The Winter Bride: frost breath (twice as far, 2 pips a hit, when widowed); Train Sweep swings her train round her.
        static void BrideKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int from = Strike.Mark(p);
            var puffs = new List<int>(); var black = new List<int>();
            foreach (var a in new[] { -12f, 0.01f, 12f })
            {
                puffs.Add(Kit.AddEffect(p, YsveldFx.Breath, offsetX: 12f, offsetY: 14f, angle: a));
                black.Add(Kit.AddEffect(p, YsveldFx.BlackBreath, offsetX: 12f, offsetY: 14f, angle: a));
            }
            int sweep = Kit.AddEffect(p, YsveldFx.TrainSweep, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            Strike.Feet(p, from, 14f);
            Func<ClipBuilder, List<int>, exSpriteAnimClip> breath = (c, fx) => c.Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff")
                .Ev(3, "AnimAttack", fx[0]).EvO(3, "AnimSound", v).Ev(4, "AnimAttack", fx[1]).Ev(5, "AnimAttack", fx[2]).Ev(-1, "AnimRun").Build();
            Func<ClipBuilder, exSpriteAnimClip> sweepClip = c =>
                c.Once().Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop").Ev(3, "AnimAttack", sweep).EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, breath(new ClipBuilder(sh, "Breath", "ModYsvBrideBreath"), puffs), 1.8f, rangeInner: 14f, rangeOuter: 50f));
            atk.Add(Kit.Attack(a0, breath(new ClipBuilder(sh, "BreathWidow", "ModYsvBrideBreathWidow"), black), 1.8f, rangeInner: 14f, rangeOuter: 90f));
            Kit.SetSpecial(p, Kit.Attack(sp, sweepClip(new ClipBuilder(sh, "Sweep", "ModYsvBrideSweep")), 0f, rangeInner: 0f, rangeOuter: 40f, rangeRetreat: 0f), 7f);
            Kit.Order(p, InOrder);
            BrideWidowed.WidowIdle = Looped(sh, "IdleWidow", "ModYsvBrideIdleWidow");
            BrideWidowed.WidowRun = Looped(sh, "RunWidow", "ModYsvBrideRunWidow");
            BrideWidowed.WidowSweep = sweepClip(new ClipBuilder(sh, "SweepWidow", "ModYsvBrideSweepWidow"));
        }

        // Snow Wraith: ice claws rake; Maelstrom drags the hero in for 2.2 s, then bursts (Cold Presence: pips up close).
        static void WraithKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p) ?? a0; var v = Kit.Voice(p);
            int from = Strike.Mark(p);
            int claw = Kit.AddEffect(p, YsveldFx.WraithClaw, attach: true, destroyOnAnimEnd: true, offsetX: 13f, offsetY: 12f);
            int vortex = Kit.AddEffect(p, YsveldFx.Vortex, spawnPoint: DamageEffectData.eSpawnPoint.ClosestEnemy);
            Strike.Feet(p, from, 12f);
            var cl = Kit.Melee(sh, "Claw", "ModYsvWraithClaw", v, 3, claw, 60f).Build();
            var ml = Special(sh, "Maelstrom", "ModYsvWraithMaelstrom").Ev(4, "AnimAttack", vortex).EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, cl, 1.5f, rangeInner: 14f, rangeOuter: 32f));
            Kit.EnableSpecial(p, Kit.Attack(sp, ml, 0f, rangeInner: 20f, rangeOuter: 130f, rangeRetreat: 0f), 7f);
            Kit.Order(p, InOrder);
        }

        // Rime Colossus: a two-fisted slam with a quake (+0.3 on ice); Glacier Run paves an ice road and belly-slides down it.
        static void ColossusKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int from = Strike.Mark(p);
            int slam = Kit.AddEffect(p, YsveldFx.Slam, attach: true, destroyOnAnimEnd: true, offsetX: 18f, offsetY: 6f);
            int slamIce = Kit.AddEffect(p, YsveldFx.SlamIce, attach: true, destroyOnAnimEnd: true, offsetX: 18f, offsetY: 6f);
            int quake = Kit.AddEffect(p, YsveldFx.Quake, offsetX: 18f, offsetY: 0f);
            int runner = Kit.AddEffect(p, YsveldFx.GlacierRunner, offsetX: 18f, offsetY: 0f);
            int belly = Kit.AddEffect(p, YsveldFx.BellyHit, attach: true, destroyOnAnimEnd: true, offsetX: 14f, offsetY: 8f);
            int spray = Kit.AddEffect(p, YsveldFx.BellySpray, attach: true, destroyOnAnimEnd: true, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            Strike.Feet(p, from, 12f);
            var sl = Kit.Melee(sh, "Slam", "ModYsvColossusSlam", v, 3, slam, 30f).Ev(3, "AnimAttack", quake).Build();
            var si = Kit.Melee(sh, "Slam", "ModYsvColossusSlamIce", v, 3, slamIce, 30f).Ev(3, "AnimAttack", quake).Build();
            var gl = Special(sh, "Glacier", "ModYsvColossusGlacier").EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(1, "AnimInputMultiplyStop")
                .Ev(2, "AnimAttack", runner).EvO(2, "AnimSound", v)
                .EvF(5, "AnimMoveStick", 230f).Ev(5, "AnimAttack", belly).Ev(5, "AnimAttack", spray).EvO(5, "AnimSound", v)
                .Ev(9, "AnimMoveStop").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sl, 1.8f, rangeInner: 18f, rangeOuter: 40f));
            atk.Add(Kit.Attack(a0, si, 1.8f, rangeInner: 18f, rangeOuter: 40f));
            Kit.SetSpecial(p, Kit.Attack(sp, gl, 0f, rangeInner: 40f, rangeOuter: 130f, rangeRetreat: 0f), 7.5f);
            Kit.Order(p, InOrder);
            ColossusDownhill.IceIdle = Looped(sh, "IdleIce", "ModYsvColossusIdleIce");
            ColossusDownhill.IceRun = Looped(sh, "RunIce", "ModYsvColossusRunIce");
        }

        // Rime Warden: an overhead mace smash; Shield Rush charges behind the shield (it stops shots from the front).
        static void WardenKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p) ?? a0; var v = Kit.Voice(p);
            int from = Strike.Mark(p);
            int smash = Kit.AddEffect(p, YsveldFx.Smash, attach: true, destroyOnAnimEnd: true, offsetX: 18f, offsetY: 6f);
            int rush = Kit.AddEffect(p, YsveldFx.RushHit, attach: true, destroyOnAnimEnd: true, offsetX: 14f, offsetY: 10f);
            Strike.Feet(p, from, 12f);
            var sm = Kit.Melee(sh, "Smash", "ModYsvWardenSmash", v, 4, smash, 40f).Build();
            var ru = Special(sh, "Rush", "ModYsvWardenRush").EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(0, "YsvShieldUp")
                .Ev(1, "AnimInputMultiplyStop").EvF(2, "AnimMoveStick", 180f).Ev(2, "AnimAttack", rush).EvO(2, "AnimSound", v)
                .Ev(6, "AnimMoveStop").Ev(7, "YsvShieldDown").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sm, 1.7f, rangeInner: 16f, rangeOuter: 34f));
            Kit.EnableSpecial(p, Kit.Attack(sp, ru, 0f, rangeInner: 30f, rangeOuter: 70f, rangeRetreat: 0f), 7f);
            Kit.Order(p, InOrder);
            WardenChallenge.ChallengeClip = sh.Has("Challenge") ? new ClipBuilder(sh, "Challenge", "ModYsvWardenChallenge").Once().Build() : null;
        }

        // The Geode: the dome slams; Geode Burst splits its seam and fires 4 crystals (Split: at half health, in two).
        static void GeodeKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p) ?? a0; var v = Kit.Voice(p);
            int from = Strike.Mark(p);
            int slam = Kit.AddEffect(p, YsveldFx.GeodeSlam, attach: true, destroyOnAnimEnd: true, offsetX: 15f, offsetY: 5f);
            int half = Kit.AddEffect(p, YsveldFx.HalfSlam, attach: true, destroyOnAnimEnd: true, offsetX: 10f, offsetY: 4f);
            var shards = new List<int>();
            foreach (var a in new[] { -18f, -6f, 6f, 18f }) shards.Add(Kit.AddEffect(p, YsveldFx.GeodeShard, offsetX: 14f, offsetY: 10f, angle: a));
            Strike.Feet(p, from, 10f);
            var sl = Kit.Melee(sh, "Slam", "ModYsvGeodeSlam", v, 3, slam, 30f).Build();
            var hs = Kit.Melee(sh, "HalfSlam", "ModYsvGeodeHalfSlam", v, 3, half, 40f).Build();
            Func<string, string, exSpriteAnimClip> burst = (anim, clip) =>
            {
                var c = Special(sh, anim, clip).EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(2, "AnimInputMultiplyStop");
                for (int i = 0; i < shards.Count; i++) c.Ev(3, "AnimAttack", shards[i], i * 0.03f);
                return c.EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            };
            atk.Clear();
            atk.Add(Kit.Attack(a0, sl, 1.8f, rangeInner: 16f, rangeOuter: 34f));
            atk.Add(Kit.Attack(a0, hs, 1.5f, rangeInner: 12f, rangeOuter: 26f));
            Kit.EnableSpecial(p, Kit.Attack(sp, burst("Burst", "ModYsvGeodeBurst"), 0f, rangeInner: 20f, rangeOuter: 90f, rangeRetreat: 0f), 7f);
            Kit.Order(p, InOrder);
            GeodeSplit.SeamIdle = Looped(sh, "IdleSeam", "ModYsvGeodeIdleSeam");
            GeodeSplit.SeamRun = Looped(sh, "RunSeam", "ModYsvGeodeRunSeam");
            GeodeSplit.SplitClip = sh.Has("Split") ? new ClipBuilder(sh, "Split", "ModYsvGeodeSplit").Once().Build() : null;
            GeodeSplit.HalfIdle = Looped(sh, "HalfIdle", "ModYsvGeodeHalfIdle");
            GeodeSplit.HalfRun = Looped(sh, "HalfRun", "ModYsvGeodeHalfRun");
            GeodeSplit.HalfBurst = burst("HalfBurst", "ModYsvGeodeHalfBurst");
        }

        // Prism Oracle: a prism bolt (Ice Lens: it bends over ice); Sunburst runs her light slab by slab through the ice.
        static void OracleKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p) ?? a0; var v = Kit.Voice(p);
            int from = Strike.Mark(p);
            int bolt = Kit.AddEffect(p, YsveldFx.PrismBolt, offsetX: 9f, offsetY: 14f);
            Strike.Feet(p, from, 14f);
            var bo = Kit.Shot(sh, "Bolt", "ModYsvOracleBolt", 3, v, 0f, bolt).Build();
            var sb = Special(sh, "Sunburst", "ModYsvOracleSunburst").Ev(3, "YsvSunburst").EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, bo, 1.5f, rangeInner: 40f, rangeOuter: 110f, rangeRetreat: 35f));
            Kit.EnableSpecial(p, Kit.Attack(sp, sb, 0f, rangeInner: 0f, rangeOuter: 80f, rangeRetreat: 0f), 7f);
            Kit.Order(p, InOrder);
        }

        // ---------------------------------------------------------------------------------------------- minions
        // Broodling (hatched by the Matron, shaken off the Tarantula; not in the roster): a small frost bite.
        static void BroodlingKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var v = Kit.Voice(p);
            int from = Strike.Mark(p);
            int bite = Kit.AddEffect(p, YsveldFx.BroodBite, attach: true, destroyOnAnimEnd: true, offsetX: 6f, offsetY: 2f);
            Strike.Feet(p, from, 3f);
            var bt = Kit.Melee(sh, "Bite", "ModYsvBroodlingBite", v, 3, bite, 60f).Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, bt, 1.4f, rangeInner: 8f, rangeOuter: 18f));
            MinionAI.Tune(p, 120f, 8f, 12f, 1.2f, 1.8f, 1.5f);   // jaws reach x 10
        }

        // The Geode's other half after a Split (not in the roster): a smaller dome slam.
        static void GeodeHalfKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var v = Kit.Voice(p);
            int from = Strike.Mark(p);
            int slam = Kit.AddEffect(p, YsveldFx.HalfSlam, attach: true, destroyOnAnimEnd: true, offsetX: 10f, offsetY: 4f);
            Strike.Feet(p, from, 6f);
            var sl = Kit.Melee(sh, "Slam", "ModYsvGeodeHalfMinionSlam", v, 3, slam, 40f).Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sl, 1.6f, rangeInner: 10f, rangeOuter: 22f));
            R.Set(p, "m_hasSpecialAttack", false);
            MinionAI.Tune(p, 160f, 12f, 18f, 1.4f, 2.0f, 1.2f);
        }

        // The perk: every Ysveld monster leaves a 3-slab ice patch where it dies and gets the ice brain (25% faster on ice).
        static void Frostbound(GameObject go, Player p)
        {
            Kit.AddDeathSpawn(p, YsveldFx.DeathIce);
            Strike.DeathAtFeet(p);
            YsveldFx.Hook(go, i => { if (i.GetComponent<YsvMonster>() == null) i.AddComponent<YsvMonster>(); });
        }

        public static readonly MonsterDef Broodling = new MonsterDef
        {
            id = "YsvBroodling", art = "YsvBroodling", basePrefab = "EnemyTinyRatFodder", health = 0.6f, speedMult = 1.25f, kit = BroodlingKit
        };

        public static readonly MonsterDef GeodeHalf = new MonsterDef
        {
            id = "YsvGeodeHalf", art = "YsvGeodeHalf", basePrefab = "EnemyTinyRatFodder", health = 3f, kit = GeodeHalfKit, customize = Frostbound
        };

        // Evolution tree: every evolution has exactly one parent, no two monsters offer the same one.
        //   Rimeling  -> Silk Weaver | Rime Lurker     Silk Weaver  -> Widow Matron | Loom Widow
        //   Hoarmoth  -> Silkmoth | Veil Witch         Rime Lurker  -> Hoarfrost Tarantula | Hoarclaw
        //   Shardling -> Rime Knight | Shard Hermit    Silkmoth     -> Pale Empress | Glasswing
        //                                              Veil Witch   -> Winter Bride | Snow Wraith
        //                                              Rime Knight  -> Rime Colossus | Rime Warden
        //                                              Shard Hermit -> The Geode | Prism Oracle
        public static readonly List<MonsterDef> Monsters = new List<MonsterDef>
        {
            new MonsterDef { id = "YsvRimeling", art = "YsvRimeling", basePrefab = "EnemyGiantSpider_Standard", health = 3.5f, evolveCost = 0f,
                             evolveTo = new[] { "YsvWeaver", "YsvLurker" }, kit = RimelingKit, customize = Frostbound },
            new MonsterDef { id = "YsvHoarmoth", art = "YsvHoarmoth", basePrefab = "EnemyFlyingEye_Dodge", health = 3f, evolveCost = 0f,
                             evolveTo = new[] { "YsvSilkmoth", "YsvVeilWitch" }, kit = HoarmothKit, customize = Frostbound },
            new MonsterDef { id = "YsvShardling", art = "YsvShardling", basePrefab = "EnemyGnome", health = 4.5f, speedMult = 0.9f, evolveCost = 0f,
                             evolveTo = new[] { "YsvRimeKnight", "YsvHermit" }, kit = ShardlingKit, customize = Frostbound },
            // ---- T2
            new MonsterDef { id = "YsvWeaver", art = "YsvWeaver", basePrefab = "EnemyGiantSpider_SpitWebs", health = 6f, evolveCost = 2.5f,
                             evolveTo = new[] { "YsvMatron", "YsvLoom" }, kit = WeaverKit, customize = Frostbound },
            new MonsterDef { id = "YsvLurker", art = "YsvLurker", basePrefab = "EnemyGiantSpider_Standard", health = 6.5f, speedMult = 0.95f, evolveCost = 2.5f,
                             evolveTo = new[] { "YsvTarantula", "YsvHoarclaw" }, kit = LurkerKit, customize = Frostbound },
            new MonsterDef { id = "YsvSilkmoth", art = "YsvSilkmoth", basePrefab = "EnemyFlyingEye_Rapidfire", health = 5.5f, evolveCost = 2.5f,
                             evolveTo = new[] { "YsvEmpress", "YsvGlasswing" }, kit = SilkmothKit, customize = Frostbound },
            new MonsterDef { id = "YsvVeilWitch", art = "YsvVeilWitch", basePrefab = "EnemySkeletonMage", health = 5.5f, evolveCost = 2.5f,
                             evolveTo = new[] { "YsvBride", "YsvWraith" }, kit = WitchKit, customize = Frostbound },
            new MonsterDef { id = "YsvRimeKnight", art = "YsvRimeKnight", basePrefab = "EnemyOrc", health = 7f, speedMult = 0.9f, evolveCost = 2.5f,
                             evolveTo = new[] { "YsvColossus", "YsvWarden" }, kit = KnightKit, customize = Frostbound },
            new MonsterDef { id = "YsvHermit", art = "YsvHermit", basePrefab = "EnemyWildShaman", health = 6f, speedMult = 0.9f, evolveCost = 2.5f,
                             evolveTo = new[] { "YsvGeode", "YsvOracle" }, kit = HermitKit, customize = Frostbound },
            // ---- T3
            new MonsterDef { id = "YsvMatron", art = "YsvMatron", basePrefab = "EnemyScorpion", health = 11.5f, speedMult = 0.85f, evolveCost = 4.5f,
                             kit = MatronKit, customize = Frostbound },
            new MonsterDef { id = "YsvLoom", art = "YsvLoom", basePrefab = "EnemyPriestess", health = 11f, speedMult = 0.9f, evolveCost = 4.5f,
                             kit = LoomKit, customize = Frostbound },
            new MonsterDef { id = "YsvTarantula", art = "YsvTarantula", basePrefab = "EnemyGhoul", health = 12f, speedMult = 0.85f, evolveCost = 4.5f,
                             kit = TarantulaKit, customize = Frostbound },
            new MonsterDef { id = "YsvHoarclaw", art = "YsvHoarclaw", basePrefab = "EnemyScorpion", health = 11.5f, speedMult = 0.9f, evolveCost = 4.5f,
                             kit = HoarclawKit, customize = Frostbound },
            new MonsterDef { id = "YsvEmpress", art = "YsvEmpress", basePrefab = "EnemyFlyingEye_Red", health = 10.5f, speedMult = 0.85f, evolveCost = 4.5f,
                             kit = EmpressKit, customize = Frostbound },
            new MonsterDef { id = "YsvGlasswing", art = "YsvGlasswing", basePrefab = "EnemyBeholder", health = 10.5f, evolveCost = 4.5f,
                             kit = GlasswingKit, customize = Frostbound },
            new MonsterDef { id = "YsvBride", art = "YsvBride", basePrefab = "EnemySkeletonPope", health = 11f, speedMult = 0.8f, evolveCost = 4.5f,
                             kit = BrideKit, customize = Frostbound },
            new MonsterDef { id = "YsvWraith", art = "YsvWraith", basePrefab = "EnemyFacelessShaman", health = 10.5f, speedMult = 0.95f, evolveCost = 4.5f,
                             kit = WraithKit, customize = Frostbound },
            new MonsterDef { id = "YsvColossus", art = "YsvColossus", basePrefab = "EnemyTroll", health = 12f, speedMult = 0.85f, evolveCost = 4.5f,
                             kit = ColossusKit, customize = Frostbound },
            new MonsterDef { id = "YsvWarden", art = "YsvWarden", basePrefab = "EnemyDarkGuardian", health = 12f, speedMult = 0.85f, evolveCost = 4.5f,
                             kit = WardenKit, customize = Frostbound },
            new MonsterDef { id = "YsvGeode", art = "YsvGeode", basePrefab = "EnemyMinotaur", health = 12f, speedMult = 0.8f, evolveCost = 4.5f,
                             kit = GeodeKit, customize = Frostbound },
            new MonsterDef { id = "YsvOracle", art = "YsvOracle", basePrefab = "EnemyWitch", health = 10.5f, speedMult = 0.9f, evolveCost = 4.5f,
                             kit = OracleKit, customize = Frostbound },
        };

        /// <summary>Each monster's signature behaviour (the others carry theirs on their effects).</summary>
        static readonly Dictionary<string, Type> Quirks = new Dictionary<string, Type>
        {
            { "YsvRimeling", typeof(RimelingSnap) }, { "YsvHermit", typeof(HermitTriangle) }, { "YsvMatron", typeof(MatronWrap) },
            { "YsvLoom", typeof(LoomSpool) }, { "YsvTarantula", typeof(TarantulaBrood) }, { "YsvEmpress", typeof(EmpressStormQueen) },
            { "YsvGlasswing", typeof(GlasswingCocoon) }, { "YsvBride", typeof(BrideWidowed) }, { "YsvWraith", typeof(WraithPresence) },
            { "YsvColossus", typeof(ColossusDownhill) }, { "YsvWarden", typeof(WardenChallenge) }, { "YsvGeode", typeof(GeodeSplit) },
            { "YsvOracle", typeof(OracleSunburst) }, { "YsvGeodeHalf", typeof(GeodeHalfCore) },
        };

        public static readonly GodDef God = new GodDef
        {
            name = "Ysveld",
            text = "Blizzards lay sliding ice",
            flavour = "The Frost Widow's web\nis made of ice.",
            winText = "THE WIDOW'S VEIL IS LIFTED",
            portraitArt = "DeityYsveld",
            startingMonsters = new[] { "YsvRimeling", "YsvHoarmoth", "YsvShardling" },
        };

        static List<DamageEffectData> SpecialFx(Powerup pu) { return R.Get<List<DamageEffectData>>(pu, "m_specialAttackDamageEffects"); }

        public static readonly List<ItemDef> Items = new List<ItemDef>
        {
            new ItemDef { id = "SpellYsvRequiem", cloneFrom = "SpellTribalShield", cost = 45, group = "GroupSpellsPurchasable",
                name = "Icicle Requiem", description = "A ring of icicles falls around you a moment later",
                bubbleArt = "IconYsvRequiemBubble",
                customize = (go, pu) =>
                {
                    var sp = SpecialFx(pu);
                    if (sp.Count == 0 || YsveldFx.HeroRequiem == null) return;
                    // the item's own crowned icicles (art/out_itemfx): same 0.7 s fall and 18 x 10 shatter
                    ItemArt.Wear(YsveldFx.HeroIcicleMark, "FxItemIcicle", "Fall");
                    ItemArt.Wear(YsveldFx.HeroIcicleHit, "FxItemIcicle", "Shatter");
                    sp[0].m_object = YsveldFx.HeroRequiem;
                    sp[0].m_offsetX = new MinMaxRange(0f); sp[0].m_offsetY = new MinMaxRange(0f);
                } },
            new ItemDef { id = "ArtifactYsvShawl", cloneFrom = "PowerupAcidBlood", cost = 40, group = "GroupArtifactsPurchasable",
                name = "Widow's Shawl", description = "Frost silk bursts out when you are hit, slowing monsters",
                bubbleArt = "IconYsvShawlBubble", hudArt = "IconYsvShawlHud",
                customize = (go, pu) =>
                {
                    var e = R.Get<System.Collections.IList>(pu, "m_effects");
                    if (e == null) return;
                    ItemArt.Wear(YsveldFx.HeroNova, "FxItemShawl", "Nova");                       // frost-silk web, 48 x 20
                    var puff = ItemArt.Visual("ModItemShawlPuff", "FxItemShawl", "Puff");
                    if (e.Count > 0) { var d = e[0] as DamageEffectData; if (d != null) { d.m_object = YsveldFx.HeroNova; d.m_attach = false; } }
                    if (e.Count > 1) { var d = e[1] as DamageEffectData; if (d != null) { d.m_object = puff ?? YsveldFx.Puff; d.m_attach = false; } }
                } },
        };

        static Deity s_deity;
        static exSpriteAnimClip s_idol;

        public static void Register()
        {
            YsveldFx.Build();
            foreach (var m in Monsters) MonsterTraits.Register(m.PrefabName, TraitsFor(m.id));
            MonsterTraits.Register(Broodling.PrefabName, new MonsterTraits { lifetime = 8f, expireFx = YsveldFx.Puff });
            MonsterTraits.Register(GeodeHalf.PrefabName, TraitsFor(GeodeHalf.id));
            var brood = MonsterFactory.Build(Broodling);
            if (brood != null)
            {
                YsveldFx.EggSac = FxKit.MinionSpawner("ModYsvEggSac", brood.gameObject, "FxYsvEggSac", "Hatch");
                Strike.ArtAt(YsveldFx.EggSac, "FxYsvEggSac", 14, 18);
                YsveldFx.BroodShake = FxKit.MinionSpawner("ModYsvBroodShake", brood.gameObject, "FxYsvBroodFur", "Drop");
                Strike.ArtAt(YsveldFx.BroodShake, "FxYsvBroodFur", 10, 17);
            }
            var half = MonsterFactory.Build(GeodeHalf);
            if (half != null)
            {
                GeodeSplit.OtherHalf = FxKit.MinionSpawner("ModYsvGeodeHalfSpawn", half.gameObject, "FxYsvGeodeCrack", "Play");
                Strike.ArtAt(GeodeSplit.OtherHalf, "FxYsvGeodeCrack", 26, 36);
            }
            foreach (var m in Monsters) MonsterFactory.Build(m);
            MonsterFactory.LinkEvolutions(Monsters);
            s_deity = DeityFactory.Register(God);
            MonsterEvents.AttackSpawned += OnAttackSpawned;
            // the gold idol carved in the Frost Widow's likeness
            var prev = SlotGods.PortraitFor;
            SlotGods.PortraitFor = (tier, perk) => tier == SlotTier.Gold && perk != null && perk == s_deity ? Idol() : (prev != null ? prev(tier, perk) : null);
            Strike.KeepAllScales();

            // Items: ItemPack.Register builds everything in ItemPack.Items. If it has already run (pack order changed),
            // build ours now; otherwise just queue them, so each item is built exactly once either way.
            bool itemsDone = ItemPack.Built.ContainsKey("SpellWickwalk");
            foreach (var def in Items)
            {
                if (itemsDone)
                {
                    try { ItemRegistry.Register(def); }
                    catch (Exception e) { Plugin.Log.LogError("Item " + def.id + " failed: " + e); }
                }
                if (!ItemPack.Items.Contains(def)) ItemPack.Items.Add(def);
            }
        }

        static MonsterTraits TraitsFor(string id)
        {
            var t = id == "YsvRimeKnight"
                ? new MonsterTraits { maxPlates = 2, plateFx = YsveldFx.Plates, plateBreakFx = YsveldFx.PlateBreak }
                : new MonsterTraits();
            Type q;
            if (Quirks.TryGetValue(id, out q)) t.behaviours.Add(q);
            return t;
        }

        static exSpriteAnimClip Idol()
        {
            if (s_idol == null) s_idol = SlotArt.Clip("DeityYsvIdol", "Idle");
            return s_idol;
        }

        static void OnAttackSpawned(Player owner, GameObject fx, GameObject template)
        {
            var q = owner != null && fx != null ? owner.GetComponent<YsveldBehaviour>() : null;
            if (q != null) q.OnAttackSpawned(fx, template);
        }
    }
}
