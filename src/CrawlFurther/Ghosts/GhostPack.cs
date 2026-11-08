using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Content.Ghosts
{
    using CrawlFurther.Art;
    using CrawlFurther.Ghosts;
    using CrawlFurther.Gods;
    using CrawlFurther.Monsters;
    using CrawlFurther.UI;
    using CrawlFurther.Util;

    /// <summary>
    /// Ghost forms: what a monster player is while they float around between bodies. Chosen on the origin
    /// page after the hero origin. Each form changes how ectoplasm is gathered and what it is spent on.
    /// </summary>
    public static class GhostPack
    {
        public static readonly List<GhostFormEntry> Forms = new List<GhostFormEntry>
        {
            new GhostFormEntry { form = GhostForm.Wisp, name = "WISP", portraitArt = "GhostWisp",
                summary = "The standard ghost, no changes", flavour = "Float, gather, return.\nThe old way." },
            new GhostFormEntry { form = GhostForm.Gleaner, name = "GLEANER", portraitArt = "GhostGleaner", bodyArt = "FormGleaner",
                summary = "Ectoplasm flies to you, worth less. Earns Motes",
                flavour = "Every scrap of the dead\nends up in its sack." },
            new GhostFormEntry { form = GhostForm.Binder, name = "BINDER", portraitArt = "GhostBinder", bodyArt = "FormBinder",
                summary = "Earn Gels. The ghost button fuses them",
                flavour = "Two make a brute.\nThree make a titan." },
            new GhostFormEntry { form = GhostForm.Poltergeist, name = "POLTERGEIST", portraitArt = "GhostPoltergeist", bodyArt = "FormPoltergeist",
                summary = "Attack throws a weak hex bolt. Earns Spitters",
                flavour = "It cannot touch you.\nIt can throw the cutlery." },
            new GhostFormEntry { form = GhostForm.Banshee, name = "BANSHEE", portraitArt = "GhostBanshee", bodyArt = "FormBanshee",
                summary = "Attack wails: slows the hero, costs ectoplasm",
                flavour = "Her grief has a voice.\nThe living stumble." },
            new GhostFormEntry { form = GhostForm.Sexton, name = "SEXTON", portraitArt = "GhostSexton", bodyArt = "FormSexton",
                summary = "Back digs a grave that rises near the hero",
                flavour = "Every grave he digs\nis already full." },
            new GhostFormEntry { form = GhostForm.Kindler, name = "KINDLER", portraitArt = "GhostKindler", bodyArt = "FormKindler",
                summary = "Attack lights a Fusebelly from afar",
                flavour = "A long taper.\nShort fuses." },
            new GhostFormEntry { form = GhostForm.Mason, name = "MASON", portraitArt = "GhostMason", bodyArt = "FormMason",
                summary = "Attack makes your Garglings spit stones",
                flavour = "Stone sentries that\nnever leave their post." },
            new GhostFormEntry { form = GhostForm.Hexer, name = "HEXER", portraitArt = "GhostHexer", bodyArt = "FormHexer",
                summary = "Attack throws a pin: hexed heroes take more",
                flavour = "A doll for every hero.\nA pin for every doll." },
            new GhostFormEntry { form = GhostForm.Miser, name = "MISER", portraitArt = "GhostMiser", bodyArt = "FormMiser",
                summary = "Back spends all your bodies on one big Mimic",
                flavour = "Why spend one coin\nwhen you can spend three?" },
            // the custom slots: ALWAYS the last two entries (add new regular forms above this line)
            new GhostFormEntry { form = GhostForm.Silver, tier = SlotTier.Silver, name = "SILVER SHADE", portraitArt = "GhostSilver",
                summary = "Your own look. Eight silver orbs upgrade a body",
                flavour = "Every death leaves silver.\nEight lift you higher." },
            new GhostFormEntry { form = GhostForm.Gold, tier = SlotTier.Gold, name = "GOLD SPECTRE", portraitArt = "GhostGold",
                summary = "Your own look. Ghost button leaves a thrall",
                flavour = "Leave every body behind.\nIt keeps fighting for you." },
        };

        /// <summary>The number of regular forms (everything before the silver and gold slots).</summary>
        public static int RegularCount { get { int n = 0; foreach (var f in Forms) if (f.tier == SlotTier.Normal) n++; return n; } }

        public static readonly Dictionary<int, int> Chosen = new Dictionary<int, int>();
        /// <summary>The form a player's ghost uses: their pick, or the Wisp for bots and for a custom slot that is still
        /// locked (the picker never lets one be confirmed, this is only a safety net).</summary>
        public static GhostForm FormOf(PlayerData pd)
        {
            var d = DefOf(pd);
            return d != null ? d.form : GhostForm.Wisp;
        }

        public static GhostFormEntry DefOf(PlayerData pd)
        {
            int i;
            if (pd == null || pd.IsBot || !Chosen.TryGetValue(pd.Id, out i) || i < 0 || i >= Forms.Count) return Forms[0];
            var d = Forms[i];
            if (d.tier == SlotTier.Silver && !Unlocks.IsUnlocked(Unlocks.IdFor("Ghost", SlotTier.Silver))) return Forms[0];
            if (d.tier == SlotTier.Gold && !Unlocks.IsUnlocked(Unlocks.IdFor("Ghost", SlotTier.Gold))) return Forms[0];
            return d;
        }

        public static GhostFormEntry Def(GhostForm f)
        {
            foreach (var d in Forms) if (d.form == f) return d;
            return null;
        }

        /// <summary>
        /// The picker portrait for a form (a looping 29 x 24 clip, cached). Custom slots show the player's own look in
        /// a silver / gold frame (rebuilt whenever the look changes); the rest show their drawn portrait.
        /// </summary>
        public static exSpriteAnimClip PortraitClip(GhostFormDef def, int playerId)
        {
            if (def == null) return null;
            if (def.tier != SlotTier.Normal)
            {
                var c = GhostCustom.PortraitClip(playerId, def.tier);
                if (c != null) return c;
            }
            exSpriteAnimClip clip;
            if (s_portraits.TryGetValue(def.portraitArt, out clip) && clip != null) return clip;
            var sh = SpriteSheets.Get(def.portraitArt);
            if (sh == null || !sh.Has("Idle")) return null;
            clip = new ClipBuilder(sh, "Idle", "ModGhostPortrait_" + def.portraitArt).Loop().Build();
            s_portraits[def.portraitArt] = clip;
            return clip;
        }
        static readonly Dictionary<string, exSpriteAnimClip> s_portraits = new Dictionary<string, exSpriteAnimClip>();

        // ------------------------------------------------------------------ templates
        public static GameObject GooGlob, GooPuddle, MergeBurst, WispPickup, WispCollect, WispFade, HexBolt, HexPuffWall, HexPuffHit,
                                 GleanerAura, BlobSpawnSplash,
                                 MoteBite, GelSlam, BruteSlam, BruteQuake, TitanSlam, TitanEngulf,
                                 KingSlam, KingQuake, KingDrop, KingDropPool;
        public static Player Mote, Spitter, Gel, Brute, Titan, King;
        static readonly Dictionary<string, GameObject> s_formPrefabs = new Dictionary<string, GameObject>();
        static readonly Dictionary<int, Player> s_byGels = new Dictionary<int, Player>();
        public static Powerup GleanerPenalty;

        static void BuildFx()
        {
            var goo = FxFactory.GetStatus("StatusLavaSteveGoo");
            GooPuddle = FxFactory.Clone("LavaEffectLongerReworkZone", "ModGooPuddle");
            if (GooPuddle != null)
            {
                var sh = SpriteSheets.Get("FxGooPuddle");
                var clip = new ClipBuilder(sh, "Life", "ModGooPuddleLife").Once().Ev(1, "AnimDamageOn").Ev(-3, "AnimDamageOff").Build();
                FxFactory.Reskin(GooPuddle, clip, sh);
                FxFactory.SetEffect(GooPuddle, destroyOnAnimEnd: true, snap: 1f);
                FxFactory.SetStatusZone(GooPuddle, goo, hitsHero: true, hitsMonster: false);
                FxKit.NoTint(GooPuddle);
                Strike.Ground(GooPuddle, "FxGooPuddle", 16, 9, 26f, 7f);   // lava-zone art + trigger sat 14 px below the splat point
            }
            GooGlob = FxKit.Projectile("ModGooGlob", "webBall", "FxGooGlob", "Fly", 160f, 0.9f, 0.5f, 0.2f, goo, 0.5f, accel: 20f, speedMax: 8f, rotate: false);
            if (GooGlob != null)
            {
                FxFactory.SetEffect(GooGlob, destroyOnAnimEnd: false, destroyAfter: 0.9f, spawnOnDestroy: GooPuddle, freeRotate: false);
                FxFactory.SetContacts(GooGlob, destroyOnHit: true, spawnOnHit: GooPuddle);
                Strike.ArtAt(GooGlob, "FxGooGlob", 9, 17);   // floor-skimming glob (hits feet), drawn at spout height
            }
            MergeBurst = FxKit.Visual("ModMergeBurst", "FxMergeBurst", "Play");
            HexBolt = FxKit.Projectile("ModHexBolt", "DFX_skelMageNewProjectile", "FxHexBolt", "Fly", 150f, 1.1f, 0.3f, 0.2f);
        // hex fire bursts instead of the skeleton mage's wall star / archer spark (FxHexPuff centre = cell (9, 13))
        HexPuffWall = FxKit.Visual("ModHexPuffWall", "FxHexPuff", "Wall");
        HexPuffHit = FxKit.Visual("ModHexPuffHit", "FxHexPuff", "Hit");
        Strike.ArtAt(HexPuffWall, "FxHexPuff", 9, 13);
        Strike.ArtAt(HexPuffHit, "FxHexPuff", 9, 13);
        SplitContacts(HexBolt, HexPuffWall, HexPuffHit);

            // the Gleaner keeps its mote swirl (it shows the pickup magnet); the Binder's chains and the Poltergeist's
            // cutlery are part of their bodies now (FormBinder / FormPoltergeist), so their old auras would only double them
            GleanerAura = Aura("ModGleanerAura", "FxGleanerAura");

            // Gleaner wisps: small, weak, plentiful ectoplasm
            WispPickup = FxFactory.Clone("EctoplasmPickup", "ModWispPickup");
            if (WispPickup != null)
            {
                var sh = SpriteSheets.Get("FxWisp");
                if (sh != null && sh.Has("Idle"))
                {
                    var clip = new ClipBuilder(sh, "Idle", "ModWispIdle").Loop().Build();
                    FxFactory.Reskin(WispPickup, clip, sh);
                }
                // its own collect pop and fade-out instead of the vanilla EctoplasmCollect / EctoplasmDisappear
                // (FxWisp centre = cell (10, 21), 2 px above the cell bottom, like the pickup's own sprite offset)
                WispCollect = WispEnd("EctoplasmCollect", "ModWispCollect", "Collect");
                WispFade = WispEnd("EctoplasmDisappear", "ModWispFade", "Fade");
                var pk = WispPickup.GetComponent<Pickup>();
                var mp = R.Get<MsgParams>(pk, "m_messageParams");
                if (mp != null) mp.m_float = 0.5f;
                if (WispCollect != null) R.Set(pk, "m_spawnOnCollect", WispCollect);
                FxFactory.SetEffect(WispPickup, destroyOnAnimEnd: false, destroyAfter: 12f,
                                    spawnOnDestroy: WispFade ?? R.Get<GameObject>(WispPickup.GetComponent<Effect>(), "m_spawnOnDestroy"));
                WispPickup.transform.localScale = new Vector3(0.85f, 0.85f, 1f);
            }

            // blob attacks
            MoteBite = FxFactory.Clone("DamageGiantRatAttack", "ModMoteBite");
            FxFactory.SetDamage(MoteBite, 0.4f, knockback: 0.2f);
            MoteBite = AimedMelee.Rotating(MoteBite);   // the bite turns with the aim
            Strike.HitBox(MoteBite, 10f * Px("BlobMote"), 10f * Px("BlobMote"));
            GelSlam = FxKit.BodyHit("ModGelSlam", 0.75f, 0f, 0.6f, 0.25f);
            // hitboxes are in design units and need the sheet's ArtScale by hand (offsets get it), else a fused blob's
            // would reach about twice as far as its body. Slams hit the floor ahead: they stay level.
            Strike.HitBox(GelSlam, 16f * Px("BlobGel"), 12f * Px("BlobGel"));
            BruteSlam = FxKit.BodyHit("ModBruteSlam", 1.2f, 0f, 1f, 0.25f);
            Strike.HitBox(BruteSlam, 22f * GrowBrute * Px("BlobBrute"), 16f * GrowBrute * Px("BlobBrute"));   // template scales were dropped by the pool after the first slam
            // the troll's shockwave pair (front + "BigShockwaveBack" child, damage events on the front clip) wearing
            // FxBlobQuake: a ring of goo, drawn at its final size (no template scale)
            BruteQuake = Quake("ModBruteQuake", 0.8f, 1.2f);
            TitanSlam = FxKit.BodyHit("ModTitanSlam", 1.6f, 0f, 1.3f, 0.25f);
            Strike.HitBox(TitanSlam, 30f * GrowTitan * Px("BlobTitan"), 20f * GrowTitan * Px("BlobTitan"));
            TitanEngulf = AimedMelee.Rotating(FxKit.BodyHit("ModTitanEngulf", 1f, 0.3f, 0.2f, 0.6f, goo, 1f));   // the gulp turns with the aim
            Strike.HitBox(TitanEngulf, 26f * GrowTitan * Px("BlobTitan"), 22f * GrowTitan * Px("BlobTitan"));
            // the King: a heavy slam that sends a goo ring out ahead, and Rain, globs that fall where their shadows grow
            KingSlam = FxKit.BodyHit("ModKingSlam", 1.2f, 0f, 1.1f, 0.25f);
            Strike.HitBox(KingSlam, 40f * GrowKing * Px("BlobKing"), 28f * GrowKing * Px("BlobKing"));
            KingQuake = Quake("ModKingQuake", 0.5f, 1f);
            KingDrop = FxKit.TimedHit("ModKingDrop", "TrollGroundPoundBigShockwave", "FxGooDrop", "Fall", 4, 5, KingRain.DropDamage, 0.4f, canFlip: false);
            Strike.Ground(KingDrop, "FxGooDrop", 13, 41, 16f, 8f);   // the splat is 16 px across; the shadow grows there for 0.8 s
            KingDropPool = FxKit.TimedHit("ModKingDropPool", "TrollGroundPoundBigShockwave", "FxGooDrop", "Fall", 4, 5, KingRain.DropDamage, 0.4f, canFlip: false);
            if (KingDropPool != null)
            {
                Strike.Ground(KingDropPool, "FxGooDrop", 13, 41, 16f, 8f);
                FxFactory.SetEffect(KingDropPool, destroyOnAnimEnd: true, spawnOnDestroy: GooPuddle, canFlip: false, freeRotate: false);   // the middle drop leaves a slowing puddle
            }
            // the splash crown a blob forms in (each slime base plays FX_SlimeSpawnShockwave from its Spawn clip)
            BlobSpawnSplash = FxFactory.Clone("FX_SlimeSpawnShockwave", "ModBlobSpawnSplash");
            if (BlobSpawnSplash != null)
            {
                FxFactory.StripChildren(BlobSpawnSplash, "ShockwaveBack");
                RingPair(BlobSpawnSplash, 17, 14, "FxBlobSpawn");
            }
        }

        /// <summary>The troll's shockwave pair (front + "BigShockwaveBack" child, damage events on the front clip) wearing
        /// FxBlobQuake: a ring of goo, drawn at its final size (no template scale).</summary>
        static GameObject Quake(string name, float damage, float knock)
        {
            var q = FxKit.Swipe(name, "TrollGroundPoundBigShockwave", damage, knock);
            if (q == null) return null;
            FxFactory.StripChildren(q, "BigShockwaveBack");
            RingPair(q, 26, 16, "FxBlobQuake");
            q.transform.localScale = Vector3.one;
            FxFactory.SetDamage(q, damage, knockback: knock, status: null);
            FxFactory.SetContacts(q, clearSpawnOnHit: true);   // no vanilla archer spark on the hero
            Strike.Collider(q, 42f, 18f);   // the ring's footprint
            return q;
        }

        internal static GameObject Aura(string name, string art)
        {
            var go = FxKit.Visual(name, art, "Play", loop: true);
            if (go != null) FxFactory.SetEffect(go, destroyOnAnimEnd: false, offsetY: 8f, canFlip: false, freeRotate: false);
            return go;
        }

        /// <summary>A wisp end effect: the vanilla ectoplasm one (motion, flash, depth) wearing an FxWisp anim.</summary>
        static GameObject WispEnd(string vanilla, string name, string anim)
        {
            var sh = SpriteSheets.Get("FxWisp");
            if (sh == null || !sh.Has(anim)) return null;
            var go = FxFactory.Clone(vanilla, name);
            if (go == null) return null;
            FxFactory.StripChildren(go);
            FxFactory.Reskin(go, new ClipBuilder(sh, anim, name + "Clip").Once().Build(), sh);
            FxFactory.SetEffect(go, destroyOnAnimEnd: true);
            var spr = go.GetComponent<exSprite>();
            if (spr != null) { spr.anchor = exPlane.Anchor.BotCenter; spr.offset = new Vector2(0f, -2f); spr.color = Color.white; }
            NoTints(go);
            return go;
        }

        static void NoTints(GameObject go)
        {
            foreach (var t in go.GetComponentsInChildren<ColorTinter>(true)) t.enabled = false;
        }

        /// <summary>
        /// A vanilla front/back shockwave pair reskinned with a mod sheet's "Ring" (front, on the root, keeping the vanilla
        /// clip's events) and "Back" (on the one remaining child). (gx, gy) = the ring centre in the sheet's cells.
        /// </summary>
        internal static void RingPair(GameObject go, int gx, int gy, string sheet)
        {
            var rsh = SpriteSheets.Get(sheet);
            if (rsh == null) return;
            string clipName = "Mod" + sheet;
            var anim = go.GetComponent<exSpriteAnimation>();
            var front = anim != null ? anim.defaultAnimation : null;
            FxFactory.Reskin(go, SpriteSheets.MakeClip(rsh, "Ring", front, clipName + "Ring"), rsh);
            Transform back = go.transform.childCount > 0 ? go.transform.GetChild(0) : null;
            if (back != null)
            {
                var ba = back.GetComponent<exSpriteAnimation>();
                FxFactory.Reskin(back.gameObject, SpriteSheets.MakeClip(rsh, "Back", ba != null ? ba.defaultAnimation : null, clipName + "Back"), rsh);
            }
            foreach (var spr in go.GetComponentsInChildren<exSprite>(true))
            {
                spr.anchor = exPlane.Anchor.BotCenter;
                spr.offset = new Vector2(rsh.manifest.cellW * 0.5f - gx - 0.5f, gy + 1f - rsh.manifest.cellH);
                spr.color = Color.white;
            }
            NoTints(go);
        }

        /// <summary>
        /// Hex bolt contacts: walls spawn <paramref name="wall"/>, body contacts that end the shot spawn <paramref name="hit"/>
        /// (and so does the legacy fallback). Runs after FxKit.Projectile, so it wins over ImpactFx's neutral puff (the
        /// ghost sheets have no god). Props the bolt passes through stay silent.
        /// </summary>
        internal static void SplitContacts(GameObject fx, GameObject wall, GameObject hit)
        {
            var d = fx != null ? fx.GetComponent<DamageEffect>() : null;
            if (d == null || wall == null || hit == null || d.m_contactData == null) return;
            int wallLayer = LayerMask.NameToLayer("Wall");
            foreach (var c in d.m_contactData)
            {
                if (c == null) continue;
                bool isWall = wallLayer >= 0 && (c.m_layerMask.value & (1 << wallLayer)) != 0;
                if (isWall) c.m_spawnOnHit = wall;
                else if (c.m_destroyOnHit || c.m_spawnOnHit != null) c.m_spawnOnHit = hit;
            }
            R.Set(d, "m_spawnOnHit", hit);
        }

        // ------------------------------------------------------------------ blob kits
        // Kit numbers below are in each sheet's design space (MonsterFactory multiplies them by ArtScale). The fusion
        // art draws Brute and Titan bigger than that (ghost_rigs.py GROW), so their design numbers grow with them.
        const float GrowBrute = 1.3f, GrowTitan = 1.2f, GrowKing = 1.3f;
        /// <summary>A sheet's ArtScale (design units -> pixels), for sizes MonsterFactory does not scale (hitboxes).</summary>
        static float Px(string sheet) { float k; return ArtScale.BySheet.TryGetValue(sheet, out k) ? k : 1f; }
        static void MoteKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0];
            int n0 = Strike.Mark(p);
            int bite = Kit.AddEffect(p, MoteBite, attach: true, destroyOnAnimEnd: true, offsetX: 6f, offsetY: 6f);   // mouth (9, 2)
            atk.Clear();
            // Bite 6: wind-up 0-2, the snap (hit) on 3, chew 4, let go 5
            atk.Add(Kit.Attack(a0, Kit.Melee(sh, "Bite", "ModMoteBite", Kit.Voice(p), 3, bite, 70f).Build(), 0.9f, rangeInner: 8f, rangeOuter: 18f));
            Strike.Feet(p, n0, 5f);
        }

        static void SpitterKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0];
            int n0 = Strike.Mark(p);
            int glob = Kit.AddEffect(p, GooGlob, offsetX: 10f, offsetY: 1f);   // on the floor under the spout (11, 13)
            atk.Clear();
            // the glob slides ~62 px before it splats
            atk.Add(Kit.Attack(a0, Kit.Shot(sh, "Spit", "ModSpitterSpit", 3, Kit.Voice(p), 0f, glob).Build(), 1.6f,
                               rangeInner: 32f, rangeOuter: 60f, rangeRetreat: 25f));
            Strike.Feet(p, n0, 9f);
        }

        static void GelKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0];
            int n0 = Strike.Mark(p);
            int slam = Kit.AddEffect(p, GelSlam, attach: true, destroyOnAnimEnd: true, offsetX: 9f, offsetY: 6f);   // splat front (17, 1)
            atk.Clear();
            atk.Add(Kit.Attack(a0, Kit.Melee(sh, "Slam", "ModGelSlam", Kit.Voice(p), 3, slam, 60f).Build(), 1.4f, rangeInner: 8f, rangeOuter: 22f));
            Strike.Feet(p, n0, 6f);
        }

        static void BruteKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            const float g = GrowBrute;
            int slam = Kit.AddEffect(p, BruteSlam, attach: true, destroyOnAnimEnd: true, offsetX: 13f * g, offsetY: 8f * g);   // front (24, 1): x 2..24
            int quake = Kit.AddEffect(p, BruteQuake, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            atk.Clear();
            atk.Add(Kit.Attack(a0, Kit.Melee(sh, "Slam", "ModBruteSlam", v, 4, slam, 60f).Build(), 1.4f, rangeInner: 12f * g, rangeOuter: 28f * g));
            var bounce = new ClipBuilder(sh, "Bounce", "ModBruteBounce").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff")
                .EvF(2, "AnimMove", 140f).Ev(2, "AnimCollideOff").Ev(5, "AnimMoveStop").Ev(5, "AnimCollideOn")
                .Ev(5, "AnimAttack", quake).EvO(5, "AnimSound", v).Ev(-1, "AnimRun").Build();
            // the hop covers ~36 px and the landing ring reaches 21 more
            Kit.EnableSpecial(p, Kit.Attack(a0, bounce, 0f, rangeInner: 25f, rangeOuter: 58f), 5f);
            Strike.Feet(p, n0, 9f * g);
        }

        static void TitanKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            const float g = GrowTitan;
            int slam = Kit.AddEffect(p, TitanSlam, attach: true, destroyOnAnimEnd: true, offsetX: 18f * g, offsetY: 10f * g);   // front (32, 1): x 3..33
            int engulf = Kit.AddEffect(p, TitanEngulf, attach: true, destroyOnAnimEnd: true, offsetX: 18f * g, offsetY: 11f * g);   // mouth (28-35, 14)
            atk.Clear();
            atk.Add(Kit.Attack(a0, Kit.Melee(sh, "Slam", "ModTitanSlam", v, 4, slam, 50f).Build(), 1.6f, rangeInner: 16f * g, rangeOuter: 36f * g));
            var eng = new ClipBuilder(sh, "Engulf", "ModTitanEngulf").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff")
                .EvF(2, "AnimMove", 160f).Ev(2, "AnimAttack", engulf).EvO(2, "AnimSound", v)
                .Ev(5, "AnimMoveStop").Ev(-1, "AnimRun").Build();
            // 160 px/s for 0.22 s = 35 px lunge + 31 px reach
            Kit.EnableSpecial(p, Kit.Attack(a0, eng, 0f, rangeInner: 25f, rangeOuter: 66f + 31f * (g - 1f)), 6f);
            Strike.Feet(p, n0, 10f * g);
        }

        static void KingKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            const float g = GrowKing;
            int slam = Kit.AddEffect(p, KingSlam, attach: true, destroyOnAnimEnd: true, offsetX: 21f * g, offsetY: 9f * g);   // the slam lands (25, 1): x 1..27
            int quake = Kit.AddEffect(p, KingQuake, offsetX: 34f * g);   // the ring rolls out ahead of the landing, 22 px out
            atk.Clear();
            // Slam 8: rears up 0-3 (0.48 s), lands on 4 with the ring
            var slamClip = Kit.Melee(sh, "Slam", "ModKingSlam", v, 4, slam, 40f).Ev(4, "AnimAttack", quake).Build();
            atk.Add(Kit.Attack(a0, slamClip, 1.8f, rangeInner: 12f * g, rangeOuter: 30f * g));   // the slam reaches 27 px, its ring 43
            // Rain 9: rears up 0-3, spews on 4 (0.54 s); each glob lands 0.8 s later where its shadow grew
            var rain = new ClipBuilder(sh, "Rain", "ModKingRain").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(3, "AnimInputMultiplyStop").Ev(3, "AnimInputOff")
                .Ev(4, KingRain.Event).EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            Kit.EnableSpecial(p, Kit.Attack(a0, rain, 0f, rangeInner: 20f, rangeOuter: KingRain.Reach), 7f);
            Strike.Feet(p, n0, 12f * g);
        }

        static readonly MonsterDef[] Blobs =
        {
            new MonsterDef { id = "BlobMote", basePrefab = "EnemySlime1BlueMedium", health = 0.6f, speedMult = 1.45f, kit = MoteKit, keepEvolutions = true },
            new MonsterDef { id = "BlobSpitter", basePrefab = "EnemySlime1BlueMedium", health = 1.2f, kit = SpitterKit, keepEvolutions = true },
            new MonsterDef { id = "BlobGel", basePrefab = "EnemySlime1BlueMedium", health = 1.4f, kit = GelKit, keepEvolutions = true },
            // fused blobs: more health than the Gels that made them (2 Gels 2.8 -> 3.5, 3 Gels 4.2 -> 6)
            new MonsterDef { id = "BlobBrute", basePrefab = "EnemySlime1BlueLarge", health = 3.5f, speedMult = 0.9f, kit = BruteKit, keepEvolutions = true, customize = Fused },
            new MonsterDef { id = "BlobTitan", basePrefab = "EnemySlime1BlueLarge", health = 6f, speedMult = 0.8f, kit = TitanKit, keepEvolutions = true, customize = Fused },
            // the silver and gold ghosts' prize: a little more health than a Titan, three bodies of ectoplasm, no Gel left
            // behind; its Rain reaches from afar but every glob shows where it lands
            new MonsterDef { id = "BlobKing", basePrefab = "EnemySlime1BlueLarge", health = 6.5f, speedMult = 0.8f, kit = KingKit, keepEvolutions = true,
                             customize = Fused, traits = new MonsterTraits().Add<KingRain>() },
        };

        /// <summary>The King's price in bodies of ectoplasm (a Titan takes three Gels).</summary>
        public const int KingBodies = 3;

        static void Fused(GameObject go, Player p) { if (go.GetComponent<FusedBlob>() == null) go.AddComponent<FusedBlob>(); }

        public static void Register()
        {
            BuildFx();
            var built = new Dictionary<string, Player>();
            foreach (var d in Blobs)
            {
                var p = MonsterFactory.Build(d);
                if (p != null) built[d.id] = p;
            }
            // every blob's Spawn clip fires AnimAttack 3 = the vanilla slime's FX_SlimeSpawnShockwave: use the goo splash
            if (BlobSpawnSplash != null)
                foreach (var b in built.Values)
                    foreach (var e in Kit.Effects(b))
                        if (e != null && e.m_object != null && e.m_object.name == "FX_SlimeSpawnShockwave") e.m_object = BlobSpawnSplash;
            // a blob's special is on the ghost button, Back only lets its player out (BlobSpecialInput)
            foreach (var b in built.Values) if (b.GetComponent<BlobSpecialInput>() == null) b.gameObject.AddComponent<BlobSpecialInput>();
            built.TryGetValue("BlobMote", out Mote);
            built.TryGetValue("BlobSpitter", out Spitter);
            built.TryGetValue("BlobGel", out Gel);
            built.TryGetValue("BlobBrute", out Brute);
            built.TryGetValue("BlobTitan", out Titan);
            built.TryGetValue("BlobKing", out King);
            // the number of Gels fused is the blob made: 2 a Brute, 3 a Titan
            if (Gel != null) MonsterTraits.Register(Gel.gameObject.name, new BlobTraits { gel = true });
            if (Brute != null) s_byGels[2] = Brute;
            if (Titan != null) s_byGels[3] = Titan;
            // a dying Titan leaves a Gel (it can be fused again with other Gels)
            var gelSpawner = Gel != null ? FxKit.MinionSpawner("ModGelSpawner", Gel.gameObject, "FxMergeBurst", "Play") : null;
            if (Titan != null && gelSpawner != null) { Kit.AddDeathSpawn(Titan, gelSpawner); Strike.DeathAtFeet(Titan); }
            Strike.KeepAllScales();
            RegisterBlobs();

            Plugin.Log.LogInfo("Ghost forms ready: " + built.Count + " blob monsters");
            try { GhostV11.Register(); } catch (Exception e) { Plugin.Log.LogError("Ghost forms (Banshee to Miser) failed: " + e); }
            GhostCustom.Load();
        }

        // ------------------------------------------------------------------ ghost behaviour
        /// <summary>Poltergeist Throw: the hex bolt leaves the hand on this frame (art/out_ghosts/TIMING.md).</summary>
        const int ThrowRelease = 3;

        /// <summary>Does a middle click mean the ghost button for this player right now (so it must not pause)?</summary>
        public static bool MiddleClickInUse(PlayerData pd)
        {
            // the ghost button itself is GhostControls (Down / Name); for the mouse player it is always the middle click
            if (pd == null || !pd.IsHuman || !GhostControls.IsMouse((int)pd.ControllerId)) return false;
            var go = pd.GameObject;
            var p = go != null ? go.GetComponent<Player>() : null;
            if (p == null) return false;
            // a ghost that spawns Gels fuses them with it; in a blob it starts the blob's special; a gold monster jumps
            // out with it
            if (ModUtil.IsGhost(p)) return FusesGels(pd);
            if (BlobSpecialInput.SpecialOnGhostButton(p)) return true;
            return FormOf(pd) == GhostForm.Gold && !pd.IsHero;
        }

        public static GameObject FormPrefab(GhostForm form, GameObject ghost)
        {
            var def = Def(form);
            return def != null && def.tier == SlotTier.Normal ? BodyPrefab(def, ghost, null, null) : null;
        }

        /// <summary>The ghost prefab a player spawns as for their chosen form (null: the vanilla ghost).</summary>
        public static GameObject BodyFor(PlayerData pd, GameObject ghost)
        {
            var def = DefOf(pd);
            if (def == null || ghost == null) return null;
            if (def.tier == SlotTier.Normal) return BodyPrefab(def, ghost, null, null);
            // custom slots: the player's own composed look (key = the look, so editing it builds a new prefab)
            var sh = GhostCustom.BodySheet(pd.Id, def.tier);
            return sh != null ? BodyPrefab(def, ghost, sh, sh.id) : null;
        }

        /// <summary>A custom look was dropped (GhostCustom.Prune): forget the ghost prefabs built on it (never destroyed:
        /// the game's pool may still hold instances of them; a new look builds a new prefab).</summary>
        internal static List<exSpriteAnimClip> ForgetLook(string lookKey)
        {
            var clips = new List<exSpriteAnimClip>();
            var gone = new List<string>();
            foreach (var kv in s_formPrefabs) if (kv.Key.EndsWith("|" + lookKey)) gone.Add(kv.Key);
            foreach (var k in gone)
            {
                var g = s_formPrefabs[k];
                s_formPrefabs.Remove(k);
                var p = g != null ? g.GetComponent<Player>() : null;
                if (p == null) continue;
                // the look's own clips (built for this prefab only): GhostCustom.Drop frees them with the atlas
                foreach (var f in new[] { "m_animationSpawn", "m_animationIdle", "m_animationRun", "m_animationDead" })
                {
                    var c = R.Get<exSpriteAnimClip>(p, f);
                    if (c != null && !clips.Contains(c)) clips.Add(c);
                }
            }
            return clips;
        }

        /// <summary>
        /// The ghost a form player flies around as: a clone of that player's own vanilla ghost prefab (P1Blue .. P4Yellow:
        /// same frames, the colour is in its material) whose clips show the form's body. Every form clip points at an atlas
        /// that wears a copy of that prefab's material with the form texture, so P2-P4's palette ramp recolours the form's
        /// shroud and skin exactly like it recolours the vanilla ghost (the art uses the vanilla ghost's key colours), and
        /// exSprite.SetSprite (which swaps in atlas.material) keeps the player's colours. Null for the Wisp.
        /// </summary>
        static GameObject BodyPrefab(GhostFormEntry def, GameObject ghost, SpriteSheet custom, string lookKey)
        {
            if (ghost == null || def.form == GhostForm.Wisp) return null;
            string key = (int)def.form + "|" + ghost.name + "|" + lookKey;
            GameObject g;
            if (s_formPrefabs.TryGetValue(key, out g) && g != null) return g;
            var fsh = custom ?? (def.bodyArt != null ? SpriteSheets.Get(def.bodyArt) : null);
            if (fsh == null) return null;
            var form = def.form;
            g = MonsterFactory.ClonePrefab(ghost, ghost.name + "_Mod" + form + (lookKey != null ? "_" + s_formPrefabs.Count : ""));
            var p = g.GetComponent<Player>();
            var r = g.GetComponent<Renderer>();
            try
            {
                // custom looks are drawn in their final colours (no player ramp): they keep the composed atlas' material
                var atlas = custom != null ? custom.atlas : PlayerAtlas(fsh, r != null ? r.sharedMaterial : null, ghost.name);
                string pre = "ModGhost" + form + "_" + ghost.name + "_" + (lookKey != null ? s_formPrefabs.Count + "_" : "");
                var spawn = Retarget(SpriteSheets.MakeClip(fsh, "Spawn", R.Get<exSpriteAnimClip>(p, "m_animationSpawn"), pre + "Spawn"), atlas);
                var idle = Retarget(SpriteSheets.MakeClip(fsh, "Idle", R.Get<exSpriteAnimClip>(p, "m_animationIdle"), pre + "Idle"), atlas);
                var run = Retarget(SpriteSheets.MakeClip(fsh, "Run", R.Get<exSpriteAnimClip>(p, "m_animationRun"), pre + "Run"), atlas);
                if (spawn != null) { spawn.wrapMode = WrapMode.Once; R.Set(p, "m_animationSpawn", spawn); }
                if (idle != null) { idle.wrapMode = WrapMode.Loop; R.Set(p, "m_animationIdle", idle); R.Set(p, "m_animationDead", idle); }
                if (run != null) { run.wrapMode = WrapMode.Loop; R.Set(p, "m_animationRun", run); }
                var spr = g.GetComponent<exSprite>();
                if (spr != null && idle != null && idle.frameInfos.Count > 0)
                {
                    spr.SetSprite(atlas, idle.frameInfos[0].index);
                    if (r != null) r.sharedMaterial = atlas.material;
                }
                var sa = g.GetComponent<exSpriteAnimation>();
                if (sa != null) { sa.animations = new List<exSpriteAnimClip>(); sa.defaultAnimation = null; }
                switch (form)
                {
                    case GhostForm.Poltergeist: ArmPoltergeist(p, fsh, atlas, pre); break;
                    case GhostForm.Banshee: GhostV11.ArmAbility(p, fsh, atlas, pre, "Wail", 3, 5f); break;
                    case GhostForm.Kindler: GhostV11.ArmAbility(p, fsh, atlas, pre, "Ignite", 3, 1.5f); break;
                    case GhostForm.Mason: GhostV11.ArmAbility(p, fsh, atlas, pre, "Rouse", 3, 4f); break;
                    case GhostForm.Hexer: GhostV11.ArmHexer(p, fsh, atlas, pre); break;
                }
            }
            catch (Exception e) { Plugin.Log.LogError("Ghost form " + form + " (" + ghost.name + ") build failed: " + e); }
            s_formPrefabs[key] = g;
            return g;
        }

        static readonly Dictionary<string, exAtlas> s_playerAtlas = new Dictionary<string, exAtlas>();

        /// <summary>The sheet's atlas, drawn with a copy of the player's ghost material (keeps its _ColorRamp, flash colour, shader).</summary>
        static exAtlas PlayerAtlas(SpriteSheet fsh, Material home, string owner)
        {
            if (home == null) return fsh.atlas;
            string k = fsh.id + "|" + owner;
            exAtlas a;
            if (s_playerAtlas.TryGetValue(k, out a) && a != null) return a;
            a = ScriptableObject.CreateInstance<exAtlas>();
            a.name = "ModAtlas_" + fsh.id + "_" + owner;
            a.texture = fsh.atlas.texture;
            a.elements = fsh.atlas.elements;
            a.material = new Material(home) { name = home.name + "+" + fsh.id, mainTexture = fsh.atlas.texture };
            a.hideFlags |= HideFlags.DontUnloadUnusedAsset;
            a.material.hideFlags |= HideFlags.DontUnloadUnusedAsset;
            s_playerAtlas[k] = a;
            return a;
        }

        internal static exSpriteAnimClip Retarget(exSpriteAnimClip c, exAtlas atlas)
        {
            if (c == null) return null;
            var frames = new List<exSpriteAnimClip.FrameInfo>(c.frameInfos.Count);
            foreach (var f in c.frameInfos)
                frames.Add(new exSpriteAnimClip.FrameInfo { atlas = atlas, index = f.index, length = f.length, textureGUID = f.textureGUID });
            c.frameInfos = frames;
            return c;
        }

        /// <summary>Poltergeist: Attack = the Throw anim; the hex bolt leaves the hand on the release frame.</summary>
        static void ArmPoltergeist(Player p, SpriteSheet fsh, exAtlas atlas, string pre)
        {
            if (!fsh.Has("Throw")) return;
            var effects = Kit.Effects(p);
            effects.Clear();
            // the release hand is at (11.6, -9.3) from the ghost's origin: node (0, 10) + (12, -1)
            int bolt = Kit.AddEffect(p, HexBolt, offsetX: 12f, offsetY: -1f);
            var clip = Retarget(new ClipBuilder(fsh, "Throw", pre + "Throw").Once()
                .Ev(ThrowRelease, "AnimAttack", bolt).Ev(-1, "AnimRun").Build(), atlas);
            var template = MonsterFactory.FindVanilla("EnemySkeletonMage");
            var a = Kit.Attack(Kit.Attacks(template)[0], clip, 1.8f, rangeInner: 40f, rangeOuter: 90f);
            a.m_sound = null;
            var atk = Kit.Attacks(p);
            atk.Clear();
            atk.Add(a);
        }

        /// <summary>What a player's Back spawns (<paramref name="vanilla"/>: the game's plain blob). The Banshee to the Miser
        /// always raise their own monster, which their abilities work on; the rest spawn the blob in effect (GhostBlobs):
        /// the regular blob, their own once earned, or what they picked.</summary>
        public static GameObject FodderFor(PlayerData pd, GameObject vanilla)
        {
            return GhostV11.FodderFor(FormOf(pd)) ?? GhostBlobs.PrefabOf(pd, vanilla);
        }

        /// <summary>The game's plain blob for a player (the large one when their god uses it), read straight from their
        /// setup so a pick never feeds back into itself.</summary>
        public static GameObject PlainBlob(PlayerData pd)
        {
            var setup = pd != null ? pd.Setup : null;
            if (setup == null) return null;
            Deity d = null;
            try { d = pd.GetDeity(); } catch { }
            return d != null && d.GetUseLargeFodder() && setup.m_fodderLarge != null ? setup.m_fodderLarge : setup.m_fodder;
        }

        // ------------------------------------------------------------------ the blob choice
        /// <summary>
        /// The blobs (GhostBlobs): the regular blob for every form. The Gleaner, Poltergeist and Binder each earn their own
        /// (Mote, Spitter, Gel) through a challenge played as that form (BlobChallenges); until then they spawn the regular
        /// blob, and after it their own is the default with the regular one still a pick. The silver and gold ghosts pick
        /// from the regular blob, every earned Mote, Spitter and Gel, and the King, which is theirs alone.
        /// </summary>
        static void RegisterBlobs()
        {
            var regular = new GhostBlobDef { id = "Plain", name = "Regular Blob", summary = "The game's own blob, nothing added", prefab = PlainBlob };
            GhostBlobs.Register(regular);
            GhostBlobs.Regular = regular;
            Blob("Mote", "Mote Blob", "Quick and fragile. They come in pairs", Mote, BlobChallenges.Mote, GhostForm.Gleaner);
            Blob("Spitter", "Spitter Blob", "Spits goo along the floor that slows", Spitter, BlobChallenges.Spitter, GhostForm.Poltergeist);
            Blob("Gel", "Gel Blob", "Fuses into bigger blobs: ghost button", Gel, BlobChallenges.Gel, GhostForm.Binder);
            GhostBlobs.OwnOf = def =>
            {
                var e = def as GhostFormEntry;
                switch (e != null ? e.form : GhostForm.Wisp)
                {
                    case GhostForm.Gleaner: return GhostBlobs.Find("Mote");
                    case GhostForm.Poltergeist: return GhostBlobs.Find("Spitter");
                    case GhostForm.Binder: return GhostBlobs.Find("Gel");
                }
                return null;
            };
            if (King != null)
                GhostBlobs.Register(new GhostBlobDef
                {
                    id = "King", name = "King Blob", summary = "Ghost button rains globs. Costs more",
                    prefab = pd => King.gameObject, art = "BlobKing", bodies = KingBodies,
                    fits = f => f != null && f.tier != SlotTier.Normal,   // the silver and gold ghosts' own prize
                });
        }

        /// <summary>A form's own blob: that form and the silver and gold ghosts may pick it once its challenge is done.</summary>
        static void Blob(string id, string name, string summary, Player p, string unlock, GhostForm owner)
        {
            if (p == null) return;
            GhostBlobs.Register(new GhostBlobDef
            {
                id = id, name = name, summary = summary, prefab = pd => p.gameObject, art = "Blob" + id, unlock = unlock,
                fits = f => f != null && (f.tier != SlotTier.Normal || (f as GhostFormEntry) != null && ((GhostFormEntry)f).form == owner),
            });
        }

        /// <summary>The player's ghost spawns Gels (the Binder once it earns them, or a silver / gold ghost that picked
        /// them): the ghost button fuses them.</summary>
        public static bool FusesGels(PlayerData pd)
        {
            return pd != null && Gel != null && FodderFor(pd, null) == Gel.gameObject;
        }

        /// <summary>The player's ghost spawns Motes (the Gleaner once it earns them, or a silver / gold ghost that picked
        /// them): they come in pairs.</summary>
        public static bool SpawnsMotes(PlayerData pd)
        {
            return pd != null && Mote != null && FodderFor(pd, null) == Mote.gameObject;
        }

        /// <summary>How close (px) to the Binder ghost its blobs must be to fuse.</summary>
        public const float FuseRange = 90f;
        /// <summary>The most Gels one fusion takes (they make a Titan).</summary>
        public const int MaxGels = 3;

        /// <summary>
        /// A ghost that spawns Gels (the Binder once it earns them, or a silver / gold ghost that picked them): fuse its Gels near the ghost into one
        /// blob: 2 Gels make a Brute, 3 a Titan. The nearest Gels go in first. Brutes and Titans never go into a fusion, so
        /// a fused blob stays what it is until it dies.
        /// </summary>
        public static bool TryMerge(Player ghost)
        {
            var pd = ghost.GetPlayerData();
            Vector2 at = ghost.transform.position;
            var near = new List<Player>();
            foreach (var mm in UnityEngine.Object.FindObjectsOfType<ModMonster>())
            {
                var blob = mm != null ? mm.Traits as BlobTraits : null;
                if (blob == null || !blob.gel) continue;
                var p = mm.GetComponent<Player>();
                var h = mm.GetComponent<Health>();
                if (p == null || h == null || !h.IsAlive() || !p.GetIsAI()) continue;
                if (R.Get<PlayerData>(p, "m_spawner") != pd) continue;
                if (((Vector2)p.transform.position - at).sqrMagnitude > FuseRange * FuseRange) continue;
                near.Add(p);
            }
            near.Sort((a, b) => ((Vector2)a.transform.position - at).sqrMagnitude.CompareTo(((Vector2)b.transform.position - at).sqrMagnitude));
            if (near.Count > MaxGels) near.RemoveRange(MaxGels, near.Count - MaxGels);
            Player made;
            if (near.Count < 2 || !s_byGels.TryGetValue(near.Count, out made)) return false;
            Vector2 mid = Vector2.zero;
            foreach (var p in near) mid += (Vector2)p.transform.position;
            mid /= near.Count;
            foreach (var p in near) p.SendMessage("MsgDespawn", SendMessageOptions.DontRequireReceiver);
            if (MergeBurst != null) SystemPool.Spawn(MergeBurst, mid);
            var go = made.gameObject.Spawn(mid, Quaternion.identity);
            if (go != null) go.GetComponent<Player>().InitAsAI(ghost.gameObject);
            return true;
        }

        public static void SpawnWisp(Vector2 near)
        {
            if (WispPickup == null) return;
            var mgr = SystemLevel.GetGhostPickupManager();
            var parent = mgr != null ? R.Get<Transform>(mgr, "m_pickupContainer") : null;
            var cam = SystemLevel.GetCamera();
            if (cam == null) return;
            var room = R.Get<Room>(Singleton<SystemLevel>.Get, "m_currentRoom");
            for (int tries = 0; tries < 6; tries++)
            {
                Vector2 half = cam.GetComponent<Camera>().ViewportToWorldPoint(new Vector3(0.95f, 0.95f, 0f)) - cam.transform.position;
                var p = (Vector2)cam.transform.position + Vector2.Scale(half, new Vector2(UnityEngine.Random.Range(-1f, 1f), UnityEngine.Random.Range(-1f, 1f)));
                if (room != null && room.IsPointInRoom(p)) continue;
                var go = WispPickup.Spawn(p, Quaternion.identity);
                if (go != null && parent != null) go.transform.parent = parent;
                return;
            }
        }
    }

    /// <summary>Per-ghost behaviour for the chosen form (Gleaner aura, magnet and wisps) and blob (the fuse button of a
    /// ghost that spawns Gels). The form's body itself is its own ghost prefab (GhostPack.FormPrefab), swapped in by
    /// Patch_SpawnGhost.</summary>
    public class GhostFormFx : MonoBehaviour
    {
        public GhostForm form;
        /// <summary>This ghost spawns Gels and fuses them with the ghost button (the Binder, or a form that picked Gels).</summary>
        public bool fuses;
        Player m_player;
        GameObject m_aura;
        float m_wispTimer;

        void Awake() { m_player = GetComponent<Player>(); }

        public void Setup(GhostForm f)
        {
            form = f;
            fuses = GhostPack.FusesGels(m_player != null ? m_player.GetPlayerData() : null);
            if (m_aura != null) { SystemPool.Despawn(m_aura); m_aura = null; }
            var tmpl = f == GhostForm.Gleaner ? GhostPack.GleanerAura : GhostV11.AuraFor(f);
            if (tmpl != null)
            {
                m_aura = SystemPool.Spawn(tmpl, transform.position);
                if (m_aura != null) { m_aura.transform.parent = transform; m_aura.transform.localPosition = new Vector3(0f, 0f, 0.5f); }
            }
            m_wispTimer = UnityEngine.Random.Range(0.5f, 1.5f);
        }

        void OnDisable()
        {
            if (m_aura != null) { SystemPool.Despawn(m_aura); m_aura = null; }
        }

        float m_fuseCooldown;
        float m_pickupScan;
        Pickup[] m_pickups;

        /// <summary>
        /// The fuse button, separate from Back (which the game also uses to spawn fodder):
        /// X on a controller (Y is the game's Start fallback on some pads), C for the keyboard player, MIDDLE CLICK for the
        /// mouse player (the game reads the middle button as Start = pause for the Mouse controller only, so
        /// Patch_MiddleClickPause swallows that pause while the mouse player is a Binder ghost).
        /// </summary>
        bool FusePressed() { return GhostControls.Down(m_player != null ? m_player.GetPlayerData() : null); }

        void Update()
        {
            if (fuses)
            {
                m_fuseCooldown -= Time.deltaTime;
                if (m_fuseCooldown <= 0f && FusePressed() && ModUtil.IsGhost(m_player))
                {
                    m_fuseCooldown = 0.3f;
                    try
                    {
                        // nothing to fuse: the stored bodies blink, as when Back cannot spawn one
                        if (!GhostPack.TryMerge(m_player)) GhostV11.Flash(m_player);
                    }
                    catch (System.Exception e) { Plugin.Log.LogError("Gel fuse failed: " + e); }
                }
            }
            if (form != GhostForm.Gleaner) return;
            Vector2 me = transform.position;
            // GetGhostPickups is a GetComponentsInChildren (a new array each call): refresh the list 5 times a second
            m_pickupScan -= Time.deltaTime;
            if (m_pickupScan <= 0f || m_pickups == null)
            {
                m_pickupScan = 0.2f;
                var mgr = SystemLevel.GetGhostPickupManager();
                m_pickups = mgr != null ? mgr.GetGhostPickups() : null;
            }
            if (m_pickups != null)
            {
                foreach (var pk in m_pickups)
                {
                    if (pk == null || !pk.gameObject.activeInHierarchy) continue;
                    var d = me - (Vector2)pk.transform.position;
                    float m = d.magnitude;
                    if (m < 110f && m > 2f) pk.transform.position += (Vector3)(d / m * Mathf.Lerp(90f, 30f, m / 110f) * Time.deltaTime);
                }
            }
            m_wispTimer -= Time.deltaTime;
            if (m_wispTimer <= 0f)
            {
                m_wispTimer = UnityEngine.Random.Range(0.7f, 1.2f);
                if (!SystemLevel.GetBossEncounterActive() || UnityEngine.Random.value < 0.5f) GhostPack.SpawnWisp(me);
            }
        }
    }

    // ---------------------------------------------------------------------- patches
    [HarmonyPatch(typeof(SystemLevel), "SpawnGhost", new[] { typeof(PlayerData), typeof(Vector2), typeof(float) })]
    static class Patch_SpawnGhost
    {
        static GameObject s_restore;
        static void Prefix(PlayerData plrData, float delay)
        {
            s_restore = null;
            if (delay > 0f || plrData == null || plrData.Setup == null) return;
            var form = GhostPack.FormOf(plrData);
            if (form == GhostForm.Wisp || plrData.IsBot) return;
            try
            {
                var body = GhostPack.BodyFor(plrData, plrData.Setup.m_ghost);
                if (body == null) return;
                s_restore = plrData.Setup.m_ghost;
                plrData.Setup.m_ghost = body;
            }
            catch (Exception e) { Plugin.Log.LogError("Ghost form swap failed: " + e); s_restore = null; }
        }

        /// <summary>Runs even if SpawnGhost throws, so the player's real ghost prefab is always put back.</summary>
        static Exception Finalizer(PlayerData plrData, Exception __exception)
        {
            if (s_restore != null && plrData != null && plrData.Setup != null) plrData.Setup.m_ghost = s_restore;
            s_restore = null;
            return __exception;
        }

        static void Postfix(PlayerData plrData, float delay)
        {
            if (delay > 0f || plrData == null) return;
            try
            {
                var go = plrData.GameObject;
                if (go == null || !R.Get<bool>(go.GetComponent<Player>(), "m_isGhost")) return;
                var fx = go.GetComponent<GhostFormFx>() ?? go.AddComponent<GhostFormFx>();
                fx.Setup(GhostPack.FormOf(plrData));
                var ab = go.GetComponent<GhostAbilityFx>() ?? go.AddComponent<GhostAbilityFx>();
                ab.Setup(GhostPack.FormOf(plrData));
            }
            catch (Exception e) { Plugin.Log.LogError("Ghost form setup failed: " + e); }
        }
    }

    [HarmonyPatch(typeof(PlayerData), "GetFodderPrefab")]
    static class Patch_FodderPrefab
    {
        static void Postfix(PlayerData __instance, ref GameObject __result)
        {
            try { __result = GhostPack.FodderFor(__instance, __result); } catch { }
        }
    }

    [HarmonyPatch(typeof(Ghost), "SpawnFodder")]
    static class Patch_GhostSpawnFodder
    {
        static bool Prefix(Ghost __instance, ref bool __result)
        {
            try
            {
                var p = __instance.GetComponent<Player>();
                if (p == null) return true;
                var form = GhostPack.FormOf(p.GetPlayerData());
                if (form == GhostForm.Sexton || form == GhostForm.Miser)
                {
                    // Sexton digs a grave, Miser spends its whole hoard on one Mimic (both handle the flash themselves)
                    __result = form == GhostForm.Sexton ? GhostV11.DigGrave(p) : GhostV11.SpendHoard(p);
                    return false;
                }
                // a blob that costs more than one body (the King): not enough stored, the bodies blink as usual
                var pd = p.GetPlayerData();
                int bodies = GhostBlobs.BodiesOf(pd);
                if (bodies > 1 && pd.GetFodderAvailable() < bodies)
                {
                    GhostV11.Flash(p);
                    __result = false;
                    return false;
                }
            }
            catch (Exception e) { Plugin.Log.LogError("Ghost Back action failed: " + e); }
            return true;
        }

        /// <summary>The game charged one body for the blob: charge the rest the same way.</summary>
        static void Postfix(Ghost __instance, bool __result)
        {
            if (!__result) return;
            try
            {
                var p = __instance.GetComponent<Player>();
                var pd = p != null ? p.GetPlayerData() : null;
                var form = GhostPack.FormOf(pd);
                if (pd == null || form == GhostForm.Sexton || form == GhostForm.Miser) return;
                int bodies = GhostBlobs.BodiesOf(pd);
                if (bodies > 1) pd.SpendEctoplasm((bodies - 1) * SystemBalance.EctoplasmFodderCost);
            }
            catch (Exception e) { Plugin.Log.LogError("Ghost Back cost failed: " + e); }
        }
    }

    [HarmonyPatch(typeof(SystemLevel), "SpawnFodder")]
    static class Patch_SpawnFodderPair
    {
        static void Postfix(Player fromPlayer, Vector2 position, bool __result)
        {
            if (!__result || fromPlayer == null) return;
            try
            {
                var pd = fromPlayer.GetPlayerData();
                BlobChallenges.BlobSpawned(pd);
                if (GhostPack.Mote == null || !GhostPack.SpawnsMotes(pd)) return;
                foreach (var off in new[] { new Vector2(9f, -3f), new Vector2(-9f, -3f), new Vector2(0f, 8f), new Vector2(0f, -8f) })
                {
                    var at = position + off;
                    if (!SystemLevel.GetInCurrentRoom(at)) continue;
                    var go = GhostPack.Mote.gameObject.Spawn(at, Quaternion.identity);
                    if (go != null) go.GetComponent<Player>().InitAsAI(fromPlayer.gameObject);
                    break;
                }
            }
            catch (Exception e) { Plugin.Log.LogError("Mote pair spawn failed: " + e); }
        }
    }

    /// <summary>Gleaner: each blob is worth 60% (it collects far more of them).</summary>
    [HarmonyPatch(typeof(PlayerGameData), "OnEctoplasmCollected")]
    static class Patch_GleanerValue
    {
        static void Prefix(PlayerGameData __instance, ref float amount)
        {
            try
            {
                var pd = SystemPlayers.GetPlayer(R.Get<int>(__instance, "m_ownerPlayerId"));
                var f = GhostPack.FormOf(pd);
                if (f == GhostForm.Gleaner) amount *= 0.6f;
                else if (f == GhostForm.Hexer) amount *= GhostV11.HexerEctoplasm;
            }
            catch { }
        }
    }
}
