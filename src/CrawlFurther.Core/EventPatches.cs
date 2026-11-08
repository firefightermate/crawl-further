using HarmonyLib;
using UnityEngine;

namespace CrawlFurther
{
    using CrawlFurther.Util;

    // The game methods behind GameEvents. Each postfix returns at once when nothing is subscribed.

    [HarmonyPatch(typeof(SystemGame), "OnStartGame")]
    static class Patch_EventRunStart
    {
        static void Postfix() { Game.ContinueGame.Reset(); GameEvents.RaiseRunStart(); }
    }

    [HarmonyPatch(typeof(SystemPlayers), "OnLevelStart")]
    static class Patch_EventFloorStart
    {
        static void Postfix() { GameEvents.RaiseFloorStart(); }
    }

    [HarmonyPatch(typeof(SystemLevel), "OnEnteredRoom")]
    static class Patch_EventRoomChanged
    {
        static void Postfix(Room room)
        {
            if (GameEvents.HasRoomChanged) GameEvents.RaiseRoomChanged(room);
        }
    }

    [HarmonyPatch(typeof(SystemLevel), "OnMonsterSpawned")]
    static class Patch_EventMonsterSpawned
    {
        static void Postfix(GameObject monster)
        {
            if (!GameEvents.HasMonsterSpawned || monster == null) return;
            var p = monster.GetComponent<Player>();
            if (p != null) GameEvents.RaiseMonsterSpawned(p);
        }
    }

    [HarmonyPatch(typeof(Health), "Damage", new[] { typeof(DamageInfo), typeof(bool) })]
    static class Patch_EventHeroDamaged
    {
        static void Postfix(Health __instance, DamageInfo damage, bool __result)
        {
            if (!__result || !GameEvents.HasHeroDamaged) return;
            if (__instance.gameObject == ModUtil.Hero()) GameEvents.RaiseHeroDamaged(damage);
        }
    }
}
