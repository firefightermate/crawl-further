using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Content.Secrets
{
    using CrawlFurther.Art;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;
    using CrawlFurther.Content.Gods.Vhorrul;

    // =====================================================================================================================
    // GOLD SECRET: the Gilded Secret, a 1 / 2 / 4 monster line with no god of its own. It is offered ONLY as the last
    // entry of a gold idol's 4th starter slot (CustomGod reads GoldSecret.StarterId). Art: tools/sprites/goldsecret_rigs.py
    // -> art/out_goldsecret (TIMING.md there). Tips: data/tips/tips_goldsecret.json.
    //
    //   Coffer Mimic (T1)  -> Vault Warden (T2) -> Hoard Wyrm, Vault Colossus
    //                      -> Gilt Regent (T2)  -> Gilded Sovereign, Grand Treasurer
    // =====================================================================================================================

    /// <summary>The Gilded Secret's effect templates and indicators.</summary>
    public static class GoldFx
    {
        public static GameObject HitSplat, MimicSnap, MimicSpring, Coins,
                                 KeySwing, KeyShot, ChainLink, Clank,
                                 Bolt, BoltPop, Seal, Tithe, Ripple,
                                 WyrmMaul, MoltenGlob, MoltenPool, Shatter,
                                 VaultSlam, Quake, Payout, Ingot,
                                 Smite, SmiteFx, Kneel, Jewel, JewelBreak, Shard,
                                 Quill, Ink, Mark, Interest, Stamp;
        public static StatusOverlayDef[] IndBank;
        public static StatusOverlayDef IndShackle, IndTax, IndGilded, IndDebt;

        public static void Build()
        {
            var goo = FxFactory.GetStatus("StatusLavaSteveGoo");
            var daze = FxFactory.GetStatus("StatusDizzy");

            HitSplat = GodArt.HitSplat("ModGoldHitSplat", "FxGiltSplat", 11, 11);

            // ---- Coffer Mimic: the lid snap (jaws at (9, -8) on Snap f3) and the bigger ambush bite out of Play Dead.
            // The bite itself is drawn on the body frames, so only the boxes turn with the aim.
            MimicSnap = AimedMelee.Rotating(FxKit.BodyHit("ModGoldMimicSnap", 0.9f, 0f, 0.6f, 0.12f));
            Strike.HitBox(MimicSnap, 12f, 10f);                       // at (9, 6): x 3..15, y 1..11
            MimicSpring = AimedMelee.Rotating(FxKit.BodyHit("ModGoldMimicSpring", 1.3f, 0f, 1.4f, 0.15f));
            Strike.HitBox(MimicSpring, 18f, 14f);                     // at (10, 7): x 1..19, y 0..14
            Coins = FxKit.Visual("ModGoldCoins", "FxGiltHoard", "Cash");
            Strike.ArtAt(Coins, "FxGiltHoard", 9, 20);

            // ---- Vault Warden: the key swing (art arc about the shoulder) and the thrown key on its chain
            KeySwing = FxKit.Swipe("ModGoldKeySwing", "OrcSwipe", 1.1f, 0.9f);
            GodArt.Swipe(KeySwing, "FxGiltKeyArc", "Swing", 15, 21);
            Strike.Collider(KeySwing, 22f, 16f, 11f, 2f);             // spawned at (5, 5): x 5..27, y -1..15 (key bit (24, 6))
            KeyShot = FxKit.Projectile("ModGoldKey", "DFX_skelMageNewProjectile", "FxGiltKey", "Fly", 200f, 0.55f, 0.6f, 0.2f, rotate: false);
            Strike.ArtAt(KeyShot, "FxGiltKey", 10, 8);
            ChainLink = FxKit.Visual("ModGoldChainLink", "FxGiltChain", "Link", loop: true);
            if (ChainLink != null) { FxFactory.SetEffect(ChainLink, destroyOnAnimEnd: false, canFlip: false, freeRotate: true); Strike.ArtAt(ChainLink, "FxGiltChain", 4, 3); }
            Clank = FxKit.Visual("ModGoldClank", "FxGiltClank", "Play");
            Strike.ArtAt(Clank, "FxGiltClank", 9, 19);

            // ---- Gilt Regent: scepter bolt, the decree's seal (lands f5-f6), the tithe and Royal Distance
            BoltPop = FxKit.Visual("ModGoldBoltPop", "FxGiltBoltPop", "Play");
            Strike.ArtAt(BoltPop, "FxGiltBoltPop", 10, 13);
            Bolt = FxKit.Projectile("ModGoldBolt", "DFX_skelMageNewProjectile", "FxGiltBolt", "Fly", 170f, 0.8f, 0.9f, 0.4f);
            if (Bolt != null) { Strike.ArtAt(Bolt, "FxGiltBolt", 12, 4); FxFactory.SetContacts(Bolt, destroyOnHit: true, spawnOnHit: BoltPop); }
            Seal = FxKit.TimedHit("ModGoldSeal", "TrollGroundPoundBigShockwave", "FxGiltSeal", "Fall", 5, 7, 0.7f, 0.8f, canFlip: false);
            Strike.Ground(Seal, "FxGiltSeal", 17, 43, 24f, 10f);     // the seal lands r 11 (ring), wax splash r 6.5
            Tithe = FxKit.Visual("ModGoldTithe", "FxGiltTithe", "Play");
            Strike.ArtAt(Tithe, "FxGiltTithe", 8, 20);
            Ripple = FxKit.TimedHit("ModGoldRipple", "TrollGroundPoundBigShockwave", "FxGiltRipple", "Play", 0, 2, 0.3f, 2.4f, canFlip: false);
            Strike.Ground(Ripple, "FxGiltRipple", 24, 10, 36f, 14f); // ring r 13 while live

            // ---- Hoard Wyrm: the maul (jaws at (31, -8)), molten globs that land as molten gold pools, the shatter
            WyrmMaul = AimedMelee.Rotating(FxKit.BodyHit("ModGoldWyrmMaul", 1.4f, 0f, 1.0f, 0.12f));
            Strike.HitBox(WyrmMaul, 18f, 14f);                        // at (24, 7): x 15..33, y 0..14
            MoltenPool = FxKit.TimedHit("ModGoldMoltenPool", "TrollGroundPoundBigShockwave", "FxGiltPool", "Life", 1, 7, 0.35f, 0.1f, goo, 0.5f,
                                        rate: 0.5f, canFlip: false);
            Strike.Ground(MoltenPool, "FxGiltPool", 13, 5, 22f, 8f);
            MoltenGlob = FxKit.Projectile("ModGoldMoltenGlob", "webBall", "FxGiltMolten", "Fly", 150f, 0.7f, 0.6f, 0.2f, accel: 20f, speedMax: 8f);
            if (MoltenGlob != null)
            {
                Strike.ArtAt(MoltenGlob, "FxGiltMolten", 7, 4 + 12);  // rolls on the floor line, art 12 px up (released at the jaws' height)
                FxFactory.SetEffect(MoltenGlob, destroyOnAnimEnd: false, destroyAfter: 0.7f, spawnOnDestroy: MoltenPool, freeRotate: false);
                FxFactory.SetContacts(MoltenGlob, destroyOnHit: true, spawnOnHit: MoltenPool);
            }
            Shatter = FxKit.TimedHit("ModGoldShatter", "TrollGroundPoundBigShockwave", "FxGiltShatter", "Play", 0, 2, 0.8f, 1.0f, canFlip: false);
            Strike.Ground(Shatter, "FxGiltShatter", 16, 17, 16f, 12f);

            // ---- Vault Colossus: ingot fists + quake, and the payout ring (damage set per spawn) with flung ingots
            VaultSlam = FxKit.BodyHit("ModGoldVaultSlam", 1.5f, 0f, 1.4f, 0.12f);
            Strike.HitBox(VaultSlam, 20f, 14f);                       // at (15, 4): x 5..25 (fists land at x 9..17)
            Quake = FxKit.TimedHit("ModGoldQuake", "TrollGroundPoundBigShockwave", "FxGiltQuake", "Ring", 0, 3, 0.5f, 0.9f, canFlip: false);
            Strike.Ground(Quake, "FxGiltQuake", 21, 9, 40f, 14f);
            Payout = FxKit.TimedHit("ModGoldPayout", "TrollGroundPoundBigShockwave", "FxGiltPayout", "Play", 0, 3, VaultBank.BaseDamage, 1.6f, canFlip: false);
            Strike.Ground(Payout, "FxGiltPayout", 33, 14, 60f, 22f);   // ring r 16..31 while live
            Ingot = FxKit.Projectile("ModGoldIngot", "DFX_skelMageNewProjectile", "FxGiltIngot", "Fly", 180f, 0.7f, 0.6f, 0.6f, rotate: false);
            Strike.ArtAt(Ingot, "FxGiltIngot", 6, 5);

            // ---- Gilded Sovereign: the smite (sapphire head at (24, -6)), Kneel (closes f0-f6, slams f7-f8), crown jewels
            Smite = FxKit.BodyHit("ModGoldSmite", 1.3f, 0f, 1.2f, 0.12f);
            Strike.HitBox(Smite, 16f, 14f);                           // at (21, 6): x 13..29, y -1..13
            SmiteFx = FxKit.Visual("ModGoldSmiteFx", "FxGiltSmite", "Play");
            Strike.ArtAt(SmiteFx, "FxGiltSmite", 17, 13);
            Kneel = FxKit.TimedHit("ModGoldKneel", "TrollGroundPoundBigShockwave", "FxGiltKneel", "Play", 7, 9, 1.2f, 0.6f, daze, 1f, canFlip: false);
            Strike.Ground(Kneel, "FxGiltKneel", 24, 12, 30f, 13f);   // the slam ring r 9..14
            Jewel = FxKit.Visual("ModGoldJewel", "FxGiltJewel", "Orbit", loop: true);
            if (Jewel != null) { FxFactory.SetEffect(Jewel, destroyOnAnimEnd: false, canFlip: false, freeRotate: false); Strike.ArtAt(Jewel, "FxGiltJewel", 12, 9); }
            JewelBreak = FxKit.Visual("ModGoldJewelBreak", "FxGiltJewel", "Break");
            Strike.ArtAt(JewelBreak, "FxGiltJewel", 12, 9);
            Shard = FxKit.Projectile("ModGoldShard", "DFX_skelMageNewProjectile", "FxGiltShard", "Fly", 210f, 0.7f, 0.5f, 0.3f);
            Strike.ArtAt(Shard, "FxGiltShard", 10, 3);

            // ---- Grand Treasurer: quills that leave ink, the audit page (lands f4), interest, the PAID stamp
            Ink = Zone("ModGoldInk", "FxGiltInk", 12, 6, 20f, 7f, goo);
            Quill = FxKit.Projectile("ModGoldQuill", "DFX_skelMageNewProjectile", "FxGiltQuill", "Fly", 200f, 0.6f, 0.6f, 0.2f);
            if (Quill != null) { Strike.ArtAt(Quill, "FxGiltQuill", 12, 3); FxFactory.SetContacts(Quill, destroyOnHit: true, spawnOnHit: Ink); }
            Mark = FxKit.TimedHit("ModGoldMark", "TrollGroundPoundBigShockwave", "FxGiltMark", "Play", 4, 5, 0.2f, 0.1f, canFlip: false);
            Strike.Ground(Mark, "FxGiltMark", 10, 29, 22f, 10f);
            Interest = FxKit.TimedHit("ModGoldInterest", "TrollGroundPoundBigShockwave", "FxGiltInterest", "Play", 2, 4, 0.3f, 0.6f, canFlip: false);
            Strike.Ground(Interest, "FxGiltInterest", 17, 23, 20f, 12f);
            Stamp = FxKit.Visual("ModGoldStamp", "FxGiltStamp", "Play");
            Strike.ArtAt(Stamp, "FxGiltStamp", 10, 19);

            // ---- indicators (stacks over heads, marks on the hero)
            IndBank = new[]
            {
                ModStatus.Indicator("ModIndGoldBank1", "FxGiltBank", "One", 1f, OverlayAt.Head),
                ModStatus.Indicator("ModIndGoldBank2", "FxGiltBank", "Two", 1f, OverlayAt.Head),
                ModStatus.Indicator("ModIndGoldBank3", "FxGiltBank", "Three", 1f, OverlayAt.Head),
            };
            IndShackle = ModStatus.Indicator("ModIndGoldShackle", "FxGiltShackle", "Loop", -2f, OverlayAt.Feet);
            IndTax = ModStatus.Indicator("ModIndGoldTax", "FxGiltTax", "Loop", 1f, OverlayAt.Head);
            IndGilded = ModStatus.Indicator("ModIndGoldGilded", "FxGiltGilded", "Loop", -2f, OverlayAt.Feet);
            IndDebt = ModStatus.Indicator("ModIndGoldDebt", "FxGiltDebt", "Loop", 1f, OverlayAt.Head);
            Plugin.Log.LogInfo("Gilded Secret FX templates built");
        }

        /// <summary>A floor zone (lava-zone clone) wearing a Life anim, applying a status while live.</summary>
        static GameObject Zone(string name, string sheet, int gx, int gy, float w, float h, Status status)
        {
            var go = FxFactory.Clone("LavaEffectLongerReworkZone", name);
            var sh = SpriteSheets.Get(sheet);
            if (go == null || sh == null) return go;
            FxFactory.Reskin(go, new ClipBuilder(sh, "Life", name + "Life").Once().Ev(1, "AnimDamageOn").Ev(-3, "AnimDamageOff").Build(), sh);
            FxFactory.SetEffect(go, destroyOnAnimEnd: true, snap: 1f);
            FxFactory.SetStatusZone(go, status, hitsHero: true, hitsMonster: false);
            FxKit.NoTint(go);
            Strike.Ground(go, sheet, gx, gy, w, h);
            return go;
        }
    }

    /// <summary>The Gilded Secret pack: seven monsters, no god, registered after the gods (see ContentManager).</summary>
    public static class GoldSecretPack
    {
        public const string Starter = "GoldMimic";
        static bool s_done;

        static ClipBuilder Cast(SpriteSheet sh, string anim, string clip, int release)
        {
            return new ClipBuilder(sh, anim, clip).Once().EvF(0, "AnimInputMultiplyFreeFace", 0f)
                .Ev(Mathf.Max(0, release - 1), "AnimInputMultiplyStop").Ev(Mathf.Max(0, release - 1), "AnimInputOff").Ev(release, "AnimMoveStop");
        }

        // Coffer Mimic (T1): Snap lunges with the lid and steals gold; Play Dead shuts the lid and lies still as a plain
        // chest (a quarter damage, but hits knock gold loose) for up to 2.4 s, springing a big bite the moment the hero
        // comes within 26 px (CofferMimic).
        static void MimicKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int snap = Kit.AddEffect(p, GoldFx.MimicSnap, attach: true, destroyOnAnimEnd: true, offsetX: 9f, offsetY: 6f);
            int spring = Kit.AddEffect(p, GoldFx.MimicSpring, attach: true, destroyOnAnimEnd: true, offsetX: 10f, offsetY: 7f);
            // Feign 3 + Lurk 4 x 2 + Spring 5 = 16 frames; frame 11 is the first Spring frame (CofferMimic jumps there)
            var pd = new ClipBuilder(sh, "Feign", "ModGoldMimicPlayDead").Once().Then("Lurk", 2).Then("Spring")
                .Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop").Ev(1, "GoldFeignOn")
                .Ev(CofferMimic.SpringFrame, "GoldFeignOff").EvF(CofferMimic.SpringFrame, "AnimMove", 90f)
                .Ev(CofferMimic.SpringFrame + 1, "AnimAttack", spring)
                .EvO(CofferMimic.SpringFrame + 1, "AnimSound", v).Ev(CofferMimic.SpringFrame + 3, "AnimMoveStop").Ev(-1, "AnimRun");
            atk.Clear();
            var bite = Kit.Attack(a0, Kit.Melee(sh, "Snap", "ModGoldMimicSnap", v, 3, snap, 60f).Build(), 1.2f, rangeInner: 8f, rangeOuter: 22f);
            AimedMelee.Angles(bite, sh, "Snap", a => Kit.Melee(sh, a, "ModGoldMimic" + a, v, 3, snap, 60f).Build());
            atk.Add(bite);
            Kit.SetSpecial(p, Kit.Attack(sp, pd.Build(), 0f, rangeInner: 0f, rangeOuter: 60f, rangeRetreat: 0f), 5.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 7f);
        }

        // Vault Warden (T2): Key Swing brings the great key round and down; Shackle hurls it on its chain: a hit chains the
        // hero to the Warden for 2.5 s (WardenGuard). Passive Strongbox: hits from in front deal 30 percent less.
        static void WardenKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int swing = Kit.AddEffect(p, GoldFx.KeySwing, attach: true, offsetX: 5f, offsetY: 5f);
            int key = Kit.AddEffect(p, GoldFx.KeyShot, offsetX: 12f, offsetY: 14f);
            var sw = Kit.Melee(sh, "Swing", "ModGoldWardenSwing", v, 3, swing, 40f).Build();
            var sk = Kit.Shot(sh, "Shackle", "ModGoldWardenShackle", 3, v, 0f, key).Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sw, 1.4f, rangeInner: 12f, rangeOuter: 30f));     // box to x 27 + hero half-width
            Kit.SetSpecial(p, Kit.Attack(sp, sk, 0f, rangeInner: 40f, rangeOuter: 110f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 14f);   // the key leaves the fist at (12, 14): fly level with the aim
        }

        // Gilt Regent (T2): Scepter Bolt; Decree drops a seal on the hero after a 0.5 s ring: if it lands he is Taxed for
        // 4 s (RegentCourt). Passive Royal Distance: a hero within 22 px is pushed away by a gold ripple (every 4 s).
        static void RegentKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int bolt = Kit.AddEffect(p, GoldFx.Bolt, offsetX: 15f, offsetY: 14.5f);
            int seal = Kit.AddEffect(p, GoldFx.Seal, spawnPoint: DamageEffectData.eSpawnPoint.ClosestEnemy);
            var bl = Kit.Shot(sh, "Bolt", "ModGoldRegentBolt", 3, v, 0f, bolt).Build();
            var dc = new ClipBuilder(sh, "Decree", "ModGoldRegentDecree").Once().Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop")
                .Ev(4, "AnimAttack", seal).EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, bl, 1.3f, rangeInner: 40f, rangeOuter: 110f, rangeRetreat: 40f));
            Kit.SetSpecial(p, Kit.Attack(sp, dc, 0f, rangeInner: 30f, rangeOuter: 140f, rangeRetreat: 30f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 14.5f);
        }

        // Hoard Wyrm (T3): Maul; Molten Breath pours three globs of molten gold that land as burning, slowing pools.
        // Passive Gilding: any Wyrm hit gilds the hero for 4 s; its next Maul on a gilded hero shatters it for 0.8 more.
        static void WyrmKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int maul = Kit.AddEffect(p, GoldFx.WyrmMaul, attach: true, destroyOnAnimEnd: true, offsetX: 24f, offsetY: 7f);
            var globs = new List<int>();
            foreach (var a in new[] { -18f, 0.01f, 18f }) globs.Add(Kit.AddEffect(p, GoldFx.MoltenGlob, offsetX: 25f, offsetY: 1f, angle: a));
            var ml = Kit.Melee(sh, "Maul", "ModGoldWyrmMaul", v, 3, maul, 50f).Build();
            var br = Cast(sh, "Breath", "ModGoldWyrmBreath", 4);
            for (int i = 0; i < globs.Count; i++) br.Ev(4, "AnimAttack", globs[i], i * 0.05f);
            br.EvO(4, "AnimSound", v).Ev(-1, "AnimRun");
            atk.Clear();
            atk.Add(Kit.Attack(a0, ml, 1.5f, rangeInner: 14f, rangeOuter: 36f));
            Kit.SetSpecial(p, Kit.Attack(sp, br.Build(), 0f, rangeInner: 30f, rangeOuter: 110f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 8f);
        }

        // Vault Colossus (T3): Ingot Slam (+ a quake ring); Payout opens the vault door: a gold shockwave whose damage
        // grows with the gold banked, plus one flung ingot per full gold bar. Passive Bank: a quarter of every hero hit
        // goes into the vault instead (up to 2.4), shown as gold bars over its head (VaultBank).
        static void VaultKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int slam = Kit.AddEffect(p, GoldFx.VaultSlam, attach: true, destroyOnAnimEnd: true, offsetX: 15f, offsetY: 4f);
            int quake = Kit.AddEffect(p, GoldFx.Quake, offsetX: 17f, offsetY: 0.01f);
            var sl = Kit.Melee(sh, "Slam", "ModGoldVaultSlam", v, 4, slam, 20f);
            sl.Ev(4, "AnimAttack", quake);
            var po = new ClipBuilder(sh, "Payout", "ModGoldVaultPayout").Once().Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop")
                .Ev(4, "GoldPayout").EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sl.Build(), 1.8f, rangeInner: 14f, rangeOuter: 34f));
            Kit.SetSpecial(p, Kit.Attack(sp, po, 0f, rangeInner: 0f, rangeOuter: 60f, rangeRetreat: 0f), 7.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 12f);
        }

        // Gilded Sovereign (T3): Scepter Smite; Kneel closes a ring of crown points round the hero for 0.9 s, then slams
        // (1.2 and a daze) unless he steps out. Passive Crown Jewels: three jewels orbit it; each halves one hero hit and
        // flies back at him as a shard; one regrows every 5 s (SovereignJewels).
        static void SovereignKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int smite = Kit.AddEffect(p, GoldFx.Smite, attach: true, destroyOnAnimEnd: true, offsetX: 21f, offsetY: 6f);
            int flash = Kit.AddEffect(p, GoldFx.SmiteFx, offsetX: 23f, offsetY: 0.01f);
            int kneel = Kit.AddEffect(p, GoldFx.Kneel, spawnPoint: DamageEffectData.eSpawnPoint.ClosestEnemy);
            var sm = Kit.Melee(sh, "Smite", "ModGoldSovereignSmite", v, 3, smite, 40f);
            sm.Ev(3, "AnimAttack", flash);
            var kn = new ClipBuilder(sh, "Kneel", "ModGoldSovereignKneel").Once().Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop")
                .Ev(4, "AnimAttack", kneel).EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sm.Build(), 1.5f, rangeInner: 14f, rangeOuter: 34f));
            Kit.SetSpecial(p, Kit.Attack(sp, kn, 0f, rangeInner: 20f, rangeOuter: 130f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 10f);
        }

        // Grand Treasurer (T3): Quills throws three gold quills (each leaves a slowing ink blot); Audit drops a ledger
        // page on the hero: if it lands he is In Debt for 5 s and then pays back about a third of all the damage he
        // took meanwhile (GoldMarks). Passive Balanced Books: no single hit takes more than 1.2 health from it.
        static void TreasurerKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            var quills = new List<int>();
            foreach (var a in new[] { -12f, 0.01f, 12f }) quills.Add(Kit.AddEffect(p, GoldFx.Quill, offsetX: 12f, offsetY: 21f, angle: a));
            int mark = Kit.AddEffect(p, GoldFx.Mark, spawnPoint: DamageEffectData.eSpawnPoint.ClosestEnemy);
            var qu = Kit.Shot(sh, "Quills", "ModGoldTreasurerQuills", 3, v, 0.03f, quills.ToArray()).Build();
            var au = new ClipBuilder(sh, "Audit", "ModGoldTreasurerAudit").Once().Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop")
                .Ev(5, "AnimAttack", mark).EvO(6, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, qu, 1.5f, rangeInner: 40f, rangeOuter: 110f, rangeRetreat: 40f));
            Kit.SetSpecial(p, Kit.Attack(sp, au, 0f, rangeInner: 20f, rangeOuter: 140f, rangeRetreat: 30f), 7.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 21f);
        }

        static void Gild(GameObject go, Player p) { Strike.DeathAtFeet(p); GodArt.UseHitSplat(p, GoldFx.HitSplat); }
        static void Books(GameObject go, Player p)
        {
            Gild(go, p);
            var h = go.GetComponent<Health>();
            if (h != null) R.Set(h, "m_maxDamagePerHit", TreasurerBooks.Cap);
        }

        public static readonly List<MonsterDef> Monsters = new List<MonsterDef>
        {
            new MonsterDef { id = "GoldMimic", art = "GoldMimic", basePrefab = "EnemyGnome", health = 4f, evolveCost = 0f,
                             evolveTo = new[] { "GoldWarden", "GoldRegent" }, kit = MimicKit, customize = Gild },
            new MonsterDef { id = "GoldWarden", art = "GoldWarden", basePrefab = "EnemyOrc", health = 6.5f, speedMult = 0.9f, evolveCost = 2.5f,
                             evolveTo = new[] { "GoldWyrm", "GoldVault" }, kit = WardenKit, customize = Gild },
            new MonsterDef { id = "GoldRegent", art = "GoldRegent", basePrefab = "EnemyWitch", health = 5.5f, evolveCost = 2.5f,
                             evolveTo = new[] { "GoldSovereign", "GoldTreasurer" }, kit = RegentKit, customize = Gild },
            new MonsterDef { id = "GoldWyrm", art = "GoldWyrm", basePrefab = "EnemyCapraDemon", health = 11.5f, speedMult = 0.9f, evolveCost = 4.5f,
                             kit = WyrmKit, customize = Gild },
            new MonsterDef { id = "GoldVault", art = "GoldVault", basePrefab = "EnemyTroll", health = 12f, speedMult = 0.8f, evolveCost = 4.5f,
                             kit = VaultKit, customize = Gild },
            new MonsterDef { id = "GoldSovereign", art = "GoldSovereign", basePrefab = "EnemyPriestess", health = 11f, evolveCost = 4.5f,
                             kit = SovereignKit, customize = Gild },
            new MonsterDef { id = "GoldTreasurer", art = "GoldTreasurer", basePrefab = "EnemySkeletonPope", health = 10.5f, evolveCost = 4.5f,
                             kit = TreasurerKit, customize = Books },
        };

        public static void Register()
        {
            if (s_done) return;
            s_done = true;
            GoldFx.Build();
            foreach (var m in Monsters) MonsterFactory.Build(m);
            MonsterFactory.LinkEvolutions(Monsters);
            GoldSecret.TreeIds.Clear();
            foreach (var m in Monsters) if (MonsterFactory.Built.ContainsKey(m.id)) GoldSecret.TreeIds.Add(m.PrefabName);
            GoldSecret.StarterId = MonsterFactory.Built.ContainsKey(Starter) ? "Mod" + Starter : null;
            Strike.KeepAllScales();
            Plugin.Log.LogInfo("Gilded Secret: " + GoldSecret.TreeIds.Count + " monsters, starter " + (GoldSecret.StarterId ?? "MISSING"));
        }

        /// <summary>
        /// Self-test (wired into SelfTest.CheckTrees): the secret line is a true 1 / 2 / 4 tree reachable from its starter,
        /// costs 0 / 2.5 / 4.5, finals evolve no further and are NOT in the statue group, no god offers any of it.
        /// Adds every monster of the line to <paramref name="reached"/>.
        /// </summary>
        public static void CheckTree(Action<string> bad, Action<string> note, HashSet<Player> reached, List<SpawnItem> statueItems)
        {
            Player start;
            if (!MonsterFactory.Built.TryGetValue(Starter, out start) || start == null) { bad("gold secret: starter " + Starter + " was not built"); return; }
            if (GoldSecret.StarterId != start.gameObject.name) bad("gold secret: GoldSecret.StarterId is " + (GoldSecret.StarterId ?? "null"));
            var tiers = new List<List<Player>> { new List<Player> { start } };
            var parent = new Dictionary<Player, Player>();
            for (int t = 0; t < 2; t++)
            {
                var next = new List<Player>();
                foreach (var p in tiers[t])
                {
                    var to = p.GetEvolveTo() ?? new Player[0];
                    if (to.Length != 2 || to[0] == to[1]) bad("gold secret: " + p.gameObject.name + " offers " + to.Length + " evolutions, must be 2 different");
                    foreach (var x in to)
                    {
                        if (x == null) continue;
                        Player first;
                        if (parent.TryGetValue(x, out first)) bad("gold secret: " + x.gameObject.name + " is offered by two monsters");
                        else parent[x] = p;
                        next.Add(x);
                    }
                }
                tiers.Add(next);
            }
            int[] want = { 1, 2, 4 };
            float[] cost = { 0f, 2.5f, 4.5f };
            var names = new List<string>();
            for (int t = 0; t < 3; t++)
            {
                if (tiers[t].Count != want[t]) bad("gold secret: T" + (t + 1) + " has " + tiers[t].Count + ", want " + want[t]);
                foreach (var p in tiers[t])
                {
                    reached.Add(p);
                    names.Add(p.gameObject.name);
                    if (!GoldSecret.TreeIds.Contains(p.gameObject.name)) bad("gold secret: " + p.gameObject.name + " missing from GoldSecret.TreeIds");
                    if (t > 0 && Mathf.Abs(R.Get<float>(p, "m_evolveCost") - cost[t]) > 0.01f) bad("gold secret: " + p.gameObject.name + " costs " + R.Get<float>(p, "m_evolveCost"));
                    if (t == 2)
                    {
                        var to = p.GetEvolveTo();
                        if (to != null && to.Length > 0) bad("gold secret: final " + p.gameObject.name + " still evolves");
                        // gold idol slot 4 only: never a room statue (Statues.Register skips GoldSecret.TreeIds)
                        if (statueItems != null && statueItems.Exists(i => i != null && i.m_object == p.gameObject)) bad("gold secret: final " + p.gameObject.name + " is in the statue group (it must stay secret)");
                    }
                }
            }
            if (GoldSecret.TreeIds.Count != 7) bad("gold secret: TreeIds has " + GoldSecret.TreeIds.Count + " entries, want 7");
            foreach (var d in SystemDeity.GetDeities() ?? new List<Deity>())
                if (d != null && d.GetStartingMonsters() != null)
                    foreach (var go in d.GetStartingMonsters())
                        if (go != null && GoldSecret.TreeIds.Contains(go.name)) bad("gold secret: god " + d.GetName() + " lists " + go.name + " as a starter");
            foreach (var kv in new[] { GoldFx.MimicSnap, GoldFx.KeyShot, GoldFx.Seal, GoldFx.MoltenGlob, GoldFx.Payout, GoldFx.Kneel, GoldFx.Jewel, GoldFx.Mark, GoldFx.Interest })
                if (kv == null) bad("gold secret: an effect template failed to build");
            if (GoldFx.Coins == null || GoldFx.IndBank == null || GoldFx.IndBank[2] == null || GoldFx.IndShackle == null
                || GoldFx.IndTax == null || GoldFx.IndGilded == null || GoldFx.IndDebt == null) bad("gold secret: an indicator failed to build");
            note("Gilded Secret: " + string.Join(", ", names.ToArray()));
        }
    }

    // ================================================================================================================ brains
    /// <summary>Shared bits for the Gilded Secret brains.</summary>
    public abstract class GoldBrain : MonoBehaviour
    {
        protected Health m_health;
        protected Player m_player;
        protected exSprite m_sprite;
        protected virtual void Awake() { m_health = GetComponent<Health>(); m_player = GetComponent<Player>(); m_sprite = GetComponent<exSprite>(); }
        public bool Alive { get { return m_health != null && m_health.IsAlive() && gameObject.activeInHierarchy; } }
        /// <summary>The art's feet (the sprite is offset from the transform; feet = cell bottom + 2).</summary>
        public Vector2 Feet { get { return (Vector2)transform.position + new Vector2(0f, m_sprite != null ? m_sprite.offset.y + 2f : 0f); } }
        protected float Facing { get { return transform.localScale.x < 0f ? -1f : 1f; } }
        public DamageSource Own()
        {
            var pd = m_player != null ? R.Get<PlayerData>(m_player, "m_playerData") : null;
            return new DamageSource(gameObject, gameObject, pd);
        }
        protected static bool From(DamageInfo d, string prefix)
        {
            var src = d != null && d.m_source != null ? d.m_source.m_source : null;
            return src != null && src.name.StartsWith(prefix);
        }
        protected static bool OnHero(DamageInfo d) { var h = ModUtil.Hero(); return d != null && h != null && d.m_victim == h; }
        protected void Spawn(GameObject t, Vector2 at) { if (t != null) FxFactory.SpawnOwned(t, at, Own()); }

        /// <summary>A resistance multiplier held while a move lasts, restored only if nothing changed it meanwhile.</summary>
        float m_base = 1f, m_mult = 1f;
        protected void Resist(float mult)
        {
            if (m_health == null) return;
            if (m_mult == 1f) m_base = R.Get<float>(m_health, "m_damageResistanceFinal");
            m_mult = mult;
            R.Set(m_health, "m_damageResistanceFinal", m_base * mult);
        }
        protected void Unresist()
        {
            if (m_mult == 1f || m_health == null) return;
            if (Mathf.Abs(R.Get<float>(m_health, "m_damageResistanceFinal") - m_base * m_mult) < 0.001f) R.Set(m_health, "m_damageResistanceFinal", m_base);
            m_mult = 1f;
        }
    }

    /// <summary>
    /// Coffer Mimic. A Snap that lands steals 1-4 of the hero's gold for the mimic's player. Play Dead: while shut it takes
    /// a quarter damage, but each hit knocks 1-4 of its player's gold loose to the hero; it springs, turned toward the
    /// hero, the moment he comes near.
    /// </summary>
    public class CofferMimic : GoldBrain
    {
        public const int SpringFrame = 11, GoldMin = 1, GoldMax = 4;
        public const float Range = 26f, Resistance = 4f;
        /// <summary>The clip shuts it for 2.76 s at most; a knockback that cuts the clip short ends Play Dead here.</summary>
        public const float MaxFeign = 3.0f;
        bool m_lurk;
        float m_feign;

        void OnEnable() { m_lurk = false; m_feign = 0f; }
        void OnDisable() { Unresist(); m_lurk = false; m_feign = 0f; }

        PlayerData Owner { get { return m_player != null ? R.Get<PlayerData>(m_player, "m_playerData") : null; } }

        void MsgOnAttackContact(DamageInfo d)
        {
            if (!Alive || !OnHero(d) || !From(d, "ModGoldMimicSnap")) return;
            var owner = Owner;
            if (owner == null || owner.IsHero) return;
            int got = Move(SystemPlayers.GetHeroPlayerData(), owner, UnityEngine.Random.Range(GoldMin, GoldMax + 1));
            if (got <= 0) return;
            Spawn(GoldFx.Coins, Feet);
            FloatNumber.RollOver(gameObject, got, GoldMax);
        }

        void OnDamaged(DamageInfo d)
        {
            // hits only: damage over time arrives without a source
            if (m_feign <= 0f || !Alive || d == null || d.m_source == null || d.m_source.m_source == null) return;
            var hero = SystemPlayers.GetHeroPlayerData();
            var by = d.m_source.m_sourcePlayer;
            int lost = Move(Owner, by != null && by == hero ? hero : null, UnityEngine.Random.Range(GoldMin, GoldMax + 1));
            if (lost <= 0) return;
            Spawn(GoldFx.Coins, Feet);
            FloatNumber.Show(lost.ToString(), NumberTone.Min, FloatNumber.OverHead(gameObject), gameObject);
        }

        /// <summary>Take up to <paramref name="n"/> gold from one player (only what they have) and give it to the other
        /// (none: the gold is lost). Returns the amount taken.</summary>
        int Move(PlayerData from, PlayerData to, int n)
        {
            if (from == null || from.GameData == null) return 0;
            int take = Mathf.Min(n, Mathf.FloorToInt(from.GameData.Gold));
            if (take <= 0 || !from.LoseGold(take, Own())) return 0;
            if (to != null) to.OnGoldCollected(take);
            return take;
        }

        public void GoldFeignOn() { m_lurk = true; m_feign = MaxFeign; Resist(Resistance); }

        public void GoldFeignOff()
        {
            m_lurk = false; m_feign = 0f; Unresist();
            // the ambush lunges at the hero, not wherever it last faced
            var mm = GetComponent<ModMonster>();
            if (mm != null && ModUtil.Hero() != null) mm.FaceHero();
        }

        void Update()
        {
            if (m_feign > 0f) { m_feign -= Time.deltaTime; if (m_feign <= 0f) GoldFeignOff(); }
            if (!m_lurk) return;
            var hero = ModUtil.Hero();
            if (hero == null || !Alive) return;
            if (((Vector2)hero.transform.position - Feet).sqrMagnitude > Range * Range) return;
            // the hero walked up to the "chest": jump the clip straight to Spring (its first event is GoldFeignOff)
            m_lurk = false;
            var an = GetComponent<exSpriteAnimation>();
            var st = an != null ? an.GetCurrentAnimation() : null;
            if (st == null || st.clip == null || !st.clip.name.StartsWith("ModGoldMimicPlayDead")) return;
            foreach (var e in st.clip.eventInfos)
                if (e.methodName == "GoldFeignOff") { an.Play(st.name, Mathf.Max(0f, e.time - 0.002f)); break; }
        }
    }

    /// <summary>Vault Warden: Shackle hits chain the hero (GoldMarks); its Strongbox front is handled in Patch_GoldDamage.</summary>
    public class WardenGuard : GoldBrain
    {
        public const float FrontMult = 0.7f;
        float m_clank;
        void MsgOnAttackContact(DamageInfo d)
        {
            if (!Alive || !OnHero(d) || !From(d, "ModGoldKey")) return;
            GoldMarks.On(d.m_victim).Shackle(this);
        }
        /// <summary>Is <paramref name="attacker"/> in front of the Warden?</summary>
        public bool InFront(GameObject attacker) { return attacker != null && (attacker.transform.position.x - transform.position.x) * Facing >= 0f; }
        public void Clanked()
        {
            if (m_clank > 0f) return;
            m_clank = 0.2f;
            Spawn(GoldFx.Clank, Feet + new Vector2(Facing * 9f, 0f));
        }
        void Update() { if (m_clank > 0f) m_clank -= Time.deltaTime; }
    }

    /// <summary>Gilt Regent: a landed seal Taxes the hero; Royal Distance ripples a close hero away every 4 s.</summary>
    public class RegentCourt : GoldBrain
    {
        public const float Near = 22f, Every = 4f, Toll = 0.3f;
        float m_cd;
        void OnEnable() { m_cd = 1f; }
        void MsgOnAttackContact(DamageInfo d)
        {
            if (!Alive || !OnHero(d) || !From(d, "ModGoldSeal")) return;
            GoldMarks.On(d.m_victim).Tax(this);
        }
        void Update()
        {
            if (m_cd > 0f) { m_cd -= Time.deltaTime; return; }
            var hero = ModUtil.Hero();
            if (hero == null || !Alive) return;
            var hh = hero.GetComponent<Health>();
            if (hh == null || !hh.IsAlive() || ((Vector2)hero.transform.position - Feet).sqrMagnitude > Near * Near) return;
            m_cd = Every;
            Spawn(GoldFx.Ripple, Feet);
        }
        /// <summary>The tax a hero hit pays to this Regent.</summary>
        public void Collect()
        {
            if (!Alive) return;
            if (m_health.GetHealthCurrent() < m_health.GetHealthMax()) { m_health.Heal(Toll); ModInd.Heal(gameObject); }
            Spawn(GoldFx.Tithe, Feet);
        }
    }

    /// <summary>Hoard Wyrm: every hit gilds the hero; a Maul on a gilded hero shatters the gold for 0.8 more.</summary>
    public class WyrmGild : GoldBrain
    {
        void MsgOnAttackContact(DamageInfo d)
        {
            if (!Alive || !OnHero(d)) return;
            var m = GoldMarks.On(d.m_victim);
            if (From(d, "ModGoldWyrmMaul"))
            {
                if (m.Gilded) { m.Ungild(); Spawn(GoldFx.Shatter, d.m_victim.transform.position); }
                else m.Gild();
            }
            else if (From(d, "ModGoldMolten")) m.Gild();
        }
    }

    /// <summary>Vault Colossus: banks a quarter of every hero hit; Payout spends it on a bigger ring and ingots.</summary>
    public class VaultBank : GoldBrain
    {
        public const float Share = 0.25f, MaxBank = 2.4f, Bar = 0.8f, BaseDamage = 0.6f, PerBanked = 0.5f, ChestY = 14f;
        float m_bank;
        public float Banked { get { return m_bank; } }
        void OnEnable() { m_bank = 0f; }
        void OnDisable() { ModInd.Count(gameObject, GoldFx.IndBank, 0); }

        /// <summary>Called for a hero hit about to land: returns the part the Colossus still takes.</summary>
        public float Deposit(float amount)
        {
            if (!Alive || m_bank >= MaxBank) return amount;
            float put = Mathf.Min(amount * Share, MaxBank - m_bank);
            m_bank += put;
            ModInd.Count(gameObject, GoldFx.IndBank, Mathf.Clamp(Mathf.CeilToInt(m_bank / Bar - 0.01f), 1, 3));
            return amount - put;
        }

        public void GoldPayout()
        {
            if (!Alive) return;
            var src = Own();
            var ring = GoldFx.Payout != null ? FxFactory.SpawnOwned(GoldFx.Payout, Feet, src) : null;
            var de = ring != null ? ring.GetComponent<DamageEffect>() : null;
            if (de != null) R.Set(de, "m_damage", BaseDamage + m_bank * PerBanked);
            int bars = Mathf.FloorToInt(m_bank / Bar + 0.01f);
            var hero = ModUtil.Hero();
            Vector2 from = Feet + new Vector2(0f, ChestY);
            Vector2 dir = hero != null ? (Vector2)hero.transform.position + new Vector2(0f, 6f) - from : new Vector2(Facing, 0f);
            float ang = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg;
            for (int i = 0; i < bars && GoldFx.Ingot != null; i++) FxFactory.SpawnOwned(GoldFx.Ingot, from, src, ang + (i - (bars - 1) * 0.5f) * 14f);
            m_bank = 0f;
            ModInd.Count(gameObject, GoldFx.IndBank, 0);
        }
    }

    /// <summary>Gilded Sovereign: three orbiting crown jewels, each halves a hero hit and returns as a shard.</summary>
    public class SovereignJewels : GoldBrain
    {
        public const int Max = 3;
        public const float Regrow = 5f, RX = 15f, RY = 6f, Height = 16f, Spin = 140f, HitMult = 0.5f;
        readonly List<GameObject> m_gems = new List<GameObject>();
        float m_regrow, m_t;
        bool m_started;
        public int Count { get { return m_gems.Count; } }

        void OnEnable() { m_started = false; m_regrow = Regrow; }
        void OnDisable() { Clear(); }
        void Clear()
        {
            foreach (var g in m_gems) if (g != null && g.activeInHierarchy) SystemPool.Despawn(g);
            m_gems.Clear();
        }
        void Add()
        {
            if (GoldFx.Jewel == null || m_gems.Count >= Max) return;
            var g = SystemPool.Spawn(GoldFx.Jewel, (Vector3)(Feet + new Vector2(0f, Height)));
            if (g != null) m_gems.Add(g);
        }

        void Update()
        {
            if (!Alive) { if (m_gems.Count > 0) Clear(); return; }
            if (!m_started) { m_started = true; Clear(); for (int i = 0; i < Max; i++) Add(); }
            m_gems.RemoveAll(g => g == null || !g.activeInHierarchy);
            if (m_gems.Count < Max) { m_regrow -= Time.deltaTime; if (m_regrow <= 0f) { m_regrow = Regrow; Add(); } }
            m_t += Time.deltaTime * Spin;
            var c = Feet + new Vector2(0f, Height);
            for (int i = 0; i < m_gems.Count; i++)
            {
                float a = (m_t + i * 360f / Mathf.Max(1, m_gems.Count)) * Mathf.Deg2Rad;
                var p = c + new Vector2(Mathf.Cos(a) * RX, Mathf.Sin(a) * RY);
                var t = m_gems[i].transform;
                // in front of the body on the near half of the orbit, behind it on the far half
                t.position = new Vector3(p.x, p.y, transform.position.z + (Mathf.Sin(a) < 0f ? 0.5f : -0.5f));
            }
        }

        /// <summary>A hero hit about to land: if a jewel is up it breaks, halves the hit and flies back at the hero.</summary>
        public float Guard(float amount, GameObject hero)
        {
            if (!Alive || m_gems.Count == 0) return amount;
            var g = m_gems[m_gems.Count - 1];
            m_gems.RemoveAt(m_gems.Count - 1);
            Vector2 at = g != null ? (Vector2)g.transform.position : Feet + new Vector2(0f, Height);
            if (g != null && g.activeInHierarchy) SystemPool.Despawn(g);
            if (GoldFx.JewelBreak != null) SystemPool.Spawn(GoldFx.JewelBreak, (Vector3)at);
            if (GoldFx.Shard != null && hero != null)
            {
                var dir = (Vector2)hero.transform.position + new Vector2(0f, 6f) - at;
                FxFactory.SpawnOwned(GoldFx.Shard, at, Own(), Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg);
            }
            m_regrow = Regrow;
            return amount * HitMult;
        }
    }

    /// <summary>Grand Treasurer: a landed audit page puts the hero In Debt; capped hits flash PAID.</summary>
    public class TreasurerBooks : GoldBrain
    {
        public const float Cap = 1.2f;
        float m_stamp;
        void MsgOnAttackContact(DamageInfo d)
        {
            if (!Alive || !OnHero(d) || !From(d, "ModGoldMark")) return;
            GoldMarks.On(d.m_victim).Debt(this);
        }
        void OnDamaged(DamageInfo d)
        {
            if (d == null || m_stamp > 0f || d.m_amount < Cap - 0.001f) return;
            m_stamp = 0.3f;
            Spawn(GoldFx.Stamp, Feet);
        }
        void Update() { if (m_stamp > 0f) m_stamp -= Time.deltaTime; }
    }

    /// <summary>
    /// Everything the Gilded Secret puts ON the hero, each with its own indicator: Shackled (chained to a Warden for 2.5 s,
    /// hauled back past 45 px, chain drawn link by link), Taxed (4 s: his hits deal 30 percent less and pay the Regent),
    /// Gilded (4 s, a Wyrm Maul shatters it), In Debt (5 s, then pays back about a third of the damage taken meanwhile).
    /// </summary>
    public class GoldMarks : MonoBehaviour
    {
        public const float ShackleTime = 2.5f, Leash = 45f, Haul = 150f, TaxTime = 4f, TaxMult = 0.7f, GildTime = 4f, DebtTime = 5f,
                           DebtShare = 0.375f, DebtMin = 0.05f, DebtMax = 1.875f;   // raw: the T3 0.8 multiplier makes it 0.3 x, max 1.5

        public static GoldMarks On(GameObject hero) { return hero.GetComponent<GoldMarks>() ?? hero.AddComponent<GoldMarks>(); }

        WardenGuard m_warden; float m_shackle, m_haul;
        readonly List<GameObject> m_links = new List<GameObject>();
        RegentCourt m_regent; float m_tax;
        float m_gild;
        TreasurerBooks m_books; DamageSource m_bookSrc; float m_debt, m_owed;

        public bool Taxed { get { return m_tax > 0f; } }
        public bool Gilded { get { return m_gild > 0f; } }
        public bool InDebt { get { return m_debt > 0f; } }
        public bool Shackled { get { return m_shackle > 0f; } }

        public void Shackle(WardenGuard w) { m_warden = w; m_shackle = ShackleTime; ModInd.Set(gameObject, GoldFx.IndShackle, true); }
        public void Tax(RegentCourt r) { m_regent = r; m_tax = TaxTime; ModInd.Set(gameObject, GoldFx.IndTax, true); }
        public void Gild() { m_gild = GildTime; ModInd.Set(gameObject, GoldFx.IndGilded, true); }
        public void Ungild() { m_gild = 0f; ModInd.Set(gameObject, GoldFx.IndGilded, false); }
        public void Debt(TreasurerBooks t)
        {
            if (m_debt <= 0f) m_owed = 0f;
            m_books = t; m_bookSrc = t.Own(); m_debt = DebtTime;
            ModInd.Set(gameObject, GoldFx.IndDebt, true);
        }
        /// <summary>Health the hero lost to a monster while In Debt.</summary>
        public void Owe(float lost) { if (m_debt > 0f && lost > 0f) m_owed += lost; }

        /// <summary>A hit the Taxed hero lands: returns the cut amount and pays the Regent.</summary>
        public float Taxing(float amount)
        {
            if (m_tax <= 0f) return amount;
            if (m_regent != null && m_regent.Alive) m_regent.Collect();
            return amount * TaxMult;
        }

        void OnDisable() { EndShackle(); m_tax = m_gild = m_debt = 0f; }

        void EndShackle()
        {
            m_shackle = 0f; m_warden = null;
            foreach (var l in m_links) if (l != null && l.activeInHierarchy) SystemPool.Despawn(l);
            m_links.Clear();
            ModInd.Set(gameObject, GoldFx.IndShackle, false);
        }

        void Update()
        {
            float dt = Time.deltaTime;
            var hh = GetComponent<Health>();
            bool alive = hh != null && hh.IsAlive();
            if (m_shackle > 0f)
            {
                m_shackle -= dt;
                if (m_shackle <= 0f || !alive || m_warden == null || !m_warden.Alive) EndShackle();
                else Chain(dt);
            }
            if (m_tax > 0f) { m_tax -= dt; if (m_tax <= 0f || !alive) { m_tax = 0f; ModInd.Set(gameObject, GoldFx.IndTax, false); } }
            if (m_gild > 0f) { m_gild -= dt; if (m_gild <= 0f || !alive) Ungild(); }
            if (m_debt > 0f)
            {
                m_debt -= dt;
                if (m_debt <= 0f || !alive)
                {
                    m_debt = 0f;
                    ModInd.Set(gameObject, GoldFx.IndDebt, false);
                    if (alive && m_owed >= DebtMin && GoldFx.Interest != null && m_bookSrc != null)
                    {
                        var fx = FxFactory.SpawnOwned(GoldFx.Interest, transform.position, m_bookSrc);
                        var de = fx != null ? fx.GetComponent<DamageEffect>() : null;
                        if (de != null) R.Set(de, "m_damage", Mathf.Min(DebtMax, m_owed * DebtShare));
                    }
                    m_owed = 0f; m_books = null; m_bookSrc = null;
                }
            }
        }

        /// <summary>Haul the hero back to the leash and lay the chain from the Warden's fist to his ankles.</summary>
        void Chain(float dt)
        {
            Vector2 w = m_warden.Feet + new Vector2(0f, 12f), h = (Vector2)transform.position + new Vector2(0f, 2f);
            var d = h - w;
            float len = d.magnitude;
            m_haul -= dt;
            if (len > Leash && m_haul <= 0f) { m_haul = 0.1f; ModUtil.Pull(gameObject, w, Haul); }
            if (GoldFx.ChainLink == null) return;
            int want = Mathf.Clamp(Mathf.CeilToInt(len / 5f), 1, 24);
            while (m_links.Count < want) { var l = SystemPool.Spawn(GoldFx.ChainLink, (Vector3)w); if (l == null) break; m_links.Add(l); }
            while (m_links.Count > want) { var l = m_links[m_links.Count - 1]; m_links.RemoveAt(m_links.Count - 1); if (l != null && l.activeInHierarchy) SystemPool.Despawn(l); }
            float ang = Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg;
            float sag = Mathf.Max(0f, Leash - len) * 0.15f;
            for (int i = 0; i < m_links.Count; i++)
            {
                if (m_links[i] == null) continue;
                float t = (i + 0.5f) / m_links.Count;
                var p = w + d * t + new Vector2(0f, -sag * 4f * t * (1f - t));
                m_links[i].transform.position = new Vector3(p.x, p.y, transform.position.z - 0.2f);
                m_links[i].transform.rotation = Quaternion.Euler(0f, 0f, ang);
            }
        }
    }

    /// <summary>
    /// The Gilded Secret's damage rules: Strongbox (Warden front 0.7), Bank (Colossus keeps a quarter), Crown Jewels
    /// (Sovereign halves), Taxed hero (0.7 and the tithe), and In Debt bookkeeping (health the hero actually lost).
    /// </summary>
    [HarmonyPatch(typeof(Health), "Damage", new[] { typeof(DamageInfo), typeof(bool) })]
    [HarmonyPriority(Priority.Low)]
    static class Patch_GoldDamage
    {
        static void Prefix(Health __instance, DamageInfo damage, bool hitFriendly, bool __runOriginal, out float __state)
        {
            __state = -1f;
            if (!__runOriginal) return;
            try
            {
                if (damage == null || damage.m_source == null || damage.m_amount <= 0f || damage.m_isDamageFromStatus) return;
                var hero = ModUtil.Hero();
                if (hero == null) return;
                var attacker = damage.m_source.m_sourceOwnerPlayer;
                var me = __instance.gameObject;
                if (me == hero)
                {
                    var gm = me.GetComponent<GoldMarks>();
                    if (gm != null && gm.InDebt && attacker != null && attacker != hero) __state = __instance.GetHealthCurrent();
                    return;
                }
                if (attacker != hero || !__instance.CanDamage(damage.m_source, hitFriendly)) return;
                var marks = hero.GetComponent<GoldMarks>();
                if (marks != null && marks.Taxed) damage.m_amount = marks.Taxing(damage.m_amount);
                var wg = me.GetComponent<WardenGuard>();
                if (wg != null && wg.Alive && wg.InFront(hero)) { damage.m_amount *= WardenGuard.FrontMult; wg.Clanked(); }
                var vb = me.GetComponent<VaultBank>();
                if (vb != null) damage.m_amount = vb.Deposit(damage.m_amount);
                var sj = me.GetComponent<SovereignJewels>();
                if (sj != null) damage.m_amount = sj.Guard(damage.m_amount, hero);
            }
            catch (Exception e) { Plugin.Log.LogWarning("Gold damage rules: " + e.Message); }
        }

        static void Postfix(Health __instance, float __state)
        {
            if (__state < 0f) return;
            try
            {
                float lost = __state - __instance.GetHealthCurrent();
                var gm = __instance.GetComponent<GoldMarks>();
                if (gm != null && lost > 0f) gm.Owe(lost);
            }
            catch { }
        }
    }

    /// <summary>Give every Gilded Secret monster instance its brain.</summary>
    [HarmonyPatch(typeof(Player), "Awake")]
    static class Patch_GoldSecretAwake
    {
        static void Postfix(Player __instance)
        {
            if (__instance == null) return;
            var go = __instance.gameObject;
            switch (ModUtil.PrefabName(go))
            {
                case "ModGoldMimic": if (go.GetComponent<CofferMimic>() == null) go.AddComponent<CofferMimic>(); break;
                case "ModGoldWarden": if (go.GetComponent<WardenGuard>() == null) go.AddComponent<WardenGuard>(); break;
                case "ModGoldRegent": if (go.GetComponent<RegentCourt>() == null) go.AddComponent<RegentCourt>(); break;
                case "ModGoldWyrm": if (go.GetComponent<WyrmGild>() == null) go.AddComponent<WyrmGild>(); break;
                case "ModGoldVault": if (go.GetComponent<VaultBank>() == null) go.AddComponent<VaultBank>(); break;
                case "ModGoldSovereign": if (go.GetComponent<SovereignJewels>() == null) go.AddComponent<SovereignJewels>(); break;
                case "ModGoldTreasurer": if (go.GetComponent<TreasurerBooks>() == null) go.AddComponent<TreasurerBooks>(); break;
            }
        }
    }
}
