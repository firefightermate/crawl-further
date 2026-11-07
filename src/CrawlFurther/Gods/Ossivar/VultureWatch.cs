using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Carrion Vulture. Death Watch: while the hero is below half health it flies <see cref="Faster"/> x as fast and its rake
    /// always bleeds (tell: its shadow circling round him). Plummet climbs out of sight (untouchable), marks the hero's spot
    /// with its shadow, then drops onto the mark.
    /// </summary>
    public class VultureWatch : OssBehaviour
    {
        public const float Faster = 1.25f, Below = 0.5f, Reach = 160f;
        bool m_watch;
        GameObject m_ring;
        Vector2 m_mark;
        float m_check;

        protected override void OnEnable() { base.OnEnable(); m_watch = false; m_check = 0f; }

        protected override void OnDisable()
        {
            base.OnDisable();
            DropRing();
            if (Hp != null) Hp.StopInvincibility("ossplummet");
        }

        void DropRing()
        {
            var h = Hero;
            if (m_ring != null) { if (h != null) ModAttach.Drop(m_ring, h); if (m_ring.activeInHierarchy) SystemPool.Despawn(m_ring); }
            m_ring = null;
        }

        void Update()
        {
            m_check -= Time.deltaTime;
            if (m_check > 0f) return;
            m_check = 0.2f;
            bool w = Alive && Hero != null && HeroHealth < Below;
            if (w == m_watch) return;
            m_watch = w;
            SpeedScale(w ? Faster : 1f);
            if (w && OssivarFx.WatchRing != null) m_ring = ModAttach.Spawn(OssivarFx.WatchRing, Hero, Vector2.zero, -0.05f);
            else DropRing();
        }

        public override void OnAttackSpawned(GameObject fx, GameObject template)
        {
            if (template != OssivarFx.VultureRake) return;
            var d = fx.GetComponent<DamageEffect>();
            if (d != null) R.Set(d, "m_statusChance", m_watch ? 1f : OssivarFx.RakeBleedChance);
        }

        /// <summary>Clip event (Plummet frame 2): gone into the sky; the shadow marks where it will land.</summary>
        public void OssPlummetUp()
        {
            if (!Alive) return;
            Vector2 d = HeroPos - Me;
            if (Hero == null) d = Face * 60f;
            if (d.sqrMagnitude > Reach * Reach) d = d.normalized * Reach;
            m_mark = ModUtil.SafePoint(Me, Me + d, 6f);
            if (Hp != null) Hp.StartInvincibility("ossplummet");
            if (OssivarFx.DiveShadow != null) SystemPool.Spawn(OssivarFx.DiveShadow, m_mark);
            StartCoroutine(Safety());
        }

        /// <summary>Clip event (Plummet frame 4): arrive over the mark.</summary>
        public void OssPlummetDown() { if (Alive) ModUtil.Teleport(gameObject, m_mark); }

        /// <summary>Clip event (Plummet frame 6): the impact; vulnerable again.</summary>
        public void OssPlummetLand() { if (Hp != null) Hp.StopInvincibility("ossplummet"); }

        IEnumerator Safety()
        {
            yield return new WaitForSeconds(1.2f);
            if (Hp != null) Hp.StopInvincibility("ossplummet");
        }
    }
}
