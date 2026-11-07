using System;

namespace CrawlFurther.Objects
{
    /// <summary>The floor environments a spawn rule allows.</summary>
    [Flags]
    public enum ObjEnv { Dungeon = 1, Crypt = 2, Mines = 4, Caves = 8, Any = 15 }
}
