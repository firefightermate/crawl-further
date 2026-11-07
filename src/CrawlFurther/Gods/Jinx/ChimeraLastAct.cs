using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Big-Top Chimera, Last Act: below half health its mane catches fire for good, and every <see cref="Stride"/> px it
    /// runs it leaves a burning pawprint (0.5 a second for 2 s). Tell: the flaming mane (the Burn idle and run) and the prints.
    /// </summary>
    public class ChimeraLastAct : JinxBehaviour
    {
        public const float Stride = 18f;
        /// <summary>The burning stance (set by the kit).</summary>
        public static exSpriteAnimClip BurnIdle, BurnRun;

        bool m_burning;
        Vector2 m_last;
        float m_walked;

        protected override void OnEnable() { base.OnEnable(); m_burning = false; m_walked = 0f; }

        void Update()
        {
            if (!Alive || Hp == null) return;
            if (!m_burning)
            {
                if (Hp.GetHealthCurrent() >= Hp.GetHealthMax() * 0.5f) return;
                m_burning = true;
                m_last = Me;
                SetStance(BurnIdle, BurnRun);
            }
            m_walked += (Me - m_last).magnitude;
            m_last = Me;
            if (m_walked < Stride || JinxFx.Pawprint == null) return;
            m_walked = 0f;
            FxFactory.SpawnOwned(JinxFx.Pawprint, Me, Own);
        }
    }
}
