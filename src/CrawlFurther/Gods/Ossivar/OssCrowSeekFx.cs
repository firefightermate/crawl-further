using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Util;

    /// <summary>A Carrion Saint's crow: it turns a little toward the hero (<see cref="turn"/> deg/s) on the way. A sent crow
    /// turns 70; Murder's crows turn 45, so the flock bends in without all landing on one spot.</summary>
    public class OssCrowSeekFx : MonoBehaviour
    {
        public float turn = 70f;
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
            float a = Mathf.MoveTowardsAngle(cur, want, turn * Time.deltaTime) * Mathf.Deg2Rad;
            m_m.SetDirection(new Vector2(Mathf.Cos(a), Mathf.Sin(a)));
        }
    }
}
