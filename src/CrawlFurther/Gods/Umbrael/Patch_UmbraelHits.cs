namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Util;

    /// <summary>
    /// Hits between the hero and Umbrael's monsters, before their damage is applied. A hero hit on an Umbrael monster goes
    /// to its quirk (block, scale, react). A monster hit on the hero first goes to the quirk of whoever struck it (a Sand
    /// Wraith holds it back, a Glass Widow glazes him), then cracks a glaze already on him (<see cref="Brittle"/>).
    /// </summary>
    [HarmonyLib.HarmonyPatch(typeof(Health), "Damage", new[] { typeof(DamageInfo), typeof(bool) })]
    static class Patch_UmbraelHits
    {
        [HarmonyLib.HarmonyPriority(HarmonyLib.Priority.High)]
        static bool Prefix(Health __instance, DamageInfo damage, bool hitFriendly, ref bool __result, bool __runOriginal)
        {
            if (!__runOriginal) return false;
            if (damage == null || damage.m_source == null || damage.m_amount <= 0f || damage.m_isDamageFromStatus) return true;
            var hero = ModUtil.Hero();
            if (hero == null || !__instance.IsAlive() || !__instance.CanDamage(damage.m_source, hitFriendly)) return true;

            if (__instance.gameObject == hero)
            {
                var owner = damage.m_source.m_sourceOwner;
                if (owner == null || owner == hero) return true;
                var striker = owner.GetComponent<UmbraelBehaviour>();
                if (striker != null && striker.HoldHitOnHero(damage)) { __result = false; return false; }
                Brittle.Strike(hero, damage);
                if (striker != null) striker.OnHitHero(damage);
                return true;
            }

            var quirk = __instance.GetComponent<UmbraelBehaviour>();
            if (quirk == null || !quirk.Alive || damage.m_source.m_sourceOwnerPlayer != hero) return true;
            if (quirk.BlockHeroHit(damage)) { __result = false; return false; }
            damage.m_amount *= quirk.HeroHitScale(damage);
            quirk.OnHeroHit(damage);
            return true;
        }
    }
}
