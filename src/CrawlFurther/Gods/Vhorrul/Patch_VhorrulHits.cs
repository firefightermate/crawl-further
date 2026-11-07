namespace CrawlFurther.Content.Gods.Vhorrul
{
    using CrawlFurther.Util;

    /// <summary>
    /// Hits between the hero and a Vhorrul monster, before their damage is applied: the monster's quirk may block, scale
    /// or react to a hit from the hero, and may change a hit it lands on him (holy fire burns and lights the wax at his
    /// feet).
    /// </summary>
    [HarmonyLib.HarmonyPatch(typeof(Health), "Damage", new[] { typeof(DamageInfo), typeof(bool) })]
    static class Patch_VhorrulHits
    {
        static bool Prefix(Health __instance, DamageInfo damage, bool hitFriendly, ref bool __result, bool __runOriginal)
        {
            if (!__runOriginal) return false;
            if (damage == null || damage.m_source == null || damage.m_amount <= 0f || damage.m_isDamageFromStatus) return true;
            var hero = ModUtil.Hero();
            if (hero == null) return true;
            var attacker = damage.m_source.m_sourceOwnerPlayer;
            if (__instance.gameObject == hero)
            {
                var q = attacker != null ? attacker.GetComponent<VhorrulBehaviour>() : null;
                if (q == null || !q.Alive || !__instance.IsAlive() || !__instance.CanDamage(damage.m_source, hitFriendly)) return true;
                if (hero.GetComponent<VhHeroWatch>() == null) hero.AddComponent<VhHeroWatch>();
                q.OnHitHero(damage);
                if (q.Anointed > 0)
                {
                    damage.m_status = VhorrulFx.OnFire;
                    foreach (var w in WaxPuddleFx.Snapshot())
                        if (w != null && w.isActiveAndEnabled && (w.Pos - (UnityEngine.Vector2)hero.transform.position).sqrMagnitude < 16f * 16f)
                            w.Ignite(damage.m_source);
                    q.SetAnointed(q.Anointed - 1);
                }
                return true;
            }
            var quirk = __instance.GetComponent<VhorrulBehaviour>();
            if (quirk == null || attacker != hero || !quirk.Alive || !__instance.CanDamage(damage.m_source, hitFriendly)) return true;
            if (quirk.BlockHeroHit(damage)) { __result = false; return false; }
            damage.m_amount *= quirk.HeroHitScale(damage);
            quirk.OnHeroHit(damage);
            return true;
        }
    }
}
