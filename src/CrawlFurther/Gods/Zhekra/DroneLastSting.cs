using UnityEngine;

namespace CrawlFurther.Content.Gods.Zhekra
{
    /// <summary>
    /// Brood Drone, Last Sting: below <see cref="Threshold"/> health its abdomen glows red and its dive hits twice as hard,
    /// and it dies at the end of that dive, its larva hatching where the hero stands. Tell: the red abdomen (IdleLast /
    /// RunLast), and the special becomes DiveLast.
    /// </summary>
    public class DroneLastSting : ZhkBehaviour
    {
        public const float Threshold = 1f;
        /// <summary>The glowing stance and the fatal dive (set by the kit).</summary>
        public static exSpriteAnimClip IdleLast, RunLast, DiveLast;

        bool m_last;

        protected override void OnEnable() { base.OnEnable(); m_last = false; }

        void Update()
        {
            bool last = Alive && Hp.GetHealthCurrent() < Threshold;
            if (last == m_last) return;
            m_last = last;
            SetStance(last ? IdleLast : null, last ? RunLast : null);
            SetSpecialClip(last ? DiveLast : null);
        }

        /// <summary>Clip event (the end of DiveLast): the sting tears out and the drone dies.</summary>
        public void ModZhkLastSting()
        {
            if (Alive) Hp.Suicide();
        }
    }
}
