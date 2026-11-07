using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Carrion Roc, Airlift: it seizes the nearest Ossivar friend (or a bone pile) within <see cref="Grab"/> px, flies it at
    /// the hero for up to <see cref="Carry"/> s and drops it on him: the drop hits, a friend lands with a plate, a pile lands
    /// right by him. Drop Zone tell: the friend dangling from its talons and its shadow on the hero.
    /// </summary>
    public class RocAirlift : OssBehaviour
    {
        public const float Grab = 40f, Carry = 1.5f, Fly = 110f, Close = 10f;
        /// <summary>Set by the kit.</summary>
        public static exSpriteAnimClip CarryClip, DropClip;
        GameObject m_ally;
        BonePileFx m_pile;
        GameObject m_shadow;
        float m_t, m_grabAt;
        bool m_carrying;

        protected override void OnEnable() { base.OnEnable(); m_carrying = false; }
        protected override void OnDisable() { base.OnDisable(); Let(false); }

        /// <summary>Clip event (Grab frame 2): seize the nearest friend or pile.</summary>
        public void OssGrab()
        {
            if (!Alive) return;
            Let(false);   // a grab whose carry never came (the clip was cut short): let that one go first
            m_grabAt = Time.time;
            float best = Grab * Grab;
            foreach (var m in Object.FindObjectsOfType<OssivarMonster>())
            {
                if (m == null || m.gameObject == gameObject || !m.isActiveAndEnabled) continue;
                var h = m.GetComponent<Health>();
                if (h == null || !h.IsAlive() || m.GetComponent<RocAirlift>() != null) continue;
                float d = ((Vector2)m.transform.position - Me).sqrMagnitude;
                if (d < best) { best = d; m_ally = m.gameObject; }
            }
            if (m_ally == null)
            {
                m_pile = BonePileFx.Nearest(Me, Grab, p => !p.Locked);
                if (m_pile != null) m_pile.Locked = true;
            }
            if (m_ally != null)
            {
                var h = m_ally.GetComponent<Health>();
                if (h != null) h.StartInvincibility("ossroc");
                var p = m_ally.GetComponent<Player>();
                if (p != null) p.Stun(Carry + 0.5f, true);
            }
        }

        /// <summary>Clip event (end of Grab): fly the cargo at the hero, or give up if the talons came up empty.</summary>
        public void OssCarry()
        {
            if (!Alive || (m_ally == null && m_pile == null)) { SendMessage("AnimRun", SendMessageOptions.DontRequireReceiver); return; }
            m_carrying = true; m_t = 0f;
            Play(CarryClip);
            if (OssivarFx.DropShadow != null && Hero != null) m_shadow = ModAttach.Spawn(OssivarFx.DropShadow, Hero, Vector2.zero, -0.05f);
        }

        void Update()
        {
            if (!m_carrying)
            {
                // seized but never carried (the Grab clip was interrupted): never leave a friend invincible
                if ((m_ally != null || m_pile != null) && Time.time - m_grabAt > Carry + 0.5f) Let(false);
                return;
            }
            if (!Alive) { Let(false); return; }
            m_t += Time.deltaTime;
            Vector2 d = HeroPos - Me;
            if (d.sqrMagnitude > 1f) { Monster.FaceHero(); Slide(d.normalized * Mathf.Min(d.magnitude, Fly * Time.deltaTime)); }
            if (m_ally != null && m_ally.activeInHierarchy) ModUtil.Teleport(m_ally, Me + new Vector2(0f, -1f));
            else if (m_pile != null && m_pile.isActiveAndEnabled) m_pile.transform.position = new Vector3(Me.x, Me.y - 1f, m_pile.transform.position.z);
            if (d.magnitude < Close || m_t > Carry) Let(true);
        }

        /// <summary>Let go: on the hero (<paramref name="drop"/>) or just where it is (it died).</summary>
        void Let(bool drop)
        {
            if (!m_carrying && m_ally == null && m_pile == null) return;
            bool carried = m_carrying;
            m_carrying = false;
            if (m_shadow != null) { if (Hero != null) ModAttach.Drop(m_shadow, Hero); if (m_shadow.activeInHierarchy) SystemPool.Despawn(m_shadow); m_shadow = null; }
            Vector2 at = drop && Hero != null ? ModUtil.SafePoint(Me, HeroPos + new Vector2(Side * -4f, 0f), 4f) : Me;
            if (m_ally != null)
            {
                if (carried && m_ally.activeInHierarchy) ModUtil.Teleport(m_ally, at);
                var h = m_ally.GetComponent<Health>();
                if (h != null) h.StopInvincibility("ossroc");
                var mm = m_ally.GetComponent<ModMonster>();
                if (drop && mm != null) mm.ModGainPlates(1);
            }
            if (m_pile != null) { m_pile.Locked = false; if (carried && m_pile.isActiveAndEnabled) m_pile.transform.position = new Vector3(at.x, at.y, m_pile.transform.position.z); }
            if (drop && (m_ally != null || m_pile != null))
            {
                if (OssivarFx.RocDrop != null) FxFactory.SpawnOwned(OssivarFx.RocDrop, at, Own);
                if (Alive) Play(DropClip);
            }
            m_ally = null; m_pile = null;
        }
    }
}
