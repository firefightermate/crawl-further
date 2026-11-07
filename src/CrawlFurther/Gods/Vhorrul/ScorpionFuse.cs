using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    using CrawlFurther.Monsters;

    /// <summary>Fuse Scorpion, Short Fuse: Light the Fuse stings the floor and starts a <see cref="VhFuseSparkFx"/>.</summary>
    public class ScorpionFuse : VhorrulBehaviour
    {
        public const float StingReach = 22f;

        /// <summary>Clip event (the sting lands).</summary>
        public void VhLightFuse()
        {
            if (Alive && VhorrulFx.FuseSpark != null) FxFactory.SpawnOwned(VhorrulFx.FuseSpark, Me + Face * StingReach, Own);
        }
    }
}
