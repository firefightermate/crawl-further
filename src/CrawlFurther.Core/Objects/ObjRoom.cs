using System;

namespace CrawlFurther.Objects
{
    /// <summary>Room kinds a spawn rule allows. A room is Fight (enemy spawners), Statue (monster statues), Corridor, or
    /// Quiet (none of those); Trapped is added when the game placed traps in it, Stairs when it holds the stairs.</summary>
    [Flags]
    public enum ObjRoom { Fight = 1, Quiet = 2, Corridor = 4, Statue = 8, Trapped = 16, Stairs = 32, Any = 63 }
}
