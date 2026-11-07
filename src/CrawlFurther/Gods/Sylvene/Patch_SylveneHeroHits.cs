namespace CrawlFurther.Content.Gods.Sylvene
{
    using CrawlFurther.Util;

    /// <summary>
    /// Hits from the hero on a Sylvene monster: its signature may scale the damage or the knockback, or react to the hit,
    /// before the damage is applied (the Briar Champion's lance is trimmed, the Puffball Brute flies back twice as far).
    /// </summary>
    [HarmonyLib.HarmonyPatch(typeof(Health), "Damage", new[] { typeof(DamageInfo), typeof(bool) })]
    static class Patch_SylveneHeroHits
    {
        static bool Prefix(Health __instance, DamageInfo damage, bool hitFriendly, bool __runOriginal)
        {
            if (!__runOriginal) return false;
            if (damage == null || damage.m_source == null || damage.m_amount <= 0f || damage.m_isDamageFromStatus) return true;
            var quirk = __instance.GetComponent<SylveneBehaviour>();
            if (quirk == null || !quirk.Alive) return true;
            var hero = ModUtil.Hero();
            if (hero == null || damage.m_source.m_sourceOwnerPlayer != hero) return true;
            if (!__instance.IsAlive() || !__instance.CanDamage(damage.m_source, hitFriendly)) return true;
            damage.m_amount *= quirk.HeroHitScale(damage);
            damage.m_knockbackMultiplier *= quirk.KnockScale(damage);
            quirk.OnHeroHit(damage);
            return true;
        }
    }
}
