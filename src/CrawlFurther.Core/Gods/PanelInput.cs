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
        static readonly Dictionary<int, int> s_busy = new Dictionary<int, int>();
        static readonly Dictionary<int, int> s_freed = new Dictionary<int, int>();

        /// <summary>Block a player's menu input (an editor or page is open for them).</summary>
        public static void Hold(int pid, object who) { s_busy[pid] = who.GetHashCode(); }

        /// <summary>Give a player's menu input back from the frame after next.</summary>
        public static void Free(int pid) { s_busy.Remove(pid); s_freed[pid] = Time.frameCount; }

        /// <summary>True while the player's menu input is held, and on the frame after it is freed.</summary>
        public static bool Blocked(int pid)
        {
            if (s_busy.ContainsKey(pid)) return true;
            int f;
            if (!s_freed.TryGetValue(pid, out f)) return false;
            if (Time.frameCount - f <= 1) return true;
            s_freed.Remove(pid);   // older than the frame after closing: forget it
            return false;
        }

        /// <summary>Anything to check this frame? Drops freed entries older than two frames as it goes.</summary>
        public static bool Any
        {
            get
            {
                if (s_busy.Count > 0) return true;
                if (s_freed.Count == 0) return false;
                List<int> old = null;
                foreach (var kv in s_freed) if (Time.frameCount - kv.Value > 1) (old ?? (old = new List<int>())).Add(kv.Key);
                if (old != null) foreach (var k in old) s_freed.Remove(k);
                return s_freed.Count > 0;
            }
        }
    }
}
