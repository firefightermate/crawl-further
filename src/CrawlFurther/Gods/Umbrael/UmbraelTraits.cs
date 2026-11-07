namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Monsters;

    /// <summary>Umbrael's monsters: nearly invisible inside darkness, with <see cref="UmbraelMonster"/>'s clip events.</summary>
    public class UmbraelTraits : MonsterTraits
    {
        public UmbraelTraits()
        {
            hiddenAt = DarknessFx.Covers;
            Add<UmbraelMonster>();
        }
    }
}
