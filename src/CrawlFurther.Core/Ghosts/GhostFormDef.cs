namespace CrawlFurther.Ghosts
{
    using CrawlFurther.Gods;

    /// <summary>A ghost form players pick on the origin page: what a monster player is between bodies.</summary>
    public class GhostFormDef
    {
        /// <summary>Unique id ("Binder"); pause pages find a form's paragraph by ">id:&lt;".</summary>
        public string id;
        /// <summary>Name on the origin page.</summary>
        public string name;
        /// <summary>One line of mechanics, shown under the name.</summary>
        public string summary;
        /// <summary>Two short lines of flavour ("\n" between them).</summary>
        public string flavour;
        /// <summary>Portrait sheet (anim "Idle", 29 x 24).</summary>
        public string portraitArt;
        /// <summary>The in-game body sheet; null keeps the vanilla ghost.</summary>
        public string bodyArt;
        /// <summary>Normal, or a silver / gold "make your own" slot (always the last two entries).</summary>
        public SlotTier tier;
    }
}
