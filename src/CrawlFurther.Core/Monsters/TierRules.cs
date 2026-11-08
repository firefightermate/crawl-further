using System;

namespace CrawlFurther.Monsters
{
    /// <summary>
    /// Rules Core applies to every mod monster by its tier, read from the evolution cost: below 2 is tier 1, below 4
    /// tier 2, from 4 up tier 3. A monster's own numbers (<see cref="MonsterDef.damageMult"/>,
    /// <see cref="MonsterDef.specialChargeTime"/>) go on top. Change the fields before your monsters are built.
    /// </summary>
    public static class TierRules
    {
        /// <summary>Multiplier on the hits a tier 2 monster lands on the hero.</summary>
        public static float T2Damage = 1f;
        /// <summary>Multiplier on the hits a tier 3 monster lands on the hero.</summary>
        public static float T3Damage = 1f;
        /// <summary>Multiplier on the special's charge time a tier 2 kit sets.</summary>
        public static float T2SpecialCharge = 0.8f;
        /// <summary>Multiplier on the special's charge time a tier 3 kit sets.</summary>
        public static float T3SpecialCharge = 0.8f;
        /// <summary>Multiplier on the hits a starting monster (evolve cost 0, see <see cref="IsStarter"/>) lands on the
        /// hero. Minions and blobs keep their base's cost and are not starters.</summary>
        public static float StarterDamage = 1f;
        /// <summary>The least max health a starting monster has (0 for no floor).</summary>
        public static float StarterMinHealth = 0f;

        /// <summary>A def's evolution cost is a starting monster's: exactly 0.</summary>
        public static bool IsStarter(float evolveCost) { return Math.Abs(evolveCost) < 0.001f; }

        /// <summary>The tier an evolution cost stands for: 1, 2 or 3.</summary>
        public static int Of(float evolveCost) { return evolveCost >= 4f ? 3 : evolveCost >= 2f ? 2 : 1; }

        /// <summary>The hit multiplier against the hero for <paramref name="tier"/> (starters: see <see cref="StarterDamage"/>).</summary>
        public static float Damage(int tier) { return tier >= 3 ? T3Damage : tier == 2 ? T2Damage : 1f; }

        /// <summary>The special charge-time multiplier for <paramref name="tier"/>.</summary>
        public static float SpecialCharge(int tier) { return tier >= 3 ? T3SpecialCharge : tier == 2 ? T2SpecialCharge : 1f; }
    }
}
