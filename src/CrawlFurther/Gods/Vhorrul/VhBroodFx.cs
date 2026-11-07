using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    using CrawlFurther.Monsters;

    /// <summary>A dying Grub Mother lets her brood loose: three grublings round the body.</summary>
    public class VhBroodFx : MonoBehaviour
    {
        public const int Count = 3;
        bool m_done;

        public void Restart() { m_done = false; }

        void Update()
        {
            if (m_done || VhorrulFx.Grubling == null) return;
            var src = FxFactory.SourceOf(gameObject);
            if (src == null) return;
            m_done = true;
            for (int i = 0; i < Count; i++)
            {
                float a = (i * 120f + 30f) * Mathf.Deg2Rad;
                FxFactory.SpawnOwned(VhorrulFx.Grubling, (Vector2)transform.position + new Vector2(Mathf.Cos(a) * 9f, Mathf.Sin(a) * 5f), src);
            }
        }
    }
}
