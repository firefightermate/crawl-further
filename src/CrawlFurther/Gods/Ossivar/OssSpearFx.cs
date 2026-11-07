using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>A Bone Lancer's spear standing in the floor: a small solid footprint that pricks the hero who runs into it
    /// (<see cref="Prick"/> and a bleed, at most once a second), then crumbles into a bone pile.</summary>
    public class OssSpearFx : MonoBehaviour
    {
        public const float Life = 5f, Prick = 0.3f, Touch = 7f;
        GameObject m_body;
        DamageSource m_src;
        exSpriteAnimation m_anim;
        float m_t, m_pricked;
        bool m_solid, m_falling;

        public void Begin(DamageSource src)
        {
            m_src = src; m_t = 0f; m_pricked = -9f; m_solid = false; m_falling = false;
            m_body = OssFloor.Body(gameObject, 5f, 3f);
            m_anim = GetComponent<exSpriteAnimation>();
        }

        void OnDisable() { if (m_body != null) m_body.SetActive(false); m_solid = false; }

        void Update()
        {
            m_t += Time.deltaTime;
            Vector2 me = transform.position;
            if (m_falling)
            {
                if (m_t > 0.45f) { OssFloor.DropPile(me, me, m_src); SystemPool.Despawn(gameObject); }
                return;
            }
            if (m_t > Life)
            {
                m_falling = true; m_t = 0f;
                if (m_body != null) m_body.SetActive(false);
                if (m_anim != null && OssivarFx.SpearCrumble != null) m_anim.Play(OssivarFx.SpearCrumble, 0);
                return;
            }
            if (!m_solid && !OssFloor.Occupied(me, 5f, 4f)) { m_solid = true; if (m_body != null) m_body.SetActive(true); }
            var hero = ModUtil.Hero();
            if (hero == null || Time.time - m_pricked < 1f) return;
            Vector2 d = (Vector2)hero.transform.position - me;
            if (d.sqrMagnitude > Touch * Touch) return;
            m_pricked = Time.time;
            var hh = hero.GetComponent<Health>();
            if (hh != null && hh.IsAlive())
                hh.Damage(new DamageInfo(Prick, 0.6f, 0f, d.sqrMagnitude > 0.01f ? d.normalized : Vector2.up, m_src), false);
            var hp = hero.GetComponent<Player>();
            var bleed = FxFactory.GetStatus("StatusBleeding");
            if (hp != null && bleed != null) hp.AddStatus(bleed, m_src, "ossspear");
        }
    }
}
