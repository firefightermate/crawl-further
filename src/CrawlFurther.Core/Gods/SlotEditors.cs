using System;

namespace CrawlFurther.Gods
{
    /// <summary>
    /// Which editor opens from each list's silver / gold slot. Each factory is called with the panel the editor must live
    /// in; return the same instance for the same panel if you cache. Left null, confirming the slot takes the stored
    /// choice without an editor.
    /// </summary>
    public static class SlotEditors
    {
        public static Func<MenuDeitySelectPlayer, ISlotEditor> God, Hero, Ghost;
    }
}
