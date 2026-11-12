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

        /// <summary>Multiplier on a starting monster's max health (after <see cref="StarterMinHealth"/>).</summary>
        public static float StarterHealth = 1f;
        /// <summary>Multiplier on a tier 2 monster's max health.</summary>
        public static float T2Health = 1f;
        /// <summary>Multiplier on a tier 3 monster's max health.</summary>
        public static float T3Health = 1f;

        /// <summary>A monster's own strength factor by def id (1 when it has none), on top of its tier's numbers: its
        /// health and its hits each take the square root, so the factor is what health x damage changes by.</summary>
        public static Func<string, float> StrengthOf;

        /// <summary><see cref="StrengthOf"/> for a def id, 1 when none is set.</summary>
        public static float Strength(string id)
        {
            if (StrengthOf == null || id == null) return 1f;
            float k = StrengthOf(id);
            return k > 0f ? k : 1f;
        }

        /// <summary>A def's evolution cost is a starting monster's: exactly 0.</summary>
        public static bool IsStarter(float evolveCost) { return Math.Abs(evolveCost) < 0.001f; }

        /// <summary>The tier an evolution cost stands for: 1, 2 or 3.</summary>
        public static int Of(float evolveCost) { return evolveCost >= 4f ? 3 : evolveCost >= 2f ? 2 : 1; }

        /// <summary>The hit multiplier against the hero for <paramref name="tier"/> (starters: see <see cref="StarterDamage"/>).</summary>
        public static float Damage(int tier) { return tier >= 3 ? T3Damage : tier == 2 ? T2Damage : 1f; }

        /// <summary>The max health multiplier for a def's evolution cost (minions and blobs: 1).</summary>
        public static float Health(float evolveCost)
        {
            if (IsStarter(evolveCost)) return StarterHealth;
            int t = Of(evolveCost);
            return t >= 3 ? T3Health : t == 2 ? T2Health : 1f;
        }

        /// <summary>The special charge-time multiplier for <paramref name="tier"/>.</summary>
        public static float SpecialCharge(int tier) { return tier >= 3 ? T3SpecialCharge : tier == 2 ? T2SpecialCharge : 1f; }
    }
}
