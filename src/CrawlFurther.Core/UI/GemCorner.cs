namespace CrawlFurther.UI
{
    /// <summary>Which corner of a sprite <see cref="ModGem"/> marks.</summary>
    public enum GemCorner
    {
        /// <summary>The top-right of the frame's visible pixels (monsters, icons).</summary>
        Art,
        /// <summary>The top-right of the whole cell (framed portraits: gods, origins, ghost forms).</summary>
        Cell,
    }
}
