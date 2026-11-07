using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Blight Bellows: its bladder bounces three times, puffing gas at each bounce, then bursts (<see cref="BladderFx"/>);
    /// Gas Lanes pumps three straight lanes of gas 60 x 10 px the way it faces, turning between pumps. Stale Air: its
    /// clouds and lanes last twice as long (built into the templates). Tell: thick, slow-curling fog.
    /// </summary>
    public class BellowsGas : SylveneBehaviour
    {
        public const int LaneTiles = 5;
        public const float TileStep = 12f;
        static readonly Vector2 Mouth = new Vector2(14f, 0f);

        /// <summary>Clip event: the bladder leaves its mouth for the hero's spot.</summary>
        public void ModSylLob()
        {
            if (!Alive || SylveneFx.Bladder == null) return;
            Vector2 from = ModUtil.SafePoint(Me, Me + new Vector2(Mouth.x * Side, Mouth.y), 3f);
            var go = SystemPool.Spawn(SylveneFx.Bladder, from);
            var b = go != null ? go.GetComponent<BladderFx>() : null;
            if (b != null) b.Throw(HeroPos, Own);
        }

        /// <summary>Clip event (each pump): a lane of gas along its facing.</summary>
        public void ModSylLane()
        {
            if (!Alive || SylveneFx.GasTile == null) return;
            var f = Face;
            for (int i = 0; i < LaneTiles; i++)
            {
                Vector2 at = Me + f * (10f + TileStep * i);
                if (!ModUtil.Clear(Me, at)) break;
                FxFactory.SpawnOwned(SylveneFx.GasTile, at, Own);
            }
        }
    }
}
