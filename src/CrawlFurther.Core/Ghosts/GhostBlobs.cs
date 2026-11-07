using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Ghosts
{
    using CrawlFurther.UI;

    /// <summary>
    /// The blobs a ghost can spawn with Back in place of its form's own (see <see cref="GhostBlobDef"/>). Each player picks
    /// one; a pick that does not fit the player's current form, or is still locked, falls back to the form's own, so a
    /// player who never picks plays exactly as before. The mod that owns the forms sets <see cref="OwnOf"/> and spawns
    /// <see cref="PrefabOf"/>.
    /// </summary>
    public static class GhostBlobs
    {
        /// <summary>Every pickable blob, in picker order.</summary>
        public static readonly List<GhostBlobDef> All = new List<GhostBlobDef>();

        /// <summary>Each player's pick by player id (a <see cref="GhostBlobDef.id"/>); missing or null means the form's own.</summary>
        public static readonly Dictionary<int, string> Chosen = new Dictionary<int, string>();

        /// <summary>A form's own monster for a player (what Back spawns without a pick); set by the forms' mod.</summary>
        public static Func<GhostFormDef, PlayerData, GameObject> OwnOf;

        /// <summary>Add a blob, or replace the one with the same id. Call it from your mod's start callback.</summary>
        public static void Register(GhostBlobDef def)
        {
            if (def == null || string.IsNullOrEmpty(def.id)) return;
            int i = All.FindIndex(d => d.id == def.id);
            if (i >= 0) All[i] = def; else All.Add(def);
        }

        public static GhostBlobDef Find(string id) { return string.IsNullOrEmpty(id) ? null : All.Find(d => d.id == id); }

        /// <summary>The blob may be picked by this form.</summary>
        public static bool Fits(GhostBlobDef def, GhostFormDef form)
        {
            if (def == null) return false;
            try { return def.fits == null || def.fits(form); } catch { return false; }
        }

        /// <summary>Its challenge is done (or it has none).</summary>
        public static bool IsOpen(GhostBlobDef def) { return def != null && (def.unlock == null || Unlocks.IsUnlocked(def.unlock)); }

        /// <summary>The monster a blob spawns for a player (null if it cannot be built).</summary>
        public static GameObject Prefab(GhostBlobDef def, PlayerData pd)
        {
            if (def == null || def.prefab == null) return null;
            try { return def.prefab(pd); } catch { return null; }
        }

        /// <summary>The form's own monster for a player (null when no forms' mod set <see cref="OwnOf"/>).</summary>
        public static GameObject Own(GhostFormDef form, PlayerData pd)
        {
            try { return OwnOf != null ? OwnOf(form, pd) : null; } catch { return null; }
        }

        /// <summary>
        /// The blobs a form can pick besides its own, in order, open or locked: every blob that fits it, except the one
        /// that is the form's own monster anyway.
        /// </summary>
        public static List<GhostBlobDef> ChoicesFor(GhostFormDef form, PlayerData pd)
        {
            var own = Own(form, pd);
            var l = new List<GhostBlobDef>();
            foreach (var d in All)
            {
                if (!Fits(d, form)) continue;
                var p = Prefab(d, pd);
                if (p != null && own != null && p == own) continue;
                l.Add(d);
            }
            return l;
        }

        /// <summary>Any blob this form could pick is open (the picker only asks then).</summary>
        public static bool AnyOpen(GhostFormDef form, PlayerData pd)
        {
            foreach (var d in ChoicesFor(form, pd)) if (IsOpen(d)) return true;
            return false;
        }

        /// <summary>The blob a player's ghost spawns now: their pick when it fits their form and is open, else null (the
        /// form's own). Bots always use their form's own.</summary>
        public static GhostBlobDef ChoiceOf(PlayerData pd)
        {
            if (pd == null || pd.IsBot) return null;
            string id;
            if (!Chosen.TryGetValue(pd.Id, out id)) return null;
            var def = Find(id);
            var form = GhostForms.FormOf != null ? GhostForms.FormOf(pd) : null;
            if (def == null || !Fits(def, form) || !IsOpen(def)) return null;
            var p = Prefab(def, pd);
            if (p == null || p == Own(form, pd)) return null;
            return def;
        }

        /// <summary>What a player's Back spawns: the picked blob's monster, else <paramref name="own"/>.</summary>
        public static GameObject PrefabOf(PlayerData pd, GameObject own)
        {
            var def = ChoiceOf(pd);
            return def != null ? Prefab(def, pd) ?? own : own;
        }

        /// <summary>What one of the player's blobs costs, in bodies of ectoplasm (1 for a form's own).</summary>
        public static int BodiesOf(PlayerData pd)
        {
            var def = ChoiceOf(pd);
            return def != null ? Math.Max(1, def.bodies) : 1;
        }

        /// <summary>Self-test: every blob is well formed and plain, and its challenge exists.</summary>
        public static void SelfCheck(Action<string> bad)
        {
            var ids = new HashSet<string>();
            foreach (var d in All)
            {
                if (!ids.Add(d.id)) bad("ghost blob " + d.id + " registered twice");
                if (d.prefab == null) bad("ghost blob " + d.id + " has no monster");
                if (d.bodies < 1) bad("ghost blob " + d.id + " costs " + d.bodies + " bodies");
                if (d.unlock != null && Unlocks.Find(d.unlock) == null) bad("ghost blob " + d.id + ": no challenge " + d.unlock);
                if (string.IsNullOrEmpty(d.name) || string.IsNullOrEmpty(d.summary)) bad("ghost blob " + d.id + " has no name or summary");
                foreach (char c in (d.name ?? "") + (d.summary ?? ""))
                    if ("%{|}~[]#".IndexOf(c) >= 0 || char.IsDigit(c)) bad("ghost blob " + d.id + " text uses '" + c + "'");
            }
        }
    }
}
