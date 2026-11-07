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
        float m_t;
        public void Reset() { m_t = 0f; }
        void OnEnable() { m_t = 0f; }

        void Update()
        {
            m_t += Time.deltaTime;
            if (m_t < SplitAt || KaurnFx.Shard == null) return;
            var m = GetComponent<ParticleMotion>();
            var dir = m != null ? m.GetDirection() : Vector2.right;
            float a = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg;
            var src = FxFactory.SourceOf(gameObject);
            for (int k = -1; k <= 1; k++) FxFactory.SpawnOwned(KaurnFx.Shard, transform.position, src, a + k * Fan);
            SystemPool.Despawn(gameObject);
        }
    }
}
