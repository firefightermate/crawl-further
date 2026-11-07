using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>Ice Lens: a Prism Oracle bolt crossing ice bends toward the hero and flashes white (the Lens clip).</summary>
    public class YsvLensFx : MonoBehaviour
    {
        public const float Turn = 260f;
        ParticleMotion m_motion;
        bool m_lens;

        void Awake() { m_motion = GetComponent<ParticleMotion>(); }
        void OnEnable() { m_lens = false; }

        void Update()
        {
            if (m_motion == null) return;
            Vector2 p = transform.position;
            bool on = YsvFloor.Count > 0 && YsvFloor.Covers(p - new Vector2(0f, 6f));
            if (on != m_lens) { m_lens = on; YsvUtil.Play(gameObject, on ? YsveldFx.LensClip : YsveldFx.PrismClip); }
            if (!on) return;
            var hero = ModUtil.Hero();
            var v = m_motion.GetVelocity();
            if (hero == null || v.sqrMagnitude < 1f) return;
            var to = (Vector2)hero.transform.position + new Vector2(0f, 8f) - p;
            float a = Mathf.Atan2(v.y, v.x) * Mathf.Rad2Deg;
            float b = Mathf.MoveTowardsAngle(a, Mathf.Atan2(to.y, to.x) * Mathf.Rad2Deg, Turn * Time.deltaTime) * Mathf.Deg2Rad;
            m_motion.SetDirection(new Vector2(Mathf.Cos(b), Mathf.Sin(b)));
        }
    }
}
