using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    /// <summary>
    /// Rime Colossus, Downhill: on ice it can't be knocked back and its hits do +0.3 (basic 1, the heavier slam; its
    /// Glacier Run belly slide is always on its own fresh road). Tell: it leans forward and frost streams off it while it
    /// stands on ice (IdleIce / RunIce).
    /// </summary>
    public class ColossusDownhill : YsveldBehaviour
    {
        public static exSpriteAnimClip IceIdle, IceRun;
        bool m_on;

        protected override void OnEnable() { base.OnEnable(); m_on = false; }

        public override void OnHeroHit(DamageInfo d) { if (OnIce) d.m_knockbackMultiplier = 0f; }

        void Update()
        {
            bool on = Alive && OnIce;
            if (on == m_on) return;
            m_on = on;
            SetStance(on ? IceIdle : null, on ? IceRun : null);
            NextBasic(on ? 1 : 0);
        }
    }
}
