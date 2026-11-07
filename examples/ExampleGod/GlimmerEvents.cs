using BepInEx.Logging;
using CrawlFurther;

namespace ExampleGod
{
    /// <summary>
    /// Counts how often Glimmer monsters hit the hero in a run and logs it at the start of each floor. A use of
    /// <see cref="GameEvents"/>: no Harmony patch of our own is needed for these moments.
    /// </summary>
    public static class GlimmerEvents
    {
        static int s_hits;

        public static void Subscribe(ManualLogSource log)
        {
            GameEvents.RunStart += () => s_hits = 0;
            GameEvents.HeroDamaged += hit =>
            {
                var attacker = hit.m_source != null ? hit.m_source.m_sourceOwner : null;
                if (GlimmerPack.IsGlimmer(attacker)) s_hits++;
            };
            GameEvents.FloorStart += () => log.LogInfo("Glimmer monsters have hit the hero " + s_hits + " times this run");
        }
    }
}
