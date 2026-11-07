namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// The god perk: an Ossivar monster eats a bone pile at its feet for a plate that blocks one hit
    /// (<see cref="OssivarMonster"/>), and piles crawl to the monsters that want them (<see cref="OssBoneCrawlFx"/>).
    /// The flags below are the few monsters that use piles their own way.
    /// </summary>
    public class OssivarTraits : MonsterTraits
    {
        /// <summary>Marrow Hound: below 3/4 health a pile heals half its health instead of giving a plate.</summary>
        public bool healOnBones;
        /// <summary>Ossuary Priest: draws piles from <see cref="OssBoneCrawlFx.ShepherdRange"/> px at double speed and keeps
        /// them at its feet for Raise instead of eating them.</summary>
        public bool shepherd;
        /// <summary>Carrion Saint: a pile becomes a perched crow instead of a plate.</summary>
        public bool pilesToCrows;

        public OssivarTraits()
        {
            maxPlates = 1;
            Add<OssivarMonster>();
        }
    }
}
