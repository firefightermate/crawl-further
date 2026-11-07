using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Tallow Sow, Greased: standing in unlit wax for <see cref="CoatTime"/> s coats her (a pale shine on her hide). The
    /// hero's shots glance off the coat for half damage (a spark where they skid off). Fire melts the coat at once.
    /// </summary>
    public class SowGreased : VhorrulBehaviour
    {
        public const float CoatTime = 1f, Glance = 0.5f;
        public static exSpriteAnimClip IdleCoat, RunCoat;
        float m_inWax;
        bool m_coated;

        protected override void OnEnable() { base.OnEnable(); m_inWax = 0f; m_coated = false; }

        void Update()
        {
            if (!Alive) return;
            if (m_coated) { if (FireNear(8f) != null) Coat(false); return; }
            m_inWax = InWax ? m_inWax + Time.deltaTime : 0f;
            if (m_inWax >= CoatTime) Coat(true);
        }

        void Coat(bool on)
        {
            m_coated = on;
            m_inWax = 0f;
            SetStance(on ? IdleCoat : null, on ? RunCoat : null);
        }

        public override float HeroHitScale(DamageInfo d)
        {
            if (!m_coated) return 1f;
            if (IsFire(d)) { Coat(false); return 1f; }
            if (!IsShot(d)) return 1f;
            if (VhorrulFx.Glance != null) SystemPool.Spawn(VhorrulFx.Glance, (Vector2)transform.position + new Vector2(0f, 6f));
            return Glance;
        }
    }
}
