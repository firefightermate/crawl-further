using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    /// <summary>
    /// Nightshade, Unseen: Shade Garden hides every pod within <see cref="Range"/> px of her for <see cref="Hidden"/> s
    /// and plants two more by the hero, hidden from the start. A hidden pod shows only as a faint purple shimmer, and
    /// only to a hero within 30 px (<see cref="SeedFx"/>).
    /// </summary>
    public class NightshadeGarden : SylveneBehaviour
    {
        public const float Range = 60f, Hidden = 6f;

        /// <summary>Clip event: the shade falls.</summary>
        public void ModSylShade()
        {
            if (!Alive) return;
            foreach (var s in SeedFx.Snapshot()) if (s != null && Near(s.Pos, Me, Range)) s.Hide(Hidden);
        }

        /// <summary>Clip event: two more pods by the hero, unseen.</summary>
        public void ModSylPlantTwo()
        {
            if (!Alive) return;
            var hero = HeroPos;
            float a = Random.Range(0f, 360f);
            for (int i = 0; i < 2; i++)
            {
                var off = (Vector2)(Quaternion.Euler(0, 0, a + i * 150f) * Vector2.right) * Random.Range(16f, 24f);
                var s = Orchard.Plant(SylveneFx.Seed, hero, hero + off, Own);
                if (s != null) s.Hide(Hidden);
            }
        }
    }
}
