using System;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Content.Ghosts
{
    using CrawlFurther.Items;
    using CrawlFurther.Util;

    /// <summary>
    /// Where the Poltergeist's hex bolt may not hurt the hero (reported 2026-11-11: "as a ghost you can be on top of the
    /// human and hit him with it. Also you can use it in the shop"). A ghost passes through the hero, so a bolt thrown from
    /// on top of him landed at once with no way to dodge it. Now:
    /// <list type="bullet">
    /// <item>the throw doesn't start within <see cref="PointBlank"/> px of the hero, or while the hero is in the shop;</item>
    /// <item>a bolt that reaches the hero while its ghost is that close, or in the shop, does nothing (a throw started
    /// further out and carried in).</item>
    /// </list>
    /// </summary>
    static class PoltergeistLimits
    {
        /// <summary>Closer than this to the hero's centre (world units, about pixels), no bolt.</summary>
        internal const float PointBlank = 32f;

        static bool s_hooked;

        internal static void Register()
        {
            if (s_hooked) return;
            s_hooked = true;
            ItemRegistry.AddDamageHook(CancelBolt);
        }

        internal static bool IsPoltergeist(GameObject body)
        {
            return body != null && ModUtil.PrefabName(body).Contains("_ModPoltergeist");
        }

        /// <summary>The hero is in the shop, or <paramref name="ghost"/> is on top of him.</summary>
        internal static bool Blocked(GameObject ghost)
        {
            try
            {
                var room = SystemLevel.GetCurrentRoom();
                if (room != null && room.m_isPowerupRoom) return true;
            }
            catch { }
            var hero = ModUtil.Hero();
            if (hero == null || ghost == null) return false;
            Vector2 d = ghost.transform.position - hero.transform.position;
            return d.sqrMagnitude < PointBlank * PointBlank;
        }

        static bool CancelBolt(Health health, DamageInfo damage, GameObject attacker)
        {
            if (GhostPack.HexBolt == null || damage == null || damage.m_source == null || damage.m_source.m_source == null) return false;
            if (health == null || health.gameObject != ModUtil.Hero()) return false;
            if (ModUtil.PrefabName(damage.m_source.m_source) != GhostPack.HexBolt.name) return false;
            return Blocked(attacker);
        }
    }

    /// <summary>A Poltergeist can't start its throw in the shop or on top of the hero.</summary>
    [HarmonyPatch(typeof(Attacks), "CanAttack")]
    static class Patch_PoltergeistCanThrow
    {
        static void Postfix(Attacks __instance, ref bool __result)
        {
            if (!__result || __instance == null) return;
            try
            {
                var owner = R.Get<object>(__instance, "m_owner");
                var body = owner is GameObject ? (GameObject)owner : owner is Component ? ((Component)owner).gameObject : null;
                if (PoltergeistLimits.IsPoltergeist(body) && PoltergeistLimits.Blocked(body)) __result = false;
            }
            catch { }
        }
    }
}
