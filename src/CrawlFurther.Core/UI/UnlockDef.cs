namespace CrawlFurther.UI
{
    using CrawlFurther.Gods;

    /// <summary>
    /// An unlock challenge: done once the counter <see cref="stat"/> reaches <see cref="target"/>. Counters persist
    /// across games; Core counts the stats named in <see cref="Unlocks"/> (Stat...) and a mod can count its own with
    /// <see cref="Unlocks.Count"/>. Register it with <see cref="Unlocks.Add"/>. Text is plain words (no "[word]",
    /// none of % { | } ~ #).
    /// </summary>
    public class UnlockDef
    {
        /// <summary>Unique id. A silver or gold slot of a picker list uses <see cref="Unlocks.IdFor"/> ("HeroSilver").</summary>
        public string id;
        /// <summary>A short title in capitals ("SLAYER").</summary>
        public string title;
        /// <summary>One line of up to 40 characters: what to do ("Kill 400 monsters as the hero").</summary>
        public string text;
        /// <summary>The counter that is checked against <see cref="target"/>.</summary>
        public string stat;
        public int target;
        /// <summary>What it opens, shown on the banner as "&lt;slot&gt; UNLOCKED" ("SILVER ORIGIN").</summary>
        public string slot;
        /// <summary>The banner's colour.</summary>
        public SlotTier tier;
    }
}
