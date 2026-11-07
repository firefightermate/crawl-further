using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    using CrawlFurther.Monsters;

    /// <summary>Briar Wyrm, Thorn Spiral: coiled and spinning for 1.5 s it throws <see cref="Volleys"/> pairs of thorns in a
    /// turning spiral (two arms, 12 thorns). Its mace (the kit) hits in front, then behind it (Both Ends).</summary>
    public class WyrmSpiral : SylveneBehaviour
    {
        public const int Volleys = 6;
        public const float Spin = 1.5f, Turn = 30f;

        /// <summary>Clip event: the spin starts.</summary>
        public void ModSylSpiral() { if (Alive) StartCoroutine(Spiral()); }

        IEnumerator Spiral()
        {
            float a = AngleTo(Me, HeroPos);
            Vector2 from = Me + new Vector2(0f, 10f);
            for (int v = 0; v < Volleys && Alive; v++)
            {
                if (SylveneFx.Thorn != null)
                {
                    FxFactory.SpawnOwned(SylveneFx.Thorn, from, Own, a);
                    FxFactory.SpawnOwned(SylveneFx.Thorn, from, Own, a + 180f);
                }
                a += Turn;
                yield return new WaitForSeconds(Spin / Volleys);
            }
        }
    }
}
