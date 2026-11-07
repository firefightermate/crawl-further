using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Monsters
{
    using CrawlFurther.Art;
    using CrawlFurther.Util;

    /// <summary>Every pooled or unpooled spawn goes through SystemPool.SpawnInternal: run the template's spawn hook there.</summary>
    [HarmonyPatch(typeof(SystemPool), "SpawnInternal")]
    static class Patch_SpawnHook
    {
        static void Postfix(GameObject prefab, GameObject __result)
        {
            if (__result == null || prefab == null) return;
            Action<GameObject> hook;
            if (FxFactory.OnSpawn.TryGetValue(prefab, out hook) && hook != null)
            {
                try { hook(__result); }
                catch (Exception e) { FurtherCore.Log.LogError("Spawn hook for " + prefab.name + " failed: " + e); }
            }
        }
    }

    /// <summary>Give every mod monster instance its <see cref="ModMonster"/>, then raise <see cref="MonsterEvents.PlayerAwake"/>.</summary>
    [HarmonyPatch(typeof(Player), "Awake")]
    static class Patch_PlayerAwake
    {
        static void Postfix(Player __instance)
        {
            if (__instance == null) return;
            var n = __instance.gameObject.name;
            if (n.StartsWith("Mod") && __instance.GetComponent<ModMonster>() == null)
                __instance.gameObject.AddComponent<ModMonster>();
            MonsterEvents.RaisePlayerAwake(__instance);
        }
    }

    /// <summary>Tier damage scaling against the hero, the item damage hooks, then plates absorbing hero hits.</summary>
    [HarmonyPatch(typeof(Health), "Damage", new[] { typeof(DamageInfo), typeof(bool) })]
    static class Patch_HealthDamage
    {
        static bool Prefix(Health __instance, DamageInfo damage, bool hitFriendly, ref bool __result, bool __runOriginal)
        {
            if (!__runOriginal) return false;   // another prefix (ours or another mod's) already cancelled this hit: use up nothing
            // only a hit the game would actually land may use up a plate (not during invincibility, friendly fire...)
            if (damage == null || damage.m_source == null || damage.m_amount <= 0f || !__instance.CanDamage(damage.m_source, hitFriendly))
                return true;
            var attacker = damage.m_source.m_sourceOwnerPlayer;
            float tierMult;
            if (attacker != null && !damage.m_isDamageFromStatus && attacker != __instance.gameObject && __instance.gameObject == ModUtil.Hero()
                && MonsterFactory.DamageMult.TryGetValue(ModUtil.PrefabName(attacker), out tierMult))
                damage.m_amount *= tierMult;
            if (Items.ItemRegistry.RunDamageHooks(__instance, damage, attacker))
            {
                __result = false;
                return false;
            }
            var mm = __instance.GetComponent<ModMonster>();
            if (mm == null || mm.Plates <= 0) return true;
            var hero = ModUtil.Hero();
            if (hero == null || damage.m_source.m_sourceOwnerPlayer != hero) return true;
            if (!mm.TryBlock(damage)) return true;
            __result = false;
            return false;
        }
    }

    /// <summary>Echoing monsters: when one spawns an attack effect that has an echo template, repeat it after a delay.</summary>
    [HarmonyPatch(typeof(Attacks), "SpawnEffect", new[] { typeof(DamageEffectData), typeof(int) })]
    static class Patch_SpawnEffectEcho
    {
        /// <summary>Attack template -> its echo (see <see cref="FxKit.EchoOf"/>).</summary>
        internal static readonly Dictionary<GameObject, GameObject> EchoOf = new Dictionary<GameObject, GameObject>();

        static readonly AccessTools.FieldRef<Attacks, IAttacksOwner> s_owner = AccessTools.FieldRefAccess<Attacks, IAttacksOwner>("m_owner");

        static void Postfix(Attacks __instance, DamageEffectData effectData, GameObject __result)
        {
            if (__result == null || effectData == null || effectData.m_object == null) return;
            var owner = s_owner(__instance) as Component;   // runs for every attack spawn in the game: no reflection lookup here
            if (owner == null) return;
            var player = owner as Player;
            if (player != null && MonsterEvents.HasAttackSpawned) MonsterEvents.RaiseAttackSpawned(player, __result, effectData.m_object);
            GameObject echo;
            if (!EchoOf.TryGetValue(effectData.m_object, out echo)) return;
            var mm = owner.GetComponent<ModMonster>();
            if (mm == null || !mm.Traits.echo) return;
            mm.QueueEcho(echo, __result.transform.position, __result.transform.rotation, __result.transform.lossyScale, FxFactory.SourceOf(__result));
        }
    }

    /// <summary>
    /// Player.Init puts the health bar at sprite.offset.y + sprite.height + 12: for vanilla that is the trimmed frame's top,
    /// for a mod monster the top of its untrimmed cell (a 49 px cell with 40 px of art floated the bar 9 px over the head).
    /// Put it 11 px over the Idle art's real top, where vanilla puts it.
    /// </summary>
    [HarmonyPatch(typeof(Player), "Init")]
    static class Patch_ModHealthBarHeight
    {
        static void Postfix(Player __instance, exSprite ___m_sprite, bool ___m_isHero, GUIHealthBar ___m_healthbar)
        {
            try
            {
                if (___m_isHero || ___m_sprite == null) return;
                var sheet = SpriteSheets.ByAtlas(___m_sprite.atlas);
                if (sheet == null) return;
                int bx, by, bw, bh;
                if (!MonsterFactory.Bounds(sheet, ___m_sprite.index, out bx, out by, out bw, out bh)) return;
                var off = new Vector3(0f, ___m_sprite.offset.y + by + bh + 11f, -20f);
                R.Set(__instance, "m_healthBarOffset", off);
                if (___m_healthbar != null) ___m_healthbar.transform.position = __instance.transform.position + off;
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Health bar height: " + e.Message); }
        }
    }
}
