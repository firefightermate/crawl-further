namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Jinx's monsters: every special draws a Wild Card (<see cref="JinxMonster.ModWildCard"/>), whose Diamonds can stack a
    /// second plate on top of their own one.
    /// </summary>
    public class JinxTraits : MonsterTraits
    {
        public JinxTraits()
        {
            maxPlates = 1;
            showPlateCount = true;
            Add<JinxMonster>();
        }
    }
}
