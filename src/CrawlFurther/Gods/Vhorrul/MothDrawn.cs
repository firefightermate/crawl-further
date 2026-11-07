using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    /// <summary>
    /// Ash Moth, Drawn to the Flame: within <see cref="Range"/> px of any fire it flies <see cref="Haste"/>x faster, its
    /// wing edges glow (the glow stance) and its puffs carry embers that light wax (its second basic attack).
    /// </summary>
    public class MothDrawn : VhorrulBehaviour
    {
        public const float Range = 40f, Haste = 1.25f;
        public static exSpriteAnimClip IdleGlow, RunGlow;
        Attacks m_attacks;
        bool m_near;
        float m_t;

        protected override void Awake() { base.Awake(); m_attacks = Body != null ? CrawlFurther.Util.R.Get<Attacks>(Body, "m_playerAttacks") : null; }
        protected override void OnEnable() { base.OnEnable(); m_near = false; m_t = 0f; }

        void Update()
        {
            m_t -= Time.deltaTime;
            if (m_t > 0f || !Alive) return;
            m_t = 0.1f;
            bool near = FireNear(Range) != null;
            if (m_attacks != null) m_attacks.SetNextAttackOverride(near ? 1 : 0);
            if (near == m_near) return;
            m_near = near;
            SetStance(near ? IdleGlow : null, near ? RunGlow : null);
            SpeedScale(near ? Haste : 1f);
        }

        /// <summary>Clip event (the dive's wind-up): bend the dive toward the nearest flame ahead.</summary>
        public void VhAimAtFlame()
        {
            var f = IgniterFx.Nearest(Me, 70f, x => Vector2.Angle(Face, x.Pos - Me) < 50f);
            if (f != null) Monster.Face(f.Pos);
        }
    }
}
