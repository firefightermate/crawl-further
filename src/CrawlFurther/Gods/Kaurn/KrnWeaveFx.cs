using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>Static Moth dart: weaves side to side (5 px, 2.2 times a second) as it flies; pairs weave in opposite phase.</summary>
    public class KrnWeaveFx : MonoBehaviour
    {
        public const float Amp = 5f, Freq = 2.2f;
        static int s_flip;
        float m_t, m_last, m_sign = 1f;
        ParticleMotion m_m;
        public void Reset() { m_t = 0f; m_last = 0f; m_sign = (s_flip++ % 2 == 0) ? 1f : -1f; m_m = GetComponent<ParticleMotion>(); }

        void Update()
        {
            m_t += Time.deltaTime;
            var dir = m_m != null ? m_m.GetDirection() : Vector2.right;
            if (dir.sqrMagnitude < 0.01f) return;
            var perp = new Vector2(-dir.y, dir.x).normalized;
            float off = Mathf.Sin(m_t * Freq * 2f * Mathf.PI) * Amp * m_sign;
            var p = (Vector2)transform.position + perp * (off - m_last);
            m_last = off;
            transform.position = new Vector3(p.x, p.y, transform.position.z);
        }
    }
}
