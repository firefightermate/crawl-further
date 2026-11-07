using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// A Candelabra flame. Crossing wax it lights the wax and splits in two, <see cref="Spread"/> degrees either side of
    /// its path, so one shot over a wax field becomes a spray (up to <see cref="MaxForks"/> splits deep).
    /// </summary>
    public class VhForkFx : MonoBehaviour
    {
        public const float Spread = 25f;
        public const int MaxForks = 2;
        /// <summary>How many times this flame's line has split already.</summary>
        public int generation;
        float m_t;

        public void Restart() { generation = 0; m_t = 0f; }

        void Update()
        {
            m_t -= Time.deltaTime;
            if (m_t > 0f) return;
            m_t = 0.04f;
            var w = WaxPuddleFx.Nearest(transform.position, 9f);
            if (w == null) return;
            var src = FxFactory.SourceOf(gameObject);
            w.Ignite(src);
            if (generation >= MaxForks || VhorrulFx.CandelabraFlame == null) return;
            var pm = GetComponent<ParticleMotion>();
            var dir = pm != null ? pm.GetDirection() : Vector2.right;
            float a = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg;
            if (VhorrulFx.Fork != null) FxFactory.SpawnOwned(VhorrulFx.Fork, transform.position, src, a);
            for (int s = -1; s <= 1; s += 2)
            {
                var child = FxFactory.SpawnOwned(VhorrulFx.CandelabraFlame, transform.position, src, a + s * Spread);
                var f = child != null ? child.GetComponent<VhForkFx>() : null;
                if (f != null) f.generation = generation + 1;
            }
            SystemPool.Despawn(gameObject);
        }
    }
}
