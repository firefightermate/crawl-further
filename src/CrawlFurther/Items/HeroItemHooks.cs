using UnityEngine;

namespace CrawlFurther.Content.Items
{
    using CrawlFurther.Util;

    /// <summary>The hero items' parts of Core's Player.Awake, Health.Damage and attack-effect patches (MonsterEvents, ItemRegistry.AddDamageHook).</summary>
    public static class HeroItemHooks
    {
        /// <summary>Every hero carries the item perk components.</summary>
        public static void PlayerAwake(Player p)
        {
            if (R.Get<bool>(p, "m_isHero") && p.GetComponent<HeroPerks>() == null)
                p.gameObject.AddComponent<HeroPerks>();
            if (R.Get<bool>(p, "m_isHero") && p.GetComponent<HeroPerks2>() == null)
                p.gameObject.AddComponent<HeroPerks2>();
        }

        /// <summary>Hero artifacts on a hit. True: the hit is cancelled.</summary>
        public static bool Damage(Health health, DamageInfo damage, GameObject attacker)
        {
            // hero artifacts: Lucky Die, Barnacle Shell, Marionette Cross (incoming) and Jester's Bell (outgoing)
            var p2 = health.GetComponent<HeroPerks2>();
            if (p2 != null && attacker != null && attacker != health.gameObject && !damage.m_isDamageFromStatus)
            {
                damage.m_amount = p2.OnIncoming(damage.m_amount, attacker);
                if (damage.m_amount <= 0f) return true;
            }
            var heroGo = ModUtil.Hero();
            if (heroGo != null && attacker == heroGo && health.gameObject != heroGo && !damage.m_isDamageFromStatus)
            {
                var hp2 = heroGo.GetComponent<HeroPerks2>();
                if (hp2 != null) damage.m_amount = hp2.OnOutgoing(damage.m_amount);
            }
            // Marrow Flask: the hero's bone plates soak monster hits
            var perks = health.GetComponent<HeroPerks>();
            if (perks != null && perks.plates > 0 && attacker != null && attacker != health.gameObject
                && attacker.GetComponent<Player>() != null && perks.TryBlock())
                return true;
            return false;
        }

        /// <summary>Hollow Crown: the hero's own weapon effects get a half-strength shadow repeat.</summary>
        public static void EffectSpawned(Component owner, GameObject instance, GameObject template)
        {
            var perks = owner.GetComponent<HeroPerks>();
            if (perks != null) perks.TryEcho(instance, template);
        }
    }
}
