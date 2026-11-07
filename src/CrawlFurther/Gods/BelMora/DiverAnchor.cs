using UnityEngine;

namespace CrawlFurther.Content.Gods.BelMora
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Bell Diver, Dropped Anchor: a chain hook that misses bites into the floor where it stops and stays
    /// <see cref="Stay"/> s; the Diver hauls itself along the chain to it at <see cref="Speed"/> px/s, shoulder first,
    /// hitting anything in the way. Tell: the chain lies taut and dripping between them, and the porthole flares (Haul).
    /// </summary>
    public class DiverAnchor : BelBehaviour
    {
        public const float Stay = 3f, Speed = 120f, Arrive = 10f, HitEvery = 0.3f;
        /// <summary>The haul (set by the kit).</summary>
        public static exSpriteAnimClip HaulClip;

        GameObject m_hook, m_anchor;
        Vector2 m_hookAt, m_anchorAt;
        float m_haulLeft, m_hit;
        readonly BelLine m_chain = new BelLine();

        protected override void OnEnable() { base.OnEnable(); m_hook = null; m_anchor = null; m_haulLeft = 0f; }
        protected override void OnDisable() { base.OnDisable(); EndHaul(); }

        public override void OnAttackSpawned(GameObject fx, GameObject template)
        {
            if (template == BelMoraFx.Hook) { m_hook = fx; m_hookAt = fx.transform.position; }
        }

        void Update()
        {
            if (!Alive) { EndHaul(); return; }
            if (m_hook != null)
            {
                if (m_hook.activeInHierarchy) { m_hookAt = m_hook.transform.position; m_chain.Lay(BelMoraFx.ChainLink, Me + new Vector2(0f, 10f), m_hookAt, 3f); }
                else { m_hook = null; m_chain.Clear(); Landed(); }
            }
            if (m_haulLeft <= 0f) return;
            m_haulLeft -= Time.deltaTime;
            var d = m_anchorAt - Me;
            if (m_haulLeft <= 0f || d.sqrMagnitude < Arrive * Arrive || (m_anchor != null && !m_anchor.activeInHierarchy)) { EndHaul(); return; }
            var step = d.normalized * Mathf.Min(Speed * Time.deltaTime, d.magnitude);
            if (!ModUtil.Clear(Me, Me + step * 2f)) { EndHaul(); return; }
            ModUtil.Teleport(gameObject, Me + step);
            Monster.Face(m_anchorAt);
            m_chain.Lay(BelMoraFx.ChainLink, Me + new Vector2(0f, 10f), m_anchorAt + new Vector2(0f, 4f), 3f, sag: 0f);
            m_hit -= Time.deltaTime;
            if (m_hit <= 0f && BelMoraFx.AnchorShoulder != null)
            {
                m_hit = HitEvery;
                FxFactory.SpawnOwned(BelMoraFx.AnchorShoulder, Me + d.normalized * 8f, Own);
            }
        }

        // the hook is gone: if it did not reach the hero, it bit into the floor where it stopped
        void Landed()
        {
            var hero = ModUtil.Hero();
            if (hero != null && ((Vector2)hero.transform.position - m_hookAt).sqrMagnitude < 16f * 16f) return;
            if (BelMoraFx.AnchorBite == null || (m_hookAt - Me).sqrMagnitude < 30f * 30f) return;
            m_anchorAt = m_hookAt;
            m_anchor = FxFactory.SpawnOwned(BelMoraFx.AnchorBite, m_anchorAt, Own);
            m_haulLeft = Stay;
            m_hit = 0f;
            Hold(HaulClip, Stay);
        }

        void EndHaul()
        {
            if (m_haulLeft > 0f && Body != null && Alive) Body.Stun(0f, true);
            m_haulLeft = 0f;
            m_chain.Clear();
            if (m_anchor != null && m_anchor.activeInHierarchy && !SystemMain.GetDeloadInProgress()) SystemPool.Despawn(m_anchor);
            m_anchor = null;
        }
    }
}
