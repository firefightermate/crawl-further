using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>Snow Wraith maelstrom: while it spins, a hero within 42 px is dragged toward its centre; then it bursts.</summary>
    public class YsvVortexFx : MonoBehaviour
    {
        public const float Reach = 42f, Pull = 70f, Every = 0.1f;
        float m_tick;
        public void Arm() { m_tick = 0.25f; }
        void OnEnable() { Arm(); }

        void Update()
        {
            m_tick -= Time.deltaTime;
            if (m_tick > 0f) return;
            m_tick = Every;
            var hero = ModUtil.Hero();
            if (hero == null) return;
            var d = (Vector2)transform.position - (Vector2)hero.transform.position;
            if (d.sqrMagnitude > Reach * Reach) return;
            ModUtil.Pull(hero, transform.position, Pull);
        }
    }
}
