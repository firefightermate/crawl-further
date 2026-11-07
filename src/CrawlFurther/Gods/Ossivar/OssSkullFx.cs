using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// The Rattlebones' skull on the floor: the hero can hit it (each hit lands on its owner), it chatters at a hero standing
    /// over it, and when called it rolls home along the floor, biting whatever it rolls through.
    /// </summary>
    public class OssSkullFx : MonoBehaviour
    {
        public const float ChatterRange = 10f, ChatterEvery = 0.6f, ChatterDamage = 0.3f, RollSpeed = 150f, RollDamage = 0.4f;
        RattleSkull m_owner;
        exSpriteAnimation m_anim;
        float m_next;
        bool m_rolling, m_bit;

        public void Bind(RattleSkull owner)
        {
            m_owner = owner; m_rolling = false; m_bit = false; m_next = Time.time + ChatterEvery;
            OssFloor.Hittable(gameObject, 10f, 8f, 4f);
            m_anim = GetComponent<exSpriteAnimation>();
            if (m_anim != null && OssivarFx.SkullChatter != null) m_anim.Play(OssivarFx.SkullChatter, 0);
        }

        void OnDisable() { m_owner = null; }

        void OnDamaged(DamageInfo d) { if (m_owner != null) m_owner.HitThroughSkull(d); }

        public void Recall()
        {
            if (m_rolling) return;
            m_rolling = true; m_bit = false;
            if (m_anim != null && OssivarFx.SkullRoll != null) m_anim.Play(OssivarFx.SkullRoll, 0);
        }

        /// <summary>Gone without rolling home (its owner fell apart or died).</summary>
        public void Vanish()
        {
            m_owner = null;
            if (OssivarFx.PlateShatter != null) SystemPool.Spawn(OssivarFx.PlateShatter, transform.position);
            if (gameObject.activeInHierarchy) SystemPool.Despawn(gameObject);
        }

        void Update()
        {
            if (m_owner == null || !m_owner.isActiveAndEnabled || !m_owner.Alive) { Vanish(); return; }
            Vector2 me = transform.position;
            var hero = ModUtil.Hero();
            Vector2 hp = hero != null ? (Vector2)hero.transform.position : new Vector2(9999f, 9999f);
            if (!m_rolling)
            {
                if (Time.time >= m_next && (hp - me).sqrMagnitude < ChatterRange * ChatterRange)
                {
                    m_next = Time.time + ChatterEvery;
                    m_owner.HurtHero(ChatterDamage);
                }
                return;
            }
            Vector2 to = m_owner.Neck - me;
            float d = to.magnitude;
            if (d < 6f) { var o = m_owner; m_owner = null; o.Home(); SystemPool.Despawn(gameObject); return; }
            Vector2 next = me + to / d * Mathf.Min(d, RollSpeed * Time.deltaTime);
            transform.position = new Vector3(next.x, next.y, transform.position.z);
            if (!m_bit && (hp - next).sqrMagnitude < 7f * 7f) { m_bit = true; m_owner.HurtHero(RollDamage, 0.3f); }
        }
    }
}
