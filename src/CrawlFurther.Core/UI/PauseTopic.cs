namespace CrawlFurther.UI
{
    /// <summary>
    /// One Pause > Tips topic: a tab header (up to 8 capitals), a short subtitle beside it and its paragraphs. Paragraphs
    /// are rich text (&lt;color=#d4be9c&gt;word&lt;/color&gt; highlights), wrapped at run time to pages of 7 lines; a paragraph
    /// starting with "- " is a bullet. <see cref="god"/> is the deity's name for a god's topic (the topics of the gods in
    /// the current game come first), empty otherwise. Add it with <see cref="TipRegistry.AddTopic"/>.
    /// </summary>
    public class PauseTopic
    {
        public readonly string id, god, header, subtitle;
        public readonly string[] paras;
        public PauseTopic(string id, string god, string header, string subtitle, string[] paras)
        { this.id = id; this.god = god; this.header = header; this.subtitle = subtitle; this.paras = paras; }
    }
}
