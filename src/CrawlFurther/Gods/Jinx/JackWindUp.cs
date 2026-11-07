using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Jack-in-the-Box, Wound Up: standing still it cranks itself, one wind a second (up to three). Its next punch hits
    /// harder by <see cref="PerWind"/> a wind and knocks back further. Tell: gold music notes (one per wind) over the box,
    /// and the crank spins (the Wind idle).
    /// </summary>
    public class JackWindUp : JinxBehaviour
    {
        public const float PerWind = 0.2f, WindTime = 1f;
        public const int MaxWinds = 3;
        /// <summary>The idle shown while it is wound (set by the kit).</summary>
        public static exSpriteAnimClip WindIdle;

        int m_winds;
        float m_still;

        protected override void OnEnable() { base.OnEnable(); m_winds = 0; m_still = 0f; }

        void Update()
        {
            if (!Alive) return;
            bool still = Body.GetState() == Player.ePlayerState.Idle;
            m_still = still ? m_still + Time.deltaTime : 0f;
            if (m_winds < MaxWinds && m_still >= WindTime)
            {
                m_still = 0f;
                SetWinds(m_winds + 1);
            }
        }

        void SetWinds(int n)
        {
            m_winds = n;
            if (JinxFx.Wind != null) ModInd.Count(gameObject, JinxFx.Wind, n);
            SetStance(n > 0 ? WindIdle : null, null);
        }

        public override void OnAttackSpawned(GameObject fx, GameObject template)
        {
            if (template != JinxFx.JackPunch || m_winds <= 0) return;
            var d = fx.GetComponent<DamageEffect>();
            if (d != null)
            {
                R.Set(d, "m_damage", R.Get<float>(d, "m_damage") + PerWind * m_winds);
                R.Set(d, "m_knockbackMultiplier", R.Get<float>(d, "m_knockbackMultiplier") * (1f + 0.4f * m_winds));
            }
            SetWinds(0);
        }
    }
}
