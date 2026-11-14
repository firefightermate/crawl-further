using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Cordyceps Saint, Infest: three spore spines fanned at the hero. Each one that hits seeds stalks in him
    /// (<see cref="HeroStalks"/>): for <see cref="HeroStalks.Duration"/> s the fungus drags him toward the Saint, then the
    /// stalks fruit in a poison burst at his feet and a shambler walks off him. The cast also infects up to
    /// <see cref="MaxKin"/> Sylvene monsters within <see cref="Range"/> px (Fruiting Bodies: they fight on after death).
    /// </summary>
    public class CordycepsInfect : SylveneBehaviour
    {
        public const float Range = 60f;
        public const int MaxKin = 2;

        /// <summary>Clip event: the spines fly; nearby kin are infected.</summary>
        public void ModSylInfect()
        {
            if (!Alive) return;
            var kin = new List<Player>();
            foreach (var p in FindObjectsOfType<Player>())
                if (p != null && p.gameObject != gameObject && SylveneMonster.IsKin(p.gameObject) && Near(p.transform.position, Me, Range)) kin.Add(p);
            kin.Sort((a, b) => ((Vector2)a.transform.position - Me).sqrMagnitude.CompareTo(((Vector2)b.transform.position - Me).sqrMagnitude));
            for (int i = 0; i < kin.Count && i < MaxKin; i++) Infected.Infect(kin[i].gameObject, Own);
        }

        protected override void OnHitHero(DamageInfo d)
        {
            if (!Dealt(d).StartsWith("ModSylSporeSpine")) return;
            var hero = ModUtil.Hero();
            if (hero != null) HeroStalks.Seed(hero, this, Own);
        }
    }

    /// <summary>
    /// Stalks the Cordyceps Saint seeded in the hero: each spine adds one (up to three). While they grow the fungus drags
    /// him toward the Saint, harder with more stalks; after <see cref="Duration"/> s they fruit: a poison burst at his feet
    /// and one shambler that walks off him. Tell: orange stalks on his head.
    /// </summary>
    public class HeroStalks : MonoBehaviour
    {
        public const float Duration = 2.5f, Every = 0.2f, Drag = 26f;
        int m_stalks;
        float m_until, m_tick;
        CordycepsInfect m_saint;
        DamageSource m_src;

        /// <summary>Seed one more stalk in <paramref name="hero"/> (refreshes the timer).</summary>
        public static void Seed(GameObject hero, CordycepsInfect saint, DamageSource src)
        {
            var s = hero.GetComponent<HeroStalks>() ?? hero.AddComponent<HeroStalks>();
            if (!s.enabled || s.m_stalks == 0) { s.m_stalks = 0; s.m_until = Time.time + Duration; }
            s.m_stalks = Mathf.Min(3, s.m_stalks + 1);
            s.m_saint = saint;
            s.m_src = src;
            s.enabled = true;
            ModInd.Set(hero, SylveneFx.StalkInd, true, Duration + 0.2f);
        }

        void OnDisable() { m_stalks = 0; }

        void Update()
        {
            if (m_stalks == 0) { enabled = false; return; }
            var hp = GetComponent<Health>();
            if (hp != null && !hp.IsAlive()) { Stop(); return; }
            m_tick -= Time.deltaTime;
            if (m_tick <= 0f && m_saint != null && m_saint.Alive)
            {
                m_tick = Every;
                ModUtil.Pull(gameObject, m_saint.transform.position, Drag * (0.7f + 0.3f * m_stalks));
            }
            if (Time.time < m_until) return;
            Vector2 at = transform.position;
            if (SylveneFx.StalkBurst != null) FxFactory.SpawnOwned(SylveneFx.StalkBurst, at, m_src);
            if (SylveneFx.ShamblerSpawner != null) FxFactory.SpawnOwned(SylveneFx.ShamblerSpawner, at + new Vector2(m_stalks % 2 == 0 ? 10f : -10f, -2f), m_src);
            Stop();
        }

        void Stop()
        {
            m_stalks = 0;
            ModInd.Set(gameObject, SylveneFx.StalkInd, false);
            enabled = false;
        }
    }
}
