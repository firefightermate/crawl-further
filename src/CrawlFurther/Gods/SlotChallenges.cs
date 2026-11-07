using System;

namespace CrawlFurther.Content.Gods
{
    using CrawlFurther.Gods;
    using CrawlFurther.UI;

    /// <summary>
    /// The six challenges that open the silver and gold slots of the origin, idol and ghost form pickers.
    /// Pace (a game is 4-6 floors; a hero kills roughly 40-90 monsters and fodder a game, a monster player evolves 5-8
    /// times, a ghost gathers 80-150 ectoplasm and the hero changes hands 4-10 times): each takes about 6 to 12 games of
    /// ordinary play, and none needs skill beyond playing.
    /// </summary>
    public static class SlotChallenges
    {
        public static void Register()
        {
            Add("Hero", SlotTier.Silver, "SLAYER", "Kill 400 monsters as the hero", Unlocks.StatHeroKills, 400, "SILVER ORIGIN");
            Add("Hero", SlotTier.Gold, "CHAMPION", "Win 5 games", Unlocks.StatWins, 5, "GOLD ORIGIN");
            Add("God", SlotTier.Silver, "SHEPHERD", "Evolve your monsters 60 times", Unlocks.StatEvolutions, 60, "SILVER IDOL");
            Add("God", SlotTier.Gold, "PANTHEON", "Evolve 20 different final forms", Unlocks.StatFinals, 20, "GOLD IDOL");
            Add("Ghost", SlotTier.Silver, "HAUNTER", "Gather 1000 ectoplasm as a ghost", Unlocks.StatEcto, 1000, "SILVER GHOST");
            Add("Ghost", SlotTier.Gold, "USURPER", "Slay the hero 40 times as a monster", Unlocks.StatHeroSlain, 40, "GOLD GHOST");
        }

        static void Add(string list, SlotTier tier, string title, string text, string stat, int target, string slot)
        {
            Unlocks.Add(new UnlockDef { id = Unlocks.IdFor(list, tier), title = title, text = text, stat = stat, target = target, slot = slot, tier = tier });
        }

        /// <summary>Every silver and gold slot has its challenge.</summary>
        public static void SelfCheck(Action<string> bad)
        {
            foreach (var list in new[] { "Hero", "God", "Ghost" })
                foreach (var t in new[] { SlotTier.Silver, SlotTier.Gold })
                    if (Unlocks.Find(Unlocks.IdFor(list, t)) == null) bad("Unlocks: no challenge " + Unlocks.IdFor(list, t));
        }
    }
}
