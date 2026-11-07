namespace CrawlFurther.Content.Gods.BelMora
{
    using CrawlFurther.Monsters;

    /// <summary>Bel'Mora's monsters: they regenerate standing in brine.</summary>
    public class BelMoraTraits : MonsterTraits
    {
        public BelMoraTraits() { regenAt = BrineFx.HealsAt; }
    }
}
