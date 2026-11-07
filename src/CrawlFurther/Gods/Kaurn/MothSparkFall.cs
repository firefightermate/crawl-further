using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Static Moth's Spark Fall: with 3 sparks stored its wings fizz white and every wing beat sheds a spark that drifts down
    /// where it flies (0.4, landing 0.6 s later, its shadow on the floor). Drink the Rods: every rod within
    /// <see cref="DrinkReach"/> px goes dark (no more arcs); it heals <see cref="Heal"/> and stores a spark for each.
    /// </summary>
    public class MothSparkFall : KaurnBehaviour
    {
        public const float Beat = 0.45f, DrinkReach = 80f, Heal = 0.6f;
        public const int MaxDrink = 4;
        public static exSpriteAnimClip FullIdle, FullRun;
        bool m_full;
        float m_beat;

        protected override void OnEnable() { base.OnEnable(); m_full = false; m_beat = Beat; }

        void Update()
        {
            bool full = Unit.pips >= KaurnUnit.MaxPips && Alive;
            if (full != m_full) { m_full = full; SetStance(full ? FullIdle : null, full ? FullRun : null); }
            if (!full) return;
            m_beat -= Time.deltaTime;
            if (m_beat > 0f) return;
            m_beat = Beat;
            if (KaurnFx.SparkFall != null) FxFactory.SpawnOwned(KaurnFx.SparkFall, Me + new Vector2(Random.Range(-5f, 5f), Random.Range(-2f, 2f)), Own);
        }

        /// <summary>Clip event: drink the rods dry.</summary>
        public void KrnDrink()
        {
            int n = 0;
            foreach (var node in KrnNode.Snapshot())
            {
                if (n >= MaxDrink) break;
                if (node == null || !node.gameObject.activeInHierarchy || !node.IsRod) continue;
                if (((Vector2)node.transform.position - Me).sqrMagnitude > DrinkReach * DrinkReach) continue;
                Vector2 at = node.transform.position;
                if (KaurnFx.Drain != null) SystemPool.Spawn(KaurnFx.Drain, at);
                if (KaurnFx.RodDark != null) SystemPool.Spawn(KaurnFx.RodDark, at);
                node.Remove();
                n++;
            }
            if (n == 0) return;
            Monster.Heal(Heal * n);
            Unit.Store(n);
        }
    }
}
