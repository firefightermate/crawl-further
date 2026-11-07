using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Bosses
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;
    using CrawlFurther.Content.Gods.BelMora;
    using CrawlFurther.Content.Gods.Jinx;

    /// <summary>
    /// Two new bosses:
    /// - THE LEVIATHAN (Bel'Mora's): a drowned three-headed sea serpent. Brine jets slow, hooks drag the hero in,
    ///   spit lands as brine, and the tide sweeps the arena every few seconds.
    /// - PANDEMONIUM (Jinx's): the big top's tentacled horror. Bursting juggling balls, loaded dice, a golden
    ///   spotlight, and a Wheel of Misfortune that rains knives, scatters confetti bombs or lets the clowns in.
    /// Both run on a vanilla boss's machinery (rooms, phases, possessable parts) with every frame redrawn
    /// (art/out_bosses, tools/sprites/boss_art.py: same cells and pivots, new creatures painted into them).
    /// Built only when <see cref="Enabled"/>.
    /// </summary>
    public static class BossPack
    {
        public static Boss Leviathan, Pandemonium;

        // --------------------------------------------------------------- palettes
        static Color32 Drowned(Color32 c)
        {
            float h, s, v;
            BossFactory.ToHSV(c, out h, out s, out v);
            if (h >= 35f && h <= 110f && s > 0.2f) return BossFactory.HSV(h + 105f, s * 0.85f, v * 0.95f);       // olive scales -> teal
            if ((h < 25f || h > 330f) && s > 0.25f) return BossFactory.HSV(h - 18f, s * 0.8f, v * 0.9f);        // flesh -> drowned coral
            if (h >= 15f && h < 35f && s > 0.2f) return BossFactory.HSV(200f, s * 0.35f, v);                     // browns -> slate
            return c;
        }

        static Color32 Carnival(Color32 c)
        {
            float h, s, v;
            BossFactory.ToHSV(c, out h, out s, out v);
            if (h >= 40f && h <= 80f && s > 0.25f) return BossFactory.HSV(352f, s * 1.5f + 0.1f, v * 1.05f);      // khaki hide -> crimson
            if (h >= 160f && h <= 200f) return BossFactory.HSV(275f, s * 0.6f, v * 0.55f);                       // teal-greys -> black-violet
            if ((h < 20f || h > 330f) && s > 0.2f) return BossFactory.HSV(42f, s * 1.1f, v * 1.1f);              // pinks -> tarnished gold
            if (h >= 20f && h < 40f && s > 0.15f) return BossFactory.HSV(345f, s * 0.9f, v * 0.8f);              // browns -> dark crimson
            return c;
        }

        static PropTrap Part(GameObject boss, string child)
        {
            foreach (var t in boss.GetComponentsInChildren<PropTrap>(true)) if (t.gameObject.name == child) return t;
            Plugin.Log.LogWarning("Boss part not found: " + child);
            return null;
        }

        static void SetEffect(PropTrap t, int i, GameObject fx, bool? attach = null)
        {
            if (t == null || fx == null) return;
            var list = R.Get<List<DamageEffectData>>(t, "m_attackDamageEffects");
            if (i < 0 || i >= list.Count) return;
            list[i].m_object = fx;
            if (attach.HasValue) list[i].m_attach = attach.Value;
        }

        static T Shared<T>(Dictionary<UnityEngine.Object, UnityEngine.Object> map, string vanillaName) where T : UnityEngine.Object
        {
            var v = FxFactory.Vanilla(vanillaName);
            UnityEngine.Object o;
            return v != null && map.TryGetValue(v, out o) ? o as T : null;
        }

        // --------------------------------------------------------------- the Leviathan
        static void BuildLeviathan()
        {
            var src = FxFactory.Vanilla("BossHydra");
            if (src == null) return;
            var map = new Dictionary<UnityEngine.Object, UnityEngine.Object>();
            var atl = new HashSet<string> { "AtlasBossHydra" };
            // new art (tools/sprites/boss_art.py); the colour transform is only the fallback when the sheet is missing
            var art = BossFactory.LoadArt("BossLeviathanArt", BossFactory.VanillaAtlas("AtlasBossHydra"));
            var go = BossFactory.RecolorClone(src, "ModBossLeviathan", "Drowned", Drowned, atl, map, art);
            BossFactory.Relink(map, art);
            var boss = go.GetComponent<Boss>();
            R.Set(boss, "m_displayName", "- Challenge THE LEVIATHAN -");

            // Head A: the flamethrower becomes a brine jet that slows instead of burning
            var jet = FxFactory.Clone("FX_hydra_flamethrower_dropperA", "ModLevBrineJet");
            // the jet and its whole chain (muzzle flare, droplets, splash, mist) wear the redrawn brine art
            if (jet != null && art != null) { BossFactory.Reskin(jet, "Drowned", Drowned, atl, map, art); map[jet] = jet; }
            var particleSrc = jet != null ? R.Get<GameObject>(jet.GetComponent<ParticleMotion>(), "m_trailObject") : null;
            if (particleSrc != null)
            {
                var particle = MonsterFactory.ClonePrefab(particleSrc, "ModLevBrineJetParticle");
                if (art != null) { BossFactory.Reskin(particle, "Drowned", Drowned, atl, map, art); map[particle] = particle; }
                else foreach (var s in particle.GetComponentsInChildren<exSprite>(true)) s.color = new Color(0.45f, 0.95f, 0.9f, 1f);
                foreach (var d in particle.GetComponentsInChildren<DamageEffect>(true))
                {
                    R.Set(d, "m_status", FxFactory.GetStatus("StatusLavaSteveGoo"));
                    R.Set(d, "m_statusChance", 0.5f);
                }
                foreach (var t in particle.GetComponentsInChildren<ColorTinter>(true)) t.enabled = false;
                R.Set(jet.GetComponent<ParticleMotion>(), "m_trailObject", particle);
            }
            var headA = Part(go, "TrapA");
            for (int i = 1; i <= 6; i++) SetEffect(headA, i, jet);

            // Head B: two of its six spits are hooks that haul the hero to the jaws
            var headB = Part(go, "TrapB");
            SetEffect(headB, 1, BelMoraFx.Hook, false);
            SetEffect(headB, 4, BelMoraFx.Hook, false);

            // Head C: its spit lands as brine
            var spit = Shared<GameObject>(map, "DFX_hydra_smallProjectile");
            var spitBehind = Shared<GameObject>(map, "DFX_hydra_smallProjectileBehind");
            foreach (var g in new[] { spit, spitBehind })
                if (g != null && BelMoraFx.Brine != null) R.Set(g.GetComponent<Effect>(), "m_spawnOnDestroy", BelMoraFx.Brine);

            if (art != null) { BossFactory.Relink(map, art); BossFactory.ArtOf[boss] = art; }
            // its effects on the shared atlas: blood pools / smears / splashes become ichor, lava / goo / acid / frost brine
            BossFactory.ReskinAll(go, map, BossFactory.LoadArt("BossLeviathanFx", BossFactory.VanillaAtlas("AtlasEffectsShared")));
            FxFactory.OnSpawn[go] = i => { var b = i.GetComponent<BossBrain>() ?? i.AddComponent<BossBrain>(); b.kind = BossBrain.Kind.Leviathan; };
            Leviathan = boss;
            BossFactory.Built.Add(boss);
            Plugin.Log.LogInfo("Boss built: The Leviathan (" + map.Count + " reskinned assets, " + (art != null ? art.count + " redrawn frames" : "colour fallback") + ")");
        }

        // --------------------------------------------------------------- Pandemonium
        static void BuildPandemonium()
        {
            var src = FxFactory.Vanilla("BossTentacleBlob");
            if (src == null) return;
            var map = new Dictionary<UnityEngine.Object, UnityEngine.Object>();
            var atl = new HashSet<string> { "AtlasBoss" };
            var art = BossFactory.LoadArt("BossPandemoniumArt", BossFactory.VanillaAtlas("AtlasBoss"));
            var go = BossFactory.RecolorClone(src, "ModBossPandemonium", "Carnival", Carnival, atl, map, art);
            BossFactory.Relink(map, art);
            var boss = go.GetComponent<Boss>();
            R.Set(boss, "m_displayName", "- Challenge PANDEMONIUM -");

            // left tentacle: lobbed juggling balls that burst in confetti
            SetEffect(Part(go, "TentacleL"), 0, JinxFx.JuggleBall);
            // right tentacle: loaded dice instead of slime bombs
            var die = FxKit.Projectile("ModBossDie", "webBall", "FxDie", "Fly", 230f, 0.9f, 0.5f, 0.8f, accel: 25f, speedMax: 12f, rotate: false);
            if (die != null)
            {
                // v0.10 sweep: drawn size (15 x 13, like the vanilla boss's 16-18 px slime bombs); it was the Jinx die blown up
                // 1.6x (24 x 21 of doubled pixels). The box keeps covering the die.
                Strike.Collider(die, 13f, 12f);
                FxFactory.SetEffect(die, destroyOnAnimEnd: false, destroyAfter: 0.9f, spawnOnDestroy: JinxFx.ConfettiPop, freeRotate: false);
                FxFactory.OnSpawn[die] = i =>
                {
                    var c = i.GetComponent<ChanceFx>() ?? i.AddComponent<ChanceFx>(); c.randomDamage = true; c.baseDamage = 0.3f; c.enabled = false; c.enabled = true;
                    var rr = i.GetComponent<RollReadout>() ?? i.AddComponent<RollReadout>();
                    rr.fromSource = true; rr.max = 6;   // the face it rolled pops up over the hero it hits, like the Jinx die
                };
            }
            var right = Part(go, "TentacleR");
            SetEffect(right, 0, die);
            SetEffect(right, 2, die);
            // the eye: a golden spotlight
            var fxArt = BossFactory.LoadArt("BossPandemoniumFx", BossFactory.VanillaAtlas("AtlasEffectsShared"));
            var beam = FxFactory.Clone("BossBeam", "ModSpotlightBeam");
            if (beam != null && fxArt != null)
            {
                // a redrawn golden shaft, and its own end piece (gold streamer curls) instead of the vanilla BossBeamEnd
                var fxAtl = new HashSet<string> { fxArt.vanillaName };
                BossFactory.Reskin(beam, fxArt.sheet, null, fxAtl, map, fxArt);
                map[beam] = beam;
                var endSrc = FxFactory.Vanilla("BossBeamEnd");
                UnityEngine.Object endObj = null;
                var end = endSrc != null && map.TryGetValue(endSrc, out endObj) ? endObj as GameObject : null;
                if (end == null && endSrc != null)
                {
                    end = BossFactory.RecolorClone(endSrc, "ModSpotlightBeamEnd", fxArt.sheet, null, fxAtl, map, fxArt, 2);
                }
                if (end != null) { end.name = "ModSpotlightBeamEnd"; FxFactory.SetEffect(beam, true, spawnOnDestroy: end); }
            }
            else if (beam != null) foreach (var s in beam.GetComponentsInChildren<exSprite>(true)) s.color = new Color(1f, 0.85f, 0.45f, 1f);
            SetEffect(Part(go, "Eye"), 0, beam);

            if (art != null) BossFactory.ArtOf[boss] = art;
            // death blasts become fireworks, the bomb in the mouth violet smoke and confetti, its blood confetti
            BossFactory.ReskinAll(go, map, fxArt);
            FxFactory.OnSpawn[go] = i => { var b = i.GetComponent<BossBrain>() ?? i.AddComponent<BossBrain>(); b.kind = BossBrain.Kind.Pandemonium; };
            Pandemonium = boss;
            BossFactory.Built.Add(boss);
            Plugin.Log.LogInfo("Boss built: Pandemonium (" + map.Count + " reskinned assets, " + (art != null ? art.count + " redrawn frames" : "colour fallback") + ")");
        }

        static BepInEx.Configuration.ConfigEntry<bool> s_enabled;

        /// <summary>
        /// Whether the two bosses are built and join the boss rotation (config [Bosses] Enabled, off by default). While
        /// off they never spawn, and their tips and pause page are left out. Jinx's jacks and wheel do not need them.
        /// </summary>
        public static bool Enabled
        {
            get
            {
                if (s_enabled == null && Plugin.I != null)
                    s_enabled = Plugin.I.Config.Bind("Bosses", "Enabled", false,
                        "Build the mod's two bosses (The Leviathan and Pandemonium) and add them to the boss rotation.");
                return s_enabled != null && s_enabled.Value;
            }
        }

        public static void Register()
        {
            if (!Enabled) { Plugin.Log.LogInfo("Bosses switched off (Bosses.Enabled = false)"); return; }
            try { BuildLeviathan(); } catch (Exception e) { Plugin.Log.LogError("Leviathan failed: " + e); }
            try { BuildPandemonium(); } catch (Exception e) { Plugin.Log.LogError("Pandemonium failed: " + e); }
            Strike.KeepAllScales();
        }
    }

    /// <summary>The new mechanics layered on each mod boss while it is alive.</summary>
    public class BossBrain : MonoBehaviour
    {
        public enum Kind { Leviathan, Pandemonium }
        public Kind kind;
        float m_timer;
        Health m_health;

        void OnEnable()
        {
            m_timer = 8f;
            // the boss's real life bar is its biggest Health (the Kourok eye has a small one of its own)
            m_health = null;
            foreach (var h in GetComponentsInChildren<Health>(true))
                if (m_health == null || h.GetHealthMax() > m_health.GetHealthMax()) m_health = h;
        }

        DamageSource Src { get { return new DamageSource(gameObject, gameObject, null); } }

        bool Active
        {
            get
            {
                if (!SystemLevel.GetBossEncounterActive()) return false;
                if (m_health != null && !m_health.IsAlive()) return false;
                return ModUtil.Hero() != null;
            }
        }

        void Update()
        {
            if (!Active) return;
            m_timer -= Time.deltaTime;
            if (m_timer > 0f) return;
            var hero = (Vector2)ModUtil.Hero().transform.position;
            if (kind == Kind.Leviathan) { Tide(hero); m_timer = UnityEngine.Random.Range(8f, 11f); }
            else { StartCoroutine(Misfortune(hero)); m_timer = UnityEngine.Random.Range(10f, 13f); }
        }

        /// <summary>The tide: a wave crosses the arena at the hero's height, and brine wells up near them.</summary>
        void Tide(Vector2 hero)
        {
            if (BelMoraFx.Wave != null)
            {
                bool fromLeft = UnityEngine.Random.value < 0.5f;
                // the wave's art foot is 8 px under its centre: ride 8 px up so it rolls along the hero's floor line
                var start = hero + new Vector2(fromLeft ? -120f : 120f, 8f);
                FxFactory.SpawnOwned(BelMoraFx.Wave, start, Src, fromLeft ? 0f : 180f);
            }
            if (BelMoraFx.Brine != null)
                for (int i = 0; i < 2; i++)
                {
                    var off = (Vector2)(Quaternion.Euler(0, 0, UnityEngine.Random.Range(0f, 360f)) * Vector2.right) * UnityEngine.Random.Range(18f, 40f);
                    FxFactory.SpawnOwned(BelMoraFx.Brine, ModUtil.SafePoint(hero, hero + off), Src);
                }
        }

        internal static int LiveJacks()
        {
            int n = 0;
            foreach (var p in FindObjectsOfType<Player>())
            {
                if (p == null || !p.gameObject.name.StartsWith("ModJackMinion")) continue;
                var h = p.GetComponent<Health>();
                if (h != null && h.IsAlive()) n++;
            }
            return n;
        }

        /// <summary>The Wheel of Misfortune: knife rain, confetti bombs, or two Jack-in-the-Boxes.</summary>
        IEnumerator Misfortune(Vector2 hero)
        {
            if (JinxFx.Wheel != null) SystemPool.Spawn(JinxFx.Wheel, (Vector2)transform.position + new Vector2(0f, 40f));
            yield return new WaitForSeconds(0.8f);
            if (!Active) yield break;   // the boss died (or the fight ended) during the wind-up: nothing lands after victory
            hero = ModUtil.Hero() != null ? (Vector2)ModUtil.Hero().transform.position : hero;
            int roll = UnityEngine.Random.Range(0, 3);
            if (roll == 0 && JinxFx.KnifeRain != null)
            {
                for (int i = 0; i < 7; i++)
                {
                    var off = i == 0 ? Vector2.zero : (Vector2)(Quaternion.Euler(0, 0, i * 60f + UnityEngine.Random.Range(-15f, 15f)) * Vector2.right) * UnityEngine.Random.Range(14f, 30f);
                    FxFactory.SpawnOwned(JinxFx.KnifeRain, ModUtil.SafePoint(hero, hero + off), Src);
                    yield return new WaitForSeconds(0.1f);
                    if (!Active) yield break;
                }
            }
            else if (roll == 1 && JinxFx.ConfettiPop != null)
            {
                for (int i = 0; i < 5; i++)
                {
                    var off = (Vector2)(Quaternion.Euler(0, 0, i * 72f + 20f) * Vector2.right) * 26f;
                    FxFactory.SpawnOwned(JinxFx.ConfettiPop, ModUtil.SafePoint(hero, hero + off), Src);
                    yield return new WaitForSeconds(0.08f);
                    if (!Active) yield break;
                }
            }
            else if (JinxFx.JackSpawner != null && LiveJacks() < 4)   // same cap as Jinx's own wheel
            {
                // v0.10 sweep: on opposite sides of the hero at a random angle (they used to always land left and right)
                float a0 = UnityEngine.Random.Range(0f, 360f);
                for (int i = 0; i < 2; i++)
                {
                    var off = (Vector2)(Quaternion.Euler(0, 0, a0 + i * 180f) * Vector2.right) * 34f;
                    FxFactory.SpawnOwned(JinxFx.JackSpawner, ModUtil.SafePoint(hero, hero + off), null);
                }
            }
        }
    }
}
