using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Ossuary Priest. Shepherd (the shepherd trait, run by <see cref="OssBoneCrawlFx"/>): piles crawl to it from 140 px,
    /// twice as fast, and wait at its feet. Raise: every pile within <see cref="Range"/> px stands up as a Bone Rat (at most
    /// four); with none, one rat crawls out of its robes.
    /// </summary>
    public class PriestRaise : OssBehaviour
    {
        public const float Range = 80f;
        public const int MaxRats = 4;

        /// <summary>Clip event (Raise frame 5).</summary>
        public void OssRaise()
        {
            if (!Alive || OssivarFx.RatSpawner == null) return;
            int n = 0;
            foreach (var p in BonePileFx.Snapshot())
            {
                if (p == null || p.Locked || n >= MaxRats || (p.Pos - Me).sqrMagnitude > Range * Range) continue;
                FxFactory.SpawnOwned(OssivarFx.RatSpawner, p.Pos, Own);
                p.Consume();
                n++;
            }
            if (n == 0)
                FxFactory.SpawnOwned(OssivarFx.RatSpawner, ModUtil.SafePoint(Me, Me + new Vector2(Side * 12f, -4f)), Own);
        }
    }
}
