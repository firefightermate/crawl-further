using UnityEngine;

namespace CrawlFurther.Content.Gods.Zhekra
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Amber Hive, Honeycomb: each hit from the hero cracks a cell and drips amber resin onto the floor under it; standing
    /// in resin it mends <see cref="Mend"/> a second (its traits' regenAt). Tell: cracked cells (IdleCrack once three are
    /// cracked) and the growing drip pool.
    /// </summary>
    public class HiveComb : ZhkBehaviour
    {
        public const float Mend = 0.4f, DripSpread = 7f;
        public const int CrackedLook = 3;
        /// <summary>The cracked stance (set by the kit).</summary>
        public static exSpriteAnimClip IdleCrack, RunCrack;

        int m_cracks;

        protected override void OnEnable() { base.OnEnable(); m_cracks = 0; }

        public override void OnHeroHit(DamageInfo d)
        {
            m_cracks++;
            if (m_cracks == CrackedLook) SetStance(IdleCrack, RunCrack);
            if (ZhekraFx.Drip == null) return;
            var off = new Vector2(Random.Range(-DripSpread, DripSpread), Random.Range(-3f, 3f));
            FxFactory.SpawnOwned(ZhekraFx.Drip, Me + off, Own);
        }

        /// <summary>Its traits' regenAt: on (or right by) an amber drip or a resin puddle.</summary>
        public static bool InResin(Vector2 at) { return ZhkResinFx.Nearest(at, 10f) != null; }
    }
}
