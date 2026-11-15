using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>Scarab Magus orb: after 0.38 s of flight it bursts into three shards fanned 22 degrees apart.</summary>
    public class KrnSplitFx : MonoBehaviour
    {
        public const float SplitAt = 0.38f, Fan = 22f;
        /// <summary>Shards it splits into and the angle between them (the Scarab Magus's Sunburst: a full ring).</summary>
        public int count = 3;
        public float fan = Fan;
        float m_t;
        public void Reset() { m_t = 0f; count = 3; fan = Fan; }
        void OnEnable() { m_t = 0f; }

        void Update()
        {
            m_t += Time.deltaTime;
            if (m_t < SplitAt || KaurnFx.Shard == null) return;
            var m = GetComponent<ParticleMotion>();
            var dir = m != null ? m.GetDirection() : Vector2.right;
            float a = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg;
            var src = FxFactory.SourceOf(gameObject);
            for (int k = 0; k < count; k++) FxFactory.SpawnOwned(KaurnFx.Shard, transform.position, src, a + (k - (count - 1) * 0.5f) * fan);
            SystemPool.Despawn(gameObject);
        }
    }
}
