using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Util;

    /// <summary>Snow Wraith, Cold Presence: a hero within 30 px of it gains a frost pip every second. Tell: a ring of
    /// frost creeping over the floor round it.</summary>
    public class WraithPresence : YsveldBehaviour
    {
        public const float Reach = 30f, Every = 1f;
        float m_tick;
        GameObject m_ring;

        protected override void OnEnable() { base.OnEnable(); m_tick = Every; }

        protected override void OnDisable() { base.OnDisable(); Drop(); }

        void Drop() { if (m_ring != null) { CrawlFurther.Monsters.ModAttach.Drop(m_ring, gameObject); m_ring = null; } }

        void Update()
        {
            if (!Alive) { Drop(); return; }
            if (m_ring == null && YsveldFx.ColdRing != null)
                m_ring = CrawlFurther.Monsters.ModAttach.Spawn(YsveldFx.ColdRing, gameObject, Vector2.zero, -2f);
            m_tick -= Time.deltaTime;
            if (m_tick > 0f) return;
            var hero = YsvUtil.LiveHero();
            if (hero == null) return;
            var d = (Vector2)hero.transform.position - Me;
            if ((d.x * d.x) + (d.y * d.y) / 0.25f > Reach * Reach) return;      // the ring is drawn 30 x 13.5: the same oval
            m_tick = Every;
            YsvUtil.Rime(hero, Own, 1, true);
        }
    }
}
