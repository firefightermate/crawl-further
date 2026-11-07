using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    /// <summary>Spore Husk, Shake the Tree: its club smash bursts every ripe pod within <see cref="Range"/> px at once.
    /// Tell: the floor rings round the club (FxSylShakeRing) and the pods shake for a beat before they go.</summary>
    public class HuskShake : SylveneBehaviour
    {
        public const float Range = 40f, Beat = 0.25f;

        /// <summary>Clip event on the smash frame.</summary>
        public void ModSylShake()
        {
            if (!Alive) return;
            foreach (var s in SeedFx.Snapshot())
                if (s != null && s.Ripe && Near(s.Pos, Me, Range)) s.ShakeLoose(Beat);
        }
    }
}
