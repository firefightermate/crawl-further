using UnityEngine;

namespace CrawlFurther.Content.Gods.Zhekra
{
    using CrawlFurther.Monsters;

    /// <summary>Acid Bloater bubble pop: a ring of droplets from where the bubble burst (owned by whoever blew it).</summary>
    public class ZhkRingFx : MonoBehaviour
    {
        public GameObject projectile;
        public int count = 6;
        bool m_done;

        void OnEnable() { m_done = false; }

        void Update()
        {
            if (m_done || projectile == null) return;
            m_done = true;
            var src = FxFactory.SourceOf(gameObject);
            float start = Random.Range(0f, 360f);
            for (int i = 0; i < count; i++) FxFactory.SpawnOwned(projectile, transform.position, src, start + i * 360f / count);
        }
    }
}
