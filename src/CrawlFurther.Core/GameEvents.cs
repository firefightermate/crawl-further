using System;

namespace CrawlFurther
{
    /// <summary>
    /// Events for common moments of a run, so mods need no Harmony patches of their own for them. Handlers run inside
    /// the game's own methods; each is called on its own, and one that throws is logged and stops neither the others nor
    /// the game. Subscribe from your start callback (see <see cref="Further.AddMod"/>), never from Awake: this class
    /// names game types.
    /// </summary>
    public static class GameEvents
    {
        /// <summary>Every pack has registered and the game's systems are up. Runs once, before the self-test.</summary>
        public static event Action GameReady;

        /// <summary>A new run starts (SystemGame.OnStartGame), before its first floor.</summary>
        public static event Action RunStart;

        /// <summary>A floor starts, once its players are set up (SystemPlayers.OnLevelStart).</summary>
        public static event Action FloorStart;

        /// <summary>The hero walked or teleported into a room, the floor's first room included.</summary>
        public static event Action<Room> RoomChanged;

        /// <summary>A monster has been set up in the level (SystemLevel.OnMonsterSpawned, which Player.Init calls).</summary>
        public static event Action<Player> MonsterSpawned;

        /// <summary>The hero took a hit: Health.Damage on the hero returned true. Blocked or cancelled hits are not reported.
        /// The argument is the hit; its m_amount is the damage dealt.</summary>
        public static event Action<DamageInfo> HeroDamaged;

        /// <summary>The players chose to keep playing at the end of a game (<see cref="Game.ContinueGame"/>). The argument is
        /// how many times this game has been continued (1 the first time). Runs once the run is back under way.</summary>
        public static event Action<int> GameContinued;

        internal static void RaiseGameReady() { Raise(GameReady, nameof(GameReady)); }
        internal static void RaiseRunStart() { Raise(RunStart, nameof(RunStart)); }
        internal static void RaiseFloorStart() { Raise(FloorStart, nameof(FloorStart)); }
        internal static bool HasRoomChanged { get { return RoomChanged != null; } }
        internal static void RaiseRoomChanged(Room room) { Raise(RoomChanged, room, nameof(RoomChanged)); }
        internal static bool HasMonsterSpawned { get { return MonsterSpawned != null; } }
        internal static void RaiseMonsterSpawned(Player p) { Raise(MonsterSpawned, p, nameof(MonsterSpawned)); }
        internal static bool HasHeroDamaged { get { return HeroDamaged != null; } }
        internal static void RaiseHeroDamaged(DamageInfo d) { Raise(HeroDamaged, d, nameof(HeroDamaged)); }
        internal static void RaiseGameContinued(int n) { Raise(GameContinued, n, nameof(GameContinued)); }

        static void Raise(Action handlers, string name)
        {
            if (handlers == null) return;
            foreach (Action h in handlers.GetInvocationList())
            {
                try { h(); }
                catch (Exception e) { FurtherCore.Log.LogError(name + " handler " + Describe(h) + " failed: " + e); }
            }
        }

        static void Raise<T>(Action<T> handlers, T arg, string name)
        {
            if (handlers == null) return;
            foreach (Action<T> h in handlers.GetInvocationList())
            {
                try { h(arg); }
                catch (Exception e) { FurtherCore.Log.LogError(name + " handler " + Describe(h) + " failed: " + e); }
            }
        }

        static string Describe(Delegate d)
        {
            return d.Method.DeclaringType == null ? d.Method.Name : d.Method.DeclaringType.FullName + "." + d.Method.Name;
        }
    }
}
