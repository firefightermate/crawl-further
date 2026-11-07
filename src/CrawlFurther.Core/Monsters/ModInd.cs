using UnityEngine;

namespace CrawlFurther.Monsters
{
    /// <summary>
    /// On-body indicators for effects that are not statuses: counters over the head, timed buffs, regeneration and heal
    /// bursts. Make your own with <see cref="ModStatus.Indicator"/> and show them with <see cref="Set"/> or
    /// <see cref="Count"/>; the built-in ones have shortcuts below. All go through <see cref="StatusOverlays"/>, so they
    /// follow the character, size to it, stack above the head with the status overlays, and are cleaned up on expiry,
    /// death, despawn and pooling.
    /// </summary>
    public static class ModInd
    {
        static bool s_built;
        static StatusOverlayDef[] s_charge, s_plates;
        static StatusOverlayDef s_regen, s_heal, s_haste, s_might;

        /// <summary>Build the built-in indicators now (otherwise on first use).</summary>
        public static void Build()
        {
            if (s_built) return;
            s_built = true;
            s_charge = new[]
            {
                ModStatus.Indicator("ModIndCharge1", "FxCommonIndCharge", "One", 1f, OverlayAt.Head),
                ModStatus.Indicator("ModIndCharge2", "FxCommonIndCharge", "Two", 1f, OverlayAt.Head),
                ModStatus.Indicator("ModIndCharge3", "FxCommonIndCharge", "Three", 1f, OverlayAt.Head),
            };
            s_plates = new[]
            {
                ModStatus.Indicator("ModIndPlates1", "FxCommonIndPlates", "One", 1f, OverlayAt.Head),
                ModStatus.Indicator("ModIndPlates2", "FxCommonIndPlates", "Two", 1f, OverlayAt.Head),
                ModStatus.Indicator("ModIndPlates3", "FxCommonIndPlates", "Three", 1f, OverlayAt.Head),
            };
            s_might = ModStatus.Indicator("ModIndMight", "FxCommonIndMight", "Loop", 1f, OverlayAt.Head);
            // body overlays: the feet line is two rows above the cell bottom
            s_regen = ModStatus.Indicator("ModIndRegen", "FxCommonIndRegen", "Loop", -2f, OverlayAt.Feet);
            s_heal = ModStatus.Indicator("ModIndHeal", "FxCommonIndHeal", "Play", -2f, OverlayAt.Feet, once: true);
            s_haste = ModStatus.Indicator("ModIndHaste", "FxCommonIndHaste", "Loop", -2f, OverlayAt.Feet);
        }

        static StatusOverlays On(GameObject who, bool add)
        {
            if (who == null) return null;
            var t = who.GetComponent<StatusOverlays>();
            if (t == null && add && who.activeInHierarchy) t = who.AddComponent<StatusOverlays>();
            return t;
        }

        /// <summary>Show or hide an indicator on <paramref name="who"/>; shown for <paramref name="seconds"/> (0 = until hidden).</summary>
        public static void Set(GameObject who, StatusOverlayDef d, bool on, float seconds = 0f)
        {
            Build();
            if (d == null) return;
            var t = On(who, on);
            if (t == null) return;
            if (on) t.Show(d, seconds); else t.Hide(d);
        }

        /// <summary>A counter: show defs[n-1] and hide the rest (n &lt;= 0 hides all; n past the end shows the last).</summary>
        public static void Count(GameObject who, StatusOverlayDef[] defs, int n)
        {
            Build();
            if (defs == null) return;
            var t = On(who, n > 0);
            if (t == null) return;
            int want = Mathf.Min(n, defs.Length) - 1;
            for (int i = 0; i < defs.Length; i++)
                if (i != want && defs[i] != null && t.Showing(defs[i])) t.Hide(defs[i]);
            if (want >= 0 && defs[want] != null) t.Show(defs[want]);
        }

        /// <summary>Charge pips (0-3) in a three-slot bolt meter.</summary>
        public static void Charge(GameObject who, int pips) { Build(); Count(who, s_charge, pips); }
        /// <summary>Hit-blocking plates (0-3), one shield each.</summary>
        public static void Plates(GameObject who, int plates) { Build(); Count(who, s_plates, plates); }
        /// <summary>Regenerating: on while it heals.</summary>
        public static void Regen(GameObject who, bool on) { Build(); Set(who, s_regen, on); }
        /// <summary>A heal burst on the body (any instant heal).</summary>
        public static void Heal(GameObject who) { Build(); Set(who, s_heal, true); }
        /// <summary>Move speed up for <paramref name="seconds"/> (0 = until switched off).</summary>
        public static void Haste(GameObject who, bool on, float seconds = 0f) { Build(); Set(who, s_haste, on, seconds); }
        /// <summary>Damage dealt up for <paramref name="seconds"/> (0 = until switched off).</summary>
        public static void Might(GameObject who, bool on, float seconds = 0f) { Build(); Set(who, s_might, on, seconds); }
    }
}
