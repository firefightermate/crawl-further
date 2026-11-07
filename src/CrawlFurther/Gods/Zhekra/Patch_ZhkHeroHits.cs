namespace CrawlFurther.Content.Gods.Zhekra
{
    using CrawlFurther.Util;

    /// <summary>
    /// Hits from the hero on a Zhekra monster: its signature may block the hit, scale it or react to it before the damage
    /// is applied, and a Nasute nearby squirts back (Bodyguard).
    /// </summary>
    [HarmonyLib.HarmonyPatch(typeof(Health), "Damage", new[] { typeof(DamageInfo), typeof(bool) })]
    static class Patch_ZhkHeroHits
    {
        [HarmonyLib.HarmonyPriority(HarmonyLib.Priority.High)]
        static bool Prefix(Health __instance, DamageInfo damage, bool hitFriendly, ref bool __result, bool __runOriginal)
        {
            if (!__runOriginal) return false;
            if (damage == null || damage.m_source == null || damage.m_amount <= 0f || damage.m_isDamageFromStatus) return true;
            var brain = __instance.GetComponent<ZhkBrain>();
            if (brain == null) return true;
            var hero = ModUtil.Hero();
            if (hero == null || damage.m_source.m_sourceOwnerPlayer != hero) return true;
            if (!__instance.IsAlive() || !__instance.CanDamage(damage.m_source, hitFriendly)) return true;
            NasuteBodyguard.KinStruck(brain);
            var quirk = __instance.GetComponent<ZhkBehaviour>();
            if (quirk == null || !quirk.Alive) return true;
            if (quirk.BlockHeroHit(damage)) { __result = false; return false; }
            damage.m_amount *= quirk.HeroHitScale(damage);
            quirk.OnHeroHit(damage);
            return true;
        }
    }
}
