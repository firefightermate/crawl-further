using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Util;

    /// <summary>A House of Cards storm card: circles its owner at chest height, then flies at the hero.</summary>
    public class JinxOrbitCardFx : MonoBehaviour
    {
        public const float RadiusX = 20f, RadiusY = 8f, Height = 14f, Spin = 220f, Speed = 170f, FlyTime = 1.1f;
        Transform m_owner;
        Health m_ownerHealth;
        float m_angle, m_launchIn, m_fly;
        Vector2 m_dir;
        bool m_flying;

        public void Bind(Transform owner, Health h, float angle, float launchIn)
        {
            m_owner = owner; m_ownerHealth = h; m_angle = angle; m_launchIn = launchIn; m_flying = false; m_fly = 0f;
            Place();
        }

        void OnDisable() { m_owner = null; m_ownerHealth = null; m_flying = false; }

        void Place()
        {
            if (m_owner == null) return;
            float a = m_angle * Mathf.Deg2Rad;
            var p = m_owner.position;
            transform.position = new Vector3(p.x + RadiusX * Mathf.Cos(a), p.y + Height + RadiusY * Mathf.Sin(a), transform.position.z);
        }

        void Update()
        {
            if (m_flying)
            {
                m_fly += Time.deltaTime;
                var p = (Vector2)transform.position + m_dir * Speed * Time.deltaTime;
                transform.position = new Vector3(p.x, p.y, transform.position.z);
                if (m_fly > FlyTime) SystemPool.Despawn(gameObject);
                return;
            }
            if (m_owner == null) return;
            if (!m_owner.gameObject.activeInHierarchy || (m_ownerHealth != null && !m_ownerHealth.IsAlive()))
            {
                m_owner = null;
                SystemPool.Despawn(gameObject);
                return;
            }
            m_angle += Spin * Time.deltaTime;
            Place();
            m_launchIn -= Time.deltaTime;
            if (m_launchIn > 0f) return;
            var hero = ModUtil.Hero();
            Vector2 tgt = hero != null ? (Vector2)hero.transform.position + new Vector2(0f, 6f) : (Vector2)transform.position + Vector2.right;
            m_dir = tgt - (Vector2)transform.position;
            m_dir = m_dir.sqrMagnitude > 0.01f ? m_dir.normalized : Vector2.right;
            m_flying = true;
        }
    }
}
