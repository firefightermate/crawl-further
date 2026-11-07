using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Bloatfly, Bile Rain: it flies over the hero and retches straight down for 1.5 s while its player steers the stream;
    /// each retch splashes the floor under its mouth and leaves a bile puddle. Spoiled: a hero standing in its bile stays
    /// poisoned twice as long (<see cref="Spoiled"/>).
    /// </summary>
    public class BloatflyRain : SylveneBehaviour
    {
        const float MouthX = 8f, Approach = 220f, ApproachTime = 0.24f;

        /// <summary>Clip event: fly to the spot that puts its mouth over the hero.</summary>
        public void ModSylRainRise() { StartCoroutine(Over()); }

        IEnumerator Over()
        {
            float t = 0f;
            while (t < ApproachTime && Alive)
            {
                Vector2 want = HeroPos - new Vector2(MouthX * Side, 0f);
                var d = want - Me;
                if (d.magnitude < 3f) break;
                Push(Vector2.ClampMagnitude(d / Mathf.Max(0.05f, ApproachTime - t), Approach), 0.08f);
                t += Time.deltaTime;
                yield return null;
            }
        }

        /// <summary>Clip event (each stream frame): bile hits the floor under its mouth.</summary>
        public void ModSylRain()
        {
            if (!Alive) return;
            Vector2 at = Me + new Vector2(MouthX * Side, 0f);
            if (SylveneFx.BileHit != null) FxFactory.SpawnOwned(SylveneFx.BileHit, at, Own);
            if (SylveneFx.BilePuddle != null) SystemPool.Spawn(SylveneFx.BilePuddle, at + new Vector2(Random.Range(-2f, 2f), Random.Range(-1f, 1f)));
        }
    }
}
