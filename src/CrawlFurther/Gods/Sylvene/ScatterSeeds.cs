using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    /// <summary>On a burst effect: on its first frame it scatters <see cref="count"/> seeds round itself, owned by its owner.</summary>
    public class ScatterSeeds : MonoBehaviour
    {
        public int count = 3;
        bool m_done;

        void OnEnable() { m_done = false; }

        void Update()
        {
            if (m_done) return;
            m_done = true;
            Vector2 at = transform.position;
            var src = CrawlFurther.Monsters.FxFactory.SourceOf(gameObject);
            float a0 = Random.Range(0f, 360f);
            for (int i = 0; i < count; i++)
            {
                var off = (Vector2)(Quaternion.Euler(0, 0, a0 + i * 360f / count) * Vector2.right) * Random.Range(9f, 14f);
                Orchard.Plant(SylveneFx.Seed, at, at + off, src);
            }
        }
    }
}
