using System;
using System.Collections.Generic;

namespace CrawlFurther.Ghosts
{
    using CrawlFurther.Gods;

    /// <summary>
    /// The ghost forms players pick from. The first registered form is the plain ghost every player starts with; the
    /// mod that owns the forms decides what each one does and sets <see cref="FormOf"/>.
    /// </summary>
    public static class GhostForms
    {
        /// <summary>Every form in list order: the normal ones, then the silver and gold slots.</summary>
        public static readonly List<GhostFormDef> All = new List<GhostFormDef>();

        /// <summary>The form a player's ghost uses; null until a mod provides forms.</summary>
        public static Func<PlayerData, GhostFormDef> FormOf;

        /// <summary>
        /// Add a form. Normal forms go in registration order before the silver and gold slots, which always stay the last
        /// two. Call it from your mod's start callback, before the god select is shown.
        /// </summary>
        public static void Register(GhostFormDef def)
        {
            if (def == null || All.Contains(def)) return;
            if (def.tier == SlotTier.Normal)
            {
                int at = All.FindIndex(d => d.tier != SlotTier.Normal);
                All.Insert(at < 0 ? All.Count : at, def);
            }
            else if (def.tier == SlotTier.Silver)
            {
                int at = All.FindIndex(d => d.tier == SlotTier.Gold);
                All.Insert(at < 0 ? All.Count : at, def);
            }
            else All.Add(def);
        }

        /// <summary>True for the plain ghost (the first form).</summary>
        public static bool IsDefault(GhostFormDef def) { return def != null && All.Count > 0 && def == All[0]; }

        /// <summary>The form with this id, or null.</summary>
        public static GhostFormDef Find(string id) { return All.Find(d => d.id == id); }
    }
}
