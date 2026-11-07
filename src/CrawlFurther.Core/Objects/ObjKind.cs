namespace CrawlFurther.Objects
{
    /// <summary>How a room object is used.</summary>
    public enum ObjKind
    {
        /// <summary>The player presses action next to it (a fountain, a shrine).</summary>
        Use,
        /// <summary>It fires when a player walks onto it (a pad, a snare).</summary>
        Touch,
        /// <summary>A trap: a ghost steps in and fires it, bots use it, the vanilla aim and enter arrows show.</summary>
        Trap,
    }
}
