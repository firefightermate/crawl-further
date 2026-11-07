using System;

namespace CrawlFurther.Objects
{
    /// <summary>Who may use or trigger a room object.</summary>
    [Flags]
    public enum ObjUser { Hero = 1, Monster = 2, Ghost = 4, Living = Hero | Monster, Anyone = Hero | Monster | Ghost }
}
