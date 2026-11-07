using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Util;

    /// <summary>Polarity Warg's Magnetize: a hero within <see cref="Reach"/> px is magnetized for 3 s (<see cref="KrnMagnet"/>).</summary>
    public class WargMagnetize : KaurnBehaviour
    {
        public const float Reach = 120f, Duration = 3f;

        /// <summary>Clip event: the mane flares.</summary>
        public void KrnMagnetize()
        {
            var hero = ModUtil.Hero();
            if (hero == null || ((Vector2)hero.transform.position - Me).sqrMagnitude > Reach * Reach) return;
            KrnMagnet.Begin(Duration, Own);
        }
    }
}
