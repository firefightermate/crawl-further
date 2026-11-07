using UnityEngine;

namespace CrawlFurther.Content.Gods.BelMora
{
    /// <summary>
    /// Barnacle Crab, Sidle: moving sideways (mostly up or down the screen while it faces left or right) it scuttles
    /// <see cref="Speed"/> times as fast, so it circles the hero. Tell: the legs blur sideways and kick up sand on both
    /// sides (the Sidle run).
    /// </summary>
    public class CrabSidle : BelBehaviour
    {
        public const float Speed = 1.4f;
        /// <summary>The run played while it sidles (set by the kit).</summary>
        public static exSpriteAnimClip SidleRun;

        bool m_side;

        protected override void OnEnable() { base.OnEnable(); m_side = false; }

        void Update()
        {
            if (!Alive || Move == null) return;
            var v = Move.GetVelocity();
            bool side = v.sqrMagnitude > 25f && Mathf.Abs(v.y) > Mathf.Abs(v.x) * 1.2f;
            if (side == m_side) return;
            m_side = side;
            SetStance(null, side ? SidleRun : null);
            SpeedScale(side ? Speed : 1f);
        }
    }
}
