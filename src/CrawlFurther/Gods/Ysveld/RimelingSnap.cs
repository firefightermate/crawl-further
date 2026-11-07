using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Util;

    /// <summary>Rimeling, Cold Snap: its bite on a hero with 2 frost pips adds 2 (the bite template carries the rule,
    /// see <see cref="YsvRimeFx.coldSnap"/>). Tell: its fangs burn white while the hero has 2 pips (IdleSnap / RunSnap).</summary>
    public class RimelingSnap : YsveldBehaviour
    {
        public static exSpriteAnimClip SnapIdle, SnapRun;
        float m_check;

        void Update()
        {
            m_check -= Time.deltaTime;
            if (m_check > 0f) return;
            m_check = 0.1f;
            bool hot = Alive && YsvRime.On(ModUtil.Hero()) == 2;
            SetStance(hot ? SnapIdle : null, hot ? SnapRun : null);
        }
    }
}
