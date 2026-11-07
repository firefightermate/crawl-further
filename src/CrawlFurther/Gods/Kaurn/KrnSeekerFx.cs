using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Arc Lantern wisp: turns toward the hero (150 deg/s) for its first 1.1 s. Hanging Sparks: a wisp that reaches the end
    /// of its flight without hitting anything stops in the air and hangs there 3 s as an arc post (KaurnFx.HangingWisp).
    /// </summary>
    public class KrnSeekerFx : MonoBehaviour
    {
        public const float Turn = 150f, HomeTime = 1.1f, HangAt = 1.55f, HangHeight = 14f;
        float m_t;
        ParticleMotion m_m;

        public void Reset() { m_t = 0f; m_m = GetComponent<ParticleMotion>(); }
        void OnEnable() { Reset(); }

        void Update()
        {
            m_t += Time.deltaTime;
            if (m_t >= HangAt)
            {
                // drawn where it hangs: the post's ground point lies under it
                if (KaurnFx.HangingWisp != null)
                    FxFactory.SpawnOwned(KaurnFx.HangingWisp, (Vector2)transform.position - new Vector2(0f, HangHeight), FxFactory.SourceOf(gameObject));
                SystemPool.Despawn(gameObject);
                return;
            }
            if (m_t > HomeTime || m_m == null) return;
            var hero = ModUtil.Hero();
            if (hero == null) return;
            var dir = m_m.GetDirection();
            if (dir.sqrMagnitude < 0.01f) return;
            float cur = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg;
            float want = KaurnFx.Angle(transform.position, KaurnFx.HeroChest(hero));
            float a = Mathf.MoveTowardsAngle(cur, want, Turn * Time.deltaTime) * Mathf.Deg2Rad;
            m_m.SetDirection(new Vector2(Mathf.Cos(a), Mathf.Sin(a)));
            transform.rotation = Quaternion.Euler(0f, 0f, a * Mathf.Rad2Deg);
        }
    }
}
