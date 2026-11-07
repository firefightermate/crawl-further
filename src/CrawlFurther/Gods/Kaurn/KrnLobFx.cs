using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Something lobbed (a Fuse Sapper canister or charge, a Forgemaster rod): it arcs from where it was thrown to its
    /// <see cref="target"/> (default: where the hero stood, at most 130 px) in <see cref="time"/> seconds, then spawns
    /// <see cref="land"/> and <see cref="land2"/> there, owned by its thrower.
    /// </summary>
    public class KrnLobFx : MonoBehaviour
    {
        public const float MaxRange = 130f, Height = 18f;
        public float time = 0.6f;
        public Vector2? target;
        public GameObject land, land2;
        float m_t;
        bool m_init;
        Vector2 m_from, m_to;

        public void Reset() { m_t = 0f; m_init = false; target = null; land = land2 = null; time = 0.6f; }

        void Update()
        {
            if (!m_init)
            {
                m_init = true;
                m_from = transform.position;
                var hero = ModUtil.Hero();
                var to = target ?? (hero != null ? (Vector2)hero.transform.position : m_from + Vector2.right * 60f);
                var d = to - m_from;
                if (d.magnitude > MaxRange) to = m_from + d.normalized * MaxRange;
                m_to = ModUtil.SafePoint(m_from, to, 4f);
            }
            m_t += Time.deltaTime;
            float k = Mathf.Clamp01(m_t / time);
            var p = Vector2.Lerp(m_from, m_to, k) + new Vector2(0f, Mathf.Sin(k * Mathf.PI) * Height);
            transform.position = new Vector3(p.x, p.y, transform.position.z);
            if (m_t < time) return;
            var src = FxFactory.SourceOf(gameObject);
            if (land != null) FxFactory.SpawnOwned(land, m_to, src);
            if (land2 != null) FxFactory.SpawnOwned(land2, m_to, src);
            SystemPool.Despawn(gameObject);
        }
    }
}
