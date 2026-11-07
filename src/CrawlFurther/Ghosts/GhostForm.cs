namespace CrawlFurther.Content.Ghosts
{
    using CrawlFurther.Ghosts;

    /// <summary>Crawl: Further's ghost forms. Silver and Gold are the custom slots (the last two entries of
    /// GhostPack.Forms whatever their values; new forms go before them).</summary>
    public enum GhostForm
    {
        Wisp = 0, Gleaner = 1, Binder = 2, Poltergeist = 3,
        Banshee = 4, Sexton = 5, Kindler = 6, Mason = 7, Hexer = 8, Miser = 9,
        Silver = 100, Gold = 101
    }

    /// <summary>A ghost form def that knows its <see cref="GhostForm"/> (its id is the form's name).</summary>
    public class GhostFormEntry : GhostFormDef
    {
        GhostForm m_form;

        public GhostForm form
        {
            get { return m_form; }
            set { m_form = value; id = value.ToString(); }
        }
    }
}
