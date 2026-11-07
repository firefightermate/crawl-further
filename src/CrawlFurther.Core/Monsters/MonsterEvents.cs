using System;
using UnityEngine;

namespace CrawlFurther.Monsters
{
    /// <summary>
    /// Events from the bodies in play (hero and monsters alike), raised from Core's own patches. A handler that throws is
    /// logged and stops neither the others nor the game. Subscribe from your start callback.
    /// </summary>
    public static class MonsterEvents
    {
        /// <summary>A player body woke (Player.Awake): once per instance, pooled ones included. Mod monsters already
        /// have their <see cref="ModMonster"/>.</summary>
        public static event Action<Player> PlayerAwake;

        /// <summary>A player's attack spawned an effect. Arguments: the attacker, the spawned instance, the effect template.</summary>
        public static event Action<Player, GameObject, GameObject> AttackSpawned;

        internal static void RaisePlayerAwake(Player p)
        {
            if (PlayerAwake == null) return;
            foreach (Action<Player> h in PlayerAwake.GetInvocationList())
            {
                try { h(p); }
                catch (Exception e) { FurtherCore.Log.LogError("PlayerAwake handler failed: " + e); }
            }
        }

        internal static bool HasAttackSpawned { get { return AttackSpawned != null; } }

        internal static void RaiseAttackSpawned(Player owner, GameObject instance, GameObject template)
        {
            foreach (Action<Player, GameObject, GameObject> h in AttackSpawned.GetInvocationList())
            {
                try { h(owner, instance, template); }
                catch (Exception e) { FurtherCore.Log.LogError("AttackSpawned handler failed: " + e); }
            }
        }
    }
}
