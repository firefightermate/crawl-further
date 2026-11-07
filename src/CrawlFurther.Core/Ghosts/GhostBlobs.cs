using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Ghosts
{
    using CrawlFurther.UI;

    /// <summary>
    /// The blobs a ghost spawns with Back (see <see cref="GhostBlobDef"/>). Every form can use the <see cref="Regular"/>
    /// blob; a blob's <see cref="GhostBlobDef.fits"/> says which other forms may pick it. A form can have a blob of its own
    /// (<see cref="OwnOf"/>): once that blob is open it is the form's default, and until then the form spawns the regular
    /// blob. Each player picks per form; a pick that does not fit the form, or is locked, counts as no pick. The mod that
    /// owns the forms sets <see cref="Regular"/> and <see cref="OwnOf"/> and spawns <see cref="PrefabOf"/>.
    /// </summary>
    public static class GhostBlobs
    {
        /// <summary>Every blob, in picker order.</summary>
        public static readonly List<GhostBlobDef> All = new List<GhostBlobDef>();

        /// <summary>Each player's picks by player id, then by form id (a <see cref="GhostBlobDef.id"/>). A form with no
        /// entry uses its default.</summary>
        public static readonly Dictionary<int, Dictionary<string, string>> Chosen = new Dictionary<int, Dictionary<string, string>>();

        /// <summary>The blob every form can use, always open (the game's own blob).</summary>
        public static GhostBlobDef Regular;

        /// <summary>A form's own blob, its default once open (null: the form has none); set by the forms' mod.</summary>
        public static Func<GhostFormDef, GhostBlobDef> OwnOf;

        /// <summary>Add a blob, or replace the one with the same id. Call it from your mod's start callback.</summary>
        public static void Register(GhostBlobDef def)
        {
            if (def == null || string.IsNullOrEmpty(def.id)) return;
            int i = All.FindIndex(d => d.id == def.id);
            if (i >= 0) All[i] = def; else All.Add(def);
        }

        public static GhostBlobDef Find(string id) { return string.IsNullOrEmpty(id) ? null : All.Find(d => d.id == id); }

        /// <summary>The blob may be picked by this form (the regular blob fits every form).</summary>
        public static bool Fits(GhostBlobDef def, GhostFormDef form)
        {
            if (def == null) return false;
            if (def == Regular) return true;
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

        /// <summary>The form's own blob (null when it has none).</summary>
        public static GhostBlobDef Own(GhostFormDef form)
        {
            try { return OwnOf != null && form != null ? OwnOf(form) : null; } catch { return null; }
        }

        /// <summary>The blobs a form can choose between, open or locked, in order: the regular blob first. One entry means
        /// the form has no choice.</summary>
        public static List<GhostBlobDef> ChoicesFor(GhostFormDef form)
        {
            var l = new List<GhostBlobDef>();
            if (Regular != null) l.Add(Regular);
            foreach (var d in All) if (d != Regular && Fits(d, form)) l.Add(d);
            return l;
        }

        /// <summary>What a form spawns with no pick: its own blob once open, else the regular one.</summary>
        public static GhostBlobDef DefaultFor(GhostFormDef form)
        {
            var own = Own(form);
            return own != null && IsOpen(own) && Fits(own, form) ? own : Regular;
        }

        /// <summary>The id a player picked for a form, or null.</summary>
        public static string PickOf(int playerId, GhostFormDef form)
        {
            Dictionary<string, string> picks;
            string id;
            if (form == null || !Chosen.TryGetValue(playerId, out picks) || !picks.TryGetValue(form.id ?? "", out id)) return null;
            return id;
        }

        /// <summary>Set a player's pick for a form; null (or the form's default) clears it, so the default follows unlocks.</summary>
        public static void SetPick(int playerId, GhostFormDef form, GhostBlobDef def)
        {
            if (form == null) return;
            Dictionary<string, string> picks;
            if (!Chosen.TryGetValue(playerId, out picks)) Chosen[playerId] = picks = new Dictionary<string, string>();
            if (def == null || def == DefaultFor(form)) picks.Remove(form.id ?? "");
            else picks[form.id ?? ""] = def.id;
        }

        /// <summary>A copy of a player's picks (to put back with <see cref="RestorePicks"/> when a menu is cancelled).</summary>
        public static Dictionary<string, string> PicksOf(int playerId)
        {
            Dictionary<string, string> picks;
            return Chosen.TryGetValue(playerId, out picks) ? new Dictionary<string, string>(picks) : new Dictionary<string, string>();
        }

        public static void RestorePicks(int playerId, Dictionary<string, string> picks)
        {
            Chosen[playerId] = picks != null ? new Dictionary<string, string>(picks) : new Dictionary<string, string>();
        }

        /// <summary>The blob a player spawns as <paramref name="form"/>: their pick when it fits and is open, else the
        /// form's default. Bots always use the default.</summary>
        public static GhostBlobDef ChoiceFor(PlayerData pd, GhostFormDef form)
        {
            if (pd != null && !pd.IsBot)
            {
                var def = Find(PickOf(pd.Id, form));
                if (def != null && Fits(def, form) && IsOpen(def)) return def;
            }
            return DefaultFor(form);
        }

        /// <summary>The blob a player's ghost spawns now (their current form).</summary>
        public static GhostBlobDef ChoiceOf(PlayerData pd)
        {
            return ChoiceFor(pd, GhostForms.FormOf != null ? GhostForms.FormOf(pd) : null);
        }

        /// <summary>What a player's Back spawns: the blob in effect's monster, else <paramref name="fallback"/>.</summary>
        public static GameObject PrefabOf(PlayerData pd, GameObject fallback)
        {
            return Prefab(ChoiceOf(pd), pd) ?? fallback;
        }

        /// <summary>What one of the player's blobs costs, in bodies of ectoplasm.</summary>
        public static int BodiesOf(PlayerData pd)
        {
            var def = ChoiceOf(pd);
            return def != null ? Math.Max(1, def.bodies) : 1;
        }

        /// <summary>Self-test: every blob is well formed and plain, its challenge exists, and there is a regular blob.</summary>
        public static void SelfCheck(Action<string> bad)
        {
            if (All.Count > 0 && (Regular == null || !All.Contains(Regular))) bad("ghost blobs: no regular blob registered");
            if (Regular != null && (Regular.unlock != null || Regular.bodies != 1)) bad("ghost blobs: the regular blob must be open and cost one body");
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
            foreach (var f in GhostForms.All)
            {
                var own = Own(f);
                if (own != null && !Fits(own, f)) bad("ghost form " + f.id + ": its own blob " + own.id + " does not fit it");
            }
        }
    }
}
