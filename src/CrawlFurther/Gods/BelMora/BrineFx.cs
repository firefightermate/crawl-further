using UnityEngine;

namespace CrawlFurther.Content.Gods.BelMora
{
    using CrawlFurther.Monsters;

    /// <summary>A brine pool. Slows the hero (its status zone); Bel'Mora monsters regenerate standing in it.</summary>
    public class BrineFx : Registered<BrineFx>
    {
        /// <summary>A brine pool within healing reach of <paramref name="p"/> (a regeneration test for MonsterTraits).</summary>
        public static bool HealsAt(Vector2 p) { return Nearest(p, 12f) != null; }
    }
}
