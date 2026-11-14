using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    /// <summary>Spore Husk, Shake the Tree: the Groundbreaker (its third smash) bursts every ripe pod within <see cref="Range"/> px at
    /// once and throws two seeds out ahead.
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

        /// <summary>Clip event (the Groundbreaker): two seeds jump out of the cracks ahead of the club.</summary>
        public void ModSylHuskSow()
        {
            if (!Alive) return;
            var f = Face;
            var side = new Vector2(-f.y, f.x);
            foreach (float s in new[] { -1f, 1f })
                Orchard.Plant(SylveneFx.Seed, Me, Me + f * 30f + side * (14f * s), Own);
        }
    }
}
