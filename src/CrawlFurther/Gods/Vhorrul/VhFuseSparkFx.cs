using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// A Fuse Scorpion's spark: it runs along the exact path the hero has walked since the sting, at
    /// <see cref="SpeedOfHero"/> times his walking speed, lighting wax as it passes (each pool it lights makes it
    /// <see cref="PerPool"/> faster) and leaving a smoking line. Catching him it bursts; it burns out after
    /// <see cref="Life"/> s.
    /// </summary>
    public class VhFuseSparkFx : MonoBehaviour
    {
        public const float SpeedOfHero = 1.5f, PerPool = 0.2f, Life = 4f, Catch = 6f, SmokeEvery = 6f;

        VhHeroTrail m_trail;
        int m_next;
        float m_t, m_speed, m_smoke;
        bool m_running;
        DamageSource m_src;

        public void Restart() { if (m_running && m_trail != null) m_trail.End(); m_running = false; m_trail = null; }
        void OnDisable() { Restart(); }

        void Begin()
        {
            var hero = ModUtil.Hero();
            m_trail = VhHeroTrail.On(hero);
            if (m_trail == null) { SystemPool.Despawn(gameObject); return; }
            m_next = m_trail.Begin();
            m_src = FxFactory.SourceOf(gameObject);
            var mv = hero.GetComponent<PlayerMovement>();
            float walk = mv != null ? R.Get<float>(mv, "m_speedMax") : 80f;
            m_speed = SpeedOfHero * Mathf.Clamp(walk, 50f, 140f);
            m_t = 0f; m_smoke = 0f;
            m_running = true;
        }

        void Update()
        {
            if (!m_running) { Begin(); if (!m_running) return; }
            m_t += Time.deltaTime;
            var hero = ModUtil.Hero();
            if (m_t > Life || hero == null) { SystemPool.Despawn(gameObject); return; }
            float budget = m_speed * Time.deltaTime;
            Vector2 p = transform.position;
            while (budget > 0f)
            {
                var target = m_next <= m_trail.Last ? m_trail.At(m_next) : (Vector2)hero.transform.position;
                var d = target - p;
                float len = d.magnitude;
                if (len <= budget) { p = target; budget -= len; if (m_next <= m_trail.Last) m_next++; else break; }
                else { p += d / len * budget; budget = 0f; }
            }
            m_smoke += (p - (Vector2)transform.position).magnitude;
            transform.position = new Vector3(p.x, p.y, transform.position.z);
            if (m_smoke >= SmokeEvery && VhorrulFx.FuseSmoke != null) { m_smoke = 0f; FxFactory.SpawnOwned(VhorrulFx.FuseSmoke, p, m_src); }
            var w = WaxPuddleFx.Nearest(p, 10f);
            if (w != null) { w.Ignite(m_src); m_speed *= 1f + PerPool; }
            if (((Vector2)hero.transform.position - p).sqrMagnitude < Catch * Catch)
            {
                if (VhorrulFx.FuseBlast != null) FxFactory.SpawnOwned(VhorrulFx.FuseBlast, p, m_src);
                SystemPool.Despawn(gameObject);
            }
        }
    }
}
