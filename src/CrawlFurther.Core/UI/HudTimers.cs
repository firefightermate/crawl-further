using System.Collections.Generic;

namespace CrawlFurther.UI
{
    using CrawlFurther.Art;

    /// <summary>
    /// Small countdowns beside a player's HUD panel: an icon and the whole seconds left, one per running effect. Works
    /// with any number of panels (1-4): beside the panel when there is room, else just above its right end.
    ///
    /// The caller owns the clock. Call <see cref="Set"/> whenever the time left changes and <see cref="Clear(int, string)"/>
    /// when the effect ends. A timer that only runs at certain times (in fights, say) keeps its number while it waits;
    /// pass <c>paused</c> to show it dimmed until it runs again.
    /// </summary>
    public static class HudTimers
    {
        /// <summary>One countdown on one player's panel.</summary>
        internal sealed class Entry
        {
            public string key;
            public float seconds;
            public SpriteSheet icon;
            public bool paused;
        }

        internal static readonly List<Entry>[] Players = { new List<Entry>(), new List<Entry>(), new List<Entry>(), new List<Entry>() };

        /// <summary>Bumped on every change, so the view only rebuilds what it shows when something changed.</summary>
        internal static int Version;

        /// <summary>True while any player has a countdown.</summary>
        public static bool Any
        {
            get { foreach (var l in Players) if (l.Count > 0) return true; return false; }
        }

        /// <summary>
        /// Show or update countdown <paramref name="key"/> on player <paramref name="playerId"/>'s panel (0-3), with
        /// <paramref name="secondsLeft"/> rounded up. <paramref name="icon"/> is drawn from the first frame of its "Idle"
        /// animation (or its first cell); null shows the number alone. Countdowns keep the order they were first set in.
        /// </summary>
        public static void Set(int playerId, string key, float secondsLeft, SpriteSheet icon = null, bool paused = false)
        {
            if (playerId < 0 || playerId >= Players.Length || string.IsNullOrEmpty(key)) return;
            if (secondsLeft <= 0f) { Clear(playerId, key); return; }
            var list = Players[playerId];
            var e = list.Find(x => x.key == key);
            if (e == null) { e = new Entry { key = key }; list.Add(e); Version++; }
            if (e.icon != icon || e.paused != paused || Shown(e.seconds) != Shown(secondsLeft)) Version++;
            e.seconds = secondsLeft;
            e.icon = icon;
            e.paused = paused;
            HudTimerView.Ensure();
        }

        /// <summary>Remove countdown <paramref name="key"/> from a player's panel.</summary>
        public static void Clear(int playerId, string key)
        {
            if (playerId < 0 || playerId >= Players.Length) return;
            if (Players[playerId].RemoveAll(x => x.key == key) > 0) Version++;
        }

        /// <summary>Remove every countdown from a player's panel.</summary>
        public static void Clear(int playerId)
        {
            if (playerId < 0 || playerId >= Players.Length || Players[playerId].Count == 0) return;
            Players[playerId].Clear();
            Version++;
        }

        /// <summary>Remove every countdown from every panel.</summary>
        public static void ClearAll()
        {
            for (int i = 0; i < Players.Length; i++) Clear(i);
        }

        /// <summary>The number shown for a time left: whole seconds, rounded up.</summary>
        internal static int Shown(float seconds) { return UnityEngine.Mathf.CeilToInt(seconds); }
    }
}
