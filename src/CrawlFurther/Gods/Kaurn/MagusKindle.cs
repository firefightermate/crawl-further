using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Scarab Magus's Kindle: it opens its shell and lets go two slow balls of lightning that drift in straight lines past
    /// either side of the hero (30 px/s, 5 s). Moving Arcs: the balls are arc ends, joined to each other, the Magus and any
    /// rod near them, so the arcs sweep across the floor as they drift.
    /// </summary>
    public class MagusKindle : KaurnBehaviour
    {
        public const float Spread = 18f;

        /// <summary>Clip event: the balls leave the open shell.</summary>
        public void KrnKindle()
        {
            if (KaurnFx.KindleOrb == null) return;
            var from = Me + new Vector2(12f * Side, 4f);
            float a = KaurnFx.Angle(from, HeroPos);
            FxFactory.SpawnOwned(KaurnFx.KindleOrb, from + new Vector2(0f, 6f), Own, a + Spread);
            FxFactory.SpawnOwned(KaurnFx.KindleOrb, from - new Vector2(0f, 6f), Own, a - Spread);
        }
    }
}
