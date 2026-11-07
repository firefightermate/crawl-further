using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Util;

    /// <summary>A Carrion Saint's sent crow: it turns a little toward the hero (<see cref="Turn"/> deg/s) on the way.</summary>
    public class OssCrowSeekFx : MonoBehaviour
    {
        public const float Turn = 70f;
        ParticleMotion m_m;
        void OnEnable() { m_m = GetComponent<ParticleMotion>(); }

        void Update()
        {
            var hero = ModUtil.Hero();
            if (hero == null || m_m == null) return;
            var dir = m_m.GetDirection();
            if (dir.sqrMagnitude < 0.01f) return;
            Vector2 to = (Vector2)hero.transform.position + new Vector2(0f, 5f) - (Vector2)transform.position;
            float cur = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg, want = Mathf.Atan2(to.y, to.x) * Mathf.Rad2Deg;
            float a = Mathf.MoveTowardsAngle(cur, want, Turn * Time.deltaTime) * Mathf.Deg2Rad;
            m_m.SetDirection(new Vector2(Mathf.Cos(a), Mathf.Sin(a)));
        }
    }
}
