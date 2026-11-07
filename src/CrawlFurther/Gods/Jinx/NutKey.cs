using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Nutcracker, Wind-up Key: every <see cref="RunDown"/> s its key runs down: it slows (the Slow idle and run, for the
    /// last <see cref="SlowTell"/> s), then freezes for <see cref="RewindTime"/> s to rewind itself, taking +50 % damage.
    /// Also its Crack: the jaws clamp in front, and a hero caught there is held for the second bite.
    /// </summary>
    public class NutKey : JinxBehaviour
    {
        public const float RunDown = 8f, SlowTell = 1.5f, RewindTime = 1.5f, RewindDamage = 1.5f;
        /// <summary>The run-down stance and the rewind (set by the kit).</summary>
        public static exSpriteAnimClip SlowIdle, SlowRun, RewindClip;

        float m_wound, m_rewindUntil;
        bool m_slow;
        GameObject m_grabbed;

        protected override void OnEnable() { base.OnEnable(); m_wound = 0f; m_rewindUntil = 0f; m_slow = false; m_grabbed = null; }

        void Update()
        {
            if (!Alive) return;
            if (m_rewindUntil > 0f)
            {
                if (Time.time < m_rewindUntil) return;
                m_rewindUntil = 0f;
                m_wound = 0f;
            }
            m_wound += Time.deltaTime;
            bool slow = m_wound >= RunDown - SlowTell;
            if (slow != m_slow) { m_slow = slow; SetStance(slow ? SlowIdle : null, slow ? SlowRun : null); }
            if (m_wound < RunDown || InAttack) return;
            m_slow = false;
            SetStance(null, null);
            m_rewindUntil = Time.time + RewindTime;
            Hold(RewindClip, RewindTime);
        }

        public override float HeroHitScale(DamageInfo d) { return m_rewindUntil > Time.time ? RewindDamage : 1f; }

        /// <summary>Clip event: the jaws clamp; a hero in front is held (rooted) for the bite.</summary>
        public void ModJinxCrackGrab()
        {
            m_grabbed = null;
            if (!Alive || JinxFx.Crunch == null) return;
            var f = Face;
            var hero = ModUtil.Hero();
            Vector2 jaw = ModUtil.SafePoint(Me, Me + f * 20f, 2f);
            if (hero != null)
            {
                var d = (Vector2)hero.transform.position - Me;
                float along = Vector2.Dot(d, f), across = Mathf.Abs(d.x * f.y - d.y * f.x);
                if (along >= -2f && along <= 30f && across <= 14f)
                {
                    m_grabbed = hero;
                    jaw = hero.transform.position;
                    var hp = hero.GetComponent<Player>();
                    if (ModStatus.Root != null && hp != null) hp.AddStatus(ModStatus.Root, Own, "jinxcrack");
                }
            }
            FxFactory.SpawnOwned(JinxFx.Crunch, jaw, Own);
        }

        /// <summary>Clip event: the second bite, on a hero still held.</summary>
        public void ModJinxCrackBite()
        {
            var h = m_grabbed;
            m_grabbed = null;
            if (h == null || !Alive || JinxFx.Crunch == null || !h.activeInHierarchy) return;
            if (((Vector2)h.transform.position - Me).sqrMagnitude > 36f * 36f) return;
            FxFactory.SpawnOwned(JinxFx.Crunch, h.transform.position, Own);
        }
    }
}
