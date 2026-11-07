namespace CrawlFurther.Monsters
{
    /// <summary>Where a status overlay or indicator sits on the character carrying it.</summary>
    public enum OverlayAt
    {
        /// <summary>The cell's bottom-centre sits offsetY px above the top of the head (stacked with other head overlays).</summary>
        Head,
        /// <summary>The cell's bottom-centre sits offsetY px above the feet.</summary>
        Feet,
    }
}
