using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Art;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Bones crawl home: a pile drags itself to the nearest Ossivar monster within <see cref="Seek"/> px that can use it
    /// (<see cref="OssivarMonster.Wants"/>), which eats it on arrival. An Ossuary Priest calls piles from
    /// <see cref="ShepherdRange"/> px at double speed and keeps them waiting at its feet; a monster that wants a pile still
    /// takes it first. Wall-safe, at most <see cref="MaxCrawl"/> seconds of crawling per pile.
    /// </summary>
    public class OssBoneCrawlFx : MonoBehaviour
    {
        public const float Seek = 90f, ShepherdRange = 140f, Speed = 34f, MaxCrawl = 6f, Settle = 0.5f, Arrive = 3f, AtFeet = 12f;
        static readonly List<OssivarMonster> s_kin = new List<OssivarMonster>();
        static float s_kinAt = -1f;
        static exSpriteAnimClip s_crawl;

        BonePileFx m_pile;
        exSpriteAnimation m_anim;
        exSpriteAnimClip m_life;
        float m_lifeTime;
        Transform m_target;
        bool m_herd;
        float m_age, m_think, m_crawled;
        bool m_crawling;

        public void Restart() { m_age = 0f; m_think = 0f; m_crawled = 0f; m_target = null; m_crawling = false; }
        void OnEnable() { Restart(); }
        void OnDisable() { m_crawling = false; m_target = null; }

        static List<OssivarMonster> Kin()
        {
            if (Time.time - s_kinAt < 0.25f) return s_kin;
            s_kinAt = Time.time;
            s_kin.Clear();
            foreach (var m in Object.FindObjectsOfType<OssivarMonster>())
                if (m != null && m.isActiveAndEnabled) s_kin.Add(m);
            return s_kin;
        }

        static bool Shepherd(OssivarMonster m)
        {
            var mm = m.GetComponent<ModMonster>();
            var t = mm != null ? mm.Traits as OssivarTraits : null;
            var h = m.GetComponent<Health>();
            return t != null && t.shepherd && h != null && h.IsAlive();
        }

        void Pick()
        {
            Vector2 me = transform.position;
            m_target = null; m_herd = false;
            float best = Seek * Seek, herd = ShepherdRange * ShepherdRange;
            Transform priest = null;
            foreach (var m in Kin())
            {
                float d = ((Vector2)m.transform.position - me).sqrMagnitude;
                if (Shepherd(m))
                {
                    if (d < herd && d > AtFeet * AtFeet && ModUtil.Clear(me, m.transform.position)) { herd = d; priest = m.transform; }
                    continue;
                }
                if (d < best && m.Wants(m_pile) && ModUtil.Clear(me, m.transform.position)) { best = d; m_target = m.transform; }
            }
            if (m_target == null && priest != null) { m_target = priest; m_herd = true; }
        }

        void Update()
        {
            if (m_pile == null) m_pile = GetComponent<BonePileFx>();
            m_age += Time.deltaTime;
            if (m_age < Settle || m_pile == null || m_pile.Locked) { Stop(); return; }
            m_think -= Time.deltaTime;
            if (m_think <= 0f) { m_think = 0.25f; if (m_crawled < MaxCrawl) Pick(); else m_target = null; }
            if (m_target == null || !m_target.gameObject.activeInHierarchy) { Stop(); return; }
            Vector2 me = transform.position, to = (Vector2)m_target.position - me;
            float d = to.magnitude;
            if (d < (m_herd ? AtFeet : Arrive)) { Stop(); return; }
            float step = Mathf.Min(d, Speed * (m_herd ? 2f : 1f) * Time.deltaTime);
            if (!ModUtil.Clear(me, me + to / d * (step + 3f))) { m_crawled = MaxCrawl; Stop(); return; }
            Go();
            m_crawled += Time.deltaTime;
            Vector2 next = me + to / d * step;
            transform.position = new Vector3(next.x, next.y, transform.position.z);
        }

        void Go()
        {
            if (m_crawling) return;
            if (m_anim == null) m_anim = GetComponent<exSpriteAnimation>();
            if (m_anim == null) return;
            if (s_crawl == null)
            {
                var sh = SpriteSheets.Get("FxBonePile");
                if (sh == null || !sh.Has("Crawl")) return;
                s_crawl = new ClipBuilder(sh, "Crawl", "ModBonePileCrawl").Loop().Build();
            }
            var st = m_anim.GetCurrentAnimation();
            m_life = st != null ? st.clip : null;
            m_lifeTime = st != null ? st.time : 0f;   // the float overload: the int one reads frames and restarts the life
            m_anim.Play(s_crawl, 0);
            m_crawling = true;
        }

        void Stop()
        {
            if (!m_crawling) return;
            m_crawling = false;
            if (m_anim != null && m_life != null) m_anim.Play(m_life, m_lifeTime);   // the pile's own life carries on where it was
        }
    }
}
