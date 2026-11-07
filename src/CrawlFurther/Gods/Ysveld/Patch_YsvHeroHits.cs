namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Util;

    /// <summary>
    /// Hits from the hero on any monster: a Rime Warden's challenge halves those that miss the Warden; on a Ysveld monster
    /// the quirk may then block the hit, scale it, or react to it before its damage is applied.
    /// </summary>
    [HarmonyLib.HarmonyPatch(typeof(Health), "Damage", new[] { typeof(DamageInfo), typeof(bool) })]
    static class Patch_YsvHeroHits
    {
        [HarmonyLib.HarmonyPriority(HarmonyLib.Priority.High)]
        static bool Prefix(Health __instance, DamageInfo damage, bool hitFriendly, ref bool __result, bool __runOriginal)
        {
            if (!__runOriginal) return false;
            if (damage == null || damage.m_source == null || damage.m_amount <= 0f || damage.m_isDamageFromStatus) return true;
            var quirk = __instance.GetComponent<YsveldBehaviour>();
            if (quirk == null && !YsvChallenged.Any) return true;
            var hero = ModUtil.Hero();
            if (hero == null || damage.m_source.m_sourceOwnerPlayer != hero || __instance.gameObject == hero) return true;
            if (!__instance.IsAlive() || !__instance.CanDamage(damage.m_source, hitFriendly)) return true;
            damage.m_amount *= YsvChallenged.ScaleFor(hero, __instance.gameObject);
            if (quirk == null || !quirk.Alive) return true;
            if (quirk.BlockHeroHit(damage)) { __result = false; return false; }
            damage.m_amount *= quirk.HeroHitScale(damage);
            quirk.OnHeroHit(damage);
            return true;
        }
    }
}
