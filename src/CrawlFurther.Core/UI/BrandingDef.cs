namespace CrawlFurther.UI
{
    /// <summary>A mod's branding on the game's menus (see <see cref="Branding.Set"/>). Every sheet is optional.</summary>
    public class BrandingDef
    {
        /// <summary>The mod's name and version, shown together on the title screen ("Crawl: Further 1.0.0").</summary>
        public string name, version;
        /// <summary>The wordmark next to every CRAWL logo: a sheet with Idle (loop), In (plays once as it appears), Glitch
        /// (while the logo glitches) and Out. Cells of 76 x 28 sit where they read from the logo's bottom right.</summary>
        public string wordmark;
        /// <summary>A small ember that now and then drifts up off the wordmark: anim Rise.</summary>
        public string spark;
        /// <summary>A flame pip burning either side of the selected main menu item: anim Burn (loop).</summary>
        public string menuPip;
        /// <summary>Dust and embers drifting up behind the title: anims Dust1-3 and Ember1-3 (small to large).</summary>
        public string menuMote;
    }
}
