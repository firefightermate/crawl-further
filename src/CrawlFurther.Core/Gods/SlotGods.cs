using System;
using System.Collections.Generic;

namespace CrawlFurther.Gods
{
    /// <summary>
    /// Hooks for slot gods: gods a player builds in a silver or gold entry at the end of the god list, taking another
    /// god's perk (Crawl: Further calls them idols). The mod that owns the slots fills these from its start callback;
    /// each is optional.
    /// </summary>
    public static class SlotGods
    {
        /// <summary>After vanilla built a panel's god list: append your slot entries here (they stay after Trials).</summary>
        public static Action<MenuDeitySelectPlayer, MenuTextMenu> AddEntries;

        /// <summary>A slot editor opened over a panel: hide what you drew on it.</summary>
        public static Action<MenuDeitySelectPlayer> HideExtras;

        /// <summary>A slot editor closed: redraw what you draw on the panel.</summary>
        public static Action<MenuDeitySelectPlayer> Redraw;

        /// <summary>The slot tier of a deity: Silver / Gold for a slot god, Normal for any other.</summary>
        public static Func<Deity, SlotTier> TierOf;

        /// <summary>For a slot god, the gods whose pause pages apply to it (the perk god first); null for any other deity.</summary>
        public static Func<Deity, List<string>> PageGodsOf;

        /// <summary>For a slot god, the god whose perk it uses; null for any other deity. While set, the god select shows
        /// that god's portrait small beside the slot god's (<see cref="SlotGodBadge"/>).</summary>
        public static Func<Deity, Deity> PerkGodOf;

        /// <summary>Optional portrait of a slot god for a given perk god (an idol carved in that god's likeness). Return
        /// null to keep the slot's own portrait.</summary>
        public static Func<SlotTier, Deity, exSpriteAnimClip> PortraitFor;

        /// <summary>The slot tier of a deity (Normal while <see cref="TierOf"/> is unset).</summary>
        public static SlotTier Tier(Deity d) { return TierOf != null && d != null ? TierOf(d) : SlotTier.Normal; }

        /// <summary>The portrait a slot god of <paramref name="tier"/> with <paramref name="perkGod"/>'s perk shows:
        /// <see cref="PortraitFor"/>'s clip, or <paramref name="fallback"/>.</summary>
        public static exSpriteAnimClip Portrait(SlotTier tier, Deity perkGod, exSpriteAnimClip fallback)
        {
            if (PortraitFor == null || perkGod == null) return fallback;
            try { return PortraitFor(tier, perkGod) ?? fallback; }
            catch (Exception e) { FurtherCore.Log.LogWarning("Slot god portrait: " + e.Message); return fallback; }
        }
    }
}
