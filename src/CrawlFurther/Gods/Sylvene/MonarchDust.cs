using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    /// <summary>
    /// Pollen Monarch, Dusted: a hero caught in its pollen storm is dusted for <see cref="DustTime"/> s, and pods burst for
    /// him from <see cref="Orchard.DustedRadius"/> px instead of 20. Tell: yellow dust on him. The storm also shakes
    /// four seeds down ahead of it.
    /// </summary>
    public class MonarchDust : SylveneBehaviour
    {
        public const float DustTime = 5f;

        protected override void OnHitHero(DamageInfo d)
        {
            if (Dealt(d).StartsWith("ModSylPollenCloud")) Orchard.Dust(DustTime);
        }

        /// <summary>Clip event: four seeds fall from the storm, spread ahead of it.</summary>
        public void ModSylStormSeeds()
        {
            if (!Alive) return;
            var f = Face;
            var side = new Vector2(-f.y, f.x);
            for (int i = 0; i < 4; i++)
            {
                Vector2 at = Me + f * (18f + 7f * i) + side * ((i % 2 == 0 ? -1f : 1f) * (6f + 3f * i));
                Orchard.Plant(SylveneFx.Seed, Me, at, Own);
            }
        }
    }
}
