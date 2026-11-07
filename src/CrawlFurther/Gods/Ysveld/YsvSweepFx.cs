using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// The Winter Bride's Train Sweep: her train of snow swept through a half circle round her, from behind her over to in
    /// front (on either side of her), in 0.3 s. A hero within 40 px (the floor ellipse: 40 x 24) whom the sweep passes is
    /// hit once: 1.2, a pip and
    /// a shove outward. Spawned at her feet by the clip, owned by her; it reads her facing when it starts.
    /// </summary>
    public class YsvSweepFx : MonoBehaviour
    {
        public const float Radius = 40f, Squash = 0.6f, Time_ = 0.3f, Damage = 1.2f, Push = 160f;
        GameObject m_owner;
        float m_age, m_side;
        bool m_hit, m_started;

        void OnEnable() { m_age = 0f; m_hit = false; m_started = false; }

        void Update()
        {
            if (!m_started)
            {
                m_started = true;
                m_owner = YsvUtil.Owner(gameObject);
                var mv = m_owner != null ? m_owner.GetComponent<PlayerMovement>() : null;
                m_side = mv != null && mv.GetFaceDirection().x < 0f ? -1f : 1f;
                var art = YsveldFx.TrainSweepArt != null ? SystemPool.Spawn(YsveldFx.TrainSweepArt, transform.position) : null;
                if (art != null) art.transform.localScale = new Vector3(m_side, 1f, 1f);
            }
            m_age += Time.deltaTime;
            if (m_age > Time_ + 0.05f) { SystemPool.Despawn(gameObject); return; }
            if (m_hit || m_owner == null) return;
            var hero = YsvUtil.LiveHero();
            if (hero == null) return;
            Vector2 c = m_owner.transform.position;
            var d = (Vector2)hero.transform.position - c;
            if ((d.x * d.x) / (Radius * Radius) + (d.y * d.y) / (Radius * Radius * Squash * Squash) > 1f) return;
            // the train's angle, measured from straight behind her (0) over the top (90) to straight ahead (180)
            float swept = Mathf.Clamp01(m_age / Time_) * 180f;
            float heroAt = Mathf.Atan2(Mathf.Abs(d.y), -d.x * m_side) * Mathf.Rad2Deg;
            if (heroAt > swept) return;
            m_hit = true;
            var src = YsvUtil.Source(m_owner);
            YsvUtil.Hurt(hero, Damage, d, src, Push);
            YsvUtil.Rime(hero, src, YsvPips(m_owner), YsvPips(m_owner) > 1);
        }

        static int YsvPips(GameObject owner)
        {
            var q = owner != null ? owner.GetComponent<YsveldBehaviour>() : null;
            return q != null ? q.PipsPerHit : 1;
        }
    }
}
