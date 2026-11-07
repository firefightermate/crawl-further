using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Glasswing, Glass Cocoon (her special, the YsvCocoon clip event): she shuts herself in glass for 2 s and can't move.
    /// Hits from the hero don't reach her: each one cracks the glass, and three cracks break it; she falls out stunned for
    /// 1.2 s. Hatch Healed: if the cocoon holds the 2 s she bursts out healed 2, and her next scythe (basic 1) hits double.
    /// Tell: the cracks on the cocoon (C0..C3) and the glow building inside; her scythes burn cyan while the double is
    /// ready (IdleKeen / RunKeen).
    /// </summary>
    public class GlasswingCocoon : YsveldBehaviour
    {
        public const float Time_ = 2f, Stun = 1.2f, Heal = 2f, CrackGap = 0.12f, Keen = 8f;
        public const int Cracks = 3;
        public static exSpriteAnimClip CurledClip, StunnedClip, KeenIdle, KeenRun;
        public static GameObject DoubleSlash;
        GameObject m_cocoon;
        float m_left, m_nextCrack, m_keen;
        int m_cracks;

        protected override void OnEnable() { base.OnEnable(); m_left = 0f; m_keen = 0f; m_cracks = 0; }

        protected override void OnDisable() { base.OnDisable(); Drop(); }

        bool Shut { get { return m_left > 0f; } }

        public void YsvCocoon()
        {
            if (!Alive) return;
            m_left = Time_; m_cracks = 0; m_nextCrack = 0f;
            Hold(CurledClip, Time_);
            if (YsveldFx.Cocoon != null) m_cocoon = ModAttach.Spawn(YsveldFx.Cocoon, gameObject, Vector2.zero, 0.05f);
        }

        void Drop() { if (m_cocoon != null) { ModAttach.Drop(m_cocoon, gameObject); m_cocoon = null; } m_left = 0f; }

        public override bool BlockHeroHit(DamageInfo d)
        {
            if (!Shut) return false;
            if (Time.time >= m_nextCrack)
            {
                m_nextCrack = Time.time + CrackGap;
                m_cracks++;
                if (m_cracks >= Cracks) { Break(); return true; }
                if (m_cocoon != null) YsvUtil.Play(m_cocoon, YsveldFx.CocoonCracks[m_cracks]);
                Show(YsveldFx.ShieldBlock, Me + new Vector2(0f, 12f));
            }
            return true;
        }

        void Break()
        {
            Drop();
            Show(YsveldFx.CocoonShatter, Me);
            Hold(StunnedClip, Stun);
        }

        void Hatch()
        {
            Drop();
            Show(YsveldFx.CocoonBurst, Me);
            Monster.Heal(Heal);
            m_keen = Keen;
            SetStance(KeenIdle, KeenRun);
            NextBasic(1);
        }

        public override void OnAttackSpawned(GameObject fx, GameObject template)
        {
            if (template != DoubleSlash || m_keen <= 0f) return;
            m_keen = 0f;
            SetStance(null, null);
            NextBasic(0);
        }

        void Update()
        {
            if (!Alive) { Drop(); return; }
            if (Shut)
            {
                m_left -= Time.deltaTime;
                if (m_left <= 0f) Hatch();
            }
            if (m_keen > 0f)
            {
                m_keen -= Time.deltaTime;
                if (m_keen <= 0f) { SetStance(null, null); NextBasic(0); }
            }
        }
    }
}
