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
    /// The ghost forms Banshee, Sexton, Kindler, Mason, Hexer and Miser, their fodder and effects. The silver / gold
    /// slot mechanics live in GhostSlots.cs (silver Ascension, gold Thralls). Art: tools/sprites/ghost_v11.py, ghost_forms_v11.py, ghost_custom.py
    /// (cells and event frames in art/out_ghosts/TIMING_v11.md). Every fodder is drawn at its final size (no ArtScale),
    /// so kit offsets below are pixels above the feet.
    /// </summary>
    public static class GhostV11
    {
        // ------------------------------------------------------------------ tuning (sidegrades to the Wisp)
        public const float WailCost = 3f;            // half a body (a body costs 6)
        public const float WailRange = 40f;
        public const float IgniteRange = 140f;
        public const float HexerEctoplasm = 0.85f;   // the Hexer's pickups are worth less
        public const int MaxGraves = 3;
        public const float GraveTrigger = 52f, GraveTimeout = 10f;

        /// <summary>True while a Sexton grave hands its ectoplasm back (unlock counters skip it).</summary>
        public static bool Refunding;
        static readonly System.Reflection.MethodInfo s_lifeStat = AccessTools.Method(typeof(PlayerGameData), "IncrementLifeStat");

        /// <summary>Give back one body's ectoplasm by un-spending it (EctoplasmEarned does not move). Falls back to a
        /// collect with Refunding set if the stat call is not there.</summary>
        public static void Refund(PlayerData pd, float amount)
        {
            if (pd == null || amount <= 0f) return;
            Refunding = true;
            try
            {
                if (s_lifeStat != null && pd.GameData != null)
                {
                    var stat = SystemLevel.GetBossEncounterActive() ? PlayerStats.eStat.EctoplasmSpentBoss : PlayerStats.eStat.EctoplasmSpent;
                    s_lifeStat.Invoke(pd.GameData, new object[] { stat, -amount });
                }
                else pd.OnEctoplasmCollected(amount);
            }
            catch (Exception e) { Plugin.Log.LogError("Grave refund failed: " + e); }
            finally { Refunding = false; }
        }

        public static Player Keener, Revenant, Fusebelly, Gargling, Poppet, Mimic;
        public static Status Hexed;
        public static GameObject Shriek, ShriekWall, ShriekHit, Claw, Lick, FuseBlast, FusePop, Stone, StoneWall, StoneHit,
                                 Jab, HexPin, HexPinWall, HexPinHit, Chomp, Coin, CoinWall, CoinHit,
                                 WailRing, WailFizzle, IgniteFizzle, RouseDust, Grave, HoardBurst, HoardAura,
                                 SilverAura, GoldAura;
        public static StatusOverlayDef HoardInd;
        /// <summary>The sizzling fuse on the Fusebelly a Kindler's Attack will light.</summary>
        public static StatusOverlayDef FuseSpark;

        static readonly Dictionary<GhostForm, string> s_fodderSheet = new Dictionary<GhostForm, string>
        {
            { GhostForm.Banshee, "FodKeener" }, { GhostForm.Sexton, "FodRevenant" }, { GhostForm.Kindler, "FodFusebelly" },
            { GhostForm.Mason, "FodGargling" }, { GhostForm.Hexer, "FodPoppet" }, { GhostForm.Miser, "FodMimic" },
        };

        // ------------------------------------------------------------------ statuses
        static Status MakeStatus(string name, string cls, float duration, Color tint, params PlayerModifier[] mods)
        {
            var src = ModStatus.Slow;
            if (src == null) return null;
            var go = MonsterFactory.ClonePrefab(src.gameObject, name);
            var s = go.GetComponent<Status>();
            s.m_class = cls;
            s.m_duration = duration;
            s.m_stacks = true;
            s.m_damage = 0f;
            s.m_preventAttack = false;
            s.m_preventMove = false;
            s.m_modifiers = new List<PlayerModifier>(mods);
            s.m_tintColour = tint;
            s.m_tintFlashTime = 0f;
            s.m_effects = new DamageEffectData[0];
            return s;
        }

        static PlayerModifier Mul(PlayerModifier.eType t, float v)
        {
            return new PlayerModifier { m_modify = t, m_type = ValueModifier.eModifierType.Multiply, m_value = v, m_priority = 500f };
        }

        static void BuildFx()
        {
            // Hexed: the hero takes a quarter more damage (resistance x0.8) for 4 s; a pin-stuck heart over the head
            Hexed = MakeStatus("ModStatusGhostHexed", "ModGhostHexed", 4f, new Color(0.7f, 0.35f, 1f, 0.15f),
                               Mul(PlayerModifier.eType.HeroDamageResistance, 0.8f), Mul(PlayerModifier.eType.MonsterDamageResistance, 0.8f));
            ModStatus.RegisterOverlay("ModStatusGhostHexed", "FxHexMark", "Loop", 1f, OverlayAt.Head);
            HoardInd = ModStatus.Indicator("ModIndGhostHoard", "FxHoardAura", "Play", -2f, OverlayAt.Feet);
            // the spark's centre (7 rows above its cell bottom) on the fuse tip, 13 px above the Fusebelly's feet
            FuseSpark = ModStatus.Indicator("ModIndFuseSpark", "FxFuseSpark", "Loop", 6f, OverlayAt.Feet);

            // fodder attacks (pixels above the feet; the sheets are final size)
            Shriek = FxKit.Projectile("ModGhostShriek", "DFX_skelMageNewProjectile", "FxShriek", "Fly", 130f, 0.45f, 0.35f, 0.2f,
                                      ModStatus.Slow, 0.4f, rotate: true);
            ShriekWall = FxKit.Visual("ModGhostShriekWall", "FxShriek", "Wall");
            ShriekHit = FxKit.Visual("ModGhostShriekHit", "FxShriek", "Hit");
            GhostPack.SplitContacts(Shriek, ShriekWall, ShriekHit);

            Claw = AimedMelee.Rotating(FxKit.BodyHit("ModGhostRevenantClaw", 0.7f, 0f, 0.5f, 0.2f));   // claw, lick, jab and chomp turn with the aim
            Strike.HitBox(Claw, 16f, 14f);
            Lick = AimedMelee.Rotating(FxKit.BodyHit("ModGhostFuseLick", 0.4f, 0f, 0.3f, 0.2f));
            Strike.HitBox(Lick, 12f, 10f);
            FuseBlast = FxKit.TimedHit("ModGhostFuseBlast", "skydropExplode", "FxFuseBlast", "Play", 1, 4, 1.4f, 1.2f, canFlip: false);
            if (FuseBlast != null) { Strike.Ground(FuseBlast, "FxFuseBlast", 36, 46, 44f, 26f); FxFactory.SetContacts(FuseBlast, clearSpawnOnHit: true); }
            FusePop = FxKit.TimedHit("ModGhostFusePop", "skydropExplode", "FxFuseBlast", "Pop", 1, 3, 0.5f, 0.6f, canFlip: false);
            if (FusePop != null) { Strike.Ground(FusePop, "FxFuseBlast", 36, 46, 22f, 14f); FxFactory.SetContacts(FusePop, clearSpawnOnHit: true); }

            Stone = FxKit.Projectile("ModGhostStone", "DFX_skelMageNewProjectile", "FxStoneShard", "Fly", 150f, 0.7f, 0.6f, 0.4f);
            StoneWall = FxKit.Visual("ModGhostStoneWall", "FxStoneShard", "Wall");
            StoneHit = FxKit.Visual("ModGhostStoneHit", "FxStoneShard", "Hit");
            GhostPack.SplitContacts(Stone, StoneWall, StoneHit);

            Jab = AimedMelee.Rotating(FxKit.BodyHit("ModGhostPoppetJab", 0.5f, 0f, 0.3f, 0.2f, Hexed, 0.35f));
            Strike.HitBox(Jab, 12f, 10f);
            HexPin = FxKit.Projectile("ModGhostHexPin", "DFX_skelMageNewProjectile", "FxHexPin", "Fly", 170f, 1.0f, 0.05f, 0.1f, Hexed, 1f);
            HexPinWall = FxKit.Visual("ModGhostHexPinWall", "FxHexPin", "Wall");
            HexPinHit = FxKit.Visual("ModGhostHexPinHit", "FxHexPin", "Hit");
            GhostPack.SplitContacts(HexPin, HexPinWall, HexPinHit);

            Chomp = AimedMelee.Rotating(FxKit.BodyHit("ModGhostMimicChomp", 0.8f, 0f, 0.6f, 0.2f));
            Strike.HitBox(Chomp, 16f, 12f);
            Coin = FxKit.Projectile("ModGhostCoin", "DFX_skelMageNewProjectile", "FxCoinShot", "Fly", 140f, 0.6f, 0.35f, 0.2f);
            CoinWall = FxKit.Visual("ModGhostCoinWall", "FxCoinShot", "Wall");
            CoinHit = FxKit.Visual("ModGhostCoinHit", "FxCoinShot", "Hit");
            GhostPack.SplitContacts(Coin, CoinWall, CoinHit);

            // ghost abilities (visuals; the logic lives in GhostAbilityFx)
            WailRing = Centered("ModGhostWailRing", "FxWailRing", "Play", 40, 22);
            WailFizzle = Centered("ModGhostWailFizzle", "FxShriek", "Hit", 11, 11);
            IgniteFizzle = Centered("ModGhostIgniteFizzle", "FxFuseBlast", "Pop", 36, 46);
            RouseDust = Centered("ModGhostRouseDust", "FxStoneShard", "Hit", 11, 8);
            HoardBurst = Centered("ModGhostHoardBurst", "FxHoardBurst", "Play", 38, 36);
            HoardAura = GhostPack.Aura("ModGhostHoardAura", "FxHoardAura");
            SilverAura = GhostPack.Aura("ModGhostSilverAura", "FxSilverAura");
            GoldAura = GhostPack.Aura("ModGhostGoldAura", "FxGoldAura");
            GhostSlots.BuildFx();
            Grave = FxKit.Visual("ModGhostGrave", "FxGrave", "Rise");
            if (Grave != null)
            {
                FxFactory.SetEffect(Grave, destroyOnAnimEnd: false, canFlip: false, freeRotate: false);
                Strike.ArtAt(Grave, "FxGrave", 11, 18);
                FxKit.NoTint(Grave);
            }
        }

        internal static GameObject CenteredFx(string name, string art, string anim, int gx, int gy) { return Centered(name, art, anim, gx, gy); }

        static GameObject Centered(string name, string art, string anim, int gx, int gy)
        {
            var go = FxKit.Visual(name, art, anim);
            if (go == null) return null;
            FxFactory.SetEffect(go, destroyOnAnimEnd: true, canFlip: false, freeRotate: false);
            Strike.ArtAt(go, art, gx, gy);
            FxKit.NoTint(go);
            return go;
        }

        static GameObject SpawnRing(string sheet)
        {
            var go = FxFactory.Clone("FX_SlimeSpawnShockwave", "Mod" + sheet);
            if (go == null) return null;
            FxFactory.StripChildren(go, "ShockwaveBack");
            GhostPack.RingPair(go, 20, 15, sheet);
            return go;
        }

        // ------------------------------------------------------------------ fodder kits
        static void KeenerKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0];
            int n0 = Strike.Mark(p);
            int shriek = Kit.AddEffect(p, Shriek, offsetX: 5f, offsetY: 8f);   // the mouth
            atk.Clear();
            // the shriek travels ~58 px before it fades
            atk.Add(Kit.Attack(a0, Kit.Shot(sh, "Shriek", "ModFodKeenerShriek", 3, Kit.Voice(p), 0f, shriek).Build(), 1.3f,
                               rangeInner: 20f, rangeOuter: 52f, rangeRetreat: 16f));
            Strike.Feet(p, n0, 8f);
        }

        static void RevenantKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0];
            int n0 = Strike.Mark(p);
            int claw = Kit.AddEffect(p, Claw, attach: true, destroyOnAnimEnd: true, offsetX: 8f, offsetY: 6f);
            atk.Clear();
            atk.Add(Kit.Attack(a0, Kit.Melee(sh, "Claw", "ModFodRevenantClaw", Kit.Voice(p), 3, claw, 70f).Build(), 1.2f,
                               rangeInner: 8f, rangeOuter: 22f));
            Strike.Feet(p, n0, 7f);
        }

        static void FusebellyKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int lick = Kit.AddEffect(p, Lick, attach: true, destroyOnAnimEnd: true, offsetX: 8f, offsetY: 9f);
            int blast = Kit.AddEffect(p, FuseBlast, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            atk.Clear();
            atk.Add(Kit.Attack(a0, Kit.Melee(sh, "Lick", "ModFodFusebellyLick", v, 2, lick, 40f).Build(), 1.1f, rangeInner: 6f, rangeOuter: 18f));
            // Blow: swells for 0.62 s, BURSTS on frame 5 (the blast, then it is gone)
            var blow = new ClipBuilder(sh, "Blow", "ModFodFusebellyBlow").Once()
                .Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop").EvO(4, "AnimSound", v)
                .Ev(5, "AnimAttack", blast).Ev(5, "AnimModBlowUp").Ev(-1, "AnimRun").Build();
            Kit.EnableSpecial(p, Kit.Attack(a0, blow, 0f, rangeInner: 0f, rangeOuter: 22f), 5f);
            Strike.Feet(p, n0, 8f);
        }

        static void GarglingKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int spit = Kit.AddEffect(p, Stone, offsetX: 7f, offsetY: 11f);   // the maw
            var fan = new int[3];
            for (int i = 0; i < 3; i++) fan[i] = Kit.AddEffect(p, Stone, offsetX: 7f, offsetY: 11f, angle: (i - 1) * 18f);
            atk.Clear();
            atk.Add(Kit.Attack(a0, Kit.Shot(sh, "Spit", "ModFodGarglingSpit", 3, v, 0f, spit).Build(), 1.6f,
                               rangeInner: 30f, rangeOuter: 95f, rangeRetreat: 20f));
            Kit.EnableSpecial(p, Kit.Attack(a0, Kit.Shot(sh, "Fan", "ModFodGarglingFan", 4, v, 0f, fan).Build(), 0f,
                                            rangeInner: 20f, rangeOuter: 90f), 5f);
            Strike.Feet(p, n0, 9f);
        }

        static void PoppetKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0];
            int n0 = Strike.Mark(p);
            int jab = Kit.AddEffect(p, Jab, attach: true, destroyOnAnimEnd: true, offsetX: 8f, offsetY: 5f);
            atk.Clear();
            atk.Add(Kit.Attack(a0, Kit.Melee(sh, "Jab", "ModFodPoppetJab", Kit.Voice(p), 3, jab, 60f).Build(), 1.0f,
                               rangeInner: 6f, rangeOuter: 18f));
            Strike.Feet(p, n0, 7f);
        }

        static void MimicKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int chomp = Kit.AddEffect(p, Chomp, attach: true, destroyOnAnimEnd: true, offsetX: 9f, offsetY: 5f);
            var coins = new int[3];
            for (int i = 0; i < 3; i++) coins[i] = Kit.AddEffect(p, Coin, offsetX: 5f, offsetY: 8f, angle: (i - 1) * 14f);
            atk.Clear();
            atk.Add(Kit.Attack(a0, Kit.Melee(sh, "Chomp", "ModFodMimicChomp", v, 3, chomp, 70f).Build(), 1.3f, rangeInner: 8f, rangeOuter: 22f));
            Kit.EnableSpecial(p, Kit.Attack(a0, Kit.Shot(sh, "Spit", "ModFodMimicSpit", 3, v, 0.06f, coins).Build(), 0f,
                                            rangeInner: 20f, rangeOuter: 80f), 5f);
            Strike.Feet(p, n0, 6f);
        }

        static readonly MonsterDef[] Defs =
        {
            new MonsterDef { id = "FodKeener", basePrefab = "EnemySlime1BlueMedium", health = 0.7f, speedMult = 1.2f, kit = KeenerKit, keepEvolutions = true },
            new MonsterDef { id = "FodRevenant", basePrefab = "EnemySlime1BlueMedium", health = 1.4f, speedMult = 1.05f, kit = RevenantKit, keepEvolutions = true },
            new MonsterDef { id = "FodFusebelly", basePrefab = "EnemySlime1BlueMedium", health = 0.8f, speedMult = 1.1f, kit = FusebellyKit, keepEvolutions = true,
                             customize = (go, p) => { if (go.GetComponent<KindlerFuse>() == null) go.AddComponent<KindlerFuse>(); } },
            new MonsterDef { id = "FodGargling", basePrefab = "EnemySlime1BlueMedium", health = 2.6f, speedMult = 0.3f, kit = GarglingKit, keepEvolutions = true },
            new MonsterDef { id = "FodPoppet", basePrefab = "EnemySlime1BlueMedium", health = 1.0f, speedMult = 1.1f, kit = PoppetKit, keepEvolutions = true },
            new MonsterDef { id = "FodMimic", basePrefab = "EnemySlime1BlueMedium", health = 1.6f, speedMult = 0.95f, kit = MimicKit, keepEvolutions = true },
        };

        static readonly string[] s_rings = { "FxKeenerRise", "FxGraveRaise", "FxWaxRing", "FxRubbleRing", "FxStuffingRing", "FxCoinRing" };

        public static void Register()
        {
            BuildFx();
            var built = new Dictionary<string, Player>();
            for (int i = 0; i < Defs.Length; i++)
            {
                var p = MonsterFactory.Build(Defs[i]);
                if (p == null) continue;
                built[Defs[i].id] = p;
                // the Spawn clip's AnimAttack 3 = the vanilla slime's splash: each fodder forms in its own ring
                var ring = SpawnRing(s_rings[i]);
                if (ring != null)
                    foreach (var e in Kit.Effects(p))
                        if (e != null && e.m_object != null && e.m_object.name == "FX_SlimeSpawnShockwave") e.m_object = ring;
            }
            built.TryGetValue("FodKeener", out Keener);
            built.TryGetValue("FodRevenant", out Revenant);
            built.TryGetValue("FodFusebelly", out Fusebelly);
            built.TryGetValue("FodGargling", out Gargling);
            built.TryGetValue("FodPoppet", out Poppet);
            built.TryGetValue("FodMimic", out Mimic);
            // a Fusebelly always pops when it dies
            if (Fusebelly != null && FusePop != null) { Kit.AddDeathSpawn(Fusebelly, FusePop); Strike.DeathAtFeet(Fusebelly); }
            Strike.KeepAllScales();
            RegisterVault();
            Plugin.Log.LogInfo("Ghost forms Banshee to Miser ready: " + built.Count + " fodder monsters");
        }

        static void RegisterVault()
        {
            foreach (var d in GhostPack.Forms)
                VaultRegistry.Add("Ghosts", "Ghost" + d.form, CapFirst(d.name), d.summary, d.portraitArt);
            VaultRegistry.Add("Monsters", "ModFodKeener", "Keener", "A Banshee's wailing head. Its shriek slows", "FodKeener");
            VaultRegistry.Add("Monsters", "ModFodRevenant", "Revenant", "A Sexton's ghoul. It claws out of a fresh grave", "FodRevenant");
            VaultRegistry.Add("Monsters", "ModFodFusebelly", "Fusebelly", "A Kindler's tallow bomb. It licks with its fuse and blows up", "FodFusebelly");
            VaultRegistry.Add("Monsters", "ModFodGargling", "Gargling", "A Mason's stone sentry. It barely moves and spits stones", "FodGargling");
            VaultRegistry.Add("Monsters", "ModFodPoppet", "Poppet", "A Hexer's voodoo doll. Its pin can hex the hero", "FodPoppet");
            VaultRegistry.Add("Monsters", "ModFodMimic", "Mimic", "A Miser's hoard with teeth. Stronger for every body spent", "FodMimic");
        }

        static string CapFirst(string s)
        {
            if (string.IsNullOrEmpty(s)) return s;
            var low = s.ToLowerInvariant();
            var c = low.ToCharArray();
            for (int i = 0; i < c.Length; i++) if (i == 0 || c[i - 1] == ' ') c[i] = char.ToUpperInvariant(c[i]);
            return new string(c);
        }

        public static GameObject FodderFor(GhostForm f)
        {
            switch (f)
            {
                case GhostForm.Banshee: return Keener != null ? Keener.gameObject : null;
                case GhostForm.Sexton: return Revenant != null ? Revenant.gameObject : null;
                case GhostForm.Kindler: return Fusebelly != null ? Fusebelly.gameObject : null;
                case GhostForm.Mason: return Gargling != null ? Gargling.gameObject : null;
                case GhostForm.Hexer: return Poppet != null ? Poppet.gameObject : null;
                case GhostForm.Miser: return Mimic != null ? Mimic.gameObject : null;
            }
            return null;
        }

        public static GameObject AuraFor(GhostForm f)
        {
            switch (f)
            {
                case GhostForm.Silver: return SilverAura;
                case GhostForm.Gold: return GoldAura;
            }
            return null;
        }

        // ------------------------------------------------------------------ ghost attacks
        static AttackData GhostAttack(exSpriteAnimClip clip, float cooldown)
        {
            var template = MonsterFactory.FindVanilla("EnemySkeletonMage");
            var a = Kit.Attack(Kit.Attacks(template)[0], clip, cooldown, rangeInner: 0f, rangeOuter: 60f);
            a.m_sound = null;
            return a;
        }

        /// <summary>Attack plays the form's anim; on <paramref name="frame"/> GhostAbilityFx does the form's ability.</summary>
        public static void ArmAbility(Player p, SpriteSheet fsh, exAtlas atlas, string pre, string anim, int frame, float cooldown)
        {
            if (!fsh.Has(anim)) return;
            Kit.Effects(p).Clear();
            var clip = GhostPack.Retarget(new ClipBuilder(fsh, anim, pre + anim).Once()
                .Ev(frame, "AnimModGhostAbility").Ev(-1, "AnimRun").Build(), atlas);
            var atk = Kit.Attacks(p);
            atk.Clear();
            atk.Add(GhostAttack(clip, cooldown));
        }

        /// <summary>Hexer: Attack = Throw; the hex pin leaves the hand on frame 3 (the Poltergeist's hand position).</summary>
        public static void ArmHexer(Player p, SpriteSheet fsh, exAtlas atlas, string pre)
        {
            if (!fsh.Has("Throw")) return;
            var effects = Kit.Effects(p);
            effects.Clear();
            int pin = Kit.AddEffect(p, HexPin, offsetX: 12f, offsetY: -1f);
            var clip = GhostPack.Retarget(new ClipBuilder(fsh, "Throw", pre + "Throw").Once()
                .Ev(3, "AnimAttack", pin).Ev(-1, "AnimRun").Build(), atlas);
            var atk = Kit.Attacks(p);
            atk.Clear();
            atk.Add(GhostAttack(clip, 6f));
        }

        // ------------------------------------------------------------------ Back: Sexton graves, Miser hoard
        static readonly System.Reflection.MethodInfo s_spawnSpace = AccessTools.Method(typeof(SystemLevel), "CheckForSpawnSpace");
        static readonly System.Reflection.MethodInfo s_flash = AccessTools.Method(typeof(Ghost), "CoroutineFlashFodderOpacity");

        /// <summary>Can a fodder be placed here (the checks SystemLevel.SpawnFodder makes)?</summary>
        public static bool CanPlace(Vector2 pos)
        {
            var room = SystemLevel.GetCurrentRoom();
            if (room == null || !room.IsFullyInRoom() || !room.IsPointInRoom(pos) || room.m_isPowerupRoom) return false;
            try { return s_spawnSpace == null || (bool)s_spawnSpace.Invoke(Singleton<SystemLevel>.Get, new object[] { pos }); }
            catch { return true; }
        }

        /// <summary>SystemLevel.SpawnFodder with a chosen prefab; returns the new fodder (null if it could not be placed).</summary>
        public static GameObject SpawnOwnFodder(Player from, Vector2 pos, GameObject prefab)
        {
            if (from == null || prefab == null || !CanPlace(pos)) return null;
            var go = prefab.Spawn(pos, Quaternion.identity);
            if (go == null) return null;
            go.GetComponent<Player>().InitAsAI(from.gameObject);
            var room = SystemLevel.GetCurrentRoom();
            if (room != null) room.CloseDoors();
            return go;
        }

        /// <summary>Blink the ghost's stored-body markers: the game's own "that did nothing" cue.</summary>
        internal static void Flash(Player ghost)
        {
            try
            {
                var g = ghost.GetComponent<Ghost>();
                if (g != null && s_flash != null)
                    g.StartCoroutine((System.Collections.IEnumerator)s_flash.Invoke(g, new object[] { Singleton<Constants>.Get.m_fodderFlashTime }));
            }
            catch { }
        }

        /// <summary>Sexton: Back plants a grave (one body's ectoplasm, or what the picked blob costs) where the ghost is;
        /// a Revenant (or the picked blob) claws out of it when the hero comes close, or after 10 s. Up to 3 graves at once.</summary>
        public static bool DigGrave(Player ghost)
        {
            var pd = ghost.GetPlayerData();
            if (pd == null || Grave == null) return false;
            Vector2 pos = ghost.transform.position;
            int bodies = GhostBlobs.BodiesOf(pd);
            if (!pd.CanSpawnFodder() || pd.GetFodderAvailable() < bodies || SextonGrave.CountFor(pd) >= MaxGraves || !CanPlace(pos)) { Flash(ghost); return false; }
            pd.OnFodderSpawned();
            if (bodies > 1) pd.SpendEctoplasm((bodies - 1) * SystemBalance.EctoplasmFodderCost);
            var go = SystemPool.Spawn(Grave, pos);
            if (go == null) return false;
            var g = go.GetComponent<SextonGrave>() ?? go.AddComponent<SextonGrave>();
            g.Begin(pd, pos, bodies);
            var room = SystemLevel.GetCurrentRoom();
            if (room != null) room.CloseDoors();
            return true;
        }

        /// <summary>Miser: Back spends EVERY stored body on one Mimic (or one of the picked blob), with that many times
        /// the health.</summary>
        public static bool SpendHoard(Player ghost)
        {
            var pd = ghost.GetPlayerData();
            if (pd == null || Mimic == null) return false;
            int n = pd.GetFodderAvailable();
            if (n < 1 || n < GhostBlobs.BodiesOf(pd)) { Flash(ghost); return false; }
            Vector2 pos = ghost.transform.position;
            var go = SpawnOwnFodder(ghost, pos, GhostBlobs.PrefabOf(pd, Mimic.gameObject));
            if (go == null) { Flash(ghost); return false; }
            pd.SpendEctoplasm(n * SystemBalance.EctoplasmFodderCost);
            var h = go.GetComponent<MimicHoard>() ?? go.AddComponent<MimicHoard>();
            h.bodies = n;
            if (HoardBurst != null) SystemPool.Spawn(HoardBurst, pos);
            return true;
        }

        public static bool Owns(Player p, PlayerData pd, string prefab)
        {
            if (p == null || pd == null || !p.GetIsAI()) return false;
            var h = p.GetComponent<Health>();
            if (h == null || !h.IsAlive()) return false;
            if (ModUtil.PrefabName(p.gameObject) != prefab) return false;
            return R.Get<PlayerData>(p, "m_spawner") == pd;
        }

        // ------------------------------------------------------------------ self test
        public static void SelfCheck(Action<string> bad)
        {
            foreach (var kv in new Dictionary<string, Player> { { "Keener", Keener }, { "Revenant", Revenant }, { "Fusebelly", Fusebelly },
                                                                { "Gargling", Gargling }, { "Poppet", Poppet }, { "Mimic", Mimic } })
                if (kv.Value == null) bad("ghost fodder " + kv.Key + " failed to build");
            if (Hexed == null) bad("ghost status Hexed failed to build");
            if (FuseSpark == null) bad("the Kindler's fuse spark failed to build");
            foreach (var go in new[] { Shriek, Claw, Lick, FuseBlast, FusePop, Stone, Jab, HexPin, Chomp, Coin, WailRing, Grave,
                                       HoardBurst, HoardAura, SilverAura, GoldAura })
                if (go == null) bad("a ghost form effect failed to build");
            var f = GhostPack.Forms;
            if (f.Count < 2 || f[f.Count - 2].tier != SlotTier.Silver || f[f.Count - 1].tier != SlotTier.Gold)
                bad("ghost forms: silver and gold must be the last two entries");
            if (GhostPack.RegularCount != 10) bad("ghost forms: expected 10 regular forms, found " + GhostPack.RegularCount);
            foreach (var d in f)
            {
                if (d.tier != SlotTier.Normal || d.form == GhostForm.Wisp) continue;
                var sh = SpriteSheets.Get(d.bodyArt);
                if (sh == null || !sh.Has("Spawn") || !sh.Has("Idle") || !sh.Has("Run")) bad("ghost form " + d.name + " body art missing");
            }
            // every form but the Wisp shows its own tip when its ghost appears (ContentSetup: MonsterTips.GhostKey)
            MonsterTip tip;
            foreach (var d in f)
                if (d.form != GhostForm.Wisp && !TipRegistry.TryGet("ModGhost" + d.id, out tip)) bad("ghost form " + d.name + " has no tip (ModGhost" + d.id + ")");
        }
    }

    // ====================================================================== the ghost's abilities
    /// <summary>
    /// Per-ghost behaviour of the Banshee to Miser forms: the attack abilities (Banshee wail, Kindler ignite, Mason rouse, fired by
    /// the form's attack clip) and the Miser's hoard aura. Silver / gold: GhostSlots.cs.
    /// </summary>
    public class GhostAbilityFx : MonoBehaviour
    {
        public GhostForm form;
        Player m_player;
        GameObject m_hoardAura;
        float m_cooldown;


        void Awake() { m_player = GetComponent<Player>(); }

        public void Setup(GhostForm f)
        {
            form = f;
            m_cooldown = 0.5f;
            ShowHoard(false);
            UpdateSpark(false);
        }

        void OnDisable() { ShowHoard(false); UpdateSpark(false); }

        PlayerData Pd { get { return m_player != null ? m_player.GetPlayerData() : null; } }

        // ---------------------------------------------------------------- clip event (Wail / Ignite / Rouse frame)
        void AnimModGhostAbility()
        {
            try
            {
                switch (form)
                {
                    case GhostForm.Banshee: Wail(); break;
                    case GhostForm.Kindler: Ignite(); break;
                    case GhostForm.Mason: Rouse(); break;
                }
            }
            catch (Exception e) { Plugin.Log.LogError("Ghost ability " + form + " failed: " + e); }
        }

        Vector2 Pos { get { return transform.position; } }

        void Wail()
        {
            var pd = Pd;
            if (pd == null) return;
            if (pd.Ectoplasm < GhostV11.WailCost || !pd.SpendEctoplasm(GhostV11.WailCost))
            {
                if (GhostV11.WailFizzle != null) SystemPool.Spawn(GhostV11.WailFizzle, Pos + new Vector2(8f, 14f));
                return;
            }
            if (GhostV11.WailRing != null) SystemPool.Spawn(GhostV11.WailRing, Pos + new Vector2(0f, 12f));
            var hero = ModUtil.Hero();
            if (hero == null) return;
            if (((Vector2)hero.transform.position - (Pos + new Vector2(0f, 6f))).magnitude > GhostV11.WailRange) return;
            var hp = hero.GetComponent<Player>();
            var sm = hp != null ? hp.GetStatusManager() : null;
            if (sm != null && ModStatus.Slow != null) sm.AddStatus(ModStatus.Slow, new DamageSource(gameObject, gameObject, pd), "ModGhostWail");
        }

        void Ignite()
        {
            var pd = Pd;
            var best = KindlerFuse.Nearest(pd, Pos, GhostV11.IgniteRange);
            if (best == null)
            {
                if (GhostV11.IgniteFizzle != null) SystemPool.Spawn(GhostV11.IgniteFizzle, Pos + new Vector2(10f, 12f));
                return;
            }
            best.Detonate(pd);
        }

        // ---------------------------------------------------------------- Kindler: which Fusebelly Attack will light
        KindlerFuse m_lit;

        /// <summary>Spark the fuse of the Fusebelly that Attack would light now. None while the ghost is over a body it
        /// can take: there, Attack takes the body instead.</summary>
        void UpdateSpark(bool ghost)
        {
            var want = ghost && !OverBody() ? KindlerFuse.Nearest(Pd, Pos, GhostV11.IgniteRange) : null;
            if (want == m_lit) return;
            if (m_lit != null) ModInd.Set(m_lit.gameObject, GhostV11.FuseSpark, false);
            m_lit = want;
            if (m_lit != null) ModInd.Set(m_lit.gameObject, GhostV11.FuseSpark, true);
        }

        bool OverBody()
        {
            var pd = Pd;
            var props = pd != null ? R.Get<List<Prop>>(m_player, "m_props") : null;
            if (props == null) return false;
            foreach (var pr in props)
                if (pr != null && pr is PropFodder && pr.GetCanAction(pd, false)) return true;
            return false;
        }

        void Rouse()
        {
            var pd = Pd;
            var hero = ModUtil.Hero();
            int n = 0;
            foreach (var mm in UnityEngine.Object.FindObjectsOfType<ModMonster>())
            {
                var p = mm.GetComponent<Player>();
                if (!GhostV11.Owns(p, pd, "ModFodGargling") || !SystemLevel.GetInCurrentRoom(p.transform.position)) continue;
                Vector2 maw = (Vector2)p.transform.position + new Vector2(0f, 11f);
                if (GhostV11.RouseDust != null) SystemPool.Spawn(GhostV11.RouseDust, maw);
                if (hero == null || GhostV11.Stone == null) continue;
                Vector2 d = (Vector2)hero.transform.position + new Vector2(0f, 6f) - maw;
                float ang = Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg;
                FxFactory.SpawnOwned(GhostV11.Stone, maw, new DamageSource(null, p.gameObject, pd), ang);
                n++;
            }
            if (n == 0 && GhostV11.RouseDust != null) SystemPool.Spawn(GhostV11.RouseDust, Pos + new Vector2(10f, 12f));
        }

        // ---------------------------------------------------------------- per frame
        void Update()
        {
            if (m_player == null) return;
            bool ghost = ModUtil.IsGhost(m_player);
            if (form == GhostForm.Kindler || m_lit != null) UpdateSpark(ghost && form == GhostForm.Kindler);
            if (!ghost) return;
            m_cooldown -= Time.deltaTime;
            try
            {
                switch (form)
                {
                    case GhostForm.Miser: ShowHoard(Pd != null && Pd.GetFodderAvailable() >= 2); break;
                }
            }
            catch (Exception e) { Plugin.Log.LogError("Ghost " + form + " update failed: " + e); form = GhostForm.Wisp; }
        }

        void ShowHoard(bool on)
        {
            if (on && m_hoardAura == null && GhostV11.HoardAura != null)
            {
                m_hoardAura = SystemPool.Spawn(GhostV11.HoardAura, transform.position);
                if (m_hoardAura != null) { m_hoardAura.transform.parent = transform; m_hoardAura.transform.localPosition = new Vector3(0f, 0f, 0.5f); }
            }
            else if (!on && m_hoardAura != null) { SystemPool.Despawn(m_hoardAura); m_hoardAura = null; }
        }

    }

    /// <summary>Kindler's Fusebelly: its Blow special (and the Kindler's Ignite) blows it up.</summary>
    public class KindlerFuse : MonoBehaviour
    {
        static readonly List<KindlerFuse> s_live = new List<KindlerFuse>();

        void OnEnable() { if (!s_live.Contains(this)) s_live.Add(this); }

        void OnDisable() { s_live.Remove(this); }

        /// <summary>The player's own free (unpossessed, living) Fusebelly nearest to <paramref name="from"/> within
        /// <paramref name="range"/> px, or null.</summary>
        public static KindlerFuse Nearest(PlayerData owner, Vector2 from, float range)
        {
            KindlerFuse best = null;
            float bd = range * range;
            foreach (var k in s_live)
            {
                var p = k != null ? k.GetComponent<Player>() : null;
                if (!GhostV11.Owns(p, owner, "ModFodFusebelly")) continue;
                float d = ((Vector2)p.transform.position - from).sqrMagnitude;
                if (d < bd) { bd = d; best = k; }
            }
            return best;
        }

        /// <summary>Clip event on Blow frame 5, right after the blast spawned.</summary>
        void AnimModBlowUp() { Die(); }

        /// <summary>The Kindler lit this one from afar: the full blast, owned by the Kindler's player.</summary>
        public void Detonate(PlayerData owner)
        {
            if (GhostV11.FuseBlast != null)
                FxFactory.SpawnOwned(GhostV11.FuseBlast, transform.position, new DamageSource(null, gameObject, owner));
            Die();
        }

        void Die()
        {
            var h = GetComponent<Health>();
            if (h == null || !h.IsAlive()) return;
            // no killer: nobody gets credit for a bomb going off
            h.InstaKill(new DamageInfo(1f, 0f, 0f, Vector2.zero, new DamageSource(gameObject, null, null)));
        }
    }

    /// <summary>Miser's Mimic: health times the bodies spent on it; a ring of coins at its feet while it holds 2+.</summary>
    public class MimicHoard : MonoBehaviour
    {
        public int bodies;
        int m_applied;

        void Update()
        {
            if (bodies <= 1 || m_applied == bodies) return;
            var h = GetComponent<Health>();
            if (h == null || !h.IsAlive()) return;
            float mx = R.Get<float>(h, "m_healthMaxFinal");
            if (mx <= 0f) return;
            R.Set(h, "m_healthMaxFinal", mx * bodies);
            R.Set(h, "m_healthCurrent", mx * bodies);
            m_applied = bodies;
            ModInd.Set(gameObject, GhostV11.HoardInd, true);
        }

        void OnDisable()
        {
            if (m_applied > 0) ModInd.Set(gameObject, GhostV11.HoardInd, false);
            bodies = 0; m_applied = 0;
        }
    }

    /// <summary>A Sexton's grave: rises out of the floor, waits (glowing while its Sexton hovers near), and lets a Revenant
    /// (or the Sexton's picked blob) claw out when the hero comes close or after GraveTimeout.</summary>
    public class SextonGrave : MonoBehaviour
    {
        static readonly List<SextonGrave> s_live = new List<SextonGrave>();
        static exSpriteAnimClip s_idle, s_glow, s_sink;
        PlayerData m_owner;
        Vector2 m_pos;
        float m_t;
        int m_state;      // 0 rising, 1 waiting, 2 sinking
        int m_bodies = 1; // what it cost: given back if it never rises
        bool m_glow;
        exSpriteAnimation m_anim;

        public static int CountFor(PlayerData pd)
        {
            int n = 0;
            foreach (var g in s_live) if (g != null && g.m_owner == pd && g.m_state < 2) n++;
            return n;
        }

        public void Begin(PlayerData owner, Vector2 pos, int bodies = 1)
        {
            m_owner = owner; m_pos = pos; m_t = 0f; m_state = 0; m_glow = false; m_bodies = Mathf.Max(1, bodies);
            m_anim = GetComponent<exSpriteAnimation>();
            if (s_idle == null)
            {
                var sh = SpriteSheets.Get("FxGrave");
                if (sh != null)
                {
                    s_idle = new ClipBuilder(sh, "Idle", "ModGhostGraveIdle").Loop().Build();
                    s_glow = new ClipBuilder(sh, "Glow", "ModGhostGraveGlow").Loop().Build();
                    s_sink = new ClipBuilder(sh, "Sink", "ModGhostGraveSink").Once().Build();
                }
            }
            if (!s_live.Contains(this)) s_live.Add(this);
        }

        void OnDisable() { s_live.Remove(this); m_owner = null; }

        void Play(exSpriteAnimClip c) { if (m_anim != null && c != null) m_anim.Play(c); }

        void Update()
        {
            if (m_owner == null) return;
            m_t += Time.deltaTime;
            if (m_state == 0 && m_t > 0.4f) { m_state = 1; Play(s_idle); }
            if (m_state == 2)
            {
                if (m_t > 0.45f) { m_owner = null; gameObject.Despawn(); }
                return;
            }
            if (!SystemLevel.GetInCurrentRoom(m_pos))
            {
                // the room was left before it rose: the ectoplasm comes back
                GhostV11.Refund(m_owner, m_bodies * SystemBalance.EctoplasmFodderCost);
                Sink();
                return;
            }
            var body = m_owner.GameObject;
            var bp = body != null ? body.GetComponent<Player>() : null;
            bool near = bp != null && ModUtil.IsGhost(bp) && ((Vector2)body.transform.position - m_pos).magnitude < 40f;
            if (m_state == 1 && near != m_glow) { m_glow = near; Play(near ? s_glow : s_idle); }
            var hero = ModUtil.Hero();
            bool trigger = m_t > GhostV11.GraveTimeout ||
                           (hero != null && m_state == 1 && ((Vector2)hero.transform.position - m_pos).magnitude < GhostV11.GraveTrigger);
            if (!trigger) return;
            var from = bp;   // the Revenant is the Sexton player's (whatever body they wear now)
            var rises = GhostBlobs.PrefabOf(m_owner, GhostV11.Revenant != null ? GhostV11.Revenant.gameObject : null);
            if (from == null || GhostV11.SpawnOwnFodder(from, m_pos, rises) == null)
                GhostV11.Refund(m_owner, m_bodies * SystemBalance.EctoplasmFodderCost);
            Sink();
        }

        void Sink() { m_state = 2; m_t = 0f; Play(s_sink); }
    }

    // ====================================================================== patches
    /// <summary>
    /// The game reads the MIDDLE mouse button as Start (pause) for the mouse player. While a Binder ghost is out on mouse
    /// or keyboard, a middle click fuses blobs instead (GhostFormFx), so that click must not also pause the game.
    /// </summary>
    [HarmonyPatch]
    static class Patch_MiddleClickPause
    {
        static System.Reflection.MethodBase TargetMethod()
        {
            return AccessTools.Method(typeof(SystemInput), "GetShouldPause", new Type[] { typeof(int) });
        }

        /// <summary>Only the mouse player's own pause, only on a middle click, only while it is their ghost button
        /// (a Binder ghost, or a silver / gold monster).</summary>
        static void Postfix(int playerId, ref bool __result)
        {
            if (!__result || !Input.GetMouseButtonDown(2)) return;
            try
            {
                var pd = SystemPlayers.GetPlayer(playerId);
                if (MouseBinder(pd) && !Input.GetKeyDown(KeyCode.Escape)) __result = false;
            }
            catch { }
        }

        public static bool MouseBinder(PlayerData pd) { return GhostPack.MiddleClickInUse(pd); }
    }

    /// <summary>
    /// SystemLevel also asks the no-player GetShouldPause() (any controller's Start) after the per-player checks: the same
    /// middle click of a mouse Binder ghost must not pause through it. Any other Start / Escape this frame still pauses.
    /// </summary>
    [HarmonyPatch(typeof(SystemInput), "GetShouldPause", new Type[0])]
    static class Patch_MiddleClickPauseAny
    {
        static void Postfix(ref bool __result)
        {
            if (!__result || !Input.GetMouseButtonDown(2) || Input.GetKeyDown(KeyCode.Escape) || Input.GetKeyDown(KeyCode.Return)) return;
            try
            {
                if (!Patch_MiddleClickPause.MouseBinder(SystemPlayers.GetPlayerWithController(eController.Mouse))) return;
                // a pad's Start pressed this same frame still pauses
                if (InControl.InputManager.CommandWasPressed) return;
                __result = false;
            }
            catch { }
        }
    }
}
