namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Util;

    /// <summary>
    /// Hits on and by Ossivar monsters: a hit from the hero may be blocked or scaled by the victim's mechanic, any hit can be
    /// changed before it lands (Church Grim's undying), and a hit on the hero may be scaled by the attacker's mechanic and
    /// reported to it once it lands.
    /// </summary>
    [HarmonyLib.HarmonyPatch(typeof(Health), "Damage", new[] { typeof(DamageInfo), typeof(bool) })]
    static class Patch_OssHits
    {
        [HarmonyLib.HarmonyPriority(HarmonyLib.Priority.High)]
        static bool Prefix(Health __instance, DamageInfo damage, bool hitFriendly, ref bool __result, bool __runOriginal)
        {
            if (!__runOriginal) return false;
            if (damage == null || damage.m_source == null || damage.m_amount <= 0f || damage.m_isDamageFromStatus) return true;
            if (!__instance.IsAlive() || !__instance.CanDamage(damage.m_source, hitFriendly)) return true;
            var hero = ModUtil.Hero();
            var attacker = damage.m_source.m_sourceOwnerPlayer;
            var victim = __instance.GetComponent<OssBehaviour>();
            if (victim != null && victim.Alive)
            {
                if (hero != null && attacker == hero)
                {
                    if (victim.BlockHeroHit(damage)) { __result = false; return false; }
                    damage.m_amount *= victim.HeroHitScale(damage);
                }
                victim.BeforeDamage(damage);
            }
            else if (hero != null && __instance.gameObject == hero && attacker != null)
            {
                var by = attacker.GetComponent<OssBehaviour>();
                if (by != null) damage.m_amount *= by.HitHeroScale(damage);
            }
            return true;
        }

        static void Postfix(Health __instance, DamageInfo damage, bool __result)
        {
            if (!__result || damage == null || damage.m_source == null || damage.m_isDamageFromStatus) return;
            var hero = ModUtil.Hero();
            var attacker = damage.m_source.m_sourceOwnerPlayer;
            if (hero == null || attacker == null || __instance.gameObject != hero) return;
            var by = attacker.GetComponent<OssBehaviour>();
            if (by != null) by.OnHitHero(damage);
        }
    }
}
