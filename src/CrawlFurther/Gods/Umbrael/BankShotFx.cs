using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Util;

    /// <summary>
    /// On a Glimmer shard, Bank Shot: once it has bounced off a wall it hits 50 % harder. Tell: it flashes white (the
    /// "Hot" anim) from the bounce on.
    /// </summary>
    public class BankShotFx : MonoBehaviour
    {
        public const float Bonus = 1.5f;
        ParticleMotion m_pm;
        DamageEffect m_de;
        Vector2 m_dir;
        float m_base;
        bool m_hot, m_init;

        void Awake() { m_pm = GetComponent<ParticleMotion>(); m_de = GetComponent<DamageEffect>(); }

        public void Arm() { m_init = false; m_hot = false; }

        void OnEnable() { Arm(); }

        void Update()
        {
            if (m_pm == null || m_hot) return;
            var v = m_pm.GetVelocity();
            if (v.sqrMagnitude < 1f) return;
            if (!m_init)
            {
                m_dir = v.normalized; m_init = true;
                if (m_de != null) m_base = R.Get<float>(m_de, "m_damage");
                return;
            }
            if (Vector2.Dot(m_dir, v.normalized) > 0.85f) { m_dir = v.normalized; return; }
            m_hot = true;
            if (m_de != null) R.Set(m_de, "m_damage", m_base * Bonus);
            var an = GetComponent<exSpriteAnimation>();
            var clip = UmbraelFx.ShardHot;
            if (an == null || clip == null) return;
            if (an.GetAnimation(clip.name) == null) an.AddAnimation(clip);
            an.Play(clip.name);
        }

        void OnDisable()
        {
            // pooled: put the cold damage and anim back for the next shard
            if (m_hot && m_de != null) R.Set(m_de, "m_damage", m_base);
            var an = GetComponent<exSpriteAnimation>();
            if (m_hot && an != null && an.defaultAnimation != null) an.Play(an.defaultAnimation.name);
            m_hot = false;
        }
    }
}
