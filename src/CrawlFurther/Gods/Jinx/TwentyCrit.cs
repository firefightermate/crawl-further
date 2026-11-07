using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Natural Twenty: Crit leaps and rolls itself on landing. 20 bursts all round, 1 fumbles (it lies flailing on its
    /// back, dazed <see cref="FumbleTime"/> s), anything else throws one d20 shard per 4 rolled. Advantage: below half
    /// health it rolls twice and keeps the better; both rolls pop up and the lower one is struck through.
    /// </summary>
    public class TwentyCrit : JinxBehaviour
    {
        public const float FumbleTime = 1.2f, ShardSpread = 12f;
        /// <summary>The fumble (set by the kit).</summary>
        public static exSpriteAnimClip FumbleClip;

        /// <summary>Clip event: it lands on its roll.</summary>
        public void ModJinxCrit()
        {
            if (!Alive) return;
            int roll = Random.Range(1, 21);
            bool advantage = Hp != null && Hp.GetHealthCurrent() < Hp.GetHealthMax() * 0.5f;
            Vector2 top = FloatNumber.OverHead(gameObject, 2f);
            if (advantage)
            {
                int other = Random.Range(1, 21);
                int keep = Mathf.Max(roll, other), lose = Mathf.Min(roll, other);
                FloatNumber.Roll(keep, 20, top + new Vector2(-7f, 0f), gameObject);
                FloatNumber.Roll(lose, 20, top + new Vector2(7f, 0f), gameObject);
                if (JinxFx.AdvantageStrike != null) SystemPool.Spawn(JinxFx.AdvantageStrike, top + new Vector2(7f, 4f));
                roll = keep;
            }
            else FloatNumber.Roll(roll, 20, top, gameObject);
            if (roll == 20)
            {
                if (JinxFx.CritBurst != null) FxFactory.SpawnOwned(JinxFx.CritBurst, Me, Own);
            }
            else if (roll == 1)
            {
                if (JinxFx.Fumble != null) SystemPool.Spawn(JinxFx.Fumble, Me + new Vector2(0f, 20f));
                Hold(FumbleClip, FumbleTime);
            }
            else if (JinxFx.D20Shard != null)
            {
                Vector2 from = Me + new Vector2(0f, 12f);
                int n = (roll + 3) / 4;
                float a = AngleTo(from, HeroPos + new Vector2(0f, 6f));
                for (int k = 0; k < n; k++) FxFactory.SpawnOwned(JinxFx.D20Shard, from, Own, a + (k - (n - 1) * 0.5f) * ShardSpread);
            }
        }
    }
}
