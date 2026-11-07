namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Util;

    /// <summary>
    /// Hits from the hero on a Jinx monster (or on an ally a Puppeteer holds): the quirk may block the hit, scale it,
    /// or react to it before its damage is applied.
    /// </summary>
    [HarmonyLib.HarmonyPatch(typeof(Health), "Damage", new[] { typeof(DamageInfo), typeof(bool) })]
    static class Patch_JinxHeroHits
    {
        [HarmonyLib.HarmonyPriority(HarmonyLib.Priority.High)]
        static bool Prefix(Health __instance, DamageInfo damage, bool hitFriendly, ref bool __result, bool __runOriginal)
        {
            if (!__runOriginal) return false;
            if (damage == null || damage.m_source == null || damage.m_amount <= 0f || damage.m_isDamageFromStatus) return true;
            var quirk = __instance.GetComponent<JinxBehaviour>();
            var strung = __instance.GetComponent<JinxStrung>();
            if (quirk == null && strung == null) return true;
            var hero = ModUtil.Hero();
            if (hero == null || damage.m_source.m_sourceOwnerPlayer != hero) return true;
            if (!__instance.IsAlive() || !__instance.CanDamage(damage.m_source, hitFriendly)) return true;
            if (strung != null && strung.Held) damage.m_amount *= JinxStrung.DamageTaken;
            if (quirk == null || !quirk.Alive) return true;
            if (quirk.BlockHeroHit(damage)) { __result = false; return false; }
            damage.m_amount *= quirk.HeroHitScale(damage);
            quirk.OnHeroHit(damage);
            return true;
        }
    }
}
