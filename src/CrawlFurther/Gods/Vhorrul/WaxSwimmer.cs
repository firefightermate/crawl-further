using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    /// <summary>
    /// Wickworm (and Candle Wyrm), Wax Swimmer: in unlit wax it sinks and swims, <see cref="SwimSpeed"/>x faster and
    /// unhittable, only its candle flames showing (the Swim stance). It surfaces to attack. Lit wax burns it out
    /// (<see cref="BurnOut"/> damage) and keeps it up for <see cref="Dry"/> s.
    /// </summary>
    public class WaxSwimmer : VhorrulBehaviour
    {
        public const float SwimSpeed = 1.4f, BurnOut = 0.5f, Dry = 1.5f, Resurface = 0.4f;
        const string Source = "VhSwim";
        /// <summary>The Wickworm's swim stance (set by its kit).</summary>
        public static exSpriteAnimClip SwimIdle, SwimRun;
        bool m_swimming;
        float m_wait;

        protected virtual exSpriteAnimClip SwimIdleClip { get { return SwimIdle; } }
        protected virtual exSpriteAnimClip SwimRunClip { get { return SwimRun; } }

        protected override void OnEnable() { base.OnEnable(); m_swimming = false; m_wait = 0f; }
        protected override void OnDisable() { Surface(); base.OnDisable(); }

        protected bool Swimming { get { return m_swimming; } }

        protected virtual void Update()
        {
            if (!Alive) { Surface(); return; }
            m_wait -= Time.deltaTime;
            if (m_swimming)
            {
                if (FireNear(7f) != null) { Surface(); HurtSelf(BurnOut); m_wait = Dry; return; }
                if (InAttack || !InWax) { Surface(); m_wait = Resurface; }
                return;
            }
            if (m_wait <= 0f && !InAttack && InWax && FireNear(10f) == null) Sink();
        }

        void Sink()
        {
            m_swimming = true;
            if (Hp != null) Hp.StartInvincibility(Source);
            SetStance(SwimIdleClip, SwimRunClip);
            SpeedScale(SwimSpeed);
            SendMessage("AnimShadowAlpha", 0f, SendMessageOptions.DontRequireReceiver);
        }

        protected void Surface()
        {
            if (!m_swimming) return;
            m_swimming = false;
            if (Hp != null) Hp.StopInvincibility(Source);
            SetStance(null, null);
            SpeedScale(1f);
            SendMessage("AnimShadowAlpha", 1f, SendMessageOptions.DontRequireReceiver);
        }
    }
}
