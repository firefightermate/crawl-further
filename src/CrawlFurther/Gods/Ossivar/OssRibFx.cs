using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;

    /// <summary>One rib of the Ossuary's cage: a solid footprint laid along the ring (so the gaps stay too narrow to walk
    /// through) that stands <see cref="Life"/> s, or breaks at the first hit from the hero.</summary>
    public class OssRibFx : MonoBehaviour
    {
        public const float Life = 2.5f;
        GameObject m_body;
        exSpriteAnimation m_anim;
        float m_t;
        bool m_left, m_broken;

        public void Begin(bool left, float tangent)
        {
            m_left = left; m_t = 0f; m_broken = false;
            m_anim = GetComponent<exSpriteAnimation>();
            if (m_anim != null) m_anim.Play(left ? OssivarFx.RibRiseL : OssivarFx.RibRise, 0);
            m_body = OssFloor.Body(gameObject, 16f, 5f, 1f, tangent);
            m_body.SetActive(true);
            OssFloor.Hittable(gameObject, 8f, 18f, 9f);
        }

        void OnDisable() { if (m_body != null) m_body.SetActive(false); }

        void OnDamaged(DamageInfo d) { Break(); }

        void Break()
        {
            if (m_broken) return;
            m_broken = true; m_t = 0f;
            if (m_body != null) m_body.SetActive(false);
            if (m_anim != null) m_anim.Play(m_left ? OssivarFx.RibBreakL : OssivarFx.RibBreak, 0);
        }

        void Update()
        {
            m_t += Time.deltaTime;
            if (!m_broken)
            {
                if (m_t > 0.18f && m_anim != null && !m_anim.IsPlaying((m_left ? OssivarFx.RibStandL : OssivarFx.RibStand).name))
                    m_anim.Play(m_left ? OssivarFx.RibStandL : OssivarFx.RibStand, 0);
                if (m_t > Life) Break();
            }
            else if (m_t > 0.3f) SystemPool.Despawn(gameObject);
        }
    }
}
