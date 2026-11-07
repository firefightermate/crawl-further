namespace CrawlFurther.Objects
{
    /// <summary>Where in a room the game may put an object (sets the vanilla SpawnConstraints).</summary>
    public enum ObjPlace
    {
        /// <summary>In the open, away from walls and doors, like the vanilla fountain.</summary>
        Open,
        /// <summary>Against a wall, like the vanilla turrets.</summary>
        Wall,
        Anywhere,
    }
}
