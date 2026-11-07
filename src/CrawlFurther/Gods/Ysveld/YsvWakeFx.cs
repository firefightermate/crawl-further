using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>Frost Wake: rides along with the diving Silkmoth and lays a streak of ice behind it, a slab every 10 px of
    /// its path (at most five: 50 px), each with the white streak hardening into it.</summary>
    public class YsvWakeFx : MonoBehaviour
    {
        public const float Gap = 10f, Life = 0.45f;
        public const int Max = 5;
        Vector2 m_last;
        int m_laid;
        float m_age;
        bool m_started;

        void OnEnable() { m_started = false; m_laid = 0; m_age = 0f; }

        void Update()
        {
            Vector2 p = transform.position;
            if (!m_started) { m_started = true; m_last = p; Lay(p); return; }
            m_age += Time.deltaTime;
            if (m_age > Life || m_laid >= Max) return;
            if ((p - m_last).sqrMagnitude < Gap * Gap) return;
            m_last = p;
            Lay(p);
        }

        void Lay(Vector2 p)
        {
            m_laid++;
            YsvFloor.Lay(p, -1, YsvFloor.KitIceLife, 0);
            YsvUtil.Floor(YsveldFx.WakeStreak, p);
        }
    }
}
