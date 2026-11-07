using System;

namespace CrawlFurther.Gods
{
    /// <summary>
    /// A full-panel editor opened from a silver or gold slot inside one player's god-select panel. Up to four panels sit
    /// side by side, so an editor must fit inside its own panel and read input only for its own player id.
    /// <see cref="SlotEditorUI"/> is a kit for building one.
    /// </summary>
    public interface ISlotEditor
    {
        bool IsOpen { get; }

        /// <summary>Open inside <paramref name="panel"/> for <paramref name="playerId"/>. Call onDone when the player
        /// confirms (the choice is already stored), onCancel when they back out (nothing changed).</summary>
        void Open(MenuDeitySelectPlayer panel, int playerId, SlotTier tier, Action onDone, Action onCancel);

        void Close();
    }
}
