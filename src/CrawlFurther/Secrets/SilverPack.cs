using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Secrets
{
    using CrawlFurther.Art;
    using CrawlFurther.Gods;
    using CrawlFurther.Monsters;
    using CrawlFurther.UI;
    using CrawlFurther.Util;
    using CrawlFurther.Content.Gods.Vhorrul;
    using CrawlFurther.Content.Tips;

    /// <summary>
    /// SILVER UNIQUES: three tier-3 monsters of their own "silver spirit" class, in no god's tree, reached ONLY through
    /// the silver ghost's tier-3 orb upgrade (GhostSlots calls <see cref="SilverUniques.RollTier3"/>). Art and timing:
    /// tools/sprites/silver_rigs.py -> art/out_silver (TIMING.md). Tips and vault lines: data/tips/tips_silver.json.
    ///   Moonwarden  (common, 20%)    moon phases over its head; Moonfall drops the moon (bigger when fuller); at Full its
    ///                                 sweeps also throw a crescent wave.
    ///   Comet Stag  (common, 20%)    Comet: a streak of starlight that rebounds off walls (3 bounces); running straight
    ///                                 for 1 s charges its antlers: the next gore bursts (knocks far, dazes).
    ///   Astrarch    (legendary, 4%)  Starshots leave stars on the floor; Constellation joins up to 5 into a shape and
    ///                                 starfall hits the hero if he is inside it; with 3+ stars out she takes 0.7x damage.
    /// </summary>
    public static class SilverFx
    {
        public static GameObject HitSplat, DeathFx;
        // Moonwarden
        public static GameObject GlaiveHit, GlaiveFx, CrescentWave, MoonfallS, MoonfallM, MoonfallL;
        // Comet Stag
        public static GameObject GoreHit, AntlerFx, ChargeBurst, CometHit, CometTrail, Bounce;
        // Astrarch
        public static GameObject Starshot, Star, StarBurst, Link, Starfall, StarHit, Arrival;
        // indicators
        public static StatusOverlayDef[] Phase;          // New, Crescent, Half, Gibbous, Full (head)
        public static StatusOverlayDef AntlerGlow, Veil;

        public const string Prefix = "ModSilver";

        public static void Build()
        {
            var daze = FxFactory.GetStatus("StatusDizzy");
            HitSplat = GodArt.HitSplat("ModSilHitSplat", "FxSilSplat", 13, 7);
            DeathFx = FxKit.Visual("ModSilDeathFx", "FxSilDeath", "Play");
            Strike.ArtAt(DeathFx, "FxSilDeath", 16, 28);

            // ---- Moonwarden: the glaive sweep (art arc centred on the hand, hitbox over the blade's path)
            GlaiveHit = AimedMelee.Rotating(FxKit.BodyHit("ModSilGlaiveHit", 1.4f, 0f, 1.0f, 0.14f));   // v0.10 sweep: sweep, gore and comet turn with the aim
            Strike.HitBox(GlaiveHit, 24f, 20f);                  // at (16, 11): x 4..28, y 1..21 (glaive tip (26, 11) on the hit frame)
            GlaiveFx = AimedMelee.Rotating(FxKit.Visual("ModSilGlaiveFx", "FxSilGlaive", "Sweep"));
            Strike.ArtAt(GlaiveFx, "FxSilGlaive", 13, 13);
            CrescentWave = FxKit.Projectile("ModSilCrescentWave", "DFX_skelMageNewProjectile", "FxSilCrescent", "Fly", 170f, 0.6f, 0.8f, 0.6f);
            Strike.ArtAt(CrescentWave, "FxSilCrescent", 11, 6);
            Strike.Collider(CrescentWave, 10f, 12f);
            var dur = new[] { 0.16f, 0.14f, 0.1f, 0.08f, 0.06f, 0.05f, 0.06f, 0.07f, 0.09f };   // 0.54 s of warning ring
            MoonfallS = FxKit.TimedHit("ModSilMoonfallS", "TrollGroundPoundBigShockwave", "FxSilMoonfall", "Small", 5, 7, 0.8f, 0.8f, durations: dur, canFlip: false);
            Strike.Ground(MoonfallS, "FxSilMoonfall", 25, 44, 24f, 10f);
            MoonfallM = FxKit.TimedHit("ModSilMoonfallM", "TrollGroundPoundBigShockwave", "FxSilMoonfall", "Mid", 5, 7, 1.2f, 1.0f, durations: dur, canFlip: false);
            Strike.Ground(MoonfallM, "FxSilMoonfall", 25, 44, 32f, 13f);
            MoonfallL = FxKit.TimedHit("ModSilMoonfallL", "TrollGroundPoundBigShockwave", "FxSilMoonfall", "Full", 5, 7, 1.6f, 1.4f, daze, 1f, durations: dur, canFlip: false);
            Strike.Ground(MoonfallL, "FxSilMoonfall", 25, 44, 40f, 16f);

            // ---- Comet Stag
            GoreHit = AimedMelee.Rotating(FxKit.BodyHit("ModSilGoreHit", 1.3f, 0f, 1.3f, 0.14f));
            Strike.HitBox(GoreHit, 18f, 18f);                    // at (19, 12): x 10..28, y 3..21 (the lowered head and brow tines reach x 26)
            AntlerFx = AimedMelee.Rotating(FxKit.Visual("ModSilAntlerFx", "FxSilAntler", "Slash"));
            Strike.ArtAt(AntlerFx, "FxSilAntler", 15, 12);
            ChargeBurst = FxKit.TimedHit("ModSilChargeBurst", "TrollGroundPoundBigShockwave", "FxSilChargeBurst", "Play", 0, 2, 0.6f, 2.4f, daze, 1f, canFlip: false);
            Strike.Ground(ChargeBurst, "FxSilChargeBurst", 18, 23, 26f, 14f);
            CometHit = AimedMelee.Rotating(FxKit.BodyHit("ModSilCometHit", 0.9f, 0.4f, 1.4f, 1.15f));
            Strike.HitBox(CometHit, 20f, 16f);
            CometTrail = FxKit.Visual("ModSilCometTrail", "FxSilCometTrail", "Play");
            if (CometTrail != null)
            {
                FxFactory.SetEffect(CometTrail, destroyOnAnimEnd: true, canFlip: false, freeRotate: true);   // turned to the flight line
                Strike.ArtAt(CometTrail, "FxSilCometTrail", 9, 6);
            }
            Bounce = FxKit.Visual("ModSilBounce", "FxSilBounce", "Play");
            Strike.ArtAt(Bounce, "FxSilBounce", 15, 27);

            // ---- Astrarch: the star bolt runs on the floor line (so its star lands where the shot ends), drawn at palm height
            StarBurst = FxKit.Visual("ModSilStarBurst", "FxSilStar", "Burst");
            Strike.ArtAt(StarBurst, "FxSilStar", 15, 23);
            Star = FxKit.Inert("ModSilStar", "FxSilStar", "Land", destroyOnAnimEnd: true, thenAnim: "Idle", thenRepeat: 15);   // 0.25 + 15 x 0.64 = 9.9 s
            Strike.ArtAt(Star, "FxSilStar", 15, 23);
            if (Star != null) FxFactory.OnSpawn[Star] = i => { var s = i.GetComponent<SilStarFx>() ?? i.AddComponent<SilStarFx>(); s.Reset(); };
            Starshot = FxKit.Projectile("ModSilStarshot", "webBall", "FxSilStarshot", "Fly", 165f, 0.55f, 0.9f, 0.4f, rotate: false);
            if (Starshot != null)
            {
                Strike.ArtAt(Starshot, "FxSilStarshot", 7, 3 + 14);
                FxFactory.SetEffect(Starshot, destroyOnAnimEnd: false, destroyAfter: 0.55f, spawnOnDestroy: Star, freeRotate: false);
                FxFactory.SetContacts(Starshot, destroyOnHit: true, spawnOnHit: Star);
                Strike.Collider(Starshot, 8f, 8f);
            }
            Link = FxKit.Visual("ModSilLink", "FxSilLink", "Play");
            Strike.ArtAt(Link, "FxSilLink", 3, 2);
            Starfall = FxKit.Visual("ModSilStarfall", "FxSilStarfall", "Fall");
            Strike.ArtAt(Starfall, "FxSilStarfall", 9, 47);
            StarHit = FxKit.TimedHit("ModSilStarHit", "TrollGroundPoundBigShockwave", "FxSilStarHit", "Play", 0, 2, 1.5f, 0.8f, daze, 1f, canFlip: false);
            Strike.Ground(StarHit, "FxSilStarHit", 18, 25, 26f, 12f);
            Arrival = FxKit.Visual("ModSilArrival", "FxSilArrival", "Play");
            Strike.ArtAt(Arrival, "FxSilArrival", 31, 47);

            // ---- indicators
            Phase = new StatusOverlayDef[5];
            string[] ph = { "New", "Crescent", "Half", "Gibbous", "Full" };
            for (int i = 0; i < 5; i++) Phase[i] = ModStatus.Indicator("ModIndSilPhase" + ph[i], "FxSilPhase", ph[i], 1f, OverlayAt.Head);
            AntlerGlow = ModStatus.Indicator("ModIndSilAntlers", "FxSilAntlerGlow", "Loop", 1f, OverlayAt.Head);
            Veil = ModStatus.Indicator("ModIndSilVeil", "FxSilVeil", "Loop", -4f, OverlayAt.Feet);

            // ---- every silver hit lands in a silver puff (not the neutral mod puff)
            foreach (var go in new[] { CrescentWave, Starshot, MoonfallS, MoonfallM, MoonfallL, ChargeBurst, StarHit })
                SilverImpact.Theme(go);
            Plugin.Log.LogInfo("Silver FX templates built");
        }
    }

    /// <summary>The silver impact puffs (FxSilImpact Wall/Hit): a copy of each neutral mod puff a template carries, reskinned.</summary>
    public static class SilverImpact
    {
        static readonly Dictionary<GameObject, GameObject> s_puff = new Dictionary<GameObject, GameObject>();

        public static void Theme(GameObject fx)
        {
            if (fx == null) return;
            foreach (var d in fx.GetComponentsInChildren<DamageEffect>(true))
            {
                if (d.m_contactData == null) continue;
                foreach (var c in d.m_contactData)
                {
                    if (c == null || c.m_spawnOnHit == null) continue;
                    var p = Of(c.m_spawnOnHit);
                    if (p != null) c.m_spawnOnHit = p;
                }
            }
        }

        static GameObject Of(GameObject neutral)
        {
            if (neutral == null || !neutral.name.StartsWith("ModImpactMod")) return null;
            GameObject g;
            if (s_puff.TryGetValue(neutral, out g)) return g;
            var sh = SpriteSheets.Get("FxSilImpact");
            bool wall = neutral.name.StartsWith("ModImpactModWall");
            if (sh == null) return null;
            string name = "ModImpactSil" + neutral.name.Substring("ModImpactMod".Length);
            g = MonsterFactory.ClonePrefab(neutral, name);
            FxFactory.Templates[name] = g;
            FxFactory.Reskin(g, new ClipBuilder(sh, wall ? "Wall" : "Hit", name + "Clip").Once().Build(), sh);
            var spr = g.GetComponent<exSprite>();
            if (spr != null) { spr.anchor = exPlane.Anchor.MidCenter; spr.offset = Vector2.zero; spr.color = Color.white; }
            s_puff[neutral] = g;
            return g;
        }
    }

    public static class SilverPack
    {
        static ClipBuilder Cast(SpriteSheet sh, string anim, string clip, int release)
        {
            return new ClipBuilder(sh, anim, clip).Once().EvF(0, "AnimInputMultiplyFreeFace", 0f)
                .Ev(Mathf.Max(0, release - 1), "AnimInputMultiplyStop").Ev(Mathf.Max(0, release - 1), "AnimInputOff").Ev(release, "AnimMoveStop");
        }

        // Moonwarden: a crescent glaive sweep (at Full moon it also throws a crescent wave, SilSweepWave); Moonfall drops the
        // moon on the hero: Small (New/Crescent) 0.8, Mid (Half/Gibbous) 1.2, Full 1.6 + daze, then the moon is New again.
        static void WardenKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int hit = Kit.AddEffect(p, SilverFx.GlaiveHit, attach: true, destroyOnAnimEnd: true, offsetX: 16f, offsetY: 11f);
            int arc = Kit.AddEffect(p, SilverFx.GlaiveFx, attach: true, offsetX: 14f, offsetY: 14f);   // arc centred on the hand (10, 14)
            var sw = Kit.Melee(sh, "Sweep", "ModSilWardenSweep", v, 2, hit, 40f);
            sw.Ev(2, "AnimAttack", arc).Ev(2, "SilSweepWave");
            var mf = Cast(sh, "Moonfall", "ModSilWardenMoonfall", 5).Ev(5, "SilMoonfall").EvO(5, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sw.Build(), 1.5f, rangeInner: 12f, rangeOuter: 34f));   // box to x 28 + hero half-width + lunge
            Kit.SetSpecial(p, Kit.Attack(sp, mf, 0f, rangeInner: 20f, rangeOuter: 140f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 12f);
        }

        // Comet Stag: an antler gore; Comet: rear up and become a streak of starlight that flies the way you face and
        // rebounds off walls up to 3 times (1.1 s, can't be hit, passes through the hero, 0.9 per pass).
        static void StagKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int gore = Kit.AddEffect(p, SilverFx.GoreHit, attach: true, destroyOnAnimEnd: true, offsetX: 19f, offsetY: 12f);
            int slash = Kit.AddEffect(p, SilverFx.AntlerFx, attach: true, offsetX: 12f, offsetY: 14f);
            int body = Kit.AddEffect(p, SilverFx.CometHit, attach: true, destroyOnAnimEnd: true, offsetX: 4f, offsetY: 12f);
            var gr = Kit.Melee(sh, "Gore", "ModSilStagGore", v, 3, gore, 60f);
            gr.Ev(3, "AnimAttack", slash);
            // CometRise 3 + CometLoop x6 (18) + CometEnd 2: the streak flies frames 3..20, lands on 21
            var cm = new ClipBuilder(sh, "CometRise", "ModSilStagComet").Once().Then("CometLoop", 6).Then("CometEnd")
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff").Ev(2, "AnimMoveStop")
                .Ev(2, "AnimStartInvincibility").Ev(3, "AnimCollideOff").Ev(3, "SilCometStart").Ev(3, "AnimAttack", body).EvO(3, "AnimSound", v)
                .Ev(21, "SilCometEnd").Ev(21, "AnimCollideOn").Ev(21, "AnimStopInvincibility").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, gr.Build(), 1.3f, rangeInner: 10f, rangeOuter: 34f));
            Kit.SetSpecial(p, Kit.Attack(sp, cm, 0f, rangeInner: 30f, rangeOuter: 150f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 12f);
        }

        // Astrarch: Starshot flings a star that sets into the floor where it stops (lasts 10 s, 5 at most); Constellation
        // joins them (3 are placed round the hero if fewer are out) and starfall strikes inside the shape 0.8 s later.
        static void AstrarchKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int shot = Kit.AddEffect(p, SilverFx.Starshot, offsetX: 9f, offsetY: 1f);    // floor line under the palm (9, 24); art 14 px up
            var ss = Kit.Shot(sh, "Starshot", "ModSilAstrarchStarshot", 3, v, 0f, shot).Build();
            var cn = Cast(sh, "Constellation", "ModSilAstrarchConstellation", 5).Ev(5, "SilConstellation").EvO(5, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, ss, 1.4f, rangeInner: 40f, rangeOuter: 100f, rangeRetreat: 40f));
            Kit.SetSpecial(p, Kit.Attack(sp, cn, 0f, rangeInner: 0f, rangeOuter: 160f, rangeRetreat: 30f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 8f);
        }

        static void Silver(GameObject go, Player p)
        {
            Kit.AddDeathSpawn(p, SilverFx.DeathFx);
            Strike.DeathAtFeet(p);
            GodArt.UseHitSplat(p, SilverFx.HitSplat);
        }

        public static readonly List<MonsterDef> Monsters = new List<MonsterDef>
        {
            // unique finals: no parent, evolve no further (evolveTo stays empty), tier-3 cost so they get the T3 multipliers
            new MonsterDef { id = "SilverMoonwarden", art = "SilMoonwarden", basePrefab = "EnemyDarkGuardian", health = 13f, speedMult = 1.15f,
                             evolveCost = 4.5f, kit = WardenKit, customize = Silver },
            new MonsterDef { id = "SilverCometStag", art = "SilCometStag", basePrefab = "EnemyEyelessBeast", health = 12.5f, speedMult = 1.1f,
                             evolveCost = 4.5f, kit = StagKit, customize = Silver },
            new MonsterDef { id = "SilverAstrarch", art = "SilAstrarch", basePrefab = "EnemyPriestess", health = 13.5f, speedMult = 0.92f,
                             evolveCost = 4.5f, kit = AstrarchKit, customize = Silver },
        };

        /// <summary>Odds of a tier-3 silver orb upgrade (the rest, 56, is the body's own Silver Ascended form).</summary>
        public const float OddsMoonwarden = 20f, OddsCometStag = 20f, OddsAstrarch = 4f;

        public static string Roll(string current)
        {
            if (SilverUniques.Ids.Count < 3) return null;
            float r = UnityEngine.Random.value * 100f;
            if (r < OddsMoonwarden) return SilverUniques.Ids[0];
            if (r < OddsMoonwarden + OddsCometStag) return SilverUniques.Ids[1];
            if (r < OddsMoonwarden + OddsCometStag + OddsAstrarch) return SilverUniques.Ids[2];
            return null;
        }

        static bool s_done;

        public static void Register()
        {
            if (s_done) return;
            s_done = true;
            SilverFx.Build();
            foreach (var m in Monsters) MonsterFactory.Build(m);
            SilverUniques.Ids.Clear();
            foreach (var m in Monsters) if (MonsterFactory.Built.ContainsKey(m.id)) SilverUniques.Ids.Add(m.PrefabName);
            if (SilverUniques.Ids.Count == 3) SilverUniques.RollTier3 = Roll;
            else Plugin.Log.LogError("Silver uniques: only " + SilverUniques.Ids.Count + " of 3 built; the tier-3 upgrade stays Ascended-only");
            Strike.KeepAllScales();
        }

        /// <summary>Self-test (wired into SelfTest.cs): built, finals with no parent, statues, FX, the odds.</summary>
        public static void SelfCheck(Action<string> bad)
        {
            if (SilverUniques.Ids.Count != 3) bad("silver uniques: " + SilverUniques.Ids.Count + " of 3 registered");
            var parents = new HashSet<string>();
            foreach (var kv in MonsterFactory.Built)
            {
                var to = kv.Value != null ? kv.Value.GetEvolveTo() : null;
                if (to != null) foreach (var t in to) if (t != null) parents.Add(t.gameObject.name);
            }
            foreach (var m in Monsters)
            {
                Player p;
                if (!MonsterFactory.Built.TryGetValue(m.id, out p) || p == null) { bad("silver unique " + m.id + " failed to build"); continue; }
                var to = p.GetEvolveTo();
                if (to != null && to.Length > 0) bad(m.PrefabName + " evolves further (" + to.Length + ")");
                if (parents.Contains(m.PrefabName)) bad(m.PrefabName + " is offered by an evolution (must have no parent)");
                if (Mathf.Abs(R.Get<float>(p, "m_evolveCost") - 4.5f) > 0.01f) bad(m.PrefabName + " is not a tier-3 cost");
                var st = p.GetAnimationStatue();
                if (st == null || !st.name.StartsWith("ModStatue_")) bad(m.PrefabName + " has no carved statue (" + (st == null ? "none" : st.name) + ")");
                MonsterTip tip;
                if (!MonsterTipsData.TryGet(m.PrefabName, out tip)) bad(m.PrefabName + " has no monster tip");
            }
            foreach (var kv in new Dictionary<string, object>
            {
                { "GlaiveHit", SilverFx.GlaiveHit }, { "GlaiveFx", SilverFx.GlaiveFx }, { "CrescentWave", SilverFx.CrescentWave },
                { "MoonfallS", SilverFx.MoonfallS }, { "MoonfallM", SilverFx.MoonfallM }, { "MoonfallL", SilverFx.MoonfallL },
                { "GoreHit", SilverFx.GoreHit }, { "AntlerFx", SilverFx.AntlerFx }, { "ChargeBurst", SilverFx.ChargeBurst },
                { "CometHit", SilverFx.CometHit }, { "CometTrail", SilverFx.CometTrail }, { "Bounce", SilverFx.Bounce },
                { "Starshot", SilverFx.Starshot }, { "Star", SilverFx.Star }, { "StarBurst", SilverFx.StarBurst }, { "Link", SilverFx.Link },
                { "Starfall", SilverFx.Starfall }, { "StarHit", SilverFx.StarHit }, { "Arrival", SilverFx.Arrival },
                { "HitSplat", SilverFx.HitSplat }, { "DeathFx", SilverFx.DeathFx }, { "AntlerGlow", SilverFx.AntlerGlow }, { "Veil", SilverFx.Veil },
            })
                if (kv.Value == null || (kv.Value is UnityEngine.Object && (UnityEngine.Object)kv.Value == null)) bad("silver FX " + kv.Key + " missing");
            if (SilverFx.Phase == null || Array.Exists(SilverFx.Phase, d => d == null)) bad("silver moon phase indicators missing");
            // obtainable ONLY through the silver ghost's tier-3 orb upgrade. No statue, spawn group, god tree,
            // starter list (idols pick from gods' starters) or evolution may offer them.
            foreach (var g in Resources.FindObjectsOfTypeAll<SpawnGroup>())
            {
                if (g == null || g.gameObject.scene.IsValid()) continue;
                var items = R.Get<List<SpawnItem>>(g, "m_items");
                if (items == null) continue;
                foreach (var it in items)
                    if (it != null && it.m_object != null && SilverUniques.Ids.Contains(it.m_object.name))
                        bad(it.m_object.name + " is in spawn group " + g.gameObject.name + " (silver uniques come only from the silver ghost upgrade)");
            }
            if (SilverUniques.Ids.Count == 0 || !SilverUniques.Ids.TrueForAll(Statues.Excluded))
                bad("Statues.Excluded does not cover the silver uniques");
            var gods = SystemDeity.GetDeities();
            if (gods != null)
                foreach (var d in gods)
                {
                    var st = d != null ? d.GetStartingMonsters() : null;
                    if (st != null) foreach (var go in st) if (go != null && SilverUniques.Ids.Contains(go.name)) bad(go.name + " is a starter of " + d.GetName());
                }
            // the odds: 10000 rolls land within a point of 20 / 20 / 4 / 56
            if (SilverUniques.Ids.Count == 3)
            {
                var n = new int[4];
                for (int i = 0; i < 10000; i++)
                {
                    var r = SilverUniques.RollTier3("ModVhAshSeraph");
                    n[r == null ? 3 : SilverUniques.Ids.IndexOf(r)]++;
                }
                float[] want = { OddsMoonwarden, OddsCometStag, OddsAstrarch, 100f - OddsMoonwarden - OddsCometStag - OddsAstrarch };
                for (int i = 0; i < 4; i++)
                    if (Mathf.Abs(n[i] / 100f - want[i]) > 1.5f) bad("silver roll " + i + ": " + (n[i] / 100f) + " in 100, want " + want[i]);
            }
        }
    }

    // ================================================================================================= brains
    /// <summary>Shared bits for the silver brains.</summary>
    public abstract class SilverBrain : MonoBehaviour
    {
        protected Health m_health;
        protected Player m_player;
        protected exSprite m_sprite;
        protected PlayerMovement m_move;
        protected virtual void Awake()
        {
            m_health = GetComponent<Health>(); m_player = GetComponent<Player>(); m_sprite = GetComponent<exSprite>(); m_move = GetComponent<PlayerMovement>();
        }
        protected bool Alive { get { return m_health != null && m_health.IsAlive(); } }
        protected Vector2 Feet { get { return (Vector2)transform.position + new Vector2(0f, m_sprite != null ? m_sprite.offset.y + 2f : 0f); } }
        protected DamageSource Own()
        {
            return ModUtil.MonsterSource(gameObject);
        }
        protected Vector2 Facing
        {
            get
            {
                var d = m_move != null ? R.Get<Vector2>(m_move, "m_faceDirection") : Vector2.zero;
                if (d.sqrMagnitude < 0.01f) d = new Vector2(transform.localScale.x < 0f ? -1f : 1f, 0f);
                return d.normalized;
            }
        }
        protected static float Angle(Vector2 d) { return Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg; }
        protected static bool From(DamageInfo d, string prefix)
        {
            var src = d != null && d.m_source != null ? d.m_source.m_source : null;
            return src != null && src.name.StartsWith(prefix);
        }
        protected static bool HeroAlive(GameObject hero)
        {
            var h = hero != null ? hero.GetComponent<Health>() : null;
            return h != null && h.IsAlive();
        }
    }

    /// <summary>
    /// Moonwarden: its moon waxes a phase every 2 s (New, Crescent, Half, Gibbous, Full) and holds at Full, shown over its
    /// head. Moonfall drops a moon sized by the phase and starts the cycle again; at Full every sweep also throws a
    /// crescent wave.
    /// </summary>
    public class SilMoonPhase : SilverBrain
    {
        public const float Step = 2f, Reach = 150f;
        public int phase;
        float m_t;
        int m_shown = -1;
        void OnEnable() { phase = 0; m_t = 0f; m_shown = -1; }
        void OnDisable() { ModInd.Count(gameObject, SilverFx.Phase, 0); m_shown = -1; }

        void Show() { if (SilverFx.Phase != null && Alive) { ModInd.Count(gameObject, SilverFx.Phase, phase + 1); m_shown = phase; } }

        void Update()
        {
            if (!Alive) { if (m_shown >= 0) { ModInd.Count(gameObject, SilverFx.Phase, 0); m_shown = -1; } return; }
            if (m_shown != phase) Show();
            if (phase >= 4) return;
            m_t += Time.deltaTime;
            if (m_t < Step) return;
            m_t = 0f; phase++;
            Show();
        }

        public void SilSweepWave()
        {
            if (phase < 4 || !Alive || SilverFx.CrescentWave == null) return;
            var dir = Facing;
            FxFactory.SpawnOwned(SilverFx.CrescentWave, Feet + new Vector2(dir.x * 12f, 12f), Own(), Angle(dir));
        }

        public void SilMoonfall()
        {
            if (!Alive) return;
            var tmpl = phase >= 4 ? SilverFx.MoonfallL : phase >= 2 ? SilverFx.MoonfallM : SilverFx.MoonfallS;
            phase = 0; m_t = 0f; Show();
            if (tmpl == null) return;
            var hero = ModUtil.Hero();
            Vector2 me = Feet, at;
            if (hero != null && HeroAlive(hero))
            {
                at = hero.transform.position;
                var d = at - me;
                if (d.magnitude > Reach) at = me + d.normalized * Reach;
            }
            else at = me + Facing * 60f;
            at = ModUtil.SafePoint(me, at, 6f);
            FxFactory.SpawnOwned(tmpl, at, Own());
        }
    }

    /// <summary>
    /// Comet Stag. Comet: the body flies at 230 px/s the way it faced, bouncing off walls (3 bounces, then it stops),
    /// leaving a trail of starlight. Passive Stampede: running at 3/4 speed or more in a straight line for 1 s charges the
    /// antlers (shown over its head): the next gore that lands also bursts (0.6, knocks far, dazes). Lasts 6 s.
    /// </summary>
    public class SilCometRun : SilverBrain
    {
        public const float Speed = 230f, ChargeTime = 1f, ChargeLife = 6f, TrailGap = 0.05f;
        public const int MaxBounces = 3;
        bool m_comet;
        Vector2 m_dir;
        int m_bounces;
        float m_trail;
        // stampede
        Vector2 m_last, m_runDir;
        float m_straight, m_charged;
        public bool Charged { get { return m_charged > 0f; } }

        float m_flown;
        void OnEnable()
        {
            m_comet = false; m_straight = 0f; m_charged = 0f; m_last = transform.position; SetGlow(false);
            if (m_player != null) m_player.AnimCollideOn();          // a pooled body that died mid-Comet collides again
        }
        void OnDisable() { m_comet = false; SetGlow(false); }
        void SetGlow(bool on) { if (SilverFx.AntlerGlow != null) ModInd.Set(gameObject, SilverFx.AntlerGlow, on); }

        public void SilCometStart()
        {
            if (!Alive) return;
            m_comet = true; m_dir = Facing; m_bounces = 0; m_trail = 0f; m_flown = 0f;
            if (m_move != null) m_move.Stop();
        }

        public void SilCometEnd()
        {
            m_comet = false;
            if (m_move != null) m_move.Stop();
        }

        void Update()
        {
            if (!Alive) { if (m_charged > 0f) { m_charged = 0f; SetGlow(false); } m_comet = false; return; }
            if (m_comet)
            {
                m_flown += Time.deltaTime;
                if (m_flown > 1.4f) { SilCometEnd(); if (m_player != null) m_player.AnimCollideOn(); }   // the clip was cut short
                else Fly();
                m_last = transform.position; return;
            }
            // stampede: straight running charges the antlers
            Vector2 pos = transform.position;
            float dt = Mathf.Max(0.0001f, Time.deltaTime);
            var vel = (pos - m_last) / dt;
            m_last = pos;
            float max = m_move != null ? R.Get<float>(m_move, "m_speedMax") : 90f;
            if (m_charged > 0f)
            {
                m_charged -= Time.deltaTime;
                if (m_charged <= 0f) SetGlow(false);
                return;
            }
            if (vel.magnitude >= max * 0.75f)
            {
                var d = vel.normalized;
                if (m_straight > 0f && Vector2.Angle(d, m_runDir) > 20f) m_straight = 0f;
                if (m_straight <= 0f) m_runDir = d;
                m_straight += Time.deltaTime;
                if (m_straight >= ChargeTime) { m_straight = 0f; m_charged = ChargeLife; SetGlow(true); }
            }
            else m_straight = Mathf.Max(0f, m_straight - Time.deltaTime * 2f);
        }

        void Fly()
        {
            Vector2 pos = transform.position;
            float step = Speed * Time.deltaTime;
            RaycastHit hit;
            if (m_bounces <= MaxBounces &&
                Physics.Raycast(new Vector3(pos.x, pos.y, 0f), new Vector3(m_dir.x, m_dir.y, 0f), out hit, step + 7f, Constants.COL_MASK_WALLS))
            {
                if (m_bounces >= MaxBounces) { m_bounces++; if (m_move != null) m_move.Stop(); return; }   // spent: hold here
                m_bounces++;
                Vector2 n = hit.normal;
                m_dir = Vector2.Reflect(m_dir, n).normalized;
                if (SilverFx.Bounce != null) FxFactory.SpawnOwned(SilverFx.Bounce, (Vector2)hit.point + n * 4f + new Vector2(0f, -2f), Own());
                if (m_move != null) m_move.SetDirection(m_dir);
                return;
            }
            if (m_bounces > MaxBounces) return;
            ModUtil.Teleport(gameObject, pos + m_dir * step);
            if (m_move != null) { m_move.Stop(); m_move.SetDirection(m_dir); }
            m_trail -= Time.deltaTime;
            if (m_trail <= 0f && SilverFx.CometTrail != null)
            {
                m_trail = TrailGap;
                FxFactory.SpawnOwned(SilverFx.CometTrail, Feet + new Vector2(0f, 12f), Own(), Angle(m_dir));   // centred on the streak
            }
        }

        void MsgOnAttackContact(DamageInfo d)
        {
            var hero = ModUtil.Hero();
            if (m_charged <= 0f || !Alive || d == null || hero == null || d.m_victim != hero || !From(d, "ModSilGoreHit")) return;
            m_charged = 0f; SetGlow(false);
            if (SilverFx.ChargeBurst != null) FxFactory.SpawnOwned(SilverFx.ChargeBurst, hero.transform.position, Own());
        }
    }

    /// <summary>A star set in the floor by the Astrarch's Starshot (lives ~10 s). Registry of live stars by owner.</summary>
    public class SilStarFx : MonoBehaviour
    {
        public static readonly List<SilStarFx> All = new List<SilStarFx>();
        public float born;
        GameObject m_owner;
        public bool consumed;
        public void Reset() { born = Time.time; consumed = false; m_owner = null; }
        void OnEnable() { if (!All.Contains(this)) All.Add(this); }
        void OnDisable() { All.Remove(this); }

        public GameObject Owner
        {
            get
            {
                if (m_owner == null)
                {
                    var src = FxFactory.SourceOf(gameObject);
                    if (src != null) m_owner = src.m_sourceOwner != null ? src.m_sourceOwner : src.m_source;
                }
                return m_owner;
            }
            set { m_owner = value; }
        }

        public Vector2 Pos { get { return transform.position; } }

        public void Burst()
        {
            if (consumed) return;
            consumed = true;
            if (SilverFx.StarBurst != null) SystemPool.Spawn(SilverFx.StarBurst, transform.position);
            SystemPool.Despawn(gameObject);
        }
    }

    /// <summary>
    /// Astrarch. Stars: at most 5 of hers stay set (the oldest bursts). Constellation: with fewer than 3 out she sets 3
    /// round the hero first; dotted starlight joins the stars' outline (0.8 s), then starfall rains inside the shape and the
    /// hero takes 1.5 (dazed) if he is inside it; the stars are spent. Passive Astral Veil: 3+ of her stars out = 0.7x damage
    /// taken. She arrives in a column of starlight.
    /// </summary>
    public class SilAstral : SilverBrain
    {
        public const int MaxStars = 5;
        public const float Warn = 0.8f, VeilResist = 1f / 0.7f, Ring = 32f, Dot = 5f;
        bool m_veil;
        float m_base = 1f, m_check;

        void OnEnable()
        {
            m_veil = false; m_check = 0f;
            if (SilverFx.Arrival != null && Time.timeSinceLevelLoad > 0.5f) SystemPool.Spawn(SilverFx.Arrival, Feet);
        }
        void OnDisable() { SetVeil(false); StopAllCoroutines(); }

        List<SilStarFx> Mine()
        {
            var l = new List<SilStarFx>();
            Vector2 me = transform.position;
            foreach (var s in SilStarFx.All)
            {
                if (s == null || s.consumed || !s.isActiveAndEnabled) continue;
                var o = s.Owner;
                if (o == gameObject || (o == null && ((Vector2)s.transform.position - me).sqrMagnitude < 220f * 220f)) { s.Owner = gameObject; l.Add(s); }
            }
            l.Sort((a, b) => a.born.CompareTo(b.born));
            return l;
        }

        void Update()
        {
            m_check -= Time.deltaTime;
            if (m_check > 0f) return;
            m_check = 0.2f;
            if (!Alive) { SetVeil(false); return; }
            var mine = Mine();
            while (mine.Count > MaxStars) { mine[0].Burst(); mine.RemoveAt(0); }
            SetVeil(mine.Count >= 3);
        }

        void SetVeil(bool on)
        {
            if (on == m_veil || m_health == null) return;
            if (on)
            {
                m_base = R.Get<float>(m_health, "m_damageResistanceFinal");
                R.Set(m_health, "m_damageResistanceFinal", m_base * VeilResist);
            }
            else if (Mathf.Abs(R.Get<float>(m_health, "m_damageResistanceFinal") - m_base * VeilResist) < 0.001f)
                R.Set(m_health, "m_damageResistanceFinal", m_base);
            m_veil = on;
            if (SilverFx.Veil != null) ModInd.Set(gameObject, SilverFx.Veil, on);
        }

        public void SilConstellation()
        {
            if (!Alive || !gameObject.activeInHierarchy) return;
            var hero = ModUtil.Hero();
            var stars = Mine();
            var pts = new List<Vector2>();
            foreach (var s in stars) pts.Add(s.Pos);
            if (pts.Count < 3 && hero != null && SilverFx.Star != null)
            {
                Vector2 hp = hero.transform.position;
                float a0 = UnityEngine.Random.Range(0f, 120f);
                for (int i = 0; i < 3; i++)
                {
                    float a = (a0 + i * 120f) * Mathf.Deg2Rad;
                    var at = ModUtil.SafePoint(hp, hp + new Vector2(Mathf.Cos(a), Mathf.Sin(a) * 0.8f) * Ring, 6f);
                    var go = FxFactory.SpawnOwned(SilverFx.Star, at, Own());
                    var sf = go != null ? go.GetComponent<SilStarFx>() : null;
                    if (sf != null) { sf.Owner = gameObject; stars.Add(sf); }
                    pts.Add(at);
                }
            }
            if (pts.Count < 3) return;
            StopAllCoroutines();
            StartCoroutine(Draw(stars, Hull(pts)));
        }

        IEnumerator<object> Draw(List<SilStarFx> stars, List<Vector2> hull)
        {
            var src = Own();
            // the outline, dot by dot
            if (SilverFx.Link != null)
                for (int i = 0; i < hull.Count; i++)
                {
                    Vector2 a = hull[i], b = hull[(i + 1) % hull.Count];
                    int n = Mathf.Max(1, Mathf.RoundToInt((b - a).magnitude / Dot));
                    for (int k = 0; k < n; k++) SystemPool.Spawn(SilverFx.Link, Vector2.Lerp(a, b, k / (float)n));
                    yield return new WaitForSeconds(0.04f);
                }
            float waited = 0.04f * hull.Count;
            if (waited < Warn) yield return new WaitForSeconds(Warn - waited);
            if (!Alive) yield break;
            // starfall over the shape
            var c = Centroid(hull);
            float area = Mathf.Abs(Area(hull));
            int falls = Mathf.Clamp(6 + Mathf.RoundToInt(area / 500f), 6, 14);
            if (SilverFx.Starfall != null)
                for (int i = 0; i < falls; i++)
                {
                    var p = Lerp3(hull, c, i);
                    SystemPool.Spawn(SilverFx.Starfall, p);
                }
            yield return new WaitForSeconds(0.18f);      // the falling stars land (Fall frame 4)
            var hero = ModUtil.Hero();
            if (hero != null && Alive && SilverFx.StarHit != null && Inside(hull, hero.transform.position, 4f))
                FxFactory.SpawnOwned(SilverFx.StarHit, hero.transform.position, src);
            foreach (var s in stars) if (s != null) s.Burst();
        }

        // ---- geometry
        static List<Vector2> Hull(List<Vector2> pts)
        {
            var p = new List<Vector2>(pts);
            p.Sort((a, b) => a.x != b.x ? a.x.CompareTo(b.x) : a.y.CompareTo(b.y));
            var h = new List<Vector2>();
            for (int pass = 0; pass < 2; pass++)
            {
                int start = h.Count;
                for (int i = 0; i < p.Count; i++)
                {
                    var q = pass == 0 ? p[i] : p[p.Count - 1 - i];
                    while (h.Count >= start + 2 && Cross(h[h.Count - 2], h[h.Count - 1], q) <= 0f) h.RemoveAt(h.Count - 1);
                    h.Add(q);
                }
                h.RemoveAt(h.Count - 1);
            }
            return h.Count >= 3 ? h : pts;
        }
        static float Cross(Vector2 o, Vector2 a, Vector2 b) { return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x); }
        static float Area(List<Vector2> h) { float s = 0f; for (int i = 0; i < h.Count; i++) { var a = h[i]; var b = h[(i + 1) % h.Count]; s += a.x * b.y - b.x * a.y; } return s * 0.5f; }
        static Vector2 Centroid(List<Vector2> h) { var c = Vector2.zero; foreach (var p in h) c += p; return c / h.Count; }
        /// <summary>Inside the convex hull (counter-clockwise from Hull), or within <paramref name="margin"/> px of it.</summary>
        static bool Inside(List<Vector2> h, Vector2 p, float margin)
        {
            for (int i = 0; i < h.Count; i++)
            {
                var a = h[i]; var b = h[(i + 1) % h.Count];
                var e = b - a;
                float len = e.magnitude;
                if (len < 0.01f) continue;
                if (Cross(a, b, p) / len < -margin) return false;
            }
            return true;
        }
        /// <summary>A spread of points inside the shape: blends of the centre and two neighbouring corners.</summary>
        static Vector2 Lerp3(List<Vector2> h, Vector2 c, int i)
        {
            var a = h[i % h.Count]; var b = h[(i + 1) % h.Count];
            float u = UnityEngine.Random.Range(0.15f, 0.8f), v = UnityEngine.Random.Range(0f, 1f - u);
            return c + (a - c) * u + (b - c) * v;
        }
    }

    /// <summary>Give the silver uniques their brain on every instance (components on a template do not survive Instantiate).</summary>
    [HarmonyLib.HarmonyPatch(typeof(Player), "Awake")]
    static class Patch_SilverAwake
    {
        static void Postfix(Player __instance)
        {
            if (__instance == null) return;
            switch (ModUtil.PrefabName(__instance.gameObject))
            {
                case "ModSilverMoonwarden": if (__instance.GetComponent<SilMoonPhase>() == null) __instance.gameObject.AddComponent<SilMoonPhase>(); break;
                case "ModSilverCometStag": if (__instance.GetComponent<SilCometRun>() == null) __instance.gameObject.AddComponent<SilCometRun>(); break;
                case "ModSilverAstrarch": if (__instance.GetComponent<SilAstral>() == null) __instance.gameObject.AddComponent<SilAstral>(); break;
            }
        }
    }
}
