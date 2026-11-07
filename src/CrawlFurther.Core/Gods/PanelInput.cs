using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Gods
{
    /// <summary>
    /// Per-player menu input lock: while a player's origin page or slot editor is open (and on the frame it closes),
    /// that player's menu state machine ignores input, so Back / Confirm never also leave the god select.
    /// </summary>
    public static class PanelInput
    {
        static readonly Dictionary<int, object> s_busy = new Dictionary<int, object>();
        static readonly Dictionary<int, int> s_freed = new Dictionary<int, int>();

        /// <summary>Block a player's menu input (an editor or page is open for them). A Unity object holder that is
        /// destroyed without calling <see cref="Free"/> stops blocking, so a player who left and joined again is never
        /// locked out by an editor that went away with their old panel.</summary>
        public static void Hold(int pid, object who) { s_busy[pid] = who; }

        /// <summary>Give a player's menu input back from the frame after next.</summary>
        public static void Free(int pid) { s_busy.Remove(pid); s_freed[pid] = Time.frameCount; }

        /// <summary>True while the player's menu input is held, and on the frame after it is freed.</summary>
        public static bool Blocked(int pid)
        {
            object who;
            if (s_busy.TryGetValue(pid, out who))
            {
                if (!Gone(who)) return true;
                s_busy.Remove(pid);
            }
            int f;
            if (!s_freed.TryGetValue(pid, out f)) return false;
            if (Time.frameCount - f <= 1) return true;
            s_freed.Remove(pid);   // older than the frame after closing: forget it
            return false;
        }

        /// <summary>Anything to check this frame? Drops freed entries older than two frames and holders that were
        /// destroyed as it goes.</summary>
        public static bool Any
        {
            get
            {
                if (s_busy.Count > 0)
                {
                    List<int> gone = null;
                    foreach (var kv in s_busy) if (Gone(kv.Value)) (gone ?? (gone = new List<int>())).Add(kv.Key);
                    if (gone != null) foreach (var k in gone) s_busy.Remove(k);
                    if (s_busy.Count > 0) return true;
                }
                if (s_freed.Count == 0) return false;
                List<int> old = null;
                foreach (var kv in s_freed) if (Time.frameCount - kv.Value > 1) (old ?? (old = new List<int>())).Add(kv.Key);
                if (old != null) foreach (var k in old) s_freed.Remove(k);
                return s_freed.Count > 0;
            }
        }

        // a destroyed Unity object compares equal to null while the reference itself is still set
        static bool Gone(object who)
        {
            var u = who as Object;
            return who == null || (!ReferenceEquals(u, null) && u == null);
        }
    }
}
